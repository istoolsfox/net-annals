# 数据结构契约（data contract）

> v2026-10-24 · 由生产数据考古整理。**改结构必须同步改前端渲染代码并 bump 缓存版本。**

## 主时间线

### data/index.json（manifest）

```json
{
  "generated": "2026-10-23T18:17:56+08:00",   // 前端分片缓存版本锚（_v() 取数字后13位）
  "total": 4993, "verified": 4820, "milestones": 37, "sourceCount": 1200,
  "cats": { "internet": 140, "...": 0 },       // 全量分类计数（工具栏徽标）
  "tags": [["标签", 次数], ...],               // 高频标签（前端再按 ≥60 过滤取前 40）
  "eras": [ { "name": "拨号时代", "range": [1994.4, 2000], "shard": "shard-1.json" }, ... ]
}
```

### data/shard-<0..7>.json → 事件数组（按日期升序）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | string | 全局唯一，格式 `YYYY-MM-DD-短横线slug`；**深链 `?event=<id>&date=<date>` 依赖它** |
| date | "YYYY-MM-DD" | acc 非 exact 时日期位可填 01 |
| title / summary_30s / detail / impact / aftermath | string | 卡片三层文本（title≤40字、summary 30秒读完、detail 经过） |
| category | enum | 11 类之一：milestone/internet/tech/hardware/company/product/national/world/society/culture/economy（**前端 CATS 硬编码同步**） |
| milestone | bool | ★ 时代转折（全库 ≤40 条，严格控制） |
| region | "cn" \| "world" | |
| date_confidence | "verified" \| "single-source" \| "uncertain" | 实证/单一来源/存疑徽标 |
| date_accuracy | "exact" \| "month" \| "year" | |
| sources | [{title, url, type?}] | **≥1 必填**，title 人类可读 |
| tags | string[] | 筛选用 |

## 人物志 persons/data.json

```json
{ "generated": "...", "count": 181, "persons": [ { ... } ] }
```

| 字段 | 说明 |
| --- | --- |
| id / name / en_name / field / region | field 为 10 类之一（ai/internet/hardware/company/game/creator/science/finance/media/sport），**前端 FIELDS 映射需同步** |
| birth / birth_accuracy / death | death 为空 = 在世（**禁止编造死亡**；前端显示 `1955– · 在世`） |
| headline | 一句话定位（卡片标题下） |
| summary_30s | 30 秒速览（卡片列表用，~150字） |
| **bio** | 250~420 字中等小传（详情页主段） |
| **timeline** | 10~18 条 `{date, acc, text}`，升序：起点→起步→转折→巅峰→结局/现状 |
| achievements / controversies / quotes | 数组，可空 |
| **legacy** | 1~2 句现状与遗产（详情页底部框） |
| sources / tags / related_entities | 溯源、筛选、与世家互链（related_entities: [{id,name}]） |

persons/groups.json：类传（版主/写手/站长等群像），{groups: [{name, era, summary_30s, members[{name,id_name,headline,text}], legacy, sources}]}。

## 世家志 entities/data.json

同 persons 骨架，差异字段：

| 字段 | 说明 |
| --- | --- |
| type | company/community/organization 等（前端 TYPES 映射） |
| founded / founded_accuracy / dissolved | dissolved 为空且 status=active → 运营中 |
| **status** | active/declined/acquired/privatized/closed（**前端 STATUS 徽标映射需同步**） |
| hq / milestones | 总部 / 关键数字（字符串数组） |
| related_persons | [{id,name}] → 人物志深链 |

## 历史上的今天 today/data.json

`{generated, count, days: {"MM-DD": [event...]}}` —— 366 键，event 为精简结构
`{id, date, title, summary, milestone, layer}`（**无 sources**，溯源靠 `?event=` 深链跳主时间线）。

## 地域日志 geo/data.json

`{generated, stats{provinces,cities,counties,placesWithEvents,taggedEvents}, p/c/k: [[编码,名,全名,上级编码,计数...]], ev: {行政编码: [[date,title,cat,mile]]}}` —— 紧凑数组结构，**列位置即语义**，改前先读 geo/index.html 的映射。

## 已知缺口

- 生成器 build.py 未入仓（在协作者 Mac 上）——迁入后本契约即其输出校验标准。
- 地域日志 206/3361 县域有条目，内容编纂持续中。
