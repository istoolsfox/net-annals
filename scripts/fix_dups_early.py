# -*- coding: utf-8 -*-
"""清除早期年段重复条目 + 修正 EU 成立日期（马约生效日为1993-11-01）"""
import json

REMOVE = [
    "1994-05-06-channel-tunnel",        # railways 层，主层 channel-tunnel-open 更全
    "1994-05-06-channel-tunnel-opens",  # science 层
    "1994-07-17-brazil-world-cup-fourth-title",  # sports 层，主层 brazil-worldcup 更全
    "1994-10-10-doom-2",                # games2 层，games 层 doom-ii 日期正确(09-30)
    "1993-01-01-grain-coupons-abolished",  # 主层内部，保留 04-01 exact 版
    "1994-01-01-tong-zhuo-de-ni",       # music 层，保留 05-01 专辑发行版
]

removed = 0
import glob
for f in glob.glob('data/events/*.json'):
    if '.parts' in f:
        continue
    d = json.load(open(f))
    out = [e for e in d if e['id'] not in REMOVE]
    if len(out) != len(d):
        removed += len(d) - len(out)
        json.dump(out, open(f, 'w'), ensure_ascii=False, indent=0)
        print(f"{f}: -{len(d)-len(out)}")

# EU 修正：1993-11-01 生效（原误标 1992-11-01）
f = 'data/events/1986-1995.json'
d = json.load(open(f))
for e in d:
    if e['id'] == '1992-11-01-eu-founded':
        e['id'] = '1993-11-01-eu-founded'
        e['date'] = '1993-11-01'
        e['detail'] = e['detail'].replace(
            '1992年11月1日，《马斯特里赫特条约》正式生效',
            '1993年11月1日，《马斯特里赫特条约》正式生效'
        )
        print("eu-founded -> 1993-11-01 修正完成")
json.dump(d, open(f, 'w'), ensure_ascii=False, indent=0)
print(f"共移除 {removed} 条")
