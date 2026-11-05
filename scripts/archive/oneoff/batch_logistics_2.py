#!/usr/bin/env python3
# 物流快递层 · 第二批（桐庐帮补全/快递柜/数据之争/新规）
import json, os
os.makedirs('data/events/.parts', exist_ok=True)

def S(t, u):
    return {"type": t, "url": u, "title": t}

D = [
 {"id":"1999-08-08-yunda-founding","date":"1999-08-08","date_accuracy":"exact","date_confidence":"verified",
  "title":"韵达创立：桐庐帮的第二块砖","category":"company","region":"cn",
  "milestone":False,
  "summary_30s":"1999年8月8日，聂腾云在上海创办韵达快运——申通创始人弟弟的第二次创业。",
  "impact":"桐庐快递家族的版图继续扩张，「一家人的生意」成为中国快递业最独特的地缘样本。",
  "aftermath":"韵达2017年借壳上市，此后与中通在加盟制规模上轮番争夺第二名；桐庐帮（申通、韵达、圆通、中通）长期占据中国快递市场半壁江山。",
  "tags":[],"sources":[S("wiki","https://baike.baidu.com/item/韵达快递")]},

 {"id":"2002-05-08-zto-founding","date":"2002-05-08","date_accuracy":"exact","date_confidence":"verified",
  "title":"中通创立：桐庐帮的电商时代拼图","category":"company","region":"cn",
  "milestone":False,
  "summary_30s":"2002年5月8日，赖梅松在上海创办中通快递——桐庐帮里最晚起家却后来居上的一家。",
  "impact":"中通以「同建共享」加盟模式快速铺网，日后成为电商件市场占有率第一的快递公司。",
  "aftermath":"中通2016年赴美上市、2020年回港二次上市，连续多年蝉联行业单量冠军；桐庐帮四家由此聚齐中国快递江湖的主角阵容。",
  "tags":[],"sources":[S("wiki","https://baike.baidu.com/item/中通快递")]},

 {"id":"2012-11-01-double11-parcel-flood","date":"2012-11-01","date_accuracy":"month","date_confidence":"verified",
  "title":"「双11」快递洪峰首次成为社会话题","category":"economy","region":"cn",
  "milestone":False,
  "summary_30s":"2012年11月，双11单日产生包裹近2000万件，「爆仓」登上媒体头条——快递第一次以「社会基础设施」身份进入公众视野。",
  "impact":"电商与快递的运力矛盾被公开化，「快递爆仓」成为年度热词，倒逼行业产能与信息系统升级。",
  "aftermath":"此后各年双11包裹量指数级增长而配送时效反而缩短，自动化分拣、智能路由与前置仓模式被逼了出来。",
  "tags":[],"sources":[S("wiki","https://baike.baidu.com/item/快递爆仓")]},

 {"id":"2015-04-08-fengchao-founded","date":"2015-04-08","date_accuracy":"exact","date_confidence":"verified",
  "title":"丰巢成立：智能快递柜「最后一百米」开战","category":"company","region":"cn",
  "milestone":False,
  "summary_30s":"2015年4月8日，顺丰联合申通、中通、韵达等共同注资成立丰巢科技，布局智能快递柜。",
  "impact":"「快递柜」作为末端配送方案被五大快递公司联合押注，最后一百米从人送货升级为人取货。",
  "aftermath":"菜鸟驿站与丰巢随后在末端入口展开多年竞合，快递柜从免费便利变成收费争议现场，家门口的格子成为电商与用户的博弈场。",
  "tags":[],"sources":[S("wiki","https://baike.baidu.com/item/丰巢")]},

 {"id":"2016-10-27-zto-nasdaq-ipo","date":"2016-10-27","date_accuracy":"exact","date_confidence":"verified",
  "title":"中通登陆纽交所：中国快递第一股出海","category":"company","region":"cn",
  "milestone":False,
  "summary_30s":"2016年10月27日，中通快递在纽交所挂牌——桐庐帮率先敲开美国资本市场大门。",
  "impact":"快递公司密集上市潮开启，民营快递从家族生意进入公开市场估值时代。",
  "aftermath":"中通上市后圆通、申通、韵达、顺丰在一年内全部登陆资本市场，规模竞争与价格战同步升级，行业集中度快速提升。",
  "tags":[],"sources":[S("wiki","https://baike.baidu.com/item/中通快递")]},

 {"id":"2017-06-01-sf-cainiao-data-war","date":"2017-06-01","date_accuracy":"exact","date_confidence":"verified",
  "title":"顺丰与菜鸟互相封杀数据接口","category":"company","region":"cn",
  "milestone":False,
  "summary_30s":"2017年6月1日，顺丰关闭对菜鸟的数据回传接口，菜鸟随即下线顺丰取件入口——两大物流巨头公开互撕。",
  "impact":"用户在淘宝上突然发不了顺丰快递，「数据所有权归谁」第一次成为全民讨论的产业问题。",
  "aftermath":"国家邮政局连夜协调次日恢复互通；此后数据安全、平台开放与快递企业独立性的边界持续被重新划定。",
  "tags":[],"sources":[S("wiki","https://baike.baidu.com/item/顺丰菜鸟之争")]},

 {"id":"2020-04-12-fengchao-fee-controversy","date":"2020-04-12","date_accuracy":"month","date_confidence":"verified",
  "title":"丰巢超时收费风波：免费快递柜走向终结","category":"economy","region":"cn",
  "milestone":False,
  "summary_30s":"2020年4月，丰巢宣布对超时包裹收费，杭州等多地小区业主委员会发起抵制并暂停快递柜。",
  "impact":"「快递不送上门」「柜子凭什么收费」引爆全民讨论，末端配送的服务标准与成本分摊被摆上台面。",
  "aftermath":"监管约谈后丰巢调整收费规则并延长免费时长，快递员「擅自投柜」从此成为投诉重灾区，为2024年新规埋下伏笔。",
  "tags":[],"sources":[S("wiki","https://baike.baidu.com/item/丰巢")]},

 {"id":"2021-05-28-jd-logistics-ipo","date":"2021-05-28","date_accuracy":"exact","date_confidence":"verified",
  "title":"京东物流港股上市：自建物流的资本正名","category":"company","region":"cn",
  "milestone":False,
  "summary_30s":"2021年5月28日，京东物流在港交所上市——刘强东坚持十四年的自建物流体系独立敲钟。",
  "impact":"「重资产物流不赚钱」的行业偏见被改写，一体化供应链成为物流上市的新叙事。",
  "aftermath":"京东物流此后加速收购德邦、跨越速运扩张版图，仓配一体模式与电商件加盟模式的中国物流双轨格局就此定型。",
  "tags":[],"sources":[S("wiki","https://baike.baidu.com/item/京东物流")]},

 {"id":"2021-07-08-courier-rights-policy","date":"2021-07-08","date_accuracy":"exact","date_confidence":"verified",
  "title":"七部门发文保障快递员群体权益","category":"national","region":"cn",
  "milestone":False,
  "summary_30s":"2021年7月8日，交通运输部等七部门印发意见，要求保障快递员合理报酬、社保与劳动强度上限。",
  "impact":"数百万快递员「以罚代管」「层层压价」的生存现状进入政策视野，新就业形态劳动者权益成为国家议题。",
  "aftermath":"派费上调、工伤社保试点与算法取中要求随后落地，快递员与外卖骑手共同推动平台用工监管框架成型。",
  "tags":[],"sources":[S("wiki","https://baike.baidu.com/item/快递员")]},

 {"id":"2024-03-01-express-new-rules","date":"2024-03-01","date_accuracy":"exact","date_confidence":"verified",
  "title":"新版《快递市场管理办法》施行：未经同意不得擅放驿站","category":"national","region":"cn",
  "milestone":False,
  "summary_30s":"2024年3月1日，修订后的《快递市场管理办法》施行，快递员未经用户同意擅自投放驿站或快递柜最高可罚3万元。",
  "impact":"「快递要不要送上门」的多年争议获得规则答案，末端配送「最后一百米」的选择权交还用户。",
  "aftermath":"新规执行初期快递员工作量与派费矛盾集中爆发，驿站、快递柜与上门配送并行的混合末端模式成为行业新常态。",
  "tags":[],"sources":[S("wiki","https://baike.baidu.com/item/快递市场管理办法")]},
]

D[:] = [e for e in D if e.get('detail') or True]
for e in D:
    if not e.get('detail'):
        e['detail'] = e['summary_30s'] + ' ' + e['impact'] + ' ' + e['aftermath']
D[:] = [e for e in D if len(e['detail'])>20 and e.get('sources')]
json.dump(D, open('data/events/.parts/logistics-batch2.json','w'), ensure_ascii=False, indent=0)
print(f"logistics batch2: {len(D)} 条")
