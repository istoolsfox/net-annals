/* 互联网编年史 · 星河长卷  app.js */
'use strict';

/* ── 配置 ─────────────────────────────────────────── */
const T0 = 1986, T1 = 2026.6, U = 88; // 年→世界坐标
const ERAS = [
  { name: '接入前史', range: [1986, 1994.4], color: 0x5b7bd5 },
  { name: '拨号时代', range: [1994.4, 2000], color: 0x4f8fdd },
  { name: '门户与泡沫', range: [2000, 2003], color: 0x7a6fd0 },
  { name: 'Web2.0 前夜', range: [2003, 2005], color: 0x9a6bc9 },
  { name: 'Web2.0', range: [2005, 2010], color: 0xb95fb4 },
  { name: '移动互联网', range: [2010, 2015], color: 0xe05e8f },
  { name: '移动成熟', range: [2015, 2020], color: 0xf08c5a },
  { name: '疫情与智能', range: [2020, 2026.6], color: 0x57c4d9 },
];
const CATS = [
  { k: 'milestone', name: '时代转折', color: '#ffd700' },
  { k: 'internet', name: '互联网', color: '#38bdf8' },
  { k: 'tech', name: '科技软件', color: '#8b5cf6' },
  { k: 'hardware', name: '硬件', color: '#fb923c' },
  { k: 'company', name: '公司商业', color: '#2dd4bf' },
  { k: 'product', name: '产品服务', color: '#f472b6' },
  { k: 'national', name: '国家大事', color: '#ef4444' },
  { k: 'world', name: '世界大事', color: '#94a3b8' },
  { k: 'society', name: '民间生活', color: '#a3e635' },
  { k: 'culture', name: '流行文化', color: '#facc15' },
  { k: 'economy', name: '经济金融', color: '#10b981' },
];
const CONF = { verified: ['实证', '#7ee787'], 'single-source': ['单一来源', '#e3c26d'], uncertain: ['存疑', '#ff9d7a'] };
const xOf = yf => (yf - T0) * U;
const xToDate = x => T0 + x / U;
const CATMAP = Object.fromEntries(CATS.map(c => [c.k, c]));

/* ── 全局状态 ─────────────────────────────────────── */
let EVENTS = [], byId = new Map(), ordered = [];
const catOn = Object.fromEntries(CATS.map(c => [c.k, true]));
let current = -1;            // 抽屉当前条目在 filtered() 中的下标
let view = 'galaxy';

const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const fmtDate = d => d.replace(/-/g, '.');
function hash(str) { let h = 2166136261; for (let i = 0; i < str.length; i++) { h ^= str.charCodeAt(i); h = Math.imul(h, 16777619); } return ((h >>> 0) % 10000) / 10000; }
const filtered = () => ordered.filter(e => catOn[e.category]);

/* ── 数据加载 ─────────────────────────────────────── */
async function boot() {
  try {
    const res = await fetch('data.json');
    if (!res.ok) throw new Error(res.status);
    const data = await res.json();
    EVENTS = data.events;
    EVENTS.forEach(e => byId.set(e.id, e));
    ordered = [...EVENTS].sort((a, b) => a.date < b.date ? -1 : a.date > b.date ? 1 : 0);
    $('#stats').textContent =
      `${EVENTS.length.toLocaleString()} 条事件 · ${ordered[0].date.slice(0, 4)}–${ordered[ordered.length - 1].date.slice(0, 4)} · ` +
      `实证 ${Math.round(EVENTS.filter(e => e.date_confidence === 'verified').length / EVENTS.length * 100)}% · 数据持续增补`;
    $('#buildTime').textContent = (data.generated || '').replace('T', ' ').slice(0, 16);
    initFilters(); initEraNav(); initGalaxy(); initList(); initDrawer(); initToggle();
    $('#loader').classList.add('hide');
    setTimeout(() => $('#loader').remove(), 800);
  } catch (err) {
    $('#loader').innerHTML = `<div class="pulse"></div><div>数据尚未生成或加载失败（${esc(err.message)}）。<br>请先在项目根目录运行 <code>./scripts/build.sh</code>，然后用本地服务器打开本页：<br><code>cd site && python3 -m http.server 8788</code></div>`;
  }
}

/* ── 顶栏控件 ─────────────────────────────────────── */
function initFilters() {
  const box = $('#catFilters');
  for (const c of CATS) {
    const b = document.createElement('button');
    b.innerHTML = `<span class="dot" style="background:${c.color}"></span>${c.name}`;
    b.title = c.k;
    b.onclick = () => { catOn[c.k] = !catOn[c.k]; b.classList.toggle('off', !catOn[c.k]); applyFilter(); };
    box.appendChild(b);
  }
}
function initEraNav() {
  const nav = $('#eraNav');
  const all = document.createElement('button');
  all.textContent = '全景'; all.classList.add('active');
  all.onclick = () => { flyTo((xOf(T0) + xOf(T1)) / 2, 300); setActive(all); };
  nav.appendChild(all);
  for (const era of ERAS) {
    const b = document.createElement('button');
    b.textContent = `${era.name} ${String(Math.floor(era.range[0])).slice(2)}–${String(Math.ceil(era.range[1])).slice(2)}`;
    b.onclick = () => {
      const [a, z] = era.range;
      flyTo((xOf(a) + xOf(z)) / 2, fitDist(z - a));
      setActive(b);
    };
    nav.appendChild(b);
  }
}
function setActive(btn) { document.querySelectorAll('#eraNav button').forEach(x => x.classList.remove('active')); btn.classList.add('active'); }
function initToggle() {
  $('#filterToggle').onclick = () => document.body.classList.toggle('show-filters');
  const g = $('#btnGalaxy'), l = $('#btnList');
  g.onclick = () => { view = 'galaxy'; $('#galaxyView').hidden = false; $('#listView').hidden = true; g.classList.add('active'); l.classList.remove('active'); };
  l.onclick = () => { view = 'list'; $('#galaxyView').hidden = true; $('#listView').hidden = false; l.classList.add('active'); g.classList.remove('active'); renderList(); };
}

/* ── 三维星河 ─────────────────────────────────────── */
let renderer, scene, camera, points, glow, sel;
const rig = { tx: (xOf(T0) + xOf(T1)) / 2, yaw: 0, pitch: 0.62, dist: 0 }; // dist=0 → 首帧按视口计算全景
let tween = null, raycaster, mouse = new THREE.Vector2(), uTime = { value: 0 }, uProgress = { value: 0 };
let mLabels = [], yLabels = [], eraLabels = [], posArr, milestones = [];

function initGalaxy() {
  const canvas = $('#river');
  renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  scene = new THREE.Scene();
  scene.fog = new THREE.FogExp2(0x05070f, 0.00025);
  camera = new THREE.PerspectiveCamera(55, 1, 0.1, 3000);

  buildEraBands(); buildTicks(); buildBackdrop();
  buildPoints(); buildGlow(); buildSelection();
  buildLabels();

  raycaster = new THREE.Raycaster();
  raycaster.params.Points = { threshold: 1.6 };

  bindControls(canvas);
  addEventListener('resize', resize);
  resize();
  animate();
  tweenProgress();
}

function buildPoints() {
  const n = EVENTS.length;
  posArr = new Float32Array(n * 3);
  const col = new Float32Array(n * 3), size = new Float32Array(n),
        birth = new Float32Array(n), phase = new Float32Array(n), vis = new Float32Array(n);
  const cTmp = new THREE.Color();
  EVENTS.forEach((e, i) => {
    const yf = +e.date.slice(0, 4) + (+e.date.slice(5, 7) - 1) / 12 + (+e.date.slice(8, 10) - 1) / 365;
    const h1 = hash(e.id + 'a'), h2 = hash(e.id + 'b'), h3 = hash(e.id + 'c');
    posArr[i * 3] = xOf(yf) + (h1 - 0.5) * U * 0.86;
    posArr[i * 3 + 1] = 2.4 + h2 * 9.5;
    posArr[i * 3 + 2] = (h3 - 0.5) * 30;
    cTmp.set(CATMAP[e.category]?.color || '#94a3b8');
    col[i * 3] = cTmp.r; col[i * 3 + 1] = cTmp.g; col[i * 3 + 2] = cTmp.b;
    const big = e.milestone;
    size[i] = big ? 7.5 + h1 * 3 : 1.7 + h2 * 1.7;
    birth[i] = i / n; phase[i] = h3; vis[i] = 1;
    if (big) milestones.push({ e, i });
  });
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(posArr, 3));
  g.setAttribute('aColor', new THREE.BufferAttribute(col, 3));
  g.setAttribute('aSize', new THREE.BufferAttribute(size, 1));
  g.setAttribute('aBirth', new THREE.BufferAttribute(birth, 1));
  g.setAttribute('aPhase', new THREE.BufferAttribute(phase, 1));
  g.setAttribute('aVis', new THREE.BufferAttribute(vis, 1));
  const m = new THREE.ShaderMaterial({
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
    uniforms: { uTime, uProgress, uPR: { value: Math.min(devicePixelRatio, 2) } },
    vertexShader: `
      attribute vec3 aColor; attribute float aSize, aBirth, aPhase, aVis;
      uniform float uTime, uProgress, uPR;
      varying vec3 vC; varying float vA;
      void main(){
        vC = aColor;
        if (aBirth > uProgress || aVis < 0.5) { gl_Position = vec4(2.0,2.0,2.0,1.0); gl_PointSize = 0.0; vA = 0.0; return; }
        vec4 mv = modelViewMatrix * vec4(position, 1.0);
        float tw = 0.72 + 0.28 * sin(uTime * (0.9 + aPhase * 1.8) + aPhase * 40.0);
        vA = tw;
        gl_PointSize = max(aSize * uPR * (300.0 / -mv.z), 1.6 * uPR);
        gl_Position = projectionMatrix * mv;
      }`,
    fragmentShader: `
      varying vec3 vC; varying float vA;
      void main(){
        float d = length(gl_PointCoord - 0.5);
        float a = pow(smoothstep(0.5, 0.02, d), 1.6);
        gl_FragColor = vec4(vC, a * vA);
      }`,
  });
  points = new THREE.Points(g, m);
  scene.add(points);
}

function buildGlow() {
  const n = milestones.length;
  const pos = new Float32Array(n * 3), ph = new Float32Array(n);
  milestones.forEach((m, j) => {
    pos[j * 3] = posArr[m.i * 3]; pos[j * 3 + 1] = posArr[m.i * 3 + 1]; pos[j * 3 + 2] = posArr[m.i * 3 + 2];
    ph[j] = hash(m.e.id + 'g');
  });
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  g.setAttribute('aPhase', new THREE.BufferAttribute(ph, 1));
  const m = new THREE.ShaderMaterial({
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
    uniforms: { uTime, uProgress, uPR: { value: Math.min(devicePixelRatio, 2) } },
    vertexShader: `
      attribute float aPhase; uniform float uTime, uProgress, uPR;
      varying float vA;
      void main(){
        vec4 mv = modelViewMatrix * vec4(position, 1.0);
        vA = 0.55 + 0.45 * sin(uTime * 1.6 + aPhase * 20.0);
        gl_PointSize = max((34.0 + 8.0 * sin(uTime * 1.6 + aPhase * 20.0)) * (300.0 / -mv.z), 4.0 * uPR);
        gl_Position = projectionMatrix * mv;
      }`,
    fragmentShader: `
      varying float vA;
      void main(){
        float d = length(gl_PointCoord - 0.5);
        float ring = smoothstep(0.5, 0.42, d) - smoothstep(0.34, 0.16, d);
        float core = smoothstep(0.2, 0.0, d) * 0.5;
        gl_FragColor = vec4(1.0, 0.86, 0.35, (ring * 0.85 + core) * vA);
      }`,
  });
  glow = new THREE.Points(g, m);
  scene.add(glow);
}

function buildSelection() {
  const cv = document.createElement('canvas'); cv.width = cv.height = 128;
  const ctx = cv.getContext('2d');
  const gr = ctx.createRadialGradient(64, 64, 0, 64, 64, 64);
  gr.addColorStop(0, 'rgba(255,255,255,0.9)'); gr.addColorStop(0.25, 'rgba(255,225,130,0.5)'); gr.addColorStop(1, 'rgba(255,215,0,0)');
  ctx.fillStyle = gr; ctx.fillRect(0, 0, 128, 128);
  const tex = new THREE.CanvasTexture(cv);
  sel = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false }));
  sel.scale.set(9, 9, 1); sel.visible = false;
  scene.add(sel);
}

function buildEraBands() {
  for (const era of ERAS) {
    const [a, z] = era.range, w = xOf(z) - xOf(a);
    const g = new THREE.PlaneGeometry(w, 52);
    const m = new THREE.MeshBasicMaterial({ color: era.color, transparent: true, opacity: 0.05, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide });
    const p = new THREE.Mesh(g, m);
    p.rotation.x = -Math.PI / 2;
    p.position.set(xOf(a) + w / 2, -2.6, 0);
    scene.add(p);
  }
  const axis = new THREE.Mesh(
    new THREE.PlaneGeometry(xOf(T1) - xOf(T0) + 200, 0.5),
    new THREE.MeshBasicMaterial({ color: 0x3d64b8, transparent: true, opacity: 0.4, blending: THREE.AdditiveBlending, depthWrite: false })
  );
  axis.rotation.x = -Math.PI / 2;
  axis.position.set((xOf(T0) + xOf(T1)) / 2, 0, 0);
  scene.add(axis);
}

function buildTicks() {
  const pts = [];
  for (let y = 1986; y <= 2026; y++) {
    const x = xOf(y), big = y % 10 === 0;
    pts.push(x, 0, -24, x, big ? 2.2 : 1.1, -24);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(pts), 3));
  scene.add(new THREE.LineSegments(g, new THREE.LineBasicMaterial({ color: 0x44598c, transparent: true, opacity: 0.55 })));
}

function buildBackdrop() {
  const n = 500, pos = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) {
    pos[i * 3] = (hash('bg' + i) - 0.5) * 5000;
    pos[i * 3 + 1] = hash('bgy' + i) * 900 - 100;
    pos[i * 3 + 2] = -400 - hash('bgz' + i) * 1600;
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  scene.add(new THREE.Points(g, new THREE.PointsMaterial({ color: 0x8fa8d8, size: 1.6, sizeAttenuation: false, transparent: true, opacity: 0.35 })));
}

function buildLabels() {
  const ov = $('#overlay');
  for (const era of ERAS) {
    const d = document.createElement('div');
    d.className = 'eLabel';
    d.textContent = `${era.name} ${String(Math.floor(era.range[0])).slice(2)}–${String(Math.ceil(era.range[1])).slice(2)}`;
    ov.appendChild(d);
    eraLabels.push({ era, el: d });
  }
  for (let y = 1986; y <= 2026; y++) {
    const d = document.createElement('div');
    d.className = 'yLabel' + (y % 10 === 0 ? ' decade' : '');
    d.textContent = y;
    ov.appendChild(d);
    yLabels.push({ year: y, el: d });
  }
  for (let i = 0; i < Math.min(milestones.length, 70); i++) {
    const d = document.createElement('div');
    d.className = 'mLabel'; d.style.display = 'none';
    ov.appendChild(d);
    mLabels.push({ el: d, m: milestones[i] });
    d.onclick = () => openDrawerById(mLabels[i].m.e.id);
  }
}

/* ── 相机与交互 ───────────────────────────────────── */
function fitDist(spanYears) {
  const fovX = 2 * Math.atan(Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)) * camera.aspect);
  return Math.min(2400, Math.max(30, (spanYears * U * 1.02) / (2 * Math.tan(fovX / 2))));
}
function flyTo(tx, dist) {
  tween = { t0: performance.now(), dur: 950, fromX: rig.tx, toX: tx, fromD: rig.dist, toD: dist };
}
function tweenProgress() {
  uProgress.value = 0;
  const t0 = performance.now();
  (function step() {
    const p = Math.min(1, (performance.now() - t0) / 2800);
    uProgress.value = p * p * (3 - 2 * p);
    if (p < 1) requestAnimationFrame(step);
  })();
}
function updateCamera() {
  if (rig.dist === 0) rig.dist = fitDist(T1 - T0);
  if (tween) {
    const p = Math.min(1, (performance.now() - tween.t0) / tween.dur);
    const e = p < 0.5 ? 4 * p ** 3 : 1 - Math.pow(-2 * p + 2, 3) / 2;
    rig.tx = tween.fromX + (tween.toX - tween.fromX) * e;
    rig.dist = tween.fromD + (tween.toD - tween.fromD) * e;
    if (p >= 1) tween = null;
  }
  const ty = 7;
  camera.position.set(
    rig.tx + rig.dist * Math.sin(rig.yaw) * Math.cos(rig.pitch),
    ty + rig.dist * Math.sin(rig.pitch),
    rig.dist * Math.cos(rig.yaw) * Math.cos(rig.pitch)
  );
  camera.lookAt(rig.tx, ty, 0);
}

function bindControls(canvas) {
  let down = null, moved = 0;
  const touches = new Map();
  let pinchBase = null;
  canvas.addEventListener('pointerdown', ev => {
    canvas.setPointerCapture(ev.pointerId);
    if (ev.pointerType === 'touch') {
      touches.set(ev.pointerId, { x: ev.clientX, y: ev.clientY });
      if (touches.size === 2) {
        const [a, b] = [...touches.values()];
        pinchBase = { gap: Math.hypot(a.x - b.x, a.y - b.y), dist: rig.dist };
        down = null;
      } else if (touches.size === 1) {
        down = { x: ev.clientX, y: ev.clientY, shift: false };
        moved = 0;
      }
      tween = null;
      return;
    }
    down = { x: ev.clientX, y: ev.clientY, shift: ev.shiftKey || ev.button === 2 };
    moved = 0; tween = null;
  });
  canvas.addEventListener('pointermove', ev => {
    if (touches.has(ev.pointerId)) {
      touches.set(ev.pointerId, { x: ev.clientX, y: ev.clientY });
      if (touches.size === 2 && pinchBase) {
        const [a, b] = [...touches.values()];
        const gap = Math.hypot(a.x - b.x, a.y - b.y);
        if (gap > 10) rig.dist = THREE.MathUtils.clamp(pinchBase.dist * (pinchBase.gap / gap), 26, 2400);
      } else if (touches.size === 1 && down) {
        const dx = ev.clientX - down.x, dy = ev.clientY - down.y;
        moved += Math.abs(dx) + Math.abs(dy);
        const panScale = THREE.MathUtils.clamp(rig.dist / 620, 0.02, 4);
        rig.tx = THREE.MathUtils.clamp(rig.tx - dx * panScale, xOf(T0 - 1), xOf(T1));
        rig.pitch = THREE.MathUtils.clamp(rig.pitch + dy * 0.0022, 0.1, 1.25);
        down.x = ev.clientX; down.y = ev.clientY;
      }
      return;
    }
    if (down) {
      const dx = ev.clientX - down.x, dy = ev.clientY - down.y;
      moved += Math.abs(dx) + Math.abs(dy);
      if (down.shift) { rig.yaw = THREE.MathUtils.clamp(rig.yaw + dx * 0.003, -1.0, 1.0); }
      else {
        const panScale = THREE.MathUtils.clamp(rig.dist / 620, 0.02, 4);
        rig.tx = THREE.MathUtils.clamp(rig.tx - dx * panScale, xOf(T0 - 1), xOf(T1));
        rig.pitch = THREE.MathUtils.clamp(rig.pitch + dy * 0.0022, 0.1, 1.25);
      }
      down.x = ev.clientX; down.y = ev.clientY;
      $('#river').style.cursor = 'grabbing';
    } else hover(ev);
  });
  const endTouch = ev => {
    touches.delete(ev.pointerId);
    if (touches.size < 2) pinchBase = null;
    if (touches.size === 1) {
      const [p] = [...touches.values()];
      down = { x: p.x, y: p.y, shift: false }; moved = 99;
    } else if (touches.size === 0) down = null;
  };
  canvas.addEventListener('pointercancel', endTouch);
  canvas.addEventListener('pointerup', ev => {
    if (ev.pointerType === 'touch') {
      const wasPinch = touches.size >= 2;
      endTouch(ev);
      if (wasPinch) return;
      if (moved < 10) pick(ev);
      $('#river').style.cursor = 'grab';
      return;
    }
    if (down && moved < 7) pick(ev);
    down = null; $('#river').style.cursor = 'grab';
  });
  canvas.addEventListener('pointerleave', () => { $('#hoverTip').style.display = 'none'; });
  canvas.addEventListener('wheel', ev => {
    ev.preventDefault(); tween = null;
    rig.dist = THREE.MathUtils.clamp(rig.dist * Math.exp(ev.deltaY * 0.001), 26, 2400);
  }, { passive: false });
  canvas.addEventListener('contextmenu', ev => ev.preventDefault());
  addEventListener('keydown', ev => {
    if (ev.key === 'Escape') closeDrawer();
    if ($('#drawer').classList.contains('open')) {
      if (ev.key === 'ArrowRight') stepDrawer(1);
      if (ev.key === 'ArrowLeft') stepDrawer(-1);
    } else {
      if (ev.key === 'ArrowRight') rig.tx = Math.min(xOf(T1), rig.tx + U);
      if (ev.key === 'ArrowLeft') rig.tx = Math.max(xOf(T0 - 1), rig.tx - U);
    }
  });
}

function castAt(ev) {
  const r = $('#river').getBoundingClientRect();
  mouse.set(((ev.clientX - r.left) / r.width) * 2 - 1, -((ev.clientY - r.top) / r.height) * 2 + 1);
  raycaster.setFromCamera(mouse, camera);
  raycaster.params.Points.threshold = THREE.MathUtils.clamp(rig.dist * 0.016, 0.9, 4.2);
  const hits = raycaster.intersectObject(points);
  for (const h of hits) {
    const e = EVENTS[h.index];
    if (e && catOn[e.category]) return { e, point: h };
  }
  return null;
}
function hover(ev) {
  const hit = castAt(ev);
  const tip = $('#hoverTip');
  if (!hit) { tip.style.display = 'none'; $('#river').style.cursor = 'grab'; return; }
  $('#river').style.cursor = 'pointer';
  const e = hit.e;
  tip.innerHTML = `<div class="d">${fmtDate(e.date)}</div><div class="t">${esc(e.title)}</div><div class="c">${CATMAP[e.category]?.name || ''}${e.milestone ? ' · ★ 时代转折' : ''}</div>`;
  tip.style.display = 'block';
  const tw = tip.offsetWidth;
  tip.style.left = Math.min(ev.clientX + 14, innerWidth - tw - 12) + 'px';
  tip.style.top = (ev.clientY + 16) + 'px';
}
function pick(ev) {
  const hit = castAt(ev);
  if (hit) openDrawer(hit.e);
}

/* ── 标签投影 ─────────────────────────────────────── */
const v3 = new THREE.Vector3();
function project(x, y, z) {
  v3.set(x, y, z).project(camera);
  if (v3.z > 1) return null;
  return { x: (v3.x + 1) / 2 * innerWidth, y: (1 - v3.y) / 2 * innerHeight };
}
function updateOverlay() {
  let lastX = -100;
  for (const { year, el } of yLabels) {
    const p = project(xOf(year), 0, -24);
    if (!p || p.x < -20 || p.x > innerWidth + 20 || p.y < 90 || p.y > innerHeight - 60) { el.style.display = 'none'; continue; }
    const decade = year % 10 === 0;
    if (!decade && p.x - lastX < 38) { el.style.display = 'none'; continue; }
    el.style.display = 'block';
    el.style.left = p.x + 'px'; el.style.top = (p.y + 6) + 'px';
    lastX = p.x;
  }
  for (const { era, el } of eraLabels) {
    const pa = project(xOf(era.range[0]), -2.2, 24), pb = project(xOf(era.range[1]), -2.2, 24);
    if (!pa || !pb || pa.y < 100 || pa.y > innerHeight - 40) { el.style.display = 'none'; continue; }
    if (Math.abs(pb.x - pa.x) < 150) { el.style.display = 'none'; continue; }
    el.style.display = 'block';
    el.style.left = ((pa.x + pb.x) / 2) + 'px';
    el.style.top = (Math.max(pa.y, pb.y) - 4) + 'px';
  }
  let shown = 0;
  const placed = [];
  for (const rec of mLabels) {
    const { e, i } = rec.m;
    if (!catOn[e.category] || shown >= 30) { rec.el.style.display = 'none'; continue; }
    const p = project(posArr[i * 3], posArr[i * 3 + 1] + 1.2, posArr[i * 3 + 2]);
    if (!p || p.x < 40 || p.x > innerWidth - 40 || p.y < 130 || p.y > innerHeight - 80) { rec.el.style.display = 'none'; continue; }
    const text = e.title.length > 13 ? e.title.slice(0, 13) + '…' : e.title;
    const estW = text.length * 11.5 + 44;
    const lx = Math.max(estW / 2 + 6, Math.min(innerWidth - estW / 2 - 6, p.x));
    const clash = placed.some(r => lx + estW / 2 > r.x0 && lx - estW / 2 < r.x1 && Math.abs(p.y - r.y) < 20);
    if (clash) { rec.el.style.display = 'none'; continue; }
    placed.push({ x0: lx - estW / 2, x1: lx + estW / 2, y: p.y });
    rec.el.style.display = 'block';
    rec.el.innerHTML = `<span class="yr">${e.date.slice(0, 4)}</span>${esc(text)}`;
    rec.el.style.left = lx + 'px'; rec.el.style.top = p.y + 'px';
    shown++;
  }
}

/* ── 过滤 ─────────────────────────────────────────── */
function applyFilter() {
  const vis = points.geometry.getAttribute('aVis');
  EVENTS.forEach((e, i) => vis.setX(i, catOn[e.category] ? 1 : 0));
  vis.needsUpdate = true;
  if (view === 'list') renderList();
  if (current >= 0) { const cur = filtered()[current]; if (cur && !catOn[cur.category]) closeDrawer(); }
}

/* ── 详情抽屉 ─────────────────────────────────────── */
function srcHtml(e) {
  return `<div class="dSec"><span class="lab">数据来源</span><ul class="srcList">` +
    e.sources.map(s => `<li><a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.title)}</a><span class="tp">${esc(s.type || '')}</span></li>`).join('') +
    `</ul></div>`;
}
function fillDrawer(e, idx) {
  const conf = CONF[e.date_confidence] || CONF.uncertain;
  $('#drawerBody').innerHTML = `
    <div class="dMeta">
      <span class="chip cat" style="border-color:${CATMAP[e.category]?.color}66;color:${CATMAP[e.category]?.color}">${CATMAP[e.category]?.name || e.category}</span>
      ${e.milestone && e.category !== 'milestone' ? '<span class="chip gold">★ 时代转折点</span>' : ''}
      <span class="chip">来源${conf[0]}</span>
      ${e.date_accuracy !== 'exact' ? `<span class="chip warn">${e.date_accuracy === 'month' ? '精确到月' : '精确到年'}</span>` : ''}
      <span class="chip">${e.region === 'cn' ? '中国' : '世界'}</span>
    </div>
    <div class="dDate">${fmtDate(e.date)}</div>
    <h2><a href="${esc(e.sources[0]?.url || '#')}" target="_blank" rel="noopener" title="点击标题跳转原文">${esc(e.title)} ↗</a></h2>
    <div class="s30"><span class="lab">⏱ 30 秒读完</span>${esc(e.summary_30s)}</div>
    <div class="dSec"><span class="lab">经过</span><p>${esc(e.detail)}</p></div>
    <div class="dSec"><span class="lab">影响</span><p>${esc(e.impact)}</p></div>
    <div class="dSec"><span class="lab">后续</span><p>${esc(e.aftermath)}</p></div>
    ${srcHtml(e)}
    <div class="eid">${esc(e.id)}</div>
    <div class="dNav"><button onclick="stepDrawer(-1)">← 上一条</button><button onclick="stepDrawer(1)">下一条 →</button></div>`;
  current = idx;
}
function openDrawer(e) {
  const f = filtered();
  const idx = f.indexOf(e);
  fillDrawer(e, idx);
  $('#drawer').classList.add('open');
  if (e.milestone || true) {
    const i = EVENTS.indexOf(e);
    sel.position.set(posArr[i * 3], posArr[i * 3 + 1], posArr[i * 3 + 2]);
    sel.visible = true;
  }
}
function openDrawerById(id) { const e = byId.get(id); if (e) openDrawer(e); }
function closeDrawer() { $('#drawer').classList.remove('open'); sel.visible = false; current = -1; }
function stepDrawer(d) {
  const f = filtered();
  if (!f.length) return;
  current = ((current ?? -1) + d + f.length) % f.length;
  fillDrawer(f[current], current);
}
function initDrawer() { $('#drawerClose').onclick = closeDrawer; }

/* ── 列表模式 ─────────────────────────────────────── */
function initList() {
  let timer;
  $('#search').addEventListener('input', () => { clearTimeout(timer); timer = setTimeout(renderList, 160); });
}
function renderList() {
  const q = $('#search').value.trim().toLowerCase();
  const box = $('#listContent');
  if (!q) {
    const years = {};
    for (const e of filtered()) (years[e.date.slice(0, 4)] ??= []).push(e);
    box.innerHTML = Object.keys(years).sort().reverse().map(y => {
      const list = years[y];
      const m = list.filter(e => e.milestone).length;
      return `<details data-year="${y}"><summary>${y} · ${list.length} 条${m ? ` <span class="mile">★${m} 个转折点</span>` : ''}</summary><div class="months"></div></details>`;
    }).join('');
    box.querySelectorAll('details').forEach(d => {
      d.addEventListener('toggle', () => { if (d.open && !d.dataset.loaded) { d.querySelector('.months').innerHTML = monthsHtml(years[d.dataset.year]); d.dataset.loaded = 1; } });
    });
    $('#searchCount').textContent = `${Object.values(years).reduce((s, a) => s + a.length, 0)} 条`;
  } else {
    const hits = filtered().filter(e =>
      [e.title, e.summary_30s, e.detail, ...(e.tags || [])].join(' ').toLowerCase().includes(q)).slice(0, 600);
    box.innerHTML = `<div class="monthGroup">${rowsHtml(hits)}</div>`;
    $('#searchCount').textContent = `${hits.length} 条结果${hits.length >= 600 ? '（截断）' : ''}`;
  }
  box.querySelectorAll('.eRow').forEach(r => r.onclick = () => openDrawerById(r.dataset.id));
}
function monthsHtml(list) {
  const months = {};
  for (const e of list) (months[e.date.slice(5, 7)] ??= []).push(e);
  return Object.keys(months).sort().map(m =>
    `<div class="monthGroup"><h4>${+m} 月</h4>${rowsHtml(months[m])}</div>`).join('');
}
function rowsHtml(list) {
  return list.map(e => `
    <div class="eRow" data-id="${esc(e.id)}">
      <div class="eHead">
        <span class="eDot" style="background:${CATMAP[e.category]?.color}"></span>
        <span class="eDate">${e.date}</span>
        <span class="eTitle">${esc(e.title)}</span>
        ${e.milestone ? '<span class="eStar">★</span>' : ''}
      </div>
      <p class="eSum">${esc(e.summary_30s)}</p>
    </div>`).join('');
}

/* ── 渲染循环 ─────────────────────────────────────── */
let hoverThrottle = 0;
function animate() {
  requestAnimationFrame(animate);
  uTime.value = performance.now() / 1000;
  updateCamera();
  renderer.render(scene, camera);
  if (view === 'galaxy') updateOverlay();
  if (sel.visible) { const s = 9 + Math.sin(uTime.value * 3) * 1.2; sel.scale.set(s, s, 1); }
}
function resize() {
  const w = innerWidth, h = innerHeight;
  renderer.setSize(w, h);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
}

boot();
