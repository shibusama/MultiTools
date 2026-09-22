"""
分析 v3 渲染 —— 为什么还是没有明暗层次？
重点检查：ColorRamp 的输入值（Shader to RGB 输出）实际分布在哪
"""
import bpy
import numpy as np

img = bpy.data.images.load(
    r"D:\C_Relocated\Users\13191\MultiTools\chiikawa动画制作\renders\preview_toon.png"
)
w, h = img.size
px = np.array(img.pixels[:]).reshape(h, w, 4)
rgb = px[:, :, :3]
lum = rgb.mean(axis=2)

# 只看中间角色区域（去掉灰色背景）
# 背景是均匀灰 ~0.55，角色是米白
center = lum[h//4:3*h//4, w//4:3*w//4]

print(f"全图亮度: {lum.min():.3f} ~ {lum.max():.3f}  均值 {lum.mean():.3f}")
print(f"中心区亮度: {center.min():.3f} ~ {center.max():.3f}  均值 {center.mean():.3f}")

# 亮度直方图 —— 看是否双峰（三渲二应该有两个明显峰：亮部/暗部）
hist, edges = np.histogram(center, bins=20, range=(0, 1))
print("\n中心区亮度直方图:")
for i, c in enumerate(hist):
    if c > center.size * 0.01:
        bar = "#" * int(c / center.size * 100)
        print(f"  {edges[i]:.2f}-{edges[i+1]:.2f}: {c/center.size*100:5.1f}% {bar}")

# 统计角色像素（排除背景灰）
# 背景色约 (0.55,0.55,0.58) 偏冷灰
bg_mask = (np.abs(rgb[:,:,0] - rgb[:,:,2]) < 0.02) & (lum > 0.4) & (lum < 0.65)
char_mask = ~bg_mask
char_lum = lum[char_mask]
print(f"\n角色像素占比: {char_mask.sum()/lum.size*100:.1f}%")
if char_lum.size:
    print(f"角色亮度: {char_lum.min():.3f} ~ {char_lum.max():.3f}  均值 {char_lum.mean():.3f}")

# 判定暗部
dark_ratio = (char_lum < 0.5).sum() / char_lum.size
print(f"角色暗部(<0.5)占比: {dark_ratio*100:.1f}%")
print("\n" + "="*55)
if char_lum.size and char_lum.std() < 0.08:
    print("✗ 角色亮度标准差过小 —— 画面是平的，没有明暗层次")
    print("  原因推测：主光方向让整个正面都受光")
else:
    print("✓ 存在明暗层次")
print("="*55)
