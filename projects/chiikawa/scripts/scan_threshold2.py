"""
阈值扫描 v2 —— 修正统计逻辑
修正点：
1. 排除背景像素（背景是浅灰 R≈G≈B）
2. 红色判定放宽
3. 直接统计角色区域
"""
import bpy
import numpy as np
import os

base = r"D:\C_Relocated\Users\13191\MultiTools\projects\chiikawa"
out_dir = os.path.join(base, "renders")
os.makedirs(out_dir, exist_ok=True)

body = bpy.data.objects.get("Body")
mat = body.data.materials[0]
nt = mat.node_tree
ramp = next(n for n in nt.nodes if n.type == 'VALTORGB')
cr = ramp.color_ramp

cr.elements[0].color = (1.0, 0.0, 0.0, 1.0)
cr.elements[1].color = (0.0, 0.0, 1.0, 1.0)

scene = bpy.context.scene
scene.render.resolution_x = 400
scene.render.resolution_y = 400

candidates = [0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.70]

print("=" * 66)
print("阈值扫描 v2（统计修正：排除背景）")
print("=" * 66)
print(f"{'阈值':>6} | {'角色像素':>8} | {'阴影%':>7} | {'亮部%':>7} | 评价")
print("-" * 66)

results = []
for thr in candidates:
    cr.elements[0].position = thr
    path = os.path.join(out_dir, "_scan_tmp.png")
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)

    img = bpy.data.images.load(path)
    w, h = img.size
    px = np.array(img.pixels[:]).reshape(h, w, 4)
    r, g, b = px[:,:,0], px[:,:,1], px[:,:,2]

    # 角色区域 = 中心 50%
    cy, cx = h//2, w//2
    rs = slice(cy-h//4, cy+h//4)
    cs = slice(cx-w//4, cx+w//4)
    rr, gg, bb = r[rs, cs], g[rs, cs], b[rs, cs]

    # 红色（阴影）: R 明显大于 G 和 B
    red = ((rr > 0.4) & (rr > gg + 0.25) & (rr > bb + 0.25)).sum()
    # 蓝色（亮部）: B 明显大于 R 和 G
    blue = ((bb > 0.4) & (bb > rr + 0.25) & (bb > gg + 0.25)).sum()
    tot = red + blue

    if tot < 100:
        print(f"{thr:>6.2f} | {tot:>8d} | {'--':>7} | {'--':>7} | 角色像素太少")
        bpy.data.images.remove(img)
        continue

    rp, bp = red/tot*100, blue/tot*100
    results.append((thr, rp, bp, tot))

    if rp < 3:
        note = "几乎全亮"
    elif rp > 75:
        note = "几乎全暗"
    elif 25 <= rp <= 45:
        note = "★ 理想"
    else:
        note = "可用"
    print(f"{thr:>6.2f} | {tot:>8d} | {rp:>6.1f}% | {bp:>6.1f}% | {note}")

    bpy.data.images.remove(img)

print("-" * 66)

if results:
    best = min(results, key=lambda x: abs(x[1] - 33))
    print(f"\n✓ 推荐阈值 = {best[0]:.2f}  (阴影 {best[1]:.1f}% / 亮部 {best[2]:.1f}%)")
else:
    print("\n✗ 所有阈值下都没检测到角色像素，需要检查渲染设置")

# 清理
tmp = os.path.join(out_dir, "_scan_tmp.png")
if os.path.exists(tmp):
    os.remove(tmp)
print("=" * 66)
