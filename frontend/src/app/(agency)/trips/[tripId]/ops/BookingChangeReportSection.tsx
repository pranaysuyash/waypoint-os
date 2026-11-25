'use client';

import { useCallback, useEffect, useState } from 'react';
import { CheckCircle2, Send } from 'lucide-react';

// FND-0410 (2026-11-18): operator entry point for the booking-change ledger
// (POST /api/v1/trips/{trip_id}/booking-changes) — hotel/airline/other
// supplier changes on confirmed bookings with honest operator_reported
// provenance (D6 posture). Mirrors IrropsReportSection; flight IRROPS keeps
// its own door — this is the booking-domain ledger.

const CHANGE_KINDS = ['cancellation', 'overbook', 'schedule_change', 'rate_change'] as const;
const SUPPLIERS = ['hotel', 'airline', 'rail', 'transfer', 'activity', 'other'] as const;
const BASIS_CHANNELS = ['email', 'phone', 'portal', 'supplier_dashboard', 'other'] as const;

type ChangeKind = (typeof CHANGE_KINDS)[number];
type Supplier = (typeof SUPPLIERS)[number];
type BasisChannel = (typeof BASIS_CHANNELS)[number];

interface BookingChangeRow {
  change_id?: string;
  change_kind?: string;
  supplier?: string;
  supplier_ref?: string | null;
  notes?: string;
  affected_travelers?: string[];
  source?: string;
  source_label?: string;
  status?: string;
  reported_at?: string;
}

const inputClasses =
  'w-full rounded border border-[#30363d] bg-[#161b22] px-2.5 py-1.5 text-xs text-[#e6edf3] placeholder:text-[#6e7681] focus:border-[#58a6ff] focus:outline-none';
const labelClasses = 'block text-[10px] font-semibold uppercase tracking-wider text-[#8b949e] mb-1';

export default function BookingChangeReportSection({ tripId }: { tripId: string }) {
  const [changeKind, setChangeKind] = useState<ChangeKind>('overbook');
  const [supplier, setSupplier] = useState<Supplier>('hotel');
  const [supplierRef, setSupplierRef] = useState('');
  const [basisChannel, setBasisChannel] = useState<BasisChannel>('email');
  const [basisReference, setBasisReference] = useState('');
  const [notes, setNotes] = useState('');
  const [affected, setAffected] = useState('');
  const [activeRows, setActiveRows] = useState<BookingChangeRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [resolvingId, setResolvingId] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const res = await fetch(`/api/v1/trips/${encodeURIComponent(tripId)}/booking-changes`);
      if (!res.ok) throw new Error(`Ledger unavailable (${res.status})`);
      const data = await res.json();
      setActiveRows(Array.isArray(data?.active) ? data.active : []);
      setError(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Booking-change ledger unavailable.');
    } finally {
      setLoading(false);
    }
  }, [tripId]);

  useEffect(() => {
    void load();
  }, [load]);

  const handleReport = async () => {
    setError(null);
    setFeedback(null);
    if (changeKind === 'cancellation' && !notes.trim()) {
      setError('A cancellation report requires notes describing the basis (what the supplier said, where).');
      return;
    }
    setIsSubmitting(true);
    try {
      const res = await fetch(`/api/v1/trips/${encodeURIComponent(tripId)}/booking-changes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          change_kind: changeKind,
          supplier,
          supplier_ref: supplierRef.trim() || null,
          basis_channel: basisChannel,
          basis_reference: basisReference.trim() || null,
          notes: notes.trim(),
          affected_travelers: affected
            .split(',')
            .map((name) => name.trim())
            .filter(Boolean),
        }),
      });
      const data = await res.json().catch(() => null);
      if (!res.ok) {
        setError(data?.detail ?? `Report failed (${res.status})`);
        return;
      }
      setFeedback('Booking change recorded. Travelers see it labeled "Reported by your travel advisor".');
      setNotes('');
      setSupplierRef('');
      setBasisReference('');
      setAffected('');
      await load();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Report failed.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleResolve = async (changeId: string) => {
    setError(null);
    setResolvingId(changeId);
    try {
      const res = await fetch(
        `/api/v1/trips/${encodeURIComponent(tripId)}/booking-changes/${encodeURIComponent(changeId)}/resolve`,
        { method: 'POST' },
      );
      if (!res.ok) {
        const data = await res.json().catch(() => null);
        setError(data?.detail ?? `Resolve failed (${res.status})`);
        return;
      }
      await load();
    } finally {
      setResolvingId(null);
    }
  };

  return (
    <section className='rounded-lg border border-[#30363d] bg-[#0d1117] p-4'>
      <h3 className='mb-1 flex items-center gap-2 text-sm font-semibold text-[#e6edf3]'>
        <Send size={14} className='text-[#d29922]' /> Booking changes
      </h3>
      <p className='mb-3 text-[11px] text-[#8b949e]'>
        Supplier-side changes to confirmed bookings (hotel overbook, cancellations, schedule/rate
        changes). Recorded as <span className='text-[#d29922]'>operator-reported</span>; a provider
        feed will supersede by authority precedence when one lands.
      </p>

      {loading ? (
        <p className='text-xs text-[#8b949e]'>Loading ledger…</p>
      ) : (
        <>
          {activeRows.length > 0 && (
            <ul className='mb-3 space-y-1.5'>
              {activeRows.map((row) => (
                <li
                  key={row.change_id}
                  className='flex flex-wrap items-start justify-between gap-2 rounded border border-[#30363d] bg-[#161b22] px-2.5 py-2'
                >
                  <div className='min-w-0 flex-1 basis-48 [overflow-wrap:anywhere]'>
                    <p className='text-xs font-semibold text-[#e6edf3]'>
                      {row.supplier} · {row.change_kind}
                      {row.supplier_ref ? ` · ${row.supplier_ref}` : ''}
                    </p>
                    <p className='whitespace-pre-wrap text-[11px] text-[#8b949e]'>{row.notes}</p>
                    <p className='text-[10px] text-[#d29922]'>
                      {row.source_label ?? 'Reported by your travel advisor'}
                      {row.reported_at ? ` · ${new Date(row.reported_at).toLocaleString()}` : ''}
                    </p>
                  </div>
                  <button
                    type='button'
                    onClick={() => row.change_id && handleResolve(row.change_id)}
                    disabled={resolvingId === row.change_id}
                    className='flex shrink-0 items-center gap-1 rounded border border-[#30363d] bg-[#161b22] px-2 py-1 text-[10px] text-[#3fb950] hover:bg-[#21262d] disabled:opacity-40'
                  >
                    <CheckCircle2 size={11} /> {resolvingId === row.change_id ? 'Resolving…' : 'Resolve'}
                  </button>
                </li>
              ))}
            </ul>
          )}

          <div className='grid grid-cols-2 gap-2 sm:grid-cols-4'>
            <div>
              <label className={labelClasses} htmlFor='bkchg-kind'>Change kind</label>
              <select id='bkchg-kind' className={inputClasses} value={changeKind} onChange={(e) => setChangeKind(e.target.value as ChangeKind)}>
                {CHANGE_KINDS.map((k) => <option key={k} value={k}>{k.replace('_', ' ')}</option>)}
              </select>
            </div>
            <div>
              <label className={labelClasses} htmlFor='bkchg-supplier'>Supplier</label>
              <select id='bkchg-supplier' className={inputClasses} value={supplier} onChange={(e) => setSupplier(e.target.value as Supplier)}>
                {SUPPLIERS.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            <div>
              <label className={labelClasses} htmlFor='bkchg-ref'>Supplier ref</label>
              <input id='bkchg-ref' className={inputClasses} value={supplierRef} onChange={(e) => setSupplierRef(e.target.value)} placeholder='HTL-ROM-991' />
            </div>
            <div>
              <label className={labelClasses} htmlFor='bkchg-basis'>Learned via</label>
              <select id='bkchg-basis' className={inputClasses} value={basisChannel} onChange={(e) => setBasisChannel(e.target.value as BasisChannel)}>
                {BASIS_CHANNELS.map((b) => <option key={b} value={b}>{b.replace('_', ' ')}</option>)}
              </select>
            </div>
          </div>
          <div className='mt-2 grid grid-cols-1 gap-2 sm:grid-cols-2'>
            <div>
              <label className={labelClasses} htmlFor='bkchg-basis-ref'>Basis reference</label>
              <input id='bkchg-basis-ref' className={inputClasses} value={basisReference} onChange={(e) => setBasisReference(e.target.value)} placeholder='Email subject / call log' />
            </div>
            <div>
              <label className={labelClasses} htmlFor='bkchg-affected'>Affected travelers (comma-separated)</label>
              <input id='bkchg-affected' className={inputClasses} value={affected} onChange={(e) => setAffected(e.target.value)} placeholder='optional' />
            </div>
          </div>
          <div className='mt-2'>
            <label className={labelClasses} htmlFor='bkchg-notes'>Notes</label>
            <textarea id='bkchg-notes' className={inputClasses} rows={2} value={notes} onChange={(e) => setNotes(e.target.value)} placeholder='What the supplier said, when, and what was offered.' />
          </div>

          {error && <p className='mt-2 text-[11px] text-[#f85149]'>{error}</p>}
          {feedback && <p className='mt-2 text-[11px] text-[#3fb950]'>{feedback}</p>}
          <button
            type='button'
            onClick={handleReport}
            disabled={isSubmitting}
            className='mt-2 flex items-center gap-1.5 rounded border border-[#30363d] bg-[#d29922] px-3 py-1.5 text-xs font-semibold text-[#0d1117] hover:bg-[#e3b341] disabled:opacity-40'
          >
            <Send size={12} /> {isSubmitting ? 'Recording…' : 'Record booking change'}
          </button>
        </>
      )}
    </section>
  );
}
