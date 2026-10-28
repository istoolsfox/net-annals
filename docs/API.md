# net-annals 公共 API v1

Base URL：`https://toolsfox.cn/api/v1/`（nginx 仅放行 `/stats/` 与 `/api/`，其余 444 黑屏）

> **⚠️ 备案期访问说明（2026-10-28）**：toolsfox.cn 域名在备案审核期间被注册商停析（公网无 A 记录），与站点同状态。服务器端 https+证书+API 全链已用 `--resolve toolsfox.cn:443:118.178.238.120` 验证通过，**备案通过、DNS 恢复解析后 API 即刻公网可用**，无需任何改动。当前调试用：
> `curl --resolve toolsfox.cn:443:118.178.238.120 https://toolsfox.cn/api/v1/health`

认证：请求头 `X-API-Key: NA-…`（`ro`=只读检索，`admin`=入库管理）。限流 ro 120 次/分、admin 30 次/分，超限 429。

## 端点

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/health` | 无需密钥。`{ok, total, db_generated}` |
| GET | `/meta` | 类目/领域层计数、年份范围、构建时间 |
| GET | `/events` | 列表查询。参数全部可选：`year`(YYYY) `date_from` `date_to`(YYYY-MM-DD) `category` `region`(cn/world) `layer`(拼音层名) `q`(≤64字符多词AND) `page` `limit`(≤200) `sort`(date_asc/date_desc) |
| GET | `/events/{id}` | 单条详情（id 形如 `1993-03-15-8th-npc-1st-session`） |
| GET | `/year/{year}` | 整年条目（≤2000 条） |
| GET | `/search?q=…&limit=≤50` | 相关度搜索：标题30/标签12/摘要6/正文2 加权，多词 AND，中文子串匹配 |
| POST | `/ingest/gap-queue` | **admin**。body 为 n8n 缺口扫荡队列 JSON（≤256KB），服务端校验结构后落盘并异步启动自动管线 |
| GET | `/ingest/status` | **admin**。管线忙闲 + 日志尾部 |

## 安全设计

- **SQL 注入**：全部查询 `?` 参数化；sort/category/region 白名单枚举；LIMIT/OFFSET 强制 int；关键词进 LIKE 前转义 `%` `_` `\`（`ESCAPE '\'`），`%%` 通配符逃逸实测归零。
- **认证**：密钥明文只显示一次，库内仅存 sha256；`hmac.compare_digest` 常时比较；密钥文件 `config/api_keys.json` 0600 不入 git，mtime 热加载 → 吊销即时生效。
- **输入**：year/date/id 正则校验，page/limit 钳制，q 长度 ≤64，未知参数不入 SQL。
- **运行面**：uvicorn 只绑 127.0.0.1，nginx 反代（`^~ /api/`，client_max_body_size 300k）；DB 0600；接口文档页（/docs）已关闭；500 统一短语不回栈帧；不打密钥日志。
- **备案期**：`/api/` 与 `/stats/` 同列白名单（密钥保护），站点其余路径维持 444 黑屏。

## 密钥管理（服务器上）

```bash
cd ~/netannals-pipeline/repo
../.venv/bin/python scripts/api_keys.py issue <名称> ro|admin   # 签发（明文仅显示一次）
../.venv/bin/python scripts/api_keys.py list                    # 列表
../.venv/bin/python scripts/api_keys.py revoke <名称>           # 吊销
```

## 自动入库闭环（每周三）

```
09:00  n8n 缺口扫荡（toolsfox 机）→ 容器内 gap_queue_<日期>.json
09:40  netannals 服务器 cron → auto_pipeline.py --fetch
         ssh 拉队列 → 查重差集 → GLM 初筛(库内相似提示≥0.15) → GLM 成条(--all-sens)
         → add_events → normalize → dedup → build → build_api_db
         → git commit+push(数据+站点工件，.parts 永不入库) → rsync 上线 + API 库热更
```

也可手动/外部触发：`POST /api/v1/ingest/gap-queue`（admin 密钥）。
管线单飞锁（flock）；git pull --ff-only 失败即中止留人工；GLM 被供应商过滤的条目留在 scored 队列待人工复核。

## 服务器部署位置（netannals 机）

- 仓库工作区：`~/netannals-pipeline/repo`（deploy key 可写推送，身份 netannals-auto）
- venv：`~/netannals-pipeline/.venv`（fastapi/uvicorn，阿里源）
- GLM 密钥：`~/.config/net-annals/glm.key`
- 服务：`systemctl {status,restart} netannals-api`（127.0.0.1:8400）
- nginx：`/etc/nginx/sites-enabled/net-annals` 的 `location ^~ /api/`
- 日志：`~/netannals-pipeline/repo/data/derived/api/pipeline.log`

## 已知边界

- v1 只开放编年主库（events）；persons/entities/geo 后续按同模式加表即可。
- 搜索为 LIKE 子串 + 加权粗排，非倒排索引——万级条目内毫秒级，够用。
- politics 自动条目若 GLM 写作被供应商过滤，会留在 `data/derived/gap_scored.json`（note=provider_filtered）待人工，不会静默丢失。
