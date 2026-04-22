'use client';

import { useMemo } from 'react';
import { Clock, User, FileText, ChevronDown, ChevronUp } from 'lucide-react';
import { useFieldAuditLog } from '@/hooks/useFieldAuditLog';
import { getChangeDescription, formatFieldLabel, getChangeSummary } from '@/types/audit';
import { useState } from 'react';

interface ChangeHistoryPanelProps {
  tripId: string;
  trip?: any;
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
      <div className='bg-[#161b22] border border-[#30363d] rounded-xl p-4'>
        <div className='flex items-center gap-2 mb-4'>
          <Clock className='w-4 h-4 text-[#8b949e]' />
          <h3 className='text-sm font-semibold text-[#e6edf3]'>Change History</h3>
        </div>
        <p className='text-sm text-[#8b949e]'>Loading change history...</p>
      </div>
    );
  }

  if (changes.length === 0) {
    return (
      <div className='bg-[#161b22] border border-[#30363d] rounded-xl p-4'>
        <div className='flex items-center justify-between mb-4'>
          <div className='flex items-center gap-2'>
            <Clock className='w-4 h-4 text-[#8b949e]' />
            <h3 className='text-sm font-semibold text-[#e6edf3]'>Change History</h3>
          </div>
          <span className='text-xs text-[#8b949e]'>No changes yet</span>
        </div>
        <p className='text-sm text-[#8b949e]'>
          Field edits will be tracked here. Edit trip details to see the history.
        </p>
      </div>
    );
  }

  return (
    <div className='bg-[#161b22] border border-[#30363d] rounded-xl p-4'>
      <div className='flex items-center justify-between mb-4'>
        <div className='flex items-center gap-2'>
          <Clock className='w-4 h-4 text-[#8b949e]' />
          <h3 className='text-sm font-semibold text-[#e6edf3]'>Change History</h3>
          <span className='text-xs bg-[#58a6ff] text-[#0d1117] px-2 py-0.5 rounded-full'>
            {changes.length}
          </span>
        </div>
        <button
          onClick={handleExport}
          className='text-xs text-[#58a6ff] hover:text-[#79b8ff]'
        >
          Export
        </button>
      </div>

      {/* Summary */}
      {summary.totalChanges > 0 && (
        <div className='grid grid-cols-2 sm:grid-cols-4 gap-2 mb-4 p-3 bg-[#0f1115] rounded-lg'>
          <div>
            <span className='text-[10px] text-[#8b949e] uppercase tracking-wide'>Total Changes</span>
            <p className='text-sm font-semibold text-[#e6edf3]'>{summary.totalChanges}</p>
          </div>
          <div>
            <span className='text-[10px] text-[#8b949e] uppercase tracking-wide'>Last Edit</span>
            <p className='text-sm font-semibold text-[#e6edf3]'>
              {summary.lastChangeAt
                ? new Date(summary.lastChangeAt).toLocaleDateString()
                : '—'}
            </p>
          </div>
          <div>
            <span className='text-[10px] text-[#8b949e] uppercase tracking-wide'>Edited By</span>
            <p className='text-sm font-semibold text-[#e6edf3]'>
              {summary.lastChangeBy || '—'}
            </p>
          </div>
          <div>
            <span className='text-[10px] text-[#8b949e] uppercase tracking-wide'>Version</span>
            <p className='text-sm font-semibold text-[#e6edf3]'>
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
                className='bg-[#0f1115] border border-[#21262d] rounded-lg p-3'
              >
                <div className='flex items-start justify-between gap-2'>
                  <div className='flex-1 min-w-0'>
                    <p className='text-sm text-[#e6edf3]'>{description}</p>
                    <div className='flex items-center gap-3 mt-1 text-xs text-[#8b949e]'>
                      <span className='flex items-center gap-1'>
                        <User className='w-3 h-3' />
                        {change.changedByName}
                      </span>
                      <span className='flex items-center gap-1'>
                        <Clock className='w-3 h-3' />
                        {new Date(change.timestamp).toLocaleString()}
                      </span>
                      {change.reason && (
                        <span className='flex items-center gap-1 text-[#58a6ff]'>
                          <FileText className='w-3 h-3' />
                          {change.reason}
                        </span>
                      )}
                    </div>
                  </div>
                  <button
                    onClick={() => toggleExpand(change.id)}
                    className='text-[#8b949e] hover:text-[#e6edf3] flex-shrink-0'
                  >
                    {isExpanded ? (
                      <ChevronUp className='w-4 h-4' />
                    ) : (
                      <ChevronDown className='w-4 h-4' />
                    )}
                  </button>
                </div>

                {isExpanded && (
                  <div className='mt-3 pt-3 border-t border-[#21262d] grid grid-cols-2 gap-2 text-xs'>
                    <div>
                      <span className='text-[#8b949e]'>Field:</span>
                      <span className='ml-2 text-[#e6edf3]'>{formatFieldLabel(change.field)}</span>
                    </div>
                    <div>
                      <span className='text-[#8b949e]'>Type:</span>
                      <span className='ml-2 text-[#e6edf3]'>{change.changeType}</span>
                    </div>
                    <div>
                      <span className='text-[#8b949e]'>Previous:</span>
                      <span className='ml-2 text-[#f85149] line-through'>
                        {change.previousValue ?? '(empty)'}
                      </span>
                    </div>
                    <div>
                      <span className='text-[#8b949e]'>New:</span>
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
