import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useDraftAutosave } from '../useDraftAutosave';

describe('useDraftAutosave', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('detects existing draft in localStorage on mount', () => {
    const draftPayload = {
      data: { raw_note: 'Flight to Tokyo with family', budget: '5000' },
      timestamp: Date.now(),
    };
    localStorage.setItem('waypoint_draft_inquiry', JSON.stringify(draftPayload));

    const { result } = renderHook(() =>
      useDraftAutosave({
        key: 'inquiry',
        data: { raw_note: '', budget: '' },
      }),
    );

    expect(result.current.hasSavedDraft).toBe(true);
    expect(result.current.savedDraft).toEqual(draftPayload.data);
  });

  it('debounces autosave when form data changes', () => {
    const { rerender } = renderHook(
      ({ data }) =>
        useDraftAutosave({
          key: 'inquiry',
          data,
          debounceMs: 500,
        }),
      {
        initialProps: { data: { raw_note: '', budget: '' } },
      },
    );

    // Update form data
    rerender({ data: { raw_note: 'Luxury safari in Kenya', budget: '15000' } });

    // Should not save immediately
    expect(localStorage.getItem('waypoint_draft_inquiry')).toBeNull();

    // Fast-forward debounce timer
    act(() => {
      vi.advanceTimersByTime(500);
    });

    const stored = JSON.parse(localStorage.getItem('waypoint_draft_inquiry') || '{}');
    expect(stored.data).toEqual({ raw_note: 'Luxury safari in Kenya', budget: '15000' });
  });

  it('clears draft from localStorage when clearDraft is called', () => {
    localStorage.setItem(
      'waypoint_draft_inquiry',
      JSON.stringify({ data: { raw_note: 'Test' }, timestamp: Date.now() }),
    );

    const { result } = renderHook(() =>
      useDraftAutosave({
        key: 'inquiry',
        data: { raw_note: 'Test' },
      }),
    );

    expect(result.current.hasSavedDraft).toBe(true);

    act(() => {
      result.current.clearDraft();
    });

    expect(result.current.hasSavedDraft).toBe(false);
    expect(result.current.savedDraft).toBeNull();
    expect(localStorage.getItem('waypoint_draft_inquiry')).toBeNull();
  });
});
