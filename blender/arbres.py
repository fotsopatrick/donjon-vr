import bpy, math, os
def mat(nom,rgba,rough=0.85):
    if len(rgba)==3: rgba=(*rgba,1.0)
    m=bpy.data.materials.new(nom); m.use_nodes=True
    b=m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value=rgba; b.inputs['Roughness'].default_value=rough
    m.diffuse_color=rgba; return m
def reset():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete()
def cyl(r1,r2,d,z,m,seg=7):
    bpy.ops.mesh.primitive_cone_add(vertices=seg,radius1=r1,radius2=r2,depth=d,location=(0,0,z))
    o=bpy.context.object; o.data.materials.append(m); return o
def ico(r,z,m,sub=1,sx=1):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub,radius=r,location=(0,0,z))
    o=bpy.context.object; o.scale=(sx,sx,0.85); o.data.materials.append(m); return o
os.makedirs(os.path.expanduser('~/donjon-vr/modeles'),exist_ok=True)
def export(path):
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(filepath=os.path.expanduser(path),export_format='GLB',use_selection=True)

# --- FEUILLU : tronc + 3 boules de feuillage ---
reset()
TR=mat('tronc',(0.34,0.22,0.12)); FEU=mat('feuille',(0.22,0.46,0.19)); FEU2=mat('feuille2',(0.28,0.54,0.24))
cyl(0.16,0.12,1.4,0.7,TR,seg=6)
ico(0.85,1.7,FEU,1,1.0); ico(0.6,2.35,FEU2,1,1.0); ico(0.5,1.55,FEU,1,1.15)
export('~/donjon-vr/modeles/arbre_feuillu.glb')
t1=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in bpy.data.objects if o.type=='MESH')

# --- CONIFERE : tronc court + 3 cones ---
reset()
TR=mat('tronc',(0.32,0.2,0.11)); PIN=mat('pin',(0.16,0.4,0.2)); PIN2=mat('pin2',(0.2,0.46,0.24))
cyl(0.14,0.11,0.9,0.45,TR,seg=6)
cyl(0.95,0.0,1.2,1.4,PIN,seg=8); cyl(0.72,0.0,1.05,2.05,PIN2,seg=8); cyl(0.5,0.0,0.9,2.65,PIN,seg=8)
export('~/donjon-vr/modeles/arbre_conifere.glb')
t2=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in bpy.data.objects if o.type=='MESH')
print("FEUILLU tris:",t1,"· CONIFERE tris:",t2)

# --- APERCU des deux ---
reset()
TR=mat('tronc',(0.34,0.22,0.12)); FEU=mat('feuille',(0.22,0.46,0.19)); FEU2=mat('f2',(0.28,0.54,0.24)); PIN=mat('pin',(0.16,0.4,0.2))
# feuillu a gauche
def feuillu(x):
    for o in [cyl(0.16,0.12,1.4,0.7,TR,6)]: o.location.x=x
    for (r,z,mm,sx) in [(0.85,1.7,FEU,1),(0.6,2.35,FEU2,1),(0.5,1.55,FEU,1.15)]:
        o=ico(r,z,mm,1,sx); o.location.x=x
def conif(x):
    o=cyl(0.14,0.11,0.9,0.45,TR,6); o.location.x=x
    for (r,z) in [(0.95,1.4),(0.72,2.05),(0.5,2.65)]:
        o=cyl(r,0,1.1,z,PIN,8); o.location.x=x
feuillu(-1.6); conif(1.6)
bpy.ops.mesh.primitive_plane_add(size=20,location=(0,0,0)); bpy.context.object.data.materials.append(mat('sol',(0.45,0.5,0.35)))
cam_d=bpy.data.cameras.new('C'); cam=bpy.data.objects.new('C',cam_d); bpy.context.scene.collection.objects.link(cam)
cam.location=(0,-7,2.5)
emp=bpy.data.objects.new('T',None); bpy.context.scene.collection.objects.link(emp); emp.location=(0,0,1.5)
c=cam.constraints.new('TRACK_TO'); c.target=emp; c.track_axis='TRACK_NEGATIVE_Z'; c.up_axis='UP_Y'
bpy.context.scene.camera=cam; sc=bpy.context.scene
sc.render.engine='BLENDER_WORKBENCH'; sc.display.shading.light='STUDIO'; sc.display.shading.color_type='MATERIAL'; sc.display.shading.show_shadows=True
sc.render.resolution_x=700; sc.render.resolution_y=500
sc.world=bpy.data.worlds.new('W'); sc.world.color=(0.6,0.75,0.95)
out=os.path.expanduser('~/donjon-vr/blender/apercu_arbres.png'); sc.render.filepath=out
bpy.ops.render.render(write_still=True); print("APERCU:",out)
