import bpy, math, os
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete()
for m in list(bpy.data.materials): bpy.data.materials.remove(m)
def mat(nom,rgba,rough=0.5,metal=0.3):
    if len(rgba)==3: rgba=(*rgba,1.0)
    m=bpy.data.materials.new(nom); m.use_nodes=True
    b=m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value=rgba; b.inputs['Roughness'].default_value=rough; b.inputs['Metallic'].default_value=metal
    m.diffuse_color=rgba; return m
ARM=mat('armure',(0.13,0.16,0.26),0.45,0.6); ARM2=mat('armure2',(0.09,0.11,0.18),0.5,0.6)
OR=mat('or',(0.86,0.68,0.24),0.3,0.9); CAPE=mat('cape',(0.52,0.07,0.07),0.7,0.0); CUIR=mat('cuir',(0.09,0.09,0.11),0.7,0.1)
LAME=mat('lame',(0.62,0.66,0.72),0.25,0.9)
col=[]
def boite(sx,sy,sz,p,m,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(size=1,location=p); o=bpy.context.object
    o.scale=(sx/2,sy/2,sz/2); o.rotation_euler=rot; o.data.materials.append(m); col.append(o); return o
def cyl(r,d,p,m,seg=10,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=seg,radius=r,depth=d,location=p); o=bpy.context.object
    o.rotation_euler=rot; o.data.materials.append(m); col.append(o); return o
def sph(r,p,m):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=r,location=p); o=bpy.context.object
    o.data.materials.append(m); col.append(o); return o

# jambes
for sx in (-0.22,0.22):
    cyl(0.16,0.75,(sx,0,0.45),ARM)          # cuisse+tibia (une pièce stylisée)
    boite(0.34,0.30,0.20,(sx,0.05,0.05),ARM2)   # solerets (pieds)
    cyl(0.19,0.14,(sx,0.02,0.82),OR,rot=(math.pi/2,0,0))  # genouillères or
# bassin
boite(0.62,0.4,0.28,(0,0,1.02),ARM2)
boite(0.66,0.42,0.08,(0,0,0.9),OR)          # ceinturon or
# torse (plastron)
boite(0.72,0.44,0.66,(0,0,1.42),ARM)
boite(0.5,0.46,0.5,(0,0.02,1.45),ARM2)      # creux du plastron
for sz in (1.3,1.5,1.65):                    # liserés or
    boite(0.5,0.02,0.05,(0,0.24,sz),OR)
# épaulières
for sx in (-0.44,0.44):
    sph(0.18,(sx,0,1.6),ARM); cyl(0.2,0.05,(sx,0,1.64),OR,rot=(0,math.pi/2,0))
# bras
for sx in (-0.42,0.42):
    cyl(0.10,0.66,(sx,0.05,1.26),ARM)        # bras
    sph(0.11,(sx,0.08,0.96),ARM2)            # gantelets
# cou + casque (heaume)
cyl(0.12,0.12,(0,0,1.78),CUIR)
boite(0.34,0.36,0.4,(0,0,2.0),ARM)           # heaume
boite(0.36,0.05,0.06,(0,0.19,2.02),ARM2)     # fente des yeux
boite(0.05,0.16,0.34,(0,0.2,2.0),OR)         # crête/nasal or
cyl(0.025,0.2,(0,-0.05,2.28),OR)             # plumet tige
sph(0.09,(0,-0.05,2.42),CAPE)                # plumet rouge
# cape (plan rouge tombant verticalement dans le dos)
bpy.ops.mesh.primitive_plane_add(size=1,location=(0,-0.42,0.85)); cp=bpy.context.object
cp.scale=(0.72,1.35,1.0); cp.rotation_euler=(math.radians(80),0,0); cp.data.materials.append(CAPE); col.append(cp)
boite(0.9,0.1,0.14,(0,-0.16,1.62),OR)        # agrafe de cape
# épée plantée devant (garde, immobile)
cyl(0.05,1.5,(0.32,0.42,0.75),LAME)          # lame verticale
boite(0.36,0.08,0.06,(0.32,0.42,1.5),OR)     # garde
cyl(0.045,0.22,(0.32,0.42,1.62),CUIR)        # poignée
sph(0.07,(0.32,0.42,1.75),OR)               # pommeau

# EXPORT
bpy.ops.object.select_all(action='DESELECT')
for o in col: o.select_set(True)
bpy.context.view_layer.objects.active=col[0]
os.makedirs(os.path.expanduser('~/donjon-vr/modeles'),exist_ok=True)
glb=os.path.expanduser('~/donjon-vr/modeles/chevalier.glb')
bpy.ops.export_scene.gltf(filepath=glb,export_format='GLB',use_selection=True)
tris=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in col if o.type=='MESH')
print("TRIANGLES:",tris); print("GLB:",glb,os.path.getsize(glb))
# RENDU
bpy.ops.mesh.primitive_plane_add(size=20,location=(0,0,0)); bpy.context.object.data.materials.append(mat('sol',(0.2,0.2,0.22),0.9,0))
cam_d=bpy.data.cameras.new('C'); cam=bpy.data.objects.new('C',cam_d); bpy.context.scene.collection.objects.link(cam)
cam.location=(2.4,4.2,1.9)
emp=bpy.data.objects.new('T',None); bpy.context.scene.collection.objects.link(emp); emp.location=(0,0,1.2)
c=cam.constraints.new('TRACK_TO'); c.target=emp; c.track_axis='TRACK_NEGATIVE_Z'; c.up_axis='UP_Y'
bpy.context.scene.camera=cam; sc=bpy.context.scene
sc.render.engine='BLENDER_WORKBENCH'; sc.display.shading.light='STUDIO'; sc.display.shading.color_type='MATERIAL'
sc.display.shading.show_shadows=True; sc.display.shading.show_cavity=True
sc.render.resolution_x=640; sc.render.resolution_y=860
sc.world=bpy.data.worlds.new('W'); sc.world.color=(0.12,0.13,0.16)
out=os.path.expanduser('~/donjon-vr/blender/apercu_chevalier.png'); sc.render.filepath=out
bpy.ops.render.render(write_still=True); print("APERCU:",out)
