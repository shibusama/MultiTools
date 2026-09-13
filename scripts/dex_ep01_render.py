# -*- coding: utf-8 -*-
"""不存在图鉴 EP01 — 拉面獭 像素动画渲染 + ffmpeg 合成
逻辑网格 90x160 → 画布 270x480 (x3) → 成片 1080x1920 (x4)
"""
import subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
from dex_ep01_bgm import timeline

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
LW, LH = 90, 160          # 逻辑网格
CW, CH = LW * 3, LH * 3   # 画布 270x480
FW, FH = CW * 4, CH * 4   # 成片 1080x1920
FPS = 30

FONTS = Path("C:/Windows/Fonts")
def font(name, size, index=0):
    return ImageFont.truetype(str(FONTS / name), size, index=index)

F_JP_BIG = font("msgothic.ttc", 20)
F_JP_MED = font("msgothic.ttc", 10)
F_JP_SM  = font("msgothic.ttc", 8)
F_CN_SUB = font("simhei.ttf", 11)
F_CN_SM  = font("simhei.ttf", 8)
F_LOGO   = font("YuGothB.ttc", 16)

RED=(200,48,40); DRED=(122,31,24); WHITE=(248,248,240); BLACK=(14,14,18)
BODY=(242,214,160); LN=(58,42,32); EYE=(26,26,26); MUZ=(255,255,255)
BOWL=(217,79,61); BOWLD=(168,58,44); NOOD=(240,200,96); STEAM=(225,238,238)
BLUSH=(240,160,168); NAVY=(16,24,48); GREEN=(90,225,125); ERR=(235,62,48)
SWEAT=(120,180,240); GRAY=(150,150,150)

SUBS = {
    "scan":  ["扫描中……错误：查无此獭"],
    "dex":   ["拉面獭 · 拉面宝可梦", "身高0.3m/体重0.8kg/特性：慢熟"],
    "twist": ["尾巴泡热水3分钟 → Q弹美味", "难过的是，至今没有训练师舍得吃它"],
    "end":   ["图鉴 No.849 · 2026.9.5 记录", "此后，再也没有人见过它"],
}

# ---------------------------------------------------------------- 拉面獭
def draw_otter(d, ox, oy, tick, sweat_drops=False):
    """在逻辑画布上 (ox,oy) 为精灵左上角画一只拉面獭，约26x26格"""
    oy += (tick // 2) % 2  # 待机浮动
    # 尾巴(面条尾, 摆动)
    wag = (tick // 2) % 2
    tail = [(22,10),(23,9),(24,8),(25,8),(25,7+wag),(24,6+wag)]
    for i,(tx,ty) in enumerate(tail):
        c = NOOD if i % 2 else (248,222,130)
        d.point((ox+tx, oy+ty), fill=c)
    # 身体
    d.ellipse((ox+2, oy+4, ox+24, oy+24), fill=BODY, outline=LN)
    # 耳朵
    d.ellipse((ox+4, oy+1, ox+9, oy+6), fill=BODY, outline=LN)
    d.ellipse((ox+17, oy+1, ox+22, oy+6), fill=BODY, outline=LN)
    d.point((ox+6, oy+3), fill=LN); d.point((ox+19, oy+3), fill=LN)
    # 白 muzzle
    d.ellipse((ox+7, oy+10, ox+19, oy+18), fill=MUZ)
    # 眼睛 (每约1秒眨一次)
    blink = (tick % 15) in (0, 1)
    if blink:
        d.rectangle((ox+8, oy+12, ox+10, oy+12), fill=EYE)
        d.rectangle((ox+16, oy+12, ox+18, oy+12), fill=EYE)
    else:
        d.rectangle((ox+8, oy+11, ox+9, oy+13), fill=EYE)
        d.rectangle((ox+17, oy+11, ox+18, oy+13), fill=EYE)
        d.point((ox+8, oy+11), fill=WHITE); d.point((ox+17, oy+11), fill=WHITE)
    # 鼻子和 :3 嘴
    d.rectangle((ox+12, oy+14, ox+13, oy+14), fill=LN)
    d.point((ox+11, oy+16), fill=LN); d.point((ox+15, oy+16), fill=LN)
    d.rectangle((ox+12, oy+17, ox+14, oy+17), fill=LN)
    # 腮红
    d.rectangle((ox+5, oy+15, ox+6, oy+15), fill=BLUSH)
    d.rectangle((ox+19, oy+15, ox+20, oy+15), fill=BLUSH)
    # 碗
    d.rectangle((ox+6, oy+21, ox+20, oy+25), fill=BOWL, outline=BOWLD)
    d.ellipse((ox+5, oy+19, ox+21, oy+23), fill=BOWL, outline=BOWLD)
    for i, nx in enumerate(range(7, 20, 3)):
        d.point((ox+nx, oy+19 - (i % 2)), fill=NOOD)
    d.point((ox+13, oy+19), fill=STEAM)  # 溏心蛋
    # 爪子搭在碗沿
    d.ellipse((ox+2, oy+20, ox+6, oy+24), fill=BODY, outline=LN)
    d.ellipse((ox+20, oy+20, ox+24, oy+24), fill=BODY, outline=LN)
    # 蒸汽 (两缕, 循环上升)
    for sx in (10, 16):
        sy = 18 - ((tick * 1 + sx) % 9)
        d.point((ox+sx + ((tick + sx) // 3) % 2 - 0, oy+sy), fill=STEAM)
        d.point((ox+sx, oy+sy+1), fill=STEAM)
    if sweat_drops:
        dy = 10 + ((tick * 2) % 12)
        d.rectangle((ox+3, oy+dy, ox+3, oy+dy+1), fill=SWEAT)
        d.rectangle((ox+23, oy+dy-4, ox+23, oy+dy-3), fill=SWEAT)

# ---------------------------------------------------------------- 帮助函数
def noise_patch(logical, x0, y0, w, h, rng):
    g = rng.integers(0, 2, size=(h, w), dtype=np.uint8) * 90 + 40
    patch = Image.fromarray(np.stack([g, g, g], axis=-1), "RGB")
    logical.paste(patch, (x0, y0))

def draw_dex_chrome(logical):
    d = ImageDraw.Draw(logical)
    d.rectangle((0, 0, LW-1, LH-1), fill=WHITE, outline=RED, width=2)
    d.rectangle((2, 2, LW-3, LH-3), outline=DRED)
    d.rectangle((2, 2, LW-3, 14), fill=RED, outline=DRED)
    d.rectangle((4, 16, 50, 78), fill=(255,255,255), outline=(40,40,40))

def sub_strip(td, scene_key):
    td.rectangle((0, 402, CW, 474), fill=(10, 10, 12))
    lines = SUBS[scene_key]
    ys = [424, 452] if len(lines) > 1 else [438]
    for ln, y in zip(lines, ys):
        td.text((CW//2, y), ln, font=F_CN_SUB, fill=WHITE,
                anchor="mm", stroke_width=2, stroke_fill=(0,0,0))

def canvas_text(canvas, scene, st, marks, tick):
    td = ImageDraw.Draw(canvas)
    # 顶栏
    td.text((CW//2, 24), "全国図鑑", font=F_JP_MED, fill=WHITE, anchor="mm")
    td.text((CW-14, 24), "EP.01", font=F_JP_SM, fill=(255,220,210), anchor="rm")

    if scene == "scan":
        if st > 1.8 and (st % 0.5) < 0.3:
            td.text((81, 66), "エラー", font=F_JP_MED, fill=ERR, anchor="mm")
            td.text((81, 90), "該当データなし", font=F_JP_SM, fill=ERR, anchor="mm")
    elif scene == "dex":
        td.text((160, 62), "ラーメンオッター", font=F_JP_MED, fill=(30,30,30), anchor="la")
        td.text((160, 84), "たかさ 0.3m", font=F_JP_SM, fill=(60,60,60), anchor="la")
        td.text((160, 102), "おもさ 0.8kg", font=F_JP_SM, fill=(60,60,60), anchor="la")
        td.text((160, 120), "とくせい じゅくれん", font=F_JP_SM, fill=(60,60,60), anchor="la")
        td.text((160, 138), "慢熟：还在泡", font=F_CN_SM, fill=RED, anchor="la")
        td.text((CW//2, 330), "受到攻击后延迟一回合才受伤", font=F_CN_SM,
                fill=(70,70,70), anchor="mm")
        td.text((CW//2, 352), "——因为它还在泡", font=F_CN_SM, fill=(70,70,70), anchor="mm")
    elif scene == "twist":
        if (st % 0.4) < 0.25:
            td.text((CW//2, 60), "!?", font=F_JP_BIG, fill=ERR, anchor="mm")
    elif scene == "end":
        td.text((CW//2, 66), "図鑑 No.849", font=F_JP_BIG, fill=WHITE, anchor="mm")
        td.text((CW//2, 104), "2026.9.5 記録", font=F_JP_SM, fill=GRAY, anchor="mm")
        td.text((CW//2, 138), "その後、誰も見ていない。", font=F_JP_MED,
                fill=(210,210,210), anchor="mm")
        td.rectangle((45, 152, 225, 192), fill=RED, outline=DRED, width=2)
        td.text((CW//2, 172), "不存在図鑑", font=F_LOGO, fill=WHITE, anchor="mm")
        td.text((CW//2, 206), "不存在图鉴 EP.01", font=F_CN_SM, fill=GRAY, anchor="mm")
    if scene in SUBS:
        sub_strip(td, scene)
    return td

# ---------------------------------------------------------------- 场景
def boot_text(canvas, st, tick):
    td = ImageDraw.Draw(canvas)
    title = "全国図鑑"
    nch = max(0, int((st - 0.2) / 0.15))
    shown = title[:nch]
    if shown:
        w = td.textlength(title, font=F_JP_BIG)
        td.text((CW//2 - w/2, 118), shown, font=F_JP_BIG, fill=WHITE)
    if st > 1.0:
        td.text((CW//2, 170), "VER.RG", font=F_JP_SM, fill=GRAY, anchor="mm")
    if st > 1.2 and tick % 30 < 15:
        td.rectangle((131, 200, 139, 208), fill=WHITE)

def scene_scan(st, tick, marks):
    logical = Image.new("RGB", (LW, LH))
    draw_dex_chrome(logical)
    d = ImageDraw.Draw(logical)
    if st < 0.9:
        noise_patch(logical, 5, 17, 44, 60, np.random.default_rng(tick))
    else:
        draw_otter(d, 14, 33, tick)
    # 扫描线
    sy = 17 + ((tick * 4) % 60)
    d.rectangle((5, sy, 49, sy), fill=GREEN)
    return logical

def scene_dex(st, tick, marks):
    logical = Image.new("RGB", (LW, LH))
    draw_dex_chrome(logical)
    draw_otter(ImageDraw.Draw(logical), 14, 33, tick)
    return logical

def scene_twist(st, tick, marks):
    logical = Image.new("RGB", (LW, LH), (24, 16, 30))
    d = ImageDraw.Draw(logical)
    tmp = Image.new("RGB", (30, 30), (24, 16, 30))
    draw_otter(ImageDraw.Draw(tmp), 2, 2, tick, sweat_drops=True)
    z = tmp.resize((60, 60), Image.NEAREST)
    dx = [0, -1, 1, -1][tick % 4]
    dy = [0, 1, -1, 1][tick % 4]
    logical.paste(z, (14 + dx, 26 + dy))
    return logical

def scene_end(st, tick, marks, slen):
    logical = Image.new("RGB", (LW, LH), (8, 8, 10))
    d = ImageDraw.Draw(logical)
    p = min(1.0, st / slen)
    ox = int(4 + p * 86)
    if ox < LW:
        d2 = ImageDraw.Draw(logical)
        draw_otter(d2, ox, 98, tick + 2)
    return logical

# ---------------------------------------------------------------- CRT 后期
def make_vignette():
    y, x = np.mgrid[0:FH, 0:FW].astype(np.float32)
    r = np.sqrt(((x - FW/2) / (FW/2))**2 + ((y - FH*0.55) / (FH/2))**2)
    v = 1.0 - 0.26 * np.clip(r, 0, 1.4) ** 2.2
    return v.astype(np.float32)

def crt(img, vig):
    arr = np.asarray(img, dtype=np.float32)
    arr[::4, :, :] *= 0.82            # 扫描线
    arr *= vig[:, :, None]
    return np.clip(arr, 0, 255).astype(np.uint8)

# ---------------------------------------------------------------- 主流程
def main():
    tl = timeline()
    marks = tl["starts"]
    total = tl["total"]
    slen = {k: tl[k] for k in ["boot", "scan", "dex", "twist", "end"]}
    nframes = int(total * FPS)
    print(f"frames={nframes} total={total:.2f}s")

    vig = make_vignette()
    cmd = ["ffmpeg", "-y", "-v", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{FW}x{FH}",
           "-r", str(FPS), "-i", "-",
           "-i", str(OUT / "dex_ep01_mix.wav"),
           "-c:v", "libx264", "-preset", "medium", "-crf", "18",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
           "-shortest", str(OUT / "dex_ep01_拉面獭.mp4")]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    for f in range(nframes):
        t = f / FPS
        tick = f // 2
        if t < marks["scan"]:
            st, scene = t - marks["boot"], "boot"
            logical = Image.new("RGB", (LW, LH), NAVY)
        elif t < marks["dex"]:
            st, scene = t - marks["scan"], "scan"
            logical = scene_scan(st, tick, marks)
        elif t < marks["twist"]:
            st, scene = t - marks["dex"], "dex"
            logical = scene_dex(st, tick, marks)
        elif t < marks["end"]:
            st, scene = t - marks["twist"], "twist"
            logical = scene_twist(st, tick, marks)
        else:
            st, scene = t - marks["end"], "end"
            logical = scene_end(st, tick, marks, slen["end"])

        canvas = logical.resize((CW, CH), Image.NEAREST)
        if scene == "boot":
            boot_text(canvas, st, tick)
        else:
            canvas_text(canvas, scene, st, marks, tick)
        frame = canvas.resize((FW, FH), Image.NEAREST)
        proc.stdin.write(crt(frame, vig).tobytes())

        if scene != "boot" and f % FPS == int(0.62 * FPS):
            pv = OUT / f"preview_{scene}.jpg"
            Image.fromarray(crt(frame, vig)).save(pv, quality=90)
        if f % 300 == 0:
            print(f"  {f}/{nframes}", flush=True)

    proc.stdin.close()
    proc.wait()
    print("saved", OUT / "dex_ep01_拉面獭.mp4")

if __name__ == "__main__":
    main()
