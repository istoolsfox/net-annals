import React from 'react';
import { Composition, AbsoluteFill, Sequence, Audio, interpolate, useCurrentFrame, Easing, Img } from 'remotion';
import { C, SERIF, MONO, EASE } from './theme';
import { TEX, appleIcon, bgm } from './textures';
import { DigitRoll } from './lib/DigitRoll';
import { Journey } from './Promo';

/** 多镜头版：17 个镜头硬切衔接（切点即节拍），每镜内部自带动效，
 *  不做任何叠化/黑场——帧帧完整画面，无闪烁可能。 */

type Cap = { tag: string; title: string };
type Shot =
  | { kind: 'title'; dur: number }
  | { kind: 'tex'; dur: number; img: string; motion: 'zoomin' | 'zoomout' | 'pandown'; origin?: string; cap?: Cap }
  | { kind: 'stats'; dur: number; rows: Array<{ v: string; lab: string }> }
  | { kind: 'cta'; dur: number };

const SHOTS: Shot[] = [
  { kind: 'title', dur: 60 },
  { kind: 'tex', dur: 45, img: 'hero', motion: 'zoomin', cap: { tag: '官网', title: '中国互联网编年史' } },
  { kind: 'tex', dur: 55, img: 'tl-1972', motion: 'zoomin', origin: '46% 52%', cap: { tag: '编年史 · 1972', title: '大事，小事，转折事' } },
  { kind: 'tex', dur: 40, img: 'tl-1994', motion: 'pandown', cap: { tag: '编年史 · 1994', title: '拨号时代' } },
  { kind: 'tex', dur: 40, img: 'tl-2003', motion: 'zoomin', cap: { tag: '编年史 · 2000', title: '门户与泡沫' } },
  { kind: 'tex', dur: 40, img: 'tl-2010', motion: 'pandown', cap: { tag: '编年史 · 2010', title: '移动互联网' } },
  { kind: 'tex', dur: 40, img: 'tl-2020', motion: 'zoomin', cap: { tag: '编年史 · 2020', title: '疫情与智能' } },
  { kind: 'stats', dur: 50, rows: [{ v: '8,562', lab: '条事件 · 精确到日' }, { v: '6,883', lab: '条双源实证' }] },
  { kind: 'stats', dur: 40, rows: [{ v: '841', lab: '个时代转折点' }, { v: '55', lab: '年 · 从未断更的长卷' }] },
  { kind: 'tex', dur: 45, img: 'persons-top', motion: 'zoomin', cap: { tag: '人物志', title: '一条条人生长卷' } },
  { kind: 'tex', dur: 45, img: 'entities-top', motion: 'zoomin', cap: { tag: '世家志', title: '兴衰成对，为每一家立传' } },
  { kind: 'tex', dur: 45, img: 'works-top', motion: 'zoomin', cap: { tag: '作品志', title: '精神地标' } },
  { kind: 'tex', dur: 40, img: 'today-list', motion: 'zoomin', cap: { tag: '历史上的今天', title: '翻开任何一天' } },
  { kind: 'tex', dur: 45, img: 'today-drawer', motion: 'zoomin', cap: { tag: '抽屉详情', title: '点开即读全文' } },
  { kind: 'tex', dur: 50, img: 'card-open', motion: 'zoomin', origin: '50% 74%', cap: { tag: '溯源', title: '每一条，都可溯源' } },
  { kind: 'tex', dur: 45, img: 'github', motion: 'zoomout', cap: { tag: '开源', title: '整部史，全部可查' } },
  { kind: 'cta', dur: 90 },
];

export const MULTI_TOTAL = SHOTS.reduce((a, s) => a + s.dur, 0);
const easeOut = Easing.bezier(0.33, 0, 0.15, 1);

const Caption: React.FC<{ cap: Cap; lf: number }> = ({ cap, lf }) => {
  const op = interpolate(lf, [4, 14], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  return (
    <div style={{ position: 'absolute', left: 96, bottom: 116, opacity: op, transform: `translateY(${(1 - op) * 18}px)` }}>
      <div style={{ fontFamily: MONO, fontSize: 24, color: C.gold, letterSpacing: '0.34em', marginBottom: 12 }}>{cap.tag}</div>
      <div style={{ display: 'inline-block', background: 'rgba(12,13,16,0.78)', border: '1px solid #c9a86a3d', borderRadius: 12, padding: '14px 34px', fontFamily: SERIF, fontSize: 74, color: C.goldBright, fontWeight: 700, textShadow: '0 4px 26px #000c' }}>{cap.title}</div>
    </div>
  );
};

const TexShot: React.FC<{ s: Extract<Shot, { kind: 'tex' }> }> = ({ s }) => {
  const f = useCurrentFrame();
  const t = interpolate(f, [0, s.dur], [0, 1], { extrapolateRight: 'clamp', easing: easeOut });
  const transform =
    s.motion === 'zoomin' ? `scale(${1.02 + t * 0.07})` :
    s.motion === 'zoomout' ? `scale(${1.1 - t * 0.08})` :
    `scale(1.06) translateY(${interpolate(f, [0, s.dur], [24, -24], { extrapolateRight: 'clamp', easing: easeOut })}px)`;
  return (
    <AbsoluteFill>
      <Img src={TEX[s.img as keyof typeof TEX]} style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover', transform, transformOrigin: s.origin ?? 'center' }} />
      <AbsoluteFill style={{ background: 'linear-gradient(180deg, #0c0d1066 0%, transparent 30%, transparent 70%, #0c0d10aa 100%)' }} />
      {s.cap ? <Caption cap={s.cap} lf={f} /> : null}
    </AbsoluteFill>
  );
};

const StatsShot: React.FC<{ rows: Array<{ v: string; lab: string }> }> = ({ rows }) => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{ justifyContent: 'center', padding: '0 220px' }}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 44 }}>
        {rows.map((r, i) => {
          const d = 4 + i * 16;
          const op = interpolate(f, [d, d + 14], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
          const tx = interpolate(f, [d, d + 14], [-56, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
          return (
            <div key={r.lab} style={{ display: 'flex', alignItems: 'baseline', gap: 30, opacity: op, transform: `translateX(${tx}px)` }}>
              <span style={{ fontFamily: MONO, fontWeight: 700, fontSize: 116, lineHeight: 1.05, color: C.goldBright }}>
                <DigitRoll value={r.v} delay={d + 2} fontSize={116} color={C.goldBright} stagger={3} roll={18} />
              </span>
              <span style={{ fontFamily: SERIF, fontSize: 42, color: C.text, letterSpacing: '0.12em' }}>{r.lab}</span>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

const TitleShot: React.FC = () => {
  const f = useCurrentFrame();
  const op = interpolate(f, [5, 34], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const ls = `${interpolate(f, [5, 44], [0.26, 0.05], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })}em`;
  const ty = interpolate(f, [5, 34], [30, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: easeOut });
  const sub = interpolate(f, [28, 48], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
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

const CtaShot: React.FC = () => {
  const f = useCurrentFrame();
  const stamp = interpolate(f, [4, 30], [1.16, 1], { extrapolateRight: 'clamp', easing: (u) => 1 - Math.pow(1 - u, 3) });
  const t1 = interpolate(f, [10, 28], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const t2 = interpolate(f, [22, 40], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const t3 = interpolate(f, [36, 52], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
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

export const MultiShot: React.FC = () => {
  let cursor = 0;
  return (
    <AbsoluteFill style={{ background: C.bg }}>
      {SHOTS.map((s, i) => {
        const from = cursor;
        cursor += s.dur;
        return (
          <Sequence key={i} from={from} durationInFrames={s.dur} name={`m${i + 1}-${s.kind}`}>
            {s.kind === 'title' ? <TitleShot /> :
             s.kind === 'stats' ? <StatsShot rows={s.rows} /> :
             s.kind === 'cta' ? <CtaShot /> :
             <TexShot s={s} />}
          </Sequence>
        );
      })}
      <Audio src={bgm} volume={(fr) => interpolate(fr, [0, 24, MULTI_TOTAL - 90, MULTI_TOTAL], [0, 0.8, 0.8, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })} />
    </AbsoluteFill>
  );
};

export const RemotionRootMulti: React.FC = () => (
  <Composition id="PromoMulti" component={MultiShot} durationInFrames={MULTI_TOTAL} fps={30} width={1920} height={1080} />
);
