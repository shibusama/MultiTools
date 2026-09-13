import json
from datetime import timedelta
from pathlib import Path

from faster_whisper import WhisperModel

ROOT = Path(__file__).resolve().parents[1]
BVID = "BV1YZ4y1F7ve"
AUDIO = ROOT / "audio" / BVID / "source.wav"
MODEL_DIR = ROOT / "models" / "large-v3"
OUT_DIR = ROOT / "outputs"


def fmt(ts: float) -> str:
    td = timedelta(seconds=max(0, ts))
    total = int(td.total_seconds())
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    ms = int((ts - int(ts)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def main() -> None:
    import ctranslate2

    cuda = ctranslate2.get_cuda_device_count() > 0
    device = "cuda" if cuda else "cpu"
    compute = "float16" if cuda else "int8"
    print(f"loading {MODEL_DIR} on {device}/{compute}", flush=True)
    model = WhisperModel(str(MODEL_DIR), device=device, compute_type=compute)
    print("model loaded, transcribing...", flush=True)

    segments, info = model.transcribe(
        str(AUDIO),
        language="zh",
        vad_filter=True,
        beam_size=5,
        condition_on_previous_text=True,
    )
    print(f"duration={info.duration:.1f}s language={info.language}", flush=True)

    rows = []
    texts = []
    for seg in segments:
        text = (seg.text or "").strip()
        if not text:
            continue
        item = {"start": seg.start, "end": seg.end, "text": text}
        rows.append(item)
        texts.append(text)
        print(f"[{fmt(seg.start)} --> {fmt(seg.end)}] {text}", flush=True)

    payload = {
        "bvid": BVID,
        "title": "【性的政治学】男权主义必然失败：“只有一种性别存在”——性多元主义与女性主义的联合之路",
        "duration": info.duration,
        "language": info.language,
        "device": device,
        "model": str(MODEL_DIR),
        "segments": rows,
        "text": "\n".join(texts),
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = OUT_DIR / f"{BVID}_whisper.json"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md_lines = [
        "# 【性的政治学】男权主义必然失败：“只有一种性别存在”——性多元主义与女性主义的联合之路",
        "",
        f"- 来源：https://www.bilibili.com/video/{BVID}",
        "- UP：未明子",
        "- 时长：45:33",
        "- 转写：本地 faster-whisper large-v3（GPU）",
        "",
        "## 全文",
        "",
        payload["text"],
        "",
        "## 时间轴",
        "",
    ]
    for item in rows:
        md_lines.append(f"**[{fmt(item['start'])} – {fmt(item['end'])}]** {item['text']}")
        md_lines.append("")

    md_path = OUT_DIR / f"{BVID}_transcript.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"segments={len(rows)} chars={len(payload['text'])}", flush=True)
    print(f"wrote {json_path}", flush=True)
    print(f"wrote {md_path}", flush=True)


if __name__ == "__main__":
    main()
