"""检查 v10 场景的灯光与材质实际状态"""
import bpy

print("=" * 58)
print("对象清单")
print("=" * 58)
for o in bpy.data.objects:
    print(f"  {o.name}: {o.type}")

print("\n灯光:")
for o in bpy.data.objects:
    if o.type == 'LIGHT':
        print(f"  {o.name}: energy={o.data.energy} "
              f"rot={tuple(round(a,3) for a in o.rotation_euler)} "
              f"constraints={[c.type for c in o.constraints]}")

print("\n材质节点检查（看 Diffuse 是否还连着）:")
for o in bpy.data.objects:
    if o.type != 'MESH':
        continue
    print(f"\n[{o.name}]")
    for m in o.data.materials:
        if not m or not m.use_nodes:
            print(f"  {m.name if m else None}: 无节点")
            continue
        types = [n.type for n in m.node_tree.nodes]
        print(f"  {m.name}: {types}")
        for n in m.node_tree.nodes:
            if n.type == 'BSDF_DIFFUSE':
                dc = n.inputs['Color'].default_value
                print(f"      Diffuse 颜色 = {tuple(round(v,3) for v in dc[:3])}")
            if n.type == 'EMISSION':
                ec = n.inputs['Color'].default_value
                linked = [l.from_node.name for l in n.inputs['Color'].links]
                print(f"      Emission 颜色={tuple(round(v,3) for v in ec[:3])} <- {linked}")
            if n.type == 'VALTORGB':
                print(f"      ColorRamp 阈值={n.color_ramp.elements[0].position:.3f}")

print("\n世界:")
w = bpy.context.scene.world
if w and w.use_nodes:
    for n in w.node_tree.nodes:
        if n.type == 'BACKGROUND':
            print(f"  Background 强度={n.inputs['Strength'].default_value:.3f} "
                  f"颜色={tuple(round(v,2) for v in n.inputs['Color'].default_value[:3])}")
print("=" * 58)
