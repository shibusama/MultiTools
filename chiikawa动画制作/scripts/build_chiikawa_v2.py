"""
Chiikawa (吉伊) 3D 模型生成脚本 v2
===================================
改进点：
- 身体更扁更宽，贴近吉伊的「团子」造型
- 耳朵位置和形状优化（更小、更靠上）
- 嘴巴改成小小的黑色弧线
- 增加腮红（粉色圆片）
- 眼睛更大更圆，符合吉伊设定

用法:
    blender --background --python build_chiikawa_v2.py
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
    """创建 UV 球并应用缩放"""
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


def build_chiikawa_v2():
    """
    吉伊造型要点（参考原作）：
    - 身体：接近正圆的团子，略扁
    - 耳朵：两个小圆，头顶偏两侧，比较小
    - 眼睛：大而圆的黑色豆豆眼，间距适中
    - 嘴：很小很小的黑点/短线
    - 脸颊：淡粉色圆片（腮红）
    """
    parts = {}

    # --- 身体：扁圆团子 ---
    # 半径 1，X 稍宽，Z 稍扁
    body = add_sphere("Body", (0, 0, 1.0), 1.0, scale=(1.08, 1.0, 0.96))
    parts['body'] = body

    # --- 耳朵：小圆球，头顶两侧偏外 ---
    ear_l = add_sphere("Ear_L", (-0.68, 0.0, 1.92), 0.30, scale=(1.0, 0.8, 1.0))
    ear_r = add_sphere("Ear_R", (0.68, 0.0, 1.92), 0.30, scale=(1.0, 0.8, 1.0))
    parts['ears'] = [ear_l, ear_r]

    # --- 眼睛：大黑豆豆眼 ---
    # 贴在球面前方，Z 略高于中心
    eye_l = add_sphere("Eye_L", (-0.40, -0.90, 1.18), 0.155)
    eye_r = add_sphere("Eye_R", (0.40, -0.90, 1.18), 0.155)
    parts['eyes'] = [eye_l, eye_r]

    # --- 嘴巴：很小的黑点，在两眼中间下方 ---
    mouth = add_sphere("Mouth", (0.0, -0.97, 0.95), 0.055,
                       scale=(1.0, 0.6, 0.8))
    parts['mouth'] = mouth

    # --- 腮红：脸颊两侧的粉色圆片 ---
    blush_l = add_sphere("Blush_L", (-0.66, -0.74, 0.98), 0.14,
                         scale=(1.0, 0.25, 1.0))
    blush_r = add_sphere("Blush_R", (0.66, -0.74, 0.98), 0.14,
                         scale=(1.0, 0.25, 1.0))
    parts['blush'] = [blush_l, blush_r]

    return parts


def main():
    print("=" * 60)
    print("构建 Chiikawa (吉伊) 模型 v2")
    print("=" * 60)

    clear_scene()
    parts = build_chiikawa_v2()

    print(f"  身体: {parts['body'].name}")
    print(f"  耳朵: {len(parts['ears'])} 个")
    print(f"  眼睛: {len(parts['eyes'])} 个")
    print(f"  嘴巴: {parts['mouth'].name}")
    print(f"  腮红: {len(parts['blush'])} 个")

    out = r"D:\C_Relocated\Users\13191\MultiTools\chiikawa动画制作\models\chiikawa_base.blend"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out)
    print(f"\n已保存: {out}")
    print("=" * 60)


if __name__ == "__main__":
    main()
