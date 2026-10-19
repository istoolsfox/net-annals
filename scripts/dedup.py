#!/usr/bin/env python3
"""跨文件去重：主年段文件优先，领域分层文件让位（文件名字典序即优先级）。
规则：
1) 隐藏文件（.开头，agent 备份/分片）一律跳过；
2) 文件内按 id 去重；
3) 跨文件：后处理文件中与已收条目 id 相同的删除；同日期+标题字符重叠 >60% 的删除；
4) 输出报告但不删「同事件不同表述」的疑似重复（留给人工/M2 复核）。
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EV = ROOT / "data" / "events"

def main() -> int:
    files = [f for f in sorted(EV.glob("*.json")) if not f.name.startswith(".")]
    main_files = [f for f in files if re.match(r"^\d{4}-\d{4}\.json$", f.name)]
    layer_files = [f for f in files if f not in main_files]
    pool: dict[str, dict] = {}              # id -> event（已收条目）
    titles: set[tuple[str, str]] = set()    # (date, title)（已收条目）
    removed = 0

    for f in main_files + layer_files:
        d = json.loads(f.read_text(encoding="utf-8"))
        seen: set[str] = set()
        out = []
        for e in d:
            dup = e["id"] in pool or e["id"] in seen \
                or (e["date"], e["title"].strip()) in titles
            if not dup:
                for (d2, t2) in titles:
                    if d2 != e["date"]:
                        continue
                    a, b = set(e["title"]), set(t2)
                    if len(a & b) / min(len(a), len(b)) > 0.6:
                        dup = True
                        print(f"  同日相似删除 {f.name}: {e['id']} ╌ {t2[:24]}")
                        break
            if dup:
                removed += 1
                print(f"  重复删除 {f.name}: {e['id']} {e.get('title','')}")
                continue
            seen.add(e["id"])
            pool[e["id"]] = e
            titles.add((e["date"], e["title"].strip()))
            out.append(e)
        f.write_text(json.dumps(out, ensure_ascii=False, indent=0), encoding="utf-8")

    all_ids = [e["id"] for f in files for e in json.loads(f.read_text(encoding="utf-8"))]
    dup = [k for k, v in Counter(all_ids).items() if v > 1]
    print(f"删除重复 {removed} 条；全库 {len(all_ids)} 条；剩余重复 {len(dup)}")
    for x in dup[:10]:
        print("  仍重复:", x)
    return 1 if dup else 0

if __name__ == "__main__":
    sys.exit(main())
