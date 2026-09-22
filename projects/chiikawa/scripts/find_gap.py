"""
找「空档」：光照值分布是双峰的，阈值应落在峰之间
"""
import bpy
import numpy as np
import os
import sys
import math

BASE = r"D:\C_Relocated\Users\13191\MultiTools\projects\chiikawa"
sys.path.insert(0, os.path.join(BASE, "scripts"))
OUT = os.path.join(BASE, "renders")
from apply_toon_v9 import make_toon_material_v9

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0,0,0),
                                     segments=64, ring_count=32)
sp = bpy.context.active_object
sp.scale = (1.08, 1.0, 0.96)
bpy.context.view_layer.objects.active = sp
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
bpy.ops.object.shade_smooth()

mat = make_toon_material_v9("CAL", (0.9,0.88,0.82))
sp.data.materials.append(mat)

bpy.ops.object.light_add(type='SUN', location=(-5,-1,1))
sun = bpy.context.active_object
sun.data.energy = 5.0
sun.rotation_euler = (math.radians(75), 0, math.radians(-85))

world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs['Color'].default_value = (1,1,1,1)
    bg.inputs['Strength'].default_value = 0.15

bpy.ops.object.camera_add(location=(0,-5,0), rotation=(1.5708,0,0))
bpy.context.scene.camera = bpy.context.active_object

sc = bpy.context.scene
sc.render.engine='BLENDER_EEVEE'
sc.render.resolution_x=400; sc.render.resolution_y=400
sc.render.film_transparent=False
try: sc.view_settings.view_transform='Standard'
except: pass

nt = mat.node_tree
bw = next(n for n in nt.nodes if n.type=='RGBTOBW')
em = next(n for n in nt.nodes if n.type=='EMISSION')
nt.links.new(bw.outputs['Val'], em.inputs['Color'])

tmp = os.path.join(OUT, "_gap.png")
sc.render.filepath = tmp
bpy.ops.render.render(write_still=True)

img = bpy.data.images.load(tmp)
w,h = img.size
v = np.array(img.pixels[:]).reshape(h,w,4)[:,:,:3].mean(axis=2)
bpy.data.images.remove(img)
s = v.ravel()
s = s[(s>0.02)&(s<0.985)]

print("=" * 62)
print("光照值精细分布（找双峰之间的空档）")
print("=" * 62)
print(f"  样本={s.size}  范围 {s.min():.3f}~{s.max():.3f}  "
      f"均值 {s.mean():.3f} 标准差 {s.std():.3f}")

hist, edges = np.histogram(s, bins=40, range=(0,1))
print("\n  精细直方图（每格 0.025）:")
for i,cnt in enumerate(hist):
    pct = cnt/s.size*100
    if pct > 0.3:
        bar = '#'*int(pct/1.5)
        print(f"    {edges[i]:.3f}-{edges[i+1]:.3f}: {pct:5.2f}% {bar}")

# 找最低谷
mn = min(range(1,39), key=lambda i: hist[i])
print(f"\n  最低谷: {edges[mn]:.3f}~{edges[mn+1]:.3f} (占 {hist[mn]/s.size*100:.2f}%)")
print(f"  >>> 推荐阈值 = {(edges[mn]+edges[mn+1])/2:.3f}")

os.remove(tmp)
print("=" * 62)
