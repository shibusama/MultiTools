"""
三渲二材质 v6 —— 不依赖 Shader to RGB 的方案
================================================
背景：实测发现 Blender 5.2 的 Shader to RGB 输出恒为 0，
      导致基于它的 ColorRamp 卡通着色完全失效。

新方案：用 Geometry Normal + 光源方向 手工计算 Lambert 光照，
        再经过 ColorRamp 做硬边量化。

优点：
- 完全可控，不依赖已失效的节点
- 数学透明，出问题能算出来
- 在任何渲染引擎下都能工作

节点结构：
    Geometry.Normal --\
                       --> Vector Math(Dot) --> Math(Clamp) --> ColorRamp --> Output
    Light Direction --/
"""
import bpy
import math
import os


def make_toon_material_v6(name, base_color, shadow_color=None,
                          ramp_pos=0.5, shadow_factor=0.78,
                          light_dir=(-0.5, -0.6, 0.62)):
    """
    用几何法线 + 固定光方向做卡通着色。

    原理：
      lambert = dot(normal, light_dir)
      用 ColorRamp 把连续的 lambert 值量化成两档颜色
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

    # --- 输出 ---
    out = nodes.new('ShaderNodeOutputMaterial')
    out.location = (900, 0)

    # --- 几何法线（世界空间） ---
    geo = nodes.new('ShaderNodeNewGeometry')
    geo.location = (-600, 100)

    # --- 光源方向（归一化向量） ---
    ld = (light_dir[0], light_dir[1], light_dir[2])
    ln = math.sqrt(sum(c*c for c in ld))
    ld_n = tuple(c/ln for c in ld)

    # --- 点乘：normal · light_dir ---
    dot = nodes.new('ShaderNodeVectorMath')
    dot.operation = 'DOT_PRODUCT'
    dot.location = (-350, 100)
    dot.inputs[1].default_value = ld_n

    # --- 重映射到 0-1 ---
    # dot 范围 [-1, 1] -> [0, 1]
    mad = nodes.new('ShaderNodeMath')
    mad.operation = 'MULTIPLY_ADD'
    mad.location = (-150, 100)
    mad.inputs[1].default_value = 0.5
    mad.inputs[2].default_value = 0.5

    # --- 限制范围 ---
    clamp = nodes.new('ShaderNodeClamp')
    clamp.location = (50, 100)
    clamp.inputs['Min'].default_value = 0.0
    clamp.inputs['Max'].default_value = 1.0

    # --- ColorRamp 量化 ---
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.location = (250, 100)
    ramp.color_ramp.interpolation = 'CONSTANT'
    ramp.color_ramp.elements[0].position = ramp_pos
    ramp.color_ramp.elements[1].position = 1.0

    if shadow_color is None:
        shadow_color = tuple(c * shadow_factor for c in base_color)
    ramp.color_ramp.elements[0].color = (*shadow_color, 1.0)
    ramp.color_ramp.elements[1].color = (*base_color, 1.0)

    # --- Emission 输出（保证颜色准确不被二次光照影响） ---
    em = nodes.new('ShaderNodeEmission')
    em.location = (650, 0)
    em.inputs['Strength'].default_value = 1.0

    # --- 连线 ---
    links.new(geo.outputs['Normal'], dot.inputs[0])
    links.new(dot.outputs['Value'], mad.inputs[0])
    links.new(mad.outputs['Value'], clamp.inputs['Value'])
    links.new(clamp.outputs['Result'], ramp.inputs['Fac'])
    links.new(ramp.outputs['Color'], em.inputs['Color'])
    links.new(em.outputs['Emission'], out.inputs['Surface'])

    return mat


def make_outline_material(name="Outline", color=(0.0, 0.0, 0.0)):
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


def add_outline(obj, thickness=0.05, mat=None):
    if mat is None:
        mat = bpy.data.materials.get("Outline") or make_outline_material()
    mats = [m for m in obj.data.materials if m]
    if mat.name not in [m.name for m in mats]:
        obj.data.materials.append(mat)
    mats = [m for m in obj.data.materials if m]
    slot = [m.name for m in mats].index(mat.name)

    mod = obj.modifiers.new(name="Outline", type='SOLIDIFY')
    mod.thickness = thickness
    mod.offset = 1.0
    mod.use_flip_normals = True
    mod.use_rim = False
    mod.material_offset = slot
    mod.material_offset_rim = slot
    return mod


def setup_render():
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = 1080
    scene.render.resolution_y = 1080
    try:
        scene.view_settings.view_transform = 'Standard'
    except Exception:
        pass


def main():
    print("=" * 60)
    print("应用三渲二材质 v6（几何法线方案，不依赖 Shader to RGB）")
    print("=" * 60)

    def srgb_to_linear(c):
        return c/12.92 if c <= 0.04045 else ((c+0.055)/1.055)**2.4

    def col(r, g, b):
        return tuple(srgb_to_linear(v) for v in (r, g, b))

    # 光源方向与 KeyLight 一致（左前上方）
    # KeyLight rotation: (52°, 0, -32°)
    LIGHT_DIR = (-0.45, -0.55, 0.70)

    specs = {
        "Body":    ("M_Body",   col(0.98, 0.97, 0.94), 0.50, 0.80),
        "Ear_L":   ("M_Ear_L",  col(0.98, 0.97, 0.94), 0.50, 0.80),
        "Ear_R":   ("M_Ear_R",  col(0.98, 0.97, 0.94), 0.50, 0.80),
        "Eye_L":   ("M_Eye_L",  col(0.05, 0.05, 0.07), 0.35, 0.95),
        "Eye_R":   ("M_Eye_R",  col(0.05, 0.05, 0.07), 0.35, 0.95),
        "Mouth":   ("M_Mouth",  col(0.15, 0.12, 0.12), 0.45, 0.90),
        "Blush_L": ("M_Blush",  col(0.96, 0.72, 0.74), 0.50, 0.88),
        "Blush_R": ("M_Blush",  col(0.96, 0.72, 0.74), 0.50, 0.88),
    }

    outline_mat = make_outline_material()
    for obj_name, (mat_name, base, rp, sf) in specs.items():
        obj = bpy.data.objects.get(obj_name)
        if not obj:
            print(f"  [跳过] {obj_name}")
            continue
        m = make_toon_material_v6(mat_name, base, ramp_pos=rp,
                                  shadow_factor=sf, light_dir=LIGHT_DIR)
        obj.data.materials.clear()
        obj.data.materials.append(m)
        if obj_name in ("Body", "Ear_L", "Ear_R"):
            add_outline(obj, thickness=0.055, mat=outline_mat)
            print(f"  {obj_name:8s} -> {mat_name} + 描边")
        else:
            print(f"  {obj_name:8s} -> {mat_name}")

    setup_render()

    # 灯光（Emission 材质不受光，但保留灯光便于后续扩展）
    for o in list(bpy.data.objects):
        if o.type == 'LIGHT':
            bpy.data.objects.remove(o, do_unlink=True)
    bpy.ops.object.light_add(type='SUN', location=(-4, -5, 5))
    k = bpy.context.active_object
    k.name = "KeyLight"
    k.data.energy = 3.0
    k.rotation_euler = (math.radians(52), 0, math.radians(-32))

    # 世界背景
    world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs['Color'].default_value = (0.86, 0.88, 0.92, 1.0)
        bg.inputs['Strength'].default_value = 1.0

    out = r"D:\C_Relocated\Users\13191\MultiTools\projects\chiikawa\models\chiikawa_toon.blend"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out)
    print(f"\n已保存: {out}")
    print("=" * 60)


if __name__ == "__main__":
    main()
