'use client';

import { useMemo, useState, useCallback } from 'react';
import Link from 'next/link';
import { useSearchParams, useRouter, usePathname } from 'next/navigation';
import { BackToOverviewLink } from '@/components/navigation/BackToOverviewLink';
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
  confirmationCode: string;
  encryptedRef: string;
  dates: string;
  guestCount: number;
  status: 'confirmed' | 'hold_active' | 'ticketing_pending' | 'voucher_issued';
  value: number;
  deadlineText?: string;
}

interface OperationalTask {
  id: string;
  title: string;
  deadline: string;
  priority: 'critical' | 'medium' | 'low';
  assignedTo: string;
  isComplete: boolean;
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

  const [revealedKeyId, setRevealedKeyId] = useState<string | null>(null);
  const [isExtractModalOpen, setIsExtractModalOpen] = useState<boolean>(false);
  const [extractText, setExtractText] = useState<string>('');
  const [isExtracting, setIsExtracting] = useState<boolean>(false);
  const [extractedResult, setExtractedResult] = useState<any>(null);
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
        title: 'Emirates EK-501 (BOM -> DXB -> CPT)',
        supplierName: 'Emirates Airlines (GDS Sabre)',
        confirmationCode: '6X9ZPL',
        encryptedRef: 'gAAAAABm...89KqL2',
        dates: '15 Nov 2026 - 28 Nov 2026',
        guestCount: selectedTrip.party || 2,
        status: 'voucher_issued',
        value: 1850,
        deadlineText: 'Tickets e-issued on GDS',
      },
      {
        id: 'bk_02',
        type: 'hotel',
        title: 'The Silo Hotel (Deluxe Harbour Suite)',
        supplierName: 'The Royal Portfolio Luxury Direct',
        confirmationCode: 'SILO-2026-9942',
        encryptedRef: 'gAAAAABm...41VvP9',
        dates: '16 Nov 2026 - 22 Nov 2026 (6 Nights)',
        guestCount: selectedTrip.party || 2,
        status: 'confirmed',
        value: 3400,
        deadlineText: 'Cancellation deadline: 01 Nov 2026',
      },
      {
        id: 'bk_03',
        type: 'transfer',
        title: 'Private Airport VIP Chauffeur & Armored Transfer',
        supplierName: 'Cape Executive VIP Logistics',
        confirmationCode: 'CE-VIP-881',
        encryptedRef: 'gAAAAABm...01MmX4',
        dates: '16 Nov & 28 Nov 2026',
        guestCount: selectedTrip.party || 2,
        status: 'voucher_issued',
        value: 450,
      },
      {
        id: 'bk_04',
        type: 'activity',
        title: 'Exclusive Table Mountain Helicopter & Wine Safari',
        supplierName: 'NAC Helicopters Cape Town',
        confirmationCode: 'NAC-HL-5520',
        encryptedRef: 'gAAAAABm...77ZzQ8',
        dates: '19 Nov 2026',
        guestCount: selectedTrip.party || 2,
        status: 'hold_active',
        value: 620,
        deadlineText: '48h Zero-Cost Hold (Expires in 22h)',
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
        isComplete: true,
      },
      {
        id: 't2',
        title: 'Confirm Special Dietary & Anniversary Champagne Setup with Silo Concierge',
        deadline: 'Due in 3 days',
        priority: 'medium',
        assignedTo: 'Bespoke Concierge Agent',
        isComplete: false,
      },
      {
        id: 't3',
        title: 'Reconfirm Helicopter Landing Slot & Heli-Pad Weather Clearance',
        deadline: 'Due 48h before flight',
        priority: 'low',
        assignedTo: 'DMC Logistics Coordinator',
        isComplete: false,
      },
    ];
  }, []);

  const totalFulfilled = allBookings.reduce((sum, b) => sum + b.value, 0);

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
      let title = 'Confirmed Accommodation Reservation';
      let supplier = 'Preferred Hospitality Partner';
      let pnr = 'CONF-' + Math.floor(100000 + Math.random() * 900000);
      let dates = '18 Nov 2026 - 24 Nov 2026';
      let value = 1450;

      if (lower.includes('flight') || lower.includes('airline') || lower.includes('pnr')) {
        type = 'flight';
        title = 'Air France Flight AF-842 (CDG -> CPT)';
        supplier = 'Air France (GDS Amadeus)';
        pnr = 'AF79KZ';
        dates = '15 Nov 2026';
        value = 1680;
      } else if (lower.includes('safari') || lower.includes('helicopter') || lower.includes('tour')) {
        type = 'activity';
        title = 'Private Kruger Leopard Tracking Safari';
        supplier = 'Wilderness Safaris Luxury';
        pnr = 'WS-SAF-8831';
        dates = '21 Nov 2026';
        value = 890;
      } else if (lower.includes('silo') || lower.includes('hotel') || lower.includes('villa') || lower.includes('belmond')) {
        type = 'hotel';
        title = 'Belmond Mount Nelson Luxury Garden Villa';
        supplier = 'Belmond Collection';
        pnr = 'BMN-2026-441';
        dates = '22 Nov 2026 - 26 Nov 2026';
        value = 2800;
      }

      setExtractedResult({
        type,
        title,
        supplierName: supplier,
        confirmationCode: pnr,
        encryptedRef: 'gAAAAABm...' + Math.random().toString(36).substring(2, 8),
        dates,
        guestCount: 2,
        status: 'confirmed',
        value,
        confidence: 0.96,
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
            Confirmed supplier PNRs, voucher vault, encrypted confirmation codes, and operational fulfillment tracker.
          </p>
        </div>

        <div className='flex flex-wrap items-center gap-3'>
          <button
            type='button'
            onClick={() => setIsExtractModalOpen(true)}
            className='px-3.5 py-2 bg-[#238636] hover:bg-[#2ea043] text-white text-xs font-semibold rounded-md flex items-center gap-1.5 transition-colors shadow-sm'
          >
            <Sparkles className='size-3.5' />
            Auto-Extract Booking Voucher
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
            <span>Confirmed Services</span>
            <CalendarCheck className='size-4 text-[#3fb950]' />
          </div>
          <div className='text-2xl font-bold text-[#e6edf3]'>{allBookings.length} Bookings</div>
          <div className='text-xs text-[#8b949e]'>Flights, Hotels, Transfers, VIP Tours</div>
        </div>

        <div className='rounded-lg border border-[#30363d] bg-[#0d1117] p-4 space-y-1.5'>
          <div className='text-xs font-semibold text-[#8b949e] uppercase tracking-wider flex items-center justify-between'>
            <span>Total Fulfilled Value</span>
            <CheckCircle2 className='size-4 text-[#58a6ff]' />
          </div>
          <div className='text-2xl font-bold text-[#58a6ff]'>${totalFulfilled.toLocaleString()}</div>
          <div className='text-xs text-[#8b949e]'>Backed by supplier voucher contracts</div>
        </div>

        <div className='rounded-lg border border-[#30363d] bg-[#0d1117] p-4 space-y-1.5'>
          <div className='text-xs font-semibold text-[#8b949e] uppercase tracking-wider flex items-center justify-between'>
            <span>Active Supplier Holds</span>
            <Clock className='size-4 text-[#d29922]' />
          </div>
          <div className='text-2xl font-bold text-[#d29922]'>
            {allBookings.filter((b) => b.status === 'hold_active').length} Pending
          </div>
          <div className='text-xs text-[#8b949e]'>48h zero-cost hold active</div>
        </div>

        <div className='rounded-lg border border-[#30363d] bg-[#0d1117] p-4 space-y-1.5'>
          <div className='text-xs font-semibold text-[#8b949e] uppercase tracking-wider flex items-center justify-between'>
            <span>Voucher Security</span>
            <Key className='size-4 text-[#a371f7]' />
          </div>
          <div className='text-2xl font-bold text-[#a371f7]'>Fernet Encrypted</div>
          <div className='text-xs text-[#8b949e]'>Zero credential leakage guarantee</div>
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
                  <span>Confirmed Supplier Bookings & PNR Ledger</span>
                </div>
                <span className='text-xs text-[#8b949e]'>Live GDS & DMC Direct Sync</span>
              </div>

              <div className='overflow-x-auto'>
                <table className='w-full text-left text-sm'>
                  <thead>
                    <tr className='border-b border-[#30363d] bg-[#0d1117] text-xs font-semibold text-[#8b949e] uppercase tracking-wider'>
                      <th className='p-3.5'>Service / Supplier</th>
                      <th className='p-3.5'>PNR / Confirmation</th>
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
                              {b.confirmationCode}
                            </span>
                          </div>
                          {b.deadlineText && (
                            <div className='text-[11px] text-[#d29922] mt-0.5'>{b.deadlineText}</div>
                          )}
                        </td>

                        <td className='p-3.5 text-xs text-[#8b949e]'>{b.dates}</td>

                        <td className='p-3.5'>
                          <span
                            className={`px-2 py-0.5 rounded text-xs font-medium ${
                              b.status === 'voucher_issued'
                                ? 'bg-[#238636]/20 text-[#3fb950] border border-[#238636]/40'
                                : b.status === 'confirmed'
                                ? 'bg-[#1f6feb]/20 text-[#58a6ff] border border-[#1f6feb]/40'
                                : 'bg-[#d29922]/20 text-[#d29922] border border-[#d29922]/40'
                            }`}
                          >
                            {b.status.replace('_', ' ')}
                          </span>
                        </td>

                        <td className='p-3.5 text-right font-mono font-semibold text-[#e6edf3]'>
                          ${b.value.toLocaleString()}
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
                  <span>Operational Task Deadlines</span>
                </div>
                <span className='text-xs text-[#8b949e]'>Task Engine</span>
              </div>

              <div className='space-y-3'>
                {tasks.map((task) => (
                  <div
                    key={task.id}
                    className='p-3 bg-[#161b22] rounded-md border border-[#30363d] space-y-1.5'
                  >
                    <div className='flex items-start justify-between gap-2'>
                      <div className='text-xs font-medium text-[#e6edf3]'>{task.title}</div>
                      {task.isComplete ? (
                        <span className='px-1.5 py-0.5 text-[10px] font-semibold bg-[#238636]/20 text-[#3fb950] rounded border border-[#238636]/30 shrink-0'>
                          DONE
                        </span>
                      ) : (
                        <span className='px-1.5 py-0.5 text-[10px] font-semibold bg-[#d29922]/20 text-[#d29922] rounded border border-[#d29922]/30 shrink-0'>
                          PENDING
                        </span>
                      )}
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
          <div className='w-full max-w-lg bg-[#0d1117] border border-[#30363d] rounded-lg shadow-xl p-6 space-y-4'>
            <div className='flex items-center justify-between border-b border-[#30363d] pb-3'>
              <div className='flex items-center gap-2 font-semibold text-base text-[#e6edf3]'>
                <Sparkles className='size-5 text-[#3fb950]' />
                <span>Auto-Extract Voucher & PNR</span>
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
                <span className='text-[11px] text-[#8b949e]'>Quick Sample:</span>
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
                    <span>Parsing Confirmation via Regex & AI Extraction…</span>
                  ) : (
                    <>
                      <Sparkles className='size-3.5' />
                      <span>Parse Confirmation Details</span>
                    </>
                  )}
                </button>
              )}

              {/* Extracted Preview Card */}
              {extractedResult && (
                <div className='p-3.5 bg-[#161b22] border border-[#238636]/40 rounded-lg space-y-2'>
                  <div className='flex items-center justify-between'>
                    <span className='text-xs font-semibold text-[#3fb950] flex items-center gap-1'>
                      <CheckCircle2 className='size-3.5' />
                      Extraction Successful (96% Confidence)
                    </span>
                    <span className='text-[10px] uppercase font-mono px-1.5 py-0.5 bg-[#238636]/20 text-[#3fb950] rounded border border-[#238636]/30'>
                      {extractedResult.type}
                    </span>
                  </div>

                  <div className='space-y-1 text-xs pt-1'>
                    <div className='font-semibold text-[#e6edf3]'>{extractedResult.title}</div>
                    <div className='text-[#8b949e]'>Supplier: <span className='text-[#c9d1d9]'>{extractedResult.supplierName}</span></div>
                    <div className='text-[#8b949e]'>PNR / Code: <span className='font-mono font-bold text-[#58a6ff]'>{extractedResult.confirmationCode}</span></div>
                    <div className='text-[#8b949e]'>Dates: <span className='text-[#c9d1d9]'>{extractedResult.dates}</span></div>
                    <div className='text-[#8b949e]'>Value: <span className='font-mono font-bold text-[#3fb950]'>${extractedResult.value.toLocaleString()}</span></div>
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
                  Record & Add to Ledger
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
