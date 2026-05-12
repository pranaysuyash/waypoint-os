import { act, renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useAllAuditLogs, useFieldAuditLog } from '../useFieldAuditLog';

describe('useAllAuditLogs', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.unstubAllEnvs();
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

  it('redacts sensitive values in export payload by default', async () => {
    const { result } = renderHook(() =>
      useFieldAuditLog({ tripId: 'trip-2', userId: 'user-1', userName: 'Jane Doe' })
    );

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    act(() => {
      result.current.logChange('passport_number' as any, 'update', 'A1234567', 'B7654321');
    });

    await waitFor(() => {
      expect(result.current.getChanges()).toHaveLength(1);
    });
    const exported = result.current.exportChanges();

    expect(exported).toContain('[REDACTED]');
    expect(exported).not.toContain('A1234567');
    expect(exported).not.toContain('B7654321');
  });
});
