"""
基于实测分布，精确计算最佳阈值
实测 dot 值分布（角色区域）：
  0.0-0.1:  9.6%  (描边，纯黑，不受阈值影响)
  0.7-0.8:  8.0%
  0.8-0.9: 32.7%
  0.9-1.0: 47.8%

不含描边的话，表面值集中在 0.7-1.0。
想要约 35% 的表面进入阴影 -> 阈值应设在 0.7-0.8 之间
"""
import bpy
import numpy as np
import os

BASE = r"D:\C_Relocated\Users\13191\MultiTools\projects\chiikawa"
OUT = os.path.join(BASE, "renders")

body = bpy.data.objects.get("Chiikawa_Body")
mat = body.data.materials[0]
nt = mat.node_tree

clamp = next(n for n in nt.nodes if n.type == 'CLAMP')
em = next(n for n in nt.nodes if n.type == 'EMISSION')
ramp = next(n for n in nt.nodes if n.type == 'VALTORGB')

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 400
scene.render.resolution_y = 400
scene.render.film_transparent = False
scene.frame_set(1)

# 渲染 clamp 输出（真实 dot 值）
nt.links.new(clamp.outputs['Result'], em.inputs['Color'])
tmp = os.path.join(OUT, "_vals.png")
scene.render.filepath = tmp
bpy.ops.render.render(write_still=True)

img = bpy.data.images.load(tmp)
w, h = img.size
px = np.array(img.pixels[:]).reshape(h, w, 4)[:, :, :3]
v = px.mean(axis=2)
bpy.data.images.remove(img)

# 只看角色表面（排除描边的近黑值）
surface = v[v > 0.15]
print("=" * 58)
print("表面 dot 值分布（已排除描边）")
print("=" * 58)
print(f"  样本数: {surface.size}")
print(f"  最小={surface.min():.3f} 最大={surface.max():.3f} 均值={surface.mean():.3f}")

print("\n  各阈值下的阴影占比:")
best = None
for thr in np.arange(0.55, 1.01, 0.05):
    below = (surface < thr).mean() * 100
    mark = ""
    if 28 <= below <= 42:
        mark = "  <<< 理想"
        if best is None:
            best = thr
    print(f"    阈值 {thr:.2f}: 阴影 {below:5.1f}%{mark}")

print("\n" + "=" * 58)
if best:
    print(f"推荐阈值 = {best:.2f}")
else:
    # 找最接近 35% 的
    cands = [(np.arange(0.55,1.01,0.05)[i], (surface < t).mean()*100)
             for i, t in enumerate(np.arange(0.55,1.01,0.05))]
    b = min(cands, key=lambda x: abs(x[1]-35))
    print(f"最接近 35% 的阈值 = {b[0]:.2f} (阴影 {b[1]:.1f}%)")
    best = b[0]
print("=" * 58)

os.remove(tmp)
