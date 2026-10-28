#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""构建 API 用的 SQLite 数据库（data/derived/api/events.db）。
全库条目入表 + 年份/类目/领域层索引 + search 拼接列（LIKE 子串检索中文）。
安全：本脚本写库无用户输入；查询侧一律参数化（见 api_server.py）。
用法: python3 scripts/build_api_db.py"""
import glob, json, os, re, sqlite3

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT_DIR = 'data/derived/api'
DB = os.path.join(OUT_DIR, 'events.db')

LAYER_NAMES = {
    "": "主时间线", "tech": "科技互联网", "games": "游戏", "games2": "游戏Ⅱ",
    "science": "科学", "space": "航天", "aviation": "航空", "exploration": "探索",
    "film": "电影", "music": "音乐", "anime": "动画", "sports": "体育", "sportsbiz": "体育产业",
    "wayback": "数字考古", "disasters": "灾疫", "media": "传媒", "food": "饮食",
    "telecom": "通信", "railways": "铁路", "autos": "汽车", "transport": "交通",
    "education": "教育", "city": "城市", "medical": "医疗健康", "retail": "零售",
    "pets": "宠物", "charity": "公益", "folklore": "非遗民俗", "publishing": "出版阅读",
    "logistics": "物流", "admarket": "广告营销", "energy": "能源电力", "museum": "博物馆文物",
    "records": "纪录", "agri": "农业", "eco": "生态", "finance": "金融",
    "appliance": "家电", "fashion": "时尚", "diglife": "数字生活", "estate": "房地产",
}


def layer_of(path):
    name = os.path.basename(path)[:-5]
    stripped = re.sub(r"^\d{4}(?:-\d{4})*-?", "", name)
    return stripped if stripped in LAYER_NAMES else (stripped or "")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    # 原子替换：写临时库后 os.replace（评审发现 os.remove 重建窗口内 API 会 503/空结果）
    tmp_db = DB + '.tmp'
    if os.path.exists(tmp_db):
        os.remove(tmp_db)
    conn = sqlite3.connect(tmp_db)
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
    CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT);
    """)
    rows = []
    seen_ids = set()
    dup_skipped = 0
    for f in sorted(glob.glob('data/events/*.json')):
        if '/.' in f or '.parts' in f:
            continue
        lay = layer_of(f) or 'main'   # 存拼音 code（API 过滤参数同口径）；主时间线空串映射为 main
        for e in json.load(open(f, encoding='utf-8')):
            eid = e.get('id', '')
            if not eid or eid in seen_ids:
                dup_skipped += 1
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
    cats = {}
    layers = {}
    for _, _, _, _, _, _, c, _, _, _, _, _, _, _, _, _, _, lay, _ in rows:
        cats[c] = cats.get(c, 0) + 1
        layers[lay] = layers.get(lay, 0) + 1
    years = sorted({r[2] for r in rows if r[2]})
    layers_meta = {code: {'name': LAYER_NAMES.get(code, code), 'count': n}
                   for code, n in sorted(layers.items())}
    conn.executemany("INSERT INTO meta VALUES(?,?)", [
        ('total', str(len(rows))),
        ('categories', json.dumps(cats, ensure_ascii=False)),
        ('layers', json.dumps(layers_meta, ensure_ascii=False)),
        ('year_min', str(years[0] if years else 0)),
        ('year_max', str(years[-1] if years else 0)),
        ('generated', __import__('datetime').datetime.now().astimezone().isoformat(timespec='seconds')),
    ])
    conn.commit()
    conn.close()
    os.replace(tmp_db, DB)          # 原子换名：读者新连接拿新库，旧连接读旧 inode，无空窗
    os.chmod(DB, 0o600)
    print(f'✓ API 数据库已构建：{DB}（{len(rows)} 条，{len(cats)} 类目，{len(layers)} 领域层'
          f'{"，丢弃重复 " + str(dup_skipped) + " 条" if dup_skipped else ""}）')


if __name__ == '__main__':
    main()
