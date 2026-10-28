# net-annals 公共 API v1 — China Internet Chronicle

**Timeline of China & the world since 1970: 6,000+ sourced events, persons, entities & works — strictly read-only.**
**中国时代编年史 API：1970 年至今 6000+ 条精确到日、逐条可溯源的历史事件，另附人物/实体/作品/世家志四个数据集。严格只读。**

Base URL：`https://toolsfox.cn/api/v1/`

> ⚠️ **临时状态（备案期）**：toolsfox.cn 域名在 ICP 备案审核期间被注册商停析（公网暂无 A 记录）。服务器侧全链已验证；**DNS 恢复后本 API 即刻公网可用，届时删除本段**。调试：`curl --resolve toolsfox.cn:443:118.178.238.120 https://toolsfox.cn/api/v1/health`

## 快速开始 / Quickstart

```bash
# 1. 元信息：条目总数、类目/领域层、年份范围
curl https://toolsfox.cn/api/v1/meta

# 2. 某年全部事件
curl "https://toolsfox.cn/api/v1/year/1994"

# 3. 过滤查询：主时间线 + 科技类
curl "https://toolsfox.cn/api/v1/events?year=1986&category=tech&limit=20"

# 4. 相关度搜索（中文子串，多词 AND）
curl "https://toolsfox.cn/api/v1/search?q=互联网"

# 5. 人物数据集
curl "https://toolsfox.cn/api/v1/persons?field=scientist&limit=10"
```

无需注册即可使用（匿名层 200 次/天/IP）；高频用户自助领免费 key（见下文认证一节）。
No sign-up required. Anonymous tier: 200 requests/day per IP. Free API key for higher volume: `POST /keys/register`.

## 端点 / Endpoints

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/` | **根索引**：自描述端点清单 + 条目总数（评审/发现用） |
| GET | `/health` | 健康检查（不计配额）。`{ok, total, db_generated, write:"none", tiers}` |
| GET | `/meta` | `total` / `categories` / `layers`（code→{中文名,count}）/ `datasets` / `year_range` / `db_generated` |
| GET | `/events` | 编年事件列表。参数全部可选：`year`(YYYY) `date_from` `date_to`(YYYY-MM-DD) `category`(枚举见下) `region`(cn/world) `layer`(领域层 code，**主时间线不传**；合法值以 `/meta.layers` 为准，非法值 400) `q`(≤64 字符多词 AND) `page`(0 起) `limit`(≤200) `sort`(date_asc/date_desc) |
| GET | `/events/{id}` | 单条详情（id 形如 `1993-03-15-8th-npc-1st-session`） |
| GET | `/year/{year}` | 整年条目（≤2000 条，1400-2100） |
| GET | `/search?q=…&limit=≤50` | 相关度搜索：标题30/标签12/摘要6/正文2 加权，多词 AND，中文子串匹配；返回 `returned` + `_score` |
| GET | `/{dataset}` | 通用数据集列表（4 个，见下表） |
| GET | `/{dataset}/{id}` | 数据集单条详情（返回站点原始完整 JSON） |
| POST | `/keys/register` | 自助领取 key。body `{"contact": "可选"}`；成功 **201** 返回明文 key（仅此一次） |
| GET | `/keys/page` | 领取页 HTML（开放） |

### 数据集（`dataset` ∈ persons / entities / works / groups）

| dataset | 内容 | 过滤参数 | 返回字段要点 |
|---|---|---|---|
| `persons` | 人物（382） | `field`(creator/scientist/…，取值见数据) `region`(cn/world) `year`(出生年 1400-2100) | id/name/en_name/birth/death/field/region/headline/summary_30s… |
| `entities` | 公司/组织/产品（236） | `type`(company/product/…) `region` `year`(创立年) | id/name/en_name/type/founded/status/hq/headline… |
| `works` | 作品（159） | `type`(film/…) `region` `year`(发行年) | id/title/en_title/type/released/creators/headline… |
| `groups` | 世家志群像（78） | （无过滤，仅 q/分页） | id/name/era/summary_30s/members[…] |

所有列表端点统一响应：`{total, page, limit, items[]}`；`q` 多词 AND ≤6 词，LIKE 子串检索中文。

### category 枚举
`milestone internet tech hardware company product national world society culture economy`

## 认证与配额 / Auth & Quotas

| 层 | 门槛 | 日配额 | 每分钟突发 | 说明 |
|---|---|---|---|---|
| **匿名** | 无 | 200/IP | 20 | 全部只读端点；响应头 `X-Anon-Quota-Remaining`；`Cache-Control: public, max-age=600` |
| **免费 key** | 自助领取（3 把/IP/天） | 2000（可调） | 120 | 响应头 `X-Quota-Limit / X-Quota-Remaining`；`Cache-Control: private` |
| **admin** | 手动签发 | 不限 | 30 | 无特权端点——只读面完全相同，仅免日配额 |

- 超额 429 + `Retry-After`；4xx 同样计配额；配额持久化（重启不清零）。
- 无效密钥探测 20 次/10 分钟 → 封 IP 1 小时。
- 使用 key：请求头 `X-API-Key: NA-<48位hex>`。
- 条款：**署名-非商业**（CC BY-NC 同等条款），禁违法违规用途。

## 限速、错误与缓存 / Limits, Errors & Caching

- 统一错误契约：`{"error": "..."}`。
- 200 JSON 带 `ETag`（≤256KB），配 `If-None-Match` 返回 304 省带宽；匿名响应带 `Cache-Control: public, max-age=600`。
- 200 JSON 均带 `Access-Control-Allow-Origin: *`（浏览器可直连）。

| 状态码 | 含义 |
|---|---|
| 400 | 参数非法（含 422 归一） |
| 401 | 密钥缺失/格式错/无效（计入探测） |
| 403 | IP 被封禁 / 跨源注册 |
| 404 | 资源不存在 |
| 411 | POST 缺 Content-Length |
| 413 | 请求体过大 |
| 415 | register 非 JSON Content-Type |
| 429 | 限流/配额尽（带 Retry-After） |
| 503 | 数据库未就绪 |

## 安全设计 / Security

- 全部查询 `?` 参数化；sort/category/region/layer 白名单展开；LIKE 转义 `%` `_` `\`。
- key 明文只显示一次，服务端仅存 sha256；`hmac.compare_digest` 恒时复核；原子写 O_EXCL 0600。
- `X-Real-IP` 仅在请求确实经过反向代理时采信（直连一律取 TCP 对端地址，头伪造无效）。
- 服务只绑 127.0.0.1 单 worker，nginx 反代 + 边缘限流；接口文档页（/docs）关闭；500 不回栈帧。
- **写面为零**：没有任何新增/修改数据的端点。数据贡献走 GitHub PR（CI 自动校验，站长审核合并）——见 `docs/CONTRIBUTING.md`。

## 数据许可 / License

数据以 **CC BY-NC 4.0 同等条款**提供：署名「toolsfox.cn 中国时代编年史」、非商业使用。商业授权请联系站长。

---

## 运维手册（站长）

### 密钥管理

```bash
cd ~/netannals-pipeline/repo
../.venv/bin/python scripts/api_keys.py issue <名称> ro|admin   # 签发（明文仅显示一次）
../.venv/bin/python scripts/api_keys.py list                    # 列表
../.venv/bin/python scripts/api_keys.py revoke <名称>           # 吊销
```

### 部署

- 本地一键：`./scripts/deploy_api.sh`（同步脚本/模板 → 拉齐数据工件 → 重建 API 库 → 重启服务 → 冒烟）
- 仓库 `~/netannals-pipeline/repo`；venv `~/netannals-pipeline/.venv`；服务 `systemctl restart netannals-api`（127.0.0.1:8400）
- nginx：`/etc/nginx/sites-enabled/net-annals` 的 `location ^~ /api/`（**双写 sites-available + sites-enabled**）+ `/etc/nginx/conf.d/netannals-api-limits.conf`（apiperip 5r/s zone，location 级 burst=20 + conn 8）
- 代码结构：`scripts/api/` 包（依赖单向）；单测 `python3 -m unittest discover -s scripts/api/tests`；集成冒烟 `python3 scripts/api_smoke_test.py [BASE]`
- 新增可查数据集：`build_api_db.py` 的 `EXTRA_SOURCES` + `api/datasets.py` 的 `DATASETS` 各登记一行（两处断言防漂移）

### 自动入库闭环（每周三）

```
09:00  n8n 缺口扫荡（toolsfox 机）→ 容器内 gap_queue_<日期>.json
09:40  netannals 服务器 cron → auto_pipeline.py --fetch
         ssh 拉队列 → 查重差集 → GLM 初筛 → GLM 成条(--all-sens)
         → add_events → normalize → dedup → build → build_api_db
         → git commit+push → rsync 上线 + API 库热更
```

管线单飞锁（flock）；ff-only 失败即中止留人工。API 不提供触发入口。

### 已知边界

- 搜索为 LIKE 子串 + 加权粗排，非倒排索引——万级条目内毫秒级。
- `/year` 单响应可达数 MB（>256KB 无 ETag）；大批量拉取请用 `/events` 分页。
- persons/entities/works/groups 返回站点原始 JSON，字段随站点演进；结构以数据为准。
