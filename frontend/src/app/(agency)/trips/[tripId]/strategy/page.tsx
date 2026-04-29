'use client';

import { useTripContext } from '@/contexts/TripContext';
import { StrategyPanel } from '@/components/workspace/panels/StrategyPanel';

export default function StrategyPage() {
  const { tripId } = useTripContext();
  
  return (
    <div className='p-6'>
      <StrategyPanel tripId={tripId || ''} />
    </div>
  );
}