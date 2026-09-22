"""
验收脚本：确认视频里真的有动画（不是 72 张相同帧）
对比不同帧的像素差异
"""
import bpy
import numpy as np
import os

BASE = r"D:\C_Relocated\Users\13191\MultiTools\projects\chiikawa"
FD = os.path.join(BASE, "renders", "frames")

def load(fn):
    img = bpy.data.images.load(os.path.join(FD, fn))
    w, h = img.size
    a = np.array(img.pixels[:]).reshape(h, w, 4)[:, :, :3]
    bpy.data.images.remove(img)
    return a

f1 = load("frame_0001.png")
f9 = load("frame_0009.png")
f18 = load("frame_0018.png")
f54 = load("frame_0054.png")
f72 = load("frame_0072.png")

print("=" * 60)
print("动画有效性验证")
print("=" * 60)

def diff(a, b, label):
    d = np.abs(a - b)
    mean = d.mean()
    changed = (d.max(axis=2) > 0.02).sum() / (d.shape[0]*d.shape[1]) * 100
    print(f"  {label:22s} 平均差异={mean:.5f}  变化像素={changed:5.2f}%")
    return changed

c1 = diff(f1, f9,  "帧1 vs 帧9")
c2 = diff(f1, f18, "帧1 vs 帧18(峰值)")
c3 = diff(f1, f54, "帧1 vs 帧54(谷值)")
c4 = diff(f1, f72, "帧1 vs 帧72(应回到起点)")

print("\n" + "=" * 60)
print("判定")
print("=" * 60)

if max(c1, c2, c3) < 0.5:
    print("✗ 帧之间几乎无变化 -> 不是动画")
else:
    print(f"✓ 存在明显动画（最大变化 {max(c1,c2,c3):.2f}% 像素）")

if c4 < 0.5:
    print("✓ 首末帧一致 -> 循环动画可无缝衔接")
else:
    print(f"⚠ 首末帧差异 {c4:.2f}% -> 循环可能不完美")

# 检查浮动方向是否合理（呼吸应该是整体上下移动）
row_f1 = f1.mean(axis=(1, 2))
row_f18 = f18.mean(axis=(1, 2))
shift = np.argmax(row_f1) - np.argmax(row_f18)
print(f"\n主体垂直位移: {shift} 像素 (帧18 相对帧1)")
print("=" * 60)
