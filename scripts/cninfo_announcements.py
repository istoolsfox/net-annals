#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""巨潮资讯公告检索（公开 JSON 接口，实测可用）。

用法:
  python3 scripts/cninfo_announcements.py <searchkey> [YYYY-MM-DD~YYYY-MM-DD] [页大小]
  例: python3 scripts/cninfo_announcements.py 乖宝宠物 2023-08-01~2023-08-31

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


def main():
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
