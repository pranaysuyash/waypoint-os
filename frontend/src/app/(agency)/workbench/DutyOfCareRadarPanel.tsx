'use client';

import React, { useState } from 'react';
import { Shield, AlertTriangle, Users, Radio, Send } from 'lucide-react';
import SimulatedBadge from '@/components/ui/SimulatedBadge';

/**
 * GM-01 honesty fix: threat incidents, traveler beacons, and consular
 * manifests here are fixture data from a deterministic simulator — there is
 * no live geofence feed and nothing is broadcast.
 */

export default function DutyOfCareRadarPanel() {
  const [isLoading, setIsLoading] = useState(false);
  const [cockpit, setCockpit] = useState<{
    cockpit_id: string;
    active_threat_incidents: Array<{ incident_id: string; headline: string; severity: string; geofence: { latitude: number; longitude: number; radius_km: number } }>;
    traveler_metrics: { total_in_hazard_zones: number; accounted_for: number; unaccounted: number };
    step_consular_manifests_compiled: number;
    ground_dispatches_active: number;
    sos_broadcast_payload: string;
  } | null>(null);

  const handleFetchCockpit = async () => {
    setIsLoading(true);
    try {
      const res = await fetch('/api/v1/duty-of-care-radar/cockpit/summary', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agency_id: 'AGENCY-ENTERPRISE-001' }),
      });
      if (res.ok) {
        const data = await res.json();
        setCockpit(data.cockpit);
      }
    } catch {
      // Fallback local preview
      setCockpit({
        cockpit_id: 'DOCKPIT-E-001',
        active_threat_incidents: [
          {
            incident_id: 'INC-TYPHOON-TYO',
            headline: 'Super Typhoon Approaching Tokyo Bay (HND / NRT Ground Stop)',
            severity: 'critical_evacuation',
            geofence: { latitude: 35.6762, longitude: 139.6503, radius_km: 150.0 },
          },
        ],
        traveler_metrics: {
          total_in_hazard_zones: 2,
          accounted_for: 1,
          unaccounted: 1,
        },
        step_consular_manifests_compiled: 2,
        ground_dispatches_active: 1,
        sos_broadcast_payload: 'Sample SOS payload preview: reply SAFE for workflow testing only.',
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="p-4 rounded-xl border border-border bg-card space-y-4">
      <div className="flex items-center justify-between gap-2">
        <h4 className="text-sm font-semibold text-foreground flex items-center gap-2">
          <Shield className="h-4 w-4 text-emerald-500" />
          Enterprise Duty-of-Care & Consular Geofence Radar (Simulator)
        </h4>
        <div className="flex items-center gap-2 shrink-0">
          <SimulatedBadge label="Simulated" />
          <span className="text-[10px] font-mono bg-emerald-500/10 text-emerald-500 px-2 py-0.5 rounded">HORIZON 3 · ISO 31030 CRISIS RADAR SIM</span>
        </div>
      </div>

      <div className="flex items-center justify-between gap-3">
        <p className="text-xs text-muted-foreground">
          Simulated threat geofence monitoring, sample passenger safety beacons, STEP consular manifest drafts, and armored transport dispatch fixtures. No live feeds — nothing is sent.
        </p>
        <button
          onClick={handleFetchCockpit}
          disabled={isLoading}
          className="py-2 px-3.5 rounded-lg bg-emerald-600 text-white text-xs font-semibold hover:bg-emerald-700 flex items-center gap-1.5 shrink-0"
        >
          <Radio className={`h-3.5 w-3.5 ${isLoading ? 'animate-pulse' : ''}`} />
          {isLoading ? 'Loading sample fixtures...' : 'Load sample threat fixtures'}
        </button>
      </div>

      {cockpit && (
        <div className="space-y-3 pt-2">
          <div className="grid grid-cols-4 gap-2 text-xs">
            <div className="p-2.5 rounded bg-muted/40 border border-border">
              <span className="text-[10px] text-muted-foreground block">Sample travelers in hazard radius</span>
              <span className="font-bold text-foreground text-sm flex items-center gap-1">
                <Users className="h-3.5 w-3.5 text-amber-500" />
                {cockpit.traveler_metrics.total_in_hazard_zones} Travelers
              </span>
            </div>
            <div className="p-2.5 rounded bg-muted/40 border border-border">
              <span className="text-[10px] text-muted-foreground block">Submitted beacon status</span>
              <span className="font-bold text-emerald-500 text-sm">{cockpit.traveler_metrics.accounted_for} Sample status</span>
            </div>
            <div className="p-2.5 rounded bg-muted/40 border border-border">
              <span className="text-[10px] text-muted-foreground block">STEP manifest drafts</span>
              <span className="font-bold text-primary text-sm">{cockpit.step_consular_manifests_compiled} Not submitted</span>
            </div>
            <div className="p-2.5 rounded bg-muted/40 border border-border">
              <span className="text-[10px] text-muted-foreground block">Dispatch fixtures</span>
              <span className="font-bold text-foreground text-sm">{cockpit.ground_dispatches_active} Not dispatched</span>
            </div>
          </div>

          <div className="p-3 rounded-lg border border-red-500/20 bg-red-500/5 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-red-500 flex items-center gap-1.5">
                <AlertTriangle className="h-3.5 w-3.5" />
                SAMPLE THREAT FIXTURE: {cockpit.active_threat_incidents[0]?.headline}
              </span>
              <span className="text-[10px] font-mono bg-red-500/20 text-red-500 px-2 py-0.5 rounded">SAMPLE RADIUS</span>
            </div>
            <div className="p-2.5 rounded bg-background/80 border border-border text-xs flex items-center justify-between">
              <div className="space-y-0.5">
                <span className="text-[10px] text-muted-foreground block font-mono">SOS PAYLOAD PREVIEW · NOT SENT</span>
                <span className="text-foreground">{cockpit.sos_broadcast_payload}</span>
              </div>
              <button className="px-3 py-1.5 bg-primary text-primary-foreground rounded text-xs font-semibold shrink-0 flex items-center gap-1">
                <Send className="h-3 w-3" />
                Simulate SOS Broadcast
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
