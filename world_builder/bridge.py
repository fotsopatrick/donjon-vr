# -*- coding: utf-8 -*-
"""bridge — pont local HTTP entre le jeu Three.js et le world builder.

Le navigateur (servi sur http://127.0.0.1:8099) ne peut ni lancer Blender ni
écrire monde/scene.json. Ce petit serveur (stdlib, ZÉRO dépendance) expose le
Director existant par HTTP local. Il n'écoute que 127.0.0.1 et ne part sur
aucun réseau : c'est une prise locale, pas un backend généraliste.

  GET  /api/etat            → scène + registre (résumé), capacité vision
  GET  /api/objet?id=…      → état + meta d'un objet
  POST /api/creer           → {demande, imageB64?, pos:{x,z}?, lieu?}
  POST /api/modifier        → {id, demande}
  POST /api/deplacer        → {id, x, z}

Lancer :   python3 -m world_builder.bridge          (port 8765)
Pour le jeu : (cd ~/donjon-vr && python3 -m http.server 8099)
"""
from __future__ import annotations

import base64
import json
import os
import re
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

ICI = os.path.dirname(os.path.abspath(__file__))
PROJET = os.path.dirname(ICI)
if PROJET not in sys.path:
    sys.path.insert(0, PROJET)

from world_builder.director import Director  # noqa: E402
from world_builder.asset_registry import Registre  # noqa: E402
from world_builder.scene_store import SceneStore  # noqa: E402

PORT = int(os.environ.get("WB_PONT_PORT", "8765"))
REFERENCES = os.path.join(ICI, "references")
_seuil = threading.Lock()
_verrou_blender = threading.Lock()   # une génération Blender à la fois


def _ecrire_image_b64(image_b64: str) -> str:
    """Décode une data URL (ou un base64 nu) vers un PNG local. Renvoie le
    chemin absolu du fichier de référence conservé."""
    os.makedirs(REFERENCES, exist_ok=True)
    m = re.match(r"data:image/(png|jpeg|jpg|webp);base64,", image_b64)
    corps = image_b64[m.end():] if m else image_b64
    suffixe = ".png"
    if m and m.group(1) in ("jpeg", "jpg"):
        suffixe = ".jpg"
    elif m and m.group(1) == "webp":
        suffixe = ".webp"
    try:
        octets = base64.b64decode(corps)
    except Exception as e:
        raise ValueError("imageB64 illisible : %s" % e)
    if not octets:
        raise ValueError("image vide")
    nom = "ref_%s%s" % (time.strftime("%Y%m%d-%H%M%S"), suffixe)
    chemin = os.path.join(REFERENCES, nom)
    with open(chemin, "wb") as f:
        f.write(octets)
    return chemin


class PontHandler(BaseHTTPRequestHandler):
    serveur_ = None

    def log_message(self, fmt, *args):  # silencieux mais pas muet
        pass
    def _tete(self, code=200, ctype="application/json; charset=utf-8"):
        self.send_response(code)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

    def _json(self, code, objet):
        corps = json.dumps(objet, ensure_ascii=False).encode("utf-8")
        self._tete(code)
        self.wfile.write(corps)

    def _corps(self):
        n = int(self.headers.get("Content-Length") or 0)
        if n <= 0:
            return {}
        try:
            return json.loads(self.rfile.read(n).decode("utf-8"))
        except Exception:
            return {}

    def do_OPTIONS(self):
        self._tete(204)
        self.wfile.write(b"")

    def do_GET(self):
        u = urlparse(self.path)
        try:
            if u.path == "/api/etat":
                self._json(200, etat_pont())
            elif u.path == "/api/objet":
                q = parse_qs(u.query)
                ident = (q.get("id") or [""])[0]
                self._json(200, objet_pont(ident))
            elif u.path == "/api/vision":
                self._json(200, vision_pont())
            else:
                self._json(404, {"ok": False, "erreur": "route inconnue: %s" % u.path})
        except KeyError as e:
            self._json(404, {"ok": False, "erreur": str(e)})
        except Exception as e:
            self._json(500, {"ok": False, "erreur": str(e)})

    def do_POST(self):
        u = urlparse(self.path)
        d = self._corps()
        try:
            if u.path == "/api/creer":
                self._json(200, creer_pont(d))
            elif u.path == "/api/modifier":
                self._json(200, modifier_pont(d))
            elif u.path == "/api/deplacer":
                self._json(200, deplacer_pont(d))
            else:
                self._json(404, {"ok": False, "erreur": "route inconnue: %s" % u.path})
        except KeyError as e:
            self._json(404, {"ok": False, "erreur": str(e)})
        except ValueError as e:
            self._json(400, {"ok": False, "erreur": str(e)})
        except Exception as e:
            self._json(500, {"ok": False, "erreur": str(e)})


_directeur = None


def configurer(directeur):
    """Injecte un Director (tests, ou director custom). Rien d'autre ne change."""
    global _directeur
    _directeur = directeur


def _director() -> Director:
    if _directeur is not None:
        return _directeur
    if not hasattr(PontHandler, "serveur_") or PontHandler.serveur_ is None:
        PontHandler.serveur_ = Director()
    return PontHandler.serveur_


def etat_pont() -> dict:
    d = _director()
    scene = d.scene
    reg = d.registre
    objets = []
    for o in sorted(scene.tout(), key=lambda x: x["id"]):
        e = reg.donnees["assets"].get(o["id"])
        objets.append({
            "id": o["id"],
            "slug": e["slug"] if e else "?",
            "version": o.get("assetVersion", 1),
            "activeVersion": e["activeVersion"] if e else o.get("assetVersion"),
            "assetFile": o.get("assetFile"),
            "lieu": o.get("lieu"),
            "position": o.get("position"),
            "rotationY": o.get("rotationY"),
            "echelle": o.get("echelle"),
        })
    return {
        "ok": True,
        "scene": {"objets": objets},
        "spec_source": _director()._spec_source(),
        "vision": vision_pont(),
    }


def objet_pont(ident: str) -> dict:
    d = _director()
    e = d.registre.obtenir(ident)
    obj = d.scene.obtenir(ident)
    return {
        "ok": True,
        "id": ident,
        "slug": e["slug"],
        "activeVersion": e["activeVersion"],
        "versions": e["versions"],
        "meta": e["meta"],
        "objet_en_scene": {
            "lieu": obj.get("lieu"),
            "position": obj.get("position"),
            "rotationY": obj.get("rotationY"),
            "echelle": obj.get("echelle"),
            "assetFile": obj.get("assetFile"),
            "assetVersion": obj.get("assetVersion"),
        },
    }


def creer_pont(d: dict) -> dict:
    demande = (d.get("demande") or "").strip()
    if not demande:
        raise ValueError("demande vide")
    image = d.get("imageB64")
    chemin = None
    if image:
        chemin = _ecrire_image_b64(image)
    pos = d.get("pos") or None
    pos_tuple = (pos["x"], pos["z"]) if isinstance(pos, dict) and pos.get("x") is not None else None
    lieu = int(d.get("lieu") or 0)
    with _verrou_blender:
        r = _director().creer(demande, image=chemin, pos=pos_tuple, lieu=lieu)
    return {
        "ok": True,
        "id": r["id"],
        "spec_source": r["spec_source"],
        "image_analysee": bool(r["ref_faits"]),
        "position": r["position"],
        "lieu": lieu,
        "assetVersion": 1,
        "glb": r["glb"],
        "octets": r.get("octets"),
        "triangles": r.get("triangles"),
        "meta": r["spec"].get("meta") or {},
        "ref_faits": r.get("ref_faits"),
    }


def modifier_pont(d: dict) -> dict:
    ident = (d.get("id") or "").strip()
    demande = (d.get("demande") or "").strip()
    if not ident or not demande:
        raise ValueError("id et demande requis")
    with _verrou_blender:
        r = _director().modifier(ident, demande)
    return {"ok": True, **r}


def deplacer_pont(d: dict) -> dict:
    ident = (d.get("id") or "").strip()
    x = float(d.get("x"))
    z = float(d.get("z"))
    if not ident:
        raise ValueError("id requis")
    s = _director().scene
    s.mettre_a_jour(ident, {"position": {"x": round(x, 3), "z": round(z, 3)}})
    return {"ok": True, "id": ident, "position": {"x": round(x, 3), "z": round(z, 3)}}


def vision_pont() -> dict:
    """Rapport honnête de la capacité vision : ce que le pipeline utilise
    RÉELLEMENT aujourd'hui. Un modèle qui ne voit pas ne s'appelle pas vision."""
    analyseur = _director().analyseur
    modele = getattr(analyseur, "modele_vision", None)
    return {
        "ok": True,
        "analyse": "palette_python_pur",
        "vision_reelle": bool(modele),
        "modele": modele,
        "avertissement": ("L'image est analysée par palette de couleurs uniquement "
                          "(pas de vision) : architecture et proportions non mesurées."),
    }


def demarrer(port: int, hote: str = "127.0.0.1") -> ThreadingHTTPServer:
    srv = ThreadingHTTPServer((hote, port), PontHandler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def main() -> int:
    srv = demarrer(PORT)
    print("pont world-builder sur http://127.0.0.1:%d  (CTRL+C pour arrêter)" % PORT)
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        print("\npont arrêté")
    return 0


if __name__ == "__main__":
    sys.exit(main())
