import bpy, bmesh, math, os

# ---------- reset ----------
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete()
for m in list(bpy.data.materials): bpy.data.materials.remove(m)

def mat(nom,rgba,rough=0.85,metal=0.0):
    if len(rgba)==3: rgba=(rgba[0],rgba[1],rgba[2],1.0)
    m=bpy.data.materials.new(nom); m.use_nodes=True
    b=m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value=rgba
    b.inputs['Roughness'].default_value=rough
    b.inputs['Metallic'].default_value=metal
    m.diffuse_color=rgba
    return m
PIERRE = mat('pierre',(0.82,0.79,0.72))
OMBRE  = mat('ombre', (0.16,0.15,0.15))   # fond sombre des arcades
CORN   = mat('corniche',(0.70,0.67,0.60))
OR     = mat('or',(0.86,0.68,0.24),rough=0.35,metal=0.85)
ROUGE  = mat('rideau',(0.52,0.07,0.07),rough=0.7)
BOIS   = mat('bois',(0.55,0.37,0.17))
TOIT   = mat('toit',(0.22,0.22,0.24))

col=[]
def cube(sx,sy,sz,x,y,z,m,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(size=1,location=(x,y,z))
    o=bpy.context.object; o.scale=(sx/2,sy/2,sz/2); o.rotation_euler=rot
    o.data.materials.append(m); col.append(o); return o
def cyl(r,d,x,y,z,m,seg=16,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=seg,radius=r,depth=d,location=(x,y,z))
    o=bpy.context.object; o.rotation_euler=rot; o.data.materials.append(m); col.append(o); return o

# ---------- un MODULE d'arcade (largeur X, hauteur Z, épaisseur Y ; face vers +Y) ----------
WMOD=2.3; PIL=0.4; ETH=2.7; EP=0.55; RARC=(WMOD-2*PIL)/2  # rayon d'arche
def etage(z0):
    # 2 piliers
    cube(PIL,EP,ETH, -(WMOD/2-PIL/2),0,z0+ETH/2, PIERRE)
    cube(PIL,EP,ETH,  (WMOD/2-PIL/2),0,z0+ETH/2, PIERRE)
    # fond sombre de l'arcade (en retrait)
    cube(WMOD-2*PIL,0.12,ETH-0.2, 0,-0.22,z0+ETH/2, OMBRE)
    # arc plein cintre : claveaux
    zt=z0+ETH-RARC
    for k in range(9):
        a=math.pi*k/8
        cube(0.34,EP,0.30, RARC*math.cos(a),0, zt+RARC*math.sin(a), PIERRE, rot=(0,-a+math.pi/2,0))
    # corniche
    cube(WMOD,EP+0.14,0.22, 0,0.02,z0+ETH+0.11, CORN)
def module():
    n0=len(col)
    etage(0.0); etage(ETH+0.22); etage(2*(ETH+0.22))
    # joindre les parts du module en un seul mesh
    parts=col[n0:]
    bpy.ops.object.select_all(action='DESELECT')
    for o in parts: o.select_set(True)
    bpy.context.view_layer.objects.active=parts[0]
    bpy.ops.object.join()
    m=bpy.context.object
    del col[n0:]; 
    return m
MOD=module()

# ---------- anneau elliptique d'arcades ----------
A,B=15.0,11.0; N=24
ring=[]
FRONT=range(N-2,N+1)  # secteurs laissés pour la façade (autour de theta ~ -90°→ on choisit le bas)
# on repère le secteur "avant" = celui le plus proche de -Y (theta=-pi/2)
front_i=set()
for i in range(N):
    th=2*math.pi*i/N - math.pi/2      # i=0 -> avant
    if i in (0,1,N-1): front_i.add(i); continue
    d=MOD.copy(); d.data=MOD.data.copy()
    bpy.context.collection.objects.link(d)
    d.location=(A*math.cos(th),B*math.sin(th),0)
    d.rotation_euler=(0,0,th-math.pi/2)
    ring.append(d); col.append(d)
bpy.data.objects.remove(MOD, do_unlink=True)

# ---------- socle + toit annulaire ----------
cyl(A+1.2,1.0,0,0,-0.5,CORN,seg=48); col[-1].scale=(1,B/A,1)   # socle elliptique
# corniche haute (anneau plat)
top=3*(ETH+0.22)
# colisée OUVERT au sommet : pas de couvercle — ce sont les corniches des arcades qui couronnent

# ---------- FAÇADE D'ENTRÉE (à l'avant, -Y) ----------
fy=-B-0.3
cube(6.4,1.6,top+1.2, 0,fy,(top+1.2)/2, PIERRE)                     # avant-corps
# grande ouverture sombre + rideau rouge
cube(3.0,0.5,top-0.4, 0,fy-0.7,(top-0.4)/2, OMBRE)
cube(2.4,0.2,top-1.0, 0,fy-1.0,(top-1.0)/2, ROUGE)                  # rideau
# colonnes de part et d'autre
for sx in (-2.2,2.2):
    cyl(0.45,top-0.2,sx,fy-0.8,(top-0.2)/2,PIERRE,seg=14)
# fronton triangulaire
bm=bmesh.new()
hw,hh,ep=3.6,1.9,1.7
vv=[bm.verts.new((-hw,-ep/2,0)),bm.verts.new((hw,-ep/2,0)),bm.verts.new((0,-ep/2,hh)),
    bm.verts.new((-hw, ep/2,0)),bm.verts.new((hw, ep/2,0)),bm.verts.new((0, ep/2,hh))]
bm.faces.new((vv[0],vv[1],vv[2])); bm.faces.new((vv[3],vv[5],vv[4]))
bm.faces.new((vv[0],vv[3],vv[4],vv[1])); bm.faces.new((vv[1],vv[4],vv[5],vv[2])); bm.faces.new((vv[2],vv[5],vv[3],vv[0]))
_me=bpy.data.meshes.new('fronton'); bm.to_mesh(_me); bm.free()
tri=bpy.data.objects.new('fronton',_me); bpy.context.collection.objects.link(tri)
tri.location=(0,fy,top+0.1); tri.data.materials.append(PIERRE); col.append(tri)
# horloge / rosace dorée
RZ=top-0.35; RY=fy-0.82
cyl(1.15,0.3,0,RY,RZ,OR,seg=28,rot=(math.pi/2,0,0))
cyl(0.85,0.34,0,RY-0.05,RZ,mat('cadran',(0.93,0.90,0.80)),seg=24,rot=(math.pi/2,0,0))
for h in range(12):                                                 # rayons de la rosace (encastrée dans le tympan)
    a=2*math.pi*h/12
    r=cube(0.08,0.1,0.9,0,RY-0.09,RZ,OR,rot=(0,a,0))
    r.location=(0.0, RY-0.09, RZ)
# échafaudages en bois (2 travées)
for sx in (-8.5,8.5):
    for zz in (1.4,4.2):
        cube(0.12,0.12,2.6,sx,fy+2.0,zz,BOIS)
        cube(2.4,0.12,0.12,sx,fy+2.0,zz+1.3,BOIS)
        cube(0.12,0.12,3.0,sx,fy+2.0,zz,BOIS,rot=(0,0.5,0))

# ---------- EXPORT ----------
bpy.ops.object.select_all(action='DESELECT')
for o in col: o.select_set(True)
bpy.context.view_layer.objects.active=col[0]
os.makedirs(os.path.expanduser('~/donjon-vr/modeles'),exist_ok=True)
glb=os.path.expanduser('~/donjon-vr/modeles/entree_colisee.glb')
bpy.ops.export_scene.gltf(filepath=glb,export_format='GLB',use_selection=True)
tris=0
for o in col:
    if o.type=='MESH': tris+=sum(len(p.vertices)-2 for p in o.data.polygons)
print("TRIANGLES:",tris)
print("GLB:",glb,os.path.getsize(glb),"octets")

# ---------- RENDU ----------
bpy.ops.mesh.primitive_plane_add(size=90,location=(0,0,-1)); bpy.context.object.data.materials.append(mat('sol',(0.30,0.34,0.30)))
cam_d=bpy.data.cameras.new('C'); cam=bpy.data.objects.new('C',cam_d); bpy.context.scene.collection.objects.link(cam)
cam.location=(0,-42,14);
emp=bpy.data.objects.new('T',None); bpy.context.scene.collection.objects.link(emp); emp.location=(0,0,5.5)
c=cam.constraints.new('TRACK_TO'); c.target=emp; c.track_axis='TRACK_NEGATIVE_Z'; c.up_axis='UP_Y'
bpy.context.scene.camera=cam
sc=bpy.context.scene
sc.render.engine='BLENDER_WORKBENCH'
sc.display.shading.light='STUDIO'; sc.display.shading.color_type='MATERIAL'
sc.display.shading.show_shadows=True; sc.display.shading.show_cavity=True
sc.render.resolution_x=1000; sc.render.resolution_y=700
sc.world=bpy.data.worlds.new('W'); sc.world.color=(0.53,0.70,0.92)
out=os.path.expanduser('~/donjon-vr/blender/apercu_colisee.png'); sc.render.filepath=out
bpy.ops.render.render(write_still=True)
print("APERCU:",out)
