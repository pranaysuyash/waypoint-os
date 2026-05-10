"use client";

import React, { useCallback } from "react";
import { AlertTriangle, AlertCircle, ChevronRight, CheckCircle2 } from "lucide-react";
import type { SuitabilityFlagData } from "@/types/spine";
import styles from "@/components/workbench/workbench.module.css";

export type { SuitabilityFlagData };

interface SuitabilitySignalProps {
  flags: SuitabilityFlagData[];
  tripId?: string;
  onDrill?: (flagType: string, stage?: string) => void;
  onAcknowledge?: (flagType: string) => void;
  acknowledgedFlags?: ReadonlySet<string>;
}

/**
 * Stable label map for coherence flags (fixed keys the backend always emits)
 * and legacy semantic flag types retained for forward compatibility.
 *
 * Activity-specific dynamic flags (suitability_exclusion_*, suitability_discouraged_*)
 * are handled by deriveFlagLabel() using the flag's details payload instead.
 */
const FLAG_LABELS: Record<string, string> = {
  // Coherence flags - keys emitted by evaluate_itinerary_coherence
  suitability_overload_elderly: "Itinerary Intensity Overload for Elderly",
  suitability_pacing_toddler: "Too Many Activities: Toddler Stamina Risk",
  // Generic coherence fallback
  suitability_coherence: "Itinerary Pacing Concern",
  itinerary_coherence: "Itinerary Pacing Concern",
  // Legacy semantic flag types (retained for future backend alignment)
  age_too_young: "Age Too Young for Activity",
  age_too_old: "Age Exceeds Activity Maximum",
  weight_exceeds_limit: "Weight Exceeds Activity Limit",
  toddler_water_unsafe: "Water Activity Not Safe for Toddlers",
  toddler_height_unsafe: "Height Restriction Excludes Toddlers",
  toddler_late_night: "Late Night Not Suitable for Toddlers",
  toddler_pacing: "Too Many Activities for Toddler",
  elderly_intense: "Physical Intensity Unsafe for Elderly",
  elderly_extreme: "Extreme Intensity Not Suitable for Elderly",
  elderly_walking_heavy: "Walking-Heavy Activity Unsuitable for Elderly",
  elderly_stairs_heavy: "Stairs Unsafe for Elderly Travelers",
  elderly_water_challenges: "Water Activity Challenges for Elderly",
  elderly_height_unsuitable: "Height Activity Not Suitable for Elderly",
  elderly_overload: "Too Much Physical Intensity in Itinerary",
  budget_luxury_mismatch: "Luxury Activity Exceeds Budget Profile",
};

/**
 * Derive a human-readable label from a flag.
 *
 * Priority:
 *   1. Static map - for coherence flags with stable, predictable keys
 *   2. Details payload - for activity-specific dynamic flags whose key encodes
 *      tier and activity_id. The details object carries activity_name and
 *      participant_label which produce a precise, readable label.
 *   3. Flag reason - the backend always provides a human-readable reason string
 *   4. Cleaned-up flag_type string - last resort
 */
function deriveFlagLabel(flag: SuitabilityFlagData): string {
  if (FLAG_LABELS[flag.flag_type]) return FLAG_LABELS[flag.flag_type];

  const activityName = flag.details?.activity_name as string | undefined;
  const participantLabel = flag.details?.participant_label as string | undefined;
  const tier = flag.details?.tier as string | undefined;

  if (activityName && participantLabel) {
    const action = tier === "exclude" ? "Not Permitted" : "Caution Advised";
    const who = participantLabel.charAt(0).toUpperCase() + participantLabel.slice(1);
    return `${activityName}: ${action} for ${who}`;
  }

  if (flag.reason && flag.reason.length > 0) {
    // Trim long reasons to a headline - keep it to the first sentence
    const first = flag.reason.split(/[.;]/)[0].trim();
    return first.length > 0 ? first : flag.flag_type;
  }

  return flag.flag_type
    .replace(/^suitability_/, "")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function classifyTier(severity: string): "tier1" | "tier2" {
  return severity === "critical" ? "tier1" : "tier2";
}

function getSeverityClass(severity: string): { bg: string; icon: string } {
  switch (severity) {
    case "critical":
      return { bg: "bg-[rgba(var(--accent-red-rgb)/0.06)]", icon: "text-accent-red" };
    case "high":
      return { bg: "bg-[rgba(var(--accent-amber-rgb)/0.06)]", icon: "text-accent-amber" };
    case "medium":
      return { bg: "bg-[rgba(var(--accent-blue-rgb)/0.06)]", icon: "text-accent-blue" };
    default:
      return { bg: "bg-elevated", icon: "text-text-muted" };
  }
}

function getBadgeClass(severity: string): string {
  switch (severity) {
    case "critical": return "bg-[rgba(var(--accent-red-rgb)/0.15)] text-accent-red";
    case "high":     return "bg-[rgba(var(--accent-amber-rgb)/0.15)] text-accent-amber";
    case "medium":   return "bg-[rgba(var(--accent-blue-rgb)/0.15)] text-accent-blue";
    default:         return "bg-elevated text-text-muted";
  }
}

interface FlagItemProps {
  flag: SuitabilityFlagData;
  onDrill?: (flagType: string) => void;
  onAcknowledge?: (flagType: string) => void;
  isAcknowledged?: boolean;
  drillable?: boolean;
}

function FlagItem({ flag, onDrill, onAcknowledge, isAcknowledged = false, drillable = true }: FlagItemProps) {
  const tier = classifyTier(flag.severity);
  const severityClass = getSeverityClass(flag.severity);
  const badgeClass = getBadgeClass(flag.severity);
  const label = deriveFlagLabel(flag);

  const handleDrill = useCallback(() => {
    if (onDrill && drillable) onDrill(flag.flag_type);
  }, [flag.flag_type, onDrill, drillable]);

  const handleAcknowledge = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      if (onAcknowledge && !isAcknowledged) onAcknowledge(flag.flag_type);
    },
    [flag.flag_type, onAcknowledge, isAcknowledged],
  );

  const travelersDisplay = flag.affected_travelers?.length
    ? flag.affected_travelers.join(", ")
    : "Multiple travelers";

  return (
    <div
      className={`${severityClass.bg} p-3 rounded-md transition-all ${
        isAcknowledged ? "opacity-60" : ""
      } ${drillable && !isAcknowledged ? "cursor-pointer hover:shadow-sm" : ""}`}
      onClick={drillable && !isAcknowledged ? handleDrill : undefined}
      onKeyDown={drillable && !isAcknowledged ? (e: React.KeyboardEvent) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); handleDrill(); } } : undefined}
      role="button"
      aria-disabled={!drillable || isAcknowledged}
      tabIndex={drillable && !isAcknowledged ? 0 : undefined}
      data-testid={`suitability-flag-${flag.flag_type}`}
    >
      <div className="flex items-start gap-3">
        <div className={`flex-shrink-0 mt-0.5 ${severityClass.icon}`}>
          {isAcknowledged
            ? <CheckCircle2 size={18} />
            : tier === "tier1"
            ? <AlertTriangle size={18} />
            : <AlertCircle size={18} />}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <div>
              <h4 className="font-semibold text-ui-sm text-text-primary">
                {label}
                {isAcknowledged && (
                  <span className="ml-2 text-ui-xs font-normal text-text-muted">
                    (acknowledged)
                  </span>
                )}
              </h4>
              <p className="text-ui-xs text-text-muted mt-1">{flag.reason}</p>
            </div>
            {drillable && !isAcknowledged && <ChevronRight size={16} className="flex-shrink-0 text-text-muted" />}
          </div>

          <div className="flex items-center gap-2 mt-2 flex-wrap">
            <span className={`text-ui-xs px-2 py-1 rounded ${badgeClass}`}>
              {flag.severity.toUpperCase()}
            </span>
            <span className="text-ui-xs text-text-muted">
              {Math.round(flag.confidence * 100)}% confidence
            </span>
            <span className="text-ui-xs text-text-muted">{travelersDisplay}</span>

            {tier === "tier1" && onAcknowledge && !isAcknowledged && (
              <button
                type="button"
                onClick={handleAcknowledge}
                className="ml-auto text-ui-xs px-2 py-1 rounded border border-[rgba(var(--accent-red-rgb)/0.4)] text-accent-red hover:bg-[rgba(var(--accent-red-rgb)/0.08)] transition-colors"
                data-testid={`acknowledge-flag-${flag.flag_type}`}
              >
                Acknowledge Risk
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export function SuitabilitySignal({
  flags,
  tripId,
  onDrill,
  onAcknowledge,
  acknowledgedFlags = new Set(),
}: SuitabilitySignalProps) {
  const tier1Flags = flags.filter((f) => classifyTier(f.severity) === "tier1");
  const tier2Flags = flags.filter((f) => classifyTier(f.severity) === "tier2");

  const unacknowledgedCritical = tier1Flags.filter((f) => !acknowledgedFlags.has(f.flag_type));

  const handleDrill = useCallback(
    (flagType: string) => {
      if (onDrill && tripId) onDrill(flagType);
    },
    [onDrill, tripId],
  );

  if (flags.length === 0) return null;

  return (
    <div className={styles.section} data-testid="suitability-signal">
      <h3 className={styles.sectionTitle}>Suitability Audit Results</h3>
      <div className={styles.card}>
        <div className="mb-4 p-3 bg-surface rounded border border-border-default">
          <p className="text-ui-sm text-text-secondary">
            <strong>{flags.length}</strong> suitability issue{flags.length !== 1 ? "s" : ""} detected
            {tier1Flags.length > 0 && (
              <span className="text-accent-red">
                {" - "}
                <strong>{unacknowledgedCritical.length > 0 ? unacknowledgedCritical.length : tier1Flags.length}</strong>
                {unacknowledgedCritical.length > 0
                  ? ` hard blocker${unacknowledgedCritical.length !== 1 ? "s" : ""} require acknowledgment before approval`
                  : ` hard blocker${tier1Flags.length !== 1 ? "s" : ""} acknowledged`}
              </span>
            )}
          </p>
        </div>

        {tier1Flags.length > 0 && (
          <div className="mb-6">
            <h4 className="font-semibold text-accent-red text-ui-sm mb-3 flex items-center gap-2">
              <AlertTriangle size={16} />
              Tier 1: Hard Blockers (Must Acknowledge Before Approval)
            </h4>
            <div className="space-y-2">
              {tier1Flags.map((flag) => (
                <FlagItem
                  key={flag.flag_type}
                  flag={flag}
                  onDrill={handleDrill}
                  onAcknowledge={onAcknowledge}
                  isAcknowledged={acknowledgedFlags.has(flag.flag_type)}
                  drillable={!!tripId}
                />
              ))}
            </div>
          </div>
        )}

        {tier2Flags.length > 0 && (
          <div>
            <h4 className="font-semibold text-accent-amber text-ui-sm mb-3 flex items-center gap-2">
              <AlertCircle size={16} />
              Tier 2: Warnings (Review Recommended)
            </h4>
            <div className="space-y-2">
              {tier2Flags.map((flag) => (
                <FlagItem
                  key={flag.flag_type}
                  flag={flag}
                  onDrill={handleDrill}
                  drillable={!!tripId}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
