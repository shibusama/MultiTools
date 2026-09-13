#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""抖音采集工具（子命令式合一版）

原 persona-skills/douyin_fetch/ 下 10 个脚本合并而来。

用法:
    python douyin.py login     [--minutes 15]                 扫码登录，存 browser_profile/
    python douyin.py posts     <sec_uid> [-o out.json]        枚举账号全部作品
    python douyin.py sample    <关键词...> [-o out.json] [--mins 3] [--headed]
    python douyin.py video     <视频url或id> [--jar jar.txt]   单视频过风控 + 导 cookie
    python douyin.py transcribe [list.json]                   批量下载转写（断点续跑）
    python douyin.py status                                   查看登录态与数据现状

常用:
    # 1) 先登录（只需一次，登录态持久化在 browser_profile/）
    python douyin.py login

    # 2) 枚举某账号的全部作品
    python douyin.py posts MS4wLjABAAAA...

    # 3) 按关键词采样文案（跨作者，不下载视频）
    python douyin.py sample 历史 科技 --mins 3

    # 4) 把 posts 的结果拿去批量转写
    python douyin.py transcribe data/video_list.json

设计约定:
    - 所有路径相对本文件所在目录，不受 cwd 影响（原来的脚本混用 cwd 与 __file__）。
    - browser_profile/ 是持久化登录态；data/ 放 json 产物；audio/、transcripts/ 放中间产物。
    - 子命令映射自旧脚本:
        login      <- douyin_login.py（login_wait.py 已被它取代，未保留）
        posts      <- enumerate_user3.py（v1/v2 是失败尝试，未保留）
        sample     <- douyin_sample.py
        video      <- douyin_bootstrap.py
        transcribe <- batch_transcribe.py

前置:
    - 抖音必须**有头**浏览器；headless 会触发验证码。sample/video 传 --headed 亦然。
    - 转写走 agent-reach（Groq whisper-large-v3），需 ffmpeg 与 curl 在 PATH 中。
"""
import argparse
import json
import os
import random
import shutil
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, urlparse

BASE = Path(__file__).resolve().parent
PROFILE_DIR = str(BASE / "browser_profile")
DATA = BASE / "data"
AUDIO = BASE / "audio"
TRANS = BASE / "transcripts"

for d in (DATA, AUDIO, TRANS):
    d.mkdir(exist_ok=True)

# 抖音登录态的 cookie 名。
# ⚠️ 不要放 passport_csrf_token——访客也会被种上这个 cookie，会造成假阳性
# （douyin_login.py 初版就踩了这个坑：一打开首页就误判"已登录"，20 秒即退出）。
LOGIN_COOKIES = {"sessionid", "sessionid_ss", "sid_tt", "uid_tt"}

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")


def _resolve_exe(env_name: str, exe: str) -> str:
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


AGENT_REACH = _resolve_exe("AGENT_REACH", "agent-reach")

# 统一的浏览器启动参数：真实 Chrome + 关代理 + 去自动化特征
LAUNCH_ARGS = ["--no-proxy-server", "--disable-blink-features=AutomationControlled"]


def _open_ctx(p, headless=False):
    """打开持久化 profile 的浏览器上下文（复用登录态）。"""
    return p.chromium.launch_persistent_context(
        PROFILE_DIR,
        headless=headless,
        channel="chrome",
        args=LAUNCH_ARGS,
        viewport={"width": 1380, "height": 900},
        locale="zh-CN",
    )


def _logged_in_cookies(ctx):
    return sorted({c["name"] for c in ctx.cookies()} & LOGIN_COOKIES)


def _out_path(p):
    """-o 的值：没有目录部分的落到 data/，有目录部分的按用户指定。"""
    if p is None:
        return None
    p = Path(p)
    return p if p.parent != Path(".") else DATA / p.name


# ============================================================ login
def cmd_login(args):
    """打开有头浏览器让用户扫码，轮询登录 cookie，登录成功即保存并退出。"""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        ctx = _open_ctx(p, headless=False)
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        already = _logged_in_cookies(ctx)
        print("=" * 60, flush=True)
        if already:
            print(f"检测到已有登录态（{already}），无需扫码。", flush=True)
        else:
            print(f"浏览器已打开抖音首页（profile: {PROFILE_DIR}）", flush=True)
            print(">>> 请在弹出的窗口里扫码登录 <<<", flush=True)
            print(f"（最多等待 {args.minutes} 分钟，登录成功后会自动关闭窗口）", flush=True)
        print("=" * 60, flush=True)

        try:
            page.goto("https://www.douyin.com/", wait_until="domcontentloaded", timeout=60000)
        except Exception as e:
            print(f"打开首页出错（不影响扫码，可手动在窗口里操作）: {str(e)[:120]}", flush=True)

        ok = bool(already)
        deadline = time.time() + args.minutes * 60
        tick = 0
        while not ok and time.time() < deadline:
            try:
                if not ctx.pages or all(pg.is_closed() for pg in ctx.pages):
                    print("窗口被关闭，未完成登录。", flush=True)
                    break
                page.wait_for_timeout(2000)
                tick += 1
                hit = _logged_in_cookies(ctx)
                if hit:
                    ok = True
                    print(f"[OK] 登录成功，检测到 {hit}", flush=True)
                    break
                if tick % 15 == 0:
                    left = int((deadline - time.time()) / 60)
                    print(f"  ...等待登录中（剩余约 {left} 分钟）", flush=True)
            except Exception as e:
                print(f"轮询异常: {str(e)[:120]}", flush=True)
                break

        if not ok:
            print("[FAIL] 未检测到登录态。若你已登录，可能是 cookie 名不同。", flush=True)
        ctx.close()
    return 0 if ok else 1


# ============================================================ posts
def cmd_posts(args):
    """枚举某账号的全部作品（有头 + 持久化 profile + 拟人节奏）。"""
    from playwright.sync_api import sync_playwright

    url = f"https://www.douyin.com/user/{args.sec_uid}"
    out = _out_path(args.out) or (DATA / "video_list.json")
    posts = {}
    state = {"has_more": None, "cursor": None, "bad_bodies": []}

    def on_response(resp):
        if "/aweme/v1/web/aweme/post/" not in resp.url:
            return
        try:
            d = resp.json()
        except Exception:
            if len(state["bad_bodies"]) < 3:
                try:
                    state["bad_bodies"].append(resp.text()[:200])
                except Exception:
                    pass
            return
        state["has_more"] = d.get("has_more")
        state["cursor"] = d.get("max_cursor")
        for a in d.get("aweme_list", []):
            video = a.get("video") or {}
            play = (video.get("play_addr") or {}).get("url_list") or []
            play2 = (video.get("play_addr_lowbr") or {}).get("url_list") or []
            posts[a["aweme_id"]] = {
                "aweme_id": a["aweme_id"],
                "desc": a.get("desc", ""),
                "create_time": a.get("create_time"),
                "duration_ms": video.get("duration"),
                "play_url": play[0] if play else (play2[0] if play2 else None),
            }

    with sync_playwright() as p:
        ctx = _open_ctx(p, headless=False)
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        print(f"登录态: {_logged_in_cookies(ctx)}", flush=True)
        page.on("response", on_response)
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(6000)

        stall_rounds = 0
        last = -1
        i = 0
        while i < args.max_scroll:
            i += 1
            # 滚真正的路由容器（window 本身不滚）
            page.evaluate("""() => {
                const c = document.querySelector('.route-scroll-container');
                if (c) c.scrollTop = c.scrollHeight;
                window.scrollTo(0, document.documentElement.scrollHeight);
            }""")
            page.mouse.wheel(0, random.randint(400, 900))
            page.wait_for_timeout(random.randint(1500, 3200))
            if i % 4 == 0:
                print(f"scroll {i}: {len(posts)} videos, has_more={state['has_more']}, "
                      f"cursor={state['cursor']}", flush=True)
            if state["has_more"] == 0 and len(posts) > 0:
                print("has_more==0, complete", flush=True)
                break
            if len(posts) == last:
                stall_rounds += 1
                if stall_rounds % 10 == 0:
                    print(f"  stalled {stall_rounds} rounds; bad body sample: "
                          f"{state['bad_bodies'][:1]}", flush=True)
                if stall_rounds >= 60:
                    print("stalled 60 rounds, stop", flush=True)
                    break
            else:
                stall_rounds = 0
            last = len(posts)
        ctx.close()

    out_list = sorted(posts.values(), key=lambda x: x["create_time"] or 0, reverse=True)
    out.write_text(json.dumps(out_list, ensure_ascii=False, indent=1), encoding="utf-8")
    total_min = sum((v["duration_ms"] or 0) for v in out_list) / 60000
    if out_list:
        print("range:",
              datetime.fromtimestamp(out_list[-1]["create_time"]).strftime("%Y-%m-%d"),
              "->",
              datetime.fromtimestamp(out_list[0]["create_time"]).strftime("%Y-%m-%d"))
        if not args.keep_urls:
            for v in out_list:
                v.pop("play_url", None)
            out.write_text(json.dumps(out_list, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"saved {len(out_list)} videos, total {total_min:.0f} min -> {out}")
    return 0


# ============================================================ sample
def _walk(obj, sink):
    """在任意层级的 JSON 里捞带 aweme_id 的条目。"""
    if isinstance(obj, dict):
        if obj.get("aweme_id"):
            sink(obj)
        for v in obj.values():
            _walk(v, sink)
    elif isinstance(obj, list):
        for v in obj:
            _walk(v, sink)


def cmd_sample(args):
    """搜索页拦接口采样文案（样本天然跨作者，不下载视频）。"""
    from playwright.sync_api import sync_playwright

    out = _out_path(args.out) or (DATA / "douyin_samples.json")
    seen = {}
    api_hits = Counter()
    all_resp = Counter()

    def on_response(resp):
        u = resp.url
        all_resp[u.split("?")[0]] += 1
        if "aweme" not in u:
            return
        api_hits[u.split("?")[0]] += 1
        try:
            d = resp.json()
        except Exception:
            return

        def sink(aweme):
            vid = aweme["aweme_id"]
            if vid in seen:
                return
            author = aweme.get("author") or {}
            video = aweme.get("video") or {}
            play = (video.get("play_addr") or {}).get("url_list") or []
            play2 = (video.get("play_addr_lowbr") or {}).get("url_list") or []
            cover = (video.get("cover") or {}).get("url_list") or []
            ocover = (video.get("origin_cover") or {}).get("url_list") or []
            seen[vid] = {
                "aweme_id": vid,
                "desc": aweme.get("desc", ""),
                "create_time": aweme.get("create_time"),
                "duration_ms": video.get("duration"),
                # play_url 供后续下载音频做转写（语速实测需要音频）
                "play_url": play[0] if play else (play2[0] if play2 else None),
                # cover 供 OCR 封面文字——封面字渲染在画面里，desc 里没有
                "cover_url": cover[0] if cover else (ocover[0] if ocover else None),
                "author": author.get("nickname"),
                "stats": {k: (aweme.get("statistics") or {}).get(k)
                          for k in ("digg_count", "comment_count", "share_count")},
            }

        _walk(d, sink)

    with sync_playwright() as p:
        ctx = _open_ctx(p, headless=not args.headed)
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.on("response", on_response)
        logged = _logged_in_cookies(ctx)
        print(f"profile 内 cookie 数: {len(ctx.cookies())}；登录态: {logged}", flush=True)
        if not logged:
            print("⚠ 未检测到登录态，建议先跑 `python douyin.py login`", flush=True)

        for kw in args.keywords:
            print(f"=== 搜索: {kw} ===", flush=True)
            try:
                page.goto(f"https://www.douyin.com/search/{kw}?type=general",
                          wait_until="domcontentloaded", timeout=60000)
            except Exception as e:
                print(f"  打开失败: {str(e)[:100]}", flush=True)
                continue
            page.wait_for_timeout(3000)
            if args.diag:
                try:
                    print(f"  title: {page.title()[:80]}", flush=True)
                    print(f"  url:   {page.url[:110]}", flush=True)
                    body = page.inner_text("body")[:200].replace("\n", " / ")
                    print(f"  正文前 200 字: {body}", flush=True)
                except Exception as e:
                    print(f"  诊断失败: {str(e)[:100]}", flush=True)
            deadline = time.time() + args.mins * 60
            last, stall = -1, 0
            while time.time() < deadline:
                page.mouse.wheel(0, 1200)
                page.wait_for_timeout(2200)
                if len(seen) == last:
                    stall += 1
                    if stall >= 8:
                        break
                else:
                    stall = 0
                last = len(seen)
            print(f"  累计 {len(seen)} 条", flush=True)
            # 结束时再看一眼标题：验证码/风控页可能在滚动过程中才出现，
            # 只看 goto 之后的标题会漏掉（实测「健康/汽车/法律」三个关键词拿到 0 条
            # 搜索结果、只抓到搜索页默认推荐流，就是这种情况）。
            try:
                t = page.title()[:60]
                if "验证" in t:
                    print(f"  ⚠ 检测到风控页: {t}", flush=True)
                else:
                    print(f"  结束时标题: {t}", flush=True)
            except Exception:
                pass

        ctx.close()

    out_list = sorted(seen.values(), key=lambda x: x.get("create_time") or 0, reverse=True)
    out.write_text(json.dumps(out_list, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"\n抓到 {len(out_list)} 条 -> {out}")
    print("含 aweme 的接口:")
    for u, n in api_hits.most_common(8):
        print(f"  {n:>5}  {u}")
    if args.diag:
        print("全部响应路径（前 15）:")
        for u, n in all_resp.most_common(15):
            print(f"  {n:>5}  {u}")
    return 0


# ============================================================ video
def _to_netscape(domain_cookies, jar_path):
    lines = ["# Netscape HTTP Cookie File"]
    for domain, cookies in domain_cookies:
        for c in cookies:
            dom = domain if domain.startswith(".") else "." + domain
            expiry = int(c.get("expires", 0)) if c.get("expires", -1) > 0 else 2147483647
            lines.append("\t".join([
                dom, "TRUE", c.get("path", "/"), "TRUE",
                str(expiry), c["name"], c["value"],
            ]))
    Path(jar_path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def cmd_video(args):
    """单视频过风控：取详情 + 导 Netscape cookie jar（供 yt-dlp 用）。"""
    from playwright.sync_api import sync_playwright

    raw = args.target
    if raw.startswith("http"):
        q = parse_qs(urlparse(raw).query).get("modal_id")
        digits = [s for s in urlparse(raw).path.split("/") if s.isdigit()]
        vid = q[0] if q else (digits[0] if digits else raw)
    else:
        vid = raw
    url = raw if "douyin.com" in raw else f"https://www.douyin.com/video/{vid}"
    jar = _out_path(args.jar) or (DATA / "douyin_cookies.txt")

    detail_json = {}
    with sync_playwright() as p:
        ctx = _open_ctx(p, headless=not args.headed)
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        def on_response(resp):
            if "aweme/v1/web/aweme/detail" in resp.url:
                try:
                    detail_json.update(resp.json())
                except Exception:
                    pass

        page.on("response", on_response)
        page.goto(url, wait_until="domcontentloaded", timeout=45000)
        for _ in range(30):
            if detail_json.get("aweme_detail"):
                break
            page.wait_for_timeout(1000)
        cookies = ctx.cookies()
        ctx.close()

    aweme = detail_json.get("aweme_detail") or {}
    author = aweme.get("author", {})
    stats = aweme.get("statistics", {})
    summary = {
        "video_id": vid,
        "desc": aweme.get("desc"),
        "create_time": aweme.get("create_time"),
        "duration_ms": aweme.get("video", {}).get("duration"),
        "nickname": author.get("nickname"),
        "sec_uid": author.get("sec_uid"),
        "uid": author.get("uid"),
        "stats": {k: stats.get(k) for k in ("digg_count", "comment_count", "share_count")},
        "cookies_exported": len(cookies),
        "cookie_names": sorted({c["name"] for c in cookies}),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if not aweme:
        print("⚠ 没抓到 aweme_detail——多半是风控页。试试 --headed 观察窗口。", flush=True)

    groups = {}
    for c in cookies:
        groups.setdefault(c["domain"], []).append(c)
    _to_netscape(groups.items(), jar)
    print(f"cookie jar -> {jar}")
    return 0


# ============================================================ transcribe
def cmd_transcribe(args):
    """批量：下载视频 -> ffmpeg 抽音 -> agent-reach 转写。断点续跑。"""
    lst = _out_path(args.list) or (DATA / "video_list.json")
    if not lst.exists():
        print(f"[FAIL] 找不到清单: {lst}", flush=True)
        print("       先跑 `python douyin.py posts <sec_uid>` 生成。", flush=True)
        return 1

    videos = json.loads(lst.read_text(encoding="utf-8"))
    print(f"{len(videos)} videos in list", flush=True)

    failures = []
    for idx, v in enumerate(videos, 1):
        vid = v["aweme_id"]
        txt = TRANS / f"{vid}.txt"
        if txt.exists() and txt.stat().st_size > 50:
            continue
        date = datetime.fromtimestamp(v.get("create_time") or 0).strftime("%Y-%m-%d")
        print(f"[{idx}/{len(videos)}] {vid} ({date}) {(v.get('desc') or '')[:30]}", flush=True)

        mp4 = AUDIO / f"{vid}.mp4"
        mp3 = AUDIO / f"{vid}.mp3"

        # ---- download ----
        ok = False
        log = open(BASE / "dl.log", "ab")
        if v.get("play_url"):
            for extra in (["-H", "Referer: https://www.douyin.com/"],
                          ["-H", "Referer: https://www.douyin.com/",
                           "-b", str(DATA / "douyin_cookies.txt")]):
                subprocess.run(
                    ["curl", "-sL", "--max-time", "300", "--max-filesize", "500M",
                     "-A", UA, *extra, "-o", str(mp4), v["play_url"]],
                    stdout=log, stderr=log)
                if mp4.exists() and mp4.stat().st_size > 100_000:
                    ok = True
                    break
        log.close()
        if not ok:
            print("  DOWNLOAD FAIL", flush=True)
            failures.append({"id": vid, "stage": "download"})
            continue

        # ---- extract audio: 16k mono mp3（够小，能过 API 体积限制）----
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(mp4), "-vn", "-ar", "16000", "-ac", "1",
             "-b:a", "48k", str(mp3), "-loglevel", "error"], capture_output=True)
        mp4.unlink(missing_ok=True)
        if not mp3.exists() or mp3.stat().st_size < 10_000:
            print("  FFMPEG FAIL", flush=True)
            failures.append({"id": vid, "stage": "ffmpeg"})
            continue

        # ---- transcribe ----
        r = subprocess.run([AGENT_REACH, "transcribe", str(mp3), "-o", str(txt)],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=600)
        if txt.exists() and txt.stat().st_size > 50:
            header = f"# {date} https://www.douyin.com/video/{vid}\n# {v.get('desc') or ''}\n\n"
            txt.write_text(header + txt.read_text(encoding="utf-8", errors="replace"),
                           encoding="utf-8")
            print(f"  OK ({txt.stat().st_size} bytes)", flush=True)
        else:
            print(f"  TRANSCRIBE FAIL: {(r.stderr or r.stdout)[:120]}", flush=True)
            failures.append({"id": vid, "stage": "transcribe"})
        mp3.unlink(missing_ok=True)
        time.sleep(2)

    (DATA / "failures.json").write_text(
        json.dumps(failures, ensure_ascii=False, indent=1), encoding="utf-8")
    done = len(list(TRANS.glob("*.txt")))
    print(f"DONE: {done} transcripts, {len(failures)} failures", flush=True)
    return 0


# ============================================================ status
def cmd_status(args):
    """看一眼现在的登录态与数据现状。"""
    print(f"目录      {BASE}")
    print(f"profile   {PROFILE_DIR}  {'存在' if Path(PROFILE_DIR).exists() else '不存在'}")

    # profile 里的登录 cookie 要开浏览器才知道；这里只静态看文件，给个粗判
    ck = Path(PROFILE_DIR) / "Default" / "Cookies"
    print(f"Cookies   {ck}  {'存在' if ck.exists() else '不存在'}")

    def _count(pat, root=None):
        root = root or DATA
        if not root.exists():
            return 0, 0
        fs = list(root.glob(pat))
        return len(fs), sum(f.stat().st_size for f in fs)

    n, sz = _count("*.json")
    print(f"data/     {n} 个 json，{sz/1024:.0f} KB")
    for f in sorted(DATA.glob("*.json")):
        print(f"    {f.stat().st_size:>9,}  {f.name}")
    n = len(list(TRANS.glob("*.txt"))) if TRANS.exists() else 0
    print(f"transcripts/  {n} 个 txt")
    n = len(list(AUDIO.iterdir())) if AUDIO.exists() else 0
    print(f"audio/        {n} 个临时文件（正常应为 0）")

    print("\n子命令: login / posts / sample / video / transcribe / status")
    return 0


# ============================================================ main
def main():
    ap = argparse.ArgumentParser(
        prog="douyin.py",
        description="抖音采集工具（子命令式合一版）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("设计约定")[0],
    )
    sub = ap.add_subparsers(dest="cmd")

    p = sub.add_parser("login", help="扫码登录，存 browser_profile/")
    p.add_argument("--minutes", type=int, default=15, help="最长等待分钟数")
    p.set_defaults(func=cmd_login)

    p = sub.add_parser("posts", help="枚举账号全部作品")
    p.add_argument("sec_uid")
    p.add_argument("-o", "--out", help="输出 json（默认 data/video_list.json）")
    p.add_argument("--max-scroll", type=int, default=800, help="最多滚动轮数")
    p.add_argument("--keep-urls", action="store_true",
                   help="保留 play_url（默认删掉——签名 URL 几小时就过期，留着是误导）")
    p.set_defaults(func=cmd_posts)

    p = sub.add_parser("sample", help="按关键词采样文案")
    p.add_argument("keywords", nargs="+")
    p.add_argument("-o", "--out", help="输出 json（默认 data/douyin_samples.json）")
    p.add_argument("--mins", type=int, default=3, help="每个关键词滚动分钟数")
    p.add_argument("--headed", action="store_true", help="显示浏览器窗口")
    p.add_argument("--diag", action="store_true", help="打印诊断信息")
    p.set_defaults(func=cmd_sample)

    p = sub.add_parser("video", help="单视频过风控 + 导 cookie jar")
    p.add_argument("target", help="视频 URL 或 aweme_id")
    p.add_argument("--jar", help="cookie jar 输出路径（默认 data/douyin_cookies.txt）")
    p.add_argument("--headed", action="store_true", help="显示浏览器窗口")
    p.set_defaults(func=cmd_video)

    p = sub.add_parser("transcribe", help="批量下载转写（断点续跑）")
    p.add_argument("list", nargs="?", help="清单 json（默认 data/video_list.json）")
    p.set_defaults(func=cmd_transcribe)

    p = sub.add_parser("status", help="查看登录态与数据现状")
    p.set_defaults(func=cmd_status)

    args = ap.parse_args()
    if not args.cmd:
        ap.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
