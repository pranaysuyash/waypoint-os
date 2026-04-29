/**
 * AnalyticsEmptyState
 *
 * Operational, not decorative.
 * Communicates what data is needed and how to create it.
 */

import { BarChart3, ArrowRight } from 'lucide-react';
import Link from 'next/link';

export function AnalyticsEmptyState({
  title = 'Not enough trip data yet',
  body = 'Insights will appear after trips move through inquiry, quote, and booking stages.',
  showCta = true,
}: {
  title?: string;
  body?: string;
  showCta?: boolean;
}) {
  return (
    <div
      className='rounded-xl border p-8 text-center flex flex-col items-center'
      style={{
        background: 'var(--bg-surface)',
        borderColor: 'var(--border-default)',
      }}
    >
      <div
        className='w-14 h-14 rounded-xl flex items-center justify-center mb-4'
        style={{
          background: 'var(--bg-elevated)',
          border: '1px solid var(--border-default)',
        }}
      >
        <BarChart3 className='w-6 h-6' style={{ color: 'var(--text-tertiary)' }} />
      </div>
      <p className='text-[14px] font-medium mb-1' style={{ color: 'var(--text-primary)' }}>{title}</p>
      <p className='text-[13px] leading-relaxed max-w-[360px]' style={{ color: 'var(--text-secondary)' }}>{body}</p>
      {showCta && (
        <Link
          href='/workbench?tab=intake'
          className='inline-flex items-center gap-1.5 mt-4 text-[13px] font-medium transition-colors'
          style={{ color: 'var(--accent-blue)' }}
        >
          Start a new inquiry
          <ArrowRight className='h-3.5 w-3.5' />
        </Link>
      )}
    </div>
  );
}
