"""
画质检查：描边完整性
对比最终视频帧与之前验证过的干净帧，看描边是否退化
"""
import bpy
import numpy as np
import os

BASE = r"D:\C_Relocated\Users\13191\MultiTools\projects\chiikawa"
FD = os.path.join(BASE, "renders", "frames")

img = bpy.data.images.load(os.path.join(FD, "frame_0018.png"))
w, h = img.size
px = np.array(img.pixels[:]).reshape(h, w, 4)[:, :, :3]

lum = px.mean(axis=2)
dark = lum < 0.2

print("=" * 58)
print("描边完整性检查 (frame 18)")
print("=" * 58)
print(f"描边像素占比: {dark.sum()/lum.size*100:.2f}%")

# 逐行扫描：统计每行描边像素数，看是否有断裂
rows = dark.sum(axis=1)
top_region = rows[h//5:h//2]   # 头顶到中部
print(f"\n头顶区域描边行分布 (每行黑像素数):")
for i in range(0, len(top_region), 20):
    r = top_region[i]
    bar = "#" * min(int(r/4), 60)
    print(f"  行{h//5+i:4d}: {r:4d} {bar}")

# 检测描边断裂：相邻行黑像素数突变
jumps = 0
for i in range(1, len(top_region)):
    if abs(int(top_region[i]) - int(top_region[i-1])) > 25:
        jumps += 1
print(f"\n描边突变次数: {jumps}")

print("\n" + "=" * 58)
if jumps > 30:
    print("⚠ 描边存在较多突变 -> 可能有断裂/锯齿")
else:
    print("✓ 描边连续")
print("=" * 58)
