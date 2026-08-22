# -*- coding: utf-8 -*-
"""scene_spec — la spécification structurée d'un asset 3D.

C'est le contrat entre l'intention (texte libre) et l'outil Blender :
rien ne part vers Blender sans être passé par ce format. La structure
découle du plan P0 « AI World Builder » : create_asset / modify_asset,
type d'objet, style, matériaux, traits, dimensions, placement.

Blender ne voit JAMAIS la demande en clair : il ne voit que ce dictionnaire.
"""
from __future__ import annotations

TYPES_SUPPORTES = ("building",)
MATERIAUX_CONNUS = ("dark_wood", "wood", "aged_stone", "stone", "plaster",
                    "moss", "thatch")
TRAITS_CONNUS = ("steep_roof", "weathered_wood", "moss", "chimney",
                 "porch", "balcony")


class ErreurSpec(Exception):
    """La spécification est invalide : on ne lance rien."""


def spec_vide() -> dict:
    return {
        "operation": "create_asset",
        "type": "building",
        "slug": "",
        "style": "generic",
        "materials": [],
        "features": [],
        "dimensions": {"l": 4.0, "p": 3.0, "h": 3.2},
        "toit": {"type": "pentu", "pente": "moyenne"},
        "variation": {"seed": 0, "weathered": 0.0, "moss": 0.0},
    }


def valider(spec: dict) -> dict:
    """Contrôle qu'une spec est exploitable, normalise les valeurs."""
    if not isinstance(spec, dict):
        raise ErreurSpec("spec doit être un objet")
    if spec.get("operation") not in ("create_asset", "modify_asset"):
        raise ErreurSpec("operation inconnue: %r" % spec.get("operation"))
    if spec.get("type") not in TYPES_SUPPORTES:
        raise ErreurSpec("type non supporté pour le P0: %r" % spec.get("type"))
    base = spec_vide()
    for k in ("materials", "features"):
        v = spec.get(k)
        if v is None:
            spec[k] = []
        elif not isinstance(v, list):
            raise ErreurSpec("%s doit être une liste" % k)
        spec[k] = [m for m in v if m]
    dims = dict(base["dimensions"])
    if isinstance(spec.get("dimensions"), dict):
        for k, d in (("l", 4.0), ("p", 3.0), ("h", 3.2)):
            v = spec["dimensions"].get(k)
            if isinstance(v, (int, float)) and 0.5 <= v <= 60:
                dims[k] = round(float(v), 2)
    spec["dimensions"] = dims
    spec.setdefault("slug", spec.get("slug") or "objet")
    spec["slug"] = "".join(c if c.isalnum() else "-" for c in spec["slug"].lower()).strip("-") or "objet"
    if not spec.get("toit"):
        spec["toit"] = base["toit"]
    var = spec.get("variation") or {}
    spec["variation"] = {
        "seed": int(var.get("seed", 0) or 0),
        "weathered": round(min(max(float(var.get("weathered", 0) or 0), 0), 1), 2),
        "moss": round(min(max(float(var.get("moss", 0) or 0), 0), 1), 2),
    }
    return spec


def est_geometrique(demande: str) -> bool:
    """La demande touche-t-elle la géométrie/matériau (Blender) ou seulement
    la transformation (Three.js) ? C'est le cœur du point 9 du P0.

    Un déplacement ou une mise à l'échelle seuls ne relancent PAS Blender.
    Ajouter/retirer un élément ou changer une matière relance Blender.
    """
    geo = ("ajoute", "ajoute", "ajout", "retire", "enleve", "change",
           "remplace", "vieillis", "viellis", "vieux", "mousse", "moisi",
           "peint", "peins", "bois", "pierre", "toit", "porte", "fenetre",
           "fenêtre", "balcon", "veranda", "cheminee", "toiture", "couleur")
    trans = ("deplace", "déplace", "avance", "recules", "recule", "gauche",
             "droite", "nord", "sud", "est", "ouest", "plus loin", "vers",
             "tourne", "pivote", "oriente", "agrandis", "agrandit", "petit",
             "grand", "reduis", "réduis", "taille", "echelle", "échelle",
             "ecart", "rapproche", "eloigne", "éloigne")
    t = demande.lower().strip(" .!?")
    if any(m in t for m in geo):
        return True
    if any(m in t for m in trans):
        return False
    return True
