"""
单独验证 v8 材质：只用一个球测试，看 dot 分布是否合理
"""
import bpy
import numpy as np
import sys
import os

BASE = r"D:\C_Relocated\Users\13191\MultiTools\chiikawa动画制作"
sys.path.insert(0, os.path.join(BASE, "scripts"))
OUT = os.path.join(BASE, "renders")

from apply_toon_v8 import make_toon_material_v8

# 清场
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# 一个球
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, location=(0, 0, 0))
sphere = bpy.context.active_object
bpy.ops.object.shade_smooth()

mat = make_toon_material_v8("TEST_V8", (0.9, 0.9, 0.9), ramp_pos=0.5)
sphere.data.materials.append(mat)

# 相机
bpy.ops.object.camera_add(location=(0, -5, 0), rotation=(1.5708, 0, 0))
bpy.context.scene.camera = bpy.context.active_object

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 300
scene.render.resolution_y = 300
scene.render.film_transparent = False
try:
    scene.view_settings.view_transform = 'Standard'
except Exception:
    pass

# 先看 clamp 输出的分布（把 clamp 接 emission）
nt = mat.node_tree
clamp = next(n for n in nt.nodes if n.type == 'CLAMP')
em = next(n for n in nt.nodes if n.type == 'EMISSION')
nt.links.new(clamp.outputs['Result'], em.inputs['Color'])

tmp = os.path.join(OUT, "_v8dist.png")
scene.render.filepath = tmp
bpy.ops.render.render(write_still=True)

img = bpy.data.images.load(tmp)
w, h = img.size
v = np.array(img.pixels[:]).reshape(h, w, 4)[:, :, :3].mean(axis=2)
c = v[h//4:3*h//4, w//4:3*w//4]
vals = c[c > 0.01]   # 排除背景

print("=" * 58)
print("v8 材质：dot' 值分布（球体正面）")
print("=" * 58)
print(f"  样本数: {vals.size}")
print(f"  范围: {vals.min():.3f} ~ {vals.max():.3f}")
print(f"  均值: {vals.mean():.3f}  标准差: {vals.std():.3f}")

hist, edges = np.histogram(vals, bins=10, range=(0, 1))
print("\n  直方图:")
for i, cnt in enumerate(hist):
    pct = cnt / vals.size * 100
    if pct > 1:
        print(f"    {edges[i]:.1f}-{edges[i+1]:.1f}: {pct:5.1f}% {'#'*int(pct/2)}")

print(f"\n  阈值 0.50 时阴影占比: {(vals < 0.5).mean()*100:.1f}%")
print(f"  阈值 0.55 时阴影占比: {(vals < 0.55).mean()*100:.1f}%")

if vals.std() > 0.1:
    print("\n  >>> 分布有足够动态范围，三渲二可行")
else:
    print("\n  >>> 分布太窄")

bpy.data.images.remove(img)
os.remove(tmp)
print("=" * 58)
