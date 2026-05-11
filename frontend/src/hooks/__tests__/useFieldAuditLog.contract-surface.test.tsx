import { renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';
import { useAllAuditLogs } from '../useFieldAuditLog';

describe('useAllAuditLogs', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('loads all versioned trip audit logs from localStorage', async () => {
    localStorage.setItem('trip_audit:v1:trip-1', JSON.stringify({ tripId: 'trip-1', changes: [], lastModified: '2026-05-11T00:00:00.000Z', version: 0 }));
    localStorage.setItem('unrelated:v1', JSON.stringify({ tripId: 'ignored' }));

    const { result } = renderHook(() => useAllAuditLogs());

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.logs).toEqual({
      'trip-1': { tripId: 'trip-1', changes: [], lastModified: '2026-05-11T00:00:00.000Z', version: 0 },
    });
  });
});
