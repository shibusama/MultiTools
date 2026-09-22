# -*- coding: utf-8 -*-
"""对标爆款拆解：镜头切点 + 音频 RMS 包络 + 关键帧导出"""
import json, subprocess, wave
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
VIDS = ROOT / "data" / "video"
FRAMES = ROOT / "outputs" / "frames"
FRAMES.mkdir(parents=True, exist_ok=True)

SR = 22050

def probe(path):
    d = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    return float(d.stdout.strip())

def scene_cuts(path):
    r = subprocess.run(
        ["ffmpeg", "-i", str(path), "-vf",
         "select='gt(scene,0.25)',metadata=print:file=-", "-f", "null", "-"],
        capture_output=True, text=True)
    cuts = []
    for line in r.stdout.splitlines():
        if "pts_time:" in line:
            cuts.append(float(line.split("pts_time:")[1].split()[0]))
    return sorted(set(round(c, 2) for c in cuts))

def audio_rms(path):
    wav = VIDS / "_tmp.wav"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(path),
                    "-ar", str(SR), "-ac", "1", str(wav)], check=True)
    with wave.open(str(wav), "rb") as w:
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    wav.unlink()
    hop = SR // 20  # 50ms
    n = len(x) // hop
    rms = np.sqrt((x[:n*hop].reshape(n, hop) ** 2).mean(axis=1))
    return rms

def onsets(rms, thresh_ratio=1.6):
    """能量突增点 = 音乐重音/音效打击点"""
    o = []
    for i in range(2, len(rms) - 2):
        base = np.mean(rms[max(0, i-8):i])
        if rms[i] > base * thresh_ratio and rms[i] >= rms[i-1] and rms[i] >= rms[i+1]:
            o.append(round(i * 0.05, 2))
    merged = []
    for t in o:
        if not merged or t - merged[-1] > 0.3:
            merged.append(t)
    return merged

def grab_frames(path, cuts, bvid):
    idxs = [0.1] + cuts
    for i, t in enumerate(idxs):
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(t), "-i", str(path),
                        "-frames:v", "1", "-vf", "scale=480:-2",
                        str(FRAMES / f"{bvid}_{i:02d}_{t:.2f}s.jpg")], check=True)

report = {}
for mp4 in sorted(p for p in VIDS.glob("*.mp4") if not p.name.startswith("_")):
    bvid = mp4.stem
    dur = probe(mp4)
    cuts = scene_cuts(mp4)
    shots = len(cuts) + 1
    avg = dur / shots
    rms = audio_rms(mp4)
    ons = onsets(rms)
    grab_frames(mp4, cuts, bvid)
    report[bvid] = {
        "duration": round(dur, 2), "cuts": cuts, "shot_count": shots,
        "avg_shot": round(avg, 2), "onsets": ons,
        "onset_count": len(ons),
        "rms_curve": [round(float(v), 3) for v in rms[::4]],  # 200ms 粒度
    }
    print(f"{bvid}: {dur:.1f}s shots={shots} avg={avg:.2f}s onsets={len(ons)}")

(ROOT / "outputs" / "reports" / "analysis_report.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
print("saved outputs/reports/analysis_report.json")
