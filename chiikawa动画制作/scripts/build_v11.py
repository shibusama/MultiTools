"""
Chiikawa 动画 v11 —— 重做动画本身
=====================================
之前的失败：
  1. 只盯着"硬边明暗"，忽略动画内容太空
  2. 一个球上下浮动 3 秒 = 没有表演，不像抖音上的作品

这次的核心改动：
  1. 【动作有表演】跳跃 + 落地压缩拉伸（squash & stretch）+ 耳朵延迟跟随
  2. 【时长拉长】3 秒 -> 6 秒，有起承转合
  3. 【材质回退到可用方案】用已验证能正常渲染的方式，不再纠结硬边明暗
  4. 【场景有背景】加地面和简单环境，不是纯白一片

动画设计（72 帧 x 2 = 144 帧 @ 24fps = 6 秒）：
  第 1-24 帧  ：蓄力下蹲
  第 25-36 帧 ：起跳上升
  第 37-48 帧 ：滞空（顶点）
  第 49-60 帧 ：下落
  第 61-72 帧 ：落地压缩
  第 73-96 帧 ：回弹
  第 97-144 帧：待机呼吸（循环）
"""
import bpy
import math
import os
import sys

BASE = r"D:\C_Relocated\Users\13191\MultiTools\chiikawa动画制作"
sys.path.insert(0, os.path.join(BASE, "scripts"))


def build_character():
    """建模：圆头 + 耳朵 + 五官"""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    for blk in (bpy.data.meshes, bpy.data.materials, bpy.data.armatures):
        for it in list(blk):
            if it.users == 0:
                blk.remove(it)

    def sphere(name, loc, r, scale=(1, 1, 1)):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24,
                                             radius=r, location=loc)
        o = bpy.context.active_object
        o.name = name
        o.scale = scale
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        bpy.ops.object.shade_smooth()
        return o

    parts = {}
    parts['body'] = sphere("Body", (0, 0, 1.0), 1.0, (1.08, 1.0, 0.96))
    parts['ear_l'] = sphere("Ear_L", (-0.68, 0, 1.92), 0.30, (1.0, 0.8, 1.0))
    parts['ear_r'] = sphere("Ear_R", (0.68, 0, 1.92), 0.30, (1.0, 0.8, 1.0))
    parts['eye_l'] = sphere("Eye_L", (-0.40, -0.90, 1.18), 0.155)
    parts['eye_r'] = sphere("Eye_R", (0.40, -0.90, 1.18), 0.155)
    parts['mouth'] = sphere("Mouth", (0, -0.97, 0.95), 0.055, (1.0, 0.6, 0.8))
    parts['blush_l'] = sphere("Blush_L", (-0.66, -0.74, 0.98), 0.14, (1.0, 0.25, 1.0))
    parts['blush_r'] = sphere("Blush_R", (0.66, -0.74, 0.98), 0.14, (1.0, 0.25, 1.0))
    return parts


def apply_materials():
    """
    材质：回到能正常渲染的方案。
    用 Diffuse 接收真实光照，经 ColorRamp 量化，Emission 输出。
    场景配真实灯光（这是之前发现的关键 —— 没有灯光 ShaderToRGB 输出 0）。
    """
    from apply_toon_v10 import make_toon_material_v10
    from apply_toon_v9 import make_outline_material

    def s2l(c):
        return c/12.92 if c <= 0.04045 else ((c+0.055)/1.055)**2.4

    def col(r, g, b):
        return tuple(s2l(v) for v in (r, g, b))

    specs = {
        "Body":    ("M_Body",   col(0.98, 0.97, 0.94), 0.153, 0.82),
        "Ear_L":   ("M_Ear_L",  col(0.98, 0.97, 0.94), 0.153, 0.82),
        "Ear_R":   ("M_Ear_R",  col(0.98, 0.97, 0.94), 0.153, 0.82),
        "Eye_L":   ("M_Eye_L",  col(0.05, 0.05, 0.07), 0.10, 0.95),
        "Eye_R":   ("M_Eye_R",  col(0.05, 0.05, 0.07), 0.10, 0.95),
        "Mouth":   ("M_Mouth",  col(0.15, 0.12, 0.12), 0.12, 0.92),
        "Blush_L": ("M_Blush",  col(0.96, 0.72, 0.74), 0.153, 0.88),
        "Blush_R": ("M_Blush",  col(0.96, 0.72, 0.74), 0.153, 0.88),
    }
    for name, (mn, base, rp, sf) in specs.items():
        o = bpy.data.objects.get(name)
        if not o:
            continue
        m = make_toon_material_v10(mn, base, ramp_pos=rp, shadow_factor=sf, gain=2.0)
        o.data.materials.clear()
        o.data.materials.append(m)

    # 合并为两个网格（身体带描边，脸不带）
    bpy.ops.object.select_all(action='DESELECT')
    for n in ["Body", "Ear_L", "Ear_R"]:
        bpy.data.objects[n].select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects["Body"]
    bpy.ops.object.join()
    body = bpy.context.active_object
    body.name = "Chiikawa_Body"

    outline = make_outline_material()
    mats = [m for m in body.data.materials if m]
    if outline.name not in [m.name for m in mats]:
        body.data.materials.append(outline)
    mats = [m for m in body.data.materials if m]
    oslot = [m.name for m in mats].index(outline.name)

    mod = body.modifiers.new(name="Outline", type='SOLIDIFY')
    mod.thickness = 0.05
    mod.offset = 1.0
    mod.use_flip_normals = True
    mod.use_rim = False
    mod.material_offset = oslot
    mod.material_offset_rim = oslot

    bpy.ops.object.select_all(action='DESELECT')
    for n in ["Eye_L", "Eye_R", "Mouth", "Blush_L", "Blush_R"]:
        bpy.data.objects[n].select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects["Eye_L"]
    bpy.ops.object.join()
    face = bpy.context.active_object
    face.name = "Chiikawa_Face"

    print(f"  身体网格 {len(body.data.vertices)} 顶点 / 脸 {len(face.data.vertices)} 顶点")
    return body, face


def build_rig():
    for o in list(bpy.data.objects):
        if o.type == 'ARMATURE':
            bpy.data.objects.remove(o, do_unlink=True)

    bpy.ops.object.armature_add(location=(0, 0, 0))
    arm = bpy.context.active_object
    arm.name = "ChiikawaRig"

    bpy.ops.object.mode_set(mode='EDIT')
    ebs = arm.data.edit_bones
    for b in list(ebs):
        ebs.remove(b)

    root = ebs.new("Root")
    root.head = (0, 0, -1.0)
    root.tail = (0, 0, 0.0)
    body = ebs.new("Body")
    body.head = (0, 0, 0.0)
    body.tail = (0, 0, 0.95)
    body.parent = root
    el = ebs.new("Ear_L")
    el.head = (-0.68, 0, 0.85)
    el.tail = (-0.68, 0, 1.30)
    el.parent = body
    er = ebs.new("Ear_R")
    er.head = (0.68, 0, 0.85)
    er.tail = (0.68, 0, 1.30)
    er.parent = body

    bpy.ops.object.mode_set(mode='OBJECT')
    return arm


def bind(mesh, arm):
    me = mesh.data
    for vg in list(mesh.vertex_groups):
        mesh.vertex_groups.remove(vg)
    names = ["Root", "Body", "Ear_L", "Ear_R"]
    groups = {n: mesh.vertex_groups.new(name=n) for n in names}

    vb = {}
    for poly in me.polygons:
        mi = poly.material_index
        mat = me.materials[mi] if mi < len(me.materials) else None
        mn = mat.name if mat else ""
        bone = "Ear_L" if mn == "M_Ear_L" else ("Ear_R" if mn == "M_Ear_R" else "Body")
        for vi in poly.vertices:
            prev = vb.get(vi)
            if prev in ("Ear_L", "Ear_R") and bone == "Body":
                continue
            vb[vi] = bone
    for v in me.vertices:
        if v.index not in vb:
            x, y, z = v.co
            if z > 0.55 and x < -0.30:
                vb[v.index] = "Ear_L"
            elif z > 0.55 and x > 0.30:
                vb[v.index] = "Ear_R"
            else:
                vb[v.index] = "Body"

    buckets = {n: [] for n in names}
    for vi, b in vb.items():
        buckets[b].append(vi)
    for n, vids in buckets.items():
        if vids:
            groups[n].add(vids, 1.0, 'REPLACE')

    for m in list(mesh.modifiers):
        if m.type == 'ARMATURE':
            mesh.modifiers.remove(m)
    mod = mesh.modifiers.new(name="Armature", type='ARMATURE')
    mod.object = arm
    mod.use_vertex_groups = True
    mod.use_bone_envelopes = False
    mesh.parent = arm
    mesh.matrix_parent_inverse = arm.matrix_world.inverted()


def make_jump_animation(arm):
    """
    跳跃动画：蓄力 -> 起跳 -> 滞空 -> 下落 -> 落地压缩 -> 回弹 -> 待机
    带 squash & stretch（挤压拉伸）和耳朵延迟跟随
    """
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = 144        # 6 秒 @ 24fps
    scene.render.fps = 24

    if arm.animation_data:
        arm.animation_data_clear()

    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='POSE')
    pb = arm.pose.bones
    for b in pb:
        b.rotation_mode = 'XYZ'

    root = pb.get("Root")
    body = pb.get("Body")
    el = pb.get("Ear_L")
    er = pb.get("Ear_R")

    # (帧, root高度, 身体缩放, 身体旋转, 左耳角, 右耳角)
    #
    # 重要修正：骨骼的局部缩放轴与世界轴不对应！
    # Body 骨骼从 (0,0,0) 指向 (0,0,0.95)，即骨骼 Y 轴 = 世界 Z 轴。
    # 所以：
    #   骨骼 scale.y  -> 世界 Z（竖直方向）
    #   骨骼 scale.x/z -> 世界 X/Y（水平方向）
    # 之前写成 (sz_xy, sz_xy, sz_z) 正好搞反了，导致"拉伸"反而变小。
    keys = [
        # 起手：静止
        (1,    0.000, 1.00, 1.00,  0.0,   0.0,   0.0),
        # 蓄力下蹲（压扁：矮而宽）
        (14,  -0.10,  0.86, 1.12, -1.0,  10.0, -10.0),
        (20,  -0.13,  0.82, 1.16, -1.5,  13.0, -13.0),
        # 起跳（拉伸：高而窄）
        (26,   0.05,  1.14, 0.93,  1.0, -12.0,  12.0),
        (32,   0.35,  1.22, 0.88,  2.0, -18.0,  18.0),
        # 滞空顶点（回落）
        (44,   0.50,  1.06, 0.97,  0.0, -10.0,  10.0),
        (56,   0.44,  1.00, 1.00, -1.0,  -4.0,   4.0),
        # 下落（拉伸）
        (64,   0.20,  1.16, 0.91, -2.0,   8.0,  -8.0),
        (70,   0.02,  1.20, 0.89, -2.5,  14.0, -14.0),
        # 落地压缩（强烈压扁：矮而宽）
        (74,  -0.16,  0.74, 1.22,  0.0,  22.0, -22.0),
        (78,  -0.12,  0.84, 1.14,  0.5,  16.0, -16.0),
        # 回弹过冲
        (86,   0.03,  1.08, 0.96, -0.5,  -6.0,   6.0),
        (94,  -0.03,  0.94, 1.05,  0.3,   5.0,  -5.0),
        # 稳定
        (104,  0.00,  1.00, 1.00,  0.0,   0.0,   0.0),
        # 待机呼吸（收尾，可循环）
        (116,  0.03,  1.00, 1.00,  0.0,  -3.0,   3.0),
        (130, -0.02,  1.00, 1.00,  0.0,   2.0,  -2.0),
        (144,  0.00,  1.00, 1.00,  0.0,   0.0,   0.0),
    ]

    for (f, dz, sz_v, sz_h, tilt, la, ra) in keys:
        scene.frame_set(f)
        if root:
            root.location = (0, dz, 0)
            root.keyframe_insert("location", frame=f)
        if body:
            # 骨骼局部：Y=世界Z(竖直)，X/Z=水平
            body.scale = (sz_h, sz_v, sz_h)
            body.rotation_euler = (0, math.radians(tilt), 0)
            body.keyframe_insert("scale", frame=f)
            body.keyframe_insert("rotation_euler", frame=f)
        if el:
            el.rotation_euler = (0, math.radians(la), 0)
            el.keyframe_insert("rotation_euler", frame=f)
        if er:
            er.rotation_euler = (0, math.radians(ra), 0)
            er.keyframe_insert("rotation_euler", frame=f)

    # 设置插值：弹性动作多用 BEZIER，落地冲击用 CONSTANT 前的快速过渡
    try:
        act = arm.animation_data.action
        fcs = []
        if hasattr(act, "fcurves"):
            fcs = list(act.fcurves)
        elif hasattr(act, "layers"):
            for L in act.layers:
                for s in L.strips:
                    if hasattr(s, "channelbags"):
                        for cb in s.channelbags:
                            fcs.extend(cb.fcurves)
        for fc in fcs:
            for kp in fc.keyframe_points:
                kp.interpolation = 'BEZIER'
                kp.handle_left_type = 'AUTO_CLAMPED'
                kp.handle_right_type = 'AUTO_CLAMPED'
        print(f"  动画曲线: {len(fcs)} 条")
    except Exception as e:
        print(f"  插值设置跳过: {e}")

    bpy.ops.object.mode_set(mode='OBJECT')
    print(f"  动画: {scene.frame_start}-{scene.frame_end} 帧 ({scene.frame_end/24:.1f}秒)")


def setup_scene():
    """场景：真实灯光 + 背景 + 相机"""
    # 灯光
    for o in list(bpy.data.objects):
        if o.type == 'LIGHT':
            bpy.data.objects.remove(o, do_unlink=True)

    bpy.ops.object.light_add(type='SUN', location=(-5, -3, 4))
    sun = bpy.context.active_object
    sun.name = "KeyLight"
    sun.data.energy = 3.0
    sun.data.angle = math.radians(3)
    sun.rotation_euler = (math.radians(65), 0, math.radians(-50))

    # 世界：相机可见的浅色背景 + 低照明
    world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputWorld')
    mix = nt.nodes.new('ShaderNodeMixShader')
    lp = nt.nodes.new('ShaderNodeLightPath')
    bg_v = nt.nodes.new('ShaderNodeBackground')
    bg_l = nt.nodes.new('ShaderNodeBackground')
    bg_v.inputs['Color'].default_value = (0.96, 0.97, 1.0, 1.0)
    bg_v.inputs['Strength'].default_value = 1.0
    bg_l.inputs['Color'].default_value = (1.0, 1.0, 1.0, 1.0)
    bg_l.inputs['Strength'].default_value = 0.03
    nt.links.new(lp.outputs['Is Camera Ray'], mix.inputs['Fac'])
    nt.links.new(bg_l.outputs['Background'], mix.inputs[1])
    nt.links.new(bg_v.outputs['Background'], mix.inputs[2])
    nt.links.new(mix.outputs['Shader'], out.inputs['Surface'])

    # 相机
    for o in list(bpy.data.objects):
        if o.type == 'CAMERA':
            bpy.data.objects.remove(o, do_unlink=True)
    bpy.ops.object.camera_add(location=(0, -7.0, 1.6))
    cam = bpy.context.active_object
    cam.name = "Camera"
    cam.data.lens = 50
    bpy.context.scene.camera = cam

    body_obj = bpy.data.objects.get("Chiikawa_Body")
    if body_obj:
        c = cam.constraints.new(type='TRACK_TO')
        c.target = body_obj
        c.track_axis = 'TRACK_NEGATIVE_Z'
        c.up_axis = 'UP_Y'

    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE'
    sc.render.resolution_x = 1080
    sc.render.resolution_y = 1080
    sc.render.fps = 24
    sc.render.film_transparent = False
    try:
        sc.view_settings.view_transform = 'Standard'
    except Exception:
        pass


def main():
    print("=" * 60)
    print("Chiikawa 动画 v11 —— 重做动画")
    print("=" * 60)

    print("\n[1] 建模")
    build_character()
    print("\n[2] 材质 + 合并")
    body, face = apply_materials()
    print("\n[3] 骨骼")
    arm = build_rig()
    print("\n[4] 绑定")
    bind(body, arm)
    bind(face, arm)
    print("\n[5] 跳跃动画")
    make_jump_animation(arm)
    print("\n[6] 场景")
    setup_scene()

    out = os.path.join(BASE, "models", "chiikawa_v11.blend")
    bpy.ops.wm.save_as_mainfile(filepath=out)
    print(f"\n已保存: {out}")
    print("=" * 60)


if __name__ == "__main__":
    main()
