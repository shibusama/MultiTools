"""Batch transcribe 主义主义 BV list: plain text, no timestamps."""

from __future__ import annotations

import csv
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BV_LIST = ROOT / "主义主义_BV列表.txt"
CSV_PATH = ROOT / "主义主义_视频清单.csv"
AUDIO_ROOT = ROOT / "audio"
OUT_ROOT = ROOT / "transcripts" / "主义主义"
XXL_DIR = ROOT / "tools/archives/Faster-Whisper-XXL_r245.4_windows/Faster-Whisper-XXL"
XXL = XXL_DIR / "faster-whisper-xxl.exe"
MODEL_DIR = ROOT / "models"
TEMP_OUT = ROOT / "outputs" / "_batch_tmp"
PROGRESS = OUT_ROOT / "_progress.log"
SUCCESS = OUT_ROOT / "_success.log"

TIMESTAMP_LINE = re.compile(
    r"^\[\d{1,2}:\d{2}(?::\d{2})?(?:\.\d+)?\s*-->\s*\d{1,2}:\d{2}(?::\d{2})?(?:\.\d+)?\]\s*"
)


def notify_success(bvid: str, index: int, total: int, title: str = "") -> None:
    short = title[:40] + ("…" if len(title) > 40 else "")
    msg = f"{index}/{total} {bvid} {short}".strip()
    line = f"OK {index}/{total} {bvid} {title}"
    with SUCCESS.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
    log(f"[success] {line}")
    ps = (
        "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, "
        "ContentType = WindowsRuntime] | Out-Null; "
        "$template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent("
        "[Windows.UI.Notifications.ToastTemplateType]::ToastText02); "
        "$text = $template.GetElementsByTagName('text'); "
        "$text[0].AppendChild($template.CreateTextNode('转写完成')); "
        f"$text[1].AppendChild($template.CreateTextNode('{msg.replace(chr(39), chr(39)+chr(39))}')); "
        "$toast = [Windows.UI.Notifications.ToastNotification]::new($template); "
        "[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("
        "'videocut').Show($toast)"
    )
    subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps],
        capture_output=True,
    )


def log(msg: str) -> None:
    line = msg.rstrip()
    print(line, flush=True)
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    with PROGRESS.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_titles() -> dict[str, str]:
    titles: dict[str, str] = {}
    if not CSV_PATH.exists():
        return titles
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            titles[row["视频编码(BV号)"]] = row["视频标题"]
    return titles


def load_bvs() -> list[str]:
    return [
        line.strip()
        for line in BV_LIST.read_text(encoding="utf-8").splitlines()
        if line.strip().startswith("BV")
    ]


def strip_timestamps(text: str) -> str:
    lines = []
    for line in text.splitlines():
        cleaned = TIMESTAMP_LINE.sub("", line).strip()
        if cleaned:
            lines.append(cleaned)
    return "\n".join(lines).strip() + "\n"


def download_audio(bvid: str) -> Path:
    out_dir = AUDIO_ROOT / bvid
    wav = out_dir / f"{bvid}.wav"
    if wav.exists() and wav.stat().st_size > 100_000:
        return wav

    out_dir.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
    cmd = [
        "bili",
        "audio",
        bvid,
        "--no-split",
        "-o",
        str(out_dir),
    ]
    log(f"[download] {bvid}")
    subprocess.run(cmd, check=True, env=env)

    m4a_files = list(out_dir.glob("*.m4a"))
    if not m4a_files:
        raise FileNotFoundError(f"No m4a downloaded for {bvid}")
    src = m4a_files[0]
    if src.name != f"{bvid}.m4a":
        target_m4a = out_dir / f"{bvid}.m4a"
        if not target_m4a.exists():
            target_m4a.write_bytes(src.read_bytes())
        src = target_m4a

    ffmpeg = subprocess.run(["where", "ffmpeg"], capture_output=True, text=True, shell=True)
    ffmpeg_bin = ffmpeg.stdout.strip().splitlines()[0] if ffmpeg.stdout.strip() else "ffmpeg"
    subprocess.run(
        [
            ffmpeg_bin,
            "-y",
            "-i",
            str(src),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-c:a",
            "pcm_s16le",
            str(wav),
        ],
        check=True,
    )
    return wav


def transcribe(wav: Path, bvid: str) -> Path:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    TEMP_OUT.mkdir(parents=True, exist_ok=True)
    final_txt = OUT_ROOT / f"{bvid}.txt"
    if final_txt.exists() and final_txt.stat().st_size > 200:
        return final_txt

    cmd = [
        str(XXL),
        str(wav),
        "--model",
        "large-v3",
        "--model_dir",
        str(MODEL_DIR),
        "--language",
        "zh",
        "--output_dir",
        str(TEMP_OUT),
        "--output_format",
        "txt",
        "--without_timestamps",
        "True",
        "--device",
        "cuda",
        "--compute_type",
        "float16",
        "--vad_filter",
        "True",
    ]
    log(f"[transcribe] {bvid}")
    proc = subprocess.run(cmd, cwd=str(XXL_DIR), capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.stdout:
        for line in proc.stdout.splitlines()[-5:]:
            log(f"  {line}")
    if proc.returncode not in (0,):
        # XXL sometimes exits nonzero after successful write
        if not (TEMP_OUT / f"{wav.stem}.txt").exists() and not (TEMP_OUT / "source.txt").exists():
            log(f"[error] {bvid} exit={proc.returncode}")
            if proc.stderr:
                log(proc.stderr[-2000:])

    candidates = [
        TEMP_OUT / f"{wav.stem}.txt",
        TEMP_OUT / "source.txt",
        TEMP_OUT / f"{bvid}.txt",
    ]
    raw = next((p for p in candidates if p.exists()), None)
    if raw is None:
        raise FileNotFoundError(f"No transcript output for {bvid}")

    text = strip_timestamps(raw.read_text(encoding="utf-8", errors="replace"))
    final_txt.write_text(text, encoding="utf-8")

    for p in candidates:
        if p.exists():
            p.unlink(missing_ok=True)
    return final_txt


def main() -> int:
    if not XXL.exists():
        log(f"Missing XXL: {XXL}")
        return 1
    bvs = load_bvs()
    titles = load_titles()
    total = len(bvs)
    log(f"batch start total={total} out={OUT_ROOT}")
    log(f"success log: {SUCCESS}")
    ok = skip = fail = 0
    for i, bvid in enumerate(bvs, 1):
        out_file = OUT_ROOT / f"{bvid}.txt"
        if out_file.exists() and out_file.stat().st_size > 200:
            skip += 1
            continue
        log(f"=== {i}/{total} {bvid} ===")
        try:
            wav = download_audio(bvid)
            transcribe(wav, bvid)
            ok += 1
            notify_success(bvid, i, total, titles.get(bvid, ""))
        except Exception as e:
            fail += 1
            log(f"[fail] {bvid}: {e}")
    log(f"finished ok={ok} skip={skip} fail={fail}")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
