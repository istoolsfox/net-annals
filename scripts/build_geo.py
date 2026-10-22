#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 生成站点地域日志数据 site/geo/data.json（紧凑数组格式）
# 用法: python3 scripts/build_geo.py
# 依赖: data/places.json（骨架）+ data/geo_index.json（事件挂载）+ data/events/*.json
import json, glob
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
places = json.load(open(ROOT / 'data/places.json'))
index = json.load(open(ROOT / 'data/geo_index.json'))

# 事件元数据（只取列表展示所需字段）
meta = {}
for f in glob.glob(str(ROOT / 'data/events/*.json')):
    for e in json.load(open(f)):
        meta[e['id']] = e

ev = {}
for code, ids in index.items():
    rows = []
    for eid in ids:
        e = meta.get(eid)
        if not e:
            continue
        rows.append([e['date'], e['title'], e['category'], 1 if e['milestone'] else 0])
    rows.sort(key=lambda r: r[0])
    ev[code] = rows

cnt = lambda code: len(ev.get(code, []))
provinces = [[p['code'], p['name'], p['short'], cnt(p['code'])] for p in places['provinces']]
cities = [[c['code'], c['name'], c['short'], c['province'], cnt(c['code'])] for c in places['cities']]
counties = [[k['code'], k['name'], k['short'], k['city'], k['province'], cnt(k['code'])]
            for k in places['counties']]

with_geo = sum(1 for row in provinces + cities + counties if row[-1] > 0)
tagged = sum(len(v) for v in ev.values())
out = {
    'generated': datetime.now().astimezone().isoformat(timespec='seconds'),
    'stats': {
        'provinces': len(provinces), 'cities': len(cities), 'counties': len(counties),
        'placesWithEvents': with_geo, 'taggedEvents': tagged,
    },
    'p': provinces, 'c': cities, 'k': counties, 'ev': ev,
}
dst = ROOT / 'site/geo/data.json'
dst.parent.mkdir(parents=True, exist_ok=True)
dst.write_text(json.dumps(out, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
import os
print(f'✓ 地域数据：省{len(provinces)} 市{len(cities)} 县{len(counties)}，'
      f'有内容单位 {with_geo} 个，挂载事件 {tagged} 条 → site/geo/data.json（{os.path.getsize(dst)//1024}KB）')
