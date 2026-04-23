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
        return `${event.flag} suppressed`;
      case 'downgrade':
        return `${event.flag} downgraded from ${event.original_severity?.toUpperCase()} to ${event.new_severity?.toUpperCase()}`;
      case 'acknowledge':
        return `${event.flag} acknowledged`;
      default:
        return event.action;
    }
  };

  const getIcon = () => {
    switch (event.action) {
      case 'suppress':
        return <AlertCircle className="h-4 w-4 text-[#da3633]" />;
      case 'downgrade':
        return <TrendingDown className="h-4 w-4 text-[#fb8500]" />;
      case 'acknowledge':
        return <CheckCircle2 className="h-4 w-4 text-[#3fb950]" />;
      default:
        return <AlertCircle className="h-4 w-4 text-[#8b949e]" />;
    }
  };

  return (
    <div className="flex gap-4 py-4 border-b border-[#30363d] last:border-0">
      <div className="flex flex-col items-center gap-2">
        {getIcon()}
        <div className="w-px h-full bg-[#30363d]" />
      </div>
      <div className="flex-1 pt-1">
        <div className="flex items-center gap-2">
          <span className="text-xs text-[#8b949e] font-mono">{time}</span>
          <span className="text-sm font-medium text-[#e6edf3]">Override</span>
        </div>
        <p className="text-sm text-[#c9d1d9] mt-1">{getActionLabel()}</p>
        <p className="text-xs text-[#8b949e] mt-2">
          Reason: {event.reason}
        </p>
        <p className="text-xs text-[#6e7681] mt-1">
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
