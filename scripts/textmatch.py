#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""标题重叠统一验证器——改题/验收脚本必须 import 本模块，禁止自建清洗规则。

背景（2026-11-04 续99轮教训）：dedup.py 与 add_events.py 的同日判定使用
「原始标题字符集（含标点，不清洗）重叠 > 0.6」；改题脚本若自建 clean 规则
（去标点/去括号），算出的重叠会系统性偏低，导致条目入库后被 dedup 误删。
凡写改题/查重/验收脚本，用本模块的 title_overlap 与 load_title_index。

用法:
    from textmatch import title_overlap, load_title_index
    idx = load_title_index()               # {date: [title, ...]}（仅 data/events 主层）
    ov = title_overlap(new_title, rival)   # 与 dedup 完全一致的判定
"""
import glob
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EV = ROOT / "data" / "events"
THRESHOLD = 0.6          # dedup.py 同日删除阈值（> THRESHOLD 删）


def title_overlap(a: str, b: str) -> float:
    """与 dedup.py/add_events.py 完全一致：原始字符串字符集交集 / 较短侧字符集大小。"""
    A, B = set(a), set(b)
    if not A or not B:
        return 0.0
    return len(A & B) / min(len(A), len(B))


def is_clash(title: str, day: str, index: dict, threshold: float = THRESHOLD) -> bool:
    """new_title 与库内同日任一条目重叠 > threshold 即 True（会 dedup 被删）。"""
    return any(title_overlap(title, t) > threshold for t in index.get(day, []))


def load_title_index(include_parts: bool = False) -> dict:
    """date -> [title]。include_parts=True 时并入 .parts/auto_geo_city_*.json（批间验收用）。"""
    index: dict[str, list] = {}
    for f in glob.glob(str(EV / "*.json")):
        if "/." in f or ".parts" in f:
            continue
        for e in json.load(open(f, encoding="utf-8")):
            index.setdefault(e["date"][:10], []).append(e["title"])
    if include_parts:
        for f in glob.glob(str(EV / ".parts" / "auto_geo_city_*.json")):
            for e in json.load(open(f, encoding="utf-8")):
                index.setdefault(e["date"][:10], []).append(e["title"])
    return index


def max_clash(title: str, day: str, index: dict) -> tuple[float, str]:
    """返回 (最大重叠, 对手标题)。改题候选挑选用。"""
    best, rival = 0.0, ""
    for t in index.get(day, []):
        mo = title_overlap(title, t)
        if mo > best:
            best, rival = mo, t
    return best, rival
