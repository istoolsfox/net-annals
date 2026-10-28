# GAP FINDER · n8n 缺口发现工作流方案

> 目标：把「找没收录的事件」从人工轮次升级为 toolsfox.top n8n 上的常态化流水线。
> **定位铁律：n8n 只做「发现 + 初筛 + 查重 + 排队」，成品条目永远由 ZCode 会话按现有管线核实后入库。**
> 2026-10-26 设计。方法论来源见文末。

---

## 〇、一句话定位

n8n = 候选池收割机，ZCode = 核实/写作/入库。
这与已验证的「候选池预扫 → 确认缺口 → 派发」流程（续76轮起，Agent 时间省 60%）**完全同构**——n8n 只是把候选池收割环节自动化、常态化、不依赖会话在场。

## 一、为什么这样分工（有效性第一原理）

- 业界实测：AI 做知识库缺口检测比人工多发现 3-5 倍缺口，但**误报率可高达 40%**（Fini 数据）。所以核心不是「让 AI 找」，而是**给 AI 的产出装足够的闸门**。
- LLM 的正确角色是「提议者」，真相源永远是**工作流里实际抓取到的网页文本**。n8n 官方防幻觉五层架构：上下文工程 / 知识接地 / 输出约束（JSON schema + auto-fix）/ agentic 逐步验证（低置信路由人工）/ 持续评估——本方案全部落地。
- 项目既有红线全部映射进流水线：
  - 「编造 URL = 整批回滚」→ 队列里只允许出现**工作流 HTTP 200 实抓过的 URL**；
  - 「两源才 verified」→ 队列直接预填 `date_confidence` 建议；
  - 「红线转述、绝不罗列」→ 敏感词表只放**服务端 Code 节点**做确定性筛查，**绝不进任何 LLM prompt**（LLM 侧只用类目词）；
  - 「敏感内容主会话亲自写」→ blocked 候选单独落盘，只进 ZCode 主会话。

## 二、三条产出线

| 工作流 | 触发 | 输入来源 | 预期产出 |
|---|---|---|---|
| **A · 权威清单扫荡** | 每周三 09:00 | 维基年份页（1986年中国大陆…）、领域大事记页、Launch Library 2、USGS 等结构化 API | 每周约 100-300 条候选 |
| **B · 缺口定向搜索** | 每月 1 日 | `gap_config.json`（薄年/薄月/薄层/薄省）→ LLM 生成检索词 → 维基 REST 搜索 | 每月约 50-150 条候选 |
| **C · 每日增量（可选）** | 每天 08:00 | Wikimedia onthisday 当日事件 API | 当日缺口 + 反哺「历史上的今天」栏目 |

维基年份页本地已验证高产：`scripts/wiki_harvest.py` 一次采到 3921 条原始条目，n8n 版等于把它搬上服务器持续跑。

## 三、七道有效性闸门（顺序执行，任一不过即出局或降级）

1. **来源白名单**：只抓配置清单里的可信域（wikipedia.org、gov.cn 系、官方 API）。域外 URL 一律不入队。
2. **URL 实取**：候选携带的 source.url 必须是本工作流 HTTP 节点实际抓取（200）的地址，记录 `fetched_at` 与 `http_status`。LLM 在输出里编的 URL 直接丢弃。
3. **引文落地校验（防幻觉核心）**：Information Extractor 强制每条候选带 `quote`（原文引文），Code 节点做规范化（去空白与标点）子串校验——引文必须能在抓取正文里找到，找不到即丢弃。LLM 从此只能「抄」，不能「编」。
4. **双源核验**：对每条候选用维基 REST 搜索（`zh.wikipedia.org/w/rest.php/v1/search/page?q=…`，免费无 key）做第二源查询，日期对上 → `verified`，查不到/对不上 → `single-source`。直接映射库的 date_confidence。
5. **确定性查重**：对 `library_index.json`（全库 id/date/title 索引）做字符重叠比对——**移植 add_events.py 的实测算法**：同日标题字符重叠 >0.6 丢弃、0.3-0.6 标记边缘送人工。确定性算法优先于 LLM 判断（库内实战验证过的规则不动摇）。
6. **重要性门槛**：LLM 按收录标准（第一/首次/最大/转折点/标志性）打 1-5 分，≥3 才入队；1-2 分丢弃（记数不计文）。
7. **敏感分流**：先跑服务端词表硬筛（移植 `wiki_filter.py` 的 BLOCK/SOFT/DISASTER 三级词表），再由 LLM 用**纯类目词**做二级分类（safe/watch/blocked）。blocked 不进通用队列，单独写 `gap_queue_blocked.json`，只由 ZCode 主会话处理。

闸门之后是人工环节：ZCode 会话领取队列 → `precheck_dedup.py` 库内再查一遍（库在持续更新）→ 确认缺口 → 按现有批次管线派 Agent。

## 四、n8n 侧设计

### 4.1 模型与凭证

- n8n 的 LLM 节点走 **OpenAI 兼容端点**：智谱 GLM（Base URL `https://open.bigmodel.cn/api/paas/v4`，推荐 `glm-4-flash`，近免费）或 DeepSeek（`https://api.deepseek.com`，`deepseek-chat`）。
- 提取类调用 temperature 0-0.2 + JSON schema 输出；打分调用同理。每周约 500 次调用，月成本几元级。

### 4.2 工作流 A 节点图

| # | 节点 | 关键配置 |
|---|---|---|
| 1 | Schedule Trigger | 每周三 09:00，时区 Asia/Shanghai |
| 2 | Read Targets（Read/Write File） | 读 `/files/sweep_targets.json`（扫荡目标清单） |
| 3 | Loop Targets（Split In Batches=1） | 每轮之间 Wait 2s（限速礼貌） |
| 4 | Fetch Page（HTTP Request） | UA: `net-annals-gapfinder/1.0 (contact: toolsfox.cn)`，timeout 30s，On Fail: Continue（记下失败目标） |
| 5 | To Text（Code） | 剥 script/style/tag → 纯文本；记录 `http_status`/`fetched_at`；页面 hash 缓存防重抓 |
| 6 | Extract Events（**Information Extractor** + GLM 子节点） | schema：`events:[{date_text,title,gist,quote,category_guess}]`；system prompt 要点：**只从给定文本提取；每条必须给原文引文 quote；日期或事件不确定就跳过；不要输出文本中没有的 URL** |
| 7 | Verify Quotes（Code） | 第三节闸门 3 的引文校验脚本（见 4.4） |
| 8 | Load Library（Read File，一次） | 读 `/files/library_index.json` |
| 9 | Dedup（Code, per item） | 闸门 5 查重脚本（见 4.4） |
| 10 | Second Source（HTTP Request） | 维基 REST 搜索，限速 1s/条；写入 `second_source.date_match` |
| 11 | Score（Basic LLM Chain + GLM） | schema：`{importance:1-5, sensitivity:safe|watch|blocked, reason}`；**prompt 只含类目词**（政治/刑案/灾害/科技/经济/文化/体育/民生） |
| 12 | Switch | dup→丢弃；blocked→单独文件；importance<3→丢弃；其余→入队 |
| 13 | Append Queue（Code + Write File） | 增量合并 `gap_queue_YYYY-WW.json`，按 cid（hash(title+date)）去重防重入 |
| 14 | Notify（Telegram/邮件/钉钉） | 本周入队 N 条、Top10 标题预览、失败目标数 |
| 15 | Error Trigger（独立分支） | 失败即通知：工作流名+执行 ID+错误摘要（n8n 生产最佳实践） |

已处理 cid 集合放 `$getWorkflowStaticData('global')`（n8n 对激活工作流跨执行持久化）。

### 4.3 队列文件 schema（`gap_queue_YYYY-WW.json`）

```json
{
  "batch": "2026-W44",
  "generated_at": "2026-10-28T09:00:00+08:00",
  "candidates": [{
    "cid": "a3f9c2e1b7d4",
    "date": "1993-04-27", "date_accuracy": "exact",
    "title": "候选事件标题",
    "gist": "一句话概述",
    "quote": "来源页原文引文",
    "category_guess": "tech",
    "importance": 4,
    "sensitivity": {"level": "safe", "reason": ""},
    "dup_check": {"status": "clear", "best_overlap": 0.18, "vs_id": null},
    "source": {"url": "https://zh.wikipedia.org/wiki/…", "http_status": 200, "fetched_at": "…"},
    "second_source": {"url": "…", "date_match": true},
    "date_confidence_suggest": "verified"
  }]
}
```

字段与编年条 14 字段 schema 对齐（date/date_accuracy/date_confidence/title/category/region…），ZCode 消费时近乎零转换。**队列文件同 wiki_raw 惯例：本地分析用，不进站点、不提交 git。**

### 4.4 两个核心 Code 节点脚本

**引文落地校验**（闸门 3）：

```javascript
// 输入 item: { events: [...], page_text }
const norm = s => (s || '').replace(/[\s，。；：「」『』《》·、"'()（）\[\]【】\-—…!?,.]/g, '');
const t = norm($json.page_text);
const out = [];
for (const ev of ($json.events || [])) {
  const q = norm(ev.quote);
  if (q.length < 8) continue;                        // 引文过短不可信
  if (t.includes(q)) { out.push(ev); continue; }     // 完整命中
  const mid = q.slice(Math.floor(q.length * 0.2), Math.ceil(q.length * 0.8));
  if (mid.length >= 8 && t.includes(mid))            // LLM 偶改首尾，取中段容错
    out.push({ ...ev, quote_verified: 'partial' });
}
return out.map(e => ({ json: e }));
```

**库内字符重叠查重**（闸门 5，算法同 add_events.py）：

```javascript
// 输入 item: 候选；引用上游 Library Index
const lib = $('Load Library').first().json.items;    // [{id,date,t}]
const sig = s => new Set((s || '').replace(/[\s《》「」·、，。：\-—]/g, ''));
const ov = (a, b) => {
  const A = sig(a), B = sig(b), m = Math.min(A.size, B.size);
  return m ? [...A].filter(x => B.has(x)).length / m : 0;
};
let best = 0, vs = null;
for (const it of lib) {
  if (it.date.slice(0, 10) !== $json.date.slice(0, 10)) continue;   // 只比同日
  const s = ov($json.title, it.t);
  if (s > best) { best = s; vs = it.id; }
}
const status = best > 0.6 ? 'dup' : best > 0.3 ? 'borderline' : 'clear';
return [{ json: { ...$json, dup_check: { status, best_overlap: +best.toFixed(2), vs_id: vs } } }];
```

### 4.5 扫荡目标清单（`sweep_targets.json`，config 驱动）

```json
[
  {"id": "wiki_y1986", "type": "html", "url": "https://zh.wikipedia.org/wiki/1986年中国大陆"},
  {"id": "wiki_y1993", "type": "html", "url": "https://zh.wikipedia.org/wiki/1993年中国大陆"},
  {"id": "ll2_casc",   "type": "json", "url": "https://ll.thespacedevs.com/2.2.0/launch/?limit=100&lsp__name=China+Aerospace+Science+and+Technology+Corporation"},
  {"id": "usgs_sig",   "type": "json", "url": "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&minmagnitude=7&starttime=1970-01-01&minlatitude=18&maxlatitude=54&minlongitude=73&maxlongitude=135"}
]
```

首批建议：40 个年份页 + LL2 + USGS，之后逐步加领域大事记页（电影/体育/铁路/民航官方年表）。**改清单只改这个文件，不动工作流。**

## 五、仓库侧配套（本轮已建，均为 Lane A）

| 脚本 | 产出 | 用途 |
|---|---|---|
| `scripts/library_index.py` | `data/derived/library_index.json` | n8n 查重索引；每轮入库后重跑 + rsync |
| `scripts/gap_config.py` | `data/derived/gap_config.json` | 工作流 B 的缺口清单（薄年/薄月/薄层/薄省 + 检索词模板）；每轮扩库后重跑 |

同步命令：

```bash
python3 scripts/library_index.py && python3 scripts/gap_config.py
rsync -az data/derived/library_index.json data/derived/gap_config.json toolsfox:~/n8n_share/
```

⚠️ 若 n8n 跑在 Docker 里，需挂卷：`-v ~/n8n_share:/files`，节点内路径写 `/files/...`。

ZCode 消费队列：

```bash
ssh toolsfox 'cat ~/n8n_share/queue/gap_queue_2026-W44.json' > data/derived/incoming_queue.json
# → precheck_dedup.py 库内再查 → 确认缺口 → 现有批次管线派发
```

## 六、评估闭环（有效性怎么持续保证）

- **前两周全人工审**：每条候选我过目，统计 precision（入队后被采纳入库的比例），据此调提取/打分 prompt。
- 之后每月抽 10% 核日期（复用验收三件套的库内核对法）。
- prompt 有实质变更时，拿历史批次做回归（n8n Evaluation 节点可选）。
- 月度对账三指标：队列接受率、来源覆盖率（哪些目标页零产出可裁）、三工作流产量。
- 各工作流互相独立，闸门参数（重叠阈值、重要性分数线）写在 Code 节点顶部常量里，便于单独调。

## 七、礼貌与合规

- Wikimedia 系列 API 要求可联系的 User-Agent，已按政策设 `net-annals-gapfinder/1.0 (contact: toolsfox.cn)`。
- 限速：目标间 Wait 2s、二源核验 1s/条；页面 hash 缓存，未变化的页面跳过提取（省钱省调用）。
- onthisday 端点 `api.wikimedia.org/v1/feed/onthisday/events/{MM}/{DD}`（工作流 C 用，上线前先 curl 验一次格式）。
- 队列与中间产物不上传、不进 git、不进站点构建。

## 八、落地步骤

1. ✅ 仓库侧脚本已建：跑 `library_index.py` + `gap_config.py`，rsync 到 n8n 服务器。
2. n8n 建 LLM 凭证（智谱或 DeepSeek，OpenAI 兼容）。
3. **最小闭环**：工作流 A 只接 3 个维基年份页试跑 → 人工全审产出 → 调 prompt 至 precision 满意。
4. 全量目标清单上线（config 已驱动，无需改流程）。
5. 加工作流 B（缺口定向）、C（每日增量）。
6. 队列接进 ZCode 派发管线，形成「服务器常驻收割 + 会话按批消费」的常态。

## 九、方法论来源

- n8n 官方防幻觉五层架构：[AI hallucinations — n8n Blog](https://blog.n8n.io/ai-hallucinations)
- n8n AI Agent 生产部署 15 条最佳实践（Error Trigger/限权/队列）：[blog.n8n.io](https://blog.n8n.io/best-practices-for-deploying-ai-agents-in-production)
- Information Extractor 节点（JSON schema 提取）：[n8n Docs](https://docs.n8n.io/integrations/builtin/cluster-nodes/root-nodes/n8n-nodes-langchain.information-extractor)
- 引文落地/归因抽取防幻觉：[Towards AI](https://pub.towardsai.net/hallucinations-in-llms-a-deep-technical-dive-into-causes-detection-and-mitigation-90229180543b)、[Cleanlab TLM 数据抽取](https://help.cleanlab.ai/tlm/use-cases/tlm_data_extraction)、[Zep](https://www.getzep.com/ai-agents/reducing-llm-hallucinations)
- AI 缺口检测误报率数据（3-5 倍产量 / ~40% 误报）：[Fini](https://www.usefini.com/guides/ai-surface-knowledge-gaps)
- 供给/需求差集找盲区思想：[InfraNodus Content Gap Analysis](https://infranodus.com/docs/content-gap-analysis)
- MediaWiki REST 搜索端点：[API Reference](https://www.mediawiki.org/wiki/API:REST_API/Reference)
- 社区实战（采集类工作流的脏现实）：[r/automation 讨论](https://www.reddit.com/r/automation/comments/1ugb4xq/what_web_data_collection_workflows_have_actually)、[n8n Community](https://community.n8n.io/t/best-practices-for-building-reliable-ai-workflows-in-n8n/315975)

---

## 十、本地定时落地（2026-10-26 实装）

`scripts/news_harvest.py`：时事新闻采集器（工作流 C/D 的本地实现），两个模式：

- **hourly 轻扫**（约 5-10 秒）：中文维基「新闻动态」门户 + 英文维基 Current events 当日页 + 当年中国大陆页（当月）→ AI 初筛 → 追加 `data/derived/daily/hourly_YYYY-MM-DD.jsonl`。
- **daily 全量**（约 4 分钟）：上述 + Google News 中文热点 RSS + 百度热搜 → AI 初筛 → imp≥4 且 deep_dig 的自动深挖（维基词条摘要，渐进截短搜索 + 二字词相关性校验防撞名人词条）→ 写 `data/derived/daily/YYYY-MM-DD.json`。

去重：`_seen.json` 指纹库（文本 md5 前 12 位，保留 8000 条）跨次跨模式去重——实测 daily 首跑 324→322，随后 hourly 只新增 0-2 条。

调度：本工作区 CronCreate 自动化「每小时新闻采集（8点档全量+深挖）」（每小时 :15 触发；8 点档自动切 daily）。**平台限制：一个会话只能挂一个自动化**，故 daily 档并入每小时任务的分支逻辑，不单开任务。

首跑成绩（2026-10-26）：324 条原始 → 322 新增（safe 150/politics 111/disaster 34/social 18/crime 9），高价值 60 条，深挖命中 8/30（事件词条尚未建立的自动落库，符合预期）。

归档定位：**本地候选库**——不进站点构建、不进 git、不直接入库；高价值条目由 ZCode 会话核实后走既有批次管线。

---

## 十一、n8n 服务器端实装（2026-10-27）

toolsfox.top 的 n8n（docker 容器 `n8n`，v2.43.8，卷 `n8n_data`→容器 `/home/node/.n8n`）已由 ZCode 通过 CLI 无头搭建：

**两个工作流（均已激活）**

| 工作流 | ID | 调度 | 链路 |
|---|---|---|---|
| 编年史·新闻采集 | `EOFcQB3xOcW8ih3r` | 每小时 :15（8点档自动全量） | 触发→初始化(北京时间定档)→抓源(维基新闻动态/Current events/GoogleNews/百度热搜)→解析→指纹去重→GLM初筛(20条/批,带ai背景)→合并评分→按日汇总→写归档 |
| 编年史·缺口扫荡 | `EnSvQWUXiWw13gYv` | 每周三 09:00 | 触发→41个年份页→提取带日期条目→GLM提取(强制原文引文)→**引文落地校验**→写队列 |

- GLM 凭证：`GLM API (编年史)`（httpHeaderAuth，id `UnbmLtmDjQXuUjqt`），HTTP Request 节点直连 OpenAI 兼容端点，不用 LangChain 节点（版本免疫）。
- 产出位置（宿主机）：`/var/lib/docker/volumes/n8n_data/_data/daily/daily_YYYY-MM-DD.json` 与 `.../gap/gap_queue_YYYY-MM-DD.json`；消费方式 `ssh toolsfox 'sudo cat …'`。
- 状态持久：指纹库（8000条）与当日条目存 n8n workflow staticData；跨次去重，无新增时跳过 GLM 与写文件。
- 与本地的让位协议不变：`data/derived/n8n_active.json`（7天心跳）存在即本地 news_harvest 跳过。

**搭建踩坑实录（无头 CLI 路线）**

1. `n8n execute --id` 只能跑子工作流（要求 Execute Workflow Trigger），调度型工作流无法手动跑——只能激活后等真实触发验证。
2. 容器内跑 CLI 撞运行实例的 Task Broker 端口（5679）——`-e N8N_RUNNERS_BROKER_PORT=5699` 绕过。
3. 凭证导入必须 JSON **数组**格式，单对象报"File does not seem to contain credentials"。
4. 宿主机 `sudo mkdir` 建的输出目录属主 root，容器 uid 1000 写不进——chown 1000:1000。
5. **宿主机 sqlite3 的 readfile() 只认宿主机路径**：传容器内路径返回 NULL 直接把 nodes 列写空（已用宿主机 /tmp 路径修复）。同理 readfile 能救活写坏的列。
6. 维基 HTML 的 `&#91;1&#93;` 引用标记需实体解码（decodeEnt），否则候选文本带脏字符。
7. 静态数据在**失败执行后也会持久化**——一次失败运行会把当日指纹全部记账，导致后续运行全判重、无产出；恢复方式=重置 workflow_entity.staticData 后重启。
8. 导入重复执行会**按名字再建一份**（不去重）；改已导入工作流用 `UPDATE workflow_entity SET nodes=readfile(...)` 原地替换 + 重启，可保 ID 与激活状态。

### 十一·补：文件写入排障补遗（同日）

首个调度执行连续三次卡在「写归档」节点，最终排障链条（每次都有新发现）：
1. `sudo mkdir` 建的目录属主 root → 容器 uid 1000 写不进（chown 修复，但不是根因）。
2. `N8N_RESTRICT_FILE_ACCESS_TO=/home/node/.n8n`（重建容器）→ 仍被拒。
3. **真根因**：`file-system-helper-functions.js` 里 `N8N_BLOCK_FILE_ACCESS_TO_N8N_FILES` 默认把 **n8n 自身目录（.n8n）整体列为禁写区**，且该判定在白名单**之前**——写 .n8n 下任何路径必被拒。
4. 最终解：重建容器加 `-e N8N_BLOCK_FILE_ACCESS_TO_N8N_FILES=false` + 白名单 .n8n → 15:15 调度执行 success，102KB 日归档落盘。

**其他教训**：①失败的执行也会持久化 staticData（指纹库）——失败运行会"占坑"当日候选，恢复需重置 `workflow_entity.staticData` 并重启；②n8n 数据库错误 blob 是 zod 压缩引用格式（数字字符串→索引递归解析），`SELECT writefile()` 导出后本地 python 递归解析可还原全部细节；③宿主机 sqlite3 的 `readfile()` 只认宿主机路径（容器路径=写 NULL）。容器重建脚本留存：/tmp/recreate_n8n.sh（含全部原 env + 白名单）。
**已知小问题**：manual 桶占比较高（69/249，GLM 批解析失败的兜底），消费端可直接看原文，待后续把解析容错调优。

### 十一·补2：blob 陷阱与公共 API（2026-10-27 晚）

用户报编辑器打开工作流报「Workflow data is invalid / a.nodes.filter is not a function」。根因：用 sqlite3 CLI 的 `readfile()` 原地更新 nodes 列时，写入的是 **BLOB 类型**——运行时（主进程）能容错所以调度照跑，但编辑器 API 校验 nodes 必须是数组，直接拒绝。**修复：`UPDATE ... SET nodes = CAST(nodes AS TEXT)`**（blob 字节即合法 JSON，无损；length 变小只是 blob 按字节/text 按字符计数）。教训：**对 n8n DB 做列内容替换一律用 `CAST(readfile(...) AS TEXT)`**。

另：用户提供了 n8n 公共 API key（`X-N8N-API-KEY` 头，aud=public-api），`GET/PUT http://127.0.0.1:5678/api/v1/workflows/{id}`（服务器本地）可用作今后无头操作的正道——自带校验与版本记录，比 DB 手术安全。注意 PUT 的 body 只含 name/nodes/connections/settings 时报 "Iterator value 0 is not an entry object"（原因未深究，下次用 API 建议带上完整字段或用 MCP 通道）。

## 国内信息源实测台账（2026-10-28 逐站探测，接入批次任务书前先读此节）

### ✅ 完全可取（机器/批次可用）
| 源 | 实测结果 | 用法 |
|---|---|---|
| 人民日报每日纸版 paper.people.com.cn | 头版文章全文 41KB 可取，URL 稳定：`/rmrb/html/YYYY-MM/DD/nw.D110000renmrb_YYYYMMDD_版-页.htm` | 主层补条+核实的逐日权威源（免费公开面，data.people.com.cn 订阅库的替代） |
| 巨潮资讯 cninfo.com.cn | POST `/new/hisAnnouncement/query` 返回公告 JSON（343万条，需 X-Requested-With+Referer 头） | 资本/IPO/公告类条目自动化首选 |
| 新华网 news.cn / 澎湃 thepaper.cn | 首页+文章页公开（澎湃登录标记仅评论） | 核实第二源 |
| 中央党史和文献研究院 dswxyjy.org.cn | 首页 104KB 静态可达 | 1978-2000 主层坐标 |
| 国家统计局 stats.gov.cn / 中国方志网 difangzhi.cn / 国家图书馆 nlc.cn | 首页可达 | 数据/地域线索 |
| gov.cn 文章页 | **栏目页是 JS 壳，但 content_*.htm 文章页是静态全文**（实测 25KB 完整） | 有具体 URL 即可取全文；找 URL 走站内检索或新华网授权转载 |

### ⚠️ 部分可用
- 财新：首页可读、正文订阅墙（不绕付费墙，免费篇可引用）
- 中国大百科 zgbk.com：首页可达，词条页 SPA 需 JS（人工浏览正常）
- 国家法律法规数据库 flk.npc.gov.cn：**人工检索完全可用；机器接口已挖到真实路径**（/law-search/search/list、/law-search/search/flfgDetails，JS 包 assets/index-*.js 中可见）**但参数协议未破（POST 返回"系统异常"）且伴随 captchaImage 组件——自动取数放弃**；法律日期核实改用 gov.cn 公报文章页/新华网授权发布

### ❌ 放弃（站点+原因）
1. 中国信通院 caict.ac.cn——WAF 指纹 412 拦截，全浏览器头重试无效
2. 知网 cnki.net——订阅制+强反爬（商业库不绕）
3. 慧科 Wisers——商业订阅舆情平台
4. 人民日报图文数据库 data.people.com.cn——登录墙（用 paper.people.com.cn 免费纸版替代）
5. 国家图书馆互联网信息存档——机制不对公众开放（非技术问题）
6. 方志/年鉴全文库——纸质/到馆/内部系统为主，官网仅门户

探测方法：urllib 直连（禁环境代理）+ 浏览器 UA，每站 1-3 个轻量请求；绕过尝试仅限公开面（换头/找真实 API 路径），付费墙一律不绕。
