---
name: douyin-collect
description: Use when collecting Douyin data in this repo — 扫码登录抖音, 枚举账号作品, 按关键词采样文案, 给 yt-dlp 刷 cookie, or when video-to-transcript is blocked by Douyin captcha. Not for Bilibili.
---

# 抖音采集

拦网页接口拿文案/列表/cookie，**默认不下载视频**。脚本：

```bash
python 解析大全/采集/douyin/douyin.py <子命令>
```

路径都相对该文件，产物在 `解析大全/采集/douyin/data/`，登录态在同级 `browser_profile/`。不要动 `browser_profile` 当普通文件夹删。

## Hard rules

- 必须有头浏览器。`login` / `posts` 已经强制有头。`sample` 和 `video` **每次都加 `--headed`**（脚本默认无头，无头必出验证码）。
- 登录 cookie 只认 `sessionid` / `sessionid_ss` / `sid_tt` / `uid_tt`。不要把 `passport_csrf_token` 当已登录（访客也有）。
- `sample` **一次一个关键词、一个进程**。多个词塞进同一次会在大约第 4 个词死掉。两次之间隔 25–30 秒。
- 采样若得到大约 18 条一模一样的推荐流，当失败，不是「样本少」。重开有头窗口或先 `login`。
- `play_url` 几小时过期。`posts` 默认删掉它。要立刻转写才加 `--keep-urls`，并马上转，不要存着以后下。

## 子命令

| 要做的事 | 命令 |
|---|---|
| 扫码登录（只需一次） | `python 解析大全/采集/douyin/douyin.py login` |
| 看登录态和已有 json | `... status` |
| 枚举某账号全部作品 | `... posts <sec_uid>` |
| 按关键词采文案（不下载） | `... sample 历史 --mins 3 --headed` |
| 单条过风控 + 导出 cookie jar | `... video <链接或 aweme_id> --headed` |
| 清单批量 Groq 转写 | `... transcribe [list.json]` |

`video` 写出的 jar 默认 `data/douyin_cookies.txt`，给本仓库 `video-to-transcript` 用。

## 分流

| 用户说 | 走 |
|---|---|
| 采文案 / 拉账号作品 / 登录 / 刷 cookie | 本技能 |
| 已经有一条抖音链接，只要文字稿 | `video-to-transcript`（风控再回来跑 `video --headed`） |
| B 站 | `bili-local-transcribe` |

## Common mistakes

| 错法 | 正法 |
|---|---|
| `sample` / `video` 不带 `--headed` | 加上 |
| 一次 `sample 历史 科技 教育` | 三个进程，各一个词 |
| 把 `data/*.json` 当可复用下载源 | 签名 URL 已死；文案字段还能用 |
| 无头 Playwright / requests 硬爬 | 用这个脚本的有头拦截 |
