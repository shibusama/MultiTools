"""
v10 标定：确定 gain 和 ramp_pos，使阴影占约 35%
"""
import bpy
import numpy as np
import os
import sys
import math

BASE = r"D:\C_Relocated\Users\13191\MultiTools\chiikawa动画制作"
sys.path.insert(0, os.path.join(BASE, "scripts"))
OUT = os.path.join(BASE, "renders")
from apply_toon_v10 import make_toon_material_v10

def build(gain):
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0,0,0),
                                         segments=64, ring_count=32)
    sp = bpy.context.active_object
    sp.scale = (1.08, 1.0, 0.96)
    bpy.context.view_layer.objects.active = sp
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bpy.ops.object.shade_smooth()

    mat = make_toon_material_v10("CAL", (0.9,0.88,0.82), gain=gain)
    sp.data.materials.append(mat)

    bpy.ops.object.light_add(type='SUN', location=(-5,-1,1))
    sun = bpy.context.active_object
    sun.data.energy = 3.0
    sun.rotation_euler = (math.radians(75), 0, math.radians(-85))

    world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs['Color'].default_value = (1,1,1,1)
        bg.inputs['Strength'].default_value = 0.02   # 低环境光

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
    clamp = next(n for n in nt.nodes if n.type=='CLAMP')
    em = next(n for n in nt.nodes if n.type=='EMISSION')
    nt.links.new(clamp.outputs['Result'], em.inputs['Color'])
    tmp = os.path.join(OUT, f"_g_{tag}.png")
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
print("gain 扫描（环境光 0.02，阳光 3.0）")
print("=" * 70)
for g in [2.0, 3.0, 4.0, 5.0]:
    mat, sc = build(g)
    s = getvals(mat, sc, str(g))
    print(f"\n  gain={g}: 范围 {s.min():.3f}~{s.max():.3f} "
          f"均值 {s.mean():.3f} 标准差 {s.std():.3f}")
    hist, edges = np.histogram(s, bins=10, range=(0,1))
    for i,cnt in enumerate(hist):
        pct=cnt/s.size*100
        if pct>2:
            print(f"      {edges[i]:.1f}-{edges[i+1]:.1f}: {pct:5.1f}% {'#'*int(pct/3)}")
    # 建议阈值
    for target in [35]:
        thr = np.percentile(s, target)
        print(f"      -> 阴影{target}% 对应阈值 {thr:.3f}")
print("=" * 70)
