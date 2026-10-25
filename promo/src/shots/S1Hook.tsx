import React from 'react';
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig, Easing } from 'remotion';
import { C, SERIF, MONO, EASE, FADE } from '../theme'
import { TEX, appleIcon } from '../textures';

/** S1 冷开场：hero 暗化垫底 + 金色衬线主张 + 细线展开 */
export const S1Hook: React.FC = () => {
  const f = useCurrentFrame();
  const { width } = useVideoConfig();
  const tIn = interpolate(f, [6, 42], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.bezier(...EASE) });
  const lsNum = interpolate(f, [6, 60], [0.28, 0.05], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.bezier(...EASE) });
  const ls = `${lsNum}em`;
  const ty = interpolate(f, [6, 42], [34, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.bezier(...EASE) });
  const rule = interpolate(f, [24, 58], [0, 520], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.bezier(...EASE) });
  const sub = interpolate(f, [40, 66], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const breathe = 1 + 0.012 * Math.sin(f / 26);
  return (
    <AbsoluteFill style={{ background: C.bg }}>
      <img src={TEX['hero']} style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover', filter: `brightness(${0.22 + 0.06 * tIn}) saturate(0.85)` }} />
      <AbsoluteFill style={{ background: `radial-gradient(ellipse at center, transparent 30%, ${C.bg}cc 100%)` }} />
      <AbsoluteFill style={{ alignItems: 'center', justifyContent: 'center', transform: `scale(${breathe})` }}>
        <div style={{ textAlign: 'center', opacity: tIn, transform: `translateY(${ty}px)` }}>
          <h1 style={{ fontFamily: SERIF, fontSize: 108, color: C.goldBright, letterSpacing: ls, margin: 0, fontWeight: 700, textShadow: `0 6px 40px #000a` }}>
            四十年，钉在日期上
          </h1>
          <div style={{ width: rule, height: 1, background: `linear-gradient(90deg, transparent, ${C.gold}, transparent)`, margin: '34px auto' }} />
          <p style={{ fontFamily: MONO, fontSize: 30, color: C.dim, letterSpacing: '0.18em', margin: 0, opacity: sub }}>
            从第一封电子邮件，到人人掌中的智能时代
          </p>
        </div>
      </AbsoluteFill>
      <div style={{ position: 'absolute', inset: 0, background: C.bg, opacity: interpolate(f, [0, FADE], [1, 0], { extrapolateRight: 'clamp' }) }} />
    </AbsoluteFill>
  );
};
