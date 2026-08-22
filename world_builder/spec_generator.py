# -*- coding: utf-8 -*-
"""spec_generator — de l'intention vers la spec structurée.

Deux chemins, un seul contrat :
  1. DeepSeek (si une clé DEEPSEEK_API_KEY est posée) — contexte minimal,
     voir deepseek_client.py. On ne lui transmet JAMAIS le projet.
  2. Règles locales (sinon) — une lecture par mots-clés de la demande.
     Ce n'est PAS une simulation de DeepSeek : c'est le chemin déterministe
     qui fait tourner le P0 sans clé, et le rapport le dit.

Les règles locales ne devinent pas au-delà de ce qu'elles lisent : tout ce
qui n'est pas reconnu reste à sa valeur par défaut et est documenté.
"""
from __future__ import annotations

from .scene_spec import valider, spec_vide

STYLES = {
    "nordique": "nordic", "nordic": "nordic", "scandinave": "nordic",
    "medieval": "medieval", "médiéval": "medieval", "rustique": "rustic",
    "japonais": "japonais", "tropical": "tropical",
}
MATS = {
    "bois sombre": "dark_wood", "bois foncé": "dark_wood", "bois fonce": "dark_wood",
    "dark wood": "dark_wood", "chêne": "dark_wood", "chene": "dark_wood",
    "bois": "wood", "wood": "wood", "pierre vieillie": "aged_stone",
    "vieille pierre": "aged_stone", "pierre": "stone", "stone": "stone",
    "crépi": "plaster", "crepi": "plaster", "plâtre": "plaster", "platre": "plaster",
    "chaume": "thatch", "thatch": "thatch", "mousse": "moss",
}
FEATS = {
    "toit pentu": "steep_roof", "toit en pente": "steep_roof",
    "bois vieilli": "weathered_wood", "bois usé": "weathered_wood", "usé": "weathered_wood",
    "moussu": "moss", "mousse": "moss", "cheminée": "chimney", "cheminee": "chimney",
    "porche": "porch", "balcon": "balcony", "véranda": "balcony", "veranda": "balcony",
}


def _contient(demande: str, *mots: str) -> bool:
    t = demande.lower()
    return any(m in t for m in mots)


def _appliquer_regles(spec: dict, t: str, ref_faits: dict | None) -> dict:
    for mot, style in STYLES.items():
        if mot in t and spec.get("style", "generic") == "generic":
            spec["style"] = style
    if _contient(t, "maison", "bâtiment", "batiment", "maisonnette", "chalet", "cabanon"):
        spec["slug"] = "maison"
    elif _contient(t, "grange", "étable"):
        spec["slug"] = "grange"
    elif _contient(t, "tour"):
        spec["slug"] = "tour"

    for mot, mat in MATS.items():
        if mot in t and mat not in spec["materials"]:
            if mat == "wood" and "dark_wood" in spec["materials"]:
                continue
            spec["materials"].append(mat)
    for mot, feat in FEATS.items():
        if mot in t and feat not in spec["features"]:
            spec["features"].append(feat)

    var = spec["variation"]
    if _contient(t, "vieillis", "vieilli", "vieux", "usé", "use", "patine"):
        var["weathered"] = max(var["weathered"], 0.7)
    if _contient(t, "mousse", "moussu"):
        var["moss"] = max(var["moss"], 0.6)
    if _contient(t, "sombre", "foncé", "fonce", "dark"):
        spec["materials"] = [m for m in spec["materials"] if m != "wood"]
        if "dark_wood" not in spec["materials"]:
            spec["materials"].insert(0, "dark_wood")

    toit = spec["toit"]
    if _contient(t, "toit pentu", "toit en pente", "pente forte"):
        toit["type"], toit["pente"] = "pentu", "forte"
    elif _contient(t, "toit plat", "toit-terrasse"):
        toit["type"], toit["pente"] = "plat", "nulle"
    elif _contient(t, "toit"):
        toit["type"], toit["pente"] = "pentu", "moyenne"
    if _contient(t, "toit rouge"):
        toit["couleur"] = "rouge"
    elif _contient(t, "toit gris"):
        toit["couleur"] = "gris"
    elif _contient(t, "toit de chaume", "toit en chaume"):
        toit["couleur"] = "chaume"

    dims = spec["dimensions"]
    if _contient(t, "petite", "petit") and not ref_faits:
        dims = {**dims, "l": min(dims["l"], 3.0), "p": min(dims["p"], 2.4), "h": min(dims["h"], 2.6)}
    elif _contient(t, "grande", "grand") and not ref_faits:
        dims = {**dims, "l": max(dims["l"], 5.5), "p": max(dims["p"], 4.2), "h": max(dims["h"], 4.0)}
    spec["dimensions"] = dims

    if ref_faits:
        ded = ref_faits.get("deductions", {})
        if ded.get("bois_sombre") and "dark_wood" not in spec["materials"]:
            spec["materials"].insert(0, "dark_wood")
        if ded.get("pierre") and "stone" not in spec["materials"]:
            spec["materials"].append("stone")
        if ded.get("style") and spec["style"] == "generic":
            spec["style"] = ded["style"]
        spec["variation"]["weathered"] = max(
            spec["variation"]["weathered"], ref_faits.get("usure_estimee", 0.0))
        if ref_faits.get("luminosite", 0.5) < 0.3:
            spec["variation"]["weathered"] = max(spec["variation"]["weathered"], 0.5)

    return spec


def generer_locale(demande: str, ref_faits: dict | None = None, operation: str = "create_asset") -> dict:
    spec = spec_vide()
    spec["operation"] = operation
    spec["slug"] = "maison"
    spec = _appliquer_regles(spec, demande.lower(), ref_faits)
    return valider(spec)


def generer_modification_locale(demande: str, spec_actuelle: dict) -> dict:
    spec = dict(spec_actuelle)
    spec["operation"] = "modify_asset"
    spec["slug"] = spec_actuelle.get("slug", "maison")
    spec = _appliquer_regles(spec, demande.lower(), None)
    return valider(spec)
