"""
在真实角色上扫描光照角度，找到能让正面出现明暗分界的角度
同时用 Light Path 分离背景色（背景亮、照明暗）
"""
import bpy
import numpy as np
import os
import math

BASE = r"D:\C_Relocated\Users\13191\MultiTools\projects\chiikawa"
OUT = os.path.join(BASE, "renders")

body = bpy.data.objects.get("Chiikawa_Body")

# --- 修世界：背景用亮色，但照明用暗色 ---
world = bpy.context.scene.world
nt = world.node_tree
nt.nodes.clear()
out = nt.nodes.new('ShaderNodeOutputWorld')
mix = nt.nodes.new('ShaderNodeMixShader')
lp = nt.nodes.new('ShaderNodeLightPath')
bg_vis = nt.nodes.new('ShaderNodeBackground')
bg_lit = nt.nodes.new('ShaderNodeBackground')
bg_vis.inputs['Color'].default_value = (0.93, 0.93, 0.93, 1.0)
bg_vis.inputs['Strength'].default_value = 1.0
bg_lit.inputs['Color'].default_value = (1.0, 1.0, 1.0, 1.0)
bg_lit.inputs['Strength'].default_value = 0.03
nt.links.new(lp.outputs['Is Camera Ray'], mix.inputs['Fac'])
nt.links.new(bg_lit.outputs['Background'], mix.inputs[1])
nt.links.new(bg_vis.outputs['Background'], mix.inputs[2])
nt.links.new(mix.outputs['Shader'], out.inputs['Surface'])

sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x = 350
sc.render.resolution_y = 350
sc.render.film_transparent = False
try:
    sc.view_settings.view_transform = 'Standard'
except Exception:
    pass

sun = bpy.data.objects.get("KeyLight")

print("=" * 62)
print("角色光照角度扫描（阈值 0.153）")
print("=" * 62)
print(f"{'方位角':>7} | 阴影占比 | 说明")
print("-" * 62)

for yaw in [0, 30, 60, 90, 120, 150, 180]:
    sun.rotation_euler = (math.radians(72), 0, math.radians(yaw))
    tmp = os.path.join(OUT, f"_yaw{yaw}.png")
    sc.render.filepath = tmp
    bpy.ops.render.render(write_still=True)

    img = bpy.data.images.load(tmp)
    w, h = img.size
    px = np.array(img.pixels[:]).reshape(h, w, 4)[:, :, :3]
    lum = px.mean(axis=2)
    # 角色区：排除背景(0.93)和描边(<0.05)
    c = lum[h//4:3*h//4, w//4:3*w//4].ravel()
    surf = c[(c > 0.06) & (c < 0.90)]
    if surf.size < 100:
        print(f"{yaw:>7} | 无有效像素")
        bpy.data.images.remove(img)
        os.remove(tmp)
        continue
    # 分档：暗(0.1-0.5) vs 亮(0.5-0.9)
    dark = ((surf >= 0.12) & (surf < 0.50)).sum() / surf.size * 100
    bright = (surf >= 0.50).sum() / surf.size * 100
    print(f"{yaw:>7} | 暗{dark:5.1f}% 亮{bright:5.1f}% | 范围 {surf.min():.3f}~{surf.max():.3f}")
    bpy.data.images.remove(img)
    os.remove(tmp)

print("-" * 62)
print("目标：暗部占 25-45%")
print("=" * 62)
