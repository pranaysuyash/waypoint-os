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

type CrisisSubTab = 'radar' | 'routing' | 'dispatch';

export function CrisisEvacuationPanel() {
  const [activeSubTab, setActiveSubTab] = useState<CrisisSubTab>('radar');

  // Crisis state
  const [selectedIncident, setSelectedIncident] = useState({
    id: 'CRISIS-JP-001',
    headline: 'Typhoon Category 5 Grounding Commercial Flights (Tokyo / Kanto)',
    severity: 'CRITICAL EVACUATION',
    affected_trips: 2,
    passengers: ['Alex Morgan', 'Taylor Morgan'],
    safe_destination: 'London Heathrow (LHR)',
  });

  // Evacuation manifest state
  const [manifest, setManifest] = useState<any>({
    manifest_id: 'EVAC-JP-88910',
    assembly_point: 'Park Hyatt Tokyo Main Lobby (Verified Safe Zone)',
    is_charter_confirmed: true,
    total_cost: 20300.0,
    consular_case_number: 'DOS-EMERG-JP-994',
    legs: [
      {
        leg: 1,
        mode: 'Overland Armored Escort Convoy',
        origin: 'Park Hyatt Tokyo',
        destination: 'Secondary Tactical Regional Airfield',
        departure: 'T+01:30 (Immediate)',
        status: 'DISPATCHED',
        cost: 1800,
      },
      {
        leg: 2,
        mode: 'Private Jet Air Charter (Citation Latitude)',
        origin: 'Secondary Tactical Regional Airfield',
        destination: 'London Heathrow (LHR)',
        departure: 'T+04:00 (Slot Guaranteed)',
        status: 'CONFIRMED',
        cost: 18500,
      },
    ],
  });

  // Dispatch state
  const [driverDispatch, setDriverDispatch] = useState<any>({
    dispatch_id: 'DRV-99418',
    driver_name: 'Marcus Vance (Certified Close Protection Driver)',
    driver_phone: '+81-90-555-0192',
    vehicle: 'Armored Mercedes V-Class (Plate: 品川 300 84-92)',
    status: 'EN ROUTE TO SHELTER (ETA: 12 Mins)',
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
                Crisis Evacuation & Irregular Disruption Dispatch
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#f85149]/20 text-[#f85149] font-medium border border-[#f85149]/30">
                  PER-950889 / PER-950898
                </span>
              </h2>
              <p className="text-ui-xs text-[#8b949e]">
                Geofenced crisis event radar, multi-modal emergency evacuation routing, and live ground driver dispatch coordination.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-[#0f1115] border border-[#f85149]/40 text-ui-xs text-[#f85149]">
            <Radio className="h-3.5 w-3.5 animate-pulse" />
            <span>Crisis Beacon Active</span>
          </div>
        </div>
      </div>

      {/* Sub tabs */}
      <div className="flex gap-2 p-1.5 bg-[#0f1115] rounded-xl border border-[#30363d]">
        {[
          { key: 'radar', label: 'Geofence Crisis Radar', icon: Radio },
          { key: 'routing', label: 'Multi-Modal Escape Routing Manifest', icon: Navigation },
          { key: 'dispatch', label: 'Live Ground Driver Dispatch', icon: Car },
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
              Active Incident Alert
            </h3>
            <div className="p-3.5 rounded-lg bg-[#0f1115] border border-[#f85149]/40 space-y-2 text-ui-xs">
              <div className="flex justify-between items-center text-[#f85149] font-bold">
                <span>{selectedIncident.id}</span>
                <span className="bg-[#f85149]/20 px-2 py-0.5 rounded font-mono">{selectedIncident.severity}</span>
              </div>
              <p className="text-white font-medium">{selectedIncident.headline}</p>
              <div className="text-[#8b949e] pt-1 border-t border-slate-900 flex justify-between">
                <span>Affected Active Trips: <strong>{selectedIncident.affected_trips} Bookings</strong></span>
                <span>Passengers at Risk: <strong>{selectedIncident.passengers.length} Pax</strong></span>
              </div>
            </div>

            <div className="p-3.5 rounded-lg bg-[#0f1115] border border-[#30363d] space-y-2 text-ui-xs">
              <span className="text-[#8b949e] block font-semibold">Tracked Travelers in Hazard Radius:</span>
              {selectedIncident.passengers.map((p) => (
                <div key={p} className="flex justify-between items-center text-white">
                  <span>👤 {p}</span>
                  <span className="text-[#3fb950] font-mono">Beacon: Safe in Shelter (GPS Verified)</span>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-xl border border-[#30363d] bg-[#161b22] p-5 space-y-3 text-ui-xs">
            <h3 className="text-ui-sm font-semibold text-white flex items-center gap-2">
              <Radio className="h-4 w-4 text-[#58a6ff]" />
              Consular Registry (STEP) Transmit
            </h3>
            <div className="p-4 rounded-lg bg-[#0f1115] border border-[#30363d] space-y-2 font-mono">
              <div className="flex justify-between items-center text-[#58a6ff]">
                <span>Case: {manifest.consular_case_number}</span>
                <span className="text-[#3fb950]">TRANSMITTED TO EMBASSY DESK</span>
              </div>
              <p className="text-[#8b949e]">U.S. Embassy Tokyo Liaison: Manifest of 2 citizens registered with emergency contact lines and verified shelter coordinates.</p>
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
              Multi-Modal Evacuation Itinerary Manifest: {manifest.manifest_id}
            </h3>
            <span className="text-ui-xs font-mono font-bold text-white bg-slate-800 px-3 py-1 rounded-lg">
              Total Budget: USD {manifest.total_cost.toLocaleString()}
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
                  <span className="text-[#3fb950] font-mono font-semibold">{l.status}</span>
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
            Live Ground Driver Dispatch Console
          </h3>

          <div className="p-4 rounded-lg bg-[#0f1115] border border-[#30363d] space-y-3 text-ui-xs">
            <div className="flex justify-between items-center">
              <span className="font-bold text-white text-sm">Dispatch Ref: {driverDispatch.dispatch_id}</span>
              <span className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 font-mono font-semibold">
                {driverDispatch.status}
              </span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-[#8b949e]">
              <div>Driver: <strong className="text-white">{driverDispatch.driver_name}</strong></div>
              <div>Phone: <strong className="text-white font-mono">{driverDispatch.driver_phone}</strong></div>
              <div>Vehicle: <strong className="text-white">{driverDispatch.vehicle}</strong></div>
              <div>Passenger Alert: <strong className="text-emerald-400">SMS / WhatsApp Broadcast Sent</strong></div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
