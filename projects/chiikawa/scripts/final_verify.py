"""
终极验证：Shader to RGB 在 Blender 5.2 EEVEE 下到底输出了什么
方法：把 ColorRamp 的 Factor 用数值节点强制指定，绕开 ShaderToRGB
"""
import bpy
import numpy as np
import os

out_dir = r"D:\C_Relocated\Users\13191\MultiTools\projects\chiikawa\renders"
body = bpy.data.objects.get("Body")
mat = body.data.materials[0]
nt = mat.node_tree
ramp = next(n for n in nt.nodes if n.type == 'VALTORGB')
out_node = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
s2rgb = next(n for n in nt.nodes if n.type == 'SHADERTORGB')

cr = ramp.color_ramp
cr.elements[0].color = (1.0, 0.0, 0.0, 1.0)
cr.elements[1].color = (0.0, 0.0, 1.0, 1.0)

scene = bpy.context.scene
scene.render.resolution_x = 300
scene.render.resolution_y = 300

def count_colors(tag):
    p = os.path.join(out_dir, f"_final_{tag}.png")
    scene.render.filepath = p
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(p)
    w, h = img.size
    px = np.array(img.pixels[:]).reshape(h, w, 4)
    a = (px[:,:,:3]*255).astype(np.uint8)
    red = ((a[:,:,0]>100) & (a[:,:,0].astype(int) > a[:,:,1].astype(int)+60)).sum()
    blue = ((a[:,:,2]>100) & (a[:,:,2].astype(int) > a[:,:,0].astype(int)+60)).sum()
    bpy.data.images.remove(img)
    return red, blue

# --- 步骤1: 断开 ShaderToRGB，改用数值节点喂 Factor ---
for link in list(ramp.inputs['Fac'].links):
    nt.links.remove(link)

val = nt.nodes.new('ShaderNodeValue')
val.location = (-100, -200)

nt.links.new(val.outputs['Value'], ramp.inputs['Fac'])
print("已切换到数值节点控制 Factor")

print("\n测试 A: Factor 强制 = 0.0 (应全红/阴影)")
val.outputs['Value'].default_value = 0.0
cr.elements[0].position = 0.5
r, b = count_colors("a")
print(f"  红={r} 蓝={b}")
if b > 0 and r == 0:
    print("  ✓ 亮部。说明 0.0 > 阈值0.5? 不对——需检查ColorRamp方向")

print("\n测试 B: Factor 强制 = 1.0")
val.outputs['Value'].default_value = 1.0
r2, b2 = count_colors("b")
print(f"  红={r2} 蓝={b2}")

print("\n" + "="*60)
if (r, b) != (r2, b2):
    print("✓ 手动喂值有效 -> ColorRamp 本身没问题")
    print("  问题出在 Shader to RGB 的输出上")
else:
    print("✗ 手动喂值也无效 -> ColorRamp 或渲染管线有问题")
print("="*60)
