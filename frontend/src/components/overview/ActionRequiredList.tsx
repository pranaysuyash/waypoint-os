import Link from 'next/link';
import { ArrowRight } from 'lucide-react';
import type { ActionRequiredItem } from '@/app/(agency)/overview/buildActionRequiredItems';

export function ActionRequiredList({ items }: { items: ActionRequiredItem[] }) {
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

      {items.length === 0 ? (
        <p className='text-[13px]' style={{ color: 'var(--text-muted)' }}>
          No urgent action detected from available data.
        </p>
      ) : (
        <ul className='space-y-2'>
          {items.map((item) => (
            <li key={item.id}>
              <div
                className='rounded-lg border p-3'
                style={{ background: 'var(--bg-elevated)', borderColor: 'var(--border-default)' }}
              >
                <p className='text-[13px] font-semibold' style={{ color: 'var(--text-primary)' }}>{item.title}</p>
                <p className='text-[12px]' style={{ color: 'var(--text-secondary)' }}>{item.subtitle}</p>
                <p className='text-[12px] mt-1' style={{ color: 'var(--text-muted)' }}>{item.reason}</p>
                <Link
                  href={item.href}
                  className='inline-flex items-center gap-1 mt-2 text-[12px] font-medium'
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
