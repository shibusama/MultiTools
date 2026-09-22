"""完整打印 v4 材质节点结构"""
import bpy

body = bpy.data.objects.get("Chiikawa_Body")
mat = body.data.materials[0]
nt = mat.node_tree

print("=" * 60)
print(f"材质: {mat.name}  节点数: {len(nt.nodes)}")
print("=" * 60)
for n in nt.nodes:
    print(f"\n[{n.name}] type={n.type} op={getattr(n,'operation','-')}")
    for i in n.inputs:
        links = [f"{l.from_node.name}.{l.from_socket.name}" for l in i.links]
        try:
            dv = i.default_value
            if hasattr(dv, '__len__'):
                dv = tuple(round(v, 3) for v in dv)
            else:
                dv = round(dv, 3)
        except Exception:
            dv = "-"
        print(f"    IN  {i.name:12s} = {dv}   <- {links}")
    for o in n.outputs:
        links = [f"{l.to_node.name}.{l.to_socket.name}" for l in o.links]
        print(f"    OUT {o.name:12s} -> {links}")
print("=" * 60)
