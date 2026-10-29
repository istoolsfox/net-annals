#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""事件条目门禁校验器（CI 与本地共用，纯 stdlib）。

用法:
  python3 scripts/validate_events.py             # 全库结构校验（schema/枚举/id唯一/文件名一致）
  python3 scripts/validate_events.py <file...>   # 变更文件深度校验（另加同日标题查重 vs 全库）
退出码 0=通过，1=存在 error。warning 不拦截。

检查项（E=error 拦截 / W=warning 提示）：
  E  JSON 可解析且为数组；跳过点开头文件与 .parts
  E  文件名层码合法且与日期前缀一致（一条一文件时 date 全文件唯一）
  E  14 个必填字段齐全、类型正确；枚举合法
     （category/region 见 config；date_confidence ∈ verified|single-source|uncertain；
      date_accuracy ∈ exact|month|year，且 month/year 精度日期须归一到 01 日）
  E  id 与 date 前缀一致、全库唯一
  E  sources 非空数组，每条含 http(s) url + title
  E  （仅指定文件模式）同日标题字符重叠 >0.6 —— 与 add_events 入库查重同规则
  W  summary_30s < 20 字；slug 过通用；title > 48 字
"""
import glob
import json
import os
import re
import sys
from datetime import date

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, 'scripts')
from api.config import CATEGORIES, LAYER_NAMES, REGIONS, RE_DATE, RE_ID, layer_of  # noqa: E402
from new_entry import PLACEHOLDER_DETAIL, PLACEHOLDER_SUMMARY  # noqa: E402

EV = 'data/events'
CONFIDENCE = {'verified', 'single-source', 'uncertain'}
ACCURACY = {'exact', 'month', 'year'}
REQUIRED_STR = ('id', 'date', 'title', 'category', 'region', 'date_confidence',
                'date_accuracy', 'summary_30s', 'detail', 'impact', 'aftermath')
GENERIC_SLUGS = {'event', 'test', 'new', 'tmp', 'temp', 'x', 'foo'}
PLACEHOLDER_MARKS = ('请改成', '（改成', '标签1', PLACEHOLDER_SUMMARY, PLACEHOLDER_DETAIL)
YEAR_MIN, YEAR_MAX = 1900, date.today().year + 1   # 库情 1970 起，给历史条目留余量
MAX_FILE_BYTES = 2 * 1024 * 1024

# 行政区划骨架码（place 字段校验用；骨架缺失时为空集=跳过存在性检查）
try:
    with open('data/places.json', encoding='utf-8') as _pf:
        _pl = json.load(_pf)
    PLACE_CODES = ({p['code'] for p in _pl['provinces']} | {c['code'] for c in _pl['cities']}
                   | {c['code'] for c in _pl['counties']})
except Exception:
    PLACE_CODES = set()


def load_repo():
    """读全库：[(文件名, [events])]；坏 JSON 记为 error（存量文件必须可解析）。"""
    files, errors = [], []
    for f in sorted(glob.glob(os.path.join(EV, '*.json'))):
        if '/.' in f or '.parts' in f:
            continue
        try:
            if os.path.getsize(f) > MAX_FILE_BYTES:
                errors.append((f, '-', f'文件超过 {MAX_FILE_BYTES // 1024 // 1024}MB 上限'))
                continue
            with open(f, encoding='utf-8') as fh:
                files.append((f, json.load(fh)))
        except Exception as exc:
            errors.append((f, '-', f'JSON 解析失败: {exc}'))
    return files, errors


def check_event(f, e, idx, id_registry, errors, warnings):
    def err(msg):
        errors.append((f, f'[{idx}]', msg))

    def warn(msg):
        warnings.append((f, f'[{idx}]', msg))

    for k in REQUIRED_STR:
        v = e.get(k, None)
        if not isinstance(v, str):
            err(f'字段 {k} 缺失或非字符串')
    if not isinstance(e.get('milestone'), bool):
        err('字段 milestone 缺失或非布尔')
    if not isinstance(e.get('tags'), list) or any(not isinstance(t, str) for t in e.get('tags', [])):
        err('字段 tags 缺失或含非字符串')
    place = e.get('place')
    if place is not None:
        if not isinstance(place, list) or any(not isinstance(x, str) for x in place):
            err('字段 place 须为字符串数组（行政区划码，可带 p:/c:/k: 前缀）')
        else:
            for tok in place:
                m = re.fullmatch(r'(?:[pck]:)?(\d{2,6})', tok)
                if not m:
                    err(f'place 码格式非法: {tok}（2/4/6 位数字，如 ["c:320100","k:110108"]）')
                elif m.group(1) not in PLACE_CODES:
                    err(f'place 码不存在于骨架: {tok}')
    if err_in := [x for x in errors if x[0] == f and x[1] == f'[{idx}]']:
        return

    eid, edate, title = e['id'], e['date'], e['title']
    if e['category'] not in CATEGORIES:
        err(f'category 非法: {e["category"]}')
    if e['region'] not in REGIONS:
        err(f'region 非法: {e["region"]}')
    if e['date_confidence'] not in CONFIDENCE:
        err(f'date_confidence 非法: {e["date_confidence"]}')
    acc = e['date_accuracy']
    if acc not in ACCURACY:
        err(f'date_accuracy 非法: {acc}')
    if not RE_DATE.fullmatch(edate):
        err(f'date 格式非法: {edate}')
    else:
        try:
            date(*(int(x) for x in edate.split('-')))
        except ValueError:
            err(f'date 不是真实日期: {edate}')
        y = int(edate[:4])
        if not (YEAR_MIN <= y <= YEAR_MAX):
            err(f'年份超界（{YEAR_MIN}-{YEAR_MAX}，超出范围走站长内部管线）: {edate}')
        if acc == 'month' and not edate.endswith('-01'):
            err(f'month 精度日期须归一到 01 日: {edate}')
        if acc == 'year' and not edate.endswith('-01-01'):
            err(f'year 精度日期须归一到 01-01: {edate}')
    if not RE_ID.fullmatch(eid):
        err(f'id 不符合规范（YYYY-MM-DD-小写slug）: {eid}')
    elif not eid.startswith(edate):
        err(f'id 日期前缀与 date 不一致: {eid} vs {edate}')
    if eid in id_registry:
        err(f'id 全库重复: {eid}（已在 {id_registry[eid]}）')
    else:
        id_registry[eid] = os.path.relpath(f, EV)
    slug = eid[len(edate) + 1:] if eid.startswith(edate + '-') else ''
    if slug in GENERIC_SLUGS:
        warn(f'slug 过于通用: {slug}')
    if len(title) > 48:
        warn(f'title 超过 48 字（{len(title)}）')
    if len(e.get('summary_30s', '')) < 20:
        warn('summary_30s 少于 20 字')
    joined = json.dumps(e, ensure_ascii=False)
    if any(m in joined for m in PLACEHOLDER_MARKS):
        err('仍含模板占位符（请改成语义 slug / 真实来源链接等）')

    srcs = e.get('sources')
    if not isinstance(srcs, list) or not srcs:
        err('sources 缺失或为空（至少一条可溯源来源）')
    else:
        for s in srcs:
            if not isinstance(s, dict) or not isinstance(s.get('url'), str) \
                    or not isinstance(s.get('title'), str) \
                    or not (s.get('url', '').startswith('http://') or s.get('url', '').startswith('https://')):
                err('sources 条目须为 {url: http(s), title}')


def check_filename(f, entries, errors):
    base = os.path.basename(f)
    lay = layer_of(base)
    if lay not in LAYER_NAMES:
        errors.append((f, '-', f'文件名层码非法: {lay!r}'))
    m = re.match(r'^(\d{4}-\d{2}-\d{2})', base)
    if m and entries:
        dates = {e.get('date') for e in entries}
        if len(dates) > 1:
            errors.append((f, '-', '一条一文件：同一文件内出现多个不同 date'))
        elif m.group(1) not in dates:
            errors.append((f, '-', f'文件名日期 {m.group(1)} 与条目 date 不一致'))
        if len(entries) > 1:
            errors.append((f, '-', f'一条一文件：单条式文件只允许 1 个条目（现有 {len(entries)} 个）'))


def char_overlap(t1, t2):
    s1, s2 = set(t1), set(t2)
    if not s1 or not s2:
        return 0.0
    return len(s1 & s2) / min(len(s1), len(s2))


def main():
    files, errors = load_repo()
    warnings = list(errors)
    id_registry = {}

    targets = sys.argv[1:]
    if targets:
        # 显式指定的 .parts 产出文件：绕过点路径过滤进入同一套 schema 校验
        # （文件名层码规则不适用于 parts 多条批次，见下方 check_filename 跳过）
        for t in targets:
            try:
                with open(t, encoding='utf-8') as fh:
                    files.append((os.path.relpath(t, EV), json.load(fh)))
            except Exception as exc:
                errors.append((t, '-', f'JSON 解析失败: {exc}'))

    by_date = {}
    for f, entries in files:
        if not isinstance(entries, list):
            errors.append((f, '-', '顶层必须是数组'))
            continue
        if '.parts' not in f:
            check_filename(f, entries, errors)
        for i, e in enumerate(entries):
            if not isinstance(e, dict):
                errors.append((f, f'[{i}]', '条目必须是对象'))
                continue
            check_event(f, e, i, id_registry, errors, warnings)
            if isinstance(e, dict) and isinstance(e.get('date'), str):
                by_date.setdefault(e['date'], []).append((os.path.relpath(f, EV), e['title']))

    # 深度模式：指定文件 → 与全库做同日标题查重（与 add_events 入库规则一致）
    targets = sys.argv[1:]
    if targets:
        target_set = {os.path.relpath(t, EV) for t in targets}
        seen_pairs = set()
        for f, entries in files:
            rel = os.path.relpath(f, EV)
            for e in entries:
                if rel not in target_set or not isinstance(e, dict):
                    continue
                for rel2, t2 in by_date.get(e.get('date', ''), []):
                    if rel2 == rel or char_overlap(e.get('title', ''), t2) <= 0.6:
                        continue
                    pair = tuple(sorted((rel, rel2)))
                    if pair in seen_pairs:
                        continue
                    seen_pairs.add(pair)
                    errors.append((f, '-', f'同日相似标题（重叠>{0.6:g}）: "{e.get("title", "")}" ╌ {t2[:30]} ({rel2})'))

    rel = os.path.relpath
    for f, loc, msg in errors:
        print(f'E {rel(f)} {loc}: {msg}')
    shown = 0
    for f, loc, msg in warnings:
        if (f, loc, msg) not in errors:
            print(f'W {rel(f)} {loc}: {msg}')
            shown += 1
            if shown >= 50:
                print('W …（警告过多，仅显示前 50 条）')
                break
    n_events = sum(len(es) for _, es in files)
    print(f'—— 校验 {len(files)} 文件 / {n_events} 条：'
          f'{len(errors)} error，{shown} warning ——')
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
