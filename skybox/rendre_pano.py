# Rend la scène City Street en panorama équirectangulaire léger (skybox du jeu).
# Usage : blender -b "City Street.blend" -P rendre_pano.py -- <cx> <cy> <cz> <hauteur> <res>
import bpy, sys, math
argv = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
cx,cy,cz = (float(argv[0]),float(argv[1]),float(argv[2])) if len(argv)>=3 else (0.0,0.0,0.0)
haut = float(argv[3]) if len(argv)>=4 else 1.7
res  = int(argv[4]) if len(argv)>=5 else 2048
out  = '/home/orel/donjon-vr/assets/skybox/city-street.png'

sc = bpy.context.scene
# caméra panoramique équirectangulaire au point donné, regardant l'horizon
cam_data = bpy.data.cameras.new('PanoCam'); cam_data.type='PANO'
try: cam_data.panorama_type='EQUIRECTANGULAR'
except Exception: 
    try: cam_data.cycles.panorama_type='EQUIRECTANGULAR'
    except Exception: pass
cam = bpy.data.objects.new('PanoCam', cam_data)
sc.collection.objects.link(cam)
cam.location=(cx,cy,cz+haut); cam.rotation_euler=(math.radians(90),0,0)  # horizon
sc.camera = cam

sc.render.engine='CYCLES'
try:
    sc.cycles.device='CPU'; sc.cycles.samples=64
    sc.cycles.use_denoising=True
except Exception: pass
sc.render.resolution_x=res; sc.render.resolution_y=res//2
sc.render.resolution_percentage=100
sc.render.image_settings.file_format='PNG'
sc.render.filepath=out
print('RENDU pano ->', out, 'cam@', (cx,cy,cz+haut))
bpy.ops.render.render(write_still=True)
print('FINI', out)
