'use client';

import { useCallback, useEffect, useState } from 'react';
import { Bell, Copy, RefreshCw, Wallet } from 'lucide-react';

// FND-0409 (2026-11-18): operator surface for group payment collection —
// per-traveler money truth (tracking-only, ADR-008), payment schedules with
// derived statuses, copyable reminder drafts (dispatch stays operator_manual
// until the DP-04b WhatsApp gate lands), and observed-payment recording.
// Extends the canonical group_booking door; nothing here charges anyone.

interface Milestone {
  label: string;
  due_at?: string | null;
  amount_cents?: number | null;
  status: string;
}

interface PassengerView {
  passenger_id: string;
  name: string;
  email?: string | null;
  share_note?: string | null;
  deposit_share_cents: number;
  paid_cents: number;
  outstanding_cents: number;
  settlement: string;
  status: string;
  schedule: Milestone[];
  recorded_payments: Array<Record<string, unknown>>;
  reminders: Array<Record<string, unknown>>;
}

interface GroupSummary {
  ok: boolean;
  trip_id: string;
  destination?: string | null;
  total_deposit_cents: number;
  collected_cents: number;
  outstanding_cents: number;
  all_satisfied: boolean;
  payment_instructions?: string | null;
  passengers: PassengerView[];
  reminder_drafts: Array<{
    passenger_id: string;
    passenger_name: string;
    outstanding_cents: number;
    trigger: string;
    due_label: string;
    draft_text: string;
    dispatch_channel: string;
  }>;
}

interface Movement {
  amount_cents: string | number;
  method: string;
  reference?: string;
  note?: string;
}

const fmt = (cents: number) =>
  (cents / 100).toLocaleString('en-US', { style: 'currency', currency: 'USD' });

const SETTLEMENT_STYLES: Record<string, string> = {
  paid: 'text-[#3fb950] bg-[#3fb950]/10 border-[#3fb950]/30',
  partial: 'text-[#d29922] bg-[#d29922]/10 border-[#d29922]/30',
  unpaid: 'text-[#8b949e] bg-[#8b949e]/10 border-[#8b949e]/30',
};

const MILESTONE_STYLES: Record<string, string> = {
  paid: 'text-[#3fb950]',
  overdue: 'text-[#f85149]',
  due_soon: 'text-[#d29922]',
  upcoming: 'text-[#8b949e]',
};

export default function GroupCollectionPanel() {
  const [tripId, setTripId] = useState('');
  const [summary, setSummary] = useState<GroupSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  // per-passenger payment form state
  const [payFor, setPayFor] = useState<string | null>(null);
  const [movement, setMovement] = useState<Movement>({ amount_cents: '', method: 'BANK_TRANSFER' });

  const load = useCallback(async (id: string) => {
    if (!id.trim()) return;
    setLoading(true);
    setError(null);
    setFeedback(null);
    try {
      const res = await fetch(`/api/v1/group/${encodeURIComponent(id.trim())}`);
      const data = await res.json().catch(() => null);
      if (!res.ok) {
        setError(data?.detail ?? `Load failed (${res.status})`);
        setSummary(null);
        return;
      }
      setSummary(data);
    } catch {
      setError('Group collection state unavailable.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const prefilled = new URLSearchParams(window.location.search).get('group_trip');
    if (prefilled) {
      setTripId(prefilled);
      void load(prefilled);
    }
  }, [load]);

  const copyDraft = async (passengerId: string, text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedId(passengerId);
      setTimeout(() => setCopiedId(null), 2000);
    } catch {
      // clipboard unavailable — the draft text is visible for manual copy
    }
  };

  const recordPayment = async (passengerId: string) => {
    setError(null);
    setFeedback(null);
    const amount = Number(movement.amount_cents);
    if (!Number.isFinite(amount) || amount <= 0) {
      setError('Payment amount (in cents) must be a positive number.');
      return;
    }
    try {
      const res = await fetch(
        `/api/v1/group/${encodeURIComponent(summary!.trip_id)}/record-payment`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            passenger_id: passengerId,
            amount_cents: amount,
            method: movement.method,
            reference: movement.reference || undefined,
            note: movement.note || undefined,
          }),
        },
      );
      const data = await res.json().catch(() => null);
      if (!res.ok) {
        setError(data?.detail ?? `Record failed (${res.status})`);
        return;
      }
      setFeedback(`Recorded ${fmt(amount)} — tracking only, no charge was made.`);
      setPayFor(null);
      setMovement({ amount_cents: '', method: 'BANK_TRANSFER' });
      await load(summary!.trip_id);
    } catch {
      setError('Record failed.');
    }
  };

  const logReminder = async (passengerId: string) => {
    setError(null);
    setFeedback(null);
    try {
      const res = await fetch(
        `/api/v1/group/${encodeURIComponent(summary!.trip_id)}/log-reminder`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ passenger_id: passengerId, channel: 'operator_manual' }),
        },
      );
      if (!res.ok) {
        const data = await res.json().catch(() => null);
        setError(data?.detail ?? `Log failed (${res.status})`);
        return;
      }
      setFeedback('Reminder send logged.');
      await load(summary!.trip_id);
    } catch {
      setError('Log failed.');
    }
  };

  return (
    <section className='rounded-lg border border-[#30363d] bg-[#0d1117] p-4 mb-6'>
      <h2 className='flex items-center gap-2 text-sm font-semibold text-[#e6edf3] mb-1'>
        <Wallet size={15} className='text-[#d29922]' /> Group collection
      </h2>
      <p className='text-[11px] text-[#8b949e] mb-3'>
        Per-traveler payment shares, schedules, and reminders for group bookings. Tracking only —
        record money you received over your own channels; nothing is charged here.
      </p>

      <div className='flex gap-2 mb-3'>
        <input
          type='text'
          value={tripId}
          onChange={(e) => setTripId(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && load(tripId)}
          placeholder='Trip ID (e.g. from the bookings dossier)'
          className='flex-1 rounded border border-[#30363d] bg-[#161b22] px-2.5 py-1.5 text-xs text-[#e6edf3] placeholder:text-[#6e7681] focus:border-[#58a6ff] focus:outline-none'
        />
        <button
          type='button'
          onClick={() => load(tripId)}
          disabled={loading || !tripId.trim()}
          className='flex items-center gap-1.5 rounded border border-[#30363d] bg-[#161b22] px-3 py-1.5 text-xs font-semibold text-[#e6edf3] hover:bg-[#21262d] disabled:opacity-40'
        >
          <RefreshCw size={12} className={loading ? 'animate-spin' : ''} /> Load
        </button>
      </div>

      {error && <p className='text-[11px] text-[#f85149] mb-2'>{error}</p>}
      {feedback && <p className='text-[11px] text-[#3fb950] mb-2'>{feedback}</p>}

      {summary && (
        <div className='space-y-4'>
          <div className='grid grid-cols-3 gap-2 text-center'>
            {[
              { label: 'Deposit total', value: fmt(summary.total_deposit_cents) },
              { label: 'Collected', value: fmt(summary.collected_cents) },
              { label: 'Outstanding', value: fmt(summary.outstanding_cents) },
            ].map((card) => (
              <div key={card.label} className='rounded border border-[#30363d] bg-[#161b22] px-2 py-2'>
                <p className='text-[10px] uppercase tracking-wider text-[#8b949e]'>{card.label}</p>
                <p className='text-sm font-bold font-mono text-[#e6edf3]'>{card.value}</p>
              </div>
            ))}
          </div>

          <div className='overflow-x-auto'>
            <table className='w-full text-xs'>
              <thead>
                <tr className='text-left text-[10px] uppercase tracking-wider text-[#8b949e] border-b border-[#30363d]'>
                  <th className='py-2 pr-2'>Traveler</th>
                  <th className='py-2 pr-2'>Share</th>
                  <th className='py-2 pr-2'>Paid</th>
                  <th className='py-2 pr-2'>Settlement</th>
                  <th className='py-2 pr-2'>Schedule</th>
                  <th className='py-2'>Actions</th>
                </tr>
              </thead>
              <tbody>
                {summary.passengers.map((p) => (
                  <tr key={p.passenger_id} className='border-b border-[#21262d] align-top'>
                    <td className='py-2 pr-2'>
                      <p className='text-[#e6edf3] font-medium'>{p.name}</p>
                      {p.share_note && <p className='text-[10px] text-[#8b949e] italic'>{p.share_note}</p>}
                    </td>
                    <td className='py-2 pr-2 font-mono text-[#e6edf3]'>{fmt(p.deposit_share_cents)}</td>
                    <td className='py-2 pr-2 font-mono text-[#3fb950]'>{fmt(p.paid_cents)}</td>
                    <td className='py-2 pr-2'>
                      <span className={`rounded border px-1.5 py-0.5 text-[10px] ${SETTLEMENT_STYLES[p.settlement] ?? ''}`}>
                        {p.settlement}
                      </span>
                    </td>
                    <td className='py-2 pr-2'>
                      {p.schedule.length === 0 ? (
                        <span className='text-[#6e7681]'>—</span>
                      ) : (
                        <ul className='space-y-0.5'>
                          {p.schedule.map((m, i) => (
                            <li key={i} className={MILESTONE_STYLES[m.status] ?? ''}>
                              {m.label}
                              {m.due_at ? ` · ${new Date(m.due_at).toLocaleDateString()}` : ''}
                              {m.status !== 'paid' ? ` (${m.status.replace('_', ' ')})` : ''}
                            </li>
                          ))}
                        </ul>
                      )}
                    </td>
                    <td className='py-2'>
                      <div className='flex flex-wrap gap-1.5'>
                        <button
                          type='button'
                          onClick={() => setPayFor(payFor === p.passenger_id ? null : p.passenger_id)}
                          className='rounded border border-[#30363d] bg-[#161b22] px-2 py-1 text-[10px] text-[#58a6ff] hover:bg-[#21262d]'
                        >
                          Record payment
                        </button>
                        <button
                          type='button'
                          onClick={() => logReminder(p.passenger_id)}
                          className='flex items-center gap-1 rounded border border-[#30363d] bg-[#161b22] px-2 py-1 text-[10px] text-[#d29922] hover:bg-[#21262d]'
                        >
                          <Bell size={10} /> Log reminder ({p.reminders.length})
                        </button>
                      </div>
                      {payFor === p.passenger_id && (
                        <div className='mt-2 rounded border border-[#30363d] bg-[#161b22] p-2 space-y-1.5'>
                          <input
                            type='number'
                            value={movement.amount_cents}
                            onChange={(e) => setMovement({ ...movement, amount_cents: e.target.value })}
                            placeholder='Amount in cents (e.g. 25000)'
                            className='w-full rounded border border-[#30363d] bg-[#0d1117] px-2 py-1 text-[11px] text-[#e6edf3] placeholder:text-[#6e7681] focus:outline-none'
                          />
                          <select
                            value={movement.method}
                            onChange={(e) => setMovement({ ...movement, method: e.target.value })}
                            className='w-full rounded border border-[#30363d] bg-[#0d1117] px-2 py-1 text-[11px] text-[#e6edf3] focus:outline-none'
                          >
                            {['BANK_TRANSFER', 'UPI', 'CARD', 'CASH', 'OTHER'].map((m) => (
                              <option key={m} value={m}>{m}</option>
                            ))}
                          </select>
                          <input
                            type='text'
                            value={movement.reference ?? ''}
                            onChange={(e) => setMovement({ ...movement, reference: e.target.value })}
                            placeholder='Reference (optional)'
                            className='w-full rounded border border-[#30363d] bg-[#0d1117] px-2 py-1 text-[11px] text-[#e6edf3] placeholder:text-[#6e7681] focus:outline-none'
                          />
                          <button
                            type='button'
                            onClick={() => recordPayment(p.passenger_id)}
                            className='w-full rounded bg-[#58a6ff] px-2 py-1 text-[11px] font-semibold text-[#0d1117] hover:bg-[#6eb5ff]'
                          >
                            Record observed payment
                          </button>
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {summary.reminder_drafts.length > 0 && (
            <div>
              <h3 className='text-xs font-semibold text-[#e6edf3] mb-2'>
                Reminder drafts ({summary.reminder_drafts.length}) — copy and send over your own channel
              </h3>
              <ul className='space-y-2'>
                {summary.reminder_drafts.map((d) => (
                  <li key={d.passenger_id} className='rounded border border-[#d29922]/30 bg-[#d29922]/5 p-2.5'>
                    <div className='flex items-center justify-between mb-1'>
                      <p className='text-[11px] font-semibold text-[#e6edf3]'>
                        {d.passenger_name} · {fmt(d.outstanding_cents)} · {d.trigger.replace('_', ' ')}
                      </p>
                      <button
                        type='button'
                        onClick={() => copyDraft(d.passenger_id, d.draft_text)}
                        className='flex items-center gap-1 rounded border border-[#30363d] bg-[#161b22] px-2 py-1 text-[10px] text-[#58a6ff] hover:bg-[#21262d]'
                      >
                        <Copy size={10} /> {copiedId === d.passenger_id ? 'Copied' : 'Copy'}
                      </button>
                    </div>
                    <pre className='whitespace-pre-wrap text-[11px] text-[#8b949e] font-sans'>{d.draft_text}</pre>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
