# -*- coding: utf-8 -*-
"""scene_spec — la spécification structurée d'un asset 3D.

C'est le contrat entre l'intention (texte libre) et l'outil Blender :
rien ne part vers Blender sans être passé par ce format. La structure
découle du plan P0 « AI World Builder » : create_asset / modify_asset,
type d'objet, style, matériaux, traits, dimensions, placement.

Blender ne voit JAMAIS la demande en clair : il ne voit que ce dictionnaire.
"""
from __future__ import annotations

import ast

TYPES_SUPPORTES = ("building",)
MATERIAUX_CONNUS = ("dark_wood", "wood", "aged_stone", "stone", "plaster",
                    "moss", "thatch")
TRAITS_CONNUS = ("steep_roof", "weathered_wood", "moss", "chimney",
                 "porch", "balcony", "dome")

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


def _decouper_liste(v: str) -> list:
    """Le modèle spec renvoie parfois un tuple en chaîne : "('stone','glass')".
    On le découpe ; sinon on garde la chaîne telle quelle."""
    s = v.strip()
    if s[:1] in "([{":
        try:
            p = ast.literal_eval(s)
            if isinstance(p, (list, tuple)):
                return [str(x) for x in p if str(x).strip()]
        except (ValueError, SyntaxError):
            pass
    return [s] if s else []


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
            spec[k] = _decouper_liste(v)
        elif isinstance(v, (list, tuple)):
            spec[k] = [m for m in v if m]
        else:
            raise ErreurSpec("%s doit être une liste" % k)
        spec[k] = [str(m).strip() for m in spec[k] if str(m).strip()]
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
        "scene": dict(spec.get("scene") or {}),
    }


def composer_scene(profil: dict) -> dict:
    """Scene Specification DÉTERMINISTE depuis le VisualProfile (benchmark 22/08).

    Seuls les éléments OBSERVED entrent dans la spec — aucune hallucination de
    fonction, aucune inférence passée pour de l'observation. C'est LA source de
    vérité que Blender utilise pour construire la scène intérieure."""
    profil = profil or {}
    scene = profil.get("scene") or {}
    comp = profil.get("spatial_composition") or {}
    arch = profil.get("architecture") or {}
    lum = profil.get("lighting") or {}
    mats = " ".join(str(m).lower() for m in (profil.get("materials_observed") or []))
    obs = " ".join(str(x).lower() for x in (profil.get("observed") or []))
    emis = " ".join(str(x).lower() for x in (lum.get("emissive_elements") or []))
    atmos = [str(a) for a in (profil.get("atmosphere") or [])]

    shape = (scene.get("dominant_shape") or "unknown").lower()
    if shape not in ("circular", "elliptical", "rectangular", "square", "irregular"):
        shape = "unknown"
    sym = (scene.get("symmetry") or "unknown").lower()
    if sym not in ("radial", "bilateral", "asymmetric"):
        sym = "unknown"

    centre_type, centre_couleur = "unknown", "unknown"
    cibles = list(comp.get("center") or [])
    for o in (profil.get("objects") or []):
        if isinstance(o, dict):
            cibles.append(o)
    # L'élément central lumineux vit souvent dans lighting (émissif/dominant)
    # et dans la palette, pas dans la liste "center". On balaie aussi là.
    lum_texte = " ".join([
        str(lum.get("dominant", "")),
        " ".join(str(x) for x in (lum.get("secondary") or [])),
        " ".join(str(x) for x in (lum.get("emissive_elements") or [])),
    ]).lower()
    palette_texte = " ".join(str(v) for v in (profil.get("color_palette") or {}).values()).lower()
    balayage = [cibles, [lum_texte], [palette_texte]]
    tout_texte = " ".join(
        " ".join(str(x).lower() for x in (c.values() if isinstance(c, dict) else [c]))
        for sous in balayage for c in sous)
    # 1) PREUVE BLEUE d'abord : si un élément bleu/cyan est observé (émissif,
    #    lumière dominante, palette, sol...), le centre est cyan. Sans quoi un
    #    « éclairé » banal (contient "clair") figerait le centre en warm avant
    #    qu'on voie le bleu (leçon d'audit salledonjon).
    if "cyan" in tout_texte or "bleu" in tout_texte:
        centre_type, centre_couleur = "luminous_area", "cyan_blue"
    else:
        # 2) centre lumineux générique (sans "clair"/"éclairé", trop banal)
        for c in [x for sous in balayage for x in sous]:
            s = " ".join(str(x).lower() for x in (c.values() if isinstance(c, dict) else [c]))
            if any(m in s for m in ("lumineux", "lueur", "luisant", "brillant",
                                    "glowing", "luminous")):
                centre_type = "luminous_area"
                centre_couleur = "warm"
                break

    colonnes = bool(arch.get("columns")) or "colonne" in obs
    arches = bool(arch.get("arches")) or "arches" in obs or "arc" in obs
    gradins = bool(comp.get("stairs")) or "gradins" in obs or "escalier" in obs
    murs = bool(arch.get("walls"))
    feux_orange = "orange" in emis or "orange" in obs or "orange" in lum_texte or "orange" in palette_texte
    centre_cyan = ("cyan" in emis or "cyan" in obs or "bleu" in emis or "bleu" in obs
                   or "cyan" in lum_texte or "bleu" in lum_texte)

    primaire = "unknown"
    if "pierre sombre" in mats or "pierre_sombre" in mats or "dark stone" in mats:
        primaire = "dark_stone"
    elif "pierre" in mats or "stone" in mats:
        primaire = "stone"
    elif "bois" in mats or "wood" in mats:
        primaire = "wood"
    elif "metal" in mats or "métal" in mats:
        primaire = "metal"

    try:
        niveaux = int(scene.get("levels") or 0)
    except (TypeError, ValueError):
        niveaux = 0

    return {
        "layout": {"shape": shape, "symmetry": sym,
                   "focal_point": "center" if centre_type != "unknown" else "unknown"},
        "center": {"type": centre_type, "color": centre_couleur},
        "perimeter": {
            "stairs": gradins,
            "columns": colonnes,
            "arches": arches,
            "walls": murs,
            "warm_lights": feux_orange,
            "cold_center": centre_cyan,
        },
        "levels": niveaux,
        "materials": {"primary": primaire},
        "lighting": {
            "warm_cold_contrast": (lum.get("warm_cold_contrast") or "unknown").lower(),
            "warm_orange": feux_orange,
            "cold_blue_center": centre_cyan,
        },
        "atmosphere": atmos[:6],
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
