'use client';

import React, { useState } from 'react';
import { RotateCcw, AlertTriangle, CheckCircle, Clock, MapPin, ShieldAlert } from 'lucide-react';

interface JourneyNode {
  id: string;
  type: 'FLIGHT' | 'TRANSFER' | 'HOTEL' | 'ACTIVITY' | 'DINING';
  title: string;
  scheduledTime: string;
  location: string;
  provider: string;
  minBufferMinutes: number;
}

const SAMPLE_JOURNEY_NODES: JourneyNode[] = [
  { id: 'node_1', type: 'FLIGHT', title: 'BA 178 (LHR -> HND)', scheduledTime: '08:00 - 14:00 GMT', location: 'Tokyo Haneda (HND)', provider: 'British Airways', minBufferMinutes: 60 },
  { id: 'node_2', type: 'TRANSFER', title: 'Co-Terminal Transfer (HND -> NRT)', scheduledTime: '14:45 - 16:45 JST', location: 'Tokyo Express Link', provider: 'Tokyo VIP Shuttles', minBufferMinutes: 120 },
  { id: 'node_3', type: 'FLIGHT', title: 'JL 809 (NRT -> TPE)', scheduledTime: '17:30 - 20:15 JST', location: 'Narita International', provider: 'Japan Airlines', minBufferMinutes: 60 },
  { id: 'node_4', type: 'HOTEL', title: 'Mandarin Oriental Taipei Check-in', scheduledTime: '21:30 JST', location: 'Taipei Songshan', provider: 'Mandarin Oriental', minBufferMinutes: 30 },
  { id: 'node_5', type: 'DINING', title: 'RAW Taipei Michelin Dinner', scheduledTime: '22:15 JST', location: 'Dazhi Taipei', provider: 'Chef André Chiang', minBufferMinutes: 45 },
];

export function JourneyGraphVisualizer() {
  const [delayMinutes, setDelayMinutes] = useState<number>(0);
  const [selectedNode, setSelectedNode] = useState<string>('node_1');

  const getNodeStatus = (nodeId: string) => {
    if (delayMinutes === 0) return { status: 'healthy', label: 'On Schedule' };
    if (nodeId === 'node_1') return { status: 'delayed', label: '+' + delayMinutes + 'm Root Delay' };

    if (nodeId === 'node_2') {
      return delayMinutes > 45
        ? { status: 'critical', label: 'Buffer Deficit (-' + (delayMinutes - 45) + 'm)' }
        : { status: 'warning', label: 'Cushion Reduced' };
    }
    if (nodeId === 'node_3') {
      return delayMinutes > 45
        ? { status: 'critical', label: 'MCT Broken · Misconnection Risk' }
        : { status: 'healthy', label: 'Connectable' };
    }
    if (nodeId === 'node_4' || nodeId === 'node_5') {
      return delayMinutes > 90
        ? { status: 'critical', label: 'Late Arrival · Late Check-in' }
        : delayMinutes > 45
        ? { status: 'warning', label: 'Delayed Arrival' }
        : { status: 'healthy', label: 'Feasible' };
    }
    return { status: 'healthy', label: 'Normal' };
  };

  return (
    <div className="rounded-xl border border-border bg-card p-5 space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-border">
        <div>
          <h3 className="text-base font-semibold text-foreground flex items-center gap-2">
            <MapPin className="h-5 w-5 text-primary" />
            Journey Dependency Graph (JDG) & Disruption Simulator
          </h3>
          <p className="text-ui-xs text-muted-foreground">
            Topological DAG tracking physical buffers, Minimum Connecting Times (MCT), and co-terminal airport links.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setDelayMinutes(0)}
            className="px-3 py-1.5 rounded-lg border border-border text-ui-xs font-medium text-muted-foreground hover:text-foreground hover:bg-muted flex items-center gap-1.5 transition-colors"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            Reset
          </button>
        </div>
      </div>

      <div className="p-4 rounded-xl bg-background border border-border space-y-3">
        <div className="flex justify-between items-center text-ui-xs font-medium">
          <span className="text-muted-foreground flex items-center gap-1.5">
            <Clock className="h-4 w-4 text-primary" />
            Simulate Root Delay on Inbound Leg (BA 178):
          </span>
          <span className={`px-2.5 py-0.5 rounded-md font-mono font-bold ${
            delayMinutes === 0 ? 'bg-muted text-muted-foreground' : delayMinutes > 60 ? 'bg-destructive/20 text-destructive border border-destructive/40' : 'bg-amber-500/20 text-amber-400 border border-amber-500/40'
          }`}>
            +{delayMinutes} minutes
          </span>
        </div>
        <input
          type="range"
          min="0"
          max="180"
          step="15"
          value={delayMinutes}
          onChange={(e) => setDelayMinutes(Number(e.target.value))}
          className="w-full accent-primary cursor-pointer"
        />
        <div className="flex justify-between text-ui-2xs text-muted-foreground font-mono">
          <span>0m (On Time)</span>
          <span>+30m (Absorbed)</span>
          <span>+60m (MCT Deficit)</span>
          <span>+120m (Critical Cascade)</span>
          <span>+180m (Cancelled)</span>
        </div>
      </div>

      <div className="space-y-3">
        <h4 className="text-ui-xs font-semibold text-muted-foreground uppercase tracking-wider">
          Itinerary Dependency Chain
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
          {SAMPLE_JOURNEY_NODES.map((node) => {
            const nodeImpact = getNodeStatus(node.id);
            const isSelected = selectedNode === node.id;
            return (
              <div
                key={node.id}
                onClick={() => setSelectedNode(node.id)}
                className={`p-3.5 rounded-xl border transition-all cursor-pointer flex flex-col justify-between space-y-2 ${
                  isSelected ? 'ring-2 ring-primary border-transparent' : 'border-border bg-background hover:border-primary/50'
                } ${
                  nodeImpact.status === 'critical' ? 'border-destructive/60 bg-destructive/5' : nodeImpact.status === 'warning' ? 'border-amber-500/50 bg-amber-500/5' : ''
                }`}
              >
                <div className="space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="px-2 py-0.5 rounded text-ui-2xs font-mono font-bold bg-muted text-foreground">
                      {node.type}
                    </span>
                    {nodeImpact.status === 'critical' ? (
                      <ShieldAlert className="h-4 w-4 text-destructive" />
                    ) : nodeImpact.status === 'warning' ? (
                      <AlertTriangle className="h-4 w-4 text-amber-400" />
                    ) : (
                      <CheckCircle className="h-4 w-4 text-emerald-400" />
                    )}
                  </div>
                  <h5 className="text-ui-xs font-semibold text-foreground line-clamp-2">
                    {node.title}
                  </h5>
                  <p className="text-ui-2xs text-muted-foreground">
                    {node.location}
                  </p>
                </div>

                <div className="pt-2 border-t border-border/50 space-y-1">
                  <span className={`block text-ui-2xs font-medium ${
                    nodeImpact.status === 'critical' ? 'text-destructive' : nodeImpact.status === 'warning' ? 'text-amber-400' : 'text-emerald-400'
                  }`}>
                    {nodeImpact.label}
                  </span>
                  <span className="block text-ui-2xs font-mono text-muted-foreground">
                    Min Buffer: {node.minBufferMinutes}m
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {delayMinutes > 45 && (
        <div className="p-4 rounded-xl bg-destructive/10 border border-destructive/30 space-y-2 text-ui-xs">
          <div className="flex items-center gap-2 text-destructive font-semibold">
            <AlertTriangle className="h-4 w-4" />
            Automatic Downstream Disruption Protocol Triggered
          </div>
          <p className="text-foreground/90 text-ui-xs">
            A +{delayMinutes}m delay on <span className="font-semibold text-foreground">BA 178</span> reduces the Haneda to Narita co-terminal transfer window below the mandatory 120-minute safety threshold. Rebooking recommendation: Protected connection on <span className="font-mono text-primary">JL 811 (Dep 19:15 JST)</span>.
          </p>
        </div>
      )}
    </div>
  );
}
