"""
验证：真实光照 + 自发光输出的三渲二方案
==========================================
抖音教程原话：「先加一个描边，然后添加一个实体化修改器，
                其他都可以复制，记得别忘记把材质都改成自发光」

关键理解：他们用【真实灯光】照场景，材质用自发光输出。
但这样一来光照就不影响颜色了... 所以更可能是：

  他们用真实灯光 + 普通材质，然后描边用自发光。
  「材质改成自发光」指的是描边材质和环境/背景材质。

  另一种更符合三渲二原理的理解：
  用 Diffuse 接收光照 -> 量化 -> Emission 输出

本脚本测试第二种：能否拿到真实光照强度。
"""
import bpy
import numpy as np
import os

OUT = r"D:\C_Relocated\Users\13191\MultiTools\projects\chiikawa\renders"

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# 球
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0,0,0))
sp = bpy.context.active_object
bpy.ops.object.shade_smooth()

# 真实灯光：太阳光从左侧掠射
bpy.ops.object.light_add(type='SUN', location=(-5,0,0))
sun = bpy.context.active_object
sun.data.energy = 3.0
sun.rotation_euler = (1.5708, 0, -1.5708)   # 从左侧水平打

# 世界环境光压低
world = bpy.data.worlds.new("W")
bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs['Color'].default_value = (1,1,1,1)
bg.inputs['Strength'].default_value = 0.08

# 材质：测试能否拿到光照
mat = bpy.data.materials.new("T")
mat.use_nodes = True
nt = mat.node_tree
nodes, links = nt.nodes, nt.links
nodes.clear()

out = nodes.new('ShaderNodeOutputMaterial')
diff = nodes.new('ShaderNodeBsdfDiffuse')
diff.inputs['Color'].default_value = (1,1,1,1)   # 白色，只取光照强度

em = nodes.new('ShaderNodeEmission')

# 方案：Diffuse -> Light Path 判断 -> Emission
# 但 Diffuse 输出是 shader，不能直接转颜色
# 用 ShaderToRGB 试试（虽然之前失效，再确认一次）
s2rgb = nodes.new('ShaderNodeShaderToRGB')
bw = nodes.new('ShaderNodeRGBToBW')

links.new(diff.outputs['BSDF'], s2rgb.inputs['Shader'])
links.new(s2rgb.outputs['Color'], bw.inputs['Color'])
links.new(bw.outputs['Val'], em.inputs['Color'])
links.new(em.outputs['Emission'], out.inputs['Surface'])

sp.data.materials.append(mat)

bpy.ops.object.camera_add(location=(0,-5,0), rotation=(1.5708,0,0))
bpy.context.scene.camera = bpy.context.active_object

sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x = 300
sc.render.resolution_y = 300
sc.render.film_transparent = False
try: sc.view_settings.view_transform = 'Standard'
except: pass

tmp = os.path.join(OUT, "_lighttest.png")
sc.render.filepath = tmp
bpy.ops.render.render(write_still=True)

img = bpy.data.images.load(tmp)
w,h = img.size
v = np.array(img.pixels[:]).reshape(h,w,4)[:,:,:3].mean(axis=2)
c = v[h//4:3*h//4, w//4:3*w//4].ravel()
s = c[(c>0.02)&(c<0.98)]

print("="*58)
print("真实光照 -> ShaderToRGB -> BW 结果")
print("="*58)
print(f"  样本={s.size}")
if s.size:
    print(f"  范围 {s.min():.4f} ~ {s.max():.4f}")
    print(f"  均值 {s.mean():.4f}  标准差 {s.std():.4f}")
    hist, edges = np.histogram(s, bins=10, range=(0,1))
    for i,cnt in enumerate(hist):
        pct=cnt/s.size*100
        if pct>2: print(f"    {edges[i]:.1f}-{edges[i+1]:.1f}: {pct:5.1f}% {'#'*int(pct/2)}")
    if s.std() > 0.1:
        print("\n  ✓ 拿到真实光照，分布有动态范围")
    else:
        print("\n  ✗ 光照值仍无变化")
else:
    print("  全黑 -> ShaderToRGB 确实失效")

bpy.data.images.remove(img)
os.remove(tmp)
print("="*58)
