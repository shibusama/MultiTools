# -*- coding: utf-8 -*-
"""EPUB → txt. OPF spine + NCX titles as ## headings."""
import argparse
import os
import re
import sys
import zipfile
from pathlib import Path

from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


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


def main() -> int:
    ap = argparse.ArgumentParser(description="EPUB → txt")
    ap.add_argument("epub", type=Path)
    ap.add_argument("-o", "--out-dir", default="txt")
    ap.add_argument("--name", default="")
    args = ap.parse_args()
    src = args.epub
    if not src.exists() or src.suffix.lower() != ".epub":
        print(f"需要 .epub 文件：{src}", file=sys.stderr)
        return 1
    name = args.name or src.stem
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    text = epub_to_text(src)
    dest = out_dir / f"{name}.txt"
    dest.write_text(text, encoding="utf-8")
    print(f"OK  {dest}  {len(text):,} 字符")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
