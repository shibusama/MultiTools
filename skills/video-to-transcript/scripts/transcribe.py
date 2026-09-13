# -*- coding: utf-8 -*-
"""链接或本地视频 → 文字稿 txt。

    python transcribe.py <抖音链接 或 本地 mp4/音频>... [-o 输出目录]
                         [--cookies cookie.jar] [--keep-media] [--dry-run]

链接走 yt-dlp 下载；本地文件直接用。视频一律先 ffmpeg 抽成 16k 单声道 mp3
（过转写 API 的体积限制），再交给 agent-reach transcribe。
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def repo_root(start: Path) -> Path:
    for p in [start, *start.parents]:
        if (p / "AGENTS.md").is_file() and (p / "skills").is_dir():
            return p
    raise FileNotFoundError("MultiTools repo root not found from " + str(start))


def resolve_exe(env_name: str, exe: str) -> str:
    override = os.environ.get(env_name)
    if override:
        return override
    found = shutil.which(exe)
    if found:
        return found
    home = Path.home()
    for cand in (
        home / ".agent-reach-venv" / "Scripts" / f"{exe}.exe",
        home / ".agent-reach-venv" / "bin" / exe,
    ):
        if cand.exists():
            return str(cand)
    return exe


ROOT = repo_root(Path(__file__).resolve())
AGENT_REACH = resolve_exe("AGENT_REACH", "agent-reach")
YTDLP = resolve_exe("YTDLP", "yt-dlp")
DEFAULT_JAR = ROOT / "解析大全" / "采集" / "douyin" / "data" / "douyin_cookies.txt"
DOUYIN_PY = ROOT / "解析大全" / "采集" / "douyin" / "douyin.py"
BILI_RE = re.compile(r"(?:bilibili\.com|b23\.tv|bili2233\.cn|/BV1|/BV)", re.I)
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
MEDIA_EXT = {".mp4", ".mov", ".mkv", ".webm", ".flv", ".avi", ".m4s",
             ".mp3", ".m4a", ".wav", ".aac", ".ogg", ".opus", ".flac"}
AUDIO_EXT = {".mp3", ".m4a", ".wav", ".aac", ".ogg", ".opus", ".flac"}
BIG = 20 * 1024 * 1024  # 超过这个体积就先压成 16k 单声道 mp3


def is_url(s: str) -> bool:
    return bool(re.match(r"^https?://", s, re.I))


def douyin_id(url: str) -> str:
    for pat in (r"/video/(\d+)", r"modal_id=(\d+)", r"/note/(\d+)", r"(?:^|\D)(\d{15,20})(?:\D|$)"):
        m = re.search(pat, url)
        if m:
            return m.group(1)
    return ""


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", **kw)


def download(url: str, workdir: Path, jar: Path, dry: bool):
    """yt-dlp 下载，返回落盘路径。"""
    tpl = str(workdir / "%(id)s.%(ext)s")
    cmd = [YTDLP, "--no-playlist", "--no-progress", "-o", tpl]
    if jar and Path(jar).exists():
        cmd += ["--cookies", str(jar)]
    cmd += ["--user-agent", UA, "--print", "after_move:filepath", url]
    if dry:
        print("    [dry-run] " + " ".join(cmd))
        return None
    r = run(cmd, timeout=600)
    paths = [ln.strip() for ln in (r.stdout or "").splitlines() if ln.strip()]
    found = [Path(p) for p in paths if Path(p).exists()]
    if found:
        return found[-1]
    print(f"    下载失败：{(r.stderr or r.stdout or '')[-300:]}")
    return None


def to_audio(media: Path, workdir: Path) -> Path:
    """抽成 16k 单声道 mp3——体积小、能过 API 体积限制。"""
    mp3 = workdir / (media.stem + ".16k.mp3")
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(media), "-vn", "-ar", "16000", "-ac", "1",
         "-b:a", "48k", str(mp3), "-loglevel", "error"],
        capture_output=True)
    return mp3 if mp3.exists() and mp3.stat().st_size > 1000 else media


def transcribe(media: Path, txt: Path) -> bool:
    r = run([AGENT_REACH, "transcribe", str(media), "-o", str(txt)], timeout=1800)
    if txt.exists() and txt.stat().st_size > 0:
        return True
    print(f"    转写失败：{(r.stderr or r.stdout or '')[-300:]}")
    return False


def main():
    ap = argparse.ArgumentParser(description="链接/视频 → 文字稿 txt")
    ap.add_argument("inputs", nargs="+", help="抖音链接，或本地视频/音频文件")
    ap.add_argument("-o", "--out-dir", default="txt", help="输出目录（默认 ./txt）")
    ap.add_argument("--name", default="", help="指定输出名（仅单条时有效）")
    ap.add_argument("--cookies", default="", help="yt-dlp 用的 cookie jar（默认找抖音的 jar）")
    ap.add_argument("--keep-media", action="store_true", help="保留下载/转码的中间媒体文件")
    ap.add_argument("--dry-run", action="store_true", help="只打印将要执行的命令")
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    workdir = out_dir / ".media"
    workdir.mkdir(parents=True, exist_ok=True)
    jar = Path(args.cookies) if args.cookies else DEFAULT_JAR

    for item in args.inputs:
        url = item if is_url(item) else ""
        name = args.name if (args.name and len(args.inputs) == 1) else (
            douyin_id(url) if url else Path(item).stem)
        print(f"===== {name}")

        if (url and BILI_RE.search(url)) or item.strip().upper().startswith("BV"):
            print("    B 站不走 yt-dlp / Groq。用 skill bili-local-transcribe：")
            print("      bili audio <BV> --no-split -o audio\\<BV>")
            print("      然后 Faster-Whisper-XXL + models")
            continue

        if url:
            print("    链接 → yt-dlp 下载")
            media = download(url, workdir, jar, args.dry_run)
            if media is None:
                if not args.dry_run:
                    print("    提示：抖音被风控时，先跑")
                    print(f"      python \"{DOUYIN_PY}\" video {url} --headed")
                    print("    刷新 cookie jar，再重试。")
                continue
        else:
            media = Path(item)
            if not media.exists():
                print(f"    找不到文件：{item}")
                continue

        if media.suffix.lower() not in AUDIO_EXT or media.stat().st_size > BIG:
            print("    抽音轨 → 16k 单声道 mp3")
            media = to_audio(media, workdir)

        txt = out_dir / f"{name}.txt"
        if args.dry_run:
            print(f"    [dry-run] {AGENT_REACH} transcribe {media} -o {txt}")
            continue
        if not transcribe(media, txt):
            continue
        header = f"# 来源: {url or Path(item).name}\n# 日期: {date.today():%Y-%m-%d}\n\n"
        txt.write_text(header + txt.read_text(encoding="utf-8", errors="replace"),
                       encoding="utf-8")
        if not args.keep_media:
            media.unlink(missing_ok=True)
        chars = len(txt.read_text(encoding="utf-8", errors="replace"))
        print(f"    OK  {txt}  {chars:,} 字符")

    if not args.keep_media and workdir.exists():
        try:
            workdir.rmdir()
        except OSError:
            pass


if __name__ == "__main__":
    main()
