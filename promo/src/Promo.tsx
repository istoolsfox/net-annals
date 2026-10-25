import React from 'react';
import { Composition, AbsoluteFill, Sequence, Audio, interpolate, useCurrentFrame } from 'remotion';
import { C } from './theme';
import { bgm } from './textures';
import { S1Hook } from './shots/S1Hook';
import { S2Scroll } from './shots/S2Scroll';
import { S3Numbers } from './shots/S3Numbers';
import { S4Views } from './shots/S4Views';
import { S5Today } from './shots/S5Today';
import { S6Proof } from './shots/S6Proof';
import { S7CTA } from './shots/S7CTA';

export const DUR = 960; // 32s @30fps

/** 镜头包装：章节式过渡——首尾各 10f 渐入/渐出黑，镜头之间不重叠。
 *  全片唯一的淡入淡出权责在这里；镜头内部禁止再做黑场。 */
const Shot: React.FC<{ from: number; dur: number; children: React.ReactNode }> = ({ from, dur, children }) => {
  const f = useCurrentFrame();
  const fadeIn = interpolate(f, [0, 10], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const fadeOut = interpolate(f, [dur - 10, dur], [1, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  return (
    <Sequence from={from} durationInFrames={dur}>
      <AbsoluteFill style={{ opacity: Math.min(fadeIn, fadeOut) }}>{children}</AbsoluteFill>
    </Sequence>
  );
};

const SHOTS: Array<[number, number, React.ReactNode]> = [
  [0, 100, <S1Hook />],
  [100, 200, <S2Scroll />],
  [300, 120, <S3Numbers />],
  [420, 165, <S4Views />],
  [585, 115, <S5Today />],
  [700, 130, <S6Proof />],
  [830, 130, <S7CTA />],
];

const Timeline: React.FC = () => {
  return (
    <AbsoluteFill style={{ background: '#000' }}>
      {SHOTS.map(([from, dur, node], i) => (
        <Sequence key={i} from={from} durationInFrames={dur} name={`S${i + 1}`}>
          <AbsoluteFill style={{ background: C.bg }}>
            {node}
          </AbsoluteFill>
        </Sequence>
      ))}
      <Audio src={bgm} volume={(fr) => interpolate(fr, [0, 30, DUR - 100, DUR], [0, 0.8, 0.8, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })} />
    </AbsoluteFill>
  );
};

export const RemotionRoot: React.FC = () => (
  <Composition id="Promo" component={Timeline} durationInFrames={DUR} fps={30} width={1920} height={1080} />
);
