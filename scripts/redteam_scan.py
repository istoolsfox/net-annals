#!/usr/bin/env python3
"""红队扫描 1：数据投毒（XSS 载荷检测）+ 转义审计辅助。"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAYLOADS = [
    (r'<script', 'script标签'), (r'onerror\s*=', 'onerror事件'), (r'onload\s*=', 'onload事件'),
    (r'javascript:', 'javascript协议'), (r'<img', 'img标签'), (r'<svg', 'svg标签'),
    (r'<iframe', 'iframe标签'), (r'document\.cookie', 'cookie窃取'), (r'eval\(', 'eval调用'),
    (r'expression\s*\(', 'CSS表达式'), (r'data:text/html', 'data协议'),
]
FIELDS = ['title', 'summary_30s', 'detail', 'impact', 'aftermath', 'tags']

def main():
    hits = []
    files = sorted((ROOT / 'data' / 'events').glob('*.json'))
    for f in files:
        try:
            d = json.load(open(f))
        except Exception as exc:
            hits.append((f.name, 'JSON解析失败', str(exc)[:60]))
            continue
        for e in d:
            for fld in FIELDS:
                v = e.get(fld)
                vals = v if isinstance(v, list) else [v]
                for v2 in vals:
                    if not isinstance(v2, str):
                        continue
                    for pat, name in PAYLOADS:
                        if re.search(pat, v2, re.I):
                            hits.append((f.name, e['id'], f'{fld} 含 {name}: {v2[:40]}'))
            for s in e.get('sources', []):
                u = str(s.get('url', ''))
                if not re.match(r'^https?://', u):
                    hits.append((f.name, e['id'], f'非http协议URL: {u[:60]}'))

    print(f"=== 红队1：数据投毒扫描（{len(files)} 个文件）===")
    if hits:
        for h in hits[:25]:
            print('  !!', h)
        print(f'共 {len(hits)} 处可疑')
        return 1
    print('  ✓ 未发现 XSS 载荷或协议逃逸')
    return 0

if __name__ == '__main__':
    sys.exit(main())
