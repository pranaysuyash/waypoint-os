'use client';

import React, { useState } from 'react';
import { 
  ShieldCheck, 
  Plane, 
  DollarSign, 
  Users, 
  Activity, 
  Sparkles,
  AlertCircle,
  CheckCircle2,
  RefreshCw,
  Clock,
  Send,
  Sliders,
  TrendingUp,
  AlertTriangle,
  Layers,
} from 'lucide-react';
import { DistributionPanel } from './DistributionPanel';
import { NegotiationPanel } from './NegotiationPanel';
import { CrisisEvacuationPanel } from './CrisisEvacuationPanel';

type CouncilViewType = 'all' | 'distribution' | 'negotiation' | 'crisis';

export default function PersonaCouncilPanel() {
  const [activeCouncilView, setActiveCouncilView] = useState<CouncilViewType>('all');
  // 1. Passenger Rights State
  const [prFlightNum, setPrFlightNum] = useState('BA112');
  const [prDistance, setPrDistance] = useState(5500);
  const [prDelayMins, setPrDelayMins] = useState(210);
  const [prIsCancelled, setPrIsCancelled] = useState(false);
  const [prExtraordinary, setPrExtraordinary] = useState(false);
  const [prResult, setPrResult] = useState<any>(null);
  const [prLoading, setPrLoading] = useState(false);

  // 2. FX Currency State
  const [fxAmount, setFxAmount] = useState(1500);
  const [fxFrom, setFxFrom] = useState('EUR');
  const [fxTo, setFxTo] = useState('USD');
  const [fxBuffer, setFxBuffer] = useState(2.0);
  const [fxResult, setFxResult] = useState<any>(null);
  const [fxLoading, setFxLoading] = useState(false);

  // 3. Counterfactual Replanner State
  const [cftNode, setCftNode] = useState('fl_jfk_lhr');
  const [cftDelay, setCftDelay] = useState(120);
  const [cftResult, setCftResult] = useState<any>(null);
  const [cftLoading, setCftLoading] = useState(false);

  // 4. Group Consensus State
  const [grpP1Budget, setGrpP1Budget] = useState(2000);
  const [grpP2Budget, setGrpP2Budget] = useState(3000);
  const [grpResult, setGrpResult] = useState<any>(null);
  const [grpLoading, setGrpLoading] = useState(false);

  // 5. Capability Token State
  const [tokRole, setTokRole] = useState('senior_agent');
  const [tokTripId, setTokTripId] = useState('trip_live_001');
  const [tokResult, setTokResult] = useState<any>(null);
  const [tokLoading, setTokLoading] = useState(false);

  // Evaluate Passenger Rights
  const handleEvaluateRights = async () => {
    setPrLoading(true);
    try {
      const res = await fetch('http://127.0.0.1:8000/api/v1/passenger-rights/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          trip_id: 'trip_council_demo',
          flight_number: prFlightNum,
          origin: 'LHR',
          destination: 'JFK',
          distance_km: Number(prDistance),
          delay_minutes: Number(prDelayMins),
          is_cancelled: prIsCancelled,
          is_extraordinary_circumstances: prExtraordinary,
        }),
      });
      const data = await res.json();
      setPrResult(data);
    } catch (err) {
      console.error(err);
    } finally {
      setPrLoading(false);
    }
  };

  // Convert FX
  const handleConvertFx = async () => {
    setFxLoading(true);
    try {
      const res = await fetch('http://127.0.0.1:8000/api/v1/financial-ops/convert-currency', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          amount: Number(fxAmount),
          from_currency: fxFrom,
          to_currency: fxTo,
          volatility_buffer_pct: Number(fxBuffer),
        }),
      });
      const data = await res.json();
      setFxResult(data);
    } catch (err) {
      console.error(err);
    } finally {
      setFxLoading(false);
    }
  };

  // Replan Disruption
  const handleReplanDisruption = async () => {
    setCftLoading(true);
    try {
      const res = await fetch('http://127.0.0.1:8000/api/v1/counterfactual/replan-disruption', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          trip_id: 'trip_council_demo',
          disrupted_node_id: cftNode,
          delay_minutes: Number(cftDelay),
        }),
      });
      const data = await res.json();
      setCftResult(data);
    } catch (err) {
      console.error(err);
    } finally {
      setCftLoading(false);
    }
  };

  // Calculate Group Consensus
  const handleGroupConsensus = async () => {
    setGrpLoading(true);
    try {
      const res = await fetch('http://127.0.0.1:8000/api/v1/counterfactual/group-consensus', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          trip_id: 'trip_group_demo',
          members: [
            { traveler_id: 'trav_alice', name: 'Alice', max_budget_usd: Number(grpP1Budget), pacing_preference: 'RELAXED', priority_activities: ['museum', 'dining'] },
            { traveler_id: 'trav_bob', name: 'Bob', max_budget_usd: Number(grpP2Budget), pacing_preference: 'INTENSE', priority_activities: ['hiking', 'adventure'] },
          ],
          candidate_options: [
            { option_id: 'opt_luxury', title: 'Luxury Alpine Escape', total_cost_usd: 2400.0, pacing: 'BALANCED', includes_activities: ['dining', 'hiking'] },
            { option_id: 'opt_budget', title: 'Backpacker Trek', total_cost_usd: 1200.0, pacing: 'INTENSE', includes_activities: ['hiking'] },
          ]
        }),
      });
      const data = await res.json();
      setGrpResult(data);
    } catch (err) {
      console.error(err);
    } finally {
      setGrpLoading(false);
    }
  };

  // Issue Capability Token
  const handleIssueToken = async () => {
    setTokLoading(true);
    try {
      const res = await fetch('http://127.0.0.1:8000/api/v1/boundaries/tokens/issue', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          agency_id: 'agency_waypoint_hq',
          trip_id: tokTripId,
          role: tokRole,
          scopes: ['TRIP_READ', 'TRIP_EDIT_PROPOSAL', 'PAYMENT_AUTHORIZE'],
          ttl_hours: 72,
        }),
      });
      const data = await res.json();
      setTokResult(data);
    } catch (err) {
      console.error(err);
    } finally {
      setTokLoading(false);
    }
  };

  return (
    <div className="space-y-8 p-6 max-w-7xl mx-auto">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 border border-indigo-800/40 rounded-2xl p-6 shadow-2xl text-white">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-indigo-400 font-mono text-sm tracking-wider uppercase">
              <Sparkles className="w-4 h-4" />
              11-Persona Council Command Center
            </div>
            <h1 className="text-2xl font-bold text-slate-100 mt-1">
              Autonomous Intelligence & Regulatory Governance
            </h1>
            <p className="text-slate-400 text-sm mt-1 max-w-2xl">
              Live operational controls for statutory passenger compensation, FX volatility buffers, multi-party Pareto consensus, and zero-trust capability tokens.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              All 11 Engines Nominal
            </span>
          </div>
        </div>
      </div>

      {/* Category Filter Selector */}
      <div className="flex flex-wrap gap-2 p-1.5 bg-slate-900/60 rounded-xl border border-slate-800">
        {[
          { key: 'all', label: 'All Operational Engines', icon: Layers },
          { key: 'distribution', label: 'GDS & NDC Protocol (PER-950887)', icon: Plane },
          { key: 'negotiation', label: 'Negotiation & Margins (PER-950888)', icon: TrendingUp },
          { key: 'crisis', label: 'Crisis Evacuation & Ground (PER-950889)', icon: AlertTriangle },
        ].map((t) => {
          const Icon = t.icon;
          const isSelected = activeCouncilView === t.key;
          return (
            <button
              key={t.key}
              onClick={() => setActiveCouncilView(t.key as any)}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-semibold transition-all ${
                isSelected
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-500/20'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <Icon className="h-3.5 w-3.5" />
              {t.label}
            </button>
          );
        })}
      </div>

      {/* Conditional Active Persona Cluster View */}
      {activeCouncilView === 'distribution' && <DistributionPanel />}
      {activeCouncilView === 'negotiation' && <NegotiationPanel />}
      {activeCouncilView === 'crisis' && <CrisisEvacuationPanel />}

      {/* Grid of Persona Cards (Rendered when 'all' is selected) */}
      {activeCouncilView === 'all' && (
        <>
          <div className="space-y-6">
            <DistributionPanel />
            <NegotiationPanel />
            <CrisisEvacuationPanel />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* 1. Passenger Rights Card */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 flex flex-col justify-between shadow-lg">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2 text-sky-400 font-semibold">
                <Plane className="w-5 h-5" />
                <span>Passenger Rights & Statutory Entitlements (EU261 / UK261)</span>
              </div>
              <span className="text-xs bg-sky-950 text-sky-300 border border-sky-800 px-2 py-0.5 rounded-md font-mono">
                PER-0933
              </span>
            </div>

            <div className="grid grid-cols-2 gap-3 text-sm mb-4">
              <div>
                <label className="block text-slate-400 text-xs mb-1">Flight Number</label>
                <input 
                  type="text" 
                  value={prFlightNum} 
                  onChange={(e) => setPrFlightNum(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-white text-sm focus:outline-none focus:border-sky-500" 
                />
              </div>
              <div>
                <label className="block text-slate-400 text-xs mb-1">Distance (km)</label>
                <input 
                  type="number" 
                  value={prDistance} 
                  onChange={(e) => setPrDistance(Number(e.target.value))}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-white text-sm focus:outline-none focus:border-sky-500" 
                />
              </div>
              <div>
                <label className="block text-slate-400 text-xs mb-1">Arrival Delay (Mins)</label>
                <input 
                  type="number" 
                  value={prDelayMins} 
                  onChange={(e) => setPrDelayMins(Number(e.target.value))}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-white text-sm focus:outline-none focus:border-sky-500" 
                />
              </div>
              <div className="flex items-center gap-4 pt-5">
                <label className="flex items-center gap-1.5 text-xs text-slate-300 cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={prIsCancelled} 
                    onChange={(e) => setPrIsCancelled(e.target.checked)} 
                    className="rounded bg-slate-800 border-slate-700 text-sky-500"
                  />
                  Cancelled
                </label>
                <label className="flex items-center gap-1.5 text-xs text-slate-300 cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={prExtraordinary} 
                    onChange={(e) => setPrExtraordinary(e.target.checked)} 
                    className="rounded bg-slate-800 border-slate-700 text-sky-500"
                  />
                  Extraordinary
                </label>
              </div>
            </div>

            {prResult && (
              <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 mb-4 text-xs font-mono space-y-1.5">
                <div className="flex justify-between text-slate-300">
                  <span>Statutory Entitlement:</span>
                  <span className="text-emerald-400 font-bold">{prResult.compensation_amount_eur ? `€${prResult.compensation_amount_eur}` : 'None'}</span>
                </div>
                <div className="flex justify-between text-slate-300">
                  <span>Right-to-Care Mandate:</span>
                  <span className="text-sky-400">{prResult.right_to_care_entitlements?.join(', ') || 'None'}</span>
                </div>
                <div className="text-slate-400 text-[11px] pt-1">
                  {prResult.legal_summary}
                </div>
              </div>
            )}
          </div>

          <button 
            onClick={handleEvaluateRights}
            disabled={prLoading}
            className="w-full bg-sky-600 hover:bg-sky-500 text-white font-medium py-2 rounded-xl text-sm transition flex items-center justify-center gap-2"
          >
            {prLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            Evaluate Statutory Entitlement
          </button>
        </div>

        {/* 2. FX Currency Card */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 flex flex-col justify-between shadow-lg">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2 text-emerald-400 font-semibold">
                <DollarSign className="w-5 h-5" />
                <span>Dynamic FX Volatility & Interchange Netting</span>
              </div>
              <span className="text-xs bg-emerald-950 text-emerald-300 border border-emerald-800 px-2 py-0.5 rounded-md font-mono">
                Financial Ops
              </span>
            </div>

            <div className="grid grid-cols-2 gap-3 text-sm mb-4">
              <div>
                <label className="block text-slate-400 text-xs mb-1">Supplier Amount</label>
                <input 
                  type="number" 
                  value={fxAmount} 
                  onChange={(e) => setFxAmount(Number(e.target.value))}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-white text-sm focus:outline-none focus:border-emerald-500" 
                />
              </div>
              <div>
                <label className="block text-slate-400 text-xs mb-1">From Currency</label>
                <select 
                  value={fxFrom} 
                  onChange={(e) => setFxFrom(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-white text-sm focus:outline-none focus:border-emerald-500"
                >
                  <option value="EUR">EUR (€)</option>
                  <option value="GBP">GBP (£)</option>
                  <option value="JPY">JPY (¥)</option>
                </select>
              </div>
              <div>
                <label className="block text-slate-400 text-xs mb-1">Target Currency</label>
                <input 
                  type="text" 
                  value={fxTo} 
                  disabled 
                  className="w-full bg-slate-800/50 border border-slate-700/50 rounded-lg px-3 py-1.5 text-slate-400 text-sm" 
                />
              </div>
              <div>
                <label className="block text-slate-400 text-xs mb-1">Volatility Buffer (%)</label>
                <input 
                  type="number" 
                  step="0.5"
                  value={fxBuffer} 
                  onChange={(e) => setFxBuffer(Number(e.target.value))}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-white text-sm focus:outline-none focus:border-emerald-500" 
                />
              </div>
            </div>

            {fxResult && (
              <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 mb-4 text-xs font-mono space-y-1.5">
                <div className="flex justify-between text-slate-300">
                  <span>Mid-Market Base:</span>
                  <span className="text-slate-300">${fxResult.converted_amount_before_buffer_usd}</span>
                </div>
                <div className="flex justify-between text-slate-300">
                  <span>Volatility Buffer ({fxBuffer}%):</span>
                  <span className="text-amber-400">+${fxResult.volatility_buffer_usd}</span>
                </div>
                <div className="flex justify-between text-slate-300 font-bold border-t border-slate-800 pt-1">
                  <span>Total Client Quote:</span>
                  <span className="text-emerald-400">${fxResult.final_client_quote_usd}</span>
                </div>
              </div>
            )}
          </div>

          <button 
            onClick={handleConvertFx}
            disabled={fxLoading}
            className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-medium py-2 rounded-xl text-sm transition flex items-center justify-center gap-2"
          >
            {fxLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <DollarSign className="w-4 h-4" />}
            Calculate FX Hedge Quote
          </button>
        </div>

        {/* 3. Counterfactual Replanner Card */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 flex flex-col justify-between shadow-lg">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2 text-violet-400 font-semibold">
                <Clock className="w-5 h-5" />
                <span>3-Tier IROPS Counterfactual Replanner</span>
              </div>
              <span className="text-xs bg-violet-950 text-violet-300 border border-violet-800 px-2 py-0.5 rounded-md font-mono">
                Counterfactual
              </span>
            </div>

            <div className="grid grid-cols-2 gap-3 text-sm mb-4">
              <div>
                <label className="block text-slate-400 text-xs mb-1">Disrupted Leg</label>
                <input 
                  type="text" 
                  value={cftNode} 
                  onChange={(e) => setCftNode(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-white text-sm focus:outline-none focus:border-violet-500" 
                />
              </div>
              <div>
                <label className="block text-slate-400 text-xs mb-1">Disruption Delay (mins)</label>
                <input 
                  type="number" 
                  value={cftDelay} 
                  onChange={(e) => setCftDelay(Number(e.target.value))}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-white text-sm focus:outline-none focus:border-violet-500" 
                />
              </div>
            </div>

            {cftResult && (
              <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 mb-4 text-xs font-mono space-y-2 max-h-44 overflow-y-auto">
                {cftResult.alternatives?.map((alt: any, idx: number) => (
                  <div key={idx} className="border-b border-slate-800/80 pb-1.5 last:border-none">
                    <div className="flex justify-between font-bold text-violet-300">
                      <span>{alt.title}</span>
                      <span className="text-slate-400 text-[10px]">Score: {alt.ranking_score}</span>
                    </div>
                    <div className="text-slate-400 text-[11px]">{alt.explanation}</div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <button 
            onClick={handleReplanDisruption}
            disabled={cftLoading}
            className="w-full bg-violet-600 hover:bg-violet-500 text-white font-medium py-2 rounded-xl text-sm transition flex items-center justify-center gap-2"
          >
            {cftLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
            Synthesize Counterfactual Recovery
          </button>
        </div>

        {/* 4. Group Consensus Pareto Card */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 flex flex-col justify-between shadow-lg">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2 text-amber-400 font-semibold">
                <Users className="w-5 h-5" />
                <span>Multi-Traveler Pareto Group Consensus</span>
              </div>
              <span className="text-xs bg-amber-950 text-amber-300 border border-amber-800 px-2 py-0.5 rounded-md font-mono">
                Group Travel
              </span>
            </div>

            <div className="grid grid-cols-2 gap-3 text-sm mb-4">
              <div>
                <label className="block text-slate-400 text-xs mb-1">Alice Max Budget ($)</label>
                <input 
                  type="number" 
                  value={grpP1Budget} 
                  onChange={(e) => setGrpP1Budget(Number(e.target.value))}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-white text-sm focus:outline-none focus:border-amber-500" 
                />
              </div>
              <div>
                <label className="block text-slate-400 text-xs mb-1">Bob Max Budget ($)</label>
                <input 
                  type="number" 
                  value={grpP2Budget} 
                  onChange={(e) => setGrpP2Budget(Number(e.target.value))}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-white text-sm focus:outline-none focus:border-amber-500" 
                />
              </div>
            </div>

            {grpResult && (
              <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 mb-4 text-xs font-mono space-y-1.5 max-h-44 overflow-y-auto">
                <div className="text-slate-300 font-semibold">Top Ranked Option: {grpResult.ranked_proposals?.[0]?.title}</div>
                <div className="text-emerald-400">Harmonic Consensus Score: {grpResult.ranked_proposals?.[0]?.consensus_score?.toFixed(1)}/100</div>
                <div className="text-slate-400 text-[11px]">Compromises: {grpResult.ranked_proposals?.[0]?.compromises?.join(', ') || 'None'}</div>
              </div>
            )}
          </div>

          <button 
            onClick={handleGroupConsensus}
            disabled={grpLoading}
            className="w-full bg-amber-600 hover:bg-amber-500 text-white font-medium py-2 rounded-xl text-sm transition flex items-center justify-center gap-2"
          >
            {grpLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Users className="w-4 h-4" />}
            Evaluate Pareto Group Consensus
          </button>
        </div>

      </div>

      {/* 5. Zero-Trust Capability Tokens Section */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-lg">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2 text-rose-400 font-semibold">
            <ShieldCheck className="w-5 h-5" />
            <span>Zero-Trust Scoped Capability Token & 5-Tier Authority Gatekeeper</span>
          </div>
          <span className="text-xs bg-rose-950 text-rose-300 border border-rose-800 px-2 py-0.5 rounded-md font-mono">
            PER-0933 / PER-0927
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div>
            <label className="block text-slate-400 text-xs mb-1">Target Role</label>
            <select 
              value={tokRole} 
              onChange={(e) => setTokRole(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-rose-500"
            >
              <option value="owner">Owner (Tier 4 Dual Control)</option>
              <option value="senior_agent">Senior Agent (Tier 2)</option>
              <option value="traveler_booker">Traveler Booker (Tier 3)</option>
              <option value="traveler_guest">Traveler Guest (Tier 0 Read Only)</option>
            </select>
          </div>
          <div>
            <label className="block text-slate-400 text-xs mb-1">Target Trip ID</label>
            <input 
              type="text" 
              value={tokTripId} 
              onChange={(e) => setTokTripId(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-rose-500" 
            />
          </div>
          <div className="flex items-end">
            <button 
              onClick={handleIssueToken}
              disabled={tokLoading}
              className="w-full bg-rose-600 hover:bg-rose-500 text-white font-medium py-2 rounded-lg text-sm transition flex items-center justify-center gap-2"
            >
              {tokLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <ShieldCheck className="w-4 h-4" />}
              Issue HMAC SHA-256 Token
            </button>
          </div>
        </div>

        {tokResult && (
          <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 text-xs font-mono space-y-2">
            <div className="text-emerald-400 font-semibold flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4" />
              Token Successfully Minted & Cryptographically Signed
            </div>
            <div className="break-all text-slate-300 bg-slate-900 p-2.5 rounded-lg border border-slate-800">
              <span className="text-slate-500 select-none">Bearer </span>{tokResult.token}
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-slate-400 text-[11px] pt-1">
              <div>Role: <span className="text-white">{tokResult.role}</span></div>
              <div>Scopes: <span className="text-white">{tokResult.scopes?.join(', ')}</span></div>
              <div>TTL: <span className="text-white">72 Hours</span></div>
              <div>Trust Zone: <span className="text-rose-400">ZONE_1_PARTNER</span></div>
            </div>
          </div>
        )}
      </div>
    </>
  )}
</div>
);
}
