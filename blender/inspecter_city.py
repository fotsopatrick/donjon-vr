import bpy, os
p=os.path.expanduser('~/Desktop/City Street.blend')
print("EXISTE:", os.path.exists(p), "TAILLE_Mo:", round(os.path.getsize(p)/1e6,1) if os.path.exists(p) else 0)
bpy.ops.wm.open_mainfile(filepath=p)
objs=[o for o in bpy.data.objects if o.type=='MESH']
tot=sum(sum(len(pg.vertices)-2 for pg in o.data.polygons) for o in objs)
print("OBJETS_MESH:", len(objs), "TRIANGLES_TOTAL:", tot)
print("IMAGES:", len(bpy.data.images), "MATERIAUX:", len(bpy.data.materials))
# bornes de la scène
import mathutils
mn=[1e9]*3; mx=[-1e9]*3
for o in objs:
    for v in o.bound_box:
        w=o.matrix_world @ mathutils.Vector(v)
        for i in range(3): mn[i]=min(mn[i],w[i]); mx[i]=max(mx[i],w[i])
print("DIMENSIONS:", [round(mx[i]-mn[i],1) for i in range(3)])
