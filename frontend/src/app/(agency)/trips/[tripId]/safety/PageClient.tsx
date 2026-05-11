'use client';

import { useTripContext } from '@/contexts/TripContext';
import { SafetyPanel } from '@/components/workspace/panels/SafetyPanel';
import { PlanningStageGate } from '@/components/workspace/PlanningStageGate';
import { getPlanningStageGateReason } from '@/lib/planning-status';

export default function SafetyPage() {
  const { tripId, trip } = useTripContext();
  const gateReason = getPlanningStageGateReason(trip, 'safety');

  return (
    <div className='p-6'>
      {tripId && gateReason ? (
        <PlanningStageGate tripId={tripId} reason={gateReason} />
      ) : (
        <SafetyPanel tripId={tripId || ''} />
      )}
    </div>
  );
}
