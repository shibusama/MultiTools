"""
v9 阈值标定：用真实灯光 + v9 材质，扫描阈值找最佳分界
基于实测分布（0.31~0.95，主峰在 0.3-0.4）
"""
import bpy
import numpy as np
import os
import sys

BASE = r"D:\C_Relocated\Users\13191\MultiTools\chiikawa动画制作"
sys.path.insert(0, os.path.join(BASE, "scripts"))
OUT = os.path.join(BASE, "renders")

from apply_toon_v9 import make_toon_material_v9

# 清场
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# 用一个接近角色形状的球
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0,0,0), segments=48, ring_count=24)
sp = bpy.context.active_object
sp.scale = (1.08, 1.0, 0.96)
bpy.context.view_layer.objects.active = sp
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
bpy.ops.object.shade_smooth()

# 材质
mat = make_toon_material_v9("CAL", (0.9, 0.88, 0.82), ramp_pos=0.5)
sp.data.materials.append(mat)

# --- 真实灯光：左侧掠射（三渲二标准打光）---
bpy.ops.object.light_add(type='SUN', location=(-5, -1, 1))
sun = bpy.context.active_object
sun.name = "KeyLight"
sun.data.energy = 3.0
sun.rotation_euler = (1.45, 0, -1.45)   # 从左前方接近水平

# 世界环境光压低
world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs['Color'].default_value = (1,1,1,1)
    bg.inputs['Strength'].default_value = 0.10

# 相机
bpy.ops.object.camera_add(location=(0,-5,0), rotation=(1.5708,0,0))
bpy.context.scene.camera = bpy.context.active_object

sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x = 300
sc.render.resolution_y = 300
sc.render.film_transparent = False
try: sc.view_settings.view_transform = 'Standard'
except: pass

ramp = next(n for n in mat.node_tree.nodes if n.type == 'VALTORGB')
cc = ramp.color_ramp
# 用红蓝标记便于统计
cc.elements[0].color = (1,0,0,1)   # 红=阴影
cc.elements[1].color = (0,0,1,1)   # 蓝=亮部

print("=" * 62)
print("v9 阈值标定（真实灯光）")
print("=" * 62)
print(f"{'阈值':>6} | {'阴影%':>7} | {'亮部%':>7} | 评价")
print("-" * 62)

results = []
for thr in [0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.70]:
    cc.elements[0].position = thr
    tmp = os.path.join(OUT, "_cal.png")
    sc.render.filepath = tmp
    bpy.ops.render.render(write_still=True)

    img = bpy.data.images.load(tmp)
    w,h = img.size
    p = np.array(img.pixels[:]).reshape(h,w,4)[:,:,:3]
    r,g,b = p[:,:,0], p[:,:,1], p[:,:,2]
    red = ((r>0.4)&(r>b+0.2)).sum()
    blue = ((b>0.4)&(b>r+0.2)).sum()
    tot = red+blue
    bpy.data.images.remove(img)
    if tot < 100:
        print(f"{thr:>6.2f} | 无有效像素")
        continue
    rp, bp = red/tot*100, blue/tot*100
    results.append((thr, rp))
    note = "★ 理想" if 25<=rp<=45 else ("偏亮" if rp<25 else "偏暗")
    print(f"{thr:>6.2f} | {rp:>6.1f}% | {bp:>6.1f}% | {note}")

print("-" * 62)
if results:
    best = min(results, key=lambda x: abs(x[1]-35))
    print(f"\n✓ 推荐阈值 = {best[0]:.2f} (阴影 {best[1]:.1f}%)")
p = os.path.join(OUT, "_cal.png")
if os.path.exists(p): os.remove(p)
print("=" * 62)
