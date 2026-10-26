#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GLM 初筛：对 gap_candidates.json 的缺口+边缘候选做敏感性/重要性/类目评审。
用法: python3 scripts/glm_screen.py [--limit N]
产出: data/derived/gap_scored.json
密钥: ~/.config/net-annals/glm.key（仓库外，chmod 600）
红线纪律：prompt 只含类目词，不含任何敏感词表。
批失败自动二分；单条仍被拒 = 供应商内容过滤 = 强敏感信号，标记 sens=politics。"""
import json, os, re, sys, time, urllib.request, urllib.error
from collections import Counter

KEY = open(os.path.expanduser('~/.config/net-annals/glm.key')).read().strip()
URL = 'https://open.bigmodel.cn/api/paas/v4/chat/completions'
MODEL = 'glm-5.3-flash'
BATCH = 25

SYS = """你是中文编年史数据库的候选事件评审员。对输入JSON数组里的每条候选（带编号i）逐条评审，输出一个JSON数组，每个元素：
{"i":编号,"usable":布尔,"sens":"safe|disaster|politics|crime|social","imp":1到5的整数,"cat":"类目","title":"简体标题","date_fix":""}

字段规则：
- usable：值得历史数据库收录为 true。琐碎的内部行政事务、无历史意义的一句话、不是事件 → false。若给出「库内相似条目」且候选与其明显是同一事件，usable=false；是不同事件则正常评审。
- sens 敏感类目（只按类目判断）：safe=科技/互联网/经济/公司产品/文化/体育/民生/建设工程；disaster=天灾/事故/疫情等公正记录类；politics=政治人事/会议/外交/军事/时政；crime=刑事案件/暴力/个人悲剧；social=维权纠纷/劳资/社会风波。
- imp 重要性：5=全国或行业转折点、全国第一/首次/最大；4=行业或地区标志性；3=有具体影响的普通事件；2=一般；1=琐碎。
- cat 从这些里选一个：milestone/internet/tech/hardware/company/product/national/world/society/culture/economy
- title：把候选文本转成简体字标题（≤22字，去掉日期前缀保留事件主干）。
- date_fix：仅当文本中出现与给定 date 矛盾、或更明确的完整日期时，填 "YYYY-MM-DD" 或 "YYYY-MM"，否则填空串。
- 繁体文本正常理解，title 一律输出简体。
只依据候选文本本身判断，不要外部想象。输出必须是纯JSON数组，不要任何其他文字或代码块标记。"""


def call_once(items):
    body = {'model': MODEL, 'temperature': 0.1, 'thinking': {'type': 'disabled'},
            'messages': [{'role': 'system', 'content': SYS},
                         {'role': 'user', 'content': json.dumps(items, ensure_ascii=False)}]}
    req = urllib.request.Request(
        URL, json.dumps(body).encode(),
        {'Content-Type': 'application/json', 'Authorization': f'Bearer {KEY}'})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            out = json.load(r)['choices'][0]['message']['content']
        arr = json.loads(re.search(r'\[.*\]', out, re.S).group(0))
        return {int(x['i']): x for x in arr if isinstance(x, dict) and 'i' in x}
    except urllib.error.HTTPError as e:
        body_txt = e.read().decode()[:150]
        print(f'\n  [HTTP {e.code}] {body_txt}')
        return None
    except Exception as e:
        print(f'\n  [{type(e).__name__}] {str(e)[:120]}')
        return None


def screen(items, rows):
    """返回 {index: 评审}；单条被拒标记供应商过滤。"""
    for attempt in range(2):
        res = call_once(items)
        if res is not None:
            return res
        time.sleep(1.5)
    if len(items) == 1:
        return {}
    mid = len(items) // 2
    left = screen(items[:mid], rows)
    right = screen(items[mid:], rows)
    left.update(right)
    return left


def main():
    g = json.load(open('data/derived/gap_candidates.json', encoding='utf-8'))
    rows = [{**r, '_kind': 'missing'} for r in g['missing']]
    rows += [{**r, '_kind': 'borderline'} for r in g['borderline']]
    if '--limit' in sys.argv:
        rows = rows[:int(sys.argv[sys.argv.index('--limit') + 1])]
    batches = [rows[i:i + BATCH] for i in range(0, len(rows), BATCH)]

    scored = []
    for bi, batch in enumerate(batches):
        items = []
        for j, r in enumerate(batch):
            it = {'i': j, 'date': r['date'], 'text': r['text'][:180]}
            if r['_kind'] == 'borderline' and r.get('vs_title'):
                it['库内相似条目'] = r['vs_title']
            items.append(it)
        res = screen(items, batch)
        for j, r in enumerate(batch):
            s = res.get(j)
            if s is None:
                # 供应商过滤：单条重试仍被拒 → 强敏感信号
                s = {'usable': True, 'sens': 'politics', 'imp': 0, 'cat': '',
                     'title': '', 'date_fix': '', 'note': 'provider_filtered'}
            scored.append({**r, 'usable': s.get('usable'), 'sens': s.get('sens'),
                           'imp': s.get('imp'), 'cat': s.get('cat'),
                           'title': s.get('title'), 'date_fix': s.get('date_fix') or '',
                           'note': s.get('note', '')})
        print(f'\r  批 {bi + 1}/{len(batches)}', end='', flush=True)
    print()
    json.dump(scored, open('data/derived/gap_scored.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    ok = [s for s in scored if s.get('usable')]
    print(f"评审 {len(scored)} → usable {len(ok)}")
    print('sens:', dict(Counter(s.get('sens') for s in ok)))
    print('imp 分布:', dict(sorted(Counter(s.get('imp') for s in ok).items())))
    pf = sum(1 for s in scored if s.get('note') == 'provider_filtered')
    print(f'供应商过滤单条: {pf}')


if __name__ == '__main__':
    main()
