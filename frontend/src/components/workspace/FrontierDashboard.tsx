import React from 'react';

interface FrontierDashboardProps {
  packetId?: string;
  sentiment?: number;
  isAnxious?: boolean;
  ghostActive?: boolean;
  intelHits?: any[];
  logicRationale?: any;
}

export const FrontierDashboard: React.FC<FrontierDashboardProps> = ({
  packetId = "PK-9912",
  sentiment = 0.82,
  isAnxious = false,
  ghostActive = true,
  intelHits = [],
  logicRationale = "Autonomic trigger based on 'visa_delay' federated risk and high-value traveler status."
}) => {
  return (
    <div className="bento-grid animate-fade-in">
      {/* 1. Ghost Concierge Status */}
      <div className="bento-item">
        <div>
          <h3 className="text-ui-xs font-mono text-tertiary mb-1 uppercase tracking-widest">Ghost Concierge</h3>
          <p className="text-ui-2xl font-bold">{ghostActive ? 'ACTIVE' : 'IDLE'}</p>
        </div>
        <div className="flex items-center gap-2 mt-4 text-ui-xs text-secondary">
          <div className={`w-2 h-2 rounded-full ${ghostActive ? 'bg-accent-green animate-pulse' : 'bg-muted'}`} />
          <span>Workflow: GHOST-SEQ-004-X</span>
        </div>
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
            style={{ width: `${sentiment * 100}%` }}
          />
        </div>
      </div>

      {/* 3. Intelligence Feed */}
      <div className="bento-item col-span-1 md:col-span-2">
        <h3 className="text-ui-xs font-mono text-tertiary mb-2 uppercase tracking-widest">Federated Intelligence Pool</h3>
        <div className="space-y-3">
          {intelHits.length > 0 ? intelHits.map((hit, i) => (
            <div key={i} className="flex gap-3 items-start p-2 bg-lg-glass-bg rounded-lg border border-lg-glass-border">
              <div className="p-1 bg-accent-amber/20 rounded">
                <svg className="w-4 h-4 text-accent-amber" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <div>
                <p className="text-ui-sm font-medium">{hit.message || hit.type}</p>
                <p className="text-ui-xs text-muted">Source: Federated Node #412</p>
              </div>
            </div>
          )) : (
            <p className="text-ui-sm text-secondary italic">No active risks detected in this sector.</p>
          )}
        </div>
      </div>

      {/* 4. Trust Anchor (Decision Logic) */}
      <div className="trust-anchor col-span-1 md:col-span-3">
        <div className="flex justify-between items-center mb-2">
          <h3 className="text-ui-sm font-bold flex items-center gap-2">
            <svg className="w-4 h-4 text-accent-blue" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
            Trust Anchor
          </h3>
          <span className="text-ui-xs font-mono bg-accent-blue/10 text-accent-blue px-2 py-0.5 rounded">AUTHENTICATED LOGIC</span>
        </div>
        <p className="text-ui-sm text-secondary">
          Waypoint OS has analyzed 412 variables including traveler loyalty, real-time FX, and federated risk pools to arrive at this strategy.
        </p>
        <div className="trust-anchor-logic">
          <p className="font-bold mb-1">RATIONALE_DUMP:</p>
          <p>
            {typeof logicRationale === 'string' 
              ? logicRationale 
              : (logicRationale?.frontier || logicRationale?.feasibility || JSON.stringify(logicRationale) || 'No specific rationale provided.')}
          </p>
        </div>
      </div>
    </div>
  );
};
