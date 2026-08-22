# -*- coding: utf-8 -*-
"""material_lib — BIBLIOTHÈQUE DE MATÉRIAUX ENVIRONMENT (P0).

Tous les matériaux de l'environment design passent par ici, plus jamais créés
ad hoc dans un générateur. Chaque matériau est un preset nommé, réutilisable
par maisons, donjons, murs, colonnes, sols, portes, props — cohérence
artistique garantie.

RÈGLE D'EXPORT glTF (leçon 22/08) : l'exporteur ne peut PAS cuire les nœuds
procéduraux (noise/voronoi) -> baseColorFactor vide -> matériaux BLANCS dans
Three.js. Chaque matériau de surface génère donc une VRAIE texture image
(blocs de pierre, patine) embarquée dans le GLB. Le noise/bump ne sert que
pour la preview Blender.

Le module est utilisable SANS Blender pour la logique pure (presets), mais
la création des matériaux exige bpy.
"""
try:
    import bpy
except ImportError:
    bpy = None

import math
import random


PRESETS = {
    "pierre": {
        "dark_stone": dict(base=(0.24, 0.24, 0.26), rough=0.95, echelle=5.0),
        "stone_floor": dict(base=(0.46, 0.45, 0.44), rough=0.88, echelle=8.0, usure=True),
        "stone_trim": dict(base=(0.60, 0.58, 0.55), rough=0.85, echelle=6.0),
        "pierre_gradins": dict(base=(0.38, 0.37, 0.36), rough=0.90, echelle=6.0),
        # futurs presets (réutilisation)
        "stone_old": dict(base=(0.34, 0.33, 0.32), rough=0.92, echelle=5.0, usure=True),
        "stone_wet": dict(base=(0.26, 0.27, 0.30), rough=0.55, echelle=5.0),
        "stone_moss": dict(base=(0.28, 0.30, 0.26), rough=0.95, echelle=5.0),
    },
    "bois": {
        "bois": dict(rgba=(0.20, 0.13, 0.08), rough=0.85),
        "old_wood": dict(rgba=(0.22, 0.14, 0.09), rough=0.92),
        "wet_wood": dict(rgba=(0.14, 0.09, 0.06), rough=0.45),
        "dark_wood": dict(rgba=(0.16, 0.09, 0.05), rough=0.90),
    },
    "metal": {
        "metal": dict(base=(0.15, 0.16, 0.19), rough=0.35),
        "metal_bleu": dict(base=(0.12, 0.16, 0.24), rough=0.30),
        "metal_rusted": dict(base=(0.22, 0.14, 0.10), rough=0.70),
        "old_metal": dict(base=(0.18, 0.18, 0.20), rough=0.55),
    },
    "eau": {
        "central_water": dict(base=(0.08, 0.40, 0.52), emissive=(0.20, 0.65, 0.95),
                              force=3.2, ripple=0.10),
        "dark_water": dict(base=(0.05, 0.14, 0.20), emissive=(0.05, 0.25, 0.40),
                           force=0.6, ripple=0.08),
    },
    "energie": {
        "magical_cyan": dict(base=(0.10, 0.45, 0.55), emissive=(0.25, 0.70, 1.0),
                             force=4.5, ripple=0.12),
        "feu_orange": dict(rgba=(1.0, 0.45, 0.12), rough=0.6,
                           emissive=(1.0, 0.45, 0.15), force=4.5),
        "feu_sol": dict(rgba=(0.60, 0.32, 0.10), rough=0.8,
                        emissive=(0.85, 0.40, 0.14), force=1.2),
    },
    "divers": {
        "dirt": dict(rgba=(0.28, 0.22, 0.16), rough=1.0),
        "cloth": dict(rgba=(0.30, 0.20, 0.15), rough=0.95),
    },
}


class MaterialLibrary:
    """Fabrique de matériaux nommés, réutilisables, exportables glTF."""

    def __init__(self, seed: int = 0, sombre: float = 0.0):
        self.seed = int(seed)
        self.sombre = float(sombre)
        self.mats = {}

    # ---------------------- moteur (Blender) ----------------------
    def _plat(self, nom, rgba, rough=0.85, metal=0.0, emissive=None, force=0.0):
        m = bpy.data.materials.new(nom)
        m.use_nodes = True
        bsdf = m.node_tree.nodes.get("Principled BSDF")
        bsdf.inputs["Base Color"].default_value = (rgba[0], rgba[1], rgba[2], 1)
        bsdf.inputs["Roughness"].default_value = rough
        bsdf.inputs["Metallic"].default_value = metal
        if emissive:
            bsdf.inputs["Emission Color"].default_value = (emissive[0], emissive[1], emissive[2], 1)
            bsdf.inputs["Emission Strength"].default_value = force
        m.diffuse_color = (rgba[0], rgba[1], rgba[2], 1)
        self.mats[nom] = m
        return m

    def _generer_texture(self, nom, base, mode="stone", taille=512,
                         usure=False, echelle=64):
        """VRAIE texture image (blocs / patine) exportable en glTF."""
        rnd = random.Random(self.seed ^ (hash(nom) & 0xffffff))
        img = bpy.data.images.new(nom + "_tex", width=taille, height=taille)
        px = [0.0] * (taille * taille * 4)
        cs = max(24, echelle)
        nb = taille // cs
        tons = {(bi, bj): rnd.uniform(0.68, 1.30 if mode == "stone" else 1.05)
                for bi in range(nb) for bj in range(nb)}
        for j in range(taille):
            dec = (cs // 2) if (j // cs) % 2 else 0
            bj = j // cs
            mj = j % cs
            for i in range(taille):
                bi = (i + dec) // cs
                mi = (i + dec) % cs
                tone = tons.get((bi, bj), 1.0)
                mortier = 0.38 if (mi < 2 or mj < 2 or mi > cs - 2 or mj > cs - 2) else 0.0
                bruit = rnd.uniform(-0.05, 0.05)
                v = [max(0.0, min(1.0, base[c] * tone * (1.0 - mortier) + bruit))
                     for c in range(3)]
                if usure:
                    d = math.hypot(i - taille / 2, j - taille / 2) / (taille / 2)
                    us = 1.0 - 0.35 * max(0.0, min(1.0, d))
                    v = [max(0.0, min(1.0, x * us)) for x in v]
                o = (j * taille + i) * 4
                px[o] = v[0]; px[o+1] = v[1]; px[o+2] = v[2]; px[o+3] = 1.0
        img.pixels[:] = px
        img.pack()
        return img

    def _pierre(self, nom, base, rough=0.9, echelle=5.0, usure=False):
        """Pierre texturée (exportable) + bump de preview."""
        base = tuple(c * (1 - self.sombre) for c in base)
        m = bpy.data.materials.new(nom)
        m.use_nodes = True
        nodes = m.node_tree.nodes
        links = m.node_tree.links
        for n in list(nodes):
            nodes.remove(n)
        out = nodes.new("ShaderNodeOutputMaterial")
        bsdf = nodes.new("ShaderNodeBsdfPrincipled")
        coord = nodes.new("ShaderNodeTexCoord")
        img = self._generer_texture(nom, base, usure=usure, echelle=int(echelle * 45))
        tex = nodes.new("ShaderNodeTexImage")
        tex.image = img
        links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = rough
        noiseN = nodes.new("ShaderNodeTexNoise")
        noiseN.inputs["Scale"].default_value = 30.0
        bump = nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.35
        links.new(coord.outputs["Object"], noiseN.inputs["Vector"])
        links.new(noiseN.outputs["Fac"], bump.inputs["Height"])
        links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
        links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
        m.diffuse_color = (base[0], base[1], base[2], 1)
        self.mats[nom] = m
        return m

    def _metal(self, nom, base, rough=0.35):
        base = tuple(c * (1 - self.sombre) for c in base)
        m = bpy.data.materials.new(nom)
        m.use_nodes = True
        nodes = m.node_tree.nodes
        links = m.node_tree.links
        for n in list(nodes):
            nodes.remove(n)
        out = nodes.new("ShaderNodeOutputMaterial")
        bsdf = nodes.new("ShaderNodeBsdfPrincipled")
        bsdf.inputs["Metallic"].default_value = 0.85
        bsdf.inputs["Roughness"].default_value = rough
        img = self._generer_texture(nom, base, mode="metal", echelle=110)
        tex = nodes.new("ShaderNodeTexImage")
        tex.image = img
        links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
        m.diffuse_color = (base[0], base[1], base[2], 1)
        self.mats[nom] = m
        return m

    def _eau(self, nom, base, emissive, force, ripple=0.10):
        m = bpy.data.materials.new(nom)
        m.use_nodes = True
        nodes = m.node_tree.nodes
        links = m.node_tree.links
        for n in list(nodes):
            nodes.remove(n)
        out = nodes.new("ShaderNodeOutputMaterial")
        bsdf = nodes.new("ShaderNodeBsdfPrincipled")
        coord = nodes.new("ShaderNodeTexCoord")
        bsdf.inputs["Base Color"].default_value = (base[0], base[1], base[2], 1)
        bsdf.inputs["Roughness"].default_value = 0.15
        bsdf.inputs["Metallic"].default_value = 0.1
        bsdf.inputs["Emission Color"].default_value = (emissive[0], emissive[1], emissive[2], 1)
        bsdf.inputs["Emission Strength"].default_value = force
        if ripple > 0:
            noise = nodes.new("ShaderNodeTexNoise")
            noise.inputs["Scale"].default_value = 28.0
            bump = nodes.new("ShaderNodeBump")
            bump.inputs["Strength"].default_value = ripple
            links.new(coord.outputs["Object"], noise.inputs["Vector"])
            links.new(noise.outputs["Fac"], bump.inputs["Height"])
            links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
        links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
        m.diffuse_color = (base[0], base[1], base[2], 1)
        self.mats[nom] = m
        return m

    # ---------------------- presets ----------------------
    # Les matériaux réellement utilisés par l'environment design. Les autres
    # presets du catalogue sont créés à la demande via get().
    CORE = ["dark_stone", "stone_floor", "stone_trim", "pierre_gradins",
            "metal", "metal_bleu", "bois", "central_water", "feu_orange",
            "feu_sol", "dirt"]

    def construire_presets(self, arena_color: str = "cyan_blue") -> dict:
        """Construit les matériaux nommés CORE du projet (exportables)."""
        cyan = "cyan" in arena_color or "bleu" in arena_color
        for nom in self.CORE:
            self.get(nom, arena_cyan=cyan)
        return self.mats

    def get(self, nom: str, arena_cyan: bool = True) -> object:
        """Renvoie un matériau du catalogue, créé à la demande s'il manque."""
        if nom in self.mats:
            return self.mats[nom]
        p = PRESETS["pierre"].get(nom) or PRESETS["metal"].get(nom) \
            or PRESETS["bois"].get(nom) or PRESETS["eau"].get(nom) \
            or PRESETS["energie"].get(nom) or PRESETS["divers"].get(nom)
        if p is None:
            raise KeyError("matériau inconnu dans material_lib: %s" % nom)
        if nom in PRESETS["pierre"]:
            self._pierre(nom, p["base"], rough=p.get("rough", 0.9),
                         echelle=p.get("echelle", 5.0), usure=p.get("usure", False))
        elif nom in PRESETS["metal"]:
            self._metal(nom, p["base"], rough=p.get("rough", 0.35))
        elif nom in PRESETS["eau"]:
            self._eau(nom, p["base"], p["emissive"], p["force"],
                      ripple=p.get("ripple", 0.1))
        elif nom in PRESETS["energie"]:
            if nom == "magical_cyan":
                self._eau(nom, p["base"], p["emissive"], p["force"],
                          ripple=p.get("ripple", 0.12))
            else:
                self._plat(nom, p["rgba"], rough=p.get("rough", 0.8),
                           emissive=p.get("emissive"), force=p.get("force", 1.0))
        else:
            self._plat(nom, p.get("rgba", (0.3, 0.3, 0.3)), rough=p.get("rough", 0.85))
        return self.mats[nom]
