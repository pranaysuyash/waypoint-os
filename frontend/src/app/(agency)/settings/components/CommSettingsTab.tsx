'use client';

import type React from 'react';
import { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  CheckCircle2,
  Clock,
  Globe,
  Mail,
  MessageCircle,
  Send,
  AlertTriangle,
  RefreshCw,
  Bell,
} from 'lucide-react';
import {
  getCommSettings,
  updateCommSettings,
  type CommSettings,
  type UpdateCommPayload,
} from '@/lib/api-client';

const COMM_QUERY_KEY = ['settings', 'comm'] as const;

const CHANNEL_OPTIONS = [
  { value: 'email', label: 'Email' },
  { value: 'whatsapp', label: 'WhatsApp' },
  { value: 'sms', label: 'SMS' },
] as const;

const DIGEST_OPTIONS = [
  { value: 'realtime', label: 'Real-time' },
  { value: 'hourly', label: 'Hourly Digest' },
  { value: 'daily', label: 'Daily Digest' },
  { value: 'never', label: 'Never' },
] as const;

const LANGUAGE_OPTIONS = [
  { value: 'en', label: 'English' },
  { value: 'hi', label: 'Hindi' },
  { value: 'es', label: 'Spanish' },
  { value: 'fr', label: 'French' },
  { value: 'de', label: 'German' },
  { value: 'ja', label: 'Japanese' },
  { value: 'ar', label: 'Arabic' },
  { value: 'pt', label: 'Portuguese' },
  { value: 'zh', label: 'Chinese' },
];

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

function Section({
  icon: Icon,
  title,
  description,
  children,
}: {
  icon: React.ComponentType<{ className?: string; style?: React.CSSProperties }>;
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
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
}

export function CommSettingsTab() {
  const queryClient = useQueryClient();
  const [saved, setSaved] = useState(false);

  const { data: settings, isLoading, error, refetch } = useQuery({
    queryKey: COMM_QUERY_KEY,
    queryFn: getCommSettings,
    staleTime: 30_000,
  });

  const saveMutation = useMutation({
    mutationFn: updateCommSettings,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: COMM_QUERY_KEY });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    },
  });

  const handleUpdate = useCallback((updates: UpdateCommPayload) => {
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

  const effectiveSettings = settings || {
    agency_id: 'default',
    default_outbound_channel: 'email' as const,
    allow_channel_switching: true,
    enable_template_library: true,
    default_greeting: 'Dear {customer_name},',
    default_sign_off: 'Best regards,\n{agent_name}',
    respect_operating_hours: false,
    send_immediately_during_hours: true,
    queue_outside_hours: true,
    max_emails_per_day_per_trip: 5,
    max_whatsapp_per_day_per_trip: 3,
    auto_detect_language: true,
    default_language: 'en',
    supported_languages: ['en', 'hi', 'es', 'fr', 'de', 'ja'],
    translate_outbound: false,
    enable_auto_followup: true,
    auto_followup_delay_days: 2,
    max_auto_followups: 3,
    followup_escalate_after_max: true,
    notify_on_customer_reply: true,
    notify_on_sla_warning: true,
    notify_on_escalation: true,
    digest_frequency: 'realtime' as const,
    include_agency_signature: true,
    include_unsubscribe_link: true,
    compliance_footer: 'You are receiving this communication from your travel advisor.',
  };

  return (
    <div className='space-y-6'>
      <div className='flex items-center justify-between'>
        <div>
          <h3 className='text-[15px] font-semibold' style={{ color: 'var(--text-primary)' }}>Communication Settings</h3>
          <p className='text-[12px] mt-0.5' style={{ color: 'var(--text-muted)' }}>Outbound messaging, templates, scheduling, and language preferences</p>
        </div>
        {saved && (
          <span className='flex items-center gap-1.5 text-[11px] text-[#3fb950]'>
            <CheckCircle2 className='size-3' /> Saved
          </span>
        )}
      </div>

      <Section icon={Send} title='Outbound Channels' description='Default channel and switching rules'>
        <div>
          <label className='block text-[11px] font-semibold uppercase tracking-wider mb-1.5' style={{ color: 'var(--text-tertiary)' }}>Default Channel</label>
          <div className='flex gap-2'>
            {CHANNEL_OPTIONS.map((opt) => (
              <button key={opt.value} type='button' onClick={() => handleUpdate({ default_outbound_channel: opt.value })}
                className={`rounded-lg border px-3 py-2 text-[12px] font-medium transition-colors ${effectiveSettings.default_outbound_channel === opt.value ? 'border-[#58a6ff]/30 bg-[#58a6ff]/10 text-[#58a6ff]' : 'border-[#30363d] bg-[#161b22] text-[#8b949e]'}`}>
                {opt.label}
              </button>
            ))}
          </div>
        </div>
        <ToggleRow label='Allow Channel Switching' description='Let agents switch channels during a conversation' enabled={effectiveSettings.allow_channel_switching} onChange={(v) => handleUpdate({ allow_channel_switching: v })} />
      </Section>

      <Section icon={Mail} title='Templates & Branding' description='Default greetings, sign-offs, and compliance'>
        <div className='space-y-3'>
          <div>
            <label className='block text-[11px] font-semibold uppercase tracking-wider mb-1.5' style={{ color: 'var(--text-tertiary)' }}>Default Greeting</label>
            <input type='text' value={effectiveSettings.default_greeting} onChange={(e) => handleUpdate({ default_greeting: e.target.value })} className='w-full rounded-lg border border-[#30363d] bg-[#0d1117] px-3 py-2 text-[13px] text-[#e6edf3] outline-none focus:border-[#58a6ff] transition-colors' />
          </div>
          <div>
            <label className='block text-[11px] font-semibold uppercase tracking-wider mb-1.5' style={{ color: 'var(--text-tertiary)' }}>Default Sign-off</label>
            <textarea value={effectiveSettings.default_sign_off} onChange={(e) => handleUpdate({ default_sign_off: e.target.value })} rows={3} className='w-full rounded-lg border border-[#30363d] bg-[#0d1117] px-3 py-2 text-[13px] text-[#e6edf3] outline-none focus:border-[#58a6ff] transition-colors resize-none font-mono' />
          </div>
          <div>
            <label className='block text-[11px] font-semibold uppercase tracking-wider mb-1.5' style={{ color: 'var(--text-tertiary)' }}>Compliance Footer (optional)</label>
            <input type='text' value={effectiveSettings.compliance_footer} onChange={(e) => handleUpdate({ compliance_footer: e.target.value })} placeholder='e.g. Registered with DOT Tourism...' className='w-full rounded-lg border border-[#30363d] bg-[#0d1117] px-3 py-2 text-[13px] text-[#e6edf3] placeholder-[#484f58] outline-none focus:border-[#58a6ff] transition-colors' />
          </div>
          <ToggleRow label='Include Agency Signature' description='Append agency signature to outbound messages' enabled={effectiveSettings.include_agency_signature} onChange={(v) => handleUpdate({ include_agency_signature: v })} />
          <ToggleRow label='Include Unsubscribe Link' description='Add unsubscribe link to marketing emails' enabled={effectiveSettings.include_unsubscribe_link} onChange={(v) => handleUpdate({ include_unsubscribe_link: v })} />
        </div>
      </Section>

      <Section icon={Clock} title='Scheduling & Rate Limits' description='Operating hours, send timing, and per-trip rate limits'>
        <ToggleRow label='Respect Operating Hours' description='Only send outbound messages during configured hours' enabled={effectiveSettings.respect_operating_hours} onChange={(v) => handleUpdate({ respect_operating_hours: v })} />
        {effectiveSettings.respect_operating_hours && (
          <>
            <ToggleRow label='Send Immediately During Hours' description='Send outbound messages immediately when within hours' enabled={effectiveSettings.send_immediately_during_hours} onChange={(v) => handleUpdate({ send_immediately_during_hours: v })} />
            <ToggleRow label='Queue Outside Hours' description='Queue messages sent outside hours for next business day' enabled={effectiveSettings.queue_outside_hours} onChange={(v) => handleUpdate({ queue_outside_hours: v })} />
          </>
        )}
        <div className='grid grid-cols-2 gap-3'>
          <div>
            <label className='block text-[11px] font-semibold uppercase tracking-wider mb-1.5' style={{ color: 'var(--text-tertiary)' }}>Max Emails / Day / Trip</label>
            <input type='number' value={effectiveSettings.max_emails_per_day_per_trip} onChange={(e) => handleUpdate({ max_emails_per_day_per_trip: parseInt(e.target.value) || 0 })} min={0} className='w-full rounded-lg border border-[#30363d] bg-[#0d1117] px-3 py-2 text-[13px] text-[#e6edf3] outline-none focus:border-[#58a6ff] transition-colors font-mono' />
          </div>
          <div>
            <label className='block text-[11px] font-semibold uppercase tracking-wider mb-1.5' style={{ color: 'var(--text-tertiary)' }}>Max WhatsApp / Day / Trip</label>
            <input type='number' value={effectiveSettings.max_whatsapp_per_day_per_trip} onChange={(e) => handleUpdate({ max_whatsapp_per_day_per_trip: parseInt(e.target.value) || 0 })} min={0} className='w-full rounded-lg border border-[#30363d] bg-[#0d1117] px-3 py-2 text-[13px] text-[#e6edf3] outline-none focus:border-[#58a6ff] transition-colors font-mono' />
          </div>
        </div>
      </Section>

      <Section icon={Globe} title='Language' description='Multi-language support and translation'>
        <ToggleRow label='Auto-detect Language' description='Automatically detect customer language and respond accordingly' enabled={effectiveSettings.auto_detect_language} onChange={(v) => handleUpdate({ auto_detect_language: v })} />
        <div className='grid grid-cols-2 gap-3'>
          <div>
            <label className='block text-[11px] font-semibold uppercase tracking-wider mb-1.5' style={{ color: 'var(--text-tertiary)' }}>Default Language</label>
            <select value={effectiveSettings.default_language} onChange={(e) => handleUpdate({ default_language: e.target.value })} className='w-full rounded-lg border border-[#30363d] bg-[#0d1117] px-3 py-2 text-[13px] text-[#e6edf3] outline-none focus:border-[#58a6ff] transition-colors'>
              {LANGUAGE_OPTIONS.map((opt) => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
            </select>
          </div>
          <ToggleRow label='Translate Outbound' description='Auto-translate outbound messages to customer language' enabled={effectiveSettings.translate_outbound} onChange={(v) => handleUpdate({ translate_outbound: v })} />
        </div>
        <div>
          <label className='block text-[11px] font-semibold uppercase tracking-wider mb-1.5' style={{ color: 'var(--text-tertiary)' }}>Supported Languages</label>
          <div className='flex flex-wrap gap-1.5'>
            {LANGUAGE_OPTIONS.map((opt) => {
              const active = effectiveSettings.supported_languages.includes(opt.value);
              return (
                <button key={opt.value} type='button' onClick={() => {
                  const next = active ? effectiveSettings.supported_languages.filter((l) => l !== opt.value) : [...effectiveSettings.supported_languages, opt.value];
                  handleUpdate({ supported_languages: next });
                }} className={`rounded-full border px-2.5 py-1 text-[11px] font-medium transition-colors ${active ? 'border-[#3fb950]/30 bg-[#3fb950]/10 text-[#3fb950]' : 'border-[#30363d] bg-[#161b22] text-[#8b949e]'}`}>
                  {opt.label}
                </button>
              );
            })}
          </div>
        </div>
      </Section>

      <Section icon={MessageCircle} title='Follow-up Automation' description='Automatic follow-up sequences and escalation'>
        <ToggleRow label='Auto Follow-up' description='Send automatic follow-up messages when customer goes silent' enabled={effectiveSettings.enable_auto_followup} onChange={(v) => handleUpdate({ enable_auto_followup: v })} />
        {effectiveSettings.enable_auto_followup && (
          <div className='grid grid-cols-2 gap-3'>
            <div>
              <label className='block text-[11px] font-semibold uppercase tracking-wider mb-1.5' style={{ color: 'var(--text-tertiary)' }}>Delay (days)</label>
              <input type='number' value={effectiveSettings.auto_followup_delay_days} onChange={(e) => handleUpdate({ auto_followup_delay_days: parseInt(e.target.value) || 1 })} min={1} className='w-full rounded-lg border border-[#30363d] bg-[#0d1117] px-3 py-2 text-[13px] text-[#e6edf3] outline-none focus:border-[#58a6ff] transition-colors font-mono' />
            </div>
            <div>
              <label className='block text-[11px] font-semibold uppercase tracking-wider mb-1.5' style={{ color: 'var(--text-tertiary)' }}>Max Follow-ups</label>
              <input type='number' value={effectiveSettings.max_auto_followups} onChange={(e) => handleUpdate({ max_auto_followups: parseInt(e.target.value) || 0 })} min={0} className='w-full rounded-lg border border-[#30363d] bg-[#0d1117] px-3 py-2 text-[13px] text-[#e6edf3] outline-none focus:border-[#58a6ff] transition-colors font-mono' />
            </div>
          </div>
        )}
        <ToggleRow label='Escalate After Max Follow-ups' description='Escalate to owner when max follow-ups are reached' enabled={effectiveSettings.followup_escalate_after_max} onChange={(v) => handleUpdate({ followup_escalate_after_max: v })} />
      </Section>

      <Section icon={Bell} title='Notifications' description='When and how to notify agents'>
        <ToggleRow label='Notify on Customer Reply' description='Alert agent when customer replies' enabled={effectiveSettings.notify_on_customer_reply} onChange={(v) => handleUpdate({ notify_on_customer_reply: v })} />
        <ToggleRow label='Notify on SLA Warning' description='Alert when response time approaches SLA limit' enabled={effectiveSettings.notify_on_sla_warning} onChange={(v) => handleUpdate({ notify_on_sla_warning: v })} />
        <ToggleRow label='Notify on Escalation' description='Alert owner on escalated tickets' enabled={effectiveSettings.notify_on_escalation} onChange={(v) => handleUpdate({ notify_on_escalation: v })} />
        <div>
          <label className='block text-[11px] font-semibold uppercase tracking-wider mb-1.5' style={{ color: 'var(--text-tertiary)' }}>Digest Frequency</label>
          <div className='flex gap-2'>
            {DIGEST_OPTIONS.map((opt) => (
              <button key={opt.value} type='button' onClick={() => handleUpdate({ digest_frequency: opt.value })}
                className={`rounded-lg border px-3 py-2 text-[11px] font-medium transition-colors ${effectiveSettings.digest_frequency === opt.value ? 'border-[#58a6ff]/30 bg-[#58a6ff]/10 text-[#58a6ff]' : 'border-[#30363d] bg-[#161b22] text-[#8b949e]'}`}>
                {opt.label}
              </button>
            ))}
          </div>
        </div>
      </Section>
    </div>
  );
}
