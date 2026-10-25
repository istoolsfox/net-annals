import React from 'react';
import { AbsoluteFill, interpolate, useCurrentFrame, spring, useVideoConfig } from 'remotion';
import { C, SERIF, MONO } from '../theme'
import { TEX, appleIcon } from '../textures';

/** S7 收尾：编章落定 + 站名 + 地址，长 hold */
export const S7CTA: React.FC = () => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const stamp = spring({ frame: f - 4, fps, config: { damping: 200, mass: 1.2 }, durationInFrames: 34 });
  const scale = interpolate(stamp, [0, 1], [1.18, 1]);
  const rot = interpolate(stamp, [0, 1], [-4, 0]);
  const t1 = interpolate(f, [22, 44], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const t2 = interpolate(f, [42, 62], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const t3 = interpolate(f, [58, 76], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const breathe = 1 + 0.01 * Math.sin(f / 24);
  return (
    <AbsoluteFill style={{ background: `radial-gradient(ellipse at center, ${C.bg2} 0%, ${C.bg} 70%)`, alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ textAlign: 'center', transform: `scale(${breathe})` }}>
        <img src={appleIcon} width={170} height={170} style={{ borderRadius: 30, transform: `scale(${scale}) rotate(${rot}deg)`, boxShadow: '0 20px 80px #000d, 0 0 0 1px #c9a86a55', margin: '0 auto' }} />
        <h1 style={{ fontFamily: SERIF, fontSize: 92, color: C.goldBright, margin: '44px 0 0', letterSpacing: '0.14em', opacity: t1, transform: `translateY(${(1 - t1) * 26}px)`, fontWeight: 700 }}>
          中国互联网编年史
        </h1>
        <div style={{ fontFamily: MONO, fontSize: 40, color: C.gold, marginTop: 30, letterSpacing: '0.22em', opacity: t2 }}>
          toolsfox.cn
        </div>
        <div style={{ fontFamily: MONO, fontSize: 22, color: C.faint, marginTop: 22, letterSpacing: '0.1em', opacity: t3 }}>
          精确到日 · 每条可溯源 · 开源
        </div>
      </div>
      <AbsoluteFill style={{ background: C.bg, opacity: interpolate(f, [0, 8], [1, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }) }} />
    </AbsoluteFill>
  );
};
