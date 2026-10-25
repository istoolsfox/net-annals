import React from 'react';
import { Composition } from 'remotion';
import { Journey } from './Promo';
import { MultiShot, MULTI_TOTAL } from './PromoMulti';

export const Root: React.FC = () => (
  <>
    <Composition id="Promo" component={Journey} durationInFrames={960} fps={30} width={1920} height={1080} />
    <Composition id="PromoMulti" component={MultiShot} durationInFrames={MULTI_TOTAL} fps={30} width={1920} height={1080} />
  </>
);
