import React from 'react';
import { AbsoluteFill, interpolate, useCurrentFrame, Easing } from 'remotion';
import { C, SERIF, MONO } from '../theme'
import { TEX, appleIcon } from '../textures';

const VIEWS = [
  { img: 'persons-top', tag: 'BIOGRAPHY', name: '人物志', sub: '一条条人生长卷' },
  { img: 'entities-top', tag: 'HEREDITARY HOUSES', name: '世家志', sub: '兴衰成对，为每一家立传' },
  { img: 'works-top', tag: 'WORKS', name: '作品志', sub: '陪伴大众精神生活的创作物' },
];
const EACH = 40;

/** S4 四视图：三个板块推近硬切 + 板块金字 */
export const S4Views: React.FC = () => {
  const f = useCurrentFrame();
  const i = Math.min(VIEWS.length - 1, Math.floor(f / EACH));
  const lf = f - i * EACH;
  const v = VIEWS[i];
  const zoom = interpolate(lf, [0, EACH], [1.0, 1.07], { extrapolateRight: 'clamp' });
  const cap = interpolate(lf, [3, 15], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const flash = interpolate(lf, [0, 3], [0.18, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  return (
    <AbsoluteFill style={{ background: C.bg }}>
      <img src={TEX[v.img]} style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover', transform: `scale(${zoom})` }} />
      <AbsoluteFill style={{ background: `linear-gradient(90deg, #0c0d10dd 0%, transparent 55%)` }} />
      <div style={{ position: 'absolute', left: 96, bottom: 120, opacity: cap, transform: `translateY(${(1 - cap) * 20}px)` }}>
        <div style={{ fontFamily: MONO, fontSize: 24, color: C.gold, letterSpacing: '0.34em', marginBottom: 14 }}>{v.tag}</div>
        <div style={{ fontFamily: SERIF, fontSize: 96, color: C.goldBright, fontWeight: 700, textShadow: '0 4px 30px #000c' }}>{v.name}</div>
        <div style={{ fontFamily: SERIF, fontSize: 38, color: C.dim, marginTop: 12, letterSpacing: '0.1em' }}>{v.sub}</div>
      </div>
      <AbsoluteFill style={{ background: '#fff', opacity: flash }} />
      <AbsoluteFill style={{ background: C.bg, opacity: interpolate(f, [VIEWS.length * EACH - FADE_OUT, VIEWS.length * EACH], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }) }} />
    </AbsoluteFill>
  );
};
const FADE_OUT = 8;
