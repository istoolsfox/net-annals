#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""缺口差集：wiki_raw 候选 vs 编年全库，产出 GLM 初筛输入。
用法: python3 scripts/gap_diff.py
产出: data/derived/gap_candidates.json
  missing     —— 库内没有的候选（GLM 打分对象）
  borderline  —— 同日标题重叠 0.3-0.6 的边缘项（GLM 仲裁是否同事件）
规则与 add_events.py/dedup.py 一致：同日标题字符重叠 >0.6 视为已收录。"""
import json, glob, re, os, datetime
from collections import defaultdict

def sig(s):
    return set(re.sub(r'[\s《》「」『』·、，。：；\-—（）()"\']', '', s or ''))

def overlap(a, b):
    A, B = sig(a), sig(b)
    m = min(len(A), len(B))
    return len(A & B) / m if m else 0

def parse_date(text, year, known):
    """返回 (date, date_accuracy)；known 为过滤器已解析的 MM-DD。"""
    if known:
        return f'{year}-{known}', 'exact'
    m = re.search(r'(\d{1,2})月(\d{1,2})日', text)
    if m:
        # 区间日期（9月4至15日/9月4日-15日）降为月精度，取首日存档
        rest = text[m.end():m.end() + 6]
        if re.match(r'\s*[至到～\-—与和]', rest):
            return f'{year}-{int(m.group(1)):02d}', 'month'
        return f'{year}-{int(m.group(1)):02d}-{int(m.group(2)):02d}', 'exact'
    m = re.search(r'(\d{1,2})月(?:中旬|下旬|上旬|底|初)?', text)
    if m:
        return f'{year}-{int(m.group(1)):02d}', 'month'
    return '', ''

# ── 载入库（现算，不用可能过期的 rsync 索引）──
lib = []
for f in glob.glob('data/events/*.json'):
    if '/.' in f or '.parts' in f:
        continue
    for e in json.load(open(f, encoding='utf-8')):
        lib.append((e['date'][:10], e['title'], e['id']))
by_day = defaultdict(list)
by_month = defaultdict(list)
for d, t, i in lib:
    by_day[d].append((t, i))
    by_month[d[:7]].append((t, i))
lib_total = len(lib)

# ── 载入候选 ──
cands = json.load(open('data/wiki_raw/candidates.json', encoding='utf-8'))
missing, borderline, covered, undated = [], [], 0, []
seen = []   # 候选内部互相去重 (date, text)

for year in sorted(cands, key=int):
    for it in cands[year]:
        text = it['text'].strip()
        date, acc = parse_date(text, year, it.get('date', ''))
        if not date:
            undated.append({'year': year, 'text': text, 'tag': it['tag']})
            continue
        # 候选互相去重
        dup_c = any(d == date and overlap(text, t) > 0.6 for d, t in seen)
        if dup_c:
            continue
        seen.append((date, text))
        # 月精度候选与库内整月比对（修淄博/科目三类同月重复漏网）
        pool = by_day.get(date, []) if len(date) == 10 else by_month.get(date, [])
        best, best_id, best_t = 0, None, ''
        for t, i in pool:
            s = overlap(text, t)
            if s > best:
                best, best_id, best_t = s, i, t
        row = {'date': date, 'acc': acc, 'year': year, 'text': text,
               'tag': it['tag'], 'best': round(best, 2), 'vs_id': best_id,
               'vs_title': best_t}
        if best > 0.6:
            covered += 1
        elif best > 0.3:
            borderline.append(row)
        else:
            missing.append(row)

missing.sort(key=lambda r: r['date'])
borderline.sort(key=lambda r: r['date'])
os.makedirs('data/derived', exist_ok=True)
out = {
    'generated_at': datetime.datetime.now().isoformat(timespec='seconds'),
    'library_total': lib_total,
    'candidates_total': covered + len(borderline) + len(missing) + len(undated),
    'covered': covered, 'missing': missing, 'borderline': borderline,
    'undated': undated,
}
json.dump(out, open('data/derived/gap_candidates.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print(f"库 {lib_total} 条 | 候选 {out['candidates_total']} → "
      f"已收录 {covered} / 缺口 {len(missing)} / 边缘 {len(borderline)} / 无日期 {len(undated)}")
print(f"→ data/derived/gap_candidates.json")
for r in missing[:5]:
    print(f"  例 {r['date']} [{r['tag']}] {r['text'][:60]}")
