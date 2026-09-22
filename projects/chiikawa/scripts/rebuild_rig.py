"""
重建骨骼 v2 —— 骨骼位置基于网格实际坐标
（网格原点在 (0,0,1)，局部 Z 范围 -1.0~1.28）
"""
import bpy
import math
import os

BASE = r"D:\C_Relocated\Users\13191\MultiTools\projects\chiikawa"


def rebuild_armature(mesh_obj):
    # 删除旧骨架
    for o in list(bpy.data.objects):
        if o.type == 'ARMATURE':
            bpy.data.objects.remove(o, do_unlink=True)

    bpy.ops.object.armature_add(location=(0, 0, 0))
    arm = bpy.context.active_object
    arm.name = "ChiikawaRig"

    bpy.ops.object.mode_set(mode='EDIT')
    ebs = arm.data.edit_bones
    for b in list(ebs):
        ebs.remove(b)

    # 网格原点在 (0,0,1)，局部坐标：
    #   身体中心 ≈ (0,0,0)，Z 范围 -1.0 ~ 1.0
    #   耳朵中心 ≈ Z 0.9, X ±0.68
    root = ebs.new("Root")
    root.head = (0, 0, -1.0)
    root.tail = (0, 0, 0.0)

    body = ebs.new("Body")
    body.head = (0, 0, 0.0)
    body.tail = (0, 0, 0.95)
    body.parent = root

    ear_l = ebs.new("Ear_L")
    ear_l.head = (-0.68, 0, 0.85)
    ear_l.tail = (-0.68, 0, 1.30)
    ear_l.parent = body

    ear_r = ebs.new("Ear_R")
    ear_r.head = (0.68, 0, 0.85)
    ear_r.tail = (0.68, 0, 1.30)
    ear_r.parent = body

    bpy.ops.object.mode_set(mode='OBJECT')
    print(f"  骨骼: {[b.name for b in arm.data.bones]}")
    return arm


def main():
    print("=" * 60)
    print("重建骨骼 v2")
    print("=" * 60)

    mesh = bpy.data.objects.get("Chiikawa")
    if not mesh:
        print("错误：找不到 Chiikawa 网格")
        return

    # 记录动画数据前先清
    arm = rebuild_armature(mesh)

    # 重新做动画
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from rig_and_animate import make_animation
    make_animation(arm)

    out = os.path.join(BASE, "models", "chiikawa_rigged.blend")
    bpy.ops.wm.save_as_mainfile(filepath=out)
    print(f"  已保存: {out}")


if __name__ == "__main__":
    main()
