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

# Direction artistique par défaut : Dark Nordic Cinematic Fantasy (DA 22).
# Persistant : un asset créé dans une scène reprend le profil de la scène
# pour rester dans le même univers visuel (DA 17).
STYLE_PROFILE_DEFAUT = {
    "architecture": "nordic medieval",
    "materials": ["dark_wood", "aged_stone", "moss"],
    "terrain": "rocky wet",
    "vegetation": "dense conifers",
    "lighting": "overcast cold",
    "accent": "warm interior lights",
    "atmosphere": "fog moisture",
}


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
        "style_profile": dict(STYLE_PROFILE_DEFAUT),
    }


def valider(spec: dict) -> dict:
    """Contrôle qu'une spec est exploitable, normalise les valeurs."""
    if not isinstance(spec, dict):
        raise ErreurSpec("spec doit être un objet")
    if spec.get("operation") not in ("create_asset", "modify_asset"):
        raise ErreurSpec("operation inconnue: %r" % spec.get("operation"))
    typ = spec.get("type")
    if isinstance(typ, (list, tuple)) and len(typ) == 1:
        typ = typ[0]
    if typ not in TYPES_SUPPORTES:
        raise ErreurSpec("type non supporté pour le P0: %r" % typ)
    spec["type"] = typ
    base = spec_vide()
    for k in ("materials", "features"):
        v = spec.get(k)
        if v is None:
            spec[k] = []
        elif isinstance(v, str):
            spec[k] = [v]
        elif isinstance(v, (list, tuple)):
            spec[k] = list(v)
        else:
            raise ErreurSpec("%s doit être une liste" % k)
        spec[k] = [m for m in spec[k] if m]
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
    profil = spec.get("style_profile")
    if not isinstance(profil, dict) or not profil:
        profil = STYLE_PROFILE_DEFAUT
    spec["style_profile"] = {k: profil.get(k, STYLE_PROFILE_DEFAUT[k])
                             for k in STYLE_PROFILE_DEFAUT}
    return spec


def meta_spec(spec: dict) -> dict:
    """Le meta d'un asset, dérivé UNIQUEMENT de la spec.

    C'est LA source de vérité commune au registre et à la scène : les deux
    écrivent la sortie de cette fonction, ils ne peuvent donc pas diverger
    (règle P0.5-16). Le registre reste l'autorité pour l'identité et les
    versions ; la scène copie ce meta quand la version active change."""
    return {
        "style": spec.get("style", "generic"),
        "materials": list(spec.get("materials", [])),
        "features": list(spec.get("features", [])),
        "dimensions": dict(spec.get("dimensions", {})),
        "toit": dict(spec.get("toit", {})),
        "variation": dict(spec.get("variation", {})),
        "style_profile": dict(spec.get("style_profile", {})),
    }


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
