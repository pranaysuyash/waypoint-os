import Link from 'next/link';
import { ArrowRight } from 'lucide-react';
import type { ActionRequiredItem } from '@/app/(agency)/overview/buildActionRequiredItems';

const PRIORITY_STYLES = {
  urgent: {
    color: 'var(--accent-red)',
    borderColor: 'rgba(248,81,73,0.32)',
    background: 'rgba(248,81,73,0.1)',
    label: 'Urgent',
  },
  high: {
    color: 'var(--accent-amber)',
    borderColor: 'rgba(210,153,34,0.28)',
    background: 'rgba(210,153,34,0.09)',
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

function toItemKey(item: ActionRequiredItem, itemIndex: number): string {
  const sourceKey = item.source || 'item';
  const titleKey = item.title?.trim().toLowerCase().replace(/\s+/g, '-').slice(0, 60) || 'untitled';
  const hrefKey = item.href || '/';
  const id = item.id || 'item';

  return [id, `source-${sourceKey}`, `title-${titleKey}`, hrefKey, `index-${itemIndex}`]
    .filter(Boolean)
    .join('-');
}

function toExampleKey(itemKey: string, example: { id: string; title: string }, index: number): string {
  return [
    itemKey,
    example.id || '',
    example.title ? example.title.trim().toLowerCase() : '',
    `index-${index}`,
  ]
    .filter(Boolean)
    .join('-');
}

function formatItemCountBadge(source: ActionRequiredItem['source'], itemCount?: number): string | null {
  if (!itemCount || itemCount <= 1 || source === 'lead') return null;

  const noun = source === 'quote'
    ? itemCount === 1
      ? 'quote'
      : 'quotes'
    : itemCount === 1
      ? 'trip'
      : 'trips';

  return `${itemCount.toLocaleString('en-IN')} matching ${noun}`;
}

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
          No blocking actions are available right now.
        </p>
      ) : (
        <ul className='divide-y' style={{ borderColor: 'var(--border-default)' }}>
          {items.map((item, itemIndex) => {
            const itemKey = toItemKey(item, itemIndex);
            const itemCountBadge = formatItemCountBadge(item.source, item.itemCount);
            return (
              <li key={itemKey} className='py-2.5 first:pt-0 last:pb-0'>
                <div className='grid gap-2 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-start'>
                  <div className='min-w-0 space-y-1'>
                    <div className='flex flex-wrap items-center gap-2'>
                      {!item.hidePriorityBadge ? (
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
                      ) : null}
                      {itemCountBadge ? (
                        <span
                          className='inline-flex rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider'
                          style={{
                            color: 'var(--text-secondary)',
                            borderColor: 'rgba(139,148,158,0.24)',
                            background: 'rgba(139,148,158,0.06)',
                          }}
                        >
                          {itemCountBadge}
                        </span>
                      ) : null}
                      <span
                        className='inline-flex rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider'
                        style={{
                          color: 'var(--text-tertiary)',
                          borderColor: 'var(--border-default)',
                          background: 'rgba(139,148,158,0.08)',
                        }}
                      >
                        {item.label}
                      </span>
                      {item.meta ? (
                        <span className='text-[12px]' style={{ color: 'var(--text-secondary)' }}>
                          {item.meta}
                        </span>
                      ) : null}
                    </div>
                    <p className='truncate text-[14px] font-semibold' style={{ color: 'var(--text-primary)' }}>
                      {item.title}
                    </p>
                    <p className='text-[12px]' style={{ color: 'var(--text-secondary)' }}>
                      {item.subtitle}
                    </p>
                    <p className='text-[12px]' style={{ color: 'var(--text-muted)' }}>
                      {item.reason}
                      {item.criticalityLabel ? ` · ${item.criticalityLabel}` : ''}
                      {item.reference ? ` · ${item.reference}` : ''}
                    </p>
                    {item.pendingActions?.length ? (
                      <p className='text-[12px]' style={{ color: 'var(--text-secondary)' }}>
                        <span className='font-medium' style={{ color: 'var(--text-tertiary)' }}>
                          Pending:
                        </span>{' '}
                        {item.pendingActions.join(' · ')}
                      </p>
                    ) : null}
                    {item.nextAction ? (
                      <p className='text-[12px]' style={{ color: 'var(--text-secondary)' }}>
                        <span className='font-medium' style={{ color: 'var(--text-tertiary)' }}>
                          Next:
                        </span>{' '}
                        {item.nextAction}
                      </p>
                    ) : null}
                    {item.examples?.length ? (
                      <ol className='mt-2 space-y-1.5'>
                        {item.examples.map((example, index) => (
                          <li
                            key={toExampleKey(itemKey, example, index)}
                            className='grid grid-cols-[1.25rem_minmax(0,1fr)] gap-1.5 text-[12px]'
                          >
                            <span className='tabular-nums' style={{ color: 'var(--text-tertiary)' }}>
                              {index + 1}.
                            </span>
                            <span className='min-w-0'>
                              <span className='font-medium' style={{ color: 'var(--text-primary)' }}>
                                {example.title}
                              </span>
                              <span style={{ color: 'var(--text-muted)' }}> · {example.detail}</span>
                            </span>
                          </li>
                        ))}
                      </ol>
                    ) : null}
                  </div>
                  <div className='flex shrink-0 flex-wrap items-center gap-x-3 gap-y-1 sm:justify-self-end'>
                    <Link
                      href={item.href}
                      className='inline-flex items-center gap-1 text-[12px] font-medium'
                      style={{ color: 'var(--accent-blue)' }}
                    >
                      {item.ctaLabel} <ArrowRight className='size-3.5' aria-hidden='true' />
                    </Link>
                    {item.secondaryHref && item.secondaryCtaLabel ? (
                      <Link
                        href={item.secondaryHref}
                        className='inline-flex items-center gap-1 text-[12px] font-medium'
                        style={{ color: 'var(--text-secondary)' }}
                      >
                        {item.secondaryCtaLabel} <ArrowRight className='size-3.5' aria-hidden='true' />
                      </Link>
                    ) : null}
                  </div>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
