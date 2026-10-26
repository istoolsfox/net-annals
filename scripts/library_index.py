#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""库索引导出器：为 n8n 缺口发现工作流（docs/GAP_FINDER.md）生成查重索引。
用法: python3 scripts/library_index.py
产出: data/derived/library_index.json —— 全库 {id,date,title,category,region,milestone} 索引
同步: rsync -az data/derived/library_index.json toolsfox:~/n8n_share/
每轮编年入库后重跑一次。"""
import json, glob, os, datetime

OUT = 'data/derived/library_index.json'
items = []
for f in glob.glob('data/events/*.json'):
    if '/.' in f or '.parts' in f:
        continue
    for e in json.load(open(f, encoding='utf-8')):
        items.append({
            'id': e['id'],
            'date': e['date'],
            't': e.get('title', ''),
            'c': e.get('category', ''),
            'r': e.get('region', ''),
            'm': bool(e.get('milestone')),
        })
items.sort(key=lambda x: x['date'])
os.makedirs('data/derived', exist_ok=True)
json.dump({'generated_at': datetime.datetime.now().isoformat(timespec='seconds'),
           'total': len(items), 'items': items},
          open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print(f'→ {OUT}: {len(items)} 条')
