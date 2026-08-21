import bpy, math, os, mathutils
V=mathutils.Vector
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete()
for m in list(bpy.data.materials): bpy.data.materials.remove(m)
def mat(nom,rgba,rough=0.7,metal=0.0):
    if len(rgba)==3: rgba=(*rgba,1.0)
    m=bpy.data.materials.new(nom); m.use_nodes=True
    b=m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value=rgba; b.inputs['Roughness'].default_value=rough; b.inputs['Metallic'].default_value=metal
    m.diffuse_color=rgba; return m
OS=mat('os',(0.88,0.85,0.76)); OSF=mat('os_f',(0.72,0.69,0.60)); SOMB=mat('sombre',(0.08,0.07,0.07))
col=[]
def os_(a,b,r=0.12,m=OS):
    a=V(a); b=V(b); d=b-a; L=max(d.length,0.001)
    bpy.ops.mesh.primitive_cylinder_add(vertices=8,radius=r,depth=L)
    o=bpy.context.object; o.location=(a+b)/2
    o.rotation_mode='QUATERNION'; o.rotation_quaternion=V((0,0,1)).rotation_difference(d)
    o.data.materials.append(m); col.append(o); return o
def bille(p,r=0.16,m=OS):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=r,location=p)
    o=bpy.context.object; o.data.materials.append(m); col.append(o); return o
def boite(sx,sy,sz,p,m=OS,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(size=1,location=p); o=bpy.context.object
    o.scale=(sx/2,sy/2,sz/2); o.rotation_euler=rot; o.data.materials.append(m); col.append(o); return o

# ---- colonne vertébrale (cou -> queue), dragon debout ----
spine=[(4.6,0,2.3),(3.7,0,2.55),(2.7,0,2.45),(1.4,0,2.35),(0,0,2.3),
       (-1.6,0,2.25),(-2.9,0,2.0),(-4.2,0,1.4),(-5.6,0,0.8),(-7.0,0,0.35)]
for i in range(len(spine)-1):
    os_(spine[i],spine[i+1],0.16 if i<7 else 0.10)
    bille(spine[i], 0.19 if i<7 else 0.12)
bille(spine[-1],0.09)

# ---- crâne allongé + mâchoire + cornes ----
hx=(5.5,0,2.25)
boite(0.9,0.7,0.7, (5.35,0,2.35), OS)               # crâne
boite(1.1,0.45,0.35,(6.25,0,2.2), OS)               # museau
boite(1.0,0.42,0.16,(6.2,0,1.98), OSF)              # mâchoire inférieure
for sy in (-0.22,0.22): bille((6.7+0,sy,2.28),0.05,SOMB)   # narines
for sy in (-0.24,0.24): bille((5.5,sy,2.55),0.09,SOMB)     # orbites (yeux vides)
for sy in (-0.28,0.28): os_((5.2,sy,2.7),(4.7,sy,3.4),0.05,OS)  # cornes
# dents
for i in range(6):
    x=5.9+i*0.14
    os_((x,-0.2,2.15),(x,-0.2,2.02),0.02,OS); os_((x,0.2,2.15),(x,0.2,2.02),0.02,OS)

# ---- côtes (torse : entre épaules et hanches) ----
for sp in spine[2:7]:
    for side in (-1,1):
        p0=V(sp); 
        pts=[p0,p0+V((0,side*0.5,-0.4)),p0+V((0.05,side*0.95,-1.1)),p0+V((0.1,side*0.8,-1.9))]
        for i in range(len(pts)-1): os_(pts[i],pts[i+1],0.05,OSF)
# sternum
os_((2.4,0,0.5),(-1.6,0,0.5),0.06,OSF)

# ---- pattes (2 avant aux épaules, 2 arrière aux hanches) ----
def patte(base, avant=True):
    bx,by,bz=base
    hip=V((bx,by,bz))
    knee=V((bx+(0.4 if avant else -0.4), by, 1.1))
    foot=V((bx+(0.6 if avant else -0.5), by, 0.0))
    os_(hip,knee,0.13); os_(knee,foot,0.11); bille(knee,0.15)
    for tx in (-0.18,0,0.18):                          # orteils/griffes
        os_(foot,(foot.x+0.35,foot.y+tx,0.0),0.05,OS)
for side in (-1,1):
    patte((2.4, side*0.75, 2.2), True)                 # avant
    patte((-2.6, side*0.8, 1.9), False)                # arrière

# ---- ailes (os seulement, déployées) ----
def aile(side):
    sh=V((2.5, side*0.5, 2.7))                          # épaule
    elb=V((2.0, side*2.2, 4.0))                         # coude
    wr=V((1.0, side*3.6, 4.6))                          # poignet
    os_(sh,elb,0.12); os_(elb,wr,0.10); bille(elb,0.12); bille(wr,0.10)
    for k,tip in enumerate([(-1.5,side*5.8,4.2),(-0.5,side*6.0,3.4),(0.5,side*5.6,2.6),(1.3,side*4.8,2.0)]):
        os_(wr,V(tip),0.06,OS)                          # doigts d'aile
for side in (-1,1): aile(side)

# ---- socle sombre (diorama) ----
boite(9.5,4.0,0.3,(-1.0,0,-0.15), SOMB)

# EXPORT
bpy.ops.object.select_all(action='DESELECT')
for o in col: o.select_set(True)
bpy.context.view_layer.objects.active=col[0]
os.makedirs(os.path.expanduser('~/donjon-vr/modeles'),exist_ok=True)
glb=os.path.expanduser('~/donjon-vr/modeles/dragon_squelette.glb')
bpy.ops.export_scene.gltf(filepath=glb,export_format='GLB',use_selection=True)
tris=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in col if o.type=='MESH')
print("TRIANGLES:",tris); print("GLB:",glb,os.path.getsize(glb))

# RENDU
bpy.ops.mesh.primitive_plane_add(size=60,location=(0,0,-0.32)); bpy.context.object.data.materials.append(mat('sol',(0.14,0.15,0.17)))
cam_d=bpy.data.cameras.new('C'); cam=bpy.data.objects.new('C',cam_d); bpy.context.scene.collection.objects.link(cam)
cam.location=(9,-13,5.5)
emp=bpy.data.objects.new('T',None); bpy.context.scene.collection.objects.link(emp); emp.location=(0,0,2)
c=cam.constraints.new('TRACK_TO'); c.target=emp; c.track_axis='TRACK_NEGATIVE_Z'; c.up_axis='UP_Y'
bpy.context.scene.camera=cam; sc=bpy.context.scene
sc.render.engine='BLENDER_WORKBENCH'; sc.display.shading.light='STUDIO'; sc.display.shading.color_type='MATERIAL'
sc.display.shading.show_shadows=True; sc.display.shading.show_cavity=True
sc.render.resolution_x=1000; sc.render.resolution_y=680
sc.world=bpy.data.worlds.new('W'); sc.world.color=(0.10,0.11,0.14)
out=os.path.expanduser('~/donjon-vr/blender/apercu_dragon.png'); sc.render.filepath=out
bpy.ops.render.render(write_still=True); print("APERCU:",out)
