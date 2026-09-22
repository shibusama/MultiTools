"""验证：脚本改的材质到底有没有落进最终文件"""
import bpy

print("=" * 60)
print("验证材质实际状态")
print("=" * 60)

body = bpy.data.objects.get("Body")
print(f"\nBody 材质槽数: {len(body.data.materials)}")
for i, m in enumerate(body.data.materials):
    print(f"  [{i}] {m.name if m else 'None'}")

mat = body.data.materials[0]
print(f"\n主体材质: {mat.name}")
print(f"  节点数: {len(mat.node_tree.nodes)}")

for n in mat.node_tree.nodes:
    if n.type == 'VALTORGB':
        cr = n.color_ramp
        print(f"\n  ColorRamp:")
        print(f"    插值 = {cr.interpolation}")
        for i, el in enumerate(cr.elements):
            print(f"    [{i}] 位置={el.position:.3f} 颜色={tuple(round(v,3) for v in el.color[:3])}")

    if n.type == 'BSDF_DIFFUSE':
        print(f"\n  Diffuse 颜色 = {tuple(round(v,3) for v in n.inputs['Color'].default_value[:3])}")

# 检查场景里所有材质名，看是否有重复/旧的
print(f"\n场景全部材质 ({len(bpy.data.materials)} 个):")
for m in bpy.data.materials:
    print(f"  - {m.name}")

# 检查灯光
print(f"\n灯光:")
import math
for obj in bpy.data.objects:
    if obj.type == 'LIGHT':
        print(f"  {obj.name}: {obj.data.type} energy={obj.data.energy} "
              f"rot={[round(math.degrees(a)) for a in obj.rotation_euler]}")
print("=" * 60)
