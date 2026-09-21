---
name: pdf-to-txt
description: >-
  Convert a PDF ebook to clean txt — PDF 转 txt, 扫描件 OCR, CamScanner,
  有文字层 PDF, RapidOCR, 整本重做. Not for EPUB (use epub-to-txt).
---

# PDF → txt

`解析大全/文字层直取/convert_to_txt.py` 是齐泽克四本书的一次性脚本（SHA 写死）。**不要直接跑它。** 用本技能脚本：

```bash
python skills/pdf-to-txt/scripts/pdf_to_txt.py <书.pdf> [-o 输出目录] [--name 书名] [--probe]
python skills/pdf-to-txt/scripts/pdf_to_txt.py <书.pdf> -o 解析大全/txt --name 书名 --ocr --scale 4
```

默认输出 `解析大全/txt/<书名>.txt`（gitignore）。OCR 缓存按书名分文件，可续跑。

## 流程

1. **先 `--probe`**。看页数、Producer、抽样汉字量、`由千`/`间题` 这类扫描 OCR 脏字。
2. 文字层干净（能选中、汉字足、没有系统性脏字）→ **不要加 `--ocr`**。脚本用普通 `extract_text()`，**禁止 layout 模式**（扫描件的 layout 会抽出大片空白）。
3. 扫描件 / CamScanner / Adobe Paper Capture / 用户说「整本重做」/ 文字层是脏 OCR → **`--ocr --scale 4`**。3.0（约 216dpi）会掉整行；4.0（约 288dpi）才稳。
4. OCR 引擎：`pip install pypdfium2 rapidocr-onnxruntime`。全书按约 1.5 秒/页估时，用专用 `--cache`，不要混用 `pages.jsonl`。
5. 跑完核对：缓存页数 = PDF 页数、无空页、正文抽几段人工看。版权页「N 万字」含标点和英文书目，不要拿它当缺页证据。

EPUB → `epub-to-txt`。

## Common mistakes

| 错法 | 正法 |
|---|---|
| `python 解析大全/文字层直取/convert_to_txt.py` | 本技能脚本，传入具体 pdf 路径 |
| `extract_text(extraction_mode="layout")` 抽扫描件 | 普通 `extract_text()`，或 `--ocr` |
| RapidOCR `--scale 3` 当默认 | `--scale 4` |
| 把 OCR 行间空行都当漏行，拿文字层整段回填 | 空行多半是段距；只补「缺了一整行」的缺口 |
| EPUB 当 PDF 解 | `epub-to-txt` |
