#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""端点层：只读查询 + 自助领取。薄——校验参数、调 store、组织响应。
写数据的端点不存在：数据新增只走 GitHub PR（站长审核）或服务器脚本。"""
import json

from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.concurrency import run_in_threadpool

from . import config, datasets, keys_store, store


def _clamp_page_limit(page, limit, max_limit=200):
    try:
        page = max(0, min(int(page), 5000))
        limit = max(1, min(int(limit), max_limit))
    except (TypeError, ValueError):
        raise HTTPException(400, 'page/limit must be integers')
    return page, limit


def _validate_events_params(sort, year, date_from, date_to, category, region, layer, q):
    if sort not in config.SORTS:
        raise HTTPException(400, 'bad sort')
    if year and not config.RE_YEAR.fullmatch(year):
        raise HTTPException(400, 'bad year')
    for d in (date_from, date_to):
        if d and not config.RE_DATE.fullmatch(d):
            raise HTTPException(400, 'bad date, expect YYYY-MM-DD')
    if date_from and date_to and date_from > date_to:
        raise HTTPException(400, 'date_from > date_to')
    if category and category not in config.CATEGORIES:
        raise HTTPException(400, 'bad category')
    if region and region not in config.REGIONS:
        raise HTTPException(400, 'bad region')
    if layer and (not config.RE_LAYER.fullmatch(layer) or layer not in config.LAYER_NAMES):
        raise HTTPException(400, 'bad layer (see /api/v1/meta layers; main timeline = omit)')
    q = q.strip()
    if len(q) > 64:
        raise HTTPException(400, 'q too long (max 64)')
    return q


def register_routes(app):

    @app.get(config.API_PREFIX)
    def index():
        """根索引：自描述端点清单（public-apis 等目录站的评审员落地页）。"""
        out = {
            'name': 'China Internet Chronicle API',
            'description': 'Timeline of China & the world since 1970: 6,000+ sourced events, '
                           'persons, entities & works (content in Chinese)',
            'version': '1.1',
            'read_only': True,
            'license': 'CC BY-NC（署名-非商业）',
            'docs': 'https://github.com/istoolsfox/net-annals/blob/main/docs/API.md',
            'auth': 'anonymous 200 req/day per IP; free key 2000/day via POST keys/register',
            'endpoints': [
                'GET /health',
                'GET /meta',
                'GET /events?year=&date_from=&date_to=&category=&region=&layer=&q=&page=&limit=&sort=',
                'GET /events/{id}',
                'GET /year/{year}',
                'GET /search?q=&limit=',
                'GET /persons?q=&field=&region=&year=&page=&limit=',
                'GET /entities?q=&type=&region=&year=&page=&limit=',
                'GET /works?q=&type=&region=&year=&page=&limit=',
                'GET /groups?q=&page=&limit=',
                'GET /{dataset}/{id}',
                'POST /keys/register',
                'GET /keys/page',
            ],
        }
        try:
            total, generated = store.events_total()
            out['total_events'] = total
            out['db_generated'] = generated
        except store.StoreUnavailable:
            pass
        return out

    @app.get('/api/v1/health')
    def health():
        try:
            total, generated = store.events_total()
        except store.StoreUnavailable:
            return {'ok': False}
        return {'ok': total > 0, 'total': total, 'db_generated': generated,
                'write': 'none (read-only API; contribute via GitHub PR)',
                'tiers': {'anonymous': f'{config.ANON_DAILY}/day per IP',
                          'free_key': f'{config.DEFAULT_RO_QUOTA}/day (self-service)',
                          'docs': config.API_PREFIX + 'keys/page'}}

    @app.get('/api/v1/meta')
    def meta():
        return store.meta()

    @app.get('/api/v1/events')
    def list_events(year: str = '', date_from: str = '', date_to: str = '',
                    category: str = '', region: str = '', layer: str = '',
                    q: str = '', page: int = 0, limit: int = 50, sort: str = 'date_asc'):
        q = _validate_events_params(sort, year, date_from, date_to, category, region, layer, q)
        page, limit = _clamp_page_limit(page, limit)
        return store.list_events(year=year, date_from=date_from, date_to=date_to,
                                 category=category, region=region, layer=layer,
                                 q=q, page=page, limit=limit, sort=sort)

    @app.get('/api/v1/events/{eid}')
    def get_event(eid: str):
        if not config.RE_ID.fullmatch(eid):
            raise HTTPException(400, 'bad event id')
        return store.event_by_id(eid)

    @app.get('/api/v1/year/{year}')
    def by_year(year: int):
        if not (1400 <= year <= 2100):
            raise HTTPException(400, 'year out of range')
        items = store.events_by_year(year)
        return {'year': year, 'total': len(items), 'items': items}

    @app.get('/api/v1/search')
    def search(q: str = '', limit: int = 20):
        q = q.strip()
        if not q or len(q) > 64:
            raise HTTPException(400, 'q required, max 64 chars')
        limit = max(1, min(int(limit), 50))
        return store.search_events(q, limit)

    # ── 通用数据集端点（persons/entities/works/groups，注册表驱动） ──

    def _make_list(ds):
        def endpoint(request: Request):
            spec = datasets.DATASETS[ds]
            filters = {}
            for param, col in spec['filters'].items():
                v = request.query_params.get(param, '')
                if v:
                    nv = datasets.validate_filter(v, col)
                    if nv is None:
                        raise HTTPException(400, f'bad {param}')
                    filters[param] = nv
            q = request.query_params.get('q', '').strip()
            if len(q) > 64:
                raise HTTPException(400, 'q too long (max 64)')
            page, limit = _clamp_page_limit(request.query_params.get('page', 0),
                                            request.query_params.get('limit', 50))
            sort = request.query_params.get('sort', 'date_asc')
            if sort not in config.SORTS:
                raise HTTPException(400, 'bad sort')
            return store.list_items(ds, q=q, page=page, limit=limit,
                                    filters=filters, sort=sort)
        endpoint.__name__ = f'list_{ds}'
        return endpoint

    def _make_detail(ds):
        def endpoint(item_id: str):
            if not config.RE_SLUG.fullmatch(item_id):
                raise HTTPException(400, 'bad item id')
            return store.item_by_id(ds, item_id)
        endpoint.__name__ = f'get_{ds}_item'
        return endpoint

    for _ds in datasets.DATASET_IDS:
        # 注册表驱动：DATASET_IDS 与具体路径（meta/events/year/search/keys）不重叠
        app.get(f'/api/v1/{_ds}')(_make_list(_ds))
        app.get(f'/api/v1/{_ds}/{{item_id}}')(_make_detail(_ds))

    # ── 自助领取（唯一带请求体的端点；配额/CSRF 防线在 gate） ────────

    @app.post('/api/v1/keys/register')
    async def register_key(request: Request):
        body = await request.body()
        if len(body) > config.REGISTER_BODY_MAX:
            raise HTTPException(413, 'payload too large')
        try:
            d = json.loads(body or b'{}')
        except Exception:
            raise HTTPException(400, 'invalid json')
        contact = str(d.get('contact', ''))[:120] if isinstance(d, dict) else ''
        # flock + fsync 的文件写入线程池（事件循环零阻塞纪律）
        raw = await run_in_threadpool(keys_store.issue,
                                      keys_store.new_key_id(), 'public', contact=contact)
        return JSONResponse(status_code=201, content={
            'ok': True, 'key': raw, 'role': 'ro',
            'daily_quota': config.DEFAULT_RO_QUOTA,
            'note': '请妥善保存（服务器只存哈希，无法找回）。使用时携带请求头 X-API-Key。'
                    '请标注数据来源 toolsfox.cn；禁止将其用于违法违规用途。',
            'docs': config.API_PREFIX + 'keys/page'})

    @app.get('/api/v1/keys/page', response_class=HTMLResponse)
    def keys_page():
        with open('site/assets/keys_page.html', encoding='utf-8') as f:
            return f.read()
