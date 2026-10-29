#!/usr/bin/env python3
"""统一合并所有子Agent产出的 parts（auto_*.json）：
全库 id+标题相似查重 → 按条目日期年段分流到主层 → 排序原子写回。
用法：python3 scripts/merge_auto_parts.py
"""
import glob, json, os, re, sys

BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "events")
PARTS = sorted(glob.glob(os.path.join(BASE, ".parts", "auto_*.json")))
if not PARTS:
    print("没有找到 auto_*.json parts")
    sys.exit(1)

def year_file(y):
    if y <= 1985: return "1970-1985.json"
    if y <= 1995: return "1986-1995.json"
    if y <= 1999: return "1996-1999.json"
    if y <= 2004: return "2000-2004.json"
    if y <= 2009: return "2005-2009.json"
    if y <= 2014: return "2010-2014.json"
    if y <= 2019: return "2015-2019.json"
    if y <= 2022: return "2020-2022.json"
    return "2023-2026.json"

# 全库既有 id 与「标题去掉标点的归一化」集合
all_files = glob.glob(os.path.join(BASE, "*.json"))
db_index = {}   # file -> list
id_set, title_set = set(), set()
for f in all_files:
    data = json.load(open(f, encoding="utf-8"))
    db_index[os.path.basename(f)] = data
    for e in data:
        id_set.add(e["id"])
        title_set.add(re.sub(r"[「」『』：:，,。（）()·\s]", "", e["title"]))

def similar_title(t):
    return re.sub(r"[「」『』：:，,。（）()·\s]", "", t) in title_set

buckets = {}
added, skipped_dup, dropped = 0, 0, 0
for p in PARTS:
    prov = os.path.basename(p).replace("auto_", "").replace(".json", "")
    items = json.load(open(p, encoding="utf-8"))
    keep = []
    for e in items:
        if e["date"][:4] < "1972":
            dropped += 1
            print(f"[{prov}] 早于1972超段丢弃: {e['id']} {e['title']}")
            continue
        if e["id"] in id_set:
            skipped_dup += 1
            print(f"[{prov}] id 重复跳过: {e['id']}")
            continue
        if similar_title(e["title"]):
            skipped_dup += 1
            print(f"[{prov}] 标题相似跳过: {e['title']}")
            continue
        y = int(e["date"][:4])
        buckets.setdefault(year_file(y), []).append(e)
        id_set.add(e["id"])
        title_set.add(re.sub(r"[「」『』：:，,。（）()·\s]", "", e["title"]))
        keep.append(e["id"])
    print(f"[{prov}] 保留 {len(keep)}/{len(items)} 条")
    added += len(keep)

total = 0
for fname, items in sorted(buckets.items()):
    db = db_index.setdefault(fname, [])
    db.extend(items)
    db.sort(key=lambda e: e["date"])
    path = os.path.join(BASE, fname)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)
    print(f"{fname}: +{len(items)} -> {len(db)}条")
    total += len(items)
print(f"TOTAL added={total} skipped={skipped_dup}")
