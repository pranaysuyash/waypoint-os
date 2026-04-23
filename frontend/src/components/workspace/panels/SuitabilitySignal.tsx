"use client";

import React, { useCallback } from "react";
import { AlertTriangle, AlertCircle, ChevronRight } from "lucide-react";
import styles from "@/app/workbench/workbench.module.css";

export interface SuitabilityFlagData {
  flag_type: string;
  severity: "low" | "medium" | "high" | "critical";
  reason: string;
  confidence: number;
  details?: Record<string, any>;
  affected_travelers?: string[];
}

interface SuitabilitySignalProps {
  flags: SuitabilityFlagData[];
  tripId?: string;
  onDrill?: (flagType: string, stage?: string) => void;
}

/**
 * Flag label mapping — convert flag_type to semantic, human-readable labels
 */
const FLAG_LABELS: Record<string, string> = {
  age_too_young: "Age Too Young",
  age_too_old: "Age Too Old",
  weight_exceeds_limit: "Weight Exceeds Limit",
  toddler_water_unsafe: "Water Activity Not Safe for Toddlers",
  toddler_height_unsafe: "Height Restriction Excludes Toddlers",
  toddler_late_night: "Late Night Not Suitable for Toddlers",
  elderly_intense: "Physical Intensity Unsafe for Elderly",
  elderly_extreme: "Extreme Intensity Not Suitable for Elderly",
  elderly_walking_heavy: "Walking-Heavy Activity Unsuitable for Elderly",
  elderly_stairs_heavy: "Stairs Unsafe for Elderly Travelers",
  elderly_water_challenges: "Water Activity Challenges for Elderly",
  elderly_height_unsuitable: "Height Activity Not Suitable for Elderly",
  budget_luxury_mismatch: "Luxury Activity Exceeds Budget Profile",
  toddler_pacing: "Too Many Activities in One Day for Toddler",
  elderly_overload: "Too Much Physical Intensity in Itinerary",
  itinerary_coherence: "Itinerary Pacing Concern",
};

/**
 * Explanation mapping — why did this flag trigger?
 */
const FLAG_EXPLANATIONS: Record<string, string> = {
  age_too_young: "Participant is below the minimum age requirement for this activity.",
  age_too_old: "Participant exceeds the maximum age for safe participation.",
  weight_exceeds_limit: "Participant weight exceeds the activity's weight limit.",
  toddler_water_unsafe: "Water-based activities pose safety risks for toddlers.",
  toddler_height_unsafe: "Height-based participation restrictions exclude toddlers from this activity.",
  toddler_late_night: "Late night activities (post-21:00) are unsuitable for toddler schedules.",
  elderly_intense: "Physical intensity of this activity may strain elderly travelers.",
  elderly_extreme: "Extreme physical intensity is unsafe for elderly travelers.",
  elderly_walking_heavy: "Walking-heavy activities may not suit elderly mobility profiles.",
  elderly_stairs_heavy: "Activities with heavy stair climbing are unsafe for elderly travelers.",
  elderly_water_challenges: "Water-based activities may present mobility challenges for elderly travelers.",
  elderly_height_unsuitable: "Height-based activities may not be safe for elderly travelers.",
  budget_luxury_mismatch: "This luxury-tier activity exceeds the identified budget-conscious traveler profile.",
  toddler_pacing: "Scheduling more than 3 activities in one day is too demanding for toddlers.",
  elderly_overload: "Two or more high-intensity activities in the itinerary create cumulative fatigue risk.",
  itinerary_coherence: "The itinerary structure may not provide adequate pacing and recovery time.",
};

/**
 * Tier classification — which flags are hard blockers vs. warnings?
 */
function classifyTier(severity: string): "tier1" | "tier2" {
  return severity === "critical" ? "tier1" : "tier2";
}

/**
 * Get severity-based styling classes
 */
function getSeverityClass(severity: string): { bg: string; border: string; icon: string } {
  switch (severity) {
    case "critical":
      return {
        bg: "bg-red-50 dark:bg-red-950",
        border: "border-l-4 border-red-500",
        icon: "text-red-600 dark:text-red-400",
      };
    case "high":
      return {
        bg: "bg-yellow-50 dark:bg-yellow-950",
        border: "border-l-4 border-yellow-500",
        icon: "text-yellow-600 dark:text-yellow-400",
      };
    case "medium":
      return {
        bg: "bg-blue-50 dark:bg-blue-950",
        border: "border-l-4 border-blue-400",
        icon: "text-blue-600 dark:text-blue-400",
      };
    default:
      return {
        bg: "bg-gray-50 dark:bg-gray-900",
        border: "border-l-4 border-gray-400",
        icon: "text-gray-500 dark:text-gray-400",
      };
  }
}

/**
 * Get badge class for severity
 */
function getBadgeClass(severity: string): string {
  switch (severity) {
    case "critical":
      return "bg-red-200 text-red-900 dark:bg-red-900 dark:text-red-100";
    case "high":
      return "bg-yellow-200 text-yellow-900 dark:bg-yellow-900 dark:text-yellow-100";
    case "medium":
      return "bg-blue-200 text-blue-900 dark:bg-blue-900 dark:text-blue-100";
    default:
      return "bg-gray-200 text-gray-900 dark:bg-gray-700 dark:text-gray-100";
  }
}

interface FlagItemProps {
  flag: SuitabilityFlagData;
  onDrill?: (flagType: string) => void;
  drillable?: boolean;
}

function FlagItem({ flag, onDrill, drillable = true }: FlagItemProps) {
  const tier = classifyTier(flag.severity);
  const severityClass = getSeverityClass(flag.severity);
  const badgeClass = getBadgeClass(flag.severity);
  const label = FLAG_LABELS[flag.flag_type] || flag.flag_type;
  const explanation = FLAG_EXPLANATIONS[flag.flag_type] || flag.reason;

  const handleDrill = useCallback(() => {
    if (onDrill && drillable) {
      onDrill(flag.flag_type);
    }
  }, [flag.flag_type, onDrill, drillable]);

  const travelersDisplay = flag.affected_travelers?.length
    ? flag.affected_travelers.join(", ")
    : "Multiple travelers";

  return (
    <div
      className={`${severityClass.bg} ${severityClass.border} p-3 rounded-md transition-all ${
        drillable ? "cursor-pointer hover:shadow-sm" : ""
      }`}
      onClick={handleDrill}
      role={drillable ? "button" : undefined}
      tabIndex={drillable ? 0 : undefined}
    >
      <div className="flex items-start gap-3">
        {/* Icon */}
        <div className={`flex-shrink-0 mt-0.5 ${severityClass.icon}`}>
          {tier === "tier1" ? <AlertTriangle size={18} /> : <AlertCircle size={18} />}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <div>
              <h4 className="font-semibold text-sm text-gray-900 dark:text-gray-100">{label}</h4>
              <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">{explanation}</p>
            </div>
            {drillable && <ChevronRight size={16} className="flex-shrink-0 text-gray-400" />}
          </div>

          {/* Metadata */}
          <div className="flex items-center gap-2 mt-2 flex-wrap">
            <span className={`text-xs px-2 py-1 rounded ${badgeClass}`}>
              {flag.severity.toUpperCase()}
            </span>
            <span className="text-xs text-gray-600 dark:text-gray-400">
              Confidence: {Math.round(flag.confidence * 100)}%
            </span>
            <span className="text-xs text-gray-600 dark:text-gray-400">
              {travelersDisplay}
            </span>
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
}: SuitabilitySignalProps) {
  // Separate Tier 1 (critical) and Tier 2 (high/medium/low)
  const tier1Flags = flags.filter((f) => classifyTier(f.severity) === "tier1");
  const tier2Flags = flags.filter((f) => classifyTier(f.severity) === "tier2");

  const handleDrill = useCallback(
    (flagType: string) => {
      if (onDrill && tripId) {
        onDrill(flagType);
      }
    },
    [onDrill, tripId]
  );

  // If no flags, return null (parent should handle empty state)
  if (flags.length === 0) {
    return null;
  }

  return (
    <div className={styles.section}>
      <h3 className={styles.sectionTitle}>Suitability Audit Results</h3>
      <div className={styles.card}>
        {/* Summary */}
        <div className="mb-4 p-3 bg-gray-50 dark:bg-gray-900 rounded border border-gray-200 dark:border-gray-700">
          <p className="text-sm text-gray-700 dark:text-gray-300">
            <strong>{flags.length}</strong> suitability issue{flags.length !== 1 ? "s" : ""} detected
            {tier1Flags.length > 0 && (
              <span className="text-red-600 dark:text-red-400">
                {" "}
                — <strong>{tier1Flags.length}</strong> hard blocker{tier1Flags.length !== 1 ? "s" : ""}
                require resolution before send
              </span>
            )}
          </p>
        </div>

        {/* Tier 1: Hard Blockers (Critical) */}
        {tier1Flags.length > 0 && (
          <div className="mb-6">
            <h4 className="font-semibold text-red-700 dark:text-red-400 text-sm mb-3 flex items-center gap-2">
              <AlertTriangle size={16} />
              Tier 1: Hard Blockers (Must Resolve)
            </h4>
            <div className="space-y-2">
              {tier1Flags.map((flag) => (
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

        {/* Tier 2: Warnings */}
        {tier2Flags.length > 0 && (
          <div>
            <h4 className="font-semibold text-yellow-700 dark:text-yellow-400 text-sm mb-3 flex items-center gap-2">
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
