#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# geo_match v2：把事件挂到行政区划索引 data/geo_index.json {place_code: [event_id, ...]}
# 用法: python3 scripts/geo_match.py
# 挂载优先级：
#   1. 事件显式 place 字段（["c:320100","k:110108"] 或裸码 320100/110108/11）直挂——机器可校验，零误伤
#   2. 文本兜底 = title + summary_30s（不动 detail，控制误伤）：
#      - 地级：city.short 出现即挂；停用表城市只用全称 name 挂（中山市/包头市…安全恢复）
#      - 直辖市：省名挂「市区」行；港澳台：省名挂省行
#      - 县级：全量 3361 只做全称 name 匹配；全称同名（朝阳区/和平区…48个）不自动挂——靠 place 直挂
# 误伤防线：长名优先+掩码（思南县⊃南县）；区结尾且长度<4 的全称（城区/郊区/东区/西区）不参与
import json, re, glob as _glob
from collections import defaultdict

PLACES = 'data/places.json'
OUT = 'data/geo_index.json'
REVIEW = 'data/derived/geo_match_review.json'

CITY_STOPLIST = {
    '吉林', '海南',            # 与省名冲突
    '东方', '大同', '文昌',    # 东方明珠/大同社会/文昌星
    '中山', '朝阳',            # 孙中山/朝阳区
    '阿里', '和田', '白银',    # 阿里巴巴/和田玉/贵金属白银
    '长治', '包头', '中卫',    # 长治久安/协议包头/足球中卫
    '兴安',                    # 兴安岭
}

places = json.load(open(PLACES))
provinces = {p['code']: p for p in places['provinces']}
cities = {c['code']: c for c in places['cities']}
counties = {c['code']: c for c in places['counties']}

# ── place 字段直挂 ──
PLACE_RE = re.compile(r'^(?:[pck]:)?(\d{2,6})$')
code_of = {**{k: ('p', v) for k, v in provinces.items()},
           **{k: ('c', v) for k, v in cities.items()},
           **{k: ('k', v) for k, v in counties.items()}}


def place_codes(e):
    out = []
    for tok in e.get('place') or []:
        m = PLACE_RE.match(str(tok))
        if not m:
            continue
        code = m.group(1)
        if code in code_of:
            out.append(code)
    return out


# ── 文本匹配键 ──
city_keys = {}      # key -> code
for code, c in cities.items():
    s = c['short']
    if s.endswith(('市区', '辖县', '直辖县级')):
        continue
    if s in CITY_STOPLIST:
        city_keys[c['name']] = code      # 停用表：仅全称
    else:
        city_keys[s] = code              # 常规：简称
prov_keys = {}
for pcode, p in provinces.items():
    if pcode in ('11', '31', '12', '50'):
        target = next(cd for cd, c in cities.items() if c['province'] == pcode and c['short'].endswith('市区'))
    elif pcode in ('71', '81', '82'):
        target = pcode
    else:
        continue
    prov_keys[p['short']] = target

county_names = defaultdict(list)
for c in counties.values():
    county_names[c['name']].append(c['code'])
dup_names = {n for n, cs in county_names.items() if len(cs) > 1}   # 全称同名：不自动挂
# 县名词干集（城市简称/县简称/省简称），用于前置字护栏：
# 「密云县」⊃「云县」「崇礼县」⊃「礼县」这类嵌套误挂——前字+县名首字构成已知词干则拒绝该处命中
STEM = ({c['short'] for c in cities.values()} | {c['short'] for c in counties.values()} |
        {p['short'] for p in provinces.values()})
# 排序：长名优先 + 掩码防嵌套（思南县 ⊃ 南县）
county_keys = sorted(((n, county_names[n][0]) for n in county_names
                      if n not in dup_names and not (n.endswith('区') and len(n) < 4)),
                     key=lambda x: -len(x[0]))


def county_hit(masked, name):
    """带护栏的全称匹配：返回（是否命中, 命中处上下文）。"""
    ok, ctx = False, ''
    i = masked.find(name)
    while i != -1:
        if i == 0 or masked[i - 1] + name[0] not in STEM:
            ok, ctx = True, masked[max(0, i - 10):i + len(name) + 10]
            break
        i = masked.find(name, i + 1)
    return ok, ctx


matched = defaultdict(list)
review_rows = []
n_ev = n_place = 0
for f in sorted(_glob.glob('data/events/*.json')):
    for e in json.load(open(f)):
        n_ev += 1
        text = e.get('title', '') + e.get('summary_30s', '')
        hits = set(place_codes(e))          # place 直挂（无误伤，不占掩码）
        n_place += len(hits)
        masked = text
        for k, code in prov_keys.items():
            if k in masked:
                hits.add(code)
        for k, code in city_keys.items():
            if k in masked:
                hits.add(code)
        for k, code in county_keys:         # 长名优先+护栏，命中即掩码
            ok, ctx = county_hit(masked, k)
            if ok:
                hits.add(code)
                masked = masked.replace(k, '■' * len(k))
                review_rows.append({'code': code, 'name': k, 'id': e['id'], 'title': e['title'][:60],
                                    'ctx': ctx, 'by': 'name'})
        for code in hits:
            matched[code].append(e['id'])

out = {code: ids for code, ids in sorted(matched.items())}
json.dump(out, open(OUT, 'w'), ensure_ascii=False, indent=1)
json.dump(review_rows, open(REVIEW, 'w'), ensure_ascii=False, indent=1)

n_hit_ev = len({i for ids in matched.values() for i in ids})
n_prov_hit = sum(1 for p in provinces.values() if matched.get(p['code']) or
                 any(matched.get(c['code']) for c in cities.values() if c['province'] == p['code']))
n_city_hit = sum(1 for c in cities.values() if matched.get(c['code']))
n_county_hit = sum(1 for c in counties.values() if matched.get(c['code']))
top = sorted(matched.items(), key=lambda x: -len(x[1]))[:15]
name_of = {**{p['code']: p['short'] for p in provinces.values()},
           **{c['code']: c['short'] for c in cities.values()},
           **{c['code']: c['short'] for c in counties.values()}}
print(f'事件 {n_ev} 条 → 挂上地域 {n_hit_ev} 条（place 直挂 {n_place} 条）')
print(f'覆盖：省 {n_prov_hit}/34 / 市 {n_city_hit}/{len(cities)} / 县 {n_county_hit}/{len(counties)}（同名 {len(dup_names)} 个全称不自动挂）')
print(f'县级挂载明细 → {REVIEW}')
print('Top15：')
for code, ids in top:
    print(f'  {name_of.get(code, code):8s} {len(ids):4d} 条')
