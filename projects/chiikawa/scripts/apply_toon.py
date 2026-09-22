"""
Chiikawa 三渲二 (NPR / Toon Shading) 材质搭建脚本
==================================================
实现经典卡通着色：
    Diffuse BSDF -> Shader to RGB -> ColorRamp -> Material Output

关键点：
1. ColorRamp 插值设为 CONSTANT（常值），产生硬边阴影
2. 滑块位置 0.5，把光照切成明暗两块
3. 只用 EEVEE 引擎（Cycles 不支持 Shader to RGB）

额外实现：
- 描边（Solidify + Backface Culling 法）

用法:
    blender --background <blend文件> --python apply_toon.py
"""

import bpy
import math
import os

# ---------------------------------------------------------------- 材质创建

def make_toon_material(name, base_color, shadow_color=None,
                       ramp_pos=0.5, shadow_factor=0.75):
    """
    创建一个三渲二卡通材质。

    参数:
        name        : 材质名
        base_color  : 受光面颜色 (R, G, B)
        shadow_color: 阴影面颜色，None 则自动从 base_color 压暗
        ramp_pos    : ColorRamp 滑块位置，默认 0.5
        shadow_factor: 自动阴影色的压暗系数
    """
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    mat.use_backface_culling = True   # 描边需要

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # 清空默认节点
    nodes.clear()

    # --- 创建节点 ---
    out = nodes.new('ShaderNodeOutputMaterial')
    out.location = (600, 0)

    # 1. Diffuse BSDF —— 光照的基础（不用 Principled，因为要能接 Shader to RGB）
    diffuse = nodes.new('ShaderNodeBsdfDiffuse')
    diffuse.location = (-400, 0)
    diffuse.inputs['Color'].default_value = (*base_color, 1.0)

    # 2. Shader to RGB —— 把光照结果转成颜色数据（EEVEE 专属）
    s2rgb = nodes.new('ShaderNodeShaderToRGB')
    s2rgb.location = (-150, 0)

    # 3. ColorRamp —— 把连续明暗压成硬边色块
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.location = (100, 0)
    ramp.color_ramp.interpolation = 'CONSTANT'   # ★核心：常值插值
    ramp.color_ramp.elements[0].position = ramp_pos
    ramp.color_ramp.elements[1].position = 1.0

    # 计算阴影色
    if shadow_color is None:
        shadow_color = tuple(c * shadow_factor for c in base_color)

    # 左侧 = 阴影色，右侧 = 受光色
    ramp.color_ramp.elements[0].color = (*shadow_color, 1.0)
    ramp.color_ramp.elements[1].color = (*base_color, 1.0)

    # --- 连线 ---
    links.new(diffuse.outputs['BSDF'], s2rgb.inputs['Shader'])
    links.new(s2rgb.outputs['Color'], ramp.inputs['Fac'])
    links.new(ramp.outputs['Color'], out.inputs['Surface'])

    return mat


def make_outline_material(name="Outline", color=(0.0, 0.0, 0.0)):
    """纯黑色描边材质（配合 Solidify 修改器使用）"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    mat.use_backface_culling = True   # ★只显示背面，形成轮廓

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out = nodes.new('ShaderNodeOutputMaterial')
    out.location = (300, 0)

    emission = nodes.new('ShaderNodeEmission')
    emission.location = (0, 0)
    emission.inputs['Color'].default_value = (*color, 1.0)
    emission.inputs['Strength'].default_value = 1.0

    links.new(emission.outputs['Emission'], out.inputs['Surface'])
    return mat


def add_outline(obj, thickness=0.03, mat=None):
    """
    给对象加描边：Solidify 修改器沿法线外扩 + 背面剔除。

    v3 修正：材质槽处理方式
    - 确保对象有 2 个材质槽：[0]=本体材质, [1]=描边材质
    - Solidify 把外扩的壳用 material_offset 指向槽 1
    """
    if mat is None:
        mat = bpy.data.materials.get("Outline") or make_outline_material()

    # 确保描边材质在槽 1
    mats = [m for m in obj.data.materials if m]
    if mat.name not in [m.name for m in mats]:
        obj.data.materials.append(mat)

    mats = [m for m in obj.data.materials if m]
    outline_slot = [m.name for m in mats].index(mat.name)

    mod = obj.modifiers.new(name="Outline", type='SOLIDIFY')
    mod.thickness = thickness
    mod.offset = 1.0                     # 完全向外扩
    mod.use_flip_normals = True          # 翻转法线 —— 只渲染背面
    mod.use_rim = False
    # 关键：让外扩的壳（含正面和背面）都使用描边材质槽
    mod.material_offset = outline_slot
    mod.material_offset_rim = outline_slot

    print(f"    [描边] 槽位={outline_slot} 厚度={thickness} 材质数={len(mats)}")
    return mod


# ---------------------------------------------------------------- 场景设置

def setup_render():
    """配置 EEVEE 渲染（三渲二必须用 EEVEE）"""
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = 1080
    scene.render.resolution_y = 1080
    scene.render.film_transparent = False

    # 色彩管理：Standard 让颜色更接近原色（Filmic 会偏灰）
    try:
        scene.view_settings.view_transform = 'Standard'
    except Exception:
        pass

    print(f"  渲染引擎: {scene.render.engine}")
    print(f"  分辨率  : {scene.render.resolution_x}x{scene.render.resolution_y}")


def setup_light():
    """
    布置灯光 v4：制造明确的明暗落差。

    根因分析（deep_diagnose.py 结论）：
    之前「整个正面全亮」不是因为阈值设错，而是因为
    环境光底座(0.55) + 太阳光(3.5) 叠加把正面像素推到饱和(≈1.0)，
    无论 ColorRamp 阈值设多少都判为亮部。

    解决：让光只从一个强方向来，且强度适中，
    使球面正对光的一侧饱和、背离的一侧衰减到阈值以下。
    """
    for obj in list(bpy.data.objects):
        if obj.type == 'LIGHT':
            bpy.data.objects.remove(obj, do_unlink=True)

    # v5: 主体光照值实测只有 0.25（太暗），需要提亮
    # 主光角度调整为左前上方 45°，能量提高，让受光面占正面约 60%
    bpy.ops.object.light_add(type='SUN', location=(-4, -5, 5))
    key = bpy.context.active_object
    key.name = "KeyLight"
    key.data.energy = 5.0                 # 提高，让正面主体光照值到 0.5~0.9
    key.data.angle = math.radians(1)
    key.rotation_euler = (math.radians(52), 0, math.radians(-32))

    # 轻微的轮廓光，避免暗部死黑
    bpy.ops.object.light_add(type='SUN', location=(6, -2, 2))
    rim = bpy.context.active_object
    rim.name = "RimLight"
    rim.data.energy = 0.5
    rim.rotation_euler = (math.radians(80), 0, math.radians(70))

    return key, rim


def setup_camera():
    """设置相机，对准角色"""
    bpy.ops.object.camera_add(location=(0, -6.5, 1.6))
    cam = bpy.context.active_object
    cam.name = "Camera"
    cam.rotation_euler = (math.radians(88), 0, 0)
    cam.data.lens = 60

    bpy.context.scene.camera = cam

    # 用跟踪约束对准身体中心
    body = bpy.data.objects.get("Body")
    if body:
        c = cam.constraints.new(type='TRACK_TO')
        c.target = body
        c.track_axis = 'TRACK_NEGATIVE_Z'
        c.up_axis = 'UP_Y'
    return cam


def setup_world():
    """
    设置世界背景色 v4。

    关键：环境光强度要压得很低！
    之前 0.92*0.6 ≈ 0.55 的环境光底座，本身就接近 ColorRamp 阈值，
    导致所有像素被抬到亮部，三渲二的明暗分界完全出不来。

    做法：世界背景用「纯色可见但照明贡献接近 0」的配置 ——
    用 Light Path 节点把相机射线和环境照明分开。
    """
    world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True

    nt = world.node_tree
    nt.nodes.clear()

    out = nt.nodes.new('ShaderNodeOutputWorld')
    out.location = (600, 0)

    # 混合：相机看到的用背景色，照明用的用暗色
    mix = nt.nodes.new('ShaderNodeMixShader')
    mix.location = (400, 0)

    lp = nt.nodes.new('ShaderNodeLightPath')
    lp.location = (0, 200)

    # 背景（相机可见）—— 浅灰蓝
    bg_visible = nt.nodes.new('ShaderNodeBackground')
    bg_visible.location = (200, 150)
    bg_visible.inputs['Color'].default_value = (0.86, 0.88, 0.92, 1.0)
    bg_visible.inputs['Strength'].default_value = 1.0

    # 环境照明（影响物体）—— 极暗，避免填平阴影
    bg_light = nt.nodes.new('ShaderNodeBackground')
    bg_light.location = (200, -80)
    bg_light.inputs['Color'].default_value = (0.6, 0.65, 0.75, 1.0)
    bg_light.inputs['Strength'].default_value = 0.10   # ★关键：压到 0.10

    nt.links.new(lp.outputs['Is Camera Ray'], mix.inputs['Fac'])
    nt.links.new(bg_light.outputs['Background'], mix.inputs[1])
    nt.links.new(bg_visible.outputs['Background'], mix.inputs[2])
    nt.links.new(mix.outputs['Shader'], out.inputs['Surface'])

    print("  世界背景: 相机可见=浅灰, 环境照明强度=0.10 (低)")


# ---------------------------------------------------------------- 主流程

def main():
    print("=" * 60)
    print("应用三渲二材质到 Chiikawa 模型")
    print("=" * 60)

    # 定义各部位材质（颜色用 sRGB 近似值，Blender 输入是线性，需转换）
    def srgb_to_linear(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    def col(r, g, b):
        return tuple(srgb_to_linear(v) for v in (r, g, b))

    # v5: 基于实测光照分布设定阈值
    # debug_lightvalue.py 实测：主体光照值集中在 0.2~0.3，受光面 0.7~0.95
    # => 阈值设在 0.45 左右，正好把主体切成「大部分亮 + 一侧暗」
    materials = {
        # 身体：米白
        "Body":  make_toon_material("M_Body",  col(0.98, 0.97, 0.94),
                                    ramp_pos=0.45, shadow_factor=0.78),
        "Ear_L": make_toon_material("M_Ear_L", col(0.98, 0.97, 0.94),
                                    ramp_pos=0.45, shadow_factor=0.78),
        "Ear_R": make_toon_material("M_Ear_R", col(0.98, 0.97, 0.94),
                                    ramp_pos=0.45, shadow_factor=0.78),
        # 眼睛：纯黑
        "Eye_L": make_toon_material("M_Eye_L", col(0.05, 0.05, 0.07),
                                    ramp_pos=0.3, shadow_factor=0.95),
        "Eye_R": make_toon_material("M_Eye_R", col(0.05, 0.05, 0.07),
                                    ramp_pos=0.3, shadow_factor=0.95),
        # 嘴巴：黑色小点
        "Mouth": make_toon_material("M_Mouth", col(0.15, 0.12, 0.12),
                                    ramp_pos=0.4, shadow_factor=0.9),
        # 腮红：淡粉
        "Blush_L": make_toon_material("M_Blush", col(0.96, 0.72, 0.74),
                                      ramp_pos=0.45, shadow_factor=0.85),
        "Blush_R": make_toon_material("M_Blush", col(0.96, 0.72, 0.74),
                                      ramp_pos=0.45, shadow_factor=0.85),
    }

    # 应用材质 + 描边（v2: 描边加粗到 0.055）
    outline_mat = make_outline_material()
    for obj_name, mat in materials.items():
        obj = bpy.data.objects.get(obj_name)
        if not obj:
            print(f"  [跳过] 未找到 {obj_name}")
            continue
        obj.data.materials.clear()
        obj.data.materials.append(mat)
        # 身体和耳朵描边；眼睛/嘴/腮红太小，描边反而糊
        if obj_name in ("Body", "Ear_L", "Ear_R"):
            add_outline(obj, thickness=0.055, mat=outline_mat)
            print(f"  {obj_name:8s} -> {mat.name} + 描边")
        else:
            print(f"  {obj_name:8s} -> {mat.name}")

    setup_render()
    setup_light()
    setup_camera()
    setup_world()

    # 保存
    out = r"D:\C_Relocated\Users\13191\MultiTools\projects\chiikawa\models\chiikawa_toon.blend"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out)
    print(f"\n已保存: {out}")
    print("=" * 60)


if __name__ == "__main__":
    main()
