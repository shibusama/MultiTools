"""
干净验证：新建一个最简场景，球体 + 简化的法线着色
只验证「Geometry.Normal 接进节点后是否保留符号」
"""
import bpy
import numpy as np
import os

OUT = r"D:\C_Relocated\Users\13191\MultiTools\projects\chiikawa\renders"

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0,0,0))
sp = bpy.context.active_object
bpy.ops.object.shade_smooth()

mat = bpy.data.materials.new("T")
mat.use_nodes = True
nt = mat.node_tree
nodes, links = nt.nodes, nt.links
nodes.clear()

out = nodes.new('ShaderNodeOutputMaterial')
geo = nodes.new('ShaderNodeNewGeometry')
sep = nodes.new('ShaderNodeSeparateXYZ')
em = nodes.new('ShaderNodeEmission')

links.new(geo.outputs['Normal'], sep.inputs['Vector'])

# 测试：X 分量 + 1 再除 2（重映射）
mad = nodes.new('ShaderNodeMath')
mad.operation = 'MULTIPLY_ADD'
mad.inputs[1].default_value = 0.5
mad.inputs[2].default_value = 0.5
links.new(sep.outputs['X'], mad.inputs[0])
links.new(mad.outputs['Value'], em.inputs['Color'])
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

tmp = os.path.join(OUT, "_nxtest.png")
sc.render.filepath = tmp
bpy.ops.render.render(write_still=True)

img = bpy.data.images.load(tmp)
w,h = img.size
v = np.array(img.pixels[:]).reshape(h,w,4)[:,:,0]
# 只看球体（排除背景）
c = v[h//4:3*h//4, w//4:3*w//4].ravel()
s = c[(c>0.02)&(c<0.98)]

print("="*56)
print("测试：nx' = (nx+1)/2  的分布")
print("="*56)
print(f"  样本={s.size}")
print(f"  范围 {s.min():.3f} ~ {s.max():.3f}  均值 {s.mean():.3f} 标准差 {s.std():.3f}")
print(f"\n  如果重映射成功：应该有 0.2~0.8 的宽分布")
print(f"  如果仍被裁剪：分布会挤在 0.5 附近")

hist, edges = np.histogram(s, bins=10, range=(0,1))
for i,cnt in enumerate(hist):
    pct = cnt/s.size*100
    if pct>2: print(f"    {edges[i]:.1f}-{edges[i+1]:.1f}: {pct:5.1f}% {'#'*int(pct/2)}")

bpy.data.images.remove(img)
os.remove(tmp)
print("="*56)
