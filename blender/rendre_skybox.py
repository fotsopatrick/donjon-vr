import bpy, os, mathutils
p=os.path.expanduser('~/Desktop/City Street.blend')
bpy.ops.wm.open_mainfile(filepath=p)
objs=[o for o in bpy.data.objects if o.type=='MESH']
mn=[1e9]*3; mx=[-1e9]*3
for o in objs:
    for v in o.bound_box:
        w=o.matrix_world @ mathutils.Vector(v)
        for i in range(3): mn[i]=min(mn[i],w[i]); mx[i]=max(mx[i],w[i])
cx=(mn[0]+mx[0])/2; cy=(mn[1]+mx[1])/2; cz=mn[2]+4.0   # niveau rue
sc=bpy.context.scene
# --- ÉCLAIRAGE : ciel clair + soleil (la scène n'en avait pas) ---
wd=bpy.data.worlds.new('cielW'); sc.world=wd; wd.use_nodes=True
bg=wd.node_tree.nodes.get('Background'); bg.inputs[0].default_value=(0.55,0.66,0.86,1); bg.inputs[1].default_value=1.8
sun_d=bpy.data.lights.new('Sun',type='SUN'); sun_d.energy=4.5; sun_d.angle=0.09
sun=bpy.data.objects.new('Sun',sun_d); sc.collection.objects.link(sun); sun.rotation_euler=(0.85,0.15,0.6)
# --- CAMÉRA panoramique 360 ---
cam_d=bpy.data.cameras.new('Pano'); cam=bpy.data.objects.new('Pano',cam_d); sc.collection.objects.link(cam)
cam.location=(cx,cy,cz); cam.rotation_euler=(1.5708,0,0)
cam_d.type='PANO'
try: cam_d.panorama_type='EQUIRECTANGULAR'
except: cam_d.cycles.panorama_type='EQUIRECTANGULAR'
sc.camera=cam
# --- RENDU ---
sc.render.engine='CYCLES'; sc.cycles.device='CPU'; sc.cycles.samples=48; sc.cycles.use_denoising=True
try: sc.view_settings.view_transform='Standard'
except: pass
sc.render.resolution_x=2048; sc.render.resolution_y=1024
sc.render.image_settings.file_format='PNG'
out=os.path.expanduser('~/donjon-vr/skybox/city_pano.png'); os.makedirs(os.path.dirname(out),exist_ok=True)
sc.render.filepath=out
print("RENDU_START centre=",round(cx,1),round(cy,1),round(cz,1))
bpy.ops.render.render(write_still=True)
print("SKYBOX_OK:", out, os.path.getsize(out) if os.path.exists(out) else 0)
