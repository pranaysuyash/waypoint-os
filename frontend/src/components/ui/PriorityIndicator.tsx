'use client';

import { memo } from 'react';

type UrgencyLevel = 'critical' | 'high' | 'normal' | 'low';
type ImportanceLevel = 'critical' | 'high' | 'normal' | 'low';

function urgencyLabel(score: number): UrgencyLevel {
  if (score >= 80) return 'critical';
  if (score >= 60) return 'high';
  if (score >= 20) return 'normal';
  return 'low';
}

function importanceLabel(score: number): ImportanceLevel {
  if (score >= 80) return 'critical';
  if (score >= 60) return 'high';
  if (score >= 20) return 'normal';
  return 'low';
}

const COLOR_MAP: Record<string, string> = {
  critical: 'var(--accent-red)',
  high: 'var(--accent-amber)',
  normal: 'var(--accent-blue)',
  low: 'var(--text-muted)',
};

const URGENCY_TEXT: Record<UrgencyLevel, string> = {
  critical: 'CRITICAL',
  high: 'HIGH',
  normal: 'NORM',
  low: 'LOW',
};

const IMPORTANCE_TEXT: Record<ImportanceLevel, string> = {
  critical: 'KEY',
  high: 'HIGH',
  normal: 'NORM',
  low: 'LOW',
};

interface PriorityIndicatorProps {
  urgency: number;
  importance: number;
  priorityLabel: 'critical' | 'high' | 'medium' | 'low';
  variant?: 'dual-badge' | 'dot-only' | 'compact';
  showLabels?: boolean;
  size?: 'sm' | 'md';
  className?: string;
}

export const PriorityIndicator = memo(function PriorityIndicator({
  urgency,
  importance,
  priorityLabel,
  variant = 'dual-badge',
  showLabels = false,
  size = 'sm',
  className = '',
}: PriorityIndicatorProps) {
  const uLevel = urgencyLabel(urgency);
  const iLevel = importanceLabel(importance);
  const uColor = COLOR_MAP[uLevel];
  const iColor = COLOR_MAP[iLevel];
  const dotSize = size === 'sm' ? 'size-2' : 'size-2.5';
  const textSize = size === 'sm' ? 'text-[10px]' : 'text-[12px]';

  if (variant === 'compact') {
    const highLabel = priorityLabel === 'critical' ? 'CRIT' : priorityLabel.toUpperCase().slice(0, 4);
    const compactColor = COLOR_MAP[priorityLabel === 'low' ? 'low' : priorityLabel === 'medium' ? 'normal' : priorityLabel];
    return (
      <span
        className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 font-semibold uppercase tracking-wider ${textSize} ${className}`}
        style={{
          color: compactColor,
          background: `${compactColor}15`,
          border: `1px solid ${compactColor}40`,
        }}
        role="status"
        aria-label={`Priority: ${priorityLabel}`}
      >
        {highLabel}
      </span>
    );
  }

  if (variant === 'dot-only') {
    return (
      <span className={`inline-flex items-center gap-1.5 ${textSize} ${className}`} role="status" aria-label={`Urgency: ${uLevel}, Importance: ${iLevel}`}>
        <span className={`inline-block rounded-full ${dotSize} shrink-0`} style={{ backgroundColor: uColor }} aria-hidden="true" />
        <span className="font-semibold text-[#e6edf3] tracking-wide uppercase">{priorityLabel === 'critical' ? 'CRIT' : priorityLabel.toUpperCase().slice(0, 4)}</span>
      </span>
    );
  }

  return (
    <span className={`inline-flex items-center gap-2 ${textSize} ${className}`} role="status" aria-label={`Urgency: ${uLevel}, Importance: ${iLevel}`}>
      <span className="inline-flex items-center gap-1">
        <span className={`inline-block rounded-full ${dotSize} shrink-0`} style={{ backgroundColor: uColor }} aria-hidden="true" />
        {showLabels && <span className="font-semibold" style={{ color: uColor }}>{URGENCY_TEXT[uLevel]}</span>}
      </span>
      <span className="inline-flex items-center gap-1">
        <span className={`inline-block ${dotSize} shrink-0`} style={{
          width: dotSize === 'size-2' ? '0.5rem' : '0.625rem',
          height: dotSize === 'size-2' ? '0.5rem' : '0.625rem',
          border: `2px solid ${iColor}`,
          borderRadius: '2px',
          backgroundColor: 'transparent',
        }} aria-hidden="true" />
        {showLabels && <span className="font-semibold" style={{ color: iColor }}>{IMPORTANCE_TEXT[iLevel]}</span>}
      </span>
    </span>
  );
});

export default PriorityIndicator;
