"""渲染 v11 完整动画序列（144 帧）"""
import bpy
import os

BASE = r"D:\C_Relocated\Users\13191\MultiTools\projects\chiikawa"
FD = os.path.join(BASE, "renders", "v11_frames")
os.makedirs(FD, exist_ok=True)

sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
sc.render.image_settings.file_format = 'PNG'
sc.render.image_settings.color_mode = 'RGBA'
sc.render.film_transparent = True
sc.render.resolution_x = 1080
sc.render.resolution_y = 1080
sc.render.resolution_percentage = 100
sc.render.filepath = os.path.join(FD, "f_")
sc.frame_start = 1
sc.frame_end = 144
sc.render.fps = 24
try:
    sc.view_settings.view_transform = 'Standard'
except Exception:
    pass

print(f"渲染 {sc.frame_start}-{sc.frame_end} 帧 -> {FD}")
bpy.ops.render.render(animation=True)

files = sorted(f for f in os.listdir(FD) if f.endswith('.png'))
print(f"完成，共 {len(files)} 帧")
if files:
    print(f"  {files[0]} ... {files[-1]}")
