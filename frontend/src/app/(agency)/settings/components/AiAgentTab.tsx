'use client';

import { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Bot,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Cpu,
  MessageSquare,
  ShieldCheck,
  Sparkles,
  AlertTriangle,
  RefreshCw,
} from 'lucide-react';
import {
  getAiAgentSettings,
  updateAiAgentSettings,
  type AiAgentSettings,
  type UpdateAiAgentPayload,
} from '@/lib/api-client';

const AI_AGENT_QUERY_KEY = ['settings', 'ai-agent'] as const;

const MODEL_OPTIONS = [
  'gemini-2.0-flash',
  'gemini-2.5-pro',
  'gpt-4o',
  'gpt-4o-mini',
  'claude-3.5-sonnet',
  'claude-3-haiku',
];

const BRAND_VOICE_OPTIONS = [
  { value: 'professional', label: 'Professional', desc: 'Formal, authoritative, efficient' },
  { value: 'friendly', label: 'Friendly', desc: 'Warm, conversational, approachable' },
  { value: 'luxury', label: 'Luxury', desc: 'Elegant, refined, premium' },
  { value: 'budget', label: 'Budget', desc: 'Value-focused, practical, straightforward' },
] as const;

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
        <span className='text-[13px] font-medium' style={{ color: 'var(--text-primary)' }}>
          {label}
        </span>
        <p className='text-[11px] mt-0.5' style={{ color: 'var(--text-muted)' }}>
          {description}
        </p>
      </div>
      <button
        type='button'
        onClick={() => onChange(!enabled)}
        className={`relative shrink-0 w-9 h-5 rounded-full transition-colors ${
          enabled ? 'bg-[#3fb950]' : 'bg-[#30363d]'
        }`}
      >
        <span
          className={`absolute top-0.5 w-4 h-4 rounded-full bg-white transition-transform ${
            enabled ? 'left-[18px]' : 'left-0.5'
          }`}
        />
      </button>
    </div>
  );
}

function SelectField({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
}) {
  return (
    <div>
      <label className='block text-[11px] font-semibold uppercase tracking-wider mb-1.5' style={{ color: 'var(--text-tertiary)' }}>
        {label}
      </label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className='w-full rounded-lg border border-[#30363d] bg-[#0d1117] px-3 py-2 text-[13px] text-[#e6edf3] outline-none focus:border-[#58a6ff] transition-colors'
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>{opt.label}</option>
        ))}
      </select>
    </div>
  );
}

function NumberField({
  label,
  value,
  onChange,
  min = 0,
  max = 100,
  step = 1,
  unit,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
  min?: number;
  max?: number;
  step?: number;
  unit?: string;
}) {
  return (
    <div>
      <label className='block text-[11px] font-semibold uppercase tracking-wider mb-1.5' style={{ color: 'var(--text-tertiary)' }}>
        {label}
      </label>
      <div className='flex items-center gap-2'>
        <input
          type='number'
          value={value}
          onChange={(e) => onChange(Math.max(min, Math.min(max, parseFloat(e.target.value) || 0)))}
          min={min}
          max={max}
          step={step}
          className='w-full rounded-lg border border-[#30363d] bg-[#0d1117] px-3 py-2 text-[13px] text-[#e6edf3] outline-none focus:border-[#58a6ff] transition-colors font-mono tabular-nums'
        />
        {unit && <span className='text-[12px] shrink-0' style={{ color: 'var(--text-muted)' }}>{unit}</span>}
      </div>
    </div>
  );
}

export function AiAgentTab() {
  const queryClient = useQueryClient();
  const [saved, setSaved] = useState(false);

  const { data: settings, isLoading, error, refetch } = useQuery({
    queryKey: AI_AGENT_QUERY_KEY,
    queryFn: getAiAgentSettings,
    staleTime: 30_000,
  });

  const saveMutation = useMutation({
    mutationFn: updateAiAgentSettings,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: AI_AGENT_QUERY_KEY });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    },
  });

  const handleUpdate = useCallback(
    (updates: UpdateAiAgentPayload) => {
      saveMutation.mutate(updates);
    },
    [saveMutation],
  );

  if (isLoading && !settings) {
    return (
      <div className='space-y-4 animate-pulse'>
        <div className='h-6 w-40 rounded' style={{ background: 'var(--bg-elevated)' }} />
        <div className='h-32 rounded-lg' style={{ background: 'var(--bg-elevated)' }} />
        <div className='h-48 rounded-lg' style={{ background: 'var(--bg-elevated)' }} />
      </div>
    );
  }

  if (error || !settings) {
    return (
      <div className='rounded-lg border border-[#f85149]/30 bg-[#f85149]/10 p-4'>
        <div className='flex items-center gap-2 text-[#f85149]'>
          <AlertTriangle className='size-4' />
          <span className='text-[13px] font-medium'>Failed to load AI agent settings</span>
        </div>
        <button onClick={() => refetch()} className='mt-3 text-[12px] font-medium' style={{ color: 'var(--accent-blue)' }}>
          Retry
        </button>
      </div>
    );
  }

  const FeatureSection = ({
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
    <div
      className='rounded-xl border p-4 space-y-3'
      style={{ background: 'var(--bg-surface)', borderColor: 'var(--border-default)' }}
    >
      <div className='flex items-center gap-3'>
        <div
          className='size-8 rounded-lg flex items-center justify-center shrink-0'
          style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-default)' }}
        >
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
      {/* Header */}
      <div className='flex items-center justify-between'>
        <div>
          <h3 className='text-[15px] font-semibold' style={{ color: 'var(--text-primary)' }}>
            AI Agent Settings
          </h3>
          <p className='text-[12px] mt-0.5' style={{ color: 'var(--text-muted)' }}>
            Control what the AI agent can do autonomously and how it behaves
          </p>
        </div>
        <div className='flex items-center gap-2'>
          {saved && (
            <span className='flex items-center gap-1.5 text-[11px] text-[#3fb950]'>
              <CheckCircle2 className='size-3' />
              Saved
            </span>
          )}
          <button
            type='button'
            onClick={() => refetch()}
            className='inline-flex items-center gap-1.5 rounded-lg border border-[#30363d] px-2.5 py-1.5 text-[11px] text-[#8b949e] hover:text-[#e6edf3] hover:bg-[#1c2128] transition-colors'
          >
            <RefreshCw className='size-3' />
          </button>
        </div>
      </div>

      {/* Feature Gates */}
      <FeatureSection
        icon={Sparkles}
        title='Feature Gates'
        description='Enable or disable AI agent capabilities'
      >
        <ToggleRow
          label='Auto Intake'
          description='Automatically process and classify incoming customer messages'
          enabled={settings.enable_auto_intake}
          onChange={(v) => handleUpdate({ enable_auto_intake: v })}
        />
        <ToggleRow
          label='Auto Shortlist'
          description='Generate destination and hotel shortlists without manual review'
          enabled={settings.enable_auto_shortlist}
          onChange={(v) => handleUpdate({ enable_auto_shortlist: v })}
        />
        <ToggleRow
          label='Auto Proposal'
          description='Generate travel proposals automatically from shortlisted options'
          enabled={settings.enable_auto_proposal}
          onChange={(v) => handleUpdate({ enable_auto_proposal: v })}
        />
        <ToggleRow
          label='Auto Negotiation'
          description='Automatically negotiate with suppliers for better rates'
          enabled={settings.enable_auto_negotiation}
          onChange={(v) => handleUpdate({ enable_auto_negotiation: v })}
        />
        <ToggleRow
          label='Frontier Orchestration'
          description='Enable advanced multi-agent orchestration for complex trips'
          enabled={settings.enable_frontier_orchestration}
          onChange={(v) => handleUpdate({ enable_frontier_orchestration: v })}
        />
        <ToggleRow
          label='Checker Agent'
          description='Secondary review agent that audits proposals for quality'
          enabled={settings.enable_checker_agent}
          onChange={(v) => handleUpdate({ enable_checker_agent: v })}
        />
        <ToggleRow
          label='Call Capture'
          description='Extract information from recorded sales calls'
          enabled={settings.enable_call_capture}
          onChange={(v) => handleUpdate({ enable_call_capture: v })}
        />
        <ToggleRow
          label='Document Extraction'
          description='AI-powered extraction of data from uploaded documents (passports, etc.)'
          enabled={settings.enable_document_extraction}
          onChange={(v) => handleUpdate({ enable_document_extraction: v })}
        />
      </FeatureSection>

      {/* Model Preferences */}
      <FeatureSection
        icon={Cpu}
        title='Model Preferences'
        description='Choose which AI models power each capability'
      >
        <div className='grid grid-cols-2 gap-3'>
          <SelectField
            label='Preferred Model'
            value={settings.preferred_model}
            onChange={(v) => handleUpdate({ preferred_model: v })}
            options={MODEL_OPTIONS.map((m) => ({ value: m, label: m }))}
          />
          <SelectField
            label='Fallback Model'
            value={settings.fallback_model}
            onChange={(v) => handleUpdate({ fallback_model: v })}
            options={MODEL_OPTIONS.map((m) => ({ value: m, label: m }))}
          />
          <SelectField
            label='Extraction Model'
            value={settings.extraction_model}
            onChange={(v) => handleUpdate({ extraction_model: v })}
            options={MODEL_OPTIONS.map((m) => ({ value: m, label: m }))}
          />
          <SelectField
            label='Checker Model'
            value={settings.checker_model}
            onChange={(v) => handleUpdate({ checker_model: v })}
            options={MODEL_OPTIONS.map((m) => ({ value: m, label: m }))}
          />
        </div>
      </FeatureSection>

      {/* Behavior Tuning */}
      <FeatureSection
        icon={MessageSquare}
        title='Behavior Tuning'
        description='Fine-tune how the agent interacts with customers'
      >
        <div className='grid grid-cols-2 gap-4'>
          <NumberField
            label='Max Negotiation Rounds'
            value={settings.max_negotiation_rounds}
            onChange={(v) => handleUpdate({ max_negotiation_rounds: v })}
            min={1}
            max={10}
          />
          <NumberField
            label='Proposal Confidence Threshold'
            value={settings.proposal_confidence_threshold}
            onChange={(v) => handleUpdate({ proposal_confidence_threshold: v })}
            min={0}
            max={1}
            step={0.05}
          />
          <NumberField
            label='Owner Review Threshold'
            value={settings.require_owner_review_above_value}
            onChange={(v) => handleUpdate({ require_owner_review_above_value: v })}
            min={0}
            max={100000}
            step={500}
            unit='USD'
          />
          <NumberField
            label='Max Follow-up Questions'
            value={settings.max_follow_up_questions}
            onChange={(v) => handleUpdate({ max_follow_up_questions: v })}
            min={0}
            max={10}
          />
        </div>
        <ToggleRow
          label='Auto-advance Stages'
          description='Automatically move trips through pipeline stages when ready'
          enabled={settings.auto_advance_stages}
          onChange={(v) => handleUpdate({ auto_advance_stages: v })}
        />
      </FeatureSection>

      {/* Voice & Language */}
      <FeatureSection
        icon={ShieldCheck}
        title='Voice & Language'
        description='Set the communication style and language'
      >
        <div className='grid grid-cols-2 gap-4'>
          <div>
            <label className='block text-[11px] font-semibold uppercase tracking-wider mb-2' style={{ color: 'var(--text-tertiary)' }}>
              Brand Voice
            </label>
            <div className='space-y-2'>
              {BRAND_VOICE_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  type='button'
                  onClick={() => handleUpdate({ brand_voice: opt.value })}
                  className={`w-full rounded-lg border p-3 text-left transition-colors ${
                    settings.brand_voice === opt.value
                      ? 'border-[#58a6ff]/40 bg-[#58a6ff]/8'
                      : 'border-[#30363d] bg-[#0d1117] hover:bg-[#161b22]'
                  }`}
                >
                  <span
                    className='text-[13px] font-medium block'
                    style={{
                      color: settings.brand_voice === opt.value ? '#58a6ff' : 'var(--text-primary)',
                    }}
                  >
                    {opt.label}
                  </span>
                  <span className='text-[11px]' style={{ color: 'var(--text-muted)' }}>
                    {opt.desc}
                  </span>
                </button>
              ))}
            </div>
          </div>
          <div>
            <SelectField
              label='Response Language'
              value={settings.response_language}
              onChange={(v) => handleUpdate({ response_language: v })}
              options={[
                { value: 'en', label: 'English' },
                { value: 'hi', label: 'Hindi' },
                { value: 'es', label: 'Spanish' },
                { value: 'fr', label: 'French' },
                { value: 'de', label: 'German' },
                { value: 'ja', label: 'Japanese' },
                { value: 'ar', label: 'Arabic' },
              ]}
            />
          </div>
        </div>
      </FeatureSection>
    </div>
  );
}
