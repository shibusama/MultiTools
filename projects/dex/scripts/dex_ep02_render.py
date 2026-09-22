# -*- coding: utf-8 -*-
"""不存在图鉴 EP02 困困鹿 — Ver.BLU 蓝主题 + roll call + 猜谜彩蛋"""
import subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
from dex_ep01_render import (LW, LH, CW, CH, FW, FH, FPS, draw_otter, noise_patch,
                             make_vignette, crt, F_JP_BIG, F_JP_MED, F_JP_SM,
                             F_CN_SUB, F_CN_SM, WHITE, BLACK, GRAY, GREEN, RED)
from dex_ep02_bgm import timeline

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "projects" / "dex" / "renders"

BLUE=(45,80,200); DBLUE=(24,44,118); NAVY=(10,16,40)
BODY=(224,204,172); LN2=(60,48,38); MUZ=(255,255,255); EYE=(26,26,26)
BLUSH=(250,170,170); ZC=(140,215,255); SIL=(205,205,215)
ACC=(255,150,60); ERR=(235,62,48)

SUBS = {
    "scan":  ["图鉴播音员3号，为您扫描"],
    "dexA":  ["困困鹿 · 瞌睡宝可梦", "身高0.5m/体重12kg/特性：叫不醒"],
    "dexB":  ["它梦到的东西……第二天……", "会消失？！"],
    "roll":  ["收录名单 · 以上全部收录完毕"],
    "end":   ["下期生物是谁？评论区猜猜看"],
}

def draw_z(d, x, y, c):
    d.point((x, y), fill=c); d.point((x+1, y), fill=c); d.point((x+2, y), fill=c)
    d.point((x+1, y+1), fill=c)
    d.point((x, y+2), fill=c); d.point((x+1, y+2), fill=c); d.point((x+2, y+2), fill=c)

def draw_deer(d, ox, oy, tick, eyes_open=False):
    """困困鹿：躺卧+闭眼+Z气泡"""
    # 尾巴
    d.rectangle((ox+1, oy+13+(tick//8)%2, ox+2, oy+14+(tick//8)%2), fill=BODY, outline=LN2)
    # 身体
    d.ellipse((ox+2, oy+10, ox+22, oy+24), fill=BODY, outline=LN2)
    # 蹄子
    d.rectangle((ox+4, oy+22, ox+6, oy+24), fill=LN2)
    d.rectangle((ox+9, oy+23, ox+11, oy+24), fill=LN2)
    # 头（前方抬起）
    d.ellipse((ox+13, oy+4, ox+26, oy+17), fill=BODY, outline=LN2)
    # 耳朵
    d.ellipse((ox+13, oy+2, ox+16, oy+6), fill=BODY, outline=LN2)
    d.ellipse((ox+23, oy+2, ox+26, oy+6), fill=BODY, outline=LN2)
    # 鹿角
    for ax in (16, 23):
        d.point((ox+ax, oy+3), fill=LN2); d.point((ox+ax, oy+2), fill=LN2)
        d.point((ox+ax-1, oy+1), fill=LN2); d.point((ox+ax+1, oy+1), fill=LN2)
    # muzzle
    d.ellipse((ox+16, oy+12, ox+25, oy+17), fill=MUZ)
    d.point((ox+20, oy+13), fill=LN2)
    d.point((ox+18, oy+15), fill=LN2); d.point((ox+19, oy+15), fill=LN2)
    # 腮红
    d.rectangle((ox+14, oy+11, ox+15, oy+11), fill=BLUSH)
    # 眼睛
    if eyes_open:
        d.rectangle((ox+16, oy+8, ox+17, oy+9), fill=WHITE, outline=EYE)
        d.rectangle((ox+21, oy+8, ox+22, oy+9), fill=WHITE, outline=EYE)
    else:
        d.point((ox+16, oy+9), fill=EYE); d.point((ox+17, oy+10), fill=EYE)
        d.point((ox+21, oy+10), fill=EYE); d.point((ox+22, oy+9), fill=EYE)
    # Z 气泡（睡着才冒）
    if not eyes_open:
        for i in range(3):
            zy = (tick + i * 4) % 12
            draw_z(d, ox+26 + (i + tick//6) % 2, oy+6 - zy, ZC)

def draw_blob(d, kind):
    """程序化剪影生物 26x26"""
    if kind == 0:      # 龟
        d.ellipse((3, 10, 23, 24), fill=SIL)
        d.ellipse((19, 5, 26, 12), fill=SIL)
    elif kind == 1:    # 鸟
        d.ellipse((4, 8, 20, 24), fill=SIL)
        d.polygon([(18, 10), (26, 13), (18, 16)], fill=SIL)
    elif kind == 2:    # 长条
        d.ellipse((8, 2, 18, 24), fill=SIL)
    elif kind == 3:    # 虫
        d.ellipse((4, 8, 22, 24), fill=SIL)
        d.line((9, 8, 6, 2), fill=SIL); d.line((17, 8, 20, 2), fill=SIL)
    elif kind == 4:    # 猫
        d.ellipse((3, 6, 23, 24), fill=SIL)
        d.polygon([(5, 8), (8, 1), (11, 7)], fill=SIL)
        d.polygon([(15, 7), (18, 1), (21, 8)], fill=SIL)
    else:              # 王冠团子(彩蛋神秘)
        d.ellipse((4, 9, 22, 24), fill=SIL)
        for cx in (8, 12, 16, 20):
            d.polygon([(cx-1, 10), (cx, 3), (cx+1, 10)], fill=SIL)

def sprite_layer(draw_fn, arg, tick, size=26):
    tmp = Image.new("RGB", (size, size), (0, 0, 0))
    draw_fn(ImageDraw.Draw(tmp), arg, tick) if arg is not None else draw_fn(ImageDraw.Draw(tmp), tick)
    return tmp

def silhouette(img):
    """非背景像素统一变剪影色"""
    a = np.array(img)
    mask = ~np.all(a < 12, axis=-1)
    a[mask] = SIL
    return Image.fromarray(a)

def chrome(canvas):
    td = ImageDraw.Draw(canvas)
    lg = Image.new("RGB", (LW, LH), WHITE)
    d = ImageDraw.Draw(lg)
    d.rectangle((0, 0, LW-1, LH-1), fill=WHITE, outline=BLUE, width=2)
    d.rectangle((2, 2, LW-3, LH-3), outline=DBLUE)
    d.rectangle((2, 2, LW-3, 14), fill=BLUE, outline=DBLUE)
    d.rectangle((4, 16, 50, 78), fill=(255, 255, 255), outline=(40, 40, 40))
    return lg

def canvas_chrome(canvas):
    td = ImageDraw.Draw(canvas)
    td.text((CW//2 - 20, 24), "全国図鑑", font=F_JP_MED, fill=WHITE, anchor="mm")
    td.text((CW//2 + 52, 24), "VER.BLU", font=F_JP_SM, fill=(200,215,255), anchor="mm")
    td.text((CW-14, 24), "EP.02", font=F_JP_SM, fill=(200,215,255), anchor="rm")

def boot_text(canvas, st, tick):
    td = ImageDraw.Draw(canvas)
    nch = max(0, int((st - 0.15) / 0.12))
    shown = "全国図鑑"[:nch]
    if shown:
        w = td.textlength("全国図鑑", font=F_JP_BIG)
        td.text((CW//2 - w/2, 108), shown, font=F_JP_BIG, fill=WHITE)
    if st > 0.7:
        td.text((CW//2, 152), "VER.BLU", font=F_JP_MED, fill=(150,175,255), anchor="mm")
    if st > 1.0:
        td.text((CW//2, 180), "収録数：850", font=F_JP_SM, fill=GRAY, anchor="mm")

def roll_entry(canvas, i, tick, t0):
    """roll call 第 i 个条目"""
    td = ImageDraw.Draw(canvas)
    names = [("No.849 RAMENOTTER", (120,235,255), "color"),
             ("No.850 SLEEPDEER", (255,220,120), "color"),
             ("No.851 JUNKFOODON", (255,120,200), 0),
             ("No.852 KOTATSUGAME", (140,255,160), 0),
             ("No.853 FLOFLOSSI", (255,160,120), 1),
             ("No.854 DANCHIDORI", (200,160,255), 2),
             ("No.855 MIZUMUSHI", (120,200,255), 3),
             ("No.8?? ??", (255,255,255), 99)]
    label, color, kind = names[i]
    tmp = Image.new("RGB", (26, 26), (0, 0, 0))
    if kind == "color":
        if i == 0:
            draw_otter(ImageDraw.Draw(tmp), 0, 0, tick + 4)
        else:
            draw_deer(ImageDraw.Draw(tmp), 0, 0, tick, eyes_open=False)
    else:
        draw_blob(ImageDraw.Draw(tmp), kind)
        if kind != 99:
            tmp = silhouette(tmp)
    big = tmp.resize((52, 52), Image.NEAREST)
    lg = Image.new("RGB", (LW, LH), NAVY)
    lg.paste(big, (19, 16))
    cv = lg.resize((CW, CH), Image.NEAREST)
    td2 = ImageDraw.Draw(cv)
    td2.text((CW//2, 250), label, font=F_JP_MED, fill=color, anchor="mm",
             stroke_width=1, stroke_fill=(0,0,0))
    if i < 7:
        td2.text((CW//2, 280), "とうろくずみ / 已收录", font=F_CN_SM, fill=GRAY, anchor="mm")
    else:
        if (tick % 20) < 12:
            td2.text((CW//2, 280), "?! 未收录个体", font=F_CN_SM, fill=ERR, anchor="mm")
    canvas.paste(cv, (0, 0))

def main():
    tl = timeline()
    marks = tl["starts"]
    total = tl["total"]
    nframes = int(total * FPS)
    print(f"frames={nframes} total={total:.2f}s")
    vig = make_vignette()
    glitch_t = marks["dex"] + tl["dexA"] + 0.15

    cmd = ["ffmpeg", "-y", "-v", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{FW}x{FH}",
           "-r", str(FPS), "-i", "-",
           "-i", str(OUT / "dex_ep02_mix.wav"),
           "-c:v", "libx264", "-preset", "medium", "-crf", "18",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
           "-shortest", str(OUT / "dex_ep02_困困鹿.mp4")]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    for f in range(nframes):
        t = f / FPS
        tick = f // 2
        # ---------- 逻辑层 ----------
        if t < marks["scan"]:
            st, scene = t - marks["boot"], "boot"
            logical = Image.new("RGB", (LW, LH), NAVY)
        elif t < marks["dex"]:
            st, scene = t - marks["scan"], "scan"
            logical = chrome(Image.new("RGB", (LW, LH)))
            d = ImageDraw.Draw(logical)
            if st < 0.8:
                noise_patch(logical, 5, 17, 44, 60, np.random.default_rng(tick))
            else:
                draw_deer(d, 13, 34, tick)
            sy = 17 + ((tick * 4) % 60)
            d.rectangle((5, sy, 49, sy), fill=GREEN)
            if st > 2.2 and (st % 0.5) < 0.3:
                new_tag = True
            else:
                new_tag = False
        elif t < marks["roll"]:
            st, scene = t - marks["dex"], "dex"
            g_on = t >= glitch_t
            shake = g_on and (t - glitch_t) % 0.4 < 0.25
            dx, dy = ((tick*3) % 3 - 1, (tick*5) % 3 - 1) if shake else (0, 0)
            logical = chrome(Image.new("RGB", (LW, LH)))
            draw_deer(ImageDraw.Draw(logical), 13 + dx, 34 + dy, tick,
                      eyes_open=shake)
        elif t < marks["end"]:
            st, scene = t - marks["roll"], "roll"
            logical = Image.new("RGB", (LW, LH), NAVY)
        else:
            st, scene = t - marks["end"], "end"
            logical = Image.new("RGB", (LW, LH), (6, 8, 12))

        canvas = logical.resize((CW, CH), Image.NEAREST)
        td = ImageDraw.Draw(canvas)
        # ---------- 画布文字层 ----------
        if scene == "boot":
            boot_text(canvas, st, tick)
        elif scene == "scan":
            canvas_chrome(canvas)
            if st > 2.2 and (st % 0.5) < 0.3:
                td.rectangle((100, 52, 144, 70), fill=ERR)
                td.text((122, 61), "NEW!", font=F_JP_SM, fill=WHITE, anchor="mm")
            sub = SUBS["scan"]
            _strip(td, sub, 1)
        elif scene == "dex":
            canvas_chrome(canvas)
            td.text((160, 62), "ネムイディア", font=F_JP_MED, fill=(30,30,30), anchor="la")
            td.text((160, 84), "たかさ 0.5m", font=F_JP_SM, fill=(60,60,60), anchor="la")
            td.text((160, 102), "おもさ 12kg", font=F_JP_SM, fill=(60,60,60), anchor="la")
            td.text((160, 120), "とくせい めざまし", font=F_JP_SM, fill=(60,60,60), anchor="la")
            td.text((160, 138), "特性「叫不醒」", font=F_CN_SM, fill=ACC, anchor="la")
            g_on = t >= glitch_t
            if not g_on:
                td.text((CW//2, 330), "它把梦吃掉当作食物", font=F_CN_SM, fill=(70,70,70), anchor="mm")
                td.text((CW//2, 352), "所以醒来的时候总是很饿", font=F_CN_SM, fill=(70,70,70), anchor="mm")
            elif (t - glitch_t) % 0.4 < 0.25:
                td.text((CW//2, 330), "它梦到的东西，第二天会消失", font=F_CN_SM, fill=ERR,
                        anchor="mm", stroke_width=1, stroke_fill=(0,0,0))
            sub = SUBS["dexB"] if t >= glitch_t else SUBS["dexA"]
            _strip(td, sub, 2 if t < glitch_t else 1)
        elif scene == "roll":
            idx = min(7, int((st - 0.2) / 0.55))
            if st >= 0.2:
                roll_entry(canvas, idx, tick, st)
            _strip(td, SUBS["roll"], 1)
        elif scene == "end":
            td.text((CW//2, 70), "図鑑 VER.BLU", font=F_JP_MED, fill=(150,175,255), anchor="mm")
            td.text((CW//2, 104), "収録数：850", font=F_JP_BIG, fill=WHITE, anchor="mm")
            if (tick % 30) < 20:
                td.text((CW//2, 170), "つぎは、だれでしょう。", font=F_JP_MED, fill=GRAY, anchor="mm")
            _strip(td, SUBS["end"], 1)

        frame = canvas.resize((FW, FH), Image.NEAREST)
        proc.stdin.write(crt(frame, vig).tobytes())
        if scene != "boot" and f % FPS == int(0.62 * FPS):
            Image.fromarray(crt(frame, vig)).save(
                OUT / f"preview02_{scene}.jpg", quality=90)
        if f % 300 == 0:
            print(f"  {f}/{nframes}", flush=True)

    proc.stdin.close()
    proc.wait()
    print("saved", OUT / "dex_ep02_困困鹿.mp4")

def _strip(td, lines, maxlines):
    td.rectangle((0, 402, CW, 474), fill=(10, 10, 12))
    ys = [424, 452] if len(lines) > 1 else [438]
    for ln, y in zip(lines[:maxlines], ys[:maxlines]):
        td.text((CW//2, y), ln, font=F_CN_SUB, fill=WHITE,
                anchor="mm", stroke_width=2, stroke_fill=(0,0,0))

if __name__ == "__main__":
    main()
