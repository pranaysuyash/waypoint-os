import { describe, expect, it } from 'vitest';
import {
  PHASE_DEVELOPMENT_SERVER,
  PHASE_PRODUCTION_BUILD,
  PHASE_PRODUCTION_SERVER,
} from 'next/constants.js';

import nextConfig from '../../../next.config.mjs';

describe('Next output directory contract', () => {
  it('isolates development output from production build and server output', () => {
    const development = nextConfig(PHASE_DEVELOPMENT_SERVER);
    const productionBuild = nextConfig(PHASE_PRODUCTION_BUILD);
    const productionServer = nextConfig(PHASE_PRODUCTION_SERVER);

    expect(development.distDir).toBe('.next-dev');
    expect(productionBuild.distDir).toBe('.next');
    expect(productionServer.distDir).toBe('.next');
    expect(development.distDir).not.toBe(productionBuild.distDir);
  });

  it('preserves the production packaging and header contracts', () => {
    const production = nextConfig(PHASE_PRODUCTION_BUILD);

    expect(production.output).toBe('standalone');
    expect(production.poweredByHeader).toBe(false);
    expect(production.rewrites).toBeUndefined();
  });
});
