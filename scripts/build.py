#!/usr/bin/env python3
"""编年史构建门禁：校验 data/events/*.json → 合并生成 site/data.json。

用法：python3 scripts/build.py
校验不过 → 退出码 1，列出全部错误；校验通过 → 输出统计并写 site/data.json。
"""
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
    files = sorted(EVENTS_DIR.glob("*.json"))
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
        m = re.match(r"^(\d{4})-(\d{4})(?:-[a-z0-9-]+)?\.json$", f.name)
        if not m:
            errors.append(f"{f.name}: 文件名不符合 <起年>-<止年>.json")
            continue
        span = (f"{m.group(1)}-01-01", f"{m.group(2)}-12-31")
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
    years = sorted(per_year)
    print(f"✓ 校验通过：{n} 条事件（{years[0]}–{years[-1]}），里程碑 {milestone_total} 条")
    print(f"  日期置信：verified {confidence_stat['verified']} / single-source "
          f"{confidence_stat['single-source']} / uncertain {confidence_stat['uncertain']}")
    print(f"  警告 {len(warnings)} 条")
    for w in warnings[:20]:
        print(f"    - {w}")
    if len(warnings) > 20:
        print(f"    … 其余 {len(warnings) - 20} 条略")
    print("  按年分布：")
    for y in years:
        bar = "█" * max(1, min(60, per_year[y] // 10))
        print(f"    {y}  {per_year[y]:4d}  {bar}")
    print(f"✓ 已生成 {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
