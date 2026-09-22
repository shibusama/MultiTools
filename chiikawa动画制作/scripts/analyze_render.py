"""
分析渲染结果 —— 程序化验证三渲二效果
检查：是否真的有硬边阴影（色块分明），描边是否存在
"""
import bpy
import numpy as np

img = bpy.data.images.load(
    r"D:\C_Relocated\Users\13191\MultiTools\chiikawa动画制作\renders\preview_toon.png"
)
w, h = img.size
px = np.array(img.pixels[:]).reshape(h, w, 4)
rgb = px[:, :, :3]

print(f"图像尺寸: {w}x{h}")
print(f"亮度范围: {rgb.min():.3f} ~ {rgb.max():.3f}")
print(f"平均亮度: {rgb.mean():.3f}")

# --- 检查是否色块化（硬边）：统计唯一颜色数量 ---
flat = (rgb.reshape(-1, 3) * 255).astype(np.uint8)
# 量化到 8 级，看颜色分布集中度
quant = (flat // 8).astype(np.int32)
keys = quant[:, 0] * 1024 + quant[:, 1] * 32 + quant[:, 2]
uniq, counts = np.unique(keys, return_counts=True)
top = np.sort(counts)[::-1][:10]
total = counts.sum()
print(f"\n不同颜色簇数量: {len(uniq)}")
print("占比最高的颜色簇 (前10):")
for c in top:
    print(f"  {c/total*100:5.1f}%")

# --- 检查暗像素比例（描边/阴影） ---
lum = rgb.mean(axis=2)
dark = (lum < 0.15).sum() / lum.size
mid = ((lum >= 0.15) & (lum < 0.6)).sum() / lum.size
bright = (lum >= 0.6).sum() / lum.size
print(f"\n亮度分布:")
print(f"  暗部 (<0.15)  : {dark*100:5.1f}%  <- 描边/深阴影")
print(f"  中间 (0.15-0.6): {mid*100:5.1f}%  <- 阴影色块")
print(f"  亮部 (>0.6)   : {bright*100:5.1f}%  <- 受光面")

# --- 判定 ---
print("\n" + "="*50)
concentrated = top[0] / total > 0.15
has_outline = dark > 0.002
print(f"色块集中度: {'✓ 高（硬边阴影成立）' if concentrated else '✗ 低（可能是渐变）'}")
print(f"描边存在  : {'✓ 是' if has_outline else '✗ 否'}")
print("="*50)
