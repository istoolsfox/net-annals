import React from 'react';
import { AbsoluteFill, interpolate, useCurrentFrame, Easing } from 'remotion';
import { C, SERIF, MONO, EASE } from '../theme';
import { TEX } from '../textures';

/** S2 长卷：两个时代各占一段，段间经黑场章节过渡（不再文字叠文字） */
const EACH = 100;
const SLICES = [
  { img: 'tl-1972', year: '1972', era: '前史与萌发', origin: '46% 52%', cap: '大事，小事，转折事' },
  { img: 'tl-2020', year: '2020', era: '疫情与智能', origin: '56% 34%', cap: '都钉在它自己的那一天上' },
];

const Slice: React.FC<{ s: typeof SLICES[0]; f: number; dur: number }> = ({ s, f, dur }) => {
  const t = interpolate(f, [0, dur], [0, 1], { extrapolateRight: 'clamp', easing: Easing.bezier(...EASE) });
  const scale = 1.3 + t * 0.22;
  const chip = interpolate(f, [12, 26], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const cap = interpolate(f, [16, 30], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  return (
    <AbsoluteFill>
      <img src={TEX[s.img]} style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover', transform: `scale(${scale})`, transformOrigin: s.origin }} />
      <AbsoluteFill style={{ background: `linear-gradient(180deg, #0c0d10d9 0%, #0c0d1099 22%, transparent 46%, transparent 74%, #0c0d10cc 100%)` }} />
      {cap ? (
        <div style={{ position: 'absolute', top: 104, left: 0, right: 0, textAlign: 'center', opacity: cap }}>
          <span style={{ display: 'inline-block', background: 'rgba(12,13,16,0.82)', border: '1px solid #c9a86a3d', borderRadius: 12, padding: '16px 40px', fontFamily: SERIF, fontSize: 58, color: C.goldBright, letterSpacing: '0.14em' }}>{s.cap}</span>
        </div>
      ) : null}
      <div style={{ position: 'absolute', left: 84, bottom: 88, opacity: chip, transform: `translateY(${(1 - chip) * 22}px)` }}>
        <div style={{ fontFamily: SERIF, fontSize: 132, color: C.goldBright, lineHeight: 1, textShadow: '0 4px 34px #000d' }}>{s.year}</div>
        <div style={{ fontFamily: MONO, fontSize: 27, color: C.dim, letterSpacing: '0.3em', marginTop: 12 }}>{s.era}</div>
      </div>
    </AbsoluteFill>
  );
};

export const S2Scroll: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill>
      {SLICES.map((s, i) => {
        const start = i * EACH;
        const lf = f - start;
        if (lf < 0 || lf > EACH) return null;
        const op = interpolate(lf, [0, 10, EACH - 10, EACH], [0, 1, 1, 0], {
          extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
        });
        return (
          <AbsoluteFill key={s.year} style={{ opacity: op }}>
            <Slice s={s} f={lf} dur={EACH} />
          </AbsoluteFill>
        );
      })}
    </AbsoluteFill>
  );
};
