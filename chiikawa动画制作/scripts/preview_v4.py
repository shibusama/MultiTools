"""渲染 v4 关键帧预览"""
import bpy
import os

BASE = r"D:\C_Relocated\Users\13191\MultiTools\chiikawa动画制作"
OUT = os.path.join(BASE, "renders")
os.makedirs(OUT, exist_ok=True)

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.image_settings.file_format = 'PNG'
scene.render.resolution_x = 600
scene.render.resolution_y = 600
scene.render.film_transparent = False
try:
    scene.view_settings.view_transform = 'Standard'
except Exception:
    pass

for f in [1, 24, 60]:
    scene.frame_set(f)
    scene.render.filepath = os.path.join(OUT, f"v4_keyframe_{f:03d}.png")
    bpy.ops.render.render(write_still=True)
    print(f"  frame {f} rendered")

print("v4 preview done")
