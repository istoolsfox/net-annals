<!-- 提交前读一遍 CONTRIBUTING.md；CI（validate）会自动校验，红了看 Actions 日志 -->

## 改动类型

- [ ] 数据新增（人物 / 世家 / 作品 / 事件 / 今天 / 地域日志）
- [ ] 数据纠错（日期 / 事实 / 来源）
- [ ] 站点代码
- [ ] 文档

## 数据 PR 自查清单（代码 PR 可跳过）

- [ ] 日期有据：不确定已降级 `acc: month|year`（日期位填 01），未编造精确日期
- [ ] 在世人物（death 为空）/ 运营中企业（status: active）未写终结
- [ ] 每条 ≥1 来源（http(s)，优先维基百科 / 官网 / 权威媒体）
- [ ] `id` 全库唯一；category / field / type / status 在白名单内
- [ ] 复用既有标签体系（先查 index.json 的 tags）
- [ ] 数据文件改动已重压同名 `.gz`
- [ ] 已在本地跑过 `python scripts/validate.py --no-git`

## 说明

<!-- 改了什么、为什么；数据纠错请附依据来源 -->
