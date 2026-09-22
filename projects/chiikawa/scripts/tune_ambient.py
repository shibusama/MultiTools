"""
关键调整：降低环境光，让「暗部」和「亮部」的数值拉开距离
现在暗部 0.41 / 亮部 0.9+，阈值无处可放。
把环境光从 0.15 降到 0.02，暗部应该降到 0.1 左右，中间就有空间了。
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

def build(ambient, energy, angle):
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
    sun.data.energy = energy
    sun.rotation_euler = (math.radians(angle), 0, math.radians(-85))

    world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs['Color'].default_value = (1,1,1,1)
        bg.inputs['Strength'].default_value = ambient

    bpy.ops.object.camera_add(location=(0,-5,0), rotation=(1.5708,0,0))
    bpy.context.scene.camera = bpy.context.active_object

    sc = bpy.context.scene
    sc.render.engine='BLENDER_EEVEE'
    sc.render.resolution_x=300; sc.render.resolution_y=300
    sc.render.film_transparent=False
    try: sc.view_settings.view_transform='Standard'
    except: pass
    return mat, sc

def getvals(mat, sc, tag):
    nt = mat.node_tree
    bw = next(n for n in nt.nodes if n.type=='RGBTOBW')
    em = next(n for n in nt.nodes if n.type=='EMISSION')
    nt.links.new(bw.outputs['Val'], em.inputs['Color'])
    tmp = os.path.join(OUT, f"_a_{tag}.png")
    sc.render.filepath = tmp
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(tmp)
    w,h = img.size
    v = np.array(img.pixels[:]).reshape(h,w,4)[:,:,:3].mean(axis=2)
    bpy.data.images.remove(img)
    os.remove(tmp)
    s = v.ravel()
    return s[(s>0.005)&(s<0.985)]

print("=" * 70)
print("环境光扫描：目标让暗部与亮部拉开，中间留出阈值空间")
print("=" * 70)
print(f"{'环境光':>7} {'阳光':>5} | {'暗部':>7} {'亮部':>7} {'间距':>7} | 建议阈值(35%阴影)")
print("-" * 70)

for amb in [0.02, 0.05, 0.10]:
    for en in [3.0, 5.0]:
        mat, sc = build(amb, en, 75)
        s = getvals(mat, sc, f"{amb}_{en}")
        # 找双峰
        lo = s[s < np.median(s)].mean() if (s<np.median(s)).any() else 0
        hi = s[s >= np.median(s)].mean() if (s>=np.median(s)).any() else 0
        gap = hi - lo
        # 35% 分位
        thr35 = np.percentile(s, 35)
        print(f"{amb:>7.2f} {en:>5.1f} | {lo:>7.3f} {hi:>7.3f} {gap:>7.3f} | "
              f"{thr35:.3f} -> 阴影35%")
print("-" * 70)
print("间距越大，明暗分界越清晰")
print("=" * 70)
