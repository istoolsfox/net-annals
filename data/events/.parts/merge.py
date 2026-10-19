#!/usr/bin/env python3
# 把 .parts/part-*.json 合并进主文件（增量、幂等、原子写）
import json, os, glob, sys, tempfile

ROOT = "/Users/jintunda/Desktop/My Person/workspace/01-projects/net-annals/data/events"
MAIN = os.path.join(ROOT, "1986-2026-music.json")

with open(MAIN, encoding="utf-8") as f:
    data = json.load(f)
existing = {e["id"] for e in data}
added, consumed = 0, []
for p in sorted(glob.glob(os.path.join(ROOT, ".parts", "part-*.json"))):
    with open(p, encoding="utf-8") as f:
        part = json.load(f)
    for e in part:
        if e["id"] in existing:
            print("SKIP dup:", e["id"])
            continue
        data.append(e)
        existing.add(e["id"])
        added += 1
    consumed.append(p)

d = os.path.dirname(MAIN)
fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp.json")
with os.fdopen(fd, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=1)
os.replace(tmp, MAIN)
for p in consumed:
    os.remove(p)
print("total:", len(data), "| added:", added)
