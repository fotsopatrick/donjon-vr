# -*- coding: utf-8 -*-
"""blender_controller — pilote Blender en mode batch depuis le P0.

Un seul geste : écrire la spec dans un fichier temporaire, lancer
   blender -b --python blender_scripts/construire.py -- <spec> <glb> <apercu> <blend>
et vérifier que le GLB existe. Le script Blender est reproductible :
même spec = même asset. Chaque version garde aussi son .blend source
(modèles/sources/), on ne détruit jamais une source existante.

Ne JAMAIS lancer Blender avec une spec invalide : c'est vérifié en amont.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile

ICI = os.path.dirname(os.path.abspath(__file__))
PROJET = os.path.dirname(ICI)
SCRIPT = os.path.join(ICI, "blender_scripts", "construire.py")
MODELLES = os.path.join(PROJET, "modeles")
GENERES = os.path.join(MODELLES, "generes")
SOURCES = os.path.join(MODELLES, "sources")
APERCUS = os.path.join(ICI, "apercus")


class ErreurBlender(Exception):
    pass


def construire(spec: dict, blender: str = "blender", temps_limite: int = 240) -> dict:
    """Lance Blender sur la spec, produit le GLB + l'aperçu + le .blend source."""
    version = spec.get("_version", 1)
    slug = spec["slug"]
    numero = spec.get("_numero")
    os.makedirs(GENERES, exist_ok=True)
    os.makedirs(SOURCES, exist_ok=True)
    os.makedirs(APERCUS, exist_ok=True)

    nom_base = "%s_%03d_v%d" % (slug, numero, version) if numero else "%s_v%d" % (slug, version)
    glb = os.path.join(GENERES, nom_base + ".glb")
    apercu = os.path.join(APERCUS, nom_base + ".png")
    blend = os.path.join(SOURCES, nom_base + ".blend")

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(spec, f, ensure_ascii=False)
        spec_fichier = f.name
    try:
        cmd = [blender, "-b", "--python", SCRIPT, "--",
               spec_fichier, glb, apercu, blend]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=temps_limite)
        rapport = proc.stdout + proc.stderr
        if not os.path.exists(glb) or os.path.getsize(glb) == 0:
            raise ErreurBlender(
                "Blender n'a pas produit de GLB.\n%s" % rapport[-2000:])
        # le script imprime une ligne de rapport RAPPORT: JSON
        donnees = {"glb": glb, "apercu": apercu if os.path.exists(apercu) else None,
                   "blend": blend if os.path.exists(blend) else None,
                   "triangles": None, "octets": os.path.getsize(glb)}
        for ligne in rapport.splitlines():
            if ligne.startswith("RAPPORT: "):
                try:
                    donnees.update(json.loads(ligne[len("RAPPORT: "):]))
                except Exception:
                    pass
        return donnees
    finally:
        try:
            os.unlink(spec_fichier)
        except OSError:
            pass
