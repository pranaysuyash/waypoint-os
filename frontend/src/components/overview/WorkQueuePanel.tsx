'use client';

/**
 * WorkQueuePanel — the operator surface over the classified incoming-work
 * queue (INCOMING_WORK_CLASSIFICATION_MAP_2026-10-24 §5 C1; the queue is the
 * one read surface over the canonical work-intake store).
 *
 * Renders urgency-ranked items with per-class counts and the outcome-state
 * lifecycle actions (map §14: claim / release / dismiss / resolve — event-
 * sourced on the backend's append-only log). Honesty rules carried over
 * from the backend contract: counts are log totals (count_basis), the
 * returning-guest badge is an on-file annotation (never confirmed trip data),
 * and the duplicate badge is a flag for operators, not an auto-merge.
 */

import { AlertTriangle, ArrowUpRight, Check, Repeat, RotateCw, X } from 'lucide-react';
import { useState } from 'react';
import { useWorkItemAction, useWorkItems } from '@/hooks/useWorkItems';
import type { WorkItemEntry, WorkItemAction } from '@/lib/work-items-api';

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
      className='inline-flex items-center gap-1 rounded-md border px-1.5 py-0.5 text-[10px] font-medium transition-colors disabled:opacity-50 shrink-0'
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
  const urgency = URGENCY_STYLE[item.urgency] ?? URGENCY_STYLE.normal;
  const claimed = item.state === 'claimed';
  const done = item.state === 'resolved' || item.state === 'dismissed';
  const editorOpen = noteEditor?.itemId === item.item_id;
  return (
    <li
      className='flex items-center gap-3 px-3 py-2 rounded-lg'
      style={{
        background: 'var(--bg-elevated)',
        opacity: done ? 0.7 : 1,
      }}
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
            {item.headline || humanizeDoor(item.door)}
          </span>
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
        {item.meta.length > 0 ? (
          <div
            className='text-[11px] mt-0.5 truncate'
            style={{ color: 'var(--text-muted)' }}
            title={`Classification: ${item.origin} · ${item.intent} · ${item.authority}${item.channel ? ` · ${item.channel}` : ''}${item.trip_id ? ` · trip ${item.trip_id}` : ''}`}
          >
            {item.meta.join(' · ')}
          </div>
        ) : (
          <div
            className='text-[11px] mt-0.5 truncate'
            style={{ color: 'var(--text-muted)' }}
            title={`Classification: ${item.origin} · ${item.intent} · ${item.authority}${item.trip_id ? ` · trip ${item.trip_id}` : ''}`}
          >
            {humanizeDoor(item.door)}
          </div>
        )}
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
        <div className='flex items-center gap-1 shrink-0'>
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
      <span className='text-[11px] shrink-0' style={{ color: 'var(--text-tertiary)' }}>
        {timeOfDay(item.received_at)}
      </span>
    </li>
  );
}

export function WorkQueuePanel() {
  const [includeDone, setIncludeDone] = useState(false);
  const { data, isLoading, error } = useWorkItems(8, includeDone);
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
            {doneCount > 0 && (
              <button
                type='button'
                onClick={() => setIncludeDone((v) => !v)}
                className='underline underline-offset-2'
                style={{ color: 'var(--accent-blue)' }}
                aria-pressed={includeDone}
              >
                {includeDone ? 'hide done' : `show ${doneCount} done`}
              </button>
            )}
          </div>
        )}
      </div>

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
        <p className='text-[11px] mt-3' style={{ color: 'var(--text-tertiary)' }}>
          Showing {data.items.length} of {data.total} · totals count the append-only work log
          <ArrowUpRight className='inline size-3 ml-1' aria-hidden='true' />
        </p>
      )}
    </section>
  );
}
