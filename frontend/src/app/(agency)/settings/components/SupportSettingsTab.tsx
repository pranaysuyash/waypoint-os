'use client';

import { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  CheckCircle2,
  Clock,
  Headphones,
  Mail,
  MessageCircle,
  Phone,
  AlertTriangle,
  RefreshCw,
  Send,
} from 'lucide-react';
import {
  getSupportSettings,
  updateSupportSettings,
  type SupportSettings,
  type UpdateSupportPayload,
} from '@/lib/api-client';

const SUPPORT_QUERY_KEY = ['settings', 'support'] as const;

const TIMEZONE_OPTIONS = [
  'Asia/Kolkata',
  'Asia/Dubai',
  'Europe/London',
  'America/New_York',
  'America/Los_Angeles',
  'Australia/Sydney',
  'Asia/Singapore',
  'Asia/Tokyo',
];

const DAY_OPTIONS = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'];

const DAY_LABELS: Record<string, string> = {
  mon: 'Mon', tue: 'Tue', wed: 'Wed', thu: 'Thu', fri: 'Fri', sat: 'Sat', sun: 'Sun',
};

const CSAT_OPTIONS = [
  { value: 'after_resolution', label: 'After Resolution' },
  { value: 'after_first_response', label: 'After First Response' },
  { value: 'never', label: 'Never' },
] as const;

function ChannelToggle({
  label,
  icon: Icon,
  enabled,
  onChange,
}: {
  label: string;
  icon: React.FC<{ className?: string }>;
  enabled: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <button
      type='button'
      onClick={() => onChange(!enabled)}
      className={`flex items-center gap-2 rounded-lg border px-3 py-2.5 text-[12px] font-medium transition-colors ${
        enabled
          ? 'border-[#3fb950]/30 bg-[#3fb950]/10 text-[#3fb950]'
          : 'border-[#30363d] bg-[#161b22] text-[#8b949e]'
      }`}
    >
      <Icon className='size-4' />
      {label}
    </button>
  );
}

function ToggleRow({
  label,
  description,
  enabled,
  onChange,
}: {
  label: string;
  description: string;
  enabled: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <div className='flex items-center justify-between py-3 border-b border-[#1c2128] last:border-b-0'>
      <div className='min-w-0 pr-4'>
        <span className='text-[13px] font-medium' style={{ color: 'var(--text-primary)' }}>{label}</span>
        <p className='text-[11px] mt-0.5' style={{ color: 'var(--text-muted)' }}>{description}</p>
      </div>
      <button
        type='button'
        onClick={() => onChange(!enabled)}
        className={`relative shrink-0 w-9 h-5 rounded-full transition-colors ${enabled ? 'bg-[#3fb950]' : 'bg-[#30363d]'}`}
      >
        <span className={`absolute top-0.5 w-4 h-4 rounded-full bg-white transition-transform ${enabled ? 'left-[18px]' : 'left-0.5'}`} />
      </button>
    </div>
  );
}

export function SupportSettingsTab() {
  const queryClient = useQueryClient();
  const [saved, setSaved] = useState(false);

  const { data: settings, isLoading, error, refetch } = useQuery({
    queryKey: SUPPORT_QUERY_KEY,
    queryFn: getSupportSettings,
    staleTime: 30_000,
  });

  const saveMutation = useMutation({
    mutationFn: updateSupportSettings,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: SUPPORT_QUERY_KEY });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    },
  });

  const handleUpdate = useCallback((updates: UpdateSupportPayload) => {
    saveMutation.mutate(updates);
  }, [saveMutation]);

  if (isLoading && !settings) {
    return (
      <div className='space-y-4 animate-pulse'>
        <div className='h-6 w-40 rounded' style={{ background: 'var(--bg-elevated)' }} />
        <div className='h-32 rounded-lg' style={{ background: 'var(--bg-elevated)' }} />
      </div>
    );
  }

  if (error || !settings) {
    return (
      <div className='rounded-lg border border-[#f85149]/30 bg-[#f85149]/10 p-4'>
        <div className='flex items-center gap-2 text-[#f85149]'>
          <AlertTriangle className='size-4' />
          <span className='text-[13px] font-medium'>Failed to load support settings</span>
        </div>
        <button onClick={() => refetch()} className='mt-3 text-[12px] font-medium' style={{ color: 'var(--accent-blue)' }}>Retry</button>
      </div>
    );
  }

  const Section = ({
    icon: Icon,
    title,
    description,
    children,
  }: {
    icon: React.FC<{ className?: string }>;
    title: string;
    description: string;
    children: React.ReactNode;
  }) => (
    <div className='rounded-xl border p-4 space-y-3' style={{ background: 'var(--bg-surface)', borderColor: 'var(--border-default)' }}>
      <div className='flex items-center gap-3'>
        <div className='size-8 rounded-lg flex items-center justify-center shrink-0' style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-default)' }}>
          <Icon className='size-4' style={{ color: 'var(--text-tertiary)' }} />
        </div>
        <div>
          <h4 className='text-[13px] font-semibold' style={{ color: 'var(--text-primary)' }}>{title}</h4>
          <p className='text-[11px]' style={{ color: 'var(--text-muted)' }}>{description}</p>
        </div>
      </div>
      {children}
    </div>
  );

  return (
    <div className='space-y-6'>
      <div className='flex items-center justify-between'>
        <div>
          <h3 className='text-[15px] font-semibold' style={{ color: 'var(--text-primary)' }}>Support Settings</h3>
          <p className='text-[12px] mt-0.5' style={{ color: 'var(--text-muted)' }}>Configure support channels, SLAs, escalation, and auto-responses</p>
        </div>
        {saved && (
          <span className='flex items-center gap-1.5 text-[11px] text-[#3fb950]'>
            <CheckCircle2 className='size-3' /> Saved
          </span>
        )}
      </div>

      <Section icon={Headphones} title='Support Channels' description='Enable or disable customer support channels'>
        <div className='flex flex-wrap gap-2'>
          <ChannelToggle label='Email' icon={Mail} enabled={settings.enable_email_support} onChange={(v) => handleUpdate({ enable_email_support: v })} />
          <ChannelToggle label='WhatsApp' icon={MessageCircle} enabled={settings.enable_whatsapp_support} onChange={(v) => handleUpdate({ enable_whatsapp_support: v })} />
          <ChannelToggle label='Chat' icon={MessageCircle} enabled={settings.enable_chat_support} onChange={(v) => handleUpdate({ enable_chat_support: v })} />
          <ChannelToggle label='Phone' icon={Phone} enabled={settings.enable_phone_support} onChange={(v) => handleUpdate({ enable_phone_support: v })} />
        </div>
      </Section>

      <Section icon={Clock} title='SLA & Hours' description='Response time targets and operating hours'>
        <div className='grid grid-cols-2 gap-3'>
          <div>
            <label className='block text-[11px] font-semibold uppercase tracking-wider mb-1.5' style={{ color: 'var(--text-tertiary)' }}>Default SLA (hours)</label>
            <input type='number' value={settings.default_response_sla_hours} onChange={(e) => handleUpdate({ default_response_sla_hours: parseInt(e.target.value) || 24 })} min={1} className='w-full rounded-lg border border-[#30363d] bg-[#0d1117] px-3 py-2 text-[13px] text-[#e6edf3] outline-none focus:border-[#58a6ff] transition-colors font-mono' />
          </div>
          <div>
            <label className='block text-[11px] font-semibold uppercase tracking-wider mb-1.5' style={{ color: 'var(--text-tertiary)' }}>Urgent SLA (hours)</label>
            <input type='number' value={settings.urgent_response_sla_hours} onChange={(e) => handleUpdate({ urgent_response_sla_hours: parseInt(e.target.value) || 4 })} min={1} className='w-full rounded-lg border border-[#30363d] bg-[#0d1117] px-3 py-2 text-[13px] text-[#e6edf3] outline-none focus:border-[#58a6ff] transition-colors font-mono' />
          </div>
          <div>
            <label className='block text-[11px] font-semibold uppercase tracking-wider mb-1.5' style={{ color: 'var(--text-tertiary)' }}>Hours Start</label>
            <input type='time' value={settings.support_hours_start} onChange={(e) => handleUpdate({ support_hours_start: e.target.value })} className='w-full rounded-lg border border-[#30363d] bg-[#0d1117] px-3 py-2 text-[13px] text-[#e6edf3] outline-none focus:border-[#58a6ff] transition-colors font-mono' />
          </div>
          <div>
            <label className='block text-[11px] font-semibold uppercase tracking-wider mb-1.5' style={{ color: 'var(--text-tertiary)' }}>Hours End</label>
            <input type='time' value={settings.support_hours_end} onChange={(e) => handleUpdate({ support_hours_end: e.target.value })} className='w-full rounded-lg border border-[#30363d] bg-[#0d1117] px-3 py-2 text-[13px] text-[#e6edf3] outline-none focus:border-[#58a6ff] transition-colors font-mono' />
          </div>
        </div>
        <div>
          <label className='block text-[11px] font-semibold uppercase tracking-wider mb-1.5' style={{ color: 'var(--text-tertiary)' }}>Support Days</label>
          <div className='flex gap-1.5'>
            {DAY_OPTIONS.map((day) => {
              const active = settings.support_days.includes(day);
              return (
                <button key={day} type='button' onClick={() => {
                  const next = active ? settings.support_days.filter((d) => d !== day) : [...settings.support_days, day];
                  handleUpdate({ support_days: next });
                }} className={`rounded-lg border px-2.5 py-1.5 text-[11px] font-medium transition-colors ${active ? 'border-[#58a6ff]/30 bg-[#58a6ff]/10 text-[#58a6ff]' : 'border-[#30363d] bg-[#161b22] text-[#8b949e]'}`}>
                  {DAY_LABELS[day]}
                </button>
              );
            })}
          </div>
        </div>
        <div>
          <label className='block text-[11px] font-semibold uppercase tracking-wider mb-1.5' style={{ color: 'var(--text-tertiary)' }}>Timezone</label>
          <select value={settings.timezone} onChange={(e) => handleUpdate({ timezone: e.target.value })} className='w-full rounded-lg border border-[#30363d] bg-[#0d1117] px-3 py-2 text-[13px] text-[#e6edf3] outline-none focus:border-[#58a6ff] transition-colors'>
            {TIMEZONE_OPTIONS.map((tz) => <option key={tz} value={tz}>{tz}</option>)}
          </select>
        </div>
      </Section>

      <Section icon={Send} title='Auto-Responses' description='Automatic acknowledgements and out-of-hours messages'>
        <ToggleRow label='Auto-Acknowledgement' description='Send automatic acknowledgement when customer reaches out' enabled={settings.enable_auto_acknowledgement} onChange={(v) => handleUpdate({ enable_auto_acknowledgement: v })} />
        {settings.enable_auto_acknowledgement && (
          <div>
            <label className='block text-[11px] font-semibold uppercase tracking-wider mb-1.5' style={{ color: 'var(--text-tertiary)' }}>Acknowledgement Message</label>
            <textarea value={settings.auto_acknowledgement_message} onChange={(e) => handleUpdate({ auto_acknowledgement_message: e.target.value })} rows={2} className='w-full rounded-lg border border-[#30363d] bg-[#0d1117] px-3 py-2 text-[13px] text-[#e6edf3] outline-none focus:border-[#58a6ff] transition-colors resize-none' />
          </div>
        )}
        <div>
          <label className='block text-[11px] font-semibold uppercase tracking-wider mb-1.5' style={{ color: 'var(--text-tertiary)' }}>Out of Hours Message</label>
          <textarea value={settings.out_of_hours_message} onChange={(e) => handleUpdate({ out_of_hours_message: e.target.value })} rows={2} className='w-full rounded-lg border border-[#30363d] bg-[#0d1117] px-3 py-2 text-[13px] text-[#e6edf3] outline-none focus:border-[#58a6ff] transition-colors resize-none' />
        </div>
      </Section>

      <Section icon={AlertTriangle} title='Escalation' description='Automatic escalation when SLAs are breached'>
        <ToggleRow label='Escalate on SLA Breach' description='Automatically escalate to owner when response SLA is breached' enabled={settings.escalation_after_sla_breach} onChange={(v) => handleUpdate({ escalation_after_sla_breach: v })} />
        {settings.escalation_after_sla_breach && (
          <div className='grid grid-cols-2 gap-3'>
            <div>
              <label className='block text-[11px] font-semibold uppercase tracking-wider mb-1.5' style={{ color: 'var(--text-tertiary)' }}>Escalation Email</label>
              <input type='email' value={settings.escalation_contact_email} onChange={(e) => handleUpdate({ escalation_contact_email: e.target.value })} placeholder='owner@agency.com' className='w-full rounded-lg border border-[#30363d] bg-[#0d1117] px-3 py-2 text-[13px] text-[#e6edf3] placeholder-[#484f58] outline-none focus:border-[#58a6ff] transition-colors font-mono' />
            </div>
            <div>
              <label className='block text-[11px] font-semibold uppercase tracking-wider mb-1.5' style={{ color: 'var(--text-tertiary)' }}>Escalation Phone</label>
              <input type='tel' value={settings.escalation_contact_phone} onChange={(e) => handleUpdate({ escalation_contact_phone: e.target.value })} placeholder='+91 98765 43210' className='w-full rounded-lg border border-[#30363d] bg-[#0d1117] px-3 py-2 text-[13px] text-[#e6edf3] placeholder-[#484f58] outline-none focus:border-[#58a6ff] transition-colors font-mono' />
            </div>
          </div>
        )}
      </Section>

      <Section icon={CheckCircle2} title='Satisfaction Tracking' description='Collect customer satisfaction feedback'>
        <ToggleRow label='CSAT Survey' description='Send satisfaction survey after support interaction' enabled={settings.enable_csat_survey} onChange={(v) => handleUpdate({ enable_csat_survey: v })} />
        {settings.enable_csat_survey && (
          <div>
            <label className='block text-[11px] font-semibold uppercase tracking-wider mb-1.5' style={{ color: 'var(--text-tertiary)' }}>Trigger</label>
            <select value={settings.csat_trigger} onChange={(e) => handleUpdate({ csat_trigger: e.target.value as SupportSettings['csat_trigger'] })} className='w-full rounded-lg border border-[#30363d] bg-[#0d1117] px-3 py-2 text-[13px] text-[#e6edf3] outline-none focus:border-[#58a6ff] transition-colors'>
              {CSAT_OPTIONS.map((opt) => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
            </select>
          </div>
        )}
      </Section>
    </div>
  );
}
