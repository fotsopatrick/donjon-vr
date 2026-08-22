# -*- coding: utf-8 -*-
"""scene_store — les objets placés dans le monde.

C'est la scène persistée que le runtime Three.js lit au démarrage :
monde/scene.json. Chaque objet porte son ID logique, le GLB actif (version),
sa position/rotation/échelle et le niveau (lieu) où il apparaît.

L'orchestrateur Python écrit ce fichier ; world-builder.js le charge.
"""
from __future__ import annotations

import json
import os

CHEMIN = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "monde", "scene.json")


class SceneStore:
    def __init__(self, chemin: str = CHEMIN):
        self.chemin = chemin
        self.donnees = self._lire()

    def _lire(self) -> dict:
        if os.path.exists(self.chemin):
            try:
                with open(self.chemin, encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {"version": 1, "objets": []}
        return {"version": 1, "objets": []}

    def _ecrire(self) -> None:
        os.makedirs(os.path.dirname(self.chemin), exist_ok=True)
        with open(self.chemin, "w", encoding="utf-8") as f:
            json.dump(self.donnees, f, ensure_ascii=False, indent=2)

    def ajouter(self, objet: dict) -> None:
        self.donnees["objets"].append(objet)
        self._ecrire()

    def obtenir(self, asset_id: str) -> dict:
        for o in self.donnees["objets"]:
            if o["id"] == asset_id:
                return o
        raise KeyError("objet absent de la scène: %s" % asset_id)

    def mettre_a_jour(self, asset_id: str, champs: dict) -> dict:
        o = self.obtenir(asset_id)
        o.update(champs)
        self._ecrire()
        return o

    def tout(self) -> list:
        return list(self.donnees["objets"])
