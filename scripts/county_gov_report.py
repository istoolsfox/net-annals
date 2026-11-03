#!/usr/bin/env python3
"""政府工作报告收割器 v0：县级报告可得性探测。
用法：
  python3 scripts/county_gov_report.py probe <县名> [县名...]   # 逐县探测报告页可得性
  python3 scripts/county_gov_report.py queue <candidates.json>  # 批量探测出队列
输出：data/derived/county_report_probe.json（机器只报告，不回写库）
搜索路径：DuckDuckGo HTML（限流敏感，q 间隔 3-8 秒）→ 候选 URL 逐个实测。
纪律：机器只报告；内容提取与入库一律人工/Agent 裁定后另行执行。
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request

OUT = 'data/derived/county_report_probe.json'
UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
YEAR = '2025'


def fetch(url, timeout=15):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read().decode('utf-8', 'ignore')


def sogou_search(query):
    """搜狗网页搜索：直接抽取结果页里的 gov.cn 真链（搜狗把真实地址内嵌在页里）。"""
    q = urllib.parse.quote(query)
    try:
        st, html = fetch(f'https://www.sogou.com/web?query={q}', timeout=20)
    except Exception as ex:
        print(f'    搜狗 FAIL: {str(ex)[:50]}')
        return []
    urls = []
    for m in re.finditer(r'https?://[A-Za-z0-9.-]+\.gov\.cn[^"\'<>\s)\\]*', html):
        u = m.group(0)
        if u not in urls and 'sogou' not in u:
            urls.append(u)
    return [(f'gov.cn 候选 {i+1}', u) for i, u in enumerate(urls[:6])]


def ddg_search(query):
    """（弃用）DuckDuckGo 反爬 202。保留占位。"""
    return []


def probe(county):
    """返回 {county, report_url, evidence_status, snippets}"""
    query = f'{county}{YEAR}年政府工作报告 全文'
    hits = sogou_search(query)
    time.sleep(4)
    picked = None
    for title, url in hits:
        # 优先政府域
        if re.search(r'\.gov\.cn', url):
            picked = (title, url)
            break
    # 启发式排序：路径含报告特征词的优先，门户根页靠后
    def score(u):
        p = u.lower()
        sc = 0
        for kw in ('zfgzbg', 'gzbg', 'gongzuobaogao', 'report'):
            if kw in p:
                sc += 10
        if re.search(r'/20\d{2}[01]\d/', p) or re.search(r'20\d{2}', p.split('/')[-1]):
            sc += 3
        if re.match(r'https?://[^/]+/?$', u):
            sc -= 8
        if any(k in p for k in ('index', 'xxgknb', 'category')):
            sc -= 5
        return sc
    hits = sorted(hits, key=lambda h: -score(h[1]))
    row = {'county': county, 'query': query, 'ddg_hits': len(hits),
           'candidates': [{'title': t, 'url': u} for t, u in hits[:5]]}
    if picked:
        # 逐个候选验证：县名 + 报告特征词 + 全文够长
        for title, url in hits[:4]:
            try:
                st, html = fetch(url)
                text = re.sub(r'<[^>]+>', '', html)
                ok = (county in text and '政府工作报告' in text
                      and len(text) > 8000 and '各位代表' in text)
                if ok:
                    row.update({'report_url': url, 'report_title': title,
                                'fetch_status': st, 'content_verified': True,
                                'content_len': len(text)})
                    break
                row.setdefault('tried', []).append({'url': url, 'len': len(text),
                                                    'has_county': county in text})
            except Exception as ex:
                row.setdefault('tried', []).append({'url': url, 'err': str(ex)[:40]})
        row.setdefault('report_url', row.get('report_url'))
    return row


def main():
    args = sys.argv[1:]
    if not args or args[0] not in ('probe', 'queue'):
        print(__doc__)
        return 1
    if args[0] == 'probe':
        counties = args[1:]
    else:
        counties = [c['name'] for c in json.load(open(args[1]))]
    rows = []
    for c in counties:
        print(f'探测 {c} …')
        rows.append(probe(c))
        time.sleep(4)
    json.dump(rows, open(OUT, 'w'), ensure_ascii=False, indent=1)
    ok = sum(1 for r in rows if r.get('content_verified'))
    print(f'—— 探测 {len(rows)} 县：报告页可验证 {ok} 个 → {OUT}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
