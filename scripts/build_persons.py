#!/usr/bin/env python3
"""人物志构建：校验 data/persons/*.json → 合并去重 → site/persons/data.json + .gz + persons-index.json
用法：python3 scripts/build_persons.py"""
import glob
import gzip
import json
import os
import re
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PERSONS_DIR = os.path.join(ROOT, "data", "persons")
OUT_DIR = os.path.join(ROOT, "site", "persons")
ID_RE = re.compile(r"^[a-z0-9-]+$")

REQUIRED = ["id", "name", "birth", "birth_accuracy", "death", "field", "region",
            "headline", "summary_30s", "timeline", "achievements", "sources", "tags"]

errors = []
files = sorted(p for p in glob.glob(os.path.join(PERSONS_DIR, "*.json")))
if not files:
    print("✗ data/persons/ 下没有 JSON")
    sys.exit(1)

all_persons, seen_ids, seen_names = [], set(), {}
for f in files:
    try:
        data = json.load(open(f, encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"{os.path.basename(f)}: JSON 解析失败 {exc}")
        continue
    for e in data:
        pid = e.get("id", "")
        for k in REQUIRED:
            if k not in e:
                errors.append(f"{pid}: 缺字段 {k}")
        if pid in seen_ids:
            errors.append(f"id 重复: {pid}")
        if ID_RE.match(pid):
            nm = e.get("name", "")
            if nm in seen_names and seen_names[nm] != pid:
                errors.append(f"姓名重复: {nm} ({seen_names[nm]} / {pid})")
            seen_names[nm] = pid
        seen_ids.add(pid)
        all_persons.append(e)

if errors:
    print(f"✗ 校验失败 {len(errors)} 项:")
    for x in errors:
        print("  -", x)
    sys.exit(1)

all_persons.sort(key=lambda e: e.get("birth", "9999"))
os.makedirs(OUT_DIR, exist_ok=True)
text = json.dumps({"generated": datetime.now().astimezone().isoformat(timespec="seconds"),
                   "count": len(all_persons), "persons": all_persons},
                  ensure_ascii=False, separators=(",", ":"))
dst = os.path.join(OUT_DIR, "data.json")
open(dst, "w", encoding="utf-8").write(text)
with open(dst + ".gz", "wb") as gf:
    with gzip.GzipFile(filename="", mode="wb", fileobj=gf, mtime=0, compresslevel=9) as g:
        g.write(text.encode("utf-8"))

fields = {}
for e in all_persons:
    fields[e["field"]] = fields.get(e["field"], 0) + 1
print(f"✓ 人物志构建完成：{len(all_persons)} 人 → site/persons/data.json（{os.path.getsize(dst)//1024}KB + .gz）")
print(f"  领域分布: {fields}")

# ---- 类传（群像列传）构建：data/persons/groups/*.json → site/persons/groups.json ----
GROUPS_DIR = os.path.join(PERSONS_DIR, "groups")
G_REQUIRED = ["id", "name", "era", "summary_30s", "members", "legacy", "sources", "tags"]
gfiles = sorted(glob.glob(os.path.join(GROUPS_DIR, "*.json")))
if gfiles:
    groups, gseen, gerrs = [], set(), []
    for f in gfiles:
        try:
            gdata = json.load(open(f, encoding="utf-8"))
        except json.JSONDecodeError as exc:
            gerrs.append(f"{os.path.basename(f)}: 解析失败 {exc}")
            continue
        for g in gdata:
            gid = g.get("id", "")
            for k in G_REQUIRED:
                if k not in g:
                    gerrs.append(f"{gid}: 缺字段 {k}")
            if not str(gid).startswith("l-"):
                gerrs.append(f"{gid}: 类传 id 必须以 l- 开头")
            if gid in gseen:
                gerrs.append(f"类传 id 重复: {gid}")
            gseen.add(gid)
            if len(g.get("members", [])) < 5:
                gerrs.append(f"{gid}: members <5")
            groups.append(g)
    if gerrs:
        print(f"✗ 类传校验失败 {len(gerrs)} 项:")
        for x in gerrs:
            print("  -", x)
        sys.exit(1)
    gtext = json.dumps({"generated": datetime.now().astimezone().isoformat(timespec="seconds"),
                        "count": len(groups), "groups": groups},
                       ensure_ascii=False, separators=(",", ":"))
    gdst = os.path.join(OUT_DIR, "groups.json")
    open(gdst, "w", encoding="utf-8").write(gtext)
    with open(gdst + ".gz", "wb") as gf:
        with gzip.GzipFile(filename="", mode="wb", fileobj=gf, mtime=0, compresslevel=9) as g:
            g.write(gtext.encode("utf-8"))
    print(f"✓ 类传构建完成：{len(groups)} 篇 → site/persons/groups.json（{os.path.getsize(gdst)//1024}KB + .gz）")
else:
    print("· 类传目录为空，跳过 groups.json")
