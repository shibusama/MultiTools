"""
最终方案：分离式描边
====================
问题根源：Solidify 修改器对整个合并网格外扩，
          连眼睛/腮红/嘴也被包了一层黑壳，视觉上就是"被切开"。

解法：建两个网格对象
  1. Chiikawa_Body  —— 身体 + 耳朵（带描边 Solidify）
  2. Chiikawa_Face  —— 眼睛 + 嘴 + 腮红（无描边）
两个都绑定到同一套骨骼，一起动。
"""
import bpy
import math
import os
import sys

BASE = r"D:\C_Relocated\Users\13191\MultiTools\projects\chiikawa"
sys.path.insert(0, os.path.join(BASE, "scripts"))


def build():
    from apply_toon_v6 import (make_toon_material_v6, make_outline_material)

    def s2l(c):
        return c/12.92 if c <= 0.04045 else ((c+0.055)/1.055)**2.4

    def col(r, g, b):
        return tuple(s2l(v) for v in (r, g, b))

    LIGHT = (-0.45, -0.55, 0.70)

    # ---------- 材质 ----------
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
    for name, (mn, base, rp, sf) in specs.items():
        obj = bpy.data.objects.get(name)
        if not obj:
            continue
        m = make_toon_material_v6(mn, base, ramp_pos=rp,
                                  shadow_factor=sf, light_dir=LIGHT)
        obj.data.materials.clear()
        obj.data.materials.append(m)

    # ---------- 网格1：身体+耳朵（带描边） ----------
    body_parts = ["Body", "Ear_L", "Ear_R"]
    bpy.ops.object.select_all(action='DESELECT')
    for p in body_parts:
        o = bpy.data.objects.get(p)
        if o:
            o.select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects["Body"]
    bpy.ops.object.join()
    body_mesh = bpy.context.active_object
    body_mesh.name = "Chiikawa_Body"

    # 加描边
    outline = make_outline_material()
    mats = [m for m in body_mesh.data.materials if m]
    if outline.name not in [m.name for m in mats]:
        body_mesh.data.materials.append(outline)
    mats = [m for m in body_mesh.data.materials if m]
    oslot = [m.name for m in mats].index(outline.name)

    mod = body_mesh.modifiers.new(name="Outline", type='SOLIDIFY')
    mod.thickness = 0.05
    mod.offset = 1.0
    mod.use_flip_normals = True
    mod.use_rim = False
    mod.material_offset = oslot
    mod.material_offset_rim = oslot
    print(f"身体网格: {len(body_mesh.data.vertices)}顶点, 描边槽={oslot}")

    # ---------- 网格2：脸部件（无描边） ----------
    face_parts = ["Eye_L", "Eye_R", "Mouth", "Blush_L", "Blush_R"]
    bpy.ops.object.select_all(action='DESELECT')
    for p in face_parts:
        o = bpy.data.objects.get(p)
        if o:
            o.select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects["Eye_L"]
    bpy.ops.object.join()
    face_mesh = bpy.context.active_object
    face_mesh.name = "Chiikawa_Face"
    print(f"脸部网格: {len(face_mesh.data.vertices)}顶点, "
          f"材质={[m.name for m in face_mesh.data.materials if m]}")

    return body_mesh, face_mesh


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
    print(f"骨骼: {[b.name for b in arm.data.bones]}")
    return arm


def bind(mesh, arm, tag):
    """刚性绑定：按材质分配，全部给 Body/Ear 骨骼"""
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

    for m in list(mesh.modifiers):
        if m.type == 'ARMATURE':
            mesh.modifiers.remove(m)
    mod = mesh.modifiers.new(name="Armature", type='ARMATURE')
    mod.object = arm
    mod.use_vertex_groups = True
    mod.use_bone_envelopes = False

    mesh.parent = arm
    mesh.matrix_parent_inverse = arm.matrix_world.inverted()
    print(f"  {tag} 绑定: " + ", ".join(f"{n}={len(buckets[n])}" for n in names if buckets[n]))


def animate(arm):
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

    root, el, er = pb.get("Root"), pb.get("Ear_L"), pb.get("Ear_R")
    keys = [
        (1,   0.000,  0.0,  0.0),
        (18,  0.045,  5.0, -5.0),
        (36,  0.000,  0.0,  0.0),
        (54, -0.035, -4.0,  4.0),
        (72,  0.000,  0.0,  0.0),
    ]
    for (f, dz, a, b) in keys:
        scene.frame_set(f)
        if root:
            root.location = (0, dz, 0)
            root.keyframe_insert("location", frame=f)
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
    except Exception:
        pass

    bpy.ops.object.mode_set(mode='OBJECT')
    print(f"动画: {scene.frame_start}-{scene.frame_end} 帧")


def main():
    print("=" * 60)
    print("最终构建：分离式描边")
    print("=" * 60)

    body, face = build()
    arm = build_armature()
    bind(body, arm, "身体")
    bind(face, arm, "脸部")
    animate(arm)

    from setup_scene import setup_render, setup_world, setup_camera
    setup_render()
    setup_world()
    setup_camera()

    out = os.path.join(BASE, "models", "chiikawa_final.blend")
    bpy.ops.wm.save_as_mainfile(filepath=out)
    print(f"\n已保存: {out}")
    print("=" * 60)


if __name__ == "__main__":
    main()
