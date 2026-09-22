"""
检查 Rigify 插件可用性 + 真实光照方案的前置条件
"""
import bpy
import addon_utils

print("=" * 60)
print("Rigify 插件检查")
print("=" * 60)

# 列出可能的 rigify 模块名
for name in ["rigify", "bl_ext.blender_org.rigify", "add_curve_extra_objects"]:
    try:
        mod = addon_utils.enable(name, default_set=False, persistent=True)
        print(f"  enable({name}) -> {mod}")
    except Exception as e:
        print(f"  enable({name}) 失败: {e}")

# 检查是否已启用
print("\n已启用的插件:")
for m in addon_utils.modules():
    if addon_utils.check(m.__name__)[1]:
        if 'rig' in m.__name__.lower():
            print(f"  ★ {m.__name__}")

# 检查骨架菜单里有没有 rigify 的骨架类型
print("\n可用骨架类型（前30）:")
try:
    types = bpy.types.EnumProperty
    # 直接从 armature_add 的枚举取
    props = bpy.ops.object.armature_basic_human_metarig
    print(f"  armature_basic_human_metarig 存在: {props is not None}")
except Exception as e:
    print(f"  检查失败: {e}")

# 更直接：查 ops
candidates = [o for o in dir(bpy.ops.object) if 'metarig' in o.lower() or 'rigify' in o.lower()]
print(f"\n相关操作符: {candidates}")

# 检查 EEVEE 真实光照相关设置
print("\n" + "=" * 60)
print("EEVEE 光照设置")
print("=" * 60)
sc = bpy.context.scene
ee = sc.eevee
for attr in ["use_gtao", "gtao_distance", "use_shadows", "shadow_ray_count",
             "use_raytracing"]:
    if hasattr(ee, attr):
        print(f"  eevee.{attr} = {getattr(ee, attr)}")

print("\n" + "=" * 60)
print("自发光(Emission)材质方案检查")
print("=" * 60)
print(f"  ShaderNodeEmission 可用: {hasattr(bpy.types, 'ShaderNodeEmission')}")
print(f"  Diffuse BSDF 可用: {hasattr(bpy.types, 'ShaderNodeBsdfDiffuse')}")
print(f"  Light Path 可用: {hasattr(bpy.types, 'ShaderNodeLightPath')}")
