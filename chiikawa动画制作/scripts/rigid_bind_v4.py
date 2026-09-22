"""
刚性绑定 v4 —— 修正版
======================
诊断结论（test_modifiers.py）：移除 Armature 修改器后模型正常，
说明变形由 Armature 修改器引起。

根因：顶点组分配不完整。用 polygons 遍历时，
     某些顶点可能没被任何一个多边形引用（或索引遗漏），
     这些顶点权重为 0，Armature 修改器会把它们留在原地，
     而相邻顶点移动了 -> 撕裂变形。

修正：遍历【所有顶点】，用空间位置兜底分配，确保 100% 覆盖。
"""
import bpy
import math
import os

BASE = r"D:\C_Relocated\Users\13191\MultiTools\chiikawa动画制作"


def rigid_bind_v4(mesh_obj, arm_obj):
    me = mesh_obj.data

    for vg in list(mesh_obj.vertex_groups):
        mesh_obj.vertex_groups.remove(vg)

    names = ["Root", "Body", "Ear_L", "Ear_R"]
    groups = {n: mesh_obj.vertex_groups.new(name=n) for n in names}

    # --- 第一步：用材质确定每个多边形的归属，记录到顶点 ---
    # 局部坐标：耳朵 Z 0.62~1.22, |X| 0.38~0.98
    # 用材质名判定更准
    vert_bone = {}   # vertex_index -> bone_name

    for poly in me.polygons:
        mi = poly.material_index
        mat = me.materials[mi] if mi < len(me.materials) else None
        mname = mat.name if mat else ""

        if mname == "M_Ear_L":
            bone = "Ear_L"
        elif mname == "M_Ear_R":
            bone = "Ear_R"
        else:
            bone = "Body"

        for vi in poly.vertices:
            # 耳朵优先（描边壳可能同时被标记）
            prev = vert_bone.get(vi)
            if prev in ("Ear_L", "Ear_R") and bone == "Body":
                continue
            vert_bone[vi] = bone

    # --- 第二步：兜底 —— 遍历所有顶点，未分配的按位置判定 ---
    unassigned = 0
    for v in me.vertices:
        if v.index in vert_bone:
            continue
        unassigned += 1
        x, y, z = v.co
        # 局部坐标下耳朵区域
        if z > 0.55 and x < -0.30:
            vert_bone[v.index] = "Ear_L"
        elif z > 0.55 and x > 0.30:
            vert_bone[v.index] = "Ear_R"
        else:
            vert_bone[v.index] = "Body"

    print(f"  未分配顶点（按位置兜底）: {unassigned}")

    # --- 第三步：真正写入权重 ---
    buckets = {n: [] for n in names}
    for vi, bone in vert_bone.items():
        buckets[bone].append(vi)

    for bone, vids in buckets.items():
        if vids:
            groups[bone].add(vids, 1.0, 'REPLACE')

    print(f"  权重写入:")
    for n in names:
        print(f"    {n:8s}: {len(buckets[n])} 顶点")

    # --- 校验：每个顶点恰好属于一个组 ---
    bad = 0
    for v in me.vertices:
        total = sum(g.weight for g in v.groups)
        if abs(total - 1.0) > 0.001:
            bad += 1
    print(f"  权重校验: {bad} 个顶点权重异常（应为 0）")

    # --- Armature 修改器（放在描边之后）---
    for m in list(mesh_obj.modifiers):
        if m.type == 'ARMATURE':
            mesh_obj.modifiers.remove(m)

    mod = mesh_obj.modifiers.new(name="Armature", type='ARMATURE')
    mod.object = arm_obj
    mod.use_vertex_groups = True
    mod.use_bone_envelopes = False     # 关闭封套，只用顶点组

    mesh_obj.parent = arm_obj
    mesh_obj.matrix_parent_inverse = arm_obj.matrix_world.inverted()
    print(f"  Armature 修改器已添加（仅用顶点组，关闭封套）")


def main():
    print("=" * 60)
    print("刚性绑定 v4")
    print("=" * 60)

    mesh = bpy.data.objects.get("Chiikawa")
    arm = bpy.data.objects.get("ChiikawaRig")
    if not mesh or not arm:
        print(f"错误: mesh={mesh} arm={arm}")
        return

    # 清掉旧父级
    mesh.parent = None
    mesh.matrix_world = mesh.matrix_world  # 保持变换

    rigid_bind_v4(mesh, arm)

    out = os.path.join(BASE, "models", "chiikawa_rigged.blend")
    bpy.ops.wm.save_as_mainfile(filepath=out)
    print(f"  已保存: {out}")
    print("=" * 60)


if __name__ == "__main__":
    main()
