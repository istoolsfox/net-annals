# net-annals 公共 API v1

Base URL：`https://toolsfox.cn/api/v1/`（nginx 白名单仅 `/stats/` 与 `/api/`，其余 444）

> **⚠️ 备案期访问说明（2026-10-28）**：toolsfox.cn 域名在备案审核期间被注册商停析（公网无 A 记录），与站点同状态。服务器端 https+证书+API 全链已用 `--resolve toolsfox.cn:443:118.178.238.120` 验证通过，**备案通过、DNS 恢复解析后 API 即刻公网可用**，无需任何改动。当前调试：
> `curl --resolve toolsfox.cn:443:118.178.238.120 https://toolsfox.cn/api/v1/health`

## 定位

**严格只读**。全站数据（编年事件 + 人物/实体/作品/世家志）全部可查；API 没有任何写数据的端点——数据新增只走两条路：

1. GitHub PR（一条一文件，CI 自动校验，站长审核合并）→ 见 `docs/CONTRIBUTING.md`；
2. 站长在服务器跑内部管线脚本。

## 认证：三层公开模型

| 层 | 门槛 | 日配额 | 每分钟突发 | 说明 |
|---|---|---|---|---|
| **匿名** | 无需密钥 | 200/IP | 20 | 全部只读端点；响应头 `X-Anon-Quota-Remaining`；`Cache-Control: public, max-age=600` |
| **免费 key** | 自助领取（3 把/IP/天） | 2000（可调） | 120 | 领取页 `/api/v1/keys/page`；响应头 `X-Quota-Limit / X-Quota-Remaining`；`Cache-Control: private` |
| **admin** | 手动签发 | 不限 | 30 | admin 无特权端点——只读面完全相同，仅免日配额 |

- 超额 429 + `Retry-After`；4xx 同样计配额；配额持久化（usage.db，重启不清零）。
- 无效密钥探测 20 次/10 分钟 → 封 IP 1 小时（403 + 解封时间）。
- 注册：`POST /keys/register` 需 `Content-Type: application/json`、浏览器请求须同源（Origin 校验）、5 次/分突发。
- 条款：署名-非商业，禁违规用途，见领取页。
- 响应均带 `X-Content-Type-Options: nosniff`；200 JSON 带 `ETag`（≤256KB），配 `If-None-Match` 返回 304 省带宽。

## 端点

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/health` | 开放（不计配额）。`{ok, total, db_generated, write:"none", tiers}` |
| GET | `/meta` | `total` / `categories` / `layers`（code→{中文名,count}）/ `datasets`（各数据集条数）/ `year_range` / `db_generated` |
| GET | `/events` | 编年事件列表。参数全部可选：`year`(YYYY) `date_from` `date_to`(YYYY-MM-DD) `category`(枚举见下) `region`(cn/world) `layer`(领域层 code，**主时间线不传**；合法值以 `/meta.layers` 为准，非法值 400) `q`(≤64 字符多词 AND) `page`(0 起) `limit`(≤200) `sort`(date_asc/date_desc) |
| GET | `/events/{id}` | 单条详情（id 形如 `1993-03-15-8th-npc-1st-session`） |
| GET | `/year/{year}` | 整年条目（≤2000 条，1400-2100） |
| GET | `/search?q=…&limit=≤50` | 相关度搜索：标题30/标签12/摘要6/正文2 加权，多词 AND，中文子串匹配；返回 `returned` + `_score` |
| GET | `/{dataset}` | 通用数据集列表（4 个，见下表） |
| GET | `/{dataset}/{id}` | 数据集单条详情（返回站点原始完整 JSON） |
| POST | `/keys/register` | 自助领取。body `{"contact": "可选"}`；成功 **201** 返回明文 key（仅此一次） |
| GET | `/keys/page` | 领取页 HTML（开放） |

### 数据集端点（`dataset` ∈ persons / entities / works / groups）

| dataset | 内容 | 过滤参数 | 返回字段要点 |
|---|---|---|---|
| `persons` | 人物（382） | `field`(creator/scientist/…，取值见数据) `region`(cn/world) `year`(出生年 1400-2100) | id/name/en_name/birth/death/field/region/headline/summary_30s… |
| `entities` | 公司/组织/产品（236） | `type`(company/product/…) `region` `year`(创立年) | id/name/en_name/type/founded/status/hq/headline… |
| `works` | 作品（159） | `type`(film/…) `region` `year`(发行年) | id/title/en_title/type/released/creators/headline… |
| `groups` | 世家志群像（78） | （无过滤，仅 q/分页） | id/name/era/summary_30s/members[…] |

所有列表端点统一响应：`{total, page, limit, items[]}`；`q` 多词 AND ≤6 词，LIKE 子串检索中文。

### category 枚举
`milestone internet tech hardware company product national world society culture economy`

## 安全设计

- **SQL 注入**：全部查询 `?` 参数化；sort/category/region/layer 白名单枚举；LIMIT/OFFSET 强制 int；LIKE 转义 `%` `_` `\`（`ESCAPE '\'`）。
- **认证**：key 明文只显示一次，库内仅存 sha256；字典查找 + `hmac.compare_digest` 复核；密钥文件 0600 不入 git，mtime 热加载 → 吊销即时生效；原子写 O_EXCL 0600。
- **输入**：全部参数正则/白名单校验；请求体外层 16KB（Content-Length 缺失 411）。
- **代理信任**：`X-Real-IP` 仅在 TCP 对端为回环（即确实经过 nginx 强制覆盖）时采信；直连一律用对端地址，头伪造无法绕配额或投毒封禁表。
- **fail-open**：配额库故障时放行并告警（绝不因配额库拖死数据面）；封禁检查同。
- **运行面**：uvicorn 只绑 127.0.0.1 单 worker（限流/配额为进程内状态）；nginx `^~ /api/`（client_max_body_size 300k + API 专属 5r/s burst20 + 并发 ≤8，全站另有 20r/s + conn30 + fail2ban）；文档页关闭；500 统一短语，日志路径经 repr 消毒。
- **错误契约**：全站统一 `{"error": "..."}`；422 参数错误归一为 400 `invalid parameters`；gate 层拒绝响应带 `Access-Control-Allow-Origin: *`。

## 密钥管理（服务器上）

```bash
cd ~/netannals-pipeline/repo
../.venv/bin/python scripts/api_keys.py issue <名称> ro|admin   # 签发（明文仅显示一次）
../.venv/bin/python scripts/api_keys.py list                    # 列表
../.venv/bin/python scripts/api_keys.py revoke <名称>           # 吊销
```

## 部署与运维（netannals 机）

- 本地一键：`./scripts/deploy_api.sh`（同步脚本/模板 → 拉齐数据工件 → 重建 API 库 → 重启服务 → 冒烟）
- 仓库 `~/netannals-pipeline/repo`；venv `~/netannals-pipeline/.venv`；服务 `systemctl restart netannals-api`（127.0.0.1:8400）
- nginx：`/etc/nginx/sites-enabled/net-annals` 的 `location ^~ /api/`（**改配置必须双写 sites-available + sites-enabled**）+ `/etc/nginx/conf.d/netannals-api-limits.conf`（apiperip zone）
- 代码结构：`scripts/api/` 包（config/ratelimit/usage_store/keys_store/datasets/store/gate/routes/app，依赖单向）；单测 `python3 -m unittest discover -s scripts/api/tests`；集成冒烟 `python3 scripts/api_smoke_test.py [BASE]`
- 新增可查数据集：`build_api_db.py` 的 `EXTRA_SOURCES` + `api/datasets.py` 的 `DATASETS` 各登记一行（两处断言防漂移）

## 自动入库闭环（每周三）

```
09:00  n8n 缺口扫荡（toolsfox 机）→ 容器内 gap_queue_<日期>.json
09:40  netannals 服务器 cron → auto_pipeline.py --fetch
         ssh 拉队列 → 查重差集 → GLM 初筛 → GLM 成条(--all-sens)
         → add_events → normalize → dedup → build → build_api_db
         → git commit+push → rsync 上线 + API 库热更
```

管线单飞锁（flock）；ff-only 失败即中止留人工。**API 不提供触发入口**（原 /ingest 端点已删除）。

## 已知边界

- 搜索为 LIKE 子串 + 加权粗排，非倒排索引——万级条目内毫秒级，够用。
- `/year` 单响应可达数 MB（>256KB 无 ETag）；大批量拉取请用 `/events` 分页。
- persons/entities/works/groups 返回站点原始 JSON，字段随站点演进；结构以数据为准。
