---
name: epub-to-txt
description: Use when converting an EPUB to a clean txt — EPUB 转 txt, 电子书转文字, azw/epub 抽文本. Not for scanned PDFs (those stay with pdf-to-txt / RapidOCR).
---

# EPUB → txt

本仓库 `解析大全/文字层直取/convert_to_txt.py` 是齐泽克四本书的一次性脚本（SHA 写死、输出路径写死）。**不要直接跑它。** 用本技能的脚本：

```bash
python skills/epub-to-txt/scripts/epub_to_txt.py <书.epub> [-o 输出目录] [--name 书名]
```

输出 `<输出目录>/<书名>.txt`。章节名来自 NCX，写成 `##` 标题。

扫描 PDF / 有文字层 PDF → 不要用本技能，走 `skills/pdf-to-txt/SKILL.md`。

## Common mistakes

| 错法 | 正法 |
|---|---|
| `python 解析大全/文字层直取/convert_to_txt.py` | 本技能脚本，传入具体 epub 路径 |
| 扫描件 PDF 当 EPUB 解 | `skills/pdf-to-txt` |
