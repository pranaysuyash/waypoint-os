'use client';

import Link from 'next/link';
import type { ProductBKpiResponse } from '@/types/product-b';

function formatRate(value: unknown): string {
  return typeof value === 'number' ? `${(value * 100).toFixed(1)}%` : '—';
}

function formatLatency(value: unknown): string {
  return typeof value === 'number' ? `${(value / 1000).toFixed(1)}s` : '—';
}

export function ProductBKpiPanel({
  data,
  isLoading,
  error,
  showPlatformLink = false,
  global = false,
  onRetry,
}: {
  data: ProductBKpiResponse | null;
  isLoading: boolean;
  error: Error | null;
  showPlatformLink?: boolean;
  global?: boolean;
  onRetry?: () => void;
}) {
  if (isLoading) {
    return (
      <section className='rounded-xl border border-[#1c2128] bg-[#0f1115] p-5' aria-label='Product-B analytics'>
        <p className='text-ui-sm text-[#8b949e]'>Loading Product-B analytics…</p>
      </section>
    );
  }

  if (error) {
    const errorStatus = error && typeof error === 'object' && 'status' in error
      ? (error as Error & { status?: number }).status
      : undefined;
    const errorMessage = error instanceof Error ? error.message.toLowerCase() : '';
    const isForbidden = errorStatus === 403 || errorMessage.includes('platform administrator');
    const isUnauthenticated = errorStatus === 401 || errorMessage.includes('not authenticated');
    return (
      <section className='rounded-xl border border-[#f85149]/30 bg-[#f85149]/5 p-5' aria-label='Product-B analytics'>
        <h2 className='text-ui-base font-semibold text-[#e6edf3]'>
          {isForbidden ? 'Platform analytics access restricted' : isUnauthenticated ? 'Sign in to view Product-B analytics' : 'Product-B analytics unavailable'}
        </h2>
        <p className='mt-1 text-ui-sm text-[#8b949e]'>
          {isForbidden
            ? 'Global Product-B KPIs are available only to explicitly authorized platform administrators.'
            : isUnauthenticated
              ? 'Your session is not authorized to read this KPI scope.'
              : 'The KPI read could not be completed for this scope.'}
        </p>
        {onRetry ? (
          <button type='button' onClick={onRetry} className='mt-3 rounded-md border border-[#f85149]/50 px-3 py-1.5 text-ui-xs text-[#ff7b72]'>
            Retry
          </button>
        ) : null}
      </section>
    );
  }

  if (!data) {
    return (
      <section className='rounded-xl border border-[#1c2128] bg-[#0f1115] p-5' aria-label='Product-B analytics'>
        <h2 className='text-ui-base font-semibold text-[#e6edf3]'>Product-B analytics</h2>
        <p className='mt-1 text-ui-sm text-[#8b949e]'>No Product-B activity is available for this scope yet.</p>
      </section>
    );
  }

  const ttf = data.kpis.time_to_first_credible_finding_ms;
  const scopeLabel = global
    ? `All permitted workspaces · ${data.scope.workspace_count}`
    : 'Current agency workspace';

  return (
    <section className='rounded-xl border border-[#1c2128] bg-[#0f1115] p-5' aria-labelledby='product-b-kpis-heading'>
      <div className='flex flex-wrap items-start justify-between gap-3'>
        <div>
          <p className='text-ui-xs font-semibold uppercase tracking-wider text-[#58a6ff]'>Product-B learning loop</p>
          <h2 id='product-b-kpis-heading' className='mt-1 text-ui-base font-semibold text-[#e6edf3]'>
            {global ? 'Platform Product-B KPIs' : 'Product-B KPIs for this agency'}
          </h2>
          <p className='mt-1 text-ui-xs text-[#8b949e]'>{scopeLabel} · Last {data.window_days} days · {data.provenance.generated_at}</p>
        </div>
        {showPlatformLink ? (
          <Link href='/platform-admin/product-b' className='text-ui-xs font-medium text-[#58a6ff] hover:underline'>
            Open platform analytics →
          </Link>
        ) : null}
      </div>

      <div className='mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3'>
        <div className='rounded-lg border border-[#1c2128] bg-[#161b22] p-3'>
          <p className='text-ui-xs text-[#8b949e]'>First credible finding p50</p>
          <p className='mt-1 text-ui-xl font-semibold text-[#e6edf3]'>{formatLatency(ttf?.p50)}</p>
          <p className='mt-1 text-ui-xs text-[#8b949e]'>n={ttf?.n ?? 0}</p>
        </div>
        <div className='rounded-lg border border-[#1c2128] bg-[#161b22] p-3'>
          <p className='text-ui-xs text-[#8b949e]'>Forwarded without edit</p>
          <p className='mt-1 text-ui-xl font-semibold text-[#e6edf3]'>{formatRate(data.kpis.forward_without_edit_rate)}</p>
          <p className='mt-1 text-ui-xs text-[#8b949e]'>Action-packet sharing</p>
        </div>
        <div className='rounded-lg border border-[#1c2128] bg-[#161b22] p-3'>
          <p className='text-ui-xs text-[#8b949e]'>Product-A pull-through</p>
          <p className='mt-1 text-ui-xl font-semibold text-[#e6edf3]'>{formatRate(data.kpis.product_a_pull_through)}</p>
          <p className='mt-1 text-ui-xs text-[#8b949e]'>Qualified inquiries</p>
        </div>
      </div>

      <p className='mt-4 text-ui-xs leading-relaxed text-[#8b949e]'>
        Values are scoped to <span className='text-[#e6edf3]'>{scopeLabel}</span>. Definitions and confidence buckets come from the KPI contract; a dash means no qualifying observation, not zero.
      </p>
    </section>
  );
}
