#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""通用事件入库工具：自动按date选主层年段文件，查重后合并。
用法：python3 scripts/add_events.py batch.json  （batch.json为条目数组）
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EV = ROOT / "data" / "events"

# 主层年段（与dedup/build口径一致）
RANGES = [
    ("1970-1985.json", 1970, 1985),
    ("1986-1995.json", 1986, 1995),
    ("1996-1999.json", 1996, 1999),
    ("2000-2004.json", 2000, 2004),
    ("2005-2009.json", 2005, 2009),
    ("2010-2014.json", 2010, 2014),
    ("2015-2019.json", 2015, 2019),
    ("2020-2022.json", 2020, 2022),
    ("2023-2026.json", 2023, 2026),
]

def all_events():
    out = {}
    for f in EV.glob("*.json"):
        if f.name.startswith(".") or ".parts" in f.name:
            continue
        try:
            data = json.load(open(f, encoding="utf-8"))
        except Exception as exc:
            print(f"  ⚠ 跳过损坏文件 {f.name}: {exc}")
            continue
        for e in data:
            out[e["id"]] = (f.name, e)
    return out

def pick_file(date: str) -> str:
    year = int(date[:4])
    for name, lo, hi in RANGES:
        if lo <= year <= hi:
            return name
    raise ValueError(f"{date} 超出主层年段范围")

def main() -> int:
    if len(sys.argv) != 2:
        print("用法: python3 scripts/add_events.py <batch.json>"); return 2
    batch = json.load(open(sys.argv[1], encoding="utf-8"))
    inventory = all_events()
    # 查重：id冲突 / 同日标题字符重叠>60%
    by_date = {}
    for name, e in inventory.values():
        by_date.setdefault(e["date"], []).append(e["title"])
    added, skipped = 0, 0
    for e in batch:
        eid, date, title = e["id"], e["date"], e["title"].strip()
        if eid in inventory:
            print(f"  跳过(id冲突): {eid}"); skipped += 1; continue
        clash = False
        for t2 in by_date.get(date, []):
            if len(set(title) & set(t2)) / min(len(set(title)), len(set(t2))) > 0.6:
                print(f"  跳过(同日相似): {eid} ╌ {t2[:26]}"); clash = True; break
        if clash:
            skipped += 1; continue
        fname = pick_file(date)
        path = EV / fname
        d = json.load(open(path, encoding="utf-8"))
        d.append(e); d.sort(key=lambda x: x["date"])
        json.dump(d, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        by_date.setdefault(date, []).append(title)
        inventory[eid] = (fname, e)
        print(f"  ✓ {eid} → {fname}")
        added += 1
    print(f"入库 {added} 条，跳过 {skipped} 条")
    return 0

if __name__ == "__main__":
    sys.exit(main())
