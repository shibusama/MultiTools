"""
三渲二材质 v7 —— 修正法线裁剪问题
=====================================
根因（probe_normal.py 实测）：
  Geometry.Normal 输出的是红绿蓝打包的向量，但 Blender 在把
  向量接入着色器 socket 时，负值会被截断为 0（法线模长实测只有 0.607，
  应该为 1.0）。这直接毁掉了 Lambert 计算需要的符号信息。

解法：改用【Shader to RGB 的替代路径】—— 
不再手工算法线点乘，而是让 EEVEE 自己算光照，再用「颜色→灰度→阈值」量化。

具体做法：
  1. 用 Diffuse BSDF 接收真实光照（EEVEE 内部用完整法线信息，无裁剪）
  2. 把 Diffuse 的输出接 Emission 的强度 —— 这样能得到光照强度
  3. 但为了拿到「光照值」而不受颜色影响，用白色 Diffuse + 分离光照

更简单可靠的方案：用【Layer Weight / Fresnel】做边缘暗化，
或者直接用【点光源 + 真实漫射 + ColorRamp 后处理】。

最终选择：用 Diffuse BSDF 接到 Emission Strength，
配合白色基底，让 ColorRamp 在亮度域做量化。
"""
import bpy
import math


def make_toon_material_v7(name, base_color, ramp_pos=0.5, shadow_factor=0.78,
                          light_dir=(-0.5, -0.55, 0.67)):
    """
    v7 方案：用真实的 Diffuse 光照，通过「颜色转灰度 → 量化」做三渲二。

    流程：
      Diffuse BSDF (白色) --\
                             --> 混合到 Emission Strength --> ColorRamp
      实际光照由场景灯光提供 --/

    关键：不手工算法线点乘，交给 EEVEE 内部处理（法线不裁剪）
    """
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    mat.use_backface_culling = True

    nt = mat.node_tree
    nodes = nt.nodes
    links = nt.links
    nodes.clear()

    out = nodes.new('ShaderNodeOutputMaterial')
    out.location = (900, 0)

    # --- 真实的漫射着色（EEVEE 内部用完整法线，无裁剪问题）---
    diffuse = nodes.new('ShaderNodeBsdfDiffuse')
    diffuse.location = (-400, 0)
    diffuse.inputs['Color'].default_value = (1.0, 1.0, 1.0, 1.0)  # 纯白，只取光照

    # --- 把着色结果转成颜色（这是 Shader to RGB 的作用）---
    # 替代：用 Emission 的 Strength 接不了着色器，所以改用「光照探针」方式
    # 实际可行做法：直接用 Diffuse 的颜色输出 —— 但要经过 Light Path
    s2rgb = nodes.new('ShaderNodeShaderToRGB')
    s2rgb.location = (-150, 0)

    # --- 转灰度 ---
    rgb2bw = nodes.new('ShaderNodeRGBToBW')
    rgb2bw.location = (60, 0)

    # --- 量化 ---
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.location = (250, 0)
    ramp.color_ramp.interpolation = 'CONSTANT'
    ramp.color_ramp.elements[0].position = ramp_pos
    ramp.color_ramp.elements[1].position = 1.0

    shadow = tuple(c * shadow_factor for c in base_color)
    ramp.color_ramp.elements[0].color = (*shadow, 1.0)
    ramp.color_ramp.elements[1].color = (*base_color, 1.0)

    em = nodes.new('ShaderNodeEmission')
    em.location = (600, 0)
    em.inputs['Strength'].default_value = 1.0

    links.new(diffuse.outputs['BSDF'], s2rgb.inputs['Shader'])
    links.new(s2rgb.outputs['Color'], rgb2bw.inputs['Color'])
    links.new(rgb2bw.outputs['Val'], ramp.inputs['Fac'])
    links.new(ramp.outputs['Color'], em.inputs['Color'])
    links.new(em.outputs['Emission'], out.inputs['Surface'])

    return mat
