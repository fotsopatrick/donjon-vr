# -*- coding: utf-8 -*-
"""construire.py — génère un asset depuis une spec (P0 : building).

Usage (lancé par blender_controller) :
   blender -b --python construire.py -- <spec.json> <glb> <apercu.png> <source.blend>

Le script est REPRODUCTIBLE : même spec = même asset. Chaque exécution :
  1. construit la géométrie paramétrique (murs, toit, porte, fenêtres, mousse),
  2. exporte le GLB qui ira dans le jeu,
  3. garde le .blend source de CETTE version,
  4. rend un aperçu Workbench (CPU, léger),
  5. imprime RAPPORT: <json> avec triangles et octets.
"""
import bpy
import bmesh
import json
import math
import mathutils
import os
import random
import sys
import time as _time

T_DEBUT = _time.time()

argv = sys.argv[sys.argv.index("--") + 1:]
SPEC, GLB, APERCU, BLEND = argv[:4]
spec = json.load(open(SPEC, encoding="utf-8"))

# ---------- nettoyage ----------
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete()
for m in list(bpy.data.materials):
    bpy.data.materials.remove(m)
for c in list(bpy.data.collections):
    bpy.data.collections.remove(c)


def mat(nom, rgba, rough=0.85, metal=0.0, emissive=None, emissive_force=0.0):
    m = bpy.data.materials.new(nom)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = rgba
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if emissive:
        bsdf.inputs["Emission Color"].default_value = emissive
        bsdf.inputs["Emission Strength"].default_value = emissive_force
    m.diffuse_color = rgba
    return m


MATS = {
    "dark_wood": mat("dark_wood", (0.20, 0.11, 0.06, 1), rough=0.92),
    "wood": mat("wood", (0.42, 0.24, 0.11, 1), rough=0.85),
    "aged_stone": mat("aged_stone", (0.30, 0.29, 0.28, 1), rough=0.95),
    "stone": mat("stone", (0.55, 0.54, 0.52, 1), rough=0.90),
    "plaster": mat("plaster", (0.82, 0.79, 0.72, 1), rough=0.90),
    "thatch": mat("thatch", (0.72, 0.62, 0.35, 1), rough=1.0),
    "moss": mat("moss", (0.28, 0.42, 0.22, 1), rough=1.0),
    "porte": mat("porte", (0.30, 0.17, 0.08, 1), rough=0.88),
    "feuillage": mat("feuillage", (0.13, 0.21, 0.13, 1), rough=1.0),
    # accent chaud (DA 10) : les fenêtres luisent ambre dans le monde froid
    "fenetre": mat("fenetre", (0.22, 0.12, 0.06, 1), rough=0.6,
                   emissive=(0.85, 0.42, 0.16, 1), emissive_force=1.6),
    "toit_rouge": mat("toit_rouge", (0.55, 0.18, 0.12, 1), rough=0.85),
    "toit_gris": mat("toit_gris", (0.40, 0.40, 0.42, 1), rough=0.85),
    "toit_bleu": mat("toit_bleu", (0.22, 0.32, 0.52, 1), rough=0.6,
                    metal=0.25),
}


def materiau_bois():
    m = spec.get("materials") or []
    for nom in ("dark_wood", "wood"):
        if nom in m:
            return MATS[nom]
    return MATS["wood"]


def ajouter(primitive, kwargs, materiau, nom):
    getattr(bpy.ops.mesh, "primitive_%s_add" % primitive)(**kwargs)
    o = bpy.context.object
    o.name = nom
    if materiau:
        o.data.materials.append(materiau)
    return o


dims = spec.get("dimensions", {"l": 4.0, "p": 3.0, "h": 3.2})
L, P, H = dims["l"], dims["p"], dims["h"]
mat_bois = materiau_bois()
mat_murs = None
for m in spec.get("materials", []):
    if m in MATS and m in ("aged_stone", "stone", "plaster"):
        mat_murs = MATS[m]
        break
if mat_murs is None:
    mat_murs = MATS["plaster"] if spec.get("style") == "nordic" else MATS["wood"]

EP = 0.12
rng = random.Random(spec.get("variation", {}).get("seed", 0))
WEATHER = spec.get("variation", {}).get("weathered", 0.0)
MOSS = spec.get("variation", {}).get("moss", 0.0)


def teinter(materiau, assombrir):
    if assombrir <= 0:
        return
    c = list(materiau.diffuse_color)
    c[0] = max(0.02, c[0] * (1.0 - 0.6 * assombrir))
    c[1] = max(0.02, c[1] * (1.0 - 0.6 * assombrir))
    c[2] = max(0.02, c[2] * (1.0 - 0.6 * assombrir))
    materiau.diffuse_color = c
    bsdf = materiau.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = min(1.0, bsdf.inputs["Roughness"].default_value + 0.06 * assombrir)


teinter(MATS["dark_wood"], WEATHER)
teinter(MATS["wood"], WEATHER)
teinter(mat_murs, WEATHER * 0.6)

# ---------- scène intérieure (benchmark vision) OU bâtiment classique ----------
sc = spec.get("scene") or {}
est_interieur = bool(sc and sc.get("layout", {}).get("shape") in
               ("circular", "elliptical", "rectangular", "square", "irregular"))
if est_interieur:
    # ============ SALLE INTÉRIEURE ============
    # DungeonChamber : kit architectural procédural. La SceneSpec pilote
    # room/arena/steps/columns/arches/wall/doorway/braseros/émissif central
    # et les matériaux de pierre texturés. Aucun modèle spécifique à une photo.
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from dungeon_kit import DungeonChamber  # noqa: E402

    chambre = DungeonChamber(
        sc,
        {"l": L, "p": P, "h": H},
        seed=spec.get("variation", {}).get("seed", 0))
    info = chambre.build()
    toit_obj = bpy.data.objects[info["objet"]]
    R = info["rayon"]
    H = info["hauteur"]
    elliptique = info["elliptique"]
    nb_colonnes = chambre.param["columns"]["count"]
    r_col = chambre.param["columns"]["ring_radius"]
    k_param = chambre.param

else:

    # ---------- 4 murs minces (intérieur vide) ----------
    demi_l, demi_p = L / 2, P / 2
    murs = []
    for (dx, dz, w, d, y_centre) in (
        (0, -demi_p, L, EP, H / 2),
        (0, demi_p, L, EP, H / 2),
        (-demi_l, 0, EP, P, H / 2),
        (demi_l, 0, EP, P, H / 2),
    ):
        m = ajouter("cube", {"size": 1, "location": (dx, dz, y_centre)},
                    mat_murs, "mur")
        m.scale = (w / 2, d / 2, H / 2)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        murs.append(m)

    # ---------- toit (prisme triangulaire) ----------
    toit = spec.get("toit", {"type": "pentu", "pente": "moyenne"})
    h_toit = {"forte": L * 0.55, "moyenne": L * 0.42, "nulle": L * 0.06}.get(toit.get("pente"), L * 0.42)
    if toit.get("type") == "plat":
        h_toit = L * 0.06

    couleur_toit = toit.get("couleur")
    if couleur_toit == "rouge":
        mat_toit = MATS["toit_rouge"]
    elif couleur_toit == "gris":
        mat_toit = MATS["toit_gris"]
    elif couleur_toit == "bleu":
        mat_toit = MATS["toit_bleu"]
    elif "thatch" in spec.get("materials", []):
        mat_toit = MATS["thatch"]
    else:
        mat_toit = materiau_bois()

    if (toit.get("type") or "").lower() in ("dome", "dôme"):
        # dôme : demi-sphère posée sur les murs (silhouette de coupole)
        dh = max(L, P) * 0.45
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12,
                                             radius=1, location=(0, 0, H))
        dome = bpy.context.object
        dome.name = "toit"
        dome.scale = (L / 2, P / 2, dh)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        bm = bmesh.new()
        bm.from_mesh(dome.data)
        for f in list(bm.faces):
            if all(v.co.z < H for v in f.verts):
                bm.faces.remove(f)
        bm.to_mesh(dome.data)
        bm.free()
        dome.data.materials.append(mat_toit)
        toit_obj = dome
    else:
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, H + h_toit / 2))
        toit_obj = bpy.context.object
        toit_obj.name = "toit"
        toit_obj.scale = (L / 2 * 1.06, P / 2 * 1.08, h_toit)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        bm = bmesh.new()
        bm.from_mesh(toit_obj.data)
        for v in bm.verts:
            k = v.co.x / (L * 0.53)
            if k >= -0.999:
                v.co.y -= (k * k) * (P * 0.42)
        bm.to_mesh(toit_obj.data)
        bm.free()
        toit_obj.data.materials.append(mat_toit)

    # ---------- porte (face avant, -Z) ----------
    porte_l, porte_h = min(0.9, L * 0.24), min(1.9, H * 0.62)
    p = ajouter("cube", {"size": 1, "location": (0, -demi_p - 0.02, porte_h / 2)},
                MATS["porte"], "porte")
    p.scale = (porte_l / 2, 0.05, porte_h / 2)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    # ---------- 2 fenêtres (côtés) ----------
    fen_l, fen_h = min(0.7, L * 0.2), min(0.8, H * 0.3)
    for sx, sz, ry in ((-demi_l - 0.02, -P * 0.15, math.pi / 2),
                       (-demi_l - 0.02, P * 0.15, math.pi / 2)):
        f = ajouter("cube", {"size": 1, "location": (sx, sz, H * 0.55), "rotation": (0, 0, ry)},
                    MATS["fenetre"], "fenetre")
        f.scale = (fen_h / 2, 0.05, fen_l / 2)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    # ---------- mousse : petits tas verts au pied des murs ----------
    nb_mousse = int(round(MOSS * 26))
    for _ in range(nb_mousse):
        x = rng.uniform(-demi_l + 0.25, demi_l - 0.25)
        z = rng.choice([-demi_p + 0.12, demi_p - 0.12])
        r = rng.uniform(0.10, 0.22)
        b = ajouter("cube", {"size": 1, "location": (x, z, r * 0.5)},
                    MATS["moss"], "mousse")
        b.scale = (r, r * 0.7, r * 0.6)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    # ---------- environnement immédiat (DA 5-7) ----------
    profil = spec.get("style_profile", {}) or {}
    terrain = profil.get("terrain", "rocky wet")
    vegetation = profil.get("vegetation", "dense conifers")

    mat_fond = MATS["aged_stone"] if "aged_stone" in spec.get("materials", []) else MATS["stone"]
    mat_roc = MATS["stone"] if "stone" in spec.get("materials", []) else mat_fond

    # fondation : l'assise qui raccroche la maison au sol, jamais parfaitement droite
    fx, fz = rng.uniform(0.96, 1.04), rng.uniform(0.96, 1.04)
    f = ajouter("cube", {"size": 1, "location": (0, 0, 0.13)}, mat_fond, "fondation")
    f.scale = (L * 0.56 * fx, P * 0.56 * fz, 0.13)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    # rochers : quelques blocs écrasés, irréguliers (DA 6)
    nb_rochers = 3 if "rocky" in terrain else 2
    emprise = max(L, P)
    for _ in range(nb_rochers):
        a = rng.uniform(0, math.tau)
        d = rng.uniform(0.85, 1.55) * emprise * 0.5
        r = rng.uniform(0.20, 0.42)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=r,
                                              location=(math.cos(a) * d, math.sin(a) * d, r * 0.28))
        roc = bpy.context.object
        roc.name = "rocher"
        roc.scale = (rng.uniform(0.8, 1.3), rng.uniform(0.8, 1.3), rng.uniform(0.45, 0.65))
        roc.rotation_euler = (rng.uniform(-0.2, 0.2), rng.uniform(-0.2, 0.2), rng.uniform(0, math.tau))
        roc.data.materials.append(mat_roc)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    # végétation : sapins low-poly groupés en bouquets (DA 7), jamais en rang
    nb_arbres = 6 if "dense" in vegetation else 3
    mat_tronc = MATS["wood"] if "wood" in spec.get("materials", []) else MATS["dark_wood"]
    for i in range(nb_arbres):
        a = rng.uniform(0, math.tau)
        d = rng.uniform(0.9, 1.8) * emprise * 0.5
        xa, za = math.cos(a) * d, math.sin(a) * d
        ech = rng.uniform(0.7, 1.35)
        bpy.ops.mesh.primitive_cylinder_add(vertices=7, radius=0.07, depth=0.55,
                                            location=(xa, za, 0.20 * ech))
        tronc = bpy.context.object
        tronc.name = "tronc"
        tronc.data.materials.append(mat_tronc)
        for k, (r, prof, yb) in enumerate(((0.36, 0.75, 0.55), (0.27, 0.6, 0.95))):
            bpy.ops.mesh.primitive_cone_add(vertices=7, radius1=r, radius2=0.01,
                                            depth=prof, location=(xa, za, yb * ech))
            con = bpy.context.object
            con.name = "cime"
            con.scale = (ech, ech, ech)
            con.data.materials.append(MATS["feuillage"])
        bpy.ops.object.select_all(action="SELECT")
        bpy.ops.object.select_by_type(type="MESH")
        bpy.ops.object.select_all(action="DESELECT")
        for o in bpy.data.objects:
            if o.name in ("cime", "tronc"):
                o.select_set(True)
        bpy.context.view_layer.objects.active = bpy.data.objects["tronc"]
        bpy.ops.object.join()
        arbre = bpy.context.object
        arbre.name = "arbre_%d" % i
        arbre.rotation_euler.z = rng.uniform(0, math.tau)
        bpy.ops.object.select_all(action="DESELECT")

# ---------- joindre ----------
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.select_by_type(type="MESH")
bpy.context.view_layer.objects.active = toit_obj
bpy.ops.object.join()
corps = bpy.context.object
corps.name = spec.get("slug", "asset")

# NOTE : la salle elliptique est gérée élément par élément par DungeonChamber
# (chaque composant est étiré individuellement, colonnes et arches restent
# circulaires). On n'étire PAS l'ensemble joint ici.

# ---------- export GLB ----------
os.makedirs(os.path.dirname(GLB), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=GLB, export_format="GLB")
triangles = sum(len(p.vertices) - 2 for p in corps.data.polygons)

# ---------- source .blend de cette version ----------
os.makedirs(os.path.dirname(BLEND), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=BLEND)

# ---------- aperçu Workbench (CPU, couleurs plates) ----------
bpy.ops.mesh.primitive_plane_add(size=L * 4, location=(0, 0, -0.01))
sol = bpy.context.object
sol.data.materials.append(mat("sol", (0.16, 0.15, 0.14, 1)))
cam_data = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_data)
bpy.context.scene.collection.objects.link(cam)
empty = bpy.data.objects.new("T", None)
bpy.context.scene.collection.objects.link(empty)
if est_interieur:
    # caméra de validation : bibliothèque reproductible, pilotée par la
    # SceneSpec (camera_lib : reference_match / cinematic / overview / gameplay)
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from camera_lib import mode_depuis_spec, regler as _regler_cam
    _mode_cam, _spec_cam = mode_depuis_spec(sc)
    _regler_cam(cam, empty, _mode_cam, R, H, L, P, _spec_cam)
else:
    cam.location = (L * 0.9, -L * 1.05, H * 0.85)
    empty.location = (0, 0, H * 0.5)
c = cam.constraints.new("TRACK_TO")
c.target = empty
c.track_axis = "TRACK_NEGATIVE_Z"
c.up_axis = "UP_Y"
bpy.context.scene.camera = cam
sc = bpy.context.scene
sc.render.resolution_x = 800
sc.render.resolution_y = 640
sc.render.film_transparent = False
sc.world = bpy.data.worlds.new("W")
if est_interieur:
    # EEVEE : rendu réel (matériaux + émissifs qui brillent + lampes).
    # La salle sombre : monde en nuit froide, la lumière vient des lampes.
    sc.render.engine = "BLENDER_EEVEE"
    sc.world.color = k_param["lighting"]["world_color"]
    try:
        # AgX (défaut) désature tout (orange -> beige). Standard garde les
        # couleurs vives : indispensable au contraste cyan/orange.
        sc.view_settings.view_transform = "Standard"
        sc.eevee.use_shadows = True
    except Exception:
        pass
    # lumière de remplissage douce (lune froide) : les murs restent lisibles,
    # sans écraser le contraste bleu/orange
    soleil = bpy.data.lights.new("Lum_ambiant", type="SUN")
    soleil.color = k_param["lighting"]["sun_color"]
    soleil.energy = k_param["lighting"]["sun_energy"]
    so = bpy.data.objects.new("Lum_ambiant", soleil)
    bpy.context.scene.collection.objects.link(so)
    so.rotation_euler = (1.05, 0.0, 0.7)
else:
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.display.shading.light = "STUDIO"
    sc.display.shading.color_type = "MATERIAL"
    sc.display.shading.show_shadows = True
    sc.world.color = (0.09, 0.10, 0.13)

# pour la salle intérieure : lampes = le contraste bleu/cyan + orange se lit.
# Couleurs et intensités pilotées par les paramètres du kit (lighting).
if est_interieur:
    bpy.ops.object.select_all(action="DESELECT")
    lum_c = k_param["lighting"]["center_color"]
    lum_p = k_param["lighting"]["perimeter_color"]
    lum = bpy.data.lights.new("Lum_centre", type="POINT")
    lum.color = lum_c; lum.energy = k_param["lighting"]["center_intensity"]
    o = bpy.data.objects.new("Lum_centre", lum)
    bpy.context.scene.collection.objects.link(o)
    o.location = (0, 0, R * 0.5)
    for i in range(nb_colonnes):
        a = i / nb_colonnes * math.tau
        lum = bpy.data.lights.new("Lum_chaud_%d" % i, type="POINT")
        lum.color = lum_p; lum.energy = k_param["lighting"]["perimeter_intensity"]
        o = bpy.data.objects.new("Lum_chaud_%d" % i, lum)
        bpy.context.scene.collection.objects.link(o)
        o.location = (math.cos(a) * r_col, math.sin(a) * r_col, 2.5)

sc.render.filepath = APERCU
_t_avant_rendu = _time.time()
bpy.ops.render.render(write_still=True)
_t_fin = _time.time()

print("RAPPORT: " + json.dumps({
    "triangles": triangles,
    "octets": os.path.getsize(GLB),
    "dimensions": [round(L, 2), round(P, 2), round(H, 2)],
    "materiaux": list(spec.get("materials", [])),
    "apercu": os.path.exists(APERCU),
    "temps_total_s": round(_t_fin - T_DEBUT, 1),
    "temps_rendu_s": round(_t_fin - _t_avant_rendu, 1),
}))
