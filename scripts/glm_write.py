#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GLM 写条目：把初筛通过的缺口候选写成 14 字段编年条（.parts 文件）。
用法: python3 scripts/glm_write.py [--min-imp 4] [--limit N]
产出: data/events/.parts/g_gapfinder_1.json
入库规则：单源（维基年份页）→ date_confidence=single-source；milestone 全 false。
红线：正文禁政治人物姓名（职务泛称）；不夹整句英文；逝世一句带过；
     detail 只扩写候选已有事实+公认背景，不得新增具体数字/日期。"""
import json, os, re, sys, time, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor

KEY = open(os.path.expanduser('~/.config/net-annals/glm.key')).read().strip()
URL = 'https://open.bigmodel.cn/api/paas/v4/chat/completions'
MODEL = 'glm-5.3-flash'
TEMPLATE = json.load(open('data/events/.parts/g_2004_2006.json', encoding='utf-8'))[0]

SYS = f"""你是中文编年史数据库的条目撰稿人。根据给定的候选事件文本写一条编年史条目，输出单个JSON对象（不要代码块标记），字段如下：
{{
 "slug": "英文小写短横线slug，2-4个单词，如 beidou-first-satellite",
 "title": "条目标题（简体，≤24字，事件主干，不要日期前缀）",
 "category": "从 milestone/internet/tech/hardware/company/product/national/world/society/culture/economy 选",
 "summary_30s": "80-120字摘要：必须含具体数字、发生机制、与此前/同期对比中的至少两项",
 "detail": "200-400字正文：只能扩写候选文本已有的事实和公认背景，不得新增任何具体数字/日期/人名/地名；不确定的细节用机制性描述带过",
 "impact": "影响：一句话，说明这件事改变了什么",
 "aftermath": "后续：一句话，这件事之后的发展或现状",
 "tags": ["中文标签", "至少两个"]
}}

写作铁律：
1. 全文简体字。
2. 正文（summary/detail/impact/aftermath）禁止出现政治人物姓名，用职务或机构泛称代替；企业家/科学家/运动员/艺术家的姓名可以写。
3. 禁止整句英文；禁止把英文当普通名词用（如"logo"要写"标识"）；括号内的英文专有名词可以。
4. 逝世相关只一句带过（时间+享年/人数+公开原因），零渲染。
5. 天灾/事故/疫情类公正记录，伤亡数字如实引用候选文本，不加形容词渲染。
6. 只依据候选文本+公认背景，绝不能编造具体数字和日期。
7. detail 里如候选文本提到具体数字可沿用，但没有的数字一个都不要造。"""


def call_write(row):
    year_page = f"https://zh.wikipedia.org/wiki/{urllib.parse.quote(str(row['year']) + '年中国大陆')}"
    user = json.dumps({'date': row['date'], '候选文本': row['text']}, ensure_ascii=False)
    body = {'model': MODEL, 'temperature': 0.3, 'thinking': {'type': 'disabled'},
            'messages': [{'role': 'system', 'content': SYS},
                         {'role': 'user', 'content': user}]}
    req = urllib.request.Request(
        URL, json.dumps(body).encode(),
        {'Content-Type': 'application/json', 'Authorization': f'Bearer {KEY}'})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                out = json.load(r)['choices'][0]['message']['content']
            m = re.search(r'\{.*\}', out, re.S)
            d = json.loads(m.group(0))
            slug = re.sub(r'[^a-z0-9-]', '', str(d.get('slug', '')).lower()).strip('-')
            if not slug:
                return None
            date = row['date_fix'] if re.match(r'^\d{4}-\d{2}(-\d{2})?$', row.get('date_fix', '')) else row['date']
            acc = 'month' if len(date) == 7 else row['acc']
            # 来源：队列候选携带词条 URL（src_url）优先，否则回退年份页（首个 GAP_FINDER 批次口径）
            src_url = row.get('src_url') or year_page
            src_title = urllib.parse.unquote(src_url.split('/wiki/')[-1]).replace('_', ' ')
            e = {
                'id': f"{date}-{slug}", 'date': date,
                'date_accuracy': acc, 'date_confidence': 'single-source',
                'title': str(d['title'])[:30], 'category': d.get('category', 'society'),
                'region': 'cn', 'milestone': False,
                'summary_30s': d['summary_30s'], 'detail': d['detail'],
                'impact': d['impact'], 'aftermath': d['aftermath'],
                'sources': [{'title': f"维基百科：{src_title}",
                             'url': src_url, 'type': 'wiki'}],
                'tags': [str(t) for t in d.get('tags', [])][:4] or ['中国'],
            }
            return e
        except urllib.error.HTTPError:
            return None   # 内容过滤：此候选放弃自动写，留在队列
        except Exception:
            if attempt == 2:
                return None
            time.sleep(2)


def main():
    scored = json.load(open('data/derived/gap_scored.json', encoding='utf-8'))
    min_imp = int(sys.argv[sys.argv.index('--min-imp') + 1]) if '--min-imp' in sys.argv else 4
    allow = ('safe', 'disaster', 'politics') if '--all-sens' in sys.argv else ('safe', 'disaster')
    rows = [r for r in scored
            if r.get('usable') and r.get('sens') in allow
            and (r.get('imp') or 0) >= min_imp and not r.get('note')]
    if '--limit' in sys.argv:
        rows = rows[:int(sys.argv[sys.argv.index('--limit') + 1])]
    print(f'待写 {len(rows)} 条（imp≥{min_imp}，{"|".join(allow)}）')

    # 库内同日再查重（防写作期间库变化+边缘漏网）
    import glob
    lib = {}
    for f in glob.glob('data/events/*.json'):
        if '/.' in f or '.parts' in f:
            continue
        for e in json.load(open(f, encoding='utf-8')):
            lib.setdefault(e['date'][:10], []).append(e['title'])

    def sig(s):
        return set(re.sub(r'[\s《》「」『』·、，。：；\-—（）()"\']', '', s or ''))

    def ov(a, b):
        A, B = sig(a), sig(b)
        m = min(len(A), len(B))
        return len(A & B) / m if m else 0

    results, skipped = [], 0
    if '--out' in sys.argv:
        out = sys.argv[sys.argv.index('--out') + 1]
    else:
        out = 'data/events/.parts/g_gapfinder_1.json'
    with ThreadPoolExecutor(max_workers=5) as ex:
        for e in ex.map(call_write, rows):
            if e is None:
                skipped += 1
                continue
            if any(ov(e['title'], t) > 0.6 for t in lib.get(e['date'][:10], [])):
                skipped += 1
                continue
            results.append(e)
            print(f'\r  已写 {len(results)} / 跳过 {skipped}', end='', flush=True)
            if len(results) % 20 == 0:   # 增量落盘，防中途丢失
                json.dump(results, open(out, 'w', encoding='utf-8'),
                          ensure_ascii=False, indent=1)
    print()
    json.dump(results, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'→ {out}: {len(results)} 条（API失败/查重跳过 {skipped}）')


if __name__ == '__main__':
    main()
