'use client';

import React, { useState } from 'react';
import { RefreshCw, ShieldAlert, Sparkles } from 'lucide-react';
import SimulatedBadge from '@/components/ui/SimulatedBadge';

/**
 * IROPS is currently a deterministic journey-graph analysis preview. It does
 * not rebook a carrier, issue payment, determine legal eligibility, or send a
 * supplier message. Keep this contract intentionally narrower than the
 * lower-level simulator's historical output.
 */
type StatutoryCompensation = {
  amount_eur: number | null;
  estimated_amount_eur?: number | null;
  regulation: string;
  status?: string;
};

type CounterfactualOption = {
  tier: string;
  title: string;
  arrival_delta_minutes: number;
  airline: string;
  cabin_class: string;
  action: string;
  status?: string;
  provider_connected?: boolean;
  external_reference?: string | null;
};

type HealingPlan = {
  incident_id: string;
  delayed_node_title: string;
  delay_minutes: number;
  ripple_summary: string;
  statutory_compensation: StatutoryCompensation;
  counterfactual_options: CounterfactualOption[];
  emergency_lodging_vcc: null;
  waiver_status?: string;
  analysis_status?: string;
  evidence_status?: string;
  operator_next_step?: string;
};

type HealingPreviewResponse = {
  status?: string;
  reality_tier?: string;
  simulation?: boolean;
  provider_connected?: boolean;
  external_action?: boolean;
  operational_write?: boolean;
  effects?: string[];
  healing_plan?: Partial<HealingPlan>;
};

const PREVIEW_NOTICE =
  'Local analysis only. No carrier booking, payment, legal claim, VCC, or supplier message is executed.';

function localPreviewPlan(delayMinutes: number): HealingPlan {
  return {
    incident_id: 'PREVIEW-IROPS-LOCAL',
    delayed_node_title: 'Illustrative inbound flight',
    delay_minutes: delayMinutes,
    ripple_summary: `Local journey-graph preview for a +${delayMinutes}m inbound delay; provider impact is unverified.`,
    statutory_compensation: {
      amount_eur: null,
      regulation: 'Eligibility not assessed — itinerary, carrier, jurisdiction, and evidence are required.',
      status: 'UNVERIFIED_LEGAL_ESTIMATE',
    },
    counterfactual_options: [
      {
        tier: 'OPTION_A_MIN_DELAY',
        title: 'Illustrative alternative route via a connecting hub',
        arrival_delta_minutes: 45,
        airline: 'Illustrative carrier candidate',
        cabin_class: 'Unverified cabin',
        action: 'Review only',
        status: 'PREVIEW_ONLY',
        provider_connected: false,
        external_reference: null,
      },
      {
        tier: 'OPTION_B_SAME_CARRIER',
        title: 'Illustrative later service on the same route',
        arrival_delta_minutes: 180,
        airline: 'Unverified carrier candidate',
        cabin_class: 'Unverified cabin',
        action: 'Review only',
        status: 'PREVIEW_ONLY',
        provider_connected: false,
        external_reference: null,
      },
      {
        tier: 'OPTION_C_COMFORT_UPGRADE',
        title: 'Illustrative comfort alternative',
        arrival_delta_minutes: 90,
        airline: 'Illustrative carrier candidate',
        cabin_class: 'Unverified cabin',
        action: 'Review only',
        status: 'PREVIEW_ONLY',
        provider_connected: false,
        external_reference: null,
      },
    ],
    emergency_lodging_vcc: null,
    waiver_status: 'DRAFT_NOT_SENT',
    analysis_status: 'PREVIEW_ONLY',
    evidence_status: 'UNVERIFIED_LOCAL_INPUT',
    operator_next_step: 'Review the analysis with an authorized operator and verify provider availability separately.',
  };
}

function normalizePreviewPlan(
  candidate: Partial<HealingPlan> | undefined,
  requestedDelay: number,
): HealingPlan {
  const fallback = localPreviewPlan(requestedDelay);
  if (!candidate || typeof candidate !== 'object') return fallback;

  const compensation = candidate.statutory_compensation;
  const options = candidate.counterfactual_options;
  return {
    ...fallback,
    ...candidate,
    delay_minutes: typeof candidate.delay_minutes === 'number' ? candidate.delay_minutes : requestedDelay,
    statutory_compensation: {
      ...fallback.statutory_compensation,
      ...(compensation && typeof compensation === 'object' ? compensation : {}),
      // A client must never render a number as a legal entitlement. The API
      // may retain an internal estimate, but the UI only displays unknown.
      amount_eur: null,
    },
    counterfactual_options: Array.isArray(options)
      ? options.map((option) => ({
          ...fallback.counterfactual_options[0],
          ...option,
          action: 'Review only',
          status: 'PREVIEW_ONLY',
          provider_connected: false,
          external_reference: null,
        }))
      : fallback.counterfactual_options,
    emergency_lodging_vcc: null,
    analysis_status: 'PREVIEW_ONLY',
    evidence_status: candidate.evidence_status ?? 'UNVERIFIED_LOCAL_INPUT',
    waiver_status: candidate.waiver_status ?? 'DRAFT_NOT_SENT',
  };
}

export default function IROPSAutoHealerPanel() {
  const [delayMinutes, setDelayMinutes] = useState(180);
  const [isHealing, setIsHealing] = useState(false);
  const [healingPlan, setHealingPlan] = useState<HealingPlan | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleHealDisruption = async () => {
    const requestedDelay = Number.isFinite(delayMinutes) ? delayMinutes : 180;
    setIsHealing(true);
    setErrorMessage(null);
    try {
      const res = await fetch('/api/v1/irops-healer/heal', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          trip_id: 'TRIP-HEAL-889',
          delayed_node_id: 'N_FLT_178',
          delay_minutes: requestedDelay,
        }),
      });
      if (!res.ok) throw new Error('IROPS preview request failed');
      const data = (await res.json()) as HealingPreviewResponse;
      setHealingPlan(normalizePreviewPlan(data.healing_plan, requestedDelay));
    } catch {
      // Degraded mode stays a truthful local preview; it must not invent a
      // payment instrument, legal amount, booking reference, or dispatch.
      setHealingPlan(localPreviewPlan(requestedDelay));
      setErrorMessage('Provider preview unavailable; showing a local analysis-only scenario.');
    } finally {
      setIsHealing(false);
    }
  };

  return (
    <div className="p-4 rounded-xl border border-border bg-card space-y-4">
      <div className="flex items-center justify-between gap-2">
        <h4 className="text-sm font-semibold text-foreground flex items-center gap-2">
          <ShieldAlert className="h-4 w-4 text-amber-500" />
          IROPS Recovery Plan Preview
        </h4>
        <div className="flex items-center gap-2 shrink-0">
          <SimulatedBadge label="Preview only" />
          <span className="text-[10px] font-mono bg-amber-500/10 text-amber-500 px-2 py-0.5 rounded">
            NO OPERATIONAL EFFECTS
          </span>
        </div>
      </div>

      <p className="text-xs text-muted-foreground" role="note">
        {PREVIEW_NOTICE}
      </p>

      <div className="flex items-center gap-3">
        <label htmlFor="irops-delay-minutes" className="text-xs text-muted-foreground">
          Preview inbound delay:
        </label>
        <input
          id="irops-delay-minutes"
          type="number"
          min={0}
          value={delayMinutes}
          onChange={(e) => setDelayMinutes(Number(e.target.value))}
          className="w-24 p-2 text-xs font-mono rounded border border-border bg-background text-foreground"
        />
        <span className="text-xs text-muted-foreground">minutes</span>
        <button
          onClick={handleHealDisruption}
          disabled={isHealing}
          className="ml-auto py-2 px-3.5 rounded-lg bg-amber-500 text-white text-xs font-semibold hover:bg-amber-600 flex items-center gap-1.5"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${isHealing ? 'animate-spin' : ''}`} />
          {isHealing ? 'Generating local preview…' : 'Generate recovery preview'}
        </button>
      </div>

      {errorMessage && (
        <p className="text-xs text-amber-600" role="status">
          {errorMessage}
        </p>
      )}

      {healingPlan && (
        <div className="space-y-3 pt-2" data-testid="irops-preview-result">
          <div className="flex flex-wrap items-center gap-2 text-[10px] font-mono uppercase text-amber-600">
            <span>PREVIEW_ONLY</span>
            <span aria-hidden="true">·</span>
            <span>UNVERIFIED LOCAL INPUT</span>
          </div>

          <div className="p-3.5 rounded-xl border border-border bg-muted/40 grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
            <div className="space-y-1">
              <span className="text-[10px] text-muted-foreground block">Disrupted leg candidate</span>
              <span className="font-bold text-foreground">{healingPlan.delayed_node_title}</span>
              <span className="text-[10px] text-red-500 font-mono block">+{healingPlan.delay_minutes}m scenario input</span>
            </div>
            <div className="space-y-1">
              <span className="text-[10px] text-muted-foreground block">Compensation eligibility</span>
              <span className="font-bold text-foreground text-sm">Not assessed</span>
              <span className="text-[10px] text-muted-foreground block">
                {healingPlan.statutory_compensation.regulation}
              </span>
            </div>
            <div className="space-y-1">
              <span className="text-[10px] text-muted-foreground block">Lodging / payment</span>
              <span className="font-bold text-foreground text-sm">Not issued</span>
              <span className="text-[10px] text-muted-foreground block">No payment provider was called.</span>
            </div>
          </div>

          <p className="text-xs text-muted-foreground">{healingPlan.ripple_summary}</p>

          <div className="space-y-2">
            <h5 className="text-xs font-semibold text-foreground flex items-center gap-1.5">
              <Sparkles className="h-3.5 w-3.5 text-primary" />
              Illustrative rerouting candidates
            </h5>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-2 text-xs">
              {healingPlan.counterfactual_options.map((opt) => (
                <div key={opt.tier} className="p-3 rounded-lg border border-border bg-background space-y-1.5">
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-bold text-foreground">{opt.airline}</span>
                    <span className="text-[10px] font-mono text-muted-foreground font-semibold">
                      +{opt.arrival_delta_minutes}m candidate
                    </span>
                  </div>
                  <p className="text-[11px] text-muted-foreground">{opt.title}</p>
                  <div className="pt-1.5 border-t border-border flex items-center justify-between gap-2">
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-muted font-mono">{opt.cabin_class}</span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded border border-amber-500/30 text-amber-600 font-semibold">
                      Review only
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-lg border border-border bg-muted/20 p-3 text-xs text-muted-foreground">
            <span className="font-semibold text-foreground">Operator next step: </span>
            {healingPlan.operator_next_step ?? 'Verify provider availability and evidence before any action.'}
          </div>
        </div>
      )}
    </div>
  );
}
