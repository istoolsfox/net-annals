import React from 'react';
import { Composition, AbsoluteFill, Sequence, Audio, interpolate } from 'remotion';
import { bgm } from './textures';
import { C } from './theme';
import { S1Hook } from './shots/S1Hook';
import { S2Scroll } from './shots/S2Scroll';
import { S3Numbers } from './shots/S3Numbers';
import { S4Views } from './shots/S4Views';
import { S5Today } from './shots/S5Today';
import { S6Proof } from './shots/S6Proof';
import { S7CTA } from './shots/S7CTA';

export const DUR = 780; // 26s @30fps

const SHOTS: Array<[number, number, React.ReactNode]> = [
  [0, 105, <S1Hook />],
  [105, 180, <S2Scroll />],
  [285, 90, <S3Numbers />],
  [375, 120, <S4Views />],
  [495, 90, <S5Today />],
  [585, 90, <S6Proof />],
  [675, 105, <S7CTA />],
];

const Timeline: React.FC = () => {
  return (
    <AbsoluteFill style={{ background: C.bg }}>
      {SHOTS.map(([from, dur, node], i) => (
        <Sequence key={i} from={from} durationInFrames={dur} name={`S${i + 1}`}>
          {node}
        </Sequence>
      ))}
      {/* BGM：开头淡入、结尾淡出 */}
      <Audio src={bgm} volume={(fr) => interpolate(fr, [0, 30, DUR - 90, DUR], [0, 0.8, 0.8, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })} />
    </AbsoluteFill>
  );
};

export const RemotionRoot: React.FC = () => (
  <Composition id="Promo" component={Timeline} durationInFrames={DUR} fps={30} width={1920} height={1080} />
);
