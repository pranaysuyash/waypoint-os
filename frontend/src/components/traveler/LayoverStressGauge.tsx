'use client';

import React, { useState } from 'react';

export interface LayoverSegment {
  inboundFlight: string;
  connectingFlight: string;
  transitHub: string;
  scheduledMinutes: number;
  minimumSafeMinutes: number;
  terminalFrom?: string;
  terminalTo?: string;
}

interface LayoverStressGaugeProps {
  segment?: LayoverSegment;
  onAdvisorHelp?: () => void;
}

const DEFAULT_SEGMENT: LayoverSegment = {
  inboundFlight: 'BA 178 (JFK → LHR)',
  connectingFlight: 'BA 304 (LHR → CDG)',
  transitHub: 'London Heathrow (LHR)',
  scheduledMinutes: 50,
  minimumSafeMinutes: 90,
  terminalFrom: 'Terminal 5',
  terminalTo: 'Terminal 3',
};

export function LayoverStressGauge({ segment = DEFAULT_SEGMENT, onAdvisorHelp }: LayoverStressGaugeProps) {
  const [delayMinutes, setDelayMinutes] = useState<number>(0);

  const deplaningMinutes = 15;
  const transitMinutes = segment.terminalFrom !== segment.terminalTo ? 30 : 15;
  const securityMinutes = 25;
  const gateCutoffMinutes = 15;
  const totalFriction = deplaningMinutes + transitMinutes + securityMinutes + gateCutoffMinutes;

  const effectiveAvailable = Math.max(0, segment.scheduledMinutes - delayMinutes);
  const netCushion = effectiveAvailable - totalFriction;

  const isCritical = netCushion < 0 || effectiveAvailable < segment.minimumSafeMinutes * 0.7;
  const isTight = !isCritical && netCushion < 25;

  const statusColor = isCritical ? '#f85149' : isTight ? '#d29922' : '#3fb950';
  const statusLabel = isCritical
    ? `CRITICAL RISK: ${Math.abs(netCushion)}m Buffer Deficit`
    : isTight
      ? 'HIGH STRESS: 64% Baggage Misconnect Risk'
      : 'SAFE CUSHION: Low Friction Buffer';

  return (
    <div
      style={{
        background: '#0d1117',
        border: '1px solid #21262d',
        borderRadius: 16,
        padding: '24px',
        color: '#e6edf3',
        fontFamily: "'Inter', system-ui, sans-serif",
      }}
    >
      {/* Header */}
      <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12, marginBottom: 20 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
            <span
              style={{
                fontSize: 10.5,
                fontWeight: 700,
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
                padding: '3px 8px',
                borderRadius: 6,
                background: `${statusColor}22`,
                color: statusColor,
                border: `1px solid ${statusColor}44`,
              }}
            >
              Travel Physics · Hub Transit
            </span>
            <span style={{ fontSize: 12, color: '#8b949e' }}>
              {segment.transitHub}
            </span>
          </div>
          <h3 style={{ fontSize: 18, fontWeight: 700, margin: 0, color: '#f0f6fc', letterSpacing: '-0.02em' }}>
            Connection Stress & Minimum Buffer Gauge
          </h3>
          <p style={{ fontSize: 13, color: '#8b949e', margin: '4px 0 0 0' }}>
            Legal ticketing doesn't mean humanly feasible. Calculated for terminal changes, security re-screening, and boarding cutoffs.
          </p>
        </div>

        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: 24, fontWeight: 800, color: statusColor, fontFamily: "'JetBrains Mono', monospace" }}>
            {netCushion >= 0 ? `+${netCushion}m` : `${netCushion}m`}
          </div>
          <div style={{ fontSize: 11, color: '#8b949e' }}>Net Safety Cushion</div>
        </div>
      </div>

      {/* Flight Transfer Nodes */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: 12,
          padding: '14px 16px',
          background: '#161b22',
          borderRadius: 12,
          border: '1px solid #30363d',
          marginBottom: 20,
        }}
      >
        <div>
          <div style={{ fontSize: 11, color: '#8b949e', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Inbound Arrival</div>
          <div style={{ fontSize: 14, fontWeight: 600, color: '#f0f6fc', marginTop: 2 }}>{segment.inboundFlight}</div>
          <div style={{ fontSize: 12, color: '#39d0d8', marginTop: 2 }}>{segment.terminalFrom ?? 'Main Terminal'}</div>
        </div>
        <div style={{ borderLeft: '1px solid #21262d', paddingLeft: 12 }}>
          <div style={{ fontSize: 11, color: '#8b949e', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Connecting Outbound</div>
          <div style={{ fontSize: 14, fontWeight: 600, color: '#f0f6fc', marginTop: 2 }}>{segment.connectingFlight}</div>
          <div style={{ fontSize: 12, color: '#39d0d8', marginTop: 2 }}>{segment.terminalTo ?? 'Connecting Terminal'}</div>
        </div>
      </div>

      {/* Interactive Stress Breakdown Bar */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8, fontSize: 12 }}>
          <span style={{ color: '#8b949e' }}>
            Scheduled Layover: <strong style={{ color: '#f0f6fc' }}>{segment.scheduledMinutes}m</strong> · Recommended MCT: <strong style={{ color: '#f0f6fc' }}>{segment.minimumSafeMinutes}m</strong>
          </span>
          <span style={{ fontWeight: 600, color: statusColor }}>{statusLabel}</span>
        </div>

        {/* Visual Progress Bar */}
        <div style={{ width: '100%', height: 26, background: '#161b22', borderRadius: 8, overflow: 'hidden', display: 'flex', border: '1px solid #30363d' }}>
          <div
            title={`Taxi & Deplaning: ${deplaningMinutes}m`}
            style={{
              width: `${(deplaningMinutes / (segment.scheduledMinutes || 90)) * 100}%`,
              background: '#238636',
              height: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 10,
              color: '#ffffff',
              fontWeight: 600,
            }}
          >
            Taxi {deplaningMinutes}m
          </div>
          <div
            style={{
              width: `${(transitMinutes / (segment.scheduledMinutes || 90)) * 100}%`,
              background: '#1f6feb',
              height: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 10,
              color: '#ffffff',
              fontWeight: 600,
            }}
          >
            Transit {transitMinutes}m
          </div>
          <div
            style={{
              width: `${(securityMinutes / (segment.scheduledMinutes || 90)) * 100}%`,
              background: '#8957e5',
              height: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 10,
              color: '#ffffff',
              fontWeight: 600,
            }}
          >
            Security {securityMinutes}m
          </div>
          <div
            style={{
              width: `${(gateCutoffMinutes / (segment.scheduledMinutes || 90)) * 100}%`,
              background: '#da3633',
              height: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 10,
              color: '#ffffff',
              fontWeight: 600,
            }}
          >
            Gate {gateCutoffMinutes}m
          </div>
          {netCushion > 0 ? (
            <div
              style={{
                flex: 1,
                background: 'rgba(57,208,216,0.2)',
                borderLeft: '1px dashed #39d0d8',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 10,
                color: '#39d0d8',
                fontWeight: 600,
              }}
            >
              +{netCushion}m Buffer
            </div>
          ) : null}
        </div>

        {/* Legend */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 14, marginTop: 10, fontSize: 11, color: '#8b949e' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <span style={{ width: 8, height: 8, borderRadius: 2, background: '#238636' }} /> Taxi & Deplane ({deplaningMinutes}m)
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <span style={{ width: 8, height: 8, borderRadius: 2, background: '#1f6feb' }} /> Inter-Terminal Transit ({transitMinutes}m)
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <span style={{ width: 8, height: 8, borderRadius: 2, background: '#8957e5' }} /> Border & Rescreening ({securityMinutes}m)
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <span style={{ width: 8, height: 8, borderRadius: 2, background: '#da3633' }} /> Boarding Cutoff ({gateCutoffMinutes}m)
          </span>
        </div>
      </div>

      {/* Root Delay Interactive Simulator */}
      <div
        style={{
          background: 'rgba(22,27,34,0.7)',
          border: '1px solid #21262d',
          borderRadius: 12,
          padding: '16px',
          marginBottom: 16,
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
          <span style={{ fontSize: 12, fontWeight: 600, color: '#c9d1d9' }}>
            Simulate Inbound Flight Runway/Holding Delay:
          </span>
          <span
            style={{
              fontSize: 12,
              fontWeight: 700,
              fontFamily: "'JetBrains Mono', monospace",
              color: delayMinutes === 0 ? '#8b949e' : delayMinutes > 30 ? '#f85149' : '#d29922',
            }}
          >
            +{delayMinutes} minutes delay
          </span>
        </div>
        <input
          type="range"
          min="0"
          max="60"
          step="5"
          value={delayMinutes}
          onChange={(e) => setDelayMinutes(Number(e.target.value))}
          style={{ width: '100%', cursor: 'pointer', accentColor: '#39d0d8' }}
          aria-label="Simulate inbound flight delay"
        />
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: '#6e7681', marginTop: 4 }}>
          <span>On-time (+0m)</span>
          <span>15m Runway queue</span>
          <span>30m Holding stack</span>
          <span>60m Critical misconnect</span>
        </div>
      </div>

      {/* The Waypoint Advantage Note */}
      <div
        style={{
          display: 'flex',
          gap: 12,
          padding: '12px 16px',
          borderRadius: 10,
          background: 'rgba(57,208,216,0.06)',
          border: '1px solid rgba(57,208,216,0.2)',
          fontSize: 12.5,
          lineHeight: 1.5,
          color: '#c9d1d9',
        }}
      >
        <span style={{ color: '#39d0d8', fontSize: 16 }}>🛡️</span>
        <div>
          <strong style={{ color: '#39d0d8' }}>How a Waypoint Advisor protects this:</strong>{' '}
          {isCritical
            ? 'We automatically re-ticket to a flight with a 110-minute buffer or add airside VIP tarmac escort to eliminate security queues, preventing stranded luggage in London.'
            : 'We pre-assign seats in front cabin rows for swift deplaning and monitor real-time tail number telemetry to re-route proactively before you land.'}
        </div>
      </div>
    </div>
  );
}
