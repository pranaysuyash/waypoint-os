'use client';

import React, { useState } from 'react';
import { Users, Scale, CreditCard } from 'lucide-react';
import SimulatedBadge from '@/components/ui/SimulatedBadge';

/**
 * GM-01 honesty fix: consensus scores, split shares, and "payment links" are
 * hardcoded sample values. The real deterministic Pareto engine is not wired
 * to this surface, and no payment processor exists behind the links.
 */

type GrpSubTab = 'consensus' | 'ledger';

export default function GroupParetoPanel() {
  const [activeTab, setActiveTab] = useState<GrpSubTab>('consensus');

  return (
    <div className="space-y-6">
      <div className="flex justify-end">
        <SimulatedBadge label="Sample data" />
      </div>
      <div className="flex items-center gap-2 border-b border-border pb-3">
        <button
          onClick={() => setActiveTab('consensus')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold tracking-wide transition-all ${
            activeTab === 'consensus' ? 'bg-primary text-primary-foreground shadow-sm' : 'bg-muted text-muted-foreground hover:bg-accent'
          }`}
        >
          <Scale className="h-3.5 w-3.5" />
          Harmonic Pareto Consensus Solver
        </button>
        <button
          onClick={() => setActiveTab('ledger')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold tracking-wide transition-all ${
            activeTab === 'ledger' ? 'bg-primary text-primary-foreground shadow-sm' : 'bg-muted text-muted-foreground hover:bg-accent'
          }`}
        >
          <CreditCard className="h-3.5 w-3.5" />
          Itemized Split-Payment Ledger
        </button>
      </div>

      {activeTab === 'consensus' && (
        <div className="p-4 rounded-xl border border-border bg-card space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-semibold text-foreground flex items-center gap-2">
              <Scale className="h-4 w-4 text-primary" />
              Harmonic Mean Dissatisfaction Solver (3 Travelers)
            </h4>
            <span className="text-[10px] font-mono bg-emerald-500/10 text-emerald-500 px-2 py-0.5 rounded">ZERO TYRANNY OF MAJORITY</span>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="p-3.5 rounded-xl border border-emerald-500/30 bg-emerald-500/5 space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-foreground">Option 1: Cultural Explorer</span>
                <span className="px-2 py-0.5 bg-emerald-500 text-white rounded font-mono text-[10px] font-bold">BEST CONSENSUS</span>
              </div>
              <p className="text-[11px] text-muted-foreground">$2,200 / person · Moderate Pace · Culture & Culinary</p>
              <div className="pt-2 border-t border-emerald-500/10 flex items-center justify-between font-mono text-[11px]">
                <span>Harmonic Score: <strong className="text-emerald-500 font-bold">0.82 / 1.0</strong></span>
                <span className="text-muted-foreground">Min Satisfaction: 0.78</span>
              </div>
            </div>

            <div className="p-3.5 rounded-xl border border-border bg-muted/20 space-y-2 opacity-75">
              <div className="flex items-center justify-between">
                <span className="font-bold text-foreground">Option 2: High-End Extreme Adventure</span>
                <span className="px-2 py-0.5 bg-red-500/10 text-red-500 rounded font-mono text-[10px] font-bold">DIVISIVE</span>
              </div>
              <p className="text-[11px] text-muted-foreground">$4,000 / person · Fast Pace · Adventure Only</p>
              <div className="pt-2 border-t border-border flex items-center justify-between font-mono text-[11px]">
                <span>Harmonic Score: <strong className="text-red-500 font-bold">0.34 / 1.0</strong></span>
                <span className="text-red-500 font-semibold">Alice Excluded (0.15)</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'ledger' && (
        <div className="p-4 rounded-xl border border-border bg-card space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-semibold text-foreground flex items-center gap-2">
              <CreditCard className="h-4 w-4 text-emerald-500" />
              Itemized Split Shares (Sample — no real payment links)
            </h4>
            <span className="text-xs font-mono text-muted-foreground">Total: $2,500.00</span>
          </div>

          <div className="space-y-2 text-xs">
            <div className="p-3 rounded-lg border border-border bg-muted/30 flex items-center justify-between">
              <div>
                <span className="font-semibold text-foreground">Alice Walker</span>
                <span className="text-[10px] text-muted-foreground block">Base: $1,000 + Private Room Supp: $350</span>
              </div>
              <div className="text-right">
                <span className="font-mono font-bold text-foreground text-sm block">$1,350.00</span>
                <span className="text-[10px] font-mono text-amber-500">PENDING LINK</span>
              </div>
            </div>

            <div className="p-3 rounded-lg border border-border bg-muted/30 flex items-center justify-between">
              <div>
                <span className="font-semibold text-foreground">Bob Jenkins</span>
                <span className="text-[10px] text-muted-foreground block">Base: $1,000 + Winery Tour Opt-In: $150</span>
              </div>
              <div className="text-right">
                <span className="font-mono font-bold text-foreground text-sm block">$1,150.00</span>
                <span className="text-[10px] font-mono text-amber-500">PENDING LINK</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
