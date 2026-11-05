#!/usr/bin/env python3
# 医疗健康层 · 第二批（干细胞/诺奖系列/现象级新药）
import json, os
os.makedirs('data/events/.parts', exist_ok=True)

def S(t, u):
    return {"type": t, "url": u, "title": t}

D = [
 {"id":"1998-11-06-hesc-isolated","date":"1998-11-06","date_accuracy":"exact","date_confidence":"verified",
  "title":"威斯康星团队首次分离人类胚胎干细胞","category":"tech","region":"world",
  "milestone":False,
  "summary_30s":"1998年11月，詹姆斯·汤姆森团队在《科学》发表成果：人类胚胎干细胞首次被分离并长期培养。",
  "impact":"再生医学看到「万能细胞」的现实可能，也点燃了此后二十年的胚胎研究伦理争论。",
  "aftermath":"美国联邦资助因此受限多年，直到iPS细胞出现才给出绕开胚胎的替代路线；干细胞移植、类器官研究均由此起步。",
  "tags":[],"sources":[S("wiki","https://zh.wikipedia.org/wiki/胚胎干细胞")]},

 {"id":"2006-11-01-ips-mouse","date":"2006-11-01","date_accuracy":"month","date_confidence":"verified",
  "title":"山中伸弥发表iPS细胞：皮肤细胞被重编程为干细胞","category":"tech","region":"world",
  "milestone":False,
  "summary_30s":"2006年11月，山中伸弥团队在《细胞》发表：四个转录因子把小鼠皮肤细胞重编程为类似胚胎干细胞的状态。",
  "impact":"不破坏胚胎就能获得「万能细胞」，干细胞研究绕开了最尖锐的伦理争议，个体化再生医学的大门打开。",
  "aftermath":"2007年人类iPS细胞相继问世，山中伸弥凭此获2012年诺贝尔生理学或医学奖；新药筛选、疾病模型、细胞治疗全面展开。",
  "tags":[],"sources":[S("wiki","https://zh.wikipedia.org/wiki/诱导性多能干细胞")]},

 {"id":"2009-10-05-telomerase-nobel","date":"2009-10-05","date_accuracy":"exact","date_confidence":"verified",
  "title":"端粒与端粒酶发现者获诺贝尔生理学或医学奖","category":"tech","region":"world",
  "milestone":False,
  "summary_30s":"2009年10月5日，布莱克本、格雷德与绍斯塔克因发现「染色体如何被端粒和端粒酶保护」分享诺奖。",
  "impact":"细胞衰老与「生命时钟」的分子机制被讲清，衰老研究与癌症研究共用同一把钥匙。",
  "aftermath":"端粒检测一度被包装成「衰老体检」引发争议，而以端粒酶为靶点的抗衰老与肿瘤疗法研究持续至今。",
  "tags":[],"sources":[S("wiki","https://zh.wikipedia.org/wiki/2009年诺贝尔生理学或医学奖")]},

 {"id":"2012-10-08-yamanaka-gurdon-nobel","date":"2012-10-08","date_accuracy":"exact","date_confidence":"verified",
  "title":"山中伸弥与格登获诺贝尔奖：细胞命运可以被重写","category":"tech","region":"world",
  "milestone":False,
  "summary_30s":"2012年10月8日，山中伸弥与约翰·格登因发现「成熟细胞可被重编程为多能细胞」分享诺贝尔生理学或医学奖。",
  "impact":"从格登1962年的核移植到山中2006年的iPS，「细胞可以返老还童」完成半个世纪的证明闭环。",
  "aftermath":"细胞重编程此后成为再生医学、疾病建模与新药测试的基础工具，山中团队继续向通用型细胞治疗推进。",
  "tags":[],"sources":[S("wiki","https://zh.wikipedia.org/wiki/山中伸弥")]},

 {"id":"2016-09-01-three-parent-baby","date":"2016-09-01","date_accuracy":"month","date_confidence":"verified",
  "title":"全球首例「三亲婴儿」出生报告","category":"tech","region":"world",
  "milestone":False,
  "summary_30s":"2016年9月，纽约团队报告全球首例借助线粒体替代疗法出生的「三亲婴儿」——携带父母及卵子供体三方遗传物质。",
  "impact":"预防线粒体遗传病从动物实验走进临床，也把「设计婴儿」边界的争论推向新高度。",
  "aftermath":"英国2017年批准该技术临床应用并孕育出本土首例，多国对其保持严格限制，生殖医学的伦理审查从此多了一个坐标。",
  "tags":[],"sources":[S("wiki","https://en.wikipedia.org/wiki/Mitochondrial_replacement_therapy")]},

 {"id":"2020-10-07-crispr-nobel","date":"2020-10-07","date_accuracy":"exact","date_confidence":"verified",
  "title":"CRISPR基因剪刀获诺贝尔化学奖","category":"tech","region":"world",
  "milestone":False,
  "summary_30s":"2020年10月7日，杜德纳与沙尔庞捷因「开发基因组编辑方法」获诺贝尔化学奖——从论文到诺奖仅八年。",
  "impact":"基因编辑以「人人可上手」的简洁性改写生命科学工具箱，从基础研究直通临床与农业。",
  "aftermath":"2023年全球首个CRISPR疗法Casgevy获批上市，基因剪刀从实验室正式走进药房；专利之争与脱靶安全讨论同步延续。",
  "tags":[],"sources":[S("wiki","https://zh.wikipedia.org/wiki/2020年诺贝尔化学奖")]},

 {"id":"2021-06-04-wegovy-approved","date":"2021-06-04","date_accuracy":"exact","date_confidence":"verified",
  "title":"Wegovy获批：GLP-1开启减重药时代","category":"tech","region":"world",
  "milestone":False,
  "summary_30s":"2021年6月4日，FDA批准司美格鲁肽减重适应症（Wegovy）——史上最有效率的减重药上市。",
  "impact":"「打一针减重」从段子变成处方，肥胖作为慢性病的医学治疗逻辑被彻底改写。",
  "aftermath":"GLP-1药物把诺和诺德、礼来推上市值巅峰，供货短缺、保险拒付与停药反弹成为新议题；中国2024年批准减重适应症后市场同步引爆。",
  "tags":[],"sources":[S("wiki","https://zh.wikipedia.org/wiki/司美格鲁肽")]},

 {"id":"2021-12-22-paxlovid-eua","date":"2021-12-22","date_accuracy":"exact","date_confidence":"verified",
  "title":"辉瑞Paxlovid获美国紧急使用授权","category":"tech","region":"world",
  "milestone":False,
  "summary_30s":"2021年12月22日，FDA授权辉瑞口服抗病毒药Paxlovid紧急使用——首款可居家服用的新冠特效药。",
  "impact":"从「感染即隔离」到「确诊即吃药」，大流行应对从疫苗独轮转向疫苗+药物双轨，高危人群重症率显著下降。",
  "aftermath":"Paxlovid在中国2023年短暂纳入医保谈判后因价格未成，国产同类3CL抑制剂与中和抗体随后接续，抗病毒药物储备成为公共卫生标配。",
  "tags":[],"sources":[S("wiki","https://baike.baidu.com/item/Paxlovid")]},
]

D[:] = [e for e in D if e.get('detail') or True]
for e in D:
    if not e.get('detail'):
        e['detail'] = e['summary_30s'] + ' ' + e['impact'] + ' ' + e['aftermath']
D[:] = [e for e in D if len(e['detail'])>20 and e.get('sources')]
json.dump(D, open('data/events/.parts/medical-batch2.json','w'), ensure_ascii=False, indent=0)
print(f"medical batch2: {len(D)} 条")
