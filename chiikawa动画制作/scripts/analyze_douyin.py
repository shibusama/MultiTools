"""分析抖音 chiikawa 采样数据"""
import json
import os
import re
from collections import Counter

p = r"D:\C_Relocated\Users\13191\MultiTools\skills\douyin-collect\data\douyin_samples.json"
data = json.load(open(p, encoding="utf-8"))

items = data if isinstance(data, list) else data.get("items", data.get("data", []))
print(f"总条数: {len(items)}")

# 看第一条结构
if items:
    print(f"\n字段: {list(items[0].keys())}")

def get(it, *keys):
    for k in keys:
        v = it.get(k)
        if v:
            return v
    return ""

rows = []
for it in items:
    desc = get(it, "desc", "title", "text")
    author = ""
    a = it.get("author")
    if isinstance(a, dict):
        author = a.get("nickname", "")
    elif isinstance(a, str):
        author = a
    stats = it.get("statistics") or it.get("stats") or {}
    digg = stats.get("digg_count", 0) if isinstance(stats, dict) else 0
    dur = it.get("duration") or it.get("duration_ms") or 0
    aid = get(it, "aweme_id", "id")
    rows.append({"desc": desc, "author": author, "digg": digg,
                 "dur": dur, "id": aid})

# 去重
seen = set()
uniq = []
for r in rows:
    if r["id"] and r["id"] not in seen:
        seen.add(r["id"])
        uniq.append(r)
print(f"去重后: {len(uniq)}")

# 按关键词分类
tut_kw = ["教程", "教学", "怎么做", "如何", "步骤", "流程", "blender", "建模",
          "绑定", "渲染", "三渲二", "分享", "学习", "入门", "干货"]
anim_kw = ["动画", "短剧", "小剧场", "整活", "二创", "自制"]

tuts, anims, others = [], [], []
for r in uniq:
    d = (r["desc"] or "").lower()
    if any(k in d for k in tut_kw):
        tuts.append(r)
    elif any(k in d for k in anim_kw):
        anims.append(r)
    else:
        others.append(r)

print(f"\n=== 教程类: {len(tuts)} 条 ===")
for r in sorted(tuts, key=lambda x: -(x["digg"] or 0))[:20]:
    dur = r["dur"]
    ds = f"{dur/1000:.0f}s" if dur and dur > 1000 else f"{dur}s"
    print(f"  [{r['digg']:>7}赞 {ds:>5}] @{r['author'][:14]:14s} {r['desc'][:52]}")

print(f"\n=== 动画/二创类: {len(anims)} 条 ===")
for r in sorted(anims, key=lambda x: -(x["digg"] or 0))[:15]:
    dur = r["dur"]
    ds = f"{dur/1000:.0f}s" if dur and dur > 1000 else f"{dur}s"
    print(f"  [{r['digg']:>7}赞 {ds:>5}] @{r['author'][:14]:14s} {r['desc'][:52]}")

print(f"\n=== 作者分布 (TOP15) ===")
for a, c in Counter(r["author"] for r in uniq if r["author"]).most_common(15):
    print(f"  {c:>3} 条  @{a}")

# 工具关键词命中统计
print(f"\n=== 工具/软件提及次数 ===")
alltext = " ".join((r["desc"] or "").lower() for r in uniq)
for tool in ["blender", "c4d", "maya", "ue5", "虚幻", "unity", "nomad",
             "ai", "即梦", "可灵", "三渲二", "绑定", "建模", "渲染",
             "教程", "动画"]:
    n = alltext.count(tool)
    if n:
        print(f"  {tool:>8}: {n}")
