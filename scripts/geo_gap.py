#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""地域缺口队列导出器：单位×年密度矩阵 → data/derived/geo_gap.json
用法: python3 scripts/geo_gap.py
产出（分层北极星口径，详见 docs/GEO_PLAN.md）:
  cities.zero    零事件地级市（P1 首批队列，剔除直辖市区/辖县行）
  cities.thin    总量 <30 的城市（P1 加厚队列）
  counties.priority_zero   县级市零事件（P2 首批队列）
  counties.priority_sparse 县级市 <5 条（P2 加厚队列）
  stats          覆盖总账
每批入库后重跑一次；与 gap_config.json 一起 rsync 到 n8n 服务器供工作流 B 消费。"""
import json, glob
from collections import Counter, defaultdict

places = json.load(open('data/places.json'))
index = json.load(open('data/geo_index.json'))
prov_name = {p['code']: p['name'] for p in places['provinces']}
cities = {c['code']: c for c in places['cities']}
counties = {c['code']: c for c in places['counties']}

ev_year = {}
for f in glob.glob('data/events/*.json'):
    for e in json.load(open(f)):
        ev_year[e['id']] = e['date'][:4]

unit_years = defaultdict(Counter)
for code, ids in index.items():
    for i in ids:
        y = ev_year.get(i)
        if y:
            unit_years[code][y] += 1


def row(code, c, level):
    ys = unit_years.get(code, Counter())
    total = sum(ys.values())
    return {'code': code, 'name': c['name'], 'level': level,
            'province': prov_name.get(c.get('province', code), ''),
            'total': total,
            'recent': sum(n for y, n in ys.items() if int(y) >= 2015),
            'years_covered': len(ys)}


city_rows = [row(k, c, 'city') for k, c in cities.items()
             if not c['short'].endswith(('市区', '辖县', '直辖县级'))]
county_rows = [row(k, c, 'county') for k, c in counties.items()]
for rows in (city_rows, county_rows):
    rows.sort(key=lambda r: (r['total'], r['name']))

zero_cities = [r for r in city_rows if r['total'] == 0]
thin_cities = [r for r in city_rows if 0 < r['total'] < 30]
prio_counties = [r for r in county_rows if r['name'].endswith('市')]   # 县级市
prio_zero = [r for r in prio_counties if r['total'] == 0]
prio_sparse = [r for r in prio_counties if 0 < r['total'] < 5]

out = {
    'generated': __import__('datetime').date.today().isoformat(),
    'thresholds': {'city_skeleton': 30, 'city_target': 60, 'county_year_target': 12, 'recent_from': 2015},
    'stats': {
        'cities_zero': len(zero_cities), 'cities_thin': len(thin_cities),
        'cities_ok': len(city_rows) - len(zero_cities) - len(thin_cities),
        'counties_mounted': sum(1 for r in county_rows if r['total'] > 0),
        'counties_total': len(county_rows),
        'priority_counties_zero': len(prio_zero), 'priority_counties_sparse': len(prio_sparse),
        'priority_counties_ok': len(prio_counties) - len(prio_zero) - len(prio_sparse),
    },
    'cities': {'zero': zero_cities, 'thin': thin_cities},
    'counties': {'priority_zero': prio_zero, 'priority_sparse': prio_sparse},
}
with open('data/derived/geo_gap.json', 'w', encoding='utf-8') as fh:
    json.dump(out, fh, ensure_ascii=False, indent=1)

s = out['stats']
print(f"城市：零事件 {s['cities_zero']} / 薄(<30) {s['cities_thin']} / 达标 {s['cities_ok']}（共 {len(city_rows)}）")
print(f"县级：已挂载 {s['counties_mounted']}/{s['counties_total']}；"
      f"县级市口径：零 {s['priority_counties_zero']} / 稀(<5) {s['priority_counties_sparse']} / 达标 {s['priority_counties_ok']}")
print(f"→ data/derived/geo_gap.json（零事件城市首批前 12：{'、'.join(r['name'] for r in zero_cities[:12])}）")
