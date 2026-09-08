'use client';

import { useMemo, useState, useCallback } from 'react';
import Link from 'next/link';
import { useSearchParams, useRouter, usePathname } from 'next/navigation';
import { BackToOverviewLink } from '@/components/navigation/BackToOverviewLink';
import { SimulatedBadge } from '@/components/ui/SimulatedBadge';
import { useTrip, useTrips } from '@/hooks/useTrips';
import { formatTripPickerLabel } from '@/lib/trip-picker-label';
import {
  CalendarCheck,
  CheckCircle2,
  Clock,
  Plane,
  Building2,
  Car,
  Shield,
  FileCheck,
  Key,
  Layers,
  ArrowRight,
  Sparkles,
  Check,
} from 'lucide-react';

interface BookingRecord {
  id: string;
  type: 'flight' | 'hotel' | 'transfer' | 'activity' | 'insurance';
  title: string;
  supplierName: string;
  referenceCode: string | null;
  dates: string;
  guestCount: number;
  status: 'sample_preview';
  value: number | null;
  sourceLabel: string;
}

interface ExtractedPreview extends Omit<BookingRecord, 'id'> {
  confidenceLabel: string;
}

interface OperationalTask {
  id: string;
  title: string;
  deadline: string;
  priority: 'critical' | 'medium' | 'low';
  assignedTo: string;
}

export default function BookingsPageClient() {
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

  const [isExtractModalOpen, setIsExtractModalOpen] = useState<boolean>(false);
  const [extractText, setExtractText] = useState<string>('');
  const [isExtracting, setIsExtracting] = useState<boolean>(false);
  const [extractedResult, setExtractedResult] = useState<ExtractedPreview | null>(null);
  const [customBookings, setCustomBookings] = useState<BookingRecord[]>([]);

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

  const initialBookings: BookingRecord[] = useMemo(() => {
    if (!selectedTrip) return [];

    return [
      {
        id: 'bk_01',
        type: 'flight',
        title: 'Sample Emirates EK-501 (BOM -> DXB -> CPT)',
        supplierName: 'Emirates (illustrative provider label)',
        referenceCode: null,
        dates: '15 Nov 2026 - 28 Nov 2026',
        guestCount: selectedTrip.party || 2,
        status: 'sample_preview',
        value: 1850,
        sourceLabel: 'Sample itinerary (demo data)',
      },
      {
        id: 'bk_02',
        type: 'hotel',
        title: 'Sample Silo Hotel (Deluxe Harbour Suite)',
        supplierName: 'Sample hotel provider (illustrative)',
        referenceCode: null,
        dates: '16 Nov 2026 - 22 Nov 2026 (6 Nights)',
        guestCount: selectedTrip.party || 2,
        status: 'sample_preview',
        value: 3400,
        sourceLabel: 'Sample itinerary (demo data)',
      },
      {
        id: 'bk_03',
        type: 'transfer',
        title: 'Sample Private Airport VIP Chauffeur & Transfer',
        supplierName: 'Sample transfer provider (illustrative)',
        referenceCode: null,
        dates: '16 Nov & 28 Nov 2026',
        guestCount: selectedTrip.party || 2,
        status: 'sample_preview',
        value: 450,
        sourceLabel: 'Sample itinerary (demo data)',
      },
      {
        id: 'bk_04',
        type: 'activity',
        title: 'Sample Table Mountain Helicopter & Wine Safari',
        supplierName: 'Sample activity provider (illustrative)',
        referenceCode: null,
        dates: '19 Nov 2026',
        guestCount: selectedTrip.party || 2,
        status: 'sample_preview',
        value: 620,
        sourceLabel: 'Sample itinerary (demo data)',
      },
    ];
  }, [selectedTrip]);

  const allBookings = useMemo(() => {
    return [...customBookings, ...initialBookings];
  }, [customBookings, initialBookings]);

  const tasks: OperationalTask[] = useMemo(() => {
    return [
      {
        id: 't1',
        title: 'Verify Passport Validity (Minimum 6 months rule for South Africa)',
        deadline: 'Complete by 15 Oct 2026',
        priority: 'critical',
        assignedTo: 'Senior Ops Lead',
      },
      {
        id: 't2',
        title: 'Confirm Special Dietary & Anniversary Champagne Setup with Silo Concierge',
        deadline: 'Due in 3 days',
        priority: 'medium',
        assignedTo: 'Bespoke Concierge Agent',
      },
      {
        id: 't3',
        title: 'Reconfirm Helicopter Landing Slot & Heli-Pad Weather Clearance',
        deadline: 'Due 48h before flight',
        priority: 'low',
        assignedTo: 'DMC Logistics Coordinator',
      },
    ];
  }, []);

  const totalIllustrativeValue = allBookings.reduce((sum, b) => sum + (b.value ?? 0), 0);

  const renderIcon = (type: BookingRecord['type']) => {
    switch (type) {
      case 'flight':
        return <Plane className='size-4 text-[#58a6ff]' />;
      case 'hotel':
        return <Building2 className='size-4 text-[#3fb950]' />;
      case 'transfer':
        return <Car className='size-4 text-[#d29922]' />;
      case 'insurance':
        return <Shield className='size-4 text-[#a371f7]' />;
      default:
        return <CalendarCheck className='size-4 text-[#58a6ff]' />;
    }
  };

  const handleRunExtraction = () => {
    if (!extractText.trim()) return;
    setIsExtracting(true);

    setTimeout(() => {
      const lower = extractText.toLowerCase();
      let type: BookingRecord['type'] = 'hotel';
      let title = 'Sample Accommodation Record';
      let supplier = 'Sample hospitality provider (illustrative)';
      let value = 1450;
      let dates = '18 Nov 2026 - 24 Nov 2026';

      const referenceMatch = extractText.match(
        /(?:pnr|booking(?:\s+reference)?|confirmation)(?:\s*(?:number|#|code|:))?\s*([A-Z0-9-]{5,})/i,
      );
      const referenceCode = referenceMatch?.[1]?.toUpperCase() ?? null;

      if (lower.includes('flight') || lower.includes('airline') || lower.includes('pnr')) {
        type = 'flight';
        title = 'Sample Air France Flight AF-842 (CDG -> CPT)';
        supplier = 'Air France (illustrative provider label)';
        dates = '15 Nov 2026';
        value = 1680;
      } else if (lower.includes('safari') || lower.includes('helicopter') || lower.includes('tour')) {
        type = 'activity';
        title = 'Sample Kruger Leopard Tracking Safari';
        supplier = 'Sample safari operator (illustrative)';
        dates = '21 Nov 2026';
        value = 890;
      } else if (lower.includes('silo') || lower.includes('hotel') || lower.includes('villa') || lower.includes('belmond')) {
        type = 'hotel';
        title = 'Sample Mount Nelson Luxury Garden Villa';
        supplier = 'Sample hotel provider (illustrative)';
        dates = '22 Nov 2026 - 26 Nov 2026';
        value = 2800;
      }

      setExtractedResult({
        type,
        title,
        supplierName: supplier,
        referenceCode,
        dates,
        guestCount: 2,
        status: 'sample_preview',
        value,
        sourceLabel: 'Local browser parse preview',
        confidenceLabel: 'Preview only — not independently verified',
      });
      setIsExtracting(false);
    }, 400);
  };

  const handleAddExtractedBooking = () => {
    if (!extractedResult) return;
    const newRecord: BookingRecord = {
      id: 'bk_custom_' + Date.now(),
      ...extractedResult,
    };
    setCustomBookings((prev) => [newRecord, ...prev]);
    setIsExtractModalOpen(false);
    setExtractText('');
    setExtractedResult(null);
  };

  return (
    <div className='p-6 space-y-6'>
      <BackToOverviewLink />

      {/* Header */}
      <div className='flex flex-col md:flex-row md:items-center md:justify-between gap-4'>
        <div>
          <h1 className='text-ui-xl font-semibold text-[#e6edf3] flex items-center gap-2'>
            <CalendarCheck className='size-6 text-[#3fb950]' />
            Bookings & Fulfillment Command
          </h1>
          <p className='text-ui-sm text-[#8b949e] mt-1'>
            Sample booking records and a local document-parse preview. No supplier, GDS, voucher, hold, payment, or booking state is connected.
          </p>
        </div>

        <div className='flex flex-wrap items-center gap-3'>
          <button
            type='button'
            onClick={() => setIsExtractModalOpen(true)}
            className='px-3.5 py-2 bg-[#238636] hover:bg-[#2ea043] text-white text-xs font-semibold rounded-md flex items-center gap-1.5 transition-colors shadow-sm'
          >
            <Sparkles className='size-3.5' />
            Preview Booking Document
          </button>

          {effectiveSelectedTripId && (
            <>
              <Link
                href={`/trips/${effectiveSelectedTripId}/ops`}
                className='px-3.5 py-2 bg-[#1f6feb] hover:bg-[#388bfd] text-white text-xs font-semibold rounded-md flex items-center gap-1.5 transition-colors shadow-sm'
              >
                <Layers className='size-3.5' />
                Open Ops Workspace
              </Link>
              <Link
                href={`/trips/${effectiveSelectedTripId}/timeline`}
                className='px-3.5 py-2 bg-[#21262d] hover:bg-[#30363d] text-[#e6edf3] text-xs font-medium rounded-md border border-[#30363d] flex items-center gap-1.5 transition-colors'
              >
                <Clock className='size-3.5 text-[#58a6ff]' />
                Trip Timeline
              </Link>
            </>
          )}
        </div>
      </div>

      <div className='flex flex-wrap items-center gap-3 rounded-lg border border-amber-500/30 bg-amber-500/5 px-4 py-3 text-xs text-amber-100'>
        <SimulatedBadge label='Sample data' />
        <span>
          This route is a visual planning sandbox. Records, references, amounts, and task states below are illustrative and are not
          provider-verified or persisted.
        </span>
      </div>

      {/* Trip Picker Selector */}
      <div className='rounded-lg border border-[#30363d] p-4 bg-[#0d1117] space-y-3'>
        <div className='flex flex-col md:flex-row md:items-center justify-between gap-3'>
          <div className='space-y-1'>
            <label htmlFor='bookings-trip-select' className='block text-xs font-medium text-[#8b949e] uppercase tracking-wider'>
              Active Trip Booking Scope
            </label>
            <select
              id='bookings-trip-select'
              data-testid='bookings-trip-select'
              value={effectiveSelectedTripId}
              onChange={(e) => handleTripChange(e.target.value)}
              className='w-full md:w-[460px] bg-[#161b22] border border-[#30363d] rounded-md p-2 text-sm text-[#e6edf3] focus:border-[#3fb950] outline-none'
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
                Travel Window: <span className='text-[#58a6ff] font-medium'>{selectedTrip.dateWindow || 'Nov 2026'}</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Metrics Row */}
      <div className='grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4'>
        <div className='rounded-lg border border-[#30363d] bg-[#0d1117] p-4 space-y-1.5'>
          <div className='text-xs font-semibold text-[#8b949e] uppercase tracking-wider flex items-center justify-between'>
            <span>Sample Service Records</span>
            <CalendarCheck className='size-4 text-[#3fb950]' />
          </div>
          <div className='text-2xl font-bold text-[#e6edf3]'>{allBookings.length} Samples</div>
          <div className='text-xs text-[#8b949e]'>Illustrative flights, hotels, transfers, and tours</div>
        </div>

        <div className='rounded-lg border border-[#30363d] bg-[#0d1117] p-4 space-y-1.5'>
          <div className='text-xs font-semibold text-[#8b949e] uppercase tracking-wider flex items-center justify-between'>
            <span>Illustrative Itinerary Value</span>
            <CheckCircle2 className='size-4 text-[#58a6ff]' />
          </div>
          <div className='text-2xl font-bold text-[#58a6ff]'>${totalIllustrativeValue.toLocaleString()}</div>
          <div className='text-xs text-[#8b949e]'>Sample amounts only — no charges or supplier contracts</div>
        </div>

        <div className='rounded-lg border border-[#30363d] bg-[#0d1117] p-4 space-y-1.5'>
          <div className='text-xs font-semibold text-[#8b949e] uppercase tracking-wider flex items-center justify-between'>
            <span>Supplier Holds</span>
            <Clock className='size-4 text-[#d29922]' />
          </div>
          <div className='text-2xl font-bold text-[#d29922]'>Unavailable</div>
          <div className='text-xs text-[#8b949e]'>Provider connection required to retrieve live holds</div>
        </div>

        <div className='rounded-lg border border-[#30363d] bg-[#0d1117] p-4 space-y-1.5'>
          <div className='text-xs font-semibold text-[#8b949e] uppercase tracking-wider flex items-center justify-between'>
            <span>Provider Artifacts</span>
            <Key className='size-4 text-[#a371f7]' />
          </div>
          <div className='text-2xl font-bold text-[#a371f7]'>Not connected</div>
          <div className='text-xs text-[#8b949e]'>Secure artifacts appear after a real booking integration</div>
        </div>
      </div>

      {/* Bookings Table & Operational Tasks */}
      {selectedTrip ? (
        <div className='grid gap-6 lg:grid-cols-3'>
          {/* Main Bookings Roster */}
          <div className='lg:col-span-2 space-y-4'>
            <div className='rounded-lg border border-[#30363d] bg-[#0d1117] overflow-hidden'>
              <div className='p-4 border-b border-[#30363d] flex items-center justify-between bg-[#161b22]'>
                <div className='flex items-center gap-2 font-semibold text-sm text-[#e6edf3]'>
                  <FileCheck className='size-4 text-[#3fb950]' />
                  <span>Sample Booking Records</span>
                </div>
                <span className='text-xs text-[#d29922]'>No live GDS/DMC connection</span>
              </div>

              <div className='overflow-x-auto'>
                <table className='w-full text-left text-sm'>
                  <thead>
                    <tr className='border-b border-[#30363d] bg-[#0d1117] text-xs font-semibold text-[#8b949e] uppercase tracking-wider'>
                      <th className='p-3.5'>Service / Supplier</th>
                      <th className='p-3.5'>Source Reference</th>
                      <th className='p-3.5'>Schedule</th>
                      <th className='p-3.5'>Status</th>
                      <th className='p-3.5 text-right'>Value</th>
                    </tr>
                  </thead>
                  <tbody className='divide-y divide-[#30363d]'>
                    {allBookings.map((b) => (
                      <tr key={b.id} className='hover:bg-[#161b22] transition-colors'>
                        <td className='p-3.5'>
                          <div className='flex items-start gap-2.5'>
                            <div className='p-1.5 bg-[#161b22] rounded border border-[#30363d] mt-0.5'>
                              {renderIcon(b.type)}
                            </div>
                            <div>
                              <div className='font-medium text-[#e6edf3]'>{b.title}</div>
                              <div className='text-xs text-[#8b949e]'>{b.supplierName}</div>
                            </div>
                          </div>
                        </td>

                        <td className='p-3.5'>
                          <div className='flex items-center gap-1.5'>
                            <span className='font-mono font-semibold text-xs text-[#58a6ff] bg-[#1f6feb]/10 px-2 py-0.5 rounded border border-[#1f6feb]/30'>
                              {b.referenceCode ?? 'Not verified'}
                            </span>
                          </div>
                          <div className='text-[11px] text-[#d29922] mt-0.5'>{b.sourceLabel}</div>
                        </td>

                        <td className='p-3.5 text-xs text-[#8b949e]'>{b.dates}</td>

                        <td className='p-3.5'>
                          <span
                            className={`px-2 py-0.5 rounded text-xs font-medium ${
                              'bg-[#d29922]/20 text-[#d29922] border border-[#d29922]/40'
                            }`}
                          >
                            Sample / unverified
                          </span>
                        </td>

                        <td className='p-3.5 text-right font-mono font-semibold text-[#e6edf3]'>
                          {b.value === null ? 'Not available' : `~$${b.value.toLocaleString()} sample`}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Operational Task Deadlines */}
          <div className='space-y-4'>
            <div className='rounded-lg border border-[#30363d] bg-[#0d1117] p-4 space-y-4'>
              <div className='flex items-center justify-between border-b border-[#30363d] pb-3'>
                <div className='font-semibold text-sm text-[#e6edf3] flex items-center gap-2'>
                  <Clock className='size-4 text-[#d29922]' />
                  <span>Sample Operational Checklist</span>
                </div>
                <span className='text-xs text-[#d29922]'>Not connected</span>
              </div>

              <div className='space-y-3'>
                {tasks.map((task) => (
                  <div
                    key={task.id}
                    className='p-3 bg-[#161b22] rounded-md border border-[#30363d] space-y-1.5'
                  >
                    <div className='flex items-start justify-between gap-2'>
                      <div className='text-xs font-medium text-[#e6edf3]'>{task.title}</div>
                      <span className='px-1.5 py-0.5 text-[10px] font-semibold bg-[#d29922]/20 text-[#d29922] rounded border border-[#d29922]/30 shrink-0'>
                        SAMPLE
                      </span>
                    </div>
                    <div className='flex items-center justify-between text-[11px] text-[#8b949e]'>
                      <span>{task.deadline}</span>
                      <span className='text-[#58a6ff]'>{task.assignedTo}</span>
                    </div>
                  </div>
                ))}
              </div>

              <div className='pt-2 border-t border-[#30363d]'>
                <Link
                  href={`/trips/${effectiveSelectedTripId}/ops`}
                  className='w-full py-2 bg-[#21262d] hover:bg-[#30363d] text-[#e6edf3] text-xs font-semibold rounded-md border border-[#30363d] flex items-center justify-center gap-1.5 transition-colors'
                >
                  <span>Manage All Operational Tasks in Ops</span>
                  <ArrowRight className='size-3.5' />
                </Link>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className='rounded-lg border border-[#30363d] bg-[#0d1117] p-8 text-center text-[#8b949e]'>
          {isLoading ? 'Loading operational bookings…' : 'No trip selected. Choose a trip above to inspect bookings.'}
        </div>
      )}

      {/* Auto-Extract Voucher Modal */}
      {isExtractModalOpen && (
        <div className='fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4'>
          <div
            role='dialog'
            aria-modal='true'
            aria-labelledby='booking-preview-dialog-title'
            className='w-full max-w-lg bg-[#0d1117] border border-[#30363d] rounded-lg shadow-xl p-6 space-y-4'
          >
            <div className='flex items-center justify-between border-b border-[#30363d] pb-3'>
              <div className='flex items-center gap-2 font-semibold text-base text-[#e6edf3]'>
                <Sparkles className='size-5 text-[#3fb950]' />
                <span id='booking-preview-dialog-title'>Preview Booking Document</span>
              </div>
              <button
                type='button'
                onClick={() => {
                  setIsExtractModalOpen(false);
                  setExtractedResult(null);
                }}
                className='text-[#8b949e] hover:text-[#e6edf3] text-sm'
              >
                ✕
              </button>
            </div>

            <div className='space-y-3 text-xs text-[#c9d1d9]'>
              <div>
                <label className='block text-[#8b949e] mb-1 font-medium'>
                  Paste Confirmation Email, E-Ticket Text, or Voucher Snippet:
                </label>
                <textarea
                  rows={4}
                  placeholder='e.g. Booking Reference: AF79KZ, Flight Air France AF842 from CDG to CPT on 15 Nov 2026. Total Amount USD 1,680.'
                  value={extractText}
                  onChange={(e) => setExtractText(e.target.value)}
                  className='w-full p-2.5 bg-[#161b22] border border-[#30363d] rounded text-sm text-[#e6edf3] outline-none focus:border-[#3fb950]'
                />
              </div>

              {/* Sample Quick Pastes */}
              <div className='flex items-center gap-2 pt-1'>
                <span className='text-[11px] text-[#8b949e]'>Sample input:</span>
                <button
                  type='button'
                  onClick={() => setExtractText('Booking Confirmation # BM-9942 from Belmond Mount Nelson Luxury Villa. Dates: 22 Nov 2026 to 26 Nov 2026. Total: USD 2,800. Guests: 2.')}
                  className='px-2 py-0.5 bg-[#161b22] hover:bg-[#30363d] border border-[#30363d] rounded text-[11px] text-[#58a6ff]'
                >
                  Belmond Hotel
                </button>
                <button
                  type='button'
                  onClick={() => setExtractText('Air France PNR: AF79KZ. Flight AF-842 CDG-CPT on 15 Nov 2026. Total cost: USD 1,680.')}
                  className='px-2 py-0.5 bg-[#161b22] hover:bg-[#30363d] border border-[#30363d] rounded text-[11px] text-[#58a6ff]'
                >
                  Air France PNR
                </button>
              </div>

              {/* Extraction Trigger */}
              {!extractedResult && (
                <button
                  type='button'
                  onClick={handleRunExtraction}
                  disabled={isExtracting || !extractText.trim()}
                  className='w-full py-2 bg-[#238636] hover:bg-[#2ea043] disabled:opacity-50 text-white rounded font-semibold flex items-center justify-center gap-1.5 transition-colors'
                >
                  {isExtracting ? (
                    <span>Parsing locally for preview…</span>
                  ) : (
                    <>
                      <Sparkles className='size-3.5' />
                      <span>Preview Parsed Details</span>
                    </>
                  )}
                </button>
              )}

              {/* Extracted Preview Card */}
              {extractedResult && (
                <div className='p-3.5 bg-[#161b22] border border-[#238636]/40 rounded-lg space-y-2'>
                  <div className='flex items-center justify-between'>
                    <span className='text-xs font-semibold text-[#3fb950] flex items-center gap-1'>
                      <Sparkles className='size-3.5' />
                      Local parse preview — not independently verified
                    </span>
                    <span className='text-[10px] uppercase font-mono px-1.5 py-0.5 bg-[#238636]/20 text-[#3fb950] rounded border border-[#238636]/30'>
                      {extractedResult.type}
                    </span>
                  </div>

                  <div className='space-y-1 text-xs pt-1'>
                    <div className='font-semibold text-[#e6edf3]'>{extractedResult.title}</div>
                    <div className='text-[#8b949e]'>Supplier: <span className='text-[#c9d1d9]'>{extractedResult.supplierName}</span></div>
                    <div className='text-[#8b949e]'>Source reference (unverified): <span className='font-mono font-bold text-[#58a6ff]'>{extractedResult.referenceCode ?? 'Not detected'}</span></div>
                    <div className='text-[#8b949e]'>Dates: <span className='text-[#c9d1d9]'>{extractedResult.dates}</span></div>
                    <div className='text-[#8b949e]'>Illustrative value: <span className='font-mono font-bold text-[#3fb950]'>${extractedResult.value?.toLocaleString() ?? 'Not available'}</span></div>
                    <div className='text-[#d29922]'>{extractedResult.confidenceLabel}</div>
                  </div>
                </div>
              )}
            </div>

            <div className='flex justify-end gap-2 pt-2 border-t border-[#30363d]'>
              <button
                type='button'
                onClick={() => {
                  setIsExtractModalOpen(false);
                  setExtractedResult(null);
                }}
                className='px-3.5 py-1.5 bg-[#21262d] text-[#e6edf3] rounded text-xs hover:bg-[#30363d] border border-[#30363d]'
              >
                Cancel
              </button>
              {extractedResult && (
                <button
                  type='button'
                  onClick={handleAddExtractedBooking}
                  className='px-3.5 py-1.5 bg-[#238636] text-white rounded text-xs font-semibold hover:bg-[#2ea043] flex items-center gap-1.5'
                >
                  <Check className='size-3.5' />
                  Add Sample to This View
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
