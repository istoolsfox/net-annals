#!/usr/bin/env python3
"""市级政府「大事记」栏目探测器 v0（C10 本地侧：n8n 工作流的前置队列）。
用法：
  python3 scripts/city_chronicle.py probe <市名> [市名...]   # 逐市探测大事记栏目页
  python3 scripts/city_chronicle.py queue <cities.json>      # 批量探测（[{name,code,province}]）
输出：data/derived/city_chronicle_probe.json（机器只报告，不回写库）
搜索路径：搜狗结果页直抽 gov.cn 真链（复用 county_gov_report 模式，DDG 反爬已弃用）。
验证：页面含「大事记」栏目特征 + 事件行（年份+动词/数字）密度。
纪律：机器只报告；内容提取与入库一律人工/Agent 裁定后另行执行。
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request

OUT = 'data/derived/city_chronicle_probe.json'
UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}

# 大事记条目行特征：行首/段首年份 + 后续含事件动词或数字规模词
EVENT_WORDS = ('成立', '设立', '开通', '通车', '通航', '投产', '获批', '奠基', '落成',
               '举行', '召开', '签署', '揭牌', '启用', '建成', '发生', '划定', '撤',
               '并入', '更名为', '入选', '获评', '开工')
YEAR_RE = re.compile(r'(19[78]\d|20[0-2]\d)年')


def fetch(url, timeout=15):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
    for enc in ('utf-8', 'gb18030'):
        try:
            return r.status, raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return r.status, raw.decode('utf-8', 'ignore')


def sogou_search(query):
    """搜狗网页搜索：直抽结果页里的 gov.cn 真链。"""
    q = urllib.parse.quote(query)
    try:
        _st, html = fetch(f'https://www.sogou.com/web?query={q}', timeout=20)
    except Exception as ex:
        print(f'    搜狗 FAIL: {str(ex)[:50]}')
        return []
    urls = []
    for m in re.finditer(r'https?://[A-Za-z0-9.-]+\.gov\.cn[^"\'<>\s)\\]*', html):
        u = m.group(0)
        if u not in urls and 'sogou' not in u:
            urls.append(u)
    return urls[:8]


def score_url(u):
    """大事记栏目启发式：路径/标题含特征词加权，门户根页降权。"""
    p = u.lower()
    sc = 0
    for kw, w in (('dsj', 10), ('dashiji', 10), ('大事记', 10), ('sznews', 3),
                  ('zhaobiao', -3), ('zwgk', 2), ('xxgk', 2)):
        if kw in p:
            sc += w
    if re.search(r'/20\d{2}[01]\d/', p) or re.search(r'20\d{2}', p.split('/')[-1]):
        sc += 2
    if re.match(r'https?://[^/]+/?$', u):
        sc -= 8
    for kw in ('index', 'col', 'category', 'list'):
        if kw in p:
            sc -= 2
    return sc


def verify_chronicle(url, city):
    """页面验证：含「大事记」字样 + 事件行密度（≥5 行含年份+事件词）。"""
    try:
        st, html = fetch(url)
    except Exception as ex:
        return {'url': url, 'err': str(ex)[:60]}
    text = re.sub(r'<script.*?</script>|<style.*?</style>', '', html, flags=re.S)
    text = re.sub(r'<[^>]+>', '\n', text)
    lines = [ln.strip() for ln in text.split('\n') if ln.strip()]
    has_kw = any('大事记' in ln for ln in lines)
    event_rows = [ln for ln in lines
                  if YEAR_RE.search(ln) and len(ln) > 12
                  and any(w in ln for w in EVENT_WORDS)]
    return {'url': url, 'status': st, 'has_keyword': has_kw,
            'event_rows': len(event_rows),
            'sample': event_rows[:3], 'content_len': len(text)}


def probe(city):
    """返回 {city, chronicle_url, verified, candidates}"""
    query = f'{city}政府 大事记'
    hits = sogou_search(query)
    time.sleep(4)
    hits.sort(key=score_url, reverse=True)
    row = {'city': city, 'query': query,
           'candidates': [{'url': u, 'score': score_url(u)} for u in hits[:5]]}
    for u in hits[:4]:
        v = verify_chronicle(u, city)
        row.setdefault('tried', []).append(v)
        ok = v.get('has_keyword') and v.get('event_rows', 0) >= 5
        if ok:
            row.update({'chronicle_url': u, 'verified': True,
                        'event_rows': v['event_rows'], 'sample': v['sample']})
            break
    return row


def main():
    args = sys.argv[1:]
    if not args or args[0] not in ('probe', 'queue'):
        print(__doc__)
        return 1
    if args[0] == 'probe':
        cities = args[1:]
    else:
        cities = [c['name'] for c in json.load(open(args[1]))]
    rows = []
    for c in cities:
        print(f'探测 {c} …')
        rows.append(probe(c))
        time.sleep(4)
    json.dump(rows, open(OUT, 'w'), ensure_ascii=False, indent=1)
    ok = sum(1 for r in rows if r.get('verified'))
    print(f'—— 探测 {len(rows)} 市：大事记栏目可验证 {ok} 个 → {OUT}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
