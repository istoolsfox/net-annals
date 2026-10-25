import React from 'react';
import { AbsoluteFill, interpolate, useCurrentFrame, Easing } from 'remotion';
import { C, SERIF, MONO } from '../theme'
import { TEX, appleIcon } from '../textures';

/** S6 可溯源 + 开源：卡片特写推近聚焦来源区 → GitHub 仓库 */
export const S6Proof: React.FC = () => {
  const f = useCurrentFrame();
  const partB = f >= 45;
  if (!partB) {
    const zoom = interpolate(f, [0, 45], [1.0, 1.16], { extrapolateRight: 'clamp', easing: Easing.bezier(0.33, 0, 0.15, 1) });
    const cap = interpolate(f, [5, 18], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
    return (
      <AbsoluteFill>
        <img src={TEX['card-open']} style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover', transform: `scale(${zoom})`, transformOrigin: '50% 74%' }} />
        <AbsoluteFill style={{ background: `linear-gradient(180deg, #0c0d10aa 0%, transparent 45%)` }} />
        <div style={{ position: 'absolute', left: 96, top: 110, opacity: cap }}>
          <div style={{ fontFamily: SERIF, fontSize: 88, color: C.goldBright, fontWeight: 700, textShadow: '0 4px 30px #000c' }}>每一条，都可溯源</div>
          <div style={{ fontFamily: MONO, fontSize: 26, color: C.dim, marginTop: 14, letterSpacing: '0.16em' }}>日期有据 · 来源可溯 · 存疑注明</div>
        </div>
        <AbsoluteFill style={{ background: C.bg, opacity: interpolate(f, [37, 45], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }) }} />
      </AbsoluteFill>
    );
  }
  const lf = f - 45;
  const zoom = interpolate(lf, [0, 45], [1.08, 1.0], { extrapolateRight: 'clamp' });
  const cap = interpolate(lf, [4, 16], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  return (
    <AbsoluteFill>
      <img src={TEX['github']} style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover', transform: `scale(${zoom})`, filter: 'brightness(0.9)' }} />
      <AbsoluteFill style={{ background: `linear-gradient(180deg, #0c0d10bb 0%, transparent 50%)` }} />
      <div style={{ position: 'absolute', left: 96, top: 110, opacity: cap }}>
        <div style={{ fontFamily: SERIF, fontSize: 88, color: C.goldBright, fontWeight: 700, textShadow: '0 4px 30px #000c' }}>整部史，开源可查</div>
        <div style={{ fontFamily: MONO, fontSize: 30, color: C.gold, marginTop: 16, letterSpacing: '0.06em' }}>github.com/istoolsfox/net-annals</div>
      </div>
      <AbsoluteFill style={{ background: C.bg, opacity: interpolate(lf, [37, 45], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }) }} />
    </AbsoluteFill>
  );
};
