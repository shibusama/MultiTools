"""
决定性测试：Geometry.Normal 到底输出了什么？
把 Normal 直接接到 Emission，渲染出来看颜色
球体表面法线应该是彩色的（XYZ -> RGB），能直接看出法线空间
"""
import bpy
import numpy as np
import os

BASE = r"D:\C_Relocated\Users\13191\MultiTools\projects\chiikawa"
OUT = os.path.join(BASE, "renders")

body = bpy.data.objects.get("Chiikawa_Body")
mat = body.data.materials[0]
nt = mat.node_tree

geo = next(n for n in nt.nodes if n.type == 'NEW_GEOMETRY')
em = next(n for n in nt.nodes if n.type == 'EMISSION')
out_node = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')

# Normal 直接输出
nt.links.new(geo.outputs['Normal'], em.inputs['Color'])

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 400
scene.render.resolution_y = 400
scene.render.film_transparent = False
scene.frame_set(1)
tmp = os.path.join(OUT, "_normal.png")
scene.render.filepath = tmp
bpy.ops.render.render(write_still=True)

img = bpy.data.images.load(tmp)
w, h = img.size
px = np.array(img.pixels[:]).reshape(h, w, 4)
rgb = px[:, :, :3]

# 角色中心区域
c = rgb[h//3:2*h//3, w//3:2*w//3].reshape(-1, 3)
# 排除黑色（描边/背景）
mask = c.sum(axis=1) > 0.1
c = c[mask]

print("=" * 58)
print("Geometry.Normal 输出分析")
print("=" * 58)
if c.size:
    print(f"  样本数: {len(c)}")
    print(f"  R 范围: {c[:,0].min():.3f} ~ {c[:,0].max():.3f}  均值 {c[:,0].mean():.3f}")
    print(f"  G 范围: {c[:,1].min():.3f} ~ {c[:,1].max():.3f}  均值 {c[:,1].mean():.3f}")
    print(f"  B 范围: {c[:,2].min():.3f} ~ {c[:,2].max():.3f}  均值 {c[:,2].mean():.3f}")
    print(f"\n  法线向量模长均值: {np.linalg.norm(c, axis=1).mean():.3f}")

    # 判断：如果 B 通道（Z 法线）接近 1，说明法线朝向相机
    # 相机在 -Y，所以应该有明显的负 Y 分量... 但法线转RGB后负值被截断为0
    print("\n  解读:")
    if c[:,2].mean() > 0.7:
        print("    Z 分量高 -> 法线主要朝上/朝相机方向")
    if c[:,0].mean() > 0.5:
        print("    X 分量偏高")
    if c[:,1].mean() < 0.3:
        print("    Y 分量低 -> 负值被截断（法线朝 -Y 即朝向相机）")

    # 关键：计算法线·相机方向
    # 相机方向 (0,-1,0)。法线朝相机时 ny<0，转 RGB 后被截为 0
    # 所以直接用 RGB 判断会丢信息
    print("\n  ⚠ 注意：法线的负值在转 RGB 时被截断为 0")
    print("     这会让明暗计算丢失一半信息！")

bpy.data.images.remove(img)
os.remove(tmp)
print("=" * 58)
