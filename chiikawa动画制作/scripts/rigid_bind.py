"""
骨骼绑定 v2 —— 手动刚性权重
============================
问题：自动权重(ARMATURE_AUTO)会把眼睛/腮红等小部件与身体骨骼混合权重，
      导致变形被拉扯（眼睛变椭圆、腮红被挤成月牙）。

方案：改用【顶点组 + 精确分配】——
      每个部件按其所在位置，100% 绑定到对应骨骼，不做混合。
      Chiikawa 是硬质卡通角色，刚性绑定正是想要的效果。
"""
import bpy
import math
import os

BASE = r"D:\C_Relocated\Users\13191\MultiTools\chiikawa动画制作"


def rigid_bind(mesh_obj, arm_obj):
    """
    刚性绑定 v3：按【材质槽】分配顶点到骨骼。

    关键发现（check_coords.py 实测）：
    - 网格对象原点在 (0,0,1)，局部 Z 范围是 -1.0~1.28（不是世界坐标 0~2.28）
    - 每个部件有独立的材质槽，用材质索引判断归属最可靠

    分配规则：
      M_Body / Outline  -> Body 骨骼
      M_Ear_L           -> Ear_L 骨骼
      M_Ear_R           -> Ear_R 骨骼
      眼睛/嘴/腮红       -> Body 骨骼（它们长在脸上，跟着身体动）
    """
    me = mesh_obj.data

    for vg in list(mesh_obj.vertex_groups):
        mesh_obj.vertex_groups.remove(vg)

    groups = {}
    for name in ["Root", "Body", "Ear_L", "Ear_R"]:
        groups[name] = mesh_obj.vertex_groups.new(name=name)

    # 材质名 -> 骨骼名
    def bone_for_material(mat_name):
        if mat_name == "M_Ear_L":
            return "Ear_L"
        if mat_name == "M_Ear_R":
            return "Ear_R"
        return "Body"   # 身体、描边、眼睛、嘴、腮红都跟身体

    counts = {}
    for poly in me.polygons:
        mi = poly.material_index
        mat = me.materials[mi] if mi < len(me.materials) else None
        mat_name = mat.name if mat else ""
        bone = bone_for_material(mat_name)

        for vi in poly.vertices:
            groups[bone].add([vi], 1.0, 'REPLACE')
            counts[bone] = counts.get(bone, 0) + 1

    # 统计实际唯一顶点
    uniq = {}
    for name, vg in groups.items():
        n = 0
        for v in me.vertices:
            for g in v.groups:
                if g.group == vg.index and g.weight > 0:
                    n += 1
                    break
        uniq[name] = n

    print(f"  顶点分配（唯一顶点数）:")
    for k, v in uniq.items():
        print(f"    {k:8s}: {v}")

    has_arm_mod = any(m.type == 'ARMATURE' for m in mesh_obj.modifiers)
    if not has_arm_mod:
        mod = mesh_obj.modifiers.new(name="Armature", type='ARMATURE')
        mod.object = arm_obj
        print("  已添加 Armature 修改器")
    else:
        for m in mesh_obj.modifiers:
            if m.type == 'ARMATURE':
                m.object = arm_obj

    mesh_obj.parent = arm_obj
    mesh_obj.matrix_parent_inverse = arm_obj.matrix_world.inverted()


def smooth_weights(mesh_obj):
    """
    可选：对耳朵根部做轻微平滑，避免生硬断裂。
    只处理耳朵根部附近的顶点。
    """
    # 这里先不做，保持刚性。如果需要可后续加。
    pass


def main():
    print("=" * 60)
    print("骨骼绑定 v2（刚性权重）")
    print("=" * 60)

    mesh = bpy.data.objects.get("Chiikawa")
    arm = bpy.data.objects.get("ChiikawaRig")

    if not mesh or not arm:
        print(f"错误: mesh={mesh}, arm={arm}")
        return

    # 移除旧的 Armature 修改器
    for m in list(mesh.modifiers):
        if m.type == 'ARMATURE':
            mesh.modifiers.remove(m)
            print("  移除旧 Armature 修改器")

    # 移除旧父级关系
    mesh.parent = None

    rigid_bind(mesh, arm)

    # 保存
    out = os.path.join(BASE, "models", "chiikawa_rigged.blend")
    bpy.ops.wm.save_as_mainfile(filepath=out)
    print(f"\n已保存: {out}")
    print("=" * 60)


if __name__ == "__main__":
    main()
