import type { Metadata } from 'next';
import { Suspense } from 'react';
import PageClient from './PageClient';

export const metadata: Metadata = {
  title: 'Waypoint OS — Quotes',
  description: 'Commercial proposals, quote versions, and pricing analysis.',
};

export default function Page() {
  return (
    <Suspense fallback={<div className="p-6 text-[#8b949e]">Loading quotes…</div>}>
      <PageClient />
    </Suspense>
  );
}
