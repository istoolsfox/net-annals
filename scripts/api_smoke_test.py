#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""API 集成冒烟测试。用法: python3 scripts/api_smoke_test.py [BASE_URL]
默认 http://127.0.0.1:8400。全部通过退出码 0。
覆盖：三层准入 / 配额 / 限流 / ETag / 注入探测 / 写面关闭 / 数据集完整性。"""
import json
import sys
import time
import urllib.error
import urllib.request

BASE = (sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8400').rstrip('/')
fails = []
# 绕过 shell 代理环境变量（http_proxy 会把 127.0.0.1 也代理出去）
_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def call(method, path, headers=None, body=None):
    h = {k: str(v) for k, v in (headers or {}).items()}
    req = urllib.request.Request(BASE + path, method=method, headers=h, data=body)
    try:
        with _opener.open(req, timeout=10) as r:
            return r.status, r.read(), {k.lower(): v for k, v in r.headers.items()}
    except urllib.error.HTTPError as e:
        return e.code, e.read(), {k.lower(): v for k, v in e.headers.items()}


def jget(path, key=None, headers=None):
    h = dict(headers or {})
    if key:
        h['X-API-Key'] = key
    st, b, hd = call('GET', path, h)
    try:
        return st, json.loads(b), hd
    except Exception:
        return st, None, hd


def check(name, cond, detail=''):
    print(f"{'✓' if cond else '✗'} {name}{(' — ' + str(detail)[:160]) if (detail and not cond) else ''}")
    if not cond:
        fails.append(name)


def main():
    # 0. health（开放路径）
    st, d, _ = jget('/api/v1/health')
    check('health 200', st == 200, st)
    check('health ok=true', isinstance(d, dict) and d.get('ok') is True, d)

    # 1. 自助领取 + 契约
    st, b, _ = call('POST', '/api/v1/keys/register',
                    {'Content-Type': 'application/json'}, b'{}')
    key = (json.loads(b).get('key') if st == 201 else None)
    check('register 201 + key', st == 201 and key, (st, b[:120]))
    st, b, _ = call('POST', '/api/v1/keys/register',
                    {'Content-Type': 'text/plain'}, b'{}')
    check('register 非 JSON Content-Type → 415', st == 415, st)

    # 2. 带 key 全功能
    st, d, hd = jget('/api/v1/meta', key)
    check('meta 200', st == 200, st)
    total = (d or {}).get('total', 0)
    check('meta total>0', total > 0, d)
    check('meta.datasets 存在', isinstance((d or {}).get('datasets'), dict), d)
    check('X-Quota 头', 'x-quota-remaining' in hd, hd)

    st, d, _ = jget('/api/v1/events?year=1994&limit=5', key)
    check('events year=1994', st == 200 and (d or {}).get('total', 0) > 0, st)
    eid = ((d or {}).get('items') or [{}])[0].get('id')
    st, d, _ = jget(f'/api/v1/events/{eid}', key)
    check('events detail', st == 200 and (d or {}).get('id') == eid, st)
    st, d, _ = jget('/api/v1/events?sort=1;DROP%20TABLE', key)
    check('注入形 sort → 400', st == 400, st)
    st, d, _ = jget('/api/v1/events?category=%27%20OR%201%3D1--', key)
    check('注入形 category → 400', st == 400, st)
    st, d, _ = jget('/api/v1/search?q=%27%20OR%201%3D1--', key)
    check('注入形 q 正常返回', st == 200 and isinstance((d or {}).get('items'), list), st)
    st, d, _ = jget('/api/v1/year/1994', key)
    check('year 1994', st == 200 and (d or {}).get('total', 0) > 0, st)

    # 3. 通用数据集
    first_ids = {}
    for ds in ('persons', 'entities', 'works', 'groups'):
        st, d, _ = jget(f'/api/v1/{ds}?limit=3', key)
        check(f'{ds} list', st == 200 and (d or {}).get('total', 0) > 0
              and len((d or {}).get('items', [])) <= 3, (st, d if st != 200 else ''))
        first_ids[ds] = ((d or {}).get('items') or [{}])[0].get('id')
    st, d, _ = jget(f"/api/v1/persons/{first_ids['persons']}", key)
    check('persons detail', st == 200 and (d or {}).get('id') == first_ids['persons'], st)
    st, d, _ = jget('/api/v1/persons/x__%2F..%2Fetc', key)
    check('persons 畸形 id → 400/404', st in (400, 404), st)
    st, d, _ = jget('/api/v1/notadataset', key)
    check('未知数据集 → 404', st == 404, st)

    # 4. 写面必须关闭
    st, b, _ = call('GET', '/api/v1/ingest/gap-queue')
    check('ingest GET → 404', st == 404, st)
    st, b, _ = call('POST', '/api/v1/ingest/gap-queue',
                    {'Content-Type': 'application/json'}, b'{}')
    check('ingest POST → 404', st == 404, st)

    # 5. ETag/304
    st, b, hd = call('GET', '/api/v1/meta', {'X-API-Key': key or ''})
    etag = hd.get('etag', '')
    check('ETag 头存在', bool(etag), hd)
    st, b, _ = call('GET', '/api/v1/meta', {'X-API-Key': key, 'If-None-Match': etag})
    check('If-None-Match → 304', st == 304, st)

    # 6. 无效 key 探测 → 401（×3 不触发封禁=20）
    for i in range(3):
        st, b, _ = call('GET', '/api/v1/meta', {'X-API-Key': 'NA-' + 'f' * 48})
        check(f'无效 key → 401 #{i+1}', st == 401, st)
    st, b, _ = call('GET', '/api/v1/meta', {'X-API-Key': 'bad-shape'})
    check('畸形 key → 401', st == 401, st)

    # 7. 匿名层配额头 + 突发限流
    st, d, hd = jget('/api/v1/meta')
    check('anon X-Anon 头', 'x-anon-quota-remaining' in hd, hd)
    hits429 = 0
    for _ in range(24):
        st, _, _ = jget('/api/v1/meta')
        if st == 429:
            hits429 += 1
        time.sleep(0.02)
    check('突发 24 连发出现 429', hits429 >= 1, hits429)

    print(f'—— smoke {len(fails)} failed ——')
    for f in fails:
        print('  FAIL:', f)
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
