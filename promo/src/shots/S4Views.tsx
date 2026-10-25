import React from 'react';
import { AbsoluteFill, interpolate, useCurrentFrame, Easing } from 'remotion';
import { C, SERIF, MONO } from '../theme'
import { TEX, appleIcon } from '../textures';

import React from 'react';
import { AbsoluteFill, interpolate, useCurrentFrame, Easing } from 'remotion';
import { C, SERIF, MONO, EASE } from '../theme';
import { TEX } from '../textures';

const VIEWS = [
  { img: 'persons-top', tag: 'BIOGRAPHY', name: '人物志', sub: '一条条人生长卷' },
  { img: 'entities-top', tag: 'HEREDITARY HOUSES', name: '世家志', sub: '兴衰成对，为每一家立传' },
  { img: 'works-top', tag: 'WORKS', name: '作品志', sub: '陪伴大众精神生活的创作物' },
];
const EACH = 50;   // 每视图 ~1.7s
const CROSS = 16;  // 交叉淡入

/** S4 板块：三视图交叉淡入 + 缓慢推近（无硬切无闪屏），取景贴内容列 */
export const S4Views: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill>
      {VIEWS.map((v, i) => {
        const start = i * (EACH - CROSS);
        const lf = f - start;
        if (lf < 0) return null;
        const op = interpolate(lf, [0, CROSS], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
        const zoom = interpolate(lf, [0, EACH], [1.02, 1.1], { extrapolateRight: 'clamp', easing: Easing.bezier(...EASE) });
        const capIn = interpolate(lf, [CROSS, CROSS + 12], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
        // 下一视图开始淡入时，本视图字幕同步退场（避免字幕与下一画面错配）
        const capOut = i < VIEWS.length - 1 ? interpolate(lf, [EACH - CROSS - 6, EACH - 2], [1, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }) : 1;
        const cap = capIn * capOut;
        return (
          <AbsoluteFill key={v.name} style={{ opacity: op }}>
            <img src={TEX[v.img]} style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover', objectPosition: 'center 62%', transform: `scale(${zoom})` }} />
            <AbsoluteFill style={{ background: `linear-gradient(90deg, #0c0d10e0 0%, #0c0d1055 45%, transparent 70%)` }} />
            <div style={{ position: 'absolute', left: 96, bottom: 120, opacity: cap, transform: `translateY(${(1 - cap) * 20}px)` }}>
              <div style={{ fontFamily: MONO, fontSize: 24, color: C.gold, letterSpacing: '0.34em', marginBottom: 14 }}>{v.tag}</div>
              <div style={{ fontFamily: SERIF, fontSize: 96, color: C.goldBright, fontWeight: 700, textShadow: '0 4px 30px #000c' }}>{v.name}</div>
              <div style={{ fontFamily: SERIF, fontSize: 38, color: C.text, marginTop: 12, letterSpacing: '0.1em' }}>{v.sub}</div>
            </div>
          </AbsoluteFill>
        );
      })}
    </AbsoluteFill>
  );
};
