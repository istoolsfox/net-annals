# -*- coding: utf-8 -*-
"""把已上线的增补档案导出为「每对象一个 JSON」，供 build.py 回灌源稿使用。

用法：
  python export_enriched.py <site目录> <输出目录>
示例：
  python scripts/export_enriched.py ../site ./源稿回灌

产出：
  <输出目录>/persons/<id>.json   完整人物记录（含 bio/timeline/legacy 等全部字段）
  <输出目录>/entities/<id>.json  完整世家记录
  <输出目录>/_manifest.json      导出清单（id/名字/字段指纹），供核对
"""
import json, os, sys, hashlib, io

site = sys.argv[1] if len(sys.argv) > 1 else '../site'
out = sys.argv[2] if len(sys.argv) > 2 else './源稿回灌'

def load(p):
    with open(p, encoding='utf-8') as f:
        return json.load(f)

manifest = {}
for kind, key in (('persons', 'persons'), ('entities', 'entities')):
    data = load(os.path.join(site, kind, 'data.json'))
    d = os.path.join(out, kind)
    os.makedirs(d, exist_ok=True)
    for r in data[key]:
        fp = os.path.join(d, r['id'] + '.json')
        with open(fp, 'w', encoding='utf-8', newline='') as f:
            json.dump(r, f, ensure_ascii=False, indent=1)
        manifest.setdefault(kind, {})[r['id']] = {
            'name': r.get('name'),
            'file': fp.replace('\\', '/'),
            'sha1': hashlib.sha1(io.open(fp, 'rb').read()).hexdigest()[:12],
            'timeline_n': len(r.get('timeline') or []),
        }

mp = os.path.join(out, '_manifest.json')
with open(mp, 'w', encoding='utf-8', newline='') as f:
    json.dump(manifest, f, ensure_ascii=False, indent=1)
print('导出完成:', {k: len(v) for k, v in manifest.items()}, '->', mp)
