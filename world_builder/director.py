# -*- coding: utf-8 -*-
"""director — l'orchestrateur central du P0 (point 10).

transforme une demande en opérations spécialisées :
  parse → (analyse de référence) → spec → Blender → GLB → registre → scène.

Décision clé (point 9) : est_geometrique() sépare ce qui relance Blender
(géométrie/matériau → nouvelle version GLB) de ce qui est une simple
transformation Three.js (position/échelle/rotation → scène seule, pas de
nouvelle version). L'opération minimale gagne.
"""
from __future__ import annotations

import os
import re

from .asset_registry import Registre
from . import blender_controller
from .deepseek_client import DeepSeekClient
from .reference_analyzer import PaletteReferenceAnalyzer, VisionReferenceAnalyzer, ErreurReference
from .scene_spec import est_geometrique, meta_spec, STYLE_PROFILE_DEFAUT
from .scene_store import SceneStore
from .spec_generator import generer_locale, generer_modification_locale


def _analyseur_par_defaut():
    """Palette par défaut (chemin historique, zéro dépendance). Si WB_VISION=1,
    on passe à la vision RÉELLE — et seulement si elle est disponible : sans
    clé on REFUSE (un pipeline qui prétend « voir » sans modèle vision ment)."""
    if os.environ.get("WB_VISION", "").strip().lower() in ("1", "true", "oui", "yes"):
        a = VisionReferenceAnalyzer()
        if not a.disponible():
            raise ErreurReference(
                "WB_VISION=1 mais aucune clé DEEPSEEK_API_KEY : la vision réelle "
                "est impossible. Déposez la clé dans l'environnement ou retirez WB_VISION.")
        return a
    return PaletteReferenceAnalyzer()


def _spec_profil_defaut() -> dict:
    return dict(STYLE_PROFILE_DEFAUT)

PROJET = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSITION_PAR_DEFAUT = {"x": 0.0, "z": 4.0}


def relatif(chemin_absolu: str) -> str:
    return os.path.relpath(chemin_absolu, PROJET)


def _position_par_defaut(pos: tuple | None) -> dict:
    if not pos:
        return dict(POSITION_PAR_DEFAUT)
    return {"x": float(pos[0]), "z": float(pos[1])}


def _numero(asset_id: str) -> int:
    m = re.search(r"(\d+)$", asset_id)
    return int(m.group(1)) if m else 0


def _spec_depuis_entree(entree: dict) -> dict:
    return {
        "operation": "modify_asset",
        "type": entree.get("type", "building"),
        "slug": entree.get("slug", "maison"),
        "style": entree.get("meta", {}).get("style", "generic"),
        "materials": list(entree.get("meta", {}).get("materials", [])),
        "features": list(entree.get("meta", {}).get("features", [])),
        "dimensions": dict(entree.get("meta", {}).get("dimensions", {})),
        "toit": dict(entree.get("meta", {}).get("toit", {"type": "pentu", "pente": "moyenne"})),
        "variation": dict(entree.get("meta", {}).get("variation", {})),
        "style_profile": dict(entree.get("meta", {}).get("style_profile", {})),
    }


def _profil_de_scene(scene: SceneStore, lieu: int) -> dict | None:
    """Règle de cohérence (DA 17) : un nouvel asset dans une scène déjà
    peuplée reprend le Style Profile du premier objet du même lieu, au lieu
    de recommencer l'interprétation artistique à zéro."""
    for o in scene.tout():
        if o.get("lieu") == lieu and o.get("meta", {}).get("style_profile"):
            return o["meta"]["style_profile"]
    return None


def _parse_transformations(demande: str) -> dict:
    """Extrait les transformations Three.js d'une demande. Rien d'autre ici
    ne touche à la scène ; la géométrie passe par Blender."""
    t = demande.lower()
    trans = {}
    m = re.search(r"(\d+)\s*(?:%|pour\s*cent)", t)
    if m and re.search(r"agrandis|agrandit|agrandissement|augmente|grand", t):
        trans["echelle"] = 1.0 + int(m.group(1)) / 100.0
    if m and re.search(r"reduis|réduis|réduit|réduit|petit", t):
        trans["echelle"] = 1.0 - int(m.group(1)) / 100.0

    m = re.search(r"(\d+)\s*m(?:è|e)?tres?", t)
    if m:
        d = float(m.group(1))
        deltas = {"x": 0.0, "z": 0.0}
        if re.search(r"nord", t):
            deltas["z"] = -d
        elif re.search(r"sud", t):
            deltas["z"] = d
        elif re.search(r"est(?!\w)", t):
            deltas["x"] = d
        elif re.search(r"ouest", t):
            deltas["x"] = -d
        elif re.search(r"droite", t):
            deltas["x"] = d
        elif re.search(r"gauche", t):
            deltas["x"] = -d
        elif re.search(r"avant|devant", t):
            deltas["z"] = -d
        elif re.search(r"arri[èe]re|derri[èe]re", t):
            deltas["z"] = d
        if any(deltas.values()):
            trans["position"] = deltas

    m = re.search(r"tourne\s+de\s+(\d+)", t)
    if m:
        import math
        trans["rotationY"] = math.radians(int(m.group(1)))

    return trans


class Director:
    def __init__(self, registre=None, scene=None, analyseur=None,
                 client=None, blender=blender_controller.construire):
        self.registre = registre or Registre()
        self.scene = scene or SceneStore()
        self.analyseur = analyseur if analyseur is not None else _analyseur_par_defaut()
        self.client = client or DeepSeekClient()
        self.blender = blender

    def _spec_source(self) -> str:
        return "deepseek" if self.client.disponible() else "regles_locales"

    def creer(self, demande: str, image: str | None = None,
              pos: tuple | None = None, lieu: int = 0) -> dict:
        ref_faits = None
        if image:
            ref_faits = self.analyseur.analyser(image)

        if self.client.disponible():
            spec = self.client.spec_create(demande, ref_faits)
            spec["operation"] = "create_asset"
        else:
            spec = generer_locale(demande, ref_faits, "create_asset")

        profil_scene = _profil_de_scene(self.scene, lieu)
        if profil_scene and spec.get("style_profile") == _spec_profil_defaut():
            spec["style_profile"] = profil_scene

        prefixe = spec["type"] or "objet"
        asset_id = self.registre.prochain_id(prefixe)
        spec["_numero"] = _numero(asset_id)
        spec["_version"] = 1
        if not spec["variation"]["seed"]:
            spec["variation"]["seed"] = spec["_numero"]

        produit = self.blender(spec)
        glb_relatif = relatif(produit["glb"])
        entree = self.registre.creer(asset_id, spec, glb_relatif)

        position = _position_par_defaut(pos)
        objet = {
            "id": asset_id,
            "slug": spec["slug"],
            "assetFile": glb_relatif,
            "assetVersion": 1,
            "lieu": lieu,
            "position": position,
            "rotationY": 0.0,
            "echelle": 1.0,
            "meta": meta_spec(spec),
        }
        self.scene.ajouter(objet)

        return {
            "id": asset_id,
            "spec": spec,
            "spec_source": self._spec_source(),
            "image_analysee": bool(ref_faits),
            "ref_faits": ref_faits,
            "glb": glb_relatif,
            "triangles": produit.get("triangles"),
            "octets": produit.get("octets"),
            "position": position,
            "lieu": lieu,
        }

    def modifier(self, asset_id: str, demande: str) -> dict:
        entree = self.registre.obtenir(asset_id)
        objet = self.scene.obtenir(asset_id)
        geometrique = est_geometrique(demande)
        trans = _parse_transformations(demande)
        rapport = {"id": asset_id, "geometrique": geometrique,
                   "transformation": trans if trans else None}

        if geometrique:
            spec_actuelle = _spec_depuis_entree(entree)
            if self.client.disponible():
                spec_cible = self.client.spec_modify(demande, spec_actuelle)
            else:
                spec_cible = generer_modification_locale(demande, spec_actuelle)
            nouveau_num = entree["activeVersion"] + 1
            spec_cible["_numero"] = _numero(asset_id)
            spec_cible["_version"] = nouveau_num
            produit = self.blender(spec_cible)
            glb_relatif = relatif(produit["glb"])
            self.registre.nouvelle_version(asset_id, spec_cible, glb_relatif)
            self.scene.mettre_a_jour(asset_id, {
                "assetFile": glb_relatif,
                "assetVersion": nouveau_num,
                "meta": meta_spec(spec_cible),
            })
            rapport["spec_source"] = self._spec_source()
            rapport["spec"] = spec_cible
            rapport["glb"] = glb_relatif
            rapport["triangles"] = produit.get("triangles")
            rapport["octets"] = produit.get("octets")
            rapport["nouvelleVersion"] = nouveau_num

        if trans:
            maj = {}
            if "position" in trans:
                p = objet["position"]
                maj["position"] = {
                    "x": round(p["x"] + trans["position"]["x"], 3),
                    "z": round(p["z"] + trans["position"]["z"], 3),
                }
            if "echelle" in trans:
                maj["echelle"] = round(objet["echelle"] * trans["echelle"], 3)
            if "rotationY" in trans:
                maj["rotationY"] = round(objet["rotationY"] + trans["rotationY"], 3)
            if maj:
                self.scene.mettre_a_jour(asset_id, maj)
            rapport["scene"] = self.scene.obtenir(asset_id)

        return rapport
