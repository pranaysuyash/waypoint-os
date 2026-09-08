'use client';

import React, { useState } from 'react';
import { MapPin, Navigation, ArrowRight, RefreshCw, Zap, CheckCircle2 } from 'lucide-react';

interface Waypoint {
  id: string;
  code: string;
  name: string;
  lat: number;
  lng: number;
  country: string;
}

const DEFAULT_WAYPOINTS: Waypoint[] = [
  { id: '1', code: 'JFK', name: 'New York JFK', lat: 40.6413, lng: -73.7781, country: 'USA' },
  { id: '2', code: 'FCO', name: 'Rome Fiumicino', lat: 41.8003, lng: 12.2389, country: 'Italy' },
  { id: '3', code: 'FLR', name: 'Florence Peretola', lat: 43.8100, lng: 11.2051, country: 'Italy' },
  { id: '4', code: 'VCE', name: 'Venice Marco Polo', lat: 45.5053, lng: 12.3519, country: 'Italy' },
  { id: '5', code: 'CDG', name: 'Paris Charles de Gaulle', lat: 49.0097, lng: 2.5479, country: 'France' },
];

export default function RouteMapStudio() {
  const [waypoints, setWaypoints] = useState<Waypoint[]>(DEFAULT_WAYPOINTS);
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [backendUnavailable, setBackendUnavailable] = useState(false);
  const [optimizationSavings, setOptimizationSavings] = useState<{
    original_km: number;
    optimized_km: number;
    savings_km: number;
    savings_percent: number;
  } | null>(null);

  const moveWaypoint = (index: number, direction: 'up' | 'down') => {
    const targetIndex = direction === 'up' ? index - 1 : index + 1;
    if (targetIndex < 0 || targetIndex >= waypoints.length) return;
    const next = [...waypoints];
    const temp = next[index];
    next[index] = next[targetIndex];
    next[targetIndex] = temp;
    setWaypoints(next);
    setOptimizationSavings(null);
    setBackendUnavailable(false);
  };

  const handle2OptOptimize = async () => {
    setIsOptimizing(true);
    setBackendUnavailable(false);
    try {
      const res = await fetch('/api/v1/logistics/assess-route', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          stops: waypoints.map(w => ({ airport_code: w.code, lat: w.lat, lng: w.lng })),
        }),
      });
      if (res.ok) {
        const data = await res.json();
        const { total_distance_km, optimized_distance_km, savings_km, savings_percent } = data;
        const valid =
          typeof total_distance_km === 'number' && Number.isFinite(total_distance_km) &&
          typeof optimized_distance_km === 'number' && Number.isFinite(optimized_distance_km) &&
          typeof savings_km === 'number' && Number.isFinite(savings_km) &&
          typeof savings_percent === 'number' && Number.isFinite(savings_percent);
        if (!valid) {
          // No fabricated defaults: an unusable payload is reported, never
          // replaced with invented savings (Part-J #5 follow-up).
          setBackendUnavailable(true);
        } else {
          setOptimizationSavings({
            original_km: total_distance_km,
            optimized_km: optimized_distance_km,
            savings_km,
            savings_percent,
          });
        }
      } else {
        // 2026-09-06 route-inventory gate: no backend endpoint exists yet.
        setBackendUnavailable(true);
      }
    } catch {
      setBackendUnavailable(true);
    } finally {
      setIsOptimizing(false);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 text-white shadow-xl">
      <div className="flex items-center justify-between pb-4 border-b border-slate-800 mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-indigo-500/10 text-indigo-400 rounded-lg border border-indigo-500/20">
            <Navigation className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-semibold tracking-tight text-slate-100">Interactive Route & Geodesic Map Studio</h2>
            <p className="text-xs text-slate-400">2-Opt path optimization, open-jaw ground connections, and waypoint ordering</p>
          </div>
        </div>

        <button
          onClick={handle2OptOptimize}
          disabled={isOptimizing}
          className="flex items-center gap-2 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold rounded-lg transition-colors shadow-sm disabled:opacity-50"
        >
          {isOptimizing ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Zap className="w-3.5 h-3.5" />}
          Run 2-Opt Geodesic Solver
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Visual Flight Arcs / Canvas Map Mock */}
        <div className="lg:col-span-2 bg-slate-950 border border-slate-800/80 rounded-lg p-5 flex flex-col justify-between relative min-h-[320px]">
          <div className="flex justify-between items-center text-xs text-slate-400 mb-2">
            <span className="font-mono flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              Geodesic Flight Matrix (WGS-84 Sphere)
            </span>
            <span className="text-[11px] text-slate-500">Projection: Mercator / Great Circle</span>
          </div>

          {/* Interactive Route Node Graph */}
          <div className="flex-1 flex items-center justify-center p-4">
            <div className="flex flex-wrap items-center justify-center gap-3">
              {waypoints.map((wp, idx) => (
                <React.Fragment key={wp.id}>
                  <div className="flex flex-col items-center bg-slate-900 border border-slate-700/60 rounded-lg p-3 min-w-[110px] text-center shadow-md">
                    <div className="w-6 h-6 rounded-full bg-indigo-500/20 text-indigo-400 text-xs font-bold flex items-center justify-center mb-1">
                      {idx + 1}
                    </div>
                    <span className="font-mono font-bold text-sm text-indigo-300">{wp.code}</span>
                    <span className="text-[11px] text-slate-400 truncate max-w-[90px]">{wp.name}</span>
                    <span className="text-[10px] text-slate-500">{wp.country}</span>
                  </div>

                  {idx < waypoints.length - 1 && (
                    <div className="flex flex-col items-center px-1">
                      <ArrowRight className="w-4 h-4 text-indigo-400/80" />
                      <span className="text-[9px] font-mono text-slate-500">
                        {wp.country === waypoints[idx + 1].country && wp.country !== 'USA' ? '// Ground' : '✈ Flight'}
                      </span>
                    </div>
                  )}
                </React.Fragment>
              ))}
            </div>
          </div>

          {backendUnavailable && (
            <div className="mt-4 p-3 bg-amber-950/40 border border-amber-800/50 rounded-lg flex items-center justify-between text-xs text-amber-300">
              <span>
                Route assessment isn&apos;t available yet — you&apos;ll see
                nothing here rather than made-up numbers.
              </span>
            </div>
          )}

          {optimizationSavings && (
            <div className="mt-4 p-3 bg-emerald-950/40 border border-emerald-800/50 rounded-lg flex items-center justify-between text-xs text-emerald-300">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>2-Opt Optimizer reduced total routing distance by <strong>{optimizationSavings.savings_km.toLocaleString()} km</strong> ({optimizationSavings.savings_percent}%)</span>
              </div>
              <span className="font-mono font-bold text-emerald-400">{optimizationSavings.optimized_km.toLocaleString()} km total</span>
            </div>
          )}
        </div>

        {/* Right Column: Ordered Waypoint Reorder Controls */}
        <div className="bg-slate-950 border border-slate-800/80 rounded-lg p-4 flex flex-col justify-between">
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-1.5">
              <MapPin className="w-3.5 h-3.5 text-indigo-400" />
              Waypoint Itinerary Order
            </h3>

            <div className="space-y-2">
              {waypoints.map((wp, idx) => (
                <div key={wp.id} className="flex items-center justify-between bg-slate-900/90 border border-slate-800 p-2.5 rounded-lg text-xs">
                  <div className="flex items-center gap-2.5">
                    <span className="font-mono text-slate-500 font-semibold w-4">{idx + 1}.</span>
                    <div>
                      <span className="font-mono font-bold text-slate-200 mr-2">{wp.code}</span>
                      <span className="text-slate-400">{wp.name}</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => moveWaypoint(idx, 'up')}
                      disabled={idx === 0}
                      className="p-1 hover:bg-slate-800 text-slate-400 hover:text-white rounded disabled:opacity-20"
                      title="Move Up"
                    >
                      ▲
                    </button>
                    <button
                      onClick={() => moveWaypoint(idx, 'down')}
                      disabled={idx === waypoints.length - 1}
                      className="p-1 hover:bg-slate-800 text-slate-400 hover:text-white rounded disabled:opacity-20"
                      title="Move Down"
                    >
                      ▼
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-800/80 text-[11px] text-slate-500 flex justify-between">
            <span>Total Segments: {waypoints.length - 1}</span>
            <span>Open-Jaw Sectors: Auto-detected</span>
          </div>
        </div>
      </div>
    </div>
  );
}
