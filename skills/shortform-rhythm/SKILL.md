---
name: shortform-rhythm
description: Use when quantitatively breaking down a short video's pacing — 对标爆款, 镜头切点, scene cut, RMS 包络, onset, 关键帧导出, 节奏分析. Not for rewriting into an H3 generate-prompt, and not for ASR.
---

# 短视频节奏拆解

对已有 mp4 做**数字**拆解：切镜头、音量包络、打击点、切点关键帧。脚本只认仓库里的文件。

## 步骤

1. 把片子放进 `analysis_videos/`，扩展名 `.mp4`。不要放进 `_tmp.wav`。
2. 从仓库根跑：

```bash
python scripts/analyze_benchmarks.py
```

3. 读 `outputs/analysis_report.json`，关键帧在 `outputs/analysis_frames/{id}_{nn}_{t}s.jpg`。

## 报告字段

| 字段 | 含义 |
|---|---|
| `duration` | 秒 |
| `cuts` | `scene>0.25` 的切点时刻 |
| `shot_count` | 切点数 + 1 |
| `avg_shot` | 平均镜头时长 |
| `onsets` | RMS 相对前 8 窗均值 ×1.6 的打击点，合并间隔 0.3s |
| `rms_curve` | 200ms 粒度能量 |

写结论时用这些数字（切得密不密、音效是否卡在切点上），不要改去「生成一条同款视频」。

## 分流

| 用户说 | 走 |
|---|---|
| 对标 / 切点 / 节奏数字 | 本技能 |
| 转成文字稿 | 抖音 → `video-to-transcript`；B 站 → `bili-local-transcribe` |
| 知识卡片 | `video-knowledge-card` |

## Common mistakes

- 用 Hub `video-deconstruct` 代替本脚本：那条是语义成片，不是这些数字。
- 只截一张封面当拆解。
