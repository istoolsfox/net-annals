#!/usr/bin/env python3
"""合并 .parts 中的新条目到主文件 1986-2026-film.json（原子写回，不覆盖已有 id）。"""
import json, os, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # data/events/.parts -> data/events
MAIN = os.path.join(BASE, "1986-2026-film.json")
PARTS_DIR = os.path.dirname(os.path.abspath(__file__))

def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def validate(items, existing_ids):
    errs = []
    seen = set()
    for e in items:
        i = e.get("id", "")
        if not i:
            errs.append(f"缺少 id: {e}")
            continue
        if i in existing_ids:
            errs.append(f"id 重复: {i}")
        if i in seen:
            errs.append(f"批次内 id 重复: {i}")
        seen.add(i)
        d = e.get("date", "")
        if not i.startswith(d):
            errs.append(f"id 前缀与 date 不一致: {i} vs {d}")
        for key in ("date_accuracy", "date_confidence", "title", "category", "region",
                    "milestone", "summary_30s", "detail", "impact", "aftermath", "sources"):
            if key not in e:
                errs.append(f"{i} 缺字段 {key}")
        sl = len(e.get("summary_30s", ""))
        if not (60 <= sl <= 220):
            errs.append(f"{i} summary_30s 长度异常: {sl}")
        dl = len(e.get("detail", ""))
        if not (150 <= dl <= 700):
            errs.append(f"{i} detail 长度异常: {dl}")
    return errs

def main():
    main_data = load(MAIN)
    existing_ids = {e["id"] for e in main_data}
    added = []
    for part in sys.argv[1:]:
        p = os.path.join(PARTS_DIR, part) if not os.path.isabs(part) else part
        items = load(p)
        errs = validate(items, existing_ids)
        if errs:
            print("校验失败：")
            for e in errs:
                print(" -", e)
            sys.exit(1)
        added.extend(items)
        existing_ids.update(e["id"] for e in items)
    main_data.extend(added)
    tmp = MAIN + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(main_data, f, ensure_ascii=False, indent=1)
    os.replace(tmp, MAIN)
    print(f"新增 {len(added)} 条，主文件现共 {len(main_data)} 条")

if __name__ == "__main__":
    main()
