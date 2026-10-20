#!/usr/bin/env python3
# 体育产业史层 · 第一批（联赛职业化/运动品牌/版权经济/健身消费，与sports赛事层互补）
import json, os
os.makedirs('data/events/.parts', exist_ok=True)

def S(t, u):
    return {"type": t, "url": u, "title": t}

D = [
 {"id":"1984-01-01-jianlibao-oriental-magic-water","date":"1984-01-01","date_accuracy":"year","date_confidence":"single-source",
  "title":"健力宝随中国奥运军团一炮而红，「东方魔水」诞生","category":"company","region":"cn",
  "milestone":False,"region_note":None,
  "summary_30s":"1984年洛杉矶奥运会，随中国代表团亮相的广东橙蜜运动饮料健力宝被外媒称作「东方魔水」。",
  "impact":"中国第一款功能性运动饮料完成现象级亮相，体育+饮料+广告的营销范式由此确立。",
  "aftermath":"健力宝此后多年冠名体育赛事成为「民族饮料第一品牌」，三水健力宝的兴衰也成为日后中国企业史的经典案例。",
  "tags":[],"sources":[S("wiki","https://baike.baidu.com/item/健力宝")]},

 {"id":"1990-01-01-li-ning-brand-founded","date":"1990-01-01","date_accuracy":"year","date_confidence":"verified",
  "title":"李宁退役后创立「李宁牌」运动品牌","category":"company","region":"cn",
  "milestone":False,
  "summary_30s":"1990年，体操王子李宁退役后创立李宁公司，品牌服装亮相北京亚运会圣火传递。",
  "impact":"中国运动员转型企业家的标杆诞生，国产运动品牌与「国家荣耀」叙事深度绑定。",
  "aftermath":"李宁公司2004年在香港上市，2018年「中国李宁」登陆纽约时装周掀起国潮，长期位居国产运动品牌前列。",
  "tags":[],"sources":[S("wiki","https://zh.wikipedia.org/wiki/李宁_(品牌)")]},

 {"id":"1994-04-17-jia-a-kickoff","date":"1994-04-17","date_accuracy":"exact","date_confidence":"verified",
  "title":"甲A联赛揭幕，中国足球职业化元年","category":"milestone","region":"cn",
  "milestone":True,
  "summary_30s":"1994年4月17日，全国足球甲级队A组联赛揭幕，中国体育第一个真正意义的职业联赛开踢。",
  "impact":"球员注册转会、俱乐部制、商业冠名（万宝路冠名首届）同步落地，中国体育从举国体制迈出职业化第一步。",
  "aftermath":"甲A十年间「工体不败」「成都金牌球市」点燃全民足球热，2004年改制为中超；职业化红利与假赌黑阴影交替成为中国足球30年主题。",
  "tags":[],"sources":[S("wiki","https://zh.wikipedia.org/wiki/中国足球甲A联赛")]},

 {"id":"1994-01-01-sports-lottery-national","date":"1994-01-01","date_accuracy":"year","date_confidence":"verified",
  "title":"体育彩票全国统一发行","category":"economy","region":"cn",
  "milestone":False,
  "summary_30s":"1994年，国家体委体育彩票管理中心成立，体育彩票开始全国统一发行。",
  "impact":"「取之于民、用之于体」的彩票公益金成为全民健身与竞技体育的重要资金来源，体育产业有了自我造血渠道。",
  "aftermath":"体彩年销量此后突破两千亿元，竞彩、即开票体系支撑起赛事运营、场馆建设与奥运争光计划的庞大开支。",
  "tags":[],"sources":[S("wiki","https://baike.baidu.com/item/中国体育彩票")]},

 {"id":"2004-05-01-csl-first-season","date":"2004-05-01","date_accuracy":"month","date_confidence":"verified",
  "title":"中超联赛元年，甲A改制为中超","category":"economy","region":"cn",
  "milestone":False,
  "summary_30s":"2004年5月，中国足球超级联赛揭幕——运营十年的甲A改制为中超。",
  "impact":"联赛准入、俱乐部股权、青训梯队标准重新划定，中国足球职业联赛进入新品牌周期。",
  "aftermath":"中超此后经历假赌黑整治、金元时代与限薪中性名改革，商业价值大起大落，但始终保持中国体育第一联赛体量。",
  "tags":[],"sources":[S("wiki","https://zh.wikipedia.org/wiki/中国足球协会超级联赛")]},

 {"id":"2009-08-01-anta-fila-china","date":"2009-08-01","date_accuracy":"month","date_confidence":"verified",
  "title":"安踏收购FILA中国业务，多品牌战略开端","category":"company","region":"cn",
  "milestone":False,
  "summary_30s":"2009年8月，安踏从百丽国际手中买下意大利品牌FILA的中国商标与经营权益。",
  "impact":"中国体育公司第一次系统运营国际中高端品牌，「单品牌+多品牌」矩阵成为行业竞争新范式。",
  "aftermath":"FILA中国此后营收破两百亿元成为安踏第二增长曲线，2022年安踏集团营收首超耐克中国，登顶中国运动品牌市场。",
  "tags":[],"sources":[S("wiki","https://baike.baidu.com/item/斐乐")]},

 {"id":"2013-11-09-evergrande-acl","date":"2013-11-09","date_accuracy":"exact","date_confidence":"verified",
  "title":"广州恒大首夺亚冠，中国俱乐部24年再登亚洲之巅","category":"milestone","region":"cn",
  "milestone":True,
  "summary_30s":"2013年11月9日，广州恒大天河主场1比1战平首尔FC，总比分战平凭客场进球首夺亚冠。",
  "impact":"中国俱乐部时隔24年重夺亚洲俱乐部最高荣誉，「金元足球」模式自此登上顶点，单场夺冠夜全国收视破亿。",
  "aftermath":"恒大2015年再夺亚冠并把俱乐部推上新三板，但母公司债务危机后俱乐部解散，金元时代落幕成为中国足球产业的分水岭。",
  "tags":[],"sources":[S("wiki","https://zh.wikipedia.org/wiki/2013年亚足联冠军联赛")]},

 {"id":"2014-10-20-doc-46-sports-industry","date":"2014-10-20","date_accuracy":"exact","date_confidence":"verified",
  "title":"国务院46号文：取消商业赛事审批，剑指5万亿体育产业","category":"milestone","region":"cn",
  "milestone":True,
  "summary_30s":"2014年10月20日，国务院印发《关于加快发展体育产业促进体育消费的若干意见》，取消商业性赛事活动审批。",
  "impact":"体育赛事从「办赛要批文」转向市场化，社会资本涌入赛事、版权、健身全产业链，5万亿元产业目标写入国家规划。",
  "aftermath":"马拉松、自行车、格斗等赛事数量此后呈几何级增长，中超80亿版权、体育小镇等热钱涌动，体育产业总规模2023年突破3.6万亿元。",
  "tags":[],"sources":[S("official","https://baike.baidu.com/item/关于加快发展体育产业促进体育消费的若干意见")]},

 {"id":"2015-02-01-keep-app-launch","date":"2015-02-01","date_accuracy":"month","date_confidence":"verified",
  "title":"Keep上线，健身走向移动互联","category":"product","region":"cn",
  "milestone":False,
  "summary_30s":"2015年2月，健身应用Keep上线——「自律给我自由」把健身课装进手机。",
  "impact":"居家健身与碎片化训练被App重新定义，健身人口由线下健身房扩展到数亿移动用户。",
  "aftermath":"Keep用户量破3亿后向硬件、内容、线下 Keepland 扩张，2023年登陆港交所成为「运动科技第一股」。",
  "tags":[],"sources":[S("wiki","https://baike.baidu.com/item/Keep")]},

 {"id":"2015-10-01-tihaodongli-8b-csl-rights","date":"2015-10-01","date_accuracy":"month","date_confidence":"verified",
  "title":"体奥动力80亿元拿下中超五年版权","category":"economy","region":"cn",
  "milestone":False,
  "summary_30s":"2015年10月，体奥动力以5年80亿元中标中超全媒体版权，价格为此前一年的20倍。",
  "impact":"中国体育版权价格一夜进入「亿元时代」，足球版权成为资本竞逐的硬通货。",
  "aftermath":"版权泡沫随后遭遇政策与市场双重回调（合同重签为10年110亿），乐视体育等烧钱玩家相继出局，「理性版权」成为行业共识。",
  "tags":[],"sources":[S("wiki","https://baike.baidu.com/item/体奥动力")]},

 {"id":"2019-01-28-wu-lei-espanyol","date":"2019-01-28","date_accuracy":"exact","date_confidence":"verified",
  "title":"武磊登陆西甲，中国球员重返五大联赛","category":"economy","region":"cn",
  "milestone":False,
  "summary_30s":"2019年1月28日，西甲西班牙人俱乐部官宣武磊加盟——中国球员时隔多年重返五大联赛。",
  "impact":"武磊效应直接拉动西班牙人母公司股价与中国转播、球衣市场，留洋再度成为国内球员的价值标杆。",
  "aftermath":"武磊效力三年多出场百余次并攻破巴萨球门，2022年回归海港；其后李刚仁、久保建英等东亚留洋潮中，武磊仍是中重量的商业参照。",
  "tags":[],"sources":[S("wiki","https://zh.wikipedia.org/wiki/武磊")]},

 {"id":"2018-12-07-anta-amer-sports-bid","date":"2018-12-07","date_accuracy":"exact","date_confidence":"verified",
  "title":"安踏牵头财团46亿欧元要约收购亚玛芬体育","category":"company","region":"cn",
  "milestone":False,
  "summary_30s":"2018年12月7日，安踏联合方源资本等发起对芬兰亚玛芬体育（Amer Sports）46亿欧元要约收购。",
  "impact":"中国体育企业史上最大海外并购落地，始祖鸟、萨洛蒙、威尔胜等品牌被收入中国公司囊中。",
  "aftermath":"收购2019年完成交割，始祖鸟借「中产户外」风潮在中国爆发式增长，亚玛芬2025年2月登陆纽交所，市值一度超安踏。",
  "tags":[],"sources":[S("wiki","https://zh.wikipedia.org/wiki/亚玛芬体育")]},

 {"id":"2020-06-20-cba-restart","date":"2020-06-20","date_accuracy":"exact","date_confidence":"verified",
  "title":"CBA复赛，疫情后国内首个重启的大型联赛","category":"economy","region":"cn",
  "milestone":False,
  "summary_30s":"2020年6月20日，CBA在东莞、青岛以赛会制空场复赛——疫情后国内第一个重启的全国性大型职业联赛。",
  "impact":"复赛为全球职业体育提供了防疫办赛的「中国方案」，也保住了联赛赞助与转播基本盘。",
  "aftermath":"中超同年7月跟进复赛，赛会制、空场、赛区闭环成为全球赛事标准动作，体育产业疫后重启自此起步。",
  "tags":[],"sources":[S("wiki","https://baike.baidu.com/item/2019－2020赛季中国男子篮球职业联赛")]},

 {"id":"2022-01-01-300m-ice-snow","date":"2022-01-01","date_accuracy":"month","date_confidence":"verified",
  "title":"「带动三亿人参与冰雪运动」目标宣告达成","category":"economy","region":"cn",
  "milestone":False,
  "summary_30s":"2022年1月，国家统计局发布数据称全国冰雪运动参与人数达3.46亿——北京冬奥会前夕「三亿人上冰雪」目标宣告达成。",
  "impact":"冰雪运动从东北区域爱好变为全国性消费，滑雪场、室内雪场、冰雪装备制造全链条扩容。",
  "aftermath":"2024-2025雪季冰雪旅游人次与消费屡创新高，哈尔滨「尔滨」爆红、滑雪装备国产品牌崛起，冰雪经济被写入地方产业规划。",
  "tags":[],"sources":[S("official","https://baike.baidu.com/item/三亿人参与冰雪运动")]},

 {"id":"2023-05-13-cun-chao-viral","date":"2023-05-13","date_accuracy":"exact","date_confidence":"verified",
  "title":"贵州「村超」爆红，草根足球成现象级文旅IP","category":"society","region":"cn",
  "milestone":False,
  "summary_30s":"2023年5月13日，贵州榕江县「村超」揭幕，村民组队的业余足球赛短视频刷屏全网。",
  "impact":"无资本、无明星的草根赛事单场观众数万、全网播放数百亿次，证明体育的原始快乐与地方文旅可以互相成就。",
  "aftermath":"榕江县此后接待游客量与旅游收入成倍增长，「村超」「村BA」被写进地方两会报告，各地竞相复制「村字号」赛事。",
  "tags":[],"sources":[S("wiki","https://zh.wikipedia.org/wiki/村超")]},

 {"id":"2023-07-12-keep-ipo","date":"2023-07-12","date_accuracy":"exact","date_confidence":"verified",
  "title":"Keep港交所上市，「运动科技第一股」诞生","category":"company","region":"cn",
  "milestone":False,
  "summary_30s":"2023年7月12日，Keep在港交所挂牌——中国最大的线上健身平台完成上市。",
  "impact":"健身App从烧钱流量生意进入盈利验证期，运动科技成为消费赛道独立板块。",
  "aftermath":"上市后Keep收缩硬件与线下业务聚焦自有品牌+会员订阅，行业普遍转向「内容+电商」的健康盈利模型。",
  "tags":[],"sources":[S("wiki","https://baike.baidu.com/item/Keep")]},

 {"id":"2024-08-03-zheng-qinwen-gold","date":"2024-08-03","date_accuracy":"exact","date_confidence":"verified",
  "title":"郑钦文巴黎奥运网球女单夺金，亚洲首人","category":"milestone","region":"cn",
  "milestone":True,
  "summary_30s":"2024年8月3日，21岁的郑钦文在罗兰·加洛斯直落两盘夺冠——亚洲选手首夺奥运网球单打金牌。",
  "impact":"中国网球商业价值被重新定价，郑钦文赛后代言费跻身全球女运动员前列，青少年网球培训报名量激增。",
  "aftermath":"武汉、京山等地网球场馆与赛事经济升温，「郑钦文效应」带动网球装备、赛事转播与网球场预订全面上涨。",
  "tags":[],"sources":[S("wiki","https://zh.wikipedia.org/wiki/郑钦文")]},
]

D[:] = [e for e in D if e.get('detail') or True]
# 本层用 summary_30s 承担摘要，detail 由 summary_30s+impact+aftermath 覆盖的条目补一个合并detail
for e in D:
    if not e.get('detail'):
        e['detail'] = e['summary_30s'] + ' ' + e['impact'] + ' ' + e['aftermath']
    e.pop('region_note', None)
D[:] = [e for e in D if len(e['detail'])>20 and e.get('sources')]
json.dump(D, open('data/events/.parts/sportsbiz-batch1.json','w'), ensure_ascii=False, indent=0)
print(f"sportsbiz batch1: {len(D)} 条")
