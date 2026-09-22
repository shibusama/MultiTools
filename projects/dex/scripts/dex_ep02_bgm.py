# -*- coding: utf-8 -*-
"""不存在图鉴 EP02 — 时间轴 + 8-bit BGM + 混音"""
import json, subprocess, wave
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
AUDIO = ROOT / "data" / "audio" / "dex_ep02"
SR = 44100
BOOT_LEN, ROLL_LEN = 1.5, 5.0

def timeline():
    tl = json.loads((AUDIO / "timeline.json").read_text(encoding="utf-8"))
    t = {
        "boot": BOOT_LEN,
        "scan": tl["s2_scan"]["duration"] + 0.4,
        "dex": tl["s3_dexA"]["duration"] + tl["s3_dexB"]["duration"] + 0.5,
        "roll": ROLL_LEN,
        "end": tl["s5_end"]["duration"] + 0.9,
    }
    t["dexA"] = tl["s3_dexA"]["duration"]
    t["total"] = sum(t[k] for k in ["boot", "scan", "dex", "roll", "end"])
    marks, cur = {}, 0.0
    for k in ["boot", "scan", "dex", "roll", "end"]:
        marks[k] = cur
        cur += t[k]
    t["starts"] = marks
    return t

def square(freq, dur, vol=0.15, duty=0.25):
    n = int(SR * dur)
    t = np.arange(n) / SR
    w = np.sign(((t * freq) % 1.0) - (1.0 - duty))
    return w * np.minimum(1.0, np.linspace(1.0, 0.0, n) * 6) * vol

def sine(freq, dur, vol=0.15):
    n = int(SR * dur)
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * freq * t) * np.exp(-t * 6) * vol

def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)

def place(buf, x, start):
    i = int(start * SR)
    j = min(len(buf), i + len(x))
    if i < len(buf):
        buf[i:j] += x[: j - i]

def make_bgm(total, marks, dexA_len):
    buf = np.zeros(int(SR * total) + SR, dtype=np.float64)
    bpm = 112
    eighth = 60.0 / bpm / 2
    chords = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]
    roots = [45, 41, 36, 43]
    pat = [0, 1, 2, 1, 0, 1, 2, 1]
    t, bar = 0.0, 0
    while t < total:
        ch = chords[bar % 4]
        for k, idx in enumerate(pat):
            place(buf, square(midi(ch[idx]), eighth * 0.9, 0.045), t + k * eighth)
        place(buf, sine(midi(roots[bar % 4]), eighth * 6, 0.055), t)
        t += eighth * 8
        bar += 1
    for i, m in enumerate([76, 79, 84]):   # 开机音
        place(buf, square(midi(m), 0.09, 0.22), marks["boot"] + 0.2 + i * 0.09)
    for i in range(2):                     # 扫描蜂鸣
        place(buf, square(110, 0.12, 0.20, duty=0.5), marks["scan"] + 2.6 + i * 0.2)
    # 播报员 bug：降调嗡 + 倒带音
    g = marks["dex"] + dexA_len + 0.1
    place(buf, square(70, 0.30, 0.16, duty=0.5), g)
    place(buf, square(90, 0.12, 0.12, duty=0.5), g + 0.42)
    # roll call：八连音阶上行
    for i, m in enumerate([60, 62, 64, 67, 69, 72, 74, 76]):
        place(buf, square(midi(m), 0.16, 0.16), marks["roll"] + 0.2 + i * 0.5)
        place(buf, square(midi(m + 12), 0.08, 0.08), marks["roll"] + 0.2 + i * 0.5 + 0.08)
    place(buf, sine(80, 0.35, 0.35), marks["end"] + 0.02)  # 收尾重音
    return buf

def load_tts():
    out = {}
    for name in ["s2_scan", "s3_dexA", "s3_dexB", "s4_roll", "s5_end"]:
        wav = AUDIO / f"{name}.wav"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(AUDIO / f"{name}.mp3"),
                        "-ar", str(SR), "-ac", "1", str(wav)], check=True)
        with wave.open(str(wav), "rb") as w:
            out[name] = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16) / 32768.0
    return out

def main():
    tl = timeline()
    marks = tl["starts"]
    print(f"total {tl['total']:.2f}s  starts={ {k: round(v,2) for k,v in marks.items()} }")
    mix = make_bgm(tl["total"], marks, tl["dexA"])
    tts = load_tts()
    place(mix, tts["s2_scan"] * 0.95, marks["scan"] + 0.35)
    place(mix, tts["s3_dexA"] * 0.95, marks["dex"] + 0.3)
    place(mix, tts["s3_dexB"] * 0.95, marks["dex"] + tl["dexA"] + 0.15)
    place(mix, tts["s4_roll"] * 0.95, marks["roll"] + 4.2)
    place(mix, tts["s5_end"] * 0.95, marks["end"] + 0.3)
    peak = np.max(np.abs(mix))
    if peak > 0.98:
        mix *= 0.98 / peak
    out = ROOT / "projects" / "dex" / "renders" / "dex_ep02_mix.wav"
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())
    print("saved", out)

if __name__ == "__main__":
    main()
