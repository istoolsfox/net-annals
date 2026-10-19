/* 互联网编年史 · 长卷 v3 — 分层架构
 *
 * Store   ：唯一数据与筛选状态源，提供选择器（selector）。视图只读 Store，不持有数据副本。
 * Timeline：纯渲染层。renderEra(i) 幂等：同一时代无论被谁触发（滚动/跳转/筛选），
 *           都走同一条渲染路径，渲染结果只由 Store 的选择器决定。
 * Nav     ：导航层。跳转 = 先同步渲染目标时代 → 再瞬时定位（禁用平滑，杜绝长途滑行）。
 * Toolbar ：控制层。只负责把用户操作转成 Store 状态变更 + 通知 Timeline 重绘。
 *
 * 原则：渲染幂等（可重入）、分层单向依赖（Toolbar→Store→Timeline）、
 *       过滤器开闭（新增过滤条件=加一个谓词，不改核心）、懒渲染只做性能优化不做正确性依赖。
 */
'use strict';

/* ── 配置常量 ─────────────────── */
const ERAS = [
  { name: '接入前史', range: [1986, 1994.4] },
  { name: '拨号时代', range: [1994.4, 2000] },
  { name: '门户与泡沫', range: [2000, 2003] },
  { name: 'Web2.0 前夜', range: [2003, 2005] },
  { name: 'Web2.0', range: [2005, 2010] },
  { name: '移动互联网', range: [2010, 2015] },
  { name: '移动成熟', range: [2015, 2020] },
  { name: '疫情与智能', range: [2020, 2027] },
];
const CATS = [
  { k: 'milestone', name: '时代转折', c: '#c9a86a' },
  { k: 'internet', name: '互联网', c: '#5b9bd5' },
  { k: 'tech', name: '科技软件', c: '#8b6fc9' },
  { k: 'hardware', name: '硬件', c: '#d08a4e' },
  { k: 'company', name: '公司商业', c: '#3aa891' },
  { k: 'product', name: '产品服务', c: '#c96a93' },
  { k: 'national', name: '国家大事', c: '#c9584f' },
  { k: 'world', name: '世界大事', c: '#8a919e' },
  { k: 'society', name: '民间生活', c: '#7ba05b' },
  { k: 'culture', name: '流行文化', c: '#c9b458' },
  { k: 'economy', name: '经济金融', c: '#4a9e8f' },
];
const CAT = Object.fromEntries(CATS.map(c => [c.k, c]));
const CONF = { verified: ['实证', 'v'], 'single-source': ['单一来源', 's'], uncertain: ['存疑', 'u'] };

/* ── UIState：纯视图状态（与数据过滤状态分离） ─────────────────── */
const UIState = { expandAll: false };

/* ── Store：状态 + 选择器（唯一事实源） ─────────────────── */
const Store = {
  events: [],
  ready: false,
  filters: { cats: new Set(CATS.map(c => c.k)), q: '', mileOnly: false },

  /** 事件所属时代索引；越界钳制到最后一个时代（杜绝事件被静默丢弃） */
  eraIndex(dateStr) {
    const yf = +dateStr.slice(0, 4) + (+dateStr.slice(5, 7) - 1) / 12;
    const i = ERAS.findIndex(e => yf >= e.range[0] && yf < e.range[1]);
    return i === -1 ? (yf < ERAS[0].range[0] ? 0 : ERAS.length - 1) : i;
  },

  /** 过滤谓词表：开闭原则——新增过滤条件只需追加谓词 */
  predicates: [
    (e, f) => f.cats.has(e.category),
    (e, f) => !f.mileOnly || !!e.milestone,
    (e, f) => {
      const q = f.q.trim().toLowerCase();
      return !q || [e.title, e.summary_30s, e.detail, ...(e.tags || []), e.date].join(' ').toLowerCase().includes(q);
    },
  ],
  passes(e) { return this.predicates.every(p => p(e, this.filters)); },

  /** 选择器：某时代的可见事件（按日期有序） */
  eventsOf(eraIdx) { return this.events.filter(e => this.eraIndex(e.date) === eraIdx && this.passes(e)); },
  visibleCount() { return this.events.filter(e => this.passes(e)).length; },

  setFilter(patch) { Object.assign(this.filters, patch); },
};

/* ── Timeline：纯渲染（幂等） ─────────────────── */
const Timeline = {
  rendered: new Set(),
  io: null, reveal: null,

  init() {
    this.io = new IntersectionObserver(es => {
      for (const en of es) if (en.isIntersecting) this.renderEra(+en.target.dataset.era);
    }, { rootMargin: '900px 0px' });
    this.reveal = new IntersectionObserver(es => {
      for (const en of es) if (en.isIntersecting) { en.target.classList.add('in'); this.reveal.unobserve(en.target); }
    }, { rootMargin: '30px' });
  },

  /** 建时代空壳（含时代头）。幂等：整体重建。 */
  buildSections() {
    const tl = document.getElementById('timeline');
    tl.innerHTML = '';
    this.rendered.clear();
    ERAS.forEach((era, i) => {
      const sec = document.createElement('section');
      sec.className = 'eraSec'; sec.id = `era-${i}`; sec.dataset.era = i;
      sec.setAttribute('aria-label', era.name);
      sec.innerHTML = `<div class="eraHead"></div><div class="eraBody"></div>`;
      tl.appendChild(sec);
      this.io.observe(sec);
      this.renderEraHead(i);       // 时代头永远同步渲染（轻量）
      this.renderEra(i);           // 若已在视口内立即出内容
    });
  },

  renderEraHead(i) {
    const evs = Store.eventsOf(i);
    const era = ERAS[i];
    const years = evs.map(e => +e.date.slice(0, 4));
    const span = evs.length ? `${Math.min(...years)}–${Math.max(...years)}` : `${Math.floor(era.range[0])}–${Math.ceil(era.range[1])}`;
    document.querySelector(`#era-${i} .eraHead`).innerHTML =
      `<span class="eraPill">${era.name}<em>${span}</em></span><span class="eraLine"></span><span class="eraCount">${evs.length} 条</span>`;
  },

  /** 渲染某时代的卡片体。幂等：已渲染则跳过；筛选变化由 rebuild() 统一清空后重渲。 */
  renderEra(i) {
    if (this.rendered.has(i)) return;
    this.rendered.add(i);
    const body = document.querySelector(`#era-${i} .eraBody`);
    if (!body) return;
    const evs = Store.eventsOf(i);
    body.innerHTML = '';
    if (!evs.length) { body.innerHTML = `<div class="empty">当前筛选下本时代暂无条目</div>`; return; }

    const byYear = new Map();
    for (const e of evs) { const y = e.date.slice(0, 4); if (!byYear.has(y)) byYear.set(y, []); byYear.get(y).push(e); }
    let flip = i % 2;
    for (const [year, list] of byYear) {
      const g = document.createElement('div');
      g.className = 'yearGroup';
      g.innerHTML = `<div class="yBadge"><span>${year}</span>${list.length > 1 ? `<small>${list.length}</small>` : ''}</div><div class="cards"></div>`;
      const cards = g.querySelector('.cards');
      for (const e of list) {
        const holder = document.createElement('div');
        holder.className = 'card' + (flip ? ' right' : '') + (e.milestone ? ' mile' : '') + (UIState.expandAll ? ' open' : '');
        holder.dataset.id = e.id;
        holder.innerHTML = this.cardHtml(e);
        cards.appendChild(holder);
        this.reveal.observe(holder);
        flip = 1 - flip;
      }
      body.appendChild(g);
      // 视口内的卡片立即置亮：跳转/筛选后不等待 IO 回调窗口
      requestAnimationFrame(() => {
        for (const holder of body.querySelectorAll('.card:not(.in)')) {
          const r = holder.getBoundingClientRect();
          if (r.top < innerHeight && r.bottom > 0) holder.classList.add('in');
        }
      });
    }
  },

  cardHtml(e) {
    const conf = CONF[e.date_confidence] || CONF.uncertain;
    const cat = CAT[e.category] || { name: e.category, c: '#8a919e' };
    const src0 = e.sources[0] || {};
    const acc = e.date_accuracy !== 'exact' ? `<span class="cAcc">${e.date_accuracy === 'month' ? '精确到月' : '精确到年'}</span>` : '';
    const long = e.summary_30s.length > 150;
    const sum = long ? e.summary_30s.slice(0, 150) + '…' : e.summary_30s;
    return `
      <div class="cHead">
        <span class="cDate">${e.date.replaceAll('-', '.')}</span>
        <span class="cDot" style="--c:${cat.c}"></span><span>${cat.name}</span>
        ${e.milestone ? '<span style="color:var(--accent)">★</span>' : ''}
        <span class="cConf ${conf[1]}">${conf[0]}</span>${acc}
        <span class="cAcc">${e.region === 'cn' ? '中国' : '世界'}</span>
      </div>
      <h3 class="cTitle"><a href="${esc(safeUrl(src0.url))}" target="_blank" rel="noopener" title="点击标题跳转原文">${esc(e.title)} <span class="arrow">↗</span></a></h3>
      <p class="cSum">${esc(sum)}${long ? ' <span class="hint">展开看全文</span>' : ''}</p>
      <button class="cMore">展开经过与影响 <i>∨</i></button>
      <div class="cBody">
        <div class="sec"><span class="lab">经过</span><p>${esc(e.detail)}</p></div>
        <div class="sec"><span class="lab">影响</span><p>${esc(e.impact)}</p></div>
        <div class="sec"><span class="lab">后续</span><p>${esc(e.aftermath)}</p></div>
        <div class="sec"><span class="lab">数据来源</span><ul class="srcList">${e.sources.map(s =>
          `<li><a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.title)}</a><span class="tp">${esc(s.type || '')}</span></li>`).join('')}</ul></div>
      </div>`;
  },

  /** 筛选变化：全部重建（简单正确优先；900 条的字符串过滤开销可忽略） */
  rebuild() {
    const n = Store.visibleCount();
    document.getElementById('qCount').textContent = n === Store.events.length ? '' : `${n} 条`;
    this.buildSections();
  },

  /** 导航：先同步渲染目标时代，再瞬时定位（杜绝长滑与落点漂移）。boot 未就绪时排队。 */
  jumpTo(i) {
    if (!Store.ready) { (this._pending ??= new Set()).add(i); return; }
    this._jump(i);
  },
  flushPending() {
    if (!this._pending) return;
    for (const i of this._pending) this._jump(i);
    this._pending.clear();
  },
  _jump(i) {
    const sec = document.getElementById(`era-${i}`);
    if (!sec) return;
    this.renderEra(i);                                // 渲染先于滚动
    const toolbarH = document.getElementById('toolbar').getBoundingClientRect().height;
    const y = sec.getBoundingClientRect().top + window.scrollY - toolbarH - 18;
    window.scrollTo({ top: y, behavior: 'instant' }); // 瞬时定位
  },
};

/* ── 工具函数 ─────────────────── */
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const safeUrl = u => /^https?:\/\//i.test(String(u)) ? u : '#';   // 纵深防御：只放行 http(s)
const $ = s => document.querySelector(s);

/* ── Toolbar：控制层（用户操作 → Store 变更 → Timeline 重绘） ─────────────────── */
const Toolbar = {
  init() {
    const jump = $('#eraJump');
    for (const [i, era] of ERAS.entries()) {
      const b = document.createElement('button');
      b.className = 'chip'; b.textContent = era.name; b.dataset.era = i;
      b.onclick = () => Timeline.jumpTo(i);
      jump.appendChild(b);
    }
    const row = $('#catRow');
    for (const c of CATS) {
      const n = Store.events.filter(e => e.category === c.k).length;
      const b = document.createElement('button');
      b.className = 'chip on';
      b.innerHTML = `<span style="color:${c.c}">●</span> ${c.name}<span class="n">${n}</span>`;
      b.onclick = () => {
        const f = Store.filters;
        if (f.cats.has(c.k) && f.cats.size === 1) return;
        f.cats.has(c.k) ? f.cats.delete(c.k) : f.cats.add(c.k);
        b.classList.toggle('on', f.cats.has(c.k));
        b.classList.toggle('off', !f.cats.has(c.k));
        Timeline.rebuild();
      };
      row.appendChild(b);
    }
    let t;
    $('#q').addEventListener('input', e => {
      clearTimeout(t);
      t = setTimeout(() => { Store.setFilter({ q: e.target.value }); Timeline.rebuild(); }, 180);
    });
    $('#expandAll').onclick = () => {
      UIState.expandAll = !UIState.expandAll;
      const on = UIState.expandAll;
      $('#expandAll').classList.toggle('on', on);
      $('#expandAll').textContent = on ? '全部收起' : '全部展开';
      document.querySelectorAll('.card').forEach(c => c.classList.toggle('open', on));
    };
    $('#mileOnly').onclick = () => {
      Store.setFilter({ mileOnly: !Store.filters.mileOnly });
      $('#mileOnly').classList.toggle('on', Store.filters.mileOnly);
      Timeline.rebuild();
    };
    $('#themeBtn').onclick = () => {
      const next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
      applyTheme(next);
    };
    $('#ctaEras').onclick = e => { e.preventDefault(); Timeline.jumpTo(0); };
    $('#toTop').onclick = () => window.scrollTo({ top: 0, behavior: 'instant' });
    addEventListener('scroll', () => {
      const h = document.documentElement;
      $('#progress').style.width = (h.scrollTop / (h.scrollHeight - h.clientHeight) * 100) + '%';
      $('#toTop').classList.toggle('show', h.scrollTop > 800);
      this.markCurrentEra();
    }, { passive: true });

    // 时代长卷内的事件代理：展开/收起
    $('#timeline').addEventListener('click', ev => {
      const more = ev.target.closest('.cMore');
      if (more) { more.closest('.card').classList.toggle('open'); return; }
      const card = ev.target.closest('.card');
      if (card && !ev.target.closest('a')) card.classList.add('open');
    });
  },

  /** 当前所在时代高亮（回答"我在哪个时代"） */
  markCurrentEra() {
    let cur = 0;
    for (const [i] of ERAS.entries()) {
      const sec = document.getElementById(`era-${i}`);
      if (sec && sec.getBoundingClientRect().top <= 280) cur = i;
    }
    document.querySelectorAll('#eraJump .chip').forEach((b, i) => b.classList.toggle('on', i === cur));
  },
};

function applyTheme(t) {
  document.documentElement.dataset.theme = t;
  localStorage.setItem('na-theme', t);
}

/* ── 启动 ─────────────────── */
async function boot() {
  applyTheme(localStorage.getItem('na-theme') || (matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark'));
  try {
    const res = await fetch('data.json');
    if (!res.ok) throw new Error(res.status);
    const data = await res.json();
    Store.events = data.events;
    const last = Store.events[Store.events.length - 1].date;
    const nV = Store.events.filter(e => e.date_confidence === 'verified').length;
    $('#heroEyebrow').textContent = `1986 — ${last.slice(0, 4)} · ${Store.events.length} 条 · 精确到日 · 每条可溯源`;
    $('#introText').textContent = `从 1986 年中关村的一间实验室，到 2026 年每个人口袋里的人工智能——本卷收录 ${Store.events.length} 条被日期钉住的时刻：互联网、科技、硬件、公司、国家大事、世界大事、民间生活与流行文化。其中 ${nV.toLocaleString()} 条经双源实证，其余均标明来源与置信度。点击任何标题可跳转原文。`;
    $('#colMeta').textContent = `构建于 ${(data.generated || '').replace('T', ' ').slice(0, 16)} · ${Store.events.length} 条事件 · 来源 ${new Set(Store.events.flatMap(e => e.sources.map(s => s.url))).size} 个 · 数据持续增补中`;
    Timeline.init();
    Toolbar.init();
    Timeline.buildSections();
    Store.ready = true;
    Timeline.flushPending();
  } catch (err) {
    document.getElementById('timeline').innerHTML = `<div class="empty">数据加载失败（${esc(err.message)}）。请先运行 scripts/deploy.sh 或 build.sh。</div>`;
  }
}

boot();
