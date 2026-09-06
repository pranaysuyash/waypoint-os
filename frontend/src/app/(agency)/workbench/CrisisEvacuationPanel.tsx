'use client';

import React, { useState } from 'react';
import {
  AlertTriangle,
  Radio,
  MapPin,
  Car,
  Plane,
  ShieldAlert,
  CheckCircle2,
  Phone,
  Send,
  Navigation,
} from 'lucide-react';
import SimulatedBadge from '@/components/ui/SimulatedBadge';

/**
 * GM-01 honesty fix: every value in this panel is a client-side fixture. No
 * crisis feed, embassy transmission, convoy dispatch, or traveler broadcast
 * exists behind it — the copy now says so explicitly, and traveler names are
 * obvious sample defaults.
 */

type CrisisSubTab = 'radar' | 'routing' | 'dispatch';

export function CrisisEvacuationPanel() {
  const [activeSubTab, setActiveSubTab] = useState<CrisisSubTab>('radar');

  // Crisis state
  const [selectedIncident, setSelectedIncident] = useState({
    id: 'CRISIS-JP-001',
    headline: 'Typhoon Category 5 Grounding Commercial Flights (Tokyo / Kanto)',
    severity: 'SAMPLE SCENARIO',
    affected_trips: 2,
    passengers: ['Sample Traveler A', 'Sample Traveler B'],
    safe_destination: 'London Heathrow (LHR) (sample destination)',
  });

  // Evacuation manifest state
  const [manifest, setManifest] = useState<any>({
    manifest_id: 'EVAC-JP-88910',
    assembly_point: 'Park Hyatt Tokyo Main Lobby (sample location; not verified)',
    is_charter_confirmed: false,
    total_cost: 20300.0,
    consular_case_number: 'DOS-EMERG-JP-994',
    legs: [
      {
        leg: 1,
        mode: 'Overland Armored Escort Convoy',
        origin: 'Park Hyatt Tokyo',
        destination: 'Secondary Tactical Regional Airfield',
        departure: 'T+01:30 (illustrative timing; no dispatch)',
        status: 'CANDIDATE PLAN',
        cost: 1800,
      },
      {
        leg: 2,
        mode: 'Private Jet Air Charter (Citation Latitude)',
        origin: 'Secondary Tactical Regional Airfield',
        destination: 'London Heathrow (LHR)',
        departure: 'T+04:00 (illustrative timing; no slot held)',
        status: 'PROVIDER STATUS UNKNOWN',
        cost: 18500,
      },
    ],
  });

  // Dispatch state
  const [driverDispatch, setDriverDispatch] = useState<any>({
    dispatch_id: 'DRV-99418',
    driver_name: 'Sample driver (no provider assignment)',
    driver_phone: '+81-XX-XXX-XXXX',
    vehicle: 'Sample vehicle (no dispatch)',
    status: 'NOT DISPATCHED (SIMULATED)',
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="rounded-xl border border-[#f85149]/30 bg-gradient-to-r from-[#f85149]/10 via-[#161b22] to-[#161b22] p-5 space-y-2">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#f85149]/20 text-[#f85149] border border-[#f85149]/30">
              <AlertTriangle className="h-4 w-4" />
            </div>
            <div>
              <h2 className="text-ui-base font-bold text-white flex items-center gap-2">
                Crisis Evacuation & Irregular Disruption Dispatch (Sample)
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#f85149]/20 text-[#f85149] font-medium border border-[#f85149]/30">
                  PER-950889 / PER-950898
                </span>
              </h2>
              <p className="text-ui-xs text-[#8b949e]">
                Demonstration surface: simulated geofence crisis radar, sample evacuation routing manifest, and a draft dispatch console. Nothing is dispatched or transmitted.
              </p>
            </div>
          </div>
          <div className="flex flex-col items-end gap-2">
            <SimulatedBadge label="Sample data" />
            <div className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-[#0f1115] border border-[#30363d] text-ui-xs text-[#8b949e]">
              <Radio className="h-3.5 w-3.5" />
              <span>Sample Incident (Not a Live Feed)</span>
            </div>
          </div>
        </div>
      </div>

      {/* Sub tabs */}
      <div className="flex gap-2 p-1.5 bg-[#0f1115] rounded-xl border border-[#30363d]">
        {[
          { key: 'radar', label: 'Geofence Crisis Radar (Sample)', icon: Radio },
          { key: 'routing', label: 'Multi-Modal Escape Routing (Sample)', icon: Navigation },
          { key: 'dispatch', label: 'Ground Dispatch Draft (Sample)', icon: Car },
        ].map((tab) => {
          const Icon = tab.icon;
          const isSelected = activeSubTab === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveSubTab(tab.key as any)}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-ui-xs font-semibold transition-all ${
                isSelected
                  ? 'bg-[#f85149] text-white shadow-md'
                  : 'text-[#8b949e] hover:text-white hover:bg-[#161b22]'
              }`}
            >
              <Icon className="h-3.5 w-3.5" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Radar Tab */}
      {activeSubTab === 'radar' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="rounded-xl border border-[#30363d] bg-[#161b22] p-5 space-y-4">
            <h3 className="text-ui-sm font-semibold text-white flex items-center gap-2">
              <ShieldAlert className="h-4 w-4 text-[#f85149]" />
              Sample Incident Alert
            </h3>
            <div className="p-3.5 rounded-lg bg-[#0f1115] border border-[#f85149]/40 space-y-2 text-ui-xs">
              <div className="flex justify-between items-center text-[#f85149] font-bold">
                <span>{selectedIncident.id}</span>
                <span className="bg-[#f85149]/20 px-2 py-0.5 rounded font-mono">{selectedIncident.severity}</span>
              </div>
              <p className="text-white font-medium">{selectedIncident.headline}</p>
              <div className="text-[#8b949e] pt-1 border-t border-slate-900 flex justify-between">
                <span>Illustrative trip count: <strong>{selectedIncident.affected_trips} sample bookings</strong></span>
                <span>Illustrative passenger count: <strong>{selectedIncident.passengers.length} sample travelers</strong></span>
              </div>
            </div>

            <div className="p-3.5 rounded-lg bg-[#0f1115] border border-[#30363d] space-y-2 text-ui-xs">
              <span className="text-[#8b949e] block font-semibold">Tracked Travelers in Hazard Radius:</span>
              {selectedIncident.passengers.map((p) => (
                <div key={p} className="flex justify-between items-center text-white">
                  <span>👤 {p}</span>
                  <span className="text-[#3fb950] font-mono">Sample beacon status (no live GPS)</span>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-xl border border-[#30363d] bg-[#161b22] p-5 space-y-3 text-ui-xs">
            <h3 className="text-ui-sm font-semibold text-white flex items-center gap-2">
              <Radio className="h-4 w-4 text-[#58a6ff]" />
              Consular Registry (STEP) Draft Manifest (Sample)
            </h3>
            <div className="p-4 rounded-lg bg-[#0f1115] border border-[#30363d] space-y-2 font-mono">
              <div className="flex justify-between items-center gap-2 text-[#58a6ff]">
                <span>Case: {manifest.consular_case_number}</span>
                <span className="text-amber-300 border border-amber-500/30 bg-amber-950/40 px-2 py-0.5 rounded text-[10px]">MANIFEST DRAFTED (SIMULATED — NOT TRANSMITTED)</span>
              </div>
              <p className="text-[#8b949e]">Embassy workflow placeholder (sample copy): a manifest of 2 sample travelers with illustrative contact lines and an unverified sample location. This demo cannot register or transmit anything externally.</p>
            </div>
          </div>
        </div>
      )}

      {/* Routing Tab */}
      {activeSubTab === 'routing' && (
        <div className="rounded-xl border border-[#30363d] bg-[#161b22] p-5 space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="text-ui-sm font-semibold text-white flex items-center gap-2">
              <Navigation className="h-4 w-4 text-[#58a6ff]" />
              Sample Evacuation Itinerary Preview: {manifest.manifest_id}
            </h3>
            <span className="text-ui-xs font-mono font-bold text-white bg-slate-800 px-3 py-1 rounded-lg">
              Illustrative total: USD {manifest.total_cost.toLocaleString()}
            </span>
          </div>

          <div className="space-y-3">
            {manifest.legs.map((l: any) => (
              <div key={l.leg} className="p-3.5 rounded-lg bg-[#0f1115] border border-[#30363d] space-y-2 text-ui-xs">
                <div className="flex justify-between items-center">
                  <span className="font-bold text-white flex items-center gap-2">
                    {l.leg === 1 ? <Car className="h-4 w-4 text-amber-400" /> : <Plane className="h-4 w-4 text-emerald-400" />}
                    Leg {l.leg}: {l.mode}
                  </span>
                  <span className="text-amber-300 font-mono font-semibold">Sample status: {l.status} (SIMULATED)</span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-[#8b949e]">
                  <div>Route: <strong className="text-white">{l.origin} → {l.destination}</strong></div>
                  <div>Departure: <strong className="text-white">{l.departure}</strong></div>
                  <div>Cost: <strong className="text-white font-mono">USD {l.cost.toLocaleString()}</strong></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Dispatch Tab */}
      {activeSubTab === 'dispatch' && (
        <div className="rounded-xl border border-[#30363d] bg-[#161b22] p-5 space-y-4">
          <h3 className="text-ui-sm font-semibold text-white flex items-center gap-2">
            <Car className="h-4 w-4 text-amber-400" />
            Sample Ground Driver Dispatch Console (Simulated)
          </h3>

          <div className="p-4 rounded-lg bg-[#0f1115] border border-[#30363d] space-y-3 text-ui-xs">
            <div className="flex justify-between items-center gap-2">
              <span className="font-bold text-white text-sm">Sample Dispatch Ref: {driverDispatch.dispatch_id}</span>
              <span className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 font-mono font-semibold">
                {driverDispatch.status}
              </span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-[#8b949e]">
              <div>Driver: <strong className="text-white">{driverDispatch.driver_name}</strong></div>
              <div>Phone: <strong className="text-white font-mono">{driverDispatch.driver_phone}</strong></div>
              <div>Vehicle: <strong className="text-white">{driverDispatch.vehicle}</strong></div>
              <div>Passenger Alert: <strong className="text-amber-300">SMS / WhatsApp broadcast simulated — nothing was sent</strong></div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
