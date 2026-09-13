---
name: video-to-transcript
description: Use when turning a Douyin link or a local mp4/m4a/mp3 into a txt transcript. Also when the user says 把这个抖音视频下载下来, 把这个视频转成文字, mp4 转文字稿, or 给这个链接出文字稿. Not for Bilibili/BV/本地 Whisper/XXL/不要走云端 — those belong to bili-local-transcribe.
---

# 视频 → 文字稿

**先分流。** B 站 / BV / Faster-Whisper-XXL / 本地 GPU / 批量讲座 / 不要走云端 → **REQUIRED SUB-SKILL:** `bili-local-transcribe`。本技能只做抖音（yt-dlp）和本地文件的 Groq 快转。知识卡片 → `video-knowledge-card`。

从仓库根：

```bash
python skills/video-to-transcript/scripts/transcribe.py <链接 或 视频文件>... [-o 输出目录] [--name 名字]
```

- **链接**：yt-dlp 下载 → ffmpeg 抽音 → 转写。脚本遇到 B 站 URL 会拒绝，改走 `bili-local-transcribe`。
- **本地 mp4/音频**：直接抽音 → 转写
- 输出 `<输出目录>/<名字>.txt`：抖音链接用 `aweme_id` 命名，本地文件用文件名；开头两行是来源与日期
- 批量就一次传多个

转写引擎是 `agent-reach transcribe`（Groq whisper-large-v3），视频一律先压成 **16k 单声道 mp3** 以过 API 体积限制。Cookie 默认用本仓库 `解析大全/采集/douyin/data/douyin_cookies.txt`。

## 依赖（本机已就位）

| 依赖 | 位置 |
|---|---|
| agent-reach | PATH，或 `~/.agent-reach-venv/` |
| yt-dlp | PATH，或同上 venv |
| ffmpeg / ffprobe | PATH |

可用环境变量覆盖：`AGENT_REACH`、`YTDLP`。

## 抖音被风控时

yt-dlp 拿不到视频时（`下载失败` 提示），先用采集工具刷新 cookie jar（会开有头浏览器）：

```bash
python "解析大全/采集/douyin/douyin.py" video <链接> --headed
```

抖音**不能无头**，headless 必触发验证码。

## 已知限制

- **语言自动识别可能误判**：口音重的长视频会被整段判成别的语言。`agent-reach transcribe` 的 CLI **不支持指定语言**；确需强制英文时用 `~/.dsh/skills/zizek-perspective/scripts/transcribe_forced.py <音频> <输出txt>`。
- 转写是 ASR 产物：专有名词会被系统性听错，**不可作逐字引用来源**；引用前核对原视频。
- 长视频耗时按音频时长走（85 分钟讲座要十几分钟），跑之前先说一声。
