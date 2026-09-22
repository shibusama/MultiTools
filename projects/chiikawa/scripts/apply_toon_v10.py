"""
三渲二材质 v10 —— 最终方案（带亮度增益）
==========================================
基于 v9 标定结果：
  - 环境光 0.02 时暗部=0.149、亮部=0.245，间距最大（0.096）
  - 但绝对值偏低，需要在着色器里做亮度增益，把结果拉回正常范围

链路：
  Diffuse(白) -> ShaderToRGB -> RGBToBW -> Math(增益) -> ColorRamp -> Emission
"""
import bpy


def make_toon_material_v10(name, base_color, ramp_pos=0.5,
                           shadow_factor=0.78, gain=3.2):
    """
    v10：真实光照 + 亮度增益 + 量化 + 自发光

    gain 用于把低环境光下的光照值放大到可用范围
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
    out.location = (1100, 0)

    diffuse = nodes.new('ShaderNodeBsdfDiffuse')
    diffuse.location = (-600, 0)
    diffuse.inputs['Color'].default_value = (1.0, 1.0, 1.0, 1.0)

    s2rgb = nodes.new('ShaderNodeShaderToRGB')
    s2rgb.location = (-350, 0)

    bw = nodes.new('ShaderNodeRGBToBW')
    bw.location = (-100, 0)

    # 亮度增益
    gainn = nodes.new('ShaderNodeMath')
    gainn.operation = 'MULTIPLY'
    gainn.location = (100, 0)
    gainn.inputs[1].default_value = gain

    clamp = nodes.new('ShaderNodeClamp')
    clamp.location = (300, 0)

    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.location = (500, 0)
    ramp.color_ramp.interpolation = 'CONSTANT'
    ramp.color_ramp.elements[0].position = ramp_pos
    ramp.color_ramp.elements[1].position = 1.0

    shadow = tuple(c * shadow_factor for c in base_color)
    ramp.color_ramp.elements[0].color = (*shadow, 1.0)
    ramp.color_ramp.elements[1].color = (*base_color, 1.0)

    em = nodes.new('ShaderNodeEmission')
    em.location = (800, 0)
    em.inputs['Strength'].default_value = 1.0

    links.new(diffuse.outputs['BSDF'], s2rgb.inputs['Shader'])
    links.new(s2rgb.outputs['Color'], bw.inputs['Color'])
    links.new(bw.outputs['Val'], gainn.inputs[0])
    links.new(gainn.outputs['Value'], clamp.inputs['Value'])
    links.new(clamp.outputs['Result'], ramp.inputs['Fac'])
    links.new(ramp.outputs['Color'], em.inputs['Color'])
    links.new(em.outputs['Emission'], out.inputs['Surface'])

    return mat
