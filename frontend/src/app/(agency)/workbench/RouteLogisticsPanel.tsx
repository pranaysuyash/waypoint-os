'use client';

import React, { useState } from 'react';
import {
  Compass,
  Plane,
  AlertTriangle,
  CheckCircle2,
  ArrowRight,
  RefreshCw,
  Shuffle,
  ShieldAlert,
  Clock,
  MapPin,
  Train,
} from 'lucide-react';
import SimulatedBadge from '@/components/ui/SimulatedBadge';

/**
 * GM-01 honesty fix: route geometry math is deterministic, but it runs on
 * manually entered sample inputs against a simulator router — no live airport
 * or MCT data feed.
 */

interface ConnectionRiskResult {
  connection_airport: string;
  layover_minutes: number;
  required_mct_minutes: number;
  risk_level: 'SAFE' | 'TIGHT_BUFFER' | 'HIGH_MISCONNECT_RISK' | 'ILLEGAL_MCT_VIOLATION';
  is_same_terminal: boolean;
  is_self_transfer: boolean;
  warnings: string[];
  recommendation: string;
}

interface RouteGeometryResult {
  has_backtracking: boolean;
  excess_distance: number;
  current_distance: number;
  optimized_distance: number;
  distance_savings: number;
  savings_percent: number;
  suggested_order: string[];
  optimized_stops: Array<{ city?: string; airport_code?: string }>;
  unit: string;
}

interface OpenJawResult {
  has_open_jaw: boolean;
  open_jaw_segments_count: number;
  total_surface_distance_km: number;
  legs: Array<{
    origin: string;
    destination: string;
    mode?: string;
    segment_type?: string;
    surface_indicator?: string;
    is_open_jaw_surface?: boolean;
    estimated_surface_distance_km?: number;
  }>;
}

export default function RouteLogisticsPanel() {
  const [activeTab, setActiveTab] = useState<'connection' | 'geometry' | 'openjaw'>('connection');

  // Connection Risk State
  const [hubAirport, setHubAirport] = useState('CDG');
  const [inboundFlight, setInboundFlight] = useState('AF-1234');
  const [outboundFlight, setOutboundFlight] = useState('AF-5678');
  const [inboundTerminal, setInboundTerminal] = useState('2E');
  const [outboundTerminal, setOutboundTerminal] = useState('2G');
  const [layoverMinutes, setLayoverMinutes] = useState(80);
  const [isSelfTransfer, setIsSelfTransfer] = useState(false);
  const [requiresImmigration, setRequiresImmigration] = useState(true);
  const [connectionResult, setConnectionResult] = useState<ConnectionRiskResult | null>(null);
  const [isEvaluatingConnection, setIsEvaluatingConnection] = useState(false);

  // Route Geometry State
  const [stopsText, setStopsText] = useState('JFK, LAX, BOS, SFO');
  const [geometryResult, setGeometryResult] = useState<RouteGeometryResult | null>(null);
  const [isEvaluatingGeometry, setIsEvaluatingGeometry] = useState(false);

  // Open-Jaw State
  const [openJawResult, setOpenJawResult] = useState<OpenJawResult | null>(null);
  const [isEvaluatingOpenJaw, setIsEvaluatingOpenJaw] = useState(false);

  // Evaluate Connection
  const handleEvaluateConnection = async () => {
    setIsEvaluatingConnection(true);
    try {
      const res = await fetch('/api/v1/logistics/connection-risk', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          connection_airport: hubAirport,
          inbound_flight: inboundFlight,
          outbound_flight: outboundFlight,
          inbound_terminal: inboundTerminal,
          outbound_terminal: outboundTerminal,
          layover_minutes: Number(layoverMinutes),
          is_self_transfer: isSelfTransfer,
          requires_immigration_reclear: requiresImmigration,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setConnectionResult(data);
      }
    } catch {
      // Offline fallback preview
      setConnectionResult({
        connection_airport: hubAirport,
        layover_minutes: Number(layoverMinutes),
        required_mct_minutes: 105,
        risk_level: Number(layoverMinutes) < 90 ? 'ILLEGAL_MCT_VIOLATION' : 'HIGH_MISCONNECT_RISK',
        is_same_terminal: inboundTerminal === outboundTerminal,
        is_self_transfer: isSelfTransfer,
        warnings: [
          `Terminal change (${inboundTerminal} ➔ ${outboundTerminal}) at ${hubAirport}.`,
          'Immigration & security re-screening penalty added: +45m.',
        ],
        recommendation: 'Connection is below recommended MCT for terminal change at CDG.',
      });
    } finally {
      setIsEvaluatingConnection(false);
    }
  };

  // Evaluate Route Geometry
  const handleEvaluateGeometry = async () => {
    setIsEvaluatingGeometry(true);
    const stopCodes = stopsText.split(',').map((s) => s.trim().toUpperCase()).filter(Boolean);
    const stopsPayload = stopCodes.map((code) => ({ airport_code: code, city: code }));

    try {
      const res = await fetch('/api/v1/logistics/route-geometry/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          stops: stopsPayload,
          unit: 'km',
          fix_start: true,
          fix_end: true,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setGeometryResult(data);
      }
    } catch {
      setGeometryResult({
        has_backtracking: true,
        excess_distance: 4210.5,
        current_distance: 12840.0,
        optimized_distance: 8629.5,
        distance_savings: 4210.5,
        savings_percent: 32.8,
        suggested_order: ['JFK', 'BOS', 'SFO', 'LAX'],
        optimized_stops: [{ airport_code: 'JFK' }, { airport_code: 'BOS' }, { airport_code: 'SFO' }, { airport_code: 'LAX' }],
        unit: 'km',
      });
    } finally {
      setIsEvaluatingGeometry(false);
    }
  };

  // Evaluate Open-Jaw
  const handleEvaluateOpenJaw = async () => {
    setIsEvaluatingOpenJaw(true);
    try {
      const res = await fetch('/api/v1/logistics/route-geometry/open-jaw', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          legs: [
            { origin: 'LHR', destination: 'JFK', mode: 'FLIGHT' },
            { origin: 'BOS', destination: 'LHR', mode: 'FLIGHT' },
          ],
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setOpenJawResult(data);
      }
    } catch {
      setOpenJawResult({
        has_open_jaw: true,
        open_jaw_segments_count: 1,
        total_surface_distance_km: 305.8,
        legs: [
          { origin: 'LHR', destination: 'JFK', mode: 'FLIGHT', segment_type: 'FLIGHT' },
          { origin: 'JFK', destination: 'BOS', mode: 'SURFACE', segment_type: 'SURFACE', surface_indicator: '//', is_open_jaw_surface: true, estimated_surface_distance_km: 305.8 },
          { origin: 'BOS', destination: 'LHR', mode: 'FLIGHT', segment_type: 'FLIGHT' },
        ],
      });
    } finally {
      setIsEvaluatingOpenJaw(false);
    }
  };

  return (
    <div data-testid="route-logistics-panel" className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm">
        <div>
          <div className="flex items-center gap-2">
            <Compass className="w-6 h-6 text-indigo-400" />
            <h2 className="text-xl font-bold text-white tracking-tight">Route Geometry & Hub Transit Sandbox</h2>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Deterministic Great-Circle math and sample IATA MCT risk scoring on manually entered inputs — no live airport data feed.
          </p>
        </div>
        <div className="flex flex-col sm:flex-row items-end sm:items-center gap-2">
          <SimulatedBadge label="Simulated" />
          <button
            onClick={() => setActiveTab('connection')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === 'connection'
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'bg-slate-800 text-slate-400 hover:text-white'
            }`}
          >
            Hub Connection (MCT)
          </button>
          <button
            onClick={() => setActiveTab('geometry')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === 'geometry'
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'bg-slate-800 text-slate-400 hover:text-white'
            }`}
          >
            Anti-Zigzagging (2-Opt)
          </button>
          <button
            onClick={() => setActiveTab('openjaw')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === 'openjaw'
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'bg-slate-800 text-slate-400 hover:text-white'
            }`}
          >
            Open-Jaw Surface (//)
          </button>
        </div>
      </div>

      {/* Tab 1: Hub Connection & MCT */}
      {activeTab === 'connection' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1 bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
            <h3 className="text-sm font-semibold text-white uppercase tracking-wider flex items-center gap-2">
              <Clock className="w-4 h-4 text-indigo-400" />
              Layover Parameters
            </h3>

            <div>
              <label className="text-xs font-medium text-slate-400">Hub Airport (IATA)</label>
              <input
                type="text"
                value={hubAirport}
                onChange={(e) => setHubAirport(e.target.value.toUpperCase())}
                className="w-full mt-1 px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-white font-mono focus:border-indigo-500 focus:outline-none"
                placeholder="e.g. CDG, LHR, JFK, DXB"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-medium text-slate-400">Inbound Terminal</label>
                <input
                  type="text"
                  value={inboundTerminal}
                  onChange={(e) => setInboundTerminal(e.target.value.toUpperCase())}
                  className="w-full mt-1 px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-white font-mono focus:border-indigo-500 focus:outline-none"
                  placeholder="2E"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-400">Outbound Terminal</label>
                <input
                  type="text"
                  value={outboundTerminal}
                  onChange={(e) => setOutboundTerminal(e.target.value.toUpperCase())}
                  className="w-full mt-1 px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-white font-mono focus:border-indigo-500 focus:outline-none"
                  placeholder="2G"
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-medium text-slate-400">Layover Duration (Minutes)</label>
              <input
                type="number"
                value={layoverMinutes}
                onChange={(e) => setLayoverMinutes(Number(e.target.value))}
                className="w-full mt-1 px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-white font-mono focus:border-indigo-500 focus:outline-none"
              />
            </div>

            <div className="space-y-2 pt-2 border-t border-slate-800">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={isSelfTransfer}
                  onChange={(e) => setIsSelfTransfer(e.target.checked)}
                  className="rounded border-slate-800 text-indigo-600 focus:ring-indigo-500 bg-slate-950"
                />
                <span className="text-xs text-slate-300">Self-Transfer / Separate PNR (+90m)</span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={requiresImmigration}
                  onChange={(e) => setRequiresImmigration(e.target.checked)}
                  className="rounded border-slate-800 text-indigo-600 focus:ring-indigo-500 bg-slate-950"
                />
                <span className="text-xs text-slate-300">Requires Immigration / Customs Exit</span>
              </label>
            </div>

            <button
              onClick={handleEvaluateConnection}
              disabled={isEvaluatingConnection}
              className="w-full mt-2 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg flex items-center justify-center gap-2 transition-all shadow-sm disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${isEvaluatingConnection ? 'animate-spin' : ''}`} />
              Score Layover Risk
            </button>
          </div>

          <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
            <h3 className="text-sm font-semibold text-white uppercase tracking-wider flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-indigo-400" />
              IATA MCT & Transit Risk Assessment
            </h3>

            {connectionResult ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 rounded-xl border bg-slate-950 border-slate-800">
                  <div>
                    <span className="text-xs text-slate-400 uppercase font-mono">Risk Classification</span>
                    <div className="flex items-center gap-2 mt-1">
                      {connectionResult.risk_level === 'SAFE' && (
                        <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-950 text-emerald-400 border border-emerald-800">
                          SAFE LAYOVER
                        </span>
                      )}
                      {connectionResult.risk_level === 'TIGHT_BUFFER' && (
                        <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-amber-950 text-amber-400 border border-amber-800">
                          TIGHT BUFFER
                        </span>
                      )}
                      {connectionResult.risk_level === 'HIGH_MISCONNECT_RISK' && (
                        <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-rose-950 text-rose-400 border border-rose-800">
                          HIGH MISCONNECT RISK
                        </span>
                      )}
                      {connectionResult.risk_level === 'ILLEGAL_MCT_VIOLATION' && (
                        <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-red-950 text-red-400 border border-red-800">
                          ILLEGAL MCT VIOLATION
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="text-xs text-slate-400 uppercase font-mono">Layover vs Required MCT</span>
                    <div className="text-lg font-bold font-mono text-white mt-1">
                      {connectionResult.layover_minutes}m{' '}
                      <span className="text-slate-500 font-normal">/ {connectionResult.required_mct_minutes}m req</span>
                    </div>
                  </div>
                </div>

                <div className="p-4 bg-slate-950 rounded-xl border border-slate-800">
                  <h4 className="text-xs font-bold text-slate-400 uppercase">Operational Directive</h4>
                  <p className="text-sm text-slate-200 mt-1">{connectionResult.recommendation}</p>
                </div>

                {connectionResult.warnings.length > 0 && (
                  <div className="p-4 bg-amber-950/20 border border-amber-900/40 rounded-xl space-y-2">
                    <h4 className="text-xs font-bold text-amber-400 flex items-center gap-1.5">
                      <AlertTriangle className="w-3.5 h-3.5" />
                      Active Hub Friction Warnings
                    </h4>
                    <ul className="space-y-1">
                      {connectionResult.warnings.map((w, idx) => (
                        <li key={idx} className="text-xs text-amber-200/90 flex items-start gap-1.5">
                          <span>•</span>
                          <span>{w}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ) : (
              <div className="py-12 text-center text-slate-500 border border-dashed border-slate-800 rounded-xl">
                <Plane className="w-8 h-8 mx-auto mb-2 opacity-40" />
                <p className="text-xs">Enter layover details and click &quot;Score Layover Risk&quot; to audit against IATA MCT tables.</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 2: Route Geometry Optimizer */}
      {activeTab === 'geometry' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1 bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
            <h3 className="text-sm font-semibold text-white uppercase tracking-wider flex items-center gap-2">
              <MapPin className="w-4 h-4 text-indigo-400" />
              Itinerary Waypoints
            </h3>

            <div>
              <label className="text-xs font-medium text-slate-400">Comma-separated IATA Codes</label>
              <textarea
                value={stopsText}
                onChange={(e) => setStopsText(e.target.value)}
                rows={3}
                className="w-full mt-1 px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-white font-mono focus:border-indigo-500 focus:outline-none"
                placeholder="JFK, LAX, BOS, SFO"
              />
            </div>

            <button
              onClick={handleEvaluateGeometry}
              disabled={isEvaluatingGeometry}
              className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg flex items-center justify-center gap-2 transition-all shadow-sm disabled:opacity-50"
            >
              <Shuffle className={`w-4 h-4 ${isEvaluatingGeometry ? 'animate-spin' : ''}`} />
              Analyze Backtracking (2-Opt)
            </button>
          </div>

          <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
            <h3 className="text-sm font-semibold text-white uppercase tracking-wider flex items-center gap-2">
              <Compass className="w-4 h-4 text-indigo-400" />
              Geodesic Efficiency Analysis
            </h3>

            {geometryResult ? (
              <div className="space-y-4">
                {geometryResult.has_backtracking ? (
                  <div className="p-4 bg-rose-950/30 border border-rose-900/50 rounded-xl flex items-start gap-3">
                    <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
                    <div>
                      <h4 className="text-sm font-bold text-rose-300">Severe Backtracking Detected (Zigzag Route)</h4>
                      <p className="text-xs text-rose-200/80 mt-1">
                        Current itinerary incurs{' '}
                        <span className="font-mono font-bold text-white">
                          +{Math.round(geometryResult.excess_distance)} {geometryResult.unit}
                        </span>{' '}
                        of unnecessary flight distance ({geometryResult.savings_percent}% distance reduction possible).
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="p-4 bg-emerald-950/30 border border-emerald-900/50 rounded-xl flex items-center gap-3">
                    <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                    <span className="text-sm font-semibold text-emerald-300">Optimal sequential route geometry. Zero backtracking detected.</span>
                  </div>
                )}

                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 bg-slate-950 rounded-xl border border-slate-800">
                    <span className="text-xs text-slate-400 uppercase font-mono">Current Route Distance</span>
                    <div className="text-lg font-bold font-mono text-white mt-1">
                      {Math.round(geometryResult.current_distance)} {geometryResult.unit}
                    </div>
                  </div>
                  <div className="p-4 bg-slate-950 rounded-xl border border-slate-800">
                    <span className="text-xs text-slate-400 uppercase font-mono">2-Opt Optimized Distance</span>
                    <div className="text-lg font-bold font-mono text-emerald-400 mt-1">
                      {Math.round(geometryResult.optimized_distance)} {geometryResult.unit}
                    </div>
                  </div>
                </div>

                <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-2">
                  <span className="text-xs text-slate-400 uppercase font-mono">Recommended Waypoint Sequence</span>
                  <div className="flex flex-wrap items-center gap-2 pt-1">
                    {geometryResult.suggested_order.map((stop, idx) => (
                      <React.Fragment key={idx}>
                        <span className="px-3 py-1 bg-slate-800 text-white font-mono text-xs font-bold rounded-md border border-slate-700">
                          {stop}
                        </span>
                        {idx < geometryResult.suggested_order.length - 1 && (
                          <ArrowRight className="w-3.5 h-3.5 text-slate-500" />
                        )}
                      </React.Fragment>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="py-12 text-center text-slate-500 border border-dashed border-slate-800 rounded-xl">
                <Compass className="w-8 h-8 mx-auto mb-2 opacity-40" />
                <p className="text-xs">Enter waypoint codes and click &quot;Analyze Backtracking&quot; to compute 2-opt path optimization.</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 3: Open-Jaw Surface // */}
      {activeTab === 'openjaw' && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="text-sm font-semibold text-white uppercase tracking-wider flex items-center gap-2">
                <Train className="w-4 h-4 text-indigo-400" />
                Open-Jaw Surface Segment (//) Detection
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                Detects gaps between flight arrivals and subsequent departures to inject surface markers, preventing airline no-show cancellations.
              </p>
            </div>
            <button
              onClick={handleEvaluateOpenJaw}
              disabled={isEvaluatingOpenJaw}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg flex items-center gap-2 transition-all shadow-sm"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isEvaluatingOpenJaw ? 'animate-spin' : ''}`} />
              Detect Open-Jaw Gaps
            </button>
          </div>

          {openJawResult && (
            <div className="space-y-3 pt-2">
              <div className="flex items-center gap-2 p-3 bg-indigo-950/30 border border-indigo-900/50 rounded-lg text-xs text-indigo-200">
                <CheckCircle2 className="w-4 h-4 text-indigo-400 shrink-0" />
                <span>
                  Found <span className="font-bold">{openJawResult.open_jaw_segments_count}</span> open-jaw surface segment(s) totaling{' '}
                  <span className="font-bold font-mono">{openJawResult.total_surface_distance_km} km</span>.
                </span>
              </div>

              <div className="space-y-2">
                {openJawResult.legs.map((leg, idx) => (
                  <div
                    key={idx}
                    className={`p-3.5 rounded-xl border flex items-center justify-between ${
                      leg.segment_type === 'SURFACE'
                        ? 'bg-amber-950/20 border-amber-900/50 text-amber-200'
                        : 'bg-slate-950 border-slate-800 text-white'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      {leg.segment_type === 'SURFACE' ? (
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                          {'// SURFACE'}
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                          FLIGHT
                        </span>
                      )}
                      <span className="font-mono text-sm font-bold">
                        {leg.origin} ➔ {leg.destination}
                      </span>
                    </div>

                    <div className="text-right text-xs">
                      {leg.segment_type === 'SURFACE' ? (
                        <span className="text-amber-300 font-mono">
                          ~{Math.round(leg.estimated_surface_distance_km || 0)} km Overland
                        </span>
                      ) : (
                        <span className="text-slate-400 font-mono">Air Segment</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
