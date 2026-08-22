# -*- coding: utf-8 -*-
"""dungeon_kit — KIT D'ENVIRONMENT DESIGN PROCÉDURAL (benchmark 22/08).

Évolution de l'étape "greybox architectural" vers de la vraie architecture
réutilisable : une DungeonChamber est composée de vrais éléments visuels
(murs segmentés et crénelés, colonnes architecturales, arcs à clé de voûte,
gradins à parement, escaliers radiaux, bassin central, niches murales, portes
voûtées, garde-corps, décor, braseros) pilotés par une Scene Specification.

Aucune copie d'une photo : la spec définit le STYLE et la COMPOSITION. La
même DungeonChamber peut produire salle rituelle, salle du trône, arène,
salle de boss, sanctuaire ou crypte — seuls les paramètres changent.

parametrer() est pure et testable sans Blender ; le reste s'exécute sous Blender.
"""
try:
    import bpy
    import bmesh
except ImportError:          # hors Blender (tests python purs)
    bpy = None
    bmesh = None

try:
    from material_lib import MaterialLibrary
except ImportError:
    MaterialLibrary = None

import math
import random


# ---------------------------------------------------------------------------
# 1. PARAMÈTRES — pure, testable sans Blender
# ---------------------------------------------------------------------------
def parametrer(sc: dict, dims: dict, seed: int = 0) -> dict:
    """SceneSpec + dimensions -> paramètres complets du kit.
    Chaque champ a un défaut raisonnable ; la spec n'écrase que ce qu'elle
    décrit réellement."""
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

    hauteur_mur = max(6.0, min(H, R * 0.85))
    r_pool = max(1.5, R * 0.20)
    r_col = R * 0.72
    n_col = max(6, min(14, int(round(R / 2.0))))

    centre_enabled = (centre.get("type") == "luminous_area") or bool(per.get("cold_center"))
    couleur_centre = (centre.get("color") or "cyan_blue").lower()
    if "cyan" not in couleur_centre and "bleu" not in couleur_centre:
        couleur_centre = "cyan_blue" if per.get("cold_center") else "warm"

    niveau_steps = int(niveau) if niveau else 3
    niveau_steps = max(2, min(5, niveau_steps))

    contraste = (lum.get("warm_cold_contrast") or "unknown").lower()

    # intensités : dérivées du contraste (paramétrables ensuite)
    if contraste == "strong":
        centre_int, perimetre_int = 3600.0, 9500.0
    elif contraste == "moderate":
        centre_int, perimetre_int = 2400.0, 5200.0
    else:
        centre_int, perimetre_int = 1700.0, 3600.0

    arena = {
        "enabled": centre_enabled,
        "radius": r_pool,
        "height": 0.9,
        "material": "water",
        "emissive": centre_enabled,
        "color": couleur_centre,
        "recessed": 0.9,
    }
    return {
        "room": {
            "shape": shape,
            "width": L,
            "depth": P,
            "height": hauteur_mur,
            "rayon": R,
            "elliptique": shape == "elliptical",
            "k_elliptique": max(1.0, L / max(P, 0.1)),
        },
        "central_area": arena,
        "arena": arena,
        "steps": {
            "count": niveau_steps,
            "inner_radius": r_pool,
            "outer_radius": R * 0.55,
            "height": 0.45,
            "depth": 0.30,
        },
        "stairs": {
            "enabled": True,
            "count": 4,
            "width": max(2.0, R * 0.16),
            "height": 0.45,
            "steps_per": 2 * niveau_steps,
        },
        "columns": {
            "count": n_col,
            "radius": R * 0.045,
            "height": hauteur_mur * 0.78,
            "ring_radius": r_col,
            "style": "fluted",
        },
        "arches": {
            "enabled": bool(per.get("arches", True)),
            "count": n_col,
            "radius": r_col,
            "width": R * 0.028,
            "height": hauteur_mur * 1.12,
        },
        "walls": {
            "radius": R * 1.04,
            "thickness": 0.35,
            "height": hauteur_mur,
            "segments": n_col,
            "parapet": True,
            "crenel": True,
        },
        "niches": {
            "enabled": True,
            "count": max(2, n_col // 2),
        },
        "doorway": {
            "enabled": True,
            "count": 2,
            "width": max(2.5, R * 0.22),
            "height": hauteur_mur * 0.72,
            "arch": True,
        },
        "railings": {
            "enabled": True,
        },
        "materials": {
            "wall": "dark_stone",
            "floor": "stone_floor",
            "trim": "stone_trim",
            "center": "water",
            "primary": (sc.get("materials", {}) or {}).get("primary", "stone"),
        },
        "lighting": {
            "center_color": (0.30, 0.55, 1.0),
            "perimeter_color": (1.0, 0.50, 0.22),
            "center_intensity": centre_int,
            "perimeter_intensity": perimetre_int,
            "warm_perimeter": bool(per.get("warm_lights", True)),
            "blue_center": centre_enabled,
            "contrast": contraste,
        },
        "atmosphere": [str(a) for a in (sc.get("atmosphere") or [])],
        "camera": sc.get("camera") or "cinematic",
        "seed": int(seed),
    }


# ---------------------------------------------------------------------------
# 2. KIT — sous Blender
# ---------------------------------------------------------------------------
class DungeonChamber:
    """Compose une salle de donjon complète (environment design) à partir
    des paramètres. Chaque composant est une méthode réutilisable."""

    def __init__(self, scene_spec: dict, dims: dict, seed: int = 0):
        if bpy is None:
            raise RuntimeError("dungeon_kit : Blender (bpy) requis")
        self.param = parametrer(scene_spec or {}, dims, seed)
        self.rng = random.Random(int(seed) or 0)
        self.objets = []
        self.ancre = None
        self.bases = []              # bases de kit à supprimer après instancing
        self.angles_colonnes = []      # angles des colonnes (utile aux portes)
        self.angles_portes = []        # angles des portes (pour escaliers/lumières)
        self._construire_materiaux()

    # ============================ MATÉRIAUX ==============================
    # DÉLÉGUÉ à material_lib : bibliothèque nommée, réutilisable (maisons,
    # donjons, props), exportable glTF. Jamais de matériaux ad hoc ici.
    def _construire_materiaux(self):
        atmos = " ".join(self.param["atmosphere"])
        sombre = 0.08 if "dark" in atmos else 0.0
        lib = MaterialLibrary(seed=self.param["seed"], sombre=sombre)
        self.mats = lib.construire_presets(self.param["arena"]["color"])
        self.lib = lib


    # ============================ HELPERS ================================
    def _ajouter(self, primitive, kwargs, mat, nom):
        getattr(bpy.ops.mesh, "primitive_%s_add" % primitive)(**kwargs)
        o = bpy.context.object
        o.name = nom
        if mat:
            o.data.materials.append(mat)
        self.objets.append(nom)
        return o

    def _echelle_x(self, o, k):
        if k > 1.001:
            o.scale = (k, 1.0, 1.0)
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    def _anneau(self, r_int, r_ext, z, h, mat, nom):
        """Couronne pleine : cylindre dont on retire le centre."""
        o = self._ajouter("cylinder", {"vertices": 48, "radius": r_ext,
                                       "depth": h, "location": (0, 0, z)},
                          mat, nom)
        if r_int > 0.001:
            bm = bmesh.new()
            bm.from_mesh(o.data)
            a_del = [v for v in bm.verts
                     if v.co.x * v.co.x + v.co.y * v.co.y < r_int * r_int - 1e-6]
            if a_del:
                bmesh.ops.delete(bm, geom=a_del, context="VERTS")
            bm.to_mesh(o.data)
            bm.free()
        return o

    def _segment_anneau(self, r_int, r_ext, a0, a1, z, h, mat, nom):
        """Segment de mur courbe : anneau réduit à l'angle [a0, a1]."""
        o = self._ajouter("cylinder", {"vertices": 48, "radius": r_ext,
                                       "depth": h, "location": (0, 0, z)},
                          mat, nom)
        bm = bmesh.new()
        bm.from_mesh(o.data)
        span = (a1 - a0) % math.tau
        a_del = []
        for v in bm.verts:
            if v.co.x * v.co.x + v.co.y * v.co.y < r_int * r_int - 1e-6:
                a_del.append(v)
                continue
            da = (math.atan2(v.co.y, v.co.x) - a0) % math.tau
            if da > span + 1e-4:
                a_del.append(v)
        if a_del:
            bmesh.ops.delete(bm, geom=a_del, context="VERTS")
        bm.to_mesh(o.data)
        bm.free()
        return o

    def _boite(self, centre, taille, rotation_z, mat, nom, echelle_x=1.0):
        """Boîte à taille et rotation données (helpers pour pièces variées)."""
        o = self._ajouter("cube", {"size": 1, "location": centre,
                                   "rotation": (0, 0, rotation_z)}, mat, nom)
        o.scale = (taille[0] * echelle_x, taille[1], taille[2])
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        return o

    # ------------------------ KIT MODULAIRE / INSTANCING ----------------------
    def _base_unique(self, nom, ajouter_pieces):
        """Construit une pièce de kit UNE FOIS : les primitives posées par
        ajouter_pieces() sont jointes en UN seul mesh partagé (la base).
        On la réinstancie ensuite partout -> mémoire réduite, scène propre,
        modification centralisée (on change la base, tout suit)."""
        debut = len(bpy.data.objects)
        ajouter_pieces()
        pieces = list(bpy.data.objects)[debut:]
        if not pieces:
            raise RuntimeError("kit: aucune pièce pour la base %s" % nom)
        if len(pieces) > 1:
            for p in pieces:
                p.select_set(True)
            bpy.context.view_layer.objects.active = pieces[0]
            bpy.ops.object.join()
        o = bpy.context.object
        o.name = nom
        o.select_set(False)
        self.bases.append(o)          # supprimée après instancing (mesh partagé conservé)
        return o

    def _instancier(self, base, nom, location, rotation_z=0.0, echelle=(1.0, 1.0, 1.0)):
        """Instance partageant le mesh de la base, avec sa propre transform.
        glTF exportera la géométrie une fois + N nœuds de transform."""
        o = bpy.data.objects.new(nom, base.data)
        bpy.context.scene.collection.objects.link(o)
        o.location = location
        o.rotation_euler = (0, 0, rotation_z)
        o.scale = echelle
        self.objets.append(nom)
        return o

    # ============================ COMPOSANTS =============================
    def elliptical_room(self):
        p = self.param["room"]
        k = p["k_elliptique"] if p["elliptique"] else 1.0
        # sol (stone_floor)
        sol = self._anneau(0, p["rayon"] * 1.02, 0.26, 0.52,
                           self.mats["stone_floor"], "sol")
        self._echelle_x(sol, k)
        # assise externe (parement trim)
        base = self._anneau(0, p["rayon"] * 1.12, 0.06, 0.34,
                            self.mats["stone_trim"], "assise")
        self._echelle_x(base, k)
        # cercle de sol en parement autour du centre (motif de sol)
        sol_motif = self._anneau(p["rayon"] * 0.62, p["rayon"] * 0.66, 0.51, 0.02,
                                 self.mats["stone_trim"], "motif_sol_1")
        self._echelle_x(sol_motif, k)

    def central_pool(self):
        a = self.param["arena"]
        if not a["enabled"]:
            return
        p = self.param["room"]
        k = p["k_elliptique"] if p["elliptique"] else 1.0
        r = a["radius"]
        # bassin creusé (profondeur visible)
        basin = self._anneau(0, r, -0.15, a["recessed"] * 0.9,
                             self.mats["dark_stone"], "bassin")
        self._echelle_x(basin, k)
        # eau / énergie émissive
        eau = self._anneau(0, r * 0.94, 0.36, 0.10,
                           self.mats["central_water"], "eau_centrale")
        self._echelle_x(eau, k)
        # anneaux émissifs internes (OPAQUES, pas de transparence : lourde en
        # EEVEE sur CPU) : profondeur visuelle de l'énergie
        for gi, fr in enumerate((0.55, 0.80)):
            anneau_i = self._anneau(r * fr - 0.06, r * fr + 0.06, 0.425, 0.02,
                                    self.mats["central_water"], "anneau_energie_%d" % gi)
            self._echelle_x(anneau_i, k)
        # bordure en pierre claire (parement)
        bord = self._anneau(r, r * 1.08, 0.50, 0.14,
                            self.mats["stone_trim"], "bordure_arena")
        self._echelle_x(bord, k)
        # jante métallique
        jante = self._ajouter("torus", {"major_radius": r * 1.04,
                                        "minor_radius": 0.05, "location": (0, 0, 0.57)},
                              self.mats["metal"], "jante_arena")
        self._echelle_x(jante, k)
        # rambarde basse autour du bord (chute protégée, détail métal)
        r_rail = r * 1.10
        rail = self._anneau(r_rail - 0.04, r_rail + 0.04, 0.72, 0.08,
                            self.mats["metal"], "rambarde_arena")
        self._echelle_x(rail, k)
        for i in range(16):
            a = i / 16 * math.tau
            x, y = math.cos(a) * r_rail, math.sin(a) * r_rail
            self._ajouter("cylinder", {"vertices": 6, "radius": 0.05, "depth": 0.5,
                                       "location": (x, y, 0.50)},
                          self.mats["metal_bleu"], "montant_rambarde_%d" % i)

    def concentric_steps(self):
        s = self.param["steps"]
        p = self.param["room"]
        k = p["k_elliptique"] if p["elliptique"] else 1.0
        n = s["count"]
        r_int = s["inner_radius"]
        r_ext = s["outer_radius"]
        for i in range(1, n + 1):
            r1 = r_int + (r_ext - r_int) * ((i - 1) / n)
            r2 = r_int + (r_ext - r_int) * (i / n)
            z = s["height"] * i + 0.15
            mat = self.mats["pierre_gradins"] if i % 2 else self.mats["dark_stone"]
            marche = self._anneau(r1, r2, z, s["depth"], mat, "gradin_%d" % i)
            self._echelle_x(marche, k)
            # parement de la contremarche (tranche claire côté centre)
            parement = self._anneau(r1 - 0.06, r1 + 0.06, z - s["depth"] / 2,
                                    s["depth"] + 0.03, self.mats["stone_trim"],
                                    "parement_%d" % i)
            self._echelle_x(parement, k)
            # NEZ DE MARCHE : finition claire sur le bord extérieur du giron
            nez = self._anneau(r2 - 0.05, r2 + 0.05, z + 0.02, 0.07,
                               self.mats["stone_trim"], "nez_%d" % i)
            self._echelle_x(nez, k)

    def radial_stairs(self):
        st = self.param["stairs"]
        if not st["enabled"]:
            return
        s = self.param["steps"]
        p = self.param["room"]
        k = p["k_elliptique"] if p["elliptique"] else 1.0
        r0 = s["inner_radius"] + 0.5
        r1 = s["outer_radius"] - 0.3
        n_steps = st["steps_per"]
        angles = self.angles_portes or [i / st["count"] * math.tau
                                        for i in range(st["count"])]
        larg = st["width"]
        for i, a in enumerate(angles[:st["count"]]):
            for kk in range(n_steps):
                r_mid = r0 + (r1 - r0) * (kk + 0.5) / n_steps
                z = 0.35 + kk * st["height"]
                b = self._boite((math.cos(a) * r_mid, math.sin(a) * r_mid, z),
                                ((r1 - r0) / n_steps, larg, st["height"]),
                                a, self.mats["stone_trim"],
                                "escalier_%d_%d" % (i, kk))
                self._echelle_x(b, k)

    def stone_columns(self):
        c = self.param["columns"]
        r_col = c["ring_radius"]
        r_shaft = c["radius"]
        h_shaft = c["height"]
        self.angles_colonnes = [i / c["count"] * math.tau for i in range(c["count"])]
        # KIT : une seule colonne construite (au centre), instanciée partout.
        base = self._base_unique("kit_colonne", lambda: self._pieces_colonne(
            r_shaft, h_shaft))
        for i, a in enumerate(self.angles_colonnes):
            x, y = math.cos(a) * r_col, math.sin(a) * r_col
            fac = 1.0 + self.rng.uniform(-0.04, 0.04)
            hfac = 1.0 + self.rng.uniform(-0.02, 0.02)
            self._instancier(base, "colonne_%d" % i, (x, y, 0.0),
                             rotation_z=a, echelle=(fac, fac, hfac))

    def _pieces_colonne(self, r_shaft, h_shaft):
        """Les pièces d'UNE colonne, centrées à l'origine (kit asset)."""
        self._ajouter("cylinder", {"vertices": 16, "radius": r_shaft * 1.8,
                                   "depth": 0.26, "location": (0, 0, 0.13)},
                      self.mats["stone_trim"], "col_base")
        self._ajouter("cylinder", {"vertices": 16, "radius": r_shaft * 1.5,
                                   "depth": 0.16, "location": (0, 0, 0.34)},
                      self.mats["stone_trim"], "col_base2")
        f = self._ajouter("cylinder", {"vertices": 16, "radius": r_shaft,
                                       "depth": h_shaft,
                                       "location": (0, 0, 0.42 + h_shaft / 2)},
                          self.mats["dark_stone"], "col_fut")
        bm = bmesh.new()
        bm.from_mesh(f.data)
        for v in bm.verts:
            if v.co.z > h_shaft / 2 - 0.02:
                v.co.x *= 0.92
                v.co.y *= 0.92
        bm.to_mesh(f.data)
        bm.free()
        if self.param["columns"]["style"] == "fluted":
            for g in range(8):
                ga = g / 8 * math.tau
                gx, gy = math.cos(ga) * r_shaft * 1.01, math.sin(ga) * r_shaft * 1.01
                self._boite((gx, gy, 0.42 + h_shaft / 2),
                            (0.10, 0.06, h_shaft * 0.88), ga,
                            self.mats["metal_bleu"], "cannelure_%d" % g)
        self._ajouter("torus", {"major_radius": r_shaft * 1.55,
                                "minor_radius": r_shaft * 0.5,
                                "location": (0, 0, 0.42 + h_shaft + 0.14)},
                      self.mats["stone_trim"], "col_tore")
        self._ajouter("cylinder", {"vertices": 16, "radius": r_shaft * 1.7,
                                   "depth": 0.18,
                                   "location": (0, 0, 0.42 + h_shaft + 0.32)},
                      self.mats["stone_trim"], "col_cap")

    def stone_arches(self):
        a = self.param["arches"]
        if not a["enabled"]:
            return
        n = a["count"]
        r_col = a["radius"]
        h_arch = 0.3 + a["height"] + 0.22
        for i in range(n):
            a1 = i / n * math.tau
            a2 = (i + 1) / n * math.tau
            aM = (a1 + a2) / 2
            mx, my = math.cos(aM) * r_col, math.sin(aM) * r_col
            r_arc = r_col * math.sin((a2 - a1) / 2)
            # variation d'épaisseur
            w_arc = a["width"] * (1.0 + self.rng.uniform(-0.06, 0.06))
            arc = self._ajouter("torus", {"major_radius": r_arc,
                                          "minor_radius": w_arc,
                                          "location": (mx, my, h_arch)},
                                self.mats["dark_stone"], "arc_%d" % i)
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
            # imposte (parement) à la retombée
            self._boite((math.cos(a1) * r_col, math.sin(a1) * r_col, h_arch - 0.2),
                        (0.30, 0.24, 0.34), aM, self.mats["stone_trim"],
                        "imposte_%d" % i)
            # clé de voûte (boîte saillante au sommet de l'arc)
            self._boite((mx, my, h_arch + r_arc * 0.5),
                        (0.20, 0.18, 0.30), aM, self.mats["stone_trim"],
                        "clef_%d" % i)
            # VOUSSOIRS : blocs segmentés le long de l'arc (alternance tonale)
            nv = 7
            tx, ty = -math.sin(aM), math.cos(aM)
            for vk in range(nv):
                th = math.pi * (vk + 0.5) / nv
                vx = mx + r_arc * math.cos(th) * tx
                vy = my + r_arc * math.cos(th) * ty
                vz = h_arch + r_arc * math.sin(th)
                mat_v = self.mats["stone_trim"] if vk % 2 else self.mats["pierre_gradins"]
                self._boite((vx, vy, vz), (0.34, 0.17, 0.17), aM, mat_v,
                            "voussoir_%d_%d" % (i, vk))

    def curved_walls(self):
        w = self.param["walls"]
        p = self.param["room"]
        k = p["k_elliptique"] if p["elliptique"] else 1.0
        n = w["segments"]
        # les portes remplacent des panneaux entiers
        angles_portes = set()
        if self.param["doorway"]["enabled"]:
            dcount = self.param["doorway"]["count"]
            for j in range(dcount):
                idx = int((j + 0.5) * n / dcount) % n
                angles_portes.add(idx)
        for i in range(n):
            a0 = i / n * math.tau
            a1 = (i + 1) / n * math.tau
            if i in angles_portes:
                continue   # laissé ouvert : la porte y sera posée
            panneau = self._segment_anneau(w["radius"] - w["thickness"], w["radius"],
                                           a0 + 0.012, a1 - 0.012,
                                           w["height"] / 2, w["height"],
                                           self.mats["dark_stone"], "mur_%d" % i)
            self._echelle_x(panneau, k)
            # parapet + créneaux au sommet
            if w["parapet"]:
                para = self._segment_anneau(w["radius"] - w["thickness"] - 0.05,
                                            w["radius"] + 0.05,
                                            a0 + 0.012, a1 - 0.012,
                                            w["height"] + 0.12, 0.24,
                                            self.mats["stone_trim"], "parapet_%d" % i)
                self._echelle_x(para, k)
            if w["crenel"]:
                nb_m = 3
                for m in range(nb_m):
                    am = a0 + (a1 - a0) * (m + 0.5) / nb_m
                    largeur = (a1 - a0) / nb_m * w["radius"] * 0.55
                    h_m = self.rng.uniform(0.25, 0.45)
                    b = self._boite((math.cos(am) * w["radius"],
                                     math.sin(am) * w["radius"],
                                     w["height"] + 0.24 + h_m / 2),
                                    (largeur, 0.42, h_m), am,
                                    self.mats["stone_trim"], "creneau_%d_%d" % (i, m))
                    self._echelle_x(b, k)
        # ancre pour le join
        self.ancre = "mur_0" if 0 not in angles_portes else "mur_1"

    def wall_niches(self):
        n = self.param["niches"]
        if not n["enabled"]:
            return
        w = self.param["walls"]
        p = self.param["room"]
        k = p["k_elliptique"] if p["elliptique"] else 1.0
        pris = set()
        if self.param["doorway"]["enabled"]:
            dcount = self.param["doorway"]["count"]
            for j in range(dcount):
                pris.add(int((j + 0.5) * w["segments"] / dcount) % w["segments"])
        angles = []
        for i in range(w["segments"]):
            if i in pris:
                continue
            angles.append((i + 0.5) / w["segments"] * math.tau)
        rng_n = self.rng
        for a in rng_n.sample(angles, min(n["count"], len(angles))):
            x, y = math.cos(a) * (w["radius"] - 0.35), math.sin(a) * (w["radius"] - 0.35)
            # niche : cadre en parement plaqué au mur
            cadre = self._boite((x, y, w["height"] * 0.55),
                                (0.16, w["radius"] * 0.14, w["height"] * 0.35),
                                a, self.mats["stone_trim"], "niche_cadre")
            self._echelle_x(cadre, k)
            # arche de niche
            nx, ny = math.cos(a) * (w["radius"] - 0.55), math.sin(a) * (w["radius"] - 0.55)
            arc = self._ajouter("torus", {"major_radius": w["radius"] * 0.06,
                                          "minor_radius": 0.10,
                                          "location": (nx, ny, w["height"] * 0.55 + w["radius"] * 0.06)},
                                self.mats["stone_trim"], "niche_arc")
            axis = __import__("mathutils").Vector((math.cos(a), math.sin(a), 0.0))
            q = __import__("mathutils").Vector((0.0, 0.0, 1.0)).rotation_difference(axis)
            arc.rotation_euler = q.to_euler("XYZ")
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
            bm = bmesh.new()
            bm.from_mesh(arc.data)
            for f in list(bm.faces):
                if all(v.co.z < w["height"] * 0.55 for v in f.verts):
                    bm.faces.remove(f)
            bm.to_mesh(arc.data)
            bm.free()
            # orbe émissif dans la niche (chaud ou froid selon le contraste)
            lum = self.param["lighting"]
            mat_orbe = self.mats["feu_orange"] if lum["warm_perimeter"] else self.mats["central_water"]
            self._ajouter("uv_sphere", {"segments": 8, "ring_count": 4,
                                        "radius": 0.16,
                                        "location": (nx, ny, w["height"] * 0.55)},
                          mat_orbe, "orbe_niche")

    def doors(self):
        d = self.param["doorway"]
        if not d["enabled"]:
            return
        w = self.param["walls"]
        p = self.param["room"]
        k = p["k_elliptique"] if p["elliptique"] else 1.0
        self.angles_portes = []
        dcount = d["count"]
        for j in range(dcount):
            idx = int((j + 0.5) * w["segments"] / dcount) % w["segments"]
            ang = (idx + 0.5) / w["segments"] * math.tau
            self.angles_portes.append(ang)
            x, y = math.cos(ang) * w["radius"], math.sin(ang) * w["radius"]
            # piédroits
            for signe in (-1, 1):
                da = signe * (d["width"] / 2 / w["radius"])
                xp, yp = math.cos(ang + da) * w["radius"], math.sin(ang + da) * w["radius"]
                pd = self._boite((xp, yp, d["height"] / 2), (0.30, 0.30, d["height"]),
                                 ang, self.mats["stone_trim"], "piedroit_%d" % j)
                self._echelle_x(pd, k)
            # linteau
            lint = self._boite((x, y, d["height"] + 0.15), (d["width"] + 0.4, 0.5, 0.30),
                               ang, self.mats["stone_trim"], "linteau_%d" % j)
            self._echelle_x(lint, k)
            # arche au-dessus de la porte
            if d["arch"]:
                r_arc = d["width"] / 2
                arc = self._ajouter("torus", {"major_radius": r_arc,
                                              "minor_radius": 0.14,
                                              "location": (x, y, d["height"] + 0.15)},
                                    self.mats["dark_stone"], "arc_porte_%d" % j)
                axis = __import__("mathutils").Vector((math.cos(ang), math.sin(ang), 0.0))
                q = __import__("mathutils").Vector((0.0, 0.0, 1.0)).rotation_difference(axis)
                arc.rotation_euler = q.to_euler("XYZ")
                bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
                bm = bmesh.new()
                bm.from_mesh(arc.data)
                for f in list(bm.faces):
                    if all(v.co.z < d["height"] + 0.15 for v in f.verts):
                        bm.faces.remove(f)
                bm.to_mesh(arc.data)
                bm.free()

    def railings(self):
        r = self.param["railings"]
        if not r["enabled"]:
            return
        s = self.param["steps"]
        p = self.param["room"]
        k = p["k_elliptique"] if p["elliptique"] else 1.0
        r_rail = s["outer_radius"]
        z_rail = s["height"] * s["count"] + 0.55
        # main courante (anneau fin)
        rail = self._anneau(r_rail - 0.06, r_rail + 0.06, z_rail, 0.10,
                            self.mats["metal"], "main_courante")
        self._echelle_x(rail, k)
        # balustres : une seule base, instanciée (kit modulaire)
        base_bal = self._base_unique("kit_balustre", lambda: self._ajouter(
            "cylinder", {"vertices": 6, "radius": 0.06, "depth": 0.7,
                         "location": (0, 0, 0)}, self.mats["stone_trim"],
            "balustre_base"))
        nb = max(12, int(r_rail * 1.2))
        for i in range(nb):
            a = i / nb * math.tau
            x, y = math.cos(a) * r_rail, math.sin(a) * r_rail
            b = self._instancier(base_bal, "balustre_%d" % i,
                                 (x, y, z_rail - 0.35), rotation_z=a)
            self._echelle_x(b, k)

    def warm_perimeter_lights(self):
        l = self.param["lighting"]
        if not l["warm_perimeter"]:
            return
        c = self.param["columns"]
        s = self.param["steps"]
        # braseros sur le gradin supérieur : visibles autour du centre, à
        # hauteur d'homme — la lumière chaude baigne la scène.
        r = c["ring_radius"] * 0.96
        z = s["height"] * s["count"] + 0.55
        n = c["count"]
        base_br = self._base_unique("kit_brasero", lambda: self._pieces_brasero(z))
        for i in range(n):
            a = i / n * math.tau + 0.02
            x, y = math.cos(a) * r, math.sin(a) * r
            fac = 1.0 + self.rng.uniform(-0.06, 0.06)
            self._instancier(base_br, "brasero_%d" % i, (x, y, 0.0),
                             rotation_z=a, echelle=(fac, fac, fac))

    def _pieces_brasero(self, z):
        """Pièces d'un brasero centré à l'origine (pied + vasque + flamme)."""
        self._ajouter("cylinder", {"vertices": 8, "radius": 0.16, "depth": 0.45,
                                   "location": (0, 0, z - 0.22)},
                      self.mats["metal"], "pied_brasero")
        self._ajouter("cylinder", {"vertices": 8, "radius": 0.40, "depth": 0.12,
                                   "location": (0, 0, z + 0.06)},
                      self.mats["metal"], "vasque")
        self._ajouter("uv_sphere", {"segments": 12, "ring_count": 6,
                                    "radius": 0.42, "location": (0, 0, z + 0.42)},
                      self.mats["feu_orange"], "flamme")

    def decorative_elements(self):
        p = self.param["room"]
        k = p["k_elliptique"] if p["elliptique"] else 1.0
        w = self.param["walls"]
        s = self.param["steps"]
        a = self.param["arena"]
        # motif de sol radial (rayons de parement autour de l'arène)
        if a["enabled"]:
            r0 = a["radius"] * 1.2
            r1 = s["inner_radius"] - 0.3
            nb = 24
            for i in range(nb):
                ang = i / nb * math.tau
                r_mid = (r0 + r1) / 2
                x, y = math.cos(ang) * r_mid, math.sin(ang) * r_mid
                b = self._boite((x, y, 0.52), ((r1 - r0), 0.14, 0.02),
                                ang, self.mats["stone_trim"], "rayon_sol_%d" % i)
                self._echelle_x(b, k)
        # pierres éparses au pied du mur : 2 bases instanciées avec variations
        base_p = self._base_unique("kit_pierre", lambda: self._ajouter(
            "ico_sphere", {"subdivisions": 1, "radius": 0.25, "location": (0, 0, 0)},
            self.mats["pierre_gradins"], "pierre_base"))
        nb = 10
        for i in range(nb):
            ang = self.rng.uniform(0, math.tau)
            r = w["radius"] - 0.8 + self.rng.uniform(-0.4, 0.4)
            x, y = math.cos(ang) * r, math.sin(ang) * r
            taille = self.rng.uniform(0.6, 1.4)
            b = self._instancier(base_p, "pierre_%d" % i, (x, y, 0),
                                 rotation_z=self.rng.uniform(0, math.tau),
                                 echelle=(taille * self.rng.uniform(0.8, 1.3),
                                          taille * self.rng.uniform(0.8, 1.3),
                                          taille * self.rng.uniform(0.5, 0.9)))
            self._echelle_x(b, k)
        # fissures légères du sol (boîtes fines et sombres, orientées au hasard)
        for i in range(6):
            ang = self.rng.uniform(0, math.tau)
            r = self.rng.uniform(1.0, p["rayon"] * 0.85)
            x, y = math.cos(ang) * r, math.sin(ang) * r
            lon = self.rng.uniform(1.0, 2.6)
            b = self._boite((x, y, 0.521), (lon, 0.05, 0.012), ang,
                            self.mats["dark_stone"], "fissure_%d" % i)
            self._echelle_x(b, k)

    def emissive_center(self):
        a = self.param["arena"]
        if not a["enabled"]:
            return
        p = self.param["room"]
        k = p["k_elliptique"] if p["elliptique"] else 1.0
        # couronne émissive autour de l'arène (souligne le point focal)
        couronne = self._anneau(a["radius"] * 1.10, a["radius"] * 1.16, 0.05, 0.05,
                                self.mats["central_water"], "couronne_emissive")
        self._echelle_x(couronne, k)

    # -------------------- PASSÉE DE DIRECTION ARTISTIQUE --------------------
    def plinthe_mur(self):
        """Transition mur/sol : bande de parement à la base du mur."""
        w = self.param["walls"]
        p = self.param["room"]
        k = p["k_elliptique"] if p["elliptique"] else 1.0
        r_int = w["radius"] - w["thickness"] - 0.10
        plinthe = self._anneau(r_int, r_int + 0.55, 0.28, 0.56,
                               self.mats["stone_trim"], "plinthe")
        self._echelle_x(plinthe, k)

    def tourelles_bassin(self):
        """4 tourelles à orbe cyan sur la bordure du bassin (points focaux)."""
        a = self.param["arena"]
        if not a["enabled"]:
            return
        r = a["radius"]
        for i in range(4):
            ang = i / 4 * math.tau + math.pi / 4
            x, y = math.cos(ang) * r * 1.10, math.sin(ang) * r * 1.10
            self._ajouter("cylinder", {"vertices": 10, "radius": 0.16, "depth": 0.7,
                                       "location": (x, y, 0.60)},
                          self.mats["stone_trim"], "tourelle_%d" % i)
            self._ajouter("cylinder", {"vertices": 10, "radius": 0.20, "depth": 0.12,
                                       "location": (x, y, 0.95)},
                          self.mats["metal"], "chapiteau_tourelle_%d" % i)
            self._ajouter("uv_sphere", {"segments": 8, "ring_count": 4,
                                        "radius": 0.09, "location": (x, y, 1.05)},
                          self.mats["central_water"], "orbe_tourelle_%d" % i)

    def obelisque_centre(self):
        """Spire d'énergie au centre du bassin (point focal vertical, héro)."""
        a = self.param["arena"]
        if not a["enabled"]:
            return
        base = self._ajouter("cylinder", {"vertices": 4, "radius": 0.30, "depth": 0.25,
                                          "location": (0, 0, 0.50)},
                             self.mats["stone_trim"], "base_obel")
        # spire émissive cyan : elle renforce le centre au lieu de le cacher
        ob = self._ajouter("cone", {"vertices": 4, "radius1": 0.24, "radius2": 0.05,
                                    "depth": 2.2, "location": (0, 0, 0.62 + 1.1)},
                           self.mats["central_water"], "obelisque")
        self._ajouter("uv_sphere", {"segments": 8, "ring_count": 4, "radius": 0.12,
                                    "location": (0, 0, 0.62 + 2.2 + 0.06)},
                      self.mats["central_water"], "pointe_obel")

    def traces_sol(self):
        """Traces d'usage : sentiers sombres des portes vers le centre."""
        if not self.angles_portes:
            return
        s = self.param["steps"]
        w = self.param["walls"]
        r0 = s["outer_radius"] + 0.6
        r1 = w["radius"] - w["thickness"] - 1.2
        for i, ang in enumerate(self.angles_portes[:2]):
            for j in (-1, 0, 1):
                a = ang + j * 0.035
                r_mid = (r0 + r1) / 2
                x, y = math.cos(a) * r_mid, math.sin(a) * r_mid
                b = self._boite((x, y, 0.525), ((r1 - r0), 0.55, 0.018), a,
                                self.mats["dark_stone"], "trace_%d_%d" % (i, j))
        return

    def meurtrieres(self):
        """Meurtrières (fentes) dans les panneaux de mur : densité médiévale."""
        w = self.param["walls"]
        p = self.param["room"]
        r_face = w["radius"] - w["thickness"] + 0.02
        for i in range(w["segments"]):
            a = (i + 0.5) / w["segments"] * math.tau
            x, y = math.cos(a) * r_face, math.sin(a) * r_face
            for hh in (0.35, 0.62):
                self._boite((x, y, w["height"] * hh), (0.10, 0.30, w["height"] * 0.10),
                            a, self.mats["metal_bleu"], "meurtriere_%d_%d" % (i, int(hh * 100)))

    def porte_bois(self):
        """Porte en bois légèrement entre-ouverte (la salle est habitée)."""
        d = self.param["doorway"]
        w = self.param["walls"]
        if not d["enabled"] or not self.angles_portes:
            return
        ang = self.angles_portes[0]
        x, y = math.cos(ang) * (w["radius"] - 0.6), math.sin(ang) * (w["radius"] - 0.6)
        large = d["width"] / 2
        for signe in (-1, 1):
            dx = signe * large * 0.5
            a = ang + signe * 0.28   # entre-ouvert
            b = self._boite((x, y, d["height"] / 2), (0.20, large * 0.92, d["height"]),
                            a, self.mats["bois"], "vantail_%d" % (0 if signe < 0 else 1))
            self._boite((x, y, d["height"] / 2), (0.24, large * 0.10, d["height"]),
                        ang, self.mats["metal"], "ferrure_%d" % (0 if signe < 0 else 1))

    def flaques_torches(self):
        """Flaques de lumière chaude au sol sous chaque brasero."""
        l = self.param["lighting"]
        if not l["warm_perimeter"]:
            return
        c = self.param["columns"]
        s = self.param["steps"]
        r = c["ring_radius"] * 0.96
        z = s["height"] * s["count"] + 0.10
        n = c["count"]
        for i in range(n):
            a = i / n * math.tau + 0.02
            x, y = math.cos(a) * r, math.sin(a) * r
            self._ajouter("cylinder", {"vertices": 12, "radius": 0.55,
                                       "depth": 0.03, "location": (x, y, z + 0.01)},
                          self.mats["feu_sol"], "flaque_%d" % i)

    # ============================ ORCHESTRATION ===========================
    def build(self) -> dict:
        self.elliptical_room()
        self.central_pool()
        self.concentric_steps()
        self.doors()
        self.radial_stairs()
        self.stone_columns()
        self.stone_arches()
        self.curved_walls()
        self.wall_niches()
        self.railings()
        self.warm_perimeter_lights()
        self.emissive_center()
        self.decorative_elements()
        # passée direction artistique : densité + storytelling
        self.plinthe_mur()
        self.tourelles_bassin()
        self.obelisque_centre()
        self.traces_sol()
        self.meurtrieres()
        self.porte_bois()
        self.flaques_torches()
        # les bases de kit ne doivent pas entrer dans le join final : on les
        # retire (leurs instances partagent le mesh, il reste référencé).
        for b in self.bases:
            try:
                bpy.data.objects.remove(b, do_unlink=True)
            except Exception:
                pass
        return {
            "ancre": self.ancre,
            "objet": self.ancre,
            "hauteur": self.param["room"]["height"],
            "rayon": self.param["room"]["rayon"],
            "elliptique": self.param["room"]["elliptique"],
        }
