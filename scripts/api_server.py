#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""net-annals 公共 API v1（FastAPI + SQLite）——三层公开访问模型。

层        认证      配额                      端点
anon     无 key    IP 200次/天 + 20次/分     health/meta/events/year/search
ro key   自助领取  key 2000次/天(可调)       同上全部只读端点
admin    手动签发  不限日配额                ingest/status

安全设计：
  · SQL 注入：全部查询 ? 参数化；枚举白名单；LIMIT/OFFSET 强制 int；LIKE 转义（ESCAPE '\'）
  · 配额/限流：key 维度日配额持久化（usage.db，重启不清零）+ 滑动窗突发限制；IP 维度匿名日配额
  · 滥用：无效 key 探测 20次/10分 → 封 IP 1h（bans 表）；注册每 IP 每天限 3 把；429 带 Retry-After
  · 认证：sha256+hmac.compare_digest；密钥文件 0600 热加载；明文只在领取响应中出现一次
  · 运行面：只绑 127.0.0.1 走 nginx /api/；文档页关闭；500 统一短语；不记录密钥
启动: uvicorn scripts.api_server:app --host 127.0.0.1 --port 8400"""
import hashlib, hmac, json, os, re, secrets, sqlite3, threading, time
from collections import defaultdict, deque
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = 'data/derived/api/events.db'
KEY_FILE = 'config/api_keys.json'
USAGE_DB = 'data/derived/api/usage.db'
PIPE_LOG = 'data/derived/api/pipeline.log'
PIPE_LOCK = 'data/derived/api/pipeline.lock'

ANON_DAILY = 200            # 匿名层：IP 每日配额
ANON_PERMIN = 20            # 匿名层：每分钟突发
RO_PERMIN = 120             # ro：每分钟突发
ADMIN_PERMIN = 30           # admin：每分钟突发
REG_PER_IP_DAY = 3          # 每 IP 每天可领 key 数
DEFAULT_RO_QUOTA = 2000     # ro 默认日配额（api_keys.json --quota 可覆盖）

app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)

# ── usage.db：持久化配额/封禁/注册计数 ───────────────────────────────
_conn_lock = threading.Lock()


def udb():
    conn = sqlite3.connect(f'file:{USAGE_DB}?mode=ro', uri=True)
    return conn


def udb_write():
    conn = sqlite3.connect(USAGE_DB, timeout=5)
    conn.execute('PRAGMA journal_mode=WAL')
    return conn


def _init_usage():
    os.makedirs(os.path.dirname(USAGE_DB), exist_ok=True)
    conn = udb_write()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS key_usage(key_id TEXT, day TEXT, count INTEGER, PRIMARY KEY(key_id, day));
    CREATE TABLE IF NOT EXISTS ip_usage(day TEXT, ip TEXT, count INTEGER, PRIMARY KEY(day, ip));
    CREATE TABLE IF NOT EXISTS reg_daily(day TEXT, ip TEXT, count INTEGER, PRIMARY KEY(day, ip));
    CREATE TABLE IF NOT EXISTS bans(ip TEXT PRIMARY KEY, until INTEGER, reason TEXT);
    """)
    conn.commit()
    conn.close()


_init_usage()


def _bump(table, keycols, keyvals):
    with _conn_lock:
        conn = udb_write()
        day = time.strftime('%Y-%m-%d')
        conn.execute(
            f'INSERT INTO {table}({",".join(keycols)},count) VALUES({",".join("?" for _ in keyvals)},1) '
            f'ON CONFLICT({",".join(keycols)}) DO UPDATE SET count = count + 1', [*keyvals])
        row = conn.execute(
            f'SELECT count FROM {table} WHERE day=? AND ' +
            ' AND '.join(f'{c}=?' for c in keycols[1:]),
            [day] + keyvals[1:]).fetchone()
        conn.commit()
        conn.close()
        return row[0] if row else 1


def _banned(ip):
    conn = udb()
    r = conn.execute('SELECT until, reason FROM bans WHERE ip=?', (ip,)).fetchone()
    conn.close()
    if r and r['until'] > time.time():
        raise HTTPException(403, f'banned until {datetime.fromtimestamp(r["until"]).strftime("%H:%M")} ({r["reason"]})')
    if r:  # 过期封禁顺手清理
        with _conn_lock:
            conn2 = udb_write()
            try:
                conn2.execute('DELETE FROM bans WHERE ip=?', (ip,))
                conn2.commit()
            finally:
                conn2.close()


def _ban(ip, hours, reason):
    with _conn_lock:
        conn = udb_write()
        try:
            conn.execute('INSERT INTO bans VALUES(?,?,?) ON CONFLICT(ip) DO UPDATE SET until=excluded.until, reason=excluded.reason',
                         (ip, time.time() + hours * 3600, reason))
            conn.commit()
        finally:
            conn.close()


def _seconds_to_midnight():
    now = datetime.now()
    return (86400 - (now.hour * 3600 + now.minute * 60 + now.second)) + 60

# ── 密钥库（sha256 + 热加载） ────────────────────────────────────────
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

# ── 突发限流（滑动窗，内存） ─────────────────────────────────────────
_hits = defaultdict(deque)
_rl_lock = threading.Lock()


def _burst(subject, limit):
    now = time.time()
    with _rl_lock:
        q = _hits[subject]
        while q and q[0] < now - 60:
            q.popleft()
        if len(q) >= limit:
            raise HTTPException(429, 'rate limit exceeded, retry later', {'Retry-After': '60'})
        q.append(now)


_probes = defaultdict(deque)   # 无效 key 探测计数（每 IP）


def _record_probe(ip):
    now = time.time()
    with _rl_lock:
        q = _probes[ip]
        while q and q[0] < now - 600:
            q.popleft()
        q.append(now)
        if len(q) >= 20:
            _ban(ip, 1, 'invalid-key probing')
            _probes.pop(ip, None)


def _client_ip(request):
    return (request.headers.get('x-real-ip') or (request.client.host if request.client else 'unknown'))[:64]

# ── 中间件：封禁/认证/配额/限流 全在这里统一执行 ────────────────────
ADMIN_PATHS = ('/api/v1/ingest/',)
READ_PATHS = ('/api/v1/meta', '/api/v1/events', '/api/v1/year/', '/api/v1/search')


@app.middleware('http')
async def gate(request: Request, call_next):
    ip = _client_ip(request)
    path = request.url.path
    try:
        if not path.startswith('/api/v1/'):
            return JSONResponse(status_code=404, content={'error': 'not found'})
        _banned(ip)

        # 管理端点：仅 admin 密钥
        if path.startswith(ADMIN_PATHS):
            k = _require_key(request, ip, role='admin')
            _burst('key:' + k['id'], ADMIN_PERMIN)
            request.state.key_id = k['id']
            request.state.quota_left = None
            resp = await call_next(request)
            return resp

        # 自助领取：仅 POST 计注册频率并进入签发；GET 无该路由（页面在 /keys/page）
        if path == '/api/v1/keys/register':
            if request.method != 'POST':
                return JSONResponse(status_code=405, content={'error': 'POST required'})
            used = _bump('reg_daily', ('day', 'ip'), [day_key(), ip])
            if used > REG_PER_IP_DAY:
                raise HTTPException(429, f'registration limit: {REG_PER_IP_DAY} keys/IP/day',
                                    {'Retry-After': str(_seconds_to_midnight())})
            resp = await call_next(request)
            return resp

        # 只读端点：有 key 走 key 配额；无 key 走匿名 IP 配额
        if path in READ_PATHS or path.startswith(('/api/v1/events/', '/api/v1/year/')):
            raw = request.headers.get('x-api-key', '')
            if raw:
                if len(raw) > 64 or not re.fullmatch(r'NA-[0-9a-f]{48}', raw):
                    _record_probe(ip)
                    raise HTTPException(401, 'malformed api key')
                k = _load_keys().get(hashlib.sha256(raw.encode()).hexdigest())
                if not k:
                    _record_probe(ip)
                    raise HTTPException(401, 'invalid api key')
                permin = ADMIN_PERMIN if k.get('role') == 'admin' else RO_PERMIN
                _burst('key:' + k['id'], permin)
                quota = k.get('daily_quota')
                if quota is None and k.get('role') != 'admin':
                    quota = DEFAULT_RO_QUOTA
                if quota is not None:
                    used = _bump('key_usage', ('day', 'key_id'), [day_key(), k['id']])
                    if used > quota:
                        raise HTTPException(429, f'daily quota {quota} exceeded',
                                            {'Retry-After': str(_seconds_to_midnight())})
                    left = max(0, quota - used)
                else:
                    left = None
                request.state.key_id = k['id']
                request.state.quota_left = left
                resp = await call_next(request)
                if left is not None:
                    resp.headers['X-Quota-Limit'] = str(quota)
                    resp.headers['X-Quota-Remaining'] = str(left)
                return resp
            # 匿名层
            _burst('ip:' + ip, ANON_PERMIN)
            used = _bump('ip_usage', ('day', 'ip'), [day_key(), ip])
            if used > ANON_DAILY:
                raise HTTPException(429, f'anonymous quota {ANON_DAILY}/day exceeded — get a free key at /api/v1/keys/page',
                                    {'Retry-After': str(_seconds_to_midnight())})
            resp = await call_next(request)
            resp.headers['X-Anon-Quota-Remaining'] = str(max(0, ANON_DAILY - used))
            resp.headers['X-Get-Free-Key'] = '/api/v1/keys/page'
            return resp

        # health / keys 页：开放
        return await call_next(request)
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code,
                            content={'error': e.detail},
                            headers=e.headers or {})


def day_key():
    return time.strftime('%Y-%m-%d')


def _require_key(request, ip, role):
    raw = request.headers.get('x-api-key', '')
    if not raw or len(raw) > 64 or not re.fullmatch(r'NA-[0-9a-f]{48}', raw):
        _record_probe(ip)
        raise HTTPException(401, 'missing or malformed api key')
    k = _load_keys().get(hashlib.sha256(raw.encode()).hexdigest())
    if not k:
        _record_probe(ip)
        raise HTTPException(401, 'invalid api key')
    if role == 'admin' and k.get('role') != 'admin':
        raise HTTPException(403, 'admin role required')
    return k


@app.exception_handler(Exception)
async def _unhandled(request, exc):
    return JSONResponse(status_code=500, content={'error': 'internal error'})

# ── 数据访问 ─────────────────────────────────────────────────────────
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


# ── 只读端点（鉴权已在中间件完成） ──────────────────────────────────
@app.get('/api/v1/health')
def health():
    if not os.path.exists(DB_PATH):
        return {'ok': False}
    conn = _db()
    total = conn.execute('SELECT value FROM meta WHERE key="total"').fetchone()
    gen = conn.execute('SELECT value FROM meta WHERE key="generated"').fetchone()
    conn.close()
    return {'ok': True, 'total': int(total['value']), 'db_generated': gen['value'],
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

# ── 自助领取 ─────────────────────────────────────────────────────────
@app.post('/api/v1/keys/register')
async def register_key(request: Request):
    ip = _client_ip(request)
    try:
        body = json.loads(await request.body() or b'{}')
    except Exception:
        raise HTTPException(400, 'invalid json')
    contact = str(body.get('contact', ''))[:120] if isinstance(body, dict) else ''
    name = f"public-{time.strftime('%Y%m%d')}-{secrets.token_hex(2)}"
    d = json.load(open(KEY_FILE, encoding='utf-8'))
    if any(k['id'] == name for k in d['keys']):
        name += secrets.token_hex(1)
    raw = 'NA-' + secrets.token_hex(24)
    d['keys'].append({'id': name, 'key_sha256': hashlib.sha256(raw.encode()).hexdigest(),
                      'role': 'ro', 'daily_quota': DEFAULT_RO_QUOTA, 'contact': contact,
                      'created': datetime.now().astimezone().isoformat(timespec='seconds')})
    os.makedirs(os.path.dirname(KEY_FILE), exist_ok=True)
    with open(KEY_FILE, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    os.chmod(KEY_FILE, 0o600)
    return {'ok': True, 'key': raw, 'role': 'ro', 'daily_quota': DEFAULT_RO_QUOTA,
            'note': '请妥善保存（服务器只存哈希，无法找回）。使用时携带请求头 X-API-Key。'
                    '请标注数据来源 toolsfox.cn；禁止将其用于违法违规用途。',
            'docs': '/api/v1/keys/page'}


@app.get('/api/v1/keys/page', response_class=HTMLResponse)
def keys_page():
    return """<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>net-annals API · 免费领取密钥</title>
<style>body{background:#0c0d10;color:#e8e6df;font:15px/1.8 -apple-system,'PingFang SC',sans-serif;max-width:640px;margin:0 auto;padding:48px 20px}
h1{font-size:1.4rem;color:#c9a86a}code,textarea,input{font-family:ui-monospace,monospace;background:#16181d;border:1px solid #30343f;border-radius:8px;color:#e8e6df}
input{padding:10px 14px;width:100%;box-sizing:border-box}button{background:#c9a86a;color:#141310;border:none;border-radius:8px;padding:10px 26px;cursor:pointer;font-size:15px}
.key{display:block;margin:12px 0;padding:14px;word-break:break-all;color:#7fd18a}a{color:#5b9bd5}
small{color:#8a8f9c}</style>
<h1>互联网编年史 · API 密钥免费领取</h1>
<p>6134+ 条精确到日、可溯源的中国时代编年数据：按年份、日期区间、类目、领域层检索，全文搜索。
匿名访问每 IP 每天 200 次；领取免费密钥后每天 <b>2000</b> 次。</p>
<p><input id="contact" placeholder="联系方式（选填，仅用于站务通知）"></p>
<button onclick="go()">领取我的密钥</button>
<pre class="key" id="out" hidden></pre>
<p><b>查询示例</b></p>
<pre><code>curl -H "X-API-Key: 你的密钥" \
  "https://toolsfox.cn/api/v1/events?year=1993&limit=20"
curl -H "X-API-Key: 你的密钥" \
  "https://toolsfox.cn/api/v1/search?q=火星" </code></pre>
<p><b>条款</b>：数据供学习研究与非商业用途自由使用，转发请注明来源 toolsfox.cn；禁止用于违法违规场景；滥用（高频抓取、转售）将被封禁。每天每 IP 限领 3 把。</p>
<small>生成式整理自公开史料，日期以所附来源为准。</small>
<script>
async function go(){
  const r = await fetch('/api/v1/keys/register',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({contact:document.getElementById('contact').value})});
  const d = await r.json();
  const out = document.getElementById('out');
  out.hidden = false;
  out.textContent = d.ok ? ('你的密钥（只显示一次）\\n' + d.key + '\\n\\n日配额 ' + d.daily_quota + ' 次。' + d.note) : ('失败：' + (d.error||''));
}
</script>"""

# ── 管理端点 ─────────────────────────────────────────────────────────
@app.post('/api/v1/ingest/gap-queue')
async def ingest_gap_queue(request: Request):
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
def ingest_status():
    out = {'busy': os.path.exists(PIPE_LOCK)}
    if os.path.exists(PIPE_LOG):
        with open(PIPE_LOG, 'rb') as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - 2000))
            out['log_tail'] = f.read().decode('utf-8', 'ignore')[-1500:]
    return out
