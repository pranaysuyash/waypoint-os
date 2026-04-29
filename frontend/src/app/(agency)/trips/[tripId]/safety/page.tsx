'use client';

import { useTripContext } from '@/contexts/TripContext';
import { SafetyPanel } from '@/components/workspace/panels/SafetyPanel';

export default function SafetyPage() {
  const { tripId } = useTripContext();
  
  return (
    <div className='p-6'>
      <SafetyPanel tripId={tripId || ''} />
    </div>
  );
}