#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""构建 API 用 SQLite 数据库（data/derived/api/events.db）。
events 表：全库事件 + 年份/类目/领域层索引 + search 拼接列（LIKE 子串检索中文）。
items 表：persons/entities/works/groups（注册表驱动，data 列存完整原始 JSON——
          站点数据结构演进时 API 自动跟随，无需改表）。
安全：本脚本写库无用户输入；查询侧一律参数化（scripts/api/store.py）。
用法: python3 scripts/build_api_db.py"""
import glob
import json
import os
import sqlite3
import sys

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, 'scripts')
from api.config import layer_of
from api import datasets as _datasets

OUT_DIR = 'data/derived/api'
DB = os.path.join(OUT_DIR, 'events.db')

# 非 events 数据集注册表（与 scripts/api/datasets.py 保持同名）：
# (数据集名, 源文件, 列表键, 主日期字段, 名称字段)
EXTRA_SOURCES = [
    ('persons',  'site/persons/data.json',   'persons',  'birth',    'name'),
    ('entities', 'site/entities/data.json',  'entities', 'founded',  'name'),
    ('works',    'site/works/data.json',     'works',    'released', 'title'),
    ('groups',   'site/persons/groups.json', 'groups',   None,       'name'),
]


def build_events(conn):
    rows = []
    seen_ids = set()
    for f in sorted(glob.glob('data/events/*.json')):
        if '/.' in f or '.parts' in f:
            continue
        lay = layer_of(f)
        for e in json.load(open(f, encoding='utf-8')):
            eid = e.get('id', '')
            if not eid or eid in seen_ids:
                continue
            seen_ids.add(eid)
            date = str(e.get('date', ''))
            tags = [str(t) for t in (e.get('tags') or [])]
            srcs = e.get('sources') or []
            rows.append((
                eid, date, int(date[:4] or 0), int(date[5:7] or 0), int(date[8:10] or 0),
                str(e.get('title', '')), str(e.get('category', '')), str(e.get('region', '')),
                1 if e.get('milestone') else 0,
                str(e.get('summary_30s', '')), str(e.get('detail', '')),
                str(e.get('impact', '')), str(e.get('aftermath', '')),
                json.dumps(tags, ensure_ascii=False), json.dumps(srcs, ensure_ascii=False),
                str(e.get('date_confidence', '')), str(e.get('date_accuracy', 'exact')), lay,
                ' '.join([str(e.get('title', '')), str(e.get('summary_30s', '')), ' '.join(tags)])
            ))
    conn.executemany(
        "INSERT INTO events VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)
    return rows


def build_items(conn):
    # 两处登记必须一致：DATASETS（路由）↔ EXTRA_SOURCES（数据源），漂移即静默空集/死端点
    assert {s[0] for s in EXTRA_SOURCES} == set(_datasets.DATASET_IDS), \
        'EXTRA_SOURCES 与 api/datasets.py DATASETS 不同步'
    counts = {}
    rows = []
    seen = set()
    for ds, path, list_key, date_field, name_field in EXTRA_SOURCES:
        try:
            payload = json.load(open(path, encoding='utf-8'))
            items = payload.get(list_key, [])
        except FileNotFoundError:
            print(f'  ⚠ {ds}: 源缺失 {path}，本轮跳过（源齐备后重建即入）')
            counts[ds] = 0
            continue
        except ValueError as e:
            print(f'  ⚠ {ds}: 源 JSON 损坏，本轮跳过（{e}）')
            counts[ds] = 0
            continue
        n = 0
        for it in items:
            iid = str(it.get('id') or '')
            if not iid or (ds, iid) in seen:
                continue
            seen.add((ds, iid))
            date = str(it.get(date_field) or '') if date_field else ''
            year = int(date[:4]) if date[:4].isdigit() else 0
            name = str(it.get(name_field) or '')
            search = ' '.join([name,
                               str(it.get('en_name') or it.get('en_title') or ''),
                               str(it.get('headline') or ''),
                               str(it.get('summary_30s') or '')])
            rows.append((ds, iid, name,
                         str(it.get('type') or it.get('field') or ''),
                         str(it.get('region') or ''),
                         date, year, search,
                         json.dumps(it, ensure_ascii=False)))
            n += 1
        counts[ds] = n
    conn.executemany(
        "INSERT INTO items(dataset,id,name,kind,region,date,year,search,data) "
        "VALUES(?,?,?,?,?,?,?,?,?)", rows)
    return counts


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    tmp = DB + '.tmp'
    if os.path.exists(tmp):
        os.remove(tmp)
    conn = sqlite3.connect(tmp)
    conn.executescript("""
    CREATE TABLE events(
      id TEXT PRIMARY KEY, date TEXT NOT NULL, year INTEGER, month INTEGER, day INTEGER,
      title TEXT NOT NULL, category TEXT, region TEXT, milestone INTEGER DEFAULT 0,
      summary TEXT, detail TEXT, impact TEXT, aftermath TEXT,
      tags TEXT, sources TEXT, date_confidence TEXT, date_accuracy TEXT, layer TEXT,
      search TEXT
    );
    CREATE INDEX idx_year ON events(year);
    CREATE INDEX idx_category ON events(category);
    CREATE INDEX idx_date ON events(date);
    CREATE INDEX idx_layer ON events(layer);
    CREATE TABLE items(
      dataset TEXT NOT NULL, id TEXT NOT NULL, name TEXT, kind TEXT, region TEXT,
      date TEXT, year INTEGER, search TEXT, data TEXT NOT NULL,
      PRIMARY KEY(dataset, id)
    );
    CREATE INDEX idx_items_year ON items(dataset, year);
    CREATE INDEX idx_items_kind ON items(dataset, kind);
    CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT);
    """)
    rows = build_events(conn)
    dataset_counts = build_items(conn)
    cats, layers = {}, {}
    for _, _, _, _, _, _, c, _, _, _, _, _, _, _, _, _, _, lay, _ in rows:
        cats[c] = cats.get(c, 0) + 1
        layers[lay] = layers.get(lay, 0) + 1
    years = sorted({r[2] for r in rows if r[2]})
    conn.executemany("INSERT INTO meta VALUES(?,?)", [
        ('total', str(len(rows))),
        ('categories', json.dumps(cats, ensure_ascii=False)),
        ('layers', json.dumps(layers, ensure_ascii=False)),
        ('datasets', json.dumps(dataset_counts, ensure_ascii=False)),
        ('year_min', str(years[0] if years else 0)),
        ('year_max', str(years[-1] if years else 0)),
        ('generated', __import__('datetime').datetime.now().astimezone().isoformat(timespec='seconds')),
    ])
    conn.commit()
    conn.close()
    os.replace(tmp, DB)   # 原子替换：构建失败不伤线上库
    os.chmod(DB, 0o600)
    print(f'✓ API 数据库已构建：{DB}（events {len(rows)} 条，'
          f'items {sum(dataset_counts.values())} 条：'
          f'{"，".join(f"{k} {v}" for k, v in dataset_counts.items())}，'
          f'{len(cats)} 类目，{len(layers)} 领域层）')


if __name__ == '__main__':
    main()
