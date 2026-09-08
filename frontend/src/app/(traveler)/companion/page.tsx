'use client';

import React, { Suspense, useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import {
  Plane,
  MapPin,
  Calendar,
  AlertTriangle,
  Radio,
  FileText,
  ShieldCheck,
  CreditCard,
  PhoneCall,
  Clock,
  Compass,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Download,
} from 'lucide-react';

interface JourneyNodeDTO {
  node_id: string;
  node_type: string;
  title: string;
  start_time: string;
  end_time: string;
  location: string;
  provider: string;
  confirmation_code?: string;
  metadata?: Record<string, unknown>;
}

interface BookingConfirmationDTO {
  pnr_locator: string;
  e_ticket_number: string;
  vcc_last4: string;
  status: string;
  fulfilled_at: string;
  reality_tier?: string;
  provider_connected?: boolean;
}

interface TripGraphData {
  status?: string;
  ok?: boolean;
  exists?: boolean;
  reality_tier?: string;
  provider_connected?: boolean;
  trip_id: string;
  destination?: string | null;
  booking_confirmation?: BookingConfirmationDTO | null;
  nodes?: JourneyNodeDTO[];
  edges?: Array<{ from_node_id: string; to_node_id: string; relation: string; min_connection_minutes: number }>;
}

interface TravelerCompanionContentProps {
  tripId: string | null;
  shareToken: string | null;
}

type TripRequestState = 'idle' | 'loading' | 'ready' | 'denied' | 'unavailable' | 'invalid' | 'empty' | 'transport-error';

function TravelerCompanionContent({ tripId, shareToken }: TravelerCompanionContentProps) {
  const [sosActive, setSosActive] = useState(false);
  const [sosDemoComplete, setSosDemoComplete] = useState(false);
  const [activeDay, setActiveDay] = useState(1);
  const [tripData, setTripData] = useState<TripGraphData | null>(null);
  // The route key remounts this data-owning component for every exact
  // tripId+token identity, so transient request state cannot cross identities.
  const [tripRequestState, setTripRequestState] = useState<TripRequestState>(
    tripId && shareToken ? 'loading' : 'idle',
  );

  useEffect(() => {
    // Service worker registration is a mount-only external-system sync.
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js').catch((err) => console.log('SW reg error:', err));
    }
  }, []);

  // Capability-gated journey graphs stay online-only until the product has a
  // bounded cache expiry/revocation policy. Legacy localStorage entries are
  // intentionally preserved, but this route neither reads nor writes them.
  useEffect(() => {
    let cancelled = false;
    const abortController = new AbortController();

    if (!tripId || !shareToken) {
      return () => {
        cancelled = true;
        abortController.abort();
      };
    }

    const loadTripGraph = async () => {
      try {
        const res = await fetch(
          `/api/public/journey-graph/${encodeURIComponent(tripId)}?token=${encodeURIComponent(shareToken)}`,
          { cache: 'no-store', signal: abortController.signal },
        );
        if (!res.ok) {
          if (cancelled) return;
          setTripData(null);
          setTripRequestState(res.status === 401 || res.status === 403 || res.status === 404 ? 'denied' : 'unavailable');
          return;
        }
        let data: TripGraphData;
        try {
          const rawData: unknown = await res.json();
          const rawRecord =
            rawData && typeof rawData === 'object' && !Array.isArray(rawData)
              ? (rawData as {
                  trip_id?: unknown;
                  nodes?: unknown;
                  exists?: unknown;
                  provider_connected?: unknown;
                  destination?: unknown;
                })
              : {};
          const nodesAreValid =
            (rawRecord.exists === false && rawRecord.nodes === undefined) ||
            (Array.isArray(rawRecord.nodes) &&
              rawRecord.nodes.every(
                (node) =>
                  node &&
                  typeof node === 'object' &&
                  typeof (node as { node_type?: unknown }).node_type === 'string',
              ));
          if (
            !rawData ||
            typeof rawData !== 'object' ||
            Array.isArray(rawData) ||
            typeof rawRecord.trip_id !== 'string' ||
            !nodesAreValid ||
            (rawRecord.exists !== undefined && typeof rawRecord.exists !== 'boolean') ||
            (rawRecord.provider_connected !== undefined && typeof rawRecord.provider_connected !== 'boolean') ||
            (rawRecord.destination !== undefined &&
              rawRecord.destination !== null &&
              typeof rawRecord.destination !== 'string')
          ) {
            if (cancelled) return;
            setTripData(null);
            setTripRequestState('invalid');
            return;
          }
          data = rawData as TripGraphData;
        } catch {
          if (cancelled) return;
          setTripData(null);
          setTripRequestState('invalid');
          return;
        }
        if (cancelled) return;
        if (data.trip_id !== tripId) {
          setTripData(null);
          setTripRequestState('invalid');
          return;
        }
        if (data.exists === false || !data.nodes || data.nodes.length === 0) {
          setTripData(null);
          setTripRequestState('empty');
          return;
        }
        setTripData(data);
        setTripRequestState('ready');
      } catch (error) {
        if (cancelled || (error instanceof Error && error.name === 'AbortError')) return;
        setTripData(null);
        setTripRequestState('transport-error');
      }
    };

    void loadTripGraph();

    return () => {
      cancelled = true;
      abortController.abort();
    };
  }, [shareToken, tripId]);

  const handleTriggerSOS = () => {
    setSosActive(true);
    setTimeout(() => {
      setSosDemoComplete(true);
    }, 1500);
  };

  const isSampleDemo = !tripId;
  const currentTripData = tripData?.trip_id === tripId ? tripData : null;
  const nodes = currentTripData?.nodes ?? [];
  const hasGraph = nodes.length > 0;
  const flightNode = nodes.find((n) => n.node_type === 'FLIGHT');
  const hotelNode = nodes.find((n) => n.node_type === 'HOTEL_CHECKIN');
  const transferNode = nodes.find((n) => n.node_type === 'TRANSFER');
  const pnr = hasGraph
    ? flightNode?.confirmation_code || currentTripData?.booking_confirmation?.pnr_locator || null
    : isSampleDemo
      ? 'SAMPLE'
      : null;
  const eTicket = hasGraph
    ? currentTripData?.booking_confirmation?.e_ticket_number || null
    : isSampleDemo
      ? 'SAMPLE'
      : null;
  const hotelVoucher = hasGraph
    ? hotelNode?.confirmation_code || null
    : isSampleDemo
      ? 'SAMPLE'
      : null;
  const flightStatusLabel = hasGraph
    ? 'NOT CONFIRMED YET'
    : isSampleDemo
      ? 'SAMPLE'
      : 'NOT CONFIRMED YET';
  const destinationLabel = hasGraph
    ? currentTripData?.destination || 'Destination on file'
    : isSampleDemo
      ? 'Sample itinerary'
      : 'Itinerary not yet available';

  // Part-H P1 + Part-J #4 (2026-09-07): simulator-generated identifiers must
  // never read as live booking truth. The backend now attests provider status
  // at the TOP LEVEL of the journey-graph response, derived fail-closed; the
  // companion trusts only that explicit attestation, with the legacy per-node
  // fallback for old response shapes; persisted payloads are not read.
  const isLive =
    hasGraph &&
    (currentTripData?.provider_connected === true ||
      (currentTripData?.provider_connected === undefined &&
        currentTripData?.booking_confirmation?.provider_connected === true &&
        nodes.every((n) => n?.metadata?.provider_connected !== false)));
  const isPreview = hasGraph && !isLive;
  const needsToken = Boolean(tripId && !shareToken);
  const itineraryStateLabel = isSampleDemo
    ? 'Sample data'
    : needsToken
      ? 'Itinerary unavailable'
      : tripRequestState === 'loading'
        ? 'Checking itinerary'
        : tripRequestState === 'denied'
          ? 'Itinerary access denied'
          : 'Itinerary unavailable';
  const itineraryStateMessage = isSampleDemo
    ? 'Demo preview with sample itinerary content — no real bookings, beacons, or transmissions are behind this page.'
    : needsToken
      ? 'This itinerary can only be opened through the private link your travel advisor sent you.'
      : tripRequestState === 'loading'
        ? 'Checking your private itinerary link…'
        : tripRequestState === 'denied'
          ? 'This private link could not be opened. Ask your travel advisor for a fresh private link.'
          : tripRequestState === 'transport-error'
            ? "We couldn't reach your private itinerary right now. No cached itinerary is shown; reconnect and try again."
            : tripRequestState === 'unavailable'
              ? 'The itinerary service is temporarily unavailable. No cached itinerary is shown; please try again later.'
            : tripRequestState === 'invalid'
              ? 'The private itinerary response was not valid. No cached itinerary is shown; ask your travel advisor to retry the link.'
              : 'Your itinerary will appear here as your travel advisor confirms bookings.';

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 font-sans pb-16">
      {/* Mobile Sticky App Header */}
      <header className="sticky top-0 z-50 bg-[#090d16]/90 backdrop-blur-md border-b border-slate-800/80 px-4 py-3.5 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-indigo-600 to-indigo-400 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/20">
            W
          </div>
          <div>
            <span className="text-sm font-bold text-white tracking-tight block">Waypoint Companion</span>
            <span className="text-[10px] text-emerald-400 font-mono flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
              Trip Sync: {destinationLabel}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {hasGraph && !isSampleDemo && (
            <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-950 text-emerald-300 border border-emerald-700">
              Itinerary loaded
            </span>
          )}
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-md mx-auto p-4 space-y-4">
        {hasGraph && currentTripData?.booking_confirmation && isPreview ? (
          <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-[11px] text-amber-200 flex items-center gap-2">
            <span className="px-2 py-0.5 rounded-lg bg-amber-500/10 text-amber-300 text-[10px] font-semibold uppercase tracking-wide border border-amber-500/30">
              Preview itinerary
            </span>
            <span>
              Prepared with your travel advisor&apos;s planning tools. The
              references below are placeholders — they become real once your
              bookings are confirmed.
            </span>
          </div>
        ) : hasGraph && currentTripData?.booking_confirmation ? (
          <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-3 py-2 text-[11px] text-emerald-200 flex items-center gap-2">
            <span className="px-2 py-0.5 rounded-lg bg-emerald-500/20 text-emerald-300 text-[10px] font-semibold uppercase tracking-wide border border-emerald-500/40">
              Your itinerary
            </span>
            <span>
              {currentTripData.destination ? `Your trip to ${currentTripData.destination}.` : 'Your trip.'}{' '}
              Booking reference: {pnr ?? 'not issued yet'} · E-Ticket: {eTicket ?? 'not issued yet'}.
            </span>
          </div>
        ) : (
          <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-[11px] text-amber-200 flex items-center gap-2">
            <span className="px-2 py-0.5 rounded-lg bg-amber-500/10 text-amber-300 text-[10px] font-semibold uppercase tracking-wide border border-amber-500/30">
              {itineraryStateLabel}
            </span>
            <span>{itineraryStateMessage}</span>
          </div>
        )}

        {/* Live Flight Status Card */}
        <section className="rounded-2xl border border-indigo-500/30 bg-gradient-to-br from-indigo-950/40 via-slate-900 to-slate-900 p-4 shadow-xl relative overflow-hidden">
          <div className="flex items-center justify-between text-xs text-indigo-400 font-mono">
            <span className="flex items-center gap-1.5">
              <Plane className="w-3.5 h-3.5" /> Next Flight ·{' '}
              {hasGraph
                ? flightNode?.provider || 'Carrier on your itinerary'
                : isSampleDemo
                  ? 'British Airways (sample)'
                  : '—'}
            </span>
            <span className="text-amber-300 font-bold px-2 py-0.5 rounded-full bg-amber-500/10 border border-amber-500/20">
              {flightStatusLabel}
            </span>
          </div>

          <div className="mt-3 flex items-center justify-between">
            <div>
              <span className="text-2xl font-black tracking-tight text-white">
                {hasGraph ? (flightNode?.location || '—') : isSampleDemo ? 'LHR' : '—'}
              </span>
              <span className="text-[11px] text-slate-400 block">
                {hasGraph ? (flightNode?.title || 'Flight details being confirmed') : isSampleDemo ? 'London Heathrow (sample)' : 'Origin to be confirmed'}
              </span>
            </div>
            <div className="flex flex-col items-center px-4">
              <span className="text-[10px] text-slate-400 font-mono">
                {hasGraph
                  ? 'Flight duration to be confirmed'
                  : isSampleDemo
                    ? '7h 30m · Nonstop (sample)'
                    : '—'}
              </span>
              <div className="w-24 h-[2px] bg-slate-700 my-1 relative flex items-center justify-center">
                <Plane className="w-3 h-3 text-indigo-400 absolute" />
              </div>
              <span className="text-[10px] text-indigo-300 font-mono">{pnr ?? 'no PNR'}</span>
            </div>
            <div className="text-right">
              <span className="text-2xl font-black tracking-tight text-white">
                {hasGraph
                  ? (currentTripData?.destination || '—').slice(0, 3).toUpperCase()
                  : isSampleDemo
                    ? 'HND'
                    : '—'}
              </span>
              <span className="text-[11px] text-slate-400 block">
                {hasGraph ? currentTripData?.destination : isSampleDemo ? 'Sample destination' : 'Destination to be confirmed'}
              </span>
            </div>
          </div>

          <div className="mt-3 pt-3 border-t border-slate-800 flex items-center justify-between text-xs">
            <div>
              <span className="text-slate-400 block text-[10px]">TERMINAL / GATE</span>
              <span className="font-bold text-white">{hasGraph || isSampleDemo ? 'Assigned at check-in' : '—'}</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[10px]">SEAT / CLASS</span>
              <span className="font-bold text-indigo-300">{hasGraph || isSampleDemo ? 'Unknown' : '—'}</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[10px]">BOARDING</span>
              <span className="font-bold text-emerald-400">{hasGraph || isSampleDemo ? 'Unknown' : '—'}</span>
            </div>
          </div>
        </section>

        {/* Emergency SOS Duty-of-Care Beacon */}
        <section className={`rounded-2xl border transition-all duration-300 p-4 ${
          sosActive
            ? 'border-red-500/60 bg-gradient-to-b from-red-950/60 to-slate-900 text-white shadow-2xl shadow-red-950/50'
            : 'border-slate-800 bg-slate-900/60 text-slate-300'
        }`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className={`p-2 rounded-xl ${sosActive ? 'bg-red-500 text-white animate-pulse' : 'bg-slate-800 text-slate-400'}`}>
                <Radio className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-xs font-bold text-white tracking-wide uppercase">SOS demonstration</h3>
                <p className="text-[10px] text-slate-400">Demonstration only — no alert is sent.</p>
              </div>
            </div>
            {!sosActive ? (
              <button
                onClick={handleTriggerSOS}
                className="px-3 py-1.5 bg-red-600 hover:bg-red-500 text-white text-xs font-bold rounded-xl shadow-lg shadow-red-600/30 transition-transform active:scale-95"
              >
                SIMULATE SOS (DEMO)
              </button>
            ) : (
              <span className="text-[10px] font-mono font-bold text-red-400 bg-red-500/20 px-2 py-1 rounded border border-red-500/30">
                DEMO ACTIVE
              </span>
            )}
          </div>

          {sosActive && (
            <div className="mt-3 p-2.5 rounded-xl bg-slate-950/80 border border-red-500/30 space-y-1.5 text-[11px] font-mono">
              <div className="flex items-center justify-between text-red-300">
                <span>Sample location:</span>
                <span className="font-bold text-white">35.6762° N, 139.6503° E (sample Tokyo coordinates)</span>
              </div>
              <div className="flex items-center justify-between text-slate-400">
                <span>Demo progress:</span>
                <span className="text-emerald-400 font-bold">
                  {sosDemoComplete ? 'SAMPLE CASE DOS-EMERG-JP-994 — flow simulated, nothing transmitted' : 'RUNNING DEMO...'}
                </span>
              </div>
              <div className="text-[10px] text-amber-300 pt-1 border-t border-slate-800">
                Demo only: no beacon was sent and no security concierge was contacted. In a real emergency contact local emergency services.
              </div>
            </div>
          )}
        </section>

        {/* Day-by-Day Interactive Itinerary */}
        <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
              <Calendar className="w-3.5 h-3.5 text-indigo-400" />
              Day-by-Day Itinerary
            </h3>
            <span className="text-[10px] font-mono text-slate-400">
              {hasGraph ? `${nodes.length} itinerary items` : isSampleDemo ? 'Sample days' : 'Days to be planned'}
            </span>
          </div>

          {/* Day Selector Pills */}
          <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-none">
            {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((d) => (
              <button
                key={d}
                onClick={() => setActiveDay(d)}
                className={`px-3 py-1.5 rounded-xl text-xs font-mono font-semibold shrink-0 transition-all ${
                  activeDay === d
                    ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                    : 'bg-slate-800 text-slate-400 hover:bg-slate-750'
                }`}
              >
                Day {d}
              </button>
            ))}
          </div>

          {/* Day Details */}
          <div className="space-y-2.5 pt-1">
            {activeDay === 1 && (
              <div className="space-y-2">
                <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-bold text-white">{transferNode?.title || (isSampleDemo ? 'Sample transfer' : 'Transfer to be confirmed')}</span>
                    <span className="text-[10px] font-mono text-indigo-400">
                      {typeof transferNode?.start_time === 'string' && transferNode.start_time
                        ? transferNode.start_time
                        : isSampleDemo ? '16:45 (sample)' : 'Time to be confirmed'}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400">
                    {transferNode?.provider
                      ? `Transfer provider on file: ${transferNode.provider}.`
                      : isSampleDemo
                        ? 'Sample transfer row — not a booking.'
                        : 'Your transfer details will appear here once confirmed.'}
                  </p>
                  <div className="text-[10px] text-emerald-400 font-mono">
                    {transferNode?.confirmation_code
                      ? `Voucher #${transferNode.confirmation_code}`
                      : isSampleDemo
                        ? 'Sample voucher'
                        : 'No voucher on file'}
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-bold text-white">{hotelNode?.title || (isSampleDemo ? 'Sample hotel' : 'Hotel to be confirmed')}</span>
                    <span className="text-[10px] font-mono text-indigo-400">
                      {typeof hotelNode?.start_time === 'string' && hotelNode.start_time
                        ? hotelNode.start_time
                        : isSampleDemo ? '17:45 (sample)' : 'Time to be confirmed'}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400">
                    {hotelNode?.provider
                      ? `Hotel provider on file: ${hotelNode.provider}.`
                      : isSampleDemo
                        ? 'Sample hotel row — not a booking.'
                        : 'Your hotel details will appear here once confirmed.'}
                  </p>
                  <div className="text-[10px] text-emerald-400 font-mono">
                    Confirmation: {hotelVoucher ?? 'none'}
                  </div>
                </div>
              </div>
            )}

            {activeDay !== 1 && (
              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-white">
                    {isSampleDemo ? `Sample day ${activeDay}` : `Day ${activeDay} is not planned yet`}
                  </span>
                  <span className="text-[10px] font-mono text-indigo-400">
                    {isSampleDemo ? '10:00 (sample)' : 'Time to be confirmed'}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400">
                  {isSampleDemo
                    ? 'Sample activity row — not a confirmed booking.'
                    : 'Plans for this day will appear here as your travel advisor builds your itinerary.'}
                </p>
                <div className="text-[10px] text-amber-300 font-mono">
                  Status: {isSampleDemo ? 'sample' : 'not planned yet'}
                </div>
              </div>
            )}
          </div>
        </section>

        {/* Digital Wallet & Documents Quick Access */}
        <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4 space-y-2.5">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
              <CreditCard className="w-3.5 h-3.5 text-indigo-400" />
              Digital Travel Wallet
            </h3>
            <span className="text-[10px] font-mono text-indigo-400">
              {hasGraph ? 'Stored passes' : isSampleDemo ? 'Sample passes' : 'No passes'}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center justify-between">
              <div>
                <span className="font-bold text-white block">E-Ticket{isPreview ? ' (preview)' : ''}</span>
                <span className="text-[10px] text-slate-400">{eTicket ?? 'none'}</span>
              </div>
              <Download className="w-4 h-4 text-indigo-400" />
            </div>

            <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center justify-between">
              <div>
                <span className="font-bold text-white block">Hotel Voucher{isPreview ? ' (preview)' : ''}</span>
                <span className="text-[10px] text-slate-400">{hotelVoucher ?? 'none'}</span>
              </div>
              <Download className="w-4 h-4 text-indigo-400" />
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}

function TravelerCompanionRoute() {
  const searchParams = useSearchParams();
  const tripId = searchParams.get('tripId');
  const shareToken = searchParams.get('token');
  const identity = `${tripId ?? ''}\u0000${shareToken ?? ''}`;

  return <TravelerCompanionContent key={identity} tripId={tripId} shareToken={shareToken} />;
}

export default function TravelerCompanionPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-[#090d16] text-slate-100 p-4">Loading companion…</div>}>
      <TravelerCompanionRoute />
    </Suspense>
  );
}
