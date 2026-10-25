import React from 'react';
import { AbsoluteFill, interpolate, useCurrentFrame, Easing } from 'remotion';
import { C, SERIF, EASE } from '../theme';
import { TEX } from '../textures';

const P2 = 58; // 第二段（抽屉特写）起点

/** S5 历史上的今天：两段式经黑场过渡（列表 → 抽屉特写），无复写无鬼影 */
export const S5Today: React.FC = () => {
  const f = useCurrentFrame();
  const listOp = interpolate(f, [0, 10, P2 - 10, P2], [0, 1, 1, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const drawerOp = interpolate(f, [P2, P2 + 10], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const drawerZoom = interpolate(f, [P2, 115], [1.0, 1.08], { extrapolateRight: 'clamp', easing: Easing.bezier(...EASE) });
  const cap = interpolate(f, [14, 28], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ opacity: listOp }}>
        <img src={TEX['today-list']} style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover' }} />
      </AbsoluteFill>
      <AbsoluteFill style={{ opacity: drawerOp }}>
        <img src={TEX['today-drawer']} style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover', transform: `scale(${drawerZoom})`, objectPosition: 'right center' }} />
      </AbsoluteFill>
      <div style={{ position: 'absolute', left: 96, bottom: 110, opacity: cap, transform: `translateY(${(1 - cap) * 20}px)` }}>
        <div style={{ fontFamily: SERIF, fontSize: 84, color: C.goldBright, fontWeight: 700, textShadow: '0 4px 30px #000c' }}>历史上的今天</div>
        <div style={{ fontFamily: SERIF, fontSize: 36, color: C.text, marginTop: 12, letterSpacing: '0.1em' }}>翻开任何一天，读那一年发生的事</div>
      </div>
    </AbsoluteFill>
  );
};
