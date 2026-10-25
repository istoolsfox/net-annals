import React from 'react';
import { Composition, AbsoluteFill, Audio, interpolate, useCurrentFrame, Img, staticFile } from 'remotion';
import { C, SERIF, MONO } from './theme';
import { TEX, appleIcon, bgm } from './textures';

export const DUR = 960; // 32s @30fps —— 一镜到底，无转场

/* ── 虚拟长页：13 个 1080 高的分区纵向拼接，摄像机从头滚到尾 ── */
const SECTIONS: Array<{ img?: string; eyebrow?: string; title?: string }> = [
  { img: 'hero' },                                                            // 0 标题垫底
  { img: 'tl-1972', eyebrow: '编年史 · 1972', title: '大事，小事，转折事' },      // 1
  { img: 'tl-1994', eyebrow: '编年史 · 1994', title: '拨号时代' },               // 2
  { img: 'tl-2003', eyebrow: '编年史 · 2000', title: '门户与泡沫' },             // 3
  { img: 'tl-2010', eyebrow: '编年史 · 2010', title: '移动互联网' },             // 4
  { img: 'tl-2020', eyebrow: '编年史 · 2020', title: '疫情与智能' },             // 5
  { img: 'card-open', eyebrow: '溯源', title: '每一条，都可溯源' },              // 6
  { img: 'persons-top', eyebrow: '人物志', title: '一条条人生长卷' },            // 7
  { img: 'entities-top', eyebrow: '世家志', title: '兴衰成对，为每一家立传' },    // 8
  { img: 'works-top', eyebrow: '作品志', title: '精神地标' },                    // 9
  { img: 'today-drawer', eyebrow: '历史上的今天', title: '翻开任何一天' },        // 10
  { img: 'github', eyebrow: '开源', title: '整部史，全部可查' },                 // 11
  {},                                                                         // 12 CTA 落版
];
const SEC_H = 1080;
const PAGE_H = SECTIONS.length * SEC_H;         // 14,040
const MAX_SCROLL = PAGE_H - 1080;               // 12,960

/* 摄像机：0-90f 停在页首（标题），90-810f 匀速滚到底，之后停在 CTA */
const scrollYAt = (f: number): number => {
  const t0 = 90, t1 = 810;
  if (f <= t0) return 0;
  if (f >= t1) return MAX_SCROLL;
  const u = (f - t0) / (t1 - t0);
  const e = u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2; // easeInOutCubic
  return MAX_SCROLL * e;
};

/* 当前视口中心所在分区索引 */
const sectionAt = (f: number): number => {
  const center = scrollYAt(f) + 540;
  return Math.max(0, Math.min(SECTIONS.length - 1, Math.floor(center / SEC_H)));
};

/* 分区标题字卡：进入分区渐显、临近离开渐隐（滚动距离驱动，确定无误） */
const SectionCaption: React.FC<{ f: number; scrollY: number }> = ({ f, scrollY }) => {
  const idx = sectionAt(f);
  const s = SECTIONS[idx];
  if (!s.title || idx === 0) return null;
  const d = scrollY + 540 - idx * SEC_H;          // 视口中心深入本分区的距离
  const opacity = Math.max(0, Math.min(d / 200, (SEC_H - d) / 200, 1));
  if (opacity <= 0.02) return null;
  return (
    <div style={{ position: 'absolute', left: 110, bottom: 130, opacity }}>
      {s.eyebrow ? <div style={{ fontFamily: MONO, fontSize: 26, color: C.gold, letterSpacing: '0.34em', marginBottom: 14 }}>{s.eyebrow}</div> : null}
      <div style={{ fontFamily: SERIF, fontSize: 84, color: C.goldBright, fontWeight: 700, textShadow: '0 4px 30px #000d', display: 'inline-block', background: 'rgba(12,13,16,0.72)', border: '1px solid #c9a86a33', borderRadius: 12, padding: '12px 34px' }}>{s.title}</div>
    </div>
  );
};

/* 开场标题：摄像机未启动时悬浮于页首 */
const TitleCard: React.FC<{ f: number; scrollY: number }> = ({ f, scrollY }) => {
  const inOp = interpolate(f, [8, 38], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const outOp = 1 - interpolate(scrollY, [10, 320], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const op = Math.min(inOp, outOp);
  if (op <= 0.01) return null;
  const ls = `${interpolate(f, [8, 48], [0.26, 0.05], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })}em`;
  return (
    <AbsoluteFill style={{ alignItems: 'center', justifyContent: 'center', opacity: op }}>
      <div style={{ textAlign: 'center' }}>
        <h1 style={{ fontFamily: SERIF, fontSize: 104, color: C.goldBright, letterSpacing: ls, margin: 0, fontWeight: 700, textShadow: '0 6px 40px #000a' }}>四十年，钉在日期上</h1>
        <div style={{ width: 520, height: 1, background: `linear-gradient(90deg, transparent, ${C.gold}, transparent)`, margin: '32px auto' }} />
        <p style={{ fontFamily: MONO, fontSize: 29, color: C.text, letterSpacing: '0.16em', margin: 0, opacity: interpolate(f, [36, 60], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }) }}>
          一部精确到日、每条可溯源的中国互联网编年史
        </p>
      </div>
    </AbsoluteFill>
  );
};

/* CTA 落版分区内容 */
const CtaSection: React.FC<{ localF: number }> = ({ localF }) => {
  const stamp = interpolate(localF, [0, 26], [1.16, 1], { extrapolateRight: 'clamp', easing: (u) => 1 - Math.pow(1 - u, 3) });
  const t1 = interpolate(localF, [10, 30], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const t2 = interpolate(localF, [24, 44], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const t3 = interpolate(localF, [38, 56], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  return (
    <AbsoluteFill style={{ alignItems: 'center', justifyContent: 'center', background: `radial-gradient(ellipse at center, ${C.bg2} 0%, ${C.bg} 72%)` }}>
      <div style={{ textAlign: 'center' }}>
        <img src={appleIcon} width={168} height={168} style={{ borderRadius: 30, transform: `scale(${stamp})`, boxShadow: '0 20px 80px #000d, 0 0 0 1px #c9a86a55', margin: '0 auto' }} />
        <h1 style={{ fontFamily: SERIF, fontSize: 92, color: C.goldBright, margin: '42px 0 0', letterSpacing: '0.14em', fontWeight: 700, opacity: t1, transform: `translateY(${(1 - t1) * 24}px)` }}>中国互联网编年史</h1>
        <div style={{ fontFamily: MONO, fontSize: 40, color: C.gold, marginTop: 28, letterSpacing: '0.22em', opacity: t2 }}>toolsfox.cn</div>
        <div style={{ fontFamily: MONO, fontSize: 22, color: C.faint, marginTop: 20, letterSpacing: '0.1em', opacity: t3 }}>精确到日 · 每条可溯源 · 开源</div>
      </div>
    </AbsoluteFill>
  );
};

const Journey: React.FC = () => {
  const f = useCurrentFrame();
  const scrollY = scrollYAt(f);
  const localF = f - (DUR - 130);   // CTA 分区内的本地帧（用于落版动画）
  return (
    <AbsoluteFill style={{ background: C.bg }}>
      {/* 虚拟长页：一台摄像机匀速滚过全部板块 */}
      <AbsoluteFill>
        <div style={{ position: 'absolute', inset: 0, transform: `translateY(${-scrollY}px)` }}>
        {SECTIONS.map((s, i) => (
          <div key={i} style={{ position: 'absolute', top: i * SEC_H, left: 0, width: '100%', height: SEC_H }}>
            {s.img ? (
              <Img src={TEX[s.img as keyof typeof TEX]} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
            ) : (
              <CtaSection localF={Math.max(0, localF)} />
            )}
          </div>
        ))}
        </div>
      </AbsoluteFill>
      {/* 全程轻遮罩：保证字幕可读 */}
      <AbsoluteFill style={{ background: `linear-gradient(180deg, #0c0d1055 0%, transparent 18%, transparent 82%, #0c0d1066 100%)` }} />
      <SectionCaption f={f} scrollY={scrollY} />
      <TitleCard f={f} scrollY={scrollY} />
      {/* 结尾收黑 */}
      <AbsoluteFill style={{ background: '#000', opacity: interpolate(f, [DUR - 28, DUR], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }) }} />
      <Audio src={bgm} volume={(fr) => interpolate(fr, [0, 30, DUR - 100, DUR], [0, 0.8, 0.8, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })} />
      {/* 开场从黑淡入 */}
      <AbsoluteFill style={{ background: '#000', opacity: interpolate(f, [0, 14], [1, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }) }} />
    </AbsoluteFill>
  );
};

export const RemotionRoot: React.FC = () => (
  <Composition id="Promo" component={Journey} durationInFrames={DUR} fps={30} width={1920} height={1080} />
);
