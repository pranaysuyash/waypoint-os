"use client";

/**
 * Integration point for override events in TimelinePanel.
 * 
 * When the trip timeline log contains override events,
 * they should be rendered alongside stage transitions.
 * 
 * Format:
 *   {
 *     "timestamp": "2026-04-22T14:32:00Z",
 *     "flag": "elderly_mobility_risk",
 *     "action": "downgrade",
 *     "new_severity": "high",
 *     "original_severity": "critical",
 *     "overridden_by": "agent_priya",
 *     "reason": "Client confirmed 10 treks to Himalayas"
 *   }
 * 
 * Display format:
 *   "14:32 | Override | elderly_mobility_risk downgraded from CRITICAL to HIGH | Reason: Client confirmed…"
 */

import React from 'react';
import { AlertCircle, CheckCircle2, TrendingDown } from 'lucide-react';
import { FLAG_LABELS, labelOrTitle } from '@/lib/label-maps';
import type { OverrideData } from '@/types/spine';

const VALID_ACTIONS = new Set(["suppress", "downgrade", "acknowledge"]);

type OverrideAction = "suppress" | "downgrade" | "acknowledge";

export function OverrideTimelineEvent({ event }: { event: OverrideData }) {
  const time = new Date(event.created_at).toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
  });

  const action: OverrideAction = VALID_ACTIONS.has(event.action)
    ? (event.action as OverrideAction)
    : "acknowledge";

  const getActionLabel = () => {
    switch (action) {
      case 'suppress':
        return `${labelOrTitle(FLAG_LABELS, event.flag)} suppressed`;
      case 'downgrade':
        return `${labelOrTitle(FLAG_LABELS, event.flag)} downgraded from ${event.original_severity?.toUpperCase()} to ${event.new_severity?.toUpperCase()}`;
      case 'acknowledge':
        return `${labelOrTitle(FLAG_LABELS, event.flag)} acknowledged`;
    }
  };

  const getIcon = () => {
    switch (action) {
      case 'suppress':
        return <AlertCircle className="size-4 text-accent-red" />;
      case 'downgrade':
        return <TrendingDown className="size-4 text-accent-orange" />;
      case 'acknowledge':
        return <CheckCircle2 className="size-4 text-accent-green" />;
    }
  };

  return (
    <div className="flex gap-4 py-4 border-b border-border-default last:border-0">
      <div className="flex flex-col items-center gap-2">
        {getIcon()}
        <div className="w-px h-full bg-border-default" />
      </div>
      <div className="flex-1 pt-1">
        <div className="flex items-center gap-2">
          <span className="text-ui-xs text-text-muted font-mono">{time}</span>
          <span className="text-ui-sm font-medium text-text-primary">Override</span>
        </div>
        <p className="text-ui-sm text-text-rationale mt-1">{getActionLabel()}</p>
        <p className="text-ui-xs text-text-muted mt-2">
          Reason: {event.reason}
        </p>
        <p className="text-ui-xs text-text-tertiary mt-1">
          by {event.overridden_by}
        </p>
      </div>
    </div>
  );
}

/**
 * TimelinePanel integration: see TimelinePanel.tsx for merge/sort/filter logic.
 * Overrides are fetched via direct fetch() to /api/trips/{tripId}/overrides,
 * merged with timeline events sorted by timestamp, and shown regardless of
 * stage filter (overrides lack stage metadata that maps to the timeline filter).
 */
