#!/usr/bin/env python3
"""世家抽取器：从编年库 data/*.json 按关键词抽取既有条目 → data/entities/.extracts/<id>.json
这些条目的日期与来源已在编年史管线中核实，是世家时间线的第一手原材料。
用法：python3 scripts/entity_extract.py [entity_id]（缺省抽全部）"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "events")
OUT = os.path.join(ROOT, "data", "entities", ".extracts")
CAP = 40

ENTITIES = {
    "tencent": ["腾讯", "OICQ", "QQ空间", "微信"],
    "alibaba": ["阿里巴巴", "淘宝", "支付宝", "蚂蚁", "天猫", "双十一"],
    "baidu": ["百度", "竞价排名", "贴吧"],
    "netease": ["网易"],
    "sina": ["新浪", "微博"],
    "sohu": ["搜狐"],
    "jd": ["京东", "京东商城", "多媒体网"],
    "bytedance": ["字节", "抖音", "今日头条", "TikTok"],
    "xiaomi": ["小米", "MIUI", "红米", "米聊"],
    "shanda": ["盛大", "传奇"],
    "kingsoft": ["金山", "WPS", "求伯君"],
    "8848": ["8848", "珠穆朗玛"],
    "smth": ["水木", "SMTH", "BBS"],
    "tianya": ["天涯"],
    "mop": ["猫扑", "大杂烩"],
    "xici": ["西祠"],
    "rongshuxia": ["榕树下"],
    "chinaren": ["ChinaRen", "chinaren", "同学录"],
    "renren": ["人人网", "校内网"],
    "tieba": ["贴吧"],
    "douban": ["豆瓣"],
    "bilibili": ["哔哩", "B站", "bilibili"],
    "zhihu": ["知乎"],
    "cstnet": ["中国科技网", "CSTNet", "全功能接入", "中关村地区教育与科研示范网络", "NCFC"],
    "chinanet": ["ChinaNet", "公用计算机互联网", "邮电部"],
    "cernet": ["CERNET", "教育科研计算机网"],
    "cnnic": ["CNNIC", "互联网络信息中心", "互联网发展状况统计报告"],
    "isc": ["互联网协会"],
    "wanwang": ["万网", "域名注册"],
    "netscape": ["网景", "Netscape", "浏览器大战"],
    "yahoo": ["雅虎", "Yahoo"],
    "icq": ["ICQ"],
    "geocities": ["GeoCities"],
    # ---- 二批（2026-10-23）----
    "eachnet": ["易趣"],
    "dangdang": ["当当"],
    "vancl": ["凡客"],
    "giantnet": ["巨人网络", "巨人集团", "征途"],
    "the9": ["第九城市", "九城"],
    "ourgame": ["联众"],
    "kuaishou": ["快手"],
    "meituan": ["美团", "大众点评"],
    "didi": ["滴滴", "嘀嘀"],
    "ctrip": ["携程"],
    "hupu": ["虎扑"],
    "nga": ["NGA", "艾泽拉斯国家地理"],
    "guokr": ["果壳"],
    "kaidi": ["凯迪"],
    "aol": ["AOL", "美国在线"],
    "msn-messenger": ["MSN"],
    "myspace": ["MySpace", "聚友"],
    "vine": ["Vine"],
    "orkut": ["Orkut"],
    # ---- 三批（2026-10-23）----
    "sogou": ["搜狗"],
    "ofo": ["ofo", "小黄车"],
    "leshi": ["乐视", "LeEco"],
    "wikipedia": ["维基百科", "Wikipedia"],
    "internetarchive": ["Internet Archive", "互联网档案馆"],
    "napster": ["Napster"],
    "digg": ["Digg"],
    "reddit": ["Reddit", "reddit"],
    # ---- 四批（2026-10-23 晚，论坛社区黄金时代+世界平台）----
    "qidian": ["起点中文网", "起点", "阅文"],
    "jjwxc": ["晋江", "晋江文学城"],
    "hjsm": ["幻剑书盟"],
    "17173": ["17173"],
    "yinghaiwei": ["瀛海威"],
    "kaixin001": ["开心网", "开心001", "偷菜"],
    "fanfou": ["饭否"],
    "blogchina": ["博客中国", "博客网", "方兴东"],
    "xunlei": ["迅雷", "迅雷下载"],
    "verycd": ["VeryCD", "电驴", "ed2k"],
    "huajun": ["华军", "华军软件园"],
    "zol": ["中关村在线", "ZOL"],
    "autohome": ["汽车之家"],
    "eastmoney": ["东方财富", "股吧"],
    "wandoujia": ["豌豆荚", "应用分发"],
    "monternet": ["移动梦网", "梦网"],
    "google": ["谷歌", "Google"],
    "youtube": ["YouTube", "油管"],
    "facebook": ["Facebook", "Facebook", "Meta"],
    "twitter": ["Twitter", "推特"],
    "netflix": ["Netflix", "网飞"],
    "amazon": ["Amazon", "亚马逊"],
    "skype": ["Skype"],
    "friendster": ["Friendster"],
}


def load_all():
    out = []
    for f in sorted(glob.glob(os.path.join(DATA, "*.json"))):
        name = os.path.basename(f)[:-5]
        layer = re.sub(r"^\d{4}(?:-\d{4})*-?", "", name) or "main"
        try:
            data = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        for e in (data if isinstance(data, list) else data.get("events", [])):
            if not isinstance(e, dict):
                continue
            out.append({
                "id": e.get("id", ""),
                "date": e.get("date", ""),
                "layer": layer,
                "title": e.get("title", ""),
                "summary": e.get("summary_30s", e.get("summary", "")),
                "detail": e.get("detail", ""),
                "sources": e.get("sources", []),
            })
    return out


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    pool = load_all()
    os.makedirs(OUT, exist_ok=True)
    done, empty = 0, []
    for eid, kws in ENTITIES.items():
        if only and eid != only:
            continue
        hits = []
        for e in pool:
            blob = (e["title"] + e["summary"] + e["detail"]).lower()
            if any(k.lower() in blob for k in kws):
                hits.append(e)
        hits.sort(key=lambda x: x["date"])
        if len(hits) > CAP:
            hits = hits[:25] + hits[-15:]  # 保留兴衰两端：早期起点 + 近期节点
        path = os.path.join(OUT, f"{eid}.json")
        json.dump(hits, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        done += 1
        if not hits:
            empty.append(eid)
        print(f"{eid}: {len(hits)} 条 → {os.path.relpath(path, ROOT)}")
    print(f"\n✓ 抽取 {done} 个主体；0 命中需纯网络补源: {', '.join(empty) if empty else '无'}")


if __name__ == "__main__":
    main()
