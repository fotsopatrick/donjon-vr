import bpy, math, os
# --- nettoyer la scene ---
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete()
for m in list(bpy.data.materials): bpy.data.materials.remove(m)

def mat(nom, rgba, rough=0.7, metal=0.0):
    m = bpy.data.materials.new(nom); m.use_nodes=True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = rgba
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = metal
    m.diffuse_color = rgba          # <- couleur vue par le rendu Workbench
    return m

BOIS   = mat('bois',   (0.42,0.24,0.11,1), rough=0.85)
BOIS2  = mat('bois_h', (0.30,0.17,0.08,1), rough=0.85)   # douves alternées
FER    = mat('fer',    (0.09,0.09,0.11,1), rough=0.5, metal=0.9)

# --- corps du tonneau : cylindre 12 faces, legerement bombe (low-poly) ---
bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.5, depth=1.1)
corps = bpy.context.object; corps.name='Tonneau'
# bomber le milieu : on pousse la boucle du centre vers l'exterieur
import bmesh
me = corps.data
bm = bmesh.new(); bm.from_mesh(me)
for v in bm.verts:
    f = 1.0 + 0.14*(1.0 - (abs(v.co.z)/0.55)**2)   # renflement au centre
    v.co.x *= f; v.co.y *= f
bm.to_mesh(me); bm.free()
corps.data.materials.append(BOIS)

# --- 3 cerclages de fer (tores bas-poly) ---
for z in (-0.42, 0.0, 0.42):
    r = 0.5*(1.0+0.14*(1.0-(abs(z)/0.55)**2)) + 0.02
    bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=0.035,
        major_segments=12, minor_segments=6, location=(0,0,z))
    an = bpy.context.object; an.rotation_euler=(math.pi/2,0,0)
    an.data.materials.append(FER)

# --- couvercle sombre au sommet ---
bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.44, depth=0.06, location=(0,0,0.55))
cap = bpy.context.object; cap.data.materials.append(BOIS2)

# --- joindre tout en un objet ---
bpy.ops.object.select_all(action='SELECT')
bpy.context.view_layer.objects.active = corps
bpy.ops.object.join()
corps = bpy.context.object

# --- EXPORT GLB pour le jeu ---
os.makedirs(os.path.expanduser('~/donjon-vr/modeles'), exist_ok=True)
glb = os.path.expanduser('~/donjon-vr/modeles/tonneau.glb')
bpy.ops.export_scene.gltf(filepath=glb, export_format='GLB', use_selection=False)
tris = sum(len(p.vertices)-2 for p in corps.data.polygons)
print("TRIANGLES:", tris)
print("GLB:", glb, os.path.getsize(glb), "octets")

# --- RENDU apercu (Workbench = sur CPU sans GPU, couleurs plates) ---
sol = bpy.ops.mesh.primitive_plane_add(size=8, location=(0,0,-0.56))
plane = bpy.context.object; plane.data.materials.append(mat('sol',(0.16,0.15,0.14,1)))
cam_data = bpy.data.cameras.new('Cam'); cam = bpy.data.objects.new('Cam',cam_data)
bpy.context.scene.collection.objects.link(cam)
cam.location=(2.2,-2.4,1.7)
empty = bpy.data.objects.new('T',None); bpy.context.scene.collection.objects.link(empty)
empty.location=(0,0,0)
c = cam.constraints.new('TRACK_TO'); c.target=empty; c.track_axis='TRACK_NEGATIVE_Z'; c.up_axis='UP_Y'
bpy.context.scene.camera = cam
sc = bpy.context.scene
sc.render.engine='BLENDER_WORKBENCH'
sc.display.shading.light='STUDIO'; sc.display.shading.color_type='MATERIAL'
sc.display.shading.show_shadows=True; sc.display.shading.show_cavity=True
sc.render.resolution_x=800; sc.render.resolution_y=640
sc.render.film_transparent=False
sc.world = bpy.data.worlds.new('W'); sc.world.color=(0.09,0.10,0.13)
out = os.path.expanduser('~/donjon-vr/blender/apercu_tonneau.png')
sc.render.filepath=out
bpy.ops.render.render(write_still=True)
print("APERCU:", out)
