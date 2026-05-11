'use client';

import { AlertTriangle } from 'lucide-react';
import { Drawer } from '@/components/ui/drawer';
import { useIntegrityIssues } from '@/hooks/useIntegrityIssues';
import type { IntegrityAction } from '@/types/spine';

interface SystemCheckPanelProps {
  open: boolean;
  onClose: () => void;
}

function formatTimestamp(value?: string | null): string {
  if (!value) {
    return 'Unknown';
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString();
}

export default function SystemCheckPanel({
  open,
  onClose,
}: SystemCheckPanelProps) {
  const { data: issues, isLoading: loading, error } = useIntegrityIssues();

  return (
    <Drawer
      isOpen={open}
      onClose={onClose}
      title="System Check"
      width="w-96"
      showCloseButton={true}
    >
      <div className='p-4 space-y-4'>
        <div className='rounded-lg border border-[#30363d] bg-[#161b22] p-3 text-ui-xs text-[#8b949e] leading-relaxed'>
          Waypoint checks whether leads, trip plans, and quote reviews are showing in the right place.
          Issues here may mean work is stuck or detached from the normal flow.
        </div>

        {loading ? (
          <div className='rounded-lg border border-[#30363d] bg-[#161b22] p-3 text-ui-xs text-[#8b949e]'>
            Checking system status…
          </div>
        ) : error ? (
          <div className='rounded-lg border border-[#f85149]/40 bg-[#161b22] p-3 text-ui-xs text-[#f85149]'>
            System check unavailable: {error.message}
          </div>
        ) : issues.length === 0 ? (
          <div className='rounded-lg border border-[#30363d] bg-[#161b22] p-3 text-ui-xs text-[#8b949e] italic'>
            No routing issues detected.
          </div>
        ) : (
          <div className='space-y-3'>
            {issues.map((issue) => {
              const allowedActions: IntegrityAction[] = issue.allowed_actions ?? [];

              return (
                <section
                  key={issue.id}
                  className='rounded-lg border border-[#30363d] bg-[#161b22] p-3 space-y-3'
                >
                  <div className='flex items-start justify-between gap-3'>
                    <div>
                      <p className='text-[12px] uppercase tracking-wide text-[#8b949e]'>
                        Routing issue
                      </p>
                      <p className='font-mono text-ui-xs text-[#e6edf3] break-all'>
                        {issue.entity_id}
                      </p>
                    </div>
                    <span className='inline-flex items-center gap-1 rounded-full bg-[#e3b341]/15 px-2 py-1 text-[12px] font-medium text-[#e3b341]'>
                      <AlertTriangle className='size-3' />
                      {issue.severity.charAt(0).toUpperCase() + issue.severity.slice(1)}
                    </span>
                  </div>

                  <dl className='grid grid-cols-[auto_1fr] gap-x-3 gap-y-2 text-ui-xs'>
                    <dt className='text-[#8b949e]'>Entity ID</dt>
                    <dd className='text-[#e6edf3] break-all'>{issue.entity_id}</dd>

                    <dt className='text-[#8b949e]'>Entity type</dt>
                    <dd className='text-[#e6edf3]'>{issue.entity_type}</dd>

                    <dt className='text-[#8b949e]'>Current status</dt>
                    <dd className='text-[#e6edf3]'>{issue.current_status ?? 'Unknown'}</dd>

                    <dt className='text-[#8b949e]'>Created at</dt>
                    <dd className='text-[#e6edf3]'>
                      {formatTimestamp(issue.created_at)}
                    </dd>

                    <dt className='text-[#8b949e]'>Detected at</dt>
                    <dd className='text-[#e6edf3]'>
                      {formatTimestamp(issue.detected_at)}
                    </dd>

                    <dt className='text-[#8b949e]'>Reason</dt>
                    <dd className='text-[#e6edf3]'>
                      This record is detached from the normal workflow.
                    </dd>

                    <dt className='text-[#8b949e]'>Available actions</dt>
                    <dd className='text-[#e6edf3]'>
                      {allowedActions.length === 0
                        ? 'Manual review required'
                        : allowedActions
                            .map((action) => action.label)
                            .join(', ')}
                    </dd>
                  </dl>
                </section>
              );
            })}
          </div>
        )}
      </div>
    </Drawer>
  );
}
