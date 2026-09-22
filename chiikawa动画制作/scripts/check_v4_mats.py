"""检查 v4 final 网格上到底挂了什么材质"""
import bpy

print("=" * 58)
print("v4 final 场景材质检查")
print("=" * 58)

print(f"\nbpy.data.materials 共 {len(bpy.data.materials)} 个:")
for m in bpy.data.materials:
    print(f"  - {m.name}  nodes={m.use_nodes}")

print("\n各网格对象的材质槽:")
for obj in bpy.data.objects:
    if obj.type != 'MESH':
        continue
    print(f"\n[{obj.name}]  {len(obj.data.materials)} 个槽")
    for i, m in enumerate(obj.data.materials):
        print(f"  [{i}] {m.name if m else 'None'}")
        if m and m.use_nodes:
            types = [n.type for n in m.node_tree.nodes]
            print(f"       节点: {types}")
            for n in m.node_tree.nodes:
                if n.type == 'VALTORGB':
                    print(f"       ColorRamp 阈值={n.color_ramp.elements[0].position:.3f}")
print("=" * 58)
