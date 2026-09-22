"""
三渲二材质 v9 —— 抖音方案（真实灯光 + ShaderToRGB + 量化 + 自发光）
=====================================================================
关键修正（相对 v6/v8 的错误）：
  之前手工算法线点乘，绕了一大圈还失败。
  正确做法是让 EEVEE 用真实灯光算光照，用 ShaderToRGB 取回结果再量化。

  实测验证：加真实灯光后 ShaderToRGB 输出标准差 0.203，分布 0.31~0.95，
  完全可用。之前判断它"失效"是因为场景没有灯光。

节点链路：
  Diffuse BSDF(白色) -> ShaderToRGB -> RGBToBW -> ColorRamp -> Emission
                        ↑
              真实灯光提供照明（EEVEE 内部用完整法线，无裁剪）
"""
import bpy


def make_toon_material_v9(name, base_color, ramp_pos=0.5, shadow_factor=0.78):
    """
    抖音方案的三渲二材质。

    参数:
        base_color  : 受光面颜色 (线性空间)
        ramp_pos    : ColorRamp 阈值（决定明暗分界）
        shadow_factor: 阴影色相对受光色的亮度比
    """
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    mat.use_backface_culling = True

    nt = mat.node_tree
    nodes, links = nt.nodes, nt.links
    nodes.clear()

    out = nodes.new('ShaderNodeOutputMaterial')
    out.location = (900, 0)

    # 1. 漫射接收真实光照（白色，只关心光照强度）
    diffuse = nodes.new('ShaderNodeBsdfDiffuse')
    diffuse.location = (-500, 0)
    diffuse.inputs['Color'].default_value = (1.0, 1.0, 1.0, 1.0)

    # 2. ShaderToRGB —— 取回光照结果（配合真实灯光才有效）
    s2rgb = nodes.new('ShaderNodeShaderToRGB')
    s2rgb.location = (-250, 0)

    # 3. 转灰度
    bw = nodes.new('ShaderNodeRGBToBW')
    bw.location = (0, 0)

    # 4. 量化成硬边色块
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.location = (200, 0)
    ramp.color_ramp.interpolation = 'CONSTANT'
    ramp.color_ramp.elements[0].position = ramp_pos
    ramp.color_ramp.elements[1].position = 1.0

    shadow = tuple(c * shadow_factor for c in base_color)
    ramp.color_ramp.elements[0].color = (*shadow, 1.0)
    ramp.color_ramp.elements[1].color = (*base_color, 1.0)

    # 5. 自发光输出（抖音教程强调的点）
    em = nodes.new('ShaderNodeEmission')
    em.location = (550, 0)
    em.inputs['Strength'].default_value = 1.0

    links.new(diffuse.outputs['BSDF'], s2rgb.inputs['Shader'])
    links.new(s2rgb.outputs['Color'], bw.inputs['Color'])
    links.new(bw.outputs['Val'], ramp.inputs['Fac'])
    links.new(ramp.outputs['Color'], em.inputs['Color'])
    links.new(em.outputs['Emission'], out.inputs['Surface'])

    return mat


def make_outline_material(name="Outline", color=(0.0, 0.0, 0.0)):
    """描边材质：纯自发光黑"""
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    mat.use_backface_culling = True

    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    out.location = (300, 0)
    em = nt.nodes.new('ShaderNodeEmission')
    em.location = (0, 0)
    em.inputs['Color'].default_value = (*color, 1.0)
    em.inputs['Strength'].default_value = 1.0
    nt.links.new(em.outputs['Emission'], out.inputs['Surface'])
    return mat
