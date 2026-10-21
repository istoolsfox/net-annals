# -*- coding: utf-8 -*-
"""覆盖度诊断：层×时代矩阵 + 薄层排行 + 年度低谷 + 分类学缺口清单。
用法：python3 scripts/coverage.py        # 全量诊断
每轮 cron 扩库前跑一次，从输出取「最薄弱处」作为当轮批次方向。"""
import json, glob
from collections import defaultdict

ERAS = [('接入前史',1986,1994.4),('拨号',1994.4,2000),('门户泡沫',2000,2003),('Web2前夜',2003,2005),
        ('Web2.0',2005,2010),('移动互联网',2010,2015),('移动成熟',2015,2020),('疫情智能',2020,2027)]
MAIN = {'1986-1995','1996-1999','2000-2004','2005-2009','2010-2014','2015-2019','2020-2022','2023-2026'}
THIN_LINE = 20      # 薄层红线：低于此条数的层优先加密
YEAR_LOW = 0.7      # 年度低谷线：低于中位数70%的年份优先补

def era_of(date):
    yf = int(date[:4]) + (int(date[5:7])-1)/12
    for i,(n,a,b) in enumerate(ERAS):
        if a <= yf < b: return i
    return 0 if yf < 1986 else 7

matrix = defaultdict(lambda: [0]*8)
by_year = defaultdict(int)
total = 0
for f in glob.glob('data/events/*.json'):
    if '.parts' in f: continue
    stem = f.split('/')[-1][:-5]
    layer = '主层' if stem in MAIN else stem.split('-',3)[-1]
    for e in json.load(open(f)):
        matrix[layer][era_of(e['date'])] += 1
        by_year[e['date'][:4]] += 1
        total += 1

print(f'全库 {total} 条，{len(matrix)} 个层')
print('\n=== 薄层排行（红线 %d 条） ===' % THIN_LINE)
for total_n,k,v in sorted(((sum(v),k,v) for k,v in matrix.items()), key=lambda x:x[0]):
    if total_n < THIN_LINE: print(f'{total_n:4d} {k:14s} ◀加密优先')
print('\n=== 层×时代 空格（该时代0条） ===')
holes = {k:[ERAS[i][0] for i,n in enumerate(v) if n==0] for k,v in matrix.items()}
empty = sum(len(h) for h in holes.values())
print(f'空格 {empty}/{len(matrix)*8}，重点：')
for k,h in sorted(holes.items()):
    if h and k not in ('diglife','tech'): print(f'  {k:14s} 缺: {", ".join(h)}')
print('\n=== 年度低谷（<中位数70%） ===')
med = sorted(by_year.values())[len(by_year)//2]
for y in sorted(by_year):
    if int(y) < 1986 or by_year[y] >= med*YEAR_LOW: continue
    print(f'{y}: {by_year[y]:4d} ◀补条优先')
print('\n=== 分类学缺口自查清单（对照 GB/T 4754 国民经济行业分类，人工维护） ===')
CHECKLIST = [
 ('金融资本市场', 'A股里程碑/银行股改上市/汇改/保险业/基金业', '缺专层，主层散见'),
 ('生态环保', '退耕还林/河长制/双碳目标/国家公园/治沙', '缺专层，energy只覆盖电力'),
 ('房地产', '房改/商品房/调控/物业/长租', '缺专层，city层散见'),
 ('农业农村', '粮价与种业/乡镇企业/脱贫产业/乡村振兴', '缺专层'),
 ('家电与制造业', '海尔砸冰箱/格力美的/中国制造升级', '缺专层，散在tech/autos'),
 ('时尚美妆', '国货美妆/服装产业/时尚媒体', '缺专层，retail偏渠道'),
]
for name, items, status in CHECKLIST:
    print(f'  □ {name:8s} {status}  可补: {items}')
