# -*- coding: utf-8 -*-
"""对纯扫描 PDF 做 OCR，产出与 convert_to_txt.pages_to_text 兼容的“每页文字行”。

用法:
    python ocr_scanned.py --pdf book.pdf --pages 3
    python ocr_scanned.py --pdf book.pdf --out txt/书名.txt
    python ocr_scanned.py --pdf book.pdf --assemble-only
"""
import argparse
import json
import statistics
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
WS = _HERE.parent
sys.path.insert(0, str(WS / "文字层直取"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np
import pypdfium2 as pdfium
from rapidocr_onnxruntime import RapidOCR

from convert_to_txt import pages_to_text

SCALE = 3.0  # 渲染倍率（3.0 ≈ 216 DPI）

_ocr = None


def get_ocr() -> RapidOCR:
    global _ocr
    if _ocr is None:
        _ocr = RapidOCR()
    return _ocr


def boxes_to_lines(items) -> list:
    """把 OCR 的文本框按坐标合并成“行”，并还原缩进与段间空行。"""
    boxes = []
    for box, text, score in items:
        if not text or not text.strip():
            continue
        xs = [float(p[0]) for p in box]
        ys = [float(p[1]) for p in box]
        boxes.append(
            {"x0": min(xs), "x1": max(xs), "cy": sum(ys) / 4, "h": max(ys) - min(ys), "t": text.strip()}
        )
    if not boxes:
        return []

    boxes.sort(key=lambda b: (b["cy"], b["x0"]))
    med_h = statistics.median(b["h"] for b in boxes) or 20.0
    rows, cur = [], [boxes[0]]
    for b in boxes[1:]:
        if abs(b["cy"] - cur[-1]["cy"]) <= med_h * 0.6:
            cur.append(b)
        else:
            rows.append(cur)
            cur = [b]
    rows.append(cur)

    left = min(min(b["x0"] for b in r) for r in rows)
    # 每个字符的像素宽度：用“文本框宽度 / 字数”估计，才能把缩进换算成字符数
    cws = [(b["x1"] - b["x0"]) / len(b["t"]) for b in boxes if len(b["t"]) >= 4]
    char_w = statistics.median(cws) if cws else 27.0

    lines, centers = [], []
    for r in rows:
        r.sort(key=lambda b: b["x0"])
        txt = ""
        for b in r:
            if txt and _needs_space(txt[-1], b["t"][0]):
                txt += " "
            txt += b["t"]
        indent = max(0, min(8, int(round((min(b["x0"] for b in r) - left) / char_w))))
        lines.append(" " * indent + txt)
        centers.append(sum(b["cy"] for b in r) / len(r))

    # 行距明显变大 => 段间空行
    if len(centers) >= 3:
        gaps = [centers[i + 1] - centers[i] for i in range(len(centers) - 1)]
        base = statistics.median(gaps)
        out = []
        for i, ln in enumerate(lines):
            if i and gaps[i - 1] > base * 1.7:
                out.append("")
            out.append(ln)
        return out
    return lines


def _needs_space(a: str, b: str) -> bool:
    return a.isascii() and a.isalnum() and b.isascii() and b.isalnum()


def load_cache(cache_path: Path) -> dict:
    done = {}
    if cache_path.exists():
        with cache_path.open(encoding="utf-8") as f:
            for line in f:
                try:
                    rec = json.loads(line)
                    done[rec["pno"]] = rec["lines"]
                except Exception:
                    continue
    return done


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", type=Path, required=True, help="扫描件 PDF")
    ap.add_argument("--out", type=Path, default=WS / "txt" / "ocr_output.txt")
    ap.add_argument("--cache", type=Path, default=WS / ".work" / "ocr_cache" / "pages.jsonl")
    ap.add_argument("--pages", type=int, default=0, help="只跑前 N 页（试跑）")
    ap.add_argument("--assemble-only", action="store_true")
    ap.add_argument("--assemble-limit", type=int, default=0, help="拼装时只取前 N 页（调试用）")
    ap.add_argument("--no-write", action="store_true", help="拼装后只打印样本，不写 txt")
    args = ap.parse_args()

    pdf_path = args.pdf
    cache_path = args.cache
    out_txt = args.out
    if not pdf_path.exists():
        print(f"找不到 PDF：{pdf_path}", file=sys.stderr)
        return 1

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    doc = pdfium.PdfDocument(str(pdf_path))
    total = len(doc)
    done = load_cache(cache_path)
    if done:
        print(f"缓存已有 {len(done)} 页，继续续跑")

    if not args.assemble_only:
        ocr = get_ocr()
        limit = min(total, args.pages) if args.pages else total
        t0 = time.time()
        with cache_path.open("a", encoding="utf-8") as fh:
            for i in range(limit):
                if i in done:
                    continue
                page = doc[i]
                img = page.render(scale=SCALE).to_pil().convert("RGB")
                arr = np.asarray(img)[:, :, ::-1]  # RapidOCR 走 BGR
                res, _ = ocr(arr)
                lines = boxes_to_lines(res or [])
                done[i] = lines
                fh.write(json.dumps({"pno": i, "lines": lines}, ensure_ascii=False) + "\n")
                fh.flush()
                if (i + 1) % 10 == 0 or i + 1 == limit:
                    el = time.time() - t0
                    sp = el / max(1, len(done))
                    print(
                        f"  {i+1}/{limit} 页 | 已用 {el/60:.1f} 分钟 | 约 {sp:.2f} 秒/页 | "
                        f"预计剩余 {(limit-len(done))*sp/60:.0f} 分钟",
                        flush=True,
                    )

    if args.pages and not args.assemble_only:
        sample = done.get(min(args.pages, total) - 1, [])
        print("\n--- 最后一页识别样本 ---")
        for ln in sample[:25]:
            print("   ", repr(ln[:70]))
        return

    pages_lines = [done.get(i, []) for i in range(args.assemble_limit or total)]
    empty = sum(1 for p in pages_lines if not p)
    if empty:
        print(f"警告：有 {empty} 页没有识别结果（可能是空白页或未跑完）")
    text = pages_to_text(pages_lines)
    if args.no_write:
        print(f"拼装完成（未写文件）: {len(text):,} 字符, "
              f"段落 {len([p for p in text.split(chr(10) + chr(10)) if p.strip()])}")
        for probe in ("26恒星视差", "割礼的犹太人”27", "26 恒星视差"):
            print(f"   页眉残留 {probe!r}: {probe in text}")
        i = text.find("视差的标准定义")
        if i > 0:
            print("--- 正文样本 ---")
            print(text[max(0, i - 150):i + 320])
        return
    out_txt.parent.mkdir(parents=True, exist_ok=True)
    out_txt.write_text(text, encoding="utf-8")
    print(f"OK  {out_txt.name}  {len(text):,} 字符  {out_txt.stat().st_size/1024:.0f} KB")


if __name__ == "__main__":
    main()
