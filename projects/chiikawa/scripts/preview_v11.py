"""渲染 v11 关键姿势预览（跳跃各阶段）"""
import bpy
import os

BASE = r"D:\C_Relocated\Users\13191\MultiTools\projects\chiikawa"
OUT = os.path.join(BASE, "renders", "v11_preview")
os.makedirs(OUT, exist_ok=True)

sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
sc.render.image_settings.file_format = 'PNG'
sc.render.resolution_x = 480
sc.render.resolution_y = 480
sc.render.film_transparent = False
try:
    sc.view_settings.view_transform = 'Standard'
except Exception:
    pass

# 跳跃各阶段：蓄力/起跳/顶点/下落/落地/回弹
poses = [20, 32, 44, 64, 74, 94]
for f in poses:
    sc.frame_set(f)
    sc.render.filepath = os.path.join(OUT, f"pose_{f:03d}.png")
    bpy.ops.render.render(write_still=True)
    print(f"  frame {f}")

print("done")
