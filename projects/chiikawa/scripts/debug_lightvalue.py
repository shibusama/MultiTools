"""
终极诊断：直接逐像素采样 Shader to RGB 的输出值
方法：把 ColorRamp 输出直连到 Emission，渲染出「光照值图」
这样就能看到 Shader to RGB 真实输出的数值分布
"""
import bpy
import numpy as np
import os

base = r"D:\C_Relocated\Users\13191\MultiTools\projects\chiikawa"
out_dir = os.path.join(base, "renders")
os.makedirs(out_dir, exist_ok=True)

print("=" * 60)
print("终极诊断：Shader to RGB 原始输出值")
print("=" * 60)

# --- 把身体材质的 ColorRamp 替换成直接输出 ShaderToRGB ---
# 这样渲染出来的灰度图 = 每个像素的光照值
body = bpy.data.objects.get("Body")
mat = body.data.materials[0]
nt = mat.node_tree

s2rgb = None
ramp = None
out_node = None
for n in nt.nodes:
    if n.type == 'SHADERTORGB':
        s2rgb = n
    elif n.type == 'VALTORGB':
        ramp = n
    elif n.type == 'OUTPUT_MATERIAL':
        out_node = n

print(f"找到节点: ShaderToRGB={s2rgb is not None}, Ramp={ramp is not None}")

# 断开 Ramp，直连 ShaderToRGB -> Output（用 Emission 保证不受光照二次影响）
em = nt.nodes.new('ShaderNodeEmission')
em.location = (400, 200)
nt.links.new(s2rgb.outputs['Color'], em.inputs['Color'])
nt.links.new(em.outputs['Emission'], out_node.inputs['Surface'])

# 渲染这张「光照值图」
scene = bpy.context.scene
scene.render.filepath = os.path.join(out_dir, "debug_lightvalue.png")
scene.render.image_settings.file_format = 'PNG'
scene.render.resolution_x = 540
scene.render.resolution_y = 540
bpy.ops.render.render(write_still=True)

# --- 分析 ---
img = bpy.data.images.load(os.path.join(out_dir, "debug_lightvalue.png"))
w, h = img.size
px = np.array(img.pixels[:]).reshape(h, w, 4)
lum = px[:, :, :3].mean(axis=2)

# 中心区域（角色）
c = lum[h//4:3*h//4, w//4:3*w//4]
print(f"\n光照值分布（中心区）:")
print(f"  最小={c.min():.3f} 最大={c.max():.3f} 均值={c.mean():.3f} 标准差={c.std():.3f}")

hist, edges = np.histogram(c, bins=10, range=(0, 1))
print("\n  直方图:")
for i, cnt in enumerate(hist):
    pct = cnt / c.size * 100
    if pct > 0.5:
        print(f"    {edges[i]:.1f}-{edges[i+1]:.1f}: {pct:5.1f}% {'#'*int(pct/2)}")

print("\n" + "="*60)
print("解读：")
print("  如果值全部集中在高段(0.8-1.0) -> 光照饱和，暗部切不出来")
print("  如果有 0.3~0.8 的过渡带 -> 阈值设在此区间才能切开明暗")
print("="*60)
