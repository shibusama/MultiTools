# -*- coding: utf-8 -*-
"""PDF → txt。

单文件实现。文字层干净走普通抽取；扫描件 / 脏 OCR 走 RapidOCR。

用法:
    python pdf_to_txt.py <书.pdf> [--probe]
    python pdf_to_txt.py <书.pdf> -o ebook-txt --name 书名
    python pdf_to_txt.py <书.pdf> -o ebook-txt --name 书名 --ocr --scale 4
    python pdf_to_txt.py <书.pdf> --ocr --pages 3      # 试跑前 3 页，只看识别样本
    python pdf_to_txt.py <书.pdf> --ocr --assemble-only # 只拼装已有缓存
"""
from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import sys
import time
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

_REPO = Path(__file__).resolve().parents[3]
_DATA = _REPO / "ebook-txt"  # 输出与缓存的默认根目录

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


# --------------------------------------------------------------------------
# 文字层抽取
# --------------------------------------------------------------------------

def plain_pages(path: Path) -> list[list[str]]:
    """普通文字层抽取：每页若干行。不要用 layout 模式（扫描件会抽成大片空白）。"""
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


# --------------------------------------------------------------------------
# 行 → 正文 / 页脚注释
# --------------------------------------------------------------------------

_CJK_RANGE = r"\u3000-\u303f\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\uff00-\uffef"
_CJK_CHAR = re.compile(f"[{_CJK_RANGE}]")
_SENT_END = re.compile(r"[。！？…；：」』”）】》]$")
_HEADING = re.compile(
    r"^(第\s*[0-9〇零一二三四五六七八九十百千]+\s*[章节節讲講部篇卷回]"
    r"|序言|序\b|前言|导论|導論|引论|引言|结语|結語|结论|結論|后记|後記|附录|附錄"
    r"|译后记|譯後記|目录|目錄|参考文献|索引)"
)
_PAGE_ONLY = re.compile(r"^[\s\-—–·]*[0-9ivxlcdmIVXLCDM]{1,6}[\s\-—–·]*$")
# 页脚注释的起首标记：1 / 1“ / 1 、或者圈码 ①…
_NOTE_START = re.compile(r"^(?:\d{1,2}(?![0-9])[\s“\"'‘（(【\[]|[①-⑳⑴-⑽])")


def norm_line(s: str) -> str:
    """归一化一行，用于统计重复出现的页眉页脚。"""
    return re.sub(r"\d+", "#", re.sub(r"\s+", "", s))[:40]


def despace(t: str) -> str:
    """删除被 PDF 排版插入的、位于中文字符之间的空格。"""
    prev = None
    while prev != t:
        prev = t
        t = re.sub(f"([{_CJK_RANGE}])[ \t]+([{_CJK_RANGE}])", r"\1\2", t)
    return t


def join_line(cur: str, nxt: str) -> str:
    if not cur:
        return nxt
    if not nxt:
        return cur
    if _CJK_CHAR.search(cur[-1]) or _CJK_CHAR.search(nxt[0]):
        return cur + nxt
    return cur + " " + nxt


def detect_indent_mode(pages_lines) -> bool:
    """判断这本书是否用行首缩进标记段落（而不是空行）。"""
    ind = tot = 0
    for lines in pages_lines:
        for ln in lines:
            if not ln.strip():
                continue
            tot += 1
            if len(ln) - len(ln.lstrip()) >= 2:
                ind += 1
    return tot > 0 and ind / tot > 0.03


def ends_sentence(s: str) -> bool:
    """去掉行尾的脚注序号后，判断是否以句末标点结尾。"""
    return bool(_SENT_END.search(re.sub(r"[\d\s\"'”’]+$", "", s)))


def collect_running_lines(pages_lines):
    """找出在大量页面里重复出现的行（页眉/页脚）。"""
    cnt = Counter()
    for lines in pages_lines:
        ne = [ln for ln in lines if ln.strip()]
        for ln in ne[:2] + ne[-2:]:
            cnt[norm_line(ln)] += 1
    threshold = max(4, int(len(pages_lines) * 0.03))
    return {k for k, v in cnt.items() if v >= threshold and len(k) > 1}


def note_is_junk(entry: str) -> bool:
    """过滤掉 OCR 噪声被误当成注释的条目（如 “1 12”“13R”）。"""
    txt = re.sub(r"^【p\.[^】]*】", "", entry).strip()
    txt = re.sub(r"^[①-⑳⑴-⑽]?\s*\d{0,3}\s*[）)】\]]?", "", txt)
    cjk = len(re.findall(r"[\u4e00-\u9fff]", txt))
    lat = len(re.findall(r"[A-Za-z]", txt))
    return len(txt) < 6 or (cjk < 2 and lat < 3)


def pages_to_text(pages_lines, probe: int = 0) -> str:
    """把“每页若干文字行”还原成正文 + 页脚注释附录。

    行首空格代表缩进；空字符串代表行间空档。缩进式与空行式排版都能处理。
    """
    if probe:
        pages_lines = pages_lines[:probe]

    running = collect_running_lines(pages_lines)

    # 估计“PDF 页序号 - 印刷页码”的偏移，用于识别“章名+页码”式页眉、
    # 以及给抽出的页脚注释标注原书页码。
    offsets = []
    for pno, lines in enumerate(pages_lines, 1):
        ne = [l.strip() for l in lines if l.strip()]
        for s in ne[:2]:
            m = re.match(r"^(\d{1,4})\s+\S", s)  # “252 绝对反冲”
            if m:
                d = pno - int(m.group(1))
                if -5 <= d <= 80:
                    offsets.append(d)
            m2 = re.match(r"^(\d{1,4})(?![0-9])", s)  # “26恒星视差：存有论差异之陷阱”
            if m2 and len(s) <= 40:
                d = pno - int(m2.group(1))
                if -5 <= d <= 80:
                    offsets.append(d)
        for s in ne[:2] + ne[-2:]:
            if re.fullmatch(r"\d{1,4}", s):  # 页眉/页脚里孤立的页码
                d = pno - int(s)
                if -5 <= d <= 80:
                    offsets.append(d)
    offset = None
    if offsets:
        v, c = Counter(offsets).most_common(1)[0]
        if c >= max(3, len(pages_lines) * 0.05):
            offset = v

    indent_mode = detect_indent_mode(pages_lines)
    paras: list[str] = []
    notes: list[str] = []
    buf = ""
    prev = ""
    for pno, lines in enumerate(pages_lines, 1):
        # 先剔掉页眉页脚，并记录每行前面是否有空行
        kept = []
        pending_blank = True  # 页首默认视作“接续上一段”
        blank_run = 0
        nb = 0
        # 每行之后紧跟的连续空行数（用于识别页眉与正文之间的空隙）
        blank_after = [0] * len(lines)
        for i in range(len(lines) - 1, 0, -1):
            blank_after[i - 1] = blank_after[i] + 1 if not lines[i].strip() else 0
        for idx, ln in enumerate(lines):
            s = ln.strip()
            if not s:
                pending_blank = True
                blank_run += 1
                continue
            is_head = False
            if nb == 0 and re.match(r"^\d{1,4}\s+\S", s):
                is_head = True  # “252 绝对反冲”式页眉
            if nb == 0 and offset is not None and len(s) <= 40:
                m = re.match(r"^(\d{1,4})(?![0-9])", s)
                if m and abs(int(m.group(1)) - (pno - offset)) <= 1:
                    is_head = True  # “26恒星视差：存有论差异之陷阱”式页眉
            if nb < 2 and offset is not None and len(s) <= 40:
                m = re.search(r"(\d{1,4})\s*$", s)
                if m and abs(int(m.group(1)) - (pno - offset)) <= 1:
                    is_head = True  # “第五章 存在、不知、绝对之知 291”式页眉
            if nb < 2 and blank_after[idx] >= 2 and len(s) <= 20 and not _SENT_END.search(s):
                is_head = True  # “黑格尔对尼采”式章节页眉
            nb += 1
            if is_head or _PAGE_ONLY.match(s) or norm_line(ln) in running:
                continue
            kept.append((ln, pending_blank, blank_run))
            pending_blank = False
            blank_run = 0

        # 页底注释块：
        #   缩进式排版：位于页面下半部、此前有连续空行或带注号，且其后各行无缩进；
        #   空行式排版：以圈码（①…）开头的行，其后续内容即为注释。
        # 页码标注：有印刷页码就用它，正文前的版权/目录页回退到 PDF 页序
        page_label = pno - offset if offset is not None else pno
        if page_label < 1:
            page_label = pno
        cut = len(kept)
        if len(kept) > 6:
            start = int(len(kept) * 0.4)
            soft, strict = [], []
            for i, (ln, _, run) in enumerate(kept):
                if i < start:
                    continue
                s = ln.strip()
                if run >= 2 and re.match(r"^[①-⑳⑴-⑽]", s):
                    soft.append(i)  # 圈码注释（两种排版都适用，续行可带缩进）
                elif indent_mode:
                    if run >= 2:
                        strict.append(i)
                    if len(ln) - len(ln.lstrip()) < 2 and _NOTE_START.match(s):
                        strict.append(i)
            ok = [
                i
                for i in sorted(set(strict))
                if i and all(len(l) - len(l.lstrip()) < 2 for l, _, _ in kept[i:])
            ]
            both = sorted(set(soft) | set(ok))
            if both:
                cut = both[0]
        note_buf = ""
        if os.environ.get("DEBUG_PDF_PAGE") == str(pno):
            print(f"[debug] pno={pno} kept={len(kept)} cut={cut} indent_mode={indent_mode} offset={offset}")
            for i, (l, _, r) in enumerate(kept):
                print(f"   {i:3d} run={r} ind={len(l)-len(l.lstrip())} {l[:46]!r}")
        for ln, _, _ in kept[cut:]:
            s = ln.strip()
            if _NOTE_START.match(s):
                if note_buf:
                    notes.append(f"【p.{page_label}】{despace(note_buf)}")
                note_buf = s
            else:
                note_buf = join_line(note_buf, s)
        if note_buf:
            notes.append(f"【p.{page_label}】{despace(note_buf)}")

        for ln, blank, _ in kept[:cut]:
            s = ln.strip()
            indent = len(ln) - len(ln.lstrip())
            if _HEADING.match(s):
                new_para = True
            elif indent_mode:
                # 缩进式排版：行首缩进 + 上一行确实是句末，才开新段
                # （避免引文块、悬挂缩进被逐行拆成段落）
                new_para = indent >= 2 and (not prev or ends_sentence(prev))
            else:
                # 空行式排版：空行 + 上一行确实是句末，才开新段；
                # 相邻两个短行（目录/标题行）也各自成段，避免标题连成一串
                new_para = blank and (
                    not prev or ends_sentence(prev) or (len(s) <= 30 and len(prev) <= 30)
                )
            if new_para and buf:
                paras.append(despace(buf))
                buf = s
            else:
                buf = join_line(buf, s)
            prev = s
    if buf:
        paras.append(despace(buf))
    text = "\n\n".join(paras) + "\n"
    clean_notes = [n for n in notes if not note_is_junk(n)]
    if clean_notes and not probe:
        dropped = len(notes) - len(clean_notes)
        text += "\n\n\n" + "=" * 20 + " 注释（原书页脚，按页码排列）" + "=" * 20 + "\n\n"
        text += "\n\n".join(clean_notes) + "\n"
        if dropped:
            print(f"    （过滤 OCR 噪声条目 {dropped} 条）")
    return text


# --------------------------------------------------------------------------
# OCR（扫描件）
# --------------------------------------------------------------------------

_ocr = None


def get_ocr():
    global _ocr
    if _ocr is None:
        from rapidocr_onnxruntime import RapidOCR

        _ocr = RapidOCR()
    return _ocr


def _needs_space(a: str, b: str) -> bool:
    return a.isascii() and a.isalnum() and b.isascii() and b.isalnum()


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


def run_ocr(
    pdf_path: Path,
    out_txt: Path,
    cache_path: Path,
    scale: float,
    pages: int = 0,
    assemble_only: bool = False,
    assemble_limit: int = 0,
    no_write: bool = False,
    quiet: bool = False,
) -> int:
    """扫描件 OCR。缓存按页落盘，中断后重跑续上。"""
    import numpy as np
    import pypdfium2 as pdfium

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    doc = pdfium.PdfDocument(str(pdf_path))
    total = len(doc)
    done = load_cache(cache_path)
    if done:
        print(f"缓存已有 {len(done)} 页，继续续跑")

    if not assemble_only:
        ocr = get_ocr()
        limit = min(total, pages) if pages else total
        t0 = time.time()
        processed = 0
        print(f"OCR {limit} 页 scale={scale} cache={cache_path}", flush=True)
        with cache_path.open("a", encoding="utf-8") as fh:
            for i in range(limit):
                if i in done:
                    continue
                page = doc[i]
                img = page.render(scale=scale).to_pil().convert("RGB")
                arr = np.asarray(img)[:, :, ::-1]  # RapidOCR 走 BGR
                res, _ = ocr(arr)
                lines = boxes_to_lines(res or [])
                done[i] = lines
                processed += 1
                fh.write(json.dumps({"pno": i, "lines": lines}, ensure_ascii=False) + "\n")
                fh.flush()
                if processed % 10 == 0 or i + 1 == limit:
                    el = time.time() - t0
                    sp = el / max(1, processed)
                    remain = limit - len([p for p in range(limit) if p in done])
                    print(
                        f"  {i+1}/{limit} 页 | 已用 {el/60:.1f} 分钟 | 约 {sp:.2f} 秒/页 | "
                        f"预计剩余 {remain*sp/60:.0f} 分钟",
                        flush=True,
                    )

    if pages and not assemble_only and not quiet:
        sample = done.get(min(pages, total) - 1, [])
        print("\n--- 最后一页识别样本 ---")
        for ln in sample[:25]:
            print("   ", repr(ln[:70]))

    pages_lines = [done.get(i, []) for i in range(assemble_limit or total)]
    empty = sum(1 for p in pages_lines if not p)
    if empty:
        print(f"警告：有 {empty} 页没有识别结果（可能是空白页或未跑完）")
    text = apply_fixes(pages_to_text(pages_lines))
    if no_write:
        paras = text.split("\n\n")
        print(f"拼装完成（未写文件）: {len(text):,} 字符, 段落 {len([p for p in paras if p.strip()])}")
        return 0
    out_txt.parent.mkdir(parents=True, exist_ok=True)
    out_txt.write_text(text, encoding="utf-8")
    print(f"OK  {out_txt}  {len(text):,} 字符  {_cjk_n(text):,} 汉字")
    return 0


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description="PDF → txt")
    ap.add_argument("pdf", type=Path)
    ap.add_argument("-o", "--out-dir", default=str(_DATA / "txt"))
    ap.add_argument("--name", default="")
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--ocr", action="store_true")
    ap.add_argument("--scale", type=float, default=4.0)
    ap.add_argument("--cache", type=Path, default=None)
    ap.add_argument("--pages", type=int, default=0, help="只 OCR 前 N 页（试跑）")
    ap.add_argument("--assemble-only", action="store_true", help="只拼装已有缓存")
    ap.add_argument("--assemble-limit", type=int, default=0)
    ap.add_argument("--no-write", action="store_true", help="拼装后只打印统计，不写 txt")
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
        cache = args.cache or (_DATA / ".work" / "ocr_cache" / f"{name}.jsonl")
        return run_ocr(
            src,
            dest,
            cache,
            args.scale,
            pages=args.pages,
            assemble_only=args.assemble_only,
            assemble_limit=args.assemble_limit,
            no_write=args.no_write,
        )

    text = apply_fixes(pages_to_text(plain_pages(src)))
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding="utf-8")
    print(f"OK  {dest}  {len(text):,} 字符  {_cjk_n(text):,} 汉字")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
