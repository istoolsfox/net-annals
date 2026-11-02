#!/usr/bin/env python3
"""存量条目 place 标签回填：给无 place 的 cn 条目补 place 直挂。
增益面 = 地名只出现在 detail（geo_match 文本匹配只读 title+summary_30s）的条目。
分析模式（默认）：落 data/derived/geo_backfill_report.json，不动库。
--apply：把 single 命中（单市/单县，零歧义）写回条目 place 字段。
"""
import glob
import json
import sys
from collections import defaultdict

REPO = __file__.rsplit('/scripts/', 1)[0]
PLACES = f'{REPO}/data/places.json'
REVIEW = f'{REPO}/data/derived/geo_backfill_report.json'

CITY_STOPLIST = {
    '吉林', '海南',
    '东方', '大同', '文昌',
    '中山', '朝阳',
    '阿里', '和田', '白银',
    '长治', '包头', '中卫',
    '兴安',
    '海东', '白山',
    '四平', '玉林', '太原', '海口', '西宁',
}
CITY_NEG_SUFFIX = {'周口': ('店',), '苏州': ('河',)}
CITY_NEG_PREFIX = {'天水': ('飞',), '海城': ('沿',), '东方市': ('新',)}

places = json.load(open(PLACES))
provinces = {p['code']: p for p in places['provinces']}
cities = {c['code']: c for c in places['cities']}
counties = {c['code']: c for c in places['counties']}

city_keys = {}
for code, c in cities.items():
    s = c['short']
    if s.endswith(('市区', '辖县', '直辖县级')):
        continue
    if s in CITY_STOPLIST:
        city_keys[c['name']] = code
    else:
        city_keys[s] = code

county_names = defaultdict(list)
for c in counties.values():
    county_names[c['name']].append(c['code'])
dup_names = {n for n, cs in county_names.items() if len(cs) > 1}
STEM = ({c['short'] for c in cities.values()} | {c['short'] for c in counties.values()} |
        {p['short'] for p in provinces.values()})
county_keys = sorted(((n, county_names[n][0]) for n in county_names
                      if n not in dup_names and not (n.endswith('区') and len(n) < 4)),
                     key=lambda x: -len(x[0]))


# 县级全称的负护栏：沿海城市⊃海城市/新东方市值⊃东方市/古县城⊃古县/地区和县级⊃和县
COUNTY_NEG_PREFIX = {'海城市': ('沿',), '东方市': ('新',), '和县': ('地',)}
COUNTY_NEG_SUFFIX = {'古县': ('城',)}


def county_hit(masked, name):
    ok, ctx = False, ''
    i = masked.find(name)
    while i != -1:
        if i == 0 or masked[i - 1] + name[0] not in STEM:
            pre = masked[i - 1:i]
            tail = masked[i + len(name):i + len(name) + 1]
            if name in COUNTY_NEG_PREFIX and pre in COUNTY_NEG_PREFIX[name]:
                i = masked.find(name, i + 1)
                continue
            if name in COUNTY_NEG_SUFFIX and tail in COUNTY_NEG_SUFFIX[name]:
                i = masked.find(name, i + 1)
                continue
            ok, ctx = True, masked[max(0, i - 10):i + len(name) + 10]
            break
        i = masked.find(name, i + 1)
    return ok, ctx


def detect(text):
    """返回（命中 set，命中明细 list）。与 geo_match 同规则。"""
    hits = set()
    rows = []
    hit_keys = {}
    masked = text
    for k, code in city_keys.items():
        if k not in masked:
            continue
        bad = False
        i = masked.find(k)
        while i != -1:
            tail = masked[i + len(k):i + len(k) + 1]
            if k in CITY_NEG_SUFFIX and tail in CITY_NEG_SUFFIX[k]:
                bad = True
                break
            i = masked.find(k, i + 1)
        if k in CITY_NEG_PREFIX and masked[masked.find(k) - 1:masked.find(k)] in CITY_NEG_PREFIX[k]:
            bad = True
        if not bad:
            hits.add(('c', code))
            hit_keys[('c', code)] = k
    for k, code in county_keys:
        ok, ctx = county_hit(masked, k)
        if ok:
            hits.add(('k', code))
            rows.append({'k', code} if False else {'kind': 'k', 'code': code, 'name': k, 'ctx': ctx})
            masked = masked.replace(k, '■' * len(k))
    return hits, rows, hit_keys


def main():
    apply = '--apply' in sys.argv
    report = {'single': [], 'multi': [], 'stats': {}}
    n_scanned = n_noplace = 0
    for f in sorted(glob.glob(f'{REPO}/data/events/*.json')):
        arr = json.load(open(f))
        changed = False
        for e in arr:
            n_scanned += 1
            if e.get('region') != 'cn':
                continue
            if e.get('place'):
                continue
            n_noplace += 1
            head = e.get('title', '') + e.get('summary_30s', '')
            detail = e.get('detail', '')
            head_hits, _, head_keys = detect(head)
            full_hits, full_rows, full_keys = detect(head + detail)
            gain = full_hits - head_hits          # detail 才有的命中 = 增量
            # 分层置信：县级全称 / 市级全称命中才自动落；市短名提及噪音大，留报告
            keep = {g for g in gain if g[0] == 'k' or full_keys.get(g) == cities.get(g[1], {}).get('name')}
            if not keep:
                continue
            cand = sorted(keep)
            if len(keep) == 1:
                report['single'].append({'id': e['id'], 'file': f.split('events/')[-1],
                                         'propose': cand})
            else:
                report['multi'].append({'id': e['id'], 'file': f.split('events/')[-1],
                                        'propose': cand, 'hits': full_rows[:6]})
            if apply and len(keep) == 1:
                (kind, code), = keep
                e['place'] = [f'{kind}:{code}']
                changed = True
        if changed:
            json.dump(arr, open(f, 'w'), ensure_ascii=False, indent=0)

    report['stats'] = {'scanned': n_scanned, 'no_place': n_noplace,
                       'single': len(report['single']), 'multi': len(report['multi'])}
    json.dump(report, open(REVIEW, 'w'), ensure_ascii=False, indent=1)
    print(f"扫描 {n_scanned} 条，无 place 的 cn 条目 {n_noplace} 条；"
          f"detail 独有地名：单命中 {len(report['single'])}（可自动回填），"
          f"多命中 {len(report['multi'])}（人工裁定）→ {REVIEW}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
