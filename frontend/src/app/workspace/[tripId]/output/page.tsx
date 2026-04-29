'use client';

import { useTripContext } from '@/contexts/TripContext';
import OutputPanel from '@/components/workspace/panels/OutputPanel';

export default function WorkspaceOutputPage() {
  const { tripId } = useTripContext();

  return (
    <div className='p-6'>
      <div className='mb-6'>
        <h2 className='text-ui-xl flex items-center gap-2 text-[#e6edf3] font-semibold'>
          Outgoing Deliverables
        </h2>
        <p className='text-ui-sm text-[#8b949e] mt-1'>
          Constructed agent notes and client-facing responses based on strategy.
        </p>
      </div>

      <OutputPanel tripId={tripId || ''} />
    </div>
  );
}