"use client";

import { Accessibility, AlertCircle, AlertTriangle, CheckCircle, Gauge, ThermometerSun, type LucideIcon } from "lucide-react";
import type { SuitabilityProfile } from "@/types/spine";
import { SUITABILITY_STATUS_LABELS } from "@/lib/label-maps";

interface SuitabilityCardProps {
  profile: SuitabilityProfile;
  compact?: boolean;
}

const TYPE_ICONS: Record<string, LucideIcon> = {
  mobility: Accessibility,
  intensity: Gauge,
  climate: ThermometerSun,
  other: AlertTriangle,
};

const STATUS_STYLES: Record<
  string,
  { border: string; bg: string; text: string; Icon: LucideIcon; iconClassName: string }
> = {
  suitable: {
    border: "border-accent-green",
    bg: "bg-[rgba(var(--accent-green-rgb)/0.06)]",
    text: "text-accent-green",
    Icon: CheckCircle,
    iconClassName: "text-accent-green",
  },
  caution: {
    border: "border-accent-amber",
    bg: "bg-[rgba(var(--accent-amber-rgb)/0.06)]",
    text: "text-accent-amber",
    Icon: AlertCircle,
    iconClassName: "text-accent-amber",
  },
  unsuitable: {
    border: "border-accent-red",
    bg: "bg-[rgba(var(--accent-red-rgb)/0.06)]",
    text: "text-accent-red",
    Icon: AlertTriangle,
    iconClassName: "text-accent-red",
  },
};

export function SuitabilityCard({ profile, compact = false }: SuitabilityCardProps) {
  const { summary, dimensions } = profile;
  const style = STATUS_STYLES[summary.status] || STATUS_STYLES.caution;
  const StatusIcon = style.Icon;

  return (
    <div
      className={`rounded-lg border ${style.border} ${style.bg} overflow-hidden`}
      data-testid="suitability-card"
    >
      {/* Header */}
      <div className="p-4 flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <StatusIcon className={`size-5 ${style.iconClassName}`} aria-hidden="true" />
          <div>
            <h3 className={`font-semibold text-ui-sm ${style.text}`}>
              {SUITABILITY_STATUS_LABELS[summary.status] || summary.status}
            </h3>
            <p className="text-ui-xs text-text-muted mt-0.5">
              {summary.primaryReason}
            </p>
          </div>
        </div>
        <div className="text-right">
          <span className={`text-ui-lg font-bold ${style.text}`}>
            {summary.overallScore}
          </span>
          <span className="text-ui-xs text-text-muted"> /100</span>
        </div>
      </div>

      {/* Dimensions */}
      {!compact && dimensions.length > 0 && (
        <div className="border-t border-border-default">
          {dimensions.map((dim) => (
            <DimensionRow key={dim.type} dimension={dim} />
          ))}
        </div>
      )}
    </div>
  );
}

function DimensionRow({ dimension }: { dimension: SuitabilityProfile["dimensions"][number] }) {
  const DimensionIcon = TYPE_ICONS[dimension.type] || TYPE_ICONS.other;
  const severityColor =
    dimension.severity === "high"
      ? "text-accent-red"
      : dimension.severity === "medium"
        ? "text-accent-amber"
        : "text-text-secondary";

  return (
    <div className="px-4 py-3 flex items-start gap-3 border-b border-border-default last:border-b-0">
      <DimensionIcon className="size-4 mt-0.5 text-text-muted" aria-hidden="true" />
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-2">
          <span className="text-ui-sm font-medium capitalize text-text-primary">
            {dimension.type}
          </span>
          <span className={`text-ui-xs font-semibold uppercase ${severityColor}`}>
            {dimension.severity.charAt(0).toUpperCase() + dimension.severity.slice(1)}
          </span>
        </div>
        <p className="text-ui-xs text-text-muted mt-0.5">
          {dimension.reason}
        </p>
        <div className="mt-1 w-full bg-highlight rounded-full h-1">
          <div
            className="bg-accent-blue h-1 rounded-full"
            style={{ width: `${Math.min(dimension.score, 100)}%` }}
          />
        </div>
      </div>
    </div>
  );
}

export default SuitabilityCard;
