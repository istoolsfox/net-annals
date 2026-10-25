import React from 'react';
import { Composition, AbsoluteFill, Sequence, Audio, interpolate, useCurrentFrame } from 'remotion';
import { C, FADE } from './theme';
import { bgm } from './textures';
import { S1Hook } from './shots/S1Hook';
import { S2Scroll } from './shots/S2Scroll';
import { S3Numbers } from './shots/S3Numbers';
import { S4Views } from './shots/S4Views';
import { S5Today } from './shots/S5Today';
import { S6Proof } from './shots/S6Proof';
import { S7CTA } from './shots/S7CTA';

export const DUR = 890; // ~29.7s @30fps

/** 镜头包装：进入时 15f 交叉淡入（叠在前一镜上），不做硬切 */
const Shot: React.FC<{ from: number; dur: number; children: React.ReactNode }> = ({ from, dur, children }) => {
  const f = useCurrentFrame();
  const opacity = interpolate(f, [0, FADE], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  return (
    <Sequence from={from} durationInFrames={dur + FADE}>
      <AbsoluteFill style={{ opacity }}>{children}</AbsoluteFill>
    </Sequence>
  );
};

const Timeline: React.FC = () => {
  const f = useCurrentFrame();
  const endFade = interpolate(f, [DUR - 25, DUR], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  return (
    <AbsoluteFill style={{ background: C.bg }}>
      <Shot from={0} dur={110}><S1Hook /></Shot>
      <Shot from={95} dur={190}><S2Scroll /></Shot>
      <Shot from={270} dur={125}><S3Numbers /></Shot>
      <Shot from={380} dur={165}><S4Views /></Shot>
      <Shot from={530} dur={125}><S5Today /></Shot>
      <Shot from={640} dur={135}><S6Proof /></Shot>
      <Shot from={760} dur={130}><S7CTA /></Shot>
      <AbsoluteFill style={{ background: C.bg, opacity: endFade }} />
      <Audio src={bgm} volume={(fr) => interpolate(fr, [0, 30, DUR - 100, DUR], [0, 0.8, 0.8, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })} />
    </AbsoluteFill>
  );
};

export const RemotionRoot: React.FC = () => (
  <Composition id="Promo" component={Timeline} durationInFrames={DUR} fps={30} width={1920} height={1080} />
);
