# -*- coding: utf-8 -*-
"""art_direction — le WorldArtDirectionProfile (P0, étape 6).

Le profil artistique GLOBAL du jeu, lisible par le world builder (Blender)
et par le jeu (Three.js). Source de vérité : art_direction.json dans ce
dossier. Ce module Python :

  * charge le JSON et le VALIDE (structure minimale attendue) ;
  * expose des accès commodes pour les générateurs :
      - palette()          -> les couleurs dominantes/secondaires/accents
      - materials(famille) -> les presets material_lib d'une famille
      - lumiere(map)       -> le preset lighting_lib conseillé pour une map
      - map(nom)           -> la fiche d'identité d'une map

RÈGLE (22/08) : jamais de valeurs inventées ici. Si le JSON est illisible ou
incomplet, on échoue (ErreurProfil) plutôt que de feindre d'avoir un profil.
"""
from __future__ import annotations

import json
import os
from typing import Any

ICI = os.path.dirname(os.path.abspath(__file__))
FICHIER = os.path.join(ICI, "art_direction.json")


class ErreurProfil(Exception):
    """Le profil artistique est absent, illisible ou incomplet."""


def charger(chemin: str | None = None) -> dict:
    """Charge et valide le profil. Échoue si le fichier est introuvable ou
    si les sections obligatoires manquent — on ne feint pas un profil."""
    p = chemin or FICHIER
    if not os.path.exists(p):
        raise ErreurProfil("profil introuvable : %s" % p)
    try:
        with open(p, encoding="utf-8") as f:
            profil = json.load(f)
    except Exception as e:
        raise ErreurProfil("profil illisible : %s" % e)

    obligatoires = ["palette", "materials", "lighting", "atmosphere",
                    "architecture", "set_dressing", "quality", "maps"]
    manquants = [k for k in obligatoires if k not in profil]
    if manquants:
        raise ErreurProfil("sections manquantes : %s" % ", ".join(manquants))
    if "nom" not in profil or profil["nom"] != "WorldArtDirectionProfile":
        raise ErreurProfil("nom de profil inattendu : %r" % profil.get("nom"))
    return profil


def palette(profil: dict) -> dict:
    """Retourne les couleurs {dominants, secondaires, accents} en hex."""
    return {
        cle: [c["hex"] for c in profil["palette"].get(cle, [])]
        for cle in ("dominants", "secondaires", "accents")
    }


def materials(profil: dict, famille: str) -> list[str]:
    """Presets material_lib d'une famille (pierre, bois, metal, eau...)."""
    f = profil["materials"].get(famille)
    if not f:
        raise ErreurProfil("famille de matériaux inconnue : %s" % famille)
    return list(f.get("presets", []))


def _vers_snake(nom: str) -> str:
    return (nom or "").lower().replace(" ", "_").replace("-", "_").strip()


def lumiere(profil: dict, map: str | None = None) -> dict:
    """Preset lighting_lib conseillé. Priorité : lighting.presets_par_map
    (si le JSON en déclare), sinon réglé sur le profil du jeu."""
    presets_map = (profil.get("lighting") or {}).get("presets_par_map") or {}
    if map:
        nom = presets_map.get(map) or presets_map.get(_vers_snake(map))
        if nom:
            return {"map": map, "preset": nom}
    return {"map": map or "?", "preset": "cinematic_contrast"}


def map(profil: dict, nom: str) -> dict:
    """Fiche d'identité d'une map. Échoue si la map n'est pas déclarée."""
    m = (profil.get("maps") or {}).get(nom) or (profil.get("maps") or {}).get(_vers_snake(nom))
    if not m:
        raise ErreurProfil("map inconnue du profil : %s" % nom)
    return m


def profil_jeu(profil: dict, nom_map: str) -> dict:
    """Tout ce qu'il faut pour rendre UNE map : rendu + palette + materials +
    lighting + atmosphere, fusionné. C'est ce que le jeu (Three.js) applique."""
    identite = map(profil, nom_map)
    return {
        "nom": profil["nom"],
        "direction": profil["direction"],
        "rendu": profil.get("rendu_definition"),
        "palette": palette(profil),
        "materials": profil["materials"],
        "lighting": profil["lighting"],
        "atmosphere": profil["atmosphere"],
        "identite_map": identite,
    }


if __name__ == "__main__":
    import sys
    try:
        p = charger()
    except ErreurProfil as e:
        print("ÉCHEC : %s" % e, file=sys.stderr)
        sys.exit(1)
    print("WorldArtDirectionProfile v%s — %s" % (p.get("version"), p.get("direction")))
    print("dominants  :", " ".join(palette(p)["dominants"]))
    print("accents    :", " ".join(palette(p)["accents"]))
    print("pierre     :", materials(p, "pierre"))
    print("maps       :", ", ".join(p["maps"].keys()))
