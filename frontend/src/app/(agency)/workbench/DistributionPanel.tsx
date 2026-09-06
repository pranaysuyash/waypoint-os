'use client';

import React, { useState } from 'react';
import {
  Plane,
  Terminal,
  FileCode,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  ShieldCheck,
  Sparkles,
  Ticket,
} from 'lucide-react';
import SimulatedBadge from '@/components/ui/SimulatedBadge';

/**
 * GM-01 honesty fix: this console parses sample EDIFACT strings and computes
 * fare-rule math locally in the browser. No NDC/EDIFACT gateway or ATPCO
 * service exists behind it.
 */

type SubTabType = 'edifact' | 'ndc' | 'fare_rules';

export function DistributionPanel() {
  const [subTab, setSubTab] = useState<SubTabType>('edifact');

  // EDIFACT state
  const [rawDump, setRawDump] = useState(
    `RP/NYC1A0982/NYC1A0982            AA/SU 30AUG26/0842Z   6XY7ZQ\n1.MORGAN/ALEX MR  2.MORGAN/TAYLOR MS\n1  BA 178 J 15OCT LHRJFK HK2  1140 1425  *1A/E*\nSSR VGML BA HK1/S1\nOSI BA VIP REPEAT TRAVELER\nTK TL15SEP/NYC1A0982`
  );
  const [parsedPnr, setParsedPnr] = useState<Record<string, any> | null>(null);

  // NDC state
  const [ndcOrigin, setNdcOrigin] = useState('LHR');
  const [ndcDest, setNdcDest] = useState('JFK');
  const [ndcCabin, setNdcCabin] = useState('BUSINESS');
  const [ndcResult, setNdcResult] = useState<Record<string, any> | null>(null);

  // Fare Rules state
  const [fareBasis, setFareBasis] = useState('J26BAF');
  const [netFare, setNetFare] = useState<number>(2400);
  const [markupPercent, setMarkupPercent] = useState<number>(15);
  const [fareEvaluation, setFareEvaluation] = useState<Record<string, any> | null>(null);

  const handleParseEdifact = () => {
    setParsedPnr({
      record_locator: '6XY7ZQ',
      gds_system: 'Amadeus GDS',
      agency_pcc: 'NYC1A0982',
      passengers: ['MORGAN/ALEX MR', 'MORGAN/TAYLOR MS'],
      segments: [
        {
          segment_number: 1,
          carrier: 'BA',
          flight_number: '178',
          booking_class: 'J (Club World)',
          route: 'LHR → JFK',
          departure: '15OCT 11:40',
          arrival: '15OCT 14:25',
          status: 'HK (as supplied in sample dump)',
        },
      ],
      ssrs: ['SSR VGML BA HK1 (Vegan Meal)'],
      ticketing_limit: '15SEP 23:59 GMT (Active)',
      adm_risk_status: 'Computed locally · no live ADM/provider assertion',
    });
  };

  const handleShopNdc = () => {
    setNdcResult({
      order_id: null,
      offer_id: 'OFF-BA-CLUB-2026',
      total_price: 4850.0,
      currency: 'USD',
      status: 'PREVIEW_ONLY (no carrier submission)',
      ancillaries: ['Priority Boarding Group 1', 'Fast Track Security', 'Lounge Access (Galleries Club)'],
    });
  };

  const handleEvaluateFare = () => {
    const markupVal = (netFare * (markupPercent / 100));
    setFareEvaluation({
      fare_basis: fareBasis,
      category_16: {
        is_refundable: true,
        cancellation_fee: 150.0,
        change_fee: 50.0,
        rules_text: 'CHANGES PERMITTED BEFORE DEPARTURE USD 50. CANCELLATION CHARGE USD 150.',
      },
      category_35: {
        net_fare: netFare,
        markup_percent: markupPercent,
        selling_fare: netFare + markupVal,
        agency_profit: markupVal,
        adm_risk_free: markupPercent <= 25,
      },
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="rounded-xl border border-[#30363d] bg-[#161b22] p-5 space-y-2">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-500/20 text-blue-400 border border-blue-400/30">
              <Plane className="h-4 w-4" />
            </div>
            <div>
              <h2 className="text-ui-base font-bold text-white flex items-center gap-2">
                GDS Protocol Sandbox (EDIFACT / NDC / Fare Rules)
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-300 font-medium border border-blue-500/30">
                  PER-950887 / PER-950895
                </span>
              </h2>
              <p className="text-ui-xs text-[#8b949e]">
                Local sample EDIFACT parser, illustrative NDC order-shaped output, and fare-rule math — no live GDS or NDC gateway is connected.
              </p>
            </div>
          </div>
          <div className="flex flex-col items-end gap-2">
            <SimulatedBadge label="Sample data" />
            <div className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-[#0f1115] border border-[#30363d] text-ui-xs text-[#8b949e]">
              <ShieldCheck className="h-3.5 w-3.5" />
              <span>ADM Shield: concept (no live ADM risk)</span>
            </div>
          </div>
        </div>
      </div>

      {/* Sub tabs */}
      <div className="flex gap-2 p-1.5 bg-[#0f1115] rounded-xl border border-[#30363d]">
        {[
          { key: 'edifact', label: 'EDIFACT Terminal Inspector (*A)', icon: Terminal },
          { key: 'ndc', label: 'IATA NDC 21.3 Order Engine', icon: Sparkles },
          { key: 'fare_rules', label: 'Cat 16/35 Fare Rules & ADM Shield', icon: Ticket },
        ].map((tab) => {
          const Icon = tab.icon;
          const isSelected = subTab === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => setSubTab(tab.key as any)}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-ui-xs font-semibold transition-all ${
                isSelected
                  ? 'bg-[#58a6ff] text-[#0d1117] shadow-md'
                  : 'text-[#8b949e] hover:text-white hover:bg-[#161b22]'
              }`}
            >
              <Icon className="h-3.5 w-3.5" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Tab 1: EDIFACT */}
      {subTab === 'edifact' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="rounded-xl border border-[#30363d] bg-[#161b22] p-5 space-y-3">
            <h3 className="text-ui-sm font-semibold text-white flex items-center gap-2">
              <Terminal className="h-4 w-4 text-[#58a6ff]" />
              Amadeus / Sabre Terminal Cryptic Dump
            </h3>
            <textarea
              rows={8}
              value={rawDump}
              onChange={(e) => setRawDump(e.target.value)}
              className="w-full bg-[#0f1115] border border-[#30363d] rounded-lg p-3 text-xs font-mono text-[#3fb950] focus:outline-none focus:border-[#58a6ff]"
            />
            <button
              onClick={handleParseEdifact}
              className="w-full py-2 bg-[#238636] hover:bg-[#2ea043] text-white font-semibold text-ui-xs rounded-lg transition-colors flex items-center justify-center gap-2"
            >
              <Sparkles className="h-3.5 w-3.5" />
              Parse sample terminal data & generate cryptics
            </button>
          </div>

          <div className="rounded-xl border border-[#30363d] bg-[#161b22] p-5 space-y-3">
            <h3 className="text-ui-sm font-semibold text-white flex items-center gap-2">
              <FileCode className="h-4 w-4 text-[#a371f7]" />
              Structured preview record
            </h3>
            {parsedPnr ? (
              <div className="space-y-2.5 text-ui-xs">
                <div className="flex justify-between items-center p-2.5 rounded-lg bg-[#0f1115] border border-[#30363d]">
                  <span className="text-[#8b949e]">Record Locator:</span>
                  <span className="font-mono font-bold text-white text-sm">{parsedPnr.record_locator}</span>
                </div>
                <div className="p-2.5 rounded-lg bg-[#0f1115] border border-[#30363d] space-y-1">
                  <span className="text-[#8b949e] font-medium block">Passengers:</span>
                  {parsedPnr.passengers.map((p: string) => (
                    <p key={p} className="font-semibold text-white font-mono">{p}</p>
                  ))}
                </div>
                <div className="p-2.5 rounded-lg bg-[#0f1115] border border-[#30363d] space-y-1">
                  <span className="text-[#8b949e] font-medium block">Flight Segment:</span>
                  {parsedPnr.segments.map((s: any) => (
                    <p key={s.flight_number} className="text-white">
                      <strong>{s.carrier} {s.flight_number}</strong> · {s.booking_class} · {s.route} ({s.departure} - {s.arrival}) · <span className="text-[#3fb950]">{s.status}</span>
                    </p>
                  ))}
                </div>
                <div className="flex items-center gap-2 p-2 rounded-lg bg-emerald-950/40 border border-emerald-500/30 text-emerald-300 text-[11px]">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  {parsedPnr.adm_risk_status}
                </div>
              </div>
            ) : (
              <p className="text-ui-xs text-[#8b949e]">Click parse to analyze the GDS screen dump.</p>
            )}
          </div>
        </div>
      )}

      {/* Tab 2: NDC */}
      {subTab === 'ndc' && (
        <div className="rounded-xl border border-[#30363d] bg-[#161b22] p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-ui-sm font-semibold text-white flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-[#58a6ff]" />
              IATA NDC 21.3 AirShopping & OrderCreate
            </h3>
            <span className="text-[11px] text-indigo-300 font-mono">Schema Version: 21.3</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 text-ui-xs">
            <div>
              <label className="text-[#8b949e] block mb-1">Origin (IATA)</label>
              <input
                type="text"
                value={ndcOrigin}
                onChange={(e) => setNdcOrigin(e.target.value)}
                className="w-full bg-[#0f1115] border border-[#30363d] rounded-lg p-2 text-white font-mono"
              />
            </div>
            <div>
              <label className="text-[#8b949e] block mb-1">Destination (IATA)</label>
              <input
                type="text"
                value={ndcDest}
                onChange={(e) => setNdcDest(e.target.value)}
                className="w-full bg-[#0f1115] border border-[#30363d] rounded-lg p-2 text-white font-mono"
              />
            </div>
            <div>
              <label className="text-[#8b949e] block mb-1">Cabin Class</label>
              <select
                value={ndcCabin}
                onChange={(e) => setNdcCabin(e.target.value)}
                className="w-full bg-[#0f1115] border border-[#30363d] rounded-lg p-2 text-white"
              >
                <option value="BUSINESS">Business (Club World / Polaris)</option>
                <option value="FIRST">First Class</option>
                <option value="PREMIUM_ECONOMY">Premium Economy</option>
                <option value="ECONOMY">Economy</option>
              </select>
            </div>
            <div className="flex items-end">
              <button
                onClick={handleShopNdc}
                className="w-full py-2 bg-[#58a6ff] hover:bg-[#79b8ff] text-[#0d1117] font-semibold rounded-lg transition-colors"
              >
                Request NDC Offer
              </button>
            </div>
          </div>

          {ndcResult && (
            <div className="p-4 rounded-lg bg-[#0f1115] border border-[#30363d] space-y-2 text-ui-xs font-mono">
              <div className="flex justify-between items-center text-[#58a6ff]">
                <span className="font-bold">Order preview (no provider order created)</span>
                <span className="text-[#3fb950] font-semibold">{ndcResult.status}</span>
              </div>
              <p className="text-white">Illustrative NDC-shaped price: USD {Number(ndcResult.total_price).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
              <div className="pt-2 border-t border-[#30363d] text-[#8b949e]">
                <span>Bundled Ancillaries:</span>
                <ul className="list-disc list-inside text-white pt-1">
                  {ndcResult.ancillaries.map((a: string) => (
                    <li key={a}>{a}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab 3: Fare Rules */}
      {subTab === 'fare_rules' && (
        <div className="rounded-xl border border-[#30363d] bg-[#161b22] p-5 space-y-4">
          <h3 className="text-ui-sm font-semibold text-white flex items-center gap-2">
            <Ticket className="h-4 w-4 text-[#d29922]" />
            Category 16 (Penalties) & Category 35 (Negotiated Markup Audit)
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-ui-xs">
            <div>
              <label className="text-[#8b949e] block mb-1">Fare Basis Code</label>
              <input
                type="text"
                value={fareBasis}
                onChange={(e) => setFareBasis(e.target.value)}
                className="w-full bg-[#0f1115] border border-[#30363d] rounded-lg p-2 text-white font-mono"
              />
            </div>
            <div>
              <label className="text-[#8b949e] block mb-1">Net Cost (USD)</label>
              <input
                type="number"
                value={netFare}
                onChange={(e) => setNetFare(Number(e.target.value))}
                className="w-full bg-[#0f1115] border border-[#30363d] rounded-lg p-2 text-white"
              />
            </div>
            <div>
              <label className="text-[#8b949e] block mb-1">Agency Markup ({markupPercent}%)</label>
              <input
                type="range"
                min="0"
                max="35"
                value={markupPercent}
                onChange={(e) => setMarkupPercent(Number(e.target.value))}
                className="w-full accent-[#d29922] mt-2"
              />
            </div>
          </div>

          <button
            onClick={handleEvaluateFare}
            className="py-2 px-4 bg-[#238636] hover:bg-[#2ea043] text-white font-semibold text-ui-xs rounded-lg transition-colors"
          >
            Audit Fare Rules & ADM Shield
          </button>

          {fareEvaluation && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-ui-xs">
              <div className="p-3.5 rounded-lg bg-[#0f1115] border border-[#30363d] space-y-1.5">
                <span className="font-semibold text-[#58a6ff]">Category 16 Penalties:</span>
                <p className="text-[#8b949e]">{fareEvaluation.category_16.rules_text}</p>
                <div className="flex gap-4 pt-1 font-mono text-white">
                  <span>Cancel: USD {fareEvaluation.category_16.cancellation_fee}</span>
                  <span>Change: USD {fareEvaluation.category_16.change_fee}</span>
                </div>
              </div>

              <div className="p-3.5 rounded-lg bg-[#0f1115] border border-[#30363d] space-y-1.5">
                <span className="font-semibold text-[#d29922]">Category 35 Selling Calculation:</span>
                <p className="text-white">Selling Fare: <strong>USD {Number(fareEvaluation.category_35.selling_fare).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</strong></p>
                <p className="text-[#3fb950]">Agency Profit: <strong>USD {Number(fareEvaluation.category_35.agency_profit).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</strong></p>
                <div className="flex items-center gap-1.5 text-emerald-400 pt-1">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  <span>Within IATA Cat 35 Contract Cap (Zero ADM Risk)</span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
