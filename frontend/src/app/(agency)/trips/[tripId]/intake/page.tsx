'use client';

import { useTripContext } from '@/contexts/TripContext';
import { IntakePanel } from '@/components/workspace/panels/IntakePanel';

export default function IntakePage() {
  const { tripId, trip } = useTripContext();
  
  return (
    <div className='p-6'>
      <IntakePanel tripId={tripId || ''} trip={trip} />
    </div>
  );
}