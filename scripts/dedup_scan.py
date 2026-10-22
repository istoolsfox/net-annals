#!/usr/bin/env python3
"""全库重复检测：同日近似标题 / 跨日同事件（标题高度重合）/ 关键词同事件。
输出可疑对供人工审查，不直接删除。用法：python3 scripts/dedup_scan.py"""
import glob, json, re, sys
from difflib import SequenceMatcher

def norm(t):
    return re.sub(r"[「」『』：:，,。（）()·、\s——\-]", "", t)

files = sorted(glob.glob("data/events/*.json"))
events = []
for f in files:
    for i, e in enumerate(json.load(open(f, encoding="utf-8"))):
        events.append((f.split("/")[-1].split("\\")[-1], i, e))

suspicious = []
seen_pairs = set()
for a in range(len(events)):
    fa, ia, ea = events[a]
    ta = norm(ea["title"])
    for b in range(a + 1, len(events)):
        fb, ib, eb = events[b]
        tb = norm(eb["title"])
        # 快速过滤：首字符不同且长度差大则跳过
        if abs(len(ta) - len(tb)) > 14 and not (ta[:4] == tb[:4]):
            continue
        ratio = SequenceMatcher(None, ta, tb).ratio()
        same_date = ea["date"] == eb["date"]
        if ratio >= 0.55 or (same_date and ratio >= 0.42):
            key = tuple(sorted([ea["id"], eb["id"]]))
            if key in seen_pairs:
                continue
            seen_pairs.add(key)
            suspicious.append((ratio, same_date, ea, eb, fa, ia, fb, ib))

suspicious.sort(key=lambda x: -x[0])
print(f"发现 {len(suspicious)} 对可疑重复：\n")
for ratio, same_date, ea, eb, fa, ia, fb, ib in suspicious:
    da, db_ = ea["date"], eb["date"]
    tag = "同日" if same_date else f"{da}/{db_}"
    keep_a = len(ea.get("detail", "")) >= len(eb.get("detail", ""))
    rec = f"  A={ea['title']}[{len(ea.get('detail',''))}字,{ea['date_confidence']}]@{fa}#{ia}"
    rec2 = f"  B={eb['title']}[{len(eb.get('detail',''))}字,{eb['date_confidence']}]@{fb}#{ib}"
    print(f"[{ratio:.2f}|{tag}] 建议{'删B保A' if keep_a else '删A保B'}")
    print(rec)
    print(rec2)
    print()
