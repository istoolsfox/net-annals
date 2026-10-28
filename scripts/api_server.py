#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""兼容入口：systemd 单元 uvicorn scripts.api_server:app 不变。
实现在 scripts/api/ 包（见包 __init__ 的模块图）。
本文件只做路径装配，不承载业务逻辑。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.app import app  # noqa: E402,F401
