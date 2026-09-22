"""渲染预览图 —— 验证三渲二效果"""
import bpy
import os
import sys

out_dir = r"D:\C_Relocated\Users\13191\MultiTools\chiikawa动画制作\renders"
os.makedirs(out_dir, exist_ok=True)

scene = bpy.context.scene
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = os.path.join(out_dir, "preview_toon.png")
scene.render.resolution_x = 1080
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100

print(f"渲染引擎: {scene.render.engine}")
print(f"输出: {scene.render.filepath}")

bpy.ops.render.render(write_still=True)
print("渲染完成")
