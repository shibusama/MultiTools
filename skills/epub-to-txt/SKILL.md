---
name: epub-to-txt
description: Use when converting an EPUB to a clean txt — EPUB 转 txt, 电子书转文字, azw/epub 抽文本. Not for scanned PDFs (those stay with pdf-to-txt / RapidOCR).
---

# EPUB → txt

用本技能的脚本（仓库里没有其他 EPUB 转换入口）：

```bash
python skills/epub-to-txt/scripts/epub_to_txt.py <书.epub> [-o 输出目录] [--name 书名]
```

输出 `<输出目录>/<书名>.txt`。章节名来自 NCX，写成 `##` 标题。

扫描 PDF / 有文字层 PDF → 不要用本技能，走 `skills/pdf-to-txt/SKILL.md`。

## Common mistakes

| 错法 | 正法 |
|---|---|
| 找 `解析大全/文字层直取/convert_to_txt.py`（已删除） | 本技能脚本是唯一入口，传入具体 epub 路径 |
| 扫描件 PDF 当 EPUB 解 | `skills/pdf-to-txt` |
