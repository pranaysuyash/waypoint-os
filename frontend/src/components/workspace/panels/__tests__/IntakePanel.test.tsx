import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { IntakePanel } from '../IntakePanel';
import { useWorkbenchStore } from '@/stores/workbench';
import { ApiException, updateTrip } from '@/lib/api-client';
import { useAuthStore } from '@/stores/auth';
import { formatInquiryReference } from '@/lib/lead-display';

const mockSaveTrip = vi.fn();
const mockStartPlanning = vi.fn();

// Mock dependencies
vi.mock('@/stores/workbench', () => ({
  useWorkbenchStore: vi.fn(),
}));

vi.mock('@/stores/auth', () => ({
  useAuthStore: vi.fn(),
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
    mutate: mockSaveTrip,
    isSaving: false,
  })),
  useStartPlanning: vi.fn(() => ({
    mutate: mockStartPlanning,
    isStarting: false,
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
    replace: vi.fn(),
  })),
  useSearchParams: vi.fn(() => new URLSearchParams()),
}));

vi.mock('@/lib/routes', () => ({
  getTripRoute: vi.fn((id, stage) => `/trips/${id}/${stage}`),
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
    mockSaveTrip.mockResolvedValue(null);
    mockStartPlanning.mockResolvedValue({ success: true, trip_id: 'TRIP-123', assigned_to: 'Alex Agent' });
    (useWorkbenchStore as any).mockReturnValue(mockStore);
    (useAuthStore as any).mockImplementation((selector: any) =>
      selector({
        user: { id: 'agent-1', email: 'alex@agency.com', name: 'Alex Agent' },
      })
    );
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
    expect(screen.getAllByText('Test Destination').length).toBeGreaterThan(0);
    expect(screen.getAllByText(formatInquiryReference('TRIP-123')).length).toBeGreaterThan(0);
    
    // Check if configuration elements are rendered
    expect(screen.getByText('Advanced configuration')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Discovery')).toBeInTheDocument();
    
    // Check if test inputs are passed to textareas
    fireEvent.click(screen.getByRole('button', { name: /Open notes/i }));
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

  it('shows review mode for incomplete leads before planning starts', () => {
    render(
      <IntakePanel
        tripId="trip_4b9e0d894872"
        trip={{
          id: 'trip_4b9e0d894872',
          destination: 'Singapore',
          type: 'Family',
          budget: '$0',
          party: 5,
          dateWindow: 'dates around 9th to 14th feb',
          state: 'blue',
          age: '1d',
          createdAt: '2026-04-23T08:00:00.000Z',
          updatedAt: '2026-04-23T08:15:00.000Z',
          status: 'incomplete',
        } as any}
      />
    );

    expect(screen.getByRole('button', { name: /start planning/i })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /process trip/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /mark ready/i })).not.toBeInTheDocument();
    expect(screen.getByText('Budget missing')).toBeInTheDocument();
    expect(screen.getByText('Around Feb 9–14')).toBeInTheDocument();
    expect(screen.getByText('Inquiry Ref')).toBeInTheDocument();
    expect(screen.getByText(/4B9E/i)).toBeInTheDocument();
    expect(screen.getByText('Missing before planning')).toBeInTheDocument();
    expect(screen.getByText('Budget and trip details need confirmation.')).toBeInTheDocument();
    expect(screen.getByText('Review the lead and confirm missing details with the traveler.')).toBeInTheDocument();
    expect(screen.getByText('Incomplete intake.')).toBeInTheDocument();
    expect(screen.queryByText('trip_4b9e0d894872')).not.toBeInTheDocument();
  });

  it('starts planning with the current agent when review mode action is used', async () => {
    render(
      <IntakePanel
        tripId="TRIP-123"
        trip={{
          id: 'TRIP-123',
          destination: 'Singapore',
          type: 'Family',
          state: 'blue',
          age: '1d',
          createdAt: '2026-04-23T08:00:00.000Z',
          updatedAt: '2026-04-23T08:15:00.000Z',
          status: 'incomplete',
        } as any}
      />
    );

    fireEvent.click(screen.getByRole('button', { name: /start planning/i }));

    await waitFor(() => {
      expect(mockStartPlanning).toHaveBeenCalledWith('TRIP-123', 'agent-1', 'Alex Agent');
    });
  });

  it('shows blocker-aware planning mode after start planning when the brief is still incomplete', () => {
    render(
      <IntakePanel
        tripId="trip_4b9e0d894872"
        trip={{
          id: 'trip_4b9e0d894872',
          destination: 'Singapore',
          type: 'Family Leisure',
          budget: '$0',
          party: 5,
          dateWindow: 'dates around 9th to 14th feb',
          state: 'amber',
          age: 'Today',
          createdAt: '2026-04-23T08:00:00.000Z',
          updatedAt: '2026-04-23T08:15:00.000Z',
          status: 'assigned',
          decision: {
            decision_state: 'ASK_FOLLOWUP',
            hard_blockers: [],
            soft_blockers: ['incomplete_intake'],
            contradictions: [],
            risk_flags: [],
            follow_up_questions: [],
            rationale: {},
            confidence: {},
            branch_options: [],
            commercial_decision: 'NONE',
            budget_breakdown: null,
          },
          validation: {
            warnings: [
              {
                severity: 'warning',
                code: 'QUOTE_READY_INCOMPLETE',
                message: 'Field budget_raw_text missing',
                field: 'budget_raw_text',
              },
            ],
          },
        } as any}
      />
    );

    expect(screen.getByText('Before building options')).toBeInTheDocument();
    expect(screen.getByText('Confirm budget range before building options.')).toBeInTheDocument();
    expect(screen.getByText('Next')).toBeInTheDocument();
    expect(screen.getByText('Ask the traveler for budget range.')).toBeInTheDocument();
    expect(screen.getByText('Watch')).toBeInTheDocument();
    expect(screen.getByText('Incomplete intake.')).toBeInTheDocument();
    expect(screen.getByText('Inquiry Ref')).toBeInTheDocument();
    expect(screen.getAllByText(/4B9E/i).length).toBeGreaterThan(0);
    expect(screen.queryByText('trip_4b9e0d894872')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Mark ready/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Process trip/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Continue planning/i })).not.toBeInTheDocument();
    expect(screen.getAllByRole('button', { name: /Draft follow-up/i }).length).toBeGreaterThanOrEqual(1);
  });

  it('prioritizes missing-customer-details workflow above generic notes when planning is blocked', () => {
    render(
      <IntakePanel
        tripId="trip_4b9e0d894872"
        trip={{
          id: 'trip_4b9e0d894872',
          destination: 'Singapore',
          type: 'Family Leisure',
          budget: '$0',
          party: 5,
          dateWindow: 'dates around 9th to 14th feb',
          state: 'amber',
          age: 'Today',
          createdAt: '2026-04-23T08:00:00.000Z',
          updatedAt: '2026-04-23T08:15:00.000Z',
          status: 'assigned',
          decision: {
            decision_state: 'ASK_FOLLOWUP',
            hard_blockers: [],
            soft_blockers: ['incomplete_intake'],
            contradictions: [],
            risk_flags: [],
            follow_up_questions: [],
            rationale: {},
            confidence: {},
            branch_options: [],
            commercial_decision: 'NONE',
            budget_breakdown: null,
          },
          validation: {
            warnings: [
              {
                severity: 'warning',
                code: 'QUOTE_READY_INCOMPLETE',
                message: 'Field budget_raw_text missing',
                field: 'budget_raw_text',
              },
              {
                severity: 'warning',
                code: 'QUOTE_READY_INCOMPLETE',
                message: 'Field origin_city missing',
                field: 'origin_city',
              },
            ],
          },
        } as any}
      />
    );

    expect(screen.getByText('Missing Customer Details')).toBeInTheDocument();
    expect(screen.getByText('Required missing fields')).toBeInTheDocument();
    expect(screen.getByText('Recommended details')).toBeInTheDocument();
    expect(screen.getByText('Budget range')).toBeInTheDocument();
    expect(screen.getByText('Trip priorities / must-haves')).toBeInTheDocument();
    expect(screen.getByText('Origin city')).toBeInTheDocument();
    expect(screen.getAllByText('Date flexibility').length).toBeGreaterThan(0);
    expect(screen.getAllByRole('button', { name: /Add budget/i }).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByRole('button', { name: /Add origin/i }).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByRole('button', { name: /Add priorities/i }).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByRole('button', { name: /Add flexibility/i }).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('Suggested Follow-up')).toBeInTheDocument();
    expect(screen.getByDisplayValue(/could you confirm your approximate budget range/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Copy message/i })).toBeInTheDocument();
    expect(screen.queryByText('Known Trip Details')).not.toBeInTheDocument();
    expect(screen.getByText('Notes')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Open notes/i })).toBeInTheDocument();
  });

  it('opens an inline editor for a missing planning detail', () => {
    render(
      <IntakePanel
        tripId="trip_4b9e0d894872"
        trip={{
          id: 'trip_4b9e0d894872',
          destination: 'Singapore',
          type: 'Family Leisure',
          budget: '$0',
          party: 5,
          dateWindow: 'dates around 9th to 14th feb',
          state: 'amber',
          age: 'Today',
          createdAt: '2026-04-23T08:00:00.000Z',
          updatedAt: '2026-04-23T08:15:00.000Z',
          status: 'assigned',
          decision: {
            decision_state: 'ASK_FOLLOWUP',
            hard_blockers: [],
            soft_blockers: ['incomplete_intake'],
            contradictions: [],
            risk_flags: [],
            follow_up_questions: [],
            rationale: {},
            confidence: {},
            branch_options: [],
            commercial_decision: 'NONE',
            budget_breakdown: null,
          },
          validation: {
            warnings: [
              {
                severity: 'warning',
                code: 'QUOTE_READY_INCOMPLETE',
                message: 'Field budget_raw_text missing',
                field: 'budget_raw_text',
              },
            ],
          },
        } as any}
      />
    );

    fireEvent.click(screen.getAllByRole('button', { name: /Add budget/i })[0]);

    expect(screen.getByPlaceholderText(/Approximate budget/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Save budget/i })).toBeInTheDocument();
  });

  it('keeps origin typing stable and saves the typed value as the origin field', async () => {
    const user = userEvent.setup();
    mockSaveTrip.mockResolvedValue({
      id: 'trip_4b9e0d894872',
      destination: 'Singapore',
      type: 'Family Leisure',
      budget: '$0',
      party: 5,
      dateWindow: 'dates around 9th to 14th feb',
      origin: 'bangalore',
      state: 'amber',
      age: 'Today',
      createdAt: '2026-04-23T08:00:00.000Z',
      updatedAt: '2026-04-23T08:15:00.000Z',
      status: 'assigned',
      decision: {
        decision_state: 'ASK_FOLLOWUP',
        hard_blockers: [],
        soft_blockers: ['incomplete_intake'],
      },
      validation: {
        warnings: [
          {
            severity: 'warning',
            code: 'QUOTE_READY_INCOMPLETE',
            message: 'Field budget_raw_text missing',
            field: 'budget_raw_text',
          },
        ],
      },
    });

    render(
      <IntakePanel
        tripId="trip_4b9e0d894872"
        trip={{
          id: 'trip_4b9e0d894872',
          destination: 'Singapore',
          type: 'Family Leisure',
          budget: '$0',
          party: 5,
          dateWindow: 'dates around 9th to 14th feb',
          origin: 'TBD',
          state: 'amber',
          age: 'Today',
          createdAt: '2026-04-23T08:00:00.000Z',
          updatedAt: '2026-04-23T08:15:00.000Z',
          status: 'assigned',
          decision: {
            decision_state: 'ASK_FOLLOWUP',
            hard_blockers: [],
            soft_blockers: ['incomplete_intake'],
          },
          validation: {
            warnings: [
              {
                severity: 'warning',
                code: 'QUOTE_READY_INCOMPLETE',
                message: 'Field budget_raw_text missing',
                field: 'budget_raw_text',
              },
              {
                severity: 'warning',
                code: 'QUOTE_READY_INCOMPLETE',
                message: 'Field origin_city missing',
                field: 'origin_city',
              },
            ],
          },
        } as any}
      />
    );

    await user.click(screen.getByRole('button', { name: /Add origin/i }));
    const originInput = screen.getByPlaceholderText(/Add the departure city/i);

    await user.type(originInput, 'bangalore');

    expect(originInput).toHaveValue('bangalore');

    await user.click(screen.getByRole('button', { name: /Save origin/i }));

    await waitFor(() => {
      expect(mockSaveTrip).toHaveBeenCalledWith('trip_4b9e0d894872', { origin: 'bangalore' });
    });
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

    const captureCallButton = screen.getByRole('button', { name: /Capture call notes/i });
    expect(captureCallButton).toBeInTheDocument();
  });

  it('shows CaptureCallPanel when Capture Call button is clicked', async () => {
    render(<IntakePanel tripId="TRIP-123" />);

    expect(screen.queryByTestId('capture-call-panel')).not.toBeInTheDocument();

    const captureCallButton = screen.getByRole('button', { name: /Capture call notes/i });
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

    const captureCallButton = screen.getByRole('button', { name: /Capture call notes/i });
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

    const captureCallButton = screen.getByRole('button', { name: /Capture call notes/i });
    fireEvent.click(captureCallButton);

    await waitFor(() => {
      expect(screen.getByTestId('capture-call-panel')).toBeInTheDocument();
    });

    const saveButton = screen.getByRole('button', { name: 'Save Trip' });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(mockRouter.push).toHaveBeenCalledWith('/trips/TRIP-456/packet');
    });
  });
});
