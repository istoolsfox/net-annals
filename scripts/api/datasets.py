#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""非 events 数据集注册表——本 API 的扩展点。
新增一个可查询数据集分两步：
  1. build_api_db.py 的 EXTRA_SOURCES 加一行（源文件 → items 表）
  2. 本文件 DATASETS 加一项（路由/过滤白名单自动生成）
items 表固定列：dataset, id, name, kind, region, date, year, search, data(完整 JSON)。
filters 只允许登记过的列，全部走参数化查询。"""

from . import config

# filters: 查询参数名 → items 表列名。value 校验：region 枚举 / year 整数 / 其余 RE_FREEWORD
DATASETS = {
    'persons': {
        'label': '人物',
        'filters': {'field': 'kind', 'region': 'region', 'year': 'year'},
    },
    'entities': {
        'label': '实体（公司/组织/产品）',
        'filters': {'type': 'kind', 'region': 'region', 'year': 'year'},
    },
    'works': {
        'label': '作品',
        'filters': {'type': 'kind', 'region': 'region', 'year': 'year'},
    },
    'groups': {
        'label': '世家志（人物群像）',
        'filters': {},
    },
}

DATASET_IDS = tuple(DATASETS)


def is_dataset(name):
    return name in DATASETS


def validate_filter(value, column):
    """过滤值白名单校验，返回规范化值或 None（表示丢弃该过滤条件→400 由路由决定）。"""
    if column == 'region':
        return value if value in config.REGIONS else None
    if column == 'year':
        try:
            y = int(value)
        except (TypeError, ValueError):
            return None
        return y if 1400 <= y <= 2100 else None
    if not isinstance(value, str) or not config.RE_FREEWORD.fullmatch(value):
        return None
    return value
