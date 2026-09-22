"""
动画 v2 —— 修正版
==================
问题：给 Body 骨骼做 scale 会连带缩放眼睛/腮红等附着部件，
      导致它们相对位置漂移、穿出身体表面。

方案：只使用【整体位移】+【耳朵旋转】，不做任何缩放。
      - Root 骨骼：整体上下浮动（呼吸感）
      - Ear_L / Ear_R：轻微摇摆
"""
import bpy
import math
import os

BASE = r"D:\C_Relocated\Users\13191\MultiTools\chiikawa动画制作"


def make_animation_v2(arm):
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = 72
    scene.render.fps = 24

    # 清除旧动画
    if arm.animation_data:
        arm.animation_data_clear()

    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='POSE')

    pb = arm.pose.bones
    for b in pb:
        b.rotation_mode = 'XYZ'

    root = pb.get("Root")
    ear_l = pb.get("Ear_L")
    ear_r = pb.get("Ear_R")

    # 关键帧：(帧, root位移Z, 左耳Y旋转, 右耳Y旋转)
    keys = [
        (1,   0.000,   0.0,   0.0),
        (18,  0.045,   5.0,  -5.0),
        (36,  0.000,   0.0,   0.0),
        (54, -0.035,  -4.0,   4.0),
        (72,  0.000,   0.0,   0.0),
    ]

    for (f, dz, el, er) in keys:
        scene.frame_set(f)

        if root:
            # 注意：骨骼局部空间中，Z 轴沿骨骼方向。
            # Root 骨骼从 (0,0,-1) 指向 (0,0,0)，方向是 +Z，
            # 所以 location 的 Y 分量对应世界 Z（Blender 骨骼朝向约定）
            root.location = (0, dz, 0)
            root.keyframe_insert("location", frame=f)

        if ear_l:
            ear_l.rotation_euler = (0, math.radians(el), 0)
            ear_l.keyframe_insert("rotation_euler", frame=f)
        if ear_r:
            ear_r.rotation_euler = (0, math.radians(er), 0)
            ear_r.keyframe_insert("rotation_euler", frame=f)

    # 设置插值
    try:
        act = arm.animation_data.action
        fcurves = []
        if hasattr(act, "fcurves"):
            fcurves = list(act.fcurves)
        elif hasattr(act, "layers"):
            for layer in act.layers:
                for strip in layer.strips:
                    if hasattr(strip, "channelbags"):
                        for cb in strip.channelbags:
                            fcurves.extend(cb.fcurves)
        for fc in fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = 'BEZIER'
        print(f"  插值设置: {len(fcurves)} 条曲线")
    except Exception as e:
        print(f"  插值跳过: {e}")

    bpy.ops.object.mode_set(mode='OBJECT')
    print(f"动画 v2 完成: {scene.frame_start}-{scene.frame_end} 帧")


def reset_pose(arm):
    """确保 rest pose 干净"""
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='POSE')
    for b in arm.pose.bones:
        b.location = (0, 0, 0)
        b.rotation_euler = (0, 0, 0)
        b.scale = (1, 1, 1)
    bpy.ops.object.mode_set(mode='OBJECT')


def main():
    print("=" * 60)
    print("动画 v2（无缩放，纯位移+旋转）")
    print("=" * 60)

    arm = bpy.data.objects.get("ChiikawaRig")
    if not arm:
        print("错误：找不到骨架")
        return

    reset_pose(arm)
    make_animation_v2(arm)

    out = os.path.join(BASE, "models", "chiikawa_rigged.blend")
    bpy.ops.wm.save_as_mainfile(filepath=out)
    print(f"  已保存: {out}")


if __name__ == "__main__":
    main()
