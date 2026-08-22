# -*- coding: utf-8 -*-
"""reference_analyzer — extraire des FAITS d'une image de référence.

Contrat (point 4 du P0) : analyser(image) -> ReferenceFacts. Le P0 n'a pas de
modèle vision : on implémente le chemin technique disponible — la PALETTE réelle
de l'image, décodée en Python pur par design/design_lib.py (déjà dans le projet).

Règle absolue : on ne SIMULE jamais une analyse qui n'a pas eu lieu.
Tout ce qui est une interprétation (matériau probable, style probable) est
étiqueté « déduction » et peut rester vide. L'interface est remplaçable
pour brancher un modèle vision/multimodal plus tard sans toucher au reste.
"""
from __future__ import annotations

import os
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
DESIGN = os.path.dirname(ICI) + os.sep + "design"
if DESIGN not in sys.path:
    sys.path.insert(0, DESIGN)
from design_lib import decode_png, profil, famille, lum  # noqa: E402


class ErreurReference(Exception):
    pass


class ReferenceAnalyzer:
    """Interface. Les implémentations remplacent analyser()."""

    def analyser(self, chemin: str) -> dict:
        raise NotImplementedError


class VisionReferenceAnalyzer(ReferenceAnalyzer):
    """Analyse RÉELLE par modèle vision (DeepSeek V4 flash vision).

    On garde la mesure réelle de palette comme base, puis un modèle vision lit
    l'image pour de vrai et rend un VisualProfile. Le profil est une LECTURE,
    toujours étiquetée comme telle ; les déductions restent des interprétations.
    Sans clé : on REFUSE — on ne simule jamais la vision.
    """

    def __init__(self, client=None):
        from .deepseek_client import DeepSeekClient, MODELE_VISION
        self.client = client or DeepSeekClient()
        self.modele_vision = MODELE_VISION
        self.palette = PaletteReferenceAnalyzer()

    def disponible(self) -> bool:
        return self.client.disponible()

    def analyser(self, chemin: str) -> dict:
        if not os.path.exists(chemin):
            raise ErreurReference("fichier de référence absent: %s" % chemin)
        if not self.client.disponible():
            raise ErreurReference(
                "clé DEEPSEEK_API_KEY absente : vision réelle indisponible. "
                "On ne simule pas la vision.")
        try:
            base = self.palette.analyser(chemin)
            palette = {
                "taille": base["taille"],
                "palette_dominante": base["palette_dominante"],
                "luminosite": base["luminosite"],
                "familles": base["familles"],
                "usure_estimee": base["usure_estimee"],
            }
        except ErreurReference as e:
            # JPEG/GIF/WebP : le décodage palette est PNG pur, donc indisponible.
            # La vision RÉELLE, elle, lit l'image — on continue, en le disant.
            palette = {
                "taille": None,
                "palette_dominante": [],
                "luminosite": None,
                "familles": {},
                "usure_estimee": None,
                "avertissement_palette": str(e),
            }
        profil = self.client.visual_profile(chemin)
        return {
            "source": chemin,
            **palette,
            "visual_profile": profil,
            "deductions": self._deductions(profil),
            "analysé_par": self.modele_vision,
            "avertissement": ("Analyse réelle : faits mesurés (palette) + lecture "
                              "par modèle vision (%s). Le profil visuel est une "
                              "lecture, pas une mesure : les proportions sont des "
                              "ratios relatifs et l'incertitude est rapportée."
                              % self.modele_vision),
        }

    @staticmethod
    def _deductions(profil: dict) -> dict:
        """Traduit le VisualProfile scène en déductions étiquetées, sans en
        inventer. Un élément non observé n'est jamais déduit."""
        obs = " ".join(str(x).lower() for x in (profil.get("observed") or []))
        mats = " ".join(str(m).lower() for m in (profil.get("materials_observed") or []))
        lum = profil.get("lighting") or {}
        emis = " ".join(str(x).lower() for x in (lum.get("emissive_elements") or []))
        arch = (profil.get("architecture") or {}).get("columns") or []
        arches = (profil.get("architecture") or {}).get("arches") or []
        stairs = (profil.get("spatial_composition") or {}).get("stairs") or []

        ded = {}
        if "sombre" in mats or "sombre" in obs or "dark" in obs:
            ded["pierre_sombre"] = True
        if "pierre" in mats or "stone" in mats or "pierre" in obs:
            ded["pierre"] = True
        if obs and any(m in obs for m in ("colonnes", "colonne", "colonnade", "colonnad", "columns", "column")) or arch:
            ded["colonnes"] = True
        if obs and ("arc" in obs or "arches" in obs) or arches:
            ded["arches"] = True
        if obs and any(m in obs for m in ("escalier", "escaliers", "gradins", "stairs")):
            ded["gradins"] = True
        if stairs:
            ded["gradins"] = True
        if ("bleu" in emis or "cyan" in emis or "bleu" in obs or "cyan" in obs):
            ded["centre_cyan"] = True
        if "orange" in emis or "orange" in obs:
            ded["feux_orange"] = True
        scene = profil.get("scene") or {}
        if (scene.get("interior_or_exterior") or "").lower() == "interior":
            ded["interieur"] = True
        if profil.get("incertitude") == "forte":
            ded["incertitude_forte"] = True
        return ded


class PaletteReferenceAnalyzer(ReferenceAnalyzer):
    """Analyse réelle par palette de couleurs (PNG). Aucune prétention de
    vision : on rapporte des faits mesurés et des déductions étiquetées."""

    def analyser(self, chemin: str) -> dict:
        if not os.path.exists(chemin):
            raise ErreurReference("fichier de référence absent: %s" % chemin)
        try:
            w, h, ch, buf = decode_png(chemin)
        except AssertionError as e:
            raise ErreurReference("image non lisible (PNG 8 bits requis) : %s" % e)
        except Exception as e:
            raise ErreurReference("décodage PNG impossible : %s" % e)

        pixels = self._echantillon(buf, w, h, ch)
        fr, lum_moy = profil(pixels)
        dominantes = self._dominantes(pixels, 5)
        usure = self._estimer_usure(pixels, lum_moy)
        return {
            "source": chemin,
            "taille": {"largeur": w, "hauteur": h},
            "palette_dominante": dominantes,
            "luminosite": round(lum_moy, 2),
            "familles": {k: round(v, 3) for k, v in fr.items()},
            "usure_estimee": usure,
            "deductions": self._deductions(pixels, lum_moy),
            "analysé_par": "palette_python_pur",
            "avertissement": "Analyse par palette uniquement (pas de vision). "
                             "Architecture et proportions NON mesurées.",
        }

    @staticmethod
    def _echantillon(buf, w, h, ch, pas=3):
        res = []
        for y in range(0, h, pas):
            base = y * w * ch
            for x in range(0, w, pas):
                o = base + x * ch
                res.append((buf[o], buf[o + 1], buf[o + 2]))
        return res

    @staticmethod
    def _dominantes(px, n=5):
        comptes = {}
        for r, g, b in px:
            cle = (r >> 4, g >> 4, b >> 4)
            comptes[cle] = comptes.get(cle, 0) + 1
        top = sorted(comptes, key=comptes.get, reverse=True)[:n]
        return ["#%02x%02x%02x" % (r << 4, g << 4, b << 4) for r, g, b in top]

    @staticmethod
    def _estimer_usure(px, lum_moy):
        pales = 0
        total = len(px) or 1
        for r, g, b in px:
            if r > 180 and g > 170 and b > 150 and lum(r, g, b) > 180:
                pales += 1
        return round(min(1.0, pales / total * 3.0), 2)

    @staticmethod
    def _deductions(px, lum_moy):
        fr = {}
        for r, g, b in px:
            f = famille(r, g, b)
            fr[f] = fr.get(f, 0) + 1
        total = len(px) or 1
        parts = {k: v / total for k, v in fr.items()}
        bruns = parts.get("ambre", 0)
        verts = parts.get("vert", 0)
        ded = {}
        if bruns > 0.18:
            ded["bois_sombre"] = True
        if verts > 0.12:
            ded["vegetation"] = True
        if lum_moy < 0.3:
            ded["style"] = "rustic"
        return ded
