#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 生成全国行政区划骨架 data/places.json（省34/市/县三级）
# 数据源：modood/Administrative-divisions-of-China（2023 民政部口径）+ 港澳台补充
# 用法: python3 scripts/geo_skeleton.py
# 产物: data/places.json  {"meta":..., "provinces":[{code,name,short}], "cities":[...], "counties":[...]}
import json

DST = '/tmp/geodata'
OUT = 'data/places.json'

prov_main = json.load(open(f'{DST}/provinces.json'))
city_main = json.load(open(f'{DST}/cities.json'))
area_main = json.load(open(f'{DST}/areas.json'))
hmt = json.load(open(f'{DST}/HK-MO-TW.json'))

PROV_SHORT_OVERRIDES = {
    '内蒙古自治区': '内蒙古', '广西壮族自治区': '广西', '西藏自治区': '西藏',
    '宁夏回族自治区': '宁夏', '新疆维吾尔自治区': '新疆', '香港特别行政区': '香港',
    '澳门特别行政区': '澳门', '黑龙江省': '黑龙江',
}

def prov_short(name):
    if name in PROV_SHORT_OVERRIDES:
        return PROV_SHORT_OVERRIDES[name]
    for suf in ('省', '市'):
        if name.endswith(suf):
            return name[:-1]
    return name

# 民族名后缀，用于从「XX族YY族自治州」剥出常用简称（大理/延边/博尔塔拉…）
ETHNONS = ['哈萨克', '柯尔克孜', '维吾尔', '土家', '朝鲜', '布依', '哈尼', '傈僳', '景颇', '羌',
           '蒙古', '彝', '白', '傣', '苗', '侗', '壮', '回', '藏']

def city_short(name, prov_s):
    if name in ('市辖区', '县'):
        return f'{prov_s}市区' if name == '市辖区' else f'{prov_s}辖县'
    if name.endswith('直辖县级行政区划'):
        return f'{prov_s}直辖县级'
    if name.endswith('自治州'):
        core = name[:-3]
        changed = True
        while changed:
            changed = False
            # 「XX族」反复剥（德宏傣族景颇族 → 德宏）；再剥裸民族名（伊犁哈萨克 → 伊犁）
            for e in ETHNONS:
                if core.endswith(e + '族') and len(core) > len(e) + 1:
                    core = core[: -len(e) - 1]
                    changed = True
                    break
                if core.endswith(e) and len(core) > len(e):
                    core = core[: -len(e)]
                    changed = True
                    break
        return core
    for suf in ('市', '地区', '盟'):
        if name.endswith(suf) and len(name) > 2:
            return name[:-1]
    return name

def county_short(name):
    for suf in ('自治县', '自治旗', '林区', '新区', '特区', '矿区', '市', '县', '区', '旗'):
        if name.endswith(suf) and len(name) > len(suf):
            return name[: -len(suf)]
    return name

provinces, cities, counties = [], [], []

for p in prov_main:
    ps = prov_short(p['name'])
    provinces.append({'code': p['code'], 'name': p['name'], 'short': ps})
for c in city_main:
    ps = next(x['short'] for x in provinces if x['code'] == c['provinceCode'])
    cs = city_short(c['name'], ps)
    cities.append({'code': c['code'], 'name': c['name'], 'short': cs, 'province': c['provinceCode']})
for a in area_main:
    cities_map = {c['code']: c for c in cities}
    cc = cities_map[a['cityCode']]
    counties.append({'code': a['code'], 'name': a['name'], 'short': county_short(a['name']),
                     'city': a['cityCode'], 'province': a['provinceCode']})

# 港澳台（GB/T 2260 惯例码：台湾71 香港81 澳门82；下级码顺序合成）
HMT_CODE = {'台湾省': '71', '香港特别行政区': '81', '澳门特别行政区': '82'}
for pname, citymap in hmt.items():
    pcode = HMT_CODE[pname]
    provinces.append({'code': pcode, 'name': pname, 'short': prov_short(pname)})
    for ci, (cname, clist) in enumerate(citymap.items(), 1):
        ccode = f'{pcode}0{ci:02d}'
        ps = prov_short(pname)
        cities.append({'code': ccode, 'name': cname, 'short': city_short(cname, ps), 'province': pcode})
        for ki, kname in enumerate(clist, 1):
            counties.append({'code': f'{ccode}{ki:02d}', 'name': kname,
                             'short': county_short(kname), 'city': ccode, 'province': pcode})

out = {
    'meta': {
        'generated': '2026-10-22',
        'source': 'modood/Administrative-divisions-of-China (民政部口径 2023) + HK-MO-TW 补充',
        'note': '骨架数据：后续按地逐个填充内容；区划调整（撤县设区等）以后续版本修补',
    },
    'provinces': provinces, 'cities': cities, 'counties': counties,
}
json.dump(out, open(OUT, 'w'), ensure_ascii=False, indent=1)
print(f'省 {len(provinces)} / 市 {len(cities)} / 县级 {len(counties)} → {OUT}')

# 重名风险报告（供 geo_match 的自动匹配排除用）
from collections import Counter
dup_c = Counter(c['short'] for c in cities if not c['short'].endswith(('市区', '辖县')))
print('市重名 short：', {k: v for k, v in dup_c.items() if v > 1})
