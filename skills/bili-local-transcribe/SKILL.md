---
name: bili-local-transcribe
description: >
  Use when transcribing Bilibili videos locally (BV, B站链接, 批量讲座, 主义主义),
  YouTube 补档 of missing 主义主义 lectures, Faster-Whisper-XXL, local GPU Whisper,
  offline ASR, 不要走云端 / 不要 Groq, HTTP 403 on YouTube audio, or titles that omit
  the matrix code (1-4-4-3 / 2-3-3-3). Also when a B站 URL would otherwise be
  downloaded with yt-dlp.
---

# Bilibili local transcribe

本机 GPU 转写 B 站长课。下载只用 `bili audio`，ASR 只用本仓库的 Faster-Whisper-XXL。命令默认在**仓库根**执行。

**REQUIRED:** 抖音短视频或明确要云端快转 → 本仓库 `video-to-transcript`。

## Hard rules

- B 站下载走 `bili audio`。禁止 `yt-dlp`。
- YouTube **只**用于 B 站没有的补档。下载走 `yt-dlp` + 下面的 player_client 链。ASR 仍走 XXL。禁止 Groq / `agent-reach transcribe`（它用默认 yt-dlp，会 403）。
- 禁止 `One Click Transcribe.bat`（它默认 `medium`，不是这套流水线）。
- 禁止直接跑仓库根的 `scripts/transcribe.py`（写死了单个 BV，模型目录还是错的 `models/large-v3`）。

基线失败：没读这个技能的 agent 会用 yt-dlp 下 B 站 + HuggingFace `WhisperModel('large-v3')`。那不是本仓库已就位的路径。

## Roots

相对仓库根：

| 东西 | 路径 |
|---|---|
| XXL | `tools/archives/Faster-Whisper-XXL_r245.4_windows/Faster-Whisper-XXL/faster-whisper-xxl.exe` |
| 模型目录 | `models/`（里面是 `faster-whisper-large-v3/`） |
| bili | PATH 上的 `bili`（系统工具，不在仓库里） |
| 批量脚本 | `scripts/batch_transcribe_zhuyizhuyi.py` |
| 续跑胶水 | `scripts/finish_temp_transcript.py` |

所有命令设 `$env:PYTHONIOENCODING='utf-8'; $env:PYTHONUTF8='1'`。`bili --help` 在 GBK 控制台会崩；中文搜索用 Python `subprocess` 调 `bili`，不要把中文直接丢进 PowerShell 参数。

## 单条 BV

1. 目标：一个 BV 或 `https://www.bilibili.com/video/BVxxxx`。
2. 若下载失败：`bili status`，未登录则 `bili login`。
3. 下载（已有 `data/audio/{BV}/{BV}.wav` 且 >100KB 则跳过）：

```powershell
bili audio BVxxxx --no-split -o data\audio\BVxxxx
ffmpeg -y -i data\audio\BVxxxx\*.m4a -vn -ac 1 -ar 16000 -c:a pcm_s16le data\audio\BVxxxx\BVxxxx.wav
```

4. 转写。在 XXL 目录设 cwd，`--model_dir` 指向仓库 `models/`（不是 `models\large-v3`）：

```powershell
$root = (Get-Location).Path
$xxl = Join-Path $root "tools\archives\Faster-Whisper-XXL_r245.4_windows\Faster-Whisper-XXL"
& "$xxl\faster-whisper-xxl.exe" (Join-Path $root "data\audio\BVxxxx\BVxxxx.wav") `
  --model large-v3 --model_dir (Join-Path $root "models") `
  --language zh --output_dir (Join-Path $root "outputs\_batch_tmp") `
  --output_format txt --without_timestamps True `
  --device cuda --compute_type float16 --vad_filter True
```

5. 把 `outputs/_batch_tmp/{BVxxxx|source}.txt` **一律去时间戳**后写入 `projects/zhuyizhuyi/raw/{BV}.txt`。`--without_timestamps True` 仍可能写出轴。XXL 有时写完文件仍非 0 退出——文件在就当成功。
6. 默认产物是**无时间轴纯 txt**。用户要带轴 `.md`/`.json` 时再改 `--without_timestamps False` 并换 `--output_format`。

去时间戳（必须覆盖 `HH:MM:SS`，不能只写 `mm:ss`）：

```
^\[\d{1,2}:\d{2}(?::\d{2})?(?:\.\d+)?\s*-->\s*\d{1,2}:\d{2}(?::\d{2})?(?:\.\d+)?\]\s*
```

完成标准：成品 txt 没有任何行以 `[` 开头的时间轴，且尾句收到「就讲到这边/今天就讲到这里」一类收束。

## YouTube 补档

B 站搜不到、用户丢了 YouTube 链接时走这条。产物：`data/audio/YT_{id}/{id}.wav` → `projects/zhuyizhuyi/raw/YT_{id}.txt`。

默认客户端会 403。按序试，拿到 >100KB 的 m4a/mp4 即停：

```powershell
# 1) web
yt-dlp -f "bestaudio/best" --extractor-args "youtube:player_client=web" -x --audio-format m4a --no-playlist -o "data\audio\YT_%(id)s\%(id)s.%(ext)s" "URL"

# 2) 403 或 Only images are available → android + 18
yt-dlp -f 18 --extractor-args "youtube:player_client=android" -x --audio-format m4a --no-playlist -o "data\audio\YT_%(id)s\%(id)s.%(ext)s" "URL"

# 3) 仍失败 → tv_embedded 音轨
yt-dlp -f 140 --extractor-args "youtube:player_client=tv_embedded" -x --audio-format m4a --no-playlist -o "data\audio\YT_%(id)s\%(id)s.%(ext)s" "URL"
```

然后同一套 `ffmpeg` 16k mono wav + XXL。不要用默认（android vr）客户端。

## 主义主义编号

标题经常不写矩阵码。先对口播/清单，再下结论「缺集」。

| 编号 | 正课 | 稿 |
|---|---|---|
| 1-3 | 复习课 `BV1gi4y1T7yg`《十六种庸俗的唯我论》 | `projects/zhuyizhuyi/raw/BV1gi4y1T7yg.txt` |
| 1-2-1-1 | YouTube `yS4-s79G70w` 自然神论 | `projects/zhuyizhuyi/raw/YT_yS4-s79G70w.txt` |
| 1-2-1-2 | YouTube `IL5E7Oh0osw` 神义论 | `projects/zhuyizhuyi/raw/YT_IL5E7Oh0osw.txt` |
| 1-4-4-3 | `BV1aX4y1V7nF`《四重竞争主义》（标题无编号） | `projects/zhuyizhuyi/raw/BV1aX4y1V7nF.txt` |
| 2-3-3-3 | `BV1SA41137C8`《逻辑原子主义》（标题无编号） | `projects/zhuyizhuyi/raw/BV1SA41137C8.txt` |

映射表：`projects/zhuyizhuyi/raw/_BV标题.txt`。

## 批量

主义主义清单已在仓库：`projects/zhuyizhuyi/index/主义主义_BV列表.txt` + `主义主义_视频清单.csv` → `projects/zhuyizhuyi/raw/`。

```powershell
python scripts/batch_transcribe_zhuyizhuyi.py
```

已有 txt 且 >200 字节会 skip。进度：`projects/zhuyizhuyi/raw/_progress.log`、`_success.log`。

其他 UP：同一套命令，换 `data/audio/`、`projects/zhuyizhuyi/raw/`、BV 列表。不要再写一份 fork 脚本。

XXL 写出了临时文件但没晋级：

```powershell
python scripts/finish_temp_transcript.py BVxxxx
```

（这个胶水仍写死主义主义目录；其他 UP 用手把 `_batch_tmp` 的 txt 拷过去并去时间戳。）

## 分流

| 用户说 | 走 |
|---|---|
| B站 / BV / 本地 / XXL / 不要云端 / 批量讲座 / YouTube 补档 | 本技能 |
| 抖音链接、本地 mp4 快转、Groq | 本仓库 `video-to-transcript` |

## Common mistakes

| 错法 | 正法 |
|---|---|
| `yt-dlp` 下 B 站 | `bili audio --no-split` |
| YouTube 默认客户端 / `agent-reach transcribe` | web → android `-f 18` → tv_embedded `-f 140`，再 XXL |
| Groq / HuggingFace `WhisperModel` | XXL exe + `--model_dir models` |
| `tools/faster-whisper-xxl/` | 空目录；用 `tools/archives/.../faster-whisper-xxl.exe` |
| One Click / `-m medium` | 上面的 XXL 参数 |
| 只剥 `mm:ss` 时间轴 | 正则必须含可选 `HH:` |
| 标题没有 `（1-4-4-3）` 就当缺集 | 对口播；见上表 |
| 抽成 16k mp3 给云端 API | 这条链路要 16k **wav** |
