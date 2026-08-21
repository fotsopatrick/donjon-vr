import bpy, os, math
def mat(nom,rgba,rough=0.8):
    if len(rgba)==3: rgba=(*rgba,1.0)
    m=bpy.data.materials.new(nom); m.use_nodes=True
    b=m.node_tree.nodes.get('Principled BSDF'); b.inputs['Base Color'].default_value=rgba; b.inputs['Roughness'].default_value=rough
    m.diffuse_color=rgba; return m
def reset():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete()
    for m in list(bpy.data.materials): bpy.data.materials.remove(m)
def export(path):
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(filepath=os.path.expanduser(path),export_format='GLB',use_selection=True)
os.makedirs(os.path.expanduser('~/donjon-vr/modeles'),exist_ok=True)
def cyl(r,d,p,m,seg=6,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=seg,radius=r,depth=d,location=p); o=bpy.context.object
    o.rotation_euler=rot; o.data.materials.append(m); return o
def ico(r,p,m,sub=1,sz=1):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub,radius=r,location=p); o=bpy.context.object
    o.scale=(1,1,sz); o.data.materials.append(m); return o

def fleur(nom,coul):
    reset()
    VERT=mat('tige',(0.2,0.42,0.16)); COEUR=mat('coeur',(0.95,0.8,0.2)); PET=mat('petale',coul)
    cyl(0.02,0.5,(0,0,0.25),VERT,5)                         # tige
    for a in range(5):                                       # 5 pétales
        an=a*2*math.pi/5
        p=ico(0.09,(math.cos(an)*0.11,math.sin(an)*0.11,0.52),PET,1,0.4)
    ico(0.06,(0,0,0.52),COEUR,1,0.6)                        # coeur
    # 2 feuilles
    for s in (-1,1): ico(0.07,(s*0.07,0,0.28),VERT,1,0.25)
    export('~/donjon-vr/modeles/'+nom+'.glb')
fleur('fleur_jaune',(0.95,0.82,0.2)); fleur('fleur_rouge',(0.85,0.2,0.2)); fleur('fleur_violet',(0.6,0.3,0.75))

# champignon
reset()
PIED=mat('pied',(0.9,0.86,0.76)); CHAP=mat('chapeau',(0.8,0.15,0.12)); POIS=mat('pois',(0.98,0.98,0.95))
cyl(0.08,0.28,(0,0,0.14),PIED,7)
ico(0.22,(0,0,0.3),CHAP,1,0.55)
for a in range(4):
    an=a*2*math.pi/4; ico(0.03,(math.cos(an)*0.13,math.sin(an)*0.13,0.34),POIS,1,0.4)
export('~/donjon-vr/modeles/champignon.glb')

# touffe d'herbe
reset()
H1=mat('h1',(0.25,0.5,0.2)); H2=mat('h2',(0.3,0.56,0.24))
import random
for i in range(9):
    an=(i*0.7); r=0.02+ (i%3)*0.03
    o=cyl(0.02,0.28+ (i%3)*0.08,(math.cos(an)*r,math.sin(an)*r,0.16),H1 if i%2 else H2,4)
    o.rotation_euler=(0.15*math.cos(an),0.15*math.sin(an),0)
export('~/donjon-vr/modeles/herbe.glb')
print("NATURE OK",[os.path.getsize(os.path.expanduser('~/donjon-vr/modeles/'+n+'.glb')) for n in ['fleur_jaune','champignon','herbe']])
