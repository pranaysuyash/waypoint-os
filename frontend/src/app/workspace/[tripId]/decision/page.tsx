'use client';

import { useTripContext } from '@/contexts/TripContext';
import { DecisionPanel } from '@/components/workspace/panels/DecisionPanel';

export default function DecisionPage() {
  const { tripId } = useTripContext();
  
  return (
    <div className='p-6'>
      <DecisionPanel tripId={tripId || ''} />
    </div>
  );
}