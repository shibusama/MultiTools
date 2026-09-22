"""
精确定位：把 ColorRamp 输入（Clamp 输出）直接渲染出来看数值分布
"""
import bpy
import numpy as np
import os

BASE = r"D:\C_Relocated\Users\13191\MultiTools\projects\chiikawa"
OUT = os.path.join(BASE, "renders")

body = bpy.data.objects.get("Chiikawa_Body")
mat = body.data.materials[0]
nt = mat.node_tree

# 找节点
clamp = next(n for n in nt.nodes if n.type == 'CLAMP')
ramp = next(n for n in nt.nodes if n.type == 'VALTORGB')
out_node = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
em = next(n for n in nt.nodes if n.type == 'EMISSION')

# 把 clamp 输出直接接到 emission（跳过 ColorRamp）
nt.links.new(clamp.outputs['Result'], em.inputs['Color'])

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 400
scene.render.resolution_y = 400
scene.render.film_transparent = False
scene.frame_set(1)
tmp = os.path.join(OUT, "_dotvalue.png")
scene.render.filepath = tmp
bpy.ops.render.render(write_still=True)

img = bpy.data.images.load(tmp)
w, h = img.size
px = np.array(img.pixels[:]).reshape(h, w, 4)[:, :, :3]
v = px.mean(axis=2)

print("=" * 58)
print("Clamp 输出（即 ColorRamp 的输入）实际分布")
print("=" * 58)
c = v[h//3:2*h//3, w//3:2*w//3]
print(f"  最小={c.min():.3f} 最大={c.max():.3f} 均值={c.mean():.3f} 标准差={c.std():.3f}")

hist, edges = np.histogram(c, bins=10, range=(0, 1))
print("\n  直方图:")
for i, cnt in enumerate(hist):
    pct = cnt/c.size*100
    if pct > 0.5:
        print(f"    {edges[i]:.1f}-{edges[i+1]:.1f}: {pct:5.1f}% {'#'*int(pct/2)}")

print(f"\n  当前 ColorRamp 阈值 = 0.50")
below = (c < 0.50).sum()/c.size*100
print(f"  低于阈值(会判为阴影)的像素: {below:.1f}%")

if below < 5:
    print("\n  >>> 几乎没有像素低于阈值 -> 全图都是亮色 -> 看不出明暗")
    print("  >>> 修法：提高阈值（让更多像素落入阴影）")
elif below > 80:
    print("\n  >>> 绝大部分像素低于阈值 -> 全图暗")
    print("  >>> 修法：降低阈值")
else:
    print(f"\n  >>> 有 {below:.1f}% 阴影，比例尚可")

bpy.data.images.remove(img)
os.remove(tmp)
print("=" * 58)
