import bpy, math, os
def mat(nom,rgba,rough=0.85):
    if len(rgba)==3: rgba=(*rgba,1.0)
    m=bpy.data.materials.new(nom); m.use_nodes=True
    b=m.node_tree.nodes.get('Principled BSDF'); b.inputs['Base Color'].default_value=rgba; b.inputs['Roughness'].default_value=rough
    m.diffuse_color=rgba; return m
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete()
for m in list(bpy.data.materials): bpy.data.materials.remove(m)
PEAU=mat('peau',(0.82,0.62,0.48)); TUN=mat('tunique',(0.35,0.45,0.28)); PANT=mat('pantalon',(0.28,0.22,0.16)); CHEV=mat('cheveux',(0.18,0.12,0.07)); CUIR=mat('cuir',(0.3,0.2,0.12))
col=[]
def boite(sx,sy,sz,p,m,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(size=1,location=p); o=bpy.context.object
    o.scale=(sx/2,sy/2,sz/2); o.rotation_euler=rot; o.data.materials.append(m); col.append(o); return o
def cyl(r,d,p,m,seg=8,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=seg,radius=r,depth=d,location=p); o=bpy.context.object
    o.rotation_euler=rot; o.data.materials.append(m); col.append(o); return o
# jambes
for sx in (-0.13,0.13): cyl(0.11,0.85,(sx,0,0.42),PANT,7); boite(0.22,0.30,0.12,(sx,0.04,0.03),CUIR)
# torse (tunique)
boite(0.5,0.28,0.62,(0,0,1.05),TUN)
boite(0.52,0.30,0.12,(0,0,0.78),CUIR)   # ceinture
# bras
for sx in (-0.31,0.31): cyl(0.075,0.62,(sx,0.02,0.98),TUN,7); cyl(0.07,0.16,(sx,0.02,0.66),PEAU,7)  # manche + main
# cou + tete
cyl(0.07,0.1,(0,0,1.42),PEAU,7)
boite(0.26,0.26,0.30,(0,0,1.6),PEAU)
boite(0.28,0.28,0.14,(0,0,1.74),CHEV)   # cheveux
boite(0.29,0.05,0.16,(0,0.14,1.66),CHEV,rot=(0.2,0,0))  # frange
for sy in (-0.07,0.07): boite(0.03,0.03,0.03,(sy,0.14,1.6),mat('oeil',(0.05,0.05,0.06)))
os.makedirs(os.path.expanduser('~/donjon-vr/modeles'),exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
glb=os.path.expanduser('~/donjon-vr/modeles/villageois.glb')
bpy.ops.export_scene.gltf(filepath=glb,export_format='GLB',use_selection=True)
tris=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in col if o.type=='MESH')
print("VILLAGEOIS tris:",tris,"·",os.path.getsize(glb),"o")
