# -*- coding: utf-8 -*-
"""拉面獭 v2 精灵稿 — 头脸手工像素网格 + 碗/尾程序化纹理"""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[3] / "projects" / "dex" / "renders"

PAL = {
    "o": (58, 42, 32), "A": (242, 214, 160), "C": (252, 238, 206),
    "W": (255, 252, 246), "w": (238, 228, 215),
    "E": (30, 26, 26), "G": (255, 255, 255), "P": (244, 158, 166),
    "N": (74, 50, 38),
}
R, D, L = (224, 82, 62), (172, 58, 44), (248, 122, 100)
Y, y, U = (244, 204, 98), (250, 226, 140), (120, 196, 110)

# 26 宽 × 18 高 头脸网格（每行必须 26 字符）
HEAD = [
    "...oo..............oo.....",
    "..oAAo..............oAAo..",
    "..oAAoooooooooooooooAAo...",
    ".oAAAAAAAAAAAAAAAAAAAAAAo.",
    "oAAAAAAAAAAAAAAAAAAAAAAAAo",
    "oAAAAAAAAAAAAAAAAAAAAAAAAo",
    "oAAAAWWWEEWWWWWWEEWWWAAAAo",
    "oAAAAWWWGEWWWWWWGEWWWAAAAo",
    "oAAAAWWWWWWWWWWWWWWWWAAAAo",
    "oAAAAWWWWWWWNNWWWWWWWAAAAo",
    "oAAAAWWWWWWNWWNWWWWWWAAAAo",
    "oAPPAAWWWWWWWWWWWWWWWWAPPo",
    "oAAAAwwwwwwwwwwwwwwwwAAAAo",
    "oAAAAAwwwwwwwwwwwwwwAAAAAo",
    "oAAAAAAwwwwwwwwwwwwAAAAAAo",
]


def build_head():
    w = 26
    h = len(HEAD)
    img = np.zeros((h, w, 4), dtype=np.uint8)
    for i, row in enumerate(HEAD):
        assert len(row) == w, f"row {i} len {len(row)} != {w}: {row!r}"
        for x, ch in enumerate(row):
            if ch != ".":
                img[i, x, :3] = PAL[ch]
                img[i, x, 3] = 255
    return Image.fromarray(img, "RGBA")


def draw_otter_v2(tick=0, blink=False, wag=0):
    """返回 32x30 精灵（含碗/爪/尾/蒸汽）"""
    head = build_head()
    if blink:
        a = np.array(head)
        for row in (6, 7):
            for x in range(26):
                if tuple(a[row, x][:3]) in (PAL["E"], PAL["G"]):
                    a[row, x] = (58, 42, 32, 255)
        head = Image.fromarray(a, "RGBA")
    W, H = 32, 30
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ox, oy = 3, 2 + (tick // 2) % 2
    img.paste(head, (ox, oy))
    d = ImageDraw.Draw(img)
    # 尾巴（右侧面条尾）
    tx, ty = ox + 24, oy + 6 + wag
    for i, (dx, dy) in enumerate([(0, 2), (1, 1), (2, 0), (3, -1), (4, -1), (5, -1)]):
        d.point((tx + dx, ty + dy), fill=y if i % 2 else Y)
    # 碗
    bx, by = ox + 2, oy + 15
    d.ellipse((bx + 1, by, bx + 21, by + 4), fill=R)
    d.rectangle((bx + 2, by + 3, bx + 20, by + 8), fill=R)
    d.rectangle((bx + 2, by + 7, bx + 20, by + 8), fill=D)
    d.point((bx + 4, by + 1), fill=L); d.point((bx + 5, by + 1), fill=L)
    d.point((bx + 18, by + 4), fill=D)
    # 面条 + 葱花
    for i, nx in enumerate(range(bx + 3, bx + 20, 2)):
        d.point((nx, by - 1 - (i % 2)), fill=y if i % 3 else Y)
        if i % 4 == 1:
            d.point((nx, by - 1), fill=U)
    d.point((bx + 10, by - 1), fill=(255, 255, 255))
    # 爪子
    d.ellipse((bx - 2, by + 1, bx + 2, by + 5), fill=PAL["A"], outline=PAL["o"])
    d.ellipse((bx + 20, by + 1, bx + 24, by + 5), fill=PAL["A"], outline=PAL["o"])
    # 蒸汽
    for i, sx in enumerate((bx + 6, bx + 12, bx + 16)):
        zy = (tick + i * 3) % 9
        c = (235, 242, 242)
        d.point((sx + ((tick + i) // 3) % 2, by - 3 - zy), fill=c)
        d.point((sx, by - 4 - zy), fill=c)
    return img


def main():
    for blink in (False, True):
        spr = draw_otter_v2(tick=0, blink=blink)
        big = spr.resize((32 * 14, 30 * 14), Image.NEAREST)
        big.save(OUT / f"sprite_v2_{int(blink)}.png")
    print("saved previews")


if __name__ == "__main__":
    main()
