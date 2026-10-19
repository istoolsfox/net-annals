#!/usr/bin/env python3
"""主会话补录批次二十三：1980 年代末大事件 3 条（URL 已全部预验证 200）。"""
import json
from pathlib import Path

EV = Path(__file__).parent.parent / "data" / "events"


def e(id, date, acc, conf, title, cat, region, milestone, s30, detail, impact, after, sources, tags):
    return {"id": id, "date": date, "date_accuracy": acc, "date_confidence": conf,
            "title": title, "category": cat, "region": region, "milestone": milestone,
            "summary_30s": s30, "detail": detail, "impact": impact, "aftermath": after,
            "sources": [{"title": t, "url": u, "type": ty} for t, u, ty in sources], "tags": tags}


E1 = [
    e("1987-10-19-black-monday",
      "1987-10-19", "exact", "verified",
      "『黑色星期一』：道指单日暴跌22.6%的世纪股灾",
      "economy", "world", True,
      "1987年10月19日，道琼斯指数单日暴跌508点（-22.6%），创下迄今无人打破的最大单日百分比跌幅——美股一天蒸发约5000亿美元市值，恐慌席卷全球：香港、悉尼、伦敦、东京接连熔断。这场『黑色星期一』没有引发大萧条2.0，却永久改写了全球股市的技术架构。",
      "成因至今是金融学悬案：组合保险（portfolio insurance）的机械性抛售、程序化交易、估值过高、美元贬值的批评（财长贝克的一句话被指扣动扳机）叠加共振。救市方式开创新纪元：美联储格林斯潘（上任仅两个月）声明『随时提供流动性』+开放贴现窗——『央行兜底』（Fed put）的雏形就此确立。制度遗产更深远：美国推出『熔断机制』（circuit breaker，1988）、全球交易所反思程序交易、『股灾-央行-流动性』三角成为此后每一次危机（1998 LTCM、2008、2020 熔断四次触发）的标准剧本。黑色星期一也是中国的『先声』：1990年沪深交易所设立时，涨跌停板制度直接借鉴了这次股灾的教训。",
      "现代金融市场风险管理的原点事件，『央行最后贷款人』从理论变成肌肉记忆。",
      "熔断机制历经1997、2015（中国）、2020（美股四次）多次实战；组合保险的变体（风险平价、Vol 目标）仍在周期性引爆。",
      [("Wikipedia: Black Monday (1987)", "https://en.wikipedia.org/wiki/Black_Monday_(1987)", "wiki")],
      ["黑色星期一", "股灾", "熔断", "格林斯潘"]),

    e("1988-09-17-seoul-olympics",
      "1988-09-17", "exact", "verified",
      "汉城奥运会开幕：民主化韩国的世界成人礼",
      "world", "world", True,
      "1988年9月17日，第24届奥运会在汉城（首尔）开幕——奥运会第一次来到亚洲发展中国家（此前只有东京1964）。『手拉手』（Hand in Hand）唱遍全球，这个曾靠军政府维持秩序的国家，以一场盛会把『汉江奇迹』推上世界舞台。",
      "汉城奥运的意义远超体育：它是在野党争取下对军政府『还政于民』的倒计时——开幕前一年，全斗焕被迫接受总统直选（1987年六月民主运动），卢泰愚当选后和平交接，奥运会成为韩国民主化与国际化的双重加冕。政治抵制潮虽未再现（朝鲜联合办赛失败后抵制，古巴埃塞俄比亚等6国缺席），但本·约翰逊兴奋剂丑闻（破百米纪录后被查）开启了奥运药检的严打时代。商业面：三星以本土赞助商身份走向世界（此后成为奥运 TOP 赞助商），韩流的文化输出以这次全球收视（覆盖22亿人）为原点。对中国观众，这是记忆中的第一次『熬夜看奥运』——央视转播让『友好运动会』之外的国际体育真正进入中国日常。",
      "奥运与发展中国家民主化的联动样本，韩国国家品牌的奠基仪式。",
      "此后首尔成为 G20 峰会与核安全峰会举办地；『汉城』2005年更名『首尔』。",
      [("Wikipedia: 1988 Summer Olympics", "https://en.wikipedia.org/wiki/1988_Summer_Olympics", "wiki")],
      ["汉城奥运", "韩国", "民主化", "手拉手"]),

    e("1993-09-13-oslo-accord",
      "1993-09-13", "exact", "verified",
      "《奥斯陆协议》签署：以巴在白宫草坪握手",
      "world", "world", True,
      "1993年9月13日，白宫南草坪，拉宾与阿拉法特在克林顿注视下握手——以色列与巴解组织相互承认，签署《奥斯陆一号协议》。『土地换和平』的蓝图让全世界以为中东百年的死结看到了解开的时刻。",
      "协议的秘密谈判在挪威进行（贝妇人和拉森主持，『奥斯陆频道』），核心安排是分阶段自治：加沙与杰里科先行、5年内谈最终地位（耶路撒冷、难民、定居点、边界）。诺贝尔和平奖次年授予三人（拉宾、佩雷斯、阿拉法特）。悲剧接踵而至：1995年拉宾被以色列极端分子刺杀，1996-2000年谈判在定居点扩张与恐怖袭击的双向拉扯中搁浅，2000年戴维营破局与第二次巴勒斯坦大起义（Intifada）彻底终结和平进程——奥斯陆框架名存实亡，哈马斯的崛起与加沙-西岸的分裂定格至今。它留下的不是和平，而是『和平最接近的一次』的坐标：此后每一轮巴以危机（包括2023年10月7日后的加沙战争），人们都会回到1993年9月13日那声握手，追问究竟是哪个环节坏了。",
      "中东和平进程的历史最高水位，『两国方案』的制度化尝试与崩塌起点。",
      "拉宾遇刺30周年纪念中奥斯陆遗产仍被激烈争论；两国方案支持率降至历史低位。",
      [("Wikipedia: Oslo I Accord", "https://en.wikipedia.org/wiki/Oslo_I_Accord", "wiki")],
      ["奥斯陆协议", "拉宾", "阿拉法特", "巴以和平"]),
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
print("补录批次二十三完成")
