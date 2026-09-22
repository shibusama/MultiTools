"""
决定性测试：法线裁剪假说验证
如果负值被裁剪是根因，那么把法线先「重映射到 0-1」再点乘，应该能恢复信息。

方法：用 Separate XYZ 拆出法线分量，每个分量单独 +1 再 /2，
      重映射到 0-1 空间（负值变正），然后手工算点乘。
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

geo = next(n for n in nodes if n.type == 'NEW_GEOMETRY')
em = next(n for n in nodes if n.type == 'EMISSION')

# 拆法线分量
sep = nodes.new('ShaderNodeSeparateXYZ')
sep.location = (-400, -300)
links.new(geo.outputs['Normal'], sep.inputs['Vector'])

# 测试1：直接看 X 分量（不做任何处理）
links.new(sep.outputs['X'], em.inputs['Color'])

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 300
scene.render.resolution_y = 300
scene.render.film_transparent = False
scene.frame_set(1)

tmp = os.path.join(OUT, "_nx.png")
scene.render.filepath = tmp
bpy.ops.render.render(write_still=True)

img = bpy.data.images.load(tmp)
w, h = img.size
px = np.array(img.pixels[:]).reshape(h, w, 4)[:, :, 0]
c = px[h//3:2*h//3, w//3:2*w//3]
m = c[c > 0.01]

print("=" * 58)
print("法线 X 分量直接输出")
print("=" * 58)
print(f"  非零样本: {m.size}")
if m.size:
    print(f"  范围: {m.min():.4f} ~ {m.max():.4f}  均值 {m.mean():.4f}")
    # 球体左侧法线 nx<0，右侧 nx>0
    # 如果负值被裁剪，应该只有正值，均值偏正
    print(f"\n  如果负值被裁剪：所有值 >0，且左右不对称")
    print(f"  实际非零占比: {m.size/c.size*100:.1f}%")
    if m.size / c.size < 0.75:
        print(f"  >>> 约 {100-m.size/c.size*100:.0f}% 的像素为 0 -> 负值确实被裁剪")
    else:
        print(f"  >>> 大部分像素有值")

bpy.data.images.remove(img)
os.remove(tmp)
print("=" * 58)
