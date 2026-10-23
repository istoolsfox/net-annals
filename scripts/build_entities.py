#!/usr/bin/env python3
"""世家构建：校验 data/entities/*.json（跳过 .parts/.extracts）→ 合并查重 →
site/entities/data.json + .gz
用法：python3 scripts/build_entities.py"""
import glob
import gzip
import json
import os
import re
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENT_DIR = os.path.join(ROOT, "data", "entities")
OUT_DIR = os.path.join(ROOT, "site", "entities")
ID_RE = re.compile(r"^[a-z0-9-]+$")

REQUIRED = ["id", "name", "type", "region", "founded", "founded_accuracy", "dissolved",
            "status", "headline", "summary_30s", "timeline", "milestones", "legacy", "sources", "tags"]

errors = []
files = sorted(p for p in glob.glob(os.path.join(ENT_DIR, "*.json")))
if not files:
    print("✗ data/entities/ 下没有正式 JSON（parts 请先验收合并）")
    sys.exit(1)

all_ents, seen_ids, seen_names = [], set(), {}
for f in files:
    try:
        data = json.load(open(f, encoding="utf-8"))
        if not isinstance(data, list):
            errors.append(f"{os.path.basename(f)}: 顶层不是数组，跳过")
            continue
    except json.JSONDecodeError as exc:
        errors.append(f"{os.path.basename(f)}: JSON 解析失败 {exc}")
        continue
    for e in data:
        eid = e.get("id", "")
        for k in REQUIRED:
            if k not in e:
                errors.append(f"{eid}: 缺字段 {k}")
        if eid in seen_ids:
            errors.append(f"id 重复: {eid}")
        if ID_RE.match(eid):
            nm = e.get("name", "")
            if nm in seen_names and seen_names[nm] != eid:
                errors.append(f"名称重复: {nm} ({seen_names[nm]} / {eid})")
            seen_names[nm] = eid
        seen_ids.add(eid)
        all_ents.append(e)

if errors:
    print(f"✗ 校验失败 {len(errors)} 项:")
    for x in errors:
        print("  -", x)
    sys.exit(1)

order = {"company": 0, "community": 1, "institution": 2}
all_ents.sort(key=lambda e: (order.get(e.get("type"), 9), e.get("founded", "9999")))
os.makedirs(OUT_DIR, exist_ok=True)
text = json.dumps({"generated": datetime.now().astimezone().isoformat(timespec="seconds"),
                   "count": len(all_ents), "entities": all_ents},
                  ensure_ascii=False, separators=(",", ":"))
dst = os.path.join(OUT_DIR, "data.json")
open(dst, "w", encoding="utf-8").write(text)
with open(dst + ".gz", "wb") as gf:
    with gzip.GzipFile(filename="", mode="wb", fileobj=gf, mtime=0, compresslevel=9) as g:
        g.write(text.encode("utf-8"))

by_type = {}
for e in all_ents:
    by_type[e["type"]] = by_type.get(e["type"], 0) + 1
print(f"✓ 世家构建完成：{len(all_ents)} 家 → site/entities/data.json（{os.path.getsize(dst)//1024}KB + .gz）")
print(f"  分布: {by_type}")

# 同步主站横幅世家数（根治静态数字过期）
_idx = os.path.join(ROOT, "site", "index.html")
try:
    _html = open(_idx, encoding="utf-8").read()
    _new = re.sub(r'(id="eCount">)\d+(<small>世家</small>)', rf'\g<1>{len(all_ents)}\g<2>', _html)
    if _new != _html:
        open(_idx, "w", encoding="utf-8").write(_new)
        print(f"  主站横幅 eCount → {len(all_ents)}")
except OSError:
    pass
