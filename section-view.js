(function () {
'use strict';
/* section-view.js — 主页多视图切换：编年史 / 人物志 / 世家志 / 作品志
 * 编年史视图保持 app.js 原逻辑不动；其余三个视图全部委托 NA 共享模块渲染
 * （卡片模板/长卷/筛选芯片/搜索均在 common.js），本文件只持有视图差异配置。
 */
'use strict';

/* 每个视图与 NA 的对接差异：数据键、容器 id、分卷、卡片工厂、筛选取值字段等 */
const VIEWS = {
  persons: {
    data: 'persons/data.json', listKey: 'persons', root: '#ptimeline', search: 'pq',
    chips: 'pFieldRow', intro: 'personsIntro', eras: 'P_ERAS', card: 'personCard',
    yearOf: p => String(p.birth || '0000').slice(0, 4), field: 'field',
    colors: 'FCOLOR', labels: 'FIELDS', fields: ['name', 'en_name', 'headline', 'tags'], unit: '人',
    introText: n => `从达·芬奇到韦东奕，${n} 位塑造时代的人物——按出生年代纵览，点击卡片展开完整人生历程。`,
    heroSub: n => `${n} 位塑造时代的人物，按出生年代纵览——点击卡片展开完整人生历程。`,
  },
  entities: {
    data: 'entities/data.json', listKey: 'entities', root: '#etimeline', search: 'eq',
    chips: 'eTypeRow', intro: 'entitiesIntro', eras: 'E_ERAS', card: 'entityCard',
    yearOf: e => String(e.founded || '0000').slice(0, 4), field: 'type',
    colors: 'TCOLOR', labels: 'TYPES', fields: ['name', 'en_name', 'headline', 'hq', 'tags'], unit: '家',
    introText: n => `${n} 家世家——企业、社区、机构的完整兴衰史，从创立到巅峰到谢幕。按创立年代纵览，点击卡片展开完整兴衰史。`,
    heroSub: n => `${n} 家企业与社区的完整兴衰史——按创立年代纵览，点击卡片展开。`,
  },
  works: {
    data: 'works/data.json', listKey: 'works', root: '#wtimeline', search: 'wq',
    chips: 'wTypeRow', intro: 'worksIntro', eras: 'W_ERAS', card: 'workCard',
    yearOf: w => String(w.released || '0000').slice(0, 4), field: 'type',
    colors: 'WTCOLOR', labels: 'WTYPES', fields: ['title', 'en_title', 'creators', 'headline', 'tags'], unit: '部',
    introText: n => `${n} 部作品——影视、文学、音乐、游戏与动画综艺，按发布年代纵览，点击卡片展开完整作品生命线。`,
    heroSub: n => `${n} 部影视文学音乐游戏经典——按发布年代纵览，点击卡片展开生命线。`,
  },
};

const SV = {
  ready: {},          // 各视图初始化标记
  current: 'annals',

  /* 某视图通用初始化：拉数据 → 回填计数文案 → 芯片行 → 长卷 → 事件委托 */
  async initView(name) {
    if (this.ready[name]) return;
    const k = VIEWS[name];
    const data = await NA.fetchGz(k.data);
    const items = data[k.listKey];
    this.HERO[name].sub = k.heroSub(items.length);
    if (this.current === name) document.getElementById('heroSub').textContent = this.HERO[name].sub;
    document.getElementById(k.intro).textContent = k.introText(items.length);
    let filter = 'all', q = '';
    const draw = () => NA.renderLongScroll(k.root, NA[k.eras],
      items.filter(it => (filter === 'all' || it[k.field] === filter) && NA.matchQ(it, q, k.fields)),
      k.yearOf, it => NA[k.card](it, { home: true }), k.unit);
    NA.buildFilterChips(document.getElementById(k.chips),
      [...new Set(items.map(it => it[k.field]))].map(f => ({ key: f, count: items.filter(it => it[k.field] === f).length })),
      { colorOf: f => NA[k.colors][f], labelOf: f => NA[k.labels][f] || f, onChange: f => { filter = f; draw(); } });
    NA.wireSearch(k.search, v => { q = v; draw(); });
    NA.wireExpand(k.root);
    draw();
    this.ready[name] = true;
  },

  /* ── 视图切换 ── */
  HERO: {
    annals: null,
    persons: { eyebrow: '人物志 · 知名人士人生历程', title: '人物<em>志</em> · 一条条人生长卷', sub: '' },
    entities: { eyebrow: '世家志 · 兴衰长卷', title: '世家<em>志</em> · 为每一家立传', sub: '' },
    works: { eyebrow: '作品志 · 精神地标', title: '作品<em>志</em> · 陪伴大众的创作物', sub: '' },
  },

  async switch(name) {
    if (name === this.current) return;
    this.current = name;
    document.querySelectorAll('.topTab').forEach(b => b.classList.toggle('on', b.dataset.view === name));
    // hero 文案跟随视图；切换后自动定位到该视图工具栏
    const h = this.HERO[name];
    const eb = document.getElementById('heroEyebrow');
    const tt = document.querySelector('.heroTitle');
    const hs = document.getElementById('heroSub');
    if (h && eb && tt && hs) {
      eb.textContent = h.eyebrow;
      tt.innerHTML = h.title;
      hs.textContent = h.sub;
    } else if (name === 'annals' && eb) {
      eb.textContent = '1972 — 2026 · 精确到日 · 每条可溯源';
      tt.innerHTML = '互联<em>网</em>编年史';
      hs.textContent = '从一封越过长城的电子邮件，到人人掌中的智能时代——每一件大事、小事、转折事，都钉在它的那一天上。';
    }
    for (const v of ['annals', 'persons', 'entities', 'works']) {
      const pane = document.getElementById('view-' + v);
      if (pane) pane.style.display = v === name ? '' : 'none';
    }
    // 切视图 = 该视图的全新落地：回顶（hero 文案刚换过，滚到工具栏会把它整个跳过，
    // 且滚动深度会继承上一视图——曾表现为"往下滑过再切人物志不回顶"）
    window.scrollTo({ top: 0, behavior: 'instant' });
    history.replaceState(null, '', name === 'annals' ? '#' : '#view=' + name);
    if (name !== 'annals') {
      try {
        await this.initView(name);
      } catch (err) {
        // 视图名首字母与长卷容器 id 前缀一一对应（p/e/w + timeline）
        const root = document.querySelector('#' + name[0] + 'timeline');
        if (root) root.innerHTML = `<div class="empty">数据加载失败（${NA.esc(String(err.message || err))}）</div>`;
      }
    }
  },
};

/* ── 启动：Tab 事件 + 深链 ── */
document.addEventListener('DOMContentLoaded', async () => {
  document.querySelectorAll('.topTab').forEach(b => {
    b.addEventListener('click', () => SV.switch(b.dataset.view));
  });
  const qp = new URLSearchParams(location.search);
  const want = qp.get('view') || (location.hash.match(/^#view=(\w+)$/) || [])[1];
  const known = ['persons', 'entities', 'works'];
  if (want && known.includes(want)) {
    await SV.switch(want);
    // 视图就绪后直接定位深链条目（不再猜延迟）
    const target = qp.get('p') || qp.get('e') || qp.get('w');
    NA.deepLinkCard(target, '#' + want[0] + 'timeline');
  }
});
})();
