"""
v9 标定 v3：调灯光强度，让光照值分布铺在 0.3~0.9 之间
然后选阈值使阴影占约 35%
"""
import bpy
import numpy as np
import os
import sys

BASE = r"D:\C_Relocated\Users\13191\MultiTools\projects\chiikawa"
sys.path.insert(0, os.path.join(BASE, "scripts"))
OUT = os.path.join(BASE, "renders")
from apply_toon_v9 import make_toon_material_v9

def build(energy, angle_deg):
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0,0,0),
                                         segments=48, ring_count=24)
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
    import math
    sun.rotation_euler = (math.radians(angle_deg), 0, math.radians(-80))

    world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs['Color'].default_value = (1,1,1,1)
        bg.inputs['Strength'].default_value = 0.25   # 提高环境光底座

    bpy.ops.object.camera_add(location=(0,-5,0), rotation=(1.5708,0,0))
    bpy.context.scene.camera = bpy.context.active_object

    sc = bpy.context.scene
    sc.render.engine='BLENDER_EEVEE'
    sc.render.resolution_x=300; sc.render.resolution_y=300
    sc.render.film_transparent=False
    try: sc.view_settings.view_transform='Standard'
    except: pass
    return mat, sc

def measure(mat, sc, tag):
    nt = mat.node_tree
    bw = next(n for n in nt.nodes if n.type=='RGBTOBW')
    em = next(n for n in nt.nodes if n.type=='EMISSION')
    nt.links.new(bw.outputs['Val'], em.inputs['Color'])
    tmp = os.path.join(OUT, f"_lv_{tag}.png")
    sc.render.filepath = tmp
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(tmp)
    w,h = img.size
    v = np.array(img.pixels[:]).reshape(h,w,4)[:,:,:3].mean(axis=2)
    bpy.data.images.remove(img)
    s = v.ravel()
    s = s[(s>0.02)&(s<0.985)]
    os.remove(tmp)
    return s

print("=" * 68)
print("灯光参数扫描：目标让光照值分布铺开到 0.3~0.95")
print("=" * 68)
print(f"{'energy':>7} {'角度':>5} | {'均值':>6} {'标准差':>6} | 阴影占比 @阈值")
print("-" * 68)

best = None
for energy in [4.0, 6.0, 8.0, 10.0]:
    for ang in [50, 70]:
        mat, sc = build(energy, ang)
        s = measure(mat, sc, f"{energy}_{ang}")
        row = " ".join(f"{t}:{(s<t).mean()*100:3.0f}%" for t in [0.5,0.6,0.7,0.8])
        print(f"{energy:>7.1f} {ang:>5} | {s.mean():6.3f} {s.std():6.3f} | {row}")
        # 找最佳：阈值 0.6-0.7 之间阴影 30-40%
        for t in [0.6, 0.65, 0.7]:
            sh = (s<t).mean()*100
            if 30 <= sh <= 42:
                if best is None or abs(sh-36) < abs(best[3]-36):
                    best = (energy, ang, t, sh)
print("-" * 68)
if best:
    print(f"✓ 最佳: energy={best[0]}, 角度={best[1]}°, 阈值={best[2]} (阴影 {best[3]:.1f}%)")
else:
    print("未找到理想组合，需扩大扫描范围")
print("=" * 68)
