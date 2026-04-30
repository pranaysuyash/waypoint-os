'use client';

import { useTripContext } from '@/contexts/TripContext';
import OutputPanel from '@/components/workspace/panels/OutputPanel';
import { PlanningStageGate } from '@/components/workspace/PlanningStageGate';
import { getPlanningStageGateReason } from '@/lib/planning-status';

export default function WorkspaceOutputPage() {
  const { tripId, trip } = useTripContext();
  const gateReason = getPlanningStageGateReason(trip, 'output');

  return (
    <div className='p-6'>
      {tripId && gateReason ? (
        <PlanningStageGate tripId={tripId} reason={gateReason} />
      ) : (
        <>
          <div className='mb-6'>
            <h2 className='text-ui-xl flex items-center gap-2 text-[#e6edf3] font-semibold'>
              Outgoing Deliverables
            </h2>
            <p className='text-ui-sm text-[#8b949e] mt-1'>
              Constructed agent notes and client-facing responses based on strategy.
            </p>
          </div>

          <OutputPanel tripId={tripId || ''} />
        </>
      )}
    </div>
  );
}
