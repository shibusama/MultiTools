"""
决定性的 A/B 测试：
把 ColorRamp 阈值设成 0.01 和 0.99，两次渲染
如果两次结果完全一样 -> ColorRamp 根本没连到最终输出
"""
import bpy
import numpy as np
import os

base = r"D:\C_Relocated\Users\13191\MultiTools\chiikawa动画制作"
out_dir = os.path.join(base, "renders")

body = bpy.data.objects.get("Body")
mat = body.data.materials[0]
nt = mat.node_tree

print("=" * 64)
print("Body 材质节点连接关系")
print("=" * 64)
for n in nt.nodes:
    print(f"\n[{n.name}] type={n.type}")
    for out in n.outputs:
        for link in out.links:
            print(f"    {out.name} --> {link.to_node.name}.{link.to_socket.name}")

ramp = next(n for n in nt.nodes if n.type == 'VALTORGB')
cr = ramp.color_ramp
cr.elements[0].color = (1.0, 0.0, 0.0, 1.0)
cr.elements[1].color = (0.0, 0.0, 1.0, 1.0)

scene = bpy.context.scene
scene.render.resolution_x = 300
scene.render.resolution_y = 300

def render_and_hash(thr, tag):
    cr.elements[0].position = thr
    p = os.path.join(out_dir, f"_ab_{tag}.png")
    scene.render.filepath = p
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(p)
    w, h = img.size
    px = np.array(img.pixels[:]).reshape(h, w, 4)
    arr = (px[:,:,:3] * 255).astype(np.uint8)
    red = ((arr[:,:,0] > 100) & (arr[:,:,0] > arr[:,:,1].astype(int) + 60)).sum()
    blue = ((arr[:,:,2] > 100) & (arr[:,:,2] > arr[:,:,0].astype(int) + 60)).sum()
    bpy.data.images.remove(img)
    print(f"  阈值={thr:.2f}: 红像素={red:6d}  蓝像素={blue:6d}")
    return red, blue

print("\n" + "=" * 64)
print("A/B 测试")
print("=" * 64)
r1, b1 = render_and_hash(0.01, "low")
r2, b2 = render_and_hash(0.99, "high")

print("\n" + "=" * 64)
if (r1, b1) == (r2, b2):
    print("!!! 两次结果完全相同 -> ColorRamp 没有影响渲染结果 !!!")
    print("    说明 Body 的材质输出没走 ColorRamp 这条链")
else:
    print("✓ ColorRamp 生效：阈值变化会改变渲染结果")
    print(f"   阈值 0.01 时红={r1} 蓝={b1}")
    print(f"   阈值 0.99 时红={r2} 蓝={b2}")
print("=" * 64)
