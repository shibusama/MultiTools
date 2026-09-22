"""
干净的量化验证：直接读 PNG 文件字节，不用 Blender 图像缓存
"""
import struct
import zlib
import os

def read_png(path):
    """最小 PNG 解码（8-bit RGB/RGBA）"""
    with open(path, "rb") as f:
        data = f.read()
    assert data[:8] == b'\x89PNG\r\n\x1a\n'
    pos = 8
    w = h = bitdepth = colortype = None
    idat = b''
    while pos < len(data):
        ln = struct.unpack('>I', data[pos:pos+4])[0]
        typ = data[pos+4:pos+8]
        chunk = data[pos+8:pos+8+ln]
        if typ == b'IHDR':
            w, h, bitdepth, colortype = struct.unpack('>IIBB', chunk[:10])
        elif typ == b'IDAT':
            idat += chunk
        elif typ == b'IEND':
            break
        pos += 12 + ln

    raw = zlib.decompress(idat)
    ch = {0:1, 2:3, 4:2, 6:4}[colortype]
    stride = w * ch
    out = bytearray(w * h * ch)
    prev = bytearray(stride)
    p = 0
    for y in range(h):
        ft = raw[p]; p += 1
        line = bytearray(raw[p:p+stride]); p += stride
        if ft == 1:
            for i in range(ch, stride):
                line[i] = (line[i] + line[i-ch]) & 255
        elif ft == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 255
        elif ft == 3:
            for i in range(stride):
                a = line[i-ch] if i >= ch else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 255
        elif ft == 4:
            for i in range(stride):
                a = line[i-ch] if i >= ch else 0
                b = prev[i]
                c = prev[i-ch] if i >= ch else 0
                pa, pb, pc = abs(b-c), abs(a-c), abs(a+b-2*c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 255
        out[y*stride:(y+1)*stride] = line
        prev = line
    return w, h, ch, out


def analyze(path, label):
    w, h, ch, px = read_png(path)
    # 中心区域
    x0, x1 = w//3, 2*w//3
    y0, y1 = h//3, 2*h//3
    vals = []
    for y in range(y0, y1):
        for x in range(x0, x1):
            i = (y*w + x) * ch
            r, g, b = px[i], px[i+1], px[i+2]
            vals.append((r+g+b)/3/255)
    vals.sort()
    n = len(vals)
    mean = sum(vals)/n
    var = sum((v-mean)**2 for v in vals)/n
    std = var**0.5

    # 排除背景(>0.97)和描边(<0.15)
    body = [v for v in vals if 0.15 < v < 0.97]
    bmean = sum(body)/len(body) if body else 0
    bstd = (sum((v-bmean)**2 for v in body)/len(body))**0.5 if body else 0

    # 直方图找峰
    bins = [0]*20
    for v in body:
        idx = min(int(v*20), 19)
        bins[idx] += 1
    peaks = []
    tot = len(body)
    for i in range(1, 19):
        if bins[i] > bins[i-1] and bins[i] > bins[i+1] and bins[i]/tot > 0.05:
            peaks.append((i/20+0.025, bins[i]/tot*100))

    print(f"[{label}] {w}x{h}")
    print(f"    角色像素={tot}  均值={bmean:.4f}  标准差={bstd:.4f}")
    print(f"    色阶峰: {[(round(p,2), round(q,1)) for p,q in peaks]}")
    return bstd, len(peaks)


BASE = r"D:\C_Relocated\Users\13191\MultiTools\chiikawa动画制作\renders"
print("=" * 60)
print("各版本三渲二效果量化对比")
print("=" * 60)

for label, fn in [("v2(点乘)", "keyframe_001.png"),
                  ("v4(阈值0.86)", "v4_keyframe_001.png"),
                  ("v5(法线重映射)", "v5_keyframe_001.png")]:
    p = os.path.join(BASE, fn)
    if os.path.exists(p):
        analyze(p, label)
    else:
        print(f"[{label}] 文件不存在")
print("=" * 60)
