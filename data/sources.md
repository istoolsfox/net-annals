# 信息源地图（查什么年代用什么源）

> 源自服务器清单《互联网编年史资源清单_2026-10-18.md》，落成操作规程。

## 三层拼装法

1. **骨架层**（大事必查）：官方大事记 + 维基逐日存档
2. **血肉层**（网民当天在看什么）：热搜归档 + 技术社区按日搜索
3. **情绪层**（当年什么氛围）：流行语榜单 + 社区兴衰长文 + 老网站截图

## 骨架层：大事必查

| 源 | 覆盖 | 用法 | 链接 |
| --- | --- | --- | --- |
| CNNIC 历年《中国互联网发展大事记》+ 半年度统计报告 | 1994– | 中国互联网官方口径大事，逐条 | https://www.cnnic.com.cn/ReportDownloads |
| CERNET《中国互联网网络基础技术起源及发展大事记》 | 1986–2024 | 接入前史+技术口径，精确到日 | https://www.cernet.edu.cn/xxh/ji_shu_ju_le_bu/Internet/202404/t20240424_2600656.shtml |
| 中央网信办《中国全功能接入国际互联网30周年述评》 | 2024-04-20 | 权威综述 | https://www.cac.gov.cn/2024-04/20/c_1715291120716362.htm |
| Hobbes' Internet Timeline | 1957–2017 | 全球互联网年表，事件级 | https://www.zakon.org/robert/internet/timeline/ |
| RFC 2235 | 至 1997 | Hobbes 冻结正式版 | https://www.rfc-editor.org/info/rfc2235 |
| The History of the Web | 1988– | 万维网史精确到日 | https://thehistoryoftheweb.com/timeline/ |
| 中文维基《新闻动态》逐日存档 | 2002-10– | 每天全球+中国大事，逐日页面 | https://zh.wikipedia.org/wiki/Portal:新聞動態 |
| 英文维基 Portal:Current events | 2002-04– | 同上英文版，存档更全 | https://en.wikipedia.org/wiki/Portal:Current_events |
| 维基 Timeline of 系列 | 分领域 | 在线视频/广告/浏览器/GitHub/YouTube | 见服务器清单 |
| Web Design Museum | 1990– | 逐年网站截图+设计史 | https://www.webdesignmuseum.org/web-design-history |

## 血肉层：逐日网民生活

| 源 | 覆盖 | 用法 |
| --- | --- | --- |
| justjavac/zhihu-trending-hot-questions 等 GitHub 热搜归档 | 2020-11-24– | 每日知乎热榜快照，按天归档 |
| https://remoshuang.com/hot | 近年 | 按日期回看每日热榜（/hot/2026-09-01） |
| hn.algolia.com（API search_by_date） | 2007– | 全球技术圈每天在聊什么 |
| Wayback Machine | 全时段 | 任意网站任意历史日期快照，终极兜底 |

## 情绪层：年度氛围

| 源 | 覆盖 |
| --- | --- |
| 《咬文嚼字》年度十大流行语 | 2008–2024（已结集；萌娘百科有整理版） |
| 社区兴衰长文 | 天涯/猫扑/贴吧/B站（虎嗅/界面/极客公园/蓝鲸） |
| B站怀旧/编年视频 | 搜"互联网编年史""中文互联网简史" |
| Google Doodles 档案 | 全球互联网文化小事件（按日） |
| 《沸腾十五年》林军（1995–2009）、《沸腾新十年》（2010–2020） | 编年体商业史，交叉核对底稿 |

## 按年代的检索策略（速查）

| 年代 | 主查 | 补充 |
| --- | --- | --- |
| 1986–1994 | CERNET 大事记、Hobbes | 学术回忆文章、清华/中科院史料 |
| 1995–2001 | CNNIC 大事记、《沸腾十五年》、公司官网"关于我们"历史页 | 水木/天涯老帖回忆文、新浪科技回顾专题 |
| 2002–2009 | 维基条目+新闻动态存档、《沸腾十五年》 | Web Design Museum、Wayback |
| 2010–2019 | 维基逐日存档、Hacker News、公司公告 | 《沸腾新十年》、虎嗅/36氪年度盘点 |
| 2020–2026 | 维基逐日存档、热搜归档（2020-11 起）、官媒 | remoshuang 热榜回看、hn.algolia |

## 已知坑

- zhihu.com 程序抓取 403 → 只作人工参考，不作 URL 来源首选
- Hobbes 2017 后停更 → 2017 后用维基存档+新闻
- 中文维基《新闻动态》存档 2002-10 才开始 → 2002 前靠大事记+书籍
- 个别著名日期本身有争议（如第一封邮件 09-14/09-20 之争）→ 按 verified 规则记录分歧
