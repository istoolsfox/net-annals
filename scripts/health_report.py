#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""数据健康度报告：一条命令输出全库基线指标。
用法：python3 scripts/health_report.py
"""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def load_dir(pattern):
    out = []
    for f in sorted(ROOT.glob(pattern)):
        if ".parts" in str(f) or f.name.startswith("."): continue
        try:
            out.extend(json.load(open(f, encoding="utf-8")))
        except Exception as e:
            print(f"[JSON损坏] {f.name}: {e}")
    return out

def main():
    events = load_dir("data/events/*.json")
    persons = load_dir("data/persons/*.json")
    conf = Counter(e.get("date_confidence") for e in events)
    years = Counter(e["date"][:4] for e in events)
    cats = Counter(e["category"] for e in events)
    fields = Counter(p.get("field") for p in persons)

    # 地域
    geo_hits = 0
    try:
        g = json.load(open(ROOT / "site/geo/data.json"))
        geo_hits = g["stats"]["placesWithEvents"]
    except Exception:
        pass

    print("═══ net-annals 数据健康度 ═══")
    print(f"编年史: {len(events)} 条 | 里程碑 {sum(bool(e.get('milestone')) for e in events)}")
    v = conf.get("verified", 0)
    print(f"置信: verified {v} ({v/len(events):.1%}) / single-source {conf.get('single-source',0)} / uncertain {conf.get('uncertain',0)}")
    print(f"人物志: {len(persons)} 人 | 领域: {dict(fields.most_common())}")
    print(f"地域覆盖: {geo_hits} 个城市有内容")
    thin = sorted((y, c) for y, c in years.items() if c < 50)
    print(f"薄年(<50条): {thin}")
    print(f"分类: {dict(cats.most_common())}")
    # 提示
    if conf.get("single-source", 0) > 500:
        print(f"→ 待办: single-source {conf['single-source']} 条可继续补源")
    print("═══ 建议下一步见 ROADMAP.md ═══")

if __name__ == "__main__":
    main()
