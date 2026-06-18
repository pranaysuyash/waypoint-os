'use client';

import { useQuery } from '@tanstack/react-query';
import { AlertTriangle, CheckCircle2, Shield, Zap, DollarSign } from 'lucide-react';
import { getLlmGuardState } from '@/lib/api-client';

const GUARD_QUERY_KEY = ['settings', 'llm-guard'] as const;

function StatusPill({ enabled }: { enabled: boolean }) {
  return (
    <span
      className='inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wider'
      style={{
        color: enabled ? '#3fb950' : '#f85149',
        background: enabled ? 'rgba(63,185,80,0.12)' : 'rgba(248,81,73,0.12)',
        border: `1px solid ${enabled ? 'rgba(63,185,80,0.28)' : 'rgba(248,81,73,0.28)'}`,
      }}
    >
      {enabled ? <CheckCircle2 className='size-3' /> : <AlertTriangle className='size-3' />}
      {enabled ? 'Active' : 'Disabled'}
    </span>
  );
}

function MetricRow({
  label,
  value,
  icon: Icon,
  sub,
}: {
  label: string;
  value: string | number;
  icon: React.FC<{ className?: string }>;
  sub?: string;
}) {
  return (
    <div className='flex items-center justify-between py-3 border-b border-[#1c2128] last:border-b-0'>
      <div className='flex items-center gap-3'>
        <div
          className='size-8 rounded-lg flex items-center justify-center shrink-0'
          style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-default)' }}
        >
          <Icon className='size-4' style={{ color: 'var(--text-tertiary)' }} />
        </div>
        <div>
          <span className='text-[13px] font-medium' style={{ color: 'var(--text-primary)' }}>{label}</span>
          {sub && <p className='text-[11px]' style={{ color: 'var(--text-muted)' }}>{sub}</p>}
        </div>
      </div>
      <span className='text-[13px] font-semibold tabular-nums' style={{ color: 'var(--text-primary)' }}>
        {value}
      </span>
    </div>
  );
}

function ModelLimitsTable({ limits }: { limits: Record<string, number> }) {
  const entries = Object.entries(limits);
  if (entries.length === 0) {
    return (
      <p className='text-[12px] py-2' style={{ color: 'var(--text-muted)' }}>
        No per-model limits configured. All models share the global hourly cap.
      </p>
    );
  }

  return (
    <div className='rounded-lg border border-[#1c2128] overflow-hidden'>
      <div className='grid grid-cols-2 gap-px' style={{ background: 'var(--border-default)' }}>
        <div className='px-3 py-2 text-[11px] font-semibold uppercase tracking-wider' style={{ color: 'var(--text-tertiary)', background: 'var(--bg-elevated)' }}>
          Model
        </div>
        <div className='px-3 py-2 text-[11px] font-semibold uppercase tracking-wider text-right' style={{ color: 'var(--text-tertiary)', background: 'var(--bg-elevated)' }}>
          Hourly Limit
        </div>
      </div>
      {entries.map(([model, limit]) => (
        <div key={model} className='grid grid-cols-2 gap-px' style={{ background: 'var(--border-default)' }}>
          <div className='px-3 py-2 text-[12px] font-mono' style={{ color: 'var(--text-primary)', background: 'var(--bg-surface)' }}>
            {model}
          </div>
          <div className='px-3 py-2 text-[12px] font-mono text-right tabular-nums' style={{ color: 'var(--text-secondary)', background: 'var(--bg-surface)' }}>
            {limit.toLocaleString()}/hr
          </div>
        </div>
      ))}
    </div>
  );
}

function UsageBar({ current, max }: { current: number; max: number | null }) {
  if (!max || max <= 0) return null;
  const pct = Math.min(100, (current / max) * 100);
  const isHigh = pct >= 80;
  const color = isHigh ? '#f85149' : pct >= 50 ? '#d29922' : '#58a6ff';

  return (
    <div className='mt-2'>
      <div className='flex items-center justify-between mb-1'>
        <span className='text-[11px]' style={{ color: 'var(--text-muted)' }}>
          {current} / {max.toLocaleString()} calls this hour
        </span>
        <span className='text-[11px] font-medium' style={{ color }}>{Math.round(pct)}%</span>
      </div>
      <div className='h-1.5 rounded-full overflow-hidden' style={{ background: 'var(--bg-elevated)' }}>
        <div className='h-full rounded-full transition-all' style={{ width: `${pct}%`, background: color }} />
      </div>
    </div>
  );
}

export function GuardTab() {
  const { data: guard, isLoading, error, refetch } = useQuery({
    queryKey: GUARD_QUERY_KEY,
    queryFn: getLlmGuardState,
    staleTime: 15_000,
  });

  if (isLoading) {
    return (
      <div className='space-y-4 animate-pulse'>
        <div className='h-6 w-40 rounded' style={{ background: 'var(--bg-elevated)' }} />
        <div className='h-20 rounded-lg' style={{ background: 'var(--bg-elevated)' }} />
        <div className='h-32 rounded-lg' style={{ background: 'var(--bg-elevated)' }} />
      </div>
    );
  }

  if (error || !guard) {
    return (
      <div className='rounded-lg border border-[#f85149]/30 bg-[#f85149]/10 p-4'>
        <div className='flex items-center gap-2 text-[#f85149]'>
          <AlertTriangle className='size-4' />
          <span className='text-[13px] font-medium'>Failed to load guard status</span>
        </div>
        <p className='text-[12px] mt-1' style={{ color: 'var(--text-secondary)' }}>
          {(error as Error)?.message ?? 'Unknown error'}
        </p>
        <button
          onClick={() => refetch()}
          className='mt-3 text-[12px] font-medium'
          style={{ color: 'var(--accent-blue)' }}
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className='space-y-6'>
      {/* Header */}
      <div className='flex items-center justify-between'>
        <div>
          <h3 className='text-[15px] font-semibold' style={{ color: 'var(--text-primary)' }}>
            LLM Usage Guard
          </h3>
          <p className='text-[12px] mt-0.5' style={{ color: 'var(--text-muted)' }}>
            Controls API rate limits and budget caps for AI model calls
          </p>
        </div>
        <StatusPill enabled={guard.enabled} />
      </div>

      {/* Current Usage */}
      <div
        className='rounded-xl border p-4'
        style={{ background: 'var(--bg-surface)', borderColor: 'var(--border-default)' }}
      >
        <h4 className='text-[12px] font-semibold uppercase tracking-wider mb-3' style={{ color: 'var(--text-tertiary)' }}>
          Current Usage
        </h4>
        <div className='grid grid-cols-2 gap-4'>
          <div>
            <span className='text-[24px] font-bold tabular-nums' style={{ color: 'var(--text-primary)' }}>
              {guard.current_hourly_calls}
            </span>
            <p className='text-[11px]' style={{ color: 'var(--text-muted)' }}>calls this hour</p>
            <UsageBar current={guard.current_hourly_calls} max={guard.max_calls_per_hour} />
          </div>
          <div>
            <span className='text-[24px] font-bold tabular-nums' style={{ color: 'var(--text-primary)' }}>
              ${guard.current_daily_cost.toFixed(2)}
            </span>
            <p className='text-[11px]' style={{ color: 'var(--text-muted)' }}>spent today</p>
          </div>
        </div>
      </div>

      {/* Limits Configuration */}
      <div
        className='rounded-xl border p-4'
        style={{ background: 'var(--bg-surface)', borderColor: 'var(--border-default)' }}
      >
        <h4 className='text-[12px] font-semibold uppercase tracking-wider mb-3' style={{ color: 'var(--text-tertiary)' }}>
          Limits Configuration
        </h4>
        <div className='space-y-0'>
          <MetricRow
            label='Hourly Call Limit'
            value={guard.max_calls_per_hour?.toLocaleString() ?? 'Unlimited'}
            icon={Zap}
            sub={guard.max_calls_per_hour ? 'Global cap across all models' : 'No hourly cap configured'}
          />
          <MetricRow
            label='Daily Budget'
            value={guard.daily_budget != null ? `$${guard.daily_budget.toFixed(2)}` : 'Unlimited'}
            icon={DollarSign}
            sub={`Mode: ${guard.budget_mode}`}
          />
          <MetricRow
            label='Guard Status'
            value={guard.enabled ? 'Enforcing' : 'Permissive'}
            icon={Shield}
            sub={guard.enabled ? 'Blocks calls when limits exceeded' : 'Logging only, no enforcement'}
          />
        </div>
      </div>

      {/* Per-Model Limits */}
      <div
        className='rounded-xl border p-4'
        style={{ background: 'var(--bg-surface)', borderColor: 'var(--border-default)' }}
      >
        <h4 className='text-[12px] font-semibold uppercase tracking-wider mb-3' style={{ color: 'var(--text-tertiary)' }}>
          Per-Model Rate Limits
        </h4>
        <ModelLimitsTable limits={guard.max_calls_per_model} />
      </div>
    </div>
  );
}
