"""
验证：合并阶段应用 Solidify 修改器是否破坏了几何
对比「应用描边修改器」vs「保留修改器直接合并」
"""
import bpy

mesh = bpy.data.objects.get("Chiikawa")
me = mesh.data

print("=" * 60)
print("几何完整性检查")
print("=" * 60)

# 按材质统计顶点分布，看眼睛/腮红是否正常
print("\n各材质顶点 Z/X 范围:")
for i, m in enumerate(me.materials):
    if not m: continue
    verts = set()
    for poly in me.polygons:
        if poly.material_index == i:
            verts.update(poly.vertices)
    if not verts:
        continue
    coords = [me.vertices[vi].co for vi in verts]
    zz = [c.z for c in coords]
    xx = [c.x for c in coords]
    yy = [c.y for c in coords]
    print(f"  {m.name:12s}: {len(verts):5d}顶点  "
          f"X[{min(xx):6.2f},{max(xx):6.2f}] "
          f"Y[{min(yy):6.2f},{max(yy):6.2f}] "
          f"Z[{min(zz):6.2f},{max(zz):6.2f}]")

# 检查是否有孤立/重复顶点
print(f"\n总计: {len(me.vertices)} 顶点, {len(me.polygons)} 面")
print(f"对象位置: {tuple(round(v,3) for v in mesh.location)}")

# 检查修改器
print(f"\n修改器:")
for m in mesh.modifiers:
    print(f"  {m.name}: {m.type}" +
          (f" show_viewport={m.show_viewport} show_render={m.show_render}"
           if m.type=='ARMATURE' else ""))

# 关键：检查眼睛顶点的 Y 坐标
# 眼睛应该在身体前表面 (Y 约 -0.9 局部坐标 -> 实际约 -0.9)
eye_verts = set()
for i, m in enumerate(me.materials):
    if m and m.name in ("M_Eye_L", "M_Eye_R"):
        for poly in me.polygons:
            if poly.material_index == i:
                eye_verts.update(poly.vertices)
if eye_verts:
    ys = [me.vertices[v].co.y for v in eye_verts]
    print(f"\n眼睛顶点 Y 范围: {min(ys):.3f} ~ {max(ys):.3f}")
    print(f"  (应集中在身体前表面，若跨度过大说明被拉伸)")
