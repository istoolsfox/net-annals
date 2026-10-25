import React from 'react';
import { AbsoluteFill, Sequence, Audio, interpolate, useCurrentFrame, Img } from 'remotion';
import { C, SERIF, MONO } from './theme';
import { TEX, appleIcon, bgm } from './textures';
import { DigitRoll } from './lib/DigitRoll';

/** 静态成片版：截图全程静止展示（零运动=零闪烁源），
 *  动画只发生在字幕与数字上；转场 = 20f 缓慢叠化（静对静，无频闪）。 */

const XFADE = 20;

type Slide =
  | { kind: 'title'; dur: number }
  | { kind: 'img'; dur: number; img: string; tag?: string; title?: string }
  | { kind: 'stats'; dur: number; rows: Array<{ v: string; lab: string }> }
  | { kind: 'cta'; dur: number };

const SLIDES: Slide[] = [
  { kind: 'title', dur: 70 },
  { kind: 'img', dur: 75, img: 'hero', tag: '官网首页', title: 'toolsfox.cn · 中国互联网编年史' },
  { kind: 'img', dur: 80, img: 'tl-1972', tag: '编年史 · 1972', title: '大事，小事，转折事' },
  { kind: 'img', dur: 70, img: 'tl-2020', tag: '编年史 · 2020', title: '疫情与智能' },
  { kind: 'stats', dur: 65, rows: [{ v: '8,562', lab: '条事件 · 精确到日' }, { v: '6,883', lab: '条双源实证' }] },
  { kind: 'stats', dur: 55, rows: [{ v: '841', lab: '个时代转折点' }, { v: '55', lab: '年 · 从未断更的长卷' }] },
  { kind: 'img', dur: 70, img: 'persons-top', tag: '人物志', title: '一条条人生长卷' },
  { kind: 'img', dur: 70, img: 'entities-top', tag: '世家志', title: '兴衰成对，为每一家立传' },
  { kind: 'img', dur: 65, img: 'works-top', tag: '作品志', title: '精神地标' },
  { kind: 'img', dur: 70, img: 'today-drawer', tag: '历史上的今天', title: '翻开任何一天' },
  { kind: 'img', dur: 70, img: 'card-open', tag: '溯源', title: '每一条，都可溯源' },
  { kind: 'img', dur: 60, img: 'github', tag: '开源', title: '整部史，全部可查' },
  { kind: 'cta', dur: 100 },
];

export const STATIC_TOTAL = SLIDES.reduce((a, s) => a + s.dur, 0) - (SLIDES.length - 1) * XFADE;

const Caption: React.FC<{ tag?: string; title: string; lf: number }> = ({ tag, title, lf }) => {
  const op = interpolate(lf, [10, 26], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  return (
    <div style={{ position: 'absolute', left: 96, bottom: 116, opacity: op, transform: `translateY(${(1 - op) * 18}px)` }}>
      {tag ? <div style={{ fontFamily: MONO, fontSize: 24, color: C.gold, letterSpacing: '0.34em', marginBottom: 12 }}>{tag}</div> : null}
      <div style={{ display: 'inline-block', background: 'rgba(12,13,16,0.78)', border: '1px solid #c9a86a3d', borderRadius: 12, padding: '14px 34px', fontFamily: SERIF, fontSize: 72, color: C.goldBright, fontWeight: 700, textShadow: '0 4px 26px #000c' }}>{title}</div>
    </div>
  );
};

const StatsSlide: React.FC<{ rows: Array<{ v: string; lab: string }>; f: number }> = ({ rows, f }) => (
  <AbsoluteFill style={{ justifyContent: 'center', padding: '0 220px' }}>
    <div style={{ display: 'flex', flexDirection: 'column', gap: 46 }}>
      {rows.map((r, i) => {
        const d = 8 + i * 20;
        const op = interpolate(f, [d, d + 16], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
        const tx = interpolate(f, [d, d + 16], [-56, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
        return (
          <div key={r.lab} style={{ display: 'flex', alignItems: 'baseline', gap: 30, opacity: op, transform: `translateX(${tx}px)` }}>
            <span style={{ fontFamily: MONO, fontWeight: 700, fontSize: 118, lineHeight: 1.05, color: C.goldBright }}>
              <DigitRoll value={r.v} delay={d + 2} fontSize={118} color={C.goldBright} stagger={4} roll={24} />
            </span>
            <span style={{ fontFamily: SERIF, fontSize: 42, color: C.text, letterSpacing: '0.12em' }}>{r.lab}</span>
          </div>
        );
      })}
    </div>
  </AbsoluteFill>
);

const TitleSlide: React.FC<{ f: number }> = ({ f }) => {
  const op = interpolate(f, [6, 36], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const ls = `${interpolate(f, [6, 46], [0.26, 0.05], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })}em`;
  const ty = interpolate(f, [6, 36], [28, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const sub = interpolate(f, [30, 50], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  return (
    <AbsoluteFill style={{ background: C.bg, alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ textAlign: 'center', opacity: op, transform: `translateY(${ty}px)` }}>
        <h1 style={{ fontFamily: SERIF, fontSize: 108, color: C.goldBright, letterSpacing: ls, margin: 0, fontWeight: 700 }}>四十年，钉在日期上</h1>
        <div style={{ width: 520, height: 1, background: `linear-gradient(90deg, transparent, ${C.gold}, transparent)`, margin: '32px auto' }} />
        <p style={{ fontFamily: MONO, fontSize: 29, color: C.dim, letterSpacing: '0.16em', margin: 0, opacity: sub }}>一部精确到日、每条可溯源的中国互联网编年史</p>
      </div>
    </AbsoluteFill>
  );
};

const CtaSlide: React.FC<{ f: number }> = ({ f }) => {
  const stamp = interpolate(f, [6, 34], [1.16, 1], { extrapolateRight: 'clamp', easing: (u) => 1 - Math.pow(1 - u, 3) });
  const t1 = interpolate(f, [12, 32], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const t2 = interpolate(f, [26, 46], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const t3 = interpolate(f, [40, 58], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  return (
    <AbsoluteFill style={{ background: `radial-gradient(ellipse at center, ${C.bg2} 0%, ${C.bg} 72%)`, alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ textAlign: 'center' }}>
        <Img src={appleIcon} width={168} height={168} style={{ borderRadius: 30, transform: `scale(${stamp})`, boxShadow: '0 20px 80px #000d, 0 0 0 1px #c9a86a55', margin: '0 auto' }} />
        <h1 style={{ fontFamily: SERIF, fontSize: 92, color: C.goldBright, margin: '42px 0 0', letterSpacing: '0.14em', fontWeight: 700, opacity: t1, transform: `translateY(${(1 - t1) * 24}px)` }}>中国互联网编年史</h1>
        <div style={{ fontFamily: MONO, fontSize: 40, color: C.gold, marginTop: 28, letterSpacing: '0.22em', opacity: t2 }}>toolsfox.cn</div>
        <div style={{ fontFamily: MONO, fontSize: 22, color: C.faint, marginTop: 20, letterSpacing: '0.1em', opacity: t3 }}>精确到日 · 每条可溯源 · 开源</div>
      </div>
    </AbsoluteFill>
  );
};

/** 渲染：所有 slide 叠放，后一张在前一张尾段 XFADE 内缓缓叠入（静对静叠化） */
export const StaticFilm: React.FC = () => {
  let start = 0;
  const laid = SLIDES.map((s) => {
    const from = start;
    start += s.dur - XFADE;
    return { ...s, from };
  });
  const f = useCurrentFrame();
  const endFade = interpolate(f, [STATIC_TOTAL - 25, STATIC_TOTAL], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  return (
    <AbsoluteFill style={{ background: '#000' }}>
      {laid.map((s, i) => {
        const lf = f - s.from;
        if (lf < 0) return null;
        // 最后一张不淡出（由全局收黑负责）；其余在尾段 XFADE 渐出交给下一张
        const isLast = i === laid.length - 1;
        const own = isLast
          ? 1
          : interpolate(lf, [s.dur - XFADE, s.dur], [1, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
        const enter = interpolate(lf, [0, XFADE], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
        const op = Math.min(enter, own);
        return (
          <Sequence key={i} from={s.from} durationInFrames={s.dur + XFADE}>
            <AbsoluteFill style={{ opacity: op }}>
              {s.kind === 'title' ? <TitleSlide f={lf} /> :
               s.kind === 'stats' ? <StatsSlide rows={s.rows} f={lf} /> :
               s.kind === 'cta' ? <CtaSlide f={lf} /> :
               <AbsoluteFill>
                 <Img src={TEX[s.img as keyof typeof TEX]} style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover' }} />
                 <AbsoluteFill style={{ background: 'linear-gradient(180deg, #0c0d1055 0%, transparent 26%, transparent 74%, #0c0d1099 100%)' }} />
                 {s.tag ? <Caption tag={s.tag} title={s.title || ''} lf={lf} /> : null}
               </AbsoluteFill>}
            </AbsoluteFill>
          </Sequence>
        );
      })}
      <AbsoluteFill style={{ background: '#000', opacity: endFade }} />
      <Audio src={bgm} volume={(fr) => interpolate(fr, [0, 30, STATIC_TOTAL - 100, STATIC_TOTAL], [0, 0.8, 0.8, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })} />
    </AbsoluteFill>
  );
};

export const RemotionRootStatic: React.FC = () => (
  <Composition id="PromoStatic" component={StaticFilm} durationInFrames={STATIC_TOTAL} fps={30} width={1920} height={1080} />
);
