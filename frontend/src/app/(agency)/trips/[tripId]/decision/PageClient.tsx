'use client';

import { useTripContext } from '@/contexts/TripContext';
import { DecisionPanel } from '@/components/workspace/panels/DecisionPanel';
import { PlanningStageGate } from '@/components/workspace/PlanningStageGate';
import { FreshnessCard } from '@/components/workspace/FreshnessCard';
import { OnFileMemoryCard } from '@/components/workspace/OnFileMemoryCard';
import { ClaimDispositionCard } from '@/components/workspace/ClaimDispositionCard';
import { GhostConciergeCard } from '@/components/workspace/GhostConciergeCard';
import { getPlanningStageGateReason } from '@/lib/planning-status';

export default function DecisionPage() {
  const { tripId, trip } = useTripContext();
  const gateReason = getPlanningStageGateReason(trip, 'decision');

  return (
    <div className='p-6'>
      {tripId && gateReason ? (
        <PlanningStageGate tripId={tripId} reason={gateReason} />
      ) : (
        <>
          {tripId && <FreshnessCard tripId={tripId} />}
          {tripId && <OnFileMemoryCard tripId={tripId} />}
          <ClaimDispositionCard trip={trip} />
          <GhostConciergeCard trip={trip} />
          <DecisionPanel tripId={tripId || ''} />
        </>
      )}
    </div>
  );
}
