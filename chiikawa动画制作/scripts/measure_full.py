"""
修正测量：用整张图的角色区域，而不是中心裁剪
中心裁剪丢掉了边缘的阴影！
"""
import sys
sys.path.insert(0, r"D:\C_Relocated\Users\13191\MultiTools\chiikawa动画制作\scripts")
from measure_png import read_png
import os

BASE = r"D:\C_Relocated\Users\13191\MultiTools\chiikawa动画制作\renders"

def analyze_full(path, label):
    w, h, ch, px = read_png(path)
    vals = []
    for y in range(h):
        for x in range(w):
            i = (y*w + x) * ch
            vals.append((px[i]+px[i+1]+px[i+2])/3/255)

    # 角色 = 非背景（背景接近纯白 >0.97 且 RGB 相等）
    body = [v for v in vals if not (v > 0.96)]
    # 分离：描边(<0.15) vs 表面(>=0.15)
    outline = [v for v in body if v < 0.15]
    surface = [v for v in body if v >= 0.15]

    n = len(surface)
    mean = sum(surface)/n
    std = (sum((v-mean)**2 for v in surface)/n)**0.5

    bins = [0]*20
    for v in surface:
        bins[min(int(v*20), 19)] += 1
    peaks = [(i/20+0.025, bins[i]/n*100) for i in range(1,19)
             if bins[i] > bins[i-1] and bins[i] > bins[i+1] and bins[i]/n > 0.05]

    print(f"[{label}]")
    print(f"    全图角色像素: 表面={n}  描边={len(outline)}")
    print(f"    表面: 均值={mean:.4f} 标准差={std:.4f}")
    print(f"    亮度范围: {min(surface):.3f} ~ {max(surface):.3f}")
    print(f"    色阶峰: {[(round(p,2), round(q,1)) for p,q in peaks]}")
    # 分档统计
    bands = [(0.15,0.5),(0.5,0.7),(0.7,0.85),(0.85,1.0)]
    print(f"    分档:", end=" ")
    for lo, hi in bands:
        cnt = sum(1 for v in surface if lo <= v < hi)
        print(f"{lo}-{hi}:{cnt/n*100:.1f}%", end="  ")
    print("\n")
    return std

print("=" * 62)
print("全图角色区域测量（不裁剪）")
print("=" * 62)
for label, fn in [("v2", "keyframe_001.png"),
                  ("v4", "v4_keyframe_001.png"),
                  ("v5", "v5_keyframe_001.png")]:
    p = os.path.join(BASE, fn)
    if os.path.exists(p):
        analyze_full(p, label)
print("=" * 62)
