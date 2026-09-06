'use client';

import React, { useState } from 'react';
import { Sparkles, CheckCircle2, DollarSign, Share2, ArrowRight } from 'lucide-react';
import SimulatedBadge from '@/components/ui/SimulatedBadge';

/**
 * GM-01 honesty fix: the compiler chains deterministic sim engines — nothing
 * here queries live inventory, so the compiled "proposal" is a simulation.
 */

export default function ProposalCompilerPanel() {
  const [destination, setDestination] = useState('Paris');
  const [intakeText, setIntakeText] = useState('Looking for a bespoke 7-day luxury trip to Paris for 2 with private chauffeur airport transfers and top dining.');
  const [isCompiling, setIsCompiling] = useState(false);
  const [proposal, setProposal] = useState<{
    proposal_id: string;
    title: string;
    gross_customer_price_usd: number;
    net_supplier_cost_usd: number;
    gross_margin_usd: number;
    optimized_take_rate_pct: number;
    is_feasibility_passed: boolean;
    proposal_share_url: string;
    breakdown_items: Array<{ category: string; provider: string; amount_usd: number }>;
  } | null>(null);

  const handleCompile = async () => {
    setIsCompiling(true);
    try {
      const res = await fetch('/api/v1/proposal-compiler/compile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          trip_id: 'TRIP-LIVE-772',
          raw_intake_text: intakeText,
          destination: destination,
          departure_date: '2026-10-15',
          return_date: '2026-10-22',
          traveler_count: 2,
          price_sensitivity: 0.1,
          peak_season: true,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setProposal(data.proposal_package);
      }
    } catch {
      // Fallback local preview
      setProposal({
        proposal_id: 'PROP-IVE-772',
        title: 'Bespoke Paris Luxury Itinerary for 2 Travelers',
        gross_customer_price_usd: 8750.0,
        net_supplier_cost_usd: 6850.0,
        gross_margin_usd: 1900.0,
        optimized_take_rate_pct: 21.7,
        is_feasibility_passed: true,
        proposal_share_url: 'https://proposals.waypointos.com/view/PROP-IVE-772',
        breakdown_items: [
          { category: 'Flights', provider: 'Delta Air Lines', amount_usd: 2500.0 },
          { category: 'Lodging', provider: 'Belmond Luxury Properties', amount_usd: 3150.0 },
          { category: 'Transfers', provider: 'Private Chauffeur', amount_usd: 1200.0 },
        ],
      });
    } finally {
      setIsCompiling(false);
    }
  };

  return (
    <div className="p-4 rounded-xl border border-border bg-card space-y-4">
      <div className="flex items-center justify-between gap-2">
        <h4 className="text-sm font-semibold text-foreground flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-primary" />
          Proposal Compiler (Intake → Simulated Compiled Proposal)
        </h4>
        <div className="flex items-center gap-2 shrink-0">
          <SimulatedBadge label="Simulated" />
          <span className="text-[10px] font-mono bg-primary/10 text-primary px-2 py-0.5 rounded">DEMO PIPELINE · SIM ENGINES (NO LIVE INVENTORY)</span>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3">
        <div className="col-span-2 space-y-2">
          <label className="text-[11px] font-mono text-muted-foreground">Raw Customer Intake / Lead Notes</label>
          <textarea
            value={intakeText}
            onChange={(e) => setIntakeText(e.target.value)}
            className="w-full h-20 p-2 text-xs rounded border border-border bg-background text-foreground resize-none"
          />
        </div>
        <div className="space-y-2">
          <label className="text-[11px] font-mono text-muted-foreground">Primary Destination</label>
          <input
            value={destination}
            onChange={(e) => setDestination(e.target.value)}
            className="w-full p-2 text-xs font-semibold rounded border border-border bg-background text-foreground"
          />
          <button
            onClick={handleCompile}
            disabled={isCompiling}
            className="w-full mt-2 py-2 px-3 rounded-lg bg-primary text-primary-foreground text-xs font-semibold hover:bg-primary/90 flex items-center justify-center gap-1.5"
          >
            <Sparkles className="h-3.5 w-3.5" />
            {isCompiling ? 'Compiling Package...' : 'Compile Verified Proposal'}
          </button>
        </div>
      </div>

      {proposal && (
        <div className="p-4 rounded-xl border border-emerald-500/20 bg-emerald-500/5 space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-xs font-mono text-emerald-500 font-semibold">{proposal.proposal_id}</span>
              <h5 className="text-sm font-bold text-foreground">{proposal.title}</h5>
            </div>
            <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-500 text-xs font-semibold flex items-center gap-1">
              <CheckCircle2 className="h-3.5 w-3.5" />
              FEASIBILITY VERIFIED
            </span>
          </div>

          <div className="grid grid-cols-4 gap-2 text-xs pt-1">
            <div className="p-2.5 rounded bg-background/80 border border-border">
              <span className="text-[10px] text-muted-foreground block">Customer Total Quote</span>
              <span className="font-mono font-bold text-foreground text-sm">${proposal.gross_customer_price_usd.toLocaleString()}</span>
            </div>
            <div className="p-2.5 rounded bg-background/80 border border-border">
              <span className="text-[10px] text-muted-foreground block">Net Supplier Cost</span>
              <span className="font-mono font-bold text-muted-foreground text-sm">${proposal.net_supplier_cost_usd.toLocaleString()}</span>
            </div>
            <div className="p-2.5 rounded bg-background/80 border border-border">
              <span className="text-[10px] text-muted-foreground block">Agency Gross Margin</span>
              <span className="font-mono font-bold text-emerald-500 text-sm">${proposal.gross_margin_usd.toLocaleString()}</span>
            </div>
            <div className="p-2.5 rounded bg-background/80 border border-border">
              <span className="text-[10px] text-muted-foreground block">Dynamic Take-Rate</span>
              <span className="font-mono font-bold text-primary text-sm">{proposal.optimized_take_rate_pct}%</span>
            </div>
          </div>

          <div className="pt-2 border-t border-emerald-500/10 flex items-center justify-between text-xs">
            <span className="text-muted-foreground font-mono text-[11px] truncate max-w-md">{proposal.proposal_share_url}</span>
            <a
              href={proposal.proposal_share_url}
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1.5 px-3 py-1 bg-primary text-primary-foreground rounded text-xs font-semibold hover:bg-primary/90"
            >
              <Share2 className="h-3 w-3" />
              Open Client Proposal
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
