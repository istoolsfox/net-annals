#!/usr/bin/env python3
# 教育层 · 第二批（教师法/高考节点/学位立法/民办与职教）
import json, os
os.makedirs('data/events/.parts', exist_ok=True)

def S(t, u):
    return {"type": t, "url": u, "title": t}

D = [
 {"id":"1993-10-31-teachers-law","date":"1993-10-31","date_accuracy":"exact","date_confidence":"verified",
  "title":"《教师法》通过：教师职业第一次有了专门法律","category":"national","region":"cn",
  "milestone":False,
  "summary_30s":"1993年10月31日，八届全国人大常委会通过《教师法》，教师的权利、资格与待遇第一次被系统立法。",
  "impact":"「教师工资不低于当地公务员平均工资水平」写入法律，教师队伍建设从政策号召转向法定保障。",
  "aftermath":"教师资格制度、教师节慰问待遇、绩效工资改革均以此为法源；教师待遇落实争议至今仍是每年的督导重点。",
  "tags":[],"sources":[S("wiki","https://baike.baidu.com/item/中华人民共和国教师法")]},

 {"id":"2003-06-07-june-gaokao-first","date":"2003-06-07","date_accuracy":"exact","date_confidence":"verified",
  "title":"高考提前至6月举行，告别「七月份的黑色」","category":"national","region":"cn",
  "milestone":False,
  "summary_30s":"2003年6月7日，全国高考首次提前到6月开考——沿用二十余年的7月「黑色七月」就此改期。",
  "impact":"考试避开酷暑与南方汛期，考生复习节奏、高校录取流程整体前移。",
  "aftermath":"当年恰逢非典疫情，全国考生测温进场成为特殊记忆；「6月7日高考」自此固定为几代人的公共日历。",
  "tags":[],"sources":[S("wiki","https://zh.wikipedia.org/wiki/普通高等学校招生全国统一考试")]},

 {"id":"2020-05-01-higher-ed-universal","date":"2020-05-01","date_accuracy":"month","date_confidence":"verified",
  "title":"高等教育毛入学率突破50%，进入普及化阶段","category":"national","region":"cn",
  "milestone":False,
  "summary_30s":"2020年5月，教育部统计显示高等教育毛入学率达51.6%——中国高等教育跨过50%的普及化门槛。",
  "impact":"从1999年扩招前不到10%到过半，「上大学」从选拔性稀缺变成大众经历。",
  "aftermath":"学历贬值焦虑、考研热与职业教育分流讨论同步升温，高校分类评价与「双一流」建设承担起质量竞争的新任务。",
  "tags":[],"sources":[S("wiki","https://baike.baidu.com/item/高等教育毛入学率")]},

 {"id":"2020-02-01-online-school-start","date":"2020-02-01","date_accuracy":"month","date_confidence":"verified",
  "title":"「停课不停学」：全国中小学生集体上网课","category":"national","region":"cn",
  "milestone":False,
  "summary_30s":"2020年2月，教育部部署「停课不停学」，数亿中小学生转向线上课堂，国家中小学网络云平台随后开通。",
  "impact":"在线教育从补充角色一夜成为基础设施，教师、家长与平台共同完成史上最大规模远程教学实验。",
  "aftermath":"网课硬件、直播系统与家庭教育矛盾集中爆发；疫情后在线教育退潮，「双减」随即改写整个教培行业格局。",
  "tags":[],"sources":[S("wiki","https://baike.baidu.com/item/停课不停学")]},

 {"id":"2021-05-14-private-education-regulation","date":"2021-05-14","date_accuracy":"exact","date_confidence":"verified",
  "title":"修订版《民办教育促进法实施条例》公布","category":"national","region":"cn",
  "milestone":False,
  "summary_30s":"2021年5月14日，修订后的《民办教育促进法实施条例》公布，义务教育阶段「公参民」学校受到严格限制。",
  "impact":"民办学校不得以营利为目的办义务教育、「名校办民校」模式被叫停，公办资源回归公办体系。",
  "aftermath":"此后两年全国数百所「公参民」学校转公或转设，民办教育从扩张期进入规范期，教培与民办义务教育双双重塑。",
  "tags":[],"sources":[S("wiki","https://baike.baidu.com/item/民办教育促进法实施条例")]},

 {"id":"2022-04-20-vocational-education-law","date":"2022-04-20","date_accuracy":"exact","date_confidence":"verified",
  "title":"新修订《职业教育法》通过：职教与普教「同等重要」入法","category":"national","region":"cn",
  "milestone":False,
  "summary_30s":"2022年4月20日，十三届全国人大常委会通过新修订的《职业教育法》，26年来首次大修。",
  "impact":"「职业教育与普通教育具有同等重要地位」首次写入法律，「职教高考」与本科层次职业教育获得法定通道。",
  "aftermath":"职业本科大学加速设立，中考分流的公众焦虑被重新讨论；技能型人才薪酬与上升通道的政策配套持续推进。",
  "tags":[],"sources":[S("wiki","https://baike.baidu.com/item/中华人民共和国职业教育法")]},

 {"id":"2024-04-26-degree-law","date":"2024-04-26","date_accuracy":"exact","date_confidence":"verified",
  "title":"《学位法》通过：中国学位制度有了专门法律","category":"national","region":"cn",
  "milestone":False,
  "summary_30s":"2024年4月26日，全国人大常委会通过《学位法》，2025年1月1日施行——1980年《学位条例》完成向法律的升级。",
  "impact":"学术学位与专业学位分类授予、学位撤销程序与救济机制首次法定，「守护学术诚信」有了明确法律框架。",
  "aftermath":"论文抽检、学位撤销争议从此有法可依，专业学位比重扩大与研究生教育分类培养同步推进。",
  "tags":[],"sources":[S("wiki","https://baike.baidu.com/item/中华人民共和国学位法")]},

 {"id":"2022-11-01-kaoyan-4-74m","date":"2022-11-01","date_accuracy":"month","date_confidence":"verified",
  "title":"考研报名人数474万创历史新高","category":"society","region":"cn",
  "milestone":False,
  "summary_30s":"2022年10月至11月，2023年考研报名人数达474万，再创历史新高——四年间几乎翻倍。",
  "impact":"「学历内卷」成为社会热词，考研从深造选择变成就业竞争的默认动作。",
  "aftermath":"2024年起报名人数连续两年回落，「逆向考研」与「考公热」此消彼长，学历竞争的拐点信号显现。",
  "tags":[],"sources":[S("wiki","https://baike.baidu.com/item/全国硕士研究生统一招生考试")]},
]

D[:] = [e for e in D if e.get('detail') or True]
for e in D:
    if not e.get('detail'):
        e['detail'] = e['summary_30s'] + ' ' + e['impact'] + ' ' + e['aftermath']
D[:] = [e for e in D if len(e['detail'])>20 and e.get('sources')]
json.dump(D, open('data/events/.parts/education-batch2.json','w'), ensure_ascii=False, indent=0)
print(f"education batch2: {len(D)} 条")
