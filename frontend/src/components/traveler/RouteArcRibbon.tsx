'use client';

import React, { useState } from 'react';

export interface RouteStop {
  id: string;
  code: string;
  city: string;
  country: string;
  stayDays?: number;
  highlight?: string;
}

export interface RouteLeg {
  fromId: string;
  toId: string;
  mode: 'flight' | 'train' | 'transfer' | 'ferry';
  durationText: string;
  notes: string;
  status: 'verified' | 'warning' | 'optimized';
}

interface RouteArcRibbonProps {
  stops?: RouteStop[];
  legs?: RouteLeg[];
}

const DEFAULT_STOPS: RouteStop[] = [
  { id: '1', code: 'JFK', city: 'New York', country: 'USA', highlight: 'Departure origin' },
  { id: '2', code: 'LHR', city: 'London', country: 'UK', highlight: '50m tight transit hub' },
  { id: '3', code: 'CDG', city: 'Paris', country: 'France', stayDays: 3, highlight: 'The Ritz Paris' },
  { id: '4', code: 'FCO', city: 'Rome', country: 'Italy', stayDays: 2, highlight: 'Hotel de Russie & Colosseum' },
];

const DEFAULT_LEGS: RouteLeg[] = [
  { fromId: '1', toId: '2', mode: 'flight', durationText: '7h 10m', notes: 'Transatlantic overnight BA178', status: 'verified' },
  { fromId: '2', toId: '3', mode: 'flight', durationText: '1h 20m', notes: 'Short haul BA304 — Tight 50m MCT connection', status: 'warning' },
  { fromId: '3', toId: '4', mode: 'train', durationText: '3h 15m (or flight)', notes: 'High-speed rail via Milan or 2h direct flight', status: 'optimized' },
];

export function RouteArcRibbon({
  stops = DEFAULT_STOPS,
  legs = DEFAULT_LEGS,
}: RouteArcRibbonProps) {
  const [selectedLegIndex, setSelectedLegIndex] = useState<number>(1);

  const selectedLeg = legs[selectedLegIndex] || legs[0];
  const fromStop = stops.find((s) => s.id === selectedLeg?.fromId) || stops[0];
  const toStop = stops.find((s) => s.id === selectedLeg?.toId) || stops[1];

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
      {/* Title */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
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
                background: 'rgba(57,208,216,0.12)',
                color: '#39d0d8',
                border: '1px solid rgba(57,208,216,0.25)',
              }}
            >
              Spatial Geography · Dynamic Journey Ribbon
            </span>
          </div>
          <h3 style={{ fontSize: 18, fontWeight: 700, margin: 0, color: '#f0f6fc', letterSpacing: '-0.02em' }}>
            Multi-Destination Route Flow & Transfer Arcs
          </h3>
          <p style={{ fontSize: 13, color: '#8b949e', margin: '4px 0 0 0' }}>
            Visual topological route mapping physical transit times and connection friction across stops.
          </p>
        </div>
        <div style={{ fontSize: 12, color: '#8b949e', fontFamily: "'JetBrains Mono', monospace" }}>
          {stops.length} Stops · {legs.length} Inter-city Legs
        </div>
      </div>

      {/* SVG Arc Visualizer */}
      <div
        style={{
          position: 'relative',
          padding: '32px 16px',
          background: 'radial-gradient(ellipse at 50% 50%, rgba(57,208,216,0.06) 0%, rgba(13,17,23,0) 80%), #161b22',
          borderRadius: 14,
          border: '1px solid #30363d',
          marginBottom: 20,
          overflowX: 'auto',
        }}
      >
        {/* Curved Connection Canvas (SVG) */}
        <div style={{ minWidth: 580, position: 'relative' }}>
          <svg
            viewBox="0 0 600 120"
            style={{ width: '100%', height: '110px', display: 'block', overflow: 'visible' }}
          >
            <defs>
              <linearGradient id="routeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#58a6ff" />
                <stop offset="40%" stopColor="#f85149" />
                <stop offset="70%" stopColor="#39d0d8" />
                <stop offset="100%" stopColor="#3fb950" />
              </linearGradient>
              <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="3" result="glow" />
                <feComposite in="SourceGraphic" in2="glow" operator="over" />
              </filter>
            </defs>

            {/* Glowing background arc */}
            <path
              d="M 50 80 Q 140 10 210 80 T 390 80 T 550 80"
              fill="none"
              stroke="url(#routeGradient)"
              strokeWidth="4"
              strokeLinecap="round"
              filter="url(#glow)"
              opacity="0.8"
            />
            {/* Animated dashed overlay */}
            <path
              d="M 50 80 Q 140 10 210 80 T 390 80 T 550 80"
              fill="none"
              stroke="#ffffff"
              strokeWidth="2"
              strokeDasharray="6, 8"
              opacity="0.6"
            />

            {/* Stop Nodes on the path */}
            {stops.map((stop, i) => {
              const xCoords = [50, 210, 390, 550];
              const x = xCoords[i] ?? 50 + i * 150;
              const y = 80;
              const isEnd = i === stops.length - 1;
              const isOrigin = i === 0;

              return (
                <g key={stop.id} transform={`translate(${x}, ${y})`}>
                  <circle
                    r="12"
                    fill="#0d1117"
                    stroke={isOrigin ? '#58a6ff' : isEnd ? '#3fb950' : '#39d0d8'}
                    strokeWidth="3"
                  />
                  <circle
                    r="5"
                    fill={isOrigin ? '#58a6ff' : isEnd ? '#3fb950' : '#39d0d8'}
                  />
                  <text
                    y="-22"
                    textAnchor="middle"
                    fill="#f0f6fc"
                    fontSize="13"
                    fontWeight="700"
                    fontFamily="'JetBrains Mono', monospace"
                  >
                    {stop.code}
                  </text>
                  <text
                    y="26"
                    textAnchor="middle"
                    fill="#8b949e"
                    fontSize="11"
                    fontFamily="'Inter', sans-serif"
                  >
                    {stop.city}
                  </text>
                  {stop.stayDays ? (
                    <text
                      y="40"
                      textAnchor="middle"
                      fill="#39d0d8"
                      fontSize="9.5"
                      fontWeight="600"
                    >
                      {stop.stayDays} nights
                    </text>
                  ) : null}
                </g>
              );
            })}
          </svg>

          {/* Interactive Leg Badges along the ribbon */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-around',
              padding: '0 40px',
              marginTop: '12px',
            }}
          >
            {legs.map((leg, index) => {
              const isSelected = selectedLegIndex === index;
              const modeIcon = leg.mode === 'flight' ? '✈️' : leg.mode === 'train' ? '🚆' : '🚗';
              const statusBg =
                leg.status === 'warning'
                  ? 'rgba(248,81,73,0.15)'
                  : leg.status === 'optimized'
                    ? 'rgba(57,208,216,0.15)'
                    : 'rgba(56,139,253,0.15)';
              const statusColor =
                leg.status === 'warning' ? '#f85149' : leg.status === 'optimized' ? '#39d0d8' : '#58a6ff';

              return (
                <button
                  key={`${leg.fromId}-${leg.toId}`}
                  onClick={() => setSelectedLegIndex(index)}
                  style={{
                    background: isSelected ? '#21262d' : statusBg,
                    border: `1px solid ${isSelected ? statusColor : 'transparent'}`,
                    borderRadius: 8,
                    padding: '6px 14px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6,
                    cursor: 'pointer',
                    color: statusColor,
                    fontSize: 12,
                    fontWeight: 600,
                    transition: 'all 0.15s ease',
                  }}
                  title={leg.notes}
                >
                  <span>{modeIcon}</span>
                  <span>{leg.durationText}</span>
                  {leg.status === 'warning' ? <span style={{ fontSize: 10 }}>⚠️</span> : null}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Selected Leg Inspector */}
      {selectedLeg ? (
        <div
          style={{
            padding: '16px',
            background: '#161b22',
            borderRadius: 12,
            border: '1px solid #30363d',
            display: 'flex',
            flexDirection: 'column',
            gap: 10,
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: 13, fontWeight: 700, color: '#f0f6fc' }}>
              Selected Segment: {fromStop.city} ({fromStop.code}) → {toStop.city} ({toStop.code})
            </span>
            <span
              style={{
                fontSize: 11,
                padding: '2px 8px',
                borderRadius: 4,
                fontWeight: 600,
                background: selectedLeg.status === 'warning' ? 'rgba(248,81,73,0.2)' : 'rgba(57,208,216,0.2)',
                color: selectedLeg.status === 'warning' ? '#f85149' : '#39d0d8',
              }}
            >
              {selectedLeg.status === 'warning' ? 'Vulnerable Segment' : 'Recommended Route'}
            </span>
          </div>

          <p style={{ margin: 0, fontSize: 12.5, color: '#c9d1d9', lineHeight: 1.55 }}>
            {selectedLeg.notes}
          </p>

          <div style={{ fontSize: 12, color: '#8b949e', display: 'flex', gap: 16 }}>
            <span>🕒 Duration: <strong style={{ color: '#f0f6fc' }}>{selectedLeg.durationText}</strong></span>
            <span>📍 Mode: <strong style={{ color: '#f0f6fc', textTransform: 'capitalize' }}>{selectedLeg.mode}</strong></span>
            {toStop.highlight ? <span>💎 Destination Focus: <strong style={{ color: '#39d0d8' }}>{toStop.highlight}</strong></span> : null}
          </div>
        </div>
      ) : null}
    </div>
  );
}
