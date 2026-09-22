"""检查合并后网格的实际坐标范围"""
import bpy

mesh = bpy.data.objects.get("Chiikawa")
me = mesh.data

zs = [v.co.z for v in me.vertices]
xs = [v.co.x for v in me.vertices]
ys = [v.co.y for v in me.vertices]

print(f"对象: {mesh.name}")
print(f"对象位置: {tuple(round(v,3) for v in mesh.location)}")
print(f"对象缩放: {tuple(round(v,3) for v in mesh.scale)}")
print(f"顶点数: {len(me.vertices)}")
print(f"\n局部坐标范围:")
print(f"  X: {min(xs):.3f} ~ {max(xs):.3f}")
print(f"  Y: {min(ys):.3f} ~ {max(ys):.3f}")
print(f"  Z: {min(zs):.3f} ~ {max(zs):.3f}")

# 顶部区域（应该是耳朵）
top = [v.co for v in me.vertices if v.co.z > (min(zs) + (max(zs)-min(zs))*0.75)]
if top:
    txs = [c.x for c in top]
    print(f"\n顶部25%区域 ({len(top)} 顶点):")
    print(f"  X: {min(txs):.3f} ~ {max(txs):.3f}")
    print(f"  Z: {min(c.z for c in top):.3f} ~ {max(c.z for c in top):.3f}")

# 材质分布：看眼睛顶点在哪
print(f"\n材质槽:")
for i, m in enumerate(me.materials):
    print(f"  [{i}] {m.name if m else None}")

# 按材质统计顶点位置
print(f"\n各材质对应顶点范围:")
for i, m in enumerate(me.materials):
    if not m: continue
    verts = []
    for poly in me.polygons:
        if poly.material_index == i:
            for vi in poly.vertices:
                verts.append(me.vertices[vi].co)
    if verts:
        zz = [c.z for c in verts]
        xx = [c.x for c in verts]
        print(f"  {m.name:12s}: Z {min(zz):6.2f}~{max(zz):6.2f}  X {min(xx):6.2f}~{max(xx):6.2f}  ({len(verts)}顶点)")
