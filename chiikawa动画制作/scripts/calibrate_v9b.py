"""
v9 标定 v2：直接把光照值渲染成灰度图，统计分布
（不用红蓝标记，避免把描边算进去）
"""
import bpy
import numpy as np
import os
import sys

BASE = r"D:\C_Relocated\Users\13191\MultiTools\chiikawa动画制作"
sys.path.insert(0, os.path.join(BASE, "scripts"))
OUT = os.path.join(BASE, "renders")

from apply_toon_v9 import make_toon_material_v9

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0,0,0),
                                     segments=48, ring_count=24)
sp = bpy.context.active_object
sp.scale = (1.08, 1.0, 0.96)
bpy.context.view_layer.objects.active = sp
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
bpy.ops.object.shade_smooth()

mat = make_toon_material_v9("CAL", (0.9, 0.88, 0.82), ramp_pos=0.5)
sp.data.materials.append(mat)

# 灯光
bpy.ops.object.light_add(type='SUN', location=(-5, -1, 1))
sun = bpy.context.active_object
sun.data.energy = 3.0
sun.rotation_euler = (1.45, 0, -1.45)

world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs['Color'].default_value = (1,1,1,1)
    bg.inputs['Strength'].default_value = 0.10

bpy.ops.object.camera_add(location=(0,-5,0), rotation=(1.5708,0,0))
bpy.context.scene.camera = bpy.context.active_object

sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x = 300
sc.render.resolution_y = 300
sc.render.film_transparent = False
try: sc.view_settings.view_transform = 'Standard'
except: pass

# --- 把 BW 输出直接接 Emission，渲染光照值 ---
nt = mat.node_tree
bw = next(n for n in nt.nodes if n.type == 'RGBTOBW')
em = next(n for n in nt.nodes if n.type == 'EMISSION')
nt.links.new(bw.outputs['Val'], em.inputs['Color'])

tmp = os.path.join(OUT, "_lightval.png")
sc.render.filepath = tmp
bpy.ops.render.render(write_still=True)

img = bpy.data.images.load(tmp)
w,h = img.size
v = np.array(img.pixels[:]).reshape(h,w,4)[:,:,:3].mean(axis=2)
bpy.data.images.remove(img)

flat = v.ravel()
# 球体像素（排除背景：背景是均匀的世界色）
surface = flat[(flat > 0.02) & (flat < 0.985)]

print("=" * 62)
print("v9 真实光照值分布")
print("=" * 62)
print(f"  样本数: {surface.size}")
print(f"  范围: {surface.min():.4f} ~ {surface.max():.4f}")
print(f"  均值: {surface.mean():.4f}  标准差: {surface.std():.4f}")

hist, edges = np.histogram(surface, bins=20, range=(0,1))
print("\n  直方图:")
for i,cnt in enumerate(hist):
    pct = cnt/surface.size*100
    if pct>1: print(f"    {edges[i]:.2f}-{edges[i+1]:.2f}: {pct:5.1f}% {'#'*int(pct/2)}")

print("\n  各阈值阴影占比:")
for thr in np.arange(0.2, 1.0, 0.1):
    print(f"    {thr:.1f}: {(surface<thr).mean()*100:5.1f}%")

os.remove(tmp)
print("=" * 62)
