#!/usr/bin/env python3
"""通用查重工具：python3 scripts/precheck_dedup.py 关键词1 关键词2 ...
对 data/events/*.json 的 title 做模糊包含匹配，打印全部命中（防截断）。"""
import glob, json, sys

if len(sys.argv) < 2:
    print("用法: python3 scripts/precheck_dedup.py 关键词1 [关键词2 ...]")
    sys.exit(1)
kws = sys.argv[1:]
db = [(e["date"], e["title"]) for f in glob.glob("data/events/*.json") for e in json.load(open(f))]
found = False
for k in kws:
    hits = [(d, t) for d, t in db if k in t]
    print(f"== {k} ({len(hits)}):")
    for d, t in hits[:12]:
        print(f"   {d} {t}")
    if len(hits) > 12:
        print(f"   … 另 {len(hits)-12} 条")
    if hits:
        found = True
print("结论: " + ("部分关键词已有条目，注意避开/改写" if found else "全部关键词均无命中，可放心收录"))
