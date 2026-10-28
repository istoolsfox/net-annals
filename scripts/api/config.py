#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""API 全局配置：路径/配额/枚举/正则——唯一真相源。
被 api 服务端、build_api_db.py、validate_events.py 共用。
铁律：本模块保持纯 stdlib，不得 import fastapi 或任何 web 依赖。"""
import os
import re

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 相对路径，运行方负责 os.chdir(PROJECT_ROOT)（app.py 导入时已做）
DB_PATH = os.path.join('data', 'derived', 'api', 'events.db')
KEY_FILE = os.path.join('config', 'api_keys.json')
KEY_LOCK = os.path.join('config', '.api_keys.lock')
USAGE_DB = os.path.join('data', 'derived', 'api', 'usage.db')

API_PREFIX = '/api/v1/'

# ── 三层公开模型配额 ──────────────────────────────────────────────
ANON_DAILY = 200            # 匿名层：IP 每日配额
ANON_PERMIN = 20            # 匿名层：每分钟突发
RO_PERMIN = 120             # ro key：每分钟突发
ADMIN_PERMIN = 30           # admin：每分钟突发（admin 也只剩只读端点）
REG_PER_IP_DAY = 3          # 每 IP 每天可自助领取 key 数
DEFAULT_RO_QUOTA = 2000     # ro 默认日配额

# ── 滥用防线 ──────────────────────────────────────────────────────
MAX_CONC_PER_IP = 8         # 单 IP 并发处理上限（恶意并发兜底；nginx limit_conn 是第一道）
MAX_BODY_BYTES = 16384      # 请求体外层上限（gate 按 Content-Length 头拒绝）
REGISTER_BODY_MAX = 4096    # register 端点实际读取上限（外层拒超大，这层兜真实体）
PROBE_LIMIT = 20            # PROBE_WINDOW 内无效 key 探测达此值 → 封 IP
PROBE_WINDOW = 600          # 探测窗口（秒）
BAN_HOURS = 1               # 探测封禁时长
CONC_BURST_AFTER = 5        # 并发超限 429 的 Retry-After（秒）
MAX_ETAG_BYTES = 262144     # 响应体超过此值不做 ETag/304（免 MB 级缓冲放大）

# ── 校验正则/枚举（查询侧输入 + 贡献校验共用同一套） ───────────────
RE_YEAR = re.compile(r'(19|20)\d{2}')
RE_DATE = re.compile(r'\d{4}-\d{2}-\d{2}')
RE_ID = re.compile(r'[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z0-9][a-z0-9-]{1,100}')
RE_LAYER = re.compile(r'[a-z0-9]{0,16}')
RE_KEY = re.compile(r'NA-[0-9a-f]{48}')
RE_SLUG = re.compile(r'[a-z0-9][a-z0-9-]{0,80}')       # persons/entities 等条目 id
RE_FREEWORD = re.compile(r'[a-z0-9\u4e00-\u9fff][^;]{0,60}')  # kind/field 类自由词（禁止分隔符注入形状）

CATEGORIES = {'milestone', 'internet', 'tech', 'hardware', 'company', 'product',
              'national', 'world', 'society', 'culture', 'economy'}
REGIONS = {'cn', 'world'}
SORTS = {'date_asc': 'date ASC, id ASC', 'date_desc': 'date DESC, id DESC'}

# 领域层：文件名后缀码 → 中文名。新增领域层在此登记即可（文件命名 <年段>-<码>.json）。
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

# 事件源文件命名两种形态：
#   年段式   2000-2004-games.json / 1972-1985.json（既有批次文件，余部即层码）
#   单条式   1994-04-20-games-<slug>.json（PR 贡献，一条一文件）
#           1994-04-20-<slug>.json（主时间线贡献，无层码）
def layer_of(filename):
    """文件名 → 领域层码。识别不了一律归主时间线('')，绝不编造层码。"""
    name = os.path.basename(filename)[:-5]
    stripped = re.sub(r'^\d{4}(?:-\d{2,4})*-?', '', name)
    if stripped == '' or stripped in LAYER_NAMES:
        return stripped
    head = stripped.split('-', 1)[0]
    return head if head in LAYER_NAMES else ''
