#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""上市公司注册地→行政区划映射（P3 源工程原型）。
用法:
  python3 scripts/geo_regloc.py 002891 300915 ...    # 逐个证券代码查注册地并映射到市/县码
数据源: 新浪财经公司资料页（静态 HTML，办公地址/注册地址）
映射规则: 地址串里做行政区划全称匹配（长名优先，县精确到区/县/县级市，市取地级市码）
用途: 重点县批次给本地上市公司公告挂 place 码；后续接 cninfo 公告队列按县出素材。"""
import json, re, sys, urllib.request

UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
SINA = 'http://vip.stock.finance.sina.com.cn/corp/go.php/vCI_CorpInfo/stockid/{}.phtml'


def fetch_address(code):
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    req = urllib.request.Request(SINA.format(code), headers=UA)
    html = opener.open(req, timeout=15).read().decode('gb18030', errors='ignore')
    addr = None
    for label in ('公司注册地', '注册地址', '办公地址'):
        m = re.search(label + r'[^<]*</td>\s*<td[^>]*>([^<]+)', html)
        if m:
            addr = m.group(1).strip()
            break
    return addr


def map_places(addr, places):
    """地址串 → [行政区划码]：县级全称长名优先命中即停其层，再补地级市。"""
    counties = sorted(places['counties'], key=lambda c: -len(c['name']))
    cities = sorted(places['cities'], key=lambda c: -len(c['name']))
    hits = []
    for c in counties:                      # 县级：全称命中（地址是规范写法，无嵌套风险）
        if c['name'] in addr:
            hits.append(('k:' + c['code'], c['name']))
            break
    for c in cities:                        # 地级：全称优先，简称兜底
        if c['name'] in addr:
            hits.append(('c:' + c['code'], c['name']))
            break
        if c['short'] in addr and not c['short'].endswith(('市区', '辖县')):
            hits.append(('c:' + c['code'], c['name'] + f'(经简称“{c["short"]}”)'))
            break
    return hits


def main():
    places = json.load(open('data/places.json'))
    for code in sys.argv[1:]:
        try:
            addr = fetch_address(code)
        except Exception as e:
            print(f'{code}: 取地址失败 {type(e).__name__}')
            continue
        if not addr:
            print(f'{code}: 页面无地址字段')
            continue
        hits = map_places(addr, places)
        tags = ' '.join(t for t, _ in hits) if hits else '未命中'
        names = ' / '.join(n for _, n in hits) if hits else '-'
        print(f'{code}: {addr}  →  {tags}（{names}）')


if __name__ == '__main__':
    main()
