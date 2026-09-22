"""Finish a batch item from temp XXL output (strip timestamps -> final txt)."""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "projects" / "zhuyizhuyi" / "raw"
TEMP_OUT = ROOT / "outputs" / "_batch_tmp"
PROGRESS = OUT_ROOT / "_progress.log"
SUCCESS = OUT_ROOT / "_success.log"
CSV_PATH = ROOT / "projects" / "zhuyizhuyi" / "index" / "主义主义_视频清单.csv"
BV_LIST = ROOT / "projects" / "zhuyizhuyi" / "index" / "主义主义_BV列表.txt"

TIMESTAMP_LINE = re.compile(
    r"^\[\d{1,2}:\d{2}(?::\d{2})?(?:\.\d+)?\s*-->\s*\d{1,2}:\d{2}(?::\d{2})?(?:\.\d+)?\]\s*"
)


def strip_timestamps(text: str) -> str:
    lines = []
    for line in text.splitlines():
        cleaned = TIMESTAMP_LINE.sub("", line).strip()
        if cleaned:
            lines.append(cleaned)
    return "\n".join(lines).strip() + "\n"


def load_titles() -> dict[str, str]:
    titles: dict[str, str] = {}
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            titles[row["视频编码(BV号)"]] = row["视频标题"]
    return titles


def bv_index(bvid: str) -> tuple[int, int]:
    bvs = [
        line.strip()
        for line in BV_LIST.read_text(encoding="utf-8").splitlines()
        if line.strip().startswith("BV")
    ]
    return bvs.index(bvid) + 1, len(bvs)


def finish(bvid: str) -> Path:
    raw = TEMP_OUT / f"{bvid}.txt"
    if not raw.exists():
        raise FileNotFoundError(f"No temp transcript: {raw}")

    index, total = bv_index(bvid)
    title = load_titles().get(bvid, "")
    final = OUT_ROOT / f"{bvid}.txt"
    text = strip_timestamps(raw.read_text(encoding="utf-8", errors="replace"))
    final.write_text(text, encoding="utf-8")
    raw.unlink(missing_ok=True)

    line = f"OK {index}/{total} {bvid} {title}"
    with SUCCESS.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
    for msg in (
        f"[finish-temp] {bvid} -> {final} ({len(text)} chars)",
        f"[success] {line}",
    ):
        print(msg)
        with PROGRESS.open("a", encoding="utf-8") as f:
            f.write(msg + "\n")
    return final


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: finish_temp_transcript.py BVxxxx", file=sys.stderr)
        return 1
    finish(sys.argv[1])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
