#!/usr/bin/env python3
"""编年史构建门禁：校验 data/events/*.json → 合并生成 site/data.json。

用法：python3 scripts/build.py
校验不过 → 退出码 1，列出全部错误；校验通过 → 输出统计并写 site/data.json。
另：按时代切分输出 site/data/（index.json + shard-0..7.json），供前端按时代
惰性加载——时代归属逻辑与 site/app.js 的 eraIndex() 必须严格一致。
"""
import gzip
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVENTS_DIR = ROOT / "data" / "events"
OUT = ROOT / "site" / "data.json"

REQUIRED = ["id", "date", "date_accuracy", "date_confidence", "title", "category",
            "region", "milestone", "summary_30s", "detail", "impact", "aftermath", "sources"]
TEXT_FIELDS = ["title", "summary_30s", "detail", "impact", "aftermath"]
ACCURACY = {"exact", "month", "year"}
CONFIDENCE = {"verified", "single-source", "uncertain"}
CATEGORIES = {"milestone", "internet", "tech", "hardware", "company", "product",
              "national", "world", "society", "culture", "economy"}
REGIONS = {"cn", "world"}
SOURCE_TYPES = {"wiki", "news", "official", "blog", "archive", "book", "video"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ID_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-[a-z0-9-]+$")
MONTH_CAP = 1000

errors, warnings = [], []


def valid_date(s: str) -> bool:
    if not DATE_RE.match(s):
        return False
    try:
        date.fromisoformat(s)
        return True
    except ValueError:
        return False


def check_event(e: dict, fname: str, i: int, span: tuple[int, int]) -> None:
    where = f"{fname}[{i}]"
    for k in REQUIRED:
        if k not in e:
            errors.append(f"{where}: 缺字段 {k}")
    if not isinstance(e.get("id"), str) or not ID_RE.match(e["id"]):
        errors.append(f"{where}: id 不合法（应为 'YYYY-MM-DD-小写slug'）：{e.get('id')!r}")
    elif not e["id"].startswith(e["date"]):
        errors.append(f"{where}: id 日期前缀与 date 不一致：{e['id']} vs {e['date']}")
    d = e.get("date", "")
    if not valid_date(d):
        errors.append(f"{where}: date 不是合法日期：{d!r}")
    elif not (span[0] <= d <= span[1]):
        errors.append(f"{where}: date {d} 超出文件年段 {span[0]}~{span[1]}")
    if e.get("date_accuracy") not in ACCURACY:
        errors.append(f"{where}: date_accuracy 非法：{e.get('date_accuracy')!r}")
    if e.get("date_confidence") not in CONFIDENCE:
        errors.append(f"{where}: date_confidence 非法：{e.get('date_confidence')!r}")
    if e.get("category") not in CATEGORIES:
        errors.append(f"{where}: category 非法：{e.get('category')!r}")
    if e.get("region") not in REGIONS:
        errors.append(f"{where}: region 非法：{e.get('region')!r}")
    if not isinstance(e.get("milestone"), bool):
        errors.append(f"{where}: milestone 必须是布尔")
    for f in TEXT_FIELDS:
        v = e.get(f)
        if not isinstance(v, str) or not v.strip():
            errors.append(f"{where}: {f} 为空")
    srcs = e.get("sources")
    if not isinstance(srcs, list) or not srcs:
        errors.append(f"{where}: sources 为空，每条必须可溯源")
    else:
        for s in srcs:
            if not isinstance(s, dict) or not s.get("title") or not s.get("url"):
                errors.append(f"{where}: sources 条目缺 title/url：{s!r}")
            elif not str(s["url"]).startswith("http"):
                errors.append(f"{where}: source url 非 http(s)：{s.get('url')!r}")
            elif s.get("type") and s["type"] not in SOURCE_TYPES:
                warnings.append(f"{where}: source type 非标准：{s['type']!r}（容忍）")
    acc = e.get("date_accuracy")
    if acc in ("month", "year") and valid_date(d) and d[8:10] != "01":
        errors.append(f"{where}: accuracy={acc} 时 date 应为当月/当年 01 日：{d}")
    if e.get("date_confidence") == "uncertain":
        warnings.append(f"{where}: uncertain 条目「{e.get('title','?')}」——确认 notes 已记录")


def main() -> int:
    if not EVENTS_DIR.exists():
        print(f"✗ 找不到 {EVENTS_DIR}")
        return 1
    files = sorted(p for p in EVENTS_DIR.glob("*.json")
                   if not p.name.startswith(".") and ".parts" not in p.name)
    if not files:
        print("✗ data/events/ 下没有任何 JSON")
        return 1

    all_events: list[dict] = []
    seen_ids: set[str] = set()
    month_counter: dict[str, int] = {}
    per_year: dict[int, int] = {}
    milestone_total = 0
    confidence_stat = {"verified": 0, "single-source": 0, "uncertain": 0}

    for f in files:
        # 两种命名：年段式 2000-2004-games.json（批次文件）/ 单条式 1994-04-20-tech-slug.json（PR 贡献）
        m = re.match(r"^(\d{4})-(\d{4})(?:-[a-z0-9-]+)?\.json$", f.name)
        if m:
            span = (f"{m.group(1)}-01-01", f"{m.group(2)}-12-31")
        else:
            m1 = re.match(r"^(\d{4}-\d{2}-\d{2})(?:-[a-z0-9-]+)?\.json$", f.name)
            if not m1:
                errors.append(f"{f.name}: 文件名不符合 <起年>-<止年>[-层码].json 或 <日期>[-层码]-slug.json")
                continue
            span = (m1.group(1), m1.group(1))   # 单条式：文件内所有条目必须同日
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{f.name}: JSON 解析失败 —— {exc}")
            continue
        if not isinstance(data, list):
            errors.append(f"{f.name}: 顶层必须是数组")
            continue
        for i, e in enumerate(data):
            check_event(e, f.name, i, span)
            eid = e.get("id")
            if eid in seen_ids:
                errors.append(f"{f.name}[{i}]: id 重复：{eid}")
            seen_ids.add(eid)
            d = e.get("date", "")
            if valid_date(d):
                month_counter[d[:7]] = month_counter.get(d[:7], 0) + 1
                per_year[int(d[:4])] = per_year.get(int(d[:4]), 0) + 1
            all_events.append(e)

    over = {k: v for k, v in month_counter.items() if v > MONTH_CAP}
    for k, v in sorted(over.items()):
        errors.append(f"{k} 月条数 {v} 超过上限 {MONTH_CAP}")

    if errors:
        print(f"✗ 校验失败，共 {len(errors)} 个错误：\n")
        for err in errors:
            print(f"  - {err}")
        return 1

    all_events.sort(key=lambda e: e["date"])
    payload = {
        "generated": datetime.now().astimezone().isoformat(timespec="seconds"),
        "count": len(all_events),
        "events": all_events,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    n = len(all_events)
    milestone_total = sum(1 for e in all_events if e.get("milestone"))
    for e in all_events:
        confidence_stat[e.get("date_confidence", "uncertain")] += 1

    # ── 时代分片输出（site/data/）────────────────────────────────────────────
    # 时代定义与 site/app.js 的 ERAS 数组完全一致；归属算法与 app.js eraIndex() 同构。
    # 改动任一侧必须同步另一侧，否则前端分片内容与时代归属会错位。
    ERAS = [
        ("接入前史", (1986, 1994.4)),
        ("拨号时代", (1994.4, 2000)),
        ("门户与泡沫", (2000, 2003)),
        ("Web2.0 前夜", (2003, 2005)),
        ("Web2.0", (2005, 2010)),
        ("移动互联网", (2010, 2015)),
        ("移动成熟", (2015, 2020)),
        ("疫情与智能", (2020, 2027)),
    ]

    def era_index(d: str) -> int:
        """year + (month-1)/12 落入左闭右开区间；越界钳制到第 0 / 最后一个时代"""
        yf = int(d[:4]) + (int(d[5:7]) - 1) / 12
        for i, (_, (lo, hi)) in enumerate(ERAS):
            if lo <= yf < hi:
                return i
        return 0 if yf < ERAS[0][1][0] else len(ERAS) - 1

    shards: list[list[dict]] = [[] for _ in ERAS]
    for e in all_events:                    # all_events 已按 date 排序，各分片天然有序
        shards[era_index(e["date"])].append(e)

    data_dir = OUT.parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    eras_manifest = []
    for i, (name, rng) in enumerate(ERAS):
        shard_name = f"shard-{i}.json"
        shard_text = json.dumps(shards[i], ensure_ascii=False, separators=(",", ":"))
        (data_dir / shard_name).write_text(shard_text, encoding="utf-8")
        gz_path = data_dir / (shard_name + ".gz")
        with open(gz_path, "wb") as gf:
            with gzip.GzipFile(filename="", mode="wb", fileobj=gf, mtime=0, compresslevel=9) as g:
                g.write(shard_text.encode("utf-8"))
        eras_manifest.append({"name": name, "range": [rng[0], rng[1]], "shard": shard_name})

    # 分类计数 + 高频标签：工具栏 chips 需要全量统计，放 manifest 里随 index.json 下发，
    # 前端不必为画 chips 而全量加载事件（标签只下发 ≥10 次的，前端仍按 ≥60 过滤）
    cat_counts: dict[str, int] = {}
    tag_counter: dict[str, int] = {}
    for e in all_events:
        cat_counts[e["category"]] = cat_counts.get(e["category"], 0) + 1
        for t in e.get("tags") or []:
            tag_counter[t] = tag_counter.get(t, 0) + 1
    tags_top = sorted(((t, c) for t, c in tag_counter.items() if c >= 10),
                      key=lambda x: (-x[1], x[0]))[:500]

    index_manifest = {
        "generated": payload["generated"],
        "total": n,
        "verified": confidence_stat["verified"],
        "milestones": milestone_total,
        "sourceCount": len({s["url"] for e in all_events for s in e.get("sources", [])}),
        "cats": cat_counts,
        "tags": tags_top,
        "eras": eras_manifest,
    }
    index_text = json.dumps(index_manifest, ensure_ascii=False, separators=(",", ":"))
    (data_dir / "index.json").write_text(index_text, encoding="utf-8")
    with open(data_dir / "index.json.gz", "wb") as gf:
        with gzip.GzipFile(filename="", mode="wb", fileobj=gf, mtime=0, compresslevel=9) as g:
            g.write(index_text.encode("utf-8"))

    years = sorted(per_year)
    print(f"✓ 校验通过：{n} 条事件（{years[0]}–{years[-1]}），里程碑 {milestone_total} 条")
    print(f"  日期置信：verified {confidence_stat['verified']} / single-source "
          f"{confidence_stat['single-source']} / uncertain {confidence_stat['uncertain']}")
    print(f"  警告 {len(warnings)} 条")
    for w in warnings[:20]:
        print(f"    - {w}")
    if len(warnings) > 20:
        print(f"    … 其余 {len(warnings) - 20} 条略")
    months = sorted(month_counter)
    if months:
        thin = [k for k in months if month_counter[k] < 5]
        print(f"  月度密度：覆盖 {len(months)} 个月，平均 {n / len(months):.1f} 条/月；<5条的薄月 {len(thin)} 个"
              + (f"（最早：{', '.join(thin[:5])}…）" if thin else ""))
    print("  按年分布：")
    for y in years:
        bar = "█" * max(1, min(60, per_year[y] // 10))
        print(f"    {y}  {per_year[y]:4d}  {bar}")
    print(f"✓ 已生成 {OUT.relative_to(ROOT)}")
    print(f"✓ 已生成 {data_dir.relative_to(ROOT)}/（index.json + {len(ERAS)} 个时代分片（含.gz预压缩）："
          + "，".join(f"shard-{i} {len(s)} 条" for i, s in enumerate(shards)) + "）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
