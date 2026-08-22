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
import os
import random
import sys

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


def mat(nom, rgba, rough=0.85, metal=0.0):
    m = bpy.data.materials.new(nom)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = rgba
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
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
    "fenetre": mat("fenetre", (0.08, 0.10, 0.16, 1), rough=0.6),
    "toit_rouge": mat("toit_rouge", (0.55, 0.18, 0.12, 1), rough=0.85),
    "toit_gris": mat("toit_gris", (0.40, 0.40, 0.42, 1), rough=0.85),
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
elif "thatch" in spec.get("materials", []):
    mat_toit = MATS["thatch"]
else:
    mat_toit = materiau_bois()

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

# ---------- joindre ----------
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.select_by_type(type="MESH")
bpy.context.view_layer.objects.active = toit_obj
bpy.ops.object.join()
corps = bpy.context.object
corps.name = spec.get("slug", "asset")

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
cam.location = (L * 0.9, -L * 1.05, H * 0.85)
empty = bpy.data.objects.new("T", None)
bpy.context.scene.collection.objects.link(empty)
empty.location = (0, 0, H * 0.5)
c = cam.constraints.new("TRACK_TO")
c.target = empty
c.track_axis = "TRACK_NEGATIVE_Z"
c.up_axis = "UP_Y"
bpy.context.scene.camera = cam
sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"
sc.display.shading.light = "STUDIO"
sc.display.shading.color_type = "MATERIAL"
sc.display.shading.show_shadows = True
sc.render.resolution_x = 800
sc.render.resolution_y = 640
sc.render.film_transparent = False
sc.world = bpy.data.worlds.new("W")
sc.world.color = (0.09, 0.10, 0.13)
sc.render.filepath = APERCU
bpy.ops.render.render(write_still=True)

print("RAPPORT: " + json.dumps({
    "triangles": triangles,
    "octets": os.path.getsize(GLB),
    "dimensions": [round(L, 2), round(P, 2), round(H, 2)],
    "materiaux": list(spec.get("materials", [])),
    "apercu": os.path.exists(APERCU),
}))
