'use client';

import { useTripContext } from '@/contexts/TripContext';
import { DecisionPanel } from '@/components/workspace/panels/DecisionPanel';
import { PlanningStageGate } from '@/components/workspace/PlanningStageGate';
import { getPlanningStageGateReason } from '@/lib/planning-status';

export default function DecisionPage() {
  const { tripId, trip } = useTripContext();
  const gateReason = getPlanningStageGateReason(trip, 'decision');

  return (
    <div className='p-6'>
      {tripId && gateReason ? (
        <PlanningStageGate tripId={tripId} reason={gateReason} />
      ) : (
        <DecisionPanel tripId={tripId || ''} />
      )}
    </div>
  );
}
