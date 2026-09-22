"""
根因定位：渲染出 clamp 输出（dot 值），看真实分布落在哪
v5 材质链路：Normal -> SEPXYZ -> MAD*3 -> MUL*3 -> ADD*2 -> CLAMP -> RAMP
把 CLAMP 结果直接接 Emission，渲染成灰度图
"""
import bpy
import numpy as np
import os

BASE = r"D:\C_Relocated\Users\13191\MultiTools\chiikawa动画制作"
OUT = os.path.join(BASE, "renders")

body = bpy.data.objects.get("Chiikawa_Body")
mat = body.data.materials[0]
nt = mat.node_tree
nodes, links = nt.nodes, nt.links

clamp = next(n for n in nodes if n.type == 'CLAMP')
em = next(n for n in nodes if n.type == 'EMISSION')

# 跳过 ColorRamp，直接输出 clamp
links.new(clamp.outputs['Result'], em.inputs['Color'])

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 400
scene.render.resolution_y = 400
scene.render.film_transparent = False
scene.frame_set(1)
tmp = os.path.join(OUT, "_v5dot.png")
scene.render.filepath = tmp
bpy.ops.render.render(write_still=True)

img = bpy.data.images.load(tmp)
w, h = img.size
v = np.array(img.pixels[:]).reshape(h, w, 4)[:, :, :3].mean(axis=2)

# 全身角色表面（排除背景>0.96 和描边<0.05）
flat = v.ravel()
surface = flat[(flat > 0.05) & (flat < 0.96)]

print("=" * 60)
print("v5 材质：Clamp 输出（dot'）的真实分布")
print("=" * 60)
print(f"  样本数: {surface.size}")
print(f"  最小={surface.min():.4f} 最大={surface.max():.4f}")
print(f"  均值={surface.mean():.4f} 标准差={surface.std():.4f}")

hist, edges = np.histogram(surface, bins=20, range=(0, 1))
print("\n  直方图:")
for i, cnt in enumerate(hist):
    pct = cnt/surface.size*100
    if pct > 0.5:
        print(f"    {edges[i]:.2f}-{edges[i+1]:.2f}: {pct:5.1f}% {'#'*int(pct/2)}")

print(f"\n  各阈值下的阴影占比:")
for thr in np.arange(0.5, 1.0, 0.05):
    print(f"    {thr:.2f}: {(surface < thr).mean()*100:5.1f}%")

bpy.data.images.remove(img)
os.remove(tmp)
print("=" * 60)
