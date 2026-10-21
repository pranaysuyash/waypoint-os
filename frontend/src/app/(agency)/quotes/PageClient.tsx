'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { useSearchParams, useRouter, usePathname } from 'next/navigation';
import { useTrips } from '@/hooks/useTrips';
import { formatTripPickerLabel } from '@/lib/trip-picker-label';
import {
  FileText,
  DollarSign,
  ShieldCheck,
  Sparkles,
  Layers,
  AlertTriangle,
  CheckCircle2,
} from 'lucide-react';

// T4 (FND-0303): this page renders the REAL quote read model from
// GET /api/v1/trips/{trip_id}/quotes — spine-persisted recommended option,
// policy-resolved margin (FND-0268 provenance), real review/proposal status.
// The former fabricated tier matrix (v1/v2/v3 from a fixed budget) is gone.

interface QuoteProvenance {
  applied_rule_id?: string;
  markup_amount_usd?: number;
  flat_planning_fee_usd?: number;
}

interface QuoteView {
  trip_id: string;
  title: string;
  currency: string;
  net_cost: number;
  net_cost_basis: string;
  margin_percent: number;
  margin_basis: string;
  margin_provenance: QuoteProvenance;
  tax_percent: number | null;
  rack_price: number;
  rack_price_basis: string;
  status: string;
  created_at: string;
  updated_at?: string | null;
  highlights: string[];
  summary?: string | null;
}

interface QuoteBranch {
  label: string;
  description?: string | null;
  priced: boolean;
}

interface QuotesResponse {
  trip_id: string;
  quote_ready: boolean;
  quotes: QuoteView[];
  branches: QuoteBranch[];
  budget_breakdown?: {
    verdict?: string;
    buckets?: Array<{ bucket: string; low: number; high: number; covered: boolean }>;
    missing_buckets?: string[];
    total_estimated_low?: number;
    total_estimated_high?: number;
  } | null;
  missing: string[];
}

const STATUS_STYLES: Record<string, string> = {
  draft: 'text-[#8b949e]',
  under_review: 'text-[#d29922]',
  approved: 'text-[#3fb950]',
  rejected: 'text-[#f85149]',
  revision_needed: 'text-[#e36f2f]',
  sent: 'text-[#58a6ff]',
};

export default function QuotesPageClient() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const urlTripId = searchParams.get('tripId') || searchParams.get('trip') || '';

  const { data: trips, isLoading } = useTrips({ view: 'workspace', limit: 100 });

  const tripOptions = useMemo(
    () => trips.map((trip) => ({ id: trip.id, label: formatTripPickerLabel(trip) })),
    [trips],
  );
  const selectedTripExists = trips.some((trip) => trip.id === urlTripId);
  const effectiveSelectedTripId = selectedTripExists ? urlTripId : trips[0]?.id ?? '';

  const [quotesData, setQuotesData] = useState<QuotesResponse | null>(null);
  const [quotesLoading, setQuotesLoading] = useState(false);
  const [quotesError, setQuotesError] = useState<string | null>(null);

  const handleTripChange = (newTripId: string) => {
    const params = new URLSearchParams(searchParams.toString());
    if (newTripId) {
      params.set('tripId', newTripId);
    } else {
      params.delete('tripId');
    }
    router.push(`${pathname}?${params.toString()}`, { scroll: false });
  };

  useEffect(() => {
    if (!effectiveSelectedTripId) {
      setQuotesData(null);
      return;
    }
    let cancelled = false;
    setQuotesLoading(true);
    setQuotesError(null);
    fetch(`/api/v1/trips/${effectiveSelectedTripId}/quotes`)
      .then(async (res) => {
        if (!res.ok) throw new Error(`Quote lookup failed (${res.status})`);
        return res.json();
      })
      .then((data: QuotesResponse) => {
        if (!cancelled) setQuotesData(data);
      })
      .catch((err: Error) => {
        if (!cancelled) setQuotesError(err.message);
      })
      .finally(() => {
        if (!cancelled) setQuotesLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [effectiveSelectedTripId]);

  const activeQuote = quotesData?.quotes[0] ?? null;
  const budget = quotesData?.budget_breakdown ?? null;

  return (
    <div className='p-6 space-y-6'>

      {/* Header */}
      <div className='flex flex-col md:flex-row md:items-center md:justify-between gap-4'>
        <div>
          <h1 className='text-ui-xl font-semibold text-[#e6edf3] flex items-center gap-2'>
            <FileText className='size-6 text-[#58a6ff]' />
            Quotes & Commercial Proposals
          </h1>
          <p className='text-ui-sm text-[#8b949e] mt-1'>
            Spine-derived quote for the selected trip: persisted itinerary cost, policy-resolved margin
            (rule provenance shown), and real review status. Nothing on this page is invented.
          </p>
        </div>

        {effectiveSelectedTripId && (
          <div className='flex items-center gap-3'>
            <Link
              href={`/trips/${effectiveSelectedTripId}/output`}
              className='px-3.5 py-2 bg-[#238636] hover:bg-[#2ea043] text-white text-xs font-semibold rounded-md flex items-center gap-1.5 transition-colors shadow-sm'
            >
              <Sparkles className='size-3.5' />
              Generate Output Artifacts
            </Link>
            <Link
              href='/reviews'
              className='px-3.5 py-2 bg-[#21262d] hover:bg-[#30363d] text-[#e6edf3] text-xs font-medium rounded-md border border-[#30363d] flex items-center gap-1.5 transition-colors'
            >
              <ShieldCheck className='size-3.5 text-[#a371f7]' />
              Quote Review Queue
            </Link>
          </div>
        )}
      </div>

      {/* Trip Picker */}
      <div className='rounded-lg border border-[#30363d] p-4 bg-[#0d1117] space-y-3'>
        <label htmlFor='quotes-trip-select' className='block text-xs font-medium text-[#8b949e] uppercase tracking-wider'>
          Active Trip Proposal Scope
        </label>
        <select
          id='quotes-trip-select'
          data-testid='quotes-trip-select'
          value={effectiveSelectedTripId}
          onChange={(e) => handleTripChange(e.target.value)}
          className='w-full md:w-[460px] bg-[#161b22] border border-[#30363d] rounded-md p-2 text-sm text-[#e6edf3] focus:border-[#58a6ff] outline-none'
          disabled={isLoading || tripOptions.length === 0}
        >
          {tripOptions.length === 0 ? (
            <option value=''>No trips in planning</option>
          ) : (
            tripOptions.map((trip) => (
              <option key={trip.id} value={trip.id}>
                {trip.label}
              </option>
            ))
          )}
        </select>
      </div>

      {/* Real quote content */}
      {quotesLoading && (
        <div className='rounded-lg border border-[#30363d] bg-[#0d1117] p-8 text-center text-sm text-[#8b949e]'>
          Loading quote…
        </div>
      )}

      {quotesError && (
        <div role='alert' data-testid='quotes-error' className='rounded-lg border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-400 flex items-center gap-2'>
          <AlertTriangle className='size-4' /> {quotesError}
        </div>
      )}

      {!quotesLoading && !quotesError && quotesData && !quotesData.quote_ready && (
        <div data-testid='quotes-not-ready' className='rounded-lg border border-[#30363d] bg-[#0d1117] p-6'>
          <div className='flex items-center gap-2 mb-3'>
            <AlertTriangle className='size-5 text-[#d29922]' />
            <h2 className='text-ui-base font-semibold text-[#e6edf3]'>No quote yet for this trip</h2>
          </div>
          <p className='text-ui-sm text-[#8b949e] mb-3'>
            Quotes are derived from spine output. This trip doesn&apos;t have the persisted inputs a real
            quote needs yet:
          </p>
          <ul className='space-y-1.5'>
            {quotesData.missing.map((m) => (
              <li key={m} className='text-ui-sm text-[#8b949e] flex items-start gap-2'>
                <span className='text-[#d29922] mt-0.5'>•</span> {m}
              </li>
            ))}
          </ul>
          {effectiveSelectedTripId && (
            <Link
              href={`/trips/${effectiveSelectedTripId}`}
              className='inline-block mt-4 px-3.5 py-2 bg-[#21262d] hover:bg-[#30363d] text-[#e6edf3] text-xs font-medium rounded-md border border-[#30363d]'
            >
              Open trip to process intake
            </Link>
          )}
        </div>
      )}

      {!quotesLoading && !quotesError && activeQuote && (
        <>
          {/* Metrics */}
          <div className='grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4'>
            <div className='rounded-lg border border-[#30363d] bg-[#0d1117] p-4 space-y-1.5'>
              <div className='text-xs font-semibold text-[#8b949e] uppercase tracking-wider flex items-center justify-between'>
                <span>Client Retail</span>
                <DollarSign className='size-4 text-[#3fb950]' />
              </div>
              <div className='text-2xl font-bold text-[#3fb950]' data-testid='quote-rack-price'>
                {activeQuote.currency === 'USD' ? '$' : `${activeQuote.currency} `}
                {activeQuote.rack_price.toLocaleString()}
              </div>
              <div className='text-xs text-[#484f58]'>Computed preview — net cost + policy margin</div>
            </div>

            <div className='rounded-lg border border-[#30363d] bg-[#0d1117] p-4 space-y-1.5'>
              <div className='text-xs font-semibold text-[#8b949e] uppercase tracking-wider'>Net Cost</div>
              <div className='text-2xl font-bold text-[#e6edf3]' data-testid='quote-net-cost'>
                {activeQuote.currency === 'USD' ? '$' : `${activeQuote.currency} `}
                {activeQuote.net_cost.toLocaleString()}
              </div>
              <div className='text-xs text-[#484f58]'>Persisted modeled cost (spine)</div>
            </div>

            <div className='rounded-lg border border-[#30363d] bg-[#0d1117] p-4 space-y-1.5'>
              <div className='text-xs font-semibold text-[#8b949e] uppercase tracking-wider'>Margin</div>
              <div className='text-2xl font-bold text-[#d29922]' data-testid='quote-margin'>
                {activeQuote.margin_percent}%
              </div>
              <div className='text-xs text-[#484f58] truncate' title={activeQuote.margin_provenance.applied_rule_id}>
                {activeQuote.margin_provenance.applied_rule_id ?? 'policy'}
              </div>
            </div>

            <div className='rounded-lg border border-[#30363d] bg-[#0d1117] p-4 space-y-1.5'>
              <div className='text-xs font-semibold text-[#8b949e] uppercase tracking-wider flex items-center justify-between'>
                <span>Commercial Status</span>
                <ShieldCheck className='size-4 text-[#a371f7]' />
              </div>
              <div
                className='text-2xl font-bold capitalize'
                data-testid='quote-status'
                style={{ color: STATUS_STYLES[activeQuote.status] ?? '#e6edf3' }}
              >
                {activeQuote.status.replace('_', ' ')}
              </div>
              <div className='text-xs text-[#484f58]'>Live review-queue + proposal-link state</div>
            </div>
          </div>

          {/* Quote detail */}
          <div className='grid gap-6 lg:grid-cols-3'>
            <div className='lg:col-span-2 space-y-4'>
              <div className='rounded-lg border border-[#30363d] bg-[#0d1117] overflow-hidden'>
                <div className='p-4 border-b border-[#30363d] flex items-center justify-between bg-[#161b22]'>
                  <div className='flex items-center gap-2 font-semibold text-sm text-[#e6edf3]'>
                    <Layers className='size-4 text-[#58a6ff]' />
                    <span data-testid='quote-title'>{activeQuote.title}</span>
                  </div>
                  <span className='text-xs text-[#484f58]'>
                    {activeQuote.updated_at
                      ? `Reviewed ${new Date(activeQuote.updated_at).toLocaleDateString()}`
                      : `Created ${activeQuote.created_at ? new Date(activeQuote.created_at).toLocaleDateString() : '—'}`}
                  </span>
                </div>
                <div className='p-4 space-y-3'>
                  {activeQuote.summary && (
                    <p className='text-ui-sm text-[#8b949e]'>{activeQuote.summary}</p>
                  )}
                  {activeQuote.highlights.length > 0 && (
                    <ul className='space-y-1.5'>
                      {activeQuote.highlights.map((h) => (
                        <li key={h} className='text-ui-sm text-[#8b949e] flex items-start gap-2'>
                          <CheckCircle2 className='size-4 text-[#3fb950] shrink-0 mt-0.5' /> {h}
                        </li>
                      ))}
                    </ul>
                  )}
                  <div className='text-xs text-[#484f58] space-y-0.5 pt-2 border-t border-[#21262d]'>
                    <p>Net cost basis: {activeQuote.net_cost_basis}</p>
                    <p>
                      Margin basis: {activeQuote.margin_basis}
                      {activeQuote.margin_provenance.flat_planning_fee_usd != null &&
                        ` · planning fee $${activeQuote.margin_provenance.flat_planning_fee_usd}`}
                      {activeQuote.margin_provenance.markup_amount_usd != null &&
                        ` · markup $${activeQuote.margin_provenance.markup_amount_usd}`}
                    </p>
                    {activeQuote.tax_percent == null && <p>Tax: no persisted tax producer yet — not estimated.</p>}
                  </div>
                </div>
              </div>

              {/* Unpriced decision branches — real, never priced here */}
              {(quotesData?.branches.length ?? 0) > 0 && (
                <div className='rounded-lg border border-[#30363d] bg-[#0d1117] p-4'>
                  <div className='font-semibold text-sm text-[#e6edf3] mb-2'>Open decision branches</div>
                  <p className='text-xs text-[#484f58] mb-3'>
                    The decision engine flagged open questions that change the trip design. These resolve
                    through the decision flow — they carry no price until the spine prices them.
                  </p>
                  <ul className='space-y-2'>
                    {quotesData!.branches.map((b) => (
                      <li key={b.label} className='text-ui-sm text-[#8b949e]'>
                        <span className='text-[#e6edf3] font-medium'>{b.label}</span>
                        {b.description ? ` — ${b.description}` : ''}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* Budget buckets */}
            <div className='space-y-4'>
              {budget?.buckets && budget.buckets.length > 0 ? (
                <div className='rounded-lg border border-[#30363d] bg-[#0d1117] p-4'>
                  <div className='font-semibold text-sm text-[#e6edf3] mb-1'>Cost basis buckets</div>
                  <div className='text-xs text-[#484f58] mb-3 capitalize'>
                    Verdict: {budget.verdict ?? '—'}
                  </div>
                  <ul className='space-y-2'>
                    {budget.buckets.map((b) => (
                      <li key={b.bucket} className='flex items-center justify-between text-ui-sm'>
                        <span className='text-[#8b949e] capitalize'>{b.bucket.replace(/_/g, ' ')}</span>
                        <span className={b.covered ? 'text-[#3fb950]' : 'text-[#d29922]'}>
                          {`$${b.low.toLocaleString()}–$${b.high.toLocaleString()}`}
                        </span>
                      </li>
                    ))}
                  </ul>
                  {(budget.missing_buckets?.length ?? 0) > 0 && (
                    <p className='text-xs text-[#d29922] mt-3'>
                      Not yet estimated: {budget.missing_buckets!.join(', ')}
                    </p>
                  )}
                </div>
              ) : (
                <div className='rounded-lg border border-[#30363d] bg-[#0d1117] p-4 text-ui-sm text-[#8b949e]'>
                  No cost bucket breakdown persisted for this trip yet.
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
