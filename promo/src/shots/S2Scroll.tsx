import React from 'react';
import { AbsoluteFill, interpolate, useCurrentFrame, Easing } from 'remotion';
import { C, SERIF, MONO, FADE } from '../theme'
import { TEX, appleIcon } from '../textures';

const SLICES = [
  { img: 'tl-1972', year: '1972', era: '前史与萌发' },
  { img: 'tl-1994', year: '1994', era: '拨号时代' },
  { img: 'tl-2003', year: '2000', era: '门户与泡沫' },
  { img: 'tl-2010', year: '2010', era: '移动互联网' },
  { img: 'tl-2020', year: '2020', era: '疫情与智能' },
];
const SLICE = 36; // 每片 1.2s

/** S2 长卷滚镜：五个真实切片硬切 + 每片内向下漂移 + 年份角标 */
export const S2Scroll: React.FC = () => {
  const f = useCurrentFrame();
  const i = Math.min(SLICES.length - 1, Math.floor(f / SLICE));
  const lf = f - i * SLICE;
  const s = SLICES[i];
  const drift = interpolate(lf, [0, SLICE], [0, -46], { extrapolateRight: 'clamp', easing: Easing.bezier(0.33, 0, 0.15, 1) });
  const zoom = interpolate(lf, [0, SLICE], [1.03, 1.09], { extrapolateRight: 'clamp' });
  const chip = interpolate(lf, [2, 14], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const flash = interpolate(lf, [0, 3], [0.22, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  return (
    <AbsoluteFill style={{ background: C.bg }}>
      <img src={TEX[s.img]} style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover', transform: `scale(${zoom}) translateY(${drift}px)` }} />
      <AbsoluteFill style={{ background: `linear-gradient(180deg, #0c0d1066 0%, transparent 30%, transparent 70%, #0c0d10aa 100%)` }} />
      <div style={{ position: 'absolute', left: 84, bottom: 96, opacity: chip, transform: `translateY(${(1 - chip) * 24}px)` }}>
        <div style={{ fontFamily: SERIF, fontSize: 120, color: C.goldBright, lineHeight: 1, textShadow: '0 4px 30px #000c' }}>{s.year}</div>
        <div style={{ fontFamily: MONO, fontSize: 26, color: C.dim, letterSpacing: '0.3em', marginTop: 12 }}>{s.era}</div>
      </div>
      <AbsoluteFill style={{ background: '#fff', opacity: flash }} />
      <AbsoluteFill style={{ background: C.bg, opacity: interpolate(f, [SLICES.length * SLICE - FADE, SLICES.length * SLICE], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }) }} />
    </AbsoluteFill>
  );
};
