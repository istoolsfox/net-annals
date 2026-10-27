/* common.js — 全站共享模块（高内聚：工具 / 数据获取 / 长卷渲染 / 卡片模板）
 * 单一事实源：esc/safeUrl/fetchGz/dsh/matchQ/wireSearch/buildFilterChips/
 * renderLongScroll/wireExpand/deepLinkCard + 三类卡片模板 + 分卷/配色配置。
 * 消费方：主页（section-view.js + app.js 别名）、子页（section-page.js）、
 * today/geo（内联脚本解构别名）。页面内不得再重复实现这些功能。
 */
'use strict';

const NA = (function () {
  const DATA_BUILD = '20261025b';

  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const safeUrl = u => /^https?:\/\//i.test(String(u)) ? u : '#';   // 纵深防御：只放行 http(s)

  /** 拉取 JSON：优先预压缩 .gz（DecompressionStream 本地解压），失败回退明文 */
  async function fetchGz(url) {
    if (typeof DecompressionStream !== 'undefined') {
      try {
        const r = await fetch(url + '.gz?v=' + DATA_BUILD);
        if (r.ok) return await new Response((await r.blob()).stream().pipeThrough(new DecompressionStream('gzip'))).json();
      } catch (e) { /* .gz 缺失或解压失败 → 回退明文 */ }
    }
    const r = await fetch(url + '?v=' + DATA_BUILD);
    if (!r.ok) throw new Error('HTTP ' + r.status);
    return r.json();
  }

  /** 时间线节点日期显示精度（year→4 位 / month→7 位 / 默认 10 位） */
  const dsh = t => String(t.date).slice(0, t.acc === 'year' ? 4 : t.acc === 'month' ? 7 : 10);

  /** 跨页相关条目链接：主页用视图深链，子页用相对路径 */
  const relUrl = (ctx, kind, param, id) => ctx && ctx.home ? `?view=${kind}&${param}=${id}` : `../${kind}/?${param}=${id}`;

  function matchQ(item, q, fields) {
    const s = q.trim().toLowerCase();
    if (!s) return true;
    const hay = fields.map(f => Array.isArray(item[f]) ? item[f].join(' ') : (item[f] || '')).join(' ').toLowerCase();
    return hay.includes(s);
  }

  /** 防抖搜索框绑定 */
  function wireSearch(inputId, cb, delay = 160) {
    let t;
    document.getElementById(inputId).addEventListener('input', e => {
      clearTimeout(t);
      t = setTimeout(() => cb(e.target.value), delay);
    });
  }

  /** 单选筛选芯片行（主页/子页同款语义：点选过滤、再点取消回全部） */
  function buildFilterChips(bar, entries, { colorOf, labelOf, onChange }) {
    let active = 'all';
    for (const { key, count } of entries) {
      const b = document.createElement('button');
      b.className = 'chip on';
      b.dataset.f = key;
      b.innerHTML = `<span style="color:${colorOf(key) || '#8a919e'}">●</span> ${labelOf(key) || key}<span class="n">${count}</span>`;
      b.onclick = () => {
        active = active === key ? 'all' : key;
        bar.querySelectorAll('.chip').forEach(x => x.classList.toggle('on', active === 'all' || x.dataset.f === active));
        onChange(active);
      };
      bar.appendChild(b);
    }
  }

  /** 卡片正文懒填充：三类卡工厂把正文构建挂到 el._fill 闭包，首次展开才建 DOM。
   *  与主页 app.js 的 Timeline.fillBody 同思路——全量预渲染的隐藏正文是手机端
   *  DOM/样式树/内存压力的主源 */
  function fillCardBody(card) {
    if (card._filled || !card._fill) return;
    card._filled = true;
    card._fill();
  }

  /** 通用长卷渲染：时代分卷 → 年份组 → 中轴交替卡片。items 须已筛选。
   *  返回可见条数（同步计算）；DOM 分帧建（每帧 12ms 时间片，与 app.js renderEra
   *  同款预算），全部就位后回调 done。同根重入（筛选/搜索连点）由 token 作废旧批次。 */
  function renderLongScroll(rootSel, eras, items, yearOf, cardFn, countUnit, done) {
    const root = document.querySelector(rootSel);
    if (!root) { if (done) done(0); return 0; }
    root._lrsToken = (root._lrsToken || 0) + 1;
    const token = root._lrsToken;
    root.innerHTML = '';
    const eraIndexOf = (y) => eras.findIndex(e => y >= e.range[0] && y < e.range[1]);
    const tasks = [];
    let shown = 0;
    eras.forEach((era, ei) => {
      const list = items.filter(it => eraIndexOf(+yearOf(it) || 0) === ei)
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
      const flip = { v: ei % 2 };                        // 同一时代内跨年份组连续交替
      for (const [year, its] of byYear) tasks.push({ body, year, its, flip });
      root.appendChild(sec);
      shown += list.length;
    });
    if (!shown) {
      root.innerHTML = '<div class="empty">没有匹配的条目——换个关键词试试</div>';
      if (done) done(0);
      return 0;
    }
    let ti = 0;
    const step = () => {
      if (token !== root._lrsToken) return;              // 已被更新的渲染作废
      const t0 = performance.now();
      while (ti < tasks.length && performance.now() - t0 < 12) {
        const { body, year, its, flip } = tasks[ti++];
        const g = document.createElement('div');
        g.className = 'yearGroup';
        g.innerHTML = `<div class="yBadge"><span>${year}</span>${its.length > 1 ? `<small>${its.length}</small>` : ''}</div><div class="cards"></div>`;
        const cards = g.querySelector('.cards');
        const frag = document.createDocumentFragment();
        for (const it of its) {
          const c = cardFn(it);
          if (flip.v) c.classList.add('right');
          frag.appendChild(c);
          flip.v = 1 - flip.v;
        }
        cards.appendChild(frag);
        body.appendChild(g);
      }
      if (ti < tasks.length) setTimeout(step, 0);
      else if (done) done(shown);
    };
    step();
    return shown;
  }

  /** 长卷行内展开事件委托：cMore 切换、卡片点击展开（点链接不触发）；展开时懒填充正文 */
  function wireExpand(rootSel) {
    document.querySelector(rootSel).addEventListener('click', ev => {
      const more = ev.target.closest('.cMore');
      if (more) {
        const card = more.closest('.card');
        if (card.classList.toggle('open')) fillCardBody(card);
        return;
      }
      const card = ev.target.closest('.card');
      if (card && !ev.target.closest('a')) { card.classList.add('open'); fillCardBody(card); }
    });
  }

  /** 深链定位：?p=/?e=/?w= 命中卡片 → 填正文 + 展开 + 居中 + 描边闪烁。
   *  居中用 window.scrollTo 瞬时定点（scrollIntoView 会吃 html{scroll-behavior:smooth}
   *  变成动画滚动，且 content-visibility 屏外组估算高度会漂移）——与 app.js 年度跳转
   *  同款「定点 + 落定回正」：350ms/1400ms 各校一次。 */
  function deepLinkCard(id, rootSel) {
    if (!id) return;
    const c = document.querySelector(`${rootSel} .card[data-id="${CSS.escape(id)}"]`);
    if (!c) return;
    fillCardBody(c);
    c.classList.add('open');
    const center = () => {
      if (!c.isConnected) return;
      const y = c.getBoundingClientRect().top + window.scrollY - innerHeight / 2 + Math.min(c.offsetHeight / 2, 240);
      window.scrollTo({ top: Math.max(0, y), behavior: 'instant' });
    };
    center();
    setTimeout(center, 350);
    setTimeout(center, 1400);
    c.style.outline = '2px solid var(--accent)';
    setTimeout(() => { c.style.outline = ''; }, 2600);
  }

  /* ── 分卷与配色配置（主页四视图与子页共用） ── */
  const P_ERAS = [
    { name: '文艺复兴与启蒙', range: [-Infinity, 1700] },
    { name: '近代先驱', range: [1700, 1900] },
    { name: '世纪之交', range: [1900, 1930] },
    { name: '战后与重建', range: [1930, 1950] },
    { name: '共和国一代', range: [1950, 1970] },
    { name: '黄金一代', range: [1970, 1985] },
    { name: '千禧一代', range: [1985, Infinity] },
  ];
  const E_ERAS = [
    { name: '奠基纪元', range: [-Infinity, 1990] },
    { name: '拨号纪元', range: [1990, 1999] },
    { name: '门户纪元', range: [1999, 2005] },
    { name: 'Web2.0 纪元', range: [2005, 2011] },
    { name: '移动纪元', range: [2011, 2016] },
    { name: '智能纪元', range: [2016, Infinity] },
  ];
  const W_ERAS = [
    { name: '纸质与胶片时代', range: [-Infinity, 1994] },
    { name: '拨号时代', range: [1994, 2000] },
    { name: '门户与光碟时代', range: [2000, 2005] },
    { name: 'Web2.0 时代', range: [2005, 2011] },
    { name: '移动与流媒体时代', range: [2011, 2017] },
    { name: '算法与国创时代', range: [2017, Infinity] },
  ];
  const FIELDS = { ai: 'AI', internet: '互联网', hardware: '硬件制造', company: '公司商业', game: '游戏电竞', creator: '创作者', science: '科学', finance: '金融', media: '媒体', sport: '体育' };
  const FCOLOR = { ai: '#c96a93', internet: '#5b9bd5', hardware: '#d08a4e', company: '#3aa891', game: '#8b6fc9', creator: '#c9b458', science: '#7ba05b', finance: '#4a9e8f', media: '#c9a86a', sport: '#c9584f' };
  const TYPES = { company: '企业', community: '社区', media: '媒体', service: '服务', infrastructure: '基础设施', organization: '机构', institution: '机构', game: '游戏' };
  const TCOLOR = { company: '#3aa891', community: '#5b9bd5', media: '#c9a86a', service: '#c96a93', infrastructure: '#7ba05b', organization: '#8a919e', game: '#8b6fc9' };
  const WTYPES = { film: '电影', tv: '剧集', book: '图书', netnovel: '网络文学', music: '音乐', game: '游戏', comic: '动画漫画', documentary: '纪录片', variety: '综艺' };
  const WTCOLOR = { film: '#c9584f', tv: '#c96a93', book: '#3aa891', netnovel: '#5b9bd5', music: '#c9a86a', game: '#8b6fc9', comic: '#d08a4e', documentary: '#7ba05b', variety: '#c9b458' };
  const SCONF = { active: 'v', declined: 's', closed: 'u' };
  const STATUS_LABEL = { active: '活跃', declined: '衰落', acquired: '被收购', privatized: '已退市', closed: '关停' };
  const REGION_LABEL = { cn: '中国', world: '世界' };

  /* ── 卡片模板（主页视图与子页共用同一套 DOM 结构） ── */

  function personCard(p, ctx) {
    const el = document.createElement('div');
    el.className = 'card in';
    el.dataset.id = p.id;
    const life = `${String(p.birth).slice(0, 4)}–${p.death ? String(p.death).slice(0, 4) : ''}`;
    const alive = p.death ? '<span class="cConf">已故</span>' : '<span class="cConf v">在世</span>';
    el.innerHTML = `
      <div class="cHead">
        <span class="cDate">${life}</span>
        <span class="cDot" style="--c:${FCOLOR[p.field] || '#8a919e'}"></span><span>${FIELDS[p.field] || p.field}</span>
        ${alive}
        <span class="cAcc">${p.region === 'cn' ? '中国' : '国际'}</span>
      </div>
      <h3 class="cTitle"><a>${esc(p.name)}${p.en_name ? ` <span class="arrow" style="font-family:var(--mono);font-size:.72rem;color:var(--faint)">${esc(p.en_name)}</span>` : ''}</a></h3>
      <p class="cSum">${esc(p.headline)}。${esc(p.summary_30s.slice(0, 90))}${p.summary_30s.length > 90 ? '…' : ''}</p>
      <button class="cMore">展开人生历程 <i>∨</i></button>
      <div class="cBody"><div class="cBodyInner"></div></div>`;
    /* 正文（小传/人生历程/成就/遗产/争议/相关世家/来源）懒填充：展开才建 */
    el._fill = () => {
      const tl = p.timeline.map(t => `<li><span class="td">${dsh(t)}</span><span class="tx">${esc(t.text)}</span></li>`).join('');
      const ach = (p.achievements || []).map(a => `· ${esc(a)}`).join('<br>');
      const ctzs = (p.controversies || []).length
        ? `<div class="sec"><span class="lab">争议记录</span>${p.controversies.map(c => `<div class="ctzBox">${esc(c)}</div>`).join('')}</div>` : '';
      const src = p.sources.map(s => `<li><a href="${safeUrl(s.url)}" target="_blank" rel="noopener">${esc(s.title)}</a></li>`).join('');
      const relE = (p.related_entities || []).length
        ? `<div class="sec"><span class="lab">相关世家</span><div class="relRow">${p.related_entities.map(r => `<a class="relChip" href="${relUrl(ctx, 'entities', 'e', r.id)}">${esc(r.name)}</a>`).join('')}</div></div>` : '';
      el.querySelector('.cBodyInner').innerHTML = `
        <div class="sec"><span class="lab">小传</span><p>${esc(p.bio || p.summary_30s)}</p></div>
        <div class="sec"><span class="lab">人生历程</span><ul class="tlList">${tl}</ul></div>
        ${ach ? `<div class="sec"><span class="lab">关键成就</span><p>${ach}</p></div>` : ''}
        <div class="sec"><span class="lab">现状与遗产</span><div class="legacyBox">${esc(p.legacy || (p.death ? '其影响已沉淀为行业史的一部分。' : '仍在活跃，故事未完。'))}</div></div>${ctzs}${relE}
        <div class="sec"><span class="lab">来源</span><ul class="srcList">${src}</ul></div>`;
    };
    return el;
  }

  function entityCard(e, ctx) {
    const el = document.createElement('div');
    el.className = 'card in';
    el.dataset.id = e.id;
    const span = e.dissolved ? `${String(e.founded).slice(0, 4)}–${String(e.dissolved).slice(0, 4)}` : `${String(e.founded).slice(0, 4)}–今`;
    const st = `<span class="cConf ${SCONF[e.status] || ''}">${STATUS_LABEL[e.status] || e.status}</span>`;
    el.innerHTML = `
      <div class="cHead">
        <span class="cDate">${span}</span>
        <span class="cDot" style="--c:${TCOLOR[e.type] || '#8a919e'}"></span><span>${TYPES[e.type] || e.type}</span>
        ${st}
        <span class="cAcc">${REGION_LABEL[e.region] || ''}</span>
      </div>
      <h3 class="cTitle"><a>${esc(e.name)}${e.en_name ? ` <span class="arrow" style="font-family:var(--mono);font-size:.72rem;color:var(--faint)">${esc(e.en_name)}</span>` : ''}</a></h3>
      <p class="cSum">${esc(e.headline)}。${esc(e.summary_30s.slice(0, 90))}${e.summary_30s.length > 90 ? '…' : ''}</p>
      <button class="cMore">展开兴衰历程 <i>∨</i></button>
      <div class="cBody"><div class="cBodyInner"></div></div>`;
    /* 正文（概述/历程/关键数字/遗产/争议/相关人物/来源）懒填充：展开才建 */
    el._fill = () => {
      const tl = e.timeline.map(t => `<li><span class="td">${dsh(t)}</span><span class="tx">${esc(t.text)}</span></li>`).join('');
      const ms = (e.milestones || []).map(a => `· ${esc(a)}`).join('<br>');
      const ctzs = (e.controversies || []).length
        ? `<div class="sec"><span class="lab">争议记录</span>${e.controversies.map(c => `<div class="ctzBox">${esc(c)}</div>`).join('')}</div>` : '';
      const src = e.sources.map(s => `<li><a href="${safeUrl(s.url)}" target="_blank" rel="noopener">${esc(s.title)}</a></li>`).join('');
      const rel = (e.related_persons || []).length
        ? `<div class="sec"><span class="lab">相关人物</span><div class="relRow">${e.related_persons.map(r => `<a class="relChip" href="${relUrl(ctx, 'persons', 'p', r.id)}">${esc(r.name)}</a>`).join('')}</div></div>` : '';
      el.querySelector('.cBodyInner').innerHTML = `
        <div class="sec"><span class="lab">兴衰概述</span><p>${esc(e.bio || e.summary_30s)}</p></div>
        <div class="sec"><span class="lab">兴衰历程</span><ul class="tlList">${tl}</ul></div>
        ${ms ? `<div class="sec"><span class="lab">关键数字</span><p>${ms}</p></div>` : ''}
        <div class="sec"><span class="lab">现状与遗产</span><div class="legacyBox">${esc(e.legacy)}</div></div>${ctzs}${rel}
        <div class="sec"><span class="lab">来源</span><ul class="srcList">${src}</ul></div>`;
    };
    return el;
  }

  function workCard(w) {
    const el = document.createElement('div');
    el.className = 'card in';
    el.dataset.id = w.id;
    el.innerHTML = `
      <div class="cHead">
        <span class="cDate">${String(w.released).slice(0, 4)}</span>
        <span class="cDot" style="--c:${WTCOLOR[w.type] || '#8a919e'}"></span><span>${WTYPES[w.type] || w.type}</span>
        <span class="cAcc">${esc((w.creators || '').slice(0, 18))}</span>
      </div>
      <h3 class="cTitle"><a>${esc(w.title)}${w.en_title ? ` <span class="arrow" style="font-family:var(--mono);font-size:.72rem;color:var(--faint)">${esc(w.en_title)}</span>` : ''}</a></h3>
      <p class="cSum">${esc(w.headline)}。${esc(w.summary_30s.slice(0, 90))}${w.summary_30s.length > 90 ? '…' : ''}</p>
      <button class="cMore">展开作品生命线 <i>∨</i></button>
      <div class="cBody"><div class="cBodyInner"></div></div>`;
    /* 正文（小传/生命线/回响/遗产/来源）懒填充：展开才建 */
    el._fill = () => {
      const tl = w.timeline.map(t => `<li><span class="td">${dsh(t)}</span><span class="tx">${esc(t.text)}</span></li>`).join('');
      const quotes = (w.quotes || []).length
        ? `<div class="sec"><span class="lab">经典回响</span>${w.quotes.map(q => `<div class="quoteBox">${esc(q)}</div>`).join('')}</div>` : '';
      const src = w.sources.map(s => `<li><a href="${safeUrl(s.url)}" target="_blank" rel="noopener">${esc(s.title)}</a></li>`).join('');
      el.querySelector('.cBodyInner').innerHTML = `
        <div class="sec"><span class="lab">作品小传</span><p>${esc(w.bio || w.summary_30s)}</p></div>
        <div class="sec"><span class="lab">生命线</span><ul class="tlList">${tl}</ul></div>
        ${quotes}
        <div class="sec"><span class="lab">精神遗产</span><div class="legacyBox">${esc(w.legacy)}</div></div>
        <div class="sec"><span class="lab">来源</span><ul class="srcList">${src}</ul></div>`;
    };
    return el;
  }

  return {
    DATA_BUILD, esc, safeUrl, fetchGz, dsh, matchQ, wireSearch, buildFilterChips,
    renderLongScroll, wireExpand, deepLinkCard, fillCardBody,
    P_ERAS, E_ERAS, W_ERAS, FIELDS, FCOLOR, TYPES, TCOLOR, WTYPES, WTCOLOR, SCONF, STATUS_LABEL, REGION_LABEL,
    personCard, entityCard, workCard,
  };
})();
