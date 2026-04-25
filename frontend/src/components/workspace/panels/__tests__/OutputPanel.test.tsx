import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import OutputPanel from '../OutputPanel';
import { useWorkbenchStore } from '@/stores/workbench';

// Mock dependencies
vi.mock('@/stores/workbench', () => ({
  useWorkbenchStore: vi.fn(),
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
    (useWorkbenchStore as any).mockReturnValue(mockStore);
  });

  it('renders an empty state when no bundles are present', () => {
    (useWorkbenchStore as any).mockReturnValue({
      ...mockStore,
      result_internal_bundle: null,
      result_traveler_bundle: null,
    });

    render(<OutputPanel tripId="TRIP-123" />);
    expect(screen.getByText(/No output data for trip TRIP-123/i)).toBeInTheDocument();
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
    (useWorkbenchStore as any).mockReturnValue({
      ...mockStore,
      debug_raw_json: true,
    });

    render(<OutputPanel tripId="TRIP-123" />);
    
    expect(screen.getByRole('button', { name: /Hide Technical Data/i })).toBeInTheDocument();
    const elements = screen.getAllByText(/Internal Context Test/);
    expect(elements.length).toBeGreaterThan(1); // One in UI, one in JSON
  });

  it('keeps send enabled when review status is undefined', () => {
    render(<OutputPanel tripId="TRIP-123" trip={{ id: "TRIP-123" } as any} />);
    const sendButton = screen.getByRole('button', { name: /Send to Customer/i });
    expect(sendButton).not.toBeDisabled();
  });

  it('blocks send with policy reason when approval is required', () => {
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
    expect(screen.getByText(/Send blocked by policy/i)).toBeInTheDocument();
    const sendButton = screen.getByRole('button', { name: /Send to Customer/i });
    expect(sendButton).toBeDisabled();
    expect(sendButton).toHaveAttribute('title', expect.stringContaining('Confidence below threshold'));
  });
});
