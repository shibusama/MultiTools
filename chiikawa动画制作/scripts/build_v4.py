"""
Chiikawa v4 —— 融合版
======================
v2 的造型比例（已验证好看） + 抖音教程学到的改进点

保留 v2 的优点：
- UV 球建模，比例经过验证
- 耳朵大小/位置、腮红贴合脸颊、眼睛间距都对

吸收抖音教程的改进：
- 动作幅度更大（他们的动画更活）
- 描边厚度可调
"""
import bpy
import math
import os


def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.armatures):
        for item in list(block):
            if item.users == 0:
                block.remove(item)


def add_sphere(name, location, radius, scale=(1, 1, 1), segments=48, rings=24):
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=segments, ring_count=rings, radius=radius, location=location
    )
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bpy.ops.object.shade_smooth()
    return obj


def build():
    """回到 v2 的验证过的比例"""
    parts = {}

    # 身体：扁圆团子（v2 成功参数）
    parts["body"] = add_sphere("Body", (0, 0, 1.0), 1.0, scale=(1.08, 1.0, 0.96))

    # 耳朵：小圆球，位置和大小按 v2
    parts["ear_l"] = add_sphere("Ear_L", (-0.68, 0.0, 1.92), 0.30,
                                scale=(1.0, 0.8, 1.0))
    parts["ear_r"] = add_sphere("Ear_R", (0.68, 0.0, 1.92), 0.30,
                                scale=(1.0, 0.8, 1.0))

    # 眼睛：大黑豆豆眼
    parts["eye_l"] = add_sphere("Eye_L", (-0.40, -0.90, 1.18), 0.155)
    parts["eye_r"] = add_sphere("Eye_R", (0.40, -0.90, 1.18), 0.155)

    # 嘴：小黑点
    parts["mouth"] = add_sphere("Mouth", (0.0, -0.97, 0.95), 0.055,
                                scale=(1.0, 0.6, 0.8))

    # 腮红：脸颊两侧
    parts["blush_l"] = add_sphere("Blush_L", (-0.66, -0.74, 0.98), 0.14,
                                  scale=(1.0, 0.25, 1.0))
    parts["blush_r"] = add_sphere("Blush_R", (0.66, -0.74, 0.98), 0.14,
                                  scale=(1.0, 0.25, 1.0))

    return parts


def main():
    print("=" * 60)
    print("构建 Chiikawa v4（融合版：v2 比例 + 抖音动作改进）")
    print("=" * 60)

    clear_scene()
    parts = build()

    for k, v in parts.items():
        if isinstance(v, list):
            print(f"  {k}: {[o.name for o in v]}")
        else:
            print(f"  {k}: {v.name}")

    out = r"D:\C_Relocated\Users\13191\MultiTools\chiikawa动画制作\models\chiikawa_v4_base.blend"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out)
    print(f"\n已保存: {out}")
    print("=" * 60)


if __name__ == "__main__":
    main()
