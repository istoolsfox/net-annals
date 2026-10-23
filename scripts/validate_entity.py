#!/usr/bin/env python3
"""世家条目校验器：python3 scripts/validate_entity.py data/entities/.parts/xxx.json
按 ENTITIES_SPEC.md 强制校验，全部通过退出码0。"""
import json, re, sys

FIELDS = ["id", "name", "type", "region", "founded", "founded_accuracy", "dissolved",
          "status", "headline", "summary_30s", "timeline", "milestones", "legacy", "sources", "tags"]
TYPES = {"company", "community", "institution"}
STATUS = {"active", "declined", "acquired", "privatized", "closed"}
ID_RE = re.compile(r"^[a-z0-9-]+$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# 红线粗筛：领导人姓名（命中即拒）
BLOCK = ["习近平", "李克强", "李强", "胡锦涛", "温家宝", "江泽民", "毛泽东", "邓小平", "周恩来",
         "朱镕基", "薄熙来", "周永康", "孙政才", "令计划", "彭丽媛", "栗战书", "汪洋", "王沪宁",
         "赵乐际", "韩正", "蔡奇", "丁薛祥", "李鹏", "华国锋", "林彪", "四人帮", "刘少奇",
         "特朗普", "拜登", "普京", "金正恩", "泽连斯基", "安倍", "莫迪", "埃尔多安"]
EMPTY_WORDS = ["不断发展", "继续深耕", "蓬勃发展", "蒸蒸日上", "稳步推进", "突飞猛进"]


def d_ok(date, acc):
    if not isinstance(date, str) or not DATE_RE.match(date):
        return False
    if acc == "year" and date[5:] != "01-01":
        return False
    if acc == "month" and date[8:] != "01":
        return False
    try:
        import datetime
        datetime.date.fromisoformat(date)
        return True
    except ValueError:
        return False


def main(path):
    try:
        items = json.load(open(path, encoding="utf-8"))
    except Exception as exc:
        print(f"✗ JSON 解析失败: {exc}")
        return 1
    if not isinstance(items, list) or not items:
        print("✗ 顶层必须是非空数组")
        return 1
    errs, seen = [], set()
    for i, e in enumerate(items):
        w = f"[{i}]{e.get('name', '?')}"
        for k in FIELDS:
            if k not in e:
                errs.append(f"{w} 缺字段 {k}")
        eid = e.get("id", "")
        if not ID_RE.match(eid or ""):
            errs.append(f"{w} id 不合法: {eid!r}")
        elif eid in seen:
            errs.append(f"{w} id 重复: {eid}")
        seen.add(eid)
        if e.get("type") not in TYPES:
            errs.append(f"{w} type 非法: {e.get('type')!r}")
        if e.get("region") not in {"cn", "world"}:
            errs.append(f"{w} region 非法")
        if e.get("status") not in STATUS:
            errs.append(f"{w} status 非法: {e.get('status')!r}")
        facc = e.get("founded_accuracy")
        if facc not in {"exact", "month", "year"}:
            errs.append(f"{w} founded_accuracy 非法: {facc!r}")
        elif not d_ok(e.get("founded", ""), facc):
            errs.append(f"{w} founded 与精度不符或非法: {e.get('founded')!r} ({facc})")
        dis = e.get("dissolved")
        if dis not in (None, "") and not DATE_RE.match(str(dis)):
            errs.append(f"{w} dissolved 非法: {dis!r}")
        hl = e.get("headline", "")
        if not hl.strip() or len(hl) > 20:
            errs.append(f"{w} headline 空或超20字: {hl!r}")
        s = e.get("summary_30s", "")
        if not (60 <= len(s) <= 220):
            errs.append(f"{w} summary_30s {len(s)}字（须60-220，建议75-90）")
        tl = e.get("timeline", [])
        if not (8 <= len(tl) <= 20):
            errs.append(f"{w} timeline {len(tl)}条（须8-20）")
        prev = ""
        for j, t in enumerate(tl):
            tw = f"{w}·tl[{j}]"
            if t.get("acc") not in {"exact", "month", "year"}:
                errs.append(f"{tw} acc 非法")
            if not d_ok(t.get("date", ""), t.get("acc", "")):
                errs.append(f"{tw} date 非法: {t.get('date')!r} ({t.get('acc')})")
            if prev and str(t.get("date", "")) < prev:
                errs.append(f"{tw} 时间未升序")
            prev = str(t.get("date", ""))
            txt = str(t.get("text", ""))
            if len(txt) < 15:
                errs.append(f"{tw} text <15字")
            if any(x in txt for x in EMPTY_WORDS):
                errs.append(f"{tw} 空话命中: {txt[:30]}")
        ms = e.get("milestones", [])
        if not (3 <= len(ms) <= 6):
            errs.append(f"{w} milestones {len(ms)}条（须3-6）")
        for m in ms:
            if len(str(m)) > 60:
                errs.append(f"{w} milestones 单条超60字")
        legacy = e.get("legacy", "")
        if not legacy.strip() or len(legacy) > 140:
            errs.append(f"{w} legacy 空或超140字")
        ctz = e.get("controversies", [])
        if len(ctz) > 2:
            errs.append(f"{w} controversies 超2条")
        for c in ctz:
            if len(str(c)) > 80:
                errs.append(f"{w} controversies 单条超80字")
        blob = e.get("name", "") + e.get("headline", "") + e.get("summary_30s", "") + \
            "".join(t.get("text", "") for t in tl) + legacy + "".join(ctz)
        for bad in BLOCK:
            if bad in blob:
                errs.append(f"{w} 红线命中领导人姓名「{bad}」→ 整条作废")
                break
        srcs = e.get("sources", [])
        if len(srcs) < 3:
            errs.append(f"{w} sources <3条")
        domains = set()
        for sr in srcs:
            u = str(sr.get("url", ""))
            if not u.startswith("http"):
                errs.append(f"{w} source url 非 http: {u[:40]}")
            else:
                domains.add(re.sub(r"^https?://([^/]+).*", r"\1", u))
        if len(domains) < 2:
            errs.append(f"{w} sources 域名 <2 种")
        tags = e.get("tags", [])
        if not (3 <= len(tags) <= 6):
            errs.append(f"{w} tags {len(tags)}个（须3-6）")
    if errs:
        print(f"✗ {len(errs)} 个错误:")
        for x in errs:
            print("  -", x)
        return 1
    print(f"✓ {len(items)} 实体全部通过: " + "、".join(e["name"] for e in items))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
