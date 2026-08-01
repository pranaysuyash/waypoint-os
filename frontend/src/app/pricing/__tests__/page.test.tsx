import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import PricingPage from '@/components/marketing/pricing-page';

describe('pricing page', () => {
  it('explains the real pricing tiers and keeps signup self-serve', () => {
    render(<PricingPage />);

    expect(
      screen.getByRole('heading', { name: /Pricing that matches how the agency actually starts using Waypoint/i, level: 1 }),
    ).toBeInTheDocument();
    expect(
      screen.getAllByRole('link', { name: /Create workspace/i }).some((link) => link.getAttribute('href') === '/signup'),
    ).toBe(true);
    expect(
      screen.getByText(/The app already supports manual capture, internal notes, and trip planning/i),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('heading', { name: /Choose the tier that fits the job you want done/i, level: 2 }),
    ).toBeInTheDocument();
  });
});
