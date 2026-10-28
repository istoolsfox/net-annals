#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""新增条目脚手架：生成"一条一文件"草稿，照模板填字段即可提 PR。

用法:
  python3 scripts/new_entry.py --date 1994-04-20 --title "标题" \
      --slug china-internet --layer tech --category tech --region cn

生成: data/events/1994-04-20-tech-china-internet.json（单条数组，与批次文件同构）
下一步: 填 summary_30s / detail / sources（占位符不改会被校验器拦下）
        → python3 scripts/validate_events.py <生成的文件>
        → git 提交并开 PR（站长审核合并）
"""
import argparse
import json
import os
import sys
from datetime import date

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, 'scripts')
from api.config import CATEGORIES, LAYER_NAMES, REGIONS  # noqa: E402

EV = 'data/events'
# 占位符全文——validate_events.py 会 import 这两个常量做拦截检测，改动必须两边同步
PLACEHOLDER_SUMMARY = '30秒摘要：谁、何时何地、做了什么、为什么重要。40-160字，写事实不堆形容词。'
PLACEHOLDER_DETAIL = '正文：背景、经过、关键数字、后续发展。'


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--date', required=True, help='YYYY-MM-DD（月/年精度请用该月/年 01 日）')
    p.add_argument('--title', required=True, help='≤48字，含关键实体名')
    p.add_argument('--slug', default='event', help='id 语义尾段，小写字母数字连字符')
    p.add_argument('--layer', default='', help=f'领域层码：{", ".join(k for k in LAYER_NAMES if k)}')
    p.add_argument('--category', default='tech', choices=sorted(CATEGORIES))
    p.add_argument('--region', default='cn', choices=sorted(REGIONS))
    p.add_argument('--force', action='store_true', help='覆盖已存在的同名文件')
    a = p.parse_args()

    try:
        y, m, d = map(int, a.date.split('-'))
        date(y, m, d)
    except (ValueError, TypeError):
        print('✗ --date 必须是真实存在的 YYYY-MM-DD')
        return 2
    if a.layer and a.layer not in LAYER_NAMES:
        print(f'✗ --layer 必须是 {", ".join(k for k in LAYER_NAMES if k)} 之一（主时间线用空串或省略）')
        return 2
    if not (a.slug.isascii() and a.slug.replace('-', '').isalnum()) or ' ' in a.slug:
        print('✗ --slug 只能是小写字母/数字/连字符')
        return 2
    if a.layer and a.slug.lower().startswith(a.layer + '-'):
        # 层码会拼进文件名，slug 再以层码开头会出现双重层码且易被误归层
        a.slug = a.slug[len(a.layer) + 1:]
        print(f'  ↺ slug 以层码开头，已自动剥离 → {a.slug}')

    fname = a.date + (f'-{a.layer}' if a.layer else '') + f'-{a.slug.lower()}.json'
    path = os.path.join(EV, fname)
    if os.path.exists(path) and not a.force:
        print(f'✗ {path} 已存在（改名或 --force）')
        return 2

    event = {
        'id': f'{a.date}-{a.slug.lower()}',
        'date': a.date,
        'title': a.title,
        'category': a.category,
        'region': a.region,
        'milestone': False,
        'date_confidence': 'single-source',
        'date_accuracy': 'exact',
        'summary_30s': PLACEHOLDER_SUMMARY,
        'detail': PLACEHOLDER_DETAIL,
        'impact': '',
        'aftermath': '',
        'tags': [],
        'sources': [{'url': 'https://（改成真实来源链接）', 'title': '来源标题'}],
    }
    os.makedirs(EV, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump([event], f, ensure_ascii=False, indent=1)
        f.write('\n')

    print(f'✓ 已生成 {path}')
    print('  下一步：')
    print('  1. 填好 summary_30s / detail / tags / sources（占位符不改会被校验器拦下）')
    print(f'  2. python3 scripts/validate_events.py {path}')
    print('  3. git add <该文件> && git commit && 推送分支开 PR（站长审核合并）')
    return 0


if __name__ == '__main__':
    sys.exit(main())
