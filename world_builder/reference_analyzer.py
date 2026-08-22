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
