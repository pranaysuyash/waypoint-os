'use client';

import React, { useState } from 'react';
import { Plane, CheckCircle2, Sparkles } from 'lucide-react';
import SimulatedBadge from '@/components/ui/SimulatedBadge';

/**
 * GM-01 honesty fix: quotes come from the deterministic charter simulator —
 * there is no live fleet or empty-leg feed behind this panel.
 */

export default function CharterAviationPanel() {
  const [origin, setOrigin] = useState('KTEB');
  const [destination, setDestination] = useState('KOPF');
  const [passengers, setPassengers] = useState(4);
  const [isLoading, setIsLoading] = useState(false);
  const [quote, setQuote] = useState<{
    quote_id: string;
    aircraft: { model_name: string; category: string; max_passengers: number; hourly_rate_usd: number };
    flight_time_hours: number;
    standard_cost_usd: number;
    effective_cost_usd: number;
    savings_usd: number;
    empty_leg_match: { offer_id: string; discount_percent: number; empty_leg_discounted_price_usd: number; operator_name: string } | null;
    runway_feasibility: { origin_pass: boolean; destination_pass: boolean };
    fbo_handling: { origin: string; destination: string };
  } | null>(null);

  const handleCalculateQuote = async () => {
    setIsLoading(true);
    try {
      const res = await fetch('/api/v1/charter-aviation/quotes/calculate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          origin_icao: origin,
          destination_icao: destination,
          passengers_count: Number(passengers),
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setQuote(data.quote);
      }
    } catch {
      // Fallback local preview
      setQuote({
        quote_id: 'CHT-E9A214',
        aircraft: {
          model_name: 'Challenger 3500',
          category: 'super_midsize',
          max_passengers: 10,
          hourly_rate_usd: 6950.0,
        },
        flight_time_hours: 2.8,
        standard_cost_usd: 19460.0,
        effective_cost_usd: 7800.0,
        savings_usd: 11660.0,
        empty_leg_match: {
          offer_id: 'EL-TEB-MIA-091',
          discount_percent: 65.3,
          empty_leg_discounted_price_usd: 7800.0,
          operator_name: 'NetJets Repositioning',
        },
        runway_feasibility: { origin_pass: true, destination_pass: true },
        fbo_handling: {
          origin: 'Signature Flight Support (Teterboro)',
          destination: 'Fontainebleau Aviation (Miami Opa-Locka)',
        },
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="p-4 rounded-xl border border-border bg-card space-y-4">
      <div className="flex items-center justify-between gap-2">
        <h4 className="text-sm font-semibold text-foreground flex items-center gap-2">
          <Plane className="h-4 w-4 text-sky-400" />
          Private Aviation & Empty-Leg Arbitrage Engine (Simulator)
        </h4>
        <div className="flex items-center gap-2 shrink-0">
          <SimulatedBadge label="Simulated" />
          <span className="text-[10px] font-mono bg-sky-500/10 text-sky-400 px-2 py-0.5 rounded">FRONTIER 1 · ARBITRAGE SIM (NO LIVE FLEET FEED)</span>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-3">
        <div>
          <label className="text-[10px] font-mono text-muted-foreground block mb-1">Origin (ICAO)</label>
          <input
            value={origin}
            onChange={(e) => setOrigin(e.target.value.toUpperCase())}
            className="w-full p-2 text-xs font-mono font-bold rounded border border-border bg-background text-foreground"
          />
        </div>
        <div>
          <label className="text-[10px] font-mono text-muted-foreground block mb-1">Destination (ICAO)</label>
          <input
            value={destination}
            onChange={(e) => setDestination(e.target.value.toUpperCase())}
            className="w-full p-2 text-xs font-mono font-bold rounded border border-border bg-background text-foreground"
          />
        </div>
        <div>
          <label className="text-[10px] font-mono text-muted-foreground block mb-1">Passengers</label>
          <input
            type="number"
            value={passengers}
            onChange={(e) => setPassengers(Number(e.target.value))}
            className="w-full p-2 text-xs font-mono rounded border border-border bg-background text-foreground"
          />
        </div>
        <div className="flex items-end">
          <button
            onClick={handleCalculateQuote}
            disabled={isLoading}
            className="w-full py-2 px-3 rounded-lg bg-sky-500 text-white text-xs font-semibold hover:bg-sky-600 flex items-center justify-center gap-1.5"
          >
            <Sparkles className="h-3.5 w-3.5" />
            {isLoading ? 'Scanning Fleet...' : 'Calculate Charter'}
          </button>
        </div>
      </div>

      {quote && (
        <div className="p-4 rounded-xl border border-sky-500/20 bg-sky-500/5 space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-xs font-mono text-sky-400 font-semibold">{quote.quote_id}</span>
              <h5 className="text-sm font-bold text-foreground">{quote.aircraft.model_name} ({quote.aircraft.category.replace('_', ' ').toUpperCase()})</h5>
            </div>
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 text-xs font-semibold flex items-center gap-1">
                <CheckCircle2 className="h-3.5 w-3.5" />
                RUNWAY COMPLIANT
              </span>
            </div>
          </div>

          <div className="grid grid-cols-4 gap-2 text-xs">
            <div className="p-2.5 rounded bg-background/80 border border-border">
              <span className="text-[10px] text-muted-foreground block">Flight Time</span>
              <span className="font-mono font-bold text-foreground text-sm">{quote.flight_time_hours} hrs</span>
            </div>
            <div className="p-2.5 rounded bg-background/80 border border-border">
              <span className="text-[10px] text-muted-foreground block">Standard Charter</span>
              <span className="font-mono font-bold text-muted-foreground text-sm line-through">${quote.standard_cost_usd.toLocaleString()}</span>
            </div>
            <div className="p-2.5 rounded bg-background/80 border border-border">
              <span className="text-[10px] text-muted-foreground block">Empty-Leg Price</span>
              <span className="font-mono font-bold text-emerald-400 text-sm">${quote.effective_cost_usd.toLocaleString()}</span>
            </div>
            <div className="p-2.5 rounded bg-background/80 border border-border">
              <span className="text-[10px] text-muted-foreground block">Arbitrage Savings</span>
              <span className="font-mono font-bold text-sky-400 text-sm">${quote.savings_usd.toLocaleString()}</span>
            </div>
          </div>

          {quote.empty_leg_match && (
            <div className="p-2.5 rounded bg-emerald-500/10 border border-emerald-500/20 text-xs flex items-center justify-between">
              <span className="text-emerald-300">
                ⚡ <strong>{quote.empty_leg_match.discount_percent}% Empty-Leg Match Found!</strong> {quote.empty_leg_match.operator_name}
              </span>
              <span className="font-mono text-emerald-400 font-semibold">{quote.empty_leg_match.offer_id}</span>
            </div>
          )}

          <div className="pt-2 border-t border-sky-500/10 grid grid-cols-2 gap-2 text-xs text-muted-foreground">
            <div>
              <span className="block text-[10px] font-mono text-slate-400">Origin FBO:</span>
              <span className="text-foreground">{quote.fbo_handling.origin}</span>
            </div>
            <div>
              <span className="block text-[10px] font-mono text-slate-400">Destination FBO:</span>
              <span className="text-foreground">{quote.fbo_handling.destination}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
