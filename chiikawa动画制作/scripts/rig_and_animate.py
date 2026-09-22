"""
骨骼绑定 + 动画
================
流程：
1. 合并所有部件为单一网格（保留材质）
2. 创建骨骼：根骨骼 + 身体骨骼 + 两只耳朵骨骼
3. 自动权重绑定
4. 做一段简单的待机动画（呼吸 + 轻微摇摆）

用法:
    blender --background <model.blend> --python rig_and_animate.py
"""
import bpy
import math
import os
from mathutils import Vector

BASE = r"D:\C_Relocated\Users\13191\MultiTools\chiikawa动画制作"


def merge_parts():
    """合并身体、耳朵等部件（眼睛/嘴/腮红也一起并，但保留材质）"""
    parts = ["Body", "Ear_L", "Ear_R", "Eye_L", "Eye_R", "Mouth",
             "Blush_L", "Blush_R"]
    objs = [bpy.data.objects.get(p) for p in parts]
    objs = [o for o in objs if o]

    if not objs:
        print("没有可合并的对象")
        return None

    # 先把描边修改器应用掉（避免合并后冲突）
    for o in objs:
        bpy.context.view_layer.objects.active = o
        for mod in list(o.modifiers):
            if mod.type == 'SOLIDIFY':
                try:
                    bpy.ops.object.modifier_apply(modifier=mod.name)
                except Exception as e:
                    print(f"  应用修改器失败 {o.name}: {e}")

    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()

    merged = bpy.context.active_object
    merged.name = "Chiikawa"
    print(f"合并完成: {merged.name}")
    print(f"  材质槽: {[m.name if m else None for m in merged.data.materials]}")
    print(f"  顶点数: {len(merged.data.vertices)}")

    # 重新加描边（合并后统一加）
    outline = bpy.data.materials.get("Outline")
    if outline:
        mats = [m for m in merged.data.materials if m]
        if outline.name not in [m.name for m in mats]:
            merged.data.materials.append(outline)
        mats = [m for m in merged.data.materials if m]
        slot = [m.name for m in mats].index(outline.name)
        mod = merged.modifiers.new(name="Outline", type='SOLIDIFY')
        mod.thickness = 0.055
        mod.offset = 1.0
        mod.use_flip_normals = True
        mod.use_rim = False
        mod.material_offset = slot
        mod.material_offset_rim = slot
        print(f"  已加描边修改器 (槽{slot})")

    return merged


def create_armature(mesh_obj):
    """创建骨骼系统"""
    # 在中心创建骨架
    bpy.ops.object.armature_add(location=(0, 0, 0))
    arm = bpy.context.active_object
    arm.name = "ChiikawaRig"

    bpy.ops.object.mode_set(mode='EDIT')
    ebs = arm.data.edit_bones

    # 删除默认骨骼
    for b in list(ebs):
        ebs.remove(b)

    # --- 根骨骼：从身体底部到中心 ---
    root = ebs.new("Root")
    root.head = (0, 0, 0)
    root.tail = (0, 0, 0.5)

    # --- 身体骨骼：贯穿身体中心 ---
    body = ebs.new("Body")
    body.head = (0, 0, 0.5)
    body.tail = (0, 0, 1.9)
    body.parent = root

    # --- 左耳骨骼 ---
    ear_l = ebs.new("Ear_L")
    ear_l.head = (-0.68, 0, 1.75)
    ear_l.tail = (-0.68, 0, 2.25)
    ear_l.parent = body

    # --- 右耳骨骼 ---
    ear_r = ebs.new("Ear_R")
    ear_r.head = (0.68, 0, 1.75)
    ear_r.tail = (0.68, 0, 2.25)
    ear_r.parent = body

    bpy.ops.object.mode_set(mode='OBJECT')

    print(f"骨骼创建完成: {[b.name for b in arm.data.bones]}")

    # --- 绑定：父子关系 + 自动权重 ---
    bpy.ops.object.select_all(action='DESELECT')
    mesh_obj.select_set(True)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')

    print("自动权重绑定完成")
    return arm


def make_animation(arm):
    """制作待机动画：呼吸 + 耳朵轻微摆动"""
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = 72          # 3秒 @ 24fps
    scene.render.fps = 24

    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='POSE')

    pb = arm.pose.bones

    # 让所有骨骼使用欧拉旋转便于K帧
    for b in pb:
        b.rotation_mode = 'XYZ'

    # --- 关键帧定义 ---
    # 呼吸：身体轻微上下缩放/位移，周期 72 帧
    keyframes = [
        # (frame, body_scale_z, body_loc_z, ear_l_rot, ear_r_rot)
        (1,   1.000, 0.000,  0.0,  0.0),
        (18,  1.025, 0.020,  3.0, -3.0),
        (36,  1.000, 0.000,  0.0,  0.0),
        (54,  0.985, -0.015, -2.0, 2.0),
        (72,  1.000, 0.000,  0.0,  0.0),
    ]

    body_bone = pb.get("Body")
    ear_l = pb.get("Ear_L")
    ear_r = pb.get("Ear_R")

    for (f, sz, lz, el, er) in keyframes:
        scene.frame_set(f)

        if body_bone:
            body_bone.scale = (1.0, 1.0, sz)
            body_bone.location = (0, 0, lz)
            body_bone.keyframe_insert("scale", frame=f)
            body_bone.keyframe_insert("location", frame=f)

        if ear_l:
            ear_l.rotation_euler = (0, math.radians(el), 0)
            ear_l.keyframe_insert("rotation_euler", frame=f)
        if ear_r:
            ear_r.rotation_euler = (0, math.radians(er), 0)
            ear_r.keyframe_insert("rotation_euler", frame=f)

    # 让动画循环平滑（插值改贝塞尔）
    # 注意：Blender 4.4+ 的 Action 改用 layers/slots 结构，fcurves 不再直接挂在 Action 上
    try:
        if arm.animation_data and arm.animation_data.action:
            act = arm.animation_data.action
            fcurves = []
            if hasattr(act, "fcurves"):
                # 旧版 API
                fcurves = list(act.fcurves)
            elif hasattr(act, "layers"):
                # 新版 API：遍历 layers -> strips -> channelbags
                for layer in act.layers:
                    for strip in layer.strips:
                        if hasattr(strip, "channelbags"):
                            for cb in strip.channelbags:
                                fcurves.extend(cb.fcurves)
            for fc in fcurves:
                for kp in fc.keyframe_points:
                    kp.interpolation = 'BEZIER'
            print(f"  插值设置完成，共 {len(fcurves)} 条曲线")
    except Exception as e:
        print(f"  插值设置跳过: {e}")

    bpy.ops.object.mode_set(mode='OBJECT')

    print(f"动画创建完成: {scene.frame_start} - {scene.frame_end} 帧 "
          f"@ {scene.render.fps}fps")


def main():
    print("=" * 60)
    print("骨骼绑定 + 动画")
    print("=" * 60)

    # 清理旧骨架
    for o in list(bpy.data.objects):
        if o.type == 'ARMATURE':
            bpy.data.objects.remove(o, do_unlink=True)

    mesh = bpy.data.objects.get("Chiikawa")
    if mesh is None:
        mesh = merge_parts()
    else:
        print("已存在合并网格 Chiikawa")

    if mesh is None:
        print("错误：无法获得网格")
        return

    arm = create_armature(mesh)
    make_animation(arm)

    out = os.path.join(BASE, "models", "chiikawa_rigged.blend")
    bpy.ops.wm.save_as_mainfile(filepath=out)
    print(f"\n已保存: {out}")
    print("=" * 60)


if __name__ == "__main__":
    main()
