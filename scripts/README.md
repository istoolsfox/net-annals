# scripts/ — 数据管线工具

## ⚠️ 回灌警告（build.py 迁入前必读）

2026-10-24 的 265 份中等详细档案（181 人物 + 84 世家：bio / timeline / legacy / controversies /
部分修正的 status/dissolved/death）目前**只存在于 `site/*/data.json`（线上已生效）**。

生成器 `build.py`（在协作者 Mac 上，尚未迁入）如果直接用旧源稿重建 `site/data`，
**会把这批档案全部冲掉**。重建前必须先回灌。

## 回灌三步

1. **导出**（本机即可）：
   ```bash
   python scripts/export_enriched.py ../site ./源稿回灌
   ```
   得到 `源稿回灌/persons/<id>.json`、`源稿回灌/entities/<id>.json`（每对象一份完整记录）
   和 `_manifest.json`（清单 + sha1 指纹）。

2. **对照合并**：把每份对象的 bio / timeline / legacy / controversies 字段内容
   写回 build.py 的对应源稿（源稿格式以 build.py 实际输入为准）。核对点：
   - timeline 必须保持时间升序、acc 降级语义不变
   - 在世人物 / active 企业不得引入终结条目
   - e04 批修正过的事实（榕树下 closed 2020-08-25、心动 2009 年创立等）不要被旧源稿覆盖

3. **重建后校验**（迁移完 build.py 后跑）：
   ```bash
   python scripts/export_enriched.py ../site ./重建后快照
   diff <(python -c "import json;print(len(json.load(open('./源稿回灌/_manifest.json'))))") /dev/null
   # 对比两份 _manifest.json 的 sha1——字段指纹一致才算回灌成功
   ```

## 工具

- `export_enriched.py` — 如上，导出/校验两用（对同一目录跑两次，指纹不变则数据未漂移）。
- `ali_ecs_api.py`（在 workspace 99-临时/）— 云助手 RunCommand 通道，运维用。
