# MultiTools

本地工具箱：B 站/抖音转写、电子书抽文本、短视频节奏分析。

本仓库**只收代码和 skill**。模型、音视频、登录态、别人的书和讲稿都留在本机，不进 git。

## 目录结构

```
skills/                          # agent 技能（6 个）
  bili-local-transcribe/         # B站/YouTube 本地 Whisper 转写
  video-to-transcript/           # 抖音链接 / 本地 mp4 转文字
    scripts/transcribe.py
  douyin-collect/                # 抖音采集：登录、枚举、采样、刷 cookie
    scripts/douyin.py
  shortform-rhythm/              # 短视频节奏分析
  epub-to-txt/
    scripts/epub_to_txt.py
  pdf-to-txt/
    scripts/pdf_to_txt.py        # 文字层 + RapidOCR，单文件

scripts/                         # 通用批处理脚本
projects/                        # 项目产物与专用脚本
  zhuyizhuyi/                    # 主义主义讲座转写
    raw/ cleaned/ filtered/ index/
  chiikawa/                      # Blender 动画项目
    scripts/ models/ renders/
  dex/                           # 「不存在图鉴」动画
    scripts/ renders/
  douyin-transcripts/            # 抖音视频转写稿

data/                            # 本机素材与采集残留
  audio/ video/ douyin/
outputs/                         # 跨项目产物
  frames/ media/ reports/ subtitles/
ebook-txt/                       # 电子书抽取输出（txt/ .work/）

models/  tools/                  # 模型与外部工具（本机，不入库）
AGENTS.md  README.md  requirements.txt
```

## 不收录（已被 .gitignore）

`.gitignore` 按两级组织：**全局规则**（跨项目）+ **按项目**。
大文件与外部工具一律留在本机。

| 类别 | 内容 |
|---|---|
| 登录态 | `*cookie*`、`browser_profile/` |
| 大文件 / 工具 | `models/`（约 2.9 GB）、`tools/archives/`、`tools/faster-whisper-xxl/`（约 4.5 GB） |
| 媒体源文件 | `*.mp4` / `*.wav` / `*.mp3` 等，以及整个 `data/` |
| 输出产物 | `outputs/`、`ebook-txt/txt/`、各项目的 `renders/` |
| 第三方内容 | `projects/zhuyizhuyi/`（讲座转写）、`projects/douyin-transcripts/` |

> 例外：`projects/chiikawa/models/*.blend` 仅 5.4 MB，**入库**（已被 `!` 规则从 `models/` 中救回）。

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
