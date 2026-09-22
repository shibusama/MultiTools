"""提取教程类视频的完整信息 + 下载链接，供转写"""
import json
import os

p = r"D:\C_Relocated\Users\13191\MultiTools\skills\douyin-collect\data\douyin_samples.json"
data = json.load(open(p, encoding="utf-8"))
items = data if isinstance(data, list) else data.get("items", [])

# 精准筛选真教程：含建模/动画/blender/maya/nomad 等工具词
TOOLS = ["blender", "maya", "c4d", "nomad", "ue5", "虚幻", "zbrush",
         "建模", "绑定", "渲染", "三渲二", "动画教程", "手办"]
SKIP = ["手游", "安装", "下载", "攻略", "穿搭", "日语", "钩织", "美食",
        "绘画教程", "我的世界", "桌宠", "桌面宠物", "deepseek"]

found = []
for it in items:
    d = (it.get("desc") or "")
    dl = d.lower()
    if any(s in dl for s in SKIP):
        continue
    hits = [t for t in TOOLS if t in dl]
    if hits:
        a = it.get("author")
        name = a.get("nickname", "") if isinstance(a, dict) else str(a)
        st = it.get("stats") or {}
        found.append({
            "id": it.get("aweme_id"),
            "desc": d,
            "author": name,
            "digg": st.get("digg_count", 0),
            "dur_ms": it.get("duration_ms", 0),
            "tools": hits,
            "play_url": it.get("play_url", ""),
        })

found.sort(key=lambda x: -x["digg"])
print(f"=== 真·3D 教学视频: {len(found)} 条 ===\n")
for f in found:
    sec = f["dur_ms"] / 1000
    print(f"[{f['digg']:>6}赞 {sec:>6.1f}s] @{f['author']}")
    print(f"    {f['desc'][:80]}")
    print(f"    工具: {', '.join(f['tools'])}")
    print(f"    id: {f['id']}")
    print()

# 保存
out = r"D:\C_Relocated\Users\13191\MultiTools\projects\chiikawa\douyin_tutorials.json"
json.dump(found, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"已保存: {out}")
