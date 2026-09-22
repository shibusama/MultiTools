"""量化验证 v5 的三渲二效果：统计画面里出现了几种色阶"""
import bpy
import numpy as np
import os

BASE = r"D:\C_Relocated\Users\13191\MultiTools\chiikawa动画制作"
OUT = os.path.join(BASE, "renders")

for tag in ["v2", "v4", "v5"]:
    p = os.path.join(OUT, f"{tag}_keyframe_001.png")
    if not os.path.exists(p):
        # v2 的预览图叫 keyframe_001.png
        alt = os.path.join(OUT, "keyframe_001.png")
        if tag == "v2" and os.path.exists(alt):
            p = alt
        else:
            print(f"[{tag}] 无预览图")
            continue

    img = bpy.data.images.load(p)
    w, h = img.size
    px = np.array(img.pixels[:]).reshape(h, w, 4)[:, :, :3]
    lum = px.mean(axis=2)

    # 取角色区域
    c = lum[h//3:2*h//3, w//3:2*w//3].ravel()

    # 排除背景(接近纯白)和描边(接近纯黑)
    body = c[(c > 0.15) & (c < 0.97)]

    # 统计有多少个明显的色阶：直方图峰的数量
    hist, edges = np.histogram(body, bins=40, range=(0.3, 1.0))
    # 找峰（局部极大且占比>3%）
    peaks = []
    for i in range(1, len(hist)-1):
        if hist[i] > hist[i-1] and hist[i] > hist[i+1]:
            if hist[i] / body.size > 0.03:
                peaks.append((edges[i], hist[i]/body.size*100))

    print(f"[{tag}] 角色像素={body.size}  标准差={body.std():.4f}")
    print(f"      检出 {len(peaks)} 个色阶峰:")
    for pos, pct in peaks:
        print(f"        亮度 {pos:.2f} -> {pct:5.1f}%")
    print()

    bpy.data.images.remove(img)

print("=" * 58)
print("三渲二判定：色阶峰数 >= 2 说明明暗分层成功")
print("=" * 58)
