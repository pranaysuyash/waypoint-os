import { describe, expect, it, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import BookingCollectionPage from '../[token]/page';

const mockGetForm = vi.fn();
const mockSubmit = vi.fn();

vi.mock('@/lib/api-client', () => ({
  getPublicCollectionForm: (...args: unknown[]) => mockGetForm(...args),
  submitPublicBookingData: (...args: unknown[]) => mockSubmit(...args),
}));

const VALID_CONTEXT = {
  valid: true,
  trip_summary: {
    destination: 'Paris',
    date_window: 'June 2026',
    traveler_count: 2,
    agency_name: 'Test Agency',
  },
};

function makeParams(token: string) {
  return Promise.resolve({ token });
}

describe('BookingCollectionPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows loading state initially', () => {
    mockGetForm.mockReturnValue(new Promise(() => {}));
    render(<BookingCollectionPage params={makeParams('abc123')} />);
    expect(screen.getByTestId('collection-loading')).toBeInTheDocument();
  });

  it('shows invalid state when token is not valid', async () => {
    mockGetForm.mockResolvedValue({ valid: false, reason: 'Token has expired.' });
    render(<BookingCollectionPage params={makeParams('expired')} />);

    await waitFor(() => {
      expect(screen.getByTestId('collection-invalid')).toBeInTheDocument();
    });
    expect(screen.getByText('Token has expired.')).toBeInTheDocument();
  });

  it('shows already-submitted state', async () => {
    mockGetForm.mockResolvedValue({ valid: true, already_submitted: true });
    render(<BookingCollectionPage params={makeParams('used123')} />);

    await waitFor(() => {
      expect(screen.getByTestId('collection-already-submitted')).toBeInTheDocument();
    });
  });

  it('renders trip summary and form fields for valid token', async () => {
    mockGetForm.mockResolvedValue(VALID_CONTEXT);
    render(<BookingCollectionPage params={makeParams('valid123')} />);

    await waitFor(() => {
      expect(screen.getByTestId('collection-form')).toBeInTheDocument();
    });
    expect(screen.getByTestId('trip-summary')).toBeInTheDocument();
    expect(screen.getByText('Paris')).toBeInTheDocument();
    expect(screen.getByText(/Test Agency/)).toBeInTheDocument();
    expect(screen.getByTestId('collection-traveler-0')).toBeInTheDocument();
  });

  it('can add and remove travelers', async () => {
    const user = userEvent.setup();
    mockGetForm.mockResolvedValue(VALID_CONTEXT);
    render(<BookingCollectionPage params={makeParams('valid123')} />);

    await waitFor(() => {
      expect(screen.getByTestId('collection-form')).toBeInTheDocument();
    });

    await user.click(screen.getByText('+ Add traveler'));
    expect(screen.getByTestId('collection-traveler-1')).toBeInTheDocument();

    const removeBtns = screen.getAllByText('Remove traveler');
    await user.click(removeBtns[0]);
    expect(screen.queryByTestId('collection-traveler-1')).not.toBeInTheDocument();
  });

  it('submits booking data', async () => {
    const user = userEvent.setup();
    mockGetForm.mockResolvedValue(VALID_CONTEXT);
    mockSubmit.mockResolvedValue({ ok: true, message: 'Submitted' });
    render(<BookingCollectionPage params={makeParams('valid123')} />);

    await waitFor(() => {
      expect(screen.getByTestId('collection-form')).toBeInTheDocument();
    });

    // Fill required fields
    const inputs = screen.getAllByRole('textbox');
    const travelerIdInput = inputs.find((el) => el.getAttribute('placeholder') === 'e.g. adult_1');
    if (travelerIdInput) await user.type(travelerIdInput, 'adult_1');

    await user.click(screen.getByTestId('collection-submit-btn'));

    await waitFor(() => {
      expect(mockSubmit).toHaveBeenCalledWith('valid123', expect.objectContaining({
        travelers: expect.arrayContaining([
          expect.objectContaining({ traveler_id: 'adult_1' }),
        ]),
      }));
    });
  });

  it('shows success state after submission', async () => {
    const user = userEvent.setup();
    mockGetForm.mockResolvedValue(VALID_CONTEXT);
    mockSubmit.mockResolvedValue({ ok: true, message: 'Submitted' });
    render(<BookingCollectionPage params={makeParams('valid123')} />);

    await waitFor(() => {
      expect(screen.getByTestId('collection-form')).toBeInTheDocument();
    });

    await user.click(screen.getByTestId('collection-submit-btn'));

    await waitFor(() => {
      expect(screen.getByTestId('collection-success')).toBeInTheDocument();
    });
  });

  it('shows error on submission failure', async () => {
    const user = userEvent.setup();
    mockGetForm.mockResolvedValue(VALID_CONTEXT);
    mockSubmit.mockRejectedValue(new Error('Server error (500)'));
    render(<BookingCollectionPage params={makeParams('valid123')} />);

    await waitFor(() => {
      expect(screen.getByTestId('collection-form')).toBeInTheDocument();
    });

    await user.click(screen.getByTestId('collection-submit-btn'));

    await waitFor(() => {
      expect(screen.getByTestId('collection-submit-error')).toBeInTheDocument();
    });
    expect(screen.getByText('Server error (500)')).toBeInTheDocument();
  });

  it('shows error when form context fails to load', async () => {
    mockGetForm.mockRejectedValue(new Error('Network error'));
    render(<BookingCollectionPage params={makeParams('bad123')} />);

    await waitFor(() => {
      expect(screen.getByTestId('collection-invalid')).toBeInTheDocument();
    });
    expect(screen.getByText('Failed to load form. Please try again later.')).toBeInTheDocument();
  });
});
