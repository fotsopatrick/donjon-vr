# -*- coding: utf-8 -*-
"""TEST RÉEL — la chaîne complète vision : photo → VisualProfile → DeepSeek spec
→ Blender → GLB → registre → scène Three.js.

Lancement : python3 world_builder/tests/test_vision_reelle.py [image] [demande]

Prérequis :
  - clé DeepSeek : env DEEPSEEK_API_KEY, sinon cherchée dans le coffre local
    opencode (~/.local/share/opencode/auth.json). Jamais affichée.
  - Blender installé (déjà utilisé par le P0).

Le registre et la scène RÉELS du jeu sont utilisés : l'objet créé entre dans
monde/scene.json et est visible dans le jeu (test Three.js séparé :
probe-asset.js). Rien n'est poussé, rien n'est simulé : sans clé, le test
s'arrête net.
"""
import json
import os
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
PROJET = os.path.dirname(os.path.dirname(ICI))
sys.path.insert(0, PROJET)

from world_builder.director import Director  # noqa: E402
from world_builder.reference_analyzer import VisionReferenceAnalyzer  # noqa: E402


def _cle_deepseek() -> str:
    cle = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if cle:
        return cle
    for chemin in (os.path.expanduser("~/.local/share/opencode/auth.json"),):
        try:
            d = json.load(open(chemin, encoding="utf-8"))
            cle = (d.get("deepseek") or {}).get("key", "")
            if cle:
                return cle
        except Exception:
            pass
    return ""


def _verifie(nom, cond, detail=""):
    ligne = "OK    : " if cond else "ÉCHEC : "
    ligne += nom
    if not cond and detail:
        ligne += "  (%s)" % detail
    print(ligne)
    return 0 if cond else 1


def main():
    image = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        ICI, "..", "apercus", "maison_003_v2.png")
    demande = sys.argv[2] if len(sys.argv) > 2 else \
        "Crée un bâtiment fidèle à l'image de référence."
    image = os.path.abspath(image)
    if not os.path.exists(image):
        print("ÉCHEC : image de référence absente : %s" % image)
        return 2

    cle = _cle_deepseek()
    if not cle:
        print("CLÉ ABSENTE : la vision réelle est impossible. On s'arrête, "
              "on ne simule pas la vision.")
        return 2
    os.environ["DEEPSEEK_API_KEY"] = cle

    echecs = 0

    # 1. L'image est LUE réellement par le modèle vision
    analyseur = VisionReferenceAnalyzer()
    print("== 1) VisualProfile réel (%s) ==" % analyseur.modele_vision)
    faits = analyseur.analyser(image)
    profil = faits["visual_profile"]
    print(json.dumps(profil, ensure_ascii=False, indent=2))
    echecs += _verifie("vision : profil structuré renvoyé", isinstance(profil, dict))
    echecs += _verifie("vision : déductions issues de la lecture",
                       bool(faits["deductions"]), str(faits["deductions"]))

    # 2 à 6. Intention + VisualProfile -> DeepSeek spec -> Blender -> GLB
    print("== 2) chaîne complète : intention + VisualProfile -> spec -> Blender -> GLB ==")
    d = Director(analyseur=analyseur)
    r = d.creer(demande, image=image, pos=(16.0, 6.0), lieu=0)
    print("  spec_source : %s" % r["spec_source"])
    print("  id          : %s" % r["id"])
    print("  spec        : %s" % json.dumps(r["spec"], ensure_ascii=False))
    print("  glb         : %s" % r["glb"])
    echecs += _verifie("create : spec produite par DeepSeek",
                       r["spec_source"] == "deepseek", r["spec_source"])
    echecs += _verifie("create : image réellement analysée", r["image_analysee"] is True)
    echecs += _verifie("create : GLB produit (octets > 0)",
                       bool(r["octets"] and r["octets"] > 0), str(r.get("octets")))
    echecs += _verifie("create : triangles > 0", bool(r["triangles"] and r["triangles"] > 0),
                       str(r.get("triangles")))
    echecs += _verifie("create : placé dans la scène réelle du jeu",
                       d.scene.obtenir(r["id"])["position"]["x"] == 16.0,
                       str(d.scene.obtenir(r["id"])["position"]))
    echecs += _verifie("create : registre réel à jour",
                       d.registre.fichier_actif(r["id"]) == r["glb"], r["glb"])

    print("\nRésultat : %d échec(s)" % echecs)
    print("Le nouvel asset est dans monde/scene.json : %s (version 1)" % r["id"])
    print("Étape suivante (Three.js) : node world_builder/tests/probe-asset.js <port> %s" % r["id"])
    return 1 if echecs else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print("ÉCHEC GLOBAL : %s" % e)
        sys.exit(1)
