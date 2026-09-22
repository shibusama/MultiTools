# -*- coding: utf-8 -*-
"""不存在图鉴 EP02 困困鹿 — 日语 TTS（含播音员 bug 段）"""
import asyncio, json, subprocess, sys
from pathlib import Path
import edge_tts

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "data" / "audio" / "dex_ep02"
OUT.mkdir(parents=True, exist_ok=True)
VOICE = "ja-JP-NanamiNeural"

# (name, text, rate, pitch)
SEGMENTS = [
    ("s2_scan",  "ずかんほうそういん、3ごうです。スキャン、します。", "+12%", "+0Hz"),
    ("s3_dexA",  "ネムイディア。ねむけポケモン。たかさゼロポイントご、おもさじゅうにキロ。ねると、おもくなります。", "+12%", "+0Hz"),
    ("s3_dexB",  "ゆめにでてきたものは……つぎのひ……きえて、います？", "+25%", "-18Hz"),
    ("s4_roll",  "ぜんぶ、とうろくずみです。", "+12%", "+0Hz"),
    ("s5_end",   "つぎは、だれでしょう。", "+8%", "+0Hz"),
]

async def synth(name, text, rate, pitch):
    mp3 = OUT / f"{name}.mp3"
    await edge_tts.Communicate(text, VOICE, rate=rate, pitch=pitch).save(str(mp3))
    d = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(mp3)], capture_output=True, text=True).stdout.strip()
    return float(d)

async def main():
    tl = {}
    for name, text, rate, pitch in SEGMENTS:
        d = await synth(name, text, rate, pitch)
        tl[name] = {"text": text, "duration": d}
        print(f"{name}: {d:.2f}s", flush=True)
    (OUT / "timeline.json").write_text(json.dumps(tl, ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == "__main__":
    asyncio.run(main())
