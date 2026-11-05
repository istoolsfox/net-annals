#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""g_gapfinder_1.json 验收修复（2026-10-26 机器验收三件套发现的 5 类问题）：
1) 月精度日期 19 条：date 补 -01、id 同步（库内规范 date=YYYY-MM-01+accuracy=month）
2) 类目越枚举 2 条：education→society、media→culture
3) 小写英文杂词 4 处：逐处改写
4) detail 过短的 2 条逝世条目：内容太薄，整条弃收
5) 月精度条目补查重：与库内同月条目重叠>0.6 判重弃收（gap_diff 曾漏比对）
跑完重新过 validate_part + 三扫描。"""
import json, glob, re

PARTS = 'data/events/.parts/g_gapfinder_1.json'
es = json.load(open(PARTS, encoding='utf-8'))

def sig(s):
    return set(re.sub(r'[\s《》「」『』·、，。：；\-—（）()"\']', '', s or ''))

def ov(a, b):
    A, B = sig(a), sig(b)
    m = min(len(A), len(B))
    return len(A & B) / m if m else 0

# 库内同月索引
lib_by_month = {}
for f in glob.glob('data/events/*.json'):
    if '/.' in f or '.parts' in f:
        continue
    for e in json.load(open(f, encoding='utf-8')):
        lib_by_month.setdefault(e['date'][:7], []).append(e['title'])

out, dropped = [], []
for e in es:
    eid = e['id']
    # 5) 月精度补查重（在改日期前做，用原月份比对）
    if len(e['date']) == 7:
        best, vs = 0, ''
        for t in lib_by_month.get(e['date'], []):
            s = ov(e['title'] + e['summary_30s'][:40], t)
            if s > best:
                best, vs = s, t
        if best > 0.6:
            dropped.append((eid, f'同月重复 vs「{vs[:28]}」{best:.2f}'))
            continue
    # 1) 月精度日期规范化
    if len(e['date']) == 7:
        e['date'] = e['date'] + '-01'
        e['id'] = e['date'] + '-' + eid.split('-', 2)[2]
    # 2) 类目映射
    if e.get('category') == 'education':
        e['category'] = 'society'
    if e.get('category') == 'media':
        e['category'] = 'culture'
    # 3) 英文杂词
    fixes = {
        '2004-02-05-miyun-lantern-stampede':
            [('safety 管理失位', '安全管理失位')],
        '2004-10-17-zhougongmiao-tomb-excavation':
            [('重要 associated 地点', '重要关联地点')],
        '2005-08-31-2005-rmb-fifth-series':
            [('随 counterfeit 手段变化', '随伪造手段变化')],
        '2010-03-01-luotuoshan-coal-mine-flood':
            [('该矿 thereafter 停产整顿', '该矿此后停产整顿')],
    }
    for old, new in fixes.get(eid, []):
        for f in ['summary_30s', 'detail', 'impact', 'aftermath']:
            if old in e.get(f, ''):
                e[f] = e[f].replace(old, new)
    # 4) 过短 detail 弃收
    if len(e['detail']) < 150:
        dropped.append((eid, f"detail 仅{len(e['detail'])}字，弃收"))
        continue
    out.append(e)

json.dump(out, open(PARTS, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'保留 {len(out)} 条 / 弃收 {len(dropped)} 条:')
for eid, why in dropped:
    print(f'  ✗ {eid}: {why}')
