#!/usr/bin/env python3
"""part 文件校验器：python3 scripts/validate_part.py data/events/.parts/xxx.json
校验子Agent产出的条目数组，全部通过退出码0；否则列出错误退出码1。"""
import json, re, sys

REQUIRED = ["id", "date", "date_accuracy", "date_confidence", "title", "category", "region",
            "milestone", "summary_30s", "detail", "impact", "aftermath", "sources", "tags"]
CATEGORIES = {"milestone", "internet", "tech", "hardware", "company", "product",
              "national", "world", "society", "culture", "economy"}
ID_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-[a-z0-9-]+$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

def main(path):
    try:
        items = json.load(open(path, encoding="utf-8"))
    except Exception as exc:
        print(f"✗ JSON 解析失败: {exc}")
        return 1
    if not isinstance(items, list) or not items:
        print("✗ 顶层必须是非空数组")
        return 1
    errs = []
    seen = set()
    for i, e in enumerate(items):
        w = f"[{i}]"
        for k in REQUIRED:
            if k not in e:
                errs.append(f"{w} 缺字段 {k}")
        eid = e.get("id", "")
        if not ID_RE.match(eid):
            errs.append(f"{w} id 不合法: {eid!r}")
        elif not eid.startswith(e.get("date", "")):
            errs.append(f"{w} id 前缀与 date 不一致: {eid} vs {e.get('date')}")
        if eid in seen:
            errs.append(f"{w} id 重复: {eid}")
        seen.add(eid)
        d = e.get("date", "")
        if not DATE_RE.match(d):
            errs.append(f"{w} date 格式非法: {d!r}")
        acc, conf = e.get("date_accuracy"), e.get("date_confidence")
        if acc not in {"exact", "month", "year"}:
            errs.append(f"{w} date_accuracy 非法: {acc!r}")
        if conf not in {"verified", "single-source", "uncertain"}:
            errs.append(f"{w} date_confidence 非法: {conf!r}")
        if acc in ("month", "year") and DATE_RE.match(d) and d[8:10] != "01":
            errs.append(f"{w} accuracy={acc} 时 date 须为当月/当年01日: {d}")
        if e.get("category") not in CATEGORIES:
            errs.append(f"{w} category 非法: {e.get('category')!r}")
        if e.get("region") not in {"cn", "world"}:
            errs.append(f"{w} region 非法: {e.get('region')!r}")
        if not isinstance(e.get("milestone"), bool):
            errs.append(f"{w} milestone 须为布尔")
        sl, dl = len(e.get("summary_30s", "")), len(e.get("detail", ""))
        if sl < 60:
            errs.append(f"{w} summary_30s 仅{sl}字（≥60，建议75-90）: {e.get('title','')[:20]}")
        if not 150 <= dl <= 700:
            errs.append(f"{w} detail {dl}字（须150-700）")
        for f in ("impact", "aftermath", "title"):
            if not str(e.get(f, "")).strip():
                errs.append(f"{w} {f} 为空")
        srcs = e.get("sources", [])
        if not isinstance(srcs, list) or not srcs:
            errs.append(f"{w} sources 为空")
        else:
            for s in srcs:
                if not (isinstance(s, dict) and s.get("title") and str(s.get("url", "")).startswith("http")):
                    errs.append(f"{w} source 缺 title/url 或 url 非 http: {s!r}")
                if isinstance(s, dict) and s.get("type") and s["type"] not in {"wiki","news","official","blog","archive","book","video"}:
                    errs.append(f"{w} source type 非标准: {s['type']}")
        if not isinstance(e.get("tags"), list) or len(e["tags"]) < 2:
            errs.append(f"{w} tags 至少2个")
    if errs:
        print(f"✗ {len(errs)} 个错误:")
        for x in errs:
            print("  -", x)
        return 1
    print(f"✓ {len(items)} 条全部通过: " + "、".join(e["id"][:13] for e in items))
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
