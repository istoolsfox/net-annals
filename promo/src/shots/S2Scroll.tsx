import React from 'react';
import { AbsoluteFill, interpolate, useCurrentFrame, Easing } from 'remotion';
import { C, SERIF, MONO, EASE } from '../theme';
import { TEX } from '../textures';

/** S2 长卷：两个时代慢推镜（1972 起点卡 → 2020 当代），交叉淡入衔接，无闪切。
 *  取景贴近内容列（base scale 1.3+），卡片文字可读，页头裁出画外。 */
const PART_A = 95;

const Slice: React.FC<{ img: string; year: string; era: string; from: number; to: number;
  origin: string; capTop?: string }> = ({ img, year, era, from, to, origin, capTop }) => {
  const f = useCurrentFrame();
  const t = interpolate(f, [from, to], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.bezier(...EASE) });
  const scale = 1.3 + t * 0.24;
  const chip = interpolate(f, [from + 6, from + 20], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const cap = capTop ? interpolate(f, [from + 10, from + 26], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }) : 0;
  return (
    <AbsoluteFill>
      <img src={TEX[img]} style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover', transform: `scale(${scale})`, transformOrigin: origin }} />
      <AbsoluteFill style={{ background: `linear-gradient(180deg, #0c0d10f0 0%, #0c0d10bb 24%, transparent 48%, transparent 74%, #0c0d10cc 100%)` }} />
      {capTop ? (
        <div style={{ position: 'absolute', top: 110, left: 0, right: 0, textAlign: 'center', opacity: cap }}>
          <span style={{ display: 'inline-block', background: 'rgba(12,13,16,0.82)', border: '1px solid #c9a86a3d', borderRadius: 12, padding: '16px 40px', fontFamily: SERIF, fontSize: 60, color: C.goldBright, letterSpacing: '0.14em', textShadow: '0 2px 18px #000' }}>{capTop}</span>
        </div>
      ) : null}
      <div style={{ position: 'absolute', left: 84, bottom: 88, opacity: chip, transform: `translateY(${(1 - chip) * 22}px)` }}>
        <div style={{ fontFamily: SERIF, fontSize: 132, color: C.goldBright, lineHeight: 1, textShadow: '0 4px 34px #000d' }}>{year}</div>
        <div style={{ fontFamily: MONO, fontSize: 27, color: C.dim, letterSpacing: '0.3em', marginTop: 12 }}>{era}</div>
      </div>
    </AbsoluteFill>
  );
};

export const S2Scroll: React.FC = () => {
  const f = useCurrentFrame();
  const cross = 24; // 两时代交叉淡入时长
  const aOp = 1 - interpolate(f, [PART_A - cross, PART_A], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const bOp = interpolate(f, [PART_A - cross, PART_A], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  return (
    <AbsoluteFill style={{ background: C.bg }}>
      <AbsoluteFill style={{ opacity: aOp }}>
        <Slice img="tl-1972" year="1972" era="前史与萌发" from={4} to={PART_A} origin="46% 52%" capTop="大事，小事，转折事" />
      </AbsoluteFill>
      <AbsoluteFill style={{ opacity: bOp }}>
        <Slice img="tl-2020" year="2020" era="疫情与智能" from={PART_A} to={190} origin="56% 34%" capTop="都钉在它自己的那一天上" />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
