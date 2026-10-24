# -*- coding: utf-8 -*-
"""Wave-1 规模化扩容批次生成：14 事件批（年份分片+密度目标+去重清单）+ 人物/世家/作品扩展批。"""
import json, io, os, glob, collections

os.makedirs('subjects3', exist_ok=True)

# ---------- 既有名单 ----------
def names_of(pattern, key):
    s = set()
    for f in glob.glob(pattern):
        try:
            for r in json.load(open(f, encoding='utf-8')):
                s.add(r.get(key) or r.get('name') or r.get('title'))
        except Exception:
            pass
    return s

existing_persons = names_of('../site/persons/data.json', 'name') | names_of('out2/out-n*.json', 'name')
existing_entities = names_of('../site/entities/data.json', 'name') | names_of('out2/out-m*.json', 'name')
existing_works = names_of('out2/out-w*.json', 'title')

# ---------- 人物扩展（横向 10x，~210 人） ----------
PE = {
 'ai': ['Andrej Karpathy','李沐','周志华','汤晓鸥','朱松纯','张钹','Dario Amodei','Emad Mostaque','Mira Murati','Noam Shazeer（Character.AI/Attention作者）','Jim Fan','肖弘','杨植麟已有跳过占位'],
 'internet_cn': ['黄峥','程一笑','吴宵光','张志东','许晨晔','陈一舟','李学凌','王高飞','奉佑生','赵鹏','罗振宇','蔡文胜','王欣','喻华峰','唐岩已有占位','姬十三已有占位','阿北（杨勃）','梁建章','庄辰超','陈琪','白鸦','王怀南','邵亦波','李国庆已有占位','戴科彬','姚军红','昌敬','王宁（Keep）','张旭豪已有占位','占位跳过'],
 'internet_world': ['Jack Dorsey','Evan Spiegel','Brian Chesky','Travis Kalanick','Daniel Ek','Pavel Durov','Jan Koum','Reed Hastings','Susan Wojcicki','Marissa Mayer','Jensen Huang已有占位','Lisa Su（苏姿丰）','Kristen? 跳过','占位'],
 'hardware_cn': ['何庭波','徐直军','尹志尧','张汝京','胡正明','李书福','魏建军','尹同跃','郭台铭','卢伟冰','刘作虎','王翔','占位跳过'],
 'company': ['Satya Nadella','Sundar Pichai','张勇（逍遥子）','井贤栋','蒋凡','徐雷','蔡崇信','刘炽平','王慧文','张勇（阿里CTO行癫）跳过','占位'],
 'finance': ['索罗斯','朱啸虎','蔡崇信已有占位','沈南鹏已有占位','占位'],
 'media': ['崔永元','窦文涛','梁文道','许知远','马东','张召忠','于丹','金星','李诞','沈腾','贾玲','黄渤','徐峥','王宝强','吴京','姜文','陈思诚','贾樟柯','郭帆','宁浩','窦唯','张楚','何勇','汪峰','朴树','许巍','阿信（五月天）','陈奕迅','刘德华','周星驰','周润发','成龙','李连杰','林俊杰','陶喆跳过','王力宏','韩寒','南派三叔','唐家三少','郑渊洁','几米','朱德庸','华农兄弟','王刚（美食作家）','蔡澜','占位'],
 'science': ['饶毅','张锋','Jennifer Doudna','中村修二','吉野彰','杨卫? 跳过','王坚已有占位','南仁东已有占位','李兰娟已有占位','颜宁已有占位','薛其坤已有占位','占位'],
 'sport': ['孙杨','傅园慧','武大靖','丁俊晖','柯洁','聂卫平','李世石','博尔特','菲尔普斯','梅西','C罗','科比','迈克尔·乔丹','勒布朗·詹姆斯','库里','刘国梁','张怡宁','羽生结弦','占位'],
 'game': ['蔡浩宇','陈星汉','Markus Persson（Notch）','三上真司跳过','占位'],
}
pe_all = []
for f, lst in PE.items():
    for name in lst:
        if '占位' in name or '跳过' in name or name in existing_persons:
            continue
        pe_all.append({'name': name, 'field': f})
# 分 6 批
for i in range(6):
    chunk = pe_all[i*34:(i+1)*34]
    if not chunk:
        continue
    io.open(f'subjects3/n{4+i}.json', 'w', encoding='utf-8').write(
        json.dumps({'batch': f'n{4+i}', 'targets': chunk, 'existing_names': sorted(existing_persons)}, ensure_ascii=False, indent=1))
print('persons expansion:', len(pe_all), '人 /', min(6, (len(pe_all)+33)//34), '批')

# ---------- 世家扩展（~120 家） ----------
EE = ['闲鱼','唯品会','蘑菇街','苏宁','国美','高德','WiFi万能钥匙','科大讯飞','商汤','旷视','寒武纪','中芯国际','台积电','阿斯麦','ARM','高通','联发科','英特尔','AMD','微众银行','银联','蚂蚁集团','海康威视','京东方','长江存储','紫光','宁德时代','比亚迪','蔚来','理想汽车','小鹏汽车','铁血社区','马蜂窝','虎牙','斗鱼','YY','A站（AcFun）','西瓜视频','抖音','QQ空间','美图','猎豹移动','完美世界','多益网络','三七互娱','淘米网络','4399','暴雪娱乐','任天堂','索尼互动娱乐','Valve','Epic Games','WhatsApp','Discord','Twitch','LinkedIn','Snapchat','Zoom','Anthropic','DeepMind','智谱AI','月之暗面','DeepSeek（深度求索）','MiniMax','百川智能','零一万物','xAI','Mistral AI','新东方在线? 跳过','东方甄选','学而思','猿辅导','作业帮','Boss直聘','货拉拉','得物',' soul? 跳过','小红书已有占位','微博已有占位','网易云音乐','QQ音乐','虾米音乐','酷狗音乐','咪咕','阅文集团','掌阅','中文在线','知网','万方? 跳过','雪球','同花顺','东方财富已有占位','挖财? 跳过','随手记? 跳过','人人贷? 跳过','拍拍贷? 跳过','陆金所? 跳过','信用体系? 跳过','快手已有','B站已有','特斯拉已有','苹果已有','微软已有','OpenAI已有','英伟达已有','华为已有','联想已有','大疆已有','拼多多已有','微信已有','支付宝已有','饿了么已有','大众点评已有','12306已有','钉钉已有','飞信已有','米聊已有','新东方已有','爱奇艺已有','优酷已有','暴风已有','快播已有','射手网已有','UC已有','锤子已有','魅族已有','中兴已有','中国移动已有','中国联通已有','米哈游已有','瑞星已有','Instagram已有','Telegram已有','360已有','微博已有']
ee_all = [n for n in EE if '跳过' not in n and '占位' not in n and n not in existing_entities]
for i in range(4):
    chunk = ee_all[i*30:(i+1)*30]
    if not chunk:
        continue
    io.open(f'subjects3/m{3+i}.json', 'w', encoding='utf-8').write(
        json.dumps({'batch': f'm{3+i}', 'targets': [{'name': n} for n in chunk], 'existing_names': sorted(existing_entities)}, ensure_ascii=False, indent=1))
print('entities expansion:', len(ee_all), '家 /', min(4, (len(ee_all)+29)//30), '批')

# ---------- 作品扩展（~110 部） ----------
WE = {
 'film': ['霸王别姬','让子弹飞','流浪地球','流浪地球2','战狼2','你好，李焕英','我不是药神','泰囧','夏洛特烦恼','长津湖','封神第一部','哪吒之魔童降世','哪吒2：妖怪闹海? 按实际名','少年的你','我和我的祖国? 跳过','满江红? 跳过','无人区? 跳过','占位'],
 'tv': ['琅琊榜','大明王朝1566','潜伏','亮剑','来自星星的你','权力的游戏','老友记','绝命毒师','生活大爆炸','纸牌屋','黑镜','人民的名义已有','狂飙已有','甄嬛传已有','蜗居已有','武林外传已有','士兵突击已有','渴望已有','编辑部的故事已有','还珠格格已有','西游记已有','三国演义已有','北京人在纽约已有','黑猫警长已有','射雕已有','少林寺已有','庐山恋已有','红高粱已有','大话西游已有','泰坦尼克号已有','编辑部已有','占位'],
 'book': ['狼图腾','人类简史','从0到1','失控','数字化生存','娱乐至死','三体已有','平凡的世界已有','万历十五年已有','美的历程已有','活着已有','白鹿原已有','撒哈拉已有','明朝那些事儿已有','鬼吹灯已有','盗墓笔记已有','悟空传已有','亲密接触已有','繁花已有','明朝已有','围城已有','顾准文集已有','第一次的亲密接触已有','成都今夜已有','诛仙已有','起点VIP已有','番茄小说已有','占位'],
 'music': ['新长征路上的摇滚','黑豹','唐朝·梦回唐朝','常回家看看','心太软','两只蝴蝶','忐忑','小苹果','月亮之上','最炫民族风','江南Style','范特西','生如夏花','平凡之路','海阔天空','光辉岁月跳过一条','乐队的夏天（综艺）','中国好声音（综艺）','快乐大本营（综艺）','非诚勿扰（综艺）','爸爸去哪儿（综艺）','奔跑吧兄弟（综艺）','中国有嘻哈（综艺）','创造101（综艺）','超级女声已有','孤勇者已有','同桌的你已有','小芳已有','老鼠爱大米已有','一无所有已有','Jay已有','仙剑奇侠传已有? 游戏算','占位'],
 'game': ['梦幻西游','大话西游2','DOTA','英雄联盟','王者荣耀','绝地求生','和平精英','阴阳师','蛋仔派对','羊了个羊','贪玩蓝月','传奇（热血传奇）','石器时代','魔兽争霸3','星际争霸','CS反恐精英','红色警戒','GTA5','我的世界','塞尔达传说：旷野之息','艾尔登法环','只狼','黑暗之魂','最终幻想7','勇者斗恶龙跳过','俄罗斯方块','炉石传说','守望先锋','魔兽世界已有','原神已有','黑神话已有','仙剑已有',' FC超级马力欧已有? 事件','占位'],
 'comic': ['龙珠','海贼王','火影忍者','EVA新世纪福音战士','攻壳机动队','千与千寻','哆啦A梦','蜡笔小新','名侦探柯南','中华小当家','数码宝贝','宝可梦（动画）','喜羊羊与灰太狼','熊出没','一人之下','狐妖小红娘','猫和老鼠','海尔兄弟','灌篮高手已有','圣斗士已有','乱马已有','魔女宅急便已有','大闹天宫已有','葫芦兄弟已有','蓝猫淘气已有','罗小黑已有','占位'],
}
we_all = []
for t, lst in WE.items():
    for title in lst:
        if '占位' in title or '跳过' in title or '已有' in title or title in existing_works:
            continue
        we_all.append({'title': title, 'type': {'film': 'film', 'tv': 'tv', 'book': 'book', 'music': 'music', 'game': 'game', 'comic': 'comic'}[t]})
for i in range(3):
    chunk = we_all[i*36:(i+1)*36]
    if not chunk:
        continue
    io.open(f'subjects3/w{4+i}.json', 'w', encoding='utf-8').write(
        json.dumps({'batch': f'w{4+i}', 'targets': chunk, 'existing_titles': sorted(existing_works)}, ensure_ascii=False, indent=1))
print('works expansion:', len(we_all), '部 /', min(3, (len(we_all)+35)//36), '批')

# ---------- 事件批（14 个年份分片，附该区间已有标题去重清单） ----------
years_events = collections.defaultdict(list)
for f in sorted(glob.glob('../site/data/shard-*.json')):
    for ev in json.load(open(f, encoding='utf-8')):
        years_events[int(ev['date'][:4])].append(ev['title'])
CHUNKS = [
    ('te-a1', 1972, 1975, 120), ('te-a2', 1976, 1979, 140),
    ('te-b1', 1980, 1983, 160), ('te-b2', 1984, 1987, 180),
    ('te-b3', 1988, 1991, 200), ('te-b4', 1992, 1995, 220),
    ('te-c1', 1996, 1999, 240), ('te-c2', 2000, 2003, 240),
    ('te-c3', 2004, 2007, 260), ('te-c4', 2008, 2011, 280),
    ('te-d1', 2012, 2015, 300), ('te-d2', 2016, 2019, 320),
    ('te-d3', 2020, 2022, 300), ('te-d4', 2023, 2026, 320),
]
for name, y0, y1, target in CHUNKS:
    dedup = []
    for y in range(y0, y1 + 1):
        dedup += years_events.get(y, [])
    io.open(f'subjects3/{name}.json', 'w', encoding='utf-8').write(
        json.dumps({'batch': name, 'year_from': y0, 'year_to': y1, 'target_min': target,
                    'dedup_titles': dedup}, ensure_ascii=False))
    print(f'{name}: {y0}-{y1} 目标{target}+ 去重清单{len(dedup)}条')
print('DONE')
