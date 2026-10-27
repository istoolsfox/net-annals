/* section-page.js — 子页通用引擎（persons/ entities/ works/ 三页同一份代码）
 * 页面只需：window.NA_PAGE_KIND='persons'|'entities'|'works' + 引入 common.js + 本文件。
 * 数据/渲染/筛选/搜索/深链全部走 NA 共享模块；本文件只持有子页语境的差异配置。
 */
'use strict';

(function () {
  const KIND = window.NA_PAGE_KIND;
  const CFG = {
    persons: {
      listKey: 'persons', root: '#ptimeline', search: 'pq', chips: 'fieldChips',
      eras: 'P_ERAS', card: 'personCard', yearOf: p => String(p.birth || '0000').slice(0, 4),
      field: 'field', colors: 'FCOLOR', labels: 'FIELDS',
      fields: ['name', 'en_name', 'headline', 'tags'], unit: '人', param: 'p',
      empty: '没有匹配的人物——换个关键词试试',
      hero: n => `${n} 位人物已收录——AI、科技、互联网、商业、游戏电竞与赛博文化圈的知名人士人生历程，逐人核实、全部可溯源。按出生年代纵览，点击卡片展开完整人生。`,
    },
    entities: {
      listKey: 'entities', root: '#etimeline', search: 'q', chips: 'typeChips',
      eras: 'E_ERAS', card: 'entityCard', yearOf: e => String(e.founded || '0000').slice(0, 4),
      field: 'type', colors: 'TCOLOR', labels: 'TYPES',
      fields: ['name', 'en_name', 'headline', 'hq', 'tags'], unit: '家', param: 'e',
      empty: '没有匹配的世家——换个关键词试试',
      hero: n => `共 ${n} 家世家——企业、社区、机构的完整兴衰史，从创立到巅峰到谢幕，每个节点精确可溯源。按创立年代纵览，点击卡片展开完整兴衰史。`,
    },
    works: {
      listKey: 'works', root: '#wtimeline', search: 'wq', chips: 'typeChips',
      eras: 'W_ERAS', card: 'workCard', yearOf: w => String(w.released || '0000').slice(0, 4),
      field: 'type', colors: 'WTCOLOR', labels: 'WTYPES',
      fields: ['title', 'en_title', 'creators', 'headline', 'tags'], unit: '部', param: 'w',
      empty: '没有匹配的作品——换个关键词试试',
      hero: n => `${n} 部作品已收录——影视、文学、音乐、游戏与动画综艺，按发布年代纵览，点击卡片展开完整作品生命线。`,
    },
  }[KIND];

  if (!CFG) { console.error('NA_PAGE_KIND 未设置'); return; }

  (async () => {
    try {
      const data = await NA.fetchGz('data.json');
      const items = data[CFG.listKey];
      let filter = 'all', q = '';
      /* draw 支持 done 回调：renderLongScroll 分帧建 DOM，深链定位需等卡片就位 */
      const draw = done => NA.renderLongScroll(CFG.root, NA[CFG.eras],
        items.filter(it => (filter === 'all' || it[CFG.field] === filter) && NA.matchQ(it, q, CFG.fields)),
        CFG.yearOf, it => NA[CFG.card](it), CFG.unit, done);
      NA.buildFilterChips(document.getElementById(CFG.chips),
        [...new Set(items.map(it => it[CFG.field]))].map(f => ({ key: f, count: items.filter(it => it[CFG.field] === f).length })),
        { colorOf: f => NA[CFG.colors][f], labelOf: f => NA[CFG.labels][f] || f, onChange: f => { filter = f; draw(); } });
      NA.wireSearch(CFG.search, v => { q = v; draw(); });
      NA.wireExpand(CFG.root);
      const hero = document.getElementById('heroSub');
      if (hero) hero.textContent = CFG.hero(items.length);
      await new Promise(r => draw(r));
      NA.deepLinkCard(new URLSearchParams(location.search).get(CFG.param), CFG.root);
    } catch (e) {
      document.querySelector(CFG.root).innerHTML = `<div class="empty">数据加载失败（${NA.esc(e.message)}）</div>`;
    }
  })();
})();
