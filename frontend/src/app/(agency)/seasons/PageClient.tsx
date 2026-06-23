'use client';

import { useMemo, useState } from 'react';
import {
  CalendarDays,
  Play,
  RefreshCw,
  Save,
  Trash2,
  Pencil,
  CheckCircle2,
  Send,
} from 'lucide-react';
import { BackToOverviewLink } from '@/components/navigation/BackToOverviewLink';
import {
  useSeasonalCampaigns,
  useCreateSeasonalCampaign,
  useUpdateSeasonalCampaign,
  useDeleteSeasonalCampaign,
  useSimulateSeasonalCampaign,
  usePreflightSeasonalCampaign,
  useDispatchSeasonalCampaign,
  type SeasonalCampaign,
  type SimulateSeasonalCampaignResponse,
  type SeasonPreflightResponse,
  type SeasonDispatchResponse,
} from '@/hooks/useSeasonalCampaigns';
import {
  CAMPAIGN_CHANNELS,
  CampaignFormState,
  campaignFormFromPlan,
  makeEmptyCampaignForm,
  parseIntValue,
  parseNumericValue,
  toCreateCampaignPayload,
  toUpdateCampaignPayload,
} from '@/lib/seasonalCampaigns';

const SCENARIO_OPTIONS = ['baseline', 'aggressive', 'conservative'];

type CampaignSummaryRecord<T> = Record<string, T>;
type ActionMessageState = Record<
  string,
  {
    simulate?: string | null;
    preflight?: string | null;
    dispatch_dry_run?: string | null;
    dispatch_live?: string | null;
  }
>;

function isMonthString(value: string): boolean {
  if (!value.trim()) return true;
  const parsed = parseIntValue(value);
  return (
    parsed !== undefined && parsed >= 1 && parsed <= 12
  );
}

function validateCampaignWindow(form: CampaignFormState): string | null {
  const start = parseIntValue(form.campaign_window_start_month);
  const end = parseIntValue(form.campaign_window_end_month);

  if (!isMonthString(form.campaign_window_start_month)) {
    return 'Start month must be an integer from 1 to 12.';
  }
  if (!isMonthString(form.campaign_window_end_month)) {
    return 'End month must be an integer from 1 to 12.';
  }
  if (start !== undefined && end !== undefined && start > end) {
    return 'Campaign start month cannot be after end month.';
  }

  return null;
}

function validateBudgetRange(minRaw: string, maxRaw: string): string | null {
  const min = parseNumericValue(minRaw);
  const max = parseNumericValue(maxRaw);

  if (minRaw.trim() && min === undefined) {
    return 'Minimum budget must be a number or blank.';
  }
  if (maxRaw.trim() && max === undefined) {
    return 'Maximum budget must be a number or blank.';
  }
  if (min !== undefined && max !== undefined && min > max) {
    return 'Minimum budget cannot be greater than maximum budget.';
  }

  return null;
}

function validateCampaignForm(form: CampaignFormState, isCreate: boolean): string | null {
  if (isCreate && !form.name.trim()) {
    return 'Campaign name is required.';
  }

  const windowError = validateCampaignWindow(form);
  if (windowError) {
    return windowError;
  }

  const budgetError = validateBudgetRange(form.target_budget_min, form.target_budget_max);
  if (budgetError) {
    return budgetError;
  }

  return null;
}

function statusClass(status: SeasonalCampaign['status']): string {
  if (status === 'active') return 'bg-[#3fb950]/10 text-[#3fb950] border-[#3fb950]/30';
  if (status === 'paused') return 'bg-[#d29922]/10 text-[#d29922] border-[#d29922]/30';
  if (status === 'archived') return 'bg-[#8b949e]/10 text-[#8b949e] border-[#8b949e]/30';
  return 'bg-[#58a6ff]/10 text-[#58a6ff] border-[#58a6ff]/30';
}

export default function SeasonsPageClient() {
  const { campaigns, total, isLoading, error, refetch } = useSeasonalCampaigns();
  const createCampaign = useCreateSeasonalCampaign();
  const updateCampaign = useUpdateSeasonalCampaign();
  const deleteCampaign = useDeleteSeasonalCampaign();
  const simulateCampaign = useSimulateSeasonalCampaign();
  const preflightCampaign = usePreflightSeasonalCampaign();
  const dispatchCampaign = useDispatchSeasonalCampaign();

  const [newCampaignForm, setNewCampaignForm] = useState<CampaignFormState>(makeEmptyCampaignForm());
  const [editingCampaignId, setEditingCampaignId] = useState<string | null>(null);
  const [editingForm, setEditingForm] = useState<CampaignFormState>(makeEmptyCampaignForm());
  const [formError, setFormError] = useState<string | null>(null);
  const [simulateByCampaignRunning, setSimulateByCampaignRunning] = useState<Record<string, boolean>>({});
  const [preflightByCampaignRunning, setPreflightByCampaignRunning] = useState<Record<string, boolean>>({});
  const [dispatchDryByCampaignRunning, setDispatchDryByCampaignRunning] = useState<Record<string, boolean>>({});
  const [dispatchLiveByCampaignRunning, setDispatchLiveByCampaignRunning] = useState<Record<string, boolean>>({});
  const [actionMessagesByCampaign, setActionMessagesByCampaign] = useState<ActionMessageState>({});
  const [scenarioByCampaign, setScenarioByCampaign] = useState<Record<string, string>>({});
  const [simulationByCampaign, setSimulationByCampaign] = useState<
    CampaignSummaryRecord<SimulateSeasonalCampaignResponse | null>
  >({});
  const [preflightByCampaign, setPreflightByCampaign] = useState<
    CampaignSummaryRecord<SeasonPreflightResponse | null>
  >({});
  const [dispatchByCampaign, setDispatchByCampaign] = useState<
    CampaignSummaryRecord<SeasonDispatchResponse | null>
  >({});

  const sortedCampaigns = useMemo(
    () => [...campaigns].sort((a, b) => (b.updated_at ?? '').localeCompare(a.updated_at ?? '')),
    [campaigns],
  );

  const totalActive = campaigns.filter((campaign) => campaign.status === 'active').length;
  const totalDraft = campaigns.filter((campaign) => campaign.status === 'draft').length;
  const totalPaused = campaigns.filter((campaign) => campaign.status === 'paused').length;

  const mutationErrors = [
    createCampaign.error?.message,
    updateCampaign.error?.message,
    deleteCampaign.error?.message,
    simulateCampaign.error?.message,
    preflightCampaign.error?.message,
    dispatchCampaign.error?.message,
  ].filter(Boolean);

  const startEdit = (campaign: SeasonalCampaign) => {
    setEditingCampaignId(campaign.plan_id);
    setEditingForm(campaignFormFromPlan(campaign));
    setFormError(null);
  };

  const cancelEdit = () => {
    setEditingCampaignId(null);
    setEditingForm(makeEmptyCampaignForm());
    setFormError(null);
  };

  const handleCreate = async () => {
    const validationError = validateCampaignForm(newCampaignForm, true);
    if (validationError) {
      setFormError(validationError);
      return;
    }

    const payload = toCreateCampaignPayload(newCampaignForm);
    if (!payload.name) return;

    setFormError(null);
    const created = await createCampaign.mutate(payload);
    if (created) {
      setNewCampaignForm(makeEmptyCampaignForm());
    }
  };

  const handleSaveCampaign = async () => {
    if (!editingCampaignId) return;
    const validationError = validateCampaignForm(editingForm, false);
    if (validationError) {
      setFormError(validationError);
      return;
    }

    const original = campaigns.find((item) => item.plan_id === editingCampaignId);
    if (!original) return;

    const payload = toUpdateCampaignPayload(editingForm, original);
    if (Object.keys(payload).length === 0) {
      setEditingCampaignId(null);
      setEditingForm(makeEmptyCampaignForm());
      setFormError(null);
      return;
    }

    const next = await updateCampaign.mutate(editingCampaignId, payload);

    if (next) {
      setEditingCampaignId(null);
      setEditingForm(makeEmptyCampaignForm());
      setFormError(null);
    }
  };

  const handleRunSimulation = async (planId: string) => {
    const scenario = scenarioByCampaign[planId] || 'baseline';
    setActionMessagesByCampaign((prev) => ({
      ...prev,
      [planId]: { ...prev[planId], simulate: null },
    }));
    setSimulationByCampaign((prev) => ({
      ...prev,
      [planId]: null,
    }));
    setSimulateByCampaignRunning((prev) => ({ ...prev, [planId]: true }));
    const nextSimulation = await simulateCampaign.mutate(planId, scenario);
    setSimulateByCampaignRunning((prev) => ({ ...prev, [planId]: false }));
    if (nextSimulation) {
      setSimulationByCampaign((prev) => ({ ...prev, [planId]: nextSimulation }));
      setActionMessagesByCampaign((prev) => ({
        ...prev,
        [planId]: { ...prev[planId], simulate: null },
      }));
      return;
    }
    setActionMessagesByCampaign((prev) => ({
      ...prev,
      [planId]: {
        ...prev[planId],
        simulate: simulateCampaign.error?.message || 'Simulation failed to run. Try again.',
      },
    }));
  };

  const handleRunPreflight = async (planId: string) => {
    setActionMessagesByCampaign((prev) => ({
      ...prev,
      [planId]: { ...prev[planId], preflight: null },
    }));
    setPreflightByCampaign((prev) => ({
      ...prev,
      [planId]: null,
    }));
    setPreflightByCampaignRunning((prev) => ({ ...prev, [planId]: true }));
    const nextPreflight = await preflightCampaign.mutate(planId);
    setPreflightByCampaignRunning((prev) => ({ ...prev, [planId]: false }));
    if (nextPreflight) {
      setPreflightByCampaign((prev) => ({ ...prev, [planId]: nextPreflight }));
      setActionMessagesByCampaign((prev) => ({
        ...prev,
        [planId]: { ...prev[planId], preflight: null },
      }));
      return;
    }
    setActionMessagesByCampaign((prev) => ({
      ...prev,
      [planId]: {
        ...prev[planId],
        preflight: preflightCampaign.error?.message || 'Preflight failed to run. Try again.',
      },
    }));
  };

  const handleDispatch = async (planId: string, dryRun: boolean) => {
    const dispatchMode = dryRun ? 'dispatch_dry_run' : 'dispatch_live';
    const scenario = scenarioByCampaign[planId] || 'baseline';
    const runningUpdater = dryRun ? setDispatchDryByCampaignRunning : setDispatchLiveByCampaignRunning;
    setActionMessagesByCampaign((prev) => ({
      ...prev,
      [planId]: { ...prev[planId], [dispatchMode]: null },
    }));
    setDispatchByCampaign((prev) => ({
      ...prev,
      [planId]: null,
    }));
    runningUpdater((prev) => ({ ...prev, [planId]: true }));
    const nextDispatch = await dispatchCampaign.mutate(planId, dryRun, scenario);
    runningUpdater((prev) => ({ ...prev, [planId]: false }));
    if (nextDispatch) {
      setDispatchByCampaign((prev) => ({ ...prev, [planId]: nextDispatch }));
      setActionMessagesByCampaign((prev) => ({
        ...prev,
        [planId]: { ...prev[planId], [dispatchMode]: null },
      }));
      return;
    }
    const dispatchErrorMessage =
      dispatchCampaign.error?.message || `${dryRun ? 'Dry run' : 'Dispatch'} failed to run. Try again.`;
    setActionMessagesByCampaign((prev) => ({
      ...prev,
      [planId]: {
        ...prev[planId],
        [dispatchMode]: dispatchErrorMessage,
      },
    }));
  };

  const handleClearActions = (planId: string) => {
    setSimulationByCampaign((prev) => {
      const next = { ...prev };
      delete next[planId];
      return next;
    });
    setPreflightByCampaign((prev) => {
      const next = { ...prev };
      delete next[planId];
      return next;
    });
    setDispatchByCampaign((prev) => {
      const next = { ...prev };
      delete next[planId];
      return next;
    });
    setActionMessagesByCampaign((prev) => {
      const next = { ...prev };
      delete next[planId];
      return next;
    });
  };

  const handleDelete = async (planId: string) => {
    if (!window.confirm('Delete this campaign?')) return;
    const deleted = await deleteCampaign.mutate(planId);
    if (deleted && editingCampaignId === planId) {
      cancelEdit();
    }
  };

  return (
    <div className="p-5 max-w-[1400px] mx-auto space-y-5">
      <BackToOverviewLink />

      <header className="flex items-center justify-between gap-3 flex-wrap">
        <div>
          <h1 className="text-ui-xl font-semibold text-[#e6edf3]">Seasonal Campaigns</h1>
          <p className="text-ui-sm text-[var(--text-muted)] mt-0.5">
            Plan, simulate, validate, and dispatch seasonal campaign plans.
          </p>
        </div>
        <button
          type="button"
          onClick={() => refetch()}
          className="inline-flex items-center gap-2 rounded-lg px-3 py-2 text-ui-sm border border-[var(--border-default)] text-[var(--text-secondary)] hover:text-[#e6edf3] hover:bg-[#161b22] transition-colors"
        >
          <RefreshCw className={`size-4 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </header>

      {formError ? (
        <div className="rounded-lg border border-[#f85149]/30 bg-[#f85149]/10 p-4 text-ui-sm text-[#f85149]">
          {formError}
        </div>
      ) : null}

      {mutationErrors.length > 0 ? (
        <div className="rounded-lg border border-[#f85149]/30 bg-[#f85149]/10 p-4 text-ui-sm text-[#f85149] space-y-1">
          {mutationErrors.map((message) => (
            <p key={message}>{message}</p>
          ))}
        </div>
      ) : null}

      <section className="grid grid-cols-1 md:grid-cols-4 gap-3">
        <article className="rounded-xl border border-[#1c2128] bg-[#0f1115] p-4">
          <p className="text-ui-xs text-[var(--text-tertiary)]">Total campaigns</p>
          <p className="text-ui-xl font-semibold text-[#e6edf3] mt-1">{total}</p>
        </article>
        <article className="rounded-xl border border-[#1c2128] bg-[#0f1115] p-4">
          <p className="text-ui-xs text-[var(--text-tertiary)]">Active</p>
          <p className="text-ui-xl font-semibold text-[#3fb950] mt-1">{totalActive}</p>
        </article>
        <article className="rounded-xl border border-[#1c2128] bg-[#0f1115] p-4">
          <p className="text-ui-xs text-[var(--text-tertiary)]">Draft</p>
          <p className="text-ui-xl font-semibold text-[#58a6ff] mt-1">{totalDraft}</p>
        </article>
        <article className="rounded-xl border border-[#1c2128] bg-[#0f1115] p-4">
          <p className="text-ui-xs text-[var(--text-tertiary)]">Paused</p>
          <p className="text-ui-xl font-semibold text-[#d29922] mt-1">{totalPaused}</p>
        </article>
      </section>

      {error ? (
        <div className="rounded-lg border border-[#f85149]/30 bg-[#f85149]/10 p-4 text-ui-sm text-[#f85149]">
          Failed to load seasonal campaigns: {error.message}
        </div>
      ) : null}

      <section className="rounded-xl border border-[#1c2128] bg-[#0f1115] p-5 space-y-4">
        <h2 className="text-ui-sm font-semibold text-[#e6edf3]">Build campaign</h2>
        <p className="text-ui-xs text-[#8b949e]">
          Define name, mix, budget range, timing window, and guardrail blocklist in one place.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <label className="text-ui-xs text-[#8b949e]">
            Campaign name
            <input
              value={newCampaignForm.name}
              onChange={(event) =>
                setNewCampaignForm((state) => ({ ...state, name: event.target.value }))
              }
              className="mt-1 w-full rounded-lg border border-[#30363d] bg-[#161b22] px-2 py-2 text-ui-sm"
              placeholder="Monsoon Beach Promotion"
            />
          </label>
          <label className="text-ui-xs text-[#8b949e]">
            Destination
            <input
              value={newCampaignForm.destination}
              onChange={(event) =>
                setNewCampaignForm((state) => ({ ...state, destination: event.target.value }))
              }
              className="mt-1 w-full rounded-lg border border-[#30363d] bg-[#161b22] px-2 py-2 text-ui-sm"
              placeholder="Goa / Dubai / Tokyo"
            />
          </label>
          <label className="text-ui-xs text-[#8b949e]">
            Status
            <select
              value={newCampaignForm.status}
              onChange={(event) =>
                setNewCampaignForm((state) => ({
                  ...state,
                  status: event.target.value as SeasonalCampaign['status'],
                }))
              }
              className="mt-1 w-full rounded-lg border border-[#30363d] bg-[#161b22] px-2 py-2 text-ui-sm text-[#e6edf3]"
            >
              <option value="draft">Draft</option>
              <option value="active">Active</option>
              <option value="paused">Paused</option>
              <option value="archived">Archived</option>
            </select>
          </label>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <label className="text-ui-xs text-[#8b949e]">
            Start month (1-12)
            <input
              type="number"
              min={1}
              max={12}
              value={newCampaignForm.campaign_window_start_month}
              onChange={(event) =>
                setNewCampaignForm((state) => ({
                  ...state,
                  campaign_window_start_month: event.target.value,
                }))
              }
              className="mt-1 w-full rounded-lg border border-[#30363d] bg-[#161b22] px-2 py-2 text-ui-sm"
            />
          </label>
          <label className="text-ui-xs text-[#8b949e]">
            End month (1-12)
            <input
              type="number"
              min={1}
              max={12}
              value={newCampaignForm.campaign_window_end_month}
              onChange={(event) =>
                setNewCampaignForm((state) => ({
                  ...state,
                  campaign_window_end_month: event.target.value,
                }))
              }
              className="mt-1 w-full rounded-lg border border-[#30363d] bg-[#161b22] px-2 py-2 text-ui-sm"
            />
          </label>
          <label className="text-ui-xs text-[#8b949e]">
            Min budget
            <input
              type="number"
              value={newCampaignForm.target_budget_min}
              onChange={(event) =>
                setNewCampaignForm((state) => ({
                  ...state,
                  target_budget_min: event.target.value,
                }))
              }
              className="mt-1 w-full rounded-lg border border-[#30363d] bg-[#161b22] px-2 py-2 text-ui-sm"
            />
          </label>
          <label className="text-ui-xs text-[#8b949e]">
            Max budget
            <input
              type="number"
              value={newCampaignForm.target_budget_max}
              onChange={(event) =>
                setNewCampaignForm((state) => ({
                  ...state,
                  target_budget_max: event.target.value,
                }))
              }
              className="mt-1 w-full rounded-lg border border-[#30363d] bg-[#161b22] px-2 py-2 text-ui-sm"
            />
          </label>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {CAMPAIGN_CHANNELS.map((channel) => (
            <label key={channel} className="text-ui-xs text-[#8b949e]">
              {channel} mix weight
              <input
                type="number"
                step={0.05}
                value={newCampaignForm.channel_mix[channel]}
                onChange={(event) =>
                  setNewCampaignForm((state) => ({
                    ...state,
                    channel_mix: {
                      ...state.channel_mix,
                      [channel]: event.target.value,
                    },
                  }))
                }
                className="mt-1 w-full rounded-lg border border-[#30363d] bg-[#161b22] px-2 py-2 text-ui-sm"
                placeholder="0.25"
              />
            </label>
          ))}
        </div>

        <label className="text-ui-xs text-[#8b949e]">
          Notes
          <textarea
            value={newCampaignForm.notes}
            onChange={(event) =>
              setNewCampaignForm((state) => ({ ...state, notes: event.target.value }))
            }
            rows={2}
            className="mt-1 w-full rounded-lg border border-[#30363d] bg-[#161b22] px-2 py-2 text-ui-sm"
            placeholder="Campaign intent, audience, and tone guardrails."
          />
        </label>

        <label className="text-ui-xs text-[#8b949e]">
          Blocklist tags (one per line)
          <textarea
            value={newCampaignForm.blocklist}
            onChange={(event) =>
              setNewCampaignForm((state) => ({ ...state, blocklist: event.target.value }))
            }
            rows={2}
            className="mt-1 w-full rounded-lg border border-[#30363d] bg-[#161b22] px-2 py-2 text-ui-sm"
            placeholder="budget_violation\ndestination_mismatch"
          />
        </label>

      <button
          type="button"
          onClick={handleCreate}
          disabled={createCampaign.isSaving || !newCampaignForm.name.trim()}
          className="inline-flex items-center gap-2 rounded-lg px-4 py-2 text-ui-sm bg-[#58a6ff] text-[#0d1117] hover:bg-[#79b8ff] transition-colors disabled:opacity-50"
        >
          <CalendarDays className="size-4" />
          Create campaign
        </button>
      </section>

      <section className="space-y-4">
        <h2 className="text-ui-sm font-semibold text-[#e6edf3]">Campaign plans</h2>
        {isLoading && campaigns.length === 0 ? (
          <div className="text-ui-sm text-[#8b949e]">Loading campaigns…</div>
        ) : sortedCampaigns.length === 0 ? (
          <div className="rounded-xl border border-[#30363d] bg-[#0f1115] p-4 text-ui-sm text-[#8b949e]">
            No campaigns yet. Start by creating your first one above.
          </div>
        ) : (
          <div className="space-y-3">
            {sortedCampaigns.map((campaign) => {
              const isEditing = editingCampaignId === campaign.plan_id;
              const form = isEditing ? editingForm : null;
              const scenario = scenarioByCampaign[campaign.plan_id] || 'baseline';

              return (
                <article key={campaign.plan_id} className="rounded-xl border border-[#30363d] bg-[#0f1115] p-4 space-y-3">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <h3 className="text-ui-sm font-semibold text-[#e6edf3]">
                        {isEditing ? (
                          <input
                            value={form?.name ?? ''}
                            onChange={(event) =>
                              setEditingForm((state) => ({ ...state, name: event.target.value }))
                            }
                            className="bg-[#161b22] border border-[#30363d] rounded-lg px-2 py-1 text-ui-sm w-full min-w-[220px]"
                          />
                        ) : (
                          campaign.name
                        )}
                      </h3>
                      <p className="text-ui-xs text-[#8b949e] mt-0.5">ID: {campaign.plan_id}</p>
                    </div>
                    <span className={`rounded-full border px-2 py-1 text-ui-xs uppercase tracking-wide ${statusClass(campaign.status)}`}>
                      {campaign.status}
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
                    <div className="text-ui-xs text-[#8b949e]">
                      <span className="text-[#c9d1d9]">Destination</span>
                      <div className="mt-1">
                        {isEditing ? (
                          <input
                            value={form?.destination ?? ''}
                            onChange={(event) =>
                              setEditingForm((state) => ({ ...state, destination: event.target.value }))
                            }
                            className="w-full bg-[#161b22] border border-[#30363d] rounded-lg px-2 py-1"
                          />
                        ) : (
                          campaign.destination || '—'
                        )}
                      </div>
                    </div>
                    <div className="text-ui-xs text-[#8b949e]">
                      <span className="text-[#c9d1d9]">Window</span>
                      <div className="mt-1">
                        {isEditing ? (
                          <div className="flex gap-2">
                            <input
                              value={form?.campaign_window_start_month ?? ''}
                              onChange={(event) =>
                                setEditingForm((state) => ({
                                  ...state,
                                  campaign_window_start_month: event.target.value,
                                }))
                              }
                              className="w-full bg-[#161b22] border border-[#30363d] rounded-lg px-2 py-1"
                              type="number"
                              placeholder="1"
                              min={1}
                              max={12}
                            />
                            <span className="py-1">→</span>
                            <input
                              value={form?.campaign_window_end_month ?? ''}
                              onChange={(event) =>
                                setEditingForm((state) => ({
                                  ...state,
                                  campaign_window_end_month: event.target.value,
                                }))
                              }
                              className="w-full bg-[#161b22] border border-[#30363d] rounded-lg px-2 py-1"
                              type="number"
                              placeholder="12"
                              min={1}
                              max={12}
                            />
                          </div>
                        ) : (
                          `${campaign.campaign_window_start_month ?? '—'} → ${campaign.campaign_window_end_month ?? '—'}`
                        )}
                      </div>
                    </div>
                    <div className="text-ui-xs text-[#8b949e]">
                      <span className="text-[#c9d1d9]">Budgets</span>
                      <div className="mt-1">
                        {isEditing ? (
                          <div className="grid grid-cols-2 gap-2">
                            <input
                              type="number"
                              value={form?.target_budget_min ?? ''}
                              onChange={(event) =>
                                setEditingForm((state) => ({
                                  ...state,
                                  target_budget_min: event.target.value,
                                }))
                              }
                              className="bg-[#161b22] border border-[#30363d] rounded-lg px-2 py-1"
                              placeholder="Min"
                            />
                            <input
                              type="number"
                              value={form?.target_budget_max ?? ''}
                              onChange={(event) =>
                                setEditingForm((state) => ({
                                  ...state,
                                  target_budget_max: event.target.value,
                                }))
                              }
                              className="bg-[#161b22] border border-[#30363d] rounded-lg px-2 py-1"
                              placeholder="Max"
                            />
                          </div>
                        ) : (
                          `${campaign.target_budget_min ?? '—'} to ${campaign.target_budget_max ?? '—'}`
                        )}
                      </div>
                    </div>
                  </div>

                  {isEditing ? (
                    <div className="space-y-3">
                      <label className="text-ui-xs text-[#8b949e]">
                        Status
                        <select
                          value={form?.status ?? campaign.status}
                          onChange={(event) =>
                            setEditingForm((state) => ({
                              ...state,
                              status: event.target.value as SeasonalCampaign['status'],
                            }))
                          }
                          className="mt-1 w-full rounded-lg border border-[#30363d] bg-[#161b22] px-2 py-1 text-ui-sm text-[#e6edf3]"
                        >
                          <option value="draft">Draft</option>
                          <option value="active">Active</option>
                          <option value="paused">Paused</option>
                          <option value="archived">Archived</option>
                        </select>
                      </label>

                      <label className="text-ui-xs text-[#8b949e]">
                        Notes
                        <textarea
                          value={form?.notes ?? ''}
                          onChange={(event) =>
                            setEditingForm((state) => ({ ...state, notes: event.target.value }))
                          }
                          rows={2}
                          className="mt-1 w-full rounded-lg border border-[#30363d] bg-[#161b22] px-2 py-1"
                        />
                      </label>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                        {CAMPAIGN_CHANNELS.map((channel) => (
                          <label key={channel} className="text-ui-xs text-[#8b949e]">
                            {channel} mix
                            <input
                              type="number"
                              step={0.05}
                              value={form?.channel_mix[channel] ?? '0'}
                              onChange={(event) =>
                                setEditingForm((state) => ({
                                  ...state,
                                  channel_mix: {
                                    ...state.channel_mix,
                                    [channel]: event.target.value,
                                  },
                                }))
                              }
                              className="mt-1 w-full rounded-lg border border-[#30363d] bg-[#161b22] px-2 py-1"
                            />
                          </label>
                        ))}
                      </div>

                      <label className="text-ui-xs text-[#8b949e]">
                        Blocklist tags (one per line)
                        <textarea
                          value={form?.blocklist ?? ''}
                          onChange={(event) =>
                            setEditingForm((state) => ({
                              ...state,
                              blocklist: event.target.value,
                            }))
                          }
                          rows={2}
                          className="mt-1 w-full rounded-lg border border-[#30363d] bg-[#161b22] px-2 py-1"
                        />
                      </label>

                      <div className="flex flex-wrap items-center gap-2">
                        <button
                          type="button"
                          onClick={handleSaveCampaign}
                          className="inline-flex items-center gap-1 rounded-lg border border-[#58a6ff] text-[#58a6ff] px-3 py-1.5 text-ui-xs hover:bg-[#58a6ff]/12"
                        >
                          <Save className="size-3.5" />
                          Save
                        </button>
                        <button
                          type="button"
                          onClick={cancelEdit}
                          className="inline-flex items-center gap-1 rounded-lg border border-[#30363d] px-3 py-1.5 text-ui-xs text-[#8b949e] hover:bg-[#1c2128]"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="rounded-lg border border-[#1c2128] bg-[#161b22] p-3 text-ui-xs text-[#8b949e]">
                      <p className="font-medium text-[#e6edf3]">Channel mix</p>
                      <p>{Object.entries(campaign.channel_mix ?? {}).map(([key, value]) => `${key}: ${value}`).join(' • ') || 'No mix set'}</p>
                    </div>
                  )}

                  <div className="flex flex-wrap items-center gap-2">
                    <label className="text-ui-xs text-[#8b949e]">
                      Scenario
                      <select
                        value={scenario}
                        onChange={(event) =>
                          setScenarioByCampaign((state) => ({
                            ...state,
                            [campaign.plan_id]: event.target.value,
                          }))
                        }
                        className="ml-2 rounded-md border border-[#30363d] bg-[#161b22] px-2 py-1 text-ui-xs text-[#e6edf3]"
                      >
                        {SCENARIO_OPTIONS.map((option) => (
                          <option key={option} value={option}>
                            {option}
                          </option>
                        ))}
                      </select>
                    </label>

                    <button
                      type="button"
                      onClick={() => handleRunSimulation(campaign.plan_id)}
                      disabled={!!simulateByCampaignRunning[campaign.plan_id]}
                      className="inline-flex items-center gap-1 rounded-lg border border-[#30363d] px-3 py-1.5 text-ui-xs text-[#e6edf3] hover:bg-[#1c2128]"
                    >
                      <Play className="size-3.5" />
                      {simulateByCampaignRunning[campaign.plan_id] ? 'Simulating…' : 'Simulate'}
                    </button>

                    <button
                      type="button"
                      onClick={() => handleRunPreflight(campaign.plan_id)}
                      disabled={!!preflightByCampaignRunning[campaign.plan_id]}
                      className="inline-flex items-center gap-1 rounded-lg border border-[#30363d] px-3 py-1.5 text-ui-xs text-[#e6edf3] hover:bg-[#1c2128]"
                    >
                      <CheckCircle2 className="size-3.5" />
                      {preflightByCampaignRunning[campaign.plan_id] ? 'Checking…' : 'Preflight'}
                    </button>

                    <button
                      type="button"
                      onClick={() => handleDispatch(campaign.plan_id, true)}
                      disabled={!!dispatchDryByCampaignRunning[campaign.plan_id]}
                      className="inline-flex items-center gap-1 rounded-lg border border-[#30363d] px-3 py-1.5 text-ui-xs text-[#e6edf3] hover:bg-[#1c2128]"
                    >
                      <Send className="size-3.5" />
                      {dispatchDryByCampaignRunning[campaign.plan_id] ? 'Dry run…' : 'Dry run'}
                    </button>

                    <button
                      type="button"
                      onClick={() => handleDispatch(campaign.plan_id, false)}
                      disabled={!!dispatchLiveByCampaignRunning[campaign.plan_id]}
                      className="inline-flex items-center gap-1 rounded-lg border border-[#2ea043] text-[#2ea043] px-3 py-1.5 text-ui-xs hover:bg-[#2ea043]/12"
                    >
                      <Play className="size-3.5" />
                      {dispatchLiveByCampaignRunning[campaign.plan_id] ? 'Dispatching…' : 'Dispatch'}
                    </button>

                    {!isEditing ? (
                      <button
                        type="button"
                        onClick={() => startEdit(campaign)}
                        className="inline-flex items-center gap-1 rounded-lg border border-[#30363d] px-3 py-1.5 text-ui-xs text-[#e6edf3] hover:bg-[#1c2128]"
                      >
                        <Pencil className="size-3.5" />
                        Edit
                      </button>
                    ) : null}

                    <button
                      type="button"
                      onClick={() => handleDelete(campaign.plan_id)}
                      disabled={deleteCampaign.isSaving}
                      className="inline-flex items-center gap-1 rounded-lg border border-[#f85149]/40 text-[#f85149] px-3 py-1.5 text-ui-xs hover:bg-[#f85149]/12"
                    >
                      <Trash2 className="size-3.5" />
                      Delete
                    </button>
                    <button
                      type="button"
                      onClick={() => handleClearActions(campaign.plan_id)}
                      className="inline-flex items-center gap-1 rounded-lg border border-[#8b949e]/40 text-[#8b949e] px-3 py-1.5 text-ui-xs hover:bg-[#1c2128]"
                    >
                      Clear action results
                    </button>
                  </div>

                  {(
                    actionMessagesByCampaign[campaign.plan_id]?.simulate ||
                    actionMessagesByCampaign[campaign.plan_id]?.preflight ||
                    actionMessagesByCampaign[campaign.plan_id]?.dispatch_dry_run ||
                    actionMessagesByCampaign[campaign.plan_id]?.dispatch_live ||
                    simulationByCampaign[campaign.plan_id] ||
                    preflightByCampaign[campaign.plan_id] ||
                    dispatchByCampaign[campaign.plan_id]
                  ) && (
                    <div className="grid grid-cols-1 xl:grid-cols-3 gap-2 text-ui-xs">
                      {actionMessagesByCampaign[campaign.plan_id]?.simulate ? (
                        <div className="rounded-lg border border-[#f85149]/30 bg-[#2c1414] p-2">
                          <p className="text-[#f85149] font-medium">Simulation error</p>
                          <p className="text-[#f7b9b8]">{actionMessagesByCampaign[campaign.plan_id]!.simulate}</p>
                        </div>
                      ) : null}

                      {actionMessagesByCampaign[campaign.plan_id]?.preflight ? (
                        <div className="rounded-lg border border-[#f85149]/30 bg-[#2c1414] p-2">
                          <p className="text-[#f85149] font-medium">Preflight error</p>
                          <p className="text-[#f7b9b8]">{actionMessagesByCampaign[campaign.plan_id]!.preflight}</p>
                        </div>
                      ) : null}

                      {actionMessagesByCampaign[campaign.plan_id]?.dispatch_dry_run ? (
                        <div className="rounded-lg border border-[#f85149]/30 bg-[#2c1414] p-2">
                          <p className="text-[#f85149] font-medium">Dry-run error</p>
                          <p className="text-[#f7b9b8]">{actionMessagesByCampaign[campaign.plan_id]!.dispatch_dry_run}</p>
                        </div>
                      ) : null}

                      {actionMessagesByCampaign[campaign.plan_id]?.dispatch_live ? (
                        <div className="rounded-lg border border-[#f85149]/30 bg-[#2c1414] p-2">
                          <p className="text-[#f85149] font-medium">Dispatch error</p>
                          <p className="text-[#f7b9b8]">{actionMessagesByCampaign[campaign.plan_id]!.dispatch_live}</p>
                        </div>
                      ) : null}

                      {simulationByCampaign[campaign.plan_id] ? (
                        <div className="rounded-lg border border-[#30363d] bg-[#161b22] p-2">
                          <p className="text-[#c9d1d9] font-medium">Simulation</p>
                          <p className="text-[#8b949e]">
                            Scenario: {simulationByCampaign[campaign.plan_id]?.scenario}
                          </p>
                          <p className="text-[#8b949e]">Leads: {simulationByCampaign[campaign.plan_id]?.projected_leads}</p>
                          <p className="text-[#8b949e]">Bookings: {simulationByCampaign[campaign.plan_id]?.projected_bookings}</p>
                          <p className="text-[#8b949e]">Margin: {simulationByCampaign[campaign.plan_id]?.projected_margin_pct}%</p>
                          <p className="text-[#8b949e]">Confidence: {simulationByCampaign[campaign.plan_id]?.confidence}</p>
                          <p className="text-[#8b949e]">Notes: {(simulationByCampaign[campaign.plan_id]?.notes ?? []).join(' • ')}</p>
                        </div>
                      ) : null}

                      {preflightByCampaign[campaign.plan_id] ? (
                        <div className="rounded-lg border border-[#30363d] bg-[#161b22] p-2">
                          <p className="text-[#c9d1d9] font-medium">Preflight</p>
                          <p className="text-[#8b949e]">
                            Status: {preflightByCampaign[campaign.plan_id]?.ok ? 'Pass' : 'Needs attention'}
                          </p>
                          <p className="text-[#8b949e]">Risk score: {preflightByCampaign[campaign.plan_id]?.risk_score}</p>
                          <ul className="mt-1 space-y-1">
                            {(preflightByCampaign[campaign.plan_id]?.checks ?? []).map((item) => (
                              <li key={item.check}>
                                {item.check}: {item.status}
                              </li>
                            ))}
                          </ul>
                        </div>
                      ) : null}

                      {dispatchByCampaign[campaign.plan_id] ? (
                        <div className="rounded-lg border border-[#30363d] bg-[#161b22] p-2">
                          <p className="text-[#c9d1d9] font-medium">Dispatch</p>
                          <p className="text-[#8b949e]">
                            Scenario: {scenarioByCampaign[campaign.plan_id] || 'baseline'}
                          </p>
                          <p className="text-[#8b949e]">Status: {dispatchByCampaign[campaign.plan_id]?.ok ? 'Ready' : 'Blocked'}</p>
                          <p className="text-[#8b949e]">Dry run: {dispatchByCampaign[campaign.plan_id]?.dry_run ? 'Yes' : 'No'}</p>
                          <p className="text-[#8b949e]">Executed at: {dispatchByCampaign[campaign.plan_id]?.executed_at}</p>
                          <p className="text-[#8b949e]">
                            Channels: {(dispatchByCampaign[campaign.plan_id]?.dispatched_channels ?? []).join(', ')}
                          </p>
                        </div>
                      ) : null}
                    </div>
                  )}
                </article>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
