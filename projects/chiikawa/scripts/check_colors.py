"""
检查扫描为什么全是"全暗"
直接输出渲染图的实际颜色值，看红色判定是否正确
"""
import bpy
import numpy as np
import os

out_dir = r"D:\C_Relocated\Users\13191\MultiTools\projects\chiikawa\renders"

# 用现有的 debug_redblue.png
p = os.path.join(out_dir, "debug_redblue.png")
img = bpy.data.images.load(p)
w, h = img.size
px = np.array(img.pixels[:]).reshape(h, w, 4)

print(f"图像 {w}x{h}")
print(f"通道范围: R={px[:,:,0].min():.3f}~{px[:,:,0].max():.3f} "
      f"G={px[:,:,1].min():.3f}~{px[:,:,1].max():.3f} "
      f"B={px[:,:,2].min():.3f}~{px[:,:,2].max():.3f}")

# 采样几个点
print("\n采样点（行,列）-> RGB:")
for r, c in [(100,100), (200,200), (270,270), (300,200), (150,270)]:
    if r < h and c < w:
        v = px[r, c]
        print(f"  ({r:3d},{c:3d}) -> R={v[0]:.3f} G={v[1]:.3f} B={v[2]:.3f} A={v[3]:.3f}")

# 统计所有唯一颜色（量化后）
flat = (px[:,:,:3] * 20).astype(np.int32)
keys = flat[:,:,0]*10000 + flat[:,:,1]*100 + flat[:,:,2]
uniq, counts = np.unique(keys, return_counts=True)
order = np.argsort(counts)[::-1][:8]
print(f"\n主要颜色（前8，量化到 1/20）:")
for i in order:
    k = uniq[i]
    rr, gg, bb = k//10000, (k//100)%100, k%100
    print(f"  R={rr/20:.2f} G={gg/20:.2f} B={bb/20:.2f}  占 {counts[i]/keys.size*100:5.1f}%")

# 关键问题：背景色是什么？如果背景占了大部分，红色统计就被污染
print(f"\n! 注意：如果背景是纯色（非红非蓝），说明角色区域很小")
print(f"  或者说明 ColorRamp 根本没被上到 Body 以外的对象")
