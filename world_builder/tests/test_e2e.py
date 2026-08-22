# -*- coding: utf-8 -*-
"""Test E2E du vertical slice : intention -> spec -> Blender -> GLB -> registre
-> scène -> modification (v2) -> transformation sans Blender.

Utilise un registre, une scène et un dossier de sortie TEMPORAIRES : le dépôt
réel n'est pas touché. Lance le vrai Blender (c'est le point du test).

Lancement : python3 world_builder/tests/test_e2e.py
"""
import os
import sys
import tempfile

ICI = os.path.dirname(os.path.abspath(__file__))
PROJET = os.path.dirname(os.path.dirname(ICI))
sys.path.insert(0, PROJET)

import world_builder.blender_controller as bc
from world_builder.asset_registry import Registre
from world_builder.director import Director
from world_builder.scene_store import SceneStore


def verifie(nom, condition, detail=""):
    if not condition:
        print("ÉCHEC : %s %s" % (nom, detail))
        return 1
    print("OK    : %s" % nom)
    return 0


def main():
    echecs = 0
    with tempfile.TemporaryDirectory() as tmp:
        reg = Registre(os.path.join(tmp, "registre.json"))
        scene = SceneStore(os.path.join(tmp, "scene.json"))
        bc.GENERES = os.path.join(tmp, "glb")
        bc.SOURCES = os.path.join(tmp, "sources")
        bc.APERCUS = os.path.join(tmp, "apercus")

        d = Director(registre=reg, scene=scene)

        # TEST 1 : créer un asset
        r = d.creer("Crée une petite maison nordique en bois sombre avec un toit pentu.",
                    pos=(-6.0, 8.0), lieu=0)
        aid = r["id"]
        echecs += verifie("create : id construit", aid == "building_001", aid)
        echecs += verifie("create : spec respecte la demande",
                          "dark_wood" in r["spec"]["materials"])
        echecs += verifie("create : source de spec annoncée",
                          r["spec_source"] in ("regles_locales", "deepseek"), r["spec_source"])

        # TEST 2 : export GLB réel
        echecs += verifie("export : GLB présent", os.path.exists(r["glb"]), r["glb"])
        echecs += verifie("export : octets > 0", r["octets"] and r["octets"] > 0)
        echecs += verifie("export : triangles > 0", r["triangles"] and r["triangles"] > 0)
        source_v1 = os.path.join(bc.SOURCES, "maison_001_v1.blend")
        echecs += verifie("export : source .blend v1", os.path.exists(source_v1), source_v1)

        # TEST 4/5 : placé + ID
        obj = scene.obtenir(aid)
        echecs += verifie("placement : position demandée",
                          obj["position"] == {"x": -6.0, "z": 8.0}, str(obj["position"]))
        echecs += verifie("identité : version 1", obj["assetVersion"] == 1)

        # TEST 8 : modifier le modèle (géométrie) -> nouvelle version
        m = d.modifier(aid, "Vieillis le bois et ajoute de la mousse, et augmente sa taille de 20%.")
        echecs += verifie("modify : géométrique détecté", m["geometrique"] is True)
        echecs += verifie("modify : nouvelle version 2", m["nouvelleVersion"] == 2)
        echecs += verifie("modify : v2 vieillie", m["spec"]["variation"]["weathered"] == 0.7)
        echecs += verifie("modify : GLB v2 présent", os.path.exists(m["glb"]), m["glb"])
        obj2 = scene.obtenir(aid)
        echecs += verifie("modify : scène pointe v2", obj2["assetVersion"] == 2)
        echecs += verifie("modify : échelle appliquée (Three.js)",
                          abs(obj2["echelle"] - 1.2) < 0.001, str(obj2["echelle"]))
        echecs += verifie("identité : même ID après modification", obj2["id"] == aid)

        # TEST 9 : réexport -> v2 bien une deuxième version distincte
        echecs += verifie("versions : v1 et v2 coexistent",
                          os.path.exists(r["glb"]) and os.path.exists(m["glb"]))

        # TEST 7 : modification uniquement de position (pas de Blender)
        p = scene.obtenir(aid)["position"]
        avant = scene.obtenir(aid)["assetVersion"]
        m2 = d.modifier(aid, "Déplace la maison de 10 mètres vers le nord.")
        echecs += verifie("déplacement : non géométrique", m2["geometrique"] is False)
        echecs += verifie("déplacement : aucune nouvelle version",
                          scene.obtenir(aid)["assetVersion"] == avant)
        echecs += verifie("déplacement : position nord",
                          scene.obtenir(aid)["position"]["z"] == round(p["z"] - 10, 3),
                          str(scene.obtenir(aid)["position"]))

        # registre : ancienne version conservée, ID stable
        entree = reg.obtenir(aid)
        echecs += verifie("registre : 2 versions", len(entree["versions"]) == 2)
        echecs += verifie("registre : v1 non supprimée",
                          entree["versions"][0]["file"].endswith("_v1.glb"))

    print("\nRésultat : %d échec(s)" % echecs)
    return 1 if echecs else 0


if __name__ == "__main__":
    sys.exit(main())
