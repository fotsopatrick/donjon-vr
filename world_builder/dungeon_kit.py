# -*- coding: utf-8 -*-
"""dungeon_kit — KIT ARCHITECTURAL PROCÉDURAL RÉUTILISABLE (benchmark 22/08).

Transforme une Scene Specification en vraie architecture intérieure de
fantasy : salle elliptique/circulaire, arène centrale, gradins concentriques,
colonnes de pierre, arcs en pierre, mur percé de portes, braseros chauds en
périphérie, bassin émissif au centre.

PRINCIPE : chaque composant est une fonction paramétrique. Aucun modèle
spécifique à une photo : la Scene Specification pilote les dimensions,
les matériaux et l'éclairage. Le kit s'exécute SOUS Blender (import bpy),
mais parametrer() reste testable sans Blender.
"""
try:
    import bpy
    import bmesh
except ImportError:          # hors Blender (tests python purs)
    bpy = None
    bmesh = None

import math
import random


# ---------------------------------------------------------------------------
# 1. PARAMÈTRES — pure, testable sans Blender
# ---------------------------------------------------------------------------
def parametrer(sc: dict, dims: dict, seed: int = 0) -> dict:
    """Traduit la Scene Specification + dimensions en paramètres de kit.
    Tous les champs ont des valeurs par défaut raisonnables ; la spec
    n'écrase que ce qu'elle décrit réellement."""
    sc = sc or {}
    dims = dims or {"l": 20.0, "p": 16.0, "h": 10.0}
    L = float(dims.get("l", 20.0))
    P = float(dims.get("p", 16.0))
    H = float(dims.get("h", 10.0))
    R = max(L, P) * 0.5

    layout = sc.get("layout", {}) or {}
    centre = sc.get("center", {}) or {}
    per = sc.get("perimeter", {}) or {}
    lum = sc.get("lighting", {}) or {}
    niveau = sc.get("levels") or 0

    shape = (layout.get("shape") or "circular").lower()
    if shape not in ("circular", "elliptical", "rectangular", "square", "irregular"):
        shape = "circular"

    hauteur_mur = max(5.0, min(H, R * 0.75))
    rayon = R
    r_pool = max(1.5, R * 0.20)
    r_col = R * 0.72
    n_col = max(6, min(12, int(round(R / 2.5))))

    centre_enabled = (centre.get("type") == "luminous_area") or bool(per.get("cold_center"))
    couleur_centre = (centre.get("color") or "cyan_blue").lower()
    if "cyan" not in couleur_centre and "bleu" not in couleur_centre:
        couleur_centre = "cyan_blue" if per.get("cold_center") else "warm"

    niveau_steps = niveau or 0
    if not niveau_steps:
        niveau_steps = 3
    niveau_steps = max(2, min(5, int(niveau_steps)))

    return {
        "room": {
            "shape": shape,
            "width": L,
            "depth": P,
            "height": hauteur_mur,
            "rayon": rayon,
            "elliptique": shape == "elliptical",
            "k_elliptique": max(1.0, L / max(P, 0.1)),
        },
        "arena": {
            "enabled": centre_enabled,
            "radius": r_pool,
            "color": couleur_centre,
            "recessed": 0.9,
        },
        "steps": {
            "count": niveau_steps,
            "inner_radius": r_pool,
            "outer_radius": R * 0.55,
            "height": 0.45,
        },
        "columns": {
            "count": n_col,
            "radius": R * 0.035,
            "height": hauteur_mur * 1.12,
            "ring_radius": r_col,
        },
        "arches": {
            "count": n_col,
            "radius": r_col,
            "width": R * 0.028,
            "height": hauteur_mur * 1.12,
        },
        "wall": {
            "radius": R * 1.04,
            "thickness": 0.35,
            "height": hauteur_mur,
        },
        "doorway": {
            "enabled": True,
            "count": 2,
            "width": max(2.5, R * 0.22),
            "height": hauteur_mur * 0.72,
        },
        "materials": {
            "primary": (sc.get("materials", {}) or {}).get("primary", "stone"),
        },
        "lighting": {
            "warm_perimeter": bool(per.get("warm_lights", True)),
            "blue_center": centre_enabled,
            "contrast": (lum.get("warm_cold_contrast") or "unknown").lower(),
        },
        "atmosphere": [str(a) for a in (sc.get("atmosphere") or [])],
        "seed": int(seed),
    }


# ---------------------------------------------------------------------------
# 2. KIT — sous Blender
# ---------------------------------------------------------------------------
class DungeonChamber:
    """Assemble la scène intérieure à partir des paramètres."""

    def __init__(self, scene_spec: dict, dims: dict, seed: int = 0):
        if bpy is None:
            raise RuntimeError("dungeon_kit : Blender (bpy) requis")
        self.param = parametrer(scene_spec or {}, dims, seed)
        self.mats = {}
        self.objets = []
        self.rng = random.Random(int(seed) or 0)
        self.ancre = None            # objet à rendre actif pour le join
        self._construire_materiaux()

    # --- matériaux ---------------------------------------------------------
    def _mat(self, nom, rgba, rough=0.85, metal=0.0, emissive=None, force=0.0):
        m = bpy.data.materials.new(nom)
        m.use_nodes = True
        bsdf = m.node_tree.nodes.get("Principled BSDF")
        bsdf.inputs["Base Color"].default_value = rgba
        bsdf.inputs["Roughness"].default_value = rough
        bsdf.inputs["Metallic"].default_value = metal
        if emissive:
            bsdf.inputs["Emission Color"].default_value = emissive
            bsdf.inputs["Emission Strength"].default_value = force
        m.diffuse_color = rgba
        self.mats[nom] = m
        return m

    def _mat_pierre(self, nom, base, rough=0.9, bruit=0.06):
        """Pierre avec variation procédurale (noise) — lisible comme de la
        pierre, pas comme un gris plat."""
        m = bpy.data.materials.new(nom)
        m.use_nodes = True
        nodes = m.node_tree.nodes
        links = m.node_tree.links
        for n in list(nodes):
            nodes.remove(n)
        out = nodes.new("ShaderNodeOutputMaterial")
        bsdf = nodes.new("ShaderNodeBsdfPrincipled")
        coord = nodes.new("ShaderNodeTexCoord")
        noise = nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 45.0
        ramp = nodes.new("ShaderNodeValToRGB")
        e0 = ramp.color_ramp.elements[0]
        e1 = ramp.color_ramp.elements[1]
        e0.color = (base[0] * 0.70, base[1] * 0.70, base[2] * 0.70, 1)
        e1.color = (min(1, base[0] * 1.15), min(1, base[1] * 1.15),
                    min(1, base[2] * 1.15), 1)
        links.new(coord.outputs["Object"], noise.inputs["Vector"])
        links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
        links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = rough + bruit * 0.3
        links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
        m.diffuse_color = (base[0], base[1], base[2], 1)
        self.mats[nom] = m
        return m

    def _construire_materiaux(self):
        p = self.param
        atmos = " ".join(p["atmosphere"])
        assombrir = 0.08 if "dark" in atmos else 0.0

        pierre = (0.24, 0.23, 0.22)
        if p["materials"]["primary"] == "stone":
            pierre = (0.23, 0.22, 0.21)
        self._mat_pierre("pierre_sombre",
                         (pierre[0] * (1 - assombrir), pierre[1] * (1 - assombrir),
                          pierre[2] * (1 - assombrir)), rough=0.95, bruit=0.08)
        self._mat_pierre("pierre_claire", (0.50, 0.48, 0.46), rough=0.9, bruit=0.05)
        self._mat_pierre("pierre_gradins", (0.40, 0.38, 0.36), rough=0.9, bruit=0.06)

        couleur = p["arena"]["color"]
        if "cyan" in couleur or "bleu" in couleur:
            eau = (0.10, 0.46, 0.58, 1)
            eau_em = (0.15, 0.60, 0.90, 1)
        else:
            eau = (0.88, 0.34, 0.08, 1)
            eau_em = (1.0, 0.52, 0.20, 1)
        self._mat("eau_lumineuse", eau, rough=0.25, metal=0.15,
                  emissive=eau_em, force=3.5)
        self._mat("feu_orange", (0.90, 0.30, 0.08, 1), rough=0.6,
                  emissive=(1.0, 0.52, 0.20, 1), force=4.0)
        self._mat("metal_sombre", (0.13, 0.13, 0.16, 1), rough=0.4, metal=0.85)

    # --- helpers géométrie -------------------------------------------------
    def _ajouter(self, primitive, kwargs, mat, nom):
        getattr(bpy.ops.mesh, "primitive_%s_add" % primitive)(**kwargs)
        o = bpy.context.object
        o.name = nom
        if mat:
            o.data.materials.append(mat)
        self.objets.append(nom)
        return o

    def _anneau(self, r_int, r_ext, z, h, mat, nom):
        """Anneau plein (couronne) : cylindre dont on retire le centre."""
        o = self._ajouter("cylinder", {"vertices": 48, "radius": r_ext,
                                       "depth": h, "location": (0, 0, z)},
                          mat, nom)
        if r_int > 0.001:
            bm = bmesh.new()
            bm.from_mesh(o.data)
            a_del = []
            for v in bm.verts:
                if v.co.x * v.co.x + v.co.y * v.co.y < r_int * r_int - 1e-6:
                    a_del.append(v)
            if a_del:
                bmesh.ops.delete(bm, geom=a_del, context="VERTS")
            bm.to_mesh(o.data)
            bm.free()
        return o

    def _echelle_x(self, o, k):
        if k > 1.001:
            o.scale = (k, 1.0, 1.0)
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    # --- composants --------------------------------------------------------
    def elliptical_room(self):
        p = self.param["room"]
        k = p["k_elliptique"] if p["elliptique"] else 1.0
        sol = self._anneau(0, p["rayon"] * 1.02, 0.28, 0.56,
                           self.mats["pierre_claire"], "sol")
        self._echelle_x(sol, k)
        # assise extérieure (base du monument)
        base = self._anneau(0, p["rayon"] * 1.10, 0.06, 0.35,
                            self.mats["pierre_sombre"], "assise")
        self._echelle_x(base, k)

    def central_arena(self):
        a = self.param["arena"]
        if not a["enabled"]:
            return
        k = self.param["room"]["k_elliptique"] if self.param["room"]["elliptique"] else 1.0
        r = a["radius"]
        # bassin creusé
        basin = self._anneau(0, r, -0.15, a["recessed"] * 0.9,
                             self.mats["pierre_sombre"], "bassin")
        self._echelle_x(basin, k)
        # remplissage émissif (l'eau / l'énergie)
        eau = self._anneau(0, r * 0.96, 0.36, 0.10,
                           self.mats["eau_lumineuse"], "eau_centrale")
        self._echelle_x(eau, k)
        # bord relevé en métal
        bord = self._ajouter("torus", {"major_radius": r, "minor_radius": 0.06,
                                       "location": (0, 0, 0.46)},
                             self.mats["metal_sombre"], "bord_arena")
        self._echelle_x(bord, k)

    def concentric_steps(self):
        s = self.param["steps"]
        k = self.param["room"]["k_elliptique"] if self.param["room"]["elliptique"] else 1.0
        n = s["count"]
        r_int = s["inner_radius"]
        r_ext = s["outer_radius"]
        for i in range(1, n + 1):
            r1 = r_int + (r_ext - r_int) * ((i - 1) / n)
            r2 = r_int + (r_ext - r_int) * (i / n)
            z = s["height"] * i + 0.15
            mat = self.mats["pierre_gradins"] if i % 2 else self.mats["pierre_sombre"]
            marche = self._anneau(r1, r2, z, 0.30, mat, "marche_%d" % i)
            self._echelle_x(marche, k)

    def stone_columns(self):
        c = self.param["columns"]
        k = self.param["room"]["k_elliptique"] if self.param["room"]["elliptique"] else 1.0
        r_col = c["ring_radius"]
        for i in range(c["count"]):
            a = i / c["count"] * math.tau
            x, y = math.cos(a) * r_col, math.sin(a) * r_col
            self._ajouter("cylinder", {"vertices": 16, "radius": c["radius"] * 1.6,
                                       "depth": 0.30, "location": (x, y, 0.15)},
                          self.mats["pierre_claire"], "col_base_%d" % i)
            self._ajouter("cylinder", {"vertices": 16, "radius": c["radius"],
                                       "depth": c["height"], "location": (x, y, 0.3 + c["height"] / 2)},
                          self.mats["pierre_sombre"], "colonne_%d" % i)
            self._ajouter("cylinder", {"vertices": 16, "radius": c["radius"] * 1.4,
                                       "depth": 0.22, "location": (x, y, 0.3 + c["height"] + 0.11)},
                          self.mats["pierre_claire"], "col_cap_%d" % i)

    def stone_arches(self):
        a = self.param["arches"]
        k = self.param["room"]["k_elliptique"] if self.param["room"]["elliptique"] else 1.0
        n = a["count"]
        r_col = a["radius"]
        h_arch = 0.3 + a["height"] + 0.22
        for i in range(n):
            a1 = i / n * math.tau
            a2 = (i + 1) / n * math.tau
            aM = (a1 + a2) / 2
            mx, my = math.cos(aM) * r_col, math.sin(aM) * r_col
            r_arc = r_col * math.sin((a2 - a1) / 2)
            arc = self._ajouter("torus", {"major_radius": r_arc,
                                          "minor_radius": a["width"],
                                          "location": (mx, my, h_arch)},
                                self.mats["pierre_sombre"], "arc_%d" % i)
            axis = __import__("mathutils").Vector((math.cos(aM), math.sin(aM), 0.0))
            q = __import__("mathutils").Vector((0.0, 0.0, 1.0)).rotation_difference(axis)
            arc.rotation_euler = q.to_euler("XYZ")
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
            bm = bmesh.new()
            bm.from_mesh(arc.data)
            for f in list(bm.faces):
                if all(v.co.z < h_arch - 0.001 for v in f.verts):
                    bm.faces.remove(f)
            bm.to_mesh(arc.data)
            bm.free()
            # imposte à la retombée de l'arc
            self._ajouter("cube", {"size": 1,
                                   "location": (math.cos(a1) * r_col, math.sin(a1) * r_col, h_arch - 0.2),
                                   "rotation": (0, 0, aM)},
                          self.mats["pierre_claire"], "imposte_%d" % i)

    def wall_and_doorway(self):
        w = self.param["wall"]
        d = self.param["doorway"]
        k = self.param["room"]["k_elliptique"] if self.param["room"]["elliptique"] else 1.0
        # mur : anneau fermé, percé ensuite de portes (percées AVANT l'étirement
        # elliptique pour que les ouvertures restent aux bons angles)
        mur = self._anneau(w["radius"] - w["thickness"], w["radius"],
                           w["height"] / 2, w["height"],
                           self.mats["pierre_sombre"], "mur_peripherique")
        self.ancre = "mur_peripherique"
        portes = []
        if d["enabled"]:
            larg_half = max(0.6, d["width"] / 2 / w["radius"])
            for j in range(d["count"]):
                ang = (0.5 + j) / d["count"] * math.tau   # entre deux colonnes
                bm = bmesh.new()
                bm.from_mesh(mur.data)
                a_del = []
                for v in bm.verts:
                    da = (math.atan2(v.co.y, v.co.x) - ang + math.pi) % math.tau - math.pi
                    if abs(da) < larg_half and v.co.z < d["height"]:
                        a_del.append(v)
                if a_del:
                    bmesh.ops.delete(bm, geom=a_del, context="VERTS")
                bm.to_mesh(mur.data)
                bm.free()
                portes.append(ang)
        self._echelle_x(mur, k)
        # encadrements de portes (posés au cercle, étirés avec la salle)
        if d["enabled"]:
            for j, ang in enumerate(portes):
                x, y = math.cos(ang) * w["radius"], math.sin(ang) * w["radius"]
                lint = self._ajouter("cube", {"size": 1, "location": (x, y, d["height"] + 0.2),
                                              "rotation": (0, 0, ang)},
                                     self.mats["pierre_claire"], "linteau_porte_%d" % j)
                self._echelle_x(lint, k)
                for signe in (-1, 1):
                    da = signe * larg_half
                    xp, yp = math.cos(ang + da) * w["radius"], math.sin(ang + da) * w["radius"]
                    pd = self._ajouter("cube", {"size": 1, "location": (xp, yp, d["height"] / 2),
                                                "rotation": (0, 0, ang)},
                                       self.mats["pierre_claire"], "piedroit_%d_%d" % (j, signe))
                    self._echelle_x(pd, k)

    def warm_perimeter_lights(self):
        l = self.param["lighting"]
        if not l["warm_perimeter"]:
            return
        w = self.param["wall"]
        n = self.param["columns"]["count"]
        r = w["radius"] - 0.35
        z = w["height"] + 0.25
        for i in range(n):
            a = i / n * math.tau
            x, y = math.cos(a) * r, math.sin(a) * r
            # brasero : pied + vasque + flamme
            self._ajouter("cylinder", {"vertices": 8, "radius": 0.18, "depth": 0.5,
                                       "location": (x, y, z - 0.25)},
                          self.mats["metal_sombre"], "pied_brasero_%d" % i)
            self._ajouter("cylinder", {"vertices": 8, "radius": 0.42, "depth": 0.12,
                                       "location": (x, y, z + 0.06)},
                          self.mats["metal_sombre"], "vasque_%d" % i)
            self._ajouter("uv_sphere", {"segments": 10, "ring_count": 5,
                                        "radius": 0.22, "location": (x, y, z + 0.3)},
                          self.mats["feu_orange"], "flamme_%d" % i)

    def emissive_center(self):
        """Couronne émissive autour de l'arène — souligne le point focal."""
        a = self.param["arena"]
        if not a["enabled"]:
            return
        k = self.param["room"]["k_elliptique"] if self.param["room"]["elliptique"] else 1.0
        couronne = self._anneau(a["radius"] * 1.02, a["radius"] * 1.12, 0.05, 0.06,
                                self.mats["eau_lumineuse"], "couronne_emissive")
        self._echelle_x(couronne, k)

    # --- orchestration -----------------------------------------------------
    def build(self) -> dict:
        self.elliptical_room()
        self.central_arena()
        self.concentric_steps()
        self.stone_columns()
        self.stone_arches()
        self.wall_and_doorway()
        self.warm_perimeter_lights()
        self.emissive_center()
        return {
            "ancre": self.ancre,
            "objet": self.ancre,
            "hauteur": self.param["room"]["height"],
            "rayon": self.param["room"]["rayon"],
            "elliptique": self.param["room"]["elliptique"],
        }
