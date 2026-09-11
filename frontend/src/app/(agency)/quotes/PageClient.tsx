'use client';

import { useMemo, useState, useCallback } from 'react';
import Link from 'next/link';
import { useSearchParams, useRouter, usePathname } from 'next/navigation';
import { BackToOverviewLink } from '@/components/navigation/BackToOverviewLink';
import SimulatedBadge from '@/components/ui/SimulatedBadge';
import { useTrip, useTrips } from '@/hooks/useTrips';
import { formatTripPickerLabel } from '@/lib/trip-picker-label';
import {
  FileText,
  DollarSign,
  ShieldCheck,
  Sparkles,
  Share2,
  CheckCircle2,
  Send,
  Layers,
  ChevronRight,
} from 'lucide-react';

interface QuoteVersion {
  id: string;
  versionNumber: string;
  tier: 'saver' | 'curated' | 'luxury';
  tierLabel: string;
  netCost: number;
  marginPercent: number;
  taxPercent: number;
  rackPrice: number;
  status: 'draft' | 'under_review' | 'sent' | 'accepted' | 'expired';
  createdAt: string;
  highlights: string[];
  inclusions: string[];
}

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
  const { data: selectedTrip } = useTrip(effectiveSelectedTripId || null);

  const [selectedVersionId, setSelectedVersionId] = useState<string>('v2');
  const [marginAdjustment, setMarginAdjustment] = useState<number>(15);

  const handleTripChange = useCallback(
    (newTripId: string) => {
      const params = new URLSearchParams(searchParams.toString());
      if (newTripId) {
        params.set('tripId', newTripId);
      } else {
        params.delete('tripId');
      }
      router.push(`${pathname}?${params.toString()}`, { scroll: false });
    },
    [pathname, router, searchParams],
  );

  const quoteVersions: QuoteVersion[] = useMemo(() => {
    if (!selectedTrip) return [];

    const baseBudget = 4200;

    return [
      {
        id: 'v1',
        versionNumber: 'Quote v1.0',
        tier: 'saver',
        tierLabel: 'Essential Saver',
        netCost: Math.round(baseBudget * 0.85),
        marginPercent: 12,
        taxPercent: 5,
        rackPrice: Math.round(baseBudget * 0.85 * 1.12 * 1.05),
        status: 'draft',
        createdAt: '2026-08-28',
        highlights: ['4-Star City Center Hotel', 'Standard Airport Transfers', 'Semi-Private City Excursions'],
        inclusions: ['Accommodation (Room Only)', 'Shared Van Transfers', 'Scheduled Sightseeing'],
      },
      {
        id: 'v2',
        versionNumber: 'Quote v2.1 (Recommended)',
        tier: 'curated',
        tierLabel: 'Signature Curator',
        netCost: baseBudget,
        marginPercent: marginAdjustment,
        taxPercent: 5,
        rackPrice: Math.round(baseBudget * (1 + marginAdjustment / 100) * 1.05),
        status: 'draft',
        createdAt: '2026-08-29',
        highlights: ['5-Star Boutique Villa', 'Private Chauffeur Throughout', 'Curated Chef Tastings & Fast-Track Access'],
        inclusions: ['Breakfast & Curated Dining', 'Dedicated Private Vehicle', 'VIP Concierge & Skip-the-line Tickets'],
      },
      {
        id: 'v3',
        versionNumber: 'Quote v3.0 (Prestige)',
        tier: 'luxury',
        tierLabel: 'Ultra Prestige Suite',
        netCost: Math.round(baseBudget * 1.6),
        marginPercent: 22,
        taxPercent: 5,
        rackPrice: Math.round(baseBudget * 1.6 * 1.22 * 1.05),
        status: 'draft',
        createdAt: '2026-08-30',
        highlights: ['Presidential / Overwater Suite', 'Helicopter Transfer & Yacht Charter', '24/7 Private Host & Michelin Dining'],
        inclusions: ['All-Inclusive Luxury Plan', 'Private Helicopter & Luxury Fleet', 'Private Yacht Day Tour & Bespoke Butler'],
      },
    ];
  }, [selectedTrip, marginAdjustment]);

  const activeQuote = quoteVersions.find((q) => q.id === selectedVersionId) || quoteVersions[1] || quoteVersions[0];

  return (
    <div className='p-6 space-y-6'>
      <BackToOverviewLink />

      {/* Header & Mission */}
      <div className='flex flex-col md:flex-row md:items-center md:justify-between gap-4'>
        <div>
          <h1 className='text-ui-xl font-semibold text-[#e6edf3] flex items-center gap-2'>
            <FileText className='size-6 text-[#58a6ff]' />
            Quotes & Commercial Proposals
            <SimulatedBadge label='Sample data' />
          </h1>
          <p className='text-ui-sm text-[#8b949e] mt-1'>
            Multi-version proposal studio, wholesale net vs rack margin modeling, approval governance, and client links.
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

      {/* Honesty banner (FND-0260): this page is an illustrative pricing model. */}
      <div
        data-testid='quotes-sample-banner'
        role='note'
        className='rounded-lg border border-amber-500/30 bg-amber-500/10 p-4 text-xs text-amber-200 space-y-1'
      >
        <p className='font-semibold uppercase tracking-wide'>Illustrative pricing model — not real quotes</p>
        <p>
          Every tier, price, margin, status, and date on this page is generated from a fixed example budget for
          exploration only. No quote has been created, persisted, or sent to a client, and client web links are
          unavailable until quotes are persisted by the spine. Real quote state lives in the{' '}
          <Link href='/reviews' className='underline hover:text-amber-100'>
            Quote Review queue
          </Link>
          .
        </p>
      </div>

      {/* Trip Picker Selector */}
      <div className='rounded-lg border border-[#30363d] p-4 bg-[#0d1117] space-y-3'>
        <div className='flex flex-col md:flex-row md:items-center justify-between gap-3'>
          <div className='space-y-1'>
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

          {selectedTrip && (
            <div className='flex items-center gap-3 text-xs bg-[#161b22] px-3 py-2 rounded-md border border-[#30363d]'>
              <div className='text-[#8b949e]'>
                Destination: <span className='text-[#e6edf3] font-medium'>{selectedTrip.destination || 'Unspecified'}</span>
              </div>
              <div className='w-px h-4 bg-[#30363d]' />
              <div className='text-[#8b949e]'>
                Party Size: <span className='text-[#e6edf3] font-medium'>{selectedTrip.party || 1} travelers</span>
              </div>
              <div className='w-px h-4 bg-[#30363d]' />
              <div className='text-[#8b949e]'>
                Stated Budget: <span className='text-[#3fb950] font-medium'>{selectedTrip.budget || ',500'}</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Metrics Row */}
      <div className='grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4'>
        <div className='rounded-lg border border-[#30363d] bg-[#0d1117] p-4 space-y-1.5'>
          <div className='text-xs font-semibold text-[#8b949e] uppercase tracking-wider flex items-center justify-between'>
            <span>Active Proposals</span>
            <FileText className='size-4 text-[#58a6ff]' />
          </div>
          <div className='text-2xl font-bold text-[#e6edf3]'>{quoteVersions.length} Tiers</div>
          <div className='text-xs text-[#8b949e]'>Saver, Recommended & Luxury</div>
        </div>

        <div className='rounded-lg border border-[#30363d] bg-[#0d1117] p-4 space-y-1.5'>
          <div className='text-xs font-semibold text-[#8b949e] uppercase tracking-wider flex items-center justify-between'>
            <span>Recommended Total</span>
            <DollarSign className='size-4 text-[#3fb950]' />
          </div>
          <div className='text-2xl font-bold text-[#3fb950]'>
            ${activeQuote?.rackPrice ? activeQuote.rackPrice.toLocaleString() : '—'}
          </div>
          <div className='text-xs text-[#8b949e]'>Illustrative net + markup + tax</div>
        </div>

        <div className='rounded-lg border border-[#30363d] bg-[#0d1117] p-4 space-y-1.5'>
          <div className='text-xs font-semibold text-[#8b949e] uppercase tracking-wider flex items-center justify-between'>
            <span>Agency Net Margin</span>
            <Sparkles className='size-4 text-[#d29922]' />
          </div>
          <div className='text-2xl font-bold text-[#d29922]'>
            ${activeQuote ? Math.round(activeQuote.netCost * (activeQuote.marginPercent / 100)).toLocaleString() : '630'} ({activeQuote?.marginPercent ?? 15}%)
          </div>
          <div className='text-xs text-[#8b949e]'>Wholesale markup protection</div>
        </div>

        <div className='rounded-lg border border-[#30363d] bg-[#0d1117] p-4 space-y-1.5'>
          <div className='text-xs font-semibold text-[#8b949e] uppercase tracking-wider flex items-center justify-between'>
            <span>Commercial Status</span>
            <ShieldCheck className='size-4 text-[#a371f7]' />
          </div>
          <div className='text-2xl font-bold text-[#a371f7] capitalize'>
            {activeQuote?.status.replace('_', ' ') || 'Ready'}
          </div>
          <div className='text-xs text-[#8b949e]'>Illustrative model — nothing persisted or sent</div>
        </div>
      </div>

      {/* Main Quote Workspace: Versions Matrix & Interactive Simulator */}
      {selectedTrip ? (
        <div className='grid gap-6 lg:grid-cols-3'>
          {/* Version Matrix Table */}
          <div className='lg:col-span-2 space-y-4'>
            <div className='rounded-lg border border-[#30363d] bg-[#0d1117] overflow-hidden'>
              <div className='p-4 border-b border-[#30363d] flex items-center justify-between bg-[#161b22]'>
                <div className='flex items-center gap-2 font-semibold text-sm text-[#e6edf3]'>
                  <Layers className='size-4 text-[#58a6ff]' />
                  <span>Multi-Tier Quote Comparison Matrix</span>
                </div>
                <span className='text-xs text-[#8b949e]'>Click a tier to inspect commercials</span>
              </div>

              <div className='overflow-x-auto'>
                <table className='w-full text-left text-sm'>
                  <thead>
                    <tr className='border-b border-[#30363d] bg-[#0d1117] text-xs font-semibold text-[#8b949e] uppercase tracking-wider'>
                      <th className='p-3.5'>Quote Tier</th>
                      <th className='p-3.5'>Net Sourcing</th>
                      <th className='p-3.5'>Margin</th>
                      <th className='p-3.5'>Client Total</th>
                      <th className='p-3.5'>Status</th>
                      <th className='p-3.5 text-right'>Action</th>
                    </tr>
                  </thead>
                  <tbody className='divide-y divide-[#30363d]'>
                    {quoteVersions.map((q) => {
                      const isSelected = q.id === selectedVersionId;
                      return (
                        <tr
                          key={q.id}
                          onClick={() => setSelectedVersionId(q.id)}
                          className={`cursor-pointer transition-colors ${
                            isSelected ? 'bg-[#1f242c]' : 'hover:bg-[#161b22]'
                          }`}
                        >
                          <td className='p-3.5'>
                            <div className='font-semibold text-[#e6edf3] flex items-center gap-2'>
                              {q.tierLabel}
                              {q.tier === 'curated' && (
                                <span className='px-1.5 py-0.5 text-[10px] font-bold bg-[#1f6feb] text-white rounded'>
                                  BEST FIT
                                </span>
                              )}
                            </div>
                            <div className='text-xs text-[#8b949e]'>{q.versionNumber}</div>
                          </td>
                          <td className='p-3.5 font-mono text-[#8b949e]'>${q.netCost.toLocaleString()}</td>
                          <td className='p-3.5 font-mono text-[#d29922]'>{q.marginPercent}%</td>
                          <td className='p-3.5 font-mono font-semibold text-[#3fb950]'>
                            ${q.rackPrice.toLocaleString()}
                          </td>
                          <td className='p-3.5'>
                            <span
                              className={`px-2 py-0.5 rounded text-xs font-medium ${
                                q.status === 'accepted'
                                  ? 'bg-[#238636]/20 text-[#3fb950] border border-[#238636]/40'
                                  : q.status === 'sent'
                                  ? 'bg-[#1f6feb]/20 text-[#58a6ff] border border-[#1f6feb]/40'
                                  : q.status === 'under_review'
                                  ? 'bg-[#d29922]/20 text-[#d29922] border border-[#d29922]/40'
                                  : 'bg-[#30363d]/50 text-[#8b949e] border border-[#30363d]'
                              }`}
                            >
                              {q.status.replace('_', ' ')}
                            </span>
                          </td>
                          <td className='p-3.5 text-right'>
                            <button
                              type='button'
                              disabled
                              title='Client web links unlock when quotes are persisted by the spine — this page is an illustrative model'
                              data-testid='quotes-share-disabled'
                              className='p-1.5 text-xs text-[#8b949e] rounded inline-flex items-center gap-1 cursor-not-allowed opacity-60'
                            >
                              <Share2 className='size-3.5' />
                              <span className='text-[11px]'>Share</span>
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Inclusions & Experience Breakdown for Selected Version */}
            {activeQuote && (
              <div className='rounded-lg border border-[#30363d] bg-[#0d1117] p-4 space-y-3'>
                <div className='flex items-center justify-between border-b border-[#30363d] pb-2'>
                  <div className='text-sm font-semibold text-[#e6edf3] flex items-center gap-2'>
                    <Sparkles className='size-4 text-[#d29922]' />
                    <span>Inclusions & Experience Scope ({activeQuote.tierLabel})</span>
                  </div>
                  <span className='text-xs text-[#8b949e]'>Version Created: {activeQuote.createdAt}</span>
                </div>

                <div className='grid gap-3 sm:grid-cols-2 pt-1'>
                  <div>
                    <div className='text-xs font-semibold text-[#8b949e] uppercase mb-2'>Key Highlights</div>
                    <ul className='space-y-1.5 text-xs text-[#c9d1d9]'>
                      {activeQuote.highlights.map((h, i) => (
                        <li key={i} className='flex items-center gap-2'>
                          <CheckCircle2 className='size-3.5 text-[#3fb950] shrink-0' />
                          <span>{h}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div>
                    <div className='text-xs font-semibold text-[#8b949e] uppercase mb-2'>Commercial Inclusions</div>
                    <ul className='space-y-1.5 text-xs text-[#c9d1d9]'>
                      {activeQuote.inclusions.map((inc, i) => (
                        <li key={i} className='flex items-center gap-2'>
                          <ChevronRight className='size-3.5 text-[#58a6ff] shrink-0' />
                          <span>{inc}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Pricing & Commercial Controls Drawer */}
          <div className='space-y-4'>
            <div className='rounded-lg border border-[#30363d] bg-[#0d1117] p-4 space-y-4'>
              <div className='flex items-center justify-between border-b border-[#30363d] pb-3'>
                <div className='font-semibold text-sm text-[#e6edf3] flex items-center gap-2'>
                  <DollarSign className='size-4 text-[#3fb950]' />
                  <span>Live Margin & Fee Modeling</span>
                </div>
                <span className='text-xs font-mono text-[#3fb950]'>{marginAdjustment}% Target</span>
              </div>

              {/* Slider for Margin % */}
              <div className='space-y-2'>
                <div className='flex justify-between text-xs text-[#8b949e]'>
                  <span>Adjust Agency Markup</span>
                  <span className='font-medium text-[#e6edf3]'>{marginAdjustment}%</span>
                </div>
                <input
                  type='range'
                  min='5'
                  max='35'
                  step='1'
                  value={marginAdjustment}
                  onChange={(e) => setMarginAdjustment(Number(e.target.value))}
                  className='w-full accent-[#58a6ff] cursor-pointer'
                />
                <div className='flex justify-between text-[10px] text-[#8b949e]'>
                  <span>5% (Volume)</span>
                  <span>15% (Standard)</span>
                  <span>35% (Bespoke)</span>
                </div>
              </div>

              {/* Commercial Cost Breakdown Box */}
              {activeQuote && (
                <div className='bg-[#161b22] p-3.5 rounded-md border border-[#30363d] space-y-2 text-xs'>
                  <div className='flex justify-between text-[#8b949e]'>
                    <span>Wholesale Sourcing Net</span>
                    <span className='font-mono text-[#e6edf3]'>${activeQuote.netCost.toLocaleString()}</span>
                  </div>
                  <div className='flex justify-between text-[#8b949e]'>
                    <span>Agency Gross Markup ({marginAdjustment}%)</span>
                    <span className='font-mono text-[#d29922]'>
                      +${Math.round(activeQuote.netCost * (marginAdjustment / 100)).toLocaleString()}
                    </span>
                  </div>
                  <div className='flex justify-between text-[#8b949e]'>
                    <span>Illustrative tax placeholder (5%)</span>
                    <span className='font-mono text-[#8b949e]'>
                      +${Math.round(activeQuote.netCost * (1 + marginAdjustment / 100) * 0.05).toLocaleString()}
                    </span>
                  </div>
                  <div className='border-t border-[#30363d] pt-2 flex justify-between font-semibold text-sm'>
                    <span className='text-[#e6edf3]'>Client Proposal Price</span>
                    <span className='font-mono text-[#3fb950]'>
                      ${Math.round(activeQuote.netCost * (1 + marginAdjustment / 100) * 1.05).toLocaleString()}
                    </span>
                  </div>
                </div>
              )}

              {/* Client Proposal Dispatch Options */}
              <div className='space-y-2 pt-2'>
                <button
                  type='button'
                  disabled
                  title='Client web links unlock when quotes are persisted by the spine — this page is an illustrative model'
                  data-testid='quotes-client-link-disabled'
                  className='w-full py-2 bg-[#21262d] text-[#8b949e] text-xs font-semibold rounded-md border border-[#30363d] flex items-center justify-center gap-1.5 cursor-not-allowed opacity-60'
                >
                  Client Web Link — unavailable for illustrative quotes
                </button>

                <Link
                  href={`/trips/${effectiveSelectedTripId}/output`}
                  className='w-full py-2 bg-[#1f6feb] hover:bg-[#388bfd] text-white text-xs font-semibold rounded-md flex items-center justify-center gap-1.5 transition-colors'
                >
                  <Send className='size-3.5' />
                  Open Full Output & Export PDF
                </Link>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className='rounded-lg border border-[#30363d] bg-[#0d1117] p-8 text-center text-[#8b949e]'>
          {isLoading ? 'Loading agency proposals…' : 'No trip selected. Choose a trip above to manage quotes.'}
        </div>
      )}
    </div>
  );
}
