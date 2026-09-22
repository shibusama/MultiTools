# MultiTools

本地工具箱：B 站/抖音转写、电子书抽文本、短视频节奏分析。

本仓库**只收代码和 skill**。模型、音视频、登录态、别人的书和讲稿都留在本机，不进 git。

## 收录（可公开）

```
skills/                          # agent 技能
  bili-local-transcribe/
  video-to-transcript/
  douyin-collect/
    scripts/douyin.py            # 抖音采集（不含 data/、browser_profile/）
  shortform-rhythm/
  epub-to-txt/
    scripts/epub_to_txt.py
  pdf-to-txt/
    scripts/pdf_to_txt.py        # 文字层 + RapidOCR，单文件
scripts/                         # 批处理、节奏分析、成片脚本
chiikawa动画制作/                 # Blender 动画项目：脚本 + 模型 + 笔记
  scripts/  models/
AGENTS.md
list_voices.ps1
requirements.txt
```

## 不收录（已被 .gitignore）

- 登录态：`*cookie*`、`browser_profile/`
- 大文件：`models/`、`tools/archives/`、`chiikawa动画制作/renders/`
- 媒体：`audio/`、`analysis_videos/`、`*.mp4` / `*.wav` / `*.mp3`
- 第三方内容：讲座转写、电子书 txt、抖音采样 json

## 本机依赖（不进仓库）

| 用途 | 怎么准备 |
|---|---|
| B 站本机转写 | 把 [Faster-Whisper-XXL](https://github.com/Purfview/whisper-standalone-win) 解压到 `tools/archives/Faster-Whisper-XXL_r245.4_windows/Faster-Whisper-XXL/`，模型放到 `models/faster-whisper-large-v3/` |
| B 站下载 | PATH 上的 `bili` |
| 抖音快转 | `agent-reach`、`yt-dlp`、`ffmpeg`（可用环境变量 `AGENT_REACH` / `YTDLP`） |
| 扫描件 OCR | `pip install pypdfium2 rapidocr-onnxruntime` |

```powershell
pip install -r requirements.txt
```

Agent 用法见 `AGENTS.md` 和各 `skills/*/SKILL.md`。
