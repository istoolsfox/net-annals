#!/usr/bin/env python3
"""开工体检：并行会话在场检测 + 车道占用报告。用法：python3 scripts/lane_check.py
规则详见 docs/COLLABORATION.md"""
import os
import subprocess
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LANES = {
    "A·编年数据": ["data/events/", "site/data/", "site/geo/", "data/persons/", "data/wiki_raw/", "scripts/batch_"],
    "B·世家栏目基建": ["data/entities/", "site/entities/", "site/today/", "data/persons/groups/", "site/assets/", "scripts/entity_extract", "scripts/validate_entity", "scripts/build_entities", "scripts/build_today", "scripts/make_og"],
}
SHARED = ["PROGRESS.md", "ROADMAP.md", "site/index.html", "scripts/deploy.sh", "scripts/build.py",
          "ENTITIES_SPEC.md", "PERSONS_SPEC.md", "site/persons/index.html", "scripts/build_persons.py"]


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def lane_of(path):
    for lane, prefixes in LANES.items():
        if any(path.startswith(p) or p in path for p in prefixes):
            return lane
    for s in SHARED:
        if path.startswith(s) or path == s:
            return "共享区"
    return "其他"


def main():
    now = datetime.now()
    print("═" * 56)
    print("开工体检 · 并行会话在场检测")
    print("═" * 56)

    # 1. 最近提交（对方心跳）
    lines = git("log", "-5", "--format=%ad%x09%s", "--date=format:%H:%M").splitlines()
    print("\n【最近提交】")
    alert = False
    for ln in lines:
        t, msg = ln.split("\t", 1)
        hh, mm = map(int, t.split(":"))
        dmin = (now.hour * 60 + now.minute) - (hh * 60 + mm)
        flag = ""
        if 0 <= dmin < 30:
            flag = "  ⚠️ 对方可能在场"
            alert = True
        print(f"  {t} ({dmin:>4}分钟前) {msg[:44]}{flag}")
    if alert:
        print("  → 最近 30 分钟有提交，开工前确认对方车道，必要时换工作面")
    else:
        print("  → 30 分钟内无提交，暂无在场迹象（不代表没人，可能是交互会话）")

    # 2. 未提交文件按车道分组
    status = git("status", "--porcelain").splitlines()
    groups = {}
    for ln in status:
        path = ln[2:].strip().strip('"')
        st = ln[:2].strip() or "??"
        groups.setdefault(lane_of(path), []).append(st + " " + path)
    print("\n【未提交文件按车道】")
    danger = []
    for lane in list(LANES) + ["共享区", "其他"]:
        files = groups.get(lane, [])
        if not files:
            continue
        print(f"  {lane}: {len(files)} 个")
        for f in files[:6]:
            print(f"     {f[:70]}")
        if len(files) > 6:
            print(f"     … 共 {len(files)} 个")
        if lane == "共享区" and files:
            danger.append("共享区有未提交改动——提交前重读最新版，小步快改立刻提交")

    # 3. 结论
    print("\n【结论】")
    if alert and any(g.get("A·编年数据") for g in [groups]):
        print("  ⚠️ 对方在场且 A 车道有 WIP：避开 A 车道，或只做 B 车道/自建新栏目")
    elif alert:
        print("  ⚠️ 对方近 30 分钟在场：遵守车道表与定点 add，共享区最小窗口")
    else:
        print("  ✓ 暂无冲突迹象：按车道表开工，遵守五条法则（docs/COLLABORATION.md）")
    for d in danger:
        print("  ⚠️", d)
    return 0


if __name__ == "__main__":
    sys.exit(main())
