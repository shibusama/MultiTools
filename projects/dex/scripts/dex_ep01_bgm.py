# -*- coding: utf-8 -*-
"""不存在图鉴 EP01 — 共享时间轴 + 8-bit BGM + 混音 → outputs/dex_ep01_mix.wav"""
import json, subprocess, wave
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
AUDIO = ROOT / "data" / "audio" / "dex_ep01"
SR = 44100

BOOT_LEN = 2.0
PAD = 0.5
TAIL_PAD = 0.9
NARR_LEAD = 0.4


def timeline():
    tl = json.loads((AUDIO / "timeline.json").read_text(encoding="utf-8"))
    d2, d3 = tl["s2_scan"]["duration"], tl["s3_dex"]["duration"]
    d4, d5 = tl["s4_twist"]["duration"], tl["s5_end"]["duration"]
    t = {}
    t["boot"] = BOOT_LEN
    t["scan"] = d2 + PAD
    t["dex"] = d3 + PAD
    t["twist"] = d4 + PAD
    t["end"] = d5 + TAIL_PAD
    t["total"] = sum(t.values())
    marks = {}
    cur = 0.0
    for k in ["boot", "scan", "dex", "twist", "end"]:
        marks[k] = cur
        cur += t[k]
    t["starts"] = marks
    return t


def square(freq, dur, vol=0.15, duty=0.25):
    n = int(SR * dur)
    t = np.arange(n) / SR
    w = np.sign(((t * freq) % 1.0) - (1.0 - duty))
    env = np.minimum(1.0, np.linspace(1.0, 0.0, n) * 6)
    return w * env * vol


def sine(freq, dur, vol=0.15):
    n = int(SR * dur)
    t = np.arange(n) / SR
    env = np.exp(-t * 6)
    return np.sin(2 * np.pi * freq * t) * env * vol


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def place(buf, x, start):
    i = int(start * SR)
    j = min(len(buf), i + len(x))
    if i < len(buf):
        buf[i:j] += x[: j - i]


def make_bgm(total, marks):
    buf = np.zeros(int(SR * total) + SR, dtype=np.float64)
    # 琶音垫: Am F C G, 112bpm 八分音符
    bpm = 112
    eighth = 60.0 / bpm / 2
    chords = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]
    roots = [45, 41, 36, 43]
    pat = [0, 1, 2, 1, 0, 1, 2, 1]
    t = 0.0
    bar = 0
    while t < total:
        ch = chords[bar % 4]
        for k, idx in enumerate(pat):
            place(buf, square(midi(ch[idx]), eighth * 0.9, 0.045), t + k * eighth)
        place(buf, sine(midi(roots[bar % 4]), eighth * 6, 0.055), t)
        t += eighth * 8
        bar += 1
    # 开机音 (boot +0.25)
    for i, m in enumerate([76, 79, 84]):
        place(buf, square(midi(m), 0.09, 0.22), marks["boot"] + 0.25 + i * 0.09)
    # 报错蜂鸣 (scan 中段)
    for i in range(2):
        place(buf, square(110, 0.12, 0.20, duty=0.5), marks["scan"] + 1.8 + i * 0.2)
    # 反转重音 (twist 开始)
    place(buf, sine(80, 0.35, 0.35), marks["twist"] + 0.02)
    place(buf, square(58, 0.10, 0.12), marks["twist"] + 0.02)
    # 结尾温柔琶音
    for i, m in enumerate([72, 76, 79, 84]):
        place(buf, square(midi(m), 0.5, 0.10), marks["end"] + 0.3 + i * 0.14)
    return buf


def load_tts():
    out = {}
    for name in ["s2_scan", "s3_dex", "s4_twist", "s5_end"]:
        wav = AUDIO / f"{name}.wav"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(AUDIO / f"{name}.mp3"),
                        "-ar", str(SR), "-ac", "1", str(wav)], check=True)
        with wave.open(str(wav), "rb") as w:
            out[name] = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16) / 32768.0
    return out


def main():
    tl = timeline()
    marks = tl["starts"]
    total = tl["total"]
    print(f"total {total:.2f}s  starts={ {k: round(v,2) for k,v in marks.items()} }")

    mix = make_bgm(total, marks)
    tts = load_tts()
    for name, seg in [("s2_scan", "scan"), ("s3_dex", "dex"),
                      ("s4_twist", "twist"), ("s5_end", "end")]:
        place(mix, tts[name] * 0.95, marks[seg] + NARR_LEAD)

    peak = np.max(np.abs(mix))
    if peak > 0.98:
        mix *= 0.98 / peak
    out = ROOT / "projects" / "dex" / "renders" / "dex_ep01_mix.wav"
    out.parent.mkdir(exist_ok=True)
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())
    print("saved", out)


if __name__ == "__main__":
    main()
