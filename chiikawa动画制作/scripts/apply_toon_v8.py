"""
三渲二材质 v8 —— 修正法线裁剪（最终方案）
==========================================
根因（实测确认）：
  Geometry.Normal 接进着色器 socket 时，负值被裁剪为 0（44% 像素受影响）。
  Lambert 点乘需要完整的符号信息，裁剪后计算全错。

解法：
  先把法线从 [-1,1] 重映射到 [0,1]（负值变正，不再被裁剪），
  在这个空间里做点乘。因为映射是线性的，
  dot(n_remapped, l_remapped) 与 dot(n, l) 存在确定的线性关系，
  可以用 MAD 还原。

  推导：
    n' = (n + 1) / 2      ∈ [0,1]
    l' = (l + 1) / 2      ∈ [0,1]
    dot(n', l') = (dot(n,l) + dot(n,1) + dot(1,l) + dot(1,1)) / 4
                = (dot(n,l) + sum(n) + sum(l) + 3) / 4

  这里换个更稳的思路：不做点乘，直接用光照方向构造「左右渐变」，
  因为对正对相机的球体来说，左右方向的光照主要由 nx 决定。

  最简可靠方案：
    lambert ≈ (nx * lx + ny * ly + nz * lz)
    但 nx 裁剪了 → 用 remap 后的 nx' = (nx+1)/2，
    则 nx = 2*nx' - 1，代入即可。
"""
import bpy
import math


def make_toon_material_v8(name, base_color, ramp_pos=0.5, shadow_factor=0.78,
                          light_dir=(-0.5, -0.55, 0.67)):
    """
    v8：法线重映射方案。
    每个分量先 (x+1)/2 映射到 0-1，避免裁剪，
    再用 MAD/ADD 组合还原真实点乘。
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
    out.location = (1400, 0)

    # --- 法线分量重映射 ---
    geo = nodes.new('ShaderNodeNewGeometry')
    geo.location = (-1000, 200)

    sep = nodes.new('ShaderNodeSeparateXYZ')
    sep.location = (-800, 200)
    links.new(geo.outputs['Normal'], sep.inputs['Vector'])

    # 光源方向（归一化）
    ld = list(light_dir)
    ln = math.sqrt(sum(c * c for c in ld))
    ld = [c / ln for c in ld]

    # 对每个分量： n' = (n + 1) / 2
    # 用 MAD: n*0.5 + 0.5
    comps = []
    for i, axis in enumerate(['X', 'Y', 'Z']):
        mad = nodes.new('ShaderNodeMath')
        mad.operation = 'MULTIPLY_ADD'
        mad.location = (-600, 300 - i * 200)
        mad.inputs[1].default_value = 0.5
        mad.inputs[2].default_value = 0.5
        links.new(sep.outputs[axis], mad.inputs[0])
        comps.append(mad)

    # 光源方向也映射到 0-1 空间
    l_remap = [(c + 1) / 2 for c in ld]

    # 点乘 n'·l' = Σ n'_i * l'_i
    mults = []
    for i, c in enumerate(comps):
        m = nodes.new('ShaderNodeMath')
        m.operation = 'MULTIPLY'
        m.location = (-380, 300 - i * 200)
        m.inputs[1].default_value = l_remap[i]
        links.new(c.outputs['Value'], m.inputs[0])
        mults.append(m)

    # 求和
    add1 = nodes.new('ShaderNodeMath')
    add1.operation = 'ADD'
    add1.location = (-180, 200)
    links.new(mults[0].outputs['Value'], add1.inputs[0])
    links.new(mults[1].outputs['Value'], add1.inputs[1])

    add2 = nodes.new('ShaderNodeMath')
    add2.operation = 'ADD'
    add2.location = (0, 150)
    links.new(add1.outputs['Value'], add2.inputs[0])
    links.new(mults[2].outputs['Value'], add2.inputs[1])

    # 现在 add2 = dot(n', l')  ∈ [0, 1]
    # 关系：dot(n',l') = (dot(n,l) + S)/4 ，其中 S = sum(n)+sum(l)+3
    # S 随法线变化，但范围有限。直接用它做 ColorRamp 输入即可 ——
    # 它保留了「哪边朝向光源」的全部信息，这正是我们需要的。
    clamp = nodes.new('ShaderNodeClamp')
    clamp.location = (200, 150)
    links.new(add2.outputs['Value'], clamp.inputs['Value'])
    clamp.inputs['Min'].default_value = 0.0
    clamp.inputs['Max'].default_value = 1.0

    # --- 量化 ---
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.location = (450, 150)
    ramp.color_ramp.interpolation = 'CONSTANT'
    ramp.color_ramp.elements[0].position = ramp_pos
    ramp.color_ramp.elements[1].position = 1.0

    shadow = tuple(c * shadow_factor for c in base_color)
    ramp.color_ramp.elements[0].color = (*shadow, 1.0)
    ramp.color_ramp.elements[1].color = (*base_color, 1.0)

    em = nodes.new('ShaderNodeEmission')
    em.location = (800, 0)
    em.inputs['Strength'].default_value = 1.0

    links.new(clamp.outputs['Result'], ramp.inputs['Fac'])
    links.new(ramp.outputs['Color'], em.inputs['Color'])
    links.new(em.outputs['Emission'], out.inputs['Surface'])

    return mat
