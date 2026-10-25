import React from 'react';
import { AbsoluteFill, interpolate, useCurrentFrame, Easing } from 'remotion';
import { C, SERIF, MONO } from '../theme'
import { TEX, appleIcon } from '../textures';

/** S5 历史上的今天：背景列表视差 + 抽屉从右滑入 */
export const S5Today: React.FC = () => {
  const f = useCurrentFrame();
  const slide = interpolate(f, [4, 34], [100, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.bezier(0.33, 0, 0.15, 1) });
  const bgShift = interpolate(f, [0, 90], [0, -40], { extrapolateRight: 'clamp' });
  const cap = interpolate(f, [26, 40], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  return (
    <AbsoluteFill style={{ background: C.bg }}>
      <img src={TEX['today-list']} style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover', transform: `translateX(${bgShift}px)`, filter: 'brightness(0.55)' }} />
      <div style={{ position: 'absolute', inset: 0, display: 'flex', justifyContent: 'flex-end' }}>
        <div style={{ width: '62%', height: '100%', transform: `translateX(${slide}%)`, boxShadow: '-30px 0 80px #000c' }}>
          <img src={TEX['today-drawer']} style={{ width: '100%', height: '100%', objectFit: 'cover', objectPosition: 'right center' }} />
        </div>
      </div>
      <div style={{ position: 'absolute', left: 96, bottom: 110, opacity: cap, transform: `translateY(${(1 - cap) * 20}px)` }}>
        <div style={{ fontFamily: SERIF, fontSize: 84, color: C.goldBright, fontWeight: 700, textShadow: '0 4px 30px #000c' }}>历史上的今天</div>
        <div style={{ fontFamily: SERIF, fontSize: 36, color: C.dim, marginTop: 12, letterSpacing: '0.1em' }}>翻开任何一天，读那一年发生的事</div>
      </div>
      <AbsoluteFill style={{ background: C.bg, opacity: interpolate(f, [0, 8], [1, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }) + interpolate(f, [82, 90], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }) }} />
    </AbsoluteFill>
  );
};
