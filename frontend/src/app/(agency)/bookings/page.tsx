import type { Metadata } from 'next';
import { Suspense } from 'react';
import PageClient from './PageClient';

export const metadata: Metadata = {
  title: 'Waypoint OS — Bookings',
  description: 'Sample booking records and local document-parse preview; no provider-backed booking state.',
};

export default function Page() {
  return (
    <Suspense fallback={<div className="p-6 text-[#8b949e]">Loading bookings…</div>}>
      <PageClient />
    </Suspense>
  );
}
