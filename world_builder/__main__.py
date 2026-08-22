# -*- coding: utf-8 -*-
"""CLI du world builder (P0).

Usage :
  python3 -m world_builder create "demande" [--image ref.png] [--pos x,z] [--lieu N]
  python3 -m world_builder modify <id> "demande"
  python3 -m world_builder list
  python3 -m world_builder show <id>
  python3 -m world_builder spec "demande" [--image ref.png]

Exemples :
  python3 -m world_builder create "Crée une petite maison nordique en bois sombre avec un toit pentu."
  python3 -m world_builder modify building_001 "Vieillis le bois et augmente sa taille de 20%."
  python3 -m world_builder modify building_001 "Déplace la maison de 10 mètres vers le nord."
"""
from __future__ import annotations

import argparse
import json
import sys

from .asset_registry import Registre
from .director import Director
from .scene_store import SceneStore


def _ligne(d) -> None:
    print(json.dumps(d, ensure_ascii=False, indent=2))


def main(argv: list | None = None) -> int:
    p = argparse.ArgumentParser(prog="world_builder",
                                description="AI World Builder — P0")
    sous = p.add_subparsers(dest="commande", required=True)

    c_create = sous.add_parser("create", help="créer un asset depuis une intention")
    c_create.add_argument("demande")
    c_create.add_argument("--image", help="image de référence (PNG)")
    c_create.add_argument("--pos", help="position x,z (sinon place par défaut)")
    c_create.add_argument("--lieu", type=int, default=0, help="niveau du monde (0=hameau)")

    c_modify = sous.add_parser("modify", help="modifier un objet existant")
    c_modify.add_argument("id")
    c_modify.add_argument("demande")

    sous.add_parser("list", help="liste des assets du registre")
    c_show = sous.add_parser("show", help="détail d'un asset")
    c_show.add_argument("id")

    c_spec = sous.add_parser("spec", help="afficher la spec sans lancer Blender")
    c_spec.add_argument("demande")
    c_spec.add_argument("--image", help="image de référence (PNG)")

    args = p.parse_args(argv)
    d = Director()

    if args.commande == "create":
        pos = tuple(float(v) for v in args.pos.split(",")) if args.pos else None
        r = d.creer(args.demande, image=args.image, pos=pos, lieu=args.lieu)
        _ligne(r)
    elif args.commande == "modify":
        r = d.modifier(args.id, args.demande)
        _ligne(r)
    elif args.commande == "list":
        reg = Registre()
        scene = SceneStore()
        for asset_id, entree in sorted(reg.tout().items()):
            obj = None
            try:
                obj = scene.obtenir(asset_id)
            except KeyError:
                pass
            print("%s  v%s  %s  %s" % (
                asset_id,
                entree["activeVersion"],
                entree["slug"],
                obj["position"] if obj else "(non placé)"))
    elif args.commande == "show":
        reg = Registre()
        entree = reg.obtenir(args.id)
        _ligne(entree)
        scene = SceneStore()
        try:
            _ligne({"objet_en_scene": scene.obtenir(args.id)})
        except KeyError:
            print("(objet non placé dans la scène)")
    elif args.commande == "spec":
        ref = None
        if args.image:
            ref = d.analyseur.analyser(args.image)
        spec = None
        if d.client.disponible():
            spec = d.client.spec_create(args.demande, ref)
            spec["operation"] = "create_asset"
            _ligne({"spec_source": "deepseek", "ref_faits": ref, "spec": spec})
        else:
            from .spec_generator import generer_locale
            spec = generer_locale(args.demande, ref, "create_asset")
            _ligne({"spec_source": "regles_locales (clé DeepSeek absente)",
                    "ref_faits": ref, "spec": spec})
    return 0


if __name__ == "__main__":
    sys.exit(main())
