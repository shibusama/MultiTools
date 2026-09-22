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

`.gitignore` 按两级组织：**全局规则**（跨项目）+ **按项目**。体积详见下一节。

| 类别 | 内容 |
|---|---|
| 登录态 | `*cookie*`、`browser_profile/` |
| 大文件 / 工具 | `models/`（2.9 GB）、`tools/archives/`、`tools/faster-whisper-xxl/`（4.4 GB），合计约 7.3 GB |
| 媒体源文件 | `*.mp4` / `*.wav` / `*.mp3` 等，以及整个 `data/`（256 MB） |
| 输出产物 | `outputs/`（3.9 MB）、各项目的 `renders/`（约 123 MB） |
| 电子书输入 | `ebook-txt/inbox/`（原始 epub/pdf）与 OCR 缓存 |

> **例外**：`projects/chiikawa/models/*.blend` 仅 5.4 MB，**已入库**（被 `!` 规则从 `models/` 中救回）。
>
> **已入库**：`projects/zhuyizhuyi/`（818 个讲座转写）、`projects/douyin-transcripts/`、`ebook-txt/txt/`（4 本电子书正文）。

## 大文件与本机依赖（不进仓库）

以下内容体积大或与本机绑定，一律留在本机、不进 git。**换机器时需要自己准备**。

### 体积一览

| 路径 | 体积 | 是什么 | 能重建吗 |
|---|---|---|---|
| `tools/archives/` | **4.4 GB** | Faster-Whisper-XXL 免安装包 | 能，重新下载 |
| `models/faster-whisper-large-v3/` | **2.9 GB** | Whisper large-v3 权重 | 能，重新下载 |
| `data/audio/` | **226 MB** | 下载的音频（按 BV / YT id 分目录） | 能，重跑下载 |
| `data/.media/` | **22 MB** | 转写中间媒体 | 能 |
| `data/video/` | **8.2 MB** | 节奏分析用的源视频 | 能 |
| `data/douyin/` | 0.2 MB | cookie 与抓取的 html | 不能，需重新登录 |
| `outputs/` | **3.9 MB** | 跨项目产物（frames/reports/subtitles） | 能，重跑脚本 |
| `projects/*/renders/` | 约 **123 MB** | 渲染帧与成片 | 能，Blender 重渲 |

> 这些加起来约 **7.7 GB**。仓库本身（入库部分）只有约 **27 MB**。

### 怎么准备

| 用途 | 怎么准备 |
|---|---|
| B 站本机转写 | ① 下载 [Faster-Whisper-XXL](https://github.com/Purfview/whisper-standalone-win) 的 `Faster-Whisper-XXL_r245.4_windows.7z`，解压后把内层 `Faster-Whisper-XXL/` 放到 `tools/archives/Faster-Whisper-XXL_r245.4_windows/`，最终 exe 位于 `tools/archives/Faster-Whisper-XXL_r245.4_windows/Faster-Whisper-XXL/faster-whisper-xxl.exe`（约 39 MB）<br>② 模型放到 `models/faster-whisper-large-v3/`（含 `model.bin`、`config.json`、`tokenizer.json`、`vocabulary.json`、`preprocessor_config.json`） |
| B 站下载 | PATH 上的 `bili` |
| 抖音快转 | `agent-reach`、`yt-dlp`、`ffmpeg`（可用环境变量 `AGENT_REACH` / `YTDLP`） |
| 扫描件 OCR | `pip install pypdfium2 rapidocr-onnxruntime` |
| chiikawa 动画 | Blender（脚本见 `projects/chiikawa/scripts/`） |

```powershell
pip install -r requirements.txt
```

> 注：`tools/faster-whisper-xxl/` 是个**空目录占位**，真正的 exe 在 `tools/archives/` 下（见上表）。

Agent 用法见 `AGENTS.md` 和各 `skills/*/SKILL.md`。
