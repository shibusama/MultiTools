"""
最终验收：直接检查合成后的 MP4（不带 alpha，所见即所得）
"""
import subprocess
import os
import numpy as np
import bpy

BASE = r"D:\C_Relocated\Users\13191\MultiTools\projects\chiikawa"
MP4 = os.path.join(BASE, "renders", "chiikawa_animation.mp4")
TMP = os.path.join(BASE, "renders", "_verify")
os.makedirs(TMP, exist_ok=True)

# 从 MP4 抽帧
for n in [0, 18, 36, 54]:
    out = os.path.join(TMP, f"mp4_{n:03d}.png")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", MP4,
                    "-vf", f"select=eq(n\\,{n})", "-vframes", "1", out],
                   capture_output=True)

def load(p):
    img = bpy.data.images.load(p)
    w, h = img.size
    a = np.array(img.pixels[:]).reshape(h, w, 4)[:, :, :3]
    bpy.data.images.remove(img)
    return a

frames = {}
for n in [0, 18, 36, 54]:
    frames[n] = load(os.path.join(TMP, f"mp4_{n:03d}.png"))

print("=" * 58)
print("最终验收：合成视频质量")
print("=" * 58)

f0 = frames[0]
lum0 = f0.mean(axis=2)

# 背景检查：角落必须是纯白（角色本体是米白 ~0.85，不能和背景混为一谈）
corner = f0[:80, :80].reshape(-1, 3)
corner_pure_white = (corner > 0.99).all(axis=1).mean() * 100
print(f"角落纯白比例: {corner_pure_white:.1f}%  (应 ~100% = 合成正确)")

# 画面中背景总量（纯白像素）
bg_ratio = (lum0 > 0.98).sum() / lum0.size * 100
print(f"纯白背景占比: {bg_ratio:.1f}%")

# 黑色描边像素
outline_ratio = ((lum0 < 0.15)).sum() / lum0.size * 100
print(f"描边像素占比: {outline_ratio:.2f}%  (应 2-6%)")

# 检查彩色部件存在（眼睛黑、腮红粉）
r, g, b = f0[:,:,0], f0[:,:,1], f0[:,:,2]
pink = ((r > 0.7) & (r > b + 0.1) & (g < r - 0.15)).sum() / lum0.size * 100
print(f"腮红(粉色)像素: {pink:.2f}%  (应 > 0.1%)")

# 动画检验
print(f"\n动画变化:")
max_ch = 0
for n in [18, 36, 54]:
    d = np.abs(frames[0] - frames[n]).max(axis=2)
    ch = (d > 0.02).sum() / d.size * 100
    max_ch = max(max_ch, ch)
    print(f"  帧1 vs 帧{n}: {ch:.2f}% 像素变化")

print("\n" + "=" * 58)
ok = True
if corner_pure_white < 99: print("✗ 背景合成有问题"); ok = False
if not (1 < outline_ratio < 8): print("✗ 描边比例异常"); ok = False
if pink < 0.05: print("✗ 腮红丢失"); ok = False
if max_ch < 1.0: print("✗ 动画变化过小"); ok = False
if ok: print("✓ 视频质量检查全部通过")
print("=" * 58)
