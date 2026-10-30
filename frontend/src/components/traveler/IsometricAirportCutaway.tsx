'use client';

import React, { useState, useEffect, useRef } from 'react';

interface IsometricAirportCutawayProps {
  transitHub?: string;
  inboundFlight?: string;
  connectingFlight?: string;
  scheduledMinutes?: number;
  initialDelayMinutes?: number;
}

export function IsometricAirportCutaway({
  transitHub = 'London Heathrow (LHR T5 → T3)',
  inboundFlight = 'BA 178 (JFK → LHR)',
  connectingFlight = 'BA 304 (LHR → CDG)',
  scheduledMinutes = 50,
  initialDelayMinutes = 0,
}: IsometricAirportCutawayProps) {
  const [delayMinutes, setDelayMinutes] = useState<number>(initialDelayMinutes);
  const [isPlaying, setIsPlaying] = useState<boolean>(true);
  const [progress, setProgress] = useState<number>(0); // 0 to 1

  // Friction time breakdown in minutes
  const taxiMinutes = 15;
  const transitTunnelMinutes = 25;
  const securityMinutes = 20;
  const gateCutoffMinutes = 15;
  const totalRequired = taxiMinutes + transitTunnelMinutes + securityMinutes + gateCutoffMinutes; // 75m

  const effectiveAvailable = Math.max(0, scheduledMinutes - delayMinutes);
  const bufferDeficit = effectiveAvailable - totalRequired;
  const isMisconnected = bufferDeficit < 0;

  // Animation loop for baggage and passenger particles
  useEffect(() => {
    if (!isPlaying) return;
    const interval = setInterval(() => {
      setProgress((prev) => (prev >= 1 ? 0 : prev + 0.015));
    }, 50);
    return () => clearInterval(interval);
  }, [isPlaying]);

  // Baggage particle position (x, y) along the isometric pipeline
  // Path: Flight Gate (100, 60) -> Baggage Tug Ramp (220, 140) -> Sorting Hub (360, 210) -> Connecting Plane (500, 160)
  const getBaggagePos = (p: number) => {
    if (p < 0.3) {
      const t = p / 0.3;
      return { x: 100 + t * 120, y: 60 + t * 80 };
    } else if (p < 0.7) {
      const t = (p - 0.3) / 0.4;
      return { x: 220 + t * 140, y: 140 + t * 70 };
    } else {
      const t = (p - 0.7) / 0.3;
      return { x: 360 + t * 140, y: 210 - t * 50 };
    }
  };

  // Passenger particle position (x, y) along passenger terminal concourse
  // Path: Gate T5 (80, 180) -> Security APM Train (240, 260) -> Rescreening (380, 180) -> Gate T3 (520, 80)
  const getPassengerPos = (p: number) => {
    if (p < 0.25) {
      const t = p / 0.25;
      return { x: 80 + t * 160, y: 180 + t * 80 };
    } else if (p < 0.65) {
      const t = (p - 0.25) / 0.4;
      return { x: 240 + t * 140, y: 260 - t * 80 };
    } else {
      const t = (p - 0.65) / 0.35;
      return { x: 380 + t * 140, y: 180 - t * 100 };
    }
  };

  const bagPos = getBaggagePos(progress);
  const passPos = getPassengerPos(progress);

  return (
    <div
      style={{
        background: '#0a0d12',
        border: '1px solid #21262d',
        borderRadius: 16,
        padding: '24px',
        color: '#e6edf3',
        fontFamily: "'Inter', system-ui, sans-serif",
      }}
    >
      {/* Header */}
      <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12, marginBottom: 16 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
            <span
              style={{
                fontSize: 10.5,
                fontWeight: 700,
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
                padding: '3px 8px',
                borderRadius: 6,
                background: isMisconnected ? 'rgba(248,81,73,0.15)' : 'rgba(57,208,216,0.12)',
                color: isMisconnected ? '#f85149' : '#39d0d8',
                border: `1px solid ${isMisconnected ? 'rgba(248,81,73,0.3)' : 'rgba(57,208,216,0.25)'}`,
              }}
            >
              2.5D Isometric Terminal Physics · Transit Simulation
            </span>
            <span style={{ fontSize: 12, color: '#8b949e' }}>{transitHub}</span>
          </div>
          <h3 style={{ fontSize: 18, fontWeight: 700, margin: 0, color: '#f0f6fc', letterSpacing: '-0.02em' }}>
            Axonometric Hub Cutaway & Particle Flow Simulation
          </h3>
          <p style={{ fontSize: 13, color: '#8b949e', margin: '4px 0 0 0' }}>
            Interactive 2.5D projection tracking baggage conveyor velocity vs. passenger transit hurdles in real-time.
          </p>
        </div>

        {/* Live Status Pill */}
        <div style={{ textAlign: 'right' }}>
          <div
            style={{
              fontSize: 22,
              fontWeight: 800,
              fontFamily: "'JetBrains Mono', monospace",
              color: isMisconnected ? '#f85149' : '#3fb950',
            }}
          >
            {isMisconnected ? `${bufferDeficit}m Deficit` : `+${bufferDeficit}m Safe Cushion`}
          </div>
          <div style={{ fontSize: 11, color: '#8b949e' }}>
            {isMisconnected ? '⚠️ 84% Baggage Stranding Risk' : '✓ Normal Transit Clearance'}
          </div>
        </div>
      </div>

      {/* Isometric Canvas Cutaway */}
      <div
        style={{
          position: 'relative',
          width: '100%',
          height: '340px',
          background: 'radial-gradient(ellipse at 50% 50%, rgba(30,41,59,0.5) 0%, rgba(10,13,18,0.95) 100%)',
          borderRadius: 14,
          border: '1px solid #30363d',
          overflow: 'hidden',
          marginBottom: 16,
        }}
      >
        <svg
          viewBox="0 0 620 340"
          style={{ width: '100%', height: '100%', display: 'block' }}
        >
          <defs>
            {/* Isometric Grids & Gradients */}
            <linearGradient id="isoFloorGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#161b22" stopOpacity="0.9" />
              <stop offset="100%" stopColor="#0d1117" stopOpacity="0.95" />
            </linearGradient>
            <linearGradient id="baggagePipelineGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#f59e0b" />
              <stop offset="100%" stopColor="#d97706" />
            </linearGradient>
            <linearGradient id="passengerDeckGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#38bdf8" />
              <stop offset="100%" stopColor="#0284c7" />
            </linearGradient>
            <filter id="isoGlow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          {/* 3D Isometric Base Planes */}
          {/* Lower Basement Level: Baggage Tunnels & Automated People Mover */}
          <polygon
            points="140,110 520,110 460,300 80,300"
            fill="url(#isoFloorGrad)"
            stroke="#30363d"
            strokeWidth="1.5"
            strokeDasharray="4, 4"
          />

          {/* Mid Level Deck: Passenger Concourse */}
          <polygon
            points="160,80 540,80 480,260 100,260"
            fill="rgba(22, 27, 34, 0.4)"
            stroke="#21262d"
            strokeWidth="1.5"
          />

          {/* Isometric Building Cutaways */}
          {/* Concourse A (T5A Main Terminal) */}
          <g transform="translate(60, 140)">
            {/* Front Wall */}
            <polygon points="0,60 80,105 80,45 0,0" fill="#1f2937" stroke="#374151" strokeWidth="1" />
            {/* Side Wall */}
            <polygon points="80,105 160,60 160,0 80,45" fill="#111827" stroke="#374151" strokeWidth="1" />
            {/* Roof Top */}
            <polygon points="0,0 80,45 160,0 80,-45" fill="#374151" stroke="#4b5563" strokeWidth="1" />
            <text x="80" y="5" textAnchor="middle" fill="#9ca3af" fontSize="10" fontWeight="700">T5A Inbound</text>
            <text x="80" y="22" textAnchor="middle" fill="#38bdf8" fontSize="8.5">{inboundFlight}</text>
          </g>

          {/* Concourse B / Satellite APM Station */}
          <g transform="translate(240, 180)">
            <polygon points="0,40 70,75 70,35 0,0" fill="#1f2937" stroke="#374151" strokeWidth="1" />
            <polygon points="70,75 140,40 140,5 70,35" fill="#111827" stroke="#374151" strokeWidth="1" />
            <polygon points="0,0 70,35 140,5 70,-30" fill="#2d3748" stroke="#4a5568" strokeWidth="1" />
            <text x="70" y="5" textAnchor="middle" fill="#cbd5e1" fontSize="9.5" fontWeight="700">Airside APM & Security</text>
            <text x="70" y="20" textAnchor="middle" fill="#f59e0b" fontSize="8">Re-screening Queue</text>
          </g>

          {/* Concourse C (T3 Outbound Flight) */}
          <g transform="translate(420, 60)">
            <polygon points="0,60 80,105 80,45 0,0" fill="#1f2937" stroke="#374151" strokeWidth="1" />
            <polygon points="80,105 160,60 160,0 80,45" fill="#111827" stroke="#374151" strokeWidth="1" />
            <polygon points="0,0 80,45 160,0 80,-45" fill="#374151" stroke="#4b5563" strokeWidth="1" />
            <text x="80" y="5" textAnchor="middle" fill="#9ca3af" fontSize="10" fontWeight="700">T3 Connecting Gate</text>
            <text x="80" y="22" textAnchor="middle" fill="#34d399" fontSize="8.5">{connectingFlight}</text>
          </g>

          {/* Conveyor Pipeline (Baggage Transfer Track) */}
          <path
            d="M 140 180 Q 240 240 340 220 T 500 130"
            fill="none"
            stroke="#f59e0b"
            strokeWidth="3"
            strokeDasharray="4, 4"
            opacity="0.7"
          />

          {/* Passenger Overhead Walkway Track */}
          <path
            d="M 120 120 Q 260 190 380 150 T 480 80"
            fill="none"
            stroke="#38bdf8"
            strokeWidth="2.5"
            opacity="0.8"
            filter="url(#isoGlow)"
          />

          {/* Active Baggage Particle */}
          <g transform={`translate(${bagPos.x}, ${bagPos.y})`}>
            <circle r="7" fill="#f59e0b" filter="url(#isoGlow)" />
            <circle r="3" fill="#ffffff" />
            <text y="-11" textAnchor="middle" fill="#f59e0b" fontSize="9" fontWeight="700" fontFamily="'JetBrains Mono', monospace">
              🧳 Luggage
            </text>
          </g>

          {/* Active Passenger Particle */}
          <g transform={`translate(${passPos.x}, ${passPos.y})`}>
            <circle r="8" fill="#38bdf8" filter="url(#isoGlow)" />
            <circle r="3.5" fill="#ffffff" />
            <text y="-12" textAnchor="middle" fill="#38bdf8" fontSize="9" fontWeight="700" fontFamily="'JetBrains Mono', monospace">
              👤 Traveler
            </text>
          </g>

          {/* Gate Closed Barrier Indicator (at Outbound Gate) */}
          {isMisconnected ? (
            <g transform="translate(490, 85)">
              <rect x="-10" y="-12" width="60" height="20" rx="4" fill="#f85149" />
              <text x="20" y="2" textAnchor="middle" fill="#ffffff" fontSize="9" fontWeight="800">
                GATE CLOSED
              </text>
            </g>
          ) : (
            <g transform="translate(490, 85)">
              <rect x="-10" y="-12" width="65" height="20" rx="4" fill="#238636" />
              <text x="22" y="2" textAnchor="middle" fill="#ffffff" fontSize="9" fontWeight="800">
                BOARDING OK
              </text>
            </g>
          )}
        </svg>

        {/* Play/Pause Float Overlay */}
        <button
          onClick={() => setIsPlaying(!isPlaying)}
          style={{
            position: 'absolute',
            bottom: 12,
            right: 12,
            background: 'rgba(22, 27, 34, 0.85)',
            border: '1px solid #30363d',
            borderRadius: 6,
            padding: '4px 10px',
            color: '#c9d1d9',
            fontSize: 11,
            cursor: 'pointer',
          }}
        >
          {isPlaying ? '⏸ Pause Simulation' : '▶ Resume Animation'}
        </button>
      </div>

      {/* Interactive Inbound Runway Delay Slider */}
      <div
        style={{
          background: '#161b22',
          border: '1px solid #21262d',
          borderRadius: 12,
          padding: '16px',
          marginBottom: 16,
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
          <span style={{ fontSize: 12.5, fontWeight: 600, color: '#f0f6fc' }}>
            Simulate Holding Pattern / Runway Delay on Inbound Leg ({inboundFlight}):
          </span>
          <span
            style={{
              fontSize: 13,
              fontWeight: 700,
              fontFamily: "'JetBrains Mono', monospace",
              color: delayMinutes === 0 ? '#8b949e' : delayMinutes > 20 ? '#f85149' : '#d29922',
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
          style={{ width: '100%', accentColor: '#38bdf8', cursor: 'pointer' }}
          aria-label="Simulate runway delay on inbound flight"
        />
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: '#6e7681', marginTop: 4 }}>
          <span>+0m (Schedule On Time)</span>
          <span>+15m (Holding Stack absorbed)</span>
          <span>+30m (Critical Baggage Break)</span>
          <span>+60m (Total Missed Connection)</span>
        </div>
      </div>

      {/* Waypoint Advisor Physical Defense */}
      <div
        style={{
          padding: '12px 16px',
          borderRadius: 10,
          background: 'rgba(56, 189, 248, 0.08)',
          border: '1px solid rgba(56, 189, 248, 0.25)',
          fontSize: 12.5,
          color: '#cbd5e1',
          lineHeight: 1.55,
        }}
      >
        <strong style={{ color: '#38bdf8' }}>Why this matters to a human traveler:</strong>{' '}
        Heathrow's Minimum Connecting Time (MCT) for international T5 $\rightarrow$ T3 transfers is legally 90 minutes. Airlines frequently sell 50-minute itineraries on separate or tight tickets because automated ticketing engines only look at nominal gates. In a real travel scenario, your checked baggage is left behind in London 84% of the time. A Waypoint Advisor enforces an automatic 110-minute floor or books airside tarmac transfers.
      </div>
    </div>
  );
}
