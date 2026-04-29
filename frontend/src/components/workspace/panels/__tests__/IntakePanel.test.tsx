import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { IntakePanel } from '../IntakePanel';
import { useWorkbenchStore } from '@/stores/workbench';
import { ApiException, updateTrip } from '@/lib/api-client';

// Mock dependencies
vi.mock('@/stores/workbench', () => ({
  useWorkbenchStore: vi.fn(),
}));

vi.mock('@/hooks/useSpineRun', () => ({
  useSpineRun: vi.fn(() => ({
    execute: vi.fn(),
    isLoading: false,
    error: null,
    reset: vi.fn(),
  })),
}));

vi.mock('@/hooks/useTrips', () => ({
  useUpdateTrip: vi.fn(() => ({
    mutate: vi.fn().mockResolvedValue(null),
    isSaving: false,
  })),
}));

vi.mock('@/contexts/TripContext', () => ({
  useTripContext: vi.fn(() => ({
    replaceTrip: vi.fn(),
    refetchTrip: vi.fn(),
  })),
}));

vi.mock('next/navigation', () => ({
  useRouter: vi.fn(() => ({
    push: vi.fn(),
  })),
}));

vi.mock('@/lib/routes', () => ({
  getTripRoute: vi.fn((id, stage) => `/workspace/${id}/${stage}`),
}));

vi.mock('@/lib/api-client', async () => {
  const actual = await vi.importActual<any>('@/lib/api-client');
  return {
    ...actual,
    updateTrip: vi.fn(),
  };
});

vi.mock('../CaptureCallPanel', () => ({
  default: ({ onSave, onCancel }: any) => (
    <div data-testid='capture-call-panel'>
      <button onClick={() => onSave({ id: 'TRIP-456' })}>Save Trip</button>
      <button onClick={onCancel}>Cancel</button>
    </div>
  ),
}));

describe('IntakePanel', () => {
  const mockStore = {
    input_raw_note: 'Test raw note',
    input_owner_note: 'Test owner note',
    setInputRawNote: vi.fn(),
    setInputOwnerNote: vi.fn(),
    stage: 'discovery',
    setStage: vi.fn(),
    operating_mode: 'normal_intake',
    setOperatingMode: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    (useWorkbenchStore as any).mockReturnValue(mockStore);
  });

  it('renders correctly with trip details', () => {
    const mockTrip = {
      id: 'TRIP-123',
      destination: 'Test Destination',
      type: 'Vacation',
      budget: '$5000',
      party: '2',
      dateWindow: 'Next month',
      age: '1d',
      state: 'blue',
    } as any;

    render(<IntakePanel tripId="TRIP-123" trip={mockTrip} />);

    // Check if trip details are rendered
    expect(screen.getByText('Test Destination')).toBeInTheDocument();
    expect(screen.getByText('TRIP-123')).toBeInTheDocument();
    
    // Check if configuration elements are rendered
    expect(screen.getByText('Configuration')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Discovery')).toBeInTheDocument();
    
    // Check if test inputs are passed to textareas
    expect(screen.getByDisplayValue('Test raw note')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Test owner note')).toBeInTheDocument();
  });

  it('renders process and save buttons', () => {
    render(<IntakePanel tripId="TRIP-123" />);

    const processButton = screen.getByRole('button', { name: /Process trip/i });
    expect(processButton).toBeInTheDocument();
    expect(processButton).not.toBeDisabled();

    const saveButton = screen.getByRole('button', { name: /Save changes/i });
    expect(saveButton).toBeInTheDocument();

    const readyButton = screen.getByRole('button', { name: /Mark ready/i });
    expect(readyButton).toBeInTheDocument();
  });

  it('disables process button when no notes are present', () => {
    (useWorkbenchStore as any).mockReturnValue({
      ...mockStore,
      input_raw_note: '',
      input_owner_note: '',
    });

    render(<IntakePanel tripId="TRIP-123" />);

    const processButton = screen.getByRole('button', { name: /Process trip/i });
    expect(processButton).toBeDisabled();
  });

  it('shows ready-gate failure details when mark ready is rejected', async () => {
    (updateTrip as any).mockRejectedValue(
      new ApiException('Ready gate failed', 400, undefined, ['Traveler-safe output is missing.'])
    );

    render(<IntakePanel tripId="TRIP-123" />);

    fireEvent.click(screen.getByRole('button', { name: /Mark ready/i }));

    await waitFor(() => {
      expect(screen.getByText(/Ready blocked:/i)).toBeInTheDocument();
      expect(screen.getByText(/Traveler-safe output is missing/i)).toBeInTheDocument();
    });
  });

  it('renders Capture Call button', () => {
    render(<IntakePanel tripId="TRIP-123" />);

    const captureCallButton = screen.getByRole('button', { name: /Capture Call/i });
    expect(captureCallButton).toBeInTheDocument();
  });

  it('shows CaptureCallPanel when Capture Call button is clicked', async () => {
    render(<IntakePanel tripId="TRIP-123" />);

    expect(screen.queryByTestId('capture-call-panel')).not.toBeInTheDocument();

    const captureCallButton = screen.getByRole('button', { name: /Capture Call/i });
    fireEvent.click(captureCallButton);

    await waitFor(() => {
      expect(screen.getByTestId('capture-call-panel')).toBeInTheDocument();
    });
  });

  it('hides CaptureCallPanel by default', () => {
    render(<IntakePanel tripId="TRIP-123" />);

    expect(screen.queryByTestId('capture-call-panel')).not.toBeInTheDocument();
  });

  it('closes CaptureCallPanel on cancel', async () => {
    render(<IntakePanel tripId="TRIP-123" />);

    const captureCallButton = screen.getByRole('button', { name: /Capture Call/i });
    fireEvent.click(captureCallButton);

    await waitFor(() => {
      expect(screen.getByTestId('capture-call-panel')).toBeInTheDocument();
    });

    const cancelButton = screen.getByRole('button', { name: 'Cancel' });
    fireEvent.click(cancelButton);

    await waitFor(() => {
      expect(screen.queryByTestId('capture-call-panel')).not.toBeInTheDocument();
    });
  });

  it('closes CaptureCallPanel and navigates on save', async () => {
    const { useRouter } = await import('next/navigation');
    const mockRouter = { push: vi.fn() };
    (useRouter as any).mockReturnValue(mockRouter);

    render(<IntakePanel tripId="TRIP-123" />);

    const captureCallButton = screen.getByRole('button', { name: /Capture Call/i });
    fireEvent.click(captureCallButton);

    await waitFor(() => {
      expect(screen.getByTestId('capture-call-panel')).toBeInTheDocument();
    });

    const saveButton = screen.getByRole('button', { name: 'Save Trip' });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(mockRouter.push).toHaveBeenCalledWith('/workspace/TRIP-456/packet');
    });
  });
});
