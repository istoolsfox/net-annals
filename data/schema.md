# 编年史条目数据结构（schema v1）

## 存储形式

`data/events/<年段>.json`：JSON **数组**，每个元素一条事件。年段文件之间不重复、不交叉。

## 条目字段

```json
{
  "id": "1987-09-14-first-email",
  "date": "1987-09-14",
  "date_accuracy": "exact",
  "date_confidence": "verified",
  "title": "中国第一封电子邮件发出",
  "category": "milestone",
  "region": "cn",
  "milestone": true,
  "summary_30s": "30 秒读完的概括（80-160 字，普通人能懂）",
  "detail": "来龙去脉（200-600 字），写清楚谁、在哪、做了什么",
  "impact": "当时造成了什么影响",
  "aftermath": "后来怎么样了 / 延续至今的后果",
  "sources": [
    {"title": "CERNET 中国互联网大事记", "url": "https://...", "type": "official"}
  ],
  "tags": ["email", "CANet", "钱天白"]
}
```

## 字段规约

| 字段 | 必填 | 规约 |
| --- | --- | --- |
| `id` | ✅ | `YYYY-MM-DD-<小写短横线slug>`，全库唯一 |
| `date` | ✅ | `YYYY-MM-DD`。accuracy 非 exact 时：month → 该月 01 日；year → 当年 01 月 01 日 |
| `date_accuracy` | ✅ | `exact`（精确到日）/ `month` / `year` |
| `date_confidence` | ✅ | `verified`（≥2 独立来源或权威一手）/ `single-source` / `uncertain`（存疑，notes 必须记录） |
| `title` | ✅ | 一句话标题，简洁有力，可含关键人名/产品名 |
| `category` | ✅ | 11 选 1（见下） |
| `region` | ✅ | `cn` / `world`（世界大事且与中国无直接关联用 world，中国相关一律 cn） |
| `milestone` | ✅ | true/false。**时代转折点**才为 true，宁少勿多 |
| `summary_30s` | ✅ | 80–160 字，去术语，能念出来的白话 |
| `detail` | ✅ | 200–600 字 |
| `impact` | ✅ | 一句话到一段话 |
| `aftermath` | ✅ | 后续发展；无明确后续写"延续至今"式的去向 |
| `sources` | ✅ | 1–3 条；`type`: wiki/news/official/blog/archive/book/video。**URL 必须真实** |
| `tags` | ⛔ | 0–6 个 |

## category 枚举（11 类，覆盖生活的方方面面）

| 值 | 含义 | 例子 |
| --- | --- | --- |
| `milestone` | 时代转折点 | 1994 全功能接入、微信上线、ChatGPT 发布 |
| `internet` | 互联网/网络大事 | 3Q 大战、宽带提速、/.cn 域名 |
| `tech` | 科技/软件 | Android 发布、GPT-4 |
| `hardware` | 硬件（电脑/手机/耳机/家电/车） | 联想收购 IBM PC、iPhone 4、小米 1 |
| `company` | 公司商业（创立/上市/并购/倒闭） | 阿里 NYSE 上市、ofo 押金危机 |
| `product` | 产品/服务上线 | 淘宝、余额宝、健康码 |
| `national` | 国家大事（政策/法规/大事件） | 双减、4G/5G 牌照、民法典 |
| `world` | 世界大事 | 911、俄乌、雷曼倒闭 |
| `society` | 民间生活（学校/工作/物价/房车/婚恋） | 大学扩招、房价、春运 |
| `culture` | 流行文化（影视/游戏/梗/流行语） | 贾君鹏、超级女声、黑神话 |
| `economy` | 经济金融 | 股市熔断、双十一成交额 |

> 一条事件只归一类，选"最接近用户感知"的那类。

## 核查纪律（写盘前自查清单）

1. 每个 `date` 有来源支撑吗？有分歧记 notes，查不到降级 accuracy，**绝不编造精确日期**。
2. `sources[].url` 都是你确认真实存在的吗？
3. `summary_30s` 是普通人白话吗？`impact`/`aftermath` 写了吗？
4. `milestone=true` 的条数，单一年段 ≤8 条了吗？
5. 同一月条数 ≤1000（硬顶）了吗？实际目标每月 10–60 条。
6. JSON 能被 `python3 -m json.tool` 无错解析吗？

## notes 文件

每批次同写 `data/notes/<年段>-notes.md`：
- 存疑条目清单（id + 分歧描述 + 倾向结论）
- 有价值的补充线索（后续批次可挖）
