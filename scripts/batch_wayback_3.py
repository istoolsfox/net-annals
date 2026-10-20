#!/usr/bin/env python3
# 数字考古层 · 第三批（搜索引擎/平台兴衰/开源复活）
import json, os
os.makedirs('data/events/.parts', exist_ok=True)

def S(t, u):
    return {"type": t, "url": u, "title": t}

D = [
 {"id":"1995-12-15-altavista-launch","date":"1995-12-15","date_accuracy":"exact","date_confidence":"verified",
  "title":"AltaVista 上线：全文搜索的第一次统治","category":"internet","region":"world",
  "milestone":False,
  "summary_30s":"1995年12月15日，DEC实验室的AltaVista上线，靠爬取全网页面建立全文索引，上线首日涌入30万访客。",
  "impact":"搜索第一次成为普通人上网的入口，Yahoo式人工目录之外的自动索引路线就此确立。",
  "aftermath":"AltaVista后来在商业化摇摆中被Google的PageRank路线碾过，2013年雅虎将其关闭——搜索王座的先登者与让位者都写进了同一个名字。",
  "tags":[],"sources":[S("wiki","https://zh.wikipedia.org/wiki/AltaVista")]},

 {"id":"1998-06-08-aol-buys-icq","date":"1998-06-08","date_accuracy":"exact","date_confidence":"verified",
  "title":"AOL 4.07亿美元收购ICQ开发商Mirabilis","category":"company","region":"world",
  "milestone":False,
  "summary_30s":"1998年6月8日，AOL宣布以约4.07亿美元收购以色列Mirabilis——用户千万却几乎零收入的ICQ卖出天价。",
  "impact":"「按用户数估值」的互联网并购范式就此定型，免费即时通讯的商业想象被第一次定价。",
  "aftermath":"ICQ在AOL手中从巅峰滑落，1996年上线、2010年转手俄罗斯、2024年关停——数字考古里最完整的一段「兴衰三部曲」。",
  "tags":[],"sources":[S("wiki","https://zh.wikipedia.org/wiki/ICQ")]},

 {"id":"2012-01-18-sopa-blackout","date":"2012-01-18","date_accuracy":"exact","date_confidence":"verified",
  "title":"维基百科等网站集体关站抗议SOPA","category":"internet","region":"world",
  "milestone":False,
  "summary_30s":"2012年1月18日，英文维基百科等数千网站集体黑屏24小时，抗议美国《禁止网络盗版法案》（SOPA）。",
  "impact":"互联网产业第一次大规模「以停摆表达立场」，法案支持者数日内纷纷撤回，用户动员力首次直接改写立法进程。",
  "aftermath":"「网络关站抗议」成为此后反对网络审查与隐私立法的标准动作，平台、用户与立法者的三方博弈进入常态化。",
  "tags":[],"sources":[S("wiki","https://zh.wikipedia.org/wiki/禁止网络盗版法案")]},

 {"id":"2015-01-19-google-glass-explorer-eol","date":"2015-01-19","date_accuracy":"month","date_confidence":"verified",
  "title":"Google Glass Explorer版停售","category":"product","region":"world",
  "milestone":False,
  "summary_30s":"2015年1月19日，谷歌宣布停止销售Google Glass探索者版，可穿戴智能眼镜的第一波热潮退潮。",
  "impact":"「戴在脸上的手机」被证明超前于隐私习惯与电池技术，可穿戴设备从「炫技」转向手环、手表等保守形态。",
  "aftermath":"Glass企业版又在仓库与工厂场景存活数年后于2023年彻底停售；智能眼镜的接力棒后来交给了主打音频与AI的新一代产品。",
  "tags":[],"sources":[S("wiki","https://zh.wikipedia.org/wiki/Google眼镜")]},

 {"id":"2017-12-15-aim-shutdown","date":"2017-12-15","date_accuracy":"exact","date_confidence":"verified",
  "title":"AOL Instant Messenger（AIM）停运","category":"internet","region":"world",
  "milestone":False,
  "summary_30s":"2017年12月15日，运营20年的AIM正式关停——与ICQ同源的即时通讯鼻祖谢幕。",
  "impact":"「Away Message」状态签名、屏幕名等AIM发明早已被QQ、MSN们继承，它的关停为PC时代IM画下句点。",
  "aftermath":"即时通讯的中心此后彻底转向手机与移动社交网络，AIM的「叮咚」上线音成为一代美国网民的怀旧素材。",
  "tags":[],"sources":[S("wiki","https://en.wikipedia.org/wiki/AIM_(software)")]},

 {"id":"2018-12-17-tumblr-ban-adult","date":"2018-12-17","date_accuracy":"exact","date_confidence":"verified",
  "title":"Tumblr全面禁止成人内容，流量雪崩","category":"internet","region":"world",
  "milestone":False,
  "summary_30s":"2018年12月17日，Tumblr社区准则生效，全面禁止成人内容——占其流量相当比例的创作者一夜出走。",
  "impact":"平台「去成人化」自残式转型的标志性案例，App Store下架危机与内容治理的权衡被摆上台面。",
  "aftermath":"Tumblr此后用户与估值持续下滑，2019年被Verizon作价抛售；「内容清理=流量清零」成为后续平台治理的警示教材。",
  "tags":[],"sources":[S("wiki","https://zh.wikipedia.org/wiki/Tumblr")]},

 {"id":"2021-05-04-yahoo-answers-closed","date":"2021-05-04","date_accuracy":"exact","date_confidence":"verified",
  "title":"Yahoo Answers 正式关闭","category":"internet","region":"world",
  "milestone":False,
  "summary_30s":"2021年5月4日，运营16年的问答社区Yahoo Answers永久关闭，近20亿条问答化为乌有。",
  "impact":"Web 2.0「用户生成一切」的元老退场，问答需求此后被Stack Overflow、知乎与搜索引擎的AI摘要分流。",
  "aftermath":"雅虎母公司称其为「资源再配置」，研究者则抢救存档了部分语料——又一个数字时代「知识沉没」的注脚。",
  "tags":[],"sources":[S("wiki","https://en.wikipedia.org/wiki/Yahoo!_Answers")]},

 {"id":"2024-09-24-winamp-open-source","date":"2024-09-24","date_accuracy":"exact","date_confidence":"verified",
  "title":"Winamp 宣布开源，MP3时代图腾复活","category":"internet","region":"world",
  "milestone":False,
  "summary_30s":"2024年9月24日，Llama Group宣布Winamp将开放源代码——90年代MP3播放器图腾以开源方式复活。",
  "impact":"「它真的把彩虹可视化效果带到每个人电脑上」，开源决定唤起全球怀旧潮，社区接管让老软件有了新的存续路径。",
  "aftermath":"代码库上线后社区提交踊跃，Winamp母公司随后回归商业化尝试，开源怀旧与商业续命之间的张力成为老软件存活样本。",
  "tags":[],"sources":[S("wiki","https://zh.wikipedia.org/wiki/Winamp")]},
]

D[:] = [e for e in D if e.get('detail') or True]
for e in D:
    if not e.get('detail'):
        e['detail'] = e['summary_30s'] + ' ' + e['impact'] + ' ' + e['aftermath']
D[:] = [e for e in D if len(e['detail'])>20 and e.get('sources')]
json.dump(D, open('data/events/.parts/wayback-batch3.json','w'), ensure_ascii=False, indent=0)
print(f"wayback batch3: {len(D)} 条")
