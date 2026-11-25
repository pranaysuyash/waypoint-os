'use client';

import { useId, useState, type FormEvent } from 'react';
import { useSearchParams } from 'next/navigation';
import { api } from '@/lib/api-client';

interface EvidenceSource {
  source_record_id: string;
  source_url: string;
  expires_at: string;
}

interface Evidence {
  state: string;
  sources: EvidenceSource[];
}

interface EvidenceResult {
  service_date: string;
  guests: number;
  state: 'evidence_found' | 'staff_review';
  provenance: 'fictional_fixture' | 'buyer_supplied_snapshot' | null;
  rate: Evidence & { amount?: string; currency?: string; basis?: string };
  calendar: Evidence & { available_guests?: number };
  review_reasons: string[];
}

const fields = [
  { name: 'supplier_id', label: 'Supplier ID', type: 'text' },
  { name: 'service_id', label: 'Service or slot ID', type: 'text' },
  { name: 'service_date', label: 'Service date', type: 'date' },
  { name: 'guests', label: 'Guests', type: 'number' },
] as const;

const states: Record<string, string> = {
  observed: 'Current observation',
  available_observed: 'Capacity observed',
  unavailable_observed: 'Insufficient capacity observed',
  missing: 'No matching record',
  stale: 'Evidence expired',
  conflicting: 'Sources disagree',
};

const sourceIssues: Record<string, string> = {
  snapshot_not_configured: 'No supplier snapshot is configured for this agency.',
  snapshot_unavailable: 'The supplier snapshot is unavailable.',
  snapshot_invalid: 'The supplier snapshot could not be read. Ask the source owner to check the export.',
};

const rateFormat = new Intl.NumberFormat(undefined, { maximumFractionDigits: 3 });

function EvidenceCard({ title, evidence, detail }: { title: string; evidence: Evidence; detail?: string }) {
  return (
    <div className='rounded-lg border border-[#30363d] bg-[#0d1117] p-3 space-y-1'>
      <h3 className='text-sm font-medium text-[#e6edf3]'>{title}</h3>
      <p className='text-xs text-[#8b949e]'>{states[evidence.state] ?? 'Evidence unavailable'}</p>
      {detail && <p className='text-sm text-[#e6edf3]'>{detail}</p>}
      {evidence.sources.length > 0 && (
        <ul className='space-y-1 pt-1 text-xs'>
          {evidence.sources.map((source, index) => (
            <li key={`${source.source_url}-${source.source_record_id}-${index}`} className='flex flex-wrap gap-x-2'>
              <a href={source.source_url} target='_blank' rel='noreferrer' className='break-all text-[#58a6ff] hover:underline'>
                {source.source_record_id}
              </a>
              <span className='text-[#8b949e]'>Expires {new Date(source.expires_at).toLocaleDateString()}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default function SupplierEvidenceLookup() {
  const initial = useSearchParams();
  const id = useId();
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<EvidenceResult | null>(null);
  const [error, setError] = useState('');

  async function lookup(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const query = new URLSearchParams();
    for (const { name } of fields) query.set(name, String(form.get(name) ?? '').trim());
    setBusy(true);
    setError('');
    setResult(null);
    try {
      setResult(await api.get<EvidenceResult>(`/api/v1/supplier/availability/evidence?${query}`));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Supplier evidence is unavailable');
    } finally {
      setBusy(false);
    }
  }

  return (
    <section aria-labelledby={`${id}-heading`} className='space-y-4 rounded-xl border border-[#30363d] bg-[#161b22] p-5'>
      <div>
        <h2 id={`${id}-heading`} className='text-base font-semibold text-[#e6edf3]'>Rate and calendar lookup</h2>
        <p className='mt-1 text-xs text-[#8b949e]'>Check recorded pricing and capacity before quoting or placing a hold.</p>
      </div>
      <form onSubmit={lookup} className='grid grid-cols-1 items-end gap-3 sm:grid-cols-2 xl:grid-cols-[1fr_1fr_160px_100px_auto]'>
        {fields.map(({ name, label, type }) => (
          <label key={name} className='grid gap-1 text-xs text-[#e6edf3]'>
            {label}
            <input
              name={name} type={type} defaultValue={initial.get(name) ?? ''} required disabled={busy}
              min={type === 'number' ? 1 : undefined} max={type === 'number' ? 10000 : undefined}
              maxLength={type === 'text' ? 96 : undefined}
              className='min-w-0 rounded-md border border-[#30363d] bg-[#0d1117] px-2.5 py-2 text-sm text-[#e6edf3]'
            />
          </label>
        ))}
        <button type='submit' disabled={busy} className='rounded-md border border-[#30363d] bg-[#21262d] px-3 py-2 text-sm font-medium text-[#e6edf3] hover:bg-[#30363d] disabled:opacity-50'>
          {busy ? 'Checking…' : 'Check evidence'}
        </button>
      </form>
      {error && <p role='alert' className='text-sm text-[#ff7b72]'>{error}</p>}
      {result && (
        <div aria-live='polite' className='space-y-2'>
          <p className='flex flex-wrap items-center gap-x-2 text-sm text-[#e6edf3]'>
            <strong>{result.state === 'evidence_found' ? 'Current evidence found' : 'Staff review needed'}</strong>
            <span className='text-xs text-[#8b949e]'>{result.service_date} · {result.guests} guests</span>
            {result.provenance === 'fictional_fixture' && <span className='text-xs text-[#e3b341]'>Sample data</span>}
          </p>
          {result.review_reasons.map((reason) => sourceIssues[reason] && <p key={reason} className='text-xs text-[#e3b341]'>{sourceIssues[reason]}</p>)}
          <div className='grid gap-3 sm:grid-cols-2'>
            <EvidenceCard title='Rate' evidence={result.rate} detail={result.rate.amount && `${result.rate.currency} ${rateFormat.format(Number(result.rate.amount))} ${result.rate.basis?.replaceAll('_', ' ') ?? ''}`} />
            <EvidenceCard title='Calendar' evidence={result.calendar} detail={result.calendar.available_guests != null ? `Capacity for ${result.calendar.available_guests} guests` : undefined} />
          </div>
        </div>
      )}
    </section>
  );
}
