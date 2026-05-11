'use client';

import { Suspense } from 'react';
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
} from 'lucide-react';
import { useSearchParams, useRouter } from 'next/navigation';
import { useId } from 'react';
import type { Trip } from '@/lib/api-client';
import { useWorkbenchStore } from '@/stores/workbench';
import type { SpineStage, OperatingMode } from '@/types/spine';

const stages: { value: SpineStage; label: string }[] = [
  { value: 'discovery', label: 'Discovery' },
  { value: 'shortlist', label: 'Shortlist' },
  { value: 'proposal', label: 'Proposal' },
  { value: 'booking', label: 'Booking' },
];

const VALID_STAGES = new Set<SpineStage>(stages.map(s => s.value));

const modes: { value: OperatingMode; label: string }[] = [
  { value: 'normal_intake', label: 'New Request' },
  { value: 'audit', label: 'Audit' },
  { value: 'emergency', label: 'Emergency' },
  { value: 'follow_up', label: 'Follow Up' },
  { value: 'cancellation', label: 'Cancellation' },
  { value: 'post_trip', label: 'Post Trip' },
];

const VALID_MODES = new Set<OperatingMode>(modes.map(m => m.value));

interface IntakeTabProps {
  trip?: Trip | null;
}

function IntakeTabInner({ trip }: IntakeTabProps) {
  const searchParams = useSearchParams();
  const getSearchParam = searchParams.get.bind(searchParams);
  const { replace } = useRouter();
  const { input_raw_note, input_owner_note, setInputRawNote, setInputOwnerNote } = useWorkbenchStore();
  const id1 = useId();
  const id2 = useId();
  const id3 = useId();
  const id4 = useId();

  const stage = (getSearchParam('stage') as SpineStage) || 'discovery';
  const operatingMode = (getSearchParam('mode') as OperatingMode) || 'normal_intake';

  const updateUrlParam = (key: string, value: string) => {
    const params = new URLSearchParams(searchParams.toString());
    params.set(key, value);
    replace(`?${params.toString()}`, { scroll: false });
  };

  const origin = trip?.origin || '-';
  const budget = trip?.budget || '-';
  const party = trip?.party || '-';
  const dateWindow = trip?.dateWindow || '-';
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
      <div className='bg-[#161b22] border border-[#30363d] rounded-xl p-4'>
        <div className='flex items-center gap-2 mb-4'>
          <Plane className='size-4 text-[#58a6ff]' />
          <h3 className='text-ui-sm font-semibold text-[#e6edf3]'>
            Captured Details
          </h3>
        </div>
        {trip ? (
          <div className='grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3'>
            <div>
              <span className='text-ui-xs text-[#8b949e] uppercase tracking-wide'>Destination</span>
              <p className='text-ui-sm text-[#e6edf3] font-medium mt-0.5 flex items-center gap-1'>
                <MapPin className='size-3 text-[#58a6ff]' />{trip.destination}
              </p>
            </div>
            <div>
              <span className='text-ui-xs text-[#8b949e] uppercase tracking-wide'>Type</span>
              <p className='text-ui-sm text-[#e6edf3] font-medium mt-0.5'>{trip.type}</p>
            </div>
            <div>
              <span className='text-ui-xs text-[#8b949e] uppercase tracking-wide'>Party Size</span>
              <p className='text-ui-sm text-[#e6edf3] font-medium mt-0.5 flex items-center gap-1'>
                <Users className='size-3 text-[#8b949e]' />{party} pax
              </p>
            </div>
            <div>
              <span className='text-ui-xs text-[#8b949e] uppercase tracking-wide'>Dates</span>
              <p className='text-ui-sm text-[#e6edf3] font-medium mt-0.5 flex items-center gap-1'>
                <Calendar className='size-3 text-[#8b949e]' />{dateWindow}
              </p>
            </div>
            <div>
              <span className='text-ui-xs text-[#8b949e] uppercase tracking-wide'>Budget</span>
              <p className='text-ui-sm text-[#e6edf3] font-medium mt-0.5 flex items-center gap-1'>
                <Wallet className='size-3 text-[#3fb950]' />{budget}
              </p>
            </div>
            <div>
              <span className='text-ui-xs text-[#8b949e] uppercase tracking-wide'>Reference</span>
              <p className='text-ui-sm text-[#e6edf3] font-mono mt-0.5'>{trip.id}</p>
            </div>
          </div>
        ) : (
          <p className='text-ui-sm text-[#8b949e]'>
            Captured details will appear here after processing the inquiry.
          </p>
        )}
      </div>

      <div className='grid grid-cols-1 lg:grid-cols-2 gap-6'>
        <div className='bg-[#161b22] border border-[#30363d] rounded-xl p-4'>
          <div className='flex items-center gap-2 mb-3'>
            <FileText className='size-4 text-[#8b949e]' />
            <label htmlFor={id1} className='text-ui-sm font-medium text-[#e6edf3]'>
              Customer Message
            </label>
          </div>
          <p className='mb-2 text-ui-xs text-[#8b949e]'>
            Paste the exact traveler-facing request: destination ideas, travel window, party details, budget hints, constraints,
            preferences, and any channel transcript (email/WhatsApp/call summary).
          </p>
          <textarea
            id={id1}
            value={input_raw_note}
            onChange={(e) => setInputRawNote(e.target.value)}
            placeholder='Example: Couple from Mumbai for 6N Bali in July, beach villa preference, INR 3-4L budget, vegetarian meals, anniversary trip.'
            rows={6}
            className='w-full px-3 py-2 bg-[#0f1115] border border-[#30363d] rounded-lg text-ui-sm text-[#e6edf3] placeholder:text-[#8b949e] focus:outline-none focus:border-[#58a6ff] resize-none font-mono'
          />
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
