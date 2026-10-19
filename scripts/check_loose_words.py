#!/usr/bin/env python3
"""全库杂字扫描：中文夹小写英文词检测。"""
import json
import glob
import re

pat = re.compile(r"[一-鿿『「]\s+([A-Za-z][A-Za-z0-9'-]{2,})\s+[一-鿿』」，。？！：]", re.I)
WHITE = {"SpaceX", "IMDb", "GitHub", "iPhone", "iPad", "iMac", "macOS", "iOS", "App", "Zoom"}
n = 0
for p in sorted(glob.glob("data/events/*.json")):
    if p.split("/")[-1].startswith("."):
        continue
    for x in json.load(open(p)):
        for f in ["summary_30s", "detail", "impact", "aftermath"]:
            t = x.get(f, "")
            for m in pat.finditer(t):
                w = m.group(1)
                if w not in WHITE and not w.isupper():
                    print(f"{p.split(chr(47))[-1]} {x['id']} [{f}] …{m.group(0)[:44]}…")
                    n += 1
print("杂字命中:", n)
