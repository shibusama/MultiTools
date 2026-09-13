# -*- coding: utf-8 -*-
"""把附件里的 EPUB / 有文字层的 PDF 转成纯文本。

用法:
    python convert_to_txt.py            # 转换全部可转的书
    python convert_to_txt.py --probe N  # 只打印前 N 页的解析预览，不写文件
"""
import glob
import os
import re
import sys
import zipfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import pypdf
from bs4 import BeautifulSoup

# 一次性脚本：默认读本目录上一级的 inbox/，输出到 解析大全/txt/。
# 可用环境变量覆盖，避免把本机绝对路径写进仓库。
_PARSE_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = Path(os.environ.get("EBOOK_SRC", _PARSE_ROOT / "inbox"))
OUT_DIR = Path(os.environ.get("EBOOK_OUT", _PARSE_ROOT / "txt"))

# sha256 前缀 -> 输出文件名（不含扩展名）
TARGETS = {
    "f2e08135": "意识形态的崇高客体",
    "72951de4": "少于无——黑格尔与辩证唯物主义的阴影",
    "ddbd28b1": "绝对反冲",
    "60fcc897": "齐泽克的笑话",
}

CJK = r"\u3000-\u303f\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\uff00-\uffef"
_CJK_CHAR = re.compile(f"[{CJK}]")
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
        # 两个中日韩字符（含全角标点）之间的单个空格
        t = re.sub(f"([{CJK}])[ \t]+([{CJK}])", r"\1\2", t)
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
    from collections import Counter

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


def pdf_to_text(path: Path, probe: int = 0) -> str:
    """有文字层的 PDF：按 layout 模式抽出每页文字行（保留行首缩进）。"""
    reader = pypdf.PdfReader(str(path))
    pages_lines = []
    for page in reader.pages:
        try:
            raw = page.extract_text(extraction_mode="layout")
        except Exception:
            try:
                raw = page.extract_text()
            except Exception:
                raw = ""
        pages_lines.append([ln.rstrip() for ln in (raw or "").split("\n")])
    return pages_to_text(pages_lines, probe)


def pages_to_text(pages_lines, probe: int = 0) -> str:
    """把“每页若干文字行”还原成正文 + 页脚注释附录。

    行首空格代表缩进；空字符串代表行间空档。缩进式与空行式排版都能处理。
    """
    if probe:
        pages_lines = pages_lines[:probe]

    running = collect_running_lines(pages_lines)

    # 估计“PDF 页序号 - 印刷页码”的偏移，用于识别“章名+页码”式页眉、
    # 以及给抽出的页脚注释标注原书页码。
    from collections import Counter as _Counter

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
        v, c = _Counter(offsets).most_common(1)[0]
        if c >= max(3, len(pages_lines) * 0.05):
            offset = v

    indent_mode = detect_indent_mode(pages_lines)
    paras = []
    notes = []
    buf = ""
    prev = ""
    for pno, lines in enumerate(pages_lines, 1):
        # 先剔掉页眉页脚，并记录每行前面是否有空行
        kept = []
        pending_blank = True  # 页首默认视作“接续上一段”
        blank_run = 0
        nb = 0
        # 页首短行 + 其后紧跟多个空行 => 页眉（章节名居中排的那种）
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


def epub_to_text(path: Path) -> str:
    z = zipfile.ZipFile(path)
    opf_name = next(n for n in z.namelist() if n.endswith(".opf"))
    base = os.path.dirname(opf_name)
    opf = BeautifulSoup(z.read(opf_name), "xml")

    manifest = {it.get("id"): it.get("href") for it in opf.find_all("item")}
    spine = [manifest.get(r.get("idref")) for r in opf.find_all("itemref")]

    titles = {}
    for ncx_name in [n for n in z.namelist() if n.endswith(".ncx")]:
        ncx = BeautifulSoup(z.read(ncx_name), "xml")
        for nav in ncx.find_all("navPoint"):
            label = nav.find("text")
            content = nav.find("content")
            if label and content:
                titles[content.get("src", "").split("#")[0].split("/")[-1]] = label.get_text(strip=True)

    chunks = []
    for href in spine:
        if not href:
            continue
        full = os.path.normpath(os.path.join(base, href)).replace("\\", "/")
        if full not in z.namelist():
            continue
        soup = BeautifulSoup(z.read(full), "html.parser")
        for tag in soup(["script", "style"]):
            tag.decompose()
        text = soup.get_text("\n")
        text = re.sub(r"[ \t\u00a0]+", " ", text)
        lines = [re.sub(r"\s+", " ", ln).strip() for ln in text.split("\n")]
        lines = [ln for ln in lines if ln]
        if not lines:
            continue
        head = titles.get(os.path.basename(full), "")
        body = "\n".join(lines)
        if head and not body.startswith(head):
            body = f"## {head}\n\n{body}"
        chunks.append(body)
    return "\n\n".join(chunks) + "\n"


def main():
    probe = 0
    if "--probe" in sys.argv:
        probe = int(sys.argv[sys.argv.index("--probe") + 1])
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1]

    files = sorted(glob.glob(str(SRC_ROOT / "**" / "*"), recursive=True))
    files = [Path(f) for f in files if Path(f).is_file()]

    if not probe:
        OUT_DIR.mkdir(parents=True, exist_ok=True)

    for f in files:
        key = next((k for k in TARGETS if k in str(f)), None)
        if not key or (only and only not in key):
            continue
        name = TARGETS[key]
        if f.suffix.lower() == ".epub":
            text = epub_to_text(f)
            size = f.stat().st_size
        elif f.suffix.lower() == ".pdf":
            text = pdf_to_text(f, probe)
            size = len(text)
        else:
            continue
        if probe:
            print(f"===== {name}  ({f.suffix}, 源 {f.stat().st_size/1024/1024:.1f} MB)")
            print(text[:2500])
            print(f"... [预览 {len(text)} 字符]\n")
            continue
        out = OUT_DIR / f"{name}.txt"
        out.write_text(text, encoding="utf-8")
        print(f"OK  {out.name}  {len(text):,} 字符  {out.stat().st_size/1024:.0f} KB  (源 {f.stat().st_size/1024/1024:.1f} MB)")


if __name__ == "__main__":
    main()
