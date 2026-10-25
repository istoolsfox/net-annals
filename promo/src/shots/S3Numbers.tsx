import React from 'react';
import { AbsoluteFill, interpolate, useCurrentFrame } from 'remotion';
import { C, SERIF, MONO, EASE } from '../theme'
import { TEX, appleIcon } from '../textures';
import { DigitRoll } from '../lib/DigitRoll';

const STATS = [
  { v: '8,562', lab: '条事件 · 精确到日', delay: 4 },
  { v: '6,883', lab: '条双源实证', delay: 22 },
  { v: '841', lab: '个时代转折点', delay: 40 },
  { v: '55', lab: '年 · 从未断更的长卷', delay: 58 },
];

/** S3 数字冲击：里程表式数字逐行落定 */
export const S3Numbers: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{ justifyContent: 'center' }}>
      <div style={{ padding: '0 220px', display: 'flex', flexDirection: 'column', gap: 34 }}>
        {STATS.map((s) => {
          const opacity = interpolate(f, [s.delay, s.delay + 16], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
          const tx = interpolate(f, [s.delay, s.delay + 16], [-60, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
          return (
            <div key={s.lab} style={{ display: 'flex', alignItems: 'baseline', gap: 30, opacity, transform: `translateX(${tx}px)` }}>
              <span style={{ fontFamily: MONO, fontSize: 110, color: C.goldBright, fontWeight: 700, lineHeight: 1.05 }}>
                <DigitRoll value={s.v} delay={s.delay + 2} fontSize={110} color={C.goldBright} stagger={2} roll={15} />
              </span>
              <span style={{ fontFamily: SERIF, fontSize: 40, color: C.text, letterSpacing: '0.12em' }}>{s.lab}</span>
            </div>
          );
        })}
      </div>
      <div style={{ position: 'absolute', right: 200, bottom: 120, fontFamily: MONO, fontSize: 22, color: C.faint, letterSpacing: '0.2em', opacity: interpolate(f, [78, 90], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }) }}>
        —— 每一条，都标注来源与置信度
      </div>
    </AbsoluteFill>
  );
};
