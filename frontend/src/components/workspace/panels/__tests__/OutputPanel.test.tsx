import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import OutputPanel from '../OutputPanel';
import { useWorkbenchStore } from '@/stores/workbench';
import { safeWriteClipboardText } from '@/lib/clipboard';

// Mock dependencies
vi.mock('@/stores/workbench', () => ({
  useWorkbenchStore: vi.fn(),
}));

vi.mock('@/lib/clipboard', () => ({
  safeWriteClipboardText: vi.fn().mockResolvedValue(true),
}));

describe('OutputPanel', () => {
  const mockStore = {
    result_internal_bundle: {
      system_context: 'Internal Context Test',
      user_message: 'Internal Message Test',
      constraints: ['Constraint 1', 'Constraint 2'],
    },
    result_traveler_bundle: {
      system_context: 'Traveler Context Test',
      user_message: 'Traveler Message Test',
      follow_up_sequence: [{ question: 'Any questions?' }],
    },
    debug_raw_json: false,
    setDebugRawJson: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.unstubAllEnvs();
    (useWorkbenchStore as any).mockReturnValue(mockStore);
  });

  it('renders an empty state when no bundles are present', () => {
    (useWorkbenchStore as any).mockReturnValue({
      ...mockStore,
      result_internal_bundle: null,
      result_traveler_bundle: null,
    });

    render(<OutputPanel tripId="TRIP-123" />);
    expect(screen.getByText(/No traveler-ready output yet/i)).toBeInTheDocument();
  });

  it('routes quote-ready trips to quote assessment from the derived output preview', () => {
    (useWorkbenchStore as any).mockReturnValue({
      ...mockStore,
      result_internal_bundle: null,
      result_traveler_bundle: null,
    });

    render(
      <OutputPanel
        tripId="TRIP-123"
        trip={{
          id: 'TRIP-123',
          strategy: {
            session_goal: 'Plan Bali',
            priority_sequence: ['Keep budget anchored to 75000'],
            tonal_guardrails: ['Stay concise'],
            risk_flags: [],
            suggested_opening: 'Here’s the options plan for Bali.',
            exit_criteria: ['Options are structured and easy to compare'],
            next_action: 'PROCEED_INTERNAL_DRAFT',
            assumptions: [],
            suggested_tone: 'professional',
          } as any,
          decision: {
            decision_state: 'PROCEED_INTERNAL_DRAFT',
          } as any,
        } as any}
      />
    );

    expect(screen.getByText(/derived preview from the current strategy and decision/i)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Open Quote Assessment/i })).toHaveAttribute(
      'href',
      '/trips/TRIP-123/decision'
    );
  });

  it('renders a derived output preview when the persisted bundle is missing', () => {
    (useWorkbenchStore as any).mockReturnValue({
      ...mockStore,
      result_internal_bundle: null,
      result_traveler_bundle: null,
    });

    render(
      <OutputPanel
        tripId="TRIP-123"
        trip={{
          id: 'TRIP-123',
          destination: 'Bali',
          strategy: {
            session_goal: 'Prepare a clear options plan for Bali while keeping budget aligned.',
            priority_sequence: ['Check origin and destination together'],
            tonal_guardrails: ['Keep the options concise and decision-friendly'],
            risk_flags: [],
            suggested_opening: 'Here’s the options plan for Bali.',
            exit_criteria: ['Options are structured and easy to compare'],
            next_action: 'PROCEED_INTERNAL_DRAFT',
            assumptions: [],
            suggested_tone: 'professional',
          } as any,
          decision: {
            decision_state: 'PROCEED_TRAVELER_SAFE',
            operating_mode: 'normal_intake',
            follow_up_questions: [],
          } as any,
        } as any}
      />
    );

    expect(screen.getByText(/derived preview from the current strategy and decision/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Here’s the options plan for Bali\./i).length).toBeGreaterThanOrEqual(2);
    expect(screen.getByRole('button', { name: /Copy Customer Draft/i })).toBeInTheDocument();
  });

  it('renders agent and customer bundles side-by-side', () => {
    render(<OutputPanel tripId="TRIP-123" />);

    // Internal bundle
    expect(screen.getByText('For You (Agent)')).toBeInTheDocument();
    expect(screen.getByText('Internal Context Test')).toBeInTheDocument();
    expect(screen.getByText('Internal Message Test')).toBeInTheDocument();
    expect(screen.getByText('Constraint 1')).toBeInTheDocument();

    // Traveler bundle
    expect(screen.getByText('For Customer')).toBeInTheDocument();
    expect(screen.getByText('Traveler Context Test')).toBeInTheDocument();
    expect(screen.getByText('Traveler Message Test')).toBeInTheDocument();
    expect(screen.getByText('Any questions?')).toBeInTheDocument();
  });

  it('toggles debug representation', () => {
    vi.stubEnv('NEXT_PUBLIC_ALLOW_DEBUG_JSON', 'true');
    const setDebugRawJsonMock = vi.fn();
    (useWorkbenchStore as any).mockReturnValue({
      ...mockStore,
      setDebugRawJson: setDebugRawJsonMock,
    });

    render(<OutputPanel tripId="TRIP-123" />);

    const button = screen.getByRole('button', { name: /Show Technical Data/i });
    expect(button).toBeInTheDocument();

    fireEvent.click(button);
    expect(setDebugRawJsonMock).toHaveBeenCalledWith(true);
  });

  it('shows JSON data when debug_raw_json is true', () => {
    vi.stubEnv('NEXT_PUBLIC_ALLOW_DEBUG_JSON', 'true');
    (useWorkbenchStore as any).mockReturnValue({
      ...mockStore,
      debug_raw_json: true,
    });

    render(<OutputPanel tripId="TRIP-123" />);
    
    expect(screen.getByRole('button', { name: /Hide Technical Data/i })).toBeInTheDocument();
    const elements = screen.getAllByText(/Internal Context Test/);
    expect(elements.length).toBeGreaterThan(1); // One in UI, one in JSON
  });

  it('keeps customer draft copy enabled when review status is undefined', () => {
    render(<OutputPanel tripId="TRIP-123" trip={{ id: "TRIP-123" } as any} />);
    const draftButton = screen.getByRole('button', { name: /Copy Customer Draft/i });
    expect(draftButton).not.toBeDisabled();
  });

  it('blocks customer draft copy with policy reason when approval is required', () => {
    render(
      <OutputPanel
        tripId="TRIP-123"
        trip={{
          id: "TRIP-123",
          analytics: {
            approvalRequiredForSend: true,
            sendPolicyReason: "Confidence below threshold (0.75)",
          },
        } as any}
      />
    );
    expect(screen.getByText(/Customer draft blocked by policy/i)).toBeInTheDocument();
    const draftButton = screen.getByRole('button', { name: /Copy Customer Draft/i });
    expect(draftButton).toBeDisabled();
    expect(draftButton).toHaveAttribute('title', expect.stringContaining('Confidence below threshold'));
  });

  it('copies the customer-safe draft to the clipboard', async () => {
    const clipboardSpy = vi.mocked(safeWriteClipboardText);

    render(<OutputPanel tripId="TRIP-123" />);

    fireEvent.click(screen.getByRole('button', { name: /Copy Customer Draft/i }));

    expect(clipboardSpy).toHaveBeenCalledWith(expect.stringContaining('Traveler Message Test'));
    expect(await screen.findByText(/Customer draft copied/i)).toBeInTheDocument();
  });

  it('keeps Technical Data blocked by default policy', () => {
    render(<OutputPanel tripId="TRIP-123" />);
    expect(screen.getByText(/hidden by privacy policy/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Show Technical Data/i })).toBeDisabled();
  });
});
