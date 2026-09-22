# -*- coding: utf-8 -*-
"""拉取难拉罐罐 B站投稿列表 (wbi 签名)"""
import hashlib, json, time, urllib.parse
from pathlib import Path
import requests

MID = 32742858
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
TAB = [46,47,18,2,53,8,23,32,15,50,10,31,58,3,45,35,27,43,5,49,33,9,42,19,29,28,
       14,39,12,38,41,13,37,48,7,16,24,55,40,61,26,17,0,1,60,51,30,4,22,25,54,
       21,56,59,6,63,57,62,11,36,20,34,44,52]

s = requests.Session()
s.headers.update({"User-Agent": UA, "Referer": f"https://space.bilibili.com/{MID}"})

nav = s.get("https://api.bilibili.com/x/web-interface/nav", timeout=10).json()
img = nav["data"]["wbi_img"]["img_url"].rsplit("/", 1)[1].split(".")[0]
sub = nav["data"]["wbi_img"]["sub_url"].rsplit("/", 1)[1].split(".")[0]
mixin = "".join((img + sub)[i] for i in TAB)[:32]

def signed(params):
    params = {**params, "wts": int(time.time())}
    q = urllib.parse.urlencode(sorted(params.items()))
    params["w_rid"] = hashlib.md5((q + mixin).encode()).hexdigest()
    return params

rows, pn = [], 1
while pn <= 6:
    try:
        r = s.get("https://api.bilibili.com/x/space/wbi/arc/search",
                  params=signed({"mid": MID, "ps": 30, "pn": pn, "order": "pubdate"}),
                  timeout=10).json()
    except Exception as e:
        print(f"page {pn}: blocked ({e.__class__.__name__}), stop")
        break
    vs = ((r.get("data") or {}).get("list") or {}).get("vlist") or []
    if not vs:
        break
    rows += vs
    print(f"page {pn}: +{len(vs)}", flush=True)
    pn += 1
    time.sleep(2.5)

out = Path(__file__).resolve().parents[1] / "outputs" / "reports" / "nankraguan_bili_videos.json"
out.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"total {len(rows)} videos -> {out}")
for v in rows[:40]:
    print(f"- {v['created']:.0f} | {v['play']:>8} 播放 | {v['length']:>6} | {v['title'][:55]}")
