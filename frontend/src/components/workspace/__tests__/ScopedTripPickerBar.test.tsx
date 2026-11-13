import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ScopedTripPickerBar } from '../ScopedTripPickerBar';

const mockUseTrips = vi.fn();

vi.mock('@/hooks/useTrips', () => ({
  useTrips: (params: unknown) => mockUseTrips(params),
}));

describe('ScopedTripPickerBar', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseTrips.mockReturnValue({
      data: [
        {
          id: 'trip_doc_1',
          destination: 'Kyoto',
          stage: 'proposal',
          status: 'assigned',
          type: 'custom',
          state: 'blue',
          age: '1d',
          updated_at: '2026-11-11T00:00:00Z',
        },
      ],
      total: 1,
      isLoading: false,
    });
  });

  it('requests narrow scope by default and switches cleanly to all workspace trips', () => {
    const onSelectTrip = vi.fn();
    render(
      <ScopedTripPickerBar
        label='Trip'
        selectId='docs-test-select'
        selectTestId='docs-test-select'
        scopedLabel='Documents & Upload-Ready'
        allLabel='All Workspace Trips'
        scope='documents'
        selectedTripId=''
        onSelectTrip={onSelectTrip}
      />
    );

    expect(mockUseTrips).toHaveBeenCalledWith(
      expect.objectContaining({ view: 'workspace', scope: 'documents', enabled: true })
    );
    expect(onSelectTrip).toHaveBeenCalledWith(
      'trip_doc_1',
      expect.objectContaining({ id: 'trip_doc_1', destination: 'Kyoto' })
    );

    fireEvent.click(screen.getByRole('button', { name: /All Workspace Trips/i }));
    expect(mockUseTrips).toHaveBeenLastCalledWith(
      expect.objectContaining({ view: 'workspace', enabled: true })
    );
  });
});
