# -*- coding: utf-8 -*-
"""spec_generator — de l'intention vers la spec structurée.

Deux chemins, un seul contrat :
  1. DeepSeek (si une clé DEEPSEEK_API_KEY est posée) — contexte minimal,
     voir deepseek_client.py. On ne lui transmet JAMAIS le projet.
  2. Règles locales (sinon) — une lecture par mots-clés de la demande.
     Ce n'est PAS une simulation de DeepSeek : c'est le chemin déterministe
     qui fait tourner le P0 sans clé, et le rapport le dit.

Les règles locales ne devinent pas au-delà de ce qu'elles lisent : tout ce
qui n'est pas reconnu reste à sa valeur par défaut et l'est documenté.
"""
from __future__ import annotations

import re

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


def generer_locale(demande: str, ref_faits: dict | None = None, operation: str = "create_asset") -> dict:
    """Construit une spec par mots-clés, sans rien inventer hors de la demande."""
    spec = spec_vide()
    spec["operation"] = operation
    spec["slug"] = "maison"
    t = demande.lower()

    for mot, style in STYLES.items():
        if mot in t:
            spec["style"] = style
            break
    if _contient(t, "maison", "bâtiment", "batiment", "maisonnette", "chalet", "cabanon"):
        spec["slug"] = "maison"
    if _contient(t, "grange", "étable"):
        spec["slug"] = "grange"
    if _contient(t, "tour"):
        spec["slug"] = "tour"

    for mot, mat in MATS.items():
        if mot in t and mat not in spec["materials"]:
            spec["materials"].append(mat)
    for mot, feat in FEATS.items():
        if mot in t and feat not in spec["features"]:
            spec["features"].append(feat)

    var = spec["variation"]
    if _contient(t, "vieillis", "vieilli", "vieux", "usé", "use", "patine"):
        var["weathered"] = 0.7
    if _contient(t, "mousse", "moussu"):
        var["moss"] = 0.6
    if _contient(t, "sombre", "foncé", "fonce", "dark"):
        spec["materials"] = [m for m in spec["materials"] if m != "wood"] or []
        if "dark_wood" not in spec["materials"]:
            spec["materials"].insert(0, "dark_wood")

    toit = spec["toit"]
    if _contient(t, "toit pentu", "toit en pente", "pente forte"):
        toit["type"], toit["pente"] = "pentu", "forte"
    elif _contient(t, "toit plat", "toit-terrasse"):
        toit["type"], toit["pente"] = "plat", "nulle"
    elif _contient(t, "toit"):
        toit["type"], toit["pente"] = "pentu", "moyenne"

    dims = spec["dimensions"]
    if _contient(t, "petite", "petit"):
        dims = {**dims, "l": 3.0, "p": 2.4, "h": 2.6}
    elif _contient(t, "grande", "grand"):
        dims = {**dims, "l": 5.5, "p": 4.2, "h": 4.0}
    spec["dimensions"] = dims

    if _contient(t, "toit rouge"):
        spec["toit"]["couleur"] = "rouge"
    if _contient(t, "toit gris"):
        spec["toit"]["couleur"] = "gris"
    if _contient(t, "toit de chaume", "toit en chaume"):
        spec["toit"]["couleur"] = "chaume"

    if ref_faits:
        ded = ref_faits.get("deductions", {})
        if ded.get("bois_sombre"):
            if "dark_wood" not in spec["materials"]:
                spec["materials"].insert(0, "dark_wood")
        if ded.get("pierre"):
            if "stone" not in spec["materials"]:
                spec["materials"].append("stone")
        if ded.get("style") and spec["style"] == "generic":
            spec["style"] = ded["style"]
        spec["variation"]["weathered"] = max(
            spec["variation"]["weathered"], ref_faits.get("usure_estimee", 0.0))
        if ref_faits.get("luminosite", 0.5) < 0.3:
            spec["variation"]["weathered"] = max(spec["variation"]["weathered"], 0.5)

    return valider(spec)
