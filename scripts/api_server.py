#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""net-annals 公共 API v1（FastAPI + SQLite）。
安全设计（对照用户要求）：
  · SQL 注入：全部查询走 ? 参数化；排序/类目/领域层用白名单枚举；LIMIT/OFFSET 强制 int；
    用户关键词进 LIKE 前转义 % _ 和反斜杠（ESCAPE '\'）；
  · 认证：X-API-Key → sha256 与库内哈希 hmac.compare_digest 比对（ro 只读 / admin 管理）；
    密钥文件 0600 不入 git，mtime 热加载支持即时吊销；
  · 限流：按密钥滑动窗口（ro 120/min，admin 30/min）→ 429；
  · 输入：年份/日期/分页/关键词长度全部严格校验；未知查询串不入 SQL；
  · 运行面：uvicorn 只绑 127.0.0.1，经 nginx /api/ 反代；DB 文件 0600；
  · 报错：统一 500 短语，不回栈帧；不打密钥日志。
启动: uvicorn scripts.api_server:app --host 127.0.0.1 --port 8400"""
import hashlib, hmac, json, os, re, sqlite3, threading, time
from collections import defaultdict, deque

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = 'data/derived/api/events.db'
KEY_FILE = 'config/api_keys.json'
INGEST_DIR = 'data/derived/gap'
PIPE_LOG = 'data/derived/api/pipeline.log'
PIPE_LOCK = 'data/derived/api/pipeline.lock'

app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)  # 不暴露接口文档页

# ── 密钥：sha256 库 + 热加载 ───────────────────────────────────────────
_keys_cache = {'mtime': 0, 'map': {}}


def _load_keys():
    try:
        mt = os.path.getmtime(KEY_FILE)
        if mt != _keys_cache['mtime']:
            d = json.load(open(KEY_FILE, encoding='utf-8'))
            _keys_cache['map'] = {k['key_sha256']: k for k in d.get('keys', [])}
            _keys_cache['mtime'] = mt
    except Exception:
        pass
    return _keys_cache['map']


def auth(request: Request, role: str):
    raw = request.headers.get('x-api-key', '')
    if not raw or len(raw) > 64 or not re.fullmatch(r'NA-[0-9a-f]{48}', raw):
        raise HTTPException(401, 'missing or malformed api key')
    h = hashlib.sha256(raw.encode()).hexdigest()
    k = _load_keys().get(h)
    if not k or not hmac.compare_digest(k['key_sha256'], h):
        raise HTTPException(401, 'invalid api key')
    if role == 'admin' and k.get('role') != 'admin':
        raise HTTPException(403, 'admin role required')
    _rate_limit(k['id'], 30 if k.get('role') == 'admin' else 120)
    return k


# ── 限流：每密钥 60s 滑动窗口 ─────────────────────────────────────────
_hits = defaultdict(deque)
_rl_lock = threading.Lock()


def _rate_limit(key_id, limit):
    now = time.time()
    with _rl_lock:
        q = _hits[key_id]
        while q and q[0] < now - 60:
            q.popleft()
        if len(q) >= limit:
            raise HTTPException(429, 'rate limit exceeded, retry later')
        q.append(now)


# ── 输入校验常量 ─────────────────────────────────────────────────────
RE_YEAR = re.compile(r'(19|20)\d{2}')
RE_DATE = re.compile(r'\d{4}-\d{2}-\d{2}')
RE_ID = re.compile(r'[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z0-9][a-z0-9-]{1,100}')
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


@app.exception_handler(Exception)
async def _unhandled(request, exc):
    return JSONResponse(status_code=500, content={'error': 'internal error'})


# ── 只读端点 ─────────────────────────────────────────────────────────
@app.get('/api/v1/health')
def health():
    if not os.path.exists(DB_PATH):
        return {'ok': False}
    conn = _db()
    total = conn.execute('SELECT value FROM meta WHERE key="total"').fetchone()
    gen = conn.execute('SELECT value FROM meta WHERE key="generated"').fetchone()
    conn.close()
    return {'ok': True, 'total': int(total['value']), 'db_generated': gen['value']}


@app.get('/api/v1/meta')
def meta(request: Request):
    auth(request, 'ro')
    conn = _db()
    m = dict(conn.execute('SELECT key, value FROM meta').fetchall())
    conn.close()
    return {'total': int(m['total']), 'categories': json.loads(m['categories']),
            'layers': json.loads(m['layers']),
            'year_range': [int(m['year_min']), int(m['year_max'])],
            'db_generated': m['generated']}


@app.get('/api/v1/events')
def list_events(request: Request, year: str = '', date_from: str = '', date_to: str = '',
                category: str = '', region: str = '', layer: str = '',
                q: str = '', page: int = 0, limit: int = 50, sort: str = 'date_asc'):
    auth(request, 'ro')
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
    if layer and not re.fullmatch(r'[a-z0-9]{0,12}', layer):
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
        # 多词 AND：每个词一个参数化 LIKE；通配符已转义
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
def get_event(eid: str, request: Request):
    auth(request, 'ro')
    if not RE_ID.fullmatch(eid):
        raise HTTPException(400, 'bad event id')
    conn = _db()
    r = conn.execute('SELECT * FROM events WHERE id = ?', (eid,)).fetchone()
    conn.close()
    if not r:
        raise HTTPException(404, 'not found')
    return _row_to_event(r)


@app.get('/api/v1/year/{year}')
def by_year(year: int, request: Request):
    auth(request, 'ro')
    if not (1970 <= year <= 2100):
        raise HTTPException(400, 'year out of range')
    conn = _db()
    rows = conn.execute('SELECT * FROM events WHERE year = ? ORDER BY date, id LIMIT 2000',
                        (year,)).fetchall()
    conn.close()
    return {'year': year, 'total': len(rows), 'items': [_row_to_event(r) for r in rows]}


@app.get('/api/v1/search')
def search(request: Request, q: str = '', limit: int = 20):
    auth(request, 'ro')
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
    # 粗排：标题命中 30 / 标签 12 / 摘要 6 / 正文 2；同分按日期新→旧
    score_sql = ("(CASE WHEN title LIKE ? ESCAPE '\\' THEN 30 ELSE 0 END"
                 " + CASE WHEN tags LIKE ? ESCAPE '\\' THEN 12 ELSE 0 END"
                 " + CASE WHEN summary LIKE ? ESCAPE '\\' THEN 6 ELSE 0 END"
                 " + CASE WHEN detail LIKE ? ESCAPE '\\' THEN 2 ELSE 0 END)")
    conn = _db()
    rows = conn.execute(
        f'SELECT *, ({score_sql}) sc FROM events {clause} '
        'ORDER BY sc DESC, date DESC, id LIMIT ?',
        params + [f'%{_like_escape(words[0])}%'] * 4 + [limit]).fetchall()
    conn.close()
    return {'q': q, 'total': len(rows),
            'items': [dict(_row_to_event(r), _score=r['sc']) for r in rows]}


# ── 管理端点：入库触发与状态 ─────────────────────────────────────────
@app.post('/api/v1/ingest/gap-queue')
async def ingest_gap_queue(request: Request):
    auth(request, 'admin')
    if os.path.exists(PIPE_LOCK):
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
    subprocess.Popen(
        ['python3', 'scripts/auto_pipeline.py', '--queue', path],
        stdout=open(PIPE_LOG, 'ab'), stderr=subprocess.STDOUT,
        cwd=os.getcwd(), start_new_session=True)
    return {'ok': True, 'queue_saved': path, 'candidates': len(d['candidates']),
            'note': 'pipeline started, poll /api/v1/ingest/status'}


@app.get('/api/v1/ingest/status')
def ingest_status(request: Request):
    auth(request, 'admin')
    out = {'busy': os.path.exists(PIPE_LOCK)}
    if os.path.exists(PIPE_LOG):
        with open(PIPE_LOG, 'rb') as f:
            f.seek(0, 2)
            size = f.tell()
            f.seek(max(0, size - 2000))
            out['log_tail'] = f.read().decode('utf-8', 'ignore')[-1500:]
    return out
