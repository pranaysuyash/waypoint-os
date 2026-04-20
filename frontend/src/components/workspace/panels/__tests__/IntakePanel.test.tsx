import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { IntakePanel } from '../IntakePanel';
import { useWorkbenchStore } from '@/stores/workbench';

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
    mutate: vi.fn(),
    isSaving: false,
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
});
