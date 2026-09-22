"""
诊断脚本：检查三渲二材质和描边是否正确生效
在渲染前先验证，避免浪费时间
"""
import bpy

print("=" * 60)
print("材质与描边诊断")
print("=" * 60)

for obj in bpy.data.objects:
    if obj.type != 'MESH':
        continue
    print(f"\n[{obj.name}]")
    mats = [m.name if m else "None" for m in obj.data.materials]
    print(f"  材质槽: {mats}")

    for mod in obj.modifiers:
        if mod.type == 'SOLIDIFY':
            print(f"  Solidify: 厚度={mod.thickness} offset={mod.offset} "
                  f"翻转法线={mod.use_flip_normals} "
                  f"材质偏移={mod.material_offset} rim={mod.material_offset_rim}")

    # 检查材质节点结构
    for m in obj.data.materials:
        if not m or not m.use_nodes:
            continue
        types = [n.type for n in m.node_tree.nodes]
        has_s2rgb = 'SHADER_TO_RGB' in types
        has_ramp = 'VALTORGB' in types
        print(f"    {m.name}: 节点={types}")
        if has_s2rgb and has_ramp:
            ramp = next(n for n in m.node_tree.nodes if n.type == 'VALTORGB')
            cr = ramp.color_ramp
            print(f"      ColorRamp 插值={cr.interpolation} "
                  f"位置=[{cr.elements[0].position:.2f}, {cr.elements[1].position:.2f}]")
            print(f"      阴影色={tuple(round(v,3) for v in cr.elements[0].color[:3])} "
                  f"亮色={tuple(round(v,3) for v in cr.elements[1].color[:3])}")
        if has_s2rgb:
            print(f"      ✓ Shader to RGB 存在")

print("\n" + "=" * 60)
print("灯光检查")
for obj in bpy.data.objects:
    if obj.type == 'LIGHT':
        import math
        rot = [math.degrees(a) for a in obj.rotation_euler]
        print(f"  {obj.name}: 类型={obj.data.type} 强度={obj.data.energy} "
              f"旋转={[round(r) for r in rot]}°")
print("=" * 60)
