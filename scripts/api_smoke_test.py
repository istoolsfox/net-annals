#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""API 集成冒烟测试。用法: python3 scripts/api_smoke_test.py [BASE_URL]
默认 http://127.0.0.1:8400。全部通过退出码 0。
覆盖：根索引/三层准入/配额/限流/ETag/注入探测/写面关闭/数据集完整性。
环境变量 API_SMOKE_KEY：注入既有 key（同 IP 当日 3 把注册额度耗尽时用，
跳过 register 与 keyed 层检查而不误报）。"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

BASE = (sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8400').rstrip('/')
fails = []
skipped = []
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


def jget(path, headers=None):
    st, b, hd = call('GET', path, headers)
    try:
        return st, json.loads(b), hd
    except Exception:
        return st, None, hd


def check(name, cond, detail=''):
    print(f"{'✓' if cond else '✗'} {name}{(' — ' + str(detail)[:160]) if (detail and not cond) else ''}")
    if not cond:
        fails.append(name)


def skip(name):
    print(f'⊙ {name}（跳过）')
    skipped.append(name)


def main():
    # 0. 开放路径
    st, d, _ = jget('/api/v1/health')
    check('health 200', st == 200, st)
    check('health ok=true', isinstance(d, dict) and d.get('ok') is True, d)
    st, d, _ = jget('/api/v1/')
    check('根索引 200', st == 200 and isinstance(d, dict) and len(d.get('endpoints', [])) >= 10, st)

    # 1. key 获取（环境变量优先；register 同 IP 3 把/天，重复冒烟优雅跳过）
    key = os.environ.get('API_SMOKE_KEY')
    if key:
        print('⊙ register（API_SMOKE_KEY 已注入，跳过）')
        skipped.append('register')
    else:
        st, b, _ = call('POST', '/api/v1/keys/register',
                        {'Content-Type': 'application/json'}, b'{}')
        if st == 201:
            key = json.loads(b).get('key')
            check('register 201 + key', bool(key), (st, b[:120]))
        elif st == 429 and b'registration limit' in b:
            skip('register 201（今日该 IP 注册额度已耗尽）')
        else:
            check('register 201 + key', False, (st, b[:120]))

    st, b, _ = call('POST', '/api/v1/keys/register',
                    {'Content-Type': 'text/plain'}, b'{}')
    check('register 非 JSON Content-Type → 415', st == 415, st)

    kh = {'X-API-Key': key} if key else {}

    # 2. meta 与查询（带 key 时顺带验配额头）
    st, d, hd = jget('/api/v1/meta', kh)
    check('meta 200', st == 200, st)
    total = (d or {}).get('total', 0)
    check('meta total>0', total > 0, d)
    check('meta.datasets 存在', isinstance((d or {}).get('datasets'), dict), d)
    if key:
        check('X-Quota 头', 'x-quota-remaining' in hd, hd)

    st, d, _ = jget('/api/v1/events?year=1994&limit=5', kh)
    check('events year=1994', st == 200 and (d or {}).get('total', 0) > 0, st)
    eid = ((d or {}).get('items') or [{}])[0].get('id')
    st, d, _ = jget(f'/api/v1/events/{eid}', kh)
    check('events detail', st == 200 and (d or {}).get('id') == eid, st)
    st, d, _ = jget('/api/v1/events?sort=1;DROP%20TABLE', kh)
    check('注入形 sort → 400', st == 400, st)
    st, d, _ = jget('/api/v1/events?category=%27%20OR%201%3D1--', kh)
    check('注入形 category → 400', st == 400, st)
    st, d, _ = jget('/api/v1/events?layer=main', kh)
    check('非法 layer=main → 400', st == 400, st)
    st, d, _ = jget('/api/v1/search?q=%27%20OR%201%3D1--', kh)
    check('注入形 q 正常返回', st == 200 and isinstance((d or {}).get('items'), list), st)
    st, d, _ = jget('/api/v1/year/1994', kh)
    check('year 1994', st == 200 and (d or {}).get('total', 0) > 0, st)

    # 3. 通用数据集
    first_ids = {}
    for ds in ('persons', 'entities', 'works', 'groups'):
        st, d, _ = jget(f'/api/v1/{ds}?limit=3', kh)
        check(f'{ds} list', st == 200 and (d or {}).get('total', 0) > 0
              and len((d or {}).get('items', [])) <= 3, (st, d if st != 200 else ''))
        first_ids[ds] = ((d or {}).get('items') or [{}])[0].get('id')
    st, d, _ = jget(f"/api/v1/persons/{first_ids['persons']}", kh)
    check('persons detail', st == 200 and (d or {}).get('id') == first_ids['persons'], st)
    st, d, _ = jget('/api/v1/persons/x__%2F..%2Fetc', kh)
    check('persons 畸形 id → 400/404', st in (400, 404), st)
    st, d, _ = jget('/api/v1/notadataset', kh)
    check('未知数据集 → 404', st == 404, st)

    # 4. 写面必须关闭
    st, b, _ = call('GET', '/api/v1/ingest/gap-queue')
    check('ingest GET → 404', st == 404, st)
    st, b, _ = call('POST', '/api/v1/ingest/gap-queue',
                    {'Content-Type': 'application/json'}, b'{}')
    check('ingest POST → 404', st == 404, st)

    # 5. ETag/304
    st, b, hd = call('GET', '/api/v1/meta', kh)
    etag = hd.get('etag', '')
    check('ETag 头存在', bool(etag), hd)
    st, b, _ = call('GET', '/api/v1/meta', {**kh, 'If-None-Match': etag})
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

    print(f'—— smoke {len(fails)} failed / {len(skipped)} skipped ——')
    for f in fails:
        print('  FAIL:', f)
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
