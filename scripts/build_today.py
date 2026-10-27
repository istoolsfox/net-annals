#!/usr/bin/env python3
"""历史上的今天：把编年库按 MM-DD 索引 → site/today/data.json + .gz
用法：python3 scripts/build_today.py"""
import glob
import gzip
import json
import os
import re
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "events")
OUT_DIR = os.path.join(ROOT, "site", "today")

# 层名中文映射（构建端直接产出 layer_label，前端不猜）
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


def layer_of(fname):
    """1986-2026-science.json → science；1986-1995.json → ''（主时间线）"""
    name = fname[:-5] if fname.endswith(".json") else fname
    stripped = re.sub(r"^\d{4}(?:-\d{4})*-?", "", name)
    return stripped if stripped in LAYER_NAMES else (stripped or "")


days = {}
total = 0
for f in sorted(glob.glob(os.path.join(DATA, "*.json"))):
    layer = layer_of(os.path.basename(f))
    try:
        data = json.load(open(f, encoding="utf-8"))
    except Exception:
        continue
    if not isinstance(data, list):
        continue
    for e in data:
        if not isinstance(e, dict):
            continue
        date = str(e.get("date", ""))
        m = re.match(r"^\d{4}-(\d{2})-(\d{2})$", date)
        if not m:
            continue
        key = m.group(1) + "-" + m.group(2)
        days.setdefault(key, []).append({
            "id": e.get("id", ""),
            "date": date,
            "title": e.get("title", ""),
            "summary": (e.get("summary_30s", e.get("summary", "")) or "")[:110],
            "milestone": bool(e.get("milestone")),
            "layer": LAYER_NAMES.get(layer, layer or "编年"),
        })
        total += 1

for evs in days.values():
    evs.sort(key=lambda x: x["date"])

generated = datetime.now().astimezone().isoformat(timespec="seconds")
text = json.dumps({"generated": generated,
                   "count": total, "days": days},
                  ensure_ascii=False, separators=(",", ":"))
os.makedirs(OUT_DIR, exist_ok=True)
dst = os.path.join(OUT_DIR, "data.json")
open(dst, "w", encoding="utf-8").write(text)
with open(dst + ".gz", "wb") as gf:
    with gzip.GzipFile(filename="", mode="wb", fileobj=gf, mtime=0, compresslevel=9) as g:
        g.write(text.encode("utf-8"))
print(f"✓ 历史上的今天构建完成：{total} 条覆盖 {len(days)} 天 → site/today/data.json（{os.path.getsize(dst)//1024}KB + .gz）")


def write_pair(path, obj):
    """月度小文件成对输出：.gz 为主（DecompressionStream 解压），.json 兜底"""
    t = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    open(path, "w", encoding="utf-8").write(t)
    with open(path + ".gz", "wb") as gf:
        with gzip.GzipFile(filename="", mode="wb", fileobj=gf, mtime=0, compresslevel=9) as g:
            g.write(t.encode("utf-8"))


# 月度分片（2026-10-26 手机端提速）：整包 974KB gz 首屏太重 → meta（约 2KB）
# + 12 个月度小文件按需懒取。data.json 保留作为旧缓存页与无 DecompressionStream 环境兜底。
month_dir = os.path.join(OUT_DIR, "data")
os.makedirs(month_dir, exist_ok=True)
months, month_days = {}, {}
for key, evs in days.items():
    m = key[:2]
    months[m] = months.get(m, 0) + len(evs)
    month_days[m] = month_days.get(m, 0) + 1
meta = {"generated": generated, "count": total,
        "dayCount": len(days), "months": months, "monthDays": month_days}
write_pair(os.path.join(month_dir, "meta.json"), meta)
emitted = []
for m in sorted(months):
    sub = {k: v for k, v in days.items() if k.startswith(m)}
    p = os.path.join(month_dir, f"m{m}.json")
    write_pair(p, {"days": sub})
    emitted.append(f"{m}({os.path.getsize(p + '.gz') // 1024}KB)")
print(f"✓ 月度分片 → site/today/data/：meta + {' '.join(emitted)}")
