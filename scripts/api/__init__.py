# -*- coding: utf-8 -*-
"""net-annals 公共 API 包（只读）。

模块划分（高内聚低耦合，依赖单向无环）：
  config.py     全局配置/枚举/正则（纯 stdlib，供服务端+构建+校验共用）
  ratelimit.py  内存突发限流与无效 key 探测
  usage_store.py usage.db（配额/封禁/注册计数，SQLite 单例）
  keys_store.py  密钥库（sha256 摘要、原子写、自助签发）
  datasets.py    非 events 数据集注册表（persons/entities/works/groups）
  store.py       只读数据访问（events + 通用 items 查询）
  gate.py        准入中间件（封禁/认证/配额/限流/并发/ETag）
  routes.py      全部端点（只读 + 自助领取）
  app.py         create_app 装配

新增数据只走两条路：GitHub PR（本人审核合并）或站长在服务器跑脚本。
API 无任何写数据的端点。
"""
