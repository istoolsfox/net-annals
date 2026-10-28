#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""net-annals 公共 API v1（FastAPI + SQLite）——三层公开访问模型。

层        认证      配额                      端点
anon     无 key    IP 200次/天 + 20次/分     health/meta/events/year/search
ro key   自助领取  key 2000次/天(可调)       同上全部只读端点
admin    手动签发  不限日配额                ingest/status

安全与可靠性设计（2026-10-28 四路对抗评审后重构）：
  · SQL 注入：全部查询 ? 参数化；枚举白名单；LIMIT/OFFSET 强制 int；LIKE 转义（ESCAPE '\'）
  · 配额/封禁：usage.db 持久化（单例长连接+WAL+synchronous=NORMAL，全程 _usage_lock 串行，
    中间件经 run_in_threadpool 调用——事件循环零阻塞）；日界由调用方固定传入防午夜错位
  · 滥用：无效 key 探测 20次/10分 → 封 IP 1h；限流字典定期清扫防无界增长；429 带 Retry-After
  · 认证：sha256 摘要字典查找 + compare_digest 复核；密钥文件 0600 + flock + 原子替换写入；
    文件缺失自动初始化；解析失败保留旧缓存并告警
  · 错误契约：全站统一 {"error": ...}（含 StarletteHTTPException/RequestValidationError 转换）
  · 可观测：全局 500 落 logging.exception（入 journald）
  · 运行面：只绑 127.0.0.1 走 nginx /api/；文档页关闭；管线子进程用 sys.executable
启动: uvicorn scripts.api_server:app --host 127.0.0.1 --port 8400"""
import fcntl
import hashlib
import hmac
import ipaddress
import json
import logging
import os
import re
import secrets
import sqlite3
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException as StarletteHTTPException

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger('netannals-api')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(PROJECT_ROOT)
DB_PATH = 'data/derived/api/events.db'
KEY_FILE = 'config/api_keys.json'
KEY_LOCK = 'config/.api_keys.lock'
USAGE_DB = 'data/derived/api/usage.db'
PIPE_LOG = 'data/derived/api/pipeline.log'
PIPE_LOCK = 'data/derived/api/pipeline.lock'
INGEST_DIR = 'data/derived/gap'

ANON_DAILY = 200            # 匿名层：IP 每日配额
ANON_PERMIN = 20            # 匿名层：每分钟突发
RO_PERMIN = 120             # ro：每分钟突发
ADMIN_PERMIN = 30           # admin：每分钟突发
REG_PER_IP_DAY = 3          # 每 IP 每天可领 key 数
DEFAULT_RO_QUOTA = 2000     # ro 默认日配额（api_keys.json --quota 可覆盖）

app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)
app.add_middleware(CORSMiddleware, allow_origins=['*'],
                   allow_methods=['GET', 'HEAD'], allow_headers=['X-API-Key'])

# ── usage.db：单例长连接 + 全局锁（配额/封禁/注册计数） ──────────────
_usage_lock = threading.Lock()
_usage_conn = None


def _usage():
    """进程内单例 rw 连接（WAL + synchronous=NORMAL 启动时设一次）。"""
    global _usage_conn
    if _usage_conn is None:
        os.makedirs(os.path.dirname(USAGE_DB), exist_ok=True)
        conn = sqlite3.connect(USAGE_DB, timeout=5, check_same_thread=False)
        conn.row_factory = sqlite3.Row   # 不设则 fetchone 返回元组，字典取键会崩（踩过的坑）
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA synchronous=NORMAL')
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS key_usage(key_id TEXT, day TEXT, count INTEGER, PRIMARY KEY(key_id, day));
        CREATE TABLE IF NOT EXISTS ip_usage(day TEXT, ip TEXT, count INTEGER, PRIMARY KEY(day, ip));
        CREATE TABLE IF NOT EXISTS reg_daily(day TEXT, ip TEXT, count INTEGER, PRIMARY KEY(day, ip));
        CREATE TABLE IF NOT EXISTS bans(ip TEXT PRIMARY KEY, until INTEGER, reason TEXT);
        """)
        conn.commit()
        _usage_conn = conn
    return _usage_conn


def _bump(table, cols, day, ident):
    """计数+1 并返回当日已用次数。day 由调用方传入（防跨午夜 INSERT/SELECT 错位）。"""
    with _usage_lock:
        conn = _usage()
        conn.execute(
            f'INSERT INTO {table}(day,{cols},count) VALUES(?,?,1) '
            f'ON CONFLICT(day,{cols}) DO UPDATE SET count=count+1', (day, ident))
        row = conn.execute(
            f'SELECT count FROM {table} WHERE day=? AND {cols}=?', (day, ident)).fetchone()
        conn.commit()
        return row[0]


def _banned(ip):
    """封禁检查：fail-open——usage.db 故障时放行并告警，绝不因配额库拖死全站。"""
    try:
        with _usage_lock:
            conn = _usage()
            r = conn.execute('SELECT until, reason FROM bans WHERE ip=?', (ip,)).fetchone()
    except sqlite3.Error as e:
        log.warning('bans check failed (fail-open): %s', e)
        return
    if r and r['until'] > time.time():
        raise HTTPException(403, f'banned until {datetime.fromtimestamp(r["until"]).strftime("%H:%M")} ({r["reason"]})')
    if r:
        with _usage_lock:
            try:
                _usage().execute('DELETE FROM bans WHERE ip=?', (ip,))
                _usage().commit()
            except sqlite3.Error as e:
                log.warning('bans cleanup failed: %s', e)


def _ban(ip, hours, reason):
    with _usage_lock:
        conn = _usage()
        conn.execute('INSERT INTO bans VALUES(?,?,?) ON CONFLICT(ip) DO UPDATE SET until=excluded.until, reason=excluded.reason',
                     (ip, time.time() + hours * 3600, reason))
        conn.commit()


def _prune_usage(days=45):
    """usage.db 保留策略：清理 N 天前的计数行（管线每周调用一次）。"""
    with _usage_lock:
        conn = _usage()
        for t in ('key_usage', 'ip_usage', 'reg_daily'):
            conn.execute(f"DELETE FROM {t} WHERE day < date('now', ?)", (f'-{days} day',))
        conn.execute('DELETE FROM bans WHERE until < ?', (time.time(),))
        conn.commit()


def _seconds_to_midnight():
    now = datetime.now()
    return (86400 - (now.hour * 3600 + now.minute * 60 + now.second)) + 60


def day_key():
    return time.strftime('%Y-%m-%d')

# ── 密钥库（sha256 摘要 + compare_digest 复核；热加载；原子写） ──────
_keys_cache = {'mtime': 0, 'map': {}}


def _load_keys():
    try:
        mt = os.path.getmtime(KEY_FILE)
        if mt != _keys_cache['mtime']:
            d = json.load(open(KEY_FILE, encoding='utf-8'))
            _keys_cache['map'] = {k['key_sha256']: k for k in d.get('keys', [])}
            _keys_cache['mtime'] = mt
    except FileNotFoundError:
        _keys_cache['map'] = {}
        _keys_cache['mtime'] = 0
    except Exception as e:
        log.warning('KEY_FILE 解析失败，沿用旧缓存（%s）', e)
    return _keys_cache['map']


def _find_key(raw):
    """raw 明文 → 密钥条目。摘要字典查找 + compare_digest 复核。"""
    digest = hashlib.sha256(raw.encode()).hexdigest()
    k = _load_keys().get(digest)
    if k and hmac.compare_digest(k['key_sha256'], digest):
        return k
    return None


def _save_keys_atomic_locked(d):
    """调用方已持 KEY_LOCK 时的原子写。"""
    tmp = KEY_FILE + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
        f.flush()
        os.fsync(f.fileno())
    os.chmod(tmp, 0o600)
    os.replace(tmp, KEY_FILE)
_hits = defaultdict(deque)
_probes = defaultdict(deque)
_rl_lock = threading.Lock()
_last_sweep = time.time()


def _sweep(now):
    """低频清扫：删掉空/过期 deque 与陈旧探测键，防海量假 IP 撑爆内存。"""
    global _last_sweep
    with _rl_lock:
        if now - _last_sweep < 300 or len(_hits) + len(_probes) < 2048:
            return
        for d in (_hits, _probes):
            stale = [k for k, q in d.items() if not q or q[-1] < now - 3600]
            for k in stale:
                d.pop(k, None)
        _last_sweep = now


def _burst(subject, limit):
    now = time.time()
    _sweep(now)
    with _rl_lock:
        q = _hits[subject]
        while q and q[0] < now - 60:
            q.popleft()
        if len(q) >= limit:
            raise HTTPException(429, 'rate limit exceeded, retry later', {'Retry-After': '60'})
        q.append(now)


_probes_lock = threading.Lock()


def _record_probe(ip):
    now = time.time()
    with _probes_lock:
        q = _probes[ip]
        while q and q[0] < now - 600:
            q.popleft()
        q.append(now)
        hot = len(q) >= 20
        if hot:
            _probes.pop(ip, None)
    if hot:
        _ban(ip, 1, 'invalid-key probing')


def _client_ip(request):
    ip = request.headers.get('x-real-ip', '')
    # 仅信任合法 IP 字面量（nginx 强制覆盖后的产物）；畸形/缺失回落直连地址
    try:
        ipaddress.ip_address(ip)
        return ip
    except ValueError:
        return (request.client.host if request.client else 'unknown')[:64]

# ── 管线忙闲：与管线共用同一把 flock（存在性≠持有） ─────────────────


def _pipeline_busy():
    fd = os.open(PIPE_LOCK, os.O_RDWR | os.O_CREAT)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return False   # 抢到锁 = 管线空闲（随即释放；admin 单人触发，竞态窗口可接受）
    except BlockingIOError:
        return True
    finally:
        os.close(fd)

# ── 中间件：封禁/认证/配额/限流（DB 操作全部入线程池） ───────────────
ADMIN_PATHS = ('/api/v1/ingest/',)
READ_PATHS = ('/api/v1/meta', '/api/v1/events', '/api/v1/year/', '/api/v1/search')
OPEN_PATHS = ('/api/v1/health', '/api/v1/keys/page')


@app.middleware('http')
async def gate(request: Request, call_next):
    ip = _client_ip(request)
    path = request.url.path
    try:
        if not path.startswith('/api/v1/'):
            return JSONResponse(status_code=404, content={'error': 'not found'})
        if path in OPEN_PATHS:
            return await call_next(request)
        await run_in_threadpool(_banned, ip)

        if path.startswith(ADMIN_PATHS):
            k = await run_in_threadpool(_require_key, request, ip, 'admin')
            _burst('key:' + k['id'], ADMIN_PERMIN)
            resp = await call_next(request)
            return resp

        if path == '/api/v1/keys/register':
            if request.method != 'POST':
                return JSONResponse(status_code=405, content={'error': 'POST required'})
            if request.headers.get('content-type', '').split(';')[0].strip() != 'application/json':
                # 挡 text/plain 简单请求型 CSRF（跨站表单可代访客烧注册额度）
                return JSONResponse(status_code=415, content={'error': 'Content-Type must be application/json'})
            used = await run_in_threadpool(_bump, 'reg_daily', 'ip', day_key(), ip)
            if used > REG_PER_IP_DAY:
                raise HTTPException(429, f'registration limit: {REG_PER_IP_DAY} keys/IP/day',
                                    {'Retry-After': str(_seconds_to_midnight())})
            resp = await call_next(request)
            resp.headers['Cache-Control'] = 'no-store'
            return resp

        if path in READ_PATHS or path.startswith(('/api/v1/events/', '/api/v1/year/')):
            raw = request.headers.get('x-api-key', '')
            if raw:
                if len(raw) > 64 or not re.fullmatch(r'NA-[0-9a-f]{48}', raw):
                    await run_in_threadpool(_record_probe, ip)
                    raise HTTPException(401, 'malformed api key')
                k = await run_in_threadpool(_find_key, raw)
                if not k:
                    await run_in_threadpool(_record_probe, ip)
                    raise HTTPException(401, 'invalid api key')
                is_admin = k.get('role') == 'admin'
                _burst('key:' + k['id'], ADMIN_PERMIN if is_admin else RO_PERMIN)
                quota = k.get('daily_quota')
                if quota is None and not is_admin:
                    quota = DEFAULT_RO_QUOTA
                left = None
                if quota is not None:
                    used = await run_in_threadpool(_bump, 'key_usage', 'key_id', day_key(), k['id'])
                    if used > quota:
                        raise HTTPException(429, f'daily quota {quota} exceeded',
                                            {'Retry-After': str(_seconds_to_midnight())})
                    left = max(0, quota - used)
                resp = await call_next(request)
                if left is not None:
                    resp.headers['X-Quota-Limit'] = str(quota)
                    resp.headers['X-Quota-Remaining'] = str(left)
                return resp
            # 匿名层
            _burst('ip:' + ip, ANON_PERMIN)
            used = await run_in_threadpool(_bump, 'ip_usage', 'ip', day_key(), ip)
            if used > ANON_DAILY:
                raise HTTPException(429, f'anonymous quota {ANON_DAILY}/day exceeded — get a free key at /api/v1/keys/page',
                                    {'Retry-After': str(_seconds_to_midnight())})
            resp = await call_next(request)
            resp.headers['X-Anon-Quota-Remaining'] = str(max(0, ANON_DAILY - used))
            resp.headers['X-Get-Free-Key'] = '/api/v1/keys/page'
            resp.headers['Cache-Control'] = 'public, max-age=600'
            return resp

        return await call_next(request)
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code,
                            content={'error': e.detail},
                            headers=e.headers or {})


def _require_key(request, ip, role):
    raw = request.headers.get('x-api-key', '')
    if not raw or len(raw) > 64 or not re.fullmatch(r'NA-[0-9a-f]{48}', raw):
        _record_probe(ip)
        raise HTTPException(401, 'missing or malformed api key')
    k = _find_key(raw)
    if not k:
        _record_probe(ip)
        raise HTTPException(401, 'invalid api key')
    if role == 'admin' and k.get('role') != 'admin':
        raise HTTPException(403, 'admin role required')
    return k


@app.exception_handler(StarletteHTTPException)
async def _http_exc(request, exc):
    return JSONResponse(status_code=exc.status_code, content={'error': exc.detail},
                        headers=getattr(exc, 'headers', None) or {})


@app.exception_handler(RequestValidationError)
async def _validation_exc(request, exc):
    return JSONResponse(status_code=400, content={'error': 'invalid parameters'},
                        headers=getattr(exc, 'headers', None) or {})


@app.exception_handler(Exception)
async def _unhandled(request, exc):
    log.exception('unhandled error on %s %s', request.method, request.url.path)
    return JSONResponse(status_code=500, content={'error': 'internal error'})

# ── 数据访问 ─────────────────────────────────────────────────────────
RE_YEAR = re.compile(r'(19|20)\d{2}')
RE_DATE = re.compile(r'\d{4}-\d{2}-\d{2}')
RE_ID = re.compile(r'[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z0-9][a-z0-9-]{1,100}')
RE_LAYER = re.compile(r'[a-z0-9]{0,16}')
CATEGORIES = {'milestone', 'internet', 'tech', 'hardware', 'company', 'product',
              'national', 'world', 'society', 'culture', 'economy'}
REGIONS = {'cn', 'world'}
SORTS = {'date_asc': 'date ASC, id ASC', 'date_desc': 'date DESC, id DESC'}


def _db():
    if not os.path.exists(DB_PATH):
        raise HTTPException(503, 'database not ready')
    conn = sqlite3.connect(f'file:{DB_PATH}?mode=ro', uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _like_escape(q):
    return q.replace('\\', '\\\\').replace('%', r'\%').replace('_', r'\_')


def _row_to_event(r):
    return {
        'id': r['id'], 'date': r['date'], 'title': r['title'],
        'category': r['category'], 'region': r['region'],
        'milestone': bool(r['milestone']),
        'summary_30s': r['summary'], 'detail': r['detail'],
        'impact': r['impact'], 'aftermath': r['aftermath'],
        'tags': json.loads(r['tags'] or '[]'),
        'sources': json.loads(r['sources'] or '[]'),
        'date_confidence': r['date_confidence'], 'date_accuracy': r['date_accuracy'],
        'layer': r['layer'],
    }

# ── 只读端点 ─────────────────────────────────────────────────────────
@app.get('/api/v1/health')
def health():
    if not os.path.exists(DB_PATH):
        return {'ok': False}
    conn = _db()
    try:
        total = conn.execute("SELECT value FROM meta WHERE key='total'").fetchone()
        gen = conn.execute("SELECT value FROM meta WHERE key='generated'").fetchone()
    finally:
        conn.close()
    return {'ok': bool(total), 'total': int(total['value']) if total else 0,
            'db_generated': gen['value'] if gen else None,
            'tiers': {'anonymous': f'{ANON_DAILY}/day per IP',
                      'free_key': f'{DEFAULT_RO_QUOTA}/day (self-service)',
                      'docs': '/api/v1/keys/page'}}


@app.get('/api/v1/meta')
def meta():
    conn = _db()
    m = dict(conn.execute('SELECT key, value FROM meta').fetchall())
    conn.close()
    return {'total': int(m['total']), 'categories': json.loads(m['categories']),
            'layers': json.loads(m['layers']),
            'year_range': [int(m['year_min']), int(m['year_max'])],
            'db_generated': m['generated']}


@app.get('/api/v1/events')
def list_events(year: str = '', date_from: str = '', date_to: str = '',
                category: str = '', region: str = '', layer: str = '',
                q: str = '', page: int = 0, limit: int = 50, sort: str = 'date_asc'):
    if sort not in SORTS:
        raise HTTPException(400, 'bad sort')
    if year and not RE_YEAR.fullmatch(year):
        raise HTTPException(400, 'bad year')
    for d in (date_from, date_to):
        if d and not RE_DATE.fullmatch(d):
            raise HTTPException(400, 'bad date, expect YYYY-MM-DD')
    if date_from and date_to and date_from > date_to:
        raise HTTPException(400, 'date_from > date_to')
    if category and category not in CATEGORIES:
        raise HTTPException(400, 'bad category')
    if region and region not in REGIONS:
        raise HTTPException(400, 'bad region')
    if layer and not RE_LAYER.fullmatch(layer):
        raise HTTPException(400, 'bad layer')
    q = q.strip()
    if len(q) > 64:
        raise HTTPException(400, 'q too long (max 64)')
    page = max(0, min(int(page), 5000))
    limit = max(1, min(int(limit), 200))
    where, params = [], []
    if year:
        where.append('year = ?')
        params.append(int(year))
    if date_from:
        where.append('date >= ?')
        params.append(date_from)
    if date_to:
        where.append('date <= ?')
        params.append(date_to)
    if category:
        where.append('category = ?')
        params.append(category)
    if region:
        where.append('region = ?')
        params.append(region)
    if layer:
        where.append('layer = ?')
        params.append(layer)
    if q:
        for w in q.split()[:6]:
            where.append('search LIKE ? ESCAPE "\\"')
            params.append(f'%{_like_escape(w)}%')
    clause = ('WHERE ' + ' AND '.join(where)) if where else ''
    conn = _db()
    total = conn.execute(f'SELECT COUNT(*) c FROM events {clause}', params).fetchone()['c']
    rows = conn.execute(
        f'SELECT * FROM events {clause} ORDER BY {SORTS[sort]} LIMIT ? OFFSET ?',
        params + [limit, page * limit]).fetchall()
    conn.close()
    return {'total': total, 'page': page, 'limit': limit,
            'items': [_row_to_event(r) for r in rows]}


@app.get('/api/v1/events/{eid}')
def get_event(eid: str):
    if not RE_ID.fullmatch(eid):
        raise HTTPException(400, 'bad event id')
    conn = _db()
    r = conn.execute('SELECT * FROM events WHERE id = ?', (eid,)).fetchone()
    conn.close()
    if not r:
        raise HTTPException(404, 'not found')
    return _row_to_event(r)


@app.get('/api/v1/year/{year}')
def by_year(year: int):
    if not (1970 <= year <= 2100):
        raise HTTPException(400, 'year out of range')
    conn = _db()
    rows = conn.execute('SELECT * FROM events WHERE year = ? ORDER BY date, id LIMIT 2000',
                        (year,)).fetchall()
    conn.close()
    return {'year': year, 'total': len(rows), 'items': [_row_to_event(r) for r in rows]}


@app.get('/api/v1/search')
def search(q: str = '', limit: int = 20):
    q = q.strip()
    if not q or len(q) > 64:
        raise HTTPException(400, 'q required, max 64 chars')
    limit = max(1, min(int(limit), 50))
    words = q.split()[:6]
    where, params = [], []
    for w in words:
        where.append('search LIKE ? ESCAPE "\\"')
        params.append(f'%{_like_escape(w)}%')
    clause = 'WHERE ' + ' AND '.join(where)
    # 相关度：逐词加权（标题30/标签12/摘要6/正文2），占位符出现在 SELECT（先于 WHERE 绑定）
    score_cases, score_params = [], []
    for w in words:
        pw = f'%{_like_escape(w)}%'
        score_cases.append("(CASE WHEN title LIKE ? ESCAPE '\\' THEN 30 ELSE 0 END"
                           " + CASE WHEN tags LIKE ? ESCAPE '\\' THEN 12 ELSE 0 END"
                           " + CASE WHEN summary LIKE ? ESCAPE '\\' THEN 6 ELSE 0 END"
                           " + CASE WHEN detail LIKE ? ESCAPE '\\' THEN 2 ELSE 0 END)")
        score_params += [pw] * 4
    conn = _db()
    rows = conn.execute(
        f'SELECT *, ({"+".join(score_cases)}) sc FROM events {clause} '
        'ORDER BY sc DESC, date DESC, id LIMIT ?',
        score_params + params + [limit]).fetchall()
    conn.close()
    return {'q': q, 'returned': len(rows),
            'items': [dict(_row_to_event(r), _score=r['sc']) for r in rows]}

# ── 自助领取 ─────────────────────────────────────────────────────────
@app.post('/api/v1/keys/register')
async def register_key(request: Request):
    try:
        body = json.loads(await request.body() or b'{}')
    except Exception:
        raise HTTPException(400, 'invalid json')
    contact = str(body.get('contact', ''))[:120] if isinstance(body, dict) else ''
    name = f"public-{time.strftime('%Y%m%d')}-{secrets.token_hex(2)}"
    lock_fd = os.open(KEY_LOCK, os.O_RDWR | os.O_CREAT)
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        try:
            d = json.load(open(KEY_FILE, encoding='utf-8'))
        except FileNotFoundError:
            d = {'keys': []}
        while any(k['id'] == name for k in d['keys']):
            name += secrets.token_hex(1)
        raw = 'NA-' + secrets.token_hex(24)
        d['keys'].append({'id': name, 'key_sha256': hashlib.sha256(raw.encode()).hexdigest(),
                          'role': 'ro', 'daily_quota': DEFAULT_RO_QUOTA, 'contact': contact,
                          'created': datetime.now().astimezone().isoformat(timespec='seconds')})
        _save_keys_atomic_locked(d)
    finally:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        os.close(lock_fd)
    return {'ok': True, 'key': raw, 'role': 'ro', 'daily_quota': DEFAULT_RO_QUOTA,
            'note': '请妥善保存（服务器只存哈希，无法找回）。使用时携带请求头 X-API-Key。'
                    '请标注数据来源 toolsfox.cn；禁止将其用于违法违规用途。',
            'docs': '/api/v1/keys/page'}


@app.get('/api/v1/keys/page', response_class=HTMLResponse)
def keys_page():
    with open(os.path.join('site', 'assets', 'keys_page.html'), encoding='utf-8') as f:
        return f.read()

# ── 管理端点 ─────────────────────────────────────────────────────────
@app.post('/api/v1/ingest/gap-queue')
async def ingest_gap_queue(request: Request):
    if _pipeline_busy():
        raise HTTPException(409, 'pipeline busy')
    body = await request.body()
    if len(body) > 262144:
        raise HTTPException(413, 'payload too large')
    try:
        d = json.loads(body)
        assert isinstance(d, dict) and isinstance(d.get('candidates'), list)
        for c in d['candidates'][:5000]:
            assert isinstance(c, dict) and all(k in c for k in ('date_text', 'title', 'quote', 'source', 'year'))
            assert isinstance(c['year'], int) and len(c['quote']) < 500 and len(str(c['source'])) < 500
    except Exception:
        raise HTTPException(400, 'invalid gap queue payload')
    os.makedirs(INGEST_DIR, exist_ok=True)
    stamp = time.strftime('%Y-%m-%d-%H%M%S')
    path = os.path.join(INGEST_DIR, f'gap_queue_{stamp}.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False)
    os.chmod(path, 0o600)
    import subprocess
    import sys
    logf = open(PIPE_LOG, 'ab')
    try:
        subprocess.Popen([sys.executable, 'scripts/auto_pipeline.py', '--queue', path],
                         stdout=logf, stderr=subprocess.STDOUT,
                         cwd=os.getcwd(), start_new_session=True)
    finally:
        logf.close()   # 父侧句柄即关（子进程已持有继承副本），防 fd 泄漏
    return {'ok': True, 'queue_saved': path, 'candidates': len(d['candidates']),
            'note': 'pipeline started, poll /api/v1/ingest/status'}


@app.get('/api/v1/ingest/status')
def ingest_status():
    out = {'busy': _pipeline_busy()}
    if os.path.exists(PIPE_LOG):
        with open(PIPE_LOG, 'rb') as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - 2000))
            out['log_tail'] = f.read().decode('utf-8', 'ignore')[-1500:]
    return out
