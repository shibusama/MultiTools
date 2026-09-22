"""
验证 v11 跳跃动画：量化各阶段的位置和形变
"""
import bpy
import numpy as np
import os

BASE = r"D:\C_Relocated\Users\13191\MultiTools\chiikawa动画制作"
OUT = os.path.join(BASE, "renders", "v11_preview")

def load(f):
    p = os.path.join(OUT, f"pose_{f:03d}.png")
    img = bpy.data.images.load(p)
    w, h = img.size
    a = np.array(img.pixels[:]).reshape(h, w, 4)[:, :, :3]
    bpy.data.images.remove(img)
    return a

print("=" * 66)
print("跳跃动画各阶段量化")
print("=" * 66)
print(f"{'帧':>5} {'阶段':>10} | {'中心Y':>7} {'宽度':>7} {'高度':>7} | 判定")
print("-" * 66)

labels = {20: "蓄力", 32: "起跳", 44: "顶点", 64: "下落", 74: "落地", 94: "回弹"}
data = {}

for f in [20, 32, 44, 64, 74, 94]:
    a = load(f)
    h, w = a.shape[:2]
    lum = a.mean(axis=2)
    # 角色 = 非背景（背景接近纯白）
    mask = lum < 0.93
    ys, xs = np.nonzero(mask)
    if len(ys) == 0:
        print(f"{f:>5} {labels[f]:>10} | 未检测到角色")
        continue
    # 图像坐标 y 向下，转成屏幕高度（越大越靠上）
    cy = h - (ys.min() + ys.max()) / 2
    bw = xs.max() - xs.min()
    bh = ys.max() - ys.min()
    data[f] = (cy, bw, bh)
    print(f"{f:>5} {labels[f]:>10} | {cy:>7.1f} {bw:>7d} {bh:>7d} |")

print("-" * 66)

if data:
    ys_ = [data[f][0] for f in sorted(data)]
    ws_ = [data[f][1] for f in sorted(data)]
    hs_ = [data[f][2] for f in sorted(data)]
    print(f"\n中心高度跨度: {min(ys_):.0f} ~ {max(ys_):.0f}  (差 {max(ys_)-min(ys_):.0f} px)")
    print(f"宽度跨度: {min(ws_)} ~ {max(ws_)}  (差 {max(ws_)-min(ws_)})")
    print(f"高度跨度: {min(hs_)} ~ {max(hs_)}  (差 {max(hs_)-min(hs_)})")

    print("\n判定:")
    if max(ys_) - min(ys_) > 40:
        print("  ✓ 有明显垂直位移（跳跃成立）")
    else:
        print("  ✗ 垂直位移太小")

    # squash: 落地时应比顶点更宽更矮
    if 74 in data and 44 in data:
        w74, h74 = data[74][1], data[74][2]
        w44, h44 = data[44][1], data[44][2]
        ratio74 = w74 / h74
        ratio44 = w44 / h44
        print(f"  落地宽高比 {ratio74:.3f} vs 顶点 {ratio44:.3f}", end="  ")
        if ratio74 > ratio44 * 1.05:
            print("✓ 落地压扁生效")
        else:
            print("✗ 压扁不明显")
print("=" * 66)
