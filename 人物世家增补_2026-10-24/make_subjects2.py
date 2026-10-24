# -*- coding: utf-8 -*-
"""生成第二批补齐任务的 subjects 文件（新人物 42 / 新世家 36 / 时间线补强 5 批）"""
import json, io, os, glob, collections

os.makedirs('subjects2', exist_ok=True)

persons = {
  'n0': [
    {'name': '杰弗里·辛顿', 'en': 'Geoffrey Hinton', 'field': 'ai', 'why': '深度学习之父、2024诺贝尔物理学奖'},
    {'name': '杨立昆', 'en': 'Yann LeCun', 'field': 'ai', 'why': 'CNN之父、图灵奖、Meta首席AI科学家'},
    {'name': '伊利亚·苏茨克维', 'en': 'Ilya Sutskever', 'field': 'ai', 'why': 'OpenAI联合创始人、SSI'},
    {'name': '李开复', 'en': 'Kai-Fu Lee', 'field': 'ai', 'why': '微软谷歌华人高管、创新工场、零一万物'},
    {'name': '王小川', 'en': 'Wang Xiaochuan', 'field': 'ai', 'why': '搜狗输入法缔造者、百川智能'},
    {'name': '陈天桥', 'en': 'Chen Tianqiao', 'field': 'internet', 'why': '盛大网络《传奇》首富、脑科学研究'},
    {'name': '李国庆', 'en': 'Li Guoqing', 'field': 'internet', 'why': '当当网联合创始人、抢公章事件'},
    {'name': '古永锵', 'en': 'Victor Koo', 'field': 'internet', 'why': '优酷创始人、合一集团'},
    {'name': '姚劲波', 'en': 'Yao Jinbo', 'field': 'internet', 'why': '58同城创始人'},
    {'name': '张旭豪', 'en': 'Zhang Xuhao', 'field': 'internet', 'why': '饿了么创始人、交棒阿里'},
    {'name': '宿华', 'en': 'Su Hua', 'field': 'internet', 'why': '快手联合创始人、短视频算法'},
    {'name': '陈睿', 'en': 'Chen Rui', 'field': 'internet', 'why': 'B站董事长、二次元社区商业化'},
    {'name': '周源', 'en': 'Zhou Yuan', 'field': 'internet', 'why': '知乎创始人'},
    {'name': '唐岩', 'en': 'Tang Yan', 'field': 'internet', 'why': '陌陌创始人'},
  ],
  'n1': [
    {'name': '陈士骏', 'en': 'Steve Chen', 'field': 'internet', 'why': 'YouTube联合创始人（华裔）'},
    {'name': '戴威', 'en': 'Dai Wei', 'field': 'internet', 'why': 'ofo创始人、共享单车大溃败核心人物'},
    {'name': '汪滔', 'en': 'Frank Wang', 'field': 'hardware', 'why': '大疆创新、全球消费级无人机霸主'},
    {'name': '梁孟松', 'en': 'Liang Mong-song', 'field': 'hardware', 'why': '台积电/三星制程传奇、中芯国际'},
    {'name': '杨元庆', 'en': 'Yang Yuanqing', 'field': 'hardware', 'why': '联想集团董事长、并购IBM PC'},
    {'name': '孙正义', 'en': 'Masayoshi Son', 'field': 'finance', 'why': '软银、阿里巴巴早期最大投资人'},
    {'name': '徐新', 'en': 'Kathy Xu', 'field': 'finance', 'why': '今日资本、京东/网易早期投资人'},
    {'name': '熊晓鸽', 'en': 'Hugo Xiong', 'field': 'finance', 'why': 'IDG资本、中国风投开创者'},
    {'name': '余承东', 'en': 'Richard Yu', 'field': 'company', 'why': '华为消费者业务、Mate崛起'},
    {'name': '周受资', 'en': 'Shou Zi Chew', 'field': 'company', 'why': '小米CFO出身、TikTok CEO美国听证会'},
    {'name': '薇娅', 'en': 'Viya Huang', 'field': 'internet', 'why': '直播带货一姐、税务事件标志性人物'},
    {'name': '张大奕', 'en': 'Zhang Dayi', 'field': 'internet', 'why': '网红电商鼻祖如涵'},
    {'name': '陈欧', 'en': 'Chen Ou', 'field': 'internet', 'why': '聚美优品、为自己代言'},
    {'name': '王思聪', 'en': 'Wang Sicong', 'field': 'internet', 'why': 'IG电竞、熊猫TV、网络文化焦点'},
  ],
  'n2': [
    {'name': '刘慈欣', 'en': 'Liu Cixin', 'field': 'creator', 'why': '《三体》雨果奖、中国科幻输出旗帜'},
    {'name': '金庸', 'en': 'Jin Yong', 'field': 'creator', 'why': '武侠小说宗师、华人网络文化母题'},
    {'name': '王小波', 'en': 'Wang Xiaobo', 'field': 'creator', 'why': '互联网时代精神偶像、《沉默的大多数》'},
    {'name': '罗翔', 'en': 'Luo Xiang', 'field': 'creator', 'why': '法考罗翔、B站顶流知识区'},
    {'name': '郭德纲', 'en': 'Guo Degang', 'field': 'creator', 'why': '德云社、相声互联网传播'},
    {'name': '饺子', 'en': 'Jiaozi (Yang Yu)', 'field': 'creator', 'why': '《哪吒》系列、中国动画影史票房'},
    {'name': '琼瑶', 'en': 'Chiung Yao', 'field': 'creator', 'why': '言情宗师、2024年离世'},
    {'name': '高晓松', 'en': 'Gao Xiaosong', 'field': 'media', 'why': '《晓说》、互联网脱口秀开创者'},
    {'name': '柴静', 'en': 'Chai Jing', 'field': 'media', 'why': '《看见》、《穹顶之下》'},
    {'name': '易中天', 'en': 'Yi Zhongtian', 'field': 'media', 'why': '《品三国》、学术网红鼻祖'},
    {'name': '冯小刚', 'en': 'Feng Xiaogang', 'field': 'media', 'why': '贺岁片开创者、微博时代争议'},
    {'name': '高锟', 'en': 'Charles Kao', 'field': 'science', 'why': '光纤之父、互联网物理基座、诺贝尔奖'},
    {'name': '南仁东', 'en': 'Nan Rendong', 'field': 'science', 'why': 'FAST天眼总工程师'},
    {'name': '黄旭华', 'en': 'Huang Xuhua', 'field': 'science', 'why': '核潜艇之父、2025年离世'},
  ],
  'n3': [
    {'name': '李晓峰', 'en': 'Sky (Li Xiaofeng)', 'field': 'game', 'why': 'Sky、中国电竞WCG两冠传奇'},
    {'name': '简自豪', 'en': 'Uzi (Jian Zihao)', 'field': 'game', 'why': 'Uzi、LPL标志性选手'},
    {'name': '郑钦文', 'en': 'Zheng Qinwen', 'field': 'sport', 'why': '2024巴黎奥运网球女单金牌'},
    {'name': '樊振东', 'en': 'Fan Zhendong', 'field': 'sport', 'why': '乒乓大满贯、2024巴黎'},
    {'name': '王楚钦', 'en': 'Wang Chuqin', 'field': 'sport', 'why': '乒乓球、网络热度顶流'},
    {'name': '全红婵', 'en': 'Quan Hongchan', 'field': 'sport', 'why': '跳水天才少女'},
    {'name': '韦东奕', 'en': 'Wei Dongyi', 'field': 'science', 'why': '北大韦神、数学网红现象'},
  ],
}

entities = {
  'm0': [
    {'name': '拼多多', 'type': 'company', 'why': '社交电商裂变、砍一刀文化'},
    {'name': '小红书', 'type': 'community', 'why': '种草社区、生活方式搜索入口'},
    {'name': '微博', 'type': 'media', 'why': '新浪微博、热点舆论广场'},
    {'name': '奇虎360', 'type': 'company', 'why': '免费杀毒颠覆、3Q大战主角'},
    {'name': '支付宝', 'type': 'service', 'why': '从淘宝担保交易到国民支付'},
    {'name': '微信', 'type': 'service', 'why': '张小龙、国民应用、公众号小程序生态'},
    {'name': '钉钉', 'type': 'service', 'why': '阿里企业社交、疫情在线办公'},
    {'name': '飞信', 'type': 'service', 'why': '中国移动、运营商IM兴衰'},
    {'name': '米聊', 'type': 'service', 'why': '小米、与微信的生死竞速'},
    {'name': '饿了么', 'type': 'service', 'why': '张旭豪、外卖大战'},
    {'name': '大众点评', 'type': 'community', 'why': 'UGC点评鼻祖、与美团合并'},
    {'name': '12306', 'type': 'infrastructure', 'why': '春运抢票、世界最大票务系统'},
  ],
  'm1': [
    {'name': '新东方', 'type': 'company', 'why': '留学教父、双减转型东方甄选'},
    {'name': '爱奇艺', 'type': 'media', 'why': '百度系长视频'},
    {'name': '优酷', 'type': 'media', 'why': '与土豆合并、阿里收购'},
    {'name': '暴风影音', 'type': 'media', 'why': '冯鑫、暴风集团神话与崩塌'},
    {'name': '快播', 'type': 'media', 'why': '王欣、技术无罪辩论、涉黄案'},
    {'name': '射手网', 'type': 'community', 'why': '字幕站文化、版权关停'},
    {'name': 'UC浏览器', 'type': 'service', 'why': '移动浏览器之王、阿里收购'},
    {'name': '锤子科技', 'type': 'company', 'why': '罗永浩、情怀手机、直播还债'},
    {'name': '魅族', 'type': 'company', 'why': '黄章、MP3转手机、珠海小厂'},
    {'name': '联想集团', 'type': 'company', 'why': '贸工技之争、IBM PC并购'},
    {'name': '华为', 'type': 'company', 'why': '通信设备→手机→鸿蒙制裁突围'},
    {'name': '中兴通讯', 'type': 'company', 'why': '2018制裁事件标志'},
  ],
  'm2': [
    {'name': '大疆创新', 'type': 'company', 'why': '全球无人机霸主'},
    {'name': '中国移动', 'type': 'infrastructure', 'why': '全球用户最大运营商、移动梦网母体'},
    {'name': '中国联通', 'type': 'infrastructure', 'why': 'CDMA、混改、5G共建'},
    {'name': '米哈游', 'type': 'game', 'why': '原神、二次元全球化'},
    {'name': '瑞星', 'type': 'company', 'why': '小狮子、杀毒软件时代'},
    {'name': 'OpenAI', 'type': 'company', 'why': 'ChatGPT、AGI竞赛、宫斗'},
    {'name': '英伟达', 'type': 'company', 'why': '显卡→AI霸主、市值之王'},
    {'name': '苹果公司', 'type': 'company', 'why': '乔布斯回归、iPhone、3万亿美元'},
    {'name': '微软', 'type': 'company', 'why': 'Windows霸权、纳德拉云转型AI豪赌'},
    {'name': '特斯拉', 'type': 'company', 'why': '电动车革命、上海超级工厂'},
    {'name': 'Instagram', 'type': 'community', 'why': '图片社交、被脸书十亿收购'},
    {'name': 'Telegram', 'type': 'service', 'why': '加密通讯、中文圈避难所'},
  ],
}

for name, lst in persons.items():
    io.open('subjects2/%s.json' % name, 'w', encoding='utf-8').write(json.dumps(lst, ensure_ascii=False, indent=1))
for name, lst in entities.items():
    io.open('subjects2/%s.json' % name, 'w', encoding='utf-8').write(json.dumps(lst, ensure_ascii=False, indent=1))
print('persons:', {k: len(v) for k, v in persons.items()}, 'entities:', {k: len(v) for k, v in entities.items()})

# 时间线补强批次：附已有事件标题防重复
years_events = collections.defaultdict(list)
for f in sorted(glob.glob('../site/data/shard-*.json')):
    for ev in json.load(open(f, encoding='utf-8')):
        years_events[ev['date'][:4]].append(ev['title'])
tl_batches = {
    't0': [str(y) for y in range(1972, 1977)],
    't1': [str(y) for y in range(1977, 1982)],
    't2': [str(y) for y in range(1982, 1986)],
    't3': ['2025'],
    't4': ['2026'],
}
for name, ys in tl_batches.items():
    payload = {y: years_events.get(y, []) for y in ys}
    io.open('subjects2/%s.json' % name, 'w', encoding='utf-8').write(json.dumps(payload, ensure_ascii=False, indent=1))
    print(name, {y: len(v) for y, v in payload.items()})
