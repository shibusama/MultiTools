"""
验证 Shader to RGB 在 Blender 5.2 的实际状态
"""
import bpy

print("=" * 60)
print("Shader to RGB 在 Blender 5.2 的状态检查")
print("=" * 60)

# 1. 节点是否存在
print(f"\n节点类型存在: {hasattr(bpy.types, 'ShaderNodeShaderToRGB')}")

# 2. 检查它的输出socket
nt = bpy.data.materials.new("test")
nt.use_nodes = True
nodes = nt.node_tree.nodes
nodes.clear()
s = nodes.new('ShaderNodeShaderToRGB')
print(f"\nShaderNodeShaderToRGB 输出接口:")
for o in s.outputs:
    print(f"  - {o.name} (type={o.type})")
print(f"输入接口:")
for i in s.inputs:
    print(f"  - {i.name} (type={i.type})")

# 3. 检查是否有版本相关的提示
print(f"\nBlender 版本: {bpy.app.version}")

# 4. 检查 EEVEE 相关设置里有没有关于 Shader to RGB 的选项
print("\n检查场景 EEVEE 设置:")
scn = bpy.context.scene
ee = scn.eevee
for attr in dir(ee):
    if not attr.startswith('_'):
        try:
            v = getattr(ee, attr)
            if not callable(v):
                print(f"  eevee.{attr} = {v}")
        except Exception:
            pass
