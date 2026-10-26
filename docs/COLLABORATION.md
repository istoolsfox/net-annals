# COLLABORATION · 并行会话协作法则

> 本仓库常有多个 ZCode 会话同时干活（实测常态）。git 对 commit 天然串行，**提交本身是安全的**；
> 真正的危险只有三类：同文件双写、部署互踩、共享区覆盖。本文件就是防这三件事。
> **任何会话开工前必读本文件并做开工体检**（一条命令，见下）。

---

## 一、开工体检（每次开工必做）

```bash
git log -3 --format="%ad %s" --date=format:"%H:%M"   # 最近提交时间，<30 分钟 = 对方在场
python3 scripts/lane_check.py                        # 一键体检：在场检测 + 车道占用报告
```

- CronList 为空 ≠ 没人干活——对方可能是交互会话。
- 若对方车道有大量未提交文件且最近 5 分钟仍在变：**换工作面**（挑对方没占的车道），不要抢。

## 二、车道表（文件级分工，进来自认领）

| 车道 | 归属 | 独占路径 |
|---|---|---|
| **A · 编年数据** | 默认数据会话 | `data/events/**`、`site/data/**`、`site/geo/**`、`data/persons/*.json`（batch 命名）、`scripts/batch_*.py`、`data/wiki_raw/**` |
| **B · 世家/栏目/基建** | 体系会话 | `data/entities/**`、`site/entities/**`、`site/today/**`、`data/persons/groups/**`、`site/assets/**`、SEO/sitemap/robots、`scripts/entity_extract.py`、`validate_entity.py`、`build_entities.py`、`build_today.py`、`make_og.py` |
| **C · 人物志 batch** | 任一空闲会话认领 | `data/persons/p_*.json`（先查重：`grep name data/persons/*.json`） |

> **防覆盖铁律（2026-10-26 增补）**：①发布目标一律 `netannals`（toolsfox 是旧服务器仅301）；②主站备案黑屏期（nginx 444，镜像 istoolsfox.github.io 服务），线上验证异常≠故障；③`site/persons/data.json` 现为370人、`data/persons/*.json` 源已齐（p_server_side_1~16），跑 build_persons 前后核对人数；④works 栏目构建管线在仓库外，数据以静态工件入库，**禁止本地重新生成 site/works/**；⑤改前端先读 common.js/section-page.js（三栏目同一引擎），禁止按旧 app.js 假设改。

> 车道占用现状（2026-10-23 下午）：主数据会话（本表编辑者）占 **A 车道**（编年补条+日期补证，`g_thin_*.json`/补证队列）与 **C 车道**（`p_legends_1`/`p_game_masters_1` 等已提交），并在 B 车道借用 `group_batch3.json` 子路径写类传（乒乓/电影演员/古代科学家/翻译家/诺奖，与 B 会话 batch1/2 共存无冲突）；B 车道其余归体系会话（世家+tianya 提取中）。
| **共享区** | 全体 | `PROGRESS.md`、`ROADMAP.md`、`site/index.html`、`scripts/deploy.sh`、`scripts/build.py`、两个 SPEC、`site/persons/index.html` |

- 新会话进入：从空闲车道认领一块，**把自己的会话标识追加到本表**（写「谁在用」），完工后标注释放。
- 跨车道迁移条目前，先在 PROGRESS 留言声明，避免对方同期动同一批文件。

## 三、五条法则

1. **定点 add**：只 `git add` 自己车道的路径，**禁 `git add -A` / `git add .`**（会连对方的半成品一起提交，实战发生过）。
2. **共享区最小窗口**：改前重读最新版 → 小步快改 → **改完立刻提交**；窗口越长越可能覆盖对方。能由构建器生成的（横幅数字等）绝不手改。
3. **撞车三原则**：
   - **先入库者留**——主题/条目重复，后写者撤稿（案例：站长类传重合 5/6 人，后写方撤）；
   - **不合格 → `.quarantine/` + README**——写明错因与修复路径，等作者修复重交，**绝不直接删**（案例：16 篇类传 34 错被隔离，对方照 README 修复后全过）；
   - **重复条目 → 机器裁决**——dedup 同日重叠规则 + 构建器 id/name 查重兜底。
4. **构建器是最终防线**：所有 build_*.py 内嵌全量校验（id 唯一、字段、红线名单），坏文件跳过 + 警告，**谁写的都复检，不带病上线**——把「信任对方会守规矩」变成「机器不信任任何人」。
5. **部署避让**：deploy 前看 `git status`——若对方车道有大量未提交文件，说明其 WIP 会被全量构建卷进发布。此时只 rsync 自己车道的目录（`rsync -az --delete site/<我的栏目>/ toolsfox:/var/www/net-annals/<栏目>/`），不跑全量 deploy.sh。

## 四、留痕

- PROGRESS.md 各记各的「续 N 轮」区块，**append-only**，不整理别人的段落。
- 隔离/撤稿/让位等决定，在 PROGRESS 与 `.quarantine/README` 双留痕，让对方会话下次开工能读到。

## 五、给派活的人（用户/主会话）

- 给新会话的任务书第一行写：**「开工前先读 docs/COLLABORATION.md 并跑 scripts/lane_check.py」**。
- 同一时刻只给一个会话派「共享区」的活（比如 index.html 改版），改完再派下一个。
