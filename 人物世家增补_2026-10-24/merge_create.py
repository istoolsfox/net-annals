# -*- coding: utf-8 -*-
"""第二轮补齐合并：新人物/新世家入册 + 新时间线事件插入分片 + 重建 index.json 与 today/data.json + 首页计数。

用法：python merge_create.py <site目录> <out2目录>
校验规则：id 全库唯一（人物/世家/事件各自集合 + 跨类型不冲突）、日期格式、category ∈ 11 类、
sources ≥1、timeline 10~18、在世者 death 必须为空。任何记录不合规 → 拒收并报告。
"""
import json, os, sys, re, glob, collections, datetime

site = sys.argv[1] if len(sys.argv) > 1 else '../site'
out2 = sys.argv[2] if len(sys.argv) > 2 else './out2'
DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')
CATS = {'milestone', 'internet', 'tech', 'hardware', 'company', 'product', 'national', 'world', 'society', 'culture', 'economy'}
P_FIELDS = {'ai', 'internet', 'hardware', 'company', 'game', 'creator', 'science', 'finance', 'media', 'sport'}
NOW = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime('%Y-%m-%dT%H:%M:%S+08:00')
report = {'applied_p': 0, 'applied_e': 0, 'applied_ev': 0, 'rejected': []}


def load(p):
    with open(p, encoding='utf-8') as f:
        return json.load(f)


def dump(obj, p):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        json.dump(obj, f, ensure_ascii=False, separators=(',', ':'))


def check_sources(srcs, rid, where):
    ok = [s for s in (srcs or []) if isinstance(s, dict) and str(s.get('url', '')).startswith('http') and str(s.get('title', '')).strip()]
    if len(ok) < 1:
        report['rejected'].append(f'{where}:{rid} 无有效来源')
    return ok


W_TYPES = {'film', 'tv', 'book', 'netnovel', 'music', 'game', 'comic', 'documentary', 'variety'}


def merge_works():
    """新建作品志：out-w*.json 全量校验入册 works/data.json。"""
    data = {'generated': NOW, 'count': 0, 'works': []}
    wp = os.path.join(site, 'works/data.json')
    if os.path.exists(wp):
        data = load(wp)
    arr = data['works']
    existing = {r['id'] for r in arr}
    for f in sorted(glob.glob(os.path.join(out2, 'out-w*.json'))):
        try:
            batch = load(f)
        except Exception as e:
            report['rejected'].append(f'{os.path.basename(f)} 解析失败: {e}')
            continue
        for w in batch if isinstance(batch, list) else []:
            wid = str(w.get('id', '')).strip()
            where = os.path.basename(f)
            if not wid or not re.match(r'^[\w-]+$', wid):
                report['rejected'].append(f'{where}: 非法id {wid!r}'); continue
            if wid in existing:
                report['rejected'].append(f'{where}:{wid} id 冲突'); continue
            if w.get('type') not in W_TYPES:
                report['rejected'].append(f'{wid}: type 非法 {w.get("type")}'); continue
            if not DATE_RE.match(str(w.get('released', ''))):
                report['rejected'].append(f'{wid}: released 坏日期'); continue
            tl = w.get('timeline') or []
            if not (6 <= len(tl) <= 20) or len(w.get('bio') or '') < 150:
                report['rejected'].append(f'{wid}: timeline/bio 不达标 ({len(tl)}/{len(w.get("bio") or "")})'); continue
            tl_ok, bad = [], False
            for t in tl:
                if not DATE_RE.match(str(t.get('date', ''))):
                    report['rejected'].append(f'{wid}: 坏日期 {t.get("date")}'); bad = True; break
                tl_ok.append({'date': t['date'], 'acc': t.get('acc', 'exact') if t.get('acc') in ('exact', 'month', 'year') else 'year', 'text': str(t.get('text', '')).strip()})
            if bad:
                continue
            w['timeline'] = sorted(tl_ok, key=lambda t: t['date'])
            if not check_sources(w.get('sources'), wid, where):
                continue
            w['sources'] = [x for x in w['sources'] if str(x.get('url', '')).startswith('http')]
            arr.append(w)
            existing.add(wid)
            report['applied_w'] = report.get('applied_w', 0) + 1
    data['count'] = len(arr)
    data['generated'] = NOW
    dump(data, wp)
    return len(arr)


def merge_records(kind):
    """新人物/世家入册。返回 (既有id集合, 更新后的数组)。"""
    fname = f'{kind}/data.json'
    data = load(os.path.join(site, fname))
    key = 'persons' if kind == 'persons' else 'entities'
    arr = data[key]
    existing = {r['id'] for r in arr}
    files = sorted(glob.glob(os.path.join(out2, f'out-[nm]*.json')))
    if kind == 'persons':
        files = [f for f in files if re.search(r'out-n\d+\.json$', f)]
    else:
        files = [f for f in files if re.search(r'out-m\d+\.json$', f)]
    for f in files:
        try:
            batch = load(f)
        except Exception as e:
            report['rejected'].append(f'{os.path.basename(f)} 解析失败: {e}')
            continue
        for r in batch if isinstance(batch, list) else []:
            rid = str(r.get('id', '')).strip()
            where = os.path.basename(f)
            if not rid or not re.match(r'^[\w-]+$', rid):
                report['rejected'].append(f'{where}: 非法id {rid!r}')
                continue
            if rid in existing:
                report['rejected'].append(f'{where}:{rid} 与既有记录 id 冲突')
                continue
            tl = r.get('timeline') or []
            if kind == 'persons':
                if r.get('field') not in P_FIELDS:
                    report['rejected'].append(f'{rid}: field 非法 {r.get("field")}'); continue
            if r.get('status') and r['status'] not in ('active', 'declined', 'acquired', 'privatized', 'closed'):
                report['rejected'].append(f'{rid}: status 非法'); continue
            if len(r.get('bio') or '') < 150:
                report['rejected'].append(f'{rid}: bio 过短'); continue
            if not (8 <= len(tl) <= 20):
                report['rejected'].append(f'{rid}: timeline {len(tl)} 条越界'); continue
            tl_ok, bad = [], False
            for t in tl:
                if not DATE_RE.match(str(t.get('date', ''))):
                    report['rejected'].append(f'{rid}: 坏日期 {t.get("date")}'); bad = True; break
                tl_ok.append({'date': t['date'], 'acc': t.get('acc', 'exact') if t.get('acc') in ('exact', 'month', 'year') else 'year', 'text': str(t.get('text', '')).strip()})
            if bad:
                continue
            r['timeline'] = sorted(tl_ok, key=lambda t: t['date'])
            if not check_sources(r.get('sources'), rid, where):
                continue
            r['sources'] = [s for s in r['sources'] if str(s.get('url', '')).startswith('http')]
            if kind == 'persons' and not r.get('death'):
                r['death'] = None
            arr.append(r)
            existing.add(rid)
            report['applied_p' if kind == 'persons' else 'applied_e'] += 1
    data['count'] = len(arr)
    data['generated'] = NOW
    dump(data, os.path.join(site, fname))
    return existing, arr


def merge_events():
    """新事件插入分片（按 era 归属、日期升序）。"""
    era_of = json.load(open(os.path.join(site, 'data/index.json'), encoding='utf-8'))
    eras = era_of['eras']

    def era_index(date):
        yf = int(date[:4]) + (int(date[5:7]) - 1) / 12
        for i, e in enumerate(eras):
            if e['range'][0] <= yf < e['range'][1]:
                return i
        return 0 if yf < eras[0]['range'][0] else len(eras) - 1

    shards = []
    for e in eras:
        shards.append(load(os.path.join(site, 'data', e['shard'])))
    all_ids = {ev['id'] for sh in shards for ev in sh}
    all_keys = {(ev['date'], ev['title']) for sh in shards for ev in sh}

    files = sorted(glob.glob(os.path.join(out2, 'out-t*.json'))) + sorted(glob.glob(os.path.join(out2, 'out-s*.json')))
    for f in files:
        try:
            batch = load(f)
        except Exception as e:
            report['rejected'].append(f'{os.path.basename(f)} 解析失败: {e}')
            continue
        for ev in batch if isinstance(batch, list) else []:
            rid = str(ev.get('id', '')).strip()
            date = str(ev.get('date', ''))
            where = os.path.basename(f)
            if not DATE_RE.match(date):
                report['rejected'].append(f'{where}:{rid} 坏日期 {date}'); continue
            if not re.match(r'^[\w-]+$', rid):
                report['rejected'].append(f'{where}: 非法id {rid!r}'); continue
            if rid in all_ids:
                report['rejected'].append(f'{where}:{rid} id 冲突'); continue
            if (date, ev.get('title')) in all_keys:
                report['rejected'].append(f'{where}:{rid} 与既有事件同日同题（疑似重复）'); continue
            if ev.get('category') not in CATS:
                report['rejected'].append(f'{where}:{rid} category 非法 {ev.get("category")}'); continue
            if not (30 <= len(str(ev.get('title', ''))) and len(str(ev.get('detail', ''))) >= 40):
                report['rejected'].append(f'{where}:{rid} 文本过短'); continue
            srcs = check_sources(ev.get('sources'), rid, where)
            if not srcs:
                continue
            ev['sources'] = srcs
            ev['milestone'] = bool(ev.get('milestone'))
            ev['layer'] = '主时间线'
            i = era_index(date)
            shards[i].append(ev)
            shards[i].sort(key=lambda x: x['date'])
            all_ids.add(rid)
            all_keys.add((date, ev.get('title')))
            report['applied_ev'] += 1
    for e, sh in zip(eras, shards):
        dump(sh, os.path.join(site, 'data', e['shard']))
    return shards, eras


def rebuild_manifest(shards, eras):
    cats = collections.Counter()
    tags = collections.Counter()
    total = verified = 0
    src_urls = set()
    for sh in shards:
        for ev in sh:
            total += 1
            cats[ev['category']] += 1
            if ev.get('milestone'):
                pass
            if ev.get('date_confidence') == 'verified':
                verified += 1
            for s in ev.get('sources', []):
                src_urls.add(s.get('url'))
            for t in ev.get('tags', []):
                tags[t] += 1
    manifest = load(os.path.join(site, 'data/index.json'))
    manifest['generated'] = NOW
    manifest['total'] = total
    manifest['verified'] = verified
    manifest['milestones'] = sum(1 for sh in shards for ev in sh if ev.get('milestone'))
    manifest['sourceCount'] = len(src_urls)
    manifest['cats'] = dict(cats)
    manifest['tags'] = [[t, n] for t, n in tags.most_common(60)]
    dump(manifest, os.path.join(site, 'data/index.json'))


def rebuild_today(shards):
    days = collections.defaultdict(list)
    for sh in shards:
        for ev in sh:
            k = ev['date'][5:10]
            days[k].append({'id': ev['id'], 'date': ev['date'], 'title': ev['title'],
                            'summary': ev.get('summary_30s', ''), 'milestone': bool(ev.get('milestone')),
                            'layer': ev.get('layer', '主时间线')})
    for k in days:
        days[k].sort(key=lambda x: x['date'])
    out = {'generated': NOW, 'count': sum(len(v) for v in days.values()), 'days': dict(days)}
    dump(out, os.path.join(site, 'today/data.json'))


if __name__ == '__main__':
    _, persons_arr = merge_records('persons')
    _, entities_arr = merge_records('entities')
    merge_works()
    shards, eras = merge_events()
    rebuild_manifest(shards, eras)
    rebuild_today(shards)
    print(f"新人物 +{report['applied_p']} | 新世家 +{report['applied_e']} | 新事件 +{report['applied_ev']} | 新作品 +{report.get('applied_w', 0)} | 拒收 {len(report['rejected'])}")
    for r in report['rejected'][:20]:
        print('  -', r)
