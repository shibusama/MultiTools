"""
最终标定：基于实测分布（主峰 0.40-0.425，尾部到 0.98）
阈值取 0.44 左右可把「环境光底座」与「受光面」分开
"""
import bpy
import numpy as np
import os
import sys
import math

BASE = r"D:\C_Relocated\Users\13191\MultiTools\chiikawa动画制作"
sys.path.insert(0, os.path.join(BASE, "scripts"))
OUT = os.path.join(BASE, "renders")
from apply_toon_v9 import make_toon_material_v9

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0,0,0),
                                     segments=64, ring_count=32)
sp = bpy.context.active_object
sp.scale = (1.08, 1.0, 0.96)
bpy.context.view_layer.objects.active = sp
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
bpy.ops.object.shade_smooth()

mat = make_toon_material_v9("CAL", (0.9,0.88,0.82))
sp.data.materials.append(mat)

bpy.ops.object.light_add(type='SUN', location=(-5,-1,1))
sun = bpy.context.active_object
sun.data.energy = 5.0
sun.rotation_euler = (math.radians(75), 0, math.radians(-85))

world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs['Color'].default_value = (1,1,1,1)
    bg.inputs['Strength'].default_value = 0.15

bpy.ops.object.camera_add(location=(0,-5,0), rotation=(1.5708,0,0))
bpy.context.scene.camera = bpy.context.active_object

sc = bpy.context.scene
sc.render.engine='BLENDER_EEVEE'
sc.render.resolution_x=400; sc.render.resolution_y=400
sc.render.film_transparent=False
try: sc.view_settings.view_transform='Standard'
except: pass

nt = mat.node_tree
bw = next(n for n in nt.nodes if n.type=='RGBTOBW')
em = next(n for n in nt.nodes if n.type=='EMISSION')
nt.links.new(bw.outputs['Val'], em.inputs['Color'])

tmp = os.path.join(OUT, "_g2.png")
sc.render.filepath = tmp
bpy.ops.render.render(write_still=True)
img = bpy.data.images.load(tmp)
w,h = img.size
v = np.array(img.pixels[:]).reshape(h,w,4)[:,:,:3].mean(axis=2)
bpy.data.images.remove(img)
s = v.ravel()
s = s[(s>0.02)&(s<0.985)]

print("=" * 58)
print("候选阈值下的阴影占比")
print("=" * 58)
for t in [0.42, 0.43, 0.44, 0.45, 0.46, 0.48, 0.50, 0.55]:
    print(f"  阈值 {t:.2f}: 阴影 {(s<t).mean()*100:5.1f}%  亮部 {(s>=t).mean()*100:5.1f}%")
print("=" * 58)
os.remove(tmp)
