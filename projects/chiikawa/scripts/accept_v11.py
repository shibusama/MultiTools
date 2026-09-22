"""
v11 成片验收：确认动画、形变、画面都正常
"""
import subprocess
import os
import numpy as np
import bpy

BASE = r"D:\C_Relocated\Users\13191\MultiTools\projects\chiikawa"
MP4 = os.path.join(BASE, "renders", "chiikawa_jump.mp4")
TMP = os.path.join(BASE, "renders", "_v11chk")
os.makedirs(TMP, exist_ok=True)

for n in [0, 20, 32, 44, 74, 120]:
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", MP4,
                    "-vf", f"select=eq(n\\,{n})", "-vframes", "1",
                    os.path.join(TMP, f"c_{n:03d}.png")], capture_output=True)

def load(n):
    img = bpy.data.images.load(os.path.join(TMP, f"c_{n:03d}.png"))
    w, h = img.size
    a = np.array(img.pixels[:]).reshape(h, w, 4)[:, :, :3]
    bpy.data.images.remove(img)
    return a

print("=" * 66)
print("v11 成片验收")
print("=" * 66)

data = {}
for n in [0, 20, 32, 44, 74, 120]:
    a = load(n)
    h, w = a.shape[:2]
    lum = a.mean(axis=2)
    mask = lum < 0.93
    ys, xs = np.nonzero(mask)
    if len(ys) == 0:
        continue
    cy = h - (ys.min()+ys.max())/2
    bw = xs.max()-xs.min()
    bh = ys.max()-ys.min()
    data[n] = (cy, bw, bh, mask.sum())

print(f"{'帧':>5} | {'中心Y':>7} {'宽':>5} {'高':>5} {'宽高比':>7} | {'面积':>8}")
print("-" * 66)
for n in sorted(data):
    cy, bw, bh, area = data[n]
    print(f"{n:>5} | {cy:>7.1f} {bw:>5d} {bh:>5d} {bw/bh:>7.3f} | {area:>8d}")

print("-" * 66)
ys_ = [data[n][0] for n in data]
ratios = [data[n][1]/data[n][2] for n in data]

print(f"\n垂直位移: {min(ys_):.0f} ~ {max(ys_):.0f}  (差 {max(ys_)-min(ys_):.0f} px)")
print(f"宽高比范围: {min(ratios):.3f} ~ {max(ratios):.3f}")

ok = True
if max(ys_)-min(ys_) < 50:
    print("✗ 垂直位移不足"); ok = False
else:
    print("✓ 跳跃位移充分")

if max(ratios)/min(ratios) < 1.3:
    print("✗ 形变不足"); ok = False
else:
    print(f"✓ 挤压拉伸明显 (变化 {max(ratios)/min(ratios):.2f}x)")

# 抽帧差异检查
print()
for i in range(len(data)-1):
    a, b = sorted(data)[i], sorted(data)[i+1]
    print(f"  帧{a}->{b}: 中心移动 {abs(data[a][0]-data[b][0]):.0f}px")

print("\n" + "=" * 66)
if ok:
    print("✓ 验收通过")
print("=" * 66)

for f in os.listdir(TMP):
    os.remove(os.path.join(TMP, f))
os.rmdir(TMP)
