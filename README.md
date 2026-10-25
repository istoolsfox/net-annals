# net-annals · 中国互联网编年史 —— 项目手册（唯一文档）

> 1972—2026 · 精确到日 · 每条可溯源。纯静态站：零依赖、无框架、无构建链。
> 线上 https://toolsfox.cn/ · 生产 netannals（阿里云杭州 i-bp1cx4xj915grm9mjmxi）· 仓库 github.com/istoolsfox/net-annals
>
> **本文是项目唯一文档**（2026-10-25 起）：原则、架构、规则、坑与解法、新增流程全在这里。
> 原 PHILOSOPHY.md、docs/data-contract.md、scripts/README.md、人物世家增补 INSTRUCTIONS*/SCALE-MODE.md 已并入本文并删除。
> AI/新协作者接入另见 **[AGENTS.md](AGENTS.md)**（开发现状快照、已有轮子与数据边界、协作规矩）——本文管"怎么干"，它管"干到哪了、别重复什么"。
> 跨项目运维知识（服务器/防火墙/云助手）在 workspace wiki「netannals服务器」「中国互联网编年史」页。

## 目录结构

```
site/                     ← 网站 web 根（nginx 直接服务，整目录可部署）
├── index.html            主页：四视图（编年史/人物志/世家志/作品志）+ hero + 板块卡
├── common.js             ★ NA 共享模块 —— 全站单一事实源（见 §2）
├── section-view.js       主页视图切换（三视图配置表 + 通用 initView）
├── app.js                编年史引擎（Toolbar→Store→Timeline 分层）+ 工具栏自动隐藏
├── style.css             全站唯一样式表
├── data/                 主时间线 shard-0..7.json(+.gz) + index.json(manifest)
├── persons/  entities/  works/   三个子页（各 3 行脚本 + data.json）+ persons/groups.json 类传
├── today/                历史上的今天（366 天分组 + 右侧抽屉）
├── geo/                  地域日志（省市县树）
└── assets/               og-card 等
scripts/                  export_enriched.py（回灌导出/校验两用）
人物世家增补_2026-10-24/    数据增补工作档案（批次数据 + merge_enrich.py / merge_create.py，Wave-2 可复用）
源稿回灌/                  265 对象档案导出（persons/<id>.json + entities/<id>.json + _manifest.json sha1 指纹）
```

## 1. 编纂原则（宪法）

一部「精确到日、每条可溯源」的中国时代编年史。**内容可信 > 体验顺滑 > 代码优雅**，冲突时按此序取舍。

- **三律**：日期有据、来源可溯、存疑注明。每条 ≥1 来源；日期分歧取多数权威口径并记录；查不到精确日期降级 `acc: month|year`（日期位填 01），text 可写「约」。
- **AI 全权收集 + 人工逐条复核**（页尾「编纂说明」的对外口径）：AI 按三律逐日检索、交叉比对、撰写，人工复核修订后收录。
- **中等详细**：读者标准——看完能懂「这是谁/这是什么、经历了什么、现在怎样或怎样结束的」。bio 250~420 字；timeline 10~18 条升序，覆盖 起点→起步→转折→巅峰→结局/现状 完整弧线。
- **绝不虚构**：在世者（death 为空）严禁写死亡/病重；active 企业严禁写关停；查不到的事实不写。
- **★ 时代转折点**全库严格控制数量（≤40）。
- 规模验收硬标准：任何十年段的事件密度 ≥ 现状×5；人物 600+、世家 300+、作品 300+ 为终态目标。

## 2. 架构与模块复用

零依赖纯静态。数据即文件（JSON + 预压缩 `.gz`，前端 `DecompressionStream` 解压，缺失回退明文）；nginx 直接服务。懒加载（IntersectionObserver + 几何兜底双保险）、分帧渲染（12ms/帧）、`grid-template-rows 0fr→1fr` 展开动画、`prefers-reduced-motion` 降级。

```
common.js (NA)  ←— 单一事实源：esc/safeUrl/fetchGz/dsh/matchQ/wireSearch/
    ↑              buildFilterChips/renderLongScroll/wireExpand/deepLinkCard
    │              personCard/entityCard/workCard 卡片模板
    │              P/E/W 分卷 + FIELDS/TYPES/WTYPES/配色/STATUS/REGION 映射 + DATA_BUILD
    ├── section-view.js   主页：视图配置表(VIEWS) + initView + SV.switch + 深链
    ├── section-page.js   子页通用引擎：persons/entities/works 三页共用，页面只声明 NA_PAGE_KIND
    ├── app.js            编年史引擎（分层单向：Toolbar→Store→Timeline，渲染幂等）
    │                     + 工具栏自动隐藏 + 芯片滚轮横滑；esc/safeUrl 用 NA 别名
    └── today/ geo/       各自特有逻辑（抽屉/省树），工具函数解构自 NA
```

**模块复用铁律**：页面内**禁止**再实现 esc/fetchGz/长卷渲染/卡片模板/筛选芯片/搜索防抖——一律引 common.js。历史上 esc 抄了 7 份、卡片模板抄了 2 份，改一处漏六处的事故已发生过。新增子页成本 = 一份 HTML 骨架 + 一行 `NA_PAGE_KIND` 配置。

## 3. 铁律规则（违反即事故）

1. **版本戳**：改 `style.css`/`common.js`/`section-view.js`/`section-page.js`/`app.js` 任一文件 → 同步 bump **所有引用页**的 `?v=N`（style.css 六页全用；common.js 主页+五子页都用）。改子页数据 json → bump `NA.DATA_BUILD`（common.js 单点）+ 重压同名 `.gz`；主时间线分片的缓存锚是 `index.json` 的 `generated`（重建即自动失效）。
2. **插值纪律**：模板字符串里一切动态值过 `esc()`；一切外链过 `safeUrl()`（只放行 http(s)）。事件一律委托到容器，不给单卡绑监听。
3. **裁剪边界**：给容器加 `content-visibility/contain` 前，先盘点悬挂在边界外的装饰（伪元素、负偏移）。现行方案：离屏裁剪挂在 `.yearGroup` 级（卡片级会剪掉 ★徽标和短刺）。
4. **样式钩子用结构类**（如 `.searchWrap input`），不用单元素 id——`#q` 曾让克隆视图裸奔成浏览器默认样式、且 id 特异性压掉子页自有样式。
5. **渲染性能红线**：新交互不得引入全量重渲；隐藏内容懒构建 DOM；枚举新值（category/field/type/status）必须先加进 common.js 映射表（一处，全站生效）。
6. **禁区**：禁止引入构建工具/框架/npm 依赖（除非用户明示）；禁止渲染路径同步网络请求；禁止绕过 Store 改视图状态；禁止为优化砍来源数据。
7. **密钥不入仓库**；源头数据文件只能由脚本生成/合并，不手改。

## 4. 坑清单（坑 → 解法，按类检索）

**JS 渲染**
- 对象前缀写错（`Timeline.markCurrentEra()` 实际定义在 Toolbar）→ 被动回调里每 tick 抛 TypeError，且中断同一回调的后续语句：时代高亮/年份标签/几何兜底/阅读位置**四个功能一起静默死亡**而页面"看着正常"。解：修正调用。排查口诀——**被动回调里多功能齐失效，先查链路入口异常**。
- IIFE 内外 `const esc` 重名 → 整个 app.js 静默失效（编年史白屏）。解：共享代码进 common.js，页面不再声明同名顶层常量。
- 枚举漏映射（institution）→ 卡片类型显示英文原文。解：映射集中 common.js 后新值只加一处。

**CSS**
- `content-visibility:auto` 剪掉悬挂伪元素（★徽标 top:-11px、短刺 right:-27px），上线一天未被发现。解：裁剪上移 `.yearGroup` 级 + padding/yBadge 让位。**加裁剪前先盘点边界外装饰**。
- 单元素 id 做样式钩子 → 克隆视图裸奔成浏览器默认样式 + id 特异性压掉子页样式。解：`.searchWrap input` 结构类。
- 横滑芯片轨道（nowrap+overflow+mask）把尾部芯片藏出视口，鼠标用户够不到。解：回退 `flex-wrap:wrap` 全量展示；高度压力由「工具栏下滑自动隐藏」化解——**一个方案只扛一个需求**。
- 自动隐藏吸顶栏：未吸顶就隐藏会卡在顶栏下露半截。解：只在 `getBoundingClientRect().top<=55`（已吸住）后允许藏；跳转后钉住 1.5s。
- 懒加载长卷上锚点平滑滚动落点漂移（页高持续增长）+ 连点互断。解：瞬时定位 + 延时校正（现行导航已无锚点链接，教训保留）。
- 子页卡片"隐形"：`.card{opacity:0}` 依赖主长卷的 reveal IO 加 `.in`，子页没有该机制。解：子页卡片创建时直接 `class="card in"`。

**缓存/文案**
- 改了 css/js 没 bump `?v=` → 用户端旧缓存（犯过两次，today/geo 曾落后两个版本）。解：§3 铁律 1，部署前 grep 对账。
- HTML 无 Cache-Control → 浏览器启发式缓存导致拿不到新 HTML。解：nginx `location ~* \.html$ { expires -1; }`。
- og/meta 文案写死计数（4900+）随数据增长过期。解：文案与计数解耦（"数千件"）或 JS 数据回填（HERO.sub）。

**数据脚本**
- merge_create.py 标题长度阈值 `30<=len` 误杀短标题（规范是 ≤40 字）→ 2,539 条被拒。解：阈值放宽到 10；部分文件正则漏配分片 → `out-n\d+(-p\d+)?\.json`。
- 在世者/active 企业写终结 = 事实事故。解：合并端校验 + §5.1 硬规则。

**Windows/自动化环境**
- Git Bash heredoc 吃反引号/模板字符串 → 写 `.py` 文件再 `python file.py`；CRLF 脚本上 Linux 失败 → 发送前替换 `\n`；`/tmp` 与 Windows Python 不通 → 用 `os.environ['TEMP']`。
- 浏览器自动化验证：合成 scrollTo 偶发不触发原生 scroll（标签页挂起恢复）→ **同一 evaluate 单元内跑完整序列**；`scrollTo(x,y)` 受 CSS smooth 影响实为平滑 → 一律 `{behavior:'instant'}`；后台标签 screenshot 返回旧合成帧（scrollY 已 1729 截图仍是页顶）→ **滚动类验证用几何断言，不信截图**。

**服务器运维**（详见 wiki「netannals服务器」）
- fail2ban 把反复认证失败的 IP 全端口 DROP（表现为超时而非拒绝）→ `fail2ban-client set sshd unbanip`；不要暴力探测认证。
- workbench CLI 403（子账号缺 Workbench 权限）→ 走云助手 RunCommand（`99-临时/ali_ecs_api.py`）。
- `/var/www` 无备份写权限 → 备份到家目录 tar；脚本 CRLF → LF；改数据必须重压 `.gz` 否则前端拿到旧压缩件。

## 5. 新增东西怎么做

### 5.1 新增/修改数据

| 改什么 | 流程 |
| --- | --- |
| 主时间线事件 | 改 `site/data/shard-*.json`（按 `Store.eraIndex` 归时代，越界自动钳制）→ 重建/更新 `index.json`（generated 变化即失效前端缓存）→ 重压 `.gz` |
| 人物/世家/作品 | 改对应 `site/<dir>/data.json` → bump `NA.DATA_BUILD` → `gzip -9 -n` 重压 → 主页四视图与子页自动生效（读同一份文件） |
| 历史上的今天 | `today/data.json`（366 天分组，精简结构无 sources，溯源靠 `?event=` 深链）→ 同上 |
| 地域日志 | `geo/data.json` 紧凑数组（列位置即语义，改前读 geo/index.html 映射）→ 同上 |

**新增人物/世家/作品的质量标准与 schema**（原批次任务书并入此处）：

- 字段骨架：`id(全库唯一 slug) / name / en_name / field|type(白名单见 common.js) / region(cn|world) / birth|founded(+accuracy) / death|dissolved(在世或运营中必须 null) / headline(一句话定位) / summary_30s(90~180字) / bio(250~420字) / timeline(10~18条 {date,acc,text} 升序) / achievements|milestones / controversies?(1~3条可选) / quotes?(人物名言可选) / legacy(1~2句现状与遗产) / sources(2~4条 {title,url}) / tags(3~6个) / related_entities|related_persons([{id,name}] 可选互链)`。
- timeline 弧线：起点→关键起步→上升与转折（成败都写）→巅峰/代表作→结局；在世者最后一条写近况，**绝不编造终结**。
- sources 优先维基百科条目 URL / 官网 / 权威媒体；上线后跑链接体检批量核验，不在生成时逐条验证。
- 输出 UTF-8 JSON 无注释不包代码块；写法凭知识（模型即数据库），整批 ≤3 次搜索只查真不确定的日期；`id` 全库唯一，同批禁止同题。

批量工具（`人物世家增补_2026-10-24/`，Wave-2 直接复用）：`merge_enrich.py`（增量合并+校验：日期正则/timeline 升序/bio 长度）、`merge_create.py`（新记录入库：id/name/title 去重、事件按 era 插片、重建 manifest+today、合并端兜底拒收）。规模化方法见 §7。

### 5.2 新增子页（如以后加「建筑志」）

1. 建目录 `site/x/`：`data.json`(+`.gz`) 与 `index.html`；
2. index.html 尾部三行：`<script>window.NA_PAGE_KIND='x'</script>` + `common.js` + `section-page.js`；
3. `section-page.js` 的 CFG 表加一份配置（root/search/chips/eras/card/yearOf/field/colors/labels/fields/unit/param/empty/hero）；若卡片是新结构，在 common.js 加 `xCard` 模板；
4. 头部样式复制现有子页（吸顶条 `.xTop` 一并带上），版本戳用当前 style 版本。

### 5.3 新增主页视图

`section-view.js` 的 `VIEWS` 配置表加一份 + `index.html` 加 `.topTab` 按钮与 `#view-x` pane（toolbar+intro+timeline 三件套）+ `SV.HERO` 文案。init/切换/深链全自动。

### 5.4 上线 checklist（每次必走）

```bash
node --check site/common.js site/section-view.js site/section-page.js site/app.js   # 语法
# 改了哪个静态资源 → 引用页 ?v= 全部 bump（grep 对账）；改了数据 → bump DATA_BUILD + 重压 .gz
python -m http.server 8123   # 本地冒烟：主页四视图卡片数 / 子页三页 / today 抽屉 / geo 树 / 深链
tar -czf /tmp/na.tar.gz -C site . && scp /tmp/na.tar.gz netannals:~/
ssh netannals "tar -czf \$HOME/net-annals-fe-backup-<主题>-<日期>.tar.gz -C /var/www/net-annals . \
  && tar -xzf ~/na.tar.gz -C /var/www/net-annals"
ssh netannals "for p in '' today/ geo/ persons/ entities/ works/; do curl -sk -o /dev/null -w '%{http_code} ' https://127.0.0.1/\$p -H 'Host: toolsfox.cn'; done"   # 全 200
git commit + push；新坑回写 wiki log
```

## 6. 数据契约（精简版；改结构必须同步 common.js/前端并 bump 版本）

- **index.json（manifest）**：`generated`（分片缓存锚）/ `total` / `verified` / `milestones` / `sourceCount` / `cats{}`（工具栏徽标）/ `tags[[标签,次数]]`（前端 ≥60 过滤取前 40）/ `eras[{name,range,shard}]`。
- **事件（shard-0..7）**：`id`（`YYYY-MM-DD-slug`，深链 `?event=&date=` 依赖）/ `date` / `title`(≤40字) / `summary_30s` / `detail` / `impact` / `aftermath` / `category`(milestone/internet/tech/hardware/company/product/national/world/society/culture/economy) / `milestone` / `region(cn|world)` / `date_confidence`(verified|single-source|uncertain) / `date_accuracy`(exact|month|year) / `sources[{title,url,type?}]`(≥1 必填) / `tags[]`。
- **人物**：见 §5.1 schema；`field` 10 类（ai/internet/hardware/company/game/creator/science/finance/media/sport）；`death:null`=在世。**persons/groups.json** 类传：`{groups:[{name,era,summary_30s,members[{name,id_name,headline,text}],legacy,sources}]}`。
- **世家**：同人物骨架，差异：`type`(company/community/media/service/infrastructure/organization/institution/game)/`founded`/`dissolved`/`status`(active|declined|acquired|privatized|closed)/`hq`/`milestones`/`related_persons`。
- **今天**：`{generated,count,days:{"MM-DD":[{id,date,title,summary,milestone,layer}]}}`。
- **geo**：`{stats{provinces,cities,counties,placesWithEvents,taggedEvents}, p/c/k:[[编码,名,全名,上级,计数...]], ev:{编码:[[date,title,cat,mile]]}}`。
- 已知缺口：**生成器 build.py 在协作者 Mac 上未入仓**——迁入后本契约即其输出校验标准；迁入前**严禁**用旧源稿直接重建（会冲掉 265 份档案）。回灌流程：`python scripts/export_enriched.py ../site ./源稿回灌` 导出（已就绪，含 `_manifest.json` sha1 指纹）→ 把每对象 bio/timeline/legacy/controversies 写回 build.py 源稿（核对：timeline 升序、在世者无终结、e04 批修正过的事实不被覆盖）→ 重建后二次导出，两份 manifest sha1 一致才算成功。

## 7. 规模化扩容方法（SCALE-MODE 精要）

> 研究级流程（逐条搜索验证）做百科型内容 = 92K tokens/事件。模型本身就是数据库：**知识优先，搜索只留给真拿不准的日期。**

1. 知识优先，整批 ≤3 次搜索；2. 大批量（事件 ≥80/批、人物 ≥30、世家 ≥25、作品 ≥30）；3. 分片输出（每 25 条一个 part 文件防超长失败，全部写完只回一行统计）；4. 质量底线不降（§1 三律 + §5.1 schema）；5. **横向扩展 10x**：每收录一个对象，同领域再想 10 个同类（刘慈欣→科幻作家群；仙剑→国产 RPG 群）；6. 先扫既有清单去重再选题。

波次节奏：每波 14 个事件批（年份分片）+ 人物/世家/作品扩展批，2 并发撞限即重试；波末 merge → 记录增量 → 不足额年份段生成下波补齐。单批验收：事件 <80 条、拒收率 >15%、同批重复 >3 → 该批重做。

## 8. 参与贡献

欢迎任何人参与修订与增补——**外部贡献一律走 PR**，CI（validate）会自动校验数据契约、JS 语法、版本戳纪律与 `.gz` 同步，人工只复核事实。流程、铁律、PR/Issue 模板见 **[CONTRIBUTING.md](CONTRIBUTING.md)**。许可：代码 MIT，数据 CC BY-SA 4.0（见 [LICENSE](LICENSE)）。

## 9. 相关

- wiki：`00-Wiki/实体/中国互联网编年史.md`（会话沉淀的教训与方法，本文的姊妹页）、`00-Wiki/实体/netannals服务器.md`（SSH/云助手/fail2ban/nginx）
- 生产 nginx：`/etc/nginx/sites-enabled/net-annals`（root /var/www/net-annals；html no-cache）
- 服务器家目录备份序列：`net-annals-fe-backup-2026102*-{主题}.tar.gz` 递增保留
