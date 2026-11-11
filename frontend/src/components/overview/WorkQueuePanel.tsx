'use client';

/**
 * WorkQueuePanel — operator triage queue over the canonical work-intake store
 * (`GET /api/v1/work-items`, `PATCH /api/v1/work-items/{id}`).
 *
 * Defaults to Client Demand (`origin: 'demand'`) so live traveler inquiries and
 * channel replies are never buried behind background watchdog alerts. Operators
 * can switch origins (Client Demand, System Alerts, Team Activity, All) and filter
 * by urgency, flagged duplicates, or returning guests.
 */

import {
  Activity,
  AlertTriangle,
  ArrowUpRight,
  Check,
  FileCheck2,
  Globe,
  MessageSquare,
  Repeat,
  RotateCw,
  X,
} from 'lucide-react';
import Link from 'next/link';
import { useState } from 'react';
import { useWorkItemAction, useWorkItems } from '@/hooks/useWorkItems';
import { getTripRoute } from '@/lib/routes';
import type { WorkItemAction, WorkItemEntry } from '@/lib/work-items-api';

type OriginTab = 'demand' | 'system' | 'operator' | 'all';
type QueueFilter = 'urgent' | 'duplicate' | 'returning' | null;

const CHANNEL_TOKEN_LABELS: Record<string, string> = {
  whatsapp: 'WhatsApp',
  whatsapp_web: 'WhatsApp',
  instagram_dm: 'Instagram DM',
  public_checker: 'Public checker',
  extension: 'Chrome extension',
  proposal_link: 'Proposal link',
};

function humanizeToken(raw: string): string {
  const mapped = CHANNEL_TOKEN_LABELS[raw];
  if (mapped) return mapped;
  return raw
    .split('_')
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

function formatMetaSegments(meta: string[]): string[] {
  return meta
    .map((segment) => {
      const trimmed = segment.trim();
      if (!trimmed) return '';
      return CHANNEL_TOKEN_LABELS[trimmed] ?? trimmed;
    })
    .filter(Boolean);
}

function timeOfDay(iso: string): string {
  try {
    return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } catch {
    return '';
  }
}

function SourceIcon({ item }: { item: WorkItemEntry }) {
  const isUrgent = item.urgency === 'high';
  let Icon = MessageSquare;
  if (item.origin === 'system') {
    Icon = AlertTriangle;
  } else if (item.channel === 'proposal_link') {
    Icon = FileCheck2;
  } else if (item.channel === 'public_checker') {
    Icon = Globe;
  } else if (item.origin === 'operator') {
    Icon = Activity;
  }

  return (
    <span
      className='inline-flex items-center justify-center size-7 rounded-md border shrink-0'
      style={{
        color: isUrgent ? 'var(--accent-red)' : 'var(--text-tertiary)',
        borderColor: isUrgent ? 'rgba(248,113,113,0.35)' : 'var(--border-default)',
        background: isUrgent ? 'rgba(248,113,113,0.10)' : 'var(--bg-surface)',
      }}
      aria-label={`urgency ${item.urgency}`}
      title={`Urgency: ${item.urgency}`}
    >
      <Icon className='size-3.5' aria-hidden='true' />
    </span>
  );
}

function ActionButton({
  label,
  title,
  onClick,
  disabled,
  icon,
  hoverColor,
}: {
  label: string;
  title: string;
  onClick: () => void;
  disabled?: boolean;
  icon: React.ReactNode;
  hoverColor: string;
}) {
  return (
    <button
      type='button'
      onClick={onClick}
      disabled={disabled}
      title={title}
      aria-label={title}
      className='inline-flex items-center gap-1 rounded-md border px-2 py-1 text-[11px] font-medium transition-colors disabled:opacity-50 shrink-0 cursor-pointer'
      style={{ borderColor: 'var(--border-default)', color: 'var(--text-tertiary)' }}
      onMouseEnter={(e) => {
        if (!disabled) e.currentTarget.style.color = hoverColor;
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.color = 'var(--text-tertiary)';
      }}
    >
      {icon}
      {label}
    </button>
  );
}

function WorkQueueRow({
  item,
  onAction,
  pending,
  noteEditor,
  onOpenNoteEditor,
  onCloseNoteEditor,
  onSubmitNote,
  noteDraft,
  onNoteDraftChange,
}: {
  item: WorkItemEntry;
  onAction: (itemId: string, action: WorkItemAction) => void;
  pending: boolean;
  noteEditor: { itemId: string; action: WorkItemAction } | null;
  onOpenNoteEditor: (itemId: string, action: WorkItemAction) => void;
  onCloseNoteEditor: () => void;
  onSubmitNote: (itemId: string, action: WorkItemAction, note: string) => void;
  noteDraft: string;
  onNoteDraftChange: (value: string) => void;
}) {
  const claimed = item.state === 'claimed';
  const done = item.state === 'resolved' || item.state === 'dismissed';
  const editorOpen = noteEditor?.itemId === item.item_id;
  const metaSegments = formatMetaSegments(item.meta);
  const subtitleText = metaSegments.length > 0 ? metaSegments.join(' · ') : humanizeToken(item.door);

  return (
    <li
      className='flex items-center gap-3 px-3 py-2.5 rounded-lg border'
      style={{
        background: 'var(--bg-elevated)',
        borderColor: 'rgba(255,255,255,0.04)',
        opacity: done ? 0.65 : 1,
      }}
    >
      <SourceIcon item={item} />

      <div className='flex-1 min-w-0'>
        <div className='flex items-center gap-2 flex-wrap'>
          <span className='text-[13px] font-medium truncate' style={{ color: 'var(--text-primary)' }}>
            {item.headline || humanizeToken(item.door)}
          </span>
          {item.urgency === 'high' && (
            <span
              className='inline-flex items-center rounded-full px-1.5 py-0.5 text-[10px] font-semibold shrink-0'
              style={{
                color: 'var(--accent-red)',
                background: 'rgba(248,113,113,0.12)',
              }}
            >
              Urgent
            </span>
          )}
          {(item.group_count ?? 1) > 1 && (
            <span
              className='inline-flex items-center rounded-full border px-1.5 py-0.5 text-[10px] font-semibold shrink-0'
              style={{ color: 'var(--text-secondary)', borderColor: 'var(--border-default)' }}
              title={`${item.group_count} identical items on this entity collapsed into one obligation — resolving this resolves them all`}
            >
              ×{item.group_count}
            </span>
          )}
          {done && (
            <span
              className='inline-flex items-center text-[10px] font-semibold uppercase tracking-wider shrink-0'
              style={{ color: 'var(--text-tertiary)' }}
            >
              {item.state}
            </span>
          )}
          {claimed && (
            <span
              className='inline-flex items-center gap-1 text-[10px] font-semibold shrink-0'
              style={{ color: 'var(--accent-blue)' }}
              title={item.claimed_by ? `Claimed by ${item.claimed_by}` : 'Claimed'}
            >
              claimed
            </span>
          )}
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
        <div
          className='text-[11px] mt-0.5 truncate'
          style={{ color: 'var(--text-muted)' }}
          title={`Classification: ${item.origin} · ${item.intent} · ${item.authority}${item.channel ? ` · ${item.channel}` : ''}${item.trip_id ? ` · trip ${item.trip_id}` : ''}`}
        >
          {subtitleText}
        </div>
      </div>

      {editorOpen && noteEditor ? (
        <form
          className='flex items-center gap-1 shrink-0'
          onSubmit={(e) => {
            e.preventDefault();
            onSubmitNote(item.item_id, noteEditor.action, noteDraft);
          }}
        >
          <input
            type='text'
            value={noteDraft}
            onChange={(e) => onNoteDraftChange(e.target.value)}
            placeholder='why? (optional)'
            aria-label={`Outcome note for ${noteEditor.action}`}
            maxLength={200}
            className='w-40 rounded-md border px-2 py-0.5 text-[11px]'
            style={{ borderColor: 'var(--border-default)', background: 'var(--bg-surface)', color: 'var(--text-primary)' }}
          />
          <button
            type='submit'
            disabled={pending}
            title={`Confirm ${noteEditor.action} with this note`}
            aria-label={`Confirm ${noteEditor.action} with this note`}
            className='inline-flex items-center rounded-md border px-1.5 py-0.5 text-[10px] font-medium transition-colors disabled:opacity-50'
            style={{ borderColor: 'var(--border-default)', color: 'var(--accent-green)' }}
          >
            Confirm
          </button>
          <ActionButton
            label='Cancel'
            title='Close the note editor'
            onClick={onCloseNoteEditor}
            disabled={pending}
            icon={<X className='size-3' aria-hidden='true' />}
            hoverColor='var(--text-secondary)'
          />
        </form>
      ) : (
        <div className='flex items-center gap-1.5 shrink-0'>
          {item.trip_id && (
            <Link
              href={getTripRoute(item.trip_id, 'intake')}
              className='inline-flex items-center gap-1 rounded-md border px-2 py-1 text-[11px] font-medium transition-colors hover:bg-white/5 shrink-0'
              style={{ borderColor: 'rgba(88,166,255,0.28)', color: 'var(--accent-blue)' }}
              title={`Open trip ${item.trip_id}`}
            >
              Open trip
              <ArrowUpRight className='size-3' aria-hidden='true' />
            </Link>
          )}
          {done ? null : claimed ? (
            <>
              <ActionButton
                label='Resolve'
                title='Mark resolved — handled, outcome recorded (add a note)'
                onClick={() => onOpenNoteEditor(item.item_id, 'resolve')}
                disabled={pending}
                icon={<Check className='size-3' aria-hidden='true' />}
                hoverColor='var(--accent-green)'
              />
              <ActionButton
                label='Release'
                title='Release the claim back to the open queue'
                onClick={() => onAction(item.item_id, 'unclaim')}
                disabled={pending}
                icon={<RotateCw className='size-3' aria-hidden='true' />}
                hoverColor='var(--text-secondary)'
              />
            </>
          ) : (
            <>
              <ActionButton
                label='Claim'
                title='Claim this item — it stays on your queue until resolved'
                onClick={() => onAction(item.item_id, 'claim')}
                disabled={pending}
                icon={<Check className='size-3' aria-hidden='true' />}
                hoverColor='var(--accent-blue)'
              />
              <ActionButton
                label='Dismiss'
                title='Dismiss — no action needed; leaves the ranked queue (add a note)'
                onClick={() => onOpenNoteEditor(item.item_id, 'dismiss')}
                disabled={pending}
                icon={<X className='size-3' aria-hidden='true' />}
                hoverColor='var(--accent-red)'
              />
            </>
          )}
        </div>
      )}

      <span className='text-[11px] tabular-nums shrink-0' style={{ color: 'var(--text-tertiary)' }}>
        {timeOfDay(item.received_at)}
      </span>
    </li>
  );
}

export function WorkQueuePanel() {
  const [originTab, setOriginTab] = useState<OriginTab>('demand');
  const [activeFilter, setActiveFilter] = useState<QueueFilter>(null);
  const [includeDone, setIncludeDone] = useState(false);

  const { data, isLoading, error } = useWorkItems({
    limit: 8,
    includeDone,
    origin: originTab === 'all' ? undefined : originTab,
    urgency: activeFilter === 'urgent' ? 'high' : undefined,
    duplicateOnly: activeFilter === 'duplicate',
    returningOnly: activeFilter === 'returning',
  });

  const action = useWorkItemAction();
  const [actionError, setActionError] = useState<string | null>(null);
  const [noteEditor, setNoteEditor] = useState<{ itemId: string; action: WorkItemAction } | null>(
    null
  );
  const [noteDraft, setNoteDraft] = useState('');

  const closeNoteEditor = () => {
    setNoteEditor(null);
    setNoteDraft('');
  };

  const handleAction = (itemId: string, act: WorkItemAction, note?: string) => {
    setActionError(null);
    closeNoteEditor();
    action.mutate(
      { itemId, action: act, note },
      { onError: () => setActionError(act) }
    );
  };

  const doneCount = data
    ? (data.counts.by_state.resolved ?? 0) + (data.counts.by_state.dismissed ?? 0)
    : 0;

  const originTabs: Array<{ id: OriginTab; label: string; count: number | null }> = [
    { id: 'demand', label: 'Client Demand', count: data ? (data.counts.by_origin.demand ?? 0) : null },
    { id: 'system', label: 'System Alerts', count: data ? (data.counts.by_origin.system ?? 0) : null },
    { id: 'operator', label: 'Team Activity', count: data ? (data.counts.by_origin.operator ?? 0) : null },
    { id: 'all', label: 'All Signals', count: data ? (data.actionable ?? 0) : null },
  ];

  return (
    <section
      className='rounded-xl border p-4'
      style={{ background: 'var(--bg-surface)', borderColor: 'var(--border-default)' }}
      aria-label='Incoming Work'
    >
      <div className='flex items-center justify-between gap-3 flex-wrap'>
        <div>
          <h2 className='text-[14px] font-semibold' style={{ color: 'var(--text-primary)' }}>
            Incoming Work
          </h2>
          <p className='text-[11px] mt-0.5' style={{ color: 'var(--text-muted)' }}>
            Live client inquiries, channel replies, and watchdog alerts
          </p>
        </div>

        {data && (
          <div className='flex items-center gap-1.5 text-[11px] flex-wrap' style={{ color: 'var(--text-muted)' }}>
            {data.counts.by_urgency.high > 0 && (
              <button
                type='button'
                onClick={() => setActiveFilter((curr) => (curr === 'urgent' ? null : 'urgent'))}
                aria-pressed={activeFilter === 'urgent'}
                title={activeFilter === 'urgent' ? 'Clear urgent filter' : 'Filter queue to urgent items'}
                className='inline-flex items-center gap-1 font-semibold rounded-full px-2 py-0.5 transition-all cursor-pointer border'
                style={{
                  color: 'var(--accent-red)',
                  borderColor: activeFilter === 'urgent' ? 'rgba(248,113,113,0.5)' : 'transparent',
                  background: activeFilter === 'urgent' ? 'rgba(248,113,113,0.18)' : 'transparent',
                }}
              >
                <AlertTriangle className='size-3' aria-hidden='true' />
                <span>{data.counts.by_urgency.high} urgent</span>
                {activeFilter === 'urgent' && <X className='size-2.5 ml-0.5 opacity-80' />}
              </button>
            )}
            {data.duplicates_flagged > 0 && (
              <button
                type='button'
                onClick={() => setActiveFilter((curr) => (curr === 'duplicate' ? null : 'duplicate'))}
                aria-pressed={activeFilter === 'duplicate'}
                title={activeFilter === 'duplicate' ? 'Clear duplicate filter' : 'Filter queue to flagged duplicates'}
                className='inline-flex items-center gap-1 font-semibold rounded-full px-2 py-0.5 transition-all cursor-pointer border'
                style={{
                  color: 'var(--accent-amber)',
                  borderColor: activeFilter === 'duplicate' ? 'rgba(245,158,11,0.5)' : 'transparent',
                  background: activeFilter === 'duplicate' ? 'rgba(245,158,11,0.18)' : 'transparent',
                }}
              >
                <span>{data.duplicates_flagged} dup?</span>
                {activeFilter === 'duplicate' && <X className='size-2.5 ml-0.5 opacity-80' />}
              </button>
            )}
            {data.returning_customers > 0 && (
              <button
                type='button'
                onClick={() => setActiveFilter((curr) => (curr === 'returning' ? null : 'returning'))}
                aria-pressed={activeFilter === 'returning'}
                title={activeFilter === 'returning' ? 'Clear returning filter' : 'Filter queue to returning guests'}
                className='inline-flex items-center gap-1 font-medium rounded-full px-2 py-0.5 transition-all cursor-pointer border'
                style={{
                  color: activeFilter === 'returning' ? 'var(--accent-blue)' : 'var(--text-secondary)',
                  borderColor: activeFilter === 'returning' ? 'rgba(59,130,246,0.5)' : 'transparent',
                  background: activeFilter === 'returning' ? 'rgba(59,130,246,0.18)' : 'transparent',
                }}
              >
                <span>{data.returning_customers} returning</span>
                {activeFilter === 'returning' && <X className='size-2.5 ml-0.5 opacity-80' />}
              </button>
            )}
            <span aria-label='total work items' className='px-1 tabular-nums'>
              {data.total} total
            </span>
            {doneCount > 0 && (
              <button
                type='button'
                onClick={() => setIncludeDone((v) => !v)}
                className='underline underline-offset-2 cursor-pointer'
                style={{ color: 'var(--accent-blue)' }}
                aria-pressed={includeDone}
              >
                {includeDone ? 'hide done' : `show ${doneCount} done`}
              </button>
            )}
          </div>
        )}
      </div>

      {!error && (
        <div
          className='mt-3 flex items-center gap-1.5 flex-wrap border-b pb-2.5'
          style={{ borderColor: 'var(--border-default)' }}
          role='tablist'
          aria-label='Filter incoming work by source'
        >
          {originTabs.map((tab) => {
            const active = originTab === tab.id;
            return (
              <button
                key={tab.id}
                type='button'
                role='tab'
                aria-selected={active}
                onClick={() => setOriginTab(tab.id)}
                className='inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 text-[11px] font-medium transition-colors cursor-pointer border'
                style={{
                  color: active ? 'var(--text-primary)' : 'var(--text-tertiary)',
                  background: active ? 'var(--bg-elevated)' : 'transparent',
                  borderColor: active ? 'var(--border-default)' : 'transparent',
                }}
              >
                <span>{tab.label}</span>
                {tab.count !== null && (
                  <span
                    className='tabular-nums text-[10px] rounded px-1 py-0.2'
                    style={{
                      color: active ? 'var(--accent-blue)' : 'var(--text-muted)',
                      background: active ? 'rgba(88,166,255,0.12)' : 'rgba(255,255,255,0.04)',
                    }}
                  >
                    {tab.count}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      )}

      {activeFilter && (
        <div
          className='mt-3 flex items-center justify-between px-3 py-1.5 rounded-lg border text-[11px]'
          style={{ background: 'var(--bg-elevated)', borderColor: 'var(--border-default)' }}
        >
          <span style={{ color: 'var(--text-secondary)' }}>
            Showing{' '}
            <strong style={{ color: 'var(--text-primary)' }}>
              {activeFilter === 'urgent' && 'High Urgency'}
              {activeFilter === 'duplicate' && 'Flagged Duplicates'}
              {activeFilter === 'returning' && 'Returning Customers'}
            </strong>{' '}
            items only
          </span>
          <button
            type='button'
            onClick={() => setActiveFilter(null)}
            className='inline-flex items-center gap-1 underline underline-offset-2 text-[11px] cursor-pointer'
            style={{ color: 'var(--accent-blue)' }}
            aria-label='Clear filter'
          >
            <X className='size-3' aria-hidden='true' />
            Show all
          </button>
        </div>
      )}

      {error && (
        <p className='text-[12px] mt-3' style={{ color: 'var(--text-muted)' }}>
          Work queue unavailable.
        </p>
      )}
      {actionError && (
        <p className='text-[12px] mt-3' style={{ color: 'var(--accent-amber)' }} role='alert'>
          Could not {actionError} that item — it may have just changed state. The queue will refresh.
        </p>
      )}
      {isLoading && (
        <div className='mt-3 space-y-2' aria-label='loading work queue'>
          {['wq-skeleton-1', 'wq-skeleton-2', 'wq-skeleton-3'].map((key) => (
            <div key={key} className='h-11 rounded-lg animate-pulse' style={{ background: 'var(--bg-elevated)' }} />
          ))}
        </div>
      )}
      {data && data.items.length === 0 && (
        <div className='text-[12px] mt-3' style={{ color: 'var(--text-muted)' }}>
          {activeFilter ? (
            <div className='flex items-center gap-2'>
              <span>No incoming work matches the {activeFilter} filter.</span>
              <button
                type='button'
                onClick={() => setActiveFilter(null)}
                className='underline underline-offset-2 cursor-pointer'
                style={{ color: 'var(--accent-blue)' }}
              >
                Clear filter
              </button>
            </div>
          ) : originTab !== 'all' && data.actionable > 0 ? (
            <div className='flex items-center gap-2'>
              <span>No open items in this category.</span>
              <button
                type='button'
                onClick={() => setOriginTab('all')}
                className='underline underline-offset-2 cursor-pointer'
                style={{ color: 'var(--accent-blue)' }}
              >
                View all {data.actionable} active items
              </button>
            </div>
          ) : (
            <p>
              No incoming work recorded yet. Every inquiry, reply, and system alert that reaches
              this agency will appear here.
            </p>
          )}
        </div>
      )}
      {data && data.items.length > 0 && (
        <ol className='mt-3 space-y-2'>
          {data.items.map((item) => (
            <WorkQueueRow
              key={item.item_id}
              item={item}
              onAction={handleAction}
              pending={action.isPending}
              noteEditor={noteEditor}
              onOpenNoteEditor={(itemId, act) => {
                setNoteEditor({ itemId, action: act });
                setNoteDraft('');
              }}
              onCloseNoteEditor={closeNoteEditor}
              onSubmitNote={handleAction}
              noteDraft={noteDraft}
              onNoteDraftChange={setNoteDraft}
            />
          ))}
        </ol>
      )}
      {data && data.items.length > 0 && data.total > data.items.length && (
        <p className='text-[11px] mt-3 tabular-nums' style={{ color: 'var(--text-tertiary)' }}>
          Showing {data.items.length} of {data.total} logged work items
        </p>
      )}
    </section>
  );
}
