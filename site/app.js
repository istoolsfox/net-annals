/* 互联网编年史 · 长卷 v2 — 按 DESIGN.md 实现 */
'use strict';

const ERAS = [
  { name: '接入前史', range: [1986, 1994.4] },
  { name: '拨号时代', range: [1994.4, 2000] },
  { name: '门户与泡沫', range: [2000, 2003] },
  { name: 'Web2.0 前夜', range: [2003, 2005] },
  { name: 'Web2.0', range: [2005, 2010] },
  { name: '移动互联网', range: [2010, 2015] },
  { name: '移动成熟', range: [2015, 2020] },
  { name: '疫情与智能', range: [2020, 2026.6] },
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
const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const fmtDate = d => d.replaceAll('-', '.');

let EVENTS = [], ordered = [];
const state = { cats: new Set(CATS.map(c => c.k)), q: '', mileOnly: false, expandAll: false };
const rendered = new Set();     // 已渲染的时代分节
const io = new IntersectionObserver(onNear, { rootMargin: '700px 0px' });
const reveal = new IntersectionObserver(onReveal, { rootMargin: '40px' });

function eraOf(date) { const yf = +date.slice(0, 4) + (+date.slice(5, 7) - 1) / 12; return ERAS.findIndex(e => yf >= e.range[0] && yf < e.range[1]); }
function visibleEvents(eraIdx) {
  const q = state.q.trim().toLowerCase();
  return ordered.filter(e => {
    if (eraOf(e.date) !== eraIdx) return false;
    if (!state.cats.has(e.category)) return false;
    if (state.mileOnly && !e.milestone) return false;
    if (q && ![e.title, e.summary_30s, e.detail, ...(e.tags || []), e.date].join(' ').toLowerCase().includes(q)) return false;
    return true;
  });
}
const pass = e => {
  if (!state.cats.has(e.category)) return false;
  if (state.mileOnly && !e.milestone) return false;
  const q = state.q.trim().toLowerCase();
  return !q || [e.title, e.summary_30s, e.detail, ...(e.tags || []), e.date].join(' ').toLowerCase().includes(q);
};

/* ── 启动 ─────────────────── */
async function boot() {
  try {
    applyTheme(localStorage.getItem('na-theme') || (matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark'));
    const res = await fetch('data.json');
    if (!res.ok) throw new Error(res.status);
    const data = await res.json();
    EVENTS = data.events;
    ordered = [...EVENTS].sort((a, b) => a.date < b.date ? -1 : 1);
    const nV = EVENTS.filter(e => e.date_confidence === 'verified').length;
    $('#heroEyebrow').textContent = `1986 — ${ordered[ordered.length - 1].date.slice(0, 4)} · ${EVENTS.length} 条 · 精确到日 · 每条可溯源`;
    $('#introText').textContent = `从 1986 年中关村的一间实验室，到 2026 年每个人口袋里的人工智能——本卷收录 ${EVENTS.length} 条被日期钉住的时刻：互联网、科技、硬件、公司、国家大事、世界大事、民间生活与流行文化。其中 ${nV.toLocaleString()} 条经双源实证，其余均标明来源与置信度。点击任何标题可跳转原文。`;
    $('#colMeta').textContent = `构建于 ${(data.generated || '').replace('T', ' ').slice(0, 16)} · ${EVENTS.length} 条事件 · 来源 ${new Set(EVENTS.flatMap(e => e.sources.map(s => s.url))).size} 个 · 数据持续增补中`;
    buildToolbar();
    buildSections();
    observeSections();
    bindUI();
  } catch (err) {
    $('#timeline').innerHTML = `<div class="empty">数据加载失败（${esc(err.message)}）。请先运行 scripts/deploy.sh 或 build.sh。</div>`;
  }
}

/* ── 工具栏 ─────────────────── */
function buildToolbar() {
  const jump = $('#eraJump');
  for (const [i, era] of ERAS.entries()) {
    const b = document.createElement('button');
    b.className = 'chip';
    b.textContent = era.name;
    b.onclick = () => document.getElementById(`era-${i}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    jump.appendChild(b);
  }
  const row = $('#catRow');
  for (const c of CATS) {
    const n = EVENTS.filter(e => e.category === c.k).length;
    const b = document.createElement('button');
    b.className = 'chip on';
    b.innerHTML = `<span style="color:${c.c}">●</span> ${c.name}<span class="n">${n}</span>`;
    b.onclick = () => {
      if (state.cats.has(c.k) && state.cats.size === 1) return;
      state.cats.has(c.k) ? state.cats.delete(c.k) : state.cats.add(c.k);
      b.classList.toggle('on', state.cats.has(c.k));
      b.classList.toggle('off', !state.cats.has(c.k));
      rebuild();
    };
    row.appendChild(b);
  }
}

function bindUI() {
  let t;
  $('#q').addEventListener('input', e => { clearTimeout(t); t = setTimeout(() => { state.q = e.target.value; rebuild(); }, 180); });
  $('#expandAll').onclick = () => {
    state.expandAll = !state.expandAll;
    $('#expandAll').textContent = state.expandAll ? '全部收起' : '全部展开';
    $('#expandAll').classList.toggle('on', state.expandAll);
    document.querySelectorAll('.card.open').forEach(c => { if (!state.expandAll) c.classList.remove('open'); });
    document.querySelectorAll('.card:not(.open)').forEach(c => { if (state.expandAll) c.classList.add('open'); });
  };
  $('#mileOnly').onclick = () => {
    state.mileOnly = !state.mileOnly;
    $('#mileOnly').classList.toggle('on', state.mileOnly);
    rebuild();
  };
  $('#themeBtn').onclick = () => applyTheme(document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark');
  $('#ctaEras').onclick = e => { e.preventDefault(); document.querySelector('.eraHead')?.scrollIntoView({ behavior: 'smooth' }); };
  $('#toTop').onclick = () => scrollTo({ top: 0, behavior: 'smooth' });
  addEventListener('scroll', () => {
    const h = document.documentElement;
    $('#progress').style.width = (h.scrollTop / (h.scrollHeight - h.clientHeight) * 100) + '%';
    $('#toTop').classList.toggle('show', h.scrollTop > 800);
  }, { passive: true });
}
function applyTheme(t) { document.documentElement.dataset.theme = t; localStorage.setItem('na-theme', t); }

/* ── 长卷构建（按时代懒渲染） ─────────────────── */
function buildSections() {
  const tl = $('#timeline');
  tl.innerHTML = '';
  rendered.clear();
  for (const [i, era] of ERAS.entries()) {
    const sec = document.createElement('section');
    sec.className = 'eraSec'; sec.id = `era-${i}`; sec.dataset.era = i;
    const count = EVENTS.filter(e => eraOf(e.date) === i).length;
    sec.innerHTML = `<div class="eraHead"><span class="eraPill">${era.name}<em>${Math.floor(era.range[0])}–${Math.ceil(era.range[1])}</em></span><span class="eraLine"></span><span class="eraCount">${count} 条</span></div><div class="eraBody"></div>`;
    tl.appendChild(sec);
    io.observe(sec);
  }
}
function onNear(entries) {
  for (const en of entries) if (en.isIntersecting) renderEra(+en.target.dataset.era);
}
function renderEra(idx) {
  if (rendered.has(idx)) return;
  rendered.add(idx);
  const sec = document.getElementById(`era-${idx}`);
  const body = sec.querySelector('.eraBody');
  body.innerHTML = '';
  const evs = visibleEvents(idx);
  if (!evs.length) {
    body.innerHTML = `<div class="empty">当前筛选下本时代无条目</div>`;
    return;
  }
  // 按年分组
  const years = new Map();
  for (const e of evs) { const y = e.date.slice(0, 4); if (!years.has(y)) years.set(y, []); years.get(y).push(e); }
  let flip = idx % 2; // 相邻时代左右起始交错
  for (const [y, list] of years) {
    const g = document.createElement('div');
    g.className = 'yearGroup';
    const nMile = list.filter(e => e.milestone).length;
    g.innerHTML = `<div class="yBadge"><span>${y}</span>${list.length > 1 ? `<small>${list.length}</small>` : ''}</div><div class="cards"></div>`;
    const cards = g.querySelector('.cards');
    for (const e of list) {
      const div = document.createElement('div');
      div.className = 'card' + (flip ? ' right' : '') + (e.milestone ? ' mile' : '');
      div.dataset.id = e.id;
      div.innerHTML = cardHtml(e);
      cards.appendChild(div);
      flip = 1 - flip;
    }
    body.appendChild(g);
  }
  body.querySelectorAll('.card').forEach(c => reveal.observe(c));
  body.addEventListener('click', onCardClick);
}
function onCardClick(ev) {
  const more = ev.target.closest('.cMore');
  if (more) { more.closest('.card').classList.toggle('open'); return; }
  const card = ev.target.closest('.card');
  if (card && !ev.target.closest('a')) card.classList.add('open');
}
function onReveal(entries) {
  for (const en of entries) if (en.isIntersecting) { en.target.classList.add('in'); reveal.unobserve(en.target); }
}

function cardHtml(e) {
  const conf = CONF[e.date_confidence] || CONF.uncertain;
  const cat = CAT[e.category] || { name: e.category, c: '#8a919e' };
  const src0 = e.sources[0] || {};
  const acc = e.date_accuracy !== 'exact' ? `<span class="cAcc">${e.date_accuracy === 'month' ? '精确到月' : '精确到年'}</span>` : '';
  const sum = e.summary_30s.length > 150 ? e.summary_30s.slice(0, 150) + '…' : e.summary_30s;
  return `
    <div class="cHead">
      <span class="cDate">${fmtDate(e.date)}</span>
      <span class="cDot" style="--c:${cat.c}"></span><span>${cat.name}</span>
      ${e.milestone ? '<span style="color:var(--accent)">★</span>' : ''}
      <span class="cConf ${conf[1]}">${conf[0]}</span>${acc}
      <span class="cAcc">${e.region === 'cn' ? '中国' : '世界'}</span>
    </div>
    <h3 class="cTitle"><a href="${esc(src0.url || '#')}" target="_blank" rel="noopener" title="点击标题跳转原文">${esc(e.title)} <span class="arrow">↗</span></a></h3>
    <p class="cSum">${esc(sum)}${e.summary_30s.length > 150 ? ' <span style="color:var(--faint);font-size:.78rem">展开看全文</span>' : ''}</p>
    <button class="cMore">展开经过与影响 <i>∨</i></button>
    <div class="cBody">
      <div class="sec"><span class="lab">经过</span><p>${esc(e.detail)}</p></div>
      <div class="sec"><span class="lab">影响</span><p>${esc(e.impact)}</p></div>
      <div class="sec"><span class="lab">后续</span><p>${esc(e.aftermath)}</p></div>
      <div class="sec"><span class="lab">数据来源</span><ul class="srcList">${e.sources.map(s =>
        `<li><a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.title)}</a><span class="tp">${esc(s.type || '')}</span></li>`).join('')}</ul></div>
    </div>`;
}

/* ── 过滤重建 ─────────────────── */
function rebuild() {
  const n = ordered.filter(pass).length;
  $('#qCount').textContent = state.q || state.mileOnly || state.cats.size < CATS.length ? `${n} 条` : '';
  buildSections();
  observeSections();
}
function observeSections() {
  document.querySelectorAll('.eraSec').forEach(s => io.observe(s));
}

boot();
