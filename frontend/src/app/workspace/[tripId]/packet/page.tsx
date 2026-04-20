'use client';

import { useTripContext } from '@/contexts/TripContext';
import { PacketPanel } from '@/components/workspace/panels/PacketPanel';

export default function PacketPage() {
  const { tripId } = useTripContext();
  
  return (
    <div className='p-6'>
      <PacketPanel tripId={tripId || ''} />
    </div>
  );
}