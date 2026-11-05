#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""临时构建器：按市合并写入 data/events/.parts/auto_geo_city_w5.json。
用法: python3 -I scripts/tmp_build_w5.py <city_key>
city_key ∈ guigang|hezhou|hechi|danzhou|zigong|neijiang
写前 json.load 校验；含同日标题重叠、id 唯一、日期约束检查。
"""
import json, sys, os, glob, re

EV = 'data/events'
PARTS = os.path.join(EV, '.parts', 'auto_geo_city_w5.json')

def E(id_, date, acc, conf, title, cat, summary, detail, impact, aftermath, sources, tags):
    return {
        "id": id_, "date": date, "date_accuracy": acc, "date_confidence": conf,
        "title": title, "category": cat, "region": "cn", "milestone": False,
        "place": [],  # 由城市键填充
        "summary_30s": summary, "detail": detail, "impact": impact, "aftermath": aftermath,
        "sources": sources, "tags": tags,
    }

CITY_PLACE = {"guigang": "c:4508", "hezhou": "c:4511", "hechi": "c:4512",
              "danzhou": "c:4604", "zigong": "c:5103", "neijiang": "c:5110"}
CITY_NAME = {"guigang": "贵港市", "hezhou": "贺州市", "hechi": "河池市",
             "danzhou": "儋州市", "zigong": "自贡市", "neijiang": "内江市"}

def load_entries(key):
    """各市条目定义从 tmp_w5_data_<key>.json 读取。"""
    path = os.path.join('scripts', f'tmp_w5_data_{key}.json')
    with open(path, encoding='utf-8') as fh:
        return json.load(fh)

def overlap(t1, t2):
    s1, s2 = set(t1), set(t2)
    if not s1 or not s2:
        return 0.0
    return len(s1 & s2) / min(len(s1), len(s2))

def main():
    key = sys.argv[1]
    place = CITY_PLACE[key]
    new_entries = load_entries(key)
    for e in new_entries:
        e['place'] = [place]

    # 全库 id 与 (date,title)
    id_reg = {}
    date_titles = []
    for f in glob.glob(os.path.join(EV, '**', '*.json'), recursive=True):
        try:
            arr = json.load(open(f, encoding='utf-8'))
        except Exception:
            continue
        for e in arr if isinstance(arr, list) else []:
            if isinstance(e, dict) and 'id' in e:
                id_reg[e['id']] = f
                date_titles.append((e.get('date'), e.get('title', '')))
    # 已有 parts
    if os.path.exists(PARTS):
        arr = json.load(open(PARTS, encoding='utf-8'))
    else:
        arr = []
    for e in arr:
        id_reg[e['id']] = PARTS
        date_titles.append((e['date'], e['title']))

    problems = []
    for e in new_entries:
        if e['id'] in id_reg:
            problems.append(f"id 重复: {e['id']} -> {id_reg[e['id']]}")
        if not e['id'].startswith(e['date']):
            problems.append(f"id 前缀不符: {e['id']}")
        if e['date_accuracy'] == 'month' and not e['date'].endswith('-01'):
            problems.append(f"month 未归一: {e['id']}")
        if e['date_accuracy'] == 'year' and not e['date'].endswith('-01-01'):
            problems.append(f"year 未归一: {e['id']}")
        if len(e['title']) > 48:
            problems.append(f"title 过长({len(e['title'])}): {e['id']}")
        if CITY_NAME[key] not in e['title'] and CITY_NAME[key][:-1] not in e['title']:
            problems.append(f"title 缺市名: {e['id']}")
        if len(e['summary_30s']) < 20 or CITY_NAME[key] not in e['summary_30s']:
            problems.append(f"summary 不合规: {e['id']}")
        if len(e['impact']) < 40 or len(e['aftermath']) < 40:
            problems.append(f"impact/aftermath 过短: {e['id']}")
        if not (4 <= len(e['tags']) <= 6):
            problems.append(f"tags 数量: {e['id']}")
        y = int(e['date'][:4])
        if y < 1970:
            problems.append(f"早于1970: {e['id']}")
        for d, t in date_titles:
            if d == e['date'] and t and overlap(t, e['title']) > 0.55:
                problems.append(f"同日标题重叠 {overlap(t, e['title']):.2f}: {e['id']} vs {t}")
    if problems:
        print('BUILD ABORT:')
        for p in problems:
            print(' -', p)
        sys.exit(1)

    arr.extend(new_entries)
    with open(PARTS, 'w', encoding='utf-8') as fh:
        json.dump(arr, fh, ensure_ascii=False, indent=2)
    print(f"{key}: +{len(new_entries)} -> total {len(arr)}")

if __name__ == '__main__':
    main()
