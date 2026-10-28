#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""密钥库：只存 sha256 摘要，明文只在签发时返回一次。
线程安全：热加载缓存（mtime 失效）+ flock 原子写（与 api_keys.py CLI 共用同一把锁）。"""
import datetime
import fcntl
import hashlib
import hmac
import json
import logging
import os
import secrets
import time

from . import config

log = logging.getLogger('netannals-api')

_cache = {'mtime': 0, 'map': {}}


def load(path=None):
    """读密钥文件（带 mtime 缓存）；文件缺失初始化为空库；解析失败沿用旧缓存。"""
    path = path or config.KEY_FILE
    try:
        mt = os.path.getmtime(path)
        if mt != _cache['mtime']:
            with open(path, encoding='utf-8') as f:
                d = json.load(f)
            _cache['map'] = {k['key_sha256']: k for k in d.get('keys', [])}
            _cache['mtime'] = mt
    except FileNotFoundError:
        _cache['map'] = {}
        _cache['mtime'] = 0
    except Exception as e:
        log.warning('KEY_FILE 解析失败，沿用旧缓存（%s）', e)
    return _cache['map']


def find(raw, path=None):
    """明文 key → 条目。摘要字典查找 + compare_digest 复核（恒时比较）。"""
    digest = hashlib.sha256(raw.encode()).hexdigest()
    k = load(path).get(digest)
    if k and hmac.compare_digest(k['key_sha256'], digest):
        return k
    return None


def _save_locked(d, path):
    """调用方已持锁时的原子写：O_EXCL 独占建 tmp（0600，防符号链接预置）+ fsync + os.replace。"""
    tmp = path + '.tmp'
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_TRUNC, 0o600)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            try:
                os.unlink(tmp)   # 写失败不留含摘要的残留
            except OSError:
                pass


def _ensure_dirs(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    os.makedirs(os.path.dirname(config.KEY_LOCK), exist_ok=True)


def issue(name, role, quota=None, contact='', path=None):
    """签发一把密钥，返回明文（仅此一次）。名称已存在抛 ValueError。"""
    path = path or config.KEY_FILE
    if role == 'public':                      # 公开自助领取层：固定 ro+默认配额
        role, quota = 'ro', quota or config.DEFAULT_RO_QUOTA
    if role not in ('ro', 'admin'):
        raise ValueError('role must be ro|admin')
    _ensure_dirs(path)
    lock_fd = os.open(config.KEY_LOCK, os.O_RDWR | os.O_CREAT)
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        try:
            with open(path, encoding='utf-8') as f:
                d = json.load(f)
        except FileNotFoundError:
            d = {'keys': []}
        while any(k['id'] == name for k in d['keys']):
            name += secrets.token_hex(1)
        raw = 'NA-' + secrets.token_hex(24)
        d['keys'].append({'id': name, 'key_sha256': hashlib.sha256(raw.encode()).hexdigest(),
                          'role': role, 'daily_quota': quota, 'contact': contact,
                          'created': datetime.datetime.now().astimezone().isoformat(timespec='seconds')})
        _save_locked(d, path)
    finally:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        os.close(lock_fd)
    return raw


def revoke(name, path=None):
    """吊销名称匹配的密钥，返回吊销数量。"""
    path = path or config.KEY_FILE
    _ensure_dirs(path)
    lock_fd = os.open(config.KEY_LOCK, os.O_RDWR | os.O_CREAT)
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        try:
            with open(path, encoding='utf-8') as f:
                d = json.load(f)
        except FileNotFoundError:
            d = {'keys': []}
        n = len(d['keys'])
        d['keys'] = [k for k in d['keys'] if k['id'] != name]
        _save_locked(d, path)
        return n - len(d['keys'])
    finally:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        os.close(lock_fd)


def list_keys(path=None):
    try:
        with open(path or config.KEY_FILE, encoding='utf-8') as f:
            return json.load(f).get('keys', [])
    except FileNotFoundError:
        return []


def new_key_id():
    return f"public-{time.strftime('%Y%m%d')}-{secrets.token_hex(2)}"
