"""Rule-based disfluency cleanup for spoken-transcript txt files.

Only removes ASR/spoken stutter artifacts:
- Collapses 3+ consecutive repeats of a short token (<=3 chars, e.g. "我……我……我……")
  down to one occurrence. Leaves full-sentence/clause repetition untouched
  (that's the speaker's rhetorical style, not a glitch).
- Normalizes messy ellipsis runs ("…", "……。", "。……") into clean punctuation.
- Collapses doubled punctuation ("。。", "，，").

Does NOT reorder words, rewrite sentences, or touch meaning. Safe to run on
all 340 files; writes cleaned copies to a separate output dir so raw
transcripts are never overwritten.

Usage:
    python scripts/clean_disfluency.py <src_dir> <dst_dir>
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

STUTTER_TOKEN = re.compile(
    r"([\u4e00-\u9fffA-Za-z]{1,3})((?:[。，,、]|……|…)+)(?:\1(?:[。，,、]|……|…)+){2,}"
)


def collapse_stutter(text: str) -> str:
    def repl(m: re.Match[str]) -> str:
        return m.group(1) + m.group(2)

    prev = None
    while prev != text:
        prev = text
        text = STUTTER_TOKEN.sub(repl, text)
    return text


def normalize_ellipsis(text: str) -> str:
    text = re.sub(r"[…]{1,}", "……", text)
    text = re.sub(r"(……){2,}", "……", text)
    text = re.sub(r"……([。！？])", r"\1", text)
    text = re.sub(r"([。！？，、])……", r"\1", text)
    text = re.sub(r"([。，,、]){2,}", r"\1", text)
    return text


def clean(text: str) -> str:
    text = collapse_stutter(text)
    text = normalize_ellipsis(text)
    text = collapse_stutter(text)
    return text


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: clean_disfluency.py <src_dir> <dst_dir>", file=sys.stderr)
        return 1
    src_dir, dst_dir = Path(sys.argv[1]), Path(sys.argv[2])
    dst_dir.mkdir(parents=True, exist_ok=True)

    total_before = total_after = 0
    count = 0
    for p in sorted(src_dir.glob("*.txt")):
        if p.name.startswith("_"):
            continue
        raw = p.read_text(encoding="utf-8", errors="replace")
        cleaned = clean(raw)
        (dst_dir / p.name).write_text(cleaned, encoding="utf-8")
        total_before += len(raw)
        total_after += len(cleaned)
        count += 1

    print(f"cleaned {count} files")
    print(f"chars before: {total_before}  after: {total_after}  removed: {total_before - total_after}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
