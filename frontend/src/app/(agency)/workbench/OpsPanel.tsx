'use client';

import { useState } from 'react';
import {
  type Trip,
  type BookingData,
  type BookingDocument,
  type BookingTraveler,
} from '@/lib/api-client';
import BookingExecutionPanel from '@/components/workspace/panels/BookingExecutionPanel';
import ConfirmationPanel from '@/components/workspace/panels/ConfirmationPanel';
import ExecutionTimelinePanel from '@/components/workspace/panels/ExecutionTimelinePanel';
import NextActionBanner from '@/components/workspace/panels/NextActionBanner';
import DataIntakeZone from '@/components/workspace/panels/DataIntakeZone';
import DocumentsZone from '@/components/workspace/panels/DocumentsZone';
import type { ReadinessAssessment } from '@/types/spine';

interface OpsPanelProps {
  trip?: Trip | null;
  mode?: 'full' | 'documents';
}

// react-doctor-disable-next-line react-doctor/prefer-useReducer — 3 mirror state vars are independent slices; useReducer would add complexity without benefit
export default function OpsPanel({ trip, mode = 'full' }: OpsPanelProps) {
  const documentsOnly = mode === 'documents';
  const readiness: ReadinessAssessment | undefined =
    (trip?.validation as { readiness?: ReadinessAssessment } | null)?.readiness;

  // Mirror state fed by child zone callbacks — used by NextActionBanner only, no new API calls
  const [opsDocs, setOpsDocs] = useState<BookingDocument[]>([]);
  const [opsPendingData, setOpsPendingData] = useState<BookingData | null>(null);
  const [opsTravelers, setOpsTravelers] = useState<BookingTraveler[]>([]);

  const stage = trip?.stage;
  const canGenerateLink = stage === 'proposal' || stage === 'booking';

  const tiers = readiness?.tiers ?? {};
  const tierEntries = Object.entries(tiers);
  const signals = readiness?.signals;
  const signalRecord =
    signals && typeof signals === 'object' && !Array.isArray(signals)
      ? (signals as Record<string, unknown>)
      : null;

  return (
    <div data-testid="ops-panel" className="space-y-6">
      {/* Next action banner — derived from already-loaded mirror state, no new API calls */}
      {!documentsOnly && (
        <NextActionBanner
          pendingData={opsPendingData}
          documents={opsDocs}
          readiness={readiness}
        />
      )}

      {/* No readiness — informational notice, all Ops sections still available */}
      {!documentsOnly && !readiness && (
        <div data-testid="ops-readiness-empty" className="rounded-lg border border-[#30363d] bg-[#0f1115] px-4 py-3 text-sm text-[#8b949e]">
          No readiness assessment available yet. Booking operations are still available below.
        </div>
      )}

      {/* Highest tier summary */}
      {!documentsOnly && readiness && (
        <div className="flex items-center gap-3">
          <span className="text-sm text-[#8b949e]">Highest ready tier:</span>
          <span
            data-testid="ops-highest-tier"
            className="text-sm font-medium text-[#e6edf3]"
          >
            {readiness?.highest_ready_tier ?? 'none'}
          </span>
        </div>
      )}

      {/* Tier details */}
      {!documentsOnly && tierEntries.length > 0 && (
        <div data-testid="ops-tiers" className="space-y-4">
          <h3 className="text-sm font-medium text-[#e6edf3]">Booking Readiness Tiers</h3>
          {tierEntries.map((entry) => {
            const [name, tier] = entry;
            return (
              <div
                key={name}
                data-testid={`ops-tier-${name}`}
                className="border border-[#30363d] rounded-lg p-4"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-[#e6edf3]">
                    {name.replace(/_/g, ' ')}
                  </span>
                  <span
                    className={`text-xs px-2 py-0.5 rounded ${
                      tier.ready
                        ? 'bg-emerald-900/50 text-emerald-400'
                        : 'bg-red-900/50 text-red-400'
                    }`}
                  >
                    {tier.ready ? 'Ready' : 'Not ready'}
                  </span>
                </div>
                {tier.met.length > 0 && (
                  <div className="mb-1">
                    <span className="text-xs text-[#8b949e]">Met: </span>
                    <span className="text-xs text-emerald-400">{tier.met.join(', ')}</span>
                  </div>
                )}
                {tier.unmet.length > 0 && (
                  <div>
                    <span className="text-xs text-[#8b949e]">Missing: </span>
                    <span className="text-xs text-red-400">{tier.unmet.join(', ')}</span>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Missing for next stage */}
      {!documentsOnly && readiness?.missing_for_next.length && readiness.missing_for_next.length > 0 && (
        <div data-testid="ops-missing" className="border border-[#30363d] rounded-lg p-4">
          <span className="text-xs text-[#8b949e]">Fields blocking next tier: </span>
          <span className="text-xs text-amber-400">
            {readiness.missing_for_next.join(', ')}
          </span>
        </div>
      )}

      {/* Auxiliary signals */}
      {!documentsOnly && signalRecord && Object.keys(signalRecord).length > 0 && (
        <div data-testid="ops-signals" className="border border-[#30363d] rounded-lg p-4">
          <h4 className="text-sm font-medium text-[#e6edf3] mb-2">Signals</h4>
          {signalRecord.visa_concerns_present === true && (
            <div
              data-testid="ops-signal-visa-concern"
              className="flex items-center gap-2 text-sm"
            >
              <span className="text-amber-400">Visa/Passport concern detected</span>
              <span className="text-xs text-[#8b949e]">
                Traveler input mentions visa or passport topics. Review may be needed.
              </span>
            </div>
          )}
        </div>
      )}

      {/* Data intake: booking details + collection link + pending customer submission */}
      {!documentsOnly && trip?.id && (
        <DataIntakeZone
          tripId={trip.id}
          canGenerateLink={canGenerateLink}
          onPendingDataChange={setOpsPendingData}
          onTravelersChange={setOpsTravelers}
        />
      )}

      {/* Documents */}
      {trip?.id && (
        <DocumentsZone
          tripId={trip.id}
          canUpload={canGenerateLink}
          travelers={opsTravelers}
          onDocumentsChange={setOpsDocs}
        />
      )}

      {/* Booking execution tasks (Phase 5A) */}
      {!documentsOnly && trip?.id && <BookingExecutionPanel tripId={trip.id} stage={stage ?? undefined} />}
      {!documentsOnly && trip?.id && <ConfirmationPanel tripId={trip.id} />}
      {!documentsOnly && trip?.id && <ExecutionTimelinePanel tripId={trip.id} />}
    </div>
  );
}
