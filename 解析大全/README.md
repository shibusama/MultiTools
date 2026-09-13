# 解析大全

电子书 → 纯文本。目录按脚本目的分类。成品 txt、OCR 引擎、inbox 都不进 git。

## 目录

| 路径 | 目的 |
|---|---|
| `文字层直取/convert_to_txt.py` | EPUB / 有文字层 PDF → txt（一次性、按书名映射；日常请用仓库 skill） |
| `扫描件OCR/ocr_scanned.py` | 纯扫描 PDF → OCR。引擎用 pip 或自备 `engine/` |
| `txt/` | 成品输出（gitignore） |
| `.work/` | OCR 分页缓存（gitignore） |
| `采集/douyin/` | 抖音采集脚本；`browser_profile/` 和 `data/` 不入库 |

先试文字层直取，抽不出字再走扫描 OCR。

日常让 agent 走 skill `epub-to-txt`：

```bash
python skills/epub-to-txt/scripts/epub_to_txt.py <书.epub> -o txt --name 书名
```

扫描件：

```powershell
pip install pypdfium2 rapidocr-onnxruntime
# 若用本目录 vendored engine：
# $env:PYTHONPATH = "$PWD\扫描件OCR\engine"

python 扫描件OCR/ocr_scanned.py --pdf <扫描件.pdf> --out txt/书名.txt --pages 40
```

`ocr_scanned.py` 需要 `--pdf`。缓存按页落盘，中断后重跑续上。
