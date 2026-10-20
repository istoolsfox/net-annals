#!/usr/bin/env python3
"""全库杂字扫描：中文夹小写英文词检测。"""
import json
import glob
import re

pat = re.compile(r"[一-鿿『「]\s+([A-Za-z][A-Za-z0-9'-]{2,})\s+[一-鿿』」，。？！：]", re.I)
WHITE = {"SpaceX", "IMDb", "GitHub", "iPhone", "iPad", "iMac", "macOS", "iOS", "App", "Zoom", "eBay", "ofo", "ispace", "nWo", "xilin", "bilibili", "rVSV-ZEBOV", "mRNA", "token", "dearMoon", "dot-com", "Gram", "Fanatical", "HiRISE", "Self-Instruct", "meme", "iCloud", "iFactory"}
n = 0
for p in sorted(glob.glob("data/events/*.json")):
    if p.split("/")[-1].startswith("."):
        continue
    for x in json.load(open(p)):
        for f in ["summary_30s", "detail", "impact", "aftermath"]:
            t = x.get(f, "")
            for m in pat.finditer(t):
                w = m.group(1)
                # 全大写=缩写（mRNA/CERN），首字母大写=专有名词（Meta/Netflix），均豁免；
                # 只报全小写英文词——真正卡在中文句子里的杂字（run/talks/hydrant）
                if w not in WHITE and not w.isupper() and not w[0].isupper():
                    print(f"{p.split(chr(47))[-1]} {x['id']} [{f}] …{m.group(0)[:44]}…")
                    n += 1
print("杂字命中:", n)
