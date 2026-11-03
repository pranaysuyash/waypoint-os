import type { Metadata } from 'next';
import { Suspense } from 'react';
import PageClient from './PageClient';

export const metadata: Metadata = {
  title: 'Waypoint OS — Destination Intelligence',
  description: 'Governed external data: safety advisories, trip-date weather, traveler ratings. Missing data shown as a gap, never guessed.',
};

export default function Page() {
  return (
    <Suspense fallback={<div className="p-6 text-[#8b949e]">Loading destination intelligence…</div>}>
      <PageClient />
    </Suspense>
  );
}
