"""
同进程验证：构建材质后立即检查阈值，排除文件陈旧问题
"""
import bpy
import sys
import os

BASE = r"D:\C_Relocated\Users\13191\MultiTools\projects\chiikawa"
sys.path.insert(0, os.path.join(BASE, "scripts"))

from apply_toon_v6 import make_toon_material_v6

def s2l(c):
    return c/12.92 if c <= 0.04045 else ((c+0.055)/1.055)**2.4

def col(r, g, b):
    return tuple(s2l(v) for v in (r, g, b))

print("=" * 58)
print("同进程阈值验证")
print("=" * 58)

# 用旧名字会命中已有材质，所以先删掉
for n in ["TEST_HI", "TEST_LO"]:
    m = bpy.data.materials.get(n)
    if m:
        bpy.data.materials.remove(m)

m_hi = make_toon_material_v6("TEST_HI", col(0.98,0.97,0.94), ramp_pos=0.86)
m_lo = make_toon_material_v6("TEST_LO", col(0.98,0.97,0.94), ramp_pos=0.50)

for m, expect in [(m_hi, 0.86), (m_lo, 0.50)]:
    ramp = next(n for n in m.node_tree.nodes if n.type == 'VALTORGB')
    actual = ramp.color_ramp.elements[0].position
    ok = abs(actual - expect) < 0.001
    print(f"  {m.name}: 阈值={actual:.3f} 期望={expect:.2f}  {'OK' if ok else 'MISMATCH'}")

# 检查当前场景里的实际材质
print("\n当前场景材质阈值:")
for mat in bpy.data.materials:
    if not mat.use_nodes:
        continue
    for n in mat.node_tree.nodes:
        if n.type == 'VALTORGB':
            print(f"  {mat.name}: {n.color_ramp.elements[0].position:.3f}")
print("=" * 58)
