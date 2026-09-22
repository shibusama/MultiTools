"""
决定性测试：光照角度是否真的影响渲染
渲染两个极端角度，比较像素
"""
import bpy
import numpy as np
import os
import math
import hashlib

BASE = r"D:\C_Relocated\Users\13191\MultiTools\chiikawa动画制作"
OUT = os.path.join(BASE, "renders")

sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x = 300
sc.render.resolution_y = 300
sc.render.film_transparent = False
try:
    sc.view_settings.view_transform = 'Standard'
except Exception:
    pass

sun = bpy.data.objects.get("KeyLight")
print(f"灯光初始: {tuple(round(a,3) for a in sun.rotation_euler)}")

# 提高采样，确保光照计算充分
sc.eevee.taa_render_samples = 64

hashes = {}
for yaw in [0.0, 90.0, 180.0]:
    sun.rotation_euler = (math.radians(72), 0, math.radians(yaw))
    bpy.context.view_layer.update()
    tmp = os.path.join(OUT, f"_angle_{int(yaw)}.png")
    sc.render.filepath = tmp
    bpy.ops.render.render(write_still=True)

    with open(tmp, 'rb') as f:
        h = hashlib.md5(f.read()).hexdigest()[:12]
    hashes[yaw] = h

    img = bpy.data.images.load(tmp)
    w, hh = img.size
    px = np.array(img.pixels[:]).reshape(hh, w, 4)[:, :, :3]
    lum = px.mean(axis=2)
    c = lum[hh//4:3*hh//4, w//4:3*w//4].ravel()
    surf = c[(c > 0.06) & (c < 0.90)]
    print(f"  yaw={yaw:5.0f}°  hash={h}  表面均值={surf.mean() if surf.size else 0:.4f}  "
          f"样本={surf.size}")
    bpy.data.images.remove(img)

print("\n" + "=" * 55)
if len(set(hashes.values())) == 1:
    print("✗ 三个角度渲染结果完全相同 -> 光照没生效")
    print("  原因：ShaderToRGB 在无头模式下可能不响应灯光变化")
else:
    print(f"✓ 光照生效（{len(set(hashes.values()))} 种不同结果）")
print("=" * 55)

for y in hashes:
    p = os.path.join(OUT, f"_angle_{int(y)}.png")
    if os.path.exists(p):
        os.remove(p)
