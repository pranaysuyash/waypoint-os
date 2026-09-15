import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { OnFileMemoryCard } from '../OnFileMemoryCard';

const fetchMock = vi.fn();

function mockFetchSequence(responses: Array<{ ok: boolean; body: unknown }>) {
  fetchMock.mockImplementation(() =>
    Promise.resolve({
      ok: responses[0]?.ok ?? false,
      json: () => Promise.resolve(responses[0]?.body),
    })
  );
}

describe('OnFileMemoryCard', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', fetchMock);
    vi.spyOn(window, 'confirm').mockReturnValue(true);
  });

  afterEach(() => {
    fetchMock.mockReset();
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it('renders nothing when nothing is on file (fail silent)', async () => {
    fetchMock.mockImplementation(() =>
      Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({ ok: true, memory_found: false, customer_id: null, facts: [] }),
      })
    );
    const { container } = render(<OnFileMemoryCard tripId="trip-1" />);
    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    expect(container.querySelector('[data-testid="on-file-memory-card"]')).toBeNull();
  });

  it('renders on-file chips with observed dates and the display-only note', async () => {
    fetchMock.mockImplementation(() =>
      Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({
            ok: true,
            memory_found: true,
            customer_id: 'cust_a@x.com',
            customer_name: 'Eleanor Vance',
            facts: [
              {
                field_name: 'dietary_requirements',
                value: 'Dietary requirement: Strict Vegan & Nut-Free',
                observed_at: '2026-09-15T10:00:00+00:00',
                source: 'memory',
              },
              {
                field_name: null,
                value: 'Room preference: High-floor quiet corner suite',
                observed_at: '2026-09-15T10:00:00+00:00',
                source: 'memory:profile',
              },
            ],
          }),
      })
    );
    render(<OnFileMemoryCard tripId="trip-1" />);

    const card = await screen.findByTestId('on-file-memory-card');
    expect(card).toBeInTheDocument();
    expect(screen.getByText(/Eleanor Vance/)).toBeInTheDocument();
    expect(screen.getByText(/Strict Vegan & Nut-Free/)).toBeInTheDocument();
    expect(screen.getByText(/not confirmed for this trip/i)).toBeInTheDocument();
    // Purge affordance present (E-D §2 corollary 4: traveler can inspect and purge).
    expect(screen.getByRole('button', { name: /erase on-file memory/i })).toBeInTheDocument();
  });

  it('purges via the forget endpoint and clears the card without faking success on failure', async () => {
    const user = userEvent.setup();
    fetchMock
      .mockImplementationOnce(() =>
        Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              ok: true,
              memory_found: true,
              customer_id: 'cust_a@x.com',
              customer_name: null,
              facts: [
                {
                  field_name: 'dietary_requirements',
                  value: 'Dietary requirement: Strict Vegan & Nut-Free',
                  observed_at: '2026-09-15T10:00:00+00:00',
                  source: 'memory',
                },
              ],
            }),
        })
      )
      .mockImplementationOnce(() =>
        Promise.resolve({ ok: true, json: () => Promise.resolve({ ok: true }) })
      );

    render(<OnFileMemoryCard tripId="trip-1" />);
    const button = await screen.findByRole('button', { name: /erase on-file memory/i });
    await user.click(button);

    await waitFor(() =>
      expect(screen.queryByTestId('on-file-memory-card')).toBeNull()
    );
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(JSON.parse(fetchMock.mock.calls[1][1].body)).toEqual({
      customerId: 'cust_a@x.com',
    });
  });
});
