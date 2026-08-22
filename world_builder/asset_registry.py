# -*- coding: utf-8 -*-
"""asset_registry — l'identité des assets générés.

Un asset a un ID LOGIQUE stable (building_042) et des VERSIONS physiques
(maison-nordique_v1.glb, _v2.glb…). L'objet placé dans le monde garde son ID
quand la version change ; l'ancienne version n'est jamais supprimée.

Le registre est un JSON local (world-builder/registre.json). Rien ici ne
part sur le réseau.
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime

CHEMIN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "registre.json")


def _horodatage() -> str:
    return datetime.now().isoformat(timespec="seconds")


class Registre:
    def __init__(self, chemin: str = CHEMIN):
        self.chemin = chemin
        self.donnees = self._lire()

    def _lire(self) -> dict:
        if os.path.exists(self.chemin):
            try:
                with open(self.chemin, encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {"assets": {}}
        return {"assets": {}}

    def _ecrire(self) -> None:
        os.makedirs(os.path.dirname(self.chemin), exist_ok=True)
        with open(self.chemin, "w", encoding="utf-8") as f:
            json.dump(self.donnees, f, ensure_ascii=False, indent=2)

    def prochain_id(self, prefixe: str) -> str:
        """construit le prochain ID libre : building_042."""
        n = 1
        while True:
            c = "%s_%03d" % (prefixe, n)
            if c not in self.donnees["assets"]:
                return c
            n += 1

    def creer(self, asset_id: str, spec: dict, fichier: str) -> dict:
        entree = {
            "id": asset_id,
            "slug": spec["slug"],
            "type": spec["type"],
            "versions": [{"version": 1, "file": fichier}],
            "activeVersion": 1,
            "meta": {
                "style": spec.get("style", "generic"),
                "materials": spec.get("materials", []),
                "features": spec.get("features", []),
                "dimensions": spec.get("dimensions", {}),
                "toit": spec.get("toit", {}),
                "variation": spec.get("variation", {}),
            },
            "creeLe": _horodatage(),
            "modifieLe": _horodatage(),
        }
        self.donnees["assets"][asset_id] = entree
        self._ecrire()
        return entree

    def nouvelle_version(self, asset_id: str, spec: dict, fichier: str) -> dict:
        entree = self.donnees["assets"].get(asset_id)
        if not entree:
            raise KeyError("asset inconnu: %s" % asset_id)
        num = entree["activeVersion"] + 1
        entree["versions"].append({"version": num, "file": fichier})
        entree["activeVersion"] = num
        entree["meta"] = {
            "style": spec.get("style", entree["meta"].get("style", "generic")),
            "materials": spec.get("materials", entree["meta"].get("materials", [])),
            "features": spec.get("features", entree["meta"].get("features", [])),
            "dimensions": spec.get("dimensions", entree["meta"].get("dimensions", {})),
            "toit": spec.get("toit", entree["meta"].get("toit", {})),
            "variation": spec.get("variation", entree["meta"].get("variation", {})),
        }
        entree["modifieLe"] = _horodatage()
        self._ecrire()
        return entree

    def obtenir(self, asset_id: str) -> dict:
        entree = self.donnees["assets"].get(asset_id)
        if not entree:
            raise KeyError("asset inconnu: %s" % asset_id)
        return entree

    def fichier_actif(self, asset_id: str) -> str:
        e = self.obtenir(asset_id)
        for v in e["versions"]:
            if v["version"] == e["activeVersion"]:
                return v["file"]
        raise KeyError("version actuelle introuvable pour %s" % asset_id)

    def tout(self) -> dict:
        return dict(self.donnees["assets"])
