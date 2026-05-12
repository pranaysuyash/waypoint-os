'use client';

import { useState, useCallback, useMemo, Suspense } from 'react';
import { useSearchParams, useRouter, usePathname } from 'next/navigation';
import {
  Building2,
  SlidersHorizontal,
  ShieldCheck,
  Users,
  Save,
  RotateCcw,
  AlertCircle,
  CheckCircle2,
} from 'lucide-react';
import { useAgencySettings, useUpdateOperationalSettings, useUpdateAutonomyPolicy } from '@/hooks/useAgencySettings';
import type { AgencySettings, UpdateOperationalPayload, UpdateAutonomyPayload } from '@/hooks/useAgencySettings';
import { ProfileTab } from './components/ProfileTab';
import { OperationalTab } from './components/OperationalTab';
import { AutonomyTab } from './components/AutonomyTab';
import { PeopleTab } from './components/PeopleTab';

const TABS = [
  { id: 'profile', label: 'Profile', icon: Building2 },
  { id: 'operations', label: 'Operations', icon: SlidersHorizontal },
  { id: 'autonomy', label: 'Approval Rules', icon: ShieldCheck },
  { id: 'people', label: 'People', icon: Users },
] as const;

type TabId = (typeof TABS)[number]['id'];

function isValidTab(tab: string | null): tab is TabId {
  return TABS.some((t) => t.id === tab);
}

function cloneSettings(settings: AgencySettings): AgencySettings {
  return JSON.parse(JSON.stringify(settings)) as AgencySettings;
}

function SettingsPageInner() {
  const searchParams = useSearchParams();
  const { push } = useRouter();
  const pathname = usePathname();

  const getSearchParam = searchParams.get.bind(searchParams);
  const rawTab = getSearchParam('tab');
  const activeTabResult = rawTab;
  const activeTab: TabId = isValidTab(activeTabResult) ? activeTabResult : 'profile';

  const { data: settings, isLoading, error, refetch } = useAgencySettings();
  const { mutate: updateOperational, isSaving: isSavingOperational, error: opError } = useUpdateOperationalSettings();
  const { mutate: updateAutonomy, isSaving: isSavingAutonomy, error: autonomyError } = useUpdateAutonomyPolicy();

  const [draft, setDraft] = useState<AgencySettings | null>(null);
  const [isDirty, setIsDirty] = useState(false);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');
  const baseDraft = useMemo(() => (settings ? cloneSettings(settings) : null), [settings]);
  const activeDraft = draft ?? baseDraft;

  const handleTabChange = useCallback(
    (tabId: TabId) => {
      const params = new URLSearchParams(searchParams.toString());
      params.set('tab', tabId);
      push(`${pathname}?${params.toString()}`);
    },
    [searchParams, push, pathname]
  );

  const updateDraft = useCallback(
    (updater: (prev: AgencySettings) => AgencySettings) => {
      setDraft((prev) => {
        const source = prev ?? baseDraft;
        if (!source) return prev;
        const next = updater(cloneSettings(source));
        setIsDirty(true);
        setSaveStatus('idle');
        return next;
      });
    },
    [baseDraft]
  );

  const handleSave = useCallback(async () => {
    if (!activeDraft || !settings) return;
    setSaveStatus('saving');

    const promises: Promise<unknown>[] = [];

    // Detect profile/operational changes
    const opPayload: UpdateOperationalPayload = {};
    if (activeDraft.profile.agency_name !== settings.profile.agency_name) opPayload.agency_name = activeDraft.profile.agency_name;
    if (activeDraft.profile.sub_brand !== settings.profile.sub_brand) opPayload.sub_brand = activeDraft.profile.sub_brand;
    if (activeDraft.profile.plan_label !== settings.profile.plan_label) opPayload.plan_label = activeDraft.profile.plan_label;
    if (activeDraft.profile.contact_email !== settings.profile.contact_email) opPayload.contact_email = activeDraft.profile.contact_email;
    if (activeDraft.profile.contact_phone !== settings.profile.contact_phone) opPayload.contact_phone = activeDraft.profile.contact_phone;
    if (activeDraft.profile.logo_url !== settings.profile.logo_url) opPayload.logo_url = activeDraft.profile.logo_url;
    if (activeDraft.profile.website !== settings.profile.website) opPayload.website = activeDraft.profile.website;
    if (activeDraft.operational.target_margin_pct !== settings.operational.target_margin_pct) opPayload.target_margin_pct = activeDraft.operational.target_margin_pct;
    if (activeDraft.operational.default_currency !== settings.operational.default_currency) opPayload.default_currency = activeDraft.operational.default_currency;
    if (activeDraft.operational.operating_hours.start !== settings.operational.operating_hours.start) opPayload.operating_hours_start = activeDraft.operational.operating_hours.start;
    if (activeDraft.operational.operating_hours.end !== settings.operational.operating_hours.end) opPayload.operating_hours_end = activeDraft.operational.operating_hours.end;
    if (JSON.stringify(activeDraft.operational.operating_days) !== JSON.stringify(settings.operational.operating_days)) opPayload.operating_days = activeDraft.operational.operating_days;
    if (JSON.stringify(activeDraft.operational.preferred_channels) !== JSON.stringify(settings.operational.preferred_channels)) opPayload.preferred_channels = activeDraft.operational.preferred_channels;
    if (activeDraft.operational.brand_tone !== settings.operational.brand_tone) opPayload.brand_tone = activeDraft.operational.brand_tone;

    if (Object.keys(opPayload).length > 0) {
      promises.push(updateOperational(opPayload));
    }

    // Detect autonomy changes
    const autonomyPayload: UpdateAutonomyPayload = {};
    if (JSON.stringify(activeDraft.autonomy.approval_gates) !== JSON.stringify(settings.autonomy.approval_gates)) {
      autonomyPayload.approval_gates = activeDraft.autonomy.approval_gates;
    }
    if (JSON.stringify(activeDraft.autonomy.mode_overrides) !== JSON.stringify(settings.autonomy.mode_overrides)) {
      autonomyPayload.mode_overrides = activeDraft.autonomy.mode_overrides;
    }
    if (activeDraft.autonomy.auto_proceed_with_warnings !== settings.autonomy.auto_proceed_with_warnings) {
      autonomyPayload.auto_proceed_with_warnings = activeDraft.autonomy.auto_proceed_with_warnings;
    }
    if (activeDraft.autonomy.learn_from_overrides !== settings.autonomy.learn_from_overrides) {
      autonomyPayload.learn_from_overrides = activeDraft.autonomy.learn_from_overrides;
    }
    if (activeDraft.autonomy.auto_reprocess_on_edit !== settings.autonomy.auto_reprocess_on_edit) {
      autonomyPayload.auto_reprocess_on_edit = activeDraft.autonomy.auto_reprocess_on_edit;
    }
    if (activeDraft.autonomy.allow_explicit_reassess !== settings.autonomy.allow_explicit_reassess) {
      autonomyPayload.allow_explicit_reassess = activeDraft.autonomy.allow_explicit_reassess;
    }
    if (JSON.stringify(activeDraft.autonomy.auto_reprocess_stages) !== JSON.stringify(settings.autonomy.auto_reprocess_stages)) {
      autonomyPayload.auto_reprocess_stages = activeDraft.autonomy.auto_reprocess_stages;
    }

    if (Object.keys(autonomyPayload).length > 0) {
      promises.push(updateAutonomy(autonomyPayload));
    }

    const results = await Promise.all(promises);
    const hasError = results.some((r) => r === null);

    if (hasError) {
      setSaveStatus('error');
    } else {
      setSaveStatus('saved');
      setIsDirty(false);
      refetch();
      setTimeout(() => setSaveStatus('idle'), 3000);
    }
  }, [activeDraft, settings, updateOperational, updateAutonomy, refetch]);

  const handleReset = useCallback(() => {
    if (settings) {
      setDraft(cloneSettings(settings));
      setIsDirty(false);
      setSaveStatus('idle');
    }
  }, [settings]);

  if (isLoading && !activeDraft) {
    return (
      <div className="p-6 flex items-center justify-center">
        <div className="text-[#8b949e] text-ui-sm animate-pulse">Loading settings…</div>
      </div>
    );
  }

  if (error || !activeDraft) {
    return (
      <div className="p-6">
        <div className="max-w-[900px] mx-auto rounded-xl border border-[#f85149]/30 bg-[#f85149]/10 p-6">
          <div className="flex items-center gap-2 text-[#f85149]">
            <AlertCircle className="size-5" />
            <h2 className="font-semibold">Failed to load settings</h2>
          </div>
          <p className="text-ui-sm text-[#e6edf3] mt-2">{error?.message}</p>
          <button
            onClick={refetch}
            className="mt-4 px-4 py-2 rounded-lg border border-[#30363d] text-ui-sm text-[#e6edf3] hover:bg-[#161b22] transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-full bg-[#080a0c] text-[#e6edf3]">
      <div className="max-w-[1100px] mx-auto px-4 sm:px-6 py-6 space-y-6">
        {/* Header */}
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-ui-xl font-semibold">Agency Settings</h1>
            <p className="text-ui-sm text-[#8b949e] mt-1">
              Configure how Waypoint operates for your agency
            </p>
          </div>
          <div className="flex items-center gap-2">
            {saveStatus === 'saved' && (
              <span className="flex items-center gap-1.5 text-ui-xs text-[#3fb950]">
                <CheckCircle2 className="size-3.5" />
                Saved
              </span>
            )}
            {saveStatus === 'error' && (
              <span className="flex items-center gap-1.5 text-ui-xs text-[#f85149]">
                <AlertCircle className="size-3.5" />
                Save failed
              </span>
            )}
            <button
              onClick={handleReset}
              disabled={!isDirty || saveStatus === 'saving'}
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-[#30363d] text-ui-sm text-[#8b949e] hover:text-[#e6edf3] hover:bg-[#161b22] transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <RotateCcw className="size-3.5" />
              Reset
            </button>
            <button
              onClick={handleSave}
              disabled={!isDirty || saveStatus === 'saving'}
              className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-[#58a6ff] text-[#0d1117] text-ui-sm font-medium hover:bg-[#79b8ff] transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <Save className="size-3.5" />
              {saveStatus === 'saving' ? 'Saving…' : 'Save Changes'}
            </button>
          </div>
        </div>

        {/* Error summary */}
        {(opError || autonomyError) && (
          <div className="rounded-lg border border-[#f85149]/30 bg-[#f85149]/10 p-3 flex items-center gap-2 text-ui-sm text-[#f85149]">
            <AlertCircle className="size-4 shrink-0" />
            {opError?.message || autonomyError?.message}
          </div>
        )}

        {/* Tabs */}
        <div className="border-b border-[#1c2128]">
          <div className="flex gap-1">
            {TABS.map((tab) => {
              const Icon = tab.icon;
              const isActive = tab.id === activeTab;
              return (
                <button
                  key={tab.id}
                  onClick={() => handleTabChange(tab.id)}
                  className={`flex items-center gap-2 px-4 py-2.5 text-ui-sm font-medium transition-colors border-b-2 -mb-px ${
                    isActive
                      ? 'border-[#58a6ff] text-[#58a6ff]'
                      : 'border-transparent text-[#8b949e] hover:text-[#c9d1d9]'
                  }`}
                >
                  <Icon className="size-4" />
                  {tab.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* Tab Content */}
        <div className="rounded-xl border border-[#1c2128] bg-[#0f1115] p-6">
          {activeTab === 'profile' && (
            <ProfileTab draft={activeDraft} onChange={updateDraft} />
          )}
          {activeTab === 'operations' && (
            <OperationalTab draft={activeDraft} onChange={updateDraft} />
          )}
          {activeTab === 'autonomy' && (
            <AutonomyTab draft={activeDraft} onChange={updateDraft} />
          )}
          {activeTab === 'people' && (
            <PeopleTab />
          )}
        </div>
      </div>
    </div>
  );
}

export default function SettingsPage() {
  return (
    <Suspense fallback={<div className="p-6 text-[#8b949e] animate-pulse">Loading settings…</div>}>
      <SettingsPageInner />
    </Suspense>
  );
}
