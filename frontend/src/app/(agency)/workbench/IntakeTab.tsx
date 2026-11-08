'use client';

import { Suspense, useId, useState, useEffect, useMemo } from 'react';
import {
  ChevronDown,
  FileText,
  User,
  MapPin,
  Calendar,
  Users,
  Wallet,
  Settings,
  Plane,
  Lightbulb,
  Zap,
  AlertTriangle,
  ShieldAlert,
  Sparkles,
  MessageSquare,
  Mail,
  PhoneCall,
  RefreshCw,
} from 'lucide-react';
import { useSearchParams, useRouter, usePathname } from 'next/navigation';
import type { Trip, LiveMessageTriageResponse } from '@/lib/api-client';
import { triageMessage } from '@/lib/api-client';
import { useWorkbenchStore } from '@/stores/workbench';
import type { SpineStage, OperatingMode } from '@/types/spine';
import { getTravelerPromptForUnknownField } from '@/lib/traveler-prompts';
import { clearDepartureBoardHandoff, readDepartureBoardHandoff } from '@/lib/departure-board-handoff';
import {
  parseMessyTravelNote,
  type ExtractedTravelSlots,
} from '@/lib/messy-ingest-cleaner';
import { RepeatTravelerRecallCard } from './RepeatTravelerRecallCard';
import { QuickIngestPalette } from './QuickIngestPalette';

const stages: { value: SpineStage; label: string }[] = [
  { value: 'discovery', label: 'Discovery' },
  { value: 'shortlist', label: 'Shortlist' },
  { value: 'proposal', label: 'Proposal' },
  { value: 'booking', label: 'Booking' },
];

const VALID_STAGES = new Set<SpineStage>(stages.map((s) => s.value));

const modes: { value: OperatingMode; label: string }[] = [
  { value: 'normal_intake', label: 'New Request' },
  { value: 'audit', label: 'Audit' },
  { value: 'emergency', label: 'Emergency' },
  { value: 'follow_up', label: 'Follow Up' },
  { value: 'cancellation', label: 'Cancellation' },
  { value: 'post_trip', label: 'Post Trip' },
];

const VALID_MODES = new Set<OperatingMode>(modes.map((m) => m.value));

const PRESET_WHATSAPP = `[10:14 AM, 4/12/2026] Rahul Verma: Hey! Need a 6N vacation in Dubai and Abu Dhabi for me, wife and 2 kids (ages 7 and 11).
[10:15 AM, 4/12/2026] Rahul Verma: Flying from DEL around Dec 20 to 28. Want Atlantis The Palm for the waterpark.
[10:16 AM, 4/12/2026] Rahul Verma: Budget is around INR 6-7 Lakhs total. Pure vegetarian meals is a must!`;

const PRESET_EMAIL = `---------- Forwarded message ---------
From: Ananya Singhania <ananya@example.com>
Date: Fri, Nov 6, 2026 at 4:15 PM
Subject: Maldives luxury honeymoon
To: reservations@waypoint.app

Hi, looking for a 5-night honeymoon in Maldives in late June. Flying from BOM. Budget is around $6,000 USD. Prefer Four Seasons or private pool water villa. Halal dining preferred.`;

const PRESET_PHONE = `Phone consultation notes (Mr. & Mrs. Kapoor):
- 10-day trip to Japan for their 20th anniversary in October
- Flying from Mumbai (BOM)
- Luxury ryokans in Kyoto and Tokyo, private tea ceremony
- Budget: $18,000 USD
- Strict vegetarian dining throughout`;

interface IntakeTabProps {
  trip?: Trip | null;
}

function IntakeTabInner({ trip }: IntakeTabProps) {
  const searchParams = useSearchParams();
  const getSearchParam = searchParams.get.bind(searchParams);
  const { replace } = useRouter();
  const pathname = usePathname();
  const {
    input_raw_note,
    input_owner_note,
    draft_status,
    setInputRawNote,
    setInputOwnerNote,
    consumePendingIntakePrefill,
  } = useWorkbenchStore();
  const id1 = useId();
  const id2 = useId();
  const id3 = useId();
  const id4 = useId();

  const [triageResult, setTriageResult] = useState<LiveMessageTriageResponse | null>(null);
  const [isTriaging, setIsTriaging] = useState<boolean>(false);

  // Synchronously compute extracted travel slots from the client message as the user types
  const liveSlots = useMemo<ExtractedTravelSlots | null>(() => {
    if (!input_raw_note || input_raw_note.trim().length < 5) return null;
    return parseMessyTravelNote(input_raw_note);
  }, [input_raw_note]);

  const hasDetectedSlots = Boolean(
    liveSlots &&
      (liveSlots.destinations.length > 0 ||
        liveSlots.origin ||
        liveSlots.partySummary ||
        liveSlots.datesSummary ||
        liveSlots.budgetSummary ||
        liveSlots.dietaryOrPreferences.length > 0),
  );

  // Message→intake hand-off (operator-surface tranche 2026-11-03; sim-pass
  // fix 2026-11-07): consume a channel message handed over from the inbox
  // ("Use for intake") or departure board handoff session.
  useEffect(() => {
    let resolvedPrefill = (consumePendingIntakePrefill() || '').trim();
    if (!resolvedPrefill) {
      const urlPrefill = getSearchParam('prefill');
      if (urlPrefill && urlPrefill.trim()) {
        resolvedPrefill = urlPrefill.trim();
      } else if (typeof window !== 'undefined') {
        const parsed = readDepartureBoardHandoff();
        clearDepartureBoardHandoff();
        if (parsed?.prefill) {
          resolvedPrefill = parsed.prefill;
        }
      }
    }

    if (resolvedPrefill) {
      setInputRawNote(
        input_raw_note.trim() && !input_raw_note.includes(resolvedPrefill)
          ? `${input_raw_note.trimEnd()}\n\n— forwarded from inbox channel message —\n${resolvedPrefill}`
          : resolvedPrefill,
      );
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const text = (input_raw_note || '').trim();
    if (text.length < 5) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setTriageResult(null);
      return;
    }

    const timer = setTimeout(async () => {
      try {
        setIsTriaging(true);
        const res = await triageMessage(text);
        setTriageResult(res);
      } catch {
        // Non-blocking background telemetry
      } finally {
        setIsTriaging(false);
      }
    }, 400);

    return () => clearTimeout(timer);
  }, [input_raw_note]);

  const stage = (getSearchParam('stage') as SpineStage) || 'discovery';
  const operatingMode = (getSearchParam('mode') as OperatingMode) || 'normal_intake';

  const updateUrlParam = (key: string, value: string) => {
    const params = new URLSearchParams(searchParams.toString());
    params.set(key, value);
    replace(`${pathname}?${params.toString()}`, { scroll: false });
  };

  const budget = trip?.budget || '-';
  const party = trip?.party || '-';
  const dateWindow = trip?.dateWindow || '-';
  const tripPurposePrompt = getTravelerPromptForUnknownField('trip_purpose');
  const stageHelp: Record<SpineStage, string> = {
    discovery: 'Use this when you are still qualifying the inquiry and need missing essentials.',
    shortlist: 'Use this when core details are known and you are preparing curated options.',
    proposal: 'Use this when you are shaping commercial quote-ready recommendations.',
    booking: 'Use this when plans are accepted and execution confirmations are underway.',
  };
  const modeHelp: Record<OperatingMode, string> = {
    normal_intake: 'Default for most new traveler inquiries.',
    audit: 'Use for quality review, correction, or historical cleanup.',
    emergency: 'Use when there is urgent traveler impact or time-critical risk.',
    follow_up: 'Use for inbound follow-ups after prior communication.',
    cancellation: 'Use when intent shifts to cancellation, refund, or rescue planning.',
    post_trip: 'Use for post-travel closure, feedback, and retention actions.',
    coordinator_group: 'Use when coordinating multi-party/internal stakeholders.',
    owner_review: 'Use when owner-level judgment is required before proceeding.',
  };

  return (
    <div className='space-y-6'>
      {getSearchParam('source') === 'departure-board' && (
        <div
          data-testid='intake-departure-board-handoff-banner'
          className='flex items-center justify-between p-3.5 rounded-xl border border-[#39d0d8]/35 bg-[#39d0d8]/10 text-ui-xs text-[#e6edf3]'
        >
          <div className='flex items-center gap-2.5'>
            <Sparkles className='size-4 text-[#39d0d8] shrink-0' />
            <div>
              <p className='font-semibold text-[#39d0d8]'>
                Departure Board Handoff Applied
              </p>
              <p className='text-[#8b949e] mt-0.5'>
                {getSearchParam('case')
                  ? `${getSearchParam('case')?.toUpperCase()} client inquiry note ingested into Raw Notes.`
                  : 'Inquiry note ingested from marketing dispatch.'}{' '}
                AI triage is analyzing travel requirements below.
              </p>
            </div>
          </div>
          {getSearchParam('iata') && (
            <span className='font-mono font-bold text-[11px] px-2.5 py-1 rounded-md bg-[#39d0d8]/20 text-[#39d0d8] border border-[#39d0d8]/40 shrink-0'>
              ✈ {getSearchParam('iata')}
            </span>
          )}
        </div>
      )}

      {/* Primary Ingestion & Captured Details Radar */}
      <div className='bg-[#161b22] border border-[#30363d] rounded-xl p-4'>
        <div className='flex items-center justify-between gap-2 mb-4'>
          <div className='flex items-center gap-2'>
            <Plane className='size-4 text-[#58a6ff]' />
            <h3 className='text-ui-sm font-semibold text-[#e6edf3]'>
              {trip ? 'Captured Details' : hasDetectedSlots ? 'Live Ingestion Signal' : 'Captured Details'}
            </h3>
          </div>
          {!trip && hasDetectedSlots && (
            <span className='text-[10px] font-mono px-2 py-0.5 rounded-md bg-[#238636]/15 text-[#3fb950] border border-[#238636]/30 flex items-center gap-1.5'>
              <span className='size-1.5 rounded-full bg-[#3fb950] animate-pulse' />
              Real-Time Signal Extracted · Ready to Process
            </span>
          )}
        </div>

        {trip ? (
          <div className='grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3'>
            <div>
              <span className='text-ui-xs text-[#8b949e] uppercase tracking-wide'>Destination</span>
              <p className='text-ui-sm text-[#e6edf3] font-medium mt-0.5 flex items-center gap-1'>
                <MapPin className='size-3 text-[#58a6ff]' />
                {trip.destination}
              </p>
            </div>
            <div>
              <span className='text-ui-xs text-[#8b949e] uppercase tracking-wide'>Type</span>
              <p className='text-ui-sm text-[#e6edf3] font-medium mt-0.5'>{trip.type}</p>
            </div>
            <div>
              <span className='text-ui-xs text-[#8b949e] uppercase tracking-wide'>Party Size</span>
              <p className='text-ui-sm text-[#e6edf3] font-medium mt-0.5 flex items-center gap-1'>
                <Users className='size-3 text-[#8b949e]' />
                {party} pax
              </p>
            </div>
            <div>
              <span className='text-ui-xs text-[#8b949e] uppercase tracking-wide'>Dates</span>
              <p className='text-ui-sm text-[#e6edf3] font-medium mt-0.5 flex items-center gap-1'>
                <Calendar className='size-3 text-[#8b949e]' />
                {dateWindow}
              </p>
            </div>
            <div>
              <span className='text-ui-xs text-[#8b949e] uppercase tracking-wide'>Budget</span>
              <p className='text-ui-sm text-[#e6edf3] font-medium mt-0.5 flex items-center gap-1'>
                <Wallet className='size-3 text-[#3fb950]' />
                {budget}
              </p>
            </div>
            <div>
              <span className='text-ui-xs text-[#8b949e] uppercase tracking-wide'>Reference</span>
              <p className='text-ui-sm text-[#e6edf3] font-mono mt-0.5'>{trip.id}</p>
            </div>
          </div>
        ) : !trip && hasDetectedSlots ? (
          <div className='grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3'>
            <div>
              <span className='text-ui-xs text-[#8b949e] uppercase tracking-wide'>Destination</span>
              <p className='text-ui-sm text-[#e6edf3] font-medium mt-0.5 flex items-center gap-1'>
                <MapPin className='size-3 text-[#58a6ff]' />
                {liveSlots?.destinations.length ? liveSlots.destinations.join(' & ') : 'Detecting…'}
              </p>
            </div>
            <div>
              <span className='text-ui-xs text-[#8b949e] uppercase tracking-wide'>Origin</span>
              <p className='text-ui-sm text-[#e6edf3] font-medium mt-0.5'>
                {liveSlots?.origin || 'Unspecified'}
              </p>
            </div>
            <div>
              <span className='text-ui-xs text-[#8b949e] uppercase tracking-wide'>Party Size</span>
              <p className='text-ui-sm text-[#e6edf3] font-medium mt-0.5 flex items-center gap-1'>
                <Users className='size-3 text-[#8b949e]' />
                {liveSlots?.partySummary || (liveSlots?.partySize ? `${liveSlots.partySize} pax` : '-')}
              </p>
            </div>
            <div>
              <span className='text-ui-xs text-[#8b949e] uppercase tracking-wide'>Dates</span>
              <p className='text-ui-sm text-[#e6edf3] font-medium mt-0.5 flex items-center gap-1'>
                <Calendar className='size-3 text-[#8b949e]' />
                {liveSlots?.datesSummary || '-'}
              </p>
            </div>
            <div>
              <span className='text-ui-xs text-[#8b949e] uppercase tracking-wide'>Budget</span>
              <p className='text-ui-sm text-[#e6edf3] font-medium mt-0.5 flex items-center gap-1'>
                <Wallet className='size-3 text-[#3fb950]' />
                {liveSlots?.budgetSummary || '-'}
              </p>
            </div>
            <div>
              <span className='text-ui-xs text-[#8b949e] uppercase tracking-wide'>Live Stage</span>
              <p className='text-ui-sm text-[#3fb950] font-mono mt-0.5'>
                {stage.toUpperCase()}
              </p>
            </div>
          </div>
        ) : draft_status === 'blocked' ? (
          <p className='text-ui-sm text-[#8b949e]'>
            Processing stopped before any details were captured — the blocked banner above lists what this inquiry is missing.
          </p>
        ) : draft_status === 'processing' ? (
          <p className='text-ui-sm text-[#8b949e]'>
            Processing the inquiry — captured details will appear here.
          </p>
        ) : draft_status === 'failed' ? (
          <p className='text-ui-sm text-[#8b949e]'>
            Processing failed before details could be captured — try processing the inquiry again.
          </p>
        ) : (
          <p className='text-ui-sm text-[#8b949e]'>
            Captured details will appear here after processing the inquiry.
          </p>
        )}
      </div>

      {/* Main Inquiry Capture Section */}
      <div className='grid grid-cols-1 lg:grid-cols-2 gap-6'>
        <div className='bg-[#161b22] border border-[#30363d] rounded-xl p-4'>
          <div className='flex items-center justify-between gap-2 mb-2'>
            <div className='flex items-center gap-2'>
              <FileText className='size-4 text-[#8b949e]' />
              <label htmlFor={id1} className='text-ui-sm font-medium text-[#e6edf3]'>
                Customer Message
              </label>
            </div>
            <QuickIngestPalette onApply={(text) => setInputRawNote(text)} />
          </div>

          {/* Quick preset selector for testing real-world unstructured briefs */}
          <div className='flex items-center gap-1.5 mb-2.5 flex-wrap text-ui-xs'>
            <span className='text-[11px] text-[#8b949e] font-medium mr-1'>Presets:</span>
            <button
              type='button'
              onClick={() => setInputRawNote(PRESET_WHATSAPP)}
              className='inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-[#21262d] hover:bg-[#30363d] text-[#c9d1d9] text-[11px] border border-[#30363d] transition-colors'
            >
              <MessageSquare className='size-2.5 text-[#3fb950]' />
              WhatsApp
            </button>
            <button
              type='button'
              onClick={() => setInputRawNote(PRESET_EMAIL)}
              className='inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-[#21262d] hover:bg-[#30363d] text-[#c9d1d9] text-[11px] border border-[#30363d] transition-colors'
            >
              <Mail className='size-2.5 text-[#58a6ff]' />
              Email
            </button>
            <button
              type='button'
              onClick={() => setInputRawNote(PRESET_PHONE)}
              className='inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-[#21262d] hover:bg-[#30363d] text-[#c9d1d9] text-[11px] border border-[#30363d] transition-colors'
            >
              <PhoneCall className='size-2.5 text-[#d2a8ff]' />
              Phone Notes
            </button>
            {input_raw_note && (
              <button
                type='button'
                onClick={() => setInputRawNote('')}
                className='inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-transparent hover:bg-[#21262d] text-[#8b949e] hover:text-[#e6edf3] text-[11px] transition-colors ml-auto'
              >
                <RefreshCw className='size-2.5' />
                Clear
              </button>
            )}
          </div>

          <p className='mb-2 text-ui-xs text-[#8b949e]'>
            Paste the exact traveler request: destination ideas, travel window, party details, trip purpose, budget hints, constraints,
            preferences, or any channel transcript (email/WhatsApp/call summary).
          </p>

          {tripPurposePrompt && (
            <div className='mb-3 rounded-lg border border-[#30363d] bg-[#0f1115] px-3 py-2 text-ui-xs text-[#c9d1d9] flex items-start gap-2'>
              <Lightbulb className='size-3.5 mt-0.5 text-[#58a6ff] shrink-0' />
              <p>Need the purpose fast? {tripPurposePrompt}</p>
            </div>
          )}

          <textarea
            id={id1}
            value={input_raw_note}
            onChange={(e) => setInputRawNote(e.target.value)}
            placeholder='Example: Couple from Mumbai for 6N Bali in July, beach villa preference, INR 3-4L budget, vegetarian meals, anniversary trip.'
            rows={6}
            className='w-full px-3 py-2 bg-[#0f1115] border border-[#30363d] rounded-lg text-ui-sm text-[#e6edf3] placeholder:text-[#8b949e] focus:outline-none focus:border-[#58a6ff] resize-none font-mono'
          />

          {/* Real-Time Extraction Signal & Semantic Triage Telemetry */}
          {(hasDetectedSlots || isTriaging || triageResult) && (
            <div className='mt-3 p-3 rounded-lg border border-[#30363d] bg-[#0d1117] text-ui-xs space-y-2.5 transition-all'>
              {/* Row 1: Extracted Travel Slots */}
              {liveSlots && (
                <div className='space-y-1.5'>
                  <div className='flex items-center justify-between text-[10px] font-mono uppercase tracking-wider text-[#8b949e]'>
                    <span>Detected Travel Slots</span>
                    <span className='text-[#3fb950] font-semibold'>Live Parser</span>
                  </div>
                  <div className='flex flex-wrap gap-1.5'>
                    {liveSlots.destinations.map((d) => (
                      <span key={d} className='px-2 py-0.5 rounded-md bg-[#1f6feb]/15 border border-[#1f6feb]/30 text-[#79c0ff] text-[11px] font-medium'>
                        📍 {d}
                      </span>
                    ))}
                    {liveSlots.origin && (
                      <span className='px-2 py-0.5 rounded-md bg-[#21262d] border border-[#30363d] text-[#c9d1d9] text-[11px]'>
                        🛫 Ex: {liveSlots.origin}
                      </span>
                    )}
                    {liveSlots.partySummary && (
                      <span className='px-2 py-0.5 rounded-md bg-[#21262d] border border-[#30363d] text-[#c9d1d9] text-[11px]'>
                        👥 {liveSlots.partySummary}
                      </span>
                    )}
                    {liveSlots.datesSummary && (
                      <span className='px-2 py-0.5 rounded-md bg-[#d29922]/15 border border-[#d29922]/30 text-[#e3b341] text-[11px]'>
                        📅 {liveSlots.datesSummary}
                      </span>
                    )}
                    {liveSlots.budgetSummary && (
                      <span className='px-2 py-0.5 rounded-md bg-[#238636]/15 border border-[#238636]/30 text-[#3fb950] text-[11px] font-medium'>
                        💰 {liveSlots.budgetSummary}
                      </span>
                    )}
                    {liveSlots.hotelMentions.map((h, i) => (
                      <span key={i} className='px-2 py-0.5 rounded-md bg-[#a371f7]/15 border border-[#a371f7]/30 text-[#d2a8ff] text-[11px]'>
                        🏨 {h}
                      </span>
                    ))}
                    {liveSlots.dietaryOrPreferences.map((pref, i) => (
                      <span key={i} className='px-2 py-0.5 rounded-md bg-[#21262d] border border-[#30363d] text-[#8b949e] text-[11px]'>
                        ✨ {pref}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Row 2: Semantic Triage Telemetry */}
              {(isTriaging || triageResult) && (
                <div className='pt-2 border-t border-[#21262d] flex flex-col gap-1.5'>
                  <div className='flex items-center justify-between'>
                    <div className='flex items-center gap-1.5 font-medium text-[#c9d1d9]'>
                      <Zap className='size-3 text-[#58a6ff]' />
                      <span>Semantic Triage</span>
                      {isTriaging && <span className='text-[#8b949e] animate-pulse'>(evaluating…)</span>}
                    </div>
                    {triageResult && (
                      <span className='text-[10px] text-[#8b949e] font-mono'>
                        {triageResult.source} • {triageResult.latency_ms}ms
                      </span>
                    )}
                  </div>

                  {triageResult && (
                    <div className='flex flex-wrap items-center gap-1.5 pt-0.5'>
                      <span className='px-2 py-0.5 rounded bg-[#21262d] text-[#58a6ff] font-semibold uppercase tracking-wider text-[10px]'>
                        Intent: {triageResult.intent}
                      </span>

                      {triageResult.is_urgent && (
                        <span className='px-2 py-0.5 rounded bg-[#f85149]/20 text-[#f85149] font-medium flex items-center gap-1 text-[10px]'>
                          <AlertTriangle className='size-2.5' /> URGENT
                        </span>
                      )}

                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-medium ${
                          triageResult.sentiment === 'FRUSTRATED'
                            ? 'bg-[#f85149]/20 text-[#f85149]'
                            : triageResult.sentiment === 'CONCERNED'
                            ? 'bg-[#d29922]/20 text-[#d29922]'
                            : 'bg-[#238636]/20 text-[#3fb950]'
                        }`}
                      >
                        Tone: {triageResult.sentiment}
                      </span>

                      {triageResult.has_policy_risk && (
                        <span className='px-2 py-0.5 rounded bg-[#da3633]/20 text-[#f85149] font-medium flex items-center gap-1 text-[10px]'>
                          <ShieldAlert className='size-2.5' /> POLICY/LEGAL RISK
                        </span>
                      )}

                      <span className='px-2 py-0.5 rounded bg-[#1f242c] text-[#8b949e] text-[10px]'>
                        Route: {triageResult.routing_recommendation}
                      </span>
                    </div>
                  )}

                  {triageResult?.advisory && (
                    <p className='text-[11px] text-[#8b949e] italic'>
                      Advisory: {triageResult.advisory}
                    </p>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        <div className='bg-[#161b22] border border-[#30363d] rounded-xl p-4'>
          <div className='flex items-center gap-2 mb-3'>
            <User className='size-4 text-[#58a6ff]' />
            <label htmlFor={id2} className='text-ui-sm font-medium text-[#e6edf3]'>
              Agent Notes
            </label>
          </div>
          <p className='mb-2 text-ui-xs text-[#8b949e]'>
            Add internal context not meant for the traveler: qualification signals, risk flags, supplier constraints, margin targets,
            urgency, and next-step instructions for the team.
          </p>
          <p className='mb-2 text-ui-xs text-[#8b949e]'>
            For sparse global-market requests, add the trip purpose here so the first pass can move past `WAITING ON CUSTOMER` when the destination and budget are already clear.
          </p>
          <textarea
            id={id2}
            value={input_owner_note}
            onChange={(e) => setInputOwnerNote(e.target.value)}
            placeholder='Example: High-intent repeat client, prefers premium inventory, keep margin >=18%, verify visa timeline before quote.'
            rows={6}
            className='w-full px-3 py-2 bg-[#0f1115] border border-[#30363d] rounded-lg text-ui-sm text-[#e6edf3] placeholder:text-[#8b949e] focus:outline-none focus:border-[#58a6ff] resize-none'
          />
        </div>
      </div>

      {/* Repeat Traveler Auto-Recall Memory Card (IMP-03, Option B+): sample-only
          panel, gated to workspaces with no captured trip. Real recall wiring is
          the later Option A slice (Docs/exploration/DEMO04_SAMPLE_PROFILE_PROVENANCE_2026-08-31.md). */}
      {!trip && <RepeatTravelerRecallCard />}

      <details className='bg-[#161b22] border border-[#30363d] rounded-xl'>
        <summary className='flex cursor-pointer list-none items-center gap-2 px-4 py-3 text-ui-sm font-medium text-[#e6edf3] hover:text-[#58a6ff] transition-colors'>
          <Settings className='size-4 text-[#8b949e]' />
          Advanced Configuration
        </summary>
        <div className='px-4 pb-1'>
          <div className='rounded-md border border-[#30363d] bg-[#0f1115] px-3 py-2 text-ui-xs text-[#8b949e] flex items-start gap-2'>
            <Lightbulb className='size-3.5 mt-0.5 text-[#58a6ff]' />
            <div>
              <p className='text-[#c9d1d9] mb-1'>Context-aware recommendation</p>
              <p>Stage: {stageHelp[stage]}</p>
              <p>Request type: {modeHelp[operatingMode]}</p>
            </div>
          </div>
        </div>
        <div className='px-4 pb-4 grid grid-cols-1 sm:grid-cols-2 gap-4'>
          <div>
            <label htmlFor={id3} className='block text-ui-sm font-medium text-[#8b949e] mb-2'>
              Stage
            </label>
            <div className='relative'>
              <select
                id={id3}
                value={stage}
                onChange={(e) => {
                  const v = e.target.value;
                  if (VALID_STAGES.has(v as SpineStage)) updateUrlParam('stage', v);
                }}
                className='w-full px-3 py-2 bg-[#0f1115] border border-[#30363d] rounded-lg text-ui-sm text-[#e6edf3] focus:outline-none focus:border-[#58a6ff] appearance-none'
              >
                {stages.map((s) => (
                  <option key={s.value} value={s.value}>
                    {s.label}
                  </option>
                ))}
              </select>
              <ChevronDown className='absolute right-3 top-1/2 -translate-y-1/2 size-4 text-[#8b949e] pointer-events-none' />
            </div>
          </div>
          <div>
            <label htmlFor={id4} className='block text-ui-sm font-medium text-[#8b949e] mb-2'>
              Request Type
            </label>
            <div className='relative'>
              <select
                id={id4}
                value={operatingMode}
                onChange={(e) => {
                  const v = e.target.value;
                  if (VALID_MODES.has(v as OperatingMode)) updateUrlParam('mode', v);
                }}
                className='w-full px-3 py-2 bg-[#0f1115] border border-[#30363d] rounded-lg text-ui-sm text-[#e6edf3] focus:outline-none focus:border-[#58a6ff] appearance-none'
              >
                {modes.map((m) => (
                  <option key={m.value} value={m.value}>
                    {m.label}
                  </option>
                ))}
              </select>
              <ChevronDown className='absolute right-3 top-1/2 -translate-y-1/2 size-4 text-[#8b949e] pointer-events-none' />
            </div>
          </div>
        </div>
      </details>

      <div className='flex items-center justify-between pt-4 border-t border-[#30363d]'>
        <div className='flex items-center gap-4 text-ui-sm text-[#8b949e]'>
          <div className='flex items-center gap-2'>
            <div className='size-2 rounded-full bg-[#3fb950]'></div>
            <span>System Ready</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function IntakeTab(props: IntakeTabProps) {
  return (
    <Suspense fallback={<div className="p-4 text-ui-sm text-[#8b949e]">Loading intake…</div>}>
      <IntakeTabInner {...props} />
    </Suspense>
  );
}
