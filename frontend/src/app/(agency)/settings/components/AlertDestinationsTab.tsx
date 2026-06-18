'use client';

import { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Bell,
  BellOff,
  CheckCircle2,
  Globe,
  Mail,
  Plus,
  RefreshCw,
  Send,
  Trash2,
  AlertTriangle,
  Shield,
} from 'lucide-react';
import {
  getAlertDestinations,
  updateAlertDestinations,
  testAlertDestination,
  type AlertDestinationConfig,
} from '@/lib/api-client';

const ALERT_QUERY_KEY = ['settings', 'alert-destinations'] as const;

const SEVERITY_OPTIONS = [
  { value: 'warning', label: 'Warning & Critical' },
  { value: 'critical', label: 'Critical Only' },
];

const EVENT_TYPE_OPTIONS = [
  { value: 'threshold_warning', label: 'Budget Threshold' },
  { value: 'rate_limit_blocked', label: 'Rate Limit Block' },
  { value: 'model_rate_limit_blocked', label: 'Model Rate Limit Block' },
  { value: 'budget_exceeded', label: 'Budget Exceeded' },
  { value: 'guard_unavailable', label: 'Guard Unavailable' },
];

function makeId(): string {
  return `dest_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
}

function emptyWebhook(): AlertDestinationConfig {
  return {
    id: makeId(),
    label: '',
    enabled: true,
    type: 'webhook',
    url: '',
    email_to: '',
    email_cc: '',
    smtp_host: '',
    smtp_port: 25,
    smtp_user: '',
    smtp_use_tls: true,
    sender: 'no-reply@waypoint.ai',
    min_severity: 'warning',
    event_types: [],
    has_smtp_password: false,
  };
}

function emptyEmail(): AlertDestinationConfig {
  return {
    id: makeId(),
    label: '',
    enabled: true,
    type: 'email',
    url: '',
    email_to: '',
    email_cc: '',
    smtp_host: '',
    smtp_port: 587,
    smtp_user: '',
    smtp_use_tls: true,
    sender: 'no-reply@waypoint.ai',
    min_severity: 'warning',
    event_types: [],
    has_smtp_password: false,
  };
}

function DestinationCard({
  dest,
  onChange,
  onRemove,
  onTest,
  isTesting,
}: {
  dest: AlertDestinationConfig;
  onChange: (id: string, updates: Partial<AlertDestinationConfig>) => void;
  onRemove: (id: string) => void;
  onTest: (dest: AlertDestinationConfig) => void;
  isTesting: boolean;
}) {
  const isWebhook = dest.type === 'webhook';
  const Icon = isWebhook ? Globe : Mail;

  return (
    <div
      className='rounded-xl border p-4 space-y-4'
      style={{ background: 'var(--bg-surface)', borderColor: 'var(--border-default)' }}
    >
      <div className='flex items-center justify-between gap-3'>
        <div className='flex items-center gap-3'>
          <div
            className='size-9 rounded-lg flex items-center justify-center shrink-0'
            style={{
              background: dest.enabled ? 'rgba(63,185,80,0.1)' : 'rgba(139,148,158,0.08)',
              border: `1px solid ${dest.enabled ? 'rgba(63,185,80,0.28)' : 'var(--border-default)'}`,
              color: dest.enabled ? '#3fb950' : 'var(--text-tertiary)',
            }}
          >
            <Icon className='size-4' />
          </div>
          <input
            type='text'
            value={dest.label}
            onChange={(e) => onChange(dest.id, { label: e.target.value })}
            placeholder={isWebhook ? 'Webhook label' : 'Email label'}
            className='text-[14px] font-medium bg-transparent border-none outline-none'
            style={{ color: 'var(--text-primary)' }}
          />
        </div>
        <div className='flex items-center gap-2'>
          <button
            type='button'
            onClick={() => onTest(dest)}
            disabled={isTesting}
            className='inline-flex items-center gap-1 rounded-lg border border-[#30363d] px-2.5 py-1.5 text-[11px] text-[#e6edf3] hover:bg-[#1c2128] transition-colors disabled:opacity-40'
          >
            <Send className='size-3' />
            {isTesting ? 'Sending…' : 'Test'}
          </button>
          <button
            type='button'
            onClick={() => onRemove(dest.id)}
            className='inline-flex items-center gap-1 rounded-lg border border-[#30363d] px-2.5 py-1.5 text-[11px] text-[#f85149] hover:bg-[#f85149]/10 transition-colors'
          >
            <Trash2 className='size-3' />
          </button>
          <button
            type='button'
            onClick={() => onChange(dest.id, { enabled: !dest.enabled })}
            className={`rounded-lg border px-2.5 py-1.5 text-[11px] font-medium transition-colors ${
              dest.enabled
                ? 'border-[#3fb950]/30 bg-[#3fb950]/10 text-[#3fb950]'
                : 'border-[#30363d] bg-[#161b22] text-[#8b949e]'
            }`}
          >
            {dest.enabled ? 'On' : 'Off'}
          </button>
        </div>
      </div>

      {isWebhook ? (
        <div>
          <label className='block text-[11px] font-semibold uppercase tracking-wider mb-1.5' style={{ color: 'var(--text-tertiary)' }}>
            Webhook URL
          </label>
          <input
            type='url'
            value={dest.url}
            onChange={(e) => onChange(dest.id, { url: e.target.value })}
            placeholder='https://hooks.slack.com/services/...'
            className='w-full rounded-lg border border-[#30363d] bg-[#0d1117] px-3 py-2 text-[13px] text-[#e6edf3] placeholder-[#484f58] outline-none focus:border-[#58a6ff] transition-colors font-mono'
          />
        </div>
      ) : (
        <div className='space-y-3'>
          <div className='grid grid-cols-2 gap-3'>
            <div>
              <label className='block text-[11px] font-semibold uppercase tracking-wider mb-1.5' style={{ color: 'var(--text-tertiary)' }}>
                Recipients (comma-separated)
              </label>
              <input
                type='text'
                value={dest.email_to}
                onChange={(e) => onChange(dest.id, { email_to: e.target.value })}
                placeholder='ops@company.com, admin@company.com'
                className='w-full rounded-lg border border-[#30363d] bg-[#0d1117] px-3 py-2 text-[13px] text-[#e6edf3] placeholder-[#484f58] outline-none focus:border-[#58a6ff] transition-colors'
              />
            </div>
            <div>
              <label className='block text-[11px] font-semibold uppercase tracking-wider mb-1.5' style={{ color: 'var(--text-tertiary)' }}>
                CC (optional)
              </label>
              <input
                type='text'
                value={dest.email_cc}
                onChange={(e) => onChange(dest.id, { email_cc: e.target.value })}
                placeholder='team@company.com'
                className='w-full rounded-lg border border-[#30363d] bg-[#0d1117] px-3 py-2 text-[13px] text-[#e6edf3] placeholder-[#484f58] outline-none focus:border-[#58a6ff] transition-colors'
              />
            </div>
          </div>
          <div className='grid grid-cols-3 gap-3'>
            <div>
              <label className='block text-[11px] font-semibold uppercase tracking-wider mb-1.5' style={{ color: 'var(--text-tertiary)' }}>
                SMTP Host
              </label>
              <input
                type='text'
                value={dest.smtp_host}
                onChange={(e) => onChange(dest.id, { smtp_host: e.target.value })}
                placeholder='smtp.gmail.com'
                className='w-full rounded-lg border border-[#30363d] bg-[#0d1117] px-3 py-2 text-[13px] text-[#e6edf3] placeholder-[#484f58] outline-none focus:border-[#58a6ff] transition-colors font-mono'
              />
            </div>
            <div>
              <label className='block text-[11px] font-semibold uppercase tracking-wider mb-1.5' style={{ color: 'var(--text-tertiary)' }}>
                Port
              </label>
              <input
                type='number'
                value={dest.smtp_port}
                onChange={(e) => onChange(dest.id, { smtp_port: parseInt(e.target.value) || 25 })}
                className='w-full rounded-lg border border-[#30363d] bg-[#0d1117] px-3 py-2 text-[13px] text-[#e6edf3] outline-none focus:border-[#58a6ff] transition-colors font-mono'
              />
            </div>
            <div>
              <label className='block text-[11px] font-semibold uppercase tracking-wider mb-1.5' style={{ color: 'var(--text-tertiary)' }}>
                Sender
              </label>
              <input
                type='email'
                value={dest.sender}
                onChange={(e) => onChange(dest.id, { sender: e.target.value })}
                placeholder='no-reply@waypoint.ai'
                className='w-full rounded-lg border border-[#30363d] bg-[#0d1117] px-3 py-2 text-[13px] text-[#e6edf3] placeholder-[#484f58] outline-none focus:border-[#58a6ff] transition-colors font-mono'
              />
            </div>
          </div>
          <div className='grid grid-cols-2 gap-3'>
            <div>
              <label className='block text-[11px] font-semibold uppercase tracking-wider mb-1.5' style={{ color: 'var(--text-tertiary)' }}>
                SMTP Username (optional)
              </label>
              <input
                type='text'
                value={dest.smtp_user}
                onChange={(e) => onChange(dest.id, { smtp_user: e.target.value })}
                placeholder='user'
                className='w-full rounded-lg border border-[#30363d] bg-[#0d1117] px-3 py-2 text-[13px] text-[#e6edf3] placeholder-[#484f58] outline-none focus:border-[#58a6ff] transition-colors font-mono'
              />
            </div>
            <div className='flex items-end gap-4'>
              <label className='flex items-center gap-2 text-[12px] text-[#c9d1d9] cursor-pointer'>
                <input
                  type='checkbox'
                  checked={dest.smtp_use_tls}
                  onChange={(e) => onChange(dest.id, { smtp_use_tls: e.target.checked })}
                  className='rounded border-[#30363d] bg-[#0d1117]'
                />
                Use TLS
              </label>
              {dest.has_smtp_password && (
                <span className='text-[11px] text-[#3fb950]'>Password configured</span>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Severity filter */}
      <div className='flex items-center gap-4'>
        <div className='flex-1'>
          <label className='block text-[11px] font-semibold uppercase tracking-wider mb-1.5' style={{ color: 'var(--text-tertiary)' }}>
            Min Severity
          </label>
          <select
            value={dest.min_severity}
            onChange={(e) => onChange(dest.id, { min_severity: e.target.value as 'warning' | 'critical' })}
            className='w-full rounded-lg border border-[#30363d] bg-[#0d1117] px-3 py-2 text-[13px] text-[#e6edf3] outline-none focus:border-[#58a6ff] transition-colors'
          >
            {SEVERITY_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>
        <div className='flex-1'>
          <label className='block text-[11px] font-semibold uppercase tracking-wider mb-1.5' style={{ color: 'var(--text-tertiary)' }}>
            Event Types (empty = all)
          </label>
          <div className='flex flex-wrap gap-1.5'>
            {EVENT_TYPE_OPTIONS.map((opt) => {
              const isActive = dest.event_types.includes(opt.value);
              return (
                <button
                  key={opt.value}
                  type='button'
                  onClick={() => {
                    const next = isActive
                      ? dest.event_types.filter((t) => t !== opt.value)
                      : [...dest.event_types, opt.value];
                    onChange(dest.id, { event_types: next });
                  }}
                  className={`rounded-full border px-2 py-0.5 text-[10px] font-medium transition-colors ${
                    isActive
                      ? 'border-[#58a6ff]/30 bg-[#58a6ff]/10 text-[#58a6ff]'
                      : 'border-[#30363d] bg-[#161b22] text-[#8b949e]'
                  }`}
                >
                  {opt.label}
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

export function AlertDestinationsTab() {
  const queryClient = useQueryClient();
  const [testResults, setTestResults] = useState<Record<string, { ok: boolean; detail: string } | null>>({});

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ALERT_QUERY_KEY,
    queryFn: getAlertDestinations,
    staleTime: 30_000,
  });

  const saveMutation = useMutation({
    mutationFn: updateAlertDestinations,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ALERT_QUERY_KEY });
    },
  });

  const testMutation = useMutation({
    mutationFn: testAlertDestination,
  });

  const handleAddDestination = useCallback(
    (type: 'webhook' | 'email') => {
      const current = data ?? { enabled: false, destinations: [] };
      const newDest = type === 'webhook' ? emptyWebhook() : emptyEmail();
      saveMutation.mutate({
        enabled: current.enabled,
        destinations: [...current.destinations, newDest],
      });
    },
    [data, saveMutation],
  );

  const handleChange = useCallback(
    (id: string, updates: Partial<AlertDestinationConfig>) => {
      const current = data ?? { enabled: false, destinations: [] };
      const updated = current.destinations.map((d) =>
        d.id === id ? { ...d, ...updates } : d,
      );
      saveMutation.mutate({
        enabled: current.enabled,
        destinations: updated,
      });
    },
    [data, saveMutation],
  );

  const handleRemove = useCallback(
    (id: string) => {
      const current = data ?? { enabled: false, destinations: [] };
      saveMutation.mutate({
        enabled: current.enabled,
        destinations: current.destinations.filter((d) => d.id !== id),
      });
    },
    [data, saveMutation],
  );

  const handleTest = useCallback(
    (dest: AlertDestinationConfig) => {
      setTestResults((prev) => ({ ...prev, [dest.id]: null }));
      testMutation.mutate(
        {
          type: dest.type,
          url: dest.url,
          email_to: dest.email_to,
          smtp_host: dest.smtp_host,
          smtp_port: dest.smtp_port,
          smtp_user: dest.smtp_user,
          sender: dest.sender,
        },
        {
          onSuccess: (result) => {
            setTestResults((prev) => ({ ...prev, [dest.id]: result }));
          },
          onError: (err) => {
            setTestResults((prev) => ({
              ...prev,
              [dest.id]: { ok: false, detail: (err as Error).message || 'Test failed' },
            }));
          },
        },
      );
    },
    [testMutation],
  );

  const handleToggleGlobal = useCallback(
    (enabled: boolean) => {
      const current = data ?? { enabled: false, destinations: [] };
      saveMutation.mutate({ enabled, destinations: current.destinations });
    },
    [data, saveMutation],
  );

  if (isLoading && !data) {
    return (
      <div className='space-y-4 animate-pulse'>
        <div className='h-6 w-40 rounded' style={{ background: 'var(--bg-elevated)' }} />
        <div className='h-32 rounded-lg' style={{ background: 'var(--bg-elevated)' }} />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className='rounded-lg border border-[#f85149]/30 bg-[#f85149]/10 p-4'>
        <div className='flex items-center gap-2 text-[#f85149]'>
          <AlertTriangle className='size-4' />
          <span className='text-[13px] font-medium'>Failed to load alert destinations</span>
        </div>
        <button onClick={() => refetch()} className='mt-3 text-[12px] font-medium' style={{ color: 'var(--accent-blue)' }}>
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
            Alert Destinations
          </h3>
          <p className='text-[12px] mt-0.5' style={{ color: 'var(--text-muted)' }}>
            Configure where LLM guard alerts are delivered — webhooks and email
          </p>
        </div>
        <button
          type='button'
          onClick={() => handleToggleGlobal(!data.enabled)}
          className={`inline-flex items-center gap-1.5 rounded-lg border px-3 py-2 text-[12px] font-medium transition-colors ${
            data.enabled
              ? 'border-[#3fb950]/30 bg-[#3fb950]/10 text-[#3fb950]'
              : 'border-[#30363d] text-[#8b949e] hover:text-[#e6edf3] hover:bg-[#161b22]'
          }`}
        >
          {data.enabled ? <Bell className='size-3.5' /> : <BellOff className='size-3.5' />}
          {data.enabled ? 'Alerts Enabled' : 'Alerts Disabled'}
        </button>
      </div>

      {data.enabled && (
        <div
          className='rounded-lg border p-3 flex items-start gap-3'
          style={{ background: 'rgba(88,166,255,0.06)', borderColor: 'rgba(88,166,255,0.2)' }}
        >
          <Shield className='size-4 text-[#58a6ff] shrink-0 mt-0.5' />
          <p className='text-[12px]' style={{ color: 'var(--text-secondary)' }}>
            When enabled, the LLM usage guard will send alerts to all configured destinations
            when rate limits are hit, budgets are exceeded, or the guard becomes unavailable.
          </p>
        </div>
      )}

      {/* Destination list */}
      <div className='space-y-4'>
        {data.destinations.map((dest) => (
          <div key={dest.id}>
            <DestinationCard
              dest={dest}
              onChange={handleChange}
              onRemove={handleRemove}
              onTest={handleTest}
              isTesting={testMutation.isPending && testMutation.variables?.type === dest.type}
            />
            {testResults[dest.id] && (
              <div
                className={`mt-2 rounded-lg border px-3 py-2 text-[12px] ${
                  testResults[dest.id]!.ok
                    ? 'border-[#3fb950]/30 bg-[#3fb950]/10 text-[#3fb950]'
                    : 'border-[#f85149]/30 bg-[#f85149]/10 text-[#f85149]'
                }`}
              >
                {testResults[dest.id]!.ok ? '✓ ' : '✗ '}
                {testResults[dest.id]!.detail}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Add buttons */}
      <div className='flex items-center gap-3'>
        <button
          type='button'
          onClick={() => handleAddDestination('webhook')}
          className='inline-flex items-center gap-1.5 rounded-lg border border-[#30363d] px-3 py-2 text-[12px] text-[#e6edf3] hover:bg-[#1c2128] transition-colors'
        >
          <Plus className='size-3.5' />
          Add Webhook
        </button>
        <button
          type='button'
          onClick={() => handleAddDestination('email')}
          className='inline-flex items-center gap-1.5 rounded-lg border border-[#30363d] px-3 py-2 text-[12px] text-[#e6edf3] hover:bg-[#1c2128] transition-colors'
        >
          <Plus className='size-3.5' />
          Add Email
        </button>
        <button
          type='button'
          onClick={() => refetch()}
          className='inline-flex items-center gap-1.5 rounded-lg border border-[#30363d] px-3 py-2 text-[12px] text-[#8b949e] hover:text-[#e6edf3] hover:bg-[#1c2128] transition-colors'
        >
          <RefreshCw className='size-3.5' />
          Refresh
        </button>
      </div>

      {data.destinations.length === 0 && (
        <div
          className='rounded-xl border border-dashed p-8 text-center'
          style={{ borderColor: 'var(--border-default)', background: 'var(--bg-surface)' }}
        >
          <BellOff className='size-8 mx-auto mb-3' style={{ color: 'var(--text-muted)' }} />
          <p className='text-[13px] font-medium' style={{ color: 'var(--text-secondary)' }}>
            No alert destinations configured
          </p>
          <p className='text-[12px] mt-1' style={{ color: 'var(--text-muted)' }}>
            Add a webhook or email destination to receive LLM guard alerts
          </p>
        </div>
      )}
    </div>
  );
}
