"""诊断背景颜色问题"""
import bpy
import numpy as np
import os

TMP = r"D:\C_Relocated\Users\13191\MultiTools\projects\chiikawa\renders\_verify"

img = bpy.data.images.load(os.path.join(TMP, "mp4_000.png"))
w, h = img.size
px = np.array(img.pixels[:]).reshape(h, w, 4)

print("=" * 55)
print("背景色诊断")
print("=" * 55)

# 采样角落（一定是背景）
corners = {
    "左上": px[h-5, 5],
    "右上": px[h-5, w-5],
    "左下": px[5, 5],
    "右下": px[5, w-5],
}
for name, v in corners.items():
    print(f"  {name}: R={v[0]:.3f} G={v[1]:.3f} B={v[2]:.3f}")

# 背景区域统计
bg = px[:100, :100, :3].reshape(-1, 3)
print(f"\n背景区域(左上100x100):")
print(f"  均值 R={bg[:,0].mean():.3f} G={bg[:,1].mean():.3f} B={bg[:,2].mean():.3f}")
print(f"  最小 {bg.min():.3f}  最大 {bg.max():.3f}")

lum = px[:,:,:3].mean(axis=2)
for thr in [0.9, 0.85, 0.8, 0.75]:
    r = (lum > thr).sum() / lum.size * 100
    print(f"  亮度>{thr}: {r:.1f}%")

print("\n判断：如果背景均值在 0.9 左右但不是纯 1.0，")
print("     说明 ffmpeg 合成时色彩范围(yuv)有损失，或者白底不是纯白")
