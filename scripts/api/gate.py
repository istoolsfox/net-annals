#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""准入中间件：路径分类 → 封禁 → 认证分层 → 配额 → 突发限流 → 并发上限 → ETag。
原则：SQLite/文件操作一律 run_in_threadpool（事件循环零阻塞）；
     所有拒绝都走统一 {"error": ...} 契约。"""
import hashlib
import ipaddress
import threading
import datetime

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
from starlette.responses import Response

from . import config, datasets, keys_store, ratelimit, usage_store

OPEN_PATHS = (config.API_PREFIX, config.API_PREFIX + 'health', config.API_PREFIX + 'keys/page')
REGISTER_PATH = config.API_PREFIX + 'keys/register'
_READ_TAILS = ('meta', 'events', 'year', 'search')
READ_PREFIXES = tuple([config.API_PREFIX + t for t in _READ_TAILS]
                      + [config.API_PREFIX + ds for ds in datasets.DATASET_IDS])

_conc = {}                       # ip → 在处理请求数
_conc_lock = threading.Lock()


def _deny(status, msg, headers=None):
    return JSONResponse(status_code=status, content={'error': msg}, headers=headers or {})


def _banned_msg(b):
    until, reason = b
    when = datetime.datetime.fromtimestamp(until).strftime('%H:%M')
    return f'banned until {when} ({reason})'


def _deny(status, msg, headers=None):
    h = {'Access-Control-Allow-Origin': '*', **(headers or {})}
    return JSONResponse(status_code=status, content={'error': msg}, headers=h)


def client_ip(request):
    """X-Real-IP 只在请求确实来自反代（peer 为回环）时才采信——nginx 必然覆盖该头；
    直连请求一律用 TCP 对端地址，防头伪造绕配额/投毒 bans 表。"""
    ip = request.headers.get('x-real-ip', '')
    peer = (request.client.host if request.client else 'unknown')[:64]
    if peer not in ('127.0.0.1', '::1'):
        return peer
    try:
        ipaddress.ip_address(ip)
        return ip
    except ValueError:
        return peer


def _classify(path):
    if path in OPEN_PATHS:
        return 'open'
    if path == REGISTER_PATH:
        return 'register'
    if any(path == p or path.startswith(p + '/') for p in READ_PREFIXES):
        return 'read'
    return 'unknown'


# ── 单 IP 并发上限：恶意并发兜底（nginx limit_conn 是第一道） ──────

def _conc_enter(ip):
    with _conc_lock:
        n = _conc.get(ip, 0)
        if n >= config.MAX_CONC_PER_IP:
            raise HTTPException(429, 'too many concurrent requests',
                                {'Retry-After': str(config.CONC_BURST_AFTER)})
        _conc[ip] = n + 1


def _conc_exit(ip):
    with _conc_lock:
        n = _conc.get(ip, 0) - 1
        if n <= 0:
            _conc.pop(ip, None)
        else:
            _conc[ip] = n


async def _on_probe(ip):
    """无效 key 探测；达阈值封 IP（写库入线程池）。"""
    if ratelimit.record_probe(ip):
        await run_in_threadpool(usage_store.ban, ip, config.BAN_HOURS, 'invalid-key probing')


# ── 分层准入 ──────────────────────────────────────────────────────

async def _require_no_ban(ip):
    b = await run_in_threadpool(usage_store.banned_since, ip)
    if b:
        raise HTTPException(403, _banned_msg(b))


async def _register_gate(request, call_next, ip):
    if request.method != 'POST':
        return _deny(405, 'POST required')
    if request.headers.get('content-type', '').split(';')[0].strip() != 'application/json':
        # 挡 text/plain 简单请求型 CSRF（跨站表单可代访客烧注册额度）
        return _deny(415, 'Content-Type must be application/json')
    origin = request.headers.get('origin', '')
    if origin:
        # 浏览器 POST 必带 Origin：跨源一律 403（显式拒绝，不依赖 CORS 中间件顺序这种偶然性质）
        host = request.headers.get('host', '')
        try:
            from urllib.parse import urlsplit
            if urlsplit(origin).netloc != host:
                return _deny(403, 'cross-origin registration not allowed')
        except ValueError:
            return _deny(403, 'bad origin')
    await _require_no_ban(ip)
    ratelimit.burst('reg:' + ip, 5)
    used = await run_in_threadpool(usage_store.peek, 'reg_daily', 'ip',
                                   usage_store.day_key(), ip)
    if used is not None and used >= config.REG_PER_IP_DAY:
        raise HTTPException(429, f'registration limit: {config.REG_PER_IP_DAY} keys/IP/day',
                            {'Retry-After': str(usage_store.seconds_to_midnight())})
    await run_in_threadpool(usage_store.bump, 'reg_daily', 'ip',
                            usage_store.day_key(), ip)
    resp = await call_next(request)
    resp.headers['Cache-Control'] = 'no-store'
    return resp


async def _read_gate(request, call_next, ip):
    await _require_no_ban(ip)
    raw = request.headers.get('x-api-key', '')
    if raw:
        if len(raw) > 64 or not config.RE_KEY.fullmatch(raw):
            await _on_probe(ip)
            raise HTTPException(401, 'malformed api key')
        k = await run_in_threadpool(keys_store.find, raw)
        if not k:
            await _on_probe(ip)
            raise HTTPException(401, 'invalid api key')
        is_admin = k.get('role') == 'admin'
        ratelimit.burst('key:' + k['id'],
                        config.ADMIN_PERMIN if is_admin else config.RO_PERMIN)
        quota = k.get('daily_quota')
        if quota is None and not is_admin:
            quota = config.DEFAULT_RO_QUOTA
        left = None
        if quota is not None:
            day = usage_store.day_key()
            used = await run_in_threadpool(usage_store.peek, 'key_usage', 'key_id',
                                           day, k['id'])
            if used is not None and used >= quota:
                raise HTTPException(429, f'daily quota {quota} exceeded',
                                    {'Retry-After': str(usage_store.seconds_to_midnight())})
            used = await run_in_threadpool(usage_store.bump, 'key_usage', 'key_id',
                                           day, k['id'])
            if used is None:
                used = quota   # fail-open：不再配额头，但请求放行
            left = max(0, quota - used)
        _conc_enter(ip)
        try:
            resp = await call_next(request)
        finally:
            _conc_exit(ip)
        if left is not None:
            resp.headers['X-Quota-Limit'] = str(quota)
            resp.headers['X-Quota-Remaining'] = str(left)
        resp.headers.setdefault('Cache-Control', 'private, max-age=600')
        return resp
    # 匿名层
    ratelimit.burst('ip:' + ip, config.ANON_PERMIN)
    day = usage_store.day_key()
    used = await run_in_threadpool(usage_store.peek, 'ip_usage', 'ip', day, ip)
    if used is not None and used >= config.ANON_DAILY:
        raise HTTPException(
            429, f'anonymous quota {config.ANON_DAILY}/day exceeded — '
                 f'get a free key at {config.API_PREFIX}keys/page',
            {'Retry-After': str(usage_store.seconds_to_midnight())})
    used = await run_in_threadpool(usage_store.bump, 'ip_usage', 'ip', day, ip)
    if used is None:
        used = config.ANON_DAILY - 1   # fail-open：请求放行，头显示接近满额
    _conc_enter(ip)
    try:
        resp = await call_next(request)
    finally:
        _conc_exit(ip)
    resp.headers['X-Anon-Quota-Remaining'] = str(max(0, config.ANON_DAILY - used))
    resp.headers['X-Get-Free-Key'] = config.API_PREFIX + 'keys/page'
    resp.headers['Cache-Control'] = 'public, max-age=600'
    return resp


# ── ETag/304：让合法高速客户端（爬虫/镜像）走条件请求省带宽 ─────────

def _etag_normalize(v):
    v = v.strip()
    if v.startswith('W/'):
        v = v[2:]
    return v.strip('"')


def _deny(status, msg, headers=None):
    h = {'Access-Control-Allow-Origin': '*', **(headers or {})}
    return JSONResponse(status_code=status, content={'error': msg}, headers=h)


async def _finalize(request, resp):
    resp.headers.setdefault('X-Content-Type-Options', 'nosniff')
    if request.method not in ('GET', 'HEAD') or resp.status_code != 200:
        return resp
    if 'application/json' not in resp.headers.get('content-type', ''):
        return resp
    if int(resp.headers.get('content-length') or 0) > config.MAX_ETAG_BYTES:
        return resp   # 大响应不做 ETag（免 MB 级内存/带宽缓冲放大）
    if not hasattr(resp, 'body'):
        # BaseHTTPMiddleware 包装的流式响应：消费迭代器重建为可求体的 Response
        body = b''
        async for chunk in resp.body_iterator:
            body += chunk
        resp = Response(content=body, status_code=resp.status_code,
                        headers=dict(resp.headers))
    etag = '"' + hashlib.md5(resp.body).hexdigest() + '"'
    inm = request.headers.get('if-none-match', '')
    if inm and _etag_normalize(inm) == _etag_normalize(etag):
        r304 = Response(status_code=304, headers={
            'ETag': etag,
            'Cache-Control': resp.headers.get('cache-control', ''),
            'Access-Control-Allow-Origin': '*'})
        return r304
    resp.headers['ETag'] = etag
    return resp


async def gate(request: Request, call_next):
    ip = client_ip(request)
    path = request.url.path
    kind = _classify(path)
    try:
        if kind == 'unknown':
            return _deny(404, 'not found')
        if request.method == 'POST':
            cl = request.headers.get('content-length')
            if cl is None:
                return _deny(411, 'content-length required')
            if cl.isdigit() and int(cl) > config.MAX_BODY_BYTES:
                return _deny(413, 'payload too large')
        if kind == 'open':
            resp = await call_next(request)
        elif kind == 'register':
            resp = await _register_gate(request, call_next, ip)
        else:
            resp = await _read_gate(request, call_next, ip)
        return await _finalize(request, resp)
    except HTTPException as e:
        return _deny(e.status_code, e.detail, e.headers or {})
    except ratelimit.RateLimited as r:
        headers = {'Retry-After': str(r.retry_after)} if r.retry_after else {}
        return _deny(429, r.message, headers)
