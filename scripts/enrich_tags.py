#!/usr/bin/env python3
"""全库标签体系化：为每条事件补充三层体系标签。
1) 领域标签：按文件层推导（影视/音乐/游戏/科学/航天/体育/媒介/数字考古/航空/探险/世界纪录/二次元）
2) 大类标签：按 category 映射（里程碑/互联网/科技/硬件/公司/产品/国家/国际/社会/文化/经济）
3) 主题标签：按关键词规则从 title+summary+tags 派生（人工智能/自然灾害/恐怖袭击/资本市场…）
已有标签保留，去重后写回。幂等：重复运行无副作用。
"""
import json
import re
import glob
from pathlib import Path

EV = Path(__file__).parent.parent / "data" / "events"

LAYER_TAGS = {
    "film": "影视", "music": "音乐", "games": "游戏", "games2": "游戏",
    "science": "科学", "space": "航天", "sports": "体育", "media": "媒介",
    "wayback": "数字考古", "aviation": "航空", "exploration": "探险",
    "records": "世界纪录", "anime": "二次元", "railways": "铁路",
    "disasters": "灾难", "autos": "汽车", "telecom": "通信", "medical": "医疗健康", "food": "饮食",
}
CATEGORY_TAGS = {
    "milestone": "里程碑", "internet": "互联网", "tech": "科技", "hardware": "硬件",
    "company": "公司", "product": "产品", "national": "国家", "world": "国际",
    "society": "社会", "culture": "文化", "economy": "经济",
}

# 主题标签规则：(标签, 关键词列表) —— 关键词在 title/summary/tags 中命中即加
THEME_RULES = [
    ("人工智能", ["人工智能", "AI", "大模型", "ChatGPT", "GPT", "AlphaGo", "机器人", "OpenAI", "deepseek", "DeepSeek", "文心", "通义"]),
    ("航天", ["火箭", "卫星", "空间站", "月球", "登月", "火星", "载人", "神舟", "嫦娥", "天问", "NASA", "SpaceX", "飞船", "发射"]),
    ("自然灾害", ["地震", "洪水", "暴雨", "台风", "飓风", "海啸", "野火", "山火", "泥石流", "干旱", "火山"]),
    ("恐怖袭击", ["恐怖袭击", "恐袭", "爆炸案", "爆炸事件", "人质", "圣战", "ISIS", "基地组织"]),
    ("资本市场", ["上市", "IPO", "股灾", "崩盘", "熔断", "牛市", "暴跌", "市值", "纳斯达克", "纽交所", "金融危机", "央行", "加息", "降息"]),
    ("芯片", ["芯片", "半导体", "晶圆", "光刻", "台积电", "中芯", "处理器", "制程"]),
    ("电竞", ["电竞", "英雄联盟", "S赛", "王者荣耀", "DOTA", "Faker", "电竞赛"]),
    ("军事与战争", ["战争", "入侵", "导弹", "空袭", "军队", "轰炸", "航母", "北约", "停火", "武器"]),
    ("医学", ["疫苗", "病毒", "癌症", "基因", "FDA", "临床", "医院", "疾病", "艾滋病", "药"]),
    ("体育大赛", ["奥运", "冬奥会", "世界杯", "亚运会", "大满贯", "世锦赛", "开幕式"]),
    ("探险", ["珠峰", "登顶", "登山", "极地", "南极", "北极", "深海", "马里亚纳", "洞穴", "环球", "漂流"]),
    ("世界纪录", ["世界纪录", "吉尼斯", "基尼斯", "最快", "最高纪录"]),
    ("二次元", ["动画", "漫画", "漫展", "Cosplay", "cos", "虚拟偶像", "声优", "Jump", "宫崎骏", "吉卜力", "B站", "番剧", "剧场版"]),
    ("能源与气候", ["气候", "碳排放", "碳中和", "石油", "油价", "核电", "光伏", "风电", "新能源", "能源"]),
    ("通信", ["5G", "4G", "3G", "宽带", "光纤", "电话", "运营商", "基站", "微信", "QQ", "短信"]),
    ("交通", ["高铁", "铁路", "地铁", "公路", "汽车", "电动车", "航空", "航线", "港口", "大桥"]),
    ("教育", ["高考", "大学", "学校", "教育", "义务教育", "高校", "招生"]),
    ("政策法规", ["条例", "法案", "立法", "政策", "意见", "白皮书", "国务院", "人大", "中央"]),
    ("社会案件", ["案", "判刑", "死刑", "被捕", "诈骗", "遇害", "遇难", "判决", "庭审"]),
    ("灾难事故", ["事故", "矿难", "沉船", "踩踏", "海难", "核事故", "火灾", "空难", "爆炸", "坍塌", "脱轨"]),
    ("文化出口", ["出海", "全球", "海外", "国际化"]),
]


def derive_theme(e):
    text = e.get("title", "") + e.get("summary_30s", "") + " ".join(e.get("tags", []))
    hits = []
    for tag, kws in THEME_RULES:
        for kw in kws:
            if kw in text:
                hits.append(tag)
                break
    return hits


def main():
    changed_files = 0
    added_total = 0
    for p in sorted(EV.glob("*.json")):
        fn = p.name
        if fn.startswith("."):
            continue
        layer = fn.replace(".json", "")
        layer_tag = None
        for k, v in LAYER_TAGS.items():
            if layer == k or layer.endswith("-" + k) or layer.startswith(k):
                layer_tag = v
                break
        d = json.loads(p.read_text(encoding="utf-8"))
        dirty = False
        for e in d:
            tags = list(e.get("tags", []))
            have = set(tags)
            add = []
            if layer_tag and layer_tag not in have:
                add.append(layer_tag)
            cat_tag = CATEGORY_TAGS.get(e.get("category"))
            if cat_tag and cat_tag not in have and cat_tag not in add:
                add.append(cat_tag)
            for t in derive_theme(e):
                if t not in have and t not in add:
                    add.append(t)
            if add:
                # 体系标签插到最前，保持原有标签在后
                e["tags"] = add + tags
                added_total += len(add)
                dirty = True
        if dirty:
            p.write_text(json.dumps(d, ensure_ascii=False, indent=0), encoding="utf-8")
            changed_files += 1
            print(f"✓ {fn}: 体系标签已补充")
    print(f"完成：{changed_files} 个文件，新增标签 {added_total} 个")


if __name__ == "__main__":
    main()
