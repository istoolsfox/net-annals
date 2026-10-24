# net-annals · 中国互联网编年史

> 1972—2026 · 精确到日 · 每条可溯源。纯静态站：零依赖、无框架、无构建链。
> 线上：https://toolsfox.cn/ （生产服务器：netannals，阿里云杭州 i-bp1cx4xj915grm9mjmxi）

## 目录结构

```
site/                  ← 网站 web 根（nginx 直接服务，整目录可部署）
├── index.html         主长卷（app.js 驱动：Store/Timeline/Toolbar 三层）
├── app.js / style.css 全站唯二共享资产
├── data/              主时间线分片（shard-0..7.json + .gz）+ index.json（manifest）
├── today/             历史上的今天（data.json 366 天分组）
├── persons/           人物志（data.json 181 人 + groups.json 类传）
├── entities/          世家志（data.json 84 家）
├── geo/               地域日志（省市县树 + 事件）
└── assets/            og-card 等静态资源
人物世家增补_2026-10-24/  ← 2026-10-24 数据增补工作档案（批次/校验脚本/输出）
PHILOSOPHY.md          ← 项目宪法（AI/协作者必读）
docs/data-contract.md  ← 数据结构契约（改数据前必读）
```

## 铁律（详见 PHILOSOPHY.md）

1. **缓存纪律**：改 `app.js`/`style.css` → 必须同步 bump 所有引用页 `?v=N`；改任何 `data/*.json` → 必须 bump 对应子页的 `DATA_BUILD` 常量 + 重压同名 `.gz`（fetchGz 优先取 .gz）。
2. **溯源纪律**：每条数据必须有 sources；不确定日期降级 `acc: exact|month|year`，绝不编造。
3. **在世者/运营中企业不写终结**。
4. 插值必须过 `esc()`；外链只放行 http(s)（`safeUrl`）。

## 部署流程（当前为手工 SCP，生成器迁入后自动化）

```bash
# 1. 本地验证
python -m http.server 8642  # 浏览器过一遍冒烟：加载/交互/移动视口/深链
# 2. 重压 .gz（如果改了数据）
gzip -9 -n < site/persons/data.json > site/persons/data.json.gz
# 3. 上传（scp 到 netannals 服务器，install 保持属主 toolsfox_netannals）
# 4. 改前备份到服务器 ~/net-annals-*-backup-<日期>/
```

## 数据管线现状（待办）

- **生成器（scripts/build.py）在队友的 Mac 上，尚未迁入本仓** —— 见 docs/data-contract.md，
  迁入后 site/data/* 由源稿重建，人工增补需回灌源稿，避免下次构建覆盖。
- 2026-10-24 全量增补：265 对象（181 人 + 84 家）中等详细档案，工作档案在
  `人物世家增补_2026-10-24/`（含合并校验脚本 merge_enrich.py，可复用）。

## 相关

- 运维细节（服务器/防火墙/fail2ban/备份）：workspace wiki「netannals服务器」「中国互联网编年史」页
