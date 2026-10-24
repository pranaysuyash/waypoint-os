'use client';

/**
 * WorkQueuePanel — the operator surface over the classified incoming-work
 * queue (INCOMING_WORK_CLASSIFICATION_MAP_2026-10-24 §5 C1; the queue is the
 * one read surface over the canonical work-intake store).
 *
 * Renders urgency-ranked items with per-class counts. Honesty rules carried
 * over from the backend contract: counts are log totals (count_basis), the
 * returning-guest badge is an on-file annotation (never confirmed trip data),
 * and the duplicate badge is a flag for operators, not an auto-merge.
 */

import { AlertTriangle, ArrowUpRight, Repeat, RotateCw } from 'lucide-react';
import { useWorkItems } from '@/hooks/useWorkItems';
import type { WorkItemEntry } from '@/lib/work-items-api';

const URGENCY_STYLE: Record<WorkItemEntry['urgency'], { color: string; bg: string }> = {
  high: { color: 'var(--accent-red)', bg: 'rgba(248,113,113,0.10)' },
  normal: { color: 'var(--text-secondary)', bg: 'transparent' },
  low: { color: 'var(--text-tertiary)', bg: 'transparent' },
};

function humanizeDoor(door: string): string {
  return door
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

function timeOfDay(iso: string): string {
  try {
    return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } catch {
    return '';
  }
}

function WorkQueueRow({ item }: { item: WorkItemEntry }) {
  const urgency = URGENCY_STYLE[item.urgency] ?? URGENCY_STYLE.normal;
  return (
    <li
      className='flex items-center gap-3 px-3 py-2 rounded-lg'
      style={{ background: 'var(--bg-elevated)' }}
    >
      <span
        className='inline-flex items-center justify-center rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider shrink-0'
        style={{
          color: urgency.color,
          borderColor: item.urgency === 'high' ? 'rgba(248,113,113,0.35)' : 'var(--border-default)',
          background: urgency.bg,
        }}
        aria-label={`urgency ${item.urgency}`}
      >
        {item.urgency}
      </span>
      <div className='flex-1 min-w-0'>
        <div className='flex items-center gap-2'>
          <span className='text-[13px] font-medium truncate' style={{ color: 'var(--text-primary)' }}>
            {humanizeDoor(item.door)}
          </span>
          {item.returning_customer && (
            <span
              className='inline-flex items-center gap-1 text-[10px] font-semibold shrink-0'
              style={{ color: 'var(--accent-green)' }}
              title={`Returning guest — ${item.memory_fact_count} facts on file`}
            >
              <RotateCw className='size-3' aria-hidden='true' />
              returning
            </span>
          )}
          {item.duplicate_of && (
            <span
              className='inline-flex items-center gap-1 text-[10px] font-semibold shrink-0'
              style={{ color: 'var(--accent-amber)' }}
              title='Same traveler submitted new demand recently — check before creating a duplicate lead'
            >
              <Repeat className='size-3' aria-hidden='true' />
              duplicate?
            </span>
          )}
          {item.money_touch && (
            <span
              className='inline-flex items-center gap-1 text-[10px] font-semibold shrink-0'
              style={{ color: 'var(--accent-blue)' }}
              title='Touches the money boundary (tracked, never moved)'
            >
              money
            </span>
          )}
        </div>
        <div className='text-[11px] mt-0.5 truncate' style={{ color: 'var(--text-muted)' }}>
          {item.origin} · {item.intent} · {item.authority}
          {item.channel ? ` · ${item.channel}` : ''}
          {item.trip_id ? ` · ${item.trip_id}` : ''}
        </div>
      </div>
      <span className='text-[11px] shrink-0' style={{ color: 'var(--text-tertiary)' }}>
        {timeOfDay(item.received_at)}
      </span>
    </li>
  );
}

export function WorkQueuePanel() {
  const { data, isLoading, error } = useWorkItems(8);

  return (
    <section
      className='rounded-xl border p-4'
      style={{ background: 'var(--bg-surface)', borderColor: 'var(--border-default)' }}
      aria-label='Incoming Work'
    >
      <div className='flex items-center justify-between gap-3 flex-wrap'>
        <div className='flex items-center gap-2'>
          <h2 className='text-[14px] font-semibold' style={{ color: 'var(--text-primary)' }}>
            Incoming Work
          </h2>
          <span
            className='inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider'
            style={{ color: 'var(--text-tertiary)', borderColor: 'var(--border-default)' }}
          >
            classified
          </span>
        </div>
        {data && (
          <div className='flex items-center gap-2 text-[11px]' style={{ color: 'var(--text-muted)' }}>
            {data.counts.by_urgency.high > 0 && (
              <span
                className='inline-flex items-center gap-1 font-semibold'
                style={{ color: 'var(--accent-red)' }}
              >
                <AlertTriangle className='size-3' aria-hidden='true' />
                {data.counts.by_urgency.high} urgent
              </span>
            )}
            {data.returning_customers > 0 && <span>{data.returning_customers} returning</span>}
            {data.duplicates_flagged > 0 && (
              <span style={{ color: 'var(--accent-amber)' }}>{data.duplicates_flagged} dup?</span>
            )}
            <span aria-label='total work items'>{data.total} total</span>
          </div>
        )}
      </div>

      {error && (
        <p className='text-[12px] mt-3' style={{ color: 'var(--text-muted)' }}>
          Work queue unavailable.
        </p>
      )}
      {isLoading && (
        <div className='mt-3 space-y-2' aria-label='loading work queue'>
          {['wq-skeleton-1', 'wq-skeleton-2', 'wq-skeleton-3'].map((key) => (
            <div key={key} className='h-10 rounded-lg animate-pulse' style={{ background: 'var(--bg-elevated)' }} />
          ))}
        </div>
      )}
      {data && data.items.length === 0 && (
        <p className='text-[12px] mt-3' style={{ color: 'var(--text-muted)' }}>
          No incoming work recorded yet. Every inquiry, reply, and system escalation that reaches
          this agency will appear here, classified.
        </p>
      )}
      {data && data.items.length > 0 && (
        <ol className='mt-3 space-y-2'>
          {data.items.map((item) => (
            <WorkQueueRow key={item.item_id} item={item} />
          ))}
        </ol>
      )}
      {data && data.items.length > 0 && data.total > data.items.length && (
        <p className='text-[11px] mt-3' style={{ color: 'var(--text-tertiary)' }}>
          Showing {data.items.length} of {data.total} · totals count the append-only work log
          <ArrowUpRight className='inline size-3 ml-1' aria-hidden='true' />
        </p>
      )}
    </section>
  );
}
