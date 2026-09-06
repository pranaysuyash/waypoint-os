// @vitest-environment jsdom

import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import DocumentMRZPanel from '../DocumentMRZPanel';

describe('DocumentMRZPanel truth boundary', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('labels checksum output as format-only and never as identity verification', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        status: 'success',
        passport: {
          surname: 'ERIKSSON',
          given_names: 'ANNA MARIA',
          passport_number: 'L898902C',
          nationality: 'UTO',
          date_of_birth: '1969-08-06',
          gender: 'F',
          expiration_date: '2028-01-02',
          checksums_valid: {
            passport_number: true,
            date_of_birth: true,
            expiration_date: true,
            composite: true,
          },
        },
      }),
    }));

    render(<DocumentMRZPanel />);
    const user = userEvent.setup();

    expect(screen.getByTestId('simulated-badge')).toHaveTextContent('Sample data');
    expect(screen.getByTestId('mrz-preview-notice')).toHaveTextContent(/does not authenticate a passport/i);

    await user.click(screen.getByRole('button', { name: /compute checksum preview/i }));

    expect(await screen.findByText(/CHECKSUMS VALID — FORMAT ONLY/i)).toBeInTheDocument();
    expect(screen.getByText(/did not verify document authenticity/i)).toBeInTheDocument();
    expect(screen.queryByText(/ZERO TRANSCRIPTION ERROR/i)).not.toBeInTheDocument();
  });

  it('does not fabricate a passport result when the parser is unavailable', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('offline')));

    render(<DocumentMRZPanel />);
    const user = userEvent.setup();

    await user.click(screen.getByRole('button', { name: /compute checksum preview/i }));

    expect(await screen.findByRole('alert')).toHaveTextContent(/no checksum result was produced/i);
    expect(screen.queryByText(/ERIKSSON/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/CHECKSUMS VALID/i)).not.toBeInTheDocument();
  });

  it('labels voucher identifiers as fixtures without provider synchronization', async () => {
    render(<DocumentMRZPanel />);
    const user = userEvent.setup();

    await user.click(screen.getByRole('button', { name: /13-digit e-ticket & vouchers/i }));

    expect(screen.getByTestId('voucher-preview-notice')).toHaveTextContent(/no ticket, booking, or hotel voucher is checked/i);
    expect(screen.getByText(/FORMAT PREVIEW ONLY/i)).toBeInTheDocument();
    expect(screen.getByText(/NO GDS LOOKUP/i)).toBeInTheDocument();
    expect(screen.getByText(/NO HOTEL API LOOKUP/i)).toBeInTheDocument();
    expect(screen.queryByText(/Amadeus Synchronized/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Direct API Linked/i)).not.toBeInTheDocument();
  });
});
