'use client';

import React, { useState } from 'react';
import { Sparkles, CheckCircle2, Share2, RefreshCw, TriangleAlert } from 'lucide-react';
import SimulatedBadge from '@/components/ui/SimulatedBadge';

/**
 * Proposal Compiler Panel
 * Chains intake parsing, GDS/NDC air shopping, dynamic take-rate optimization,
 * and constraint verification into a compiled proposal package.
 *
 * Honesty notes (PA-25 / F-42): the compiled package is SYNTHETIC (sandbox air
 * offers plus fabricated lodging/transfer providers), so this panel is
 * compile-and-display only. The previous accept → fulfill → VCC chain was
 * removed: it targeted hardcoded sample records that 404 via the route map and
 * presented simulated booking artifacts as confirmed supplier commitments.
 * Share links are only shown when the backend actually minted a token
 * (simulated inventory blocks share minting by default).
 */

interface ProposalPackage {
  proposal_id: string;
  trip_id: string;
  title: string;
  destination: string;
  gross_customer_price_usd: number;
  net_supplier_cost_usd: number;
  gross_margin_usd: number;
  optimized_take_rate_pct: number;
  is_feasibility_passed: boolean;
  proposal_share_url: string | null;
  share_token: string | null;
  share_blocked_reason?: string | null;
  reality_tier?: string;
  provider_connected?: boolean;
  breakdown_items: Array<{ category: string; provider: string; amount_usd: number }>;
}

export default function ProposalCompilerPanel() {
  const [destination, setDestination] = useState('Paris');
  const [intakeText, setIntakeText] = useState('Looking for a bespoke 7-day luxury trip to Paris for 2 with private chauffeur airport transfers and top dining.');
  const [tripRef, setTripRef] = useState('');
  const [isCompiling, setIsCompiling] = useState(false);
  const [compileError, setCompileError] = useState<string | null>(null);
  const [proposal, setProposal] = useState<ProposalPackage | null>(null);

  const handleCompile = async () => {
    setIsCompiling(true);
    setCompileError(null);
    setProposal(null);
    try {
      const res = await fetch('/api/v1/proposal-compiler/compile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          trip_id: tripRef,
          raw_intake_text: intakeText,
          destination: destination,
          departure_date: '2026-10-15',
          return_date: '2026-10-22',
          traveler_count: 2,
          price_sensitivity: 0.1,
          peak_season: true,
        }),
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({ detail: 'Proposal compilation failed' }));
        throw new Error(errData.detail || 'Proposal compilation failed');
      }
      const data = await res.json();
      setProposal(data.proposal_package);
    } catch (err: any) {
      setCompileError(err?.message || 'Proposal compilation failed');
    } finally {
      setIsCompiling(false);
    }
  };

  return (
    <div className="p-4 rounded-xl border border-border bg-card space-y-4">
      <div className="flex items-center justify-between gap-2">
        <h4 className="text-sm font-semibold text-foreground flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-primary" />
          Proposal Compiler
        </h4>
        <div className="flex items-center gap-2 shrink-0">
          <SimulatedBadge label="Amadeus NDC sandbox & simulated inventory" />
          <span className="text-[10px] font-mono bg-primary/10 text-primary px-2 py-0.5 rounded">AUTONOMOUS PIPELINE</span>
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
          <label className="text-[11px] font-mono text-muted-foreground">Trip Reference</label>
          <input
            aria-label="Trip Reference"
            placeholder="existing trip id"
            value={tripRef}
            onChange={(e) => setTripRef(e.target.value)}
            className="w-full p-2 text-xs font-mono rounded border border-border bg-background text-foreground"
          />
          <button
            onClick={handleCompile}
            disabled={isCompiling || !tripRef.trim()}
            className="w-full mt-2 py-2 px-3 rounded-lg bg-primary text-primary-foreground text-xs font-semibold hover:bg-primary/90 flex items-center justify-center gap-1.5 transition-all"
          >
            {isCompiling ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <Sparkles className="h-3.5 w-3.5" />}
            {isCompiling ? 'Compiling Package...' : 'Compile Verified Proposal'}
          </button>
        </div>
      </div>

      {compileError && (
        <div className="p-2.5 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs">
          {compileError}
        </div>
      )}

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

          <div className="space-y-1.5 pt-1">
            {proposal.breakdown_items.map((item) => (
              <div key={item.category} className="flex items-center justify-between text-xs px-2.5 py-1.5 rounded bg-background/60 border border-border">
                <span className="text-muted-foreground">{item.category} · {item.provider}</span>
                <span className="font-mono font-semibold text-foreground">${item.amount_usd.toLocaleString()}</span>
              </div>
            ))}
          </div>

          <div className="pt-2 border-t border-emerald-500/10 flex items-center justify-between text-xs">
            <span className="text-muted-foreground font-mono text-[11px]">
              Preview compiled locally — no provider connected, so treat every price as an estimate.
            </span>
            {proposal.proposal_share_url && proposal.share_token ? (
              <a
                href={proposal.proposal_share_url}
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-1.5 px-3 py-1.5 bg-background border border-border text-foreground rounded text-xs font-semibold hover:bg-muted"
              >
                <Share2 className="h-3 w-3" />
                Client Link
              </a>
            ) : (
              <span className="px-3 py-1.5 rounded bg-amber-500/10 border border-amber-500/20 text-amber-500 text-[11px] font-mono">
                Share link unavailable: {proposal.share_blocked_reason ?? 'not_minted'}
              </span>
            )}
          </div>

          {/* Sample-data notice — replaces the removed compile → share → accept → fulfill → VCC chain */}
          <div className="p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-start gap-2 text-amber-500 text-xs">
            <TriangleAlert className="h-3.5 w-3.5 mt-0.5 shrink-0" />
            <span>
              Sample data notice: this package is compiled from simulated inventory (sandbox air offers
              and placeholder lodging/transfer providers). No client e-signature, booking, PNR, or
              virtual card is executed from this panel. Real fulfillment requires connected provider
              inventory and runs from a durable trip record.
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
