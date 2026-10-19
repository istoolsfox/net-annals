#!/usr/bin/env python3
"""来源 URL 存活检查：HEAD 请求全库来源链接，报告死链。
判定：2xx/3xx/405/406/429/403 → 存活（403/429 视为反爬拦截）；404/410/5xx/超时 → 死链候选。
用法：python3 scripts/check_urls.py [--limit N]
"""
import json
import sys
import urllib.request
import urllib.parse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EV = ROOT / "data" / "events"
ALIVE_OK = {200, 201, 202, 203, 204, 206, 301, 302, 303, 307, 308, 401, 403, 405, 406, 418, 429, 567}


def check(url: str) -> tuple[str, int]:
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "Mozilla/5.0 (Macintosh) net-annals-linkcheck/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            return url, r.status
    except Exception as exc:
        code = getattr(exc, "code", None)
        if code is not None:
            return url, code
        return url, -1  # 超时/连接错误


def main() -> int:
    limit = 0
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])
    urls = set()
    url_events: dict[str, list] = {}
    for f in sorted(EV.glob("*.json")):
        for e in json.loads(f.read_text(encoding="utf-8")):
            for s in e.get("sources", []):
                u = s.get("url", "")
                if u.startswith("http"):
                    uq = urllib.parse.quote(u, safe=":/#?=&%+,;@()!~'*")
                    urls.add(uq)
                    url_events.setdefault(uq, []).append(e["id"])
    if limit:
        urls = set(sorted(urls)[:limit])
    print(f"待检查唯一 URL：{len(urls)}")
    results = {}
    with ThreadPoolExecutor(max_workers=16) as pool:
        for url, status in pool.map(check, urls):
            results[url] = status
    dead = {u: s for u, s in results.items() if s not in ALIVE_OK}
    stat = Counter(results.values())
    print(f"状态分布：{dict(sorted(stat.items()))}")
    if dead:
        print(f"\n✗ 死链候选 {len(dead)} 个：")
        for u, s in sorted(dead.items(), key=lambda x: x[1]):
            evs = url_events[u][:2]
            print(f"  [{s}] {u[:90]}  ← {', '.join(evs)}")
    else:
        print("✓ 全部存活")
    return 1 if dead else 0


if __name__ == "__main__":
    sys.exit(main())
