#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 把现有事件自动挂到行政区划索引：data/geo_index.json {place_code: [event_id, ...]}
# 用法: python3 scripts/geo_match.py
# 规则：
#   - 匹配文本 = title + summary_30s（不动 detail，控制误伤）
#   - 地级：city.short 出现即挂（直辖市的省名匹配挂到「市区」行；港澳台省名挂省行）
#   - 县级：仅白名单（义乌/昆山/敦煌等知名县级单位）参与自动挂
#   - 停用表：与省名冲突（吉林/海南）或常见词误伤（中山/朝阳/阿里…）不参与自动挂
import json, re
from collections import defaultdict

PLACES = 'data/places.json'
OUT = 'data/geo_index.json'

CITY_STOPLIST = {
    '吉林', '海南',            # 与省名冲突
    '东方', '大同', '文昌',    # 东方明珠/大同社会/文昌星
    '中山', '朝阳',            # 孙中山/朝阳区
    '阿里', '和田', '白银',    # 阿里巴巴/和田玉/贵金属白银
    '长治', '包头', '中卫',    # 长治久安/协议包头/足球中卫
    '兴安',                    # 兴安岭
}
# 知名县级单位白名单：名称独特、事件价值高
COUNTY_WHITELIST = {
    '义乌', '昆山', '江阴', '张家港', '常熟', '诸暨', '慈溪', '余姚', '乐清',
    '晋江', '石狮', '顺德', '寿光', '敦煌', '曲阜', '平遥', '婺源', '都江堰',
    '九寨沟', '武夷山', '香格里拉', '井冈山',
    # 灾疫节点所在县（地域日志需要这些坐标）
    '汶川', '北川', '舟曲', '涿州', '苍南', '温岭', '门头沟', '且末',
}

d = json.load(open(PLACES))
provinces = {p['code']: p for p in d['provinces']}
cities = {c['code']: c for c in d['cities']}
counties = {c['code']: c for c in d['counties']}

# 城市匹配键（跳过停用/直辖市区行——直辖市走省名）
city_keys = {}
for code, c in cities.items():
    s = c['short']
    if s in CITY_STOPLIST or s.endswith(('市区', '辖县', '直辖县级')):
        continue
    city_keys[s] = code
# 直辖市/港澳台：省名 → 目标行（直辖市挂「市区」，港澳台挂省行）
prov_keys = {}
for pcode, p in provinces.items():
    if pcode in ('11', '31', '12', '50'):
        target = next(cd for cd, c in cities.items() if c['province'] == pcode and c['short'].endswith('市区'))
    elif pcode in ('71', '81', '82'):
        target = pcode
    else:
        continue
    prov_keys[p['short']] = target
county_keys = {c['short']: c['code'] for c in counties.values() if c['short'] in COUNTY_WHITELIST}

import glob as _glob
matched = defaultdict(list)
n_ev = 0
for f in sorted(_glob.glob('data/events/*.json')):
    for e in json.load(open(f)):
        n_ev += 1
        text = e.get('title', '') + e.get('summary_30s', '')
        hits = set()
        for k, code in prov_keys.items():
            if k in text:
                hits.add(code)
        for k, code in city_keys.items():
            if k in text:
                hits.add(code)
        for k, code in county_keys.items():
            if k in text:
                hits.add(code)
        for code in hits:
            matched[code].append(e['id'])

out = {code: ids for code, ids in sorted(matched.items())}
json.dump(out, open(OUT, 'w'), ensure_ascii=False, indent=1)

n_hit_ev = len({i for ids in matched.values() for i in ids})
n_prov_hit = sum(1 for p in provinces.values() if matched.get(p['code']) or
                 any(matched.get(c['code']) for c in cities.values() if c['province'] == p['code']))
top = sorted(matched.items(), key=lambda x: -len(x[1]))[:15]
name_of = {**{p['code']: p['short'] for p in provinces.values()},
           **{c['code']: c['short'] for c in cities.values()},
           **{c['code']: c['short'] for c in counties.values()}}
print(f'事件 {n_ev} 条 → 挂上地域 {n_hit_ev} 条，覆盖 {len(matched)} 个地级单位（含县级白名单）')
print(f'省级行政区覆盖：{n_prov_hit}/34')
print('Top15：')
for code, ids in top:
    print(f'  {name_of.get(code, code):8s} {len(ids):4d} 条')
