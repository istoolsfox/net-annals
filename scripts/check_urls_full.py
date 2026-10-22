# -*- coding: utf-8 -*-
"""全库 URL 存活复检：并发验证，输出死链清单 JSON。"""
import json, glob, concurrent.futures, urllib.request, socket
from urllib.parse import quote, urlparse

OK = {200,201,202,203,204,206,301,302,303,307,308,401,403,405,406,418,429,567}

def check(args):
    eid, u = args
    p = urlparse(u)
    full = f'{p.scheme}://{p.netloc}{quote(p.path, safe="/%:@")}'
    req = urllib.request.Request(full, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        r = urllib.request.urlopen(req, timeout=12)
        code = r.getcode()
    except Exception as ex:
        code = getattr(ex, 'code', 0) or str(ex)[:20]
    alive = (code in OK) or (p.netloc == 'baike.baidu.com' and code == 403)
    return (eid, u, code, alive)

items = []
for f in sorted(glob.glob('data/events/*.json')):
    if '.parts' in f: continue
    for e in json.load(open(f)):
        for s in e['sources']:
            items.append((e['id'], s['url']))
print('total urls:', len(items))

dead = []
with concurrent.futures.ThreadPoolExecutor(max_workers=16) as ex:
    for i, res in enumerate(ex.map(check, items)):
        eid, u, code, alive = res
        if not alive:
            dead.append({'id': eid, 'url': u, 'code': str(code)})
        if (i+1) % 500 == 0:
            print(f'... {i+1}/{len(items)} dead so far: {len(dead)}')

json.dump(dead, open('data/events/.parts/dead_urls.json', 'w'), ensure_ascii=False, indent=1)
print(f'DONE: {len(items)} urls, {len(dead)} dead -> data/events/.parts/dead_urls.json')
