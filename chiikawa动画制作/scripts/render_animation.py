"""
渲染动画序列帧
输出 PNG 序列，之后用 ffmpeg 合成视频
"""
import bpy
import os

BASE = r"D:\C_Relocated\Users\13191\MultiTools\chiikawa动画制作"
FRAME_DIR = os.path.join(BASE, "renders", "frames")
os.makedirs(FRAME_DIR, exist_ok=True)

scene = bpy.context.scene

# 渲染设置
scene.render.engine = 'BLENDER_EEVEE'
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
scene.render.film_transparent = True      # 透明背景，便于后期
scene.render.resolution_x = 1080
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100
scene.render.filepath = os.path.join(FRAME_DIR, "frame_")

scene.frame_start = 1
scene.frame_end = 72
scene.render.fps = 24

try:
    scene.view_settings.view_transform = 'Standard'
except Exception:
    pass

print("=" * 60)
print("渲染动画序列帧")
print(f"  帧范围: {scene.frame_start} - {scene.frame_end}")
print(f"  输出: {FRAME_DIR}")
print(f"  分辨率: {scene.render.resolution_x}x{scene.render.resolution_y}")
print(f"  透明背景: {scene.render.film_transparent}")
print("=" * 60)

bpy.ops.render.render(animation=True)

# 统计
files = sorted([f for f in os.listdir(FRAME_DIR) if f.endswith('.png')])
print(f"\n渲染完成，共 {len(files)} 帧")
if files:
    print(f"  首帧: {files[0]}")
    print(f"  末帧: {files[-1]}")
print("=" * 60)
