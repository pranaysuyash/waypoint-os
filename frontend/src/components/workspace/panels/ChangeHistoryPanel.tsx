'use client';

import { useMemo } from 'react';
import { Clock, User, FileText, ChevronDown, ChevronUp } from 'lucide-react';
import { useFieldAuditLog } from '@/hooks/useFieldAuditLog';
import { useClientDate, useClientDateTime } from '@/hooks/useClientDate';
import { getChangeDescription, formatFieldLabel, getChangeSummary } from '@/types/audit';
import { useState } from 'react';
import type { Trip } from '@/lib/api-client';

interface ChangeHistoryPanelProps {
  tripId: string;
  trip?: Trip | null;
}

export function ChangeHistoryPanel({ tripId, trip }: ChangeHistoryPanelProps) {
  const { getChanges, isLoading, exportChanges } = useFieldAuditLog({ tripId });
  const [expandedChanges, setExpandedChanges] = useState<Set<string>>(new Set());

  const changes = useMemo(() => {
    return getChanges();
  }, [getChanges]);

  const summary = useMemo(() => {
    return getChangeSummary(changes);
  }, [changes]);

  const toggleExpand = (id: string) => {
    setExpandedChanges(prev => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const handleExport = () => {
    const data = exportChanges();
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${tripId}-audit-log-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (isLoading) {
    return (
      <div className='bg-elevated border border-border-default rounded-xl p-4'>
        <div className='flex items-center gap-2 mb-4'>
          <Clock className='size-4 text-text-muted' />
          <h3 className='text-ui-sm font-semibold text-text-primary'>Change History</h3>
        </div>
        <p className='text-ui-sm text-text-muted'>Loading change history…</p>
      </div>
    );
  }

  if (changes.length === 0) {
    return (
      <div className='bg-elevated border border-border-default rounded-xl p-4'>
        <div className='flex items-center justify-between mb-4'>
          <div className='flex items-center gap-2'>
            <Clock className='size-4 text-text-muted' />
            <h3 className='text-ui-sm font-semibold text-text-primary'>Change History</h3>
          </div>
          <span className='text-ui-xs text-text-muted'>No changes yet</span>
        </div>
        <p className='text-ui-sm text-text-muted'>
          Field edits will be tracked here. Edit trip details to see the history.
        </p>
      </div>
    );
  }

  return (
    <div className='bg-elevated border border-border-default rounded-xl p-4'>
      <div className='flex items-center justify-between mb-4'>
        <div className='flex items-center gap-2'>
          <Clock className='size-4 text-text-muted' />
          <h3 className='text-ui-sm font-semibold text-text-primary'>Change History</h3>
          <span className='text-ui-xs bg-[#58a6ff] text-[#0d1117] px-2 py-0.5 rounded-full'>
            {changes.length}
          </span>
        </div>
        <button
          onClick={handleExport}
          className='text-ui-xs text-accent-blue hover:text-[#79b8ff]'
        >
          Export
        </button>
      </div>

      {/* Summary */}
      {summary.totalChanges > 0 && (
        <div className='grid grid-cols-2 sm:grid-cols-4 gap-2 mb-4 p-3 bg-surface rounded-lg'>
          <div>
            <span className='text-[var(--ui-text-xs)] text-text-muted uppercase tracking-wide'>Total Changes</span>
            <p className='text-ui-sm font-semibold text-text-primary'>{summary.totalChanges}</p>
          </div>
          <div>
            <span className='text-[var(--ui-text-xs)] text-text-muted uppercase tracking-wide'>Last Edit</span>
            <p className='text-ui-sm font-semibold text-text-primary'>
              {summary.lastChangeAt
                ? useClientDate(summary.lastChangeAt)
                : '-'}
            </p>
          </div>
          <div>
            <span className='text-[var(--ui-text-xs)] text-text-muted uppercase tracking-wide'>Edited By</span>
            <p className='text-ui-sm font-semibold text-text-primary'>
              {summary.lastChangeBy || '-'}
            </p>
          </div>
          <div>
            <span className='text-[var(--ui-text-xs)] text-text-muted uppercase tracking-wide'>Version</span>
            <p className='text-ui-sm font-semibold text-text-primary'>
              v{changes.length}
            </p>
          </div>
        </div>
      )}

      {/* Changes List */}
      <div className='space-y-2 max-h-96 overflow-y-auto'>
        {[...changes]
          .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
          .map((change) => {
            const isExpanded = expandedChanges.has(change.id);
            const description = getChangeDescription(change);

            return (
              <div
                key={change.id}
                className='bg-surface border border-[#21262d] rounded-lg p-3'
              >
                <div className='flex items-start justify-between gap-2'>
                  <div className='flex-1 min-w-0'>
                    <p className='text-ui-sm text-text-primary'>{description}</p>
                    <div className='flex items-center gap-3 mt-1 text-ui-xs text-text-muted'>
                      <span className='flex items-center gap-1'>
                        <User className='size-3' />
                        {change.changedByName}
                      </span>
                      <span className='flex items-center gap-1'>
                        <Clock className='size-3' />
                        {useClientDateTime(change.timestamp)}
                      </span>
                      {change.reason && (
                        <span className='flex items-center gap-1 text-accent-blue'>
                          <FileText className='size-3' />
                          {change.reason}
                        </span>
                      )}
                    </div>
                  </div>
                  <button
                    onClick={() => toggleExpand(change.id)}
                    className='text-text-muted hover:text-text-primary flex-shrink-0'
                  >
                    {isExpanded ? (
                      <ChevronUp className='size-4' />
                    ) : (
                      <ChevronDown className='size-4' />
                    )}
                  </button>
                </div>

                {isExpanded && (
                  <div className='mt-3 pt-3 border-t border-[#21262d] grid grid-cols-2 gap-2 text-ui-xs'>
                    <div>
                      <span className='text-text-muted'>Field:</span>
                      <span className='ml-2 text-text-primary'>{formatFieldLabel(change.field)}</span>
                    </div>
                    <div>
                      <span className='text-text-muted'>Type:</span>
                      <span className='ml-2 text-text-primary'>{change.changeType}</span>
                    </div>
                    <div>
                      <span className='text-text-muted'>Previous:</span>
                      <span className='ml-2 text-[#f85149] line-through'>
                        {change.previousValue ?? '(empty)'}
                      </span>
                    </div>
                    <div>
                      <span className='text-text-muted'>New:</span>
                      <span className='ml-2 text-[#3fb950]'>
                        {change.newValue ?? '(empty)'}
                      </span>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
      </div>
    </div>
  );
}
