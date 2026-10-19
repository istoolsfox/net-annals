#!/usr/bin/env python3
"""跨文件去重：主年段文件优先，-tech 分层文件让位。
规则：
1) 文件内按 id 去重；
2) 跨文件：-tech 文件中与主文件 id 相同的条目删除；同日期+标题完全相同的也删除；
3) 输出报告但不删「同事件不同表述」的疑似重复（留给人工/M2 复核）。
"""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EV = ROOT / "data" / "events"

def main() -> int:
    files = sorted(EV.glob("*.json"))
    main_files = [f for f in files if "-tech" not in f.name]
    tech_files = [f for f in files if "-tech" in f.name]
    pool: dict[str, dict] = {}   # id -> event (来自主文件)
    titles: set[tuple[str, str]] = set()
    removed = 0

    for f in main_files:
        d = json.loads(f.read_text(encoding="utf-8"))
        seen: set[str] = set()
        out = []
        for e in d:
            if e["id"] in seen:
                removed += 1
                print(f"  文件内重复删除 {f.name}: {e['id']}")
                continue
            seen.add(e["id"])
            pool[e["id"]] = e
            titles.add((e["date"], e["title"].strip()))
            out.append(e)
        f.write_text(json.dumps(out, ensure_ascii=False, indent=0), encoding="utf-8")

    for f in tech_files:
        d = json.loads(f.read_text(encoding="utf-8"))
        seen: set[str] = set()
        out = []
        for e in d:
            dup = (e["id"] in pool or (e["date"], e["title"].strip()) in titles or e["id"] in seen)
            if dup:
                removed += 1
                print(f"  与主文件重复删除 {f.name}: {e['id']} {e.get('title','')}")
                continue
            seen.add(e["id"])
            out.append(e)
        f.write_text(json.dumps(out, ensure_ascii=False, indent=0), encoding="utf-8")

    # 全库 id 唯一性终检
    all_ids = []
    for f in files:
        all_ids += [e["id"] for e in json.loads(f.read_text(encoding="utf-8"))]
    dup = [k for k, v in Counter(all_ids).items() if v > 1]
    print(f"删除重复 {removed} 条；全库 {len(all_ids)} 条；剩余重复 {len(dup)}")
    for x in dup[:10]:
        print("  仍重复:", x)
    return 1 if dup else 0

if __name__ == "__main__":
    sys.exit(main())
