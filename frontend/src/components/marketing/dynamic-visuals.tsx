'use client';

import dynamic from 'next/dynamic';

export const DynamicDataTransformationHero = dynamic(
  () => import('@/components/marketing/MarketingVisuals').then((m) => m.DataTransformationHero),
);
