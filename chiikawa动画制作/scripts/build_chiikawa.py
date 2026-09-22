"""
Chiikawa (吉伊) 3D 模型生成脚本
================================
用 Blender Python API 程序化生成吉伊卡哇角色模型。

设计：
- 吉伊造型极简：白色圆球身体 + 两只小耳朵 + 豆豆眼 + 小嘴
- 全部用基本几何体变形组合，便于后续绑骨和渲染

用法:
    blender --background --python build_chiikawa.py
"""

import bpy
import bmesh
import math
from mathutils import Vector, Matrix

# ---------------------------------------------------------------- 工具函数

def clear_scene():
    """清空场景所有对象"""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    # 清理孤立数据
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.armatures):
        for item in list(block):
            if item.users == 0:
                block.remove(item)


def create_uv_sphere(name, location=(0, 0, 0), radius=1.0,
                     segments=32, rings=16):
    """创建一个 UV 球"""
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=segments, ring_count=rings,
        radius=radius, location=location
    )
    obj = bpy.context.active_object
    obj.name = name
    bpy.ops.object.shade_smooth()
    return obj


def scale_object(obj, scale):
    """按给定比例缩放对象（在对象模式）"""
    obj.scale = scale
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)


def join_objects(objects, name):
    """合并多个对象"""
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    result = bpy.context.active_object
    result.name = name
    return result


# ---------------------------------------------------------------- 建模

def build_chiikawa():
    """
    构建吉伊模型。
    吉伊特征：
    - 大圆球身体（白色）
    - 头顶两只小圆耳朵
    - 两颗黑豆豆眼
    - 小小的嘴巴
    """
    parts = {}

    # --- 身体：一个略扁的球 ---
    body = create_uv_sphere("Body", location=(0, 0, 1.0), radius=1.0)
    # 稍微压扁一点，让造型更 Q
    scale_object(body, (1.0, 0.95, 0.92))
    parts['body'] = body

    # --- 耳朵：两个小球，放头顶两侧 ---
    ear_l = create_uv_sphere("Ear_L", location=(-0.55, 0.0, 1.85), radius=0.34)
    scale_object(ear_l, (1.0, 0.75, 1.0))
    ear_r = create_uv_sphere("Ear_R", location=(0.55, 0.0, 1.85), radius=0.34)
    scale_object(ear_r, (1.0, 0.75, 1.0))
    parts['ears'] = [ear_l, ear_r]

    # --- 眼睛：两个小黑球，贴在身体前表面 ---
    eye_l = create_uv_sphere("Eye_L", location=(-0.32, -0.86, 1.15), radius=0.13)
    eye_r = create_uv_sphere("Eye_R", location=(0.32, -0.86, 1.15), radius=0.13)
    parts['eyes'] = [eye_l, eye_r]

    # --- 腮红/嘴巴区域（后续着色用） ---
    # 嘴：一个小扁球
    mouth = create_uv_sphere("Mouth", location=(0.0, -0.94, 0.92), radius=0.09)
    scale_object(mouth, (1.3, 0.5, 0.7))
    parts['mouth'] = mouth

    return parts


def add_subdivision(obj, levels=1):
    """加细分表面修改器，让模型更圆润"""
    mod = obj.modifiers.new(name="Subdivision", type='SUBSURF')
    mod.levels = levels
    mod.render_levels = levels
    return mod


# ---------------------------------------------------------------- 主流程

def main():
    print("=" * 60)
    print("开始构建 Chiikawa (吉伊) 模型")
    print("=" * 60)

    clear_scene()

    parts = build_chiikawa()

    print(f"  身体   : {parts['body'].name}")
    print(f"  耳朵   : {len(parts['ears'])} 个")
    print(f"  眼睛   : {len(parts['eyes'])} 个")
    print(f"  嘴巴   : {parts['mouth'].name}")

    # 保存
    out = r"D:\C_Relocated\Users\13191\MultiTools\chiikawa动画制作\models\chiikawa_base.blend"
    import os
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out)
    print(f"\n已保存: {out}")
    print("=" * 60)

    # 输出对象清单供检查
    print("\n场景对象清单:")
    for obj in bpy.data.objects:
        print(f"  - {obj.name} @ {tuple(round(v,2) for v in obj.location)}")


if __name__ == "__main__":
    main()
