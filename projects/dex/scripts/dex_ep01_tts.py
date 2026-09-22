# -*- coding: utf-8 -*-
"""不存在图鉴 EP01 日语 TTS 配音生成"""
import asyncio, json, subprocess, sys
from pathlib import Path
import edge_tts

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "data" / "audio" / "dex_ep01"
OUT.mkdir(parents=True, exist_ok=True)

VOICE = "ja-JP-NanamiNeural"

SEGMENTS = {
    "s2_scan": "スキャン中……エラー。該当データなし。",
    "s3_dex": "ラーメンオッター。ラーメンポケモン。たかさゼロポイントさん、おもさゼロポイントはち。とくせいは、じゅくれん。",
    "s4_twist": "しっぽをお湯に三分。ぷるぷるになって、とても、おいしくなります。悲しいことに、食べてくれるトレーナーはいません。",
    "s5_end": "図鑑ナンバー849。本日、記録。その後、誰も見ていません。",
}

async def synth(name, text):
    mp3 = OUT / f"{name}.mp3"
    await edge_tts.Communicate(text, VOICE, rate="+12%").save(str(mp3))
    d = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(mp3)],
        capture_output=True, text=True).stdout.strip()
    return name, text, float(d)

async def main():
    results = {}
    for name, text in SEGMENTS.items():
        n, t, d = await synth(name, text)
        results[n] = {"text": t, "duration": d}
        print(f"{n}: {d:.2f}s", flush=True)
    (OUT / "timeline.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print("total narration:", f"{sum(v['duration'] for v in results.values()):.2f}s")

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
