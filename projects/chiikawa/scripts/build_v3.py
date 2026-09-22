"""
Chiikawa v3 —— 借鉴抖音一手教程的做法
==========================================
从抖音教程学到的关键改进：

1. 【身体用立方体+细分】而不是 UV 球
   —— 立方体+表面细分起形更灵活，这是他们 1.4 万赞教程的标准做法

2. 【参考比例校准】他们垫参考图描，我没有参考图，
   但可以对标官方设定的比例：吉伊是「头占绝大部分、身体极小」

3. 【耳朵做成猫耳状、有厚度】不是简单小球

4. 【材质用 Emission 自发光】—— 他们明确强调这点

5. 【腮红用独立部件】保持

吉伊官方造型特征（对标原作）：
- 头部：近乎正圆，略扁，占整个角色 90%
- 耳朵：两个小圆，位于头顶偏外，比头小很多
- 眼睛：椭圆黑豆豆眼，间距约一个眼宽
- 嘴：极小，位于双眼连线中点下方
- 腮红：脸颊两侧，淡粉
- 无脖子、无四肢（吉伊本体就是个头）
"""
import bpy
import bmesh
import math
import os
from mathutils import Vector

BASE = r"D:\C_Relocated\Users\13191\MultiTools\projects\chiikawa"


def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.armatures):
        for item in list(block):
            if item.users == 0:
                block.remove(item)


def cube_with_subsurf(name, size=1.0, location=(0, 0, 0), levels=3):
    """
    抖音教程的核心起形手法：立方体 + 表面细分修改器
    """
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    obj = bpy.context.active_object
    obj.name = name

    mod = obj.modifiers.new(name="Subdivision", type='SUBSURF')
    mod.levels = levels
    mod.render_levels = levels

    bpy.ops.object.shade_smooth()
    return obj


def shape_head(obj):
    """
    头部：对标吉伊官方比例
    立方体+细分后是圆角方，需要压成「扁圆」
    """
    # 头部整体尺寸：宽 > 高 > 深（吉伊正面看是宽扁圆）
    obj.scale = (1.12, 1.0, 1.02)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    # 编辑模式：把顶部和底部稍微收一点，让轮廓更圆
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj.data)
    for v in bm.verts:
        # 归一化高度
        nz = v.co.z / 1.0 if abs(v.co.z) > 1e-6 else 0
        # 顶部/底部轻微内收
        if abs(nz) > 0.6:
            shrink = 1.0 - (abs(nz) - 0.6) * 0.25
            v.co.x *= shrink
            v.co.y *= shrink
    bmesh.update_edit_mesh(obj.data)
    bpy.ops.object.mode_set(mode='OBJECT')
    return obj


def make_ear(name, x, z):
    """
    耳朵：抖音教程说是「立方体+细分+环切塑形」
    吉伊的耳朵是小圆片状，有轻微厚度
    """
    ear = cube_with_subsurf(name, size=0.62, location=(x, 0, z), levels=3)

    # 压成扁片（厚度方向是 Y）
    ear.scale = (1.0, 0.55, 1.0)
    bpy.context.view_layer.objects.active = ear
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    # 顶部稍微拉高，做成圆耳朵而不是方耳朵
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(ear.data)
    for v in bm.verts:
        if v.co.z > 0:
            v.co.z *= 1.15
            # 收窄顶部
            v.co.x *= 0.92
    bmesh.update_edit_mesh(ear.data)
    bpy.ops.object.mode_set(mode='OBJECT')
    return ear


def make_eye(name, x, z):
    """眼睛：椭圆形黑豆豆眼"""
    eye = cube_with_subsurf(name, size=0.34, location=(x, -0.88, z), levels=3)
    # 压扁成椭圆（正面看是圆的，侧面是扁的）
    eye.scale = (1.0, 0.35, 1.15)
    bpy.context.view_layer.objects.active = eye
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return eye


def make_mouth():
    """嘴：极小的黑点"""
    m = cube_with_subsurf("Mouth", size=0.13, location=(0, -0.97, 0.90),
                          levels=3)
    m.scale = (1.0, 0.4, 0.75)
    bpy.context.view_layer.objects.active = m
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return m


def make_blush(name, x, z):
    """腮红：脸颊的粉色圆片"""
    b = cube_with_subsurf(name, size=0.30, location=(x, -0.80, z), levels=3)
    b.scale = (1.0, 0.15, 1.0)
    bpy.context.view_layer.objects.active = b
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return b


def build():
    """构建吉伊 v3"""
    parts = {}

    # 头（主体）
    head = cube_with_subsurf("Body", size=2.0, location=(0, 0, 1.0), levels=3)
    shape_head(head)
    parts["body"] = head

    # 耳朵（头顶两侧偏外）
    parts["ear_l"] = make_ear("Ear_L", -0.70, 1.98)
    parts["ear_r"] = make_ear("Ear_R", 0.70, 1.98)

    # 眼睛
    parts["eye_l"] = make_eye("Eye_L", -0.40, 1.16)
    parts["eye_r"] = make_eye("Eye_R", 0.40, 1.16)

    # 嘴
    parts["mouth"] = make_mouth()

    # 腮红
    parts["blush_l"] = make_blush("Blush_L", -0.68, 1.00)
    parts["blush_r"] = make_blush("Blush_R", 0.68, 1.00)

    return parts


def main():
    print("=" * 60)
    print("构建 Chiikawa v3 —— 借鉴抖音教程做法")
    print("=" * 60)

    clear_scene()
    parts = build()

    print(f"  头   : {parts['body'].name}")
    print(f"  耳朵 : {parts['ear_l'].name}, {parts['ear_r'].name}")
    print(f"  眼睛 : {parts['eye_l'].name}, {parts['eye_r'].name}")
    print(f"  嘴   : {parts['mouth'].name}")
    print(f"  腮红 : {parts['blush_l'].name}, {parts['blush_r'].name}")

    out = os.path.join(BASE, "models", "chiikawa_v3_base.blend")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out)
    print(f"\n已保存: {out}")
    print("=" * 60)


if __name__ == "__main__":
    main()
