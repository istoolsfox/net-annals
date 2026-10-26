#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""新闻采集器（GAP_FINDER 工作流C/D 本地版）：时事热点采集 + AI初筛 + 深挖 + 本地归档。
用法:
  python3 scripts/news_harvest.py --mode hourly   轻扫（维基新闻动态门户+当年页当月），追加 jsonl
  python3 scripts/news_harvest.py --mode daily    全量（+Google News热点+百度热搜），AI深挖，写日归档
产出:
  data/derived/daily/YYYY-MM-DD.json        daily 归档（含深挖结果）
  data/derived/daily/hourly_YYYY-MM-DD.jsonl hourly 增量（每行一条）
  data/derived/daily/_seen.json             跨次去重库（保留最近8000 cid）
纪律: 本地候选库，绝不进站点构建、不进 git；AI 只输出类目/评分/标题，敏感词表永不进 prompt。"""
import json, os, re, sys, time, html, calendar, hashlib, glob, urllib.request, urllib.parse, urllib.error
from datetime import datetime
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DAILY = 'data/derived/daily'
SEEN_F = f'{DAILY}/_seen.json'
N8N_FLAG = 'data/derived/n8n_active.json'   # n8n 接管握手文件：存在且7天内 → 本脚本让位


def n8n_active():
    if not os.path.exists(N8N_FLAG):
        return False
    return time.time() - os.path.getmtime(N8N_FLAG) < 7 * 86400
UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) net-annals-news/1.0 (contact: toolsfox.cn)'}
_key_path = os.path.expanduser('~/.config/net-annals/glm.key')
KEY = open(_key_path).read().strip() if os.path.exists(_key_path) else None
GLM = 'https://open.bigmodel.cn/api/paas/v4/chat/completions'
MODEL = 'glm-5.3-flash'
MODE = 'daily' if 'daily' in sys.argv[1:] else 'hourly'
TODAY = datetime.now()
# 门户页导航噪音：命中即丢弃
JUNK = re.compile(r'维基新闻|Wikinews|存档|提交|提供新闻|點此|点此|编辑|查看|历史|摘要|本月|上月|下月|'
                  r'新闻动态|当前事件|當前事件|首页|首頁|分类|分類|指南|討論|讨论|条目|條目|刷新|purge|'
                  r'更多当今|更多當今|阅读其他|閱讀其他')


def fetch(url, timeout=25):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode('utf-8', 'ignore')


def strip_tags(t):
    t = re.sub(r'<script.*?</script>|<style.*?</style>', '', t, flags=re.S)
    t = re.sub(r'<[^>]+>', '', t)
    return html.unescape(t).strip()


def q(s):
    return urllib.parse.quote(s)


def _lis(raw, min_len):
    body = re.sub(r'<script.*?</script>|<style.*?</style>', '', raw, flags=re.S)
    out = []
    for li in re.findall(r'<li[^>]*>(.*?)</li>', body, re.S):
        t = re.sub(r'^\((图|圖)\)\s*', '', strip_tags(li))
        if len(t) < min_len or JUNK.search(t):
            continue
        m = re.search(r'href="(/wiki/[^"#]+)"', li)
        link = ('https://zh.wikipedia.org' + m.group(1)) if m and ':' not in m.group(1) else ''
        out.append((t, link))
    return out


# ── 源1: 中文维基 新闻动态门户（聚合近数日） ──
def src_zh_portal(d):
    raw = fetch(f'https://zh.wikipedia.org/wiki/{q("Portal:新闻动态")}')
    return [{'date': d.strftime('%Y-%m-%d'), 'text': t[:230], 'link': lk, 'src': 'zh维基新闻动态'}
            for t, lk in _lis(raw, 14)]


# ── 源2: 英文维基 Current events 当日页 ──
def src_en_portal(d):
    title = f'Portal:Current events/{d.year}_{calendar.month_name[d.month]}_{d.day}'
    raw = fetch(f'https://en.wikipedia.org/wiki/{q(title)}')
    return [{'date': d.strftime('%Y-%m-%d'), 'text': t[:260], 'link': lk, 'src': 'en维基当前事件'}
            for t, lk in _lis(raw, 15)]


# ── 源3: 当年中国大陆页（只取当月，更早归每周 gap-finder） ──
def src_zh_year(d):
    raw = fetch(f'https://zh.wikipedia.org/wiki/{q(f"{d.year}年中国大陆")}')
    out = []
    for t, lk in _lis(raw, 8):
        m = re.match(r'^(\d{1,2})月(\d{1,2})日', t)
        if m and int(m.group(1)) == d.month:
            out.append({'date': f'{d.year}-{d.month:02d}-{int(m.group(2)):02d}',
                        'text': t[:230], 'src': f'{d.year}年中国大陆'})
    return out


# ── 源4: Google News 中文热点（daily） ──
def src_gnews(d):
    xml = fetch('https://news.google.com/rss?hl=zh-CN&gl=CN&ceid=CN:zh-Hans', timeout=20)
    out = []
    for it in re.findall(r'<item>(.*?)</item>', xml, re.S)[:60]:
        m = re.search(r'<title>(.*?)</title>', it, re.S)
        if not m:
            continue
        title = re.sub(r'\s*-\s*[^-]{2,22}$', '', strip_tags(m.group(1)))
        if len(title) >= 10:
            out.append({'date': d.strftime('%Y-%m-%d'), 'text': title[:200], 'src': 'google-news'})
    return out


# ── 源5: 百度热搜（daily，尽力而为） ──
def src_baidu(d):
    raw = fetch('https://top.baidu.com/board?tab=realtime', timeout=15)
    out = []
    for m in re.finditer(r'"word":"([^"]{6,44})"', raw):
        out.append({'date': d.strftime('%Y-%m-%d'), 'text': m.group(1), 'src': '百度热搜'})
    return out


# ── GLM 初筛（1301 整批拒绝→递归二分；单条拒绝=强敏感信号） ──
SYS_NEWS = """你是新闻事件分诊员。对输入JSON数组逐条评审，输出JSON数组，每项：
{"i":编号,"sens":"safe|disaster|politics|crime|social","imp":1到5,"deep_dig":布尔,"title":"简体标题(≤24字)","note":""}
- sens：safe=科技/经济/公司/文化/体育/民生/工程；disaster=天灾/事故/疫情；politics=政治/外交/军事/时政人事；crime=刑案/暴力；social=纠纷/风波
- imp：5=全国或全球性大事/转折；4=行业或地区标志性；3=有实际影响；2=一般；1=琐屑（热搜口水帖/日常播报/一句话花边）
- deep_dig：值得继续深挖（有背景、有数字、有后续价值，且 imp>=4）为 true
- title：简体标题；繁体文本也输出简体
只依据文本本身判断，只输出JSON数组，无任何其他文字。"""


def glm_batch(items):
    if not KEY:
        return {}
    body = {'model': MODEL, 'temperature': 0.1, 'thinking': {'type': 'disabled'},
            'messages': [{'role': 'system', 'content': SYS_NEWS},
                         {'role': 'user', 'content': json.dumps(items, ensure_ascii=False)}]}
    req = urllib.request.Request(GLM, json.dumps(body).encode(),
                                 {'Content-Type': 'application/json', 'Authorization': f'Bearer {KEY}'})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            out = json.load(r)['choices'][0]['message']['content']
        arr = json.loads(re.search(r'\[.*\]', out, re.S).group(0))
        return {int(x['i']): x for x in arr if isinstance(x, dict) and 'i' in x}
    except urllib.error.HTTPError:
        return None
    except Exception:
        return None


def glm_screen(rows):
    out = {}

    def rec(idxs):
        items = [{'i': k, 'text': rows[k]['text'][:220]} for k in idxs]
        res = glm_batch(items)
        if res is not None:
            for k in idxs:
                out[k] = res.get(k, {'sens': 'unknown', 'imp': 0, 'deep_dig': False, 'title': ''})
            return
        if len(idxs) == 1:
            out[idxs[0]] = {'sens': 'politics', 'imp': 0, 'deep_dig': False,
                            'title': '', 'note': 'provider_filtered'}
            return
        m = len(idxs) // 2
        rec(idxs[:m])
        rec(idxs[m:])

    rec(list(range(len(rows))))
    return out


# ── 深挖：渐进截短搜索 + 条目链接候选，逐个验证摘要质量与相关性 ──
def deep_dig(item):
    title = (item.get('title') or item['text'])[:26]
    text = item.get('text') or ''

    def valid_summary(summ):
        pt = summ.get('title', '')
        extract = summ.get('extract') or ''
        if len(pt) > 26 or pt.endswith('列表') or re.fullmatch(r'\d{1,4}年?', pt) or len(extract) < 50:
            return None
        # 相关性：词条标题（去数字标点）须与原文共享至少一个二字词
        clean = re.sub(r'[\d\s\-—·（）()\-–，。]', '', pt)
        grams = {clean[i:i + 2] for i in range(len(clean) - 1)} if len(clean) >= 2 else {clean}
        if not any(g in text for g in grams if len(g) == 2):
            return None
        return {'url': summ.get('content_urls', {}).get('desktop', {}).get('page', ''),
                'title': pt, 'extract': extract[:500]}

    def try_summary(lang, t):
        try:
            s = json.loads(fetch(f'https://{lang}.wikipedia.org/w/rest.php/v1/search/page?q={q(t)}&limit=1'))
            if not s.get('pages'):
                return None
            return valid_summary(json.loads(fetch(
                f'https://{lang}.wikipedia.org/api/rest_v1/page/summary/{q(s["pages"][0]["title"])}')))
        except Exception:
            return None

    # 1) 渐进截短搜索：整题→逐字截短→4字止
    base = re.sub(r'^（图）|^\(图\)', '', title)
    for n in range(min(12, len(base)), 3, -1):
        for lang in ('zh', 'en'):
            r = try_summary(lang, base[:n])
            if r:
                return r
    # 2) 条目内链接兜底
    link = item.get('link') or ''
    if '/wiki/' in link:
        try:
            t = urllib.parse.unquote(link.split('/wiki/', 1)[1])
            summ = json.loads(fetch(f'https://zh.wikipedia.org/api/rest_v1/page/summary/{q(t)}'))
            r = valid_summary(summ)
            if r:
                return r
        except Exception:
            pass
    return None


def cid(text):
    return hashlib.md5((text or '').encode()).hexdigest()[:12]


def main():
    t0 = time.time()
    os.makedirs(DAILY, exist_ok=True)
    if n8n_active():
        print(f'[让位] 检测到 {N8N_FLAG}（n8n 已接管采集），本次跳过。')
        return
    seen_set = set(json.load(open(SEEN_F, encoding='utf-8'))['cids']) if os.path.exists(SEEN_F) else set()

    # 库内同日标题索引：给候选打 existing_hint（是否疑似已收录）
    lib_day = {}
    for f in glob.glob('data/events/*.json'):
        if '/.' in f or '.parts' in f:
            continue
        for e in json.load(open(f, encoding='utf-8')):
            lib_day.setdefault(e['date'][:10], []).append(e['title'])

    sources = [src_zh_portal, src_en_portal, src_zh_year] + \
              ([src_gnews, src_baidu] if MODE == 'daily' else [])
    raw, src_stat = [], {}
    with ThreadPoolExecutor(max_workers=4) as ex:
        for f, res in zip(sources, ex.map(lambda f: _safe(f, TODAY), sources)):
            src_stat[f.__name__] = len(res)
            raw.extend(res)

    # 站内去重 + 跨次去重
    uniq, seen_now = [], []
    for r in raw:
        c = cid(r['text'])
        if c in seen_set or any(r['text'] == u['text'] for u in uniq):
            continue
        seen_now.append(c)
        uniq.append(r)

    scores = glm_screen(uniq)

    def _sig(s):
        return set(re.sub(r'[\s《》「」『』·、，。：；\-—（）()"\']', '', s or ''))

    def _ov(a, b):
        A, B = _sig(a), _sig(b)
        m = min(len(A), len(B))
        return len(A & B) / m if m else 0

    items = []
    for k, r in enumerate(uniq):
        s = scores.get(k, {})
        hint = max((_ov(r['text'][:60], t) for t in lib_day.get(r['date'], [])), default=0)
        items.append({**r, 'cid': cid(r['text']),
                      'title': (s.get('title') or r['text'][:24])[:26],
                      'sens': s.get('sens', 'unknown'), 'imp': s.get('imp', 0),
                      'deep_dig': bool(s.get('deep_dig')), 'note': s.get('note', ''),
                      'existing_hint': round(hint, 2)})

    dug = 0
    if MODE == 'daily':
        targets = [it for it in items if it['deep_dig'] and it['imp'] >= 4 and it['sens'] != 'crime'][:30]
        with ThreadPoolExecutor(max_workers=3) as ex:
            for it, dig in zip(targets, ex.map(deep_dig, targets)):
                if dig:
                    it['dig'] = dig
                    dug += 1

    stamp = TODAY.strftime('%Y-%m-%d')
    ts = datetime.now().isoformat(timespec='seconds')
    if MODE == 'daily':
        path = f'{DAILY}/{stamp}.json'
        json.dump({'generated_at': ts, 'mode': MODE, 'sources': src_stat,
                   'raw_total': len(raw), 'items': items},
                  open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        if os.path.exists(SEEN_F):
            seen = json.load(open(SEEN_F, encoding='utf-8'))
        else:
            seen = {'cids': []}
        seen['cids'] = (seen_now + seen['cids'])[-8000:]
        json.dump(seen, open(SEEN_F, 'w', encoding='utf-8'), ensure_ascii=False)
    else:
        path = f'{DAILY}/hourly_{stamp}.jsonl'
        with open(path, 'a', encoding='utf-8') as f:
            for it in items:
                f.write(json.dumps({**it, 'ts': ts}, ensure_ascii=False) + '\n')

    hi = [it for it in items if it['imp'] >= 4]
    print(f'[{MODE}] {ts} 耗时{time.time()-t0:.0f}s')
    print(f'原始 {len(raw)} {src_stat} → 去重后新增 {len(items)}')
    print(f"sens: {dict(Counter(it['sens'] for it in items))}")
    print(f'高价值 imp>=4: {len(hi)} | 深挖成功: {dug} | 归档: {path}')


def _safe(fn, d):
    try:
        return fn(d)
    except Exception as e:
        print(f'  [源失败] {fn.__name__}: {type(e).__name__} {str(e)[:60]}')
        return []


if __name__ == '__main__':
    main()
