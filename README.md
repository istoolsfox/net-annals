# net-annals · 中国互联网编年史

> 从 1987 年第一封电子邮件到今天，精确到日、可溯源的中国时代编年史 + Three.js 星河可视化。

**是什么**：一部覆盖互联网、科技、硬件、公司、国家大事、世界大事、民间生活、流行文化、经济的中国编年史数据库，外加一个让人"漫游时间长河"的三维可视化站点。

**什么状态**：M1 建设中。总计划见 [PLAN.md](PLAN.md)，进度台账见 [PROGRESS.md](PROGRESS.md)。

**怎么运行（看站点）**：

```bash
./scripts/build.sh          # 校验合并数据 → site/data.json
cd site && python3 -m http.server 8788
# 浏览器打开 http://localhost:8788
```

**目录**：

```
PLAN.md            总体计划（分期/批次/核查纪律/可视化设计）
PROGRESS.md        批次进度台账（断点续跑的真相源）
data/schema.md     条目数据结构 + 核查纪律
data/sources.md    信息源地图（什么年代查什么源）
data/platforms.md  信息传播平台编年
data/events/*.json 编年史数据（按年段分文件）
data/notes/*.md    各批次存疑记录
site/              Three.js 星河站点（静态，可 rsync 发布）
scripts/           build.py（校验+合并）/ build.sh
_server_docs/      服务器拉回的原始需求清单
```

**纪律**：日期必须有来源支撑，有分歧记 notes，查不到降级精度，绝不编造；`site/data.json` 为构建产物不入 git。
