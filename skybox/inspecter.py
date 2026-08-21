import bpy
print("=== SCENES ===")
for sc in bpy.data.scenes: print(" scene:", sc.name)
objs=[o for o in bpy.data.objects]
print("nb objets:", len(objs))
cams=[o for o in objs if o.type=='CAMERA']
print("cameras:", [ (c.name, tuple(round(v,2) for v in c.location)) for c in cams])
# bornes globales (approx via origines)
import mathutils
mn=[1e9]*3; mx=[-1e9]*3
for o in objs:
    if o.type in ('MESH',):
        x,y,z=o.location
        for i,v in enumerate((x,y,z)):
            mn[i]=min(mn[i],v); mx[i]=max(mx[i],v)
print("bbox min approx:", [round(v,1) for v in mn])
print("bbox max approx:", [round(v,1) for v in mx])
print("centre approx:", [round((mn[i]+mx[i])/2,1) for i in range(3)])
print("=== FIN ===")
