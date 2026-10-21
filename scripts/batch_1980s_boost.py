# -*- coding: utf-8 -*-
import json, os

D = []

D.append({
 "id": "1986-08-03-first-bankrupt-factory",
 "date": "1986-08-03", "date_accuracy": "exact", "date_confidence": "single-source",
 "title": "沈阳防爆器械厂破产：新中国第一家破产的企业",
 "category": "economy", "region": "cn", "milestone": True,
 "summary_30s": "1986年8月3日，沈阳市工商行政管理部门宣布连续亏损多年的集体企业沈阳防爆器械厂破产，收缴其营业执照——新中国第一家正式破产的企业诞生。『社会主义企业也会倒闭』从此不再是禁忌话题。",
 "detail": "这家只有70多名职工的小厂连亏10年、负债率极高，沈阳市在集体企业破产试点中把它列为首家破产处理对象，职工通过劳务市场自谋出路。三个月后的1986年12月2日，《企业破产法（试行）》由全国人大常委会通过，1988年11月正式试行。破产在中国的破冰为国企改革提供了『退出机制』这一最难的制度拼图。",
 "impact": "企业第一次可以『合法死亡』，铁饭碗的绝对性被打开一道口子，市场经济的退出机制自此起步。",
 "aftermath": "破产法1988年试行后长期少用；2007年新企业破产法施行，市场主体退出制度逐步完善。",
 "sources": [{"title": "百度百科：企业破产法", "url": "https://baike.baidu.com/item/中华人民共和国企业破产法", "type": "wiki"}],
 "tags": ["社会", "企业破产", "国企改革", "1980s"]
})

D.append({
 "id": "1988-01-01-wangshuo-year",
 "date": "1988-01-01", "date_accuracy": "month", "date_confidence": "single-source",
 "title": "『王朔年』：一年四部小说同时搬上银幕",
 "category": "culture", "region": "cn", "milestone": False,
 "summary_30s": "1988年，王朔的《轮回》《顽主》《大喘气》《一半是火焰一半是海水》四部小说同年被搬上银幕，文学界惊呼『王朔年』。京味痞子文学与都市青年文化第一次合流，中国大众文化的新语法就此登场。",
 "detail": "王朔1984年以《空中小姐》出道，1987年起《浮出海面》《橡皮人》接连发表；1988年四部小说集中影视化，米家山、黄建新、叶大鹰等导演把『调侃崇高、解构严肃』的顽主们推上大银幕。此后王朔与冯小刚共同缔造了90年代贺岁片与《编辑部的故事》等大众文化巅峰，『我是流氓我怕谁』式的语言风格深刻影响网络时代的中文表达。",
 "impact": "大众文化与精英文化的分野第一次公开化，市井语言登堂入室成为中国流行文化的常用语料。",
 "aftermath": "王朔1990年代淡出创作转向幕后，其语言遗产在互联网时代的段子、吐槽文化中被反复回收。",
 "sources": [{"title": "百度百科：王朔", "url": "https://baike.baidu.com/item/王朔", "type": "wiki"}],
 "tags": ["文化", "王朔", "大众文化", "1980s"]
})

D.append({
 "id": "1988-05-01-karaoke-enters-china",
 "date": "1988-05-01", "date_accuracy": "month", "date_confidence": "single-source",
 "title": "卡拉OK进入中国：全民K歌的前夜",
 "category": "culture", "region": "cn", "milestone": False,
 "summary_30s": "1988年前后，卡拉OK机经广东进入中国，『伴唱机+空麦克风』的娱乐方式迅速从歌舞厅蔓延到街巷。此后十年，卡拉OK厅遍布全国城市，中国人第一次可以随时当众唱歌。",
 "detail": "卡拉OK1971年由日本人井上大佑发明，1980年代中期随三资企业进入广东，1988年前后北京的歌舞厅开始出现伴唱机。1990年代中国自产卡拉OK机遍地开花，VCD影碟机与伴唱碟让K歌进入家庭，1995年前后钱柜等KTV业态进入大陆，量贩式KTV随后崛起。从歌舞厅到家庭K歌再到移动端全民K歌，这条娱乐主线由1988年起步。",
 "impact": "大众娱乐从『观看』转向『参与』，K歌成为中国人最重要的社交方式之一。",
 "aftermath": "KTV行业2010年代达到巅峰后受政策与市场调整收缩；全民K歌、唱吧把K歌搬进手机，完成又一次形态迁移。",
 "sources": [{"title": "百度百科：卡拉OK", "url": "https://baike.baidu.com/item/卡拉OK", "type": "wiki"}],
 "tags": ["文化", "卡拉OK", "KTV", "大众娱乐"]
})

D.append({
 "id": "1988-06-01-yanwu-ad-campaign",
 "date": "1988-06-01", "date_accuracy": "month", "date_confidence": "single-source",
 "title": "『燕舞，燕舞，一片歌来一片情』：央视广告的全民记忆",
 "category": "culture", "region": "cn", "milestone": False,
 "summary_30s": "1988年前后，江苏盐城燕舞牌收录机的电视广告唱遍大江南北：小伙子抱着吉他唱出『一片歌来一片情』。这条广告让燕舞成为全国收录机第一品牌，也教会了中国企业什么叫『广告轰炸』。",
 "detail": "燕舞集团1980年代以收录机崛起，广告在央视黄金时段高频播出，『燕舞』的旋律几乎成为频道切换的背景音。1990年前后燕舞收录机销量全国领先，但收银录音机（卡座）向组合音响、随身听的技术迭代中转型迟缓，加上管理问题，1990年代末燕舞走向破产，『一片歌来一片情』成为那个广告黄金年代的绝响样本。",
 "impact": "央视广告的点石成金效应被燕舞验证，此后秦池、爱多等『标王』故事都从这条旋律开始。",
 "aftermath": "燕舞的衰落与标王们的沉浮共同构成中国广告业『成也央视、败也央视』的时代注脚。",
 "sources": [{"title": "百度百科：燕舞集团", "url": "https://baike.baidu.com/item/燕舞集团", "type": "wiki"}],
 "tags": ["文化", "燕舞", "收录机", "电视广告"]
})

D.append({
 "id": "1988-08-19-price-reform-panic-buying",
 "date": "1988-08-19", "date_accuracy": "exact", "date_confidence": "verified",
 "title": "物价闯关与抢购风潮：货架被一夜搬空之夏",
 "category": "society", "region": "cn", "milestone": False,
 "summary_30s": "1988年8月19日晨，中央人民广播电台播出价格改革方案，提前放开的消息引发全国抢购：从火柴食盐到彩电冰箱，商店货架被一夜搬空，银行出现挤兑。这场风潮让『物价闯关』紧急刹车，也成为价格改革最深刻的一课。",
 "detail": "1988年年中物价上涨压力加大，8月中旬政治局会议通过价格工资改革初步方案的消息传开后，公众预期物价将大涨，8月19日新闻播出后全国出现抢购与银行提款潮，当月零售物价指数同比涨幅逼近26%。中央随即紧急叫停『闯关』，转入治理整顿，利率保值储蓄等措施出台。1992年后价格改革以渐进方式重启，绝大多数商品价格在1990年代末实现市场定价。",
 "impact": "价格改革的『一步到位』方案被民意与市场用脚投票否决，渐进式改革自此成为共识路径。",
 "aftermath": "抢购潮的记忆塑造了此后历次改革对公众预期管理的重视；1990年代凭证供应的全面退出让这段记忆成为里程碑式注脚。",
 "sources": [{"title": "百度百科：物价闯关", "url": "https://baike.baidu.com/item/1988年物价闯关", "type": "wiki"}],
 "tags": ["社会", "物价闯关", "抢购风潮", "价格改革"]
})

out = 'data/events/.parts/batch_1980s_boost.json'
os.makedirs(os.path.dirname(out), exist_ok=True)
json.dump(D, open(out, 'w'), ensure_ascii=False, indent=0)
print('written', len(D), 'entries ->', out)
for e in D:
    print(e['id'], '|', e['title'][:32], '|', e['category'], '| ms:', e['milestone'])
