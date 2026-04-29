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
 *     "stage": "override",
 *     "event_type": "override_created",
 *     "flag": "elderly_mobility_risk",
 *     "action": "downgrade",
 *     "new_severity": "high",
 *     "original_severity": "critical",
 *     "overridden_by": "agent_priya",
 *     "reason": "Client confirmed 10 treks to Himalayas"
 *   }
 * 
 * Display format:
 *   "14:32 | Override | elderly_mobility_risk downgraded from CRITICAL to HIGH | Reason: Client confirmed..."
 */

import React from 'react';
import { AlertCircle, CheckCircle2, TrendingDown } from 'lucide-react';
import { FLAG_LABELS, labelOrTitle } from '@/lib/label-maps';

interface OverrideEventDisplay {
  timestamp: string;
  flag: string;
  action: "suppress" | "downgrade" | "acknowledge";
  original_severity?: string;
  new_severity?: string;
  reason: string;
  overridden_by: string;
}

export function OverrideTimelineEvent({ event }: { event: OverrideEventDisplay }) {
  const time = new Date(event.timestamp).toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
  });

  const getActionLabel = () => {
    switch (event.action) {
      case 'suppress':
        return `${labelOrTitle(FLAG_LABELS, event.flag)} suppressed`;
      case 'downgrade':
        return `${labelOrTitle(FLAG_LABELS, event.flag)} downgraded from ${event.original_severity?.toUpperCase()} to ${event.new_severity?.toUpperCase()}`;
      case 'acknowledge':
        return `${labelOrTitle(FLAG_LABELS, event.flag)} acknowledged`;
      default:
        return event.action;
    }
  };

  const getIcon = () => {
    switch (event.action) {
      case 'suppress':
        return <AlertCircle className="h-4 w-4 text-accent-red" />;
      case 'downgrade':
        return <TrendingDown className="h-4 w-4 text-accent-orange" />;
      case 'acknowledge':
        return <CheckCircle2 className="h-4 w-4 text-accent-green" />;
      default:
        return <AlertCircle className="h-4 w-4 text-text-muted" />;
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
 * Integration notes for TimelinePanel:
 * 
 * 1. Fetch overrides for trip:
 *    const overrides = await getOverrides(tripId);
 * 
 * 2. Merge override events with timeline events
 *    by sorting on timestamp
 * 
 * 3. Filter timeline events by stage if needed
 *    but overrides should always be shown
 * 
 * 4. Render override events between other events
 *    using OverrideTimelineEvent component
 */
