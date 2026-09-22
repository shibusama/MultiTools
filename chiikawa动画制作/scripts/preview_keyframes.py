"""
渲染关键帧预览（第 1、18、54 帧）—— 快速验证动画是否正确
"""
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

for f in [1, 18, 36, 54]:
    scene.frame_set(f)
    scene.render.filepath = os.path.join(OUT, f"keyframe_{f:03d}.png")
    bpy.ops.render.render(write_still=True)
    print(f"  帧 {f} 已渲染")

print("关键帧预览完成")
