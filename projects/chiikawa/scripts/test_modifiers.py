"""
决定性测试：逐个移除修改器，找出是哪个导致变形
"""
import bpy
import os

BASE = r"D:\C_Relocated\Users\13191\MultiTools\projects\chiikawa"
OUT = os.path.join(BASE, "renders")

mesh = bpy.data.objects.get("Chiikawa")
print("=" * 60)
print("修改器列表（按顺序）")
print("=" * 60)
for i, m in enumerate(mesh.modifiers):
    print(f"  [{i}] {m.name} type={m.type} "
          f"{'对象=' + m.object.name if m.type=='ARMATURE' and m.object else ''}")

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 600
scene.render.resolution_y = 600
scene.frame_set(1)

# 测试1: 移除所有修改器
saved = []
for m in list(mesh.modifiers):
    saved.append((m.name, m.type))
    mesh.modifiers.remove(m)

scene.render.filepath = os.path.join(OUT, "test_no_modifiers.png")
bpy.ops.render.render(write_still=True)
print("\n测试1: 移除所有修改器 -> test_no_modifiers.png")

# 测试2: 只加回 Armature
for name, typ in saved:
    if typ == 'ARMATURE':
        mod = mesh.modifiers.new(name=name, type='ARMATURE')
        if mesh.parent:
            mod.object = mesh.parent
        break

scene.render.filepath = os.path.join(OUT, "test_only_armature.png")
bpy.ops.render.render(write_still=True)
print("测试2: 只加 Armature -> test_only_armature.png")

print("\n对比这两张图就能定位问题")
print("=" * 60)
