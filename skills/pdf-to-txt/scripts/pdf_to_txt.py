# -*- coding: utf-8 -*-
"""PDF → txt. Plain text-layer first; --ocr for RapidOCR at scale 4."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

_REPO = Path(__file__).resolve().parents[3]
_PARSE = _REPO / "解析大全"
_OCR_PY = _PARSE / "扫描件OCR" / "ocr_scanned.py"
sys.path.insert(0, str(_PARSE / "文字层直取"))

from convert_to_txt import pages_to_text  # noqa: E402

CJK = re.compile(r"[\u4e00-\u9fff]")
DIRT = ("由千", "对千", "关千", "间题", "写千", "坰塌")
FIXES = [
    ("进人", "进入"),
    ("陷人", "陷入"),
    ("投人", "投入"),
    ("并人", "并入"),
    ("注人", "注入"),
    ("涌人", "涌入"),
    ("自已", "自己"),
    ("己经", "已经"),
    ("究竞", "究竟"),
    ("千是", "于是"),
    ("由千", "由于"),
    ("对千", "对于"),
    ("关千", "关于"),
    ("间题", "问题"),
    ("写千", "写于"),
    ("坰塌", "坍塌"),
    ("垀塌", "坍塌"),
]


def _cjk_n(s: str) -> int:
    return len(CJK.findall(s))


def plain_pages(path: Path) -> list[list[str]]:
    import pypdf

    reader = pypdf.PdfReader(str(path))
    pages = []
    for page in reader.pages:
        raw = page.extract_text() or ""
        pages.append([ln.rstrip() for ln in raw.split("\n")])
    return pages


def probe(path: Path) -> None:
    import pypdf

    reader = pypdf.PdfReader(str(path))
    n = len(reader.pages)
    meta = reader.metadata
    producer = (meta.producer if meta else None) or ""
    creator = (meta.creator if meta else None) or ""
    title = (meta.title if meta else None) or ""
    print(f"pages {n}")
    print(f"producer {producer!r}")
    print(f"creator {creator!r}")
    print(f"title {title!r}")
    dirt_hits = {k: 0 for k in DIRT}
    body_cjk = []
    for i in range(n):
        if i not in {0, 1, 2, 5, 10, 20, min(50, n - 1), min(80, n - 1), n - 1}:
            continue
        raw = reader.pages[i].extract_text() or ""
        cjk = _cjk_n(raw)
        if i >= 3:
            body_cjk.append(cjk)
        for k in DIRT:
            dirt_hits[k] += raw.count(k)
        print(f"--- page {i + 1} cjk={cjk} chars={len(raw.strip())} ---")
        print(repr(raw[:280]))
    dirty = sum(dirt_hits.values())
    print("dirt", {k: v for k, v in dirt_hits.items() if v})
    scan_hint = any(
        s in f"{producer} {creator} {title}"
        for s in ("CamScanner", "Paper Capture", "扫描")
    )
    weak = bool(body_cjk) and (sorted(body_cjk)[len(body_cjk) // 2] < 80)
    if scan_hint or dirty or weak:
        print("recommend --ocr --scale 4")
    else:
        print("recommend text-layer (no --ocr)")


def apply_fixes(text: str) -> str:
    for a, b in FIXES:
        text = text.replace(a, b)
    return text


def write_txt(pages_lines: list[list[str]], dest: Path) -> None:
    text = apply_fixes(pages_to_text(pages_lines))
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding="utf-8")
    print(f"OK  {dest}  {len(text):,} 字符  {_cjk_n(text):,} 汉字")


def run_ocr(pdf: Path, dest: Path, cache: Path, scale: float) -> int:
    import subprocess

    cache.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        str(_OCR_PY),
        "--pdf",
        str(pdf),
        "--out",
        str(dest),
        "--cache",
        str(cache),
        "--scale",
        str(scale),
    ]
    print(" ".join(cmd), flush=True)
    rc = subprocess.call(cmd)
    if rc == 0 and dest.exists():
        dest.write_text(apply_fixes(dest.read_text(encoding="utf-8")), encoding="utf-8")
    return rc


def main() -> int:
    ap = argparse.ArgumentParser(description="PDF → txt")
    ap.add_argument("pdf", type=Path)
    ap.add_argument("-o", "--out-dir", default=str(_PARSE / "txt"))
    ap.add_argument("--name", default="")
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--ocr", action="store_true")
    ap.add_argument("--scale", type=float, default=4.0)
    ap.add_argument("--cache", type=Path, default=None)
    args = ap.parse_args()
    src = args.pdf
    if not src.exists() or src.suffix.lower() != ".pdf":
        print(f"需要 .pdf 文件：{src}", file=sys.stderr)
        return 1
    if args.probe:
        probe(src)
        return 0
    name = args.name or src.stem
    dest = Path(args.out_dir) / f"{name}.txt"
    if args.ocr:
        cache = args.cache or (_PARSE / ".work" / "ocr_cache" / f"{name}.jsonl")
        return run_ocr(src, dest, cache, args.scale)
    write_txt(plain_pages(src), dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
