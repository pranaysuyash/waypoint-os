import Link from 'next/link';
import { ArrowRight } from 'lucide-react';
import type { ActionRequiredItem } from '@/app/(agency)/overview/buildActionRequiredItems';

const PRIORITY_STYLES = {
  urgent: {
    color: 'var(--accent-red)',
    borderColor: 'rgba(248,81,73,0.24)',
    background: 'rgba(248,81,73,0.08)',
    label: 'Urgent',
  },
  high: {
    color: 'var(--accent-amber)',
    borderColor: 'rgba(210,153,34,0.24)',
    background: 'rgba(210,153,34,0.08)',
    label: 'High',
  },
  normal: {
    color: 'var(--accent-blue)',
    borderColor: 'rgba(88,166,255,0.24)',
    background: 'rgba(88,166,255,0.08)',
    label: 'Next',
  },
  low: {
    color: 'var(--text-muted)',
    borderColor: 'var(--border-default)',
    background: 'var(--bg-elevated)',
    label: 'Later',
  },
} as const;

export function ActionRequiredList({
  items,
  isLoading = false,
  error = null,
}: {
  items: ActionRequiredItem[];
  isLoading?: boolean;
  error?: Error | null;
}) {
  return (
    <section
      className='rounded-xl border p-4'
      style={{ background: 'var(--bg-surface)', borderColor: 'var(--border-default)' }}
      aria-label='Action Required'
    >
      <div className='mb-3'>
        <h2 className='text-[12px] font-semibold uppercase tracking-wider' style={{ color: 'var(--text-tertiary)' }}>
          Action Required
        </h2>
        <p className='text-[13px] mt-1' style={{ color: 'var(--text-secondary)' }}>
          Trips, enquiries, and quotes that need attention first.
        </p>
      </div>

      {isLoading ? (
        <p className='text-[13px]' style={{ color: 'var(--text-muted)' }}>
          Checking for action required…
        </p>
      ) : error ? (
        <div className='space-y-1'>
          <p className='text-[13px]' style={{ color: 'var(--accent-red)' }}>
            Action required is unavailable right now.
          </p>
          <p className='text-[12px]' style={{ color: 'var(--text-muted)' }}>
            Some overview data could not be loaded.
          </p>
        </div>
      ) : items.length === 0 ? (
        <p className='text-[13px]' style={{ color: 'var(--text-muted)' }}>
          No urgent action detected from available data.
        </p>
      ) : (
        <ul className='divide-y' style={{ borderColor: 'var(--border-default)' }}>
          {items.map((item) => (
            <li key={item.id} className='py-3 first:pt-0 last:pb-0'>
              <div className='flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between'>
                <div className='min-w-0'>
                  <div className='flex items-center gap-2 mb-1.5'>
                    <span
                      className='inline-flex rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider'
                      style={{
                        color: PRIORITY_STYLES[item.priority].color,
                        borderColor: PRIORITY_STYLES[item.priority].borderColor,
                        background: PRIORITY_STYLES[item.priority].background,
                      }}
                    >
                      {PRIORITY_STYLES[item.priority].label}
                    </span>
                    <p className='text-[13px] font-semibold' style={{ color: 'var(--text-primary)' }}>{item.title}</p>
                  </div>
                  <p className='text-[13px]' style={{ color: 'var(--text-secondary)' }}>{item.subtitle}</p>
                  {item.meta ? (
                    <p className='text-[12px] mt-0.5' style={{ color: 'var(--accent-blue)' }}>{item.meta}</p>
                  ) : null}
                  <p className='text-[12px] mt-1' style={{ color: 'var(--text-muted)' }}>{item.reason}</p>
                </div>
                <Link
                  href={item.href}
                  className='inline-flex shrink-0 items-center gap-1 text-[12px] font-medium sm:mt-0'
                  style={{ color: 'var(--accent-blue)' }}
                >
                  {item.ctaLabel} <ArrowRight className='size-3.5' aria-hidden='true' />
                </Link>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
