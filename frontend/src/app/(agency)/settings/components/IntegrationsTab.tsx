'use client';

import type React from 'react';
import {
  AlertCircle,
  CalendarDays,
  CheckCircle2,
  CircleDashed,
  Cloud,
  HardDrive,
  Mail,
  MessageCircle,
  Phone,
  PlugZap,
  RefreshCw,
  ShieldCheck,
} from 'lucide-react';
import { useIntegrations, type Integration } from '@/hooks/useIntegrations';

const STATUS_LABELS: Record<Integration['status'], string> = {
  disabled: 'Disabled',
  connected: 'Connected',
  degraded: 'Degraded',
  auth_expired: 'Auth expired',
  misconfigured: 'Misconfigured',
};

const STATUS_STYLES: Record<Integration['status'], string> = {
  disabled: 'border-[#30363d] bg-[#161b22] text-[#8b949e]',
  connected: 'border-[#3fb950]/30 bg-[#3fb950]/10 text-[#3fb950]',
  degraded: 'border-[#d29922]/30 bg-[#d29922]/10 text-[#d29922]',
  auth_expired: 'border-[#f85149]/30 bg-[#f85149]/10 text-[#f85149]',
  misconfigured: 'border-[#f85149]/30 bg-[#f85149]/10 text-[#f85149]',
};

const PROVIDER_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  whatsapp: MessageCircle,
  gmail: Mail,
  google_calendar: CalendarDays,
  google_drive: HardDrive,
  sms: Phone,
  telegram: MessageCircle,
};

const CATEGORY_LABELS: Record<string, string> = {
  messaging: 'Messaging',
  email: 'Email',
  calendar: 'Calendar',
  storage: 'Storage',
};

function formatCapability(capability: string): string {
  return capability
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

function formatDate(value: string | null): string {
  if (!value) return 'Never checked';
  try {
    return new Intl.DateTimeFormat(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(new Date(value));
  } catch {
    return 'Unknown';
  }
}

function statusIcon(status: Integration['status']) {
  if (status === 'connected') return CheckCircle2;
  if (status === 'disabled') return CircleDashed;
  return AlertCircle;
}

export function IntegrationCard({ integration }: { integration: Integration }) {
  const ProviderIcon = PROVIDER_ICONS[integration.provider] ?? Cloud;
  const StatusIcon = statusIcon(integration.status);

  return (
    <article className="rounded-xl border border-[#30363d] bg-[#0d1117] p-4 space-y-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3 min-w-0">
          <div className="size-10 rounded-lg border border-[#30363d] bg-[#161b22] flex items-center justify-center text-[#58a6ff] shrink-0">
            <ProviderIcon className="size-5" />
          </div>
          <div className="min-w-0">
            <h3 className="text-ui-sm font-semibold text-[#e6edf3] truncate">
              {integration.display_name}
            </h3>
            <p className="text-ui-xs text-[#8b949e]">
              {CATEGORY_LABELS[integration.category] ?? integration.category}
            </p>
          </div>
        </div>
        <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-ui-xs font-medium ${STATUS_STYLES[integration.status]}`}>
          <StatusIcon className="size-3.5" />
          {STATUS_LABELS[integration.status]}
        </span>
      </div>

      <div className="flex flex-wrap gap-1.5">
        {integration.capabilities.map((capability) => (
          <span
            key={capability}
            className="rounded-full border border-[#30363d] bg-[#161b22] px-2 py-1 text-[11px] text-[#c9d1d9]"
          >
            {formatCapability(capability)}
          </span>
        ))}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-ui-xs">
        <div className="rounded-lg border border-[#30363d] bg-[#161b22] p-2.5">
          <p className="text-[#8b949e]">Last health check</p>
          <p className="mt-1 text-[#e6edf3]">{formatDate(integration.last_health_check_at)}</p>
        </div>
        <div className="rounded-lg border border-[#30363d] bg-[#161b22] p-2.5">
          <p className="text-[#8b949e]">Last success</p>
          <p className="mt-1 text-[#e6edf3]">{formatDate(integration.last_success_at)}</p>
        </div>
      </div>

      {integration.last_error_code || integration.last_error_message_safe ? (
        <div className="rounded-lg border border-[#d29922]/30 bg-[#d29922]/10 p-3 text-ui-xs text-[#d29922]">
          <p className="font-medium">Safe provider status</p>
          <p className="mt-1">
            {[integration.last_error_code, integration.last_error_message_safe].filter(Boolean).join(' · ')}
          </p>
        </div>
      ) : null}
    </article>
  );
}

export function IntegrationsTab() {
  const { data, isLoading, error, refetch } = useIntegrations();

  if (isLoading && !data) {
    return (
      <div className="space-y-4">
        <div>
          <h2 className="text-ui-sm font-semibold text-[#e6edf3]">Integrations</h2>
          <p className="text-ui-xs text-[#8b949e] mt-1">Loading provider status…</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {['integration-skeleton-1', 'integration-skeleton-2', 'integration-skeleton-3', 'integration-skeleton-4'].map((key) => (
            <div key={key} className="h-44 rounded-xl border border-[#30363d] bg-[#0d1117] animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="rounded-xl border border-[#f85149]/30 bg-[#f85149]/10 p-4 space-y-3">
        <div className="flex items-center gap-2 text-ui-sm text-[#f85149]">
          <AlertCircle className="size-4 shrink-0" />
          Failed to load integration status.
        </div>
        <p className="text-ui-xs text-[#f0f6fc]">{error?.message ?? 'Unknown error'}</p>
        <button
          onClick={() => refetch()}
          className="inline-flex items-center gap-1.5 rounded-lg border border-[#30363d] px-3 py-1.5 text-ui-xs text-[#e6edf3] hover:bg-[#1c2128] transition-colors"
        >
          <RefreshCw className="size-3.5" />
          Retry
        </button>
      </div>
    );
  }

  const connectedCount = data.integrations.filter((item) => item.status === 'connected').length;

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-ui-sm font-semibold text-[#e6edf3]">Integrations</h2>
          <p className="text-ui-xs text-[#8b949e] mt-1">
            Agency-scoped provider status. Setup and credential rotation stay disabled until the credential boundary and audit events are implemented.
          </p>
        </div>
        <button
          onClick={() => refetch()}
          className="inline-flex items-center gap-1.5 rounded-lg border border-[#30363d] px-3 py-2 text-ui-xs text-[#e6edf3] hover:bg-[#1c2128] transition-colors"
        >
          <RefreshCw className="size-3.5" />
          Refresh
        </button>
      </div>

      <div className="rounded-xl border border-[#30363d] bg-[#161b22] p-4 flex items-start gap-3">
        <div className="size-9 rounded-lg bg-[#58a6ff]/10 text-[#58a6ff] flex items-center justify-center shrink-0">
          <ShieldCheck className="size-4" />
        </div>
        <div className="space-y-1">
          <p className="text-ui-sm font-medium text-[#e6edf3]">
            {connectedCount} of {data.total} providers connected
          </p>
          <p className="text-ui-xs text-[#8b949e]">
            This is the read-only foundation. It proves which provider capabilities the agency could enable without exposing credentials or raw provider data.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {data.integrations.map((integration) => (
          <IntegrationCard key={integration.provider} integration={integration} />
        ))}
      </div>

      <div className="rounded-xl border border-[#30363d] bg-[#0d1117] p-4 flex items-start gap-3">
        <PlugZap className="size-4 text-[#8b949e] shrink-0 mt-0.5" />
        <p className="text-ui-xs text-[#8b949e]">
          Next safe step: add audited enable/disable/test actions after the credential storage contract is defined. Do not paste API keys or webhook secrets into generic settings fields.
        </p>
      </div>
    </div>
  );
}
