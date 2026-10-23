#!/usr/bin/env python3
"""世家来源 URL 全量体检：并发验证 data/entities/*.json 的 sources URL。
存活判定：HTTP 200/206/403（百度百科反爬惯例）/405/429/999 视为存活；超时/5xx/404/3xx环 视为可疑。
用法：python3 scripts/check_entity_urls.py [--fix-report] → 控制台报告 + data/entities/.urlcheck.json"""
import concurrent.futures
import glob
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENT = os.path.join(ROOT, "data", "entities")
ALIVE = {200, 201, 206, 226, 401, 403, 405, 406, 429, 999}  # 403=baike反爬 401=Reuters等bot墙 999=部分站点反爬
TIMEOUT = 15


def check_url(url):
    """HEAD 失败回退 GET；返回 (url, code或'ERR', err简述)"""
    for method in ("HEAD", "GET"):
        try:
            r = subprocess.run(
                ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "-L", "--max-time", str(TIMEOUT),
                 "-A", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)", "-X", method, url],
                capture_output=True, text=True, timeout=TIMEOUT + 5)
            code = r.stdout.strip()
            if code.isdigit() and int(code) in ALIVE:
                return url, int(code), ""
            if method == "GET":
                return url, (int(code) if code.isdigit() else 0), r.stderr[:80]
        except Exception as exc:
            if method == "GET":
                return url, 0, str(exc)[:80]
    return url, 0, "unreachable"


def main():
    urls = []
    owner = {}
    for f in sorted(glob.glob(os.path.join(ENT, "*.json"))):
        for e in json.load(open(f, encoding="utf-8")):
            for s in e.get("sources", []):
                u = s.get("url", "")
                if u.startswith("http"):
                    urls.append(u)
                    owner[u] = e.get("name", "?")
    urls = sorted(set(urls))
    print(f"共 {len(urls)} 个待验 URL（{ALIVE - {200,201,206,226}} 视为反爬存活）…")

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
        for res in ex.map(check_url, urls):
            results.append(res)

    dead = [(u, c, err) for u, c, err in results if not (isinstance(c, int) and c in ALIVE)]
    ok = len(results) - len(dead)
    print(f"\n✓ 存活 {ok} / {len(results)}")
    if dead:
        print(f"✗ 可疑/死亡 {len(dead)} 个：")
        for u, c, err in dead:
            print(f"  [{c}] {owner.get(u,'?')} {u[:80]}  {err[:40]}")
    out = os.path.join(ENT, ".urlcheck.json")
    json.dump({"checked": len(results), "dead": [{"url": u, "code": c, "err": err, "entity": owner.get(u, "")} for u, c, err in dead]},
              open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n报告 → {os.path.relpath(out, ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
