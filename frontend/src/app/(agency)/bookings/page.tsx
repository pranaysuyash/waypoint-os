import type { Metadata } from 'next';
import { Suspense } from 'react';
import PageClient from './PageClient';

export const metadata: Metadata = {
  title: 'Waypoint OS — Bookings',
  description: 'Confirmed operational booking records and fulfillment tracking.',
};

export default function Page() {
  return (
    <Suspense fallback={<div className="p-6 text-[#8b949e]">Loading bookings…</div>}>
      <PageClient />
    </Suspense>
  );
}
