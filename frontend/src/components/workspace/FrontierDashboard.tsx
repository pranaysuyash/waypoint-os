import React from 'react';
import { useWorkbenchStore } from '@/stores/workbench';

interface FrontierResult {
  ghost_triggered?: boolean;
  ghost_workflow_id?: string;
  sentiment_score?: number;
  anxiety_alert?: boolean;
  intelligence_hits?: Array<{ message?: string; type?: string; source?: string; severity?: string }>;
  specialty_knowledge?: Array<{ topic?: string; detail?: string }>;
  mitigation_applied?: boolean;
  requires_manual_audit?: boolean;
  audit_reason?: string;
  negotiation_active?: boolean;
  negotiation_logs?: Array<{ step?: string; outcome?: string }>;
}

interface FrontierDashboardProps {
  /** Fallback packet ID - used when no store data available */
  packetId?: string;
}

export const FrontierDashboard: React.FC<FrontierDashboardProps> = ({
  packetId,
}) => {
  const resultFrontier = useWorkbenchStore((s) => s.result_frontier) as FrontierResult | null;
  const resultPacket = useWorkbenchStore((s) => s.result_packet) as { packet_id?: string } | null;

  // Derive from store, with null-safe defaults
  const frontier = resultFrontier ?? {};
  const ghostActive = frontier.ghost_triggered ?? false;
  const sentiment = frontier.sentiment_score ?? 0.5;
  const isAnxious = frontier.anxiety_alert ?? false;
  const intelHits = frontier.intelligence_hits ?? [];
  const requiresAudit = frontier.requires_manual_audit ?? false;
  const mitigationApplied = frontier.mitigation_applied ?? false;
  const negotiationActive = frontier.negotiation_active ?? false;
  const activePacketId = packetId ?? resultPacket?.packet_id ?? '-';

  const hasRealData = resultFrontier !== null && resultFrontier !== undefined;

  return (
    <div className="bento-grid animate-fade-in">
      {/* 1. Ghost Concierge Status */}
      <div className="bento-item">
        <div>
          <h3 className="text-ui-xs font-mono text-tertiary mb-1 uppercase tracking-widest">Ghost Concierge</h3>
          <p className="text-ui-2xl font-bold">{ghostActive ? 'ACTIVE' : 'IDLE'}</p>
        </div>
        <div className="flex items-center gap-2 mt-4 text-ui-xs text-secondary">
          <div className={`size-2 rounded-full ${ghostActive ? 'bg-accent-green animate-pulse' : 'bg-muted'}`} />
          <span>
            {ghostActive && frontier.ghost_workflow_id
              ? `Workflow: ${frontier.ghost_workflow_id}`
              : ghostActive
                ? 'Ghost workflow active'
                : 'No ghost workflow triggered'}
          </span>
        </div>
        {frontier.ghost_workflow_id && (
          <p className="text-ui-xs text-muted mt-1 font-mono">Packet: {activePacketId}</p>
        )}
      </div>

      {/* 2. Sentiment Meter */}
      <div className={`bento-item ${isAnxious ? 'sentiment-glow-anxious' : 'sentiment-glow-calm'}`}>
        <div>
          <h3 className="text-ui-xs font-mono text-tertiary mb-1 uppercase tracking-widest">Traveler Sentiment</h3>
          <div className="flex items-center gap-2">
            <p className="text-ui-2xl font-bold">{(sentiment * 100).toFixed(0)}%</p>
            <span className={`text-ui-xs font-bold uppercase tracking-wider ${isAnxious ? 'text-accent-red' : 'text-accent-green'}`}>
              {isAnxious ? 'ANXIOUS' : 'STABLE'}
            </span>
          </div>
        </div>
        <div className="w-full bg-bg-canvas h-1 rounded-full mt-4 overflow-hidden">
          <div
            className={`h-full transition-all duration-1000 ${isAnxious ? 'bg-accent-red' : 'bg-accent-green'}`}
            style={{ width: `${Math.max(0, Math.min(100, sentiment * 100))}%` }}
          />
        </div>
        {!hasRealData && (
          <p className="text-ui-xs text-muted mt-2 italic">No frontier data - run a pipeline to populate</p>
        )}
      </div>

      {/* 3. Intelligence Feed */}
      <div className="bento-item col-span-1 md:col-span-2">
        <h3 className="text-ui-xs font-mono text-tertiary mb-2 uppercase tracking-widest">Federated Intelligence Pool</h3>
        <div className="space-y-3">
          {intelHits.length > 0 ? intelHits.map((hit) => (
            <div key={`hit-${hit.type || hit.severity}-${(hit.message || '').slice(0, 20)}`} className="flex gap-3 items-start p-2 bg-lg-glass-bg rounded-lg border border-lg-glass-border">
              <div className={`p-1 rounded ${
                hit.severity === 'critical' ? 'bg-accent-red/20' :
                hit.severity === 'high' ? 'bg-accent-amber/20' :
                'bg-accent-blue/20'
              }`}>
                <svg className={`size-4 ${
                  hit.severity === 'critical' ? 'text-accent-red' :
                  hit.severity === 'high' ? 'text-accent-amber' :
                  'text-accent-blue'
                }`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <div>
                <p className="text-ui-sm font-medium">{hit.message || hit.type || 'Intelligence alert'}</p>
                <p className="text-ui-xs text-muted">{hit.source ? `Source: ${hit.source}` : 'Source: Federated Intelligence'}</p>
              </div>
            </div>
          )) : (
            <p className="text-ui-sm text-secondary italic">
              {hasRealData ? 'No active risks detected in this sector.' : 'Run a pipeline to see federated intelligence.'}
            </p>
          )}
        </div>
      </div>

      {/* 4. Status Flags */}
      <div className="bento-item">
        <h3 className="text-ui-xs font-mono text-tertiary mb-2 uppercase tracking-widest">Status Flags</h3>
        <div className="space-y-2">
          <div className="flex items-center justify-between text-ui-sm">
            <span>Mitigation Applied</span>
            <span className={mitigationApplied ? 'text-accent-green font-bold' : 'text-muted'}>{mitigationApplied ? 'YES' : 'NO'}</span>
          </div>
          <div className="flex items-center justify-between text-ui-sm">
            <span>Manual Audit Required</span>
            <span className={requiresAudit ? 'text-accent-red font-bold' : 'text-muted'}>{requiresAudit ? 'YES' : 'NO'}</span>
          </div>
          <div className="flex items-center justify-between text-ui-sm">
            <span>Negotiation Active</span>
            <span className={negotiationActive ? 'text-accent-amber font-bold' : 'text-muted'}>{negotiationActive ? 'YES' : 'NO'}</span>
          </div>
        </div>
        {requiresAudit && frontier.audit_reason && (
          <p className="text-ui-xs text-accent-red mt-2">Reason: {frontier.audit_reason}</p>
        )}
      </div>

      {/* 5. Trust Anchor (Decision Logic) */}
      <div className="trust-anchor col-span-1 md:col-span-3">
        <div className="flex justify-between items-center mb-2">
	          <h3 className="text-ui-sm font-semibold flex items-center gap-2">
            <svg className="size-4 text-accent-blue" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
            Trust Anchor
          </h3>
          <span className={`text-ui-xs font-mono px-2 py-0.5 rounded ${
            hasRealData ? 'bg-accent-blue/10 text-accent-blue' : 'bg-muted/20 text-muted'
          }`}>
            {hasRealData ? 'LIVE DATA' : 'NO DATA'}
          </span>
        </div>
        <p className="text-ui-sm text-secondary">
          {hasRealData
            ? `Waypoint OS frontier analysis for packet ${activePacketId}. Sentiment: ${(sentiment * 100).toFixed(0)}%. ${ghostActive ? 'Ghost concierge triggered.' : ''} ${intelHits.length} intelligence hit(s).`
            : 'Run a pipeline to see frontier analysis, sentiment scoring, and federated intelligence.'}
        </p>
      </div>
    </div>
  );
};
