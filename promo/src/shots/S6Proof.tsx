import React from 'react';
import { AbsoluteFill, interpolate, useCurrentFrame, Easing } from 'remotion';
import { C, SERIF, MONO, EASE } from '../theme';
import { TEX } from '../textures';

const P2 = 65; // 第二段（GitHub）起点，段间经黑场

/** S6 可溯源 + 开源：两段式经黑场过渡 */
export const S6Proof: React.FC = () => {
  const f = useCurrentFrame();
  const aOp = interpolate(f, [0, 10, P2 - 10, P2], [0, 1, 1, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const aZoom = interpolate(f, [0, P2], [1.0, 1.14], { extrapolateRight: 'clamp', easing: Easing.bezier(...EASE) });
  const bOp = interpolate(f, [P2, P2 + 10], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const bZoom = interpolate(f, [P2, 130], [1.08, 1.0], { extrapolateRight: 'clamp', easing: Easing.bezier(...EASE) });
  const capA = interpolate(f, [6, 20], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }) * interpolate(f, [P2 - 22, P2 - 8], [1, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const capB = interpolate(f, [P2 + 6, P2 + 20], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ opacity: aOp }}>
        <img src={TEX['card-open']} style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover', transform: `scale(${aZoom})`, transformOrigin: '50% 74%' }} />
        <AbsoluteFill style={{ background: `linear-gradient(180deg, #0c0d10aa 0%, transparent 45%)` }} />
        <div style={{ position: 'absolute', left: 96, top: 110, opacity: capA }}>
          <div style={{ fontFamily: SERIF, fontSize: 88, color: C.goldBright, fontWeight: 700, textShadow: '0 4px 30px #000c' }}>每一条，都可溯源</div>
          <div style={{ fontFamily: MONO, fontSize: 26, color: C.dim, marginTop: 14, letterSpacing: '0.16em' }}>日期有据 · 来源可溯 · 存疑注明</div>
        </div>
      </AbsoluteFill>
      <AbsoluteFill style={{ opacity: bOp }}>
        <img src={TEX.github} style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover', transform: `scale(${bZoom})`, filter: 'brightness(0.9)' }} />
        <AbsoluteFill style={{ background: `linear-gradient(180deg, #0c0d10bb 0%, transparent 50%)` }} />
        <div style={{ position: 'absolute', left: 96, top: 110, opacity: capB }}>
          <div style={{ fontFamily: SERIF, fontSize: 88, color: C.goldBright, fontWeight: 700, textShadow: '0 4px 30px #000c' }}>整部史，开源可查</div>
          <div style={{ fontFamily: MONO, fontSize: 30, color: C.gold, marginTop: 16, letterSpacing: '0.06em' }}>github.com/istoolsfox/net-annals</div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
