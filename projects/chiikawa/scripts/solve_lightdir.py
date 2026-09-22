"""
求解：什么光照方向能让正面产生 35% 左右的阴影？
对球体（相机在 -Y 方向），分析不同光方向下的可见面明暗比
"""
import numpy as np

# 相机在 (0,-6.2,1.15)，看向 +Y。可见的是球面 -Y 侧
# 球面点 (x,y,z) 归一化法线，可见条件：法线·(0,-1,0) > 0 即 ny < 0

def analyze(light_dir, n=400):
    ld = np.array(light_dir, dtype=float)
    ld /= np.linalg.norm(ld)

    # 采样球面（只取朝向相机的一半 + 稍微多一点）
    pts = []
    for i in range(n):
        for j in range(n):
            a = np.pi * i / n          # 极角 0..pi
            b = 2 * np.pi * j / n      # 方位角
            nx = np.sin(a) * np.cos(b)
            ny = np.sin(a) * np.sin(b)
            nz = np.cos(a)
            # 可见：朝向相机（-Y 分量）
            if ny < -0.15:
                pts.append((nx, ny, nz))
    pts = np.array(pts)

    dots = pts @ ld
    vals = dots * 0.5 + 0.5      # MAD 映射到 0-1

    out = {}
    for thr in [0.5, 0.6, 0.7, 0.8]:
        out[thr] = (vals < thr).mean() * 100
    return vals, out


print("=" * 70)
print("不同光照方向下，可见表面的明暗分布")
print("=" * 70)
print(f"{'光方向':>26} | {'均值':>6} | {'<0.5':>6} {'<0.6':>6} {'<0.7':>6} {'<0.8':>6}")
print("-" * 70)

candidates = [
    ("当前(-0.45,-0.55,0.70)", (-0.45, -0.55, 0.70)),
    ("左侧(-1, 0, 0)",         (-1.0, 0.0, 0.0)),
    ("左前(-1,-0.6,0)",        (-1.0, -0.6, 0.0)),
    ("左侧偏上(-1,0,0.35)",    (-1.0, 0.0, 0.35)),
    ("右上(0.8,-0.6,0.3)",     (0.8, -0.6, 0.3)),
    ("右前(1,-0.8,0)",         (1.0, -0.8, 0.0)),
    ("正前(0,-1,0)",           (0.0, -1.0, 0.0)),
]

for name, d in candidates:
    vals, out = analyze(d)
    print(f"{name:>26} | {vals.mean():6.3f} | "
          f"{out[0.5]:5.1f}% {out[0.6]:5.1f}% {out[0.7]:5.1f}% {out[0.8]:5.1f}%")

print("\n" + "=" * 70)
print("目标：让 <0.5 的占比落在 30-40%（阈值0.5时即可产生明显明暗）")
print("=" * 70)
