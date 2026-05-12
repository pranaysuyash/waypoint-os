import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { SafetyPanel } from '../SafetyPanel';
import { useWorkbenchStore } from '@/stores/workbench';

vi.mock('@/stores/workbench', () => ({
  useWorkbenchStore: vi.fn(),
}));

describe('SafetyPanel privacy gating', () => {
  const baseStore = {
    result_safety: {
      leakage_passed: true,
      leakage_errors: [],
      strict_leakage: false,
    },
    result_traveler_bundle: {
      system_context: 'Traveler context',
      user_message: 'Traveler message',
      follow_up_sequence: [],
    },
    result_internal_bundle: {
      internal_notes: 'Internal notes',
    },
    debug_raw_json: false,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.unstubAllEnvs();
    (useWorkbenchStore as unknown as { mockReturnValue: (value: unknown) => void }).mockReturnValue(baseStore);
  });

  it('keeps diagnostic data blocked by default policy', () => {
    render(<SafetyPanel tripId="trip-1" />);

    expect(screen.getByText(/hidden by privacy policy/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Show Diagnostic Data/i })).toBeDisabled();
  });

  it('shows diagnostic data only in secure debug mode', () => {
    vi.stubEnv('NEXT_PUBLIC_ALLOW_DEBUG_JSON', 'true');
    render(<SafetyPanel tripId="trip-1" />);

    const toggle = screen.getByRole('button', { name: /Show Diagnostic Data/i });
    expect(toggle).not.toBeDisabled();
    fireEvent.click(toggle);

    expect(screen.getAllByText(/Traveler context/i).length).toBeGreaterThan(1);
    expect(screen.getByText(/Internal notes/i)).toBeInTheDocument();
  });
});
