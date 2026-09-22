"""
诊断 v4 三渲二为什么变平
检查：材质里的光照方向 vs 相机方向 vs 实际渲染结果
"""
import bpy
import numpy as np
import os

BASE = r"D:\C_Relocated\Users\13191\MultiTools\chiikawa动画制作"

print("=" * 58)
print("v4 三渲二诊断")
print("=" * 58)

# 1. 检查材质节点的光照方向
body = bpy.data.objects.get("Chiikawa_Body")
if body:
    for m in body.data.materials:
        if not m or not m.use_nodes:
            continue
        for n in m.node_tree.nodes:
            if n.type == 'VECTOR_MATH' and n.operation == 'DOT_PRODUCT':
                ld = n.inputs[1].default_value
                print(f"  {m.name} 光照方向: "
                      f"({ld[0]:.2f}, {ld[1]:.2f}, {ld[2]:.2f})")
            if n.type == 'VALTORGB':
                cr = n.color_ramp
                print(f"  {m.name} ColorRamp 阈值={cr.elements[0].position:.2f} "
                      f"阴影色={tuple(round(v,3) for v in cr.elements[0].color[:3])} "
                      f"亮色={tuple(round(v,3) for v in cr.elements[1].color[:3])}")

# 2. 检查相机
cam = bpy.data.objects.get("Camera")
if cam:
    print(f"\n  相机位置: {tuple(round(v,2) for v in cam.location)}")
    print(f"  相机旋转: {tuple(round(np.degrees(a),1) for a in cam.rotation_euler)}")
    print(f"  镜头: {cam.data.lens}mm")

# 3. 渲染一帧到临时文件，分析明暗分布
OUT = os.path.join(BASE, "renders")
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 400
scene.render.resolution_y = 400
scene.render.film_transparent = False
scene.frame_set(1)
tmp = os.path.join(OUT, "_diag_v4.png")
scene.render.filepath = tmp
bpy.ops.render.render(write_still=True)

img = bpy.data.images.load(tmp)
w, h = img.size
px = np.array(img.pixels[:]).reshape(h, w, 4)[:, :, :3]
lum = px.mean(axis=2)

# 角色区域（中心）
c = lum[h//3:2*h//3, w//3:2*w//3]
print(f"\n  角色区亮度: {c.min():.3f} ~ {c.max():.3f}  "
      f"均值={c.mean():.3f}  标准差={c.std():.3f}")

hist, edges = np.histogram(c, bins=10, range=(0, 1))
print(f"\n  亮度直方图:")
for i, cnt in enumerate(hist):
    pct = cnt/c.size*100
    if pct > 1:
        print(f"    {edges[i]:.1f}-{edges[i+1]:.1f}: {pct:5.1f}% {'#'*int(pct/2)}")

print(f"\n  标准差 {c.std():.4f}")
if c.std() < 0.05:
    print("  >>> 画面很平 -> 明暗分界没落在可见区")
    print("  >>> 光方向需要调整，或阈值要改")
else:
    print("  >>> 有明暗层次")

bpy.data.images.remove(img)
os.remove(tmp)
print("=" * 58)
