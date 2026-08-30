'use client';

import React, { useState } from 'react';
import {
  TrendingUp,
  DollarSign,
  FileCheck,
  ShieldCheck,
  Sparkles,
  Percent,
  Sliders,
  CheckCircle2,
  Mail,
  Zap,
} from 'lucide-react';

type NegSubTab = 'bargaining' | 'margins' | 'waivers';

export function NegotiationPanel() {
  const [activeSubTab, setActiveSubTab] = useState<NegSubTab>('margins');

  // Margin Optimizer state
  const [netCost, setNetCost] = useState<number>(4500);
  const [leadTimeDays, setLeadTimeDays] = useState<number>(4);
  const [isPeak, setIsPeak] = useState<boolean>(true);
  const [sensitivity, setSensitivity] = useState<number>(0.2); // Luxury / inelastic
  const [marginResult, setMarginResult] = useState<Record<string, any> | null>(null);

  // Bargaining State
  const [supplierName, setSupplierName] = useState('Bali Luxury DMCs');
  const [initialQuote, setInitialQuote] = useState<number>(8000);
  const [targetBudget, setTargetBudget] = useState<number>(7000);
  const [negotiationRounds, setNegotiationRounds] = useState<Array<Record<string, any>>>([
    {
      round: 1,
      actor: 'Waypoint AI Negotiator',
      offer: 7360,
      note: 'Volume leverage applied (Platinum Tier: $500k annual volume)',
      status: 'Countered by Supplier ($7,500)',
    },
    {
      round: 2,
      actor: 'Waypoint AI Negotiator',
      offer: 7420,
      note: 'Split gap + requested complimentary airport transfer',
      status: 'Accepted by Supplier ✅ ($7,420 + Transfer Included)',
    },
  ]);

  // Waiver bot state
  const [waiverBookingRef, setWaiverBookingRef] = useState('BK-MARRIOTT-9921');
  const [waiverPenalty, setWaiverPenalty] = useState<number>(450);
  const [waiverLetter, setWaiverLetter] = useState<string | null>(null);

  const handleCalculateMargin = () => {
    const urgency = leadTimeDays <= 3 ? 1.35 : leadTimeDays <= 7 ? 1.20 : 1.0;
    const season = isPeak ? 1.15 : 0.95;
    const base = 0.16;
    const rawMargin = Math.max(0.10, Math.min(0.28, (base * urgency * season) - (sensitivity * 0.30)));
    const sellPrice = netCost / (1.0 - rawMargin);

    setMarginResult({
      net_cost: netCost,
      selling_price: sellPrice,
      margin_percent: Math.round(rawMargin * 1000) / 10,
      gross_profit: sellPrice - netCost,
      urgency_multiplier: urgency,
    });
  };

  const handleGenerateWaiver = () => {
    setWaiverLetter(
      `Dear Trade Relations Desk,\n\nRE: Request for Full Penalty Waiver on Booking #${waiverBookingRef}\n\nWaypoint OS accounts for over USD 600,000 in annual bookings with your group. Due to an urgent client bereavement, we kindly request a one-time goodwill waiver of the USD ${waiverPenalty} penalty. Note our recent accommodation of your 3-hour HVAC outage on June 15th (Res #49102).\n\nThank you,\nWaypoint OS Partner Operations`
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="rounded-xl border border-[#30363d] bg-[#161b22] p-5 space-y-2">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/20 text-emerald-400 border border-emerald-400/30">
              <TrendingUp className="h-4 w-4" />
            </div>
            <div>
              <h2 className="text-ui-base font-bold text-white flex items-center gap-2">
                Autonomous Negotiation & Dynamic Margin Optimizer
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 font-medium border border-emerald-500/30">
                  PER-950888 / PER-20690
                </span>
              </h2>
              <p className="text-ui-xs text-[#8b949e]">
                B2B multi-round concession bargaining, demand elasticity margin curve optimization, and automated fee waiver bots.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-[#0f1115] border border-[#30363d] text-ui-xs text-[#3fb950]">
            <Zap className="h-3.5 w-3.5" />
            <span>Volume Leverage: Platinum ($500k)</span>
          </div>
        </div>
      </div>

      {/* Sub tabs */}
      <div className="flex gap-2 p-1.5 bg-[#0f1115] rounded-xl border border-[#30363d]">
        {[
          { key: 'margins', label: 'Dynamic Take-Rate Margin Curve', icon: Percent },
          { key: 'bargaining', label: 'B2B Concession Bargaining Bot', icon: Sliders },
          { key: 'waivers', label: 'Automated Fee Waiver Bot', icon: Mail },
        ].map((tab) => {
          const Icon = tab.icon;
          const isSelected = activeSubTab === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveSubTab(tab.key as any)}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-ui-xs font-semibold transition-all ${
                isSelected
                  ? 'bg-emerald-600 text-white shadow-md'
                  : 'text-[#8b949e] hover:text-white hover:bg-[#161b22]'
              }`}
            >
              <Icon className="h-3.5 w-3.5" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Margins Tab */}
      {activeSubTab === 'margins' && (
        <div className="rounded-xl border border-[#30363d] bg-[#161b22] p-5 space-y-4">
          <h3 className="text-ui-sm font-semibold text-white flex items-center gap-2">
            <DollarSign className="h-4 w-4 text-[#3fb950]" />
            Dynamic Margin Take-Rate Calculator
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 text-ui-xs">
            <div>
              <label className="text-[#8b949e] block mb-1">Net Supplier Cost (USD)</label>
              <input
                type="number"
                value={netCost}
                onChange={(e) => setNetCost(Number(e.target.value))}
                className="w-full bg-[#0f1115] border border-[#30363d] rounded-lg p-2 text-white"
              />
            </div>
            <div>
              <label className="text-[#8b949e] block mb-1">Lead Time: <strong>{leadTimeDays} days</strong></label>
              <input
                type="range"
                min="1"
                max="90"
                value={leadTimeDays}
                onChange={(e) => setLeadTimeDays(Number(e.target.value))}
                className="w-full accent-emerald-500 mt-2"
              />
            </div>
            <div>
              <label className="text-[#8b949e] block mb-1">Client Price Sensitivity</label>
              <select
                value={sensitivity}
                onChange={(e) => setSensitivity(Number(e.target.value))}
                className="w-full bg-[#0f1115] border border-[#30363d] rounded-lg p-2 text-white"
              >
                <option value={0.1}>0.1 - Luxury / Inelastic (High margin)</option>
                <option value={0.5}>0.5 - Standard Commercial</option>
                <option value={0.9}>0.9 - Hyper-sensitive / Budget</option>
              </select>
            </div>
            <div className="flex items-center pt-5">
              <label className="flex items-center gap-2 text-white cursor-pointer">
                <input
                  type="checkbox"
                  checked={isPeak}
                  onChange={(e) => setIsPeak(e.target.checked)}
                  className="rounded border-slate-700 bg-slate-950 text-emerald-500"
                />
                <span>Peak Season Surge</span>
              </label>
            </div>
          </div>

          <button
            onClick={handleCalculateMargin}
            className="py-2 px-4 bg-[#238636] hover:bg-[#2ea043] text-white font-semibold text-ui-xs rounded-lg transition-colors flex items-center gap-2"
          >
            <Sparkles className="h-3.5 w-3.5" />
            Optimize Take-Rate Margin
          </button>

          {marginResult && (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2 text-ui-xs">
              <div className="p-3.5 rounded-lg bg-[#0f1115] border border-[#30363d]">
                <span className="text-[#8b949e]">Recommended Retail Selling Price:</span>
                <p className="text-xl font-bold text-white mt-1">USD {marginResult.selling_price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
              </div>
              <div className="p-3.5 rounded-lg bg-[#0f1115] border border-[#30363d]">
                <span className="text-[#8b949e]">Optimized Take-Rate Margin:</span>
                <p className="text-xl font-bold text-[#3fb950] mt-1">{marginResult.margin_percent}%</p>
              </div>
              <div className="p-3.5 rounded-lg bg-[#0f1115] border border-[#30363d]">
                <span className="text-[#8b949e]">Gross Profit Contribution:</span>
                <p className="text-xl font-bold text-[#58a6ff] mt-1">+USD {marginResult.gross_profit.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Bargaining Tab */}
      {activeSubTab === 'bargaining' && (
        <div className="rounded-xl border border-[#30363d] bg-[#161b22] p-5 space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="text-ui-sm font-semibold text-white flex items-center gap-2">
              <Sliders className="h-4 w-4 text-emerald-400" />
              Live Multi-Round Bargaining Log
            </h3>
            <span className="text-[11px] text-emerald-400 bg-emerald-950/40 border border-emerald-500/30 px-2 py-0.5 rounded-full font-medium">
              Autonomous Session Completed
            </span>
          </div>

          <div className="space-y-3">
            {negotiationRounds.map((r) => (
              <div key={r.round} className="p-3.5 rounded-lg bg-[#0f1115] border border-[#30363d] space-y-1.5 text-ui-xs">
                <div className="flex justify-between items-center">
                  <span className="font-semibold text-white">Round {r.round}: {r.actor}</span>
                  <span className="text-emerald-400 font-mono font-bold">Proposed: USD {r.offer.toLocaleString()}</span>
                </div>
                <p className="text-[#8b949e]">{r.note}</p>
                <div className="text-white font-medium pt-1 border-t border-slate-900">
                  Outcome: {r.status}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Waivers Tab */}
      {activeSubTab === 'waivers' && (
        <div className="rounded-xl border border-[#30363d] bg-[#161b22] p-5 space-y-4">
          <h3 className="text-ui-sm font-semibold text-white flex items-center gap-2">
            <Mail className="h-4 w-4 text-[#58a6ff]" />
            Automated Supplier Fee Waiver Request
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-ui-xs">
            <div>
              <label className="text-[#8b949e] block mb-1">Booking Reference</label>
              <input
                type="text"
                value={waiverBookingRef}
                onChange={(e) => setWaiverBookingRef(e.target.value)}
                className="w-full bg-[#0f1115] border border-[#30363d] rounded-lg p-2 text-white font-mono"
              />
            </div>
            <div>
              <label className="text-[#8b949e] block mb-1">Penalty Amount (USD)</label>
              <input
                type="number"
                value={waiverPenalty}
                onChange={(e) => setWaiverPenalty(Number(e.target.value))}
                className="w-full bg-[#0f1115] border border-[#30363d] rounded-lg p-2 text-white"
              />
            </div>
          </div>

          <button
            onClick={handleGenerateWaiver}
            className="py-2 px-4 bg-[#58a6ff] hover:bg-[#79b8ff] text-[#0d1117] font-semibold text-ui-xs rounded-lg transition-colors"
          >
            Generate Goodwill Waiver Letter
          </button>

          {waiverLetter && (
            <div className="p-4 rounded-lg bg-[#0f1115] border border-[#30363d] space-y-2 text-ui-xs font-mono text-[#c9d1d9] whitespace-pre-wrap">
              {waiverLetter}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
