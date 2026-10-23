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
        if not isinstance(data, list):
            errors.append(f"{os.path.basename(f)}: 顶层不是数组，跳过")
            continue
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
# 全量校验（与 validate_group.py 同规则），不合格文件跳过并在下方警告，不带病上线。
GROUPS_DIR = os.path.join(PERSONS_DIR, "groups")
G_REQUIRED = ["id", "name", "era", "summary_30s", "members", "legacy", "sources", "tags"]
G_BLOCK = ["习近平", "李克强", "李强", "胡锦涛", "温家宝", "江泽民", "毛泽东", "邓小平", "周恩来",
           "朱镕基", "薄熙来", "周永康", "孙政才", "令计划", "彭丽媛", "栗战书", "汪洋", "王沪宁",
           "赵乐际", "韩正", "蔡奇", "丁薛祥", "李鹏", "华国锋", "林彪", "四人帮", "刘少奇",
           "特朗普", "拜登", "普京", "金正恩", "泽连斯基", "安倍", "莫迪", "埃尔多安"]
gfiles = sorted(glob.glob(os.path.join(GROUPS_DIR, "*.json")))
if gfiles:
    groups, gseen, gerrs, skipped = [], set(), [], []
    for f in gfiles:
        try:
            gdata = json.load(open(f, encoding="utf-8"))
        except json.JSONDecodeError as exc:
            skipped.append((f, [f"解析失败 {exc}"]))
            continue
        ferrs = []
        for g in gdata:
            gid = g.get("id", "")
            for k in G_REQUIRED:
                if k not in g:
                    ferrs.append(f"{gid or '?'}: 缺字段 {k}")
            if not str(gid).startswith("l-"):
                ferrs.append(f"{gid}: 类传 id 必须以 l- 开头")
            if gid in gseen:
                ferrs.append(f"{gid}: 类传 id 重复")
            gseen.add(gid)
            if not (60 <= len(str(g.get("summary_30s", ""))) <= 220):
                ferrs.append(f"{gid}: summary_30s 长度非法")
            members = g.get("members", [])
            if not (5 <= len(members) <= 9):
                ferrs.append(f"{gid}: members {len(members)}人（须5-9）")
            for m in members:
                if not (40 <= len(str(m.get("text", ""))) <= 160):
                    ferrs.append(f"{gid}·{m.get('name', '?')}: text 长度非法")
                elif not re.search(r"\d", str(m.get("text", ""))):
                    ferrs.append(f"{gid}·{m.get('name', '?')}: text 无数字")
                if not (0 < len(str(m.get("headline", ""))) <= 20):
                    ferrs.append(f"{gid}·{m.get('name', '?')}: headline 非法")
            if not str(g.get("legacy", "")).strip() or len(str(g.get("legacy", ""))) > 140:
                ferrs.append(f"{gid}: legacy 空或超140字")
            blob = json.dumps(g, ensure_ascii=False)
            for bad in G_BLOCK:
                if bad in blob:
                    ferrs.append(f"{gid}: 红线命中领导人姓名「{bad}」")
                    break
            srcs = g.get("sources", [])
            if len(srcs) < 3:
                ferrs.append(f"{gid}: sources <3条")
            gdomains = {re.sub(r"^https?://([^/]+).*", r"\1", str(s.get("url", ""))) for s in srcs if str(s.get("url", "")).startswith("http")}
            if len(gdomains) < 2:
                ferrs.append(f"{gid}: sources 域名 <2 种")
            tags = g.get("tags", [])
            if not (3 <= len(tags) <= 6):
                ferrs.append(f"{gid}: tags {len(tags)}个（须3-6）")
        if ferrs:
            skipped.append((f, ferrs))
            continue
        groups.extend(gdata)
    if skipped:
        print(f"⚠️ 类传不合格被跳过 {len(skipped)} 个文件（不带病上线，修复后移回）:")
        for f, errs in skipped:
            print(f"  - {os.path.basename(f)}: {len(errs)} 错，首错: {errs[0]}")
    if groups:
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
        print("· 无合格类传，跳过 groups.json")
else:
    print("· 类传目录为空，跳过 groups.json")
