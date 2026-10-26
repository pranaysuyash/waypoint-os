'use client';

/**
 * LandingVariant — FND-0386: the departure-board landing is a big interactive
 * bet; it must not silently replace the proven landing. Selection is env-
 * driven: NEXT_PUBLIC_LANDING_VARIANT=departure-board opts in; the default
 * stays the committed V5 landing. No runtime UI, no persistence — build/deploy
 * time flag only.
 */

import { DepartureBoardLandingPage } from '@/components/marketing/departure-board/DepartureBoardHero';
import { V5LandingPage } from '@/components/marketing/landing-v5';

export type LandingVariantName = 'v5' | 'departure-board';

export function resolveLandingVariant(raw: string | undefined): LandingVariantName {
  return raw === 'departure-board' ? 'departure-board' : 'v5';
}

export default function LandingVariant({ variant }: { variant?: LandingVariantName }) {
  const raw = process.env.NEXT_PUBLIC_LANDING_VARIANT;
  const resolved =
    variant ??
    (raw === undefined && process.env.NODE_ENV === 'development'
      ? 'departure-board'
      : resolveLandingVariant(raw));
  if (resolved === 'departure-board') {
    return <DepartureBoardLandingPage />;
  }
  return <V5LandingPage />;
}
