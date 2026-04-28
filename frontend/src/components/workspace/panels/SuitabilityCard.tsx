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
    border: "border-green-500",
    bg: "bg-green-50 dark:bg-green-950",
    text: "text-green-800 dark:text-green-200",
    Icon: CheckCircle,
    iconClassName: "text-green-600",
  },
  caution: {
    border: "border-yellow-500",
    bg: "bg-yellow-50 dark:bg-yellow-950",
    text: "text-yellow-800 dark:text-yellow-200",
    Icon: AlertCircle,
    iconClassName: "text-yellow-600",
  },
  unsuitable: {
    border: "border-red-500",
    bg: "bg-red-50 dark:bg-red-950",
    text: "text-red-800 dark:text-red-200",
    Icon: AlertTriangle,
    iconClassName: "text-red-600",
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
          <StatusIcon className={`h-5 w-5 ${style.iconClassName}`} aria-hidden="true" />
          <div>
            <h3 className={`font-semibold text-sm ${style.text}`}>
              {SUITABILITY_STATUS_LABELS[summary.status] || summary.status}
            </h3>
            <p className="text-xs text-gray-600 dark:text-gray-400 mt-0.5">
              {summary.primaryReason}
            </p>
          </div>
        </div>
        <div className="text-right">
          <span className={`text-lg font-bold ${style.text}`}>
            {summary.overallScore}
          </span>
          <span className="text-xs text-gray-500"> /100</span>
        </div>
      </div>

      {/* Dimensions */}
      {!compact && dimensions.length > 0 && (
        <div className="border-t border-gray-200 dark:border-gray-700">
          {dimensions.map((dim, idx) => (
            <DimensionRow key={idx} dimension={dim} />
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
      ? "text-red-700 dark:text-red-300"
      : dimension.severity === "medium"
        ? "text-yellow-700 dark:text-yellow-300"
        : "text-gray-700 dark:text-gray-300";

  return (
    <div className="px-4 py-3 flex items-start gap-3 border-b border-gray-100 dark:border-gray-800 last:border-b-0">
      <DimensionIcon className="h-4 w-4 mt-0.5 text-gray-500 dark:text-gray-400" aria-hidden="true" />
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-2">
          <span className="text-sm font-medium capitalize text-gray-900 dark:text-gray-100">
            {dimension.type}
          </span>
          <span className={`text-xs font-semibold uppercase ${severityColor}`}>
            {dimension.severity.charAt(0).toUpperCase() + dimension.severity.slice(1)}
          </span>
        </div>
        <p className="text-xs text-gray-600 dark:text-gray-400 mt-0.5">
          {dimension.reason}
        </p>
        <div className="mt-1 w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1">
          <div
            className="bg-blue-500 h-1 rounded-full"
            style={{ width: `${Math.min(dimension.score, 100)}%` }}
          />
        </div>
      </div>
    </div>
  );
}

export default SuitabilityCard;
