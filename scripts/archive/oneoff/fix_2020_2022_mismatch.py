# -*- coding: utf-8 -*-
"""2020-2022 层错位清障：删真重复8条；修错位条目的 id/date/title。
原则：id 语义必须与 title 一致；date 以 detail 事实为准；污染前缀一律清除。
"""
import json

F = 'data/events/2020-2022.json'

DELETE = [
    '2020-06-30-hongkong-nsa-reading',   # 国安法双条，留 330 字主条
    '2020-11-01-senate-race',            # 泡泡玛特与 12-11-popmart-ipo 重复
    '2020-11-01-icu-nurse-donate',       # Moderna 数据与 nasdaq-ant 条重复
    '2020-12-01-squid-dok2',             # TikTok 与 2020-01-01-tiktok-downloads-first 重复
    '2020-12-01-wonder-woman-streaming', # TikTok 第三条重复且标题半成品
    '2021-07-20-zhengzhou-rainstorm',    # 郑州暴雨双条，留 341 字 henan-flood
    '2021-08-15-afghan-fall-kabul',      # 喀布尔双条，留 277 字 kabul-falls
    '2021-11-26-edinburgh-covid',        # Omicron 双条，留 omicron-variant
    '2021-10-01-chernobyl-solar',        # 一期投运实为 2018 年，内容日期错误删除
]

# id -> (new_id, new_date, date_accuracy, new_title)
FIX = {
 '2020-03-22-biological-male-swimming': ('2020-03-19-bergamo-military-trucks','2020-03-19','exact','意大利贝加莫军车运尸：欧洲疫情最黑暗的影像'),
 '2020-08-19-avatar-china-rerun': ('2020-08-02-babai-release','2020-08-02','exact','《八佰》定档：中国影院重启的救市之作'),
 '2020-08-20-commodore-64-telegram': ('2020-08-05-clean-network-initiative','2020-08-05','exact','美国『清洁网络』计划与微信禁令：数字铁幕西段'),
 '2020-09-16-nintendo-switch-oled': ('2020-09-16-ps5-xsx-announced','2020-09-16','exact','PS5 与 Xbox Series X 发布：第九世代主机大战'),
 '2020-09-22-qq-cybertruck-battery-day': ('2020-09-22-tesla-battery-day','2020-09-22','exact','特斯拉电池日：4680电池与降本56%的宣言'),
 '2020-10-01-blackpink-lisa': ('2020-09-01-bts-dynamite-no1','2020-09-01','month','BTS 登 Billboard 冠军与 K-pop 的美国主流化'),
 '2020-10-01-nba-tencent': ('2021-02-12-bbc-banned-cn','2021-02-12','exact','中国禁止BBC世界新闻播出：舆论战的对等反制'),
 '2020-10-01-chess-dot-com': ('2020-10-01-chess-online-boom','2020-10-01','month','线上国象爆发：Chess.com 用户破千万与『后翼弃兵』效应'),
 '2020-11-01-jaguar-ipace': ('2020-11-15-spacex-crew1','2020-11-15','exact','SpaceX 载人龙 Crew-1：商业航天的首次正式班机'),
 '2020-11-01-lunar-new-year-film': ('2020-06-22-wwdc-apple-silicon','2020-06-22','exact','WWDC 转向自研芯片预告：苹果生态的『移山』工程'),
 '2020-11-01-richest-luxury': ('2020-11-18-musk-second-richest','2020-11-18','exact','马斯克超过比尔·盖茨：世界第二富豪的硅谷时刻'),
 '2020-11-01-ukraine-biden-call': ('2020-11-10-nagorno-karabakh-ceasefire','2020-11-10','exact','纳卡战争停火：44天无人机战争的终局'),
 '2020-11-01-wuhan-hero-city': ('2020-12-30-eu-china-cai-concluded','2020-12-30','exact','中欧投资协定谈判完成：七年长跑的压线时刻'),
 '2020-11-03-nasdaq-ant': ('2020-11-16-moderna-efficacy-mkt','2020-11-16','exact','Moderna 与辉瑞疫苗数据接力：mRNA 的世纪验证'),
 '2020-11-05-xiaomi-super': ('2020-10-13-iphone-12-5g','2020-10-13','exact','iPhone 12 全系5G登场：5G换机潮启动'),
 '2020-11-09-shanghai-disney': ('2020-05-01-byd-mask-50m','2020-05-01','month','产能出海：比亚迪口罩日产5000万只的世界纪录'),
 '2020-11-24-turkish-santa': ('2020-09-21-un-75-anniversary','2020-09-21','exact','联合国75周年峰会：多边主义的至暗自省'),
 '2020-12-01-digital-wealth': ('2020-12-02-evergrande-property-ipo','2020-12-02','exact','恒大物业上市：地产帝国分拆自救的资本突围'),
 '2020-12-11-mcu-phase-4': ('2020-12-25-wonder-woman-1984-hbo-max','2020-12-25','exact','《神奇女侠1984》同步流媒体：窗口期革命的第一枪'),
 '2020-12-14-hawley-tiktok-deal': ('2020-12-14-first-us-covid-shot','2020-12-14','exact','辉瑞疫苗第一针：纽约护士成为全球接种里程碑'),
 '2020-12-17-belarus-olympics': ('2020-12-01-sports-calendar-restructure','2020-12-01','month','体育日历大重构：欧洲杯美洲杯延期与温网取消'),
 '2020-12-25-mooncake-festival-film': ('2020-12-25-soul-pixar-china','2020-12-25','exact','《心灵奇旅》与皮克斯的流媒体圣诞：合家欢的云端化'),
 '2021-03-01-crypto-nft-top': ('2021-06-01-nft-cn-collections','2021-06-01','month','支付宝NFT邮票与中国数字藏品元年'),
 '2021-03-01-tencent-music-ipo': ('2021-01-22-relx-ipo','2021-01-22','exact','悦刻上市与电子烟监管风暴：新消费的监管第一课'),
 '2021-04-10-flutter-through': ('2021-04-01-shipping-crisis-chain','2021-04-01','month','苏伊士之外：2021年全球海运的连锁危机'),
 '2021-04-20-akp-george-floyd-verdict': ('2021-04-20-chauvin-verdict','2021-04-20','exact','肖万被定罪：弗洛伊德案的司法时刻'),
 '2021-05-31-yuan-sesame-street-cny': ('2021-05-31-three-child-policy','2021-05-31','exact','三孩政策出台：中国人口政策的重大转向'),
 '2021-06-01-crypto-com-arena': ('2021-06-01-chip-shortage-2021','2021-06-01','month','全球芯片荒：一颗 Missing Chip 停产一辆车'),
 '2021-06-01-minecraft-youtube': ('2021-06-01-genshin-global','2021-06-01','month','《原神》全球化现象级成功：中国游戏的出海里程碑'),
 '2021-06-01-wuhan-vaccine-who': ('2021-06-01-who-eul-sinovac','2021-06-01','exact','世卫批准科兴与国药疫苗进入紧急使用清单'),
 '2021-06-11-unesco-world-heritage': ('2021-07-25-quanzhou-unesco','2021-07-25','exact','泉州申遗成功：宋元中国的世界海洋商贸中心'),
 '2021-06-19-dongguan-nba': ('2021-05-30-tianzhou-2-docking','2021-05-30','exact','天舟二号与空间站对接：载人航天工程密集期开启'),
 '2021-06-25-suez-bbc-oval-office': ('2021-08-10-cuomo-resigns','2021-08-10','exact','纽约州长科莫性骚扰调查报告与辞职：疫情明星的陨落'),
 '2021-07-01-beach-olympic-trials': ('2021-05-21-gaza-ceasefire','2021-05-21','exact','以色列-加沙11天战争停火：火箭与铁穹的五月'),
 '2021-07-20-nba-playoffs-china': ('2021-07-20-bucks-nba-title','2021-07-20','exact','雄鹿时隔50年再夺冠：字母哥的单核传奇'),
 '2021-08-01-xiaomi-phone-surpass': ('2021-03-30-leijun-ev','2021-03-30','exact','雷军宣布小米造车：人生最后一次重大创业'),
 '2021-09-01-quantumscape': ('2021-09-01-tesla-4680-gigacasting','2021-09-01','month','特斯拉4680电池量产准备与一体化压铸：制造革命之年'),
 '2021-09-05-alliance-of-sahel': ('2021-09-05-guinea-coup','2021-09-05','exact','几内亚政变：孔戴被扣，萨赫勒政变带继续蔓延'),
 '2021-10-01-crypto-mining-texas': ('2021-10-01-bitcoin-mining-exodus','2021-10-01','month','比特币算力中国清零后的北美大迁徙'),
 '2021-10-08-didi-ban': ('2021-11-24-changjinhu-record','2021-11-24','exact','《长津湖》57.75亿登顶：主旋律大片的市场巅峰'),
 '2021-10-22-dune-oscar-run': ('2021-10-22-dune-villeneuve','2021-10-22','exact','《沙丘》上映：维伦纽瓦的沙漠史诗与影院救市'),
 '2021-11-01-crypto-tax': ('2021-11-15-us-infrastructure-bill','2021-11-15','exact','美国万亿基建法案签署：含加密经纪商报税条款'),
 '2021-11-01-russian-troops-spring': ('2021-11-01-russia-border-buildup','2021-11-01','exact','俄军集结乌克兰边境：战争阴云的公开化'),
 '2021-11-01-tencent-super-app': ('2021-11-01-metaverse-cn-mania','2021-11-01','month','元宇宙概念入侵中文互联网：中青宝们股价过山车'),
 '2021-11-06-beer-champion': ('2021-11-06-edg-worlds-title','2021-11-06','exact','EDG 夺得英雄联盟S11全球总决赛冠军：中国电竞的全民之夜'),
 '2021-11-08-nikkei-vaccine-pass': ('2021-11-08-vaccine-passport','2021-11-08','month','疫苗护照全球推行：健康码的国际化年'),
 '2021-11-08-south-africa-olive': ('2021-04-01-ai-voice-vtuber-economy','2021-04-01','month','格莱姆斯 AI 声音开源与虚拟偶像经济元年'),
 '2021-11-11-james-webb-christmas': ('2021-11-09-nvidia-omniverse','2021-11-09','exact','英伟达 Omniverse 与工业元宇宙起步'),
 '2021-11-24-lady-gaga-house': ('2021-11-24-house-of-gucci','2021-11-24','exact','《古驰家族》上映与时尚IP电影潮'),
 '2021-12-01-hardware-wallet': ('2021-12-01-wearables-big-year','2021-12-01','month','可穿戴设备大年：Apple Watch 与智能眼镜的前奏'),
 '2021-12-01-hmrc-charging': ('2021-12-01-shenzhen-price-decline','2021-12-01','month','深圳房价首次整年下跌的拐点'),
 '2021-12-01-macgyver-mandela': ('2021-12-26-desmond-tutu-died','2021-12-26','exact','德斯蒙德·图图逝世：南非良心走完90年'),
 '2021-12-01-super-app-swiggy': ('2021-12-01-india-unicorn-ipo-wave','2021-12-01','month','印度独角兽大爆发：Zomato、Paytm、Nykaa 上市潮'),
 '2022-06-16-maldives-president-assassination-attempt': ('2022-06-17-fda-under5-vaccines','2022-06-17','exact','FDA 批准辉瑞与莫德纳疫苗用于5岁以下幼儿'),
 '2022-08-01-bajaj-ipo': ('2022-08-01-baojiaolou-rescue','2022-08-01','month','LPR 非对称降息与保交楼：地产纾困之年'),
 '2022-08-01-chennai-floods': ('2022-08-01-china-ev-penetration-25','2022-08-01','month','中国新能源渗透率破25%：比亚迪跃升全球新能源销冠的前夜'),
}

d = json.load(open(F))
removed = [e['id'] for e in d if e['id'] in DELETE]
d = [e for e in d if e['id'] not in DELETE]
fixed = 0
for e in d:
    if e['id'] in FIX:
        nid, nd, acc, ntitle = FIX[e['id']]
        e['id'] = nid
        e['date'] = nd
        e['date_accuracy'] = acc
        e['title'] = ntitle
        fixed += 1
json.dump(d, open(F, 'w'), ensure_ascii=False, indent=0)
print(f"删除 {len(removed)} 条，修复 {fixed} 条，文件剩余 {len(d)} 条")
ids = [e['id'] for e in d]
print('仍重复的 id:', [i for i in set(ids) if ids.count(i) > 1])
