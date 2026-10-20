#!/usr/bin/env python3
"""月度密度追踪：对照「每月 350 条」北极星，输出各年段达标情况。"""
import json, glob
from collections import Counter

TARGET = 350  # 北极星：每月条数

def main():
    mc = Counter()
    for f in sorted(glob.glob("data/events/*.json")):
        if "/." in f:
            continue
        for e in json.load(open(f)):
            mc[e["id"][:7]] += 1
    total = sum(mc.values())
    years = sorted({m[:4] for m in mc})
    print(f"全库 {total} 条 | 覆盖 {len(mc)}/488 个月 | 月均 {total/488:.1f}（北极星 {TARGET}）")
    print(f"{'年份':<6}{'条数':>7}{'月均':>8}{'达标率':>9}  密度条")
    for y in years:
        months = [mc.get(f"{y}-{m:02d}", 0) for m in range(1, 13)]
        n = sum(months)
        avg = n / 12
        rate = avg / TARGET * 100
        bar = "█" * int(rate / 4)
        print(f"{y:<6}{n:>7}{avg:>8.1f}{rate:>8.0f}%  {bar}")
    # 密度排行
    top = mc.most_common(5)
    print("\n最高月份:", ", ".join(f"{m}={c}" for m, c in top))

if __name__ == "__main__":
    main()
