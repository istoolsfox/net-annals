#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 中文维基逐年页无损采集器：先拿全，后分析
# 用法: python3 scripts/wiki_harvest.py [起始年] [结束年]   （默认 1986-2026）
# 产出: data/wiki_raw/YYYY.json（原始条目数组；该目录只做本地分析，不进站点、不提交 git）
# 说明: 只采集各月「大事记」章节；灾害/事故/逝世/节假日等章节对本库无用，
#       其章节名记录进 _meta.json 备查（审计跳过了什么）。
import json, os, re, sys, time, html, urllib.request, urllib.parse

START = int(sys.argv[1]) if len(sys.argv) > 1 else 1986
END = int(sys.argv[2]) if len(sys.argv) > 2 else 2026
OUT = 'data/wiki_raw'
os.makedirs(OUT, exist_ok=True)
UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) net-annals-research/1.0'}
META = f'{OUT}/_meta.json'
meta = json.load(open(META)) if os.path.exists(META) else {}

def fetch(year):
    title = urllib.parse.quote(f'{year}年中国大陆')
    req = urllib.request.Request(f'https://zh.wikipedia.org/wiki/{title}', headers=UA)
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read().decode('utf-8')

def parse(raw):
    m = re.search(r'mw-parser-output', raw)
    if not m:
        return [], []
    body = re.sub(r'<script.*?</script>|<style.*?</style>', '', raw[m.start():], flags=re.S)
    hpat = re.compile(r'<h[23][^>]*>(.*?)</h[23]>', re.S)
    lipat = re.compile(r'<li[^>]*>(.*?)</li>', re.S)
    def strip(t):
        t = re.sub(r'<[^>]+>', '', t)
        return html.unescape(t).strip()
    parts = hpat.split(body)
    sections, items = [], []
    for i in range(1, len(parts), 2):
        head = strip(parts[i])
        if not head:
            continue
        sections.append(head)
        # 只收「X月」或「X月上旬」这类大事记章节
        if not re.match(r'^(1[0-2]|[1-9])月', head):
            continue
        for li in lipat.findall(parts[i + 1]):
            t = strip(li)
            if len(t) >= 10:
                items.append({'section': head, 'text': t})
    # 兜底：早年页面大事记是整段流文本（无月份标题、无列表），按「X月X日，」切分
    if not items:
        in_events = False
        blob = ''
        for i in range(1, len(parts), 2):
            head = strip(parts[i])
            if in_events and head == '参考文献':
                break
            if head == '大事記':
                in_events = True
            if in_events:
                blob += parts[i + 1]
        text = html.unescape(re.sub(r'<[^>]+>', '', blob))
        text = re.sub(r'\[\d+\]', '', text)  # 去引用角标
        # 情形A：大事記本身就是平铺 li（无月份子标题）——直接抓 li
        lis = lipat.findall(blob)
        if len(lis) >= 3:
            for li in lis:
                t = strip(li)
                if len(t) >= 10:
                    items.append({'section': '大事記', 'text': t})
        # 情形B：整段流文本，按「X月X日+分隔符」切分（兼容 ，,：:－—- 等分隔）
        if not items:
            segs = re.split(r'(?=(?:1[0-2]|[1-9])月(?:[0-3]?\d日)?[，,：:－—\-])', text)
            for s in segs:
                s = s.strip()
                if len(s) >= 10 and re.match(r'^(?:1[0-2]|[1-9])月', s):
                    items.append({'section': '流文本', 'text': s})
    return sections, items

total = 0
for y in range(START, END + 1):
    f = f'{OUT}/{y}.json'
    if os.path.exists(f):
        n = len(json.load(open(f)))
        print(f'-- {y} 已存在（{n}条），跳过')
        total += n
        continue
    try:
        raw = fetch(y)
        sections, items = parse(raw)
        json.dump(items, open(f, 'w'), ensure_ascii=False, indent=1)
        meta[str(y)] = sections
        json.dump(meta, open(META, 'w'), ensure_ascii=False, indent=1)
        print(f'✓ {y}: {len(items)} 条原始条目，章节 {len(sections)} 个')
        total += len(items)
        time.sleep(1.2)
    except Exception as e:
        print(f'✗ {y}: {type(e).__name__} {e}')
print(f'采集完成，共 {total} 条 → {OUT}/')
