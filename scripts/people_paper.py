#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""人民日报每日纸版抓取器（paper.people.com.cn 免费公开面）。

覆盖实测（2026-10-28）：静态页仅 2023-2024 年；2022 及以前=付费库(data.people.com.cn，
页面 403)；2025 起=JS SPA 未接入。1994 等 URL 返回 404。访问需带 Referer（版面页裸请求 403）。

用法:
  python3 scripts/people_paper.py date YYYY-MM-DD       # 列当日全部版面与文章标题
  python3 scripts/people_paper.py match <candidates.json> [--min 0.5]
      candidates: [{"id","date","title"}, ...]（同日条目合并取纸版）
      输出匹配报告（条目 vs 当日纸版文章，字符重叠比），机器只报告不回写库。

用途：给 2023-2024 的 single-source 条目补人民日报来源（升 verified 需人工确认匹配）。"""
import json
import re
import ssl
import sys
import time
import urllib.parse
import urllib.request

BASE = 'http://paper.people.com.cn/rmrb/html/'
UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126.0 Safari/537.36'}
_ctx = ssl.create_default_context()
_ctx.check_hostname = False
_ctx.verify_mode = ssl.CERT_NONE
_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}),
                                      urllib.request.HTTPSHandler(context=_ctx))

_A_RE = re.compile(r'<a[^>]+href=(["\']?)([^"\'>\s]*nw\.D110000renmrb[^"\'>\s]*\.htm)\1[^>]*>(.*?)</a>', re.S)
_NBS_RE = re.compile(r'href=(["\']?)([^"\'>\s]*nbs\.D110000renmrb[^"\'>\s]*\.htm)\1')
_TAG_RE = re.compile(r'<[^>]+>')


def _get(url, referer):
    h = dict(UA)
    h['Referer'] = referer
    last = None
    for i in range(3):                     # 403 限速退避重试
        try:
            r = _opener.open(urllib.request.Request(url, headers=h), timeout=15)
            return r.read(400000).decode('utf-8', 'ignore')
        except urllib.error.HTTPError as e:
            last = e
            if e.code in (403, 429):
                time.sleep(2 + i * 3)
                continue
            raise
    raise last


def date_base(date):
    y, m, d = date.split('-')
    return f'{BASE}{y}-{m}/{d}/'


def fetch_date(date, _cache={}):
    """返回 [(版面名, [文章(title,url)...])]；同进程内按日期缓存。"""
    if date in _cache:
        return _cache[date]
    base = date_base(date)
    first = base + 'nbs.D110000renmrb_01.htm'
    txt = _get(first, base)
    page_links = sorted({m[1] for m in _NBS_RE.findall(txt)})
    pages = []
    for p in page_links:
        url = urllib.parse.urljoin(first, p)
        if url == first:
            body = txt
        else:
            time.sleep(0.4)
            body = _get(url, first)
        for _q, href, inner in _A_RE.findall(body):
            title = _TAG_RE.sub('', inner).strip()
            if title:
                pages.append((url, urllib.parse.urljoin(url, href), title))
    # 版面名：从各版面页 <title> 或导航锚文本缺失时退化为页码
    out = {}
    for url, art_url, title in pages:
        page_no = re.search(r'_1?(\d+)\.htm', url)
        name = f'第{page_no.group(1) if page_no else "?"}版'
        out.setdefault(name, []).append({'title': title, 'url': art_url})
    result = [(k, v) for k, v in sorted(out.items())]
    _cache[date] = result
    return result


def _clean(s):
    return re.sub(r'[\s《》「」（）()、，。：:;；\-—·""\'""]', '', s)


def overlap(a, b):
    sa, sb = set(_clean(a)), set(_clean(b))
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / min(len(sa), len(sb))


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    cmd = sys.argv[1]
    if cmd == 'date':
        for name, arts in fetch_date(sys.argv[2]):
            print(f'── {name}（{len(arts)}篇）')
            for a in arts:
                print(f'  {a["title"][:44]}\n      {a["url"]}')
        return 0
    if cmd == 'match':
        import datetime
        cands = json.load(open(sys.argv[2], encoding='utf-8'))
        min_ratio = 0.5
        if '--min' in sys.argv:
            min_ratio = float(sys.argv[sys.argv.index('--min') + 1])
        hits = misses = nodata = 0
        for c in cands:
            # 报道滞后规律：事件日与次日两版都试（06-07 开考 → 06-08 见报）
            d = datetime.date(*(int(x) for x in c['date'].split('-')))
            dates = [c['date'], (d + datetime.timedelta(days=1)).isoformat()]
            best = None
            ok_date = None
            for dd in dates:
                try:
                    arts = [a for _, page_arts in fetch_date(dd) for a in page_arts]
                except Exception as e:
                    print(f'✗ {c["id"]} {dd}: 取纸版失败 {type(e).__name__}')
                    continue
                ok_date = dd
                for a in arts:
                    r = overlap(c['title'], a['title'])
                    if best is None or r > best[0]:
                        best = (r, a, dd)
            if best and best[0] >= min_ratio:
                hits += 1
                print(f'● {c["id"]} [{c["date"]}] {c["title"][:30]}')
                print(f'    匹配 {best[0]:.2f}（{best[2]}版）→ {best[1]["title"][:44]}')
                print(f'      {best[1]["url"]}')
            elif ok_date:
                misses += 1
                r = f'{best[0]:.2f}' if best else '-'
                print(f'○ {c["id"]} [{c["date"]}] {c["title"][:30]}（最佳 {r}）')
            else:
                nodata += 1
        print(f'—— 匹配 {hits} / 未中 {misses} / 取数失败 {nodata} ——')
        return 0
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main())
