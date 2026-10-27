#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性：把本地新闻采集归档里人工裁定过的候选写成编年条（.parts）。
用法: python3 scripts/batch_ingest_news.py
裁定原则（2026-10-27 两日归档人工过目）：
  - 只收 safe/disaster 且 imp>=3；股市日波动/热搜口水不收；
  - 同一事件多表述合并（巴青=那曲同一场7.0级地震）；
  - 来源：维基新闻动态门户（当日存档，可溯）+ 深挖词条（需通过强化相关性校验）；
  - 深挖校验强化：词条标题含年份须与事件同年；摘要有双向二字词重叠（防 2025旧页/1940开明街类错挖）。
红线同 glm_write.py：正文禁政治人物姓名、禁整句英文、逝世一句带过、不造数字。
产出: data/events/.parts/g_news_1.json → 人工复核后 add_events.py 入库"""
import json, os, re, sys, time, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, 'scripts')
import news_harvest as nh   # 复用 deep_dig/fetch；import 时会 chdir 到仓库根（本就在根）

KEY = nh.KEY
PORTAL = 'https://zh.wikipedia.org/wiki/Portal:新闻动态'

# 人工裁定后的入库清单（date=事件日期；terms=深挖搜索词；region/sens 已定）
ROWS = [
    {'date': '2026-10-26', 'text': '西藏那曲市巴青县发生7.0级地震，致16死76伤', 'try': ['巴青县', '西藏地震'],
     'title_hint': '西藏巴青7.0级地震', 'region': 'cn', 'cat': 'national', 'sens': 'disaster'},
    {'date': '2026-10-26', 'text': '俄罗斯鼠疫研究所一名研究人员感染肺鼠疫死亡，相关接触者隔离',
     'try': ['肺鼠疫', '鼠疫'], 'title_hint': '俄罗斯鼠疫研究所肺鼠疫死亡', 'region': 'world', 'cat': 'world', 'sens': 'disaster'},
    {'date': '2026-10-26', 'text': '日本发射火星卫星探测器，赴火卫一采样返回',
     'try': ['火星卫星探测器', 'MMX'], 'title_hint': '日本火星卫星探测器', 'region': 'world', 'cat': 'tech', 'sens': 'safe'},
    {'date': '2026-10-27', 'text': '长三角货物贸易进出口规模连续19个月增长',
     'try': ['长三角'], 'title_hint': '长三角外贸连续19个月增长', 'region': 'cn', 'cat': 'economy', 'sens': 'safe'},
    {'date': '2026-10-27', 'text': '博通为Anthropic敲定630亿美元融资安排',
     'try': ['Anthropic', '博通'], 'title_hint': '博通为Anthropic安排630亿美元融资', 'region': 'world', 'cat': 'tech', 'sens': 'safe'},
    {'date': '2026-10-27', 'text': '凯恩荣膺金球奖，系25年来首位英格兰球员',
     'try': ['金球奖'], 'title_hint': '凯恩金球奖', 'region': 'world', 'cat': 'culture', 'sens': 'safe'},
    {'date': '2026-10-27', 'text': '广电总局要求有线电视开机画面不得播放商业广告',
     'try': ['有线电视'], 'title_hint': '广电要求有线电视开机不播广告', 'region': 'cn', 'cat': 'society', 'sens': 'safe'},
    {'date': '2026-10-27', 'text': '泡泡玛特三季度收益预估同比下降45%-50%',
     'try': ['泡泡玛特'], 'title_hint': '泡泡玛特Q3收益预降', 'region': 'cn', 'cat': 'company', 'sens': 'safe'},
]

SYS = """你是中文编年史数据库的条目撰稿人。根据给定的当日新闻事实写一条编年史条目，输出单个JSON对象（不要代码块标记），字段：
{
 "slug": "英文小写短横线slug，2-4个单词",
 "title": "条目标题（简体，≤24字，事件主干，不要日期前缀）",
 "category": "从 milestone/internet/tech/hardware/company/product/national/world/society/culture/economy 选",
 "summary_30s": "80-120字摘要：含具体数字、发生机制、对比背景中的至少两项",
 "detail": "200-350字正文：只扩写给定事实与公认背景，不得新增任何具体数字/日期/人名；不确定细节用机制性描述带过",
 "impact": "影响：一句话",
 "aftermath": "后续：一句话",
 "tags": ["中文标签", "至少两个"]
}
铁律：1.全文简体。2.正文禁政治人物姓名（职务/机构泛称代替）；运动员/企业家/科学家可写名。3.禁整句英文，括号内英文专名可以。4.伤亡/灾害公正记录，数字如实引用给定事实，零渲染。5.绝不编造给定事实之外的数字和日期。"""


def strengthened_dig(row):
    """强化版深挖：搜索词人工指定 + 年份一致性 + 双向二字词重叠"""
    for term in row['try']:
        for lang in ('zh', 'en'):
            try:
                s = json.loads(nh.fetch(f'https://{lang}.wikipedia.org/w/rest.php/v1/search/page?q={nh.q(term)}&limit=1'))
                if not s.get('pages'):
                    continue
                pt = s['pages'][0]['title']
                summ = json.loads(nh.fetch(f'https://{lang}.wikipedia.org/api/rest_v1/page/summary/{nh.q(pt)}'))
                extract = summ.get('extract') or ''
                if len(extract) < 50:
                    continue
                yr = row['date'][:4]
                if re.search(r'\d{4}', pt) and yr not in pt and f'{int(yr)-1}' not in pt:
                    continue   # 词条标题年份与事件不符（防 2025旧页）
                clean_t = re.sub(r'[\d\s\-—·（）()，。]', '', row['text'])
                clean_p = re.sub(r'[\d\s\-—·（）()，。]', '', pt + extract[:200])
                gt = {clean_t[i:i+2] for i in range(len(clean_t)-1)}
                gp = {clean_p[i:i+2] for i in range(len(clean_p)-1)}
                if len(gt & gp) < 2:            # 双向重叠至少2个二字词
                    continue
                return {'url': summ.get('content_urls', {}).get('desktop', {}).get('page', ''),
                        'title': pt, 'extract': extract[:400]}
            except Exception:
                continue
    return None


def call_write(row, dig):
    user = json.dumps({'date': row['date'], '事件事实': row['text'],
                       '参考词条摘要': (dig or {}).get('extract', '')}, ensure_ascii=False)
    body = {'model': nh.MODEL, 'temperature': 0.3, 'thinking': {'type': 'disabled'},
            'messages': [{'role': 'system', 'content': SYS}, {'role': 'user', 'content': user}]}
    req = urllib.request.Request(nh.GLM, json.dumps(body).encode(),
                                 {'Content-Type': 'application/json', 'Authorization': f'Bearer {KEY}'})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                out = json.load(r)['choices'][0]['message']['content']
            d = json.loads(re.search(r'\{.*\}', out, re.S).group(0))
            slug = re.sub(r'[^a-z0-9-]', '', str(d.get('slug', '')).lower()).strip('-')
            if not slug:
                return None
            sources = [{'title': f"维基百科：新闻动态（{row['date']} 存档）", 'url': PORTAL, 'type': 'wiki'}]
            if dig and dig.get('url') and dig['url'] not in PORTAL:
                sources.append({'title': f"维基百科：{dig['title']}", 'url': dig['url'], 'type': 'wiki'})
            return {
                'id': f"{row['date']}-{slug}", 'date': row['date'],
                'date_accuracy': 'exact', 'date_confidence': 'single-source',
                'title': str(d['title'])[:30], 'category': row['cat'],
                'region': row['region'], 'milestone': False,
                'summary_30s': d['summary_30s'], 'detail': d['detail'],
                'impact': d['impact'], 'aftermath': d['aftermath'],
                'sources': sources,
                'tags': [str(t) for t in d.get('tags', [])][:4] or ['时事'],
            }
        except urllib.error.HTTPError:
            return None
        except Exception:
            if attempt == 2:
                return None
            time.sleep(2)


def main():
    # 库内同日查重索引
    lib = {}
    import glob
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

    results = []
    for row in ROWS:
        dig = strengthened_dig(row)
        tag = f"dig✓{dig['title']}" if dig else 'dig✗(仅门户源)'
        print(f"  {row['date']} {row['title_hint']} → {tag}")
        e = call_write(row, dig)
        if e is None:
            print(f"    ✗ GLM 写作失败/被滤，放弃")
            continue
        if any(ov(e['title'], t) > 0.6 for t in lib.get(e['date'], [])):
            print(f"    ✗ 同日库内相似，跳过")
            continue
        results.append(e)

    out = 'data/events/.parts/g_news_1.json'
    json.dump(results, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f"\n→ {out}: {len(results)} 条（候选 {len(ROWS)}）")
    for e in results:
        print(f"  ✓ {e['id']} [{e['category']}] {e['title']} | src×{len(e['sources'])}")


if __name__ == '__main__':
    main()
