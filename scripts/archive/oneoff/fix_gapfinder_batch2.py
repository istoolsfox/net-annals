#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""g_gapfinder_1 验收第二批（2026-10-26 跨月近重审计后的人工裁定）：
1) 弃收 36 条与库内正本重复的条目（含同日/跨日变体，逐一人工裁定）
2) 修库内三条发射日差一天的条目（原始采集 UTC/北京时间错位）：
   神舟一号 11-19→11-20、神舟二号 01-09→01-10、嫦娥三号 12-01→12-02
3) 同日共享≥6字子串的变体查重补扫（打印人工复核）
"""
import json, glob, re

PARTS = 'data/events/.parts/g_gapfinder_1.json'
DROPS = {
    '2021-05-07-china-international-consumer-',   # 消博会（库05-06开幕正本）
    '2021-04-01-seventh-census-2021',             # 七普（库05-11数据公布正本）
    '2010-08-08-zhouqu-mudslide-disaster',        # 舟曲（库08-07正本）
    '1999-11-20-shenzhou-1-launch',               # 神一（库正本，日期见第2项修正）
    '2003-04-29-xiaotangshan-sars-hospital',      # 小汤山（库04-30正本）
    '2004-08-02-guangzhou-baiyun-airport-new',    # 白云机场（库08-05启用正本）
    '2020-03-31-xichang-forest-fire-19-deaths',   # 西昌火（库03-30正本）
    '2002-02-17-yang-yang-first-winter-gold',     # 杨扬首金（库02-16正本）
    '2010-04-05-wangjialing-mine-rescue',         # 王家岭获救（库03-28正本含生还）
    '2002-09-28-loongson-first-cpu',              # 龙芯（库08-10流片正本）
    '2010-10-28-tianhe-1a-fastest-supercomput',   # 天河一号A（库11-14正本）
    '2001-01-10-shenzhou-2-launch',               # 神二（库正本，日期见第2项修正）
    '2019-04-01-muli-forest-fire',                # 木里（库03-30正本）
    '1991-11-01-first-womens-world-cup',          # 女足世界杯（库11-16开幕正本）
    '2013-12-02-change-3-launch',                 # 嫦三（库正本，日期见第2项修正）
    '2005-08-12-nanjing-metro-line1-opening',     # 南京地铁（库09-01通车正本）
    '2002-01-01-china-analog-network-shutdown',   # 模拟网关闭（库12-31正本）
    '2010-08-24-beijing-tibet-highway-mega-ja',   # 京藏堵车（库08-14正本）
    '1990-10-08-mcdonalds-first-shenzhen',        # 麦当劳首店（库同日正本，变体漏网）
    '2017-12-14-google-ai-china-lab',             # 谷歌AI中心（库12-13正本）
    '2021-10-12-china-first-national-parks',      # 首批国家公园（库同日正本）
    '2004-01-15-daolang-first-album-2002-snow',   # 刀郎（库01-01正本）
    '2008-05-24-telecom-restructure-announcem',   # 六合三（库05-23正本）
    '2023-05-13-sudirman-cup-2023-suzhou',        # 苏杯开赛（库05-21三连冠正本）
    '2004-08-27-liuxiang-110mh-gold-athens',      # 刘翔（库同日正本）
    '1989-01-03-gezhouba-completion',             # 葛洲坝（库88-12-10竣工正本）
    '2021-06-11-tianwen-1-mars-first-images',     # 天问影像（库05-15着陆正本）
    '2021-06-02-harmonyos-2-launch',              # 鸿蒙（库同日正本）
    '1987-04-30-yellow-river-drift-expedition',   # 黄河漂流（库04月正本）
    '2016-06-23-yancheng-tornado-disaster',       # 盐城龙卷（库同日正本）
    '2008-01-01-2008-china-ice-snow-disaster',    # 南方雪灾（库01-25正本）
    '1986-10-12-queen-elizabeth-ii-visit-chin',   # 英女王访华（库同日正本）
    '1998-08-28-guangshen-x2000-high-speed',      # 广深新时速（库同日正本）
    '2020-06-01-2020-south-china-floods',         # 2020南方水灾（库07-01正本）
    '2008-05-14-wenchuan-death-toll-update',      # 汶川伤亡更新（库国殇正本）
    '2001-07-13-beijing-wins-2008-olympics',      # 申奥成功（库同日正本）
}

es = json.load(open(PARTS, encoding='utf-8'))
kept, dropped = [], []
for e in es:
    if e['id'] in DROPS:
        dropped.append(e['id'])
        continue
    kept.append(e)
print(f'第2批弃收 {len(dropped)} 条，保留 {len(kept)} 条')

# ── 库内三条错一天日期修正 ──
FIXES = [
    ('神舟一号发射', '1999-11-19', '1999-11-20'),
    ('神舟二号发射', '2001-01-09', '2001-01-10'),
    ('嫦娥三号发射', '2013-12-01', '2013-12-02'),
]
for f in glob.glob('data/events/*.json'):
    if '/.' in f or '.parts' in f:
        continue
    arr = json.load(open(f, encoding='utf-8'))
    changed = False
    for e in arr:
        for kw, old, new in FIXES:
            if kw in e['title'] and e['date'] == old:
                print(f"  库修正: {f.split('/')[-1]} 「{e['title'][:30]}」 {old} → {new}")
                e['date'] = new
                if e['id'].startswith(old):
                    e['id'] = new + e['id'][len(old):]
                changed = True
    if changed:
        json.dump(arr, open(f, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

# ── 同日共享长子串变体补扫（只打印） ──
lib_by_day = {}
for f in glob.glob('data/events/*.json'):
    if '/.' in f or '.parts' in f:
        continue
    for e in json.load(open(f, encoding='utf-8')):
        lib_by_day.setdefault(e['date'][:10], []).append(e['title'])

def lcs(a, b):
    best, cur = 0, 0
    for i in range(len(a)):
        for j in range(len(b)):
            k = 0
            while i + k < len(a) and j + k < len(b) and a[i + k] == b[j + k]:
                k += 1
            best = max(best, k)
    return best

suspects = 0
for e in kept:
    for t in lib_by_day.get(e['date'][:10], []):
        if lcs(e['title'], t) >= 6:
            print(f'  ⚠同日子串: 「{e["title"][:24]}」 vs 「{t[:28]}」')
            suspects += 1
print(f'同日长子串嫌疑: {suspects}（人工复核）')

json.dump(kept, open(PARTS, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'→ {PARTS}: {len(kept)} 条')
