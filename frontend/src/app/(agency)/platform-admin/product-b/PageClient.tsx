'use client';

import Link from 'next/link';
import { ArrowLeft, ShieldCheck } from 'lucide-react';
import { ProductBKpiPanel } from '@/components/insights/ProductBKpiPanel';
import { usePlatformProductBKpis } from '@/hooks/useGovernance';

export default function PlatformProductBPageClient() {
  const {
    data,
    isLoading,
    error,
    refetch,
  } = usePlatformProductBKpis(30, true);

  return (
    <main className='mx-auto max-w-[1200px] space-y-6 p-5 pb-10'>
      <header className='flex flex-col gap-4 border-b border-[#1c2128] pb-5 sm:flex-row sm:items-start sm:justify-between'>
        <div>
          <div className='mb-2 flex items-center gap-2 text-ui-xs font-medium uppercase tracking-[0.16em] text-[#8b949e]'>
            <ShieldCheck className='size-4 text-[#58a6ff]' aria-hidden='true' />
            Platform administration · read only
          </div>
          <h1 className='text-ui-2xl font-semibold text-[#e6edf3]'>Platform Product-B Analytics</h1>
          <p className='mt-1 max-w-2xl text-ui-base text-[#8b949e]'>
            Global adoption and performance across agencies. This view is intentionally separate from agency operations and is restricted to platform administrators.
          </p>
        </div>
        <Link
          href='/insights'
          className='inline-flex shrink-0 items-center gap-2 text-ui-sm font-medium text-[#58a6ff] hover:text-[#79b8ff]'
        >
          <ArrowLeft className='size-4' aria-hidden='true' />
          Agency insights
        </Link>
      </header>

      <ProductBKpiPanel
        data={data}
        isLoading={isLoading}
        error={error}
        onRetry={() => void refetch()}
        global
      />
    </main>
  );
}
