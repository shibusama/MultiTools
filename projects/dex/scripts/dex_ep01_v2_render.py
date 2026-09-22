# -*- coding: utf-8 -*-
"""不存在图鉴 EP.01 v2 重制版 — 逐像素精灵 + 分层背景 + 粒子 + 运镜
音频复用 EP.01（dex_ep01_mix.wav），纯视觉对比升级
"""
import subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
from dex_ep01_render import (LW, LH, CW, CH, FW, FH, FPS, F_JP_BIG, F_JP_MED,
                             F_JP_SM, F_CN_SUB, F_CN_SM, make_vignette, crt)
from dex_ep01_bgm import timeline
from sprite_v2 import draw_otter_v2

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "projects" / "dex" / "renders"

RED = (200, 48, 40); DRED = (122, 31, 24); WHITE = (250, 248, 240)
BLACK = (14, 14, 18); GRAY = (150, 150, 150); GREEN = (90, 225, 125)
ERR = (235, 62, 48); ACC = (255, 150, 60)

SUBS = {
    "scan":  ["扫描中……错误：查无此獭"],
    "dex":   ["拉面獭 · 拉面宝可梦", "身高0.3m/体重0.8kg/特性：慢熟"],
    "twist": ["尾巴泡热水3分钟 → Q弹美味", "难过的是，至今没有训练师舍得吃它"],
    "end":   ["图鉴 No.849 · 2026.9.5 记录", "此后，再也没有人见过它"],
}

RNG = np.random.default_rng(42)
STARS = [(int(x), int(y)) for x, y in RNG.uniform((0, 0), (CW, 300), (60, 2)).astype(int)]
STARS = [(x % CW, int(y) % 300) for x, y in STARS]
GRASSPX = [(int(x), int(h)) for x, h in RNG.uniform((0, 0), (LW, 8), (90, 2))]

def vgrad(w, h, top, bot):
    t = np.linspace(0, 1, h)[:, None, None]
    arr = (np.array(top) * (1 - t) + np.array(bot) * t)
    arr = np.repeat(arr, w, axis=1).astype(np.uint8)
    return Image.fromarray(arr, "RGB")

def rgrad(w, h, inner, outer, cx=0.5, cy=0.42):
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.sqrt(((x - w * cx) / (w * 0.55)) ** 2 + ((y - h * cy) / (h * 0.55)) ** 2)
    r = np.clip(r, 0, 1)[:, :, None]
    arr = (np.array(inner) * (1 - r) + np.array(outer) * r).astype(np.uint8)
    return Image.fromarray(arr, "RGB")

def stars(td, tick, n=60, y_max=300):
    for i, (x, y) in enumerate(STARS[:n]):
        if (tick + i * 7) % 40 < 28:
            c = (230, 232, 255) if (i + tick) % 3 else (160, 170, 230)
            td.point((x, y % y_max), fill=c)

def mountains(d, y0, h, color):
    d.polygon([(0, y0 + 8), (18, y0), (40, y0 + h), (0, y0 + h)], fill=color)
    d.polygon([(25, y0 + 14), (52, y0 + 2), (86, y0 + h + 6), (25, y0 + h + 6)], fill=color)
    d.polygon([(60, y0 + 6), (80, y0 - 4), (104, y0 + h), (60, y0 + h)], fill=color)

def cloud(d, x, y, s=1):
    for dx, dy, r in [(0, 0, 5), (6, -2, 6), (12, 0, 5), (6, 3, 5)]:
        d.ellipse((x + dx * s - r, y + dy * s - r, x + dx * s + r, y + dy * s + r), fill=(250, 250, 252))

def grass(d, y0, seed_shift=0):
    d.rectangle((0, y0, LW - 1, LH - 1), fill=(96, 168, 88))
    d.rectangle((0, y0, LW - 1, y0 + 2), fill=(120, 196, 104))
    for i, (x, h) in enumerate(GRASSPX):
        d.point((x, y0 + 3 + (h % 8)), fill=(72, 140, 70) if (x + i) % 3 else (140, 210, 120))

def speed_lines(canvas, tick):
    ov = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    cx, cy = CW // 2, 190
    for i in range(28):
        ang = i * np.pi / 14 + (tick % 4) * 0.02
        r0 = 70 + (i * 37) % 60
        r1 = r0 + 60 + (i * 23) % 50
        x0, y0 = cx + np.cos(ang) * r0, cy + np.sin(ang) * r0 * 1.4
        x1, y1 = cx + np.cos(ang) * r1, cy + np.sin(ang) * r1 * 1.4
        d.line((x0, y0, x1, y1), fill=(255, 90, 70, 60), width=2)
    canvas.paste(Image.alpha_composite(canvas.convert("RGBA"), ov).convert("RGB"), (0, 0))

def chrome_v2(logical):
    d = ImageDraw.Draw(logical)
    d.rectangle((0, 0, LW - 1, LH - 1), fill=WHITE, outline=RED, width=2)
    d.rectangle((2, 2, LW - 3, LH - 3), outline=DRED)
    d.rectangle((2, 2, LW - 3, 14), fill=RED, outline=DRED)
    for sx in (1, LW - 3):
        for sy in (1, LH - 3):
            d.point((sx, sy), fill=(230, 200, 180)); d.point((sx + (1 if sx == 1 else -1), sy), fill=DRED)
    d.rectangle((4, 16, 50, 78), outline=(40, 40, 40))
    return logical

def window_scene(logical, tick, scene):
    """展示窗内分层小场景"""
    win = Image.new("RGB", (45, 61))
    if scene == "scan":
        win.paste(vgrad(45, 61, (120, 170, 235), (200, 224, 245)))
        d = ImageDraw.Draw(win)
        mountains(d, 34, 20, (110, 150, 120))
    elif scene == "dex":
        win.paste(vgrad(45, 61, (110, 175, 240), (205, 230, 248)))
        d = ImageDraw.Draw(win)
        d.ellipse((34, 4, 40, 10), fill=(255, 236, 150))  # 太阳
        cloud(d, (2 + tick * 0.15) % 55 - 8, 8)
        cloud(d, (28 - tick * 0.1) % 55 - 8, 15, s=1)
        mountains(d, 32, 22, (120, 160, 130))
        mountains(d, 38, 18, (96, 140, 104))
        grass(d, 48)
    d = ImageDraw.Draw(win)
    return win

def draw_window(logical, tick, scene):
    win = window_scene(logical, tick, scene)
    logical.paste(win, (5, 17))
    d = ImageDraw.Draw(logical)
    d.rectangle((4, 16, 50, 78), outline=(40, 40, 40))
    if scene == "scan":
        if st_scan < 0.9:
            noise_patch2(logical, 5, 17, 45, 61, np.random.default_rng(tick))
        else:
            spr = draw_otter_v2(tick, blink=(tick % 15) in (0, 1))
            logical.paste(spr, (11, 32), spr)
    elif scene == "dex":
        spr = draw_otter_v2(tick, blink=(tick % 15) in (0, 1))
        logical.paste(spr, (11, 32), spr)
    if scene == "scan":
        sy = 17 + ((tick * 4) % 60)
        d.rectangle((5, sy, 49, sy), fill=(120, 255, 150))

def noise_patch2(logical, x0, y0, w, h, rng):
    g = rng.integers(0, 2, size=(h, w), dtype=np.uint8) * 90 + 40
    patch = Image.fromarray(np.stack([g, g, g], axis=-1), "RGB")
    logical.paste(patch, (x0, y0))

def canvas_text_v2(canvas, scene, st, tick):
    td = ImageDraw.Draw(canvas)
    td.text((CW // 2, 24), "全国図鑑", font=F_JP_MED, fill=WHITE, anchor="mm")
    td.text((CW - 40, 24), "▮▮▯", font=F_JP_SM, fill=(255, 220, 210), anchor="rm")
    td.text((CW - 14, 24), "EP.01", font=F_JP_SM, fill=(255, 220, 210), anchor="rm")
    td.text((160, 62), "ラーメンオッター", font=F_JP_MED, fill=(30, 30, 30), anchor="la")
    td.text((160, 84), "たかさ 0.3m", font=F_JP_SM, fill=(60, 60, 60), anchor="la")
    td.text((160, 102), "おもさ 0.8kg", font=F_JP_SM, fill=(60, 60, 60), anchor="la")
    td.text((160, 120), "とくせい じゅくれん", font=F_JP_SM, fill=(60, 60, 60), anchor="la")
    td.text((160, 138), "慢熟：还在泡", font=F_CN_SM, fill=ACC, anchor="la")

def strip(td, lines):
    td.rectangle((0, 402, CW, 474), fill=(10, 10, 12))
    ys = [424, 452] if len(lines) > 1 else [438]
    for ln, y in zip(lines, ys):
        td.text((CW // 2, y), ln, font=F_CN_SUB, fill=WHITE, anchor="mm",
                stroke_width=2, stroke_fill=(0, 0, 0))

def main():
    tl = timeline()
    marks = tl["starts"]
    total = tl["total"]
    nframes = int(total * FPS)
    print(f"frames={nframes} total={total:.2f}s")
    vig = make_vignette()
    global st_scan
    boot_bg = rgrad(CW, CH, (30, 34, 80), (12, 12, 30), cy=0.3)
    twist_bg = rgrad(CW, CH, (150, 24, 28), (40, 8, 12))
    end_bg = vgrad(CW, 300, (16, 18, 50), (40, 30, 70))

    cmd = ["ffmpeg", "-y", "-v", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{FW}x{FH}", "-r", str(FPS), "-i", "-",
           "-i", str(OUT / "dex_ep01_mix.wav"),
           "-c:v", "libx264", "-preset", "medium", "-crf", "18",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest",
           str(OUT / "dex_ep01_拉面獭_v2.mp4")]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    for f in range(nframes):
        t = f / FPS
        tick = f // 2
        if t < marks["scan"]:
            st, scene = t - marks["boot"], "boot"
            canvas = boot_bg.copy()
            td = ImageDraw.Draw(canvas)
            stars(td, tick, y_max=180)
            td.rectangle((0, 150, CW, 240), fill=(40, 46, 100))
            td.rectangle((0, 150, CW, 152), fill=(70, 80, 150))
            nch = max(0, int((st - 0.2) / 0.15))
            shown = "全国図鑑"[:nch]
            if shown:
                w = td.textlength("全国図鑑", font=F_JP_BIG)
                td.text((CW // 2 - w / 2, 170), shown, font=F_JP_BIG, fill=WHITE)
            if st > 1.0:
                td.text((CW // 2, 240), "VER.RG", font=F_JP_MED, fill=(150, 160, 220), anchor="mm")
            if st > 1.2 and tick % 30 < 15:
                td.rectangle((131, 280, 139, 288), fill=WHITE)
            logical = None
        elif t < marks["dex"]:
            st_scan = t - marks["scan"]
            scene = "scan"
            logical = chrome_v2(Image.new("RGB", (LW, LH)))
            draw_window(logical, tick, "scan")
            canvas = logical.resize((CW, CH), Image.NEAREST)
            td = ImageDraw.Draw(canvas)
            td.text((CW // 2, 24), "全国図鑑", font=F_JP_MED, fill=WHITE, anchor="mm")
            td.text((CW - 14, 24), "EP.01", font=F_JP_SM, fill=(255, 220, 210), anchor="rm")
            if st_scan > 1.8 and (st_scan % 0.5) < 0.3:
                td.text((81, 66), "エラー", font=F_JP_MED, fill=ERR, anchor="mm")
                td.text((81, 90), "該当データなし", font=F_JP_SM, fill=ERR, anchor="mm")
            strip(td, SUBS["scan"])
        elif t < marks["twist"]:
            st, scene = t - marks["dex"], "dex"
            logical = chrome_v2(Image.new("RGB", (LW, LH)))
            draw_window(logical, tick, "dex")
            canvas = logical.resize((CW, CH), Image.NEAREST)
            z = 1.0 + min(0.05, st * 0.006)
            canvas = canvas.crop((int(CW * (1 - 1 / z) / 2), int(CH * (1 - 1 / z) / 2),
                                  int(CW * (1 + 1 / z) / 2), int(CH * (1 + 1 / z) / 2))
                                 ).resize((CW, CH), Image.NEAREST)
            td = ImageDraw.Draw(canvas)
            td.text((CW // 2, 24), "全国図鑑", font=F_JP_MED, fill=WHITE, anchor="mm")
            td.text((CW - 14, 24), "EP.01", font=F_JP_SM, fill=(255, 220, 210), anchor="rm")
            canvas_text_v2(canvas, scene, st, tick)
            td.text((CW // 2, 255), "受到攻击后延迟一回合才受伤", font=F_CN_SM, fill=(70, 70, 70), anchor="mm")
            td.text((CW // 2, 277), "——因为它还在泡", font=F_CN_SM, fill=(70, 70, 70), anchor="mm")
            strip(td, SUBS["dex"])
        elif t < marks["end"]:
            st, scene = t - marks["twist"], "twist"
            canvas = twist_bg.copy()
            td = ImageDraw.Draw(canvas)
            speed_lines(canvas, tick)
            spr = draw_otter_v2(tick, blink=(tick % 12) in (0, 1),
                                wag=[0, 1][(tick // 2) % 2])
            big = spr.resize((64, 60), Image.NEAREST)
            dx = [0, -2, 2, -2][tick % 4]; dy = [0, 2, -2, 2][tick % 4]
            canvas.paste(big, (103 + dx, 120 + dy), big)
            for i, sx in enumerate((105, 160)):
                dy2 = 130 + ((tick * 3 + i * 5) % 40)
                td.ellipse((sx, dy2, sx + 5, dy2 + 7), fill=(150, 200, 250))
                td.point((sx + 1, dy2 + 1), fill=(230, 245, 255))
            if (st % 0.4) < 0.25:
                td.text((CW // 2, 60), "!?", font=F_JP_BIG, fill=ERR, anchor="mm",
                        stroke_width=2, stroke_fill=(0, 0, 0))
            strip(td, SUBS["twist"])
        else:
            st, scene = t - marks["end"], "end"
            slen = tl["end"]
            canvas = Image.new("RGB", (CW, CH), (8, 8, 10))
            canvas.paste(end_bg, (0, 0))
            td = ImageDraw.Draw(canvas)
            stars(td, tick, y_max=200)
            td.ellipse((200, 60, 236, 96), fill=(240, 238, 210))
            td.ellipse((206, 66, 216, 76), fill=(210, 208, 180))
            td.polygon([(0, 300), (40, 250), (90, 300)], fill=(24, 26, 48))
            td.polygon([(60, 300), (130, 240), (210, 300)], fill=(20, 22, 42))
            td.polygon([(170, 300), (230, 255), (270, 300)], fill=(26, 28, 52))
            td.rectangle((0, 292, CW, CH), fill=(18, 22, 20))
            p = min(1.0, st / slen)
            ox = int(6 + p * 100)
            spr = draw_otter_v2(tick, blink=(tick % 14) in (0, 1), wag=(tick // 2) % 2)
            spr48 = spr.resize((48, 45), Image.NEAREST)
            canvas.paste(spr48, (ox, 258), spr48)
            td = ImageDraw.Draw(canvas)
            td.text((CW // 2, 66), "図鑑 No.849", font=F_JP_BIG, fill=WHITE, anchor="mm")
            td.text((CW // 2, 104), "2026.9.5 記録", font=F_JP_SM, fill=GRAY, anchor="mm")
            td.text((CW // 2, 138), "その後、誰も見ていない。", font=F_JP_MED,
                    fill=(210, 210, 210), anchor="mm")
            td.rectangle((45, 152, 225, 192), fill=RED, outline=DRED, width=2)
            td.text((CW // 2, 172), "不存在図鑑", font=F_LOGO if False else F_JP_BIG,
                    fill=WHITE, anchor="mm")
            td.text((CW // 2, 206), "不存在图鉴 EP.01", font=F_CN_SM, fill=GRAY, anchor="mm")
            strip(td, SUBS["end"])

        frame = canvas.resize((FW, FH), Image.NEAREST)
        proc.stdin.write(crt(frame, vig).tobytes())
        if scene != "boot" and f % FPS == int(0.62 * FPS):
            Image.fromarray(crt(frame, vig)).save(OUT / f"previewV2_{scene}.jpg", quality=90)
        if f % 300 == 0:
            print(f"  {f}/{nframes}", flush=True)

    proc.stdin.close()
    proc.wait()
    print("saved", OUT / "dex_ep01_拉面獭_v2.mp4")

if __name__ == "__main__":
    main()
