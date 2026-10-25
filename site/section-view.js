(function () {
'use strict';
/* section-view.js — 主页多视图切换：编年史 / 人物志 / 世家志 / 作品志
 * 设计：编年史视图保持 app.js 原逻辑不动；其余三个视图由本文件用同一套
 * 长卷骨架（eraSec/yearGroup/yBadge/card + cMore/cBody 行内展开）渲染。
 * 首次切到某视图才拉数据（fetchGz + DecompressionStream，与子页一致）。
 */

const SV = {
  ready: {},          // 各视图初始化标记
  current: 'annals',

  async fetchGz(url) {
    const v = '20261025a';
    if (typeof DecompressionStream !== 'undefined') {
      try {
        const r = await fetch(url + '.gz?v=' + v);
        if (r.ok) return await new Response((await r.blob()).stream().pipeThrough(new DecompressionStream('gzip'))).json();
      } catch (e) { /* 回退明文 */ }
    }
    const r = await fetch(url + '?v=' + v);
    if (!r.ok) throw new Error('HTTP ' + r.status);
    return r.json();
  },

  /* ── 分卷定义 ── */
  P_ERAS: [
    { name: '文艺复兴与启蒙', range: [-Infinity, 1700] },
    { name: '近代先驱', range: [1700, 1900] },
    { name: '世纪之交', range: [1900, 1930] },
    { name: '战后与重建', range: [1930, 1950] },
    { name: '共和国一代', range: [1950, 1970] },
    { name: '黄金一代', range: [1970, 1985] },
    { name: '千禧一代', range: [1985, Infinity] },
  ],
  E_ERAS: [
    { name: '奠基纪元', range: [-Infinity, 1990] },
    { name: '拨号纪元', range: [1990, 1999] },
    { name: '门户纪元', range: [1999, 2005] },
    { name: 'Web2.0 纪元', range: [2005, 2011] },
    { name: '移动纪元', range: [2011, 2016] },
    { name: '智能纪元', range: [2016, Infinity] },
  ],
  W_ERAS: [
    { name: '纸质与胶片时代', range: [-Infinity, 1994] },
    { name: '拨号时代', range: [1994, 2000] },
    { name: '门户与光碟时代', range: [2000, 2005] },
    { name: 'Web2.0 时代', range: [2005, 2011] },
    { name: '移动与流媒体时代', range: [2011, 2017] },
    { name: '算法与国创时代', range: [2017, Infinity] },
  ],
  FIELDS: { ai: 'AI', internet: '互联网', hardware: '硬件制造', company: '公司商业', game: '游戏电竞', creator: '创作者', science: '科学', finance: '金融', media: '媒体', sport: '体育' },
  FCOLOR: { ai: '#c96a93', internet: '#5b9bd5', hardware: '#d08a4e', company: '#3aa891', game: '#8b6fc9', creator: '#c9b458', science: '#7ba05b', finance: '#4a9e8f', media: '#c9a86a', sport: '#c9584f' },
  TYPES: { company: '企业', community: '社区', media: '媒体', service: '服务', infrastructure: '基础设施', organization: '机构', institution: '机构', game: '游戏' },
  TCOLOR: { company: '#3aa891', community: '#5b9bd5', media: '#c9a86a', service: '#c96a93', infrastructure: '#7ba05b', organization: '#8a919e', game: '#8b6fc9' },
  WTYPES: { film: '电影', tv: '剧集', book: '图书', netnovel: '网络文学', music: '音乐', game: '游戏', comic: '动画漫画', documentary: '纪录片', variety: '综艺' },
  WTCOLOR: { film: '#c9584f', tv: '#c96a93', book: '#3aa891', netnovel: '#5b9bd5', music: '#c9a86a', game: '#8b6fc9', comic: '#d08a4e', documentary: '#7ba05b', variety: '#c9b458' },
  SCONF: { active: 'v', declined: 's', closed: 'u' },

  eraIndexOf(eras, y) { return eras.findIndex(e => y >= e.range[0] && y < e.range[1]); },

  /** 通用长卷渲染：按年份组 → 中轴交替卡片 */
  renderLongScroll(rootSel, eras, items, yearOf, cardFn, countUnit) {
    const root = document.querySelector(rootSel);
    root.innerHTML = '';
    let shown = 0;
    eras.forEach((era, ei) => {
      const list = items.filter(it => this.eraIndexOf(eras, +yearOf(it) || 0) === ei)
        .sort((a, b) => yearOf(a).localeCompare(yearOf(b)));
      if (!list.length) return;
      const sec = document.createElement('section');
      sec.className = 'eraSec';
      const ys = list.map(it => +yearOf(it));
      sec.innerHTML = `<div class="eraHead"><span class="eraPill">${era.name}<em>${Math.min(...ys)}–${Math.max(...ys)}</em></span><span class="eraLine"></span><span class="eraCount">${list.length} ${countUnit}</span></div><div class="eraBody"></div>`;
      const body = sec.querySelector('.eraBody');
      const byYear = new Map();
      for (const it of list) {
        const y = yearOf(it);
        if (!byYear.has(y)) byYear.set(y, []);
        byYear.get(y).push(it);
      }
      let flip = ei % 2;
      for (const [year, its] of byYear) {
        const g = document.createElement('div');
        g.className = 'yearGroup';
        g.innerHTML = `<div class="yBadge"><span>${year}</span>${its.length > 1 ? `<small>${its.length}</small>` : ''}</div><div class="cards"></div>`;
        const cards = g.querySelector('.cards');
        for (const it of its) {
          const c = cardFn(it);
          if (flip) c.classList.add('right');
          cards.appendChild(c);
          flip = 1 - flip;
          shown++;
        }
        body.appendChild(g);
      }
      root.appendChild(sec);
    });
    if (!shown) root.innerHTML = '<div class="empty">没有匹配的条目——换个关键词试试</div>';
    return shown;
  },

  /* 行内展开事件委托（每个视图容器挂一次） */
  wireExpand(rootSel) {
    document.querySelector(rootSel).addEventListener('click', ev => {
      const more = ev.target.closest('.cMore');
      if (more) { more.closest('.card').classList.toggle('open'); return; }
      const card = ev.target.closest('.card');
      if (card && !ev.target.closest('a')) card.classList.add('open');
    });
  },

  /* ── 人物志 ── */
  async initPersons() {
    if (this.ready.persons) return;
    const data = await this.fetchGz('persons/data.json');
    this.HERO.persons.sub = `${data.persons.length} 位塑造时代的人物，按出生年代纵览——点击卡片展开完整人生历程。`;
    let filter = 'all', q = '';
    const bar = document.getElementById('pFieldRow');
    const present = [...new Set(data.persons.map(p => p.field))];
    for (const f of present) {
      const n = data.persons.filter(p => p.field === f).length;
      const b = document.createElement('button');
      b.className = 'chip on'; b.dataset.f = f;
      b.innerHTML = `<span style="color:${this.FCOLOR[f] || '#8a919e'}">●</span> ${this.FIELDS[f] || f}<span class="n">${n}</span>`;
      b.onclick = () => {
        filter = filter === f ? 'all' : f;
        bar.querySelectorAll('.chip').forEach(x => x.classList.toggle('on', x.dataset.f === filter || filter === 'all'));
        draw();
      };
      bar.appendChild(b);
    }
    const dsh = t => String(t.date).slice(0, t.acc === 'year' ? 4 : t.acc === 'month' ? 7 : 10);
    const cardFn = p => {
      const el = document.createElement('div');
      el.className = 'card in';
      el.dataset.id = p.id;
      const life = `${String(p.birth).slice(0, 4)}–${p.death ? String(p.death).slice(0, 4) : ''}`;
      const alive = p.death ? '<span class="cConf">已故</span>' : '<span class="cConf v">在世</span>';
      const tl = p.timeline.map(t => `<li><span class="td">${dsh(t)}</span><span class="tx">${esc(t.text)}</span></li>`).join('');
      const ach = (p.achievements || []).map(a => `· ${esc(a)}`).join('<br>');
      const ctzs = (p.controversies || []).length
        ? `<div class="sec"><span class="lab">争议记录</span>${p.controversies.map(c => `<div class="ctzBox">${esc(c)}</div>`).join('')}</div>` : '';
      const src = p.sources.map(s => `<li><a href="${esc(safeUrl(s.url))}" target="_blank" rel="noopener">${esc(s.title)}</a></li>`).join('');
      const relE = (p.related_entities || []).length
        ? `<div class="sec"><span class="lab">相关世家</span><div class="relRow">${p.related_entities.map(r => `<a class="relChip" href="?view=entities&e=${r.id}" data-goto-entities="${r.id}">${esc(r.name)}</a>`).join('')}</div></div>` : '';
      el.innerHTML = `
        <div class="cHead">
          <span class="cDate">${life}</span>
          <span class="cDot" style="--c:${this.FCOLOR[p.field] || '#8a919e'}"></span><span>${this.FIELDS[p.field] || p.field}</span>
          ${alive}
          <span class="cAcc">${p.region === 'cn' ? '中国' : '国际'}</span>
        </div>
        <h3 class="cTitle"><a>${esc(p.name)}${p.en_name ? ` <span class="arrow" style="font-family:var(--mono);font-size:.72rem;color:var(--faint)">${esc(p.en_name)}</span>` : ''}</a></h3>
        <p class="cSum">${esc(p.headline)}。${esc(p.summary_30s.slice(0, 90))}${p.summary_30s.length > 90 ? '…' : ''}</p>
        <button class="cMore">展开人生历程 <i>∨</i></button>
        <div class="cBody"><div class="cBodyInner">
          <div class="sec"><span class="lab">小传</span><p>${esc(p.bio || p.summary_30s)}</p></div>
          <div class="sec"><span class="lab">人生历程</span><ul class="tlList">${tl}</ul></div>
          ${ach ? `<div class="sec"><span class="lab">关键成就</span><p>${ach}</p></div>` : ''}
          <div class="sec"><span class="lab">现状与遗产</span><div class="legacyBox">${esc(p.legacy || (p.death ? '其影响已沉淀为行业史的一部分。' : '仍在活跃，故事未完。'))}</div></div>${ctzs}${relE}
          <div class="sec"><span class="lab">来源</span><ul class="srcList">${src}</ul></div>
        </div></div>`;
      return el;
    };
    const draw = () => {
      const list = data.persons.filter(p => (filter === 'all' || p.field === filter) && matchQ(p, q, ['name', 'en_name', 'headline', 'tags']));
      this.renderLongScroll('#ptimeline', this.P_ERAS, list, p => String(p.birth || '0000').slice(0, 4), cardFn, '人');
    };
    wireSearch('pq', v => { q = v; draw(); });
    document.getElementById('personsIntro').textContent = `从达·芬奇到韦东奕，${data.persons.length} 位塑造时代的人物——按出生年代纵览，点击卡片展开完整人生历程。`;
    this.wireExpand('#ptimeline');
    draw();
    this.ready.persons = true;
  },

  /* ── 世家志 ── */
  async initEntities() {
    if (this.ready.entities) return;
    const data = await this.fetchGz('entities/data.json');
    this.HERO.entities.sub = `${data.entities.length} 家企业与社区的完整兴衰史——按创立年代纵览，点击卡片展开。`;
    let filter = 'all', q = '';
    const bar = document.getElementById('eTypeRow');
    const present = [...new Set(data.entities.map(e => e.type))];
    for (const f of present) {
      const n = data.entities.filter(e => e.type === f).length;
      const b = document.createElement('button');
      b.className = 'chip on'; b.dataset.f = f;
      b.innerHTML = `<span style="color:${this.TCOLOR[f] || '#8a919e'}">●</span> ${this.TYPES[f] || f}<span class="n">${n}</span>`;
      b.onclick = () => {
        filter = filter === f ? 'all' : f;
        bar.querySelectorAll('.chip').forEach(x => x.classList.toggle('on', x.dataset.f === filter || filter === 'all'));
        draw();
      };
      bar.appendChild(b);
    }
    const dsh = t => String(t.date).slice(0, t.acc === 'year' ? 4 : t.acc === 'month' ? 7 : 10);
    const cardFn = e => {
      const el = document.createElement('div');
      el.className = 'card in';
      el.dataset.id = e.id;
      const span = e.dissolved ? `${String(e.founded).slice(0, 4)}–${String(e.dissolved).slice(0, 4)}` : `${String(e.founded).slice(0, 4)}–今`;
      const st = `<span class="cConf ${this.SCONF[e.status] || ''}">${STATUS_LABEL[e.status] || e.status}</span>`;
      const tl = e.timeline.map(t => `<li><span class="td">${dsh(t)}</span><span class="tx">${esc(t.text)}</span></li>`).join('');
      const ms = (e.milestones || []).map(a => `· ${esc(a)}`).join('<br>');
      const ctzs = (e.controversies || []).length
        ? `<div class="sec"><span class="lab">争议记录</span>${e.controversies.map(c => `<div class="ctzBox">${esc(c)}</div>`).join('')}</div>` : '';
      const src = e.sources.map(s => `<li><a href="${esc(safeUrl(s.url))}" target="_blank" rel="noopener">${esc(s.title)}</a></li>`).join('');
      const rel = (e.related_persons || []).length
        ? `<div class="sec"><span class="lab">相关人物</span><div class="relRow">${e.related_persons.map(r => `<a class="relChip" href="?view=persons&p=${r.id}" data-goto-persons="${r.id}">${esc(r.name)}</a>`).join('')}</div></div>` : '';
      el.innerHTML = `
        <div class="cHead">
          <span class="cDate">${span}</span>
          <span class="cDot" style="--c:${this.TCOLOR[e.type] || '#8a919e'}"></span><span>${this.TYPES[e.type] || e.type}</span>
          ${st}
          <span class="cAcc">${REGION_LABEL[e.region] || ''}</span>
        </div>
        <h3 class="cTitle"><a>${esc(e.name)}${e.en_name ? ` <span class="arrow" style="font-family:var(--mono);font-size:.72rem;color:var(--faint)">${esc(e.en_name)}</span>` : ''}</a></h3>
        <p class="cSum">${esc(e.headline)}。${esc(e.summary_30s.slice(0, 90))}${e.summary_30s.length > 90 ? '…' : ''}</p>
        <button class="cMore">展开兴衰历程 <i>∨</i></button>
        <div class="cBody"><div class="cBodyInner">
          <div class="sec"><span class="lab">兴衰概述</span><p>${esc(e.bio || e.summary_30s)}</p></div>
          <div class="sec"><span class="lab">兴衰历程</span><ul class="tlList">${tl}</ul></div>
          ${ms ? `<div class="sec"><span class="lab">关键数字</span><p>${ms}</p></div>` : ''}
          <div class="sec"><span class="lab">现状与遗产</span><div class="legacyBox">${esc(e.legacy)}</div></div>${ctzs}${rel}
          <div class="sec"><span class="lab">来源</span><ul class="srcList">${src}</ul></div>
        </div></div>`;
      return el;
    };
    const draw = () => {
      const list = data.entities.filter(e => (filter === 'all' || e.type === filter) && matchQ(e, q, ['name', 'en_name', 'headline', 'hq', 'tags']));
      this.renderLongScroll('#etimeline', this.E_ERAS, list, e => String(e.founded || '0000').slice(0, 4), cardFn, '家');
    };
    wireSearch('eq', v => { q = v; draw(); });
    document.getElementById('entitiesIntro').textContent = `${data.entities.length} 家世家——企业、社区、机构的完整兴衰史，从创立到巅峰到谢幕。按创立年代纵览，点击卡片展开完整兴衰史。`;
    this.wireExpand('#etimeline');
    draw();
    this.ready.entities = true;
  },

  /* ── 作品志 ── */
  async initWorks() {
    if (this.ready.works) return;
    const data = await this.fetchGz('works/data.json');
    this.HERO.works.sub = `${data.works.length} 部影视文学音乐游戏经典——按发布年代纵览，点击卡片展开生命线。`;
    let filter = 'all', q = '';
    const bar = document.getElementById('wTypeRow');
    const present = [...new Set(data.works.map(w => w.type))];
    for (const f of present) {
      const n = data.works.filter(w => w.type === f).length;
      const b = document.createElement('button');
      b.className = 'chip on'; b.dataset.f = f;
      b.innerHTML = `<span style="color:${this.WTCOLOR[f] || '#8a919e'}">●</span> ${this.WTYPES[f] || f}<span class="n">${n}</span>`;
      b.onclick = () => {
        filter = filter === f ? 'all' : f;
        bar.querySelectorAll('.chip').forEach(x => x.classList.toggle('on', x.dataset.f === filter || filter === 'all'));
        draw();
      };
      bar.appendChild(b);
    }
    const dsh = t => String(t.date).slice(0, t.acc === 'year' ? 4 : t.acc === 'month' ? 7 : 10);
    const cardFn = w => {
      const el = document.createElement('div');
      el.className = 'card in';
      el.dataset.id = w.id;
      const tl = w.timeline.map(t => `<li><span class="td">${dsh(t)}</span><span class="tx">${esc(t.text)}</span></li>`).join('');
      const quotes = (w.quotes || []).length
        ? `<div class="sec"><span class="lab">经典回响</span>${w.quotes.map(q2 => `<div class="quoteBox">${esc(q2)}</div>`).join('')}</div>` : '';
      const src = w.sources.map(s => `<li><a href="${esc(safeUrl(s.url))}" target="_blank" rel="noopener">${esc(s.title)}</a></li>`).join('');
      el.innerHTML = `
        <div class="cHead">
          <span class="cDate">${String(w.released).slice(0, 4)}</span>
          <span class="cDot" style="--c:${this.WTCOLOR[w.type] || '#8a919e'}"></span><span>${this.WTYPES[w.type] || w.type}</span>
          <span class="cAcc">${esc((w.creators || '').slice(0, 18))}</span>
        </div>
        <h3 class="cTitle"><a>${esc(w.title)}${w.en_title ? ` <span class="arrow" style="font-family:var(--mono);font-size:.72rem;color:var(--faint)">${esc(w.en_title)}</span>` : ''}</a></h3>
        <p class="cSum">${esc(w.headline)}。${esc(w.summary_30s.slice(0, 90))}${w.summary_30s.length > 90 ? '…' : ''}</p>
        <button class="cMore">展开作品生命线 <i>∨</i></button>
        <div class="cBody"><div class="cBodyInner">
          <div class="sec"><span class="lab">作品小传</span><p>${esc(w.bio || w.summary_30s)}</p></div>
          <div class="sec"><span class="lab">生命线</span><ul class="tlList">${tl}</ul></div>
          ${quotes}
          <div class="sec"><span class="lab">精神遗产</span><div class="legacyBox">${esc(w.legacy)}</div></div>
          <div class="sec"><span class="lab">来源</span><ul class="srcList">${src}</ul></div>
        </div></div>`;
      return el;
    };
    const draw = () => {
      const list = data.works.filter(w => (filter === 'all' || w.type === filter) && matchQ(w, q, ['title', 'en_title', 'creators', 'headline', 'tags']));
      this.renderLongScroll('#wtimeline', this.W_ERAS, list, w => String(w.released || '0000').slice(0, 4), cardFn, '部');
    };
    wireSearch('wq', v => { q = v; draw(); });
    document.getElementById('worksIntro').textContent = `${data.works.length} 部作品——影视、文学、音乐、游戏与动画综艺，按发布年代纵览，点击卡片展开完整作品生命线。`;
    this.wireExpand('#wtimeline');
    draw();
    this.ready.works = true;
  },

  /* ── 视图切换 ── */
  HERO: {
    annals: null,
    persons: { eyebrow: '人物志 · 知名人士人生历程', title: '人物<em>志</em> · 一条条人生长卷', sub: '370 位塑造时代的人物，按出生年代纵览——点击卡片展开完整人生历程。' },
    entities: { eyebrow: '世家志 · 兴衰长卷', title: '世家<em>志</em> · 为每一家立传', sub: '236 家企业与社区的完整兴衰史——按创立年代纵览，点击卡片展开。' },
    works: { eyebrow: '作品志 · 精神地标', title: '作品<em>志</em> · 陪伴大众的创作物', sub: '159 部影视文学音乐游戏经典——按发布年代纵览，点击卡片展开生命线。' },
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
    history.replaceState(null, '', name === 'annals' ? '#' : '#view=' + name);
    const pane = document.getElementById('view-' + name);
    if (pane && name !== 'annals') {
      pane.querySelector('.toolbar')?.scrollIntoView({ block: 'start', behavior: 'instant' });
      try {
        await this['init' + name[0].toUpperCase() + name.slice(1)]();
      } catch (err) {
        // persons/entities/works 的首字母与各长卷容器 id 前缀一一对应（p/e/w + timeline）
        const root = document.querySelector('#' + name[0] + 'timeline');
        if (root) root.innerHTML = `<div class="empty">数据加载失败（${esc(String(err.message || err))}）</div>`;
      }
    }
  },
};

const STATUS_LABEL = { active: '活跃', declined: '衰落', acquired: '被收购', privatized: '已退市', closed: '关停' };
const REGION_LABEL = { cn: '中国', world: '世界' };
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const safeUrl = u => /^https?:\/\//i.test(String(u)) ? u : '#';
function matchQ(item, q, fields) {
  const s = q.trim().toLowerCase();
  if (!s) return true;
  const hay = fields.map(f => Array.isArray(item[f]) ? item[f].join(' ') : (item[f] || '')).join(' ').toLowerCase();
  return hay.includes(s);
}
function wireSearch(inputId, cb) {
  let t;
  document.getElementById(inputId).addEventListener('input', e => {
    clearTimeout(t);
    t = setTimeout(() => cb(e.target.value), 160);
  });
}

/* ── 启动：Tab 事件 + 深链 ── */
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.topTab').forEach(b => {
    b.addEventListener('click', () => SV.switch(b.dataset.view));
  });
  const want = new URLSearchParams(location.search).get('view') || (location.hash.match(/^#view=(\w+)$/) || [])[1];
  const known = ['persons', 'entities', 'works'];
  if (want && known.includes(want)) {
    SV.switch(want);
    // 深链到具体条目
    const pid = new URLSearchParams(location.search).get('p');
    const eid = new URLSearchParams(location.search).get('e');
    const wid = new URLSearchParams(location.search).get('w');
    const target = pid || eid || wid;
    if (target) setTimeout(() => {
      const sel = pid ? '#ptimeline' : eid ? '#etimeline' : '#wtimeline';
      const c = document.querySelector(`${sel} .card[data-id="${target}"]`);
      if (c) {
        c.classList.add('open');
        c.scrollIntoView({ block: 'center', behavior: 'instant' });
        c.style.outline = '2px solid var(--accent)';
        setTimeout(() => { c.style.outline = ''; }, 2600);
      }
    }, 600);
  }
});
})();
