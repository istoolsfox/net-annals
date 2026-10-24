# -*- coding: utf-8 -*-
"""合并增补输出到 persons/entities data.json。
用法: python merge_enrich.py <base_dir>   # base_dir 含 persons/data.json 与 entities/data.json
从 out/ 读取 out-*.json（{id: {bio, timeline, legacy, controversies?, sources?, death?...}}），
校验后应用增量，生成 *_new.json 并打印覆盖率与质检结果。
"""
import json, glob, os, sys, re

BASE = sys.argv[1] if len(sys.argv) > 1 else '.'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out')
DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')

def load(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)

def validate_delta(did, delta):
    problems = []
    clean = {}
    if 'bio' in delta:
        bio = str(delta['bio']).strip()
        if len(bio) < 120: problems.append(f'bio过短({len(bio)}字)')
        clean['bio'] = bio
    if 'timeline' in delta:
        tl = []
        for t in delta['timeline']:
            if not isinstance(t, dict) or not DATE_RE.match(str(t.get('date', ''))):
                problems.append(f'timeline日期非法: {str(t)[:40]}'); continue
            acc = t.get('acc', 'exact')
            if acc not in ('exact', 'month', 'year'): acc = 'year'
            text = str(t.get('text', '')).strip()
            if len(text) < 6: problems.append(f'timeline条目过短: {t.get("date")}'); continue
            tl.append({'date': t['date'], 'acc': acc, 'text': text})
        if len(tl) < 6: problems.append(f'timeline条目不足({len(tl)})')
        tl.sort(key=lambda t: t['date'])
        clean['timeline'] = tl
    for k in ('legacy', 'status', 'death', 'dissolved', 'founded'):
        if k in delta and delta[k] not in (None, ''):
            clean[k] = delta[k]
    if 'controversies' in delta:
        c = [str(x).strip() for x in delta['controversies'] if str(x).strip()]
        if c: clean['controversies'] = c[:3]
    if 'sources' in delta:
        s = [x for x in delta['sources'] if isinstance(x, dict) and str(x.get('url', '')).startswith('http')]
        if s: clean['sources'] = s[:4]
    return clean, problems

def apply(kind):
    fname = 'persons/data.json' if kind == 'p' else 'entities/data.json'
    records = load(os.path.join(BASE, fname))
    key = 'persons' if kind == 'p' else 'entities'
    arr = records[key]
    by_id = {r['id']: r for r in arr}
    stats = {'applied': 0, 'unknown': [], 'problems': {}, 'files': 0}
    for f in sorted(glob.glob(os.path.join(OUT, f'out-{kind}*.json'))):
        stats['files'] += 1
        try:
            deltas = load(f)
        except Exception as e:
            print(f'[ERR] 解析失败 {os.path.basename(f)}: {e}'); continue
        for did, delta in deltas.items():
            if did not in by_id:
                stats['unknown'].append(f'{os.path.basename(f)}:{did}'); continue
            clean, problems = validate_delta(did, delta)
            if problems:
                stats['problems'][did] = problems
            if not clean:
                continue
            by_id[did].update(clean)
            stats['applied'] += 1
    records['count'] = len(arr)
    records['generated'] = __import__('datetime').datetime.now(
        __import__('datetime').timezone(__import__('datetime').timedelta(hours=8))).strftime('%Y-%m-%dT%H:%M:%S+08:00')
    out = os.path.join(BASE, fname.replace('.json', '_new.json'))
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, separators=(',', ':'))
    # 质检摘要
    tl = [len(r.get('timeline') or []) for r in arr]
    bios = sum(1 for r in arr if r.get('bio'))
    print(f'[{kind}] 应用 {stats["applied"]}/{len(arr)} | 文件 {stats["files"]} | bio覆盖 {bios} | '
          f'timeline 中位数 {sorted(tl)[len(tl)//2]} 最少 {min(tl)}')
    if stats['unknown']: print('  未知ID:', stats['unknown'][:5])
    if stats['problems']:
        for did, ps in list(stats['problems'].items())[:8]:
            print(f'  质检 {did}: {ps}')

if __name__ == '__main__':
    apply('p'); apply('e')
