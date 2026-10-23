#!/usr/bin/env python3
"""类传（群像列传）校验器：python3 scripts/validate_group.py data/persons/groups/g_xxx.json
按 PERSONS_SPEC.md 附录B 强制校验，全部通过退出码0。"""
import json, re, sys

ID_RE = re.compile(r"^l-[a-z0-9-]+$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
BLOCK = ["习近平", "李克强", "李强", "胡锦涛", "温家宝", "江泽民", "毛泽东", "邓小平", "周恩来",
         "朱镕基", "薄熙来", "周永康", "孙政才", "令计划", "彭丽媛", "栗战书", "汪洋", "王沪宁",
         "赵乐际", "韩正", "蔡奇", "丁薛祥", "李鹏", "华国锋", "林彪", "四人帮", "刘少奇",
         "特朗普", "拜登", "普京", "金正恩", "泽连斯基", "安倍", "莫迪", "埃尔多安"]


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
        for k in ["id", "name", "era", "summary_30s", "members", "legacy", "sources", "tags"]:
            if k not in e:
                errs.append(f"{w} 缺字段 {k}")
        gid = e.get("id", "")
        if not ID_RE.match(gid or ""):
            errs.append(f"{w} id 必须以 l- 开头且合法: {gid!r}")
        elif gid in seen:
            errs.append(f"{w} id 重复: {gid}")
        seen.add(gid)
        if not str(e.get("era", "")).strip():
            errs.append(f"{w} era 空")
        s = e.get("summary_30s", "")
        if not (60 <= len(s) <= 220):
            errs.append(f"{w} summary_30s {len(s)}字（须60-220）")
        members = e.get("members", [])
        if not (5 <= len(members) <= 9):
            errs.append(f"{w} members {len(members)}人（须5-9）")
        for j, m in enumerate(members):
            mw = f"{w}·m[{j}]{m.get('name', '?')}"
            if not str(m.get("name", "")).strip():
                errs.append(f"{mw} name 空")
            hl = str(m.get("headline", ""))
            if not hl.strip() or len(hl) > 20:
                errs.append(f"{mw} headline 空或超20字")
            txt = str(m.get("text", ""))
            if not (40 <= len(txt) <= 160):
                errs.append(f"{mw} text {len(txt)}字（须40-160）")
            elif not re.search(r"\d", txt):
                errs.append(f"{mw} text 无数字（须事件+数字或机制）")
        legacy = e.get("legacy", "")
        if not legacy.strip() or len(legacy) > 140:
            errs.append(f"{w} legacy 空或超140字")
        blob = json.dumps(e, ensure_ascii=False)
        for bad in BLOCK:
            if bad in blob:
                errs.append(f"{w} 红线命中领导人姓名「{bad}」→ 整篇作废")
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
    print(f"✓ {len(items)} 篇类传全部通过: " + "、".join(e["name"] for e in items))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
