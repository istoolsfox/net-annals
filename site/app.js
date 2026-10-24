/* 互联网编年史 · 长卷 v3 — 分层架构
 *
 * Store   ：唯一数据与筛选状态源，提供选择器（selector）。视图只读 Store，不持有数据副本。
 *           数据按时代分片（site/data/shard-*.json）惰性加载：Store.shards[i] 只存已加载分片。
 * Timeline：纯渲染层。renderEra(i) 幂等：同一时代无论被谁触发（滚动/跳转/筛选），
 *           都走同一条渲染路径，渲染结果只由 Store 的选择器决定。
 *           懒加载 + 懒渲染：boot 只建时代空壳，IntersectionObserver 触发时才取分片、建卡片 DOM。
 * Nav     ：导航层。跳转 = 先确保目标时代分片已加载并渲染 → 再瞬时定位（禁用平滑，杜绝长途滑行）。
 * Toolbar ：控制层。只负责把用户操作转成 Store 状态变更 + 通知 Timeline 重绘。
 *
 * 原则：渲染幂等（可重入）、分层单向依赖（Toolbar→Store→Timeline）、
 *       过滤器开闭（新增过滤条件=加一个谓词，不改核心）、懒渲染只做性能优化不做正确性依赖。
 */
'use strict';

/* ── 配置常量 ─────────────────── */
const ERAS = [
  { name: '前史与萌发', range: [1972, 1994.4] },
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
  manifest: null,                                   // data/index.json：总量统计 + 分片清单
  shards: ERAS.map(() => null),                     // 各时代事件分片（加载后填充，按日期有序）
  shardState: ERAS.map(() => 'empty'),              // empty | loading | loaded | error
  ready: false,
  filters: { cats: new Set(CATS.map(c => c.k)), q: '', mileOnly: false, tag: null },

  /** 事件所属时代索引；越界钳制到最后一个时代（杜绝事件被静默丢弃）
   *  注意：必须与 scripts/build.py 的分片归属逻辑严格一致 */
  eraIndex(dateStr) {
    const yf = +dateStr.slice(0, 4) + (+dateStr.slice(5, 7) - 1) / 12;
    const i = ERAS.findIndex(e => yf >= e.range[0] && yf < e.range[1]);
    return i === -1 ? (yf < ERAS[0].range[0] ? 0 : ERAS.length - 1) : i;
  },

  /** 拉取某时代分片：并发去重；失败标记 error（由 Timeline 呈现重试按钮）
   *  传输优化：优先取预压缩 .gz（体积-80%），用 DecompressionStream 本地解压；
   *  不支持该 API 或 .gz 缺失时回退原始 .json。URL 带 ?v= 构建时间戳保证缓存一致性。 */
  _v() { return this._ver || (this._ver = 'v' + ((this.manifest.generated || '').replace(/\D/g, '').slice(-13))); },
  async _fetchShard(url) {
    const v = this._v();
    if (typeof DecompressionStream !== 'undefined') {
      try {
        const r = await fetch(url + '.gz?v=' + v);
        if (r.ok) {
          const stream = (await r.blob()).stream().pipeThrough(new DecompressionStream('gzip'));
          return await new Response(stream).json();
        }
      } catch (e) { /* .gz 缺失或解压失败 → 回退明文 */ }
    }
    const r = await fetch(url + '?v=' + v);
    if (!r.ok) throw new Error('HTTP ' + r.status);
    return r.json();
  },
  loadShard(i) {
    if (this.shardState[i] === 'loaded') return Promise.resolve();
    (this._inflight ??= {});
    if (this._inflight[i]) return this._inflight[i];
    this.shardState[i] = 'loading';
    const p = this._fetchShard('data/' + this.manifest.eras[i].shard)
      .then(evs => { this.shards[i] = evs; this.shardState[i] = 'loaded'; })
      .catch(err => { this.shardState[i] = 'error'; throw err; });
    this._inflight[i] = p.finally(() => { delete this._inflight[i]; });
    return this._inflight[i];
  },

  /** 过滤谓词表：开闭原则——新增过滤条件只需追加谓词 */
  predicates: [
    (e, f) => f.cats.has(e.category),
    (e, f) => !f.mileOnly || !!e.milestone,
    (e, f) => !f.tag || (e.tags || []).includes(f.tag),
    (e, f) => {
      const q = f.q.trim().toLowerCase();
      return !q || [e.title, e.summary_30s, e.detail, ...(e.tags || []), e.date].join(' ').toLowerCase().includes(q);
    },
  ],
  passes(e) { return this.predicates.every(p => p(e, this.filters)); },

  /** 已加载事件总量（qCount 的"全量"基准只看已加载分片，全部分片到位后即为精确值） */
  loadedTotal() { return this.shards.reduce((n, s) => n + (s ? s.length : 0), 0); },

  /** 选择器：某时代的可见事件（按日期有序；只看已加载分片） */
  eventsOf(eraIdx) { return (this.shards[eraIdx] || []).filter(e => this.passes(e)); },
  visibleCount() { return this.shards.reduce((n, s) => s ? n + s.filter(e => this.passes(e)).length : n, 0); },

  setFilter(patch) { Object.assign(this.filters, patch); },
};

/* ── Timeline：纯渲染（幂等） ─────────────────── */
const Timeline = {
  rendered: new Set(),
  io: null, reveal: null,

  init() {
    this.io = new IntersectionObserver(es => {
      for (const en of es) if (en.isIntersecting) this.ensureEra(+en.target.dataset.era);
    }, { rootMargin: '900px 0px' });
    this.reveal = new IntersectionObserver(es => {
      for (const en of es) if (en.isIntersecting) { en.target.classList.add('in'); this.reveal.unobserve(en.target); }
    }, { rootMargin: '30px' });
  },

  /** 确保某时代分片已加载并渲染（IO 滚动触发与跳转共用的唯一入口） */
  async ensureEra(i) {
    if (this.rendered.has(i)) return;
    try {
      await Store.loadShard(i);
      if (this.rendered.has(i)) return;            // 并发触发时后来者让位
      this.renderEraHead(i);
      this.renderEra(i);
      this.refreshQCount();
    } catch (err) {
      this.renderError(i, err);
    }
  },

  /** 建时代空壳（含时代头）。幂等：整体重建。分片未加载前只有空壳，由 IO 驱动填充。 */
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
      this.renderEraHead(i);       // 时代头永远同步渲染（分片未加载时显示占位「… 条」）
    });
  },

  renderEraHead(i) {
    const era = ERAS[i];
    const loaded = Store.shardState[i] === 'loaded';
    const evs = loaded ? Store.eventsOf(i) : [];
    const years = evs.map(e => +e.date.slice(0, 4));
    const span = evs.length ? `${Math.min(...years)}–${Math.max(...years)}` : `${Math.floor(era.range[0])}–${Math.ceil(era.range[1])}`;
    document.querySelector(`#era-${i} .eraHead`).innerHTML =
      `<span class="eraPill">${era.name}<em>${span}</em></span><span class="eraLine"></span><span class="eraCount">${loaded ? evs.length + ' 条' : '… 条'}</span>`;
  },

  /** 分片加载失败：在该时代体里给出错误与重试按钮（点击重取分片） */
  renderError(i, err) {
    const body = document.querySelector(`#era-${i} .eraBody`);
    if (!body) return;
    body.innerHTML = `<div class="empty">本时代数据加载失败（${esc(String((err && err.message) || err))}）<br>
      <button class="tBtn retryBtn">↺ 重试加载</button></div>`;
    body.querySelector('.retryBtn').onclick = () => {
      Store.shardState[i] = 'empty';
      body.innerHTML = '';
      this.ensureEra(i);
    };
  },

  /** 渲染某时代的卡片体（调用前必须确保分片已加载）。
   *  分帧渲染：按年份组分批建 DOM（每帧预算 12ms），大分片（1300+ 条）不再阻塞主线程；
   *  token 防竞态：rebuild 清空后旧分批自动作废。 */
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
    (this._tokens ??= {})[i] = (this._tokens[i] || 0) + 1;
    const token = this._tokens[i];
    const groups = [...byYear.entries()];
    let gi = 0;
    let done;
    const finished = new Promise(res => { done = res; });

    const renderGroup = ([year, list]) => {
      const g = document.createElement('div');
      g.className = 'yearGroup';
      g.innerHTML = `<div class="yBadge" data-year="${year}" title="点击复制这一年的链接"><span>${year}</span>${list.length > 1 ? `<small>${list.length}</small>` : ''}</div><div class="cards"></div>`;
      const cards = g.querySelector('.cards');
      const frag = document.createDocumentFragment();
      // 同日分组：date 相同的事件共享一个卡位——主事件占位，其余收进可展开的「同日」折叠层。
      // 左右交替按"卡位"（组）计数，整组同侧，视觉不乱。
      const byDate = new Map();
      for (const e of list) {
        let arr = byDate.get(e.date);
        if (!arr) byDate.set(e.date, arr = []);
        arr.push(e);
      }
      for (const dayEv of byDate.values()) {
        const p = dayEv.length === 1 ? dayEv[0] : this.pickPrimary(dayEv);
        const extras = dayEv.length > 1 ? dayEv.filter(e => e !== p) : null;
        const holder = document.createElement('div');
        holder.className = 'card' + (flip ? ' right' : '') + (p.milestone ? ' mile' : '') + (UIState.expandAll ? ' open' : '');
        holder.dataset.id = p.id;
        holder.innerHTML = this.cardHtml(p);
        if (extras) holder.appendChild(this.sameDayEl(extras));
        frag.appendChild(holder);
        this.reveal.observe(holder);
        flip = 1 - flip;
      }
      cards.appendChild(frag);
      body.appendChild(g);
    };
    const sweep = () => {
      for (const holder of body.querySelectorAll('.card:not(.in)')) {
        const r = holder.getBoundingClientRect();
        if (r.top < innerHeight + 200 && r.bottom > -200) holder.classList.add('in');
      }
    };
    const renderBatch = () => {
      if (token !== this._tokens[i]) return;                   // 本时代已被重建，作废旧批次
      const t0 = performance.now();
      while (gi < groups.length && performance.now() - t0 < 12) renderGroup(groups[gi++]);
      if (gi < groups.length) {
        setTimeout(renderBatch, 0);                            // 后台标签 rAF 不派发，统一用 setTimeout
      } else {
        // 全部就位：视口内卡片立即置亮（跳转/筛选后不等待 IO 回调窗口）
        setTimeout(() => { sweep(); done(); }, 0);
      }
    };
    renderBatch();
    // 首批渲染后视口内立即置亮
    setTimeout(sweep, 0);
    return finished;
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
      <div class="cBody"><div class="cBodyInner">${this.bodyHtml(e)}</div></div>`;
  },

  /** 卡片正文（经过/影响/后续/来源）：主卡与同日折叠行详情共用同一套 .sec 语言 */
  bodyHtml(e) {
    return `
      <div class="sec"><span class="lab">经过</span><p>${esc(e.detail)}</p></div>
      <div class="sec"><span class="lab">影响</span><p>${esc(e.impact)}</p></div>
      <div class="sec"><span class="lab">后续</span><p>${esc(e.aftermath)}</p></div>
      <div class="sec"><span class="lab">数据来源</span><ul class="srcList">${e.sources.map(s =>
        `<li><a href="${esc(safeUrl(s.url))}" target="_blank" rel="noopener">${esc(s.title)}</a><span class="tp">${esc(s.type || '')}</span></li>`).join('')}</ul></div>`;
  },

  /** 同日分组的主事件挑选（确定性）：时代转折 > 双源实证 > 正文更详 > 数据序。
   *  分组发生在筛选之后，故筛选变化时主事件随可见集自动切换。 */
  pickPrimary(g) {
    const score = e => (e.milestone ? 2 : 0) + (e.sources.length >= 2 ? 1 : 0);
    let best = g[0], bs = score(best);
    for (const e of g) {
      const s = score(e);
      if (s > bs || (s === bs && (e.detail || '').length > (best.detail || '').length)) { best = e; bs = s; }
    }
    return best;
  },

  /** 同日折叠层骨架：只建 toggle 条与空容器——行 DOM 首次展开才构建，行内详情再懒一层 */
  sameDayEl(extras) {
    const el = document.createElement('div');
    el.className = 'sameDay';
    const hints = extras.slice(0, 2).map(e => e.title).join('；');
    el.innerHTML = `
      <button class="sdToggle" aria-expanded="false" title="展开同日事件">
        <i class="sdArrow">▸</i>同日还有 ${extras.length} 件<span class="sdHints">${esc(hints)}${extras.length > 2 ? '…' : ''}</span>
      </button>
      <div class="sdList"><div class="sdListInner"></div></div>`;
    el._extras = extras;
    return el;
  },

  /** 同日行的紧凑外观；详情默认 0fr 收起，展开复用主卡正文 */
  sdRowHtml(e) {
    const cat = CAT[e.category] || { name: e.category, c: '#8a919e' };
    const conf = CONF[e.date_confidence] || CONF.uncertain;
    return `
      <button class="sdRow" aria-expanded="false">
        <span class="cDot" style="--c:${cat.c}"></span>
        <span class="sdCat">${cat.name}</span>
        <span class="sdTitle">${esc(e.title)}</span>
        <span class="sdMeta"><span class="cConf ${conf[1]}">${conf[0]}</span><span class="cAcc">${e.region === 'cn' ? '中国' : '世界'}</span></span>
      </button>
      <div class="sdDetail"><div class="sdDetailInner">${this.bodyHtml(e)}</div></div>`;
  },

  /** 首次展开同日层时构建行 DOM（全库 1100+ 条同日事件，隐藏详情不预渲染） */
  fillSameDay(sd) {
    if (sd._filled) return;
    sd.querySelector('.sdListInner').innerHTML = sd._extras.map(e => `<div class="sdItem">${this.sdRowHtml(e)}</div>`).join('');
    sd._filled = true;
  },

  /** 筛选变化：重建空壳，只同步重渲「已加载且在视口附近」的时代，其余交给 IO（避免全量重渲） */
  rebuild() {
    this.refreshQCount();
    this.buildSections();
    for (const [i] of ERAS.entries()) {
      if (Store.shardState[i] !== 'loaded') continue;
      const sec = document.getElementById(`era-${i}`);
      if (!sec) continue;
      const r = sec.getBoundingClientRect();
      if (r.top < innerHeight + 900 && r.bottom > -900) this.renderEra(i);   // 900px 与 IO rootMargin 一致
    }
  },
  refreshQCount() {
    const n = Store.visibleCount();
    document.getElementById('qCount').textContent = n === Store.loadedTotal() ? '' : `${n} 条`;
  },

  /** 几何兜底：按视口位置直接驱动加载渲染（scroll 时调用 + boot 后首查）。
   *  IntersectionObserver 在个别 WebView/内嵌环境不派发回调，此路径保证任何环境都能渲染；
   *  ensureEra 幂等，与 IO 并存无副作用。 */
  checkViewport() {
    if (!Store.ready) return;
    // 后台 WebView 里 innerHeight 可能为 0，几何判断会整体失效——取保守回退值
    const vh = innerHeight || document.documentElement.clientHeight || 1080;
    for (const [i] of ERAS.entries()) {
      if (this.rendered.has(i) || Store.shardState[i] === 'loading') continue;
      const sec = document.getElementById(`era-${i}`);
      if (!sec) continue;
      const r = sec.getBoundingClientRect();
      if (r.top < vh + 900 && r.bottom > -900) this.ensureEra(i);   // 900px 与 IO rootMargin 一致
    }
  },

  /** reveal 兜底：点亮滚动进入视口的未显影卡片（IO 不可用环境的渐入替代）。 */
  revealSweep() {
    for (const holder of document.querySelectorAll('.card:not(.in)')) {
      const r = holder.getBoundingClientRect();
      if (r.top < innerHeight + 200 && r.bottom > -200) {
        holder.classList.add('in');
        this.reveal?.unobserve(holder);
      }
    }
  },

  /** 导航：先确保目标时代分片加载并渲染，再瞬时定位（杜绝长滑与落点漂移）。boot 未就绪时排队。 */
  jumpTo(i) {
    if (!Store.ready) { (this._pending ??= new Set()).add(i); return; }
    return this._jump(i);
  },
  async flushPending() {
    if (!this._pending) return;
    const pend = [...this._pending];
    this._pending.clear();
    for (const i of pend) await this._jump(i);
  },
  jumpToYear(year, replaceUrl = false) {
    if (!Store.ready) { this.jumpTo(Store.eraIndex(year + '-06-01')); return; }
    const eraIdx = Store.eraIndex(year + '-06-01');
    return (async () => {
      try {
        await Store.loadShard(eraIdx);
        this.renderEraHead(eraIdx);
        await this.renderEra(eraIdx);                          // 等待分批渲染完成，确保目标年份组已在DOM
      } catch (err) {
        this.renderError(eraIdx, err);
      }
      const g = [...document.querySelectorAll(`#era-${eraIdx} .yearGroup`)]
        .find(x => x.querySelector('.yBadge span')?.textContent === year);
      if (!g) { await this._jump(eraIdx); return; }
      const y = g.getBoundingClientRect().top + window.scrollY - 150;
      window.scrollTo({ top: y, behavior: 'instant' });
      if (replaceUrl) history.replaceState(null, '', location.pathname + '?year=' + year);
      g.querySelector('.yBadge').classList.add('flash');
      setTimeout(() => g.querySelector('.yBadge')?.classList.remove('flash'), 2200);
    })();
  },
  async _jump(i) {
    const sec = document.getElementById(`era-${i}`);
    if (!sec) return;
    try {
      await Store.loadShard(i);                         // 分片未加载先取
      this.renderEraHead(i);
      this.renderEra(i);                                // 渲染先于滚动
    } catch (err) {
      this.renderError(i, err);                         // 失败也落位，让用户看到错误与重试按钮
    }
    const toolbarH = document.getElementById('toolbar').getBoundingClientRect().height;
    const y = sec.getBoundingClientRect().top + window.scrollY - toolbarH - 26;
    window.scrollTo({ top: y, behavior: 'instant' }); // 瞬时定位
  },
};

/* ── 工具函数 ─────────────────── */
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const safeUrl = u => /^https?:\/\//i.test(String(u)) ? u : '#';   // 纵深防御：只放行 http(s)
const $ = s => document.querySelector(s);

/* 轻提示：复制成功/失败等瞬时反馈（单例，避免连续触发堆叠） */
let _toastEl = null, _toastTimer = 0;
function toast(msg) {
  if (!_toastEl) {
    _toastEl = document.createElement('div');
    _toastEl.className = 'toast';
    document.body.appendChild(_toastEl);
  }
  _toastEl.textContent = msg;
  _toastEl.classList.add('show');
  clearTimeout(_toastTimer);
  _toastTimer = setTimeout(() => _toastEl.classList.remove('show'), 2200);
}

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
      const n = (Store.manifest.cats && Store.manifest.cats[c.k]) || 0;   // 全量分类计数随 manifest 下发
      const b = document.createElement('button');
      b.className = 'chip on';
      b.innerHTML = `<span style="color:${c.c}">●</span> ${c.name}<span class="n">${n}</span>`;
      b.onclick = () => {
        const f = Store.filters;
        if (f.cats.has(c.k) && f.cats.size === 1) return;
        f.cats.has(c.k) ? f.cats.delete(c.k) : f.cats.add(c.k);
        b.classList.toggle('on', f.cats.has(c.k));
        b.classList.toggle('off', !f.cats.has(c.k));
        Timeline.rebuild(); syncReset();
      };
      row.appendChild(b);
    }
    /* 标签筛选：聚合高频标签为可点选 chips（单选切换）。
       候选清单随 manifest 下发（≥10 次者），前端仍按 ≥60 过滤取前 40 */
    const topTags = (Store.manifest.tags || []).filter(([, n]) => n >= 60).sort((a, b) => b[1] - a[1]).slice(0, 40);
    const tagRow = $('#tagRow');
    for (const [t, n] of topTags) {
      const b = document.createElement('button');
      b.className = 'chip'; b.textContent = t;
      b.title = `${n} 条`;
      b.insertAdjacentHTML('beforeend', `<span class="n">${n}</span>`);
      b.onclick = () => {
        const on = Store.filters.tag === t;
        Store.setFilter({ tag: on ? null : t });
        tagRow.querySelectorAll('.chip').forEach(x => x.classList.remove('on', 'off'));
        if (!on) b.classList.add('on');
        Timeline.rebuild(); syncReset();
      };
      tagRow.appendChild(b);
    }
    let t;
    $('#q').addEventListener('input', e => {
      clearTimeout(t);
      t = setTimeout(() => { Store.setFilter({ q: e.target.value }); Timeline.rebuild(); syncReset(); }, 180);
    });
    $('#expandAll').onclick = () => {
      UIState.expandAll = !UIState.expandAll;
      const on = UIState.expandAll;
      $('#expandAll').classList.toggle('on', on);
      $('#expandAll').textContent = on ? '全部收起' : '全部展开';
      document.querySelectorAll('.card').forEach(c => c.classList.toggle('open', on));
    };
    const reset = document.createElement('button');
    reset.className = 'tBtn'; reset.id = 'resetAll'; reset.textContent = '↺ 重置';
    reset.style.display = 'none';
    reset.onclick = () => {
      Store.setFilter({ q: '', mileOnly: false, cats: new Set(CATS.map(c => c.k)), tag: null });
      document.querySelectorAll('#tagRow .chip').forEach(x => { x.classList.remove('on'); x.classList.remove('off'); });
      $('#q').value = '';
      $('#mileOnly').classList.remove('on');
      document.querySelectorAll('#catRow .chip').forEach(b => { b.classList.add('on'); b.classList.remove('off'); });
      Timeline.rebuild();
      syncReset();
    };
    $('#mileOnly').after(reset);
    window.syncReset = () => {
      const f = Store.filters;
      const dirty = f.q.trim() || f.mileOnly || f.cats.size < CATS.length || !!f.tag;
      $('#resetAll').style.display = dirty ? 'inline-block' : 'none';
    };
    const _obs = new MutationObserver(syncReset);
    _obs.observe(document.getElementById('qCount'), { childList: true, characterData: true, subtree: true });
    $('#mileOnly').onclick = () => {
      Store.setFilter({ mileOnly: !Store.filters.mileOnly });
      $('#mileOnly').classList.toggle('on', Store.filters.mileOnly);
      Timeline.rebuild(); syncReset();
    };
    $('#themeBtn').onclick = () => {
      const next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
      applyTheme(next);
    };
    $('#ctaEras').onclick = e => { e.preventDefault(); Timeline.jumpTo(0); };
    $('#toTop').onclick = () => window.scrollTo({ top: 0, behavior: 'instant' });
    let lastSave = 0;
    let scrollLast = 0;
    let revealLast = 0;
    addEventListener('scroll', () => {
      // 时间节流而非 rAF 节流：个别 WebView/后台标签 rAF 不派发，滚动兜底链不能依赖它
      const now = Date.now();
      if (now - scrollLast < 80) return;
      scrollLast = now;
      const h = document.documentElement;
      $('#progress').style.width = (h.scrollTop / (h.scrollHeight - h.clientHeight) * 100) + '%';
      $('#toTop').classList.toggle('show', h.scrollTop > 800);
      // 注意：本回调注册于 Toolbar.init，箭头函数 this 是 Toolbar——
      // Timeline 的方法必须显式引用（历史上 this.markCurrentEra 在此静默报错多年）
      Timeline.markCurrentEra();
      Timeline.checkViewport();                              // 几何兜底：IO 不可用的环境靠滚动驱动渲染
      if (now - revealLast > 150) {                        // reveal 兜底：IO 不可用时滚动也能点亮卡片
        revealLast = now;
        Timeline.revealSweep();
      }
      if (now - lastSave > 2000 && Store.ready) {          // 节流记录阅读位置
        lastSave = now;
        const y = Timeline.currentYear();
        if (y) localStorage.setItem('na-last-read', y);
      }
    }, { passive: true });

    // 时代长卷内的事件代理：展开/收起
    $('#timeline').addEventListener('click', ev => {
      const badge = ev.target.closest('.yBadge');
      if (badge) {
        const url = location.origin + location.pathname + '?year=' + badge.dataset.year;
        navigator.clipboard?.writeText(url).then(
          () => toast(`已复制 ${badge.dataset.year} 年的链接`),
          () => toast('复制失败，请手动复制地址栏'));
        return;
      }
      const more = ev.target.closest('.cMore');
      if (more) { more.closest('.card').classList.toggle('open'); return; }
      // 同日折叠层：层内点击不冒泡成卡片展开；toggle 懒构建行，行点击懒开详情
      if (ev.target.closest('.sameDay')) {
        const row = ev.target.closest('.sdRow');
        if (row) {
          const item = row.closest('.sdItem');
          const on = item.classList.toggle('open');
          row.setAttribute('aria-expanded', on);
          return;
        }
        const tg = ev.target.closest('.sdToggle');
        if (tg) {
          const sd = tg.closest('.sameDay');
          const on = sd.classList.toggle('open');
          tg.setAttribute('aria-expanded', on);
          if (on) Timeline.fillSameDay(sd);
        }
        return;
      }
      const card = ev.target.closest('.card');
      if (card && !ev.target.closest('a')) card.classList.add('open');
    });
  },

  /** 当前所在时代高亮 + 工具栏实时年份指示（回答"我读到哪了"）。
   *  结果与上次相同则不写 DOM，杜绝每帧的 chips forEach 与文本写入。 */
  markCurrentEra() {
    let cur = 0;
    for (const [i] of ERAS.entries()) {
      const sec = document.getElementById(`era-${i}`);
      if (sec && sec.getBoundingClientRect().top <= 280) cur = i;
    }
    const y = this.currentYear();
    const label = y ? `${y} · ${ERAS[cur].name}` : '时代';
    if (cur === this._curEra && label === this._curLabel) return;
    this._curEra = cur; this._curLabel = label;
    document.querySelectorAll('#eraJump .chip').forEach((b, i) => b.classList.toggle('on', i === cur));
    const lab = document.querySelector('.tJumpRow .tLab');
    if (lab) lab.textContent = label;
  },
  /** 倒序找第一个 top≤300 的年份组即当前年份，命中即 break（避免全量 getBoundingClientRect） */
  currentYear() {
    const groups = document.querySelectorAll('.yearGroup');
    for (let k = groups.length - 1; k >= 0; k--) {
      if (groups[k].getBoundingClientRect().top <= 300) return groups[k].querySelector('.yBadge span')?.textContent ?? null;
    }
    return null;
  },
};

function applyTheme(t) {
  const root = document.documentElement;
  root.classList.add('theming');            // 换肤瞬间冻结全局过渡（style.css 侧配套 .theming 规则），避免数千卡片边框同时动画
  root.dataset.theme = t;
  localStorage.setItem('na-theme', t);
  setTimeout(() => root.classList.remove('theming'), 50);
}

/* ── 启动 ─────────────────── */
async function boot() {
  applyTheme(localStorage.getItem('na-theme') || (matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark'));  // 幂等：index.html 内联脚本已先行着色
  try {
    const res = await fetch('data/index.json?v=' + Date.now());   // manifest必须新鲜：其generated决定分片缓存版本
    if (!res.ok) throw new Error(res.status);
    const m = await res.json();
    Store.manifest = m;
    const endYear = Math.ceil(m.eras[m.eras.length - 1].range[1]) - 1;
    $('#heroEyebrow').textContent = `1972 — ${endYear} · ${m.total} 条 · 精确到日 · 每条可溯源`;
    $('#introText').textContent = `从 1972 年的第一声电视新闻，到 ${endYear} 年每个人口袋里的人工智能——本卷收录 ${m.total} 条被日期钉住的时刻：改革开放、互联网、科技、硬件、公司、国家大事、世界大事、民间生活与流行文化。其中 ${m.verified.toLocaleString()} 条经双源实证，其余均标明来源与置信度。点击任何标题可跳转原文。`;
    $('#colMeta').textContent = `构建于 ${(m.generated || '').replace('T', ' ').slice(0, 16)} · ${m.total} 条事件 · 来源 ${m.sourceCount} 个 · 数据持续增补中`;
    Timeline.init();
    Toolbar.init();
    Timeline.buildSections();
    Store.ready = true;
    // 首查兜底：个别 WebView 初始帧 innerHeight=0、布局未完成，几何判断会整体落空——
    // 视口就绪（0→vh）必触发 resize；再辅以多级延迟补查，与 IO/scroll 兜底共同覆盖所有环境
    addEventListener('resize', () => Timeline.checkViewport(), { passive: true });
    requestAnimationFrame(() => Timeline.checkViewport());
    for (const d of [300, 1200, 3000]) setTimeout(() => Timeline.checkViewport(), d);
    Timeline.flushPending();
    const wantYear = new URLSearchParams(location.search).get('year');
    const lastRead = localStorage.getItem('na-last-read');
    if (wantYear && /^\d{4}$/.test(wantYear)) {
      Timeline.jumpToYear(wantYear, true);
    } else if (lastRead && /^\d{4}$/.test(lastRead)) {
      const bar = document.createElement('div');
      bar.className = 'resumeBar';
      bar.innerHTML = `<span>上次读到 <b>${lastRead}</b> 年</span><button class="btn primary" style="padding:7px 18px;font-size:.76rem">继续阅读</button><button class="btn ghost" style="padding:7px 18px;font-size:.76rem">从头开始</button>`;
      document.body.appendChild(bar);
      bar.querySelector('.btn.primary').onclick = () => { Timeline.jumpToYear(lastRead); bar.remove(); localStorage.removeItem('na-last-read'); };
      bar.querySelector('.btn.ghost').onclick = () => { bar.remove(); localStorage.removeItem('na-last-read'); };
      setTimeout(() => bar.classList.add('show'), 400);
      setTimeout(() => bar.remove(), 12000);
    }
  } catch (err) {
    document.getElementById('timeline').innerHTML = `<div class="empty">数据加载失败（${esc(err.message)}）。请先运行 scripts/build.py 生成 site/data/。</div>`;
  }
}

boot();
