"""
阈值扫描：一次性找出最佳 ColorRamp 阈值
对每个候选阈值渲染一次，统计阴影占比，选出最接近目标(35%阴影)的
"""
import bpy
import numpy as np
import os

base = r"D:\C_Relocated\Users\13191\MultiTools\chiikawa动画制作"
out_dir = os.path.join(base, "renders")
os.makedirs(out_dir, exist_ok=True)

body = bpy.data.objects.get("Body")
mat = body.data.materials[0]
nt = mat.node_tree
ramp = next(n for n in nt.nodes if n.type == 'VALTORGB')
cr = ramp.color_ramp

# 用红蓝做标记便于统计
cr.elements[0].color = (1.0, 0.0, 0.0, 1.0)   # 红 = 阴影
cr.elements[1].color = (0.0, 0.0, 1.0, 1.0)   # 蓝 = 亮部

scene = bpy.context.scene
scene.render.resolution_x = 400
scene.render.resolution_y = 400

candidates = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.50, 0.60]

print("=" * 62)
print("阈值扫描（目标：阴影占比约 30~40%）")
print("=" * 62)
print(f"{'阈值':>6} | {'阴影%':>7} | {'亮部%':>7} | 评价")
print("-" * 62)

results = []
for thr in candidates:
    cr.elements[0].position = thr
    path = os.path.join(out_dir, f"_scan_{int(thr*100):03d}.png")
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)

    img = bpy.data.images.load(path)
    w, h = img.size
    px = np.array(img.pixels[:]).reshape(h, w, 4)
    r, g, b = px[:,:,0], px[:,:,1], px[:,:,2]
    red = ((r > 0.5) & (b < 0.3)).sum()
    blue = ((b > 0.5) & (r < 0.3)).sum()
    tot = red + blue
    if tot == 0:
        print(f"{thr:>6.2f} | {'--':>7} | {'--':>7} | 无有效像素")
        continue
    rp = red / tot * 100
    bp = blue / tot * 100
    results.append((thr, rp, bp))

    # 评价
    if rp < 5:
        note = "几乎全亮 ✗"
    elif rp > 70:
        note = "几乎全暗 ✗"
    elif 25 <= rp <= 45:
        note = "★ 理想区间"
    else:
        note = "可用"
    print(f"{thr:>6.2f} | {rp:>6.1f}% | {bp:>6.1f}% | {note}")

    bpy.data.images.remove(img)

print("-" * 62)

# 选最优
best = None
for thr, rp, bp in results:
    if 25 <= rp <= 45:
        if best is None or abs(rp - 35) < abs(best[1] - 35):
            best = (thr, rp, bp)

print("\n" + "=" * 62)
if best:
    print(f"✓ 推荐阈值 = {best[0]:.2f}  (阴影占 {best[1]:.1f}%)")
else:
    print("未找到理想阈值，看上面表格选最接近 35% 阴影的")
    if results:
        b = min(results, key=lambda x: abs(x[1] - 35))
        print(f"  最接近的: 阈值={b[0]:.2f} 阴影={b[1]:.1f}%")
print("=" * 62)

# 清理临时文件
for thr, _, _ in results:
    p = os.path.join(out_dir, f"_scan_{int(thr*100):03d}.png")
    if os.path.exists(p):
        os.remove(p)
