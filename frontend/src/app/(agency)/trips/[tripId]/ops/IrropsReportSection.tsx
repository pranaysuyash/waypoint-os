'use client';

import { useCallback, useEffect, useState } from 'react';
import { AlertTriangle, CheckCircle2, Send } from 'lucide-react';
import type { Trip } from '@/lib/api-client';

// FND-0405 (2026-11-07): operator entry point for the IRROPS report endpoint
// (POST /api/v1/disruptions/{trip_id}/report) — until now it was curl-only.
// Shows the trip's active disruption (radar-shaped active_disruption) with a
// Resolve action (archives to disruption_history) and a compact report form.

const TRIGGER_KINDS = ['cancellation', 'delay', 'schedule_change', 'diversion', 'denial_of_boarding'] as const;
type TriggerKind = (typeof TRIGGER_KINDS)[number];

interface ActiveDisruption {
  disruption_type?: string;
  flight_number?: string;
  severity?: string;
  trigger_kind?: string;
  delay_minutes?: number;
  source?: string;
  status?: string;
}

export default function IrropsReportSection({ tripId }: { tripId: string }) {
  const [triggerKind, setTriggerKind] = useState<TriggerKind>('delay');
  const [flightRef, setFlightRef] = useState('');
  const [delayMinutes, setDelayMinutes] = useState('');
  const [notes, setNotes] = useState('');
  const [active, setActive] = useState<ActiveDisruption | null>(null);
  const [loading, setLoading] = useState(true);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isResolving, setIsResolving] = useState(false);

  const loadState = useCallback(async () => {
    try {
      const res = await fetch(`/api/v1/trips/${encodeURIComponent(tripId)}`);
      if (!res.ok) throw new Error(`Trip unavailable (${res.status})`);
      const data = await res.json();
      const d = data?.active_disruption;
      setActive(d && d.status !== 'RESOLVED' ? d : null);
      setError(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Disruption state unavailable.');
    } finally {
      setLoading(false);
    }
  }, [tripId]);

  useEffect(() => {
    void loadState();
  }, [loadState]);

  const handleReport = async () => {
    setError(null);
    setFeedback(null);
    if (!flightRef.trim()) {
      setError('Flight reference is required.');
      return;
    }
    if (triggerKind === 'delay' && (!delayMinutes || Number(delayMinutes) < 0)) {
      setError('Delay reports need delay_minutes.');
      return;
    }
    setIsSubmitting(true);
    try {
      const res = await fetch(`/api/v1/disruptions/${encodeURIComponent(tripId)}/report`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          trigger_kind: triggerKind,
          flight_ref: flightRef.trim(),
          notes: notes.trim(),
          delay_minutes: triggerKind === 'delay' || delayMinutes ? Number(delayMinutes) || undefined : undefined,
        }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(body?.detail || `Report failed (${res.status})`);
      setActive(body.disruption);
      setFlightRef('');
      setDelayMinutes('');
      setNotes('');
      setFeedback('Disruption reported — it is now on the disruption radar.');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Report failed.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleResolve = async () => {
    setError(null);
    setIsResolving(true);
    try {
      const res = await fetch(`/api/v1/disruptions/${encodeURIComponent(tripId)}/resolve`, { method: 'POST' });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(body?.detail || `Resolve failed (${res.status})`);
      setActive(null);
      setFeedback('Disruption resolved and archived to disruption history.');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Resolve failed.');
    } finally {
      setIsResolving(false);
    }
  };

  if (loading) {
    return (
      <div className='p-4 text-ui-sm text-[#8b949e]' data-testid='irrops-section-loading'>
        Loading disruption state…
      </div>
    );
  }

  return (
    <div className='rounded-xl border border-[#30363d] bg-[#0f1115] p-4 space-y-3' data-testid='irrops-section'>
      <div className='flex items-center gap-2'>
        <AlertTriangle className='size-4 text-[#d29922]' />
        <span className='text-ui-sm font-semibold text-[#e6edf3]'>Disruption (IROPS)</span>
      </div>

      {active && (
        <div
          className='rounded-lg border border-[#f85149]/30 bg-[#f85149]/10 p-3 space-y-1'
          data-testid='irrops-active'
        >
          <p className='text-ui-sm font-semibold text-[#f85149]'>
            ACTIVE: {(active.disruption_type || active.trigger_kind || 'disruption').replace(/_/g, ' ')} ·{' '}
            {active.flight_number || 'unknown flight'} · {(active.severity || 'unknown').toUpperCase()}
          </p>
          <p className='text-ui-xs text-[#8b949e]'>
            {active.source === 'operator_reported' ? 'Operator-reported' : 'Provider-observed'}
            {active.delay_minutes ? ` · ${active.delay_minutes} min delay` : ''}
          </p>
          <button
            type='button'
            onClick={handleResolve}
            disabled={isResolving}
            className='mt-1 inline-flex items-center gap-1 px-2.5 py-1 rounded-lg border border-[#3fb950]/40 bg-[#3fb950]/10 text-[11px] font-semibold text-[#3fb950] disabled:opacity-50'
            data-testid='irrops-resolve'
          >
            <CheckCircle2 className='size-3' />
            {isResolving ? 'Resolving…' : 'Mark resolved'}
          </button>
        </div>
      )}

      <div className='space-y-2'>
        <div className='grid grid-cols-2 gap-2'>
          <label className='text-ui-xs text-[#8b949e]'>
            Trigger
            <select
              value={triggerKind}
              onChange={(e) => setTriggerKind(e.target.value as TriggerKind)}
              className='mt-0.5 w-full px-2 py-1.5 bg-[#0f1115] border border-[#30363d] rounded-lg text-ui-xs text-[#e6edf3]'
              data-testid='irrops-trigger-select'
            >
              {TRIGGER_KINDS.map((k) => (
                <option key={k} value={k}>{k.replace(/_/g, ' ')}</option>
              ))}
            </select>
          </label>
          <label className='text-ui-xs text-[#8b949e]'>
            Flight ref
            <input
              value={flightRef}
              onChange={(e) => setFlightRef(e.target.value)}
              placeholder='AI-471'
              className='mt-0.5 w-full px-2 py-1.5 bg-[#0f1115] border border-[#30363d] rounded-lg text-ui-xs text-[#e6edf3] placeholder:text-[#484f58]'
              data-testid='irrops-flight-input'
            />
          </label>
        </div>
        {triggerKind === 'delay' && (
          <label className='block text-ui-xs text-[#8b949e]'>
            Delay (minutes)
            <input
              type='number'
              min={0}
              value={delayMinutes}
              onChange={(e) => setDelayMinutes(e.target.value)}
              placeholder='e.g. 185'
              className='mt-0.5 w-full px-2 py-1.5 bg-[#0f1115] border border-[#30363d] rounded-lg text-ui-xs text-[#e6edf3] placeholder:text-[#484f58]'
              data-testid='irrops-delay-input'
            />
          </label>
        )}
        <label className='block text-ui-xs text-[#8b949e]'>
          Notes
          <input
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder='Carrier notification, rebooking status…'
            className='mt-0.5 w-full px-2 py-1.5 bg-[#0f1115] border border-[#30363d] rounded-lg text-ui-xs text-[#e6edf3] placeholder:text-[#484f58]'
          />
        </label>
        <button
          type='button'
          onClick={handleReport}
          disabled={isSubmitting}
          className='inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#d29922] text-[#1a0e02] text-ui-xs font-semibold disabled:opacity-50'
          data-testid='irrops-report-submit'
        >
          <Send className='size-3' />
          {isSubmitting ? 'Reporting…' : 'Report disruption'}
        </button>
        {error && <p role='alert' className='text-ui-xs text-[#f85149]'>{error}</p>}
        {feedback && <p className='text-ui-xs text-[#3fb950]' data-testid='irrops-feedback'>{feedback}</p>}
      </div>
    </div>
  );
}
