import { afterEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import AuditPage from '../PageClient';

vi.mock('@/hooks/useClientDate', () => ({
  ClientDateTime: ({ value }: { value: string }) => <span>{value}</span>,
}));

describe('AuditPage', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders audit events from the entries contract returned by the backend', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo) => {
        const url = String(input);
        if (url.includes('event_type=routing_health_alert_triage')) {
          return {
            ok: true,
            json: async () => ({ ok: true, items: [] }),
          } as Response;
        }
        if (url.includes('event_type=routing_health_alert_suppressed')) {
          return {
            ok: true,
            json: async () => ({ ok: true, items: [] }),
          } as Response;
        }
        if (url.includes('event_type=routing_health_alert')) {
          return {
            ok: true,
            json: async () => ({ ok: true, items: [] }),
          } as Response;
        }
        if (url.includes('event_type=routing_health_paging_alert')) {
          return {
            ok: true,
            json: async () => ({ ok: true, items: [] }),
          } as Response;
        }
        if (url.includes('event_type=routing_health_paging_alert_suppressed')) {
          return {
            ok: true,
            json: async () => ({ ok: true, items: [] }),
          } as Response;
        }
        return {
          ok: true,
          json: async () => ({
            ok: true,
            entries: [
              {
                id: 'audit-1',
                type: 'trip.stage.changed',
                user_id: 'agent-1',
                timestamp: '2026-06-23T02:00:00.000Z',
                details: { from: 'intake', to: 'strategy' },
              },
            ],
          }),
        } as Response;
      })
    );

    render(<AuditPage />);

    await waitFor(() => expect(screen.getByText('trip.stage.changed')).toBeInTheDocument());
    expect(screen.getByText('2026-06-23T02:00:00.000Z')).toBeInTheDocument();
    expect(screen.getByText(/\"from\":\"intake\"/)).toBeInTheDocument();
    expect(screen.getByText(/\"to\":\"strategy\"/)).toBeInTheDocument();
  });

  it('surfaces routing health alerts and latest triage state in a dedicated operator panel', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo) => {
        const url = String(input);
        if (url.includes('event_type=routing_health_alert_triage')) {
          return {
            ok: true,
            json: async () => ({
              ok: true,
              items: [
                {
                  id: 'triage-existing',
                  type: 'routing_health_alert_triage',
                  user_id: 'system',
                  timestamp: '2026-07-01T08:02:00.000Z',
                  details: {
                    target_event_id: 'routing-alert-1',
                    action: 'acknowledge',
                    note: 'Already noted',
                  },
                },
              ],
            }),
          } as Response;
        }
        if (url.includes('event_type=routing_health_alert_suppressed')) {
          return {
            ok: true,
            json: async () => ({ ok: true, items: [] }),
          } as Response;
        }
        if (url.includes('event_type=routing_health_alert_paging')) {
          return {
            ok: true,
            json: async () => ({ ok: true, items: [] }),
          } as Response;
        }
        if (url.includes('event_type=routing_health_alert')) {
          return {
            ok: true,
            json: async () => ({
              ok: true,
              items: [
                {
                  id: 'routing-alert-1',
                  type: 'routing_health_alert',
                  user_id: 'system',
                  timestamp: '2026-07-01T08:00:00.000Z',
                  details: {
                    trip_id: 'trip-abc',
                    status: 'critical',
                    workflow: 'extraction',
                    workflow_unit_id: 'workflow-1',
                    metric: 'fallback_trigger_rate',
                    min_occurrences: 3,
                    window_minutes: 60,
                  },
                },
              ],
            }),
          } as Response;
        }
        if (url.includes('event_type=routing_health_paging_alert_suppressed')) {
          return {
            ok: true,
            json: async () => ({ ok: true, items: [] }),
          } as Response;
        }
        if (url.includes('event_type=routing_health_paging_alert')) {
          return {
            ok: true,
            json: async () => ({
              ok: true,
              items: [
                {
                  id: 'paging-alert-1',
                  type: 'routing_health_paging_alert',
                  user_id: 'system',
                  timestamp: '2026-07-01T09:00:00.000Z',
                  details: {
                    trip_id: 'trip-abc',
                    status: 'critical',
                    occurrence_index: 4,
                    sustained_window_seconds: 3600,
                    paging_cooldown_seconds: 3600,
                  },
                },
              ],
            }),
          } as Response;
        }
        return {
          ok: true,
          json: async () => ({ ok: true, entries: [] }),
        } as Response;
      })
    );

    render(<AuditPage />);

    await waitFor(() =>
      expect(screen.getByText('Routing health alerts')).toBeInTheDocument()
    );
    expect(
      screen.getByText(
        'status:critical · trip:trip-abc · workflow:extraction · metric:fallback_trigger_rate · min_occurrences:3 · window:60m'
      )
    ).toBeInTheDocument();
    expect(screen.getByText('status:critical · trip:trip-abc · occurrence:4 · sustained_window:3600s · cooldown:3600s')).toBeInTheDocument();
    expect(screen.getByText('Triaged: acknowledge by system')).toBeInTheDocument();
  });

  it('supports posting routing health alert triage actions', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo, init?: RequestInit) => {
      const url = String(input);
      const method = init?.method ?? 'GET';

      if (method === 'POST' && url.includes('/legacy_ops/audit/routing-alert-1/triage')) {
        const requestBody = JSON.parse(
          typeof init?.body === 'string' ? init.body : '{}'
        );
        return {
          ok: true,
          json: async () => ({
            success: true,
            event_id: 'routing-alert-1',
            target_event_id: 'routing-alert-1',
            action: requestBody.action,
            triage_event: {
              id: 'triage-1',
              type: 'routing_health_alert_triage',
              user_id: 'agency_test',
              timestamp: '2026-07-01T10:00:00.000Z',
              details: {
                target_event_id: 'routing-alert-1',
                action: requestBody.action,
                note: requestBody.note,
              },
            },
          }),
        } as Response;
      }
      if (url.includes('event_type=routing_health_alert_triage')) {
        return {
          ok: true,
          json: async () => ({ ok: true, items: [] }),
        } as Response;
      }
      if (url.includes('event_type=routing_health_paging_alert_suppressed')) {
        return {
          ok: true,
          json: async () => ({ ok: true, items: [] }),
        } as Response;
      }
      if (url.includes('event_type=routing_health_alert')) {
        return {
          ok: true,
          json: async () => ({
            ok: true,
            items: [
              {
                id: 'routing-alert-1',
                type: 'routing_health_alert',
                user_id: 'system',
                timestamp: '2026-07-01T08:00:00.000Z',
                details: {
                  trip_id: 'trip-abc',
                  status: 'critical',
                  workflow: 'extraction',
                  workflow_unit_id: 'workflow-1',
                  metric: 'fallback_trigger_rate',
                  min_occurrences: 3,
                  window_minutes: 60,
                },
              },
            ],
          }),
        } as Response;
      }
      if (url.includes('event_type=routing_health_paging_alert')) {
        return {
          ok: true,
          json: async () => ({ ok: true, items: [] }),
        } as Response;
      }
      return {
        ok: true,
        json: async () => ({ ok: true, entries: [] }),
      } as Response;
    });

    vi.stubGlobal('fetch', fetchMock);

    render(<AuditPage />);

    await waitFor(() =>
      expect(screen.getByRole('heading', { name: 'Routing health alerts' })).toBeInTheDocument()
    );

    const noteInput = screen.getByLabelText('Note', {
      selector: 'input#note-routing-alert-1',
    });
    fireEvent.change(noteInput, { target: { value: 'Escalate to ops queue' } });

    const escalateButton = screen.getByRole('button', { name: /Escalate/i });
    fireEvent.click(escalateButton);

    await waitFor(() =>
      expect(screen.getByText('Triaged: escalate by agency_test')).toBeInTheDocument()
    );

    const triagePostCall = fetchMock.mock.calls.find(
      ([calledUrl, init]) =>
        String(calledUrl).includes('/legacy_ops/audit/routing-alert-1/triage') &&
        (init?.method ?? 'GET') === 'POST'
    );
    expect(triagePostCall).toBeDefined();
    const postedBody = JSON.parse(String(triagePostCall?.[1]?.body ?? '{}'));
    expect(postedBody).toEqual({
      action: 'escalate',
      note: 'Escalate to ops queue',
    });
  });

  it('supports batch triage across selected routing-health alerts', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo, init?: RequestInit) => {
      const url = String(input);
      const method = init?.method ?? 'GET';

      if (method === 'POST' && url.includes('/legacy_ops/audit/routing-health/batch-triage')) {
        const body = JSON.parse(typeof init?.body === 'string' ? init.body : '[]');
        return {
          ok: true,
          json: async () => ({
            success: true,
            requested: body.length,
            succeeded: body.length,
            failed: 0,
            results: body.map((item: { event_id: string; action: string; note?: string }) => ({
              event_id: item.event_id,
              success: true,
              action: item.action,
              note: item.note ?? '',
              triage_event: {
                id: `triage-${item.event_id}`,
                type: 'routing_health_alert_triage',
                user_id: 'agency_test',
                timestamp: '2026-07-01T10:00:00.000Z',
                details: {
                  target_event_id: item.event_id,
                  action: item.action,
                  note: item.note ?? '',
                },
              },
              error: null,
            })),
          }),
        } as Response;
      }

      if (url.includes('event_type=routing_health_alert_triage')) {
        return {
          ok: true,
          json: async () => ({ ok: true, items: [] }),
        } as Response;
      }
      if (url.includes('event_type=routing_health_paging_alert_suppressed')) {
        return {
          ok: true,
          json: async () => ({ ok: true, items: [] }),
        } as Response;
      }
      if (url.includes('event_type=routing_health_alert')) {
        return {
          ok: true,
          json: async () => ({
            ok: true,
            items: [
              {
                id: 'routing-alert-1',
                type: 'routing_health_alert',
                user_id: 'system',
                timestamp: '2026-07-01T08:00:00.000Z',
                details: {
                  trip_id: 'trip-abc',
                  status: 'warning',
                  workflow: 'extraction',
                  min_occurrences: 3,
                  window_minutes: 60,
                },
              },
              {
                id: 'routing-alert-2',
                type: 'routing_health_alert',
                user_id: 'system',
                timestamp: '2026-07-01T08:01:00.000Z',
                details: {
                  trip_id: 'trip-def',
                  status: 'critical',
                  workflow: 'analysis',
                  min_occurrences: 2,
                  window_minutes: 30,
                },
              },
            ],
          }),
        } as Response;
      }
      if (url.includes('event_type=routing_health_paging_alert')) {
        return {
          ok: true,
          json: async () => ({ ok: true, items: [] }),
        } as Response;
      }
      return {
        ok: true,
        json: async () => ({ ok: true, entries: [] }),
      } as Response;
    });

    vi.stubGlobal('fetch', fetchMock);

    render(<AuditPage />);

    await waitFor(() =>
      expect(screen.getByRole('heading', { name: 'Routing health alerts' })).toBeInTheDocument()
    );

    const first = screen.getByLabelText('Select alert routing-alert-1');
    const second = screen.getByLabelText('Select alert routing-alert-2');
    fireEvent.click(first);
    fireEvent.click(second);

    const actionSelect = screen.getByLabelText('Action');
    fireEvent.change(actionSelect, { target: { value: 'close' } });
    fireEvent.change(screen.getByLabelText('Note', { selector: 'input#batch-note' }), {
      target: { value: 'Batch note for review' },
    });

    const runButton = screen.getByRole('button', { name: /Run batch triage/i });
    fireEvent.click(runButton);

    await waitFor(() => expect(screen.getByText(/batch result:/i)).toBeInTheDocument());

    const batchCall = fetchMock.mock.calls.find(
      ([calledUrl, init]) =>
        String(calledUrl).includes('/legacy_ops/audit/routing-health/batch-triage') &&
        (init?.method ?? 'GET') === 'POST',
    );
    expect(batchCall).toBeDefined();
    const postedBody = JSON.parse(String(batchCall?.[1]?.body ?? '[]'));
    expect(Array.isArray(postedBody)).toBe(true);
    expect(postedBody).toEqual([
      { event_id: 'routing-alert-1', action: 'close', note: 'Batch note for review' },
      { event_id: 'routing-alert-2', action: 'close', note: 'Batch note for review' },
    ]);
  });

  it('supports paging-alert suppression actions', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo, init?: RequestInit) => {
      const url = String(input);
      const method = init?.method ?? 'GET';

      if (method === 'POST' && url.includes('/legacy_ops/audit/paging-alert-1/suppress-routing-health-paging')) {
        return {
          ok: true,
          json: async () => ({
            success: true,
            event_id: 'paging-alert-1',
            suppression_event: {
              id: 'suppressed-1',
              type: 'routing_health_paging_alert_suppressed',
              user_id: 'agency_test',
              timestamp: '2026-07-01T10:00:00.000Z',
              details: {
                target_event_id: 'paging-alert-1',
                target_event_type: 'routing_health_paging_alert',
                suppress_for_minutes: 60,
                note: 'Muted for 60',
              },
            },
          }),
        } as Response;
      }
      if (url.includes('event_type=routing_health_alert_triage')) {
        return {
          ok: true,
          json: async () => ({ ok: true, items: [] }),
        } as Response;
      }
      if (url.includes('event_type=routing_health_paging_alert_suppressed')) {
        return {
          ok: true,
          json: async () => ({ ok: true, items: [] }),
        } as Response;
      }
      if (url.includes('event_type=routing_health_alert')) {
        return {
          ok: true,
          json: async () => ({ ok: true, items: [] }),
        } as Response;
      }
      if (url.includes('event_type=routing_health_paging_alert')) {
        return {
          ok: true,
          json: async () => ({
            ok: true,
            items: [
              {
                id: 'paging-alert-1',
                type: 'routing_health_paging_alert',
                user_id: 'system',
                timestamp: '2026-07-01T09:00:00.000Z',
                details: {
                  trip_id: 'trip-abc',
                  status: 'critical',
                  occurrence_index: 4,
                  sustained_window_seconds: 3600,
                  paging_cooldown_seconds: 3600,
                },
              },
            ],
          }),
        } as Response;
      }
      return {
        ok: true,
        json: async () => ({ ok: true, entries: [] }),
      } as Response;
    });

    vi.stubGlobal('fetch', fetchMock);

    render(<AuditPage />);

    await waitFor(() =>
      expect(screen.getByText('Routing health paging alerts')).toBeInTheDocument()
    );

    const minutesInput = screen.getByLabelText('Suppress for (minutes)');
    const noteInput = screen.getByLabelText('Suppression note');
    fireEvent.change(minutesInput, { target: { value: '60' } });
    fireEvent.change(noteInput, { target: { value: 'Muted for 60' } });

    const suppressButton = screen.getByRole('button', { name: /Suppress paging/i });
    fireEvent.click(suppressButton);

    const suppressionCall = fetchMock.mock.calls.find(
      ([calledUrl, init]) =>
        String(calledUrl).includes('/legacy_ops/audit/paging-alert-1/suppress-routing-health-paging') &&
        (init?.method ?? 'GET') === 'POST',
    );
    expect(suppressionCall).toBeDefined();
    const postedBody = JSON.parse(String(suppressionCall?.[1]?.body ?? '{}'));
    expect(postedBody).toEqual({ suppress_for_minutes: 60, note: 'Muted for 60' });
  });

  it('supports CSV and JSON evidence export from routing-health panel', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo, init?: RequestInit) => {
      const url = String(input);
      const method = init?.method ?? 'GET';

      if (method === 'GET' && url.includes('/legacy_ops/audit/routing-health/export')) {
        if (url.includes('format=csv')) {
          return {
            ok: true,
            text: async () => 'id,type\n1,routing_health_alert',
            headers: {
              get: () => 'text/csv',
            },
          } as unknown as Response;
        }
        return {
          ok: true,
          json: async () => ({
            generated_at: '2026-07-01T10:00:00.000Z',
            total: 1,
            items: [],
          }),
        } as Response;
      }

      if (url.includes('event_type=routing_health_alert_triage')) {
        return {
          ok: true,
          json: async () => ({ ok: true, items: [] }),
        } as Response;
      }
      if (url.includes('event_type=routing_health_paging_alert_suppressed')) {
        return {
          ok: true,
          json: async () => ({ ok: true, items: [] }),
        } as Response;
      }
      if (url.includes('event_type=routing_health_alert')) {
        return {
          ok: true,
          json: async () => ({ ok: true, items: [] }),
        } as Response;
      }
      if (url.includes('event_type=routing_health_paging_alert')) {
        return {
          ok: true,
          json: async () => ({ ok: true, items: [] }),
        } as Response;
      }
      return {
        ok: true,
        json: async () => ({ ok: true, entries: [] }),
      } as Response;
    });

    vi.stubGlobal('fetch', fetchMock);

    const createObjectURL = vi.spyOn(window.URL, 'createObjectURL').mockReturnValue('blob:test');
    const revokeObjectURL = vi.spyOn(window.URL, 'revokeObjectURL').mockImplementation(() => undefined);

    render(<AuditPage />);

    await waitFor(() => expect(screen.getByText('Routing-health evidence export')).toBeInTheDocument());

    const exportButton = screen.getByRole('button', { name: /Export evidence/i });
    fireEvent.click(exportButton);

    const jsonCall = fetchMock.mock.calls.find(
      ([calledUrl, init]) =>
        String(calledUrl).includes('/legacy_ops/audit/routing-health/export') &&
        (init?.method ?? 'GET') === 'GET' &&
        String(calledUrl).includes('format=json')
    );
    expect(jsonCall).toBeDefined();

    const formatSelect = screen.getByLabelText('Format');
    fireEvent.change(formatSelect, { target: { value: 'csv' } });
    fireEvent.click(exportButton);

    const csvCall = fetchMock.mock.calls.find(
      ([calledUrl, init]) =>
        String(calledUrl).includes('/legacy_ops/audit/routing-health/export') &&
        (init?.method ?? 'GET') === 'GET' &&
        String(calledUrl).includes('format=csv')
    );
    expect(csvCall).toBeDefined();

    await waitFor(() => expect(createObjectURL).toHaveBeenCalledTimes(2));
    await waitFor(() => expect(revokeObjectURL).toHaveBeenCalled());
  });

  it('supports pause/resume live refresh controls', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo) => {
      const url = String(input);
      if (url.includes('event_type=')) {
        return {
          ok: true,
          json: async () => ({ ok: true, items: [] }),
        } as Response;
      }
      return {
        ok: true,
        json: async () => ({ ok: true, entries: [] }),
      } as Response;
    });

    vi.stubGlobal('fetch', fetchMock);

    render(<AuditPage />);

    const toggleButton = await screen.findByRole('button', { name: /pause live refresh/i });
    expect(toggleButton).toBeInTheDocument();

    fireEvent.click(toggleButton);
    expect(screen.getByRole('button', { name: /Enable live refresh/i })).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /Enable live refresh/i }));
    expect(screen.getByRole('button', { name: /Pause live refresh/i })).toBeInTheDocument();
  });

  it('supports manual refresh action', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo) => {
      const url = String(input);
      if (url.includes('event_type=')) {
        return {
          ok: true,
          json: async () => ({ ok: true, items: [] }),
        } as Response;
      }
      return {
        ok: true,
        json: async () => ({ ok: true, entries: [] }),
      } as Response;
    });

    vi.stubGlobal('fetch', fetchMock);

    render(<AuditPage />);

    const refreshButton = await screen.findByRole('button', { name: /Refresh now/i });
    const initialFetches = fetchMock.mock.calls.length;

    fireEvent.click(refreshButton);

    await waitFor(() => expect(fetchMock.mock.calls.length).toBeGreaterThan(initialFetches));
  });

  it('shows the empty state when the backend returns no entries', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo) => {
        const url = String(input);
        if (url.includes('event_type=')) {
          return {
            ok: true,
            json: async () => ({ ok: true, items: [] }),
          } as Response;
        }
        return {
          ok: true,
          json: async () => ({ ok: true, entries: [] }),
        } as Response;
      })
    );

    render(<AuditPage />);

    await waitFor(() => expect(screen.getByText('No audit events recorded yet.')).toBeInTheDocument());
  });
});
