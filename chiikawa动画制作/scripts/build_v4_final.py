"""
v4 完整流程：材质 + 描边 + 骨骼 + 绑定 + 动画 + 场景
动作幅度比 v2 更大（借鉴抖音教程的活泼感）
"""
import bpy
import math
import os
import sys

BASE = r"D:\C_Relocated\Users\13191\MultiTools\chiikawa动画制作"
sys.path.insert(0, os.path.join(BASE, "scripts"))


def apply_materials():
    from apply_toon_v6 import make_toon_material_v6

    def s2l(c):
        return c/12.92 if c <= 0.04045 else ((c+0.055)/1.055)**2.4

    def col(r, g, b):
        return tuple(s2l(v) for v in (r, g, b))

    LIGHT = (-0.45, -0.55, 0.70)

    # v4 修正：实测 dot 值分布 —— 88.5% 落在 0.7-1.0，仅 10.8% 低于 0.5
    # 阈值 0.50 时阴影只有 10.8%（且多为描边），画面看着是平的。
    # 把阈值提到 0.86，让约 40% 的表面落入阴影区，明暗分界才明显。
    specs = {
        "Body":    ("M_Body",   col(0.98, 0.97, 0.94), 0.86, 0.80),
        "Ear_L":   ("M_Ear_L",  col(0.98, 0.97, 0.94), 0.86, 0.80),
        "Ear_R":   ("M_Ear_R",  col(0.98, 0.97, 0.94), 0.86, 0.80),
        "Eye_L":   ("M_Eye_L",  col(0.05, 0.05, 0.07), 0.35, 0.95),
        "Eye_R":   ("M_Eye_R",  col(0.05, 0.05, 0.07), 0.35, 0.95),
        "Mouth":   ("M_Mouth",  col(0.15, 0.12, 0.12), 0.45, 0.90),
        "Blush_L": ("M_Blush",  col(0.96, 0.72, 0.74), 0.86, 0.86),
        "Blush_R": ("M_Blush",  col(0.96, 0.72, 0.74), 0.86, 0.86),
    }
    for name, (mn, base, rp, sf) in specs.items():
        obj = bpy.data.objects.get(name)
        if not obj:
            continue
        m = make_toon_material_v6(mn, base, ramp_pos=rp,
                                  shadow_factor=sf, light_dir=LIGHT)
        obj.data.materials.clear()
        obj.data.materials.append(m)
        print(f"    {name} -> {mn}")


def make_two_meshes():
    from apply_toon_v6 import make_outline_material

    bpy.ops.object.select_all(action='DESELECT')
    for n in ["Body", "Ear_L", "Ear_R"]:
        o = bpy.data.objects.get(n)
        if o:
            o.select_set(True)
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
    mod.thickness = 0.055
    mod.offset = 1.0
    mod.use_flip_normals = True
    mod.use_rim = False
    mod.material_offset = oslot
    mod.material_offset_rim = oslot
    print(f"  身体网格: {len(body.data.vertices)} 顶点, 描边槽={oslot}")

    bpy.ops.object.select_all(action='DESELECT')
    for n in ["Eye_L", "Eye_R", "Mouth", "Blush_L", "Blush_R"]:
        o = bpy.data.objects.get(n)
        if o:
            o.select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects["Eye_L"]
    bpy.ops.object.join()
    face = bpy.context.active_object
    face.name = "Chiikawa_Face"
    print(f"  脸部网格: {len(face.data.vertices)} 顶点")

    return body, face


def build_armature():
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
    print(f"  骨骼: {[b.name for b in arm.data.bones]}")
    return arm


def bind(mesh, arm, tag):
    me = mesh.data
    for vg in list(mesh.vertex_groups):
        mesh.vertex_groups.remove(vg)

    names = ["Root", "Body", "Ear_L", "Ear_R"]
    groups = {n: mesh.vertex_groups.new(name=n) for n in names}

    vert_bone = {}
    for poly in me.polygons:
        mi = poly.material_index
        mat = me.materials[mi] if mi < len(me.materials) else None
        mn = mat.name if mat else ""
        bone = "Ear_L" if mn == "M_Ear_L" else ("Ear_R" if mn == "M_Ear_R" else "Body")
        for vi in poly.vertices:
            prev = vert_bone.get(vi)
            if prev in ("Ear_L", "Ear_R") and bone == "Body":
                continue
            vert_bone[vi] = bone

    for v in me.vertices:
        if v.index not in vert_bone:
            x, y, z = v.co
            if z > 0.55 and x < -0.30:
                vert_bone[v.index] = "Ear_L"
            elif z > 0.55 and x > 0.30:
                vert_bone[v.index] = "Ear_R"
            else:
                vert_bone[v.index] = "Body"

    buckets = {n: [] for n in names}
    for vi, b in vert_bone.items():
        buckets[b].append(vi)
    for n, vids in buckets.items():
        if vids:
            groups[n].add(vids, 1.0, 'REPLACE')

    bad = sum(1 for v in me.vertices
              if abs(sum(g.weight for g in v.groups) - 1.0) > 0.001)

    for m in list(mesh.modifiers):
        if m.type == 'ARMATURE':
            mesh.modifiers.remove(m)
    mod = mesh.modifiers.new(name="Armature", type='ARMATURE')
    mod.object = arm
    mod.use_vertex_groups = True
    mod.use_bone_envelopes = False

    mesh.parent = arm
    mesh.matrix_parent_inverse = arm.matrix_world.inverted()
    print(f"  {tag}: " + ", ".join(f"{n}={len(buckets[n])}" for n in names if buckets[n])
          + f"  权重异常={bad}")


def animate(arm):
    """动作幅度更大：位移 0.09 + 身体侧倾 + 耳朵 9°"""
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = 72
    scene.render.fps = 24

    if arm.animation_data:
        arm.animation_data_clear()

    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='POSE')
    pb = arm.pose.bones
    for b in pb:
        b.rotation_mode = 'XYZ'

    root = pb.get("Root")
    body_bone = pb.get("Body")
    el = pb.get("Ear_L")
    er = pb.get("Ear_R")

    keys = [
        (1,   0.000,  0.0,   0.0,   0.0),
        (12,  0.065,  2.0,   8.0,  -6.0),
        (24,  0.095,  3.0,  10.0,  -9.0),
        (36,  0.030,  0.0,   0.0,   0.0),
        (48, -0.050, -2.0,  -7.0,   6.0),
        (60, -0.065, -2.5,  -8.0,   7.0),
        (72,  0.000,  0.0,   0.0,   0.0),
    ]

    for (f, dz, tilt, a, b) in keys:
        scene.frame_set(f)
        if root:
            root.location = (0, dz, 0)
            root.keyframe_insert("location", frame=f)
        if body_bone:
            body_bone.rotation_euler = (0, math.radians(tilt), 0)
            body_bone.keyframe_insert("rotation_euler", frame=f)
        if el:
            el.rotation_euler = (0, math.radians(a), 0)
            el.keyframe_insert("rotation_euler", frame=f)
        if er:
            er.rotation_euler = (0, math.radians(b), 0)
            er.keyframe_insert("rotation_euler", frame=f)

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
        print(f"  动画曲线: {len(fcs)} 条")
    except Exception as e:
        print(f"  插值跳过: {e}")

    bpy.ops.object.mode_set(mode='OBJECT')


def main():
    print("=" * 60)
    print("v4 完整流程")
    print("=" * 60)

    print("\n[1] 材质")
    apply_materials()
    print("\n[2] 双网格")
    body, face = make_two_meshes()
    print("\n[3] 骨骼")
    arm = build_armature()
    print("\n[4] 绑定")
    bind(body, arm, "身体")
    bind(face, arm, "脸部")
    print("\n[5] 动画")
    animate(arm)
    print("\n[6] 场景")
    from setup_scene import setup_render, setup_world, setup_camera
    setup_render()
    setup_world()
    setup_camera()

    out = os.path.join(BASE, "models", "chiikawa_v4_final.blend")
    bpy.ops.wm.save_as_mainfile(filepath=out)
    print(f"\n已保存: {out}")
    print("=" * 60)


if __name__ == "__main__":
    main()
