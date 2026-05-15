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
import ReadinessSummary from '@/components/workspace/panels/ReadinessSummary';
import DataIntakeZone from '@/components/workspace/panels/DataIntakeZone';
import DocumentsZone from '@/components/workspace/panels/DocumentsZone';
import type { ReadinessAssessment } from '@/types/spine';

interface OpsPanelProps {
  trip?: Trip | null;
  mode?: 'full' | 'documents';
}

export default function OpsPanel({ trip, mode = 'full' }: OpsPanelProps) {
  const documentsOnly = mode === 'documents';
  const readiness: ReadinessAssessment | undefined =
    (trip?.validation as { readiness?: ReadinessAssessment } | null)?.readiness;

  // Mirror state fed by child zone callbacks — used by NextActionBanner/DocumentsZone only, no new API calls
  const [opsDocs, setOpsDocs] = useState<BookingDocument[]>([]);
  const [opsPendingData, setOpsPendingData] = useState<BookingData | null>(null);
  const [opsTravelers, setOpsTravelers] = useState<BookingTraveler[]>([]);

  const stage = trip?.stage;
  const canGenerateLink = stage === 'proposal' || stage === 'booking';

  return (
    <div data-testid="ops-panel" className="space-y-6">
      {!documentsOnly && (
        <NextActionBanner
          pendingData={opsPendingData}
          documents={opsDocs}
          readiness={readiness}
        />
      )}

      {!documentsOnly && <ReadinessSummary readiness={readiness} />}

      {!documentsOnly && trip?.id && (
        <DataIntakeZone
          tripId={trip.id}
          canGenerateLink={canGenerateLink}
          onPendingDataChange={setOpsPendingData}
          onTravelersChange={setOpsTravelers}
        />
      )}

      {trip?.id && (
        <DocumentsZone
          tripId={trip.id}
          canUpload={canGenerateLink}
          travelers={opsTravelers}
          onDocumentsChange={setOpsDocs}
        />
      )}

      {!documentsOnly && trip?.id && <BookingExecutionPanel tripId={trip.id} stage={stage ?? undefined} />}
      {!documentsOnly && trip?.id && <ConfirmationPanel tripId={trip.id} />}
      {!documentsOnly && trip?.id && <ExecutionTimelinePanel tripId={trip.id} />}
    </div>
  );
}
