#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""巨潮资讯公告检索（公开 JSON 接口，实测可用）。

用法:
  python3 scripts/cninfo_announcements.py <searchkey> [YYYY-MM-DD~YYYY-MM-DD] [页大小]
  例: python3 scripts/cninfo_announcements.py 乖宝宠物 2023-08-01~2023-08-31
  python3 scripts/cninfo_announcements.py enrich <candidates.json>
      candidates: [{"id","date","searchkey"}, ...]
      对每条查事件日±10天公告，报告 上市公告书/招股说明书 类命中（含日期差与PDF链接）。
      机器只出报告（data/derived/cninfo_enrich_report.json），回写库人工裁定。
  python3 scripts/cninfo_announcements.py byregion build [限额]
      全量 A 股建 code→注册地映射（Sina 资料页，复用 geo_regloc），断点续跑
      → data/derived/sec_region_map.json
  python3 scripts/cninfo_announcements.py byregion <市名> [市名...]
      从已建映射过滤出注册地在该市（含下辖县）的公司清单

输出: 公告列表（标题 / 日期 / 代码 / PDF 链接）。
用途：资本类条目（上市/IPO/并购/问询函）的日期核实与 source 补强——公告日期精确到日。
仅做只读查询，不绕任何权限；接口限速自守（页大小≤30，翻页自加延时）。"""
import datetime
import json
import re
import ssl
import sys
import time
import urllib.parse
import urllib.request

URL = 'http://www.cninfo.com.cn/new/hisAnnouncement/query'
UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126.0 Safari/537.36',
      'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
      'X-Requested-With': 'XMLHttpRequest',
      'Referer': 'http://www.cninfo.com.cn/new/commonUrl?page=disclosure/list/notice'}
_ctx = ssl.create_default_context()
_ctx.check_hostname = False
_ctx.verify_mode = ssl.CERT_NONE
_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}),
                                      urllib.request.HTTPSHandler(context=_ctx))


def query(searchkey, se_date='', page_size=30, page=1):
    form = urllib.parse.urlencode({
        'pageNum': page, 'pageSize': min(page_size, 30), 'column': 'szse',
        'tabName': 'fulltext', 'plate': '', 'stock': '', 'searchkey': searchkey,
        'secid': '', 'category': '', 'trade': '', 'seDate': se_date,
        'sortName': '', 'sortType': '', 'isHLtitle': 'true',
    }).encode()
    req = urllib.request.Request(URL, data=form, headers=UA)
    r = _opener.open(req, timeout=20)
    d = json.loads(r.read(2000000).decode('utf-8', 'ignore'))
    out = []
    for a in d.get('announcements') or []:
        title = re.sub(r'<[^>]+>', '', a.get('announcementTitle', ''))
        ts = a.get('announcementTime')
        date = datetime.datetime.fromtimestamp(ts / 1000).strftime('%Y-%m-%d') if ts else '?'
        pdf = ''
        if a.get('adjunctUrl'):
            pdf = 'http://static.cninfo.com.cn/' + a['adjunctUrl']
        out.append({'date': date, 'title': title, 'sec': a.get('secCode', ''),
                    'name': re.sub(r'<[^>]+>', '', a.get('secName', '')), 'pdf': pdf})
    return out, d.get('totalAnnouncement')


KEYWORDS = ('上市公告书', '招股说明书', '首次公开发行', '上市保荐书', '股票上市')


def enrich(cands_path):
    import datetime
    cands = json.load(open(cands_path, encoding='utf-8'))
    report = []
    for c in cands:
        d = datetime.date(*(int(x) for x in c['date'].split('-')))
        window = f"{(d - datetime.timedelta(days=10)).isoformat()}~{(d + datetime.timedelta(days=2)).isoformat()}"
        try:
            rows, _ = query(c['searchkey'], window)
        except Exception as e:
            print(f'✗ {c["id"]}: {type(e).__name__} {str(e)[:40]}')
            continue
        hits = [a for a in rows if any(k in a['title'] for k in KEYWORDS)]
        best = None
        for a in hits:
            ad = datetime.date(*(int(x) for x in a['date'].split('-')))
            delta = (ad - d).days
            if best is None or abs(delta) < abs(best['delta']):
                best = {**a, 'delta': delta}
        if best:
            print(f'● {c["id"]} [{c["date"]}] {c["searchkey"]}')
            print(f'    {best["date"]}（差{best["delta"]:+d}天）{best["title"][:46]}')
            print(f'      {best["pdf"][:88]}')
            report.append({**c, **best})
        else:
            print(f'○ {c["id"]} [{c["date"]}] {c["searchkey"]}（±10天无上市类公告）')
    out = 'data/derived/cninfo_enrich_report.json'
    json.dump(report, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'—— 命中 {len(report)}/{len(cands)} → {out} ——')


def byregion(args):
    sys.path.insert(0, 'scripts')
    import geo_regloc
    places = json.load(open('data/places.json'))
    # 市名→（该市码 + 下辖县码集合）
    city_index = {}
    for c in places['cities']:
        city_index[c['short']] = c['code']
        city_index[c['name']] = c['code']
    county_of_city = {}
    for c in places['counties']:
        pref = c['code'][:4]
        county_of_city.setdefault(pref, []).append((c['code'], c['name']))

    MAP = 'data/derived/sec_region_map.json'
    try:
        reg = json.load(open(MAP, encoding='utf-8'))
    except Exception:
        reg = {}

    if args and args[0] == 'build':
        limit = int(args[1]) if len(args) > 1 else 999999
        import ssl as _ssl
        _h = urllib.request.HTTPSHandler(context=_ssl.create_default_context())
        _h.context = _ssl._create_unverified_context()
        _op2 = urllib.request.build_opener(urllib.request.ProxyHandler({}), _h)
        stock = json.loads(_op2.open(urllib.request.Request(
            'http://www.cninfo.com.cn/new/data/szse_stock.json',
            headers={'User-Agent': 'Mozilla/5.0'}), timeout=30).read(3000000))['stockList']
        ab = [x for x in stock if x['category'] == 'A股' and x['code'] not in reg]
        todo = ab[:limit]
        print(f'待建 {len(todo)}（已建 {len(reg)}，总量 {len(stock)}）')
        for i, x in enumerate(todo):
            code = x['code']
            try:
                addr = geo_regloc.fetch_address(code)
                hits = geo_regloc.map_places(addr, places) if addr else []
                reg[code] = {'name': x.get('zwjc', ''), 'addr': addr[:60],
                             'place': [h[0] for h in hits]} if addr else {'name': x.get('zwjc', ''), 'addr': '', 'place': []}
            except Exception as e:
                reg[code] = {'name': x.get('zwjc', ''), 'addr': f'ERR {str(e)[:30]}', 'place': []}
            if (i + 1) % 20 == 0:
                json.dump(reg, open(MAP, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
                print(f'  {i+1}/{len(todo)} 已缓存')
            time.sleep(0.4)
        json.dump(reg, open(MAP, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
        print(f'—— 映射现 {len(reg)} 条 → {MAP}')
        return

    # 过滤模式：byregion <市名>...
    want = set()
    for name in args:
        code = city_index.get(name)
        if not code:
            print(f'!! 未知市: {name}')
            continue
        want.add(code)
        for cc, cn in county_of_city.get(code, []):
            want.add(cc)
    rows = []
    for code, v in reg.items():
        if any(p in want for p in v.get('place', [])):
            rows.append({'code': code, 'name': v['name'], 'addr': v['addr'], 'place': v['place']})
    print(f'—— {"/".join(args)}: 注册地命中 {len(rows)} 家')
    for r in rows[:40]:
        print(f"  {r['code']} {r['name']}  {r['addr'][:40]}")


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == 'enrich':
        enrich(sys.argv[2])
    if len(sys.argv) >= 3 and sys.argv[1] == 'byregion':
        byregion(sys.argv[2:])
        return 0
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    searchkey = sys.argv[1]
    se_date = sys.argv[2] if len(sys.argv) > 2 else ''
    rows, total = query(searchkey, se_date)
    print(f'—— {searchkey} {se_date or "全时段"}（命中 {len(rows)}，库内总量 {total}）——')
    for a in rows:
        print(f'{a["date"]}  [{a["sec"] or "—"}] {a["name"][:8]}  {a["title"][:52]}')
        if a['pdf']:
            print(f'      {a["pdf"][:90]}')
    return 0

    return 0


if __name__ == '__main__':
    sys.exit(main())
