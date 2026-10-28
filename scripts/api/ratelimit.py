#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""内存突发限流 + 无效 key 探测计数。
纯逻辑模块：不 import web 框架，超限抛 RateLimited，由 gate 翻译成 HTTP 429。
单进程假设：usage 与限流都在单 uvicorn worker 进程内（systemd 配置如此）。"""
import threading
import time
from collections import defaultdict, deque

from . import config


class RateLimited(Exception):
    """超限信号。retry_after 秒；message 面向调用方。"""

    def __init__(self, message, retry_after=None):
        super().__init__(message)
        self.message = message
        self.retry_after = retry_after


_hits = defaultdict(deque)      # subject('ip:x'/'key:y') → 最近命中时间戳
_probes = defaultdict(deque)    # ip → 最近无效 key 探测时间戳
_rl_lock = threading.Lock()
_last_sweep = time.time()


def _sweep(now):
    """低频清扫空/过期桶，防海量假 IP 撑爆内存。"""
    global _last_sweep
    with _rl_lock:
        if now - _last_sweep < 300 or len(_hits) + len(_probes) < 2048:
            return
        for d in (_hits, _probes):
            stale = [k for k, q in d.items() if not q or q[-1] < now - 3600]
            for k in stale:
                d.pop(k, None)
        _last_sweep = now


def burst(subject, limit):
    """滑动窗口限流：60 秒内第 limit+1 次抛 RateLimited。"""
    now = time.time()
    _sweep(now)
    with _rl_lock:
        q = _hits[subject]
        while q and q[0] < now - 60:
            q.popleft()
        if len(q) >= limit:
            raise RateLimited('rate limit exceeded, retry later', retry_after=60)
        q.append(now)


def record_probe(ip):
    """无效 key 探测 +1；达到 config.PROBE_LIMIT 返回 True（由调用方执行封禁）。"""
    now = time.time()
    with _rl_lock:
        q = _probes[ip]
        while q and q[0] < now - config.PROBE_WINDOW:
            q.popleft()
        q.append(now)
        hot = len(q) >= config.PROBE_LIMIT
        if hot:
            _probes.pop(ip, None)
    return hot
