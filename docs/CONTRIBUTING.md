# 贡献指南（新增一条编年史条目）

本站数据**只能**通过两条路进入：

1. **GitHub PR**（推荐给贡献者）：一条一文件，站长审核后合并；
2. **站长服务器脚本**：内部管线（n8n 扫荡 / GLM 成条 / add_events）。

**API 永远只读**——没有任何新增/修改数据的 HTTP 端点。

## 三步新增一条事件

```bash
# ① 生成草稿（照模板，一条一文件）
python3 scripts/new_entry.py --date 1994-04-20 --title "中国全功能接入互联网" \
    --slug china-internet --layer tech --category tech --region cn

# ② 编辑生成的 data/events/1994-04-20-tech-china-internet.json
#    填 summary_30s / detail / tags / sources（占位符不改过不了校验）

# ③ 本地校验
python3 scripts/validate_events.py data/events/1994-04-20-tech-china-internet.json
```

然后 `git add` 该文件 → 提交分支 → 开 PR。CI 会自动跑全库校验 + 变更文件深度查重，红了的 PR 不会被合并。**合并后**由站长在服务器跑 `deploy.sh` 上线（API 库随 `build_api_db.py` 自动重建，周三维护管线也会顺带拉取部署）。

## 字段说明（14 个必填）

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | str | `YYYY-MM-DD-小写语义slug`（不含层码），与 `date` 前缀一致，全库唯一 |
| `date` | str | `YYYY-MM-DD` 真实日期，年份限 1900–次年；月/年精度时归一到 01 日并同步 `date_accuracy` |
| `title` | str | ≤48 字（软约束，超长只警告），含关键实体名（检索主要依据） |
| `category` | str | milestone / internet / tech / hardware / company / product / national / world / society / culture / economy |
| `region` | str | `cn` 或 `world` |
| `milestone` | bool | 一般 `false`；里程碑事件才 `true` |
| `date_confidence` | str | verified / single-source / uncertain |
| `date_accuracy` | str | exact / month / year |
| `summary_30s` | str | 30 秒摘要，≥20 字（软约束）；40-160 字为宜 |
| `detail` | str | 正文；数字必须能溯源到 sources |
| `impact` / `aftermath` | str | 可为空串 |
| `tags` | list[str] | 检索辅助标签 |
| `sources` | list | 至少一条 `{url: http(s), title}`；**编造 URL = 整 PR 拒收** |

规则与红线：

- **一条一文件**：文件名 `YYYY-MM-DD[-层码]-slug.json`（注意**文件名带层码、id 不带**），与文件内唯一条目的 `date` 一致；层码见 `scripts/api/config.py` 的 `LAYER_NAMES`。主时间线条目**不带层码**（`--layer` 省略）。
- **slug 不要以层码开头**（如主时间线条目用 `games-xxx` 当 slug 会被误归入游戏层）——`new_entry.py` 已自动剥离，手工改名的注意。
- **同日查重**：与已有条目标题字符重叠 >60% 会被 CI 拦下（`validate_events.py` 深度模式，规则与入库器一致）。
- **年份范围**：1900 至次年。更早的历史条目走站长内部管线。
- 中性记述允许出现人名（企业家/科学家/运动员/艺术家/历史人物）；不做主观定性，不写宣扬性语言。
- 一切以可溯源为准：给不出来源链接的"事实"不要写。

## 本地校验 API（可选）

```bash
pip install fastapi uvicorn
python3 scripts/build_api_db.py
uvicorn scripts.api_server:app --port 8400 &
python3 scripts/api_smoke_test.py http://127.0.0.1:8400
```
