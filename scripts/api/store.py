#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""只读数据访问层：events + 通用 items（persons/entities/works/groups）。
铁律：查询全部 ? 参数化；LIMIT/OFFSET 强制 int；LIKE 转义（ESCAPE '\'）；
排序/过滤只允许白名单展开进 SQL。库缺失抛 StoreUnavailable。"""
import json
import os
import sqlite3

from . import config, datasets


class StoreUnavailable(Exception):
    pass


class NotFound(Exception):
    pass


def connect():
    if not os.path.exists(config.DB_PATH):
        raise StoreUnavailable('database not ready')
    c = sqlite3.connect(f'file:{config.DB_PATH}?mode=ro', uri=True)
    c.row_factory = sqlite3.Row
    return c


def like_escape(q):
    return q.replace('\\', '\\\\').replace('%', r'\%').replace('_', r'\_')


def row_to_event(r):
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


# ── events ────────────────────────────────────────────────────────

def meta():
    c = connect()
    try:
        m = dict(c.execute('SELECT key, value FROM meta').fetchall())
    finally:
        c.close()
    out = {'total': int(m.get('total', 0)),
           'categories': json.loads(m.get('categories', '{}')),
           'layers': json.loads(m.get('layers', '{}')),
           'year_range': [int(m.get('year_min', 0)), int(m.get('year_max', 0))],
           'db_generated': m.get('generated')}
    try:
        out['datasets'] = json.loads(m.get('datasets', '{}'))
    except ValueError:
        out['datasets'] = {}
    return out


def events_total():
    c = connect()
    try:
        row = c.execute("SELECT value FROM meta WHERE key='total'").fetchone()
        gen = c.execute("SELECT value FROM meta WHERE key='generated'").fetchone()
    finally:
        c.close()
    return (int(row['value']) if row else 0, gen['value'] if gen else None)


def _events_where(year, date_from, date_to, category, region, layer, words):
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
    for w in words:
        where.append('search LIKE ? ESCAPE \'\\\'')
        params.append(f'%{like_escape(w)}%')
    return ('WHERE ' + ' AND '.join(where)) if where else '', params


def list_events(year='', date_from='', date_to='', category='', region='', layer='',
                q='', page=0, limit=50, sort='date_asc'):
    words = q.split()[:6] if q else []
    clause, params = _events_where(year, date_from, date_to, category, region, layer, words)
    c = connect()
    try:
        total = c.execute(f'SELECT COUNT(*) c FROM events {clause}', params).fetchone()['c']
        rows = c.execute(
            f'SELECT * FROM events {clause} ORDER BY {config.SORTS[sort]} LIMIT ? OFFSET ?',
            params + [limit, page * limit]).fetchall()
    finally:
        c.close()
    return {'total': total, 'page': page, 'limit': limit,
            'items': [row_to_event(r) for r in rows]}


def event_by_id(eid):
    c = connect()
    try:
        r = c.execute('SELECT * FROM events WHERE id = ?', (eid,)).fetchone()
    finally:
        c.close()
    if not r:
        raise NotFound(eid)
    return row_to_event(r)


def events_by_year(year):
    c = connect()
    try:
        rows = c.execute('SELECT * FROM events WHERE year = ? ORDER BY date, id LIMIT 2000',
                         (year,)).fetchall()
    finally:
        c.close()
    return [row_to_event(r) for r in rows]


def search_events(q, limit=20):
    words = q.split()[:6]
    where, params = _events_where('', '', '', '', '', '', words)
    score_cases, score_params = [], []
    for w in words:
        pw = f'%{like_escape(w)}%'
        score_cases.append("(CASE WHEN title LIKE ? ESCAPE '\\' THEN 30 ELSE 0 END"
                           " + CASE WHEN tags LIKE ? ESCAPE '\\' THEN 12 ELSE 0 END"
                           " + CASE WHEN summary LIKE ? ESCAPE '\\' THEN 6 ELSE 0 END"
                           " + CASE WHEN detail LIKE ? ESCAPE '\\' THEN 2 ELSE 0 END)")
        score_params += [pw] * 4
    c = connect()
    try:
        rows = c.execute(
            f'SELECT *, ({"+".join(score_cases)}) sc FROM events {where} '
            'ORDER BY sc DESC, date DESC, id LIMIT ?',
            score_params + params + [limit]).fetchall()
    finally:
        c.close()
    return {'q': q, 'returned': len(rows),
            'items': [dict(row_to_event(r), _score=r['sc']) for r in rows]}


# ── 通用 items（persons/entities/works/groups）───────────────────

def list_items(dataset, q='', page=0, limit=50, filters=None, sort='date_asc'):
    spec = datasets.DATASETS[dataset]
    where, params = ['dataset = ?'], [dataset]
    for param, value in (filters or {}).items():
        col = spec['filters'][param]
        where.append(f'{col} = ?')
        params.append(value)
    words = q.split()[:6] if q else []
    for w in words:
        where.append('search LIKE ? ESCAPE \'\\\'')
        params.append(f'%{like_escape(w)}%')
    clause = 'WHERE ' + ' AND '.join(where)
    c = connect()
    try:
        total = c.execute(f'SELECT COUNT(*) c FROM items {clause}', params).fetchone()['c']
        rows = c.execute(
            f'SELECT data FROM items {clause} ORDER BY {config.SORTS[sort]} LIMIT ? OFFSET ?',
            params + [limit, page * limit]).fetchall()
    finally:
        c.close()
    return {'total': total, 'page': page, 'limit': limit,
            'items': [json.loads(r['data']) for r in rows]}


def item_by_id(dataset, item_id):
    c = connect()
    try:
        r = c.execute('SELECT data FROM items WHERE dataset = ? AND id = ?',
                      (dataset, item_id)).fetchone()
    finally:
        c.close()
    if not r:
        raise NotFound(item_id)
    return json.loads(r['data'])
