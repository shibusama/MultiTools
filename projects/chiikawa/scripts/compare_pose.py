"""
精确对比测试：rest pose vs 动画 pose
用来确认变形到底来自绑定还是动画
"""
import bpy
import os

BASE = r"D:\C_Relocated\Users\13191\MultiTools\projects\chiikawa"
OUT = os.path.join(BASE, "renders")

mesh = bpy.data.objects.get("Chiikawa")
arm = bpy.data.objects.get("ChiikawaRig")

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 600
scene.render.resolution_y = 600

# --- 测试 A：完全禁用 Armature 修改器 ---
for m in mesh.modifiers:
    if m.type == 'ARMATURE':
        m.show_render = False
        m.show_viewport = False
scene.render.filepath = os.path.join(OUT, "cmp_A_no_armature.png")
bpy.ops.render.render(write_still=True)
print("A: Armature 禁用 -> cmp_A_no_armature.png")

# --- 测试 B：启用 Armature，但骨架设为 rest position ---
for m in mesh.modifiers:
    if m.type == 'ARMATURE':
        m.show_render = True
        m.show_viewport = True

arm.data.pose_position = 'REST'
bpy.context.view_layer.update()
scene.render.filepath = os.path.join(OUT, "cmp_B_rest_pose.png")
bpy.ops.render.render(write_still=True)
print("B: 骨架 REST 姿态 -> cmp_B_rest_pose.png")

# --- 测试 C：骨架设为 pose position，第1帧 ---
arm.data.pose_position = 'POSE'
scene.frame_set(1)
bpy.context.view_layer.update()
scene.render.filepath = os.path.join(OUT, "cmp_C_pose_f1.png")
bpy.ops.render.render(write_still=True)
print("C: 骨架 POSE 第1帧 -> cmp_C_pose_f1.png")

print("\n对比三张图：")
print("  A 正常 + B 正常 + C 变形  -> 问题在动画关键帧")
print("  A 正常 + B 变形           -> 问题在绑定/权重")
print("  A 变形                    -> 问题在别处")
