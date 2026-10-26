#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""缺口配置导出器：把覆盖诊断变成 n8n 工作流 B（缺口定向搜索）可读的 JSON。
用法: python3 scripts/gap_config.py
产出: data/derived/gap_config.json —— 薄年/薄月/薄层/薄省 + 检索词模板
每轮扩库入库后重跑一次，与 library_index.json 一起 rsync 到 n8n 服务器。"""
import json, glob, os, datetime
from collections import Counter

# ── 年/月计数 ──
ym = Counter()
for f in glob.glob('data/events/*.json'):
    if '/.' in f or '.parts' in f:
        continue
    for e in json.load(open(f, encoding='utf-8')):
        ym[e['date'][:7]] += 1
years = Counter()
for m, n in ym.items():
    years[m[:4]] += n
med = sorted(years.values())[len(years) // 2]
thin_years = [{'year': y, 'count': n, 'month_avg': round(n / 12, 1)}
              for y, n in sorted(years.items()) if n < med * 0.7]
thin_months = sorted(((m, n) for m, n in ym.items()
                      if int(m[:4]) >= 1986 and n < 6), key=lambda x: x[1])[:30]

# ── 薄层（领域层条数 < 20；主层除外）──
MAIN = {'1986-1995', '1996-1999', '2000-2004', '2005-2009',
        '2010-2014', '2015-2019', '2020-2022', '2023-2026'}
layer_cnt = Counter()
for f in glob.glob('data/events/*.json'):
    if '/.' in f or '.parts' in f:
        continue
    stem = os.path.basename(f)[:-5]
    layer = '主层' if stem in MAIN else stem.split('-', 3)[-1]
    layer_cnt[layer] += sum(1 for _ in json.load(open(f, encoding='utf-8')))
thin_layers = [{'layer': l, 'count': n}
               for l, n in sorted(layer_cnt.items(), key=lambda x: x[1]) if n < 20]

# ── 薄省（按省聚合事件数：ev 地点码前两位=省码；直辖市事件集中在市区，
#    用地点数会严重失真，故主口径=事件数，地点数仅参考）──
thin_provinces = []
try:
    g = json.load(open('site/geo/data.json'))
    prov_names = {p[0]: p[1] for p in g['p']}
    ev_n, place_n = Counter(), Counter()
    for code, lst in g['ev'].items():
        prov = str(code)[:2]
        ev_n[prov] += len(lst)
        place_n[prov] += 1
    for code, name in prov_names.items():
        n = ev_n.get(code, 0)
        if n <= 40:
            thin_provinces.append({'province': name, 'events': n,
                                   'places': place_n.get(code, 0)})
    thin_provinces.sort(key=lambda x: x['events'])
except Exception as e:
    print(f'[warn] 薄省统计跳过: {e}')

cfg = {
    'generated_at': datetime.datetime.now().isoformat(timespec='seconds'),
    'library_total': sum(years.values()),
    'thin_years': thin_years,
    'thin_months': thin_months,
    'thin_layers': thin_layers,
    'thin_provinces': thin_provinces[:15],
    'query_templates': [
        '{year}年 中国 大事记',
        '{year}年 {domain} 里程碑 首次',
        '{province} 历史 大事 改革开放 里程碑',
    ],
}
os.makedirs('data/derived', exist_ok=True)
json.dump(cfg, open('data/derived/gap_config.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print(f"→ data/derived/gap_config.json: 薄年{len(thin_years)} 薄月{len(thin_months)} "
      f"薄层{len(thin_layers)} 薄省{len(thin_provinces[:15])}")