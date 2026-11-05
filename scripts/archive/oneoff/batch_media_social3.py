#!/usr/bin/env python3
"""主会话补录批次三：科技/社会/体育/文化 8 条（URL 已全部预验证 200）。"""
import json
from pathlib import Path

EV = Path(__file__).parent.parent / "data" / "events"


def e(id, date, acc, conf, title, cat, region, milestone, s30, detail, impact, after, sources, tags):
    return {"id": id, "date": date, "date_accuracy": acc, "date_confidence": conf,
            "title": title, "category": cat, "region": region, "milestone": milestone,
            "summary_30s": s30, "detail": detail, "impact": impact,
            "aftermath": after,
            "sources": [{"title": t, "url": u, "type": ty} for t, u, ty in sources], "tags": tags}


E1 = [
    e("1991-08-25-linux-announced",
      "1991-08-25", "exact", "verified",
      "Linus 宣告 Linux：一个『爱好』统治世界",
      "tech", "world", True,
      "1991年8月25日，21岁的芬兰大学生 Linus Torvalds 在新闻组发帖：『我正在做一个（免费的）操作系统，只是个爱好，不会像 gnu 那样大而专业。』这个『爱好』后来长成了运行全球绝大多数服务器、手机（安卓内核）和超级计算机的操作系统内核。",
      "Linus 当时在赫尔辛基大学写终端模拟程序练手，帖子还向网友求助 POSIX 规范文档。0.01版1991年9月发布，仅1万行代码；1992年改用 GPL 协议后，全球志愿者通过邮件列表和版本控制接力开发——『集市式』协作自此与『大教堂式』商业开发分庭抗礼。1998年 IBM 等巨头宣布支持后 Linux 进入企业市场；今天安卓手机内核、全球Top500超算全部、云计算主力机型都在跑 Linux。开源许可证、版本控制（Git 也是 Linus 写的）、社区治理等现代软件工程基础设施，几乎都能追到这个帖子上。",
      "证明分布式社区协作可以造出工业级软件，开源从此成为软件业的主导生产方式。",
      "2020年代大模型热潮重演了开源/闭源路线之争，Linux 的社区模式仍是参照系；Linus 本人以『终身仁慈独裁者』自嘲至今仍在合并补丁。",
      [("Wikipedia: History of Linux", "https://en.wikipedia.org/wiki/History_of_Linux", "wiki")],
      ["Linux", "开源", "Linus", "操作系统"]),
]

E2 = [
    e("2002-06-26-yao-ming-number-one",
      "2002-06-26", "exact", "verified",
      "姚明当选 NBA 状元：中国体育的全球化时刻",
      "culture", "cn", False,
      "2002年6月26日，NBA 选秀大会上休斯顿火箭用状元签选中22岁的姚明——NBA 历史上第一位外籍状元。一个2米26的上海青年，从此成为中西方之间最大的一座『桥』。",
      "姚明此前刚率上海大鲨鱼夺得 CBA 总冠军（决赛场均41分），赴美前经历了与上海体育局、篮协的漫长谈判。新秀赛季开局挣扎（首战0分），11月对湖人砍下20分、12月单场命中率12投12中让解说员喊出『巨人正在苏醒』，全明星票王随之而来。NBA 借姚明打开中国市场：转播费、中国赛、球衣销量暴涨，NBA 成为在中国影响力第一的国际体育联盟。姚明9次全明星、2016年入选名人堂，2011年退役后执掌中国篮协，『姚明效应』至今仍在商业与外交层面回响。",
      "中国体育明星全球化的顶点，NBA 商业版图因他东移。",
      "王治郅、易建联相继登陆 NBA 但未能复制其高度；『下一个姚明』成为其后二十年篮球圈的持续命题。",
      [("Wikipedia: 姚明", "https://zh.wikipedia.org/wiki/姚明", "wiki")],
      ["姚明", "NBA", "火箭", "体育全球化"]),
]

E3 = [
    e("2010-06-11-south-africa-world-cup",
      "2010-06-11", "exact", "verified",
      "南非世界杯开幕：世界杯第一次走进非洲",
      "world", "world", False,
      "2010年6月11日，第19届世界杯在南非约翰内斯堡足球城球场开幕，世界杯首次来到非洲大陆。『呜呜祖拉』的嗡鸣声通过转播传遍全球，西班牙最终首次捧杯。",
      "南非击败摩洛哥、埃及获得主办权时举国欢腾——曼德拉将其视为种族隔离后国家形象的又一次正名。赛事投入超百亿美元修场馆、建高铁，但赛后多数球场闲置成为『白象工程』的争议样本。赛场上的名场面不少：郑大世的眼泪、兰帕德的『门线冤案』（直接催生门线技术）、章鱼保罗的8连中预测，以及7月12日决赛伊涅斯塔第116分钟绝杀荷兰。对电视机前的中国观众，这是央视首次全程高清转播的世界杯，也是网络视频第一次大规模分流直播权——CNTV 与多家门户的转播大战开启了此后每届世界杯的版权军备竞赛。",
      "体育赛事全球化的标志性一站，也暴露了新兴市场办大赛的成本难题。",
      "卡塔尔2022年以2200亿美元刷新办赛烧钱纪录；视频技术与 VAR 从这届的冤案讨论中萌芽。",
      [("Wikipedia: 2010 FIFA World Cup", "https://en.wikipedia.org/wiki/2010_FIFA_World_Cup", "wiki")],
      ["世界杯", "南非", "足球", "呜呜祖拉"]),
]

E4 = [
    e("2010-11-28-wikileaks-cables",
      "2010-11-28", "exact", "verified",
      "维基解密公布25万份美国外交电报：国家机密遇上互联网",
      "internet", "world", False,
      "2010年11月28日，维基解密联合《纽约时报》等五家媒体开始公布25万份美国外交电报。这场『 Cablegate 』是有史以来规模最大的机密文件泄露，把『透明』与『国家安全』的战争搬到了互联网上。",
      "朱利安·阿桑奇创办的维基解密此前已公布美军『附加打击』视频（2010年4月）与阿富汗战争日记（7月）。电报门暴露了美国对盟友的监听（对联合国官员搜集情报）、对多国政府的坦率评估，中东多国元首形象受损。美国政府施压下，亚马逊停止托管、Visa/Mastercard 切断支付、PayPal 冻结账户——阿桑奇的支持者以『匿名者』发起报复性 DDoS（Operation Avenge Assange），第一次让『支付武器化』『云服务政治化』进入公众视野。瑞典性侵指控随后启动，阿桑奇2012年进入厄瓜多尔驻英使馆避难长达7年。",
      "互联网泄密与国家权力正面对撞的元年事件，平台中立性神话开始破产。",
      "2013年斯诺登事件把监控议题推向顶点；阿桑奇2019年在使馆被捕，2024年认罪后获释。",
      [("Wikipedia: United States diplomatic cables leak", "https://en.wikipedia.org/wiki/United_States_diplomatic_cables_leak", "wiki")],
      ["维基解密", "阿桑奇", "泄密", "外交电报"]),
]

E5 = [
    e("2012-09-09-didi-launch",
      "2012-09-09", "exact", "single-source",
      "滴滴打车上线：打车难的战役从这里打响",
      "company", "cn", False,
      "2012年9月9日，滴滴打车（小桔科技）App 在北京上线。当时没有多少人相信『用手机叫出租车』能成—— Smartphone 司机装一个 app 都难。十年后它成了日订单数千万单的出行巨头，网约车也彻底改写了中国人的出行方式。",
      "程维从阿里离职创业，初期靠地推一家家说服出租车公司装终端，先在86家出租车公司中被78家拒绝。2012年11月北京大雪叫车需求暴涨，滴滴订单单日破千完成第一次爆发。真正的转折是2014年腾讯投资后的补贴大战：滴滴与快的发红包、免起步价，一天烧钱数千万，最终2015年情人节两家合并；随后与 Uber 中国的战争又以2016年 Uber 出售中国业务告终。网约车重塑了出行、支付（打车成为移动支付高频场景）与就业（数百万司机），也经历了安全事件后的强监管与合规化。",
      "确立移动互联网『烧钱换市场』的打法模板，出行成为移动支付的最大高频场景。",
      "2018年顺风车安全事件后全国性整改；高德聚合、T3、曹操等平台混战，网约车进入存量合规时代。",
      [("Wikipedia: 滴滴出行", "https://zh.wikipedia.org/wiki/滴滴出行", "wiki")],
      ["滴滴", "网约车", "补贴大战", "共享出行"]),
]

E6 = [
    e("2015-07-30-ethereum-frontier",
      "2015-07-30", "exact", "verified",
      "以太坊主网上线：区块链从账本变成平台",
      "tech", "world", False,
      "2015年7月30日，以太坊 Frontier 主网正式上线。21岁的 Vitalik Buterin 把『智能合约』变成现实：区块链不再只是比特币式的账本，而是一台人人可编程的世界计算机。",
      "Vitalik 2013年19岁时发布白皮书，认为比特币脚本能力太弱，提出图灵完备的智能合约平台；2014年众筹1.8万枚比特币（当时约1800万美元）创下纪录。2016年 The DAO 被盗事件引发硬分叉（ETH/ETC 分家），2017年 ICO 狂潮把以太坊推向『泡沫之王』，2020年后 DeFi、NFT 全部建立在以太坊及兼容链上。它证明了『可编程货币』的想象力，也数度因扩容瓶颈与 Gas 费暴涨被讥讽『用不起』，2022年9月转为权益证明后能耗下降99.9%。",
      "智能合约成为区块链行业的默认叙事，Web3 的技术底座由此奠定。",
      "NFT、DeFi、DAO 等概念均诞生于以太坊生态；监管始终在『创新与风险』之间摇摆。",
      [("Wikipedia: Ethereum", "https://en.wikipedia.org/wiki/Ethereum", "wiki")],
      ["以太坊", "智能合约", "Vitalik", "区块链"]),
]

E7 = [
    e("2019-11-27-number-portability-nationwide",
      "2019-11-27", "exact", "verified",
      "携号转网全国正式实施：号码自由落地的最后一块拼图",
      "society", "cn", False,
      "2019年11月27日，三大运营商在全国范围正式提供携号转网服务。手机号码不再被运营商『锁死』——换网不用换号，这个喊了9年的承诺终于全国兑现。",
      "2010年工信部在天津、海南试点携号转网，2014年扩至江西、湖北、云南，但长期『试点不停、全面不推』，转网流程被用户吐槽『层层设卡』。2019年《政府工作报告》明确全国推进，11月27日三大运营商同步正式开放。流程简化为短信查询资格、营业厅一小时内办结。对用户是自由，对运营商是倒逼：转网数据成为服务质量的试金石，5G 竞争从拼信号转向拼资费与服务。累计转网用户此后达千万级，单个号码背后绑定的银行、社交账号太多，实际转网率低于预期，但『可转』本身就是威慑。",
      "用户主权的标志性进展，运营商服务竞争从垄断惯性转向体验。",
      "携号转网叠加5G资费战，运营商 ARPU 持续承压；互联网套餐、定向流量成为标配。",
      [("Wikipedia: 携号转网", "https://zh.wikipedia.org/wiki/携号转网", "wiki")],
      ["携号转网", "运营商", "用户权益", "电信改革"]),
]

E8 = [
    e("2022-08-22-stable-diffusion-release",
      "2022-08-22", "exact", "verified",
      "Stable Diffusion 公开发布：AI 绘画走向全民",
      "tech", "world", False,
      "2022年8月22日，Stability AI 联合学界公开 Stable Diffusion 模型权重。与 DALL·E、Midjourney 的封闭路线不同，它把文生图模型直接放到网上任人下载——AI 绘画由此从演示品变成全民生产力，也点燃了艺术圈的版权大战。",
      "模型由路德维希·马克西米利安大学的 CompVis 团队与 Runway 合作研发、Stability AI 出资训练，以『开放权重』发布，任何人都能本地部署、微调、商用。两个月内社区造出 ControlNet、LoRA 等微调生态，二次元、国风等细分模型百花齐放，Civitai 等模型站崛起；中文圈随之出现基于开源底座的国产绘画应用。争议同步而至：2023年初Getty 起诉 Stability 侵权，画师圈发起集体抵制，『AI 生成内容标识』成为各国监管议题。与 ChatGPT（同年11月发布）前后脚，AI 民主化浪潮的图像侧由此引爆。",
      "开源文生图确立 AIGC 图像赛道格局，创意产业的成本结构与版权规则被重写。",
      "SDXL、SD3 迭代不断；国内以通义万相、混元文生图等自研模型跟进，开源权重路线延续。",
      [("Wikipedia: Stable Diffusion", "https://en.wikipedia.org/wiki/Stable_Diffusion", "wiki")],
      ["Stable Diffusion", "AI绘画", "开源模型", "AIGC"]),
]


def merge(fn, items):
    p = EV / fn
    d = json.loads(p.read_text(encoding="utf-8"))
    have = {x["id"] for x in d}
    add = [x for x in items if x["id"] not in have]
    d.extend(add)
    d.sort(key=lambda x: x["date"])
    p.write_text(json.dumps(d, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"✓ {fn}: +{len(add)}（现 {len(d)} 条）")


merge("1986-1995.json", E1)
merge("2000-2004.json", E2)
merge("2010-2014.json", E3 + E4 + E5)
merge("2015-2019.json", E6 + E7)
merge("2020-2022.json", E8)
print("补录批次三完成")
