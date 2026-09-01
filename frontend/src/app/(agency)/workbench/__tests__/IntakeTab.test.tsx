import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import IntakeTab from '../IntakeTab';
import type { Trip } from '@/lib/api-client';

const mockReplace = vi.fn();

// Mutable holder so tests can drive the workbench draft state the component reads.
const mockStore = vi.hoisted(() => ({
  input_raw_note: '',
  input_owner_note: '',
  draft_status: 'open',
  setInputRawNote: vi.fn(),
  setInputOwnerNote: vi.fn(),
}));

vi.mock('next/navigation', () => ({
  useSearchParams: () => new URLSearchParams(),
  useRouter: () => ({ replace: mockReplace }),
  usePathname: () => '/workbench',
}));

vi.mock('@/stores/workbench', () => ({
  useWorkbenchStore: () => mockStore,
}));

const baseTrip = {
  id: 'trip-intake-tab',
  destination: 'Bali',
  type: 'family leisure',
  state: 'green',
  age: '1h',
  createdAt: '2026-08-31T00:00:00Z',
  updatedAt: '2026-08-31T00:00:00Z',
  party: 4,
  budget: '₹4L',
  dateWindow: 'Jul 2026',
} as Trip;

describe('IntakeTab', () => {
  beforeEach(() => {
    mockReplace.mockReset();
    mockStore.input_raw_note = '';
    mockStore.input_owner_note = '';
    mockStore.draft_status = 'open';
  });

  it('shows the canonical trip purpose prompt in the intake helper copy', () => {
    render(<IntakeTab trip={null} />);

    expect(screen.getByText(/What is the purpose of this trip/i)).toBeInTheDocument();
    expect(screen.getByText(/Need the purpose fast\?/i)).toBeInTheDocument();
  });

  it('updates the full workbench pathname when the stage changes', async () => {
    render(<IntakeTab trip={null} />);

    await userEvent.selectOptions(screen.getByLabelText('Stage'), 'booking');

    expect(mockReplace).toHaveBeenCalledWith('/workbench?stage=booking', { scroll: false });
  });

  // IMP-03 (DEMO-08): the captured-details empty state must reflect run state honestly.
  it('shows the captured-details empty state before any run', () => {
    render(<IntakeTab trip={null} />);

    expect(
      screen.getByText('Captured details will appear here after processing the inquiry.'),
    ).toBeInTheDocument();
  });

  it('shows an in-flight line while processing instead of the pre-run copy', () => {
    mockStore.draft_status = 'processing';
    render(<IntakeTab trip={null} />);

    expect(
      screen.getByText(/Processing the inquiry — captured details will appear here\./),
    ).toBeInTheDocument();
    expect(
      screen.queryByText('Captured details will appear here after processing the inquiry.'),
    ).not.toBeInTheDocument();
  });

  it('does not duplicate the empty-state copy after a blocked run', () => {
    mockStore.draft_status = 'blocked';
    render(<IntakeTab trip={null} />);

    expect(
      screen.queryByText('Captured details will appear here after processing the inquiry.'),
    ).not.toBeInTheDocument();
    expect(
      screen.getByText(/Processing stopped before any details were captured/i),
    ).toBeInTheDocument();
  });

  it('renders the sample recall card only when no trip is captured', () => {
    const { rerender } = render(<IntakeTab trip={null} />);

    expect(screen.getByTestId('sample-data-badge')).toBeInTheDocument();

    rerender(<IntakeTab trip={baseTrip} />);

    expect(screen.queryByTestId('sample-data-badge')).not.toBeInTheDocument();
    expect(screen.getByText('Bali')).toBeInTheDocument();
  });
});
