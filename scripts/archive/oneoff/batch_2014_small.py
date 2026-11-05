#!/usr/bin/env python3
"""续24轮：2014池残量2条（西吉踩踏/鲁甸地震）→ 2010-2014.json"""
import json, os
E = []
def add(id_, date, acc, conf, title, cat, mile, s30, detail, impact, after, sources, tags):
    assert len(s30) >= 60, f"{id_} summary {len(s30)}"
    assert 150 <= len(detail) <= 700, f"{id_} detail {len(detail)}"
    E.append({"id": id_, "date": date, "date_accuracy": acc, "date_confidence": conf,
        "title": title, "category": cat, "region": "cn", "milestone": mile,
        "summary_30s": s30, "detail": detail, "impact": impact, "aftermath": after,
        "sources": sources, "tags": tags})

add("2014-01-05-xiji-stampede",
    "2014-01-05", "exact", "verified",
    "宁夏西吉北大寺踩踏事故：14人遇难的宗教活动安全之殇",
    "society", False,
    "宁夏固原市西吉县北大寺发生信众聚集踩踏事故，共造成14人死亡、4人重伤，大型宗教聚集活动缺乏人流组织的安全问题随之进入公共治理视野。",
    "1月5日早晨，宁夏固原市西吉县北大寺举行宗教活动，大量信众涌入寺内一处狭窄坡道与台阶区域时发生拥挤踩踏，造成14人死亡、4人重伤。事发地点坡陡路窄、人流密度极高，缺乏分流与限流组织是伤亡扩大的直接原因。事故发生在回族聚居区的重要宗教节点，善后处理兼顾民族习俗与安全整改，地方政府此后对大型宗教聚集活动实行报备与安保评估制度。",
    "大型宗教聚集活动的拥挤踩踏风险首次以重大伤亡形式进入公共治理议程。",
    "固原市此后对重点场所实施人流预警与限流管理；与次年上海外滩踩踏共同推动全国大型群众性活动安全评估制度化。",
    [{"title": "维基百科：2014年中国大陆", "url": "https://zh.wikipedia.org/wiki/2014%E5%B9%B4%E4%B8%AD%E5%9B%BD%E5%A4%A7%E9%99%86", "type": "wiki"}],
    ["踩踏", "安全事故", "disaster_ok", "固原", "西吉", "宁夏"])

add("2014-08-03-ludian-earthquake",
    "2014-08-03", "exact", "verified",
    "鲁甸6.5级地震：617人遇难的乌蒙山浅源强震",
    "society", False,
    "云南昭通鲁甸县发生6.5级地震，造成617人遇难、112人失踪，浅源高烈度叠加山区土房是伤亡惨重的主因，为云南十四年来最重地震灾害。",
    "8月3日16时30分，云南省昭通市鲁甸县发生6.5级地震，震源深度仅12公里，极震区烈度达9度。震中位于乌蒙山连片特困山区，大量农村土坯与砖混自建房抗震性能极差，加之震区人口稠密，地震共造成617人遇难、112人失踪、3100余人受伤，是云南2000年以来伤亡最重的地震。牛栏江红石岩段因山体滑坡形成堰塞湖，威胁下游数千人，抢险排险持续多日。灾后重建采用「抗震民居」标准，农村住房抗震改造自此在云南全面推开。",
    "浅源强震与农村不抗震自建房叠加的伤亡模式再次警示，农村抗震改造成为灾后重建核心议题。",
    "鲁甸灾区一年内完成民房重建，牛栏江堰塞湖改造成水利枢纽；云南省此后推进农危改与抗震安居工程。",
    [{"title": "维基百科：2014年鲁甸地震", "url": "https://zh.wikipedia.org/wiki/2014%E5%B9%B4%E9%B2%81%E7%94%B8%E5%9C%B0%E9%9C%87", "type": "wiki"}],
    ["地震", "鲁甸", "disaster_ok", "昭通", "云南", "自然灾害"])
MAIN = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "events", "2010-2014.json")
db = json.load(open(MAIN, encoding="utf-8"))
ids = {e["id"] for e in db}
new = [e for e in E if e["id"] not in ids]
db.extend(new)
db.sort(key=lambda e: e["date"])
tmp = MAIN + ".tmp"
with open(tmp, "w", encoding="utf-8") as f:
    json.dump(db, f, ensure_ascii=False, indent=1)
os.replace(tmp, MAIN)
print(f"added={len(new)} skipped={len(E)-len(new)}")
