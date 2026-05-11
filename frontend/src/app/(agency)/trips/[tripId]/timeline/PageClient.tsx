'use client';

import { useTripContext } from '@/contexts/TripContext';
import { TimelinePanel } from '@/components/workspace/panels/TimelinePanel';

export default function TimelinePage() {
  const { tripId } = useTripContext();
  
  return (
    <div className='p-6'>
      <TimelinePanel tripId={tripId || ''} />
    </div>
  );
}
