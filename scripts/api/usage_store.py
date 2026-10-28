#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""usage.db：配额/封禁/自助领取计数（SQLite 持久化）。
单例长连接 + WAL + 全局锁串行写；所有函数可在工作线程中调用（gate 经 run_in_threadpool）。"""
import logging
import os
import sqlite3
import threading
import time

from . import config

_lock = threading.Lock()
_conn = None


def conn():
    """进程内单例 rw 连接。row_factory 必设：不设 fetchone 返回元组，字典取键会崩（踩过的坑）。"""
    global _conn
    if _conn is None:
        try:
            os.makedirs(os.path.dirname(config.USAGE_DB), exist_ok=True)
        except OSError:
            pass   # 目录建不出来时让 sqlite3.connect 抛 OperationalError，走调用方 fail-open
        c = sqlite3.connect(config.USAGE_DB, timeout=5, check_same_thread=False)
        c.row_factory = sqlite3.Row
        c.execute('PRAGMA journal_mode=WAL')
        c.execute('PRAGMA synchronous=NORMAL')
        c.executescript("""
        CREATE TABLE IF NOT EXISTS key_usage(key_id TEXT, day TEXT, count INTEGER, PRIMARY KEY(key_id, day));
        CREATE TABLE IF NOT EXISTS ip_usage(day TEXT, ip TEXT, count INTEGER, PRIMARY KEY(day, ip));
        CREATE TABLE IF NOT EXISTS reg_daily(day TEXT, ip TEXT, count INTEGER, PRIMARY KEY(day, ip));
        CREATE TABLE IF NOT EXISTS bans(ip TEXT PRIMARY KEY, until INTEGER, reason TEXT);
        """)
        c.commit()
        _conn = c
    return _conn


def bump(table, col, day, ident):
    """当日计数 +1，返回当日已用次数；配额库故障返回 None（fail-open，调用方跳过配额判定）。
    day 由调用方传入（防跨午夜 INSERT/SELECT 错位）。"""
    try:
        with _lock:
            c = conn()
            c.execute(
                f'INSERT INTO {table}(day,{col},count) VALUES(?,?,1) '
                f'ON CONFLICT(day,{col}) DO UPDATE SET count=count+1', (day, ident))
            row = c.execute(f'SELECT count FROM {table} WHERE day=? AND {col}=?',
                            (day, ident)).fetchone()
            c.commit()
            return row[0]
    except sqlite3.Error as e:
        logging.getLogger('netannals-api').warning('%s bump failed (fail-open): %s', table, e)
        return None


def peek(table, col, day, ident):
    """只读查当日已用次数（不写库）；故障返回 None。配额判定先 peek 再 bump，
    被拒请求零写入（防 SQLite 写放大攻击）。"""
    try:
        with _lock:
            row = conn().execute(f'SELECT count FROM {table} WHERE day=? AND {col}=?',
                                 (day, ident)).fetchone()
            return row[0] if row else 0
    except sqlite3.Error as e:
        logging.getLogger('netannals-api').warning('%s peek failed (fail-open): %s', table, e)
        return None


def banned_since(ip):
    """封禁查询：fail-open——usage.db 故障返回 None 放行并告警，绝不因配额库拖死全站。
    返回 None=未封禁；否则 (until_epoch, reason)。"""
    import logging
    try:
        with _lock:
            r = conn().execute('SELECT until, reason FROM bans WHERE ip=?', (ip,)).fetchone()
    except sqlite3.Error as e:
        logging.getLogger('netannals-api').warning('bans check failed (fail-open): %s', e)
        return None
    if r and r['until'] > time.time():
        return (r['until'], r['reason'])
    if r:
        try:
            with _lock:
                conn().execute('DELETE FROM bans WHERE ip=?', (ip,))
                conn().commit()
        except sqlite3.Error:
            pass
    return None


def ban(ip, hours, reason):
    with _lock:
        c = conn()
        c.execute('INSERT INTO bans VALUES(?,?,?) '
                  'ON CONFLICT(ip) DO UPDATE SET until=excluded.until, reason=excluded.reason',
                  (ip, time.time() + hours * 3600, reason))
        c.commit()


def prune(days=45):
    """保留策略：清 N 天前计数与过期封禁（管线每周调用一次）。"""
    with _lock:
        c = conn()
        for t in ('key_usage', 'ip_usage', 'reg_daily'):
            c.execute(f"DELETE FROM {t} WHERE day < date('now', ?)", (f'-{days} day',))
        c.execute('DELETE FROM bans WHERE until < ?', (time.time(),))
        c.commit()


def day_key():
    return time.strftime('%Y-%m-%d')


def seconds_to_midnight():
    import datetime
    now = datetime.datetime.now()
    return (86400 - (now.hour * 3600 + now.minute * 60 + now.second)) + 60
