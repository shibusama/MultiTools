"""
求解：什么光照方向能让 dot' 分布在中段铺开？

v8 材质的映射：dot' = Σ ((n_i+1)/2) * ((l_i+1)/2)
对朝向相机的可见半球，n_y < 0。要让分布铺开，
光应该主要沿 X（左右）方向，这样 nx 从 -1 到 +1 扫过全范围。
"""
import numpy as np

def simulate(light_dir, n=300):
    ld = np.array(light_dir, float); ld /= np.linalg.norm(ld)
    l_remap = (ld + 1) / 2

    vals = []
    for i in range(n):
        for j in range(n):
            a = np.pi * i / n
            b = 2 * np.pi * j / n
            nx, ny, nz = np.sin(a)*np.cos(b), np.sin(a)*np.sin(b), np.cos(a)
            # 可见：朝向相机（相机在 -Y）
            if ny < -0.2:
                n_remap = (np.array([nx, ny, nz]) + 1) / 2
                vals.append(float(np.dot(n_remap, l_remap)))
    v = np.array(vals)
    return v

print("=" * 70)
print("光照方向 -> dot' 分布（可见半球）")
print("=" * 70)
print(f"{'光方向':>24} | {'均值':>6} {'标准差':>6} | 各阈值阴影占比")
print("-" * 70)

for name, d in [
    ("当前(-0.5,-0.55,0.67)", (-0.5, -0.55, 0.67)),
    ("纯左侧(-1,0,0)",        (-1.0, 0.0, 0.0)),
    ("左侧稍前(-1,-0.3,0)",   (-1.0, -0.3, 0.0)),
    ("左上(-1,0,0.4)",        (-1.0, 0.0, 0.4)),
    ("左前上(-0.8,-0.4,0.4)", (-0.8, -0.4, 0.4)),
    ("右侧(1,0,0)",           (1.0, 0.0, 0.0)),
    ("右上(0.9,-0.2,0.4)",    (0.9, -0.2, 0.4)),
]:
    v = simulate(d)
    row = "  ".join(f"{t:.1f}:{(v<t).mean()*100:4.0f}%" for t in [0.6,0.7,0.8,0.9])
    print(f"{name:>24} | {v.mean():6.3f} {v.std():6.3f} | {row}")

print("\n" + "=" * 70)
print("目标：阈值 0.7 附近能有 25-40% 阴影 -> 选标准差大且分布居中的方向")
print("=" * 70)
