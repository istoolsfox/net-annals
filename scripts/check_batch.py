#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""地域批次通用验收器：对单个 .parts 批次文件做全套结构+查重检查。

用法:
  python3 scripts/check_batch.py auto_geo_city_x10.json [--fix]
检查项（按序）:
  1. <1970 年下限违规条目（--fix 时剔除）
  2. date_confidence 数字值 / date 非完整格式（--fix 时自动修复：数字→single-source；YYYY-MM→补-01+month）
  3. category 库外枚举（--fix 时按 MAP 映射：sport→culture/education→society/transport→economy/media→culture/eco→society/social→society/science→tech）
  4. 批内 id 冲突 / 与主库撞 id
  5. 同日撞主库 & 批间（textmatch 算法，>0.6 列出对手——需人工改题，不自动改）
输出: 各项计数与明细；--fix 时写回修复。
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from textmatch import title_overlap, load_title_index, THRESHOLD  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CAT_MAP = {'sport': 'culture', 'education': 'society', 'transport': 'economy',
           'media': 'culture', 'eco': 'society', 'social': 'society', 'science': 'tech'}
VALID_CAT = {'national', 'world', 'society', 'culture', 'economy', 'company',
             'product', 'internet', 'tech', 'hardware', 'milestone'}


def main():
    args = sys.argv[1:]
    fix = '--fix' in args
    path = ROOT / 'data' / 'events' / '.parts' / args[0]
    arr = json.load(open(path, encoding='utf-8'))
    changed = False

    # 1. 年下限
    bad_year = [e['id'] for e in arr if int(e['date'][:4]) < 1970]
    if bad_year:
        print('1) <1970:', bad_year)
        if fix:
            arr = [e for e in arr if int(e['date'][:4]) >= 1970]
            changed = True
            print('   已剔除')
    else:
        print('1) <1970: 0')

    # 2. 置信度/日期格式
    n_conf = n_date = 0
    for e in arr:
        if isinstance(e.get('date_confidence'), (int, float)):
            e['date_confidence'] = 'single-source'
            n_conf += 1; changed = True
        d = e.get('date', '')
        if re.fullmatch(r'\d{4}-\d{2}', d):
            nd = d + '-01'
            e['date'] = nd
            e['date_accuracy'] = 'month'
            parts = e['id'].split('-')
            if len(parts) > 2 and not e['id'].startswith(nd):
                e['id'] = nd + '-' + '-'.join(parts[2:])
            n_date += 1; changed = True
    print(f'2) 数字置信度: {n_conf} | YYYY-MM 畸形date: {n_date}' + ('（已修）' if fix else ''))

    # 3. 类目
    n_cat = 0
    for e in arr:
        c = e.get('category')
        if c in CAT_MAP:
            e['category'] = CAT_MAP[c]
            n_cat += 1; changed = True
        elif c not in VALID_CAT:
            print(f'   ⚠ 未知类目 {c}: {e["id"][:40]}')
    print(f'3) 库外类目映射: {n_cat}' + ('（已修）' if fix else ''))

    # 4. id 冲突
    ids = [e['id'] for e in arr]
    print(f'4) 批内id冲突: {len(ids) - len(set(ids))} | 撞主库id:',
          sum(1 for i in ids if i in _main_ids()))

    # 5. 同日重叠（含批间 parts）
    idx = load_title_index(include_parts=True)
    own = {}
    for e in arr:
        own.setdefault(e['date'], []).append((e['id'], e['title']))
    clashes = []
    for day, rows in own.items():
        for j, (id1, t1) in enumerate(rows):
            for t2 in idx.get(day, []):
                if t2 == t1:
                    continue
                mo = title_overlap(t1, t2)
                if mo > THRESHOLD:
                    clashes.append((round(mo, 2), id1, t2))
            for id2, t2 in rows[j + 1:]:
                mo = title_overlap(t1, t2)
                if mo > THRESHOLD:
                    clashes.append((round(mo, 2), id1, f'[批内]{id2}'))
    print(f'5) 同日重叠 >{THRESHOLD}: {len(clashes)} 对（需人工改题）')
    for mo, eid, t in clashes:
        print(f'   {mo} {eid[:40]} | {t[:30]}')

    if fix and changed:
        json.dump(arr, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print(f'—— 修复已写回（现 {len(arr)} 条）')
    else:
        print(f'—— 共 {len(arr)} 条')
    return 0


_main_ids_cache = None


def _main_ids():
    global _main_ids_cache
    if _main_ids_cache is None:
        _main_ids_cache = set()
        for f in glob_main():
            for e in json.load(open(f, encoding='utf-8')):
                _main_ids_cache.add(e['id'])
    return _main_ids_cache


def glob_main():
    import glob
    return [f for f in glob.glob(str(ROOT / 'data' / 'events' / '*.json'))
            if '/.' not in f and '.parts' not in f]


if __name__ == '__main__':
    sys.exit(main())
