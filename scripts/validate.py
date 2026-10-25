#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""数据与前端一致性校验（CI / 本地两用）

用法：
  python scripts/validate.py --base origin/main   # CI：校验全部数据 + PR 的版本戳一致性
  python scripts/validate.py --no-git             # 本地：只校验数据，不做 git diff 对账

检查项（硬失败=err，软提醒=warn）：
  A. JS 语法（node --check）
  B. 数据契约：必填字段 / 枚举白名单 / 日期格式 / id 唯一 / 来源可溯 / 在世者无终结
  C. 交叉引用：related_entities/related_persons 指向真实存在的 id
  D. 事件分片归属与 index.json eras 一致
  E. 每个数据 json 都有内容一致的 .gz（gzip -d 相等）
  F. 版本戳纪律：改了共享静态资源 → 引用页 ?v= 必须 bump；改了数据 → DATA_BUILD 必须 bump
"""
import gzip
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / 'site'
ERR, WARN = [], []
err, warn = ERR.append, WARN.append

DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')
ID_RE = re.compile(r'^\d{4}-\d{2}-\d{2}-[a-z0-9][a-z0-9-]*$')
CATEGORIES = {'milestone', 'internet', 'tech', 'hardware', 'company', 'product',
              'national', 'world', 'society', 'culture', 'economy'}
CONFIDENCE = {'verified', 'single-source', 'uncertain'}
ACCURACY = {'exact', 'month', 'year'}
FIELDS = {'ai', 'internet', 'hardware', 'company', 'game', 'creator', 'science', 'finance', 'media', 'sport'}
ETYPES = {'company', 'community', 'media', 'service', 'infrastructure', 'organization', 'institution', 'game'}
WTYPES = {'film', 'tv', 'book', 'netnovel', 'music', 'game', 'comic', 'documentary', 'variety'}
ESTATUS = {'active', 'declined', 'acquired', 'privatized', 'closed'}
REGIONS = {'cn', 'world'}
ASSETS = ['style.css', 'common.js', 'section-view.js', 'section-page.js', 'app.js']
# 在世者 timeline 终点出现这些词 = 疑似写了终结（软提醒，人工复核）
END_WORDS = ['逝世', '去世', '病逝', '自杀', '身亡', '猝逝', '宣布解散', '正式关停', '停止运营', '宣告破产']


def load_json(path):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception as e:
        err(f'{path.relative_to(ROOT)}: JSON 解析失败 — {e}')
        return None


def check_date(s, label):
    if not DATE_RE.match(str(s)):
        err(f'{label}: 日期格式应为 YYYY-MM-DD，实际 {s!r}')
        return False
    m, d = int(s[5:7]), int(s[8:10])
    if not (1 <= m <= 12 and 1 <= d <= 31):
        err(f'{label}: 日期越界 {s}')
        return False
    return True


def check_sources(items, label, lo=1):
    src = items.get('sources') or []
    if len(src) < lo:
        err(f'{label}: sources 至少 {lo} 条，实际 {len(src)}')
    for s in src:
        if not (s.get('title') and str(s.get('url', '')).startswith(('http://', 'https://'))):
            err(f'{label}: 来源缺 title 或 url 非 http(s)：{s}')


def check_tl(timeline, label, lo=6, hi=25):
    if not isinstance(timeline, list) or not timeline:
        err(f'{label}: timeline 缺失或为空')
        return
    if not (lo <= len(timeline) <= hi):
        warn(f'{label}: timeline {len(timeline)} 条（建议 {lo}~{hi}）')
    last = ''
    for t in timeline:
        if not DATE_RE.match(str(t.get('date', ''))):
            err(f'{label}: timeline 节点日期非法 {t.get("date")!r}')
        if t.get('acc') not in ACCURACY:
            err(f'{label}: timeline acc 非法 {t.get("acc")!r}')
        if not str(t.get('text', '')).strip():
            err(f'{label}: timeline 节点空 text')
        if str(t['date']) < last:
            err(f'{label}: timeline 未按时间升序（{last} → {t["date"]}）')
        last = str(t['date'])


def json_fresh_gz(jp: Path):
    gz = Path(str(jp) + '.gz')
    if not gz.exists():
        err(f'{jp.relative_to(ROOT)}: 缺同名 .gz（改数据必须重压）')
        return
    try:
        if gzip.decompress(gz.read_bytes()) != jp.read_bytes():
            err(f'{gz.name}: 与 json 内容不一致（数据改了没重压 .gz）')
    except Exception as e:
        err(f'{gz.name}: 解压失败 — {e}')


# ── B/C/D. 数据契约 ────────────────────────────────────────────
def validate_data():
    person_ids, entity_ids = set(), set()

    # 主时间线
    idx = load_json(SITE / 'data' / 'index.json')
    shards = sorted((SITE / 'data').glob('shard-*.json'))
    eras = (idx or {}).get('eras') or []
    if not eras:
        err('data/index.json: 缺 eras')

    def era_of(date):
        yf = int(date[:4]) + (int(date[5:7]) - 1) / 12
        for i, e in enumerate(eras):
            if e['range'][0] <= yf < e['range'][1]:
                return i
        return 0 if yf < eras[0]['range'][0] else len(eras) - 1

    seen_ids = set()
    for sp in shards:
        evs = load_json(sp) or []
        m = re.search(r'shard-(\d+)\.json$', sp.name)
        si = int(m.group(1)) if m else -1
        for e in evs:
            label = f'事件 {e.get("id")}'
            eid = e.get('id')
            if not eid or not ID_RE.match(eid):
                err(f'{label}: id 缺失或不符合 YYYY-MM-DD-slug 格式')
            elif eid in seen_ids:
                err(f'{label}: id 全库重复')
            seen_ids.add(eid)
            if check_date(e.get('date', ''), label) and eid and not eid.startswith(e['date']):
                warn(f'{label}: id 前缀与 date 不一致（{eid} vs {e["date"]}）')
            for f in ('title', 'summary_30s', 'detail', 'impact', 'aftermath'):
                if not str(e.get(f, '')).strip():
                    err(f'{label}: 缺 {f}')
            if e.get('category') not in CATEGORIES:
                err(f'{label}: category 非白名单 {e.get("category")!r}')
            if e.get('date_confidence') not in CONFIDENCE:
                err(f'{label}: date_confidence 非白名单 {e.get("date_confidence")!r}')
            if e.get('date_accuracy') not in ACCURACY:
                err(f'{label}: date_accuracy 非白名单 {e.get("date_accuracy")!r}')
            if e.get('region') not in REGIONS:
                err(f'{label}: region 非白名单 {e.get("region")!r}')
            check_sources(e, label)
            if si in range(len(eras)) and eras and era_of(e['date']) != si:
                warn(f'{label}: 分片归属与 eras 区间不符（在 shard-{si}，按区间应在 shard-{era_of(e["date"])}）')

    # 人物
    pdata = load_json(SITE / 'persons' / 'data.json') or {}
    for p in pdata.get('persons', []):
        label = f'人物 {p.get("id")}'
        if p.get('id') in person_ids:
            err(f'{label}: id 重复')
        person_ids.add(p.get('id'))
        if p.get('field') not in FIELDS:
            err(f'{label}: field 非白名单 {p.get("field")!r}')
        if p.get('region') not in REGIONS:
            err(f'{label}: region 非白名单 {p.get("region")!r}')
        if not p.get('birth'):
            err(f'{label}: 缺 birth')
        check_date(p.get('birth', ''), label + ' birth')
        if p.get('death'):
            check_date(p['death'], label + ' death')
        for f in ('name', 'headline', 'summary_30s', 'bio', 'legacy'):
            if not str(p.get(f, '')).strip():
                err(f'{label}: 缺 {f}')
        check_tl(p.get('timeline'), label)
        check_sources(p, label, lo=1)
        if not p.get('death'):  # 在世者：timeline 终点疑似写了终结
            tail = ' '.join(str(t.get('text', '')) for t in (p.get('timeline') or [])[-2:])
            hit = [w for w in END_WORDS if w in tail]
            if hit:
                warn(f'{label}: 在世（death 为空）但 timeline 终点出现 {hit}，请人工复核')

    # 世家
    edata = load_json(SITE / 'entities' / 'data.json') or {}
    for e in edata.get('entities', []):
        label = f'世家 {e.get("id")}'
        if e.get('id') in entity_ids:
            err(f'{label}: id 重复')
        entity_ids.add(e.get('id'))
        if e.get('type') not in ETYPES:
            err(f'{label}: type 非白名单 {e.get("type")!r}')
        if e.get('status') not in ESTATUS:
            err(f'{label}: status 非白名单 {e.get("status")!r}')
        check_date(e.get('founded', ''), label + ' founded')
        if e.get('dissolved'):
            check_date(e['dissolved'], label + ' dissolved')
            if e.get('status') == 'active':
                err(f'{label}: 已写 dissolved 却 status=active，自相矛盾')
        elif e.get('status') == 'closed':
            err(f'{label}: 无 dissolved 却 status=closed')
        for f in ('name', 'headline', 'summary_30s', 'bio', 'legacy'):
            if not str(e.get(f, '')).strip():
                err(f'{label}: 缺 {f}')
        check_tl(e.get('timeline'), label)
        check_sources(e, label, lo=1)

    # 作品
    wdata = load_json(SITE / 'works' / 'data.json') or {}
    for w in wdata.get('works', []):
        label = f'作品 {w.get("id")}'
        check_date(w.get('released', ''), label + ' released')
        if w.get('type') not in WTYPES:
            err(f'{label}: type 非白名单 {w.get("type")!r}')
        for f in ('title', 'headline', 'summary_30s', 'bio', 'legacy'):
            if not str(w.get(f, '')).strip():
                err(f'{label}: 缺 {f}')
        check_tl(w.get('timeline'), label)
        check_sources(w, label, lo=1)

    # 类传 / 今天 / geo 仅做可解析与骨架轻检
    g = load_json(SITE / 'persons' / 'groups.json')
    if g and not isinstance(g.get('groups'), list):
        err('persons/groups.json: 缺 groups 数组')
    td = load_json(SITE / 'today' / 'data.json')
    if td:
        n = sum(len(v) for v in td.get('days', {}).values())
        if td.get('count') != n:
            warn(f'today/data.json: count={td.get("count")} 与实际 {n} 不符')
        bad = [k for k in td.get('days', {}) if not re.match(r'^\d{2}-\d{2}$', k)]
        if bad:
            err(f'today/data.json: 日期键非法 {bad[:5]}')
    load_json(SITE / 'geo' / 'data.json')

    # C. 交叉引用
    for p in pdata.get('persons', []):
        for r in p.get('related_entities') or []:
            if r.get('id') not in entity_ids:
                warn(f'人物 {p.get("id")}: related_entities 指向不存在的世家 {r.get("id")!r}')
    for e in edata.get('entities', []):
        for r in e.get('related_persons') or []:
            if r.get('id') not in person_ids:
                warn(f'世家 {e.get("id")}: related_persons 指向不存在的人物 {r.get("id")!r}')

    # E. .gz 同步
    for jp in list(SITE.rglob('*.json')):
        if '.gz' in jp.name or 'node_modules' in jp.parts:
            continue
        json_fresh_gz(jp)


# ── A. JS 语法 ────────────────────────────────────────────────
def validate_js():
    import shutil
    if not shutil.which('node'):
        warn('未安装 node，跳过 JS 语法检查')
        return
    for f in ASSETS:
        if not f.endswith('.js'):
            continue
        p = SITE / f
        if not p.exists():
            err(f'缺 {f}')
            continue
        r = subprocess.run(['node', '--check', str(p)], capture_output=True, text=True)
        if r.returncode != 0:
            err(f'{f}: 语法错误 — {r.stderr.strip()[:300]}')


# ── F. 版本戳纪律（需要 git base） ─────────────────────────────
def git_diff_names(base):
    r = subprocess.run(['git', 'diff', '--name-only', f'{base}...HEAD'],
                       cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        return None
    return set(x.strip() for x in r.stdout.splitlines() if x.strip())


def show_base(path, base):
    r = subprocess.run(['git', 'show', f'{base}:{path}'], cwd=ROOT, capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def validate_stamps(base):
    changed = git_diff_names(base)
    if changed is None:
        err(f'git base {base!r} 不可用（先 fetch，或本地用 --no-git）')
        return
    rel = lambda p: f'site/{p}'
    changed_assets = {a for a in ASSETS if rel(a) in changed}
    data_changed = any(ch in changed and ch.endswith('.json') and ch.startswith(('site/data/', 'site/persons/', 'site/entities/', 'site/works/', 'site/today/', 'site/geo/'))
                       for ch in changed)
    if not changed_assets and not data_changed:
        return

    pages = [p for p in SITE.rglob('index.html')]
    for a in changed_assets:
        for page in pages:
            rp = page.relative_to(ROOT).as_posix()
            cur = page.read_text(encoding='utf-8')
            old = show_base(rp, base)
            if old is None:
                continue  # 新增页面
            pat = re.compile(re.escape(a) + r'\?v=([\w-]+)')
            m_cur, m_old = pat.search(cur), pat.search(old)
            if m_cur and m_old and m_cur.group(1) == m_old.group(1):
                err(f'{rp}: {a} 改了但 ?v= 没 bump（{m_cur.group(1)}）')

    if data_changed:
        cur = (SITE / 'common.js').read_text(encoding='utf-8')
        old = show_base('site/common.js', base) or ''
        mc = re.search(r"DATA_BUILD = '([\w-]+)'", cur)
        mo = re.search(r"DATA_BUILD = '([\w-]+)'", old)
        if mc and mo and mc.group(1) == mo.group(1):
            err(f'数据改了但 common.js 的 DATA_BUILD 没 bump（仍为 {mc.group(1)}）')


def main():
    args = sys.argv[1:]
    base = 'origin/main'
    no_git = '--no-git' in args
    if '--base' in args:
        base = args[args.index('--base') + 1]

    validate_js()
    validate_data()
    if not no_git:
        validate_stamps(base)

    for w in WARN:
        print(f'⚠️  {w}')
    if ERR:
        print(f'\n❌ {len(ERR)} 项硬失败：')
        for e in ERR:
            print(f'  ✗ {e}')
        sys.exit(1)
    print(f'✅ 校验通过（{len(WARN)} 条软提醒）')


if __name__ == '__main__':
    main()
