# -*- coding: utf-8 -*-
"""Tests du pont HTTP local (P0.5-A).

On démarre le pont sur un port éphémère avec un Director injecté sur des
stores TEMPORAIRES : aucun fichier réel n'est touché, aucun Blender n'est
lancé. On vérifie le contrat du pont : etat, objet, deplacer, vision,
et le décodage des images base64.

Lancement : python3 world_builder/tests/test_bridge.py
"""
import base64
import json
import os
import sys
import tempfile
import urllib.request

ICI = os.path.dirname(os.path.abspath(__file__))
PROJET = os.path.dirname(os.path.dirname(ICI))
sys.path.insert(0, PROJET)

from world_builder.asset_registry import Registre  # noqa: E402
from world_builder.director import Director  # noqa: E402
from world_builder.scene_store import SceneStore  # noqa: E402
from world_builder.scene_spec import spec_vide  # noqa: E402
from world_builder import bridge  # noqa: E402


def verifie(nom, condition, detail=""):
    if not condition:
        print("ÉCHEC : %s %s" % (nom, detail))
        return 1
    print("OK    : %s" % nom)
    return 0


def post(srv, route, objet):
    req = urllib.request.Request(
        "http://127.0.0.1:%d%s" % (srv.server_port, route),
        data=json.dumps(objet).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode("utf-8"))


def get(srv, route):
    with urllib.request.urlopen("http://127.0.0.1:%d%s" % (srv.server_port, route)) as r:
        return json.loads(r.read().decode("utf-8"))


def main():
    echecs = 0
    tmp = tempfile.TemporaryDirectory()
    spec = spec_vide()
    spec["slug"] = "maison"
    d = Director(registre=Registre(os.path.join(tmp.name, "registre.json")),
                 scene=SceneStore(os.path.join(tmp.name, "scene.json")),
                 blender=lambda s: {"glb": "modeles/generes/maison_001_v1.glb",
                                    "octets": 1234, "triangles": 600})
    bridge.configurer(d)
    srv = bridge.demarrer(0)

    # 1. etat : scène vide au départ, capacité vision honnête
    etat = get(srv, "/api/etat")
    echecs += verifie("pont : /api/etat ok", etat.get("ok") is True)
    echecs += verifie("pont : scène vide au départ", etat["scene"]["objets"] == [])
    echecs += verifie("pont : vision honnête (pas de faux multimodal)",
                      etat["vision"]["vision_reelle"] is False and
                      "palette" in etat["vision"]["analyse"])

    # 2. creer (Blender simulé) : l'objet arrive au registre ET à la scène
    r = post(srv, "/api/creer", {"demande": "Crée une petite maison nordique en bois sombre.",
                                 "pos": {"x": 3, "z": 5}})
    echecs += verifie("pont : create renvoie un id", r.get("ok") and r["id"] == "building_001", str(r))
    echecs += verifie("pont : create place à la position demandée",
                      r.get("position") == {"x": 3.0, "z": 5.0}, str(r.get("position")))
    etat = get(srv, "/api/etat")
    echecs += verifie("pont : un objet dans la scène", len(etat["scene"]["objets"]) == 1)
    echecs += verifie("pont : meta de l'objet cohérent (registre == scène)",
                      etat["scene"]["objets"][0]["activeVersion"] == 1)

    # 3. objet : détails complets
    o = get(srv, "/api/objet?id=building_001")
    echecs += verifie("pont : /api/objet expose versions + meta",
                      o["ok"] and o["activeVersion"] == 1 and o["versions"][0]["version"] == 1
                      and "materials" in o["meta"], str(o))

    # 4. deplacer : persiste dans la scène
    m = post(srv, "/api/deplacer", {"id": "building_001", "x": 10, "z": 12})
    echecs += verifie("pont : deplacer ok", m.get("ok") and m["position"] == {"x": 10.0, "z": 12.0})
    o = get(srv, "/api/objet?id=building_001")
    echecs += verifie("pont : position persistée", o["objet_en_scene"]["position"]["x"] == 10.0)

    # 5. id inconnu → erreur propre, pas de plantage
    try:
        get(srv, "/api/objet?id=building_999")
        echecs += verifie("pont : objet inconnu → erreur", False)
    except urllib.error.HTTPError as e:
        echecs += verifie("pont : objet inconnu → erreur propre", e.code == 404)

    # 6. décodage image base64 (data URL PNG)
    png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rtest\x00\x00\x00\x00IEND\xaeB`\x82"
    b64 = "data:image/png;base64," + base64.b64encode(png).decode()
    chemin = bridge._ecrire_image_b64(b64)
    echecs += verifie("pont : imageB64 décodée à l'identique",
                      os.path.exists(chemin) and open(chemin, "rb").read() == png)
    os.unlink(chemin)

    srv.shutdown()
    bridge.configurer(None)
    tmp.cleanup()

    print("\nRésultat : %d échec(s)" % echecs)
    return 1 if echecs else 0


if __name__ == "__main__":
    sys.exit(main())
