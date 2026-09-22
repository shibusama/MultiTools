import bpy
import sys

print("=== BLENDER VERSION ===")
print(bpy.app.version_string)

print("=== RENDER ENGINES ===")
try:
    prop = bpy.types.RenderSettings.bl_rna.properties['engine']
    for item in prop.enum_items:
        print(" ", item.identifier, "|", item.name)
except Exception as e:
    print("ERR:", e)

print("=== SHADER TO RGB AVAILABLE? ===")
try:
    node = bpy.types.ShaderNodeShaderToRGB
    print("  ShaderNodeShaderToRGB EXISTS:", node.bl_rna.identifier)
except Exception as e:
    print("  NOT FOUND:", e)

print("=== COLOR RAMP INTERPOLATION OPTIONS ===")
try:
    prop = bpy.types.ColorRampElement.bl_rna.properties.get('color')
    print("  color prop ok:", prop is not None)
    interp = bpy.types.ColorRamp.bl_rna.properties['interpolation']
    for item in interp.enum_items:
        print(" ", item.identifier, "|", item.name)
except Exception as e:
    print("ERR:", e)

print("=== EEVEE NEXT NAME CHECK ===")
try:
    scn = bpy.context.scene
    for eng in ['BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE', 'CYCLES', 'BLENDER_WORKBENCH']:
        try:
            scn.render.engine = eng
            print("  OK:", eng)
        except Exception as e:
            print("  FAIL:", eng, e)
except Exception as e:
    print("ERR:", e)

print("=== MATERIAL OUTPUT / NODE TYPES ===")
print("  Diffuse BSDF:", hasattr(bpy.types, 'ShaderNodeBsdfDiffuse'))
print("  Emission   :", hasattr(bpy.types, 'ShaderNodeEmission'))
print("  Solidify mod:", hasattr(bpy.types, 'SolidifyModifier'))
print("=== DONE ===")
