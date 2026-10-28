#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""应用装配：FastAPI 实例、CORS、准入中间件、统一错误契约、路由注册。
启动: uvicorn scripts.api_server:app --host 127.0.0.1 --port 8400（单 worker：
usage 连接与限流均为进程内状态，多 worker 会破坏配额一致性——systemd 配置如此）。"""
import logging
import os

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import config, datasets, store
from .gate import gate
from .routes import register_routes

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
os.chdir(config.PROJECT_ROOT)   # 相对路径锚点（systemd WorkingDirectory 之外的兜底）


def create_app() -> FastAPI:
    # 数据集名不得撞保留路径（撞了会与 gate 分类/路由注册顺序纠缠，出难排查的怪行为）
    reserved = {'meta', 'events', 'year', 'search', 'keys', 'health'}
    clash = set(datasets.DATASET_IDS) & reserved
    assert not clash, f'dataset id 与保留路径冲突: {clash}'
    app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)   # 文档面不暴露
    app.add_middleware(CORSMiddleware, allow_origins=['*'],
                       allow_methods=['GET', 'HEAD', 'POST'],
                       allow_headers=['X-API-Key', 'Content-Type'])

    @app.middleware('http')
    async def _gate(request, call_next):
        return await gate(request, call_next)

    @app.exception_handler(StarletteHTTPException)
    async def _http_exc(request, exc):
        return JSONResponse(status_code=exc.status_code, content={'error': exc.detail},
                            headers=getattr(exc, 'headers', None) or {})

    @app.exception_handler(RequestValidationError)
    async def _validation_exc(request, exc):
        return JSONResponse(status_code=400, content={'error': 'invalid parameters'})

    @app.exception_handler(store.StoreUnavailable)
    async def _store_unavailable(request, exc):
        return JSONResponse(status_code=503, content={'error': 'database not ready'})

    @app.exception_handler(store.NotFound)
    async def _not_found(request, exc):
        return JSONResponse(status_code=404, content={'error': 'not found'})

    @app.exception_handler(Exception)
    async def _unhandled(request, exc):
        # repr() 防路径中的控制字符伪造日志行
        logging.getLogger('netannals-api').exception(
            'unhandled error on %s %s', request.method, repr(request.url.path)[:200])
        return JSONResponse(status_code=500, content={'error': 'internal error'})

    register_routes(app)
    return app


app = create_app()
