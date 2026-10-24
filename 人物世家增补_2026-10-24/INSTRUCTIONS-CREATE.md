# 创建模式任务说明（新增人物 / 新增世家 / 补时间线事件）

与「增补模式」不同：你负责的对象是**全新创建**，不是增量修改。质量标准与硬规则与
INSTRUCTIONS.md 完全一致（先读它）：中等详细、绝不虚构、日期不确定就降级 acc、
在世者/运营中企业不写终结、可溯源。

## A. 新建人物（输出完整记录，字段缺一不可）

```json
{
  "id": "拼音或通行英文名-slug",          // 全库唯一
  "name": "中文名", "en_name": "English Name",
  "birth": "YYYY-MM-DD", "birth_accuracy": "exact|month|year",
  "death": "YYYY-MM-DD 或 null",          // 在世必须 null
  "field": "ai|internet|hardware|company|game|creator|science|finance|media|sport",
  "region": "cn|world",
  "headline": "一句话定位（≤24字）",
  "summary_30s": "30秒速览 130~180字",
  "bio": "250~420字 中等小传：定位→出身→主线→现状/结局",
  "timeline": [ {"date":"YYYY-MM-DD","acc":"...","text":"40~120字"} ],   // 10~18条升序
  "achievements": ["..."],                 // 3~6条
  "controversies": ["..."],                // 可选 1~3条
  "quotes": ["..."],                       // 可选 1~3条名言
  "legacy": "1~2句 现状与遗产",
  "sources": [{"title":"...","url":"https://..."}],  // 2~4条可靠来源
  "tags": ["标签1", "标签2"],              // 3~6个
  "related_entities": [{"id":"世家id","name":"名"}]   // 可选
}
```

## B. 新建世家（输出完整记录）

```json
{
  "id": "slug", "name": "中文名", "en_name": "...",
  "type": "company|community|media|service|infrastructure|game",
  "region": "cn|world",
  "founded": "YYYY-MM-DD", "founded_accuracy": "...",
  "dissolved": "YYYY-MM-DD 或 null", "status": "active|declined|acquired|privatized|closed",
  "hq": "总部地",
  "headline": "一句话定位",
  "summary_30s": "90~180字 兴衰速览",
  "bio": "250~420字 兴衰概述：是什么→怎么起家→关键转折→现状",
  "timeline": [ {"date":"...","acc":"...","text":"40~120字"} ],  // 10~18条 创立→发展→巅峰→结局/现状
  "milestones": ["关键数字/里程碑，3~6条"],
  "legacy": "1~2句 现状与遗产",
  "controversies": ["..."],                // 可选
  "sources": [{"title":"...","url":"..."}],  // 2~4条
  "tags": ["..."],
  "related_persons": [{"id":"人物id","name":"名"}]   // 可选
}
```

## C. 补时间线事件（输出事件数组，不套壳）

```json
[ { "id": "YYYY-MM-DD-slug", "date": "YYYY-MM-DD", "title": "≤40字", "summary_30s": "60~120字",
    "detail": "80~200字 经过", "impact": "40~120字 影响", "aftermath": "40~100字 后续",
    "category": "11类之一", "milestone": false, "region": "cn|world",
    "date_confidence": "verified|single-source", "date_accuracy": "exact|month|year",
    "sources": [{"title":"...","url":"..."}], "tags": ["..."] } ]
```

硬要求：
- **每条必须真实、有至少 1 个可靠来源 URL**（权威媒体/官方/维基），confidence 按证据定
- 任务书里给了**该年份已有事件标题清单**——不许与它们重复，补的是清单之外的增量
- 中国互联网主线优先，兼顾世界科技史；民间生活/流行文化类也要（这是本史特色）
- 每年补 8~12 条，宁缺毋滥；日期拿不准就降级 acc 并选该月 01 日
- id 全库唯一；category 必须是 11 类之一


## D. 新建作品志（影视/文学/音乐/游戏/综艺动画等创作物）

```json
{
  "id": "slug", "title": "作品名", "en_title": "English Title 或 null",
  "type": "film|tv|book|netnovel|music|game|comic|documentary|variety",
  "region": "cn|hk|tw|jp|kr|us|world",
  "released": "YYYY-MM-DD", "released_accuracy": "exact|month|year",   // 首映/首播/出版/发售日
  "creators": "作者/导演/主演/乐队（一句话）",
  "headline": "一句话定位（≤24字）",
  "summary_30s": "90~180字 速览",
  "bio": "250~420字：它是什么→创作背景→讲了什么→为什么是精神地标",
  "timeline": [ {"date":"...","acc":"...","text":"40~120字"} ],   // 8~14条：创作→发布→反响→经典化→长期影响
  "legacy": "1~2句 留给大众的精神遗产",
  "quotes": ["经典台词/名句 1~3条"],
  "sources": [{"title":"...","url":"..."}],  // 2~4条
  "tags": ["类型", "主题", ...]              // 3~6个
}
```
硬要求同 A/B：真实可考、日期降级、宁缺毋滥；作品评分/票房等数字要能溯源。