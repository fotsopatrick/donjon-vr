# -*- coding: utf-8 -*-
"""Tests unitaires du world builder (spec, registre, scène, analyse, décomposition).

Lancement : python3 world_builder/tests/test_unit.py
"""
import os
import sys
import tempfile

ICI = os.path.dirname(os.path.abspath(__file__))
PROJET = os.path.dirname(os.path.dirname(ICI))
sys.path.insert(0, PROJET)

from world_builder.asset_registry import Registre
from world_builder.director import _parse_transformations
from world_builder.reference_analyzer import PaletteReferenceAnalyzer
from world_builder.scene_spec import STYLE_PROFILE_DEFAUT, est_geometrique, meta_spec, valider
from world_builder.scene_store import SceneStore
from world_builder.spec_generator import generer_locale

AUTRES = ("   ", 0)


def verifie(nom, condition, detail=""):
    if not condition:
        print("ÉCHEC : %s %s" % (nom, detail))
        return 1
    print("OK    : %s" % nom)
    return 0


def main():
    echecs = 0

    # 1. spec : valeurs par défaut, style_profile présent, validation
    spec = valider({"operation": "create_asset", "type": "building",
                    "slug": "Maison Nordique!", "materials": ["dark_wood"]})
    echecs += verifie("spec slug normalisé", spec["slug"] == "maison-nordique", spec["slug"])
    echecs += verifie("spec type", spec["type"] == "building")
    echecs += verifie("spec style_profile par défaut",
                      spec["style_profile"] == STYLE_PROFILE_DEFAUT,
                      str(spec["style_profile"]))
    try:
        valider({"operation": "create_asset", "type": "vaisseau"})
        echecs += verifie("spec rejette un type inconnu", False)
    except Exception:
        echecs += verifie("spec rejette un type inconnu", True)

    # 2. règles locales
    spec2 = generer_locale("Crée une petite maison nordique en bois sombre avec un toit pentu.")
    echecs += verifie("règles : style nordic", spec2["style"] == "nordic")
    echecs += verifie("règles : dark_wood présent", "dark_wood" in spec2["materials"])
    echecs += verifie("règles : toit pentu fort", spec2["toit"]["pente"] == "forte")
    echecs += verifie("règles : dimensions petites", spec2["dimensions"]["l"] <= 3.0)

    # 3. décomposition géométrie vs transformation (point 9)
    echecs += verifie("déplacement = transformation",
                      est_geometrique("Déplace la maison de 10 mètres vers le nord") is False)
    echecs += verifie("vieillir = géométrique",
                      est_geometrique("Vieillis le bois") is True)
    echecs += verifie("échelle seule = transformation",
                      est_geometrique("Augmente sa taille de 20 pour cent") is False)

    # 4. parse des transformations
    t = _parse_transformations("Déplace la maison de 10 mètres vers le nord")
    echecs += verifie("parse : déplacement nord", t.get("position", {}).get("z") == -10, str(t))
    t = _parse_transformations("Vieillis le bois et augmente sa taille de 20%")
    echecs += verifie("parse : échelle +20%", abs(t.get("echelle", 0) - 1.2) < 0.001, str(t))

    # 5. registre : ID, versions jamais supprimées
    with tempfile.TemporaryDirectory() as tmp:
        r = Registre(os.path.join(tmp, "registre.json"))
        aid = r.prochain_id("building")
        echecs += verifie("registre : prochain id", aid == "building_001", aid)
        r.creer(aid, spec, "maison_001_v1.glb")
        echecs += verifie("registre : version 1 active", r.fichier_actif(aid) == "maison_001_v1.glb")
        r.nouvelle_version(aid, spec, "maison_001_v2.glb")
        echecs += verifie("registre : v2 active", r.fichier_actif(aid) == "maison_001_v2.glb")
        echecs += verifie("registre : ancienne version conservée",
                          r.obtenir(aid)["versions"][0]["file"] == "maison_001_v1.glb")
        echecs += verifie("registre : même ID logique", aid == "building_001")

        s = SceneStore(os.path.join(tmp, "scene.json"))
        s.ajouter({"id": aid, "assetFile": "maison_001_v2.glb", "assetVersion": 2,
                   "lieu": 0, "position": {"x": -6.0, "z": 8.0}, "rotationY": 0,
                   "echelle": 1.2, "meta": {}})
        s.mettre_a_jour(aid, {"position": {"x": -6.0, "z": -2.0}})
        echecs += verifie("scène : position à jour",
                          s.obtenir(aid)["position"]["z"] == -2.0)

        # cohérence meta registre/scène (P0.5-16) : le chemin EXACT de
        # director.modifier() — nouvelle_version + meta_spec dans la scène.
        spec_v2 = dict(spec)
        spec_v2["materials"] = ["dark_wood", "moss"]
        r.nouvelle_version(aid, spec_v2, "maison_001_v2.glb")
        s.mettre_a_jour(aid, {"assetVersion": 2, "meta": meta_spec(spec_v2)})
        echecs += verifie("cohérence : meta registre == meta scène",
                          r.obtenir(aid)["meta"] == s.obtenir(aid)["meta"],
                          "registre %s != scène %s" % (r.obtenir(aid)["meta"],
                                                       s.obtenir(aid)["meta"]))

    # 6. analyse de référence RÉELLE (PNG du projet, palette)
    apercu = os.path.join(PROJET, "blender", "apercu_tonneau.png")
    if os.path.exists(apercu):
        faits = PaletteReferenceAnalyzer().analyser(apercu)
        echecs += verifie("analyse : palette non vide", len(faits["palette_dominante"]) > 0,
                          str(faits["palette_dominante"]))
        echecs += verifie("analyse : avertissement honnête présent",
                          "avertissement" in faits and "vision" in faits["avertissement"])
    else:
        echecs += verifie("analyse : PNG de référence absent", False, apercu)

    # 7. vision RÉELLE : jamais de simulation, déductions issues du profil
    from world_builder.reference_analyzer import VisionReferenceAnalyzer  # noqa: E402
    from world_builder.deepseek_client import DeepSeekClient  # noqa: E402
    vision_sans_cle = VisionReferenceAnalyzer(client=DeepSeekClient(cle=""))
    echecs += verifie("vision : pas de clé → indisponible",
                      vision_sans_cle.disponible() is False)
    try:
        vision_sans_cle.analyser(apercu)
        echecs += verifie("vision : refuse d'agir sans clé (pas de simulation)", False)
    except Exception as e:
        msg = str(e)
        echecs += verifie("vision : refuse d'agir sans clé (pas de simulation)",
                          "simule" in msg or "clé" in msg, msg)

    profil = {"materials_observed": ["pierre sombre", "stone"],
              "observed": ["grande salle circulaire", "colonnade", "arches",
                           "sol bleu lumineux", "anneau de lumières orange"],
              "spatial_composition": {"stairs": ["gradins concentriques"]},
              "lighting": {"emissive_elements": ["sol bleu lumineux",
                                                 "points orange lumineux"]},
              "scene": {"interior_or_exterior": "interior"},
              "incertitude": "faible"}
    ded = VisionReferenceAnalyzer._deductions(profil)
    echecs += verifie("vision : déductions = lecture du profil",
                      ded.get("pierre_sombre") and ded.get("pierre") and ded.get("colonnes")
                      and ded.get("arches") and ded.get("gradins") and ded.get("centre_cyan")
                      and ded.get("feux_orange") and ded.get("interieur"), str(ded))
    profil2 = {"materials_observed": ["wood"], "incertitude": "forte"}
    ded2 = VisionReferenceAnalyzer._deductions(profil2)
    echecs += verifie("vision : wood seul n'est pas du bois_sombre",
                      "pierre_sombre" not in ded2 and "bois" not in ded2, str(ded2))

    print("\nRésultat : %d échec(s)" % echecs)
    return 1 if echecs else 0


if __name__ == "__main__":
    sys.exit(main())
