#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性：把 n8n 缺口扫荡队列（gap_queue_*.json）转成 gap_candidates.json 格式
（复用 gap_diff 的查重规则：同日 >0.6 已收录 / 0.3-0.6 边缘；月精度对整月比对）。
队列字段 {date_text,title,quote,cat,imp,source,year} → 行格式 {date,acc,year,text,tag,src_url,...}
tag 携带 source URL 穿透 glm_screen/glm_write。
用法: python3 scripts/batch_gap_queue_diff.py data/derived/gap/gap_queue_2026-10-28.json"""
import json, glob, re, os, sys
from collections import defaultdict

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

queue_path = sys.argv[1] if len(sys.argv) > 1 else 'data/derived/gap/gap_queue_2026-10-28.json'
queue = json.load(open(queue_path, encoding='utf-8'))['candidates']


def sig(s):
    return set(re.sub(r'[\s《》「」『』·、，。：；\-—（）()"\']', '', s or ''))


def ov(a, b):
    A, B = sig(a), sig(b)
    m = min(len(A), len(B))
    return len(A & B) / m if m else 0


def known_mmdd(dt):
    """date_text → 已知 MM-DD（gap_diff 的 known 参数）；解析不出返回 ''"""
    dt = dt.strip()
    m = re.fullmatch(r'(\d{4})年(\d{1,2})月(\d{1,2})日', dt)
    if m:
        return f'{int(m.group(2)):02d}-{int(m.group(3)):02d}'
    m = re.fullmatch(r'(\d{1,2})月(\d{1,2})日', dt)
    if m:
        return f'{int(m.group(1)):02d}-{int(m.group(2)):02d}'
    return ''


def parse_date(text, year, known):
    if known:
        return f'{year}-{known}', 'exact'
    m = re.search(r'(\d{1,2})月(\d{1,2})日', text)
    if m:
        rest = text[m.end():m.end() + 6]
        if re.match(r'\s*[至到～\-—与和]', rest):
            return f'{year}-{int(m.group(1)):02d}', 'month'
        return f'{year}-{int(m.group(1)):02d}-{int(m.group(2)):02d}', 'exact'
    m = re.search(r'(\d{1,2})月(?:中旬|下旬|上旬|底|初)?', text)
    if m:
        return f'{year}-{int(m.group(1)):02d}', 'month'
    return '', ''


# 载入库
by_day, by_month = defaultdict(list), defaultdict(list)
for f in glob.glob('data/events/*.json'):
    if '/.' in f or '.parts' in f:
        continue
    for e in json.load(open(f, encoding='utf-8')):
        by_day[e['date'][:10]].append(e['title'])
        by_month[e['date'][:7]].append(e['title'])

missing, borderline, covered = [], [], 0
seen = []
for c in queue:
    text = f"{c['title']}：{c['quote']}"
    known = known_mmdd(c['date_text'])
    date, acc = parse_date(text, c['year'], known)
    if not date:
        continue
    if any(d == date and ov(text, t) > 0.6 for d, t in seen):
        continue
    seen.append((date, text))
    pool = by_day.get(date, []) if len(date) == 10 else by_month.get(date, [])
    best, best_t = 0, ''
    for t in pool:
        s = ov(text, t)
        if s > best:
            best, best_t = s, t
    row = {'date': date, 'acc': acc, 'year': c['year'], 'text': text,
           'tag': c['cat'], 'src_url': c['source'], 'imp_queue': c['imp'],
           'quote': c['quote'], 'best': round(best, 2), 'vs_title': best_t}
    if best > 0.6:
        covered += 1
    elif best > 0.3:
        borderline.append(row)
    else:
        missing.append(row)

out = {'missing': missing, 'borderline': borderline, 'undated': []}
json.dump(out, open('data/derived/gap_candidates.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print(f'队列 {len(queue)} 条 → 缺口 {len(missing)} | 边缘 {len(borderline)} | 库内已收 {covered}')
print(f"年份: {sorted(set(r['year'] for r in missing + borderline))}")
