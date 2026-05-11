'use client';

import { useTripContext } from '@/contexts/TripContext';
import { StrategyPanel } from '@/components/workspace/panels/StrategyPanel';
import { PlanningStageGate } from '@/components/workspace/PlanningStageGate';
import { getPlanningStageGateReason } from '@/lib/planning-status';

export default function StrategyPage() {
  const { tripId, trip } = useTripContext();
  const gateReason = getPlanningStageGateReason(trip, 'strategy');

  return (
    <div className='p-6'>
      {tripId && gateReason ? (
        <PlanningStageGate tripId={tripId} reason={gateReason} />
      ) : (
        <StrategyPanel tripId={tripId || ''} />
      )}
    </div>
  );
}
