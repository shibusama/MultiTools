"""
在同一进程内验证：改完材质立刻渲染，排除文件读写问题
同时把 ColorRamp 两端的颜色改成极端对比（红/蓝），肉眼可辨
"""
import bpy
import numpy as np
import os

base = r"D:\C_Relocated\Users\13191\MultiTools\projects\chiikawa"
out_dir = os.path.join(base, "renders")

print("=" * 60)
print("同进程验证：极端配色测试")
print("=" * 60)

body = bpy.data.objects.get("Body")
mat = body.data.materials[0]
nt = mat.node_tree

ramp = next(n for n in nt.nodes if n.type == 'VALTORGB')
cr = ramp.color_ramp

# 改成极端对比：阴影=纯红，亮部=纯蓝
cr.elements[0].color = (1.0, 0.0, 0.0, 1.0)   # 红 = 阴影
cr.elements[1].color = (0.0, 0.0, 1.0, 1.0)   # 蓝 = 亮部
cr.elements[0].position = 0.45
print(f"  阈值={cr.elements[0].position}")
print(f"  阴影色=红  亮部色=蓝")

# 渲染
scene = bpy.context.scene
scene.render.filepath = os.path.join(out_dir, "debug_redblue.png")
scene.render.resolution_x = 540
scene.render.resolution_y = 540
bpy.ops.render.render(write_still=True)

# 分析：数红像素 vs 蓝像素
img = bpy.data.images.load(os.path.join(out_dir, "debug_redblue.png"))
w, h = img.size
px = np.array(img.pixels[:]).reshape(h, w, 4)
r, g, b = px[:,:,0], px[:,:,1], px[:,:,2]

red_mask = (r > 0.5) & (b < 0.3)
blue_mask = (b > 0.5) & (r < 0.3)
total_colored = red_mask.sum() + blue_mask.sum()

print(f"\n结果:")
print(f"  红(阴影)像素: {red_mask.sum():>7d}  {red_mask.sum()/max(total_colored,1)*100:5.1f}%")
print(f"  蓝(亮部)像素: {blue_mask.sum():>7d}  {blue_mask.sum()/max(total_colored,1)*100:5.1f}%")

if red_mask.sum() == 0:
    print("\n  >>> 完全没有红色 = ColorRamp 从未输出过左侧颜色")
    print("  >>> 说明 Shader to RGB 的值始终 > 0.45")
elif blue_mask.sum() == 0:
    print("\n  >>> 完全没有蓝色 = ColorRamp 从未输出过右侧颜色")
    print("  >>> 说明 Shader to RGB 的值始终 < 0.45")
else:
    ratio = red_mask.sum() / max(total_colored, 1)
    print(f"\n  >>> 明暗分裂成功！阴影占 {ratio*100:.1f}%")
    print(f"  >>> 想要更多阴影就提高阈值，想要更少就降低")

print("=" * 60)
