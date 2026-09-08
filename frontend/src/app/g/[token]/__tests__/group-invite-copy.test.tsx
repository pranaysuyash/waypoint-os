// @vitest-environment jsdom

import { describe, expect, it, vi, afterEach, beforeEach } from 'vitest';
import { render, screen, waitFor, cleanup } from '@testing-library/react';

vi.mock('next/navigation', () => ({
  useParams: () => ({ token: 'tok-browser-smoke' }),
}));

/**
 * Part-K AT-21 coverage: the group member page (/g/[token]) previously had
 * NO test coverage, and browser error strings ("Failed to fetch") leaked to
 * the error screen. Gates: fixed traveler-voiced copy renders, internal
 * vocabulary never does.
 */

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe('Group invite page copy honesty (AT-21)', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn());
  });

  it('renders the fixed traveler line on network failure — never the browser error', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockRejectedValue(new TypeError('Failed to fetch')),
    );

    const { default: PublicGroupSharePage } = await import('../page');
    render(<PublicGroupSharePage />);

    await waitFor(() => {
      expect(
        screen.getByText(
          /This invite link is not working right now. Please ask your travel advisor to resend it./i,
        ),
      ).toBeInTheDocument();
    });
    expect(screen.queryByText(/Failed to fetch/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/TypeError/i)).not.toBeInTheDocument();
  });

  it('renders the fixed traveler line when the invite is invalid or expired', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({ ok: false, status: 404, json: async () => ({}) }),
    );

    const { default: PublicGroupSharePage } = await import('../page');
    render(<PublicGroupSharePage />);

    await waitFor(() => {
      expect(
        screen.getByText(/This invite link is not working right now/i),
      ).toBeInTheDocument();
    });
    expect(screen.queryByText(/Failed to load group invite/i)).not.toBeInTheDocument();
  });
});
