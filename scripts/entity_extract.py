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
}


def load_all():
    out = []
    for f in sorted(glob.glob(os.path.join(DATA, "*.json"))):
        layer = re.sub(r"^\d{4}-?", "", os.path.basename(f)[:-5]) or "main"
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
