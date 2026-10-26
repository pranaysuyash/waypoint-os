// @vitest-environment jsdom

import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import LandingVariant, { resolveLandingVariant } from '../LandingVariant';

vi.mock('@/components/marketing/landing-v5', () => ({
  V5LandingPage: () => <div data-testid='v5-landing' />,
}));
vi.mock('@/components/marketing/departure-board/DepartureBoardHero', () => ({
  DepartureBoardLandingPage: () => <div data-testid='departure-landing' />,
}));

describe('LandingVariant (FND-0386 flag)', () => {
  let original: string | undefined;

  beforeEach(() => {
    original = process.env.NEXT_PUBLIC_LANDING_VARIANT;
  });
  afterEach(() => {
    if (original === undefined) delete process.env.NEXT_PUBLIC_LANDING_VARIANT;
    else process.env.NEXT_PUBLIC_LANDING_VARIANT = original;
    vi.restoreAllMocks();
  });

  it('defaults to the committed V5 landing when no variant is set', () => {
    delete process.env.NEXT_PUBLIC_LANDING_VARIANT;
    render(<LandingVariant />);
    expect(screen.getByTestId('v5-landing')).toBeInTheDocument();
    expect(screen.queryByTestId('departure-landing')).not.toBeInTheDocument();
  });

  it('opts into the departure board only via the explicit env flag', () => {
    process.env.NEXT_PUBLIC_LANDING_VARIANT = 'departure-board';
    render(<LandingVariant />);
    expect(screen.getByTestId('departure-landing')).toBeInTheDocument();
    expect(screen.queryByTestId('v5-landing')).not.toBeInTheDocument();
  });

  it('falls back to v5 on an unknown variant value', () => {
    process.env.NEXT_PUBLIC_LANDING_VARIANT = 'experimental-thing';
    render(<LandingVariant />);
    expect(screen.getByTestId('v5-landing')).toBeInTheDocument();
  });

  it('resolveLandingVariant is total', () => {
    expect(resolveLandingVariant(undefined)).toBe('v5');
    expect(resolveLandingVariant('')).toBe('v5');
    expect(resolveLandingVariant('departure-board')).toBe('departure-board');
    expect(resolveLandingVariant('garbage')).toBe('v5');
  });
});
