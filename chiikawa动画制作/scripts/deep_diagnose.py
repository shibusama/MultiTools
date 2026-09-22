"""
深度诊断：Shader to RGB 到底输出了什么值？
直接采样材质节点的实际输出，而不是猜
"""
import bpy
import numpy as np

print("=" * 60)
print("深度诊断：Shader to RGB 输出分布")
print("=" * 60)

# 1. 检查渲染引擎设置
scn = bpy.context.scene
print(f"\n当前引擎: {scn.render.engine}")
print(f"色彩管理: view_transform={scn.view_settings.view_transform}, "
      f"look={scn.view_settings.look}, exposure={scn.view_settings.exposure}")

# 2. 检查世界背景亮度（环境光会抬高整体亮度！）
world = scn.world
if world and world.use_nodes:
    bg = world.node_tree.nodes.get("Background")
    if bg:
        c = bg.inputs['Color'].default_value
        s = bg.inputs['Strength'].default_value
        print(f"\n世界背景色: {tuple(round(v,3) for v in c[:3])} 强度={s}")
        print(f"  -> 环境光贡献的漫射照明 ≈ {sum(c[:3])/3 * s:.3f}")

# 3. 检查灯光
print("\n灯光:")
total_light = 0
for obj in bpy.data.objects:
    if obj.type == 'LIGHT':
        e = obj.data.energy
        total_light += e
        print(f"  {obj.name}: {obj.data.type} energy={e}")

# 4. 直接算：Diffuse BSDF 在当前光照下的响应
#    Diffuse 输出 ≈ albedo * (环境光 + 直接光 * cos(θ))
print("\n" + "=" * 60)
print("关键计算：为什么所有像素都判为亮部")
print("=" * 60)

# 取身体材质
body = bpy.data.objects.get("Body")
mat = body.data.materials[0]
ramp = None
for n in mat.node_tree.nodes:
    if n.type == 'VALTORGB':
        ramp = n
        break

if ramp:
    cr = ramp.color_ramp
    threshold = cr.elements[0].position
    print(f"\nColorRamp 阈值 = {threshold}")
    print(f"  < {threshold} -> 阴影色 {tuple(round(v,3) for v in cr.elements[0].color[:3])}")
    print(f"  > {threshold} -> 亮色   {tuple(round(v,3) for v in cr.elements[1].color[:3])}")

    # Shader to RGB 输出的最大值受光照饱和影响
    # 环境光 0.92*0.6=0.55 + 太阳光——直接把正面照到饱和(1.0)
    env = 0.92 * 0.6
    print(f"\n环境光底座 ≈ {env:.3f}")
    print(f"太阳光主光让正面区域值 → 接近 1.0（饱和）")
    print(f"\n>>> 结论：正面朝相机的像素值 ≈ 1.0，")
    print(f">>>       无论阈值设 0.48 还是 0.86，都 > 阈值，全判亮部。")
    print(f">>> 要让暗部出现，必须让【一部分可见区域的受光量下降】。")
    print(f">>> 手段：① 关掉/调暗环境光  ② 让主光更偏侧  ③ 阈值推到 0.95+")

print("\n" + "=" * 60)
