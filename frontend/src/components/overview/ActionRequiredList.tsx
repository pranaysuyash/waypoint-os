import Link from 'next/link';
import { ArrowRight, CheckCircle2 } from 'lucide-react';
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

function sanitizeReason(reason?: string): string {
  if (!reason) return '';
  return reason
    .replace(/Decision state STOP_NEEDS_REVIEW requires owner review/gi, 'Policy threshold hold · Owner review required')
    .replace(/STOP_NEEDS_REVIEW/g, 'Safety review hold')
    .replace(/^PENDING\b/i, 'Planning blockers flagged');
}

function sanitizePendingActions(actions?: string[]): string[] {
  if (!actions) return [];
  return actions
    .filter((a) => Boolean(a) && a.trim().toUpperCase() !== 'PENDING')
    .map((a) => a.replace(/STOP_NEEDS_REVIEW/g, 'Safety review hold'));
}

function cleanCriticality(criticality?: string, subtitle?: string): string | null {
  if (!criticality) return null;
  let text = criticality;
  if (subtitle && subtitle.includes('oldest') && text.includes('unassigned oldest')) {
    text = text.replace(/·\s*unassigned oldest \d+d waiting/g, '').trim();
  }
  return text || null;
}

function parseExampleDetail(detail: string): string[] {
  if (!detail) return [];
  return detail.split(/\s*·\s*/).filter(Boolean);
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
      <div className='mb-3 flex items-center justify-between gap-2 flex-wrap'>
        <div>
          <div className='flex items-center gap-2'>
            <h2 className='text-[12px] font-semibold uppercase tracking-wider' style={{ color: 'var(--text-tertiary)' }}>
              Action Required
            </h2>
            {items.length > 0 ? (
              <span
                className='inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold tracking-wider'
                style={{
                  color: 'var(--accent-red)',
                  borderColor: 'rgba(248,81,73,0.32)',
                  background: 'rgba(248,81,73,0.1)',
                }}
              >
                {items.length} {items.length === 1 ? 'alert' : 'alerts'}
              </span>
            ) : null}
          </div>
          <p className='text-[13px] mt-1' style={{ color: 'var(--text-secondary)' }}>
            Trips, enquiries, and quotes that need attention first.
          </p>
        </div>
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
        <div className='flex items-center gap-2 py-2 text-[13px]' style={{ color: 'var(--text-muted)' }}>
          <CheckCircle2 className='size-4 text-emerald-400' />
          <span>No blocking actions are available right now.</span>
        </div>
      ) : (
        <ul className='space-y-3'>
          {items.map((item, itemIndex) => {
            const itemKey = toItemKey(item, itemIndex);
            const itemCountBadge = formatItemCountBadge(item.source, item.itemCount);
            const sanitizedReason = sanitizeReason(item.reason);
            const sanitizedPending = sanitizePendingActions(item.pendingActions);
            const cleanedCriticality = cleanCriticality(item.criticalityLabel, item.subtitle);

            return (
              <li
                key={itemKey}
                className='rounded-xl border p-4 transition-all hover:border-[#384358]'
                style={{
                  background: 'rgba(22, 27, 34, 0.65)',
                  borderColor: 'var(--border-default)',
                }}
              >
                <div className='flex flex-wrap items-start gap-3'>
                  <div className='min-w-0 grow basis-80 space-y-2 [overflow-wrap:anywhere]'>
                    {/* Badge Row */}
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
                      ) : (
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
                      )}

                      {item.meta ? (
                        <span
                          className={`inline-flex rounded-full border px-2 py-0.5 text-[10px] font-medium ${
                            item.meta.toLowerCase().includes('red')
                              ? 'border-red-500/30 bg-red-500/10 text-red-400 font-semibold uppercase tracking-wider'
                              : item.meta.toLowerCase().includes('waiting') || item.meta.toLowerCase().includes('overdue')
                                ? 'border-amber-500/30 bg-amber-500/10 text-amber-400'
                                : 'border-[#30363d] bg-white/5 text-slate-300'
                          }`}
                        >
                          {item.meta}
                        </span>
                      ) : null}
                    </div>

                    {/* Title & Diagnostic Context */}
                    <div>
                      <p className='text-[15px] font-semibold tracking-tight' style={{ color: 'var(--text-primary)' }}>
                        {item.title}
                      </p>
                      <p className='text-[12px] mt-0.5' style={{ color: 'var(--text-secondary)' }}>
                        {item.subtitle}
                      </p>
                    </div>

                    {/* Diagnostic Summary Line */}
                    {(sanitizedReason || cleanedCriticality || item.reference) ? (
                      <p className='text-[12px]' style={{ color: 'var(--text-muted)' }}>
                        {sanitizedReason}
                        {cleanedCriticality ? ` · ${cleanedCriticality}` : ''}
                        {item.reference ? ` · ${item.reference}` : ''}
                      </p>
                    ) : null}

                    {/* Pending Actions as Chips */}
                    {sanitizedPending.length > 0 ? (
                      <div className='flex flex-wrap items-center gap-1.5 pt-1'>
                        <span className='text-[11px] font-semibold uppercase tracking-wider' style={{ color: 'var(--text-tertiary)' }}>
                          Pending:
                        </span>
                        {sanitizedPending.map((action, i) => (
                          <span
                            key={i}
                            className='inline-flex items-center rounded-md border px-2 py-0.5 text-[11px] font-medium'
                            style={{
                              background: 'var(--bg-elevated)',
                              borderColor: 'var(--border-default)',
                              color: 'var(--text-secondary)',
                            }}
                          >
                            {action}
                          </span>
                        ))}
                      </div>
                    ) : null}

                    {/* Next Action Callout */}
                    {item.nextAction ? (
                      <p className='text-[12px]' style={{ color: 'var(--text-secondary)' }}>
                        <span className='font-semibold' style={{ color: 'var(--text-tertiary)' }}>
                          Next:
                        </span>{' '}
                        <span>{item.nextAction}</span>
                      </p>
                    ) : null}
                  </div>

                  {/* Dispatch Action CTAs */}
                  <div className='flex min-w-0 max-w-full flex-wrap items-center gap-2'>
                    <Link
                      href={item.href}
                      className='inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-[12px] font-semibold transition-all hover:brightness-110'
                      style={{
                        color: PRIORITY_STYLES[item.priority].color,
                        borderColor: PRIORITY_STYLES[item.priority].borderColor,
                        background: PRIORITY_STYLES[item.priority].background,
                      }}
                    >
                      {item.ctaLabel} <ArrowRight className='size-3.5 shrink-0' aria-hidden='true' />
                    </Link>
                    {item.secondaryHref && item.secondaryCtaLabel ? (
                      <Link
                        href={item.secondaryHref}
                        className='inline-flex items-center gap-1 rounded-lg border border-transparent px-2.5 py-1.5 text-[12px] font-medium transition-all hover:bg-white/5'
                        style={{ color: 'var(--text-secondary)' }}
                      >
                        {item.secondaryCtaLabel} <ArrowRight className='size-3 shrink-0' aria-hidden='true' />
                      </Link>
                    ) : null}
                  </div>
                </div>
                {/* Queue examples use the entire card width. */}
                {item.examples?.length ? (
                  <div className='mt-3 space-y-2 border-t pt-3' style={{ borderColor: 'var(--border-default)' }}>
                    <p className='text-[10px] font-semibold uppercase tracking-wider' style={{ color: 'var(--text-tertiary)' }}>
                      Actionable Queue Items
                    </p>
                    <div className='grid grid-cols-[repeat(auto-fit,minmax(min(100%,16rem),1fr))] gap-2'>
                      {item.examples.map((example, index) => {
                        const detailTags = parseExampleDetail(example.detail);
                        return (
                          <Link
                            key={toExampleKey(itemKey, example, index)}
                            href={example.href}
                            className='group flex min-w-0 items-center justify-between gap-2.5 rounded-lg border p-2.5 transition-colors hover:border-blue-500/40'
                            style={{
                              background: 'var(--bg-subtle, #0d1117)',
                              borderColor: 'var(--border-default)',
                            }}
                          >
                            <div className='min-w-0 flex-1 space-y-1 [overflow-wrap:anywhere]'>
                              <div className='flex items-center gap-1.5 flex-wrap'>
                                <span
                                  className='inline-flex items-center justify-center rounded px-1.5 py-0.5 text-[10px] font-mono font-medium'
                                  style={{
                                    background: 'var(--bg-elevated)',
                                    color: 'var(--text-tertiary)',
                                    borderColor: 'var(--border-default)',
                                  }}
                                >
                                  #{index + 1}
                                </span>
                                <span
                                  className='min-w-0 text-[12px] font-semibold transition-colors group-hover:text-blue-400'
                                  style={{ color: 'var(--text-primary)' }}
                                >
                                  {example.title}
                                </span>
                              </div>
                              {detailTags.length > 0 ? (
                                <div className='flex items-center gap-1 flex-wrap'>
                                  {detailTags.map((tag, tagIdx) => {
                                    const isRef = tag.startsWith('Ref ');
                                    const isRed = tag.toLowerCase().includes('red');
                                    const isWaiting = tag.toLowerCase().includes('waiting');
                                    return (
                                      <span
                                        key={tagIdx}
                                        className={`inline-flex items-center rounded px-1.5 py-0.5 text-[10px] border ${
                                          isRef
                                            ? 'font-mono bg-blue-500/10 text-blue-300 border-blue-500/20'
                                            : isRed
                                              ? 'bg-red-500/10 text-red-400 border-red-500/20 font-semibold'
                                              : isWaiting
                                                ? 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                                                : 'bg-white/5 text-slate-400 border-[#30363d]'
                                        }`}
                                      >
                                        {tag}
                                      </span>
                                    );
                                  })}
                                </div>
                              ) : null}
                            </div>
                            <ArrowRight aria-hidden='true' className='size-3.5 shrink-0 text-slate-500 group-hover:text-blue-400 transition-transform group-hover:translate-x-0.5' />
                          </Link>
                        );
                      })}
                    </div>
                  </div>
                ) : null}
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
