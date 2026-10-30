'use client';

import React, { useState } from 'react';

export interface RoomTierComparison {
  hotelName: string;
  city: string;
  consortiaProgram: string;
  roomRatePublic: number;
  otaRoom: {
    category: string;
    areaSqm: number;
    view: string;
    breakfastCost: number;
    credits: number;
    cancellation: string;
    upgradeEligible: boolean;
  };
  waypointSuite: {
    category: string;
    areaSqm: number;
    view: string;
    breakfastCost: number;
    credits: number;
    cancellation: string;
    upgradeEligible: boolean;
    amenitiesValue: number;
  };
}

const DEFAULT_HOTEL: RoomTierComparison = {
  hotelName: 'The Ritz Paris',
  city: 'Place Vendôme, Paris',
  consortiaProgram: 'Virtuoso & Leading Hotels Leaders Club Desk',
  roomRatePublic: 1450,
  otaRoom: {
    category: 'Superior Room (Entry Level)',
    areaSqm: 35,
    view: 'Interior Courtyard',
    breakfastCost: 90, // $90 per person per day
    credits: 0,
    cancellation: 'Non-refundable / 14-day strict',
    upgradeEligible: false,
  },
  waypointSuite: {
    category: 'Deluxe Suite with Private Salon',
    areaSqm: 68,
    view: 'Place Vendôme & Parisian Rooftops',
    breakfastCost: 0, // Complimentary daily breakfast for two
    credits: 100, // $100 USD hotel dining/spa credit
    cancellation: 'Flexible 24h cancellation prior to arrival',
    upgradeEligible: true,
    amenitiesValue: 640,
  },
};

export function IsometricHotelSanctuary({
  hotel = DEFAULT_HOTEL,
  onClaim,
}: {
  hotel?: RoomTierComparison;
  onClaim?: () => void;
}) {
  const [selectedWing, setSelectedWing] = useState<'both' | 'ota' | 'waypoint'>('both');

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
      <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12, marginBottom: 18 }}>
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
                background: 'rgba(52, 211, 153, 0.12)',
                color: '#34d399',
                border: '1px solid rgba(52, 211, 153, 0.25)',
              }}
            >
              Architectural Axonometry · Suite Tier Arbitrage
            </span>
            <span style={{ fontSize: 12, color: '#8b949e' }}>{hotel.hotelName} ({hotel.city})</span>
          </div>
          <h3 style={{ fontSize: 18, fontWeight: 700, margin: 0, color: '#f0f6fc', letterSpacing: '-0.02em' }}>
            Isometric Suite Cutaway: Unlocked VIP Amenities
          </h3>
          <p style={{ fontSize: 13, color: '#8b949e', margin: '4px 0 0 0' }}>
            Both bookings pay the exact same public rate (${hotel.roomRatePublic}/night). Waypoint unlocks top-tier suites and complimentary benefits.
          </p>
        </div>

        {/* Tally */}
        <div style={{ textAlign: 'right' }}>
          <div
            style={{
              fontSize: 24,
              fontWeight: 800,
              fontFamily: "'JetBrains Mono', monospace",
              color: '#34d399',
            }}
          >
            +${hotel.waypointSuite.amenitiesValue}
          </div>
          <div style={{ fontSize: 11, color: '#8b949e' }}>Complimentary Value Unlocked</div>
        </div>
      </div>

      {/* Isometric 2.5D Cutaway SVG */}
      <div
        style={{
          width: '100%',
          height: '280px',
          background: 'radial-gradient(ellipse at 50% 60%, rgba(30, 41, 59, 0.6) 0%, #0d1117 100%)',
          borderRadius: 14,
          border: '1px solid #30363d',
          position: 'relative',
          overflow: 'hidden',
          marginBottom: 16,
        }}
      >
        <svg
          viewBox="0 0 600 280"
          style={{ width: '100%', height: '100%', display: 'block' }}
        >
          <defs>
            <linearGradient id="suiteGlow" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#34d399" stopOpacity="0.4" />
              <stop offset="100%" stopColor="#059669" stopOpacity="0.1" />
            </linearGradient>
            <linearGradient id="otaGlow" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#64748b" stopOpacity="0.25" />
              <stop offset="100%" stopColor="#1e293b" stopOpacity="0.1" />
            </linearGradient>
          </defs>

          {/* Isometric Ground Plane */}
          <polygon
            points="300,40 540,140 300,240 60,140"
            fill="#111827"
            stroke="#1f2937"
            strokeWidth="2"
          />

          {/* Left Wing: OTA / Standard DIY Room (Muted Grey Tone) */}
          <g opacity={selectedWing === 'waypoint' ? 0.3 : 1} style={{ transition: 'opacity 0.2s' }}>
            {/* Room Base Cube */}
            <polygon points="120,130 240,180 240,110 120,60" fill="#1e293b" stroke="#334155" />
            <polygon points="240,180 300,150 300,80 240,110" fill="#0f172a" stroke="#334155" />
            <polygon points="120,60 240,110 300,80 180,30" fill="url(#otaGlow)" stroke="#475569" />

            {/* Room Furniture Miniatures */}
            <polygon points="150,95 210,120 195,127 135,102" fill="#475569" />
            <text x="210" y="80" textAnchor="middle" fill="#94a3b8" fontSize="10" fontWeight="700">Standard Room (35m²)</text>
            <text x="210" y="96" textAnchor="middle" fill="#ef4444" fontSize="8.5">❌ No Breakfast · No Upgrades</text>
          </g>

          {/* Right Wing: Waypoint Virtuoso Luxury Suite (Vibrant Gold/Emerald Tone) */}
          <g opacity={selectedWing === 'ota' ? 0.3 : 1} style={{ transition: 'opacity 0.2s' }}>
            {/* Suite Base Cube (Twice as large + Balcony) */}
            <polygon points="300,150 480,225 480,135 300,60" fill="#064e3b" stroke="#059669" strokeWidth="1.5" />
            <polygon points="480,225 540,195 540,105 480,135" fill="#022c22" stroke="#059669" strokeWidth="1.5" />
            <polygon points="300,60 480,135 540,105 360,30" fill="url(#suiteGlow)" stroke="#10b981" strokeWidth="1.5" />

            {/* Private Terrace Outcropping */}
            <polygon points="420,200 480,225 450,238 390,213" fill="#047857" stroke="#34d399" />

            <text x="420" y="75" textAnchor="middle" fill="#34d399" fontSize="11" fontWeight="800">Deluxe Suite (68m²)</text>
            <text x="420" y="92" textAnchor="middle" fill="#f8fafc" fontSize="9">✨ $100 Credit + Daily Breakfast for Two</text>
            <text x="420" y="106" textAnchor="middle" fill="#a7f3d0" fontSize="8.5">Place Vendôme Terrace View</text>
          </g>

          {/* Central Architectural Dividing Axis */}
          <line x1="300" y1="40" x2="300" y2="240" stroke="#334155" strokeWidth="1.5" strokeDasharray="3, 3" />
          <text x="300" y="260" textAnchor="middle" fill="#64748b" fontSize="9" fontFamily="'JetBrains Mono', monospace">
            IDENTICAL PUBLIC RATE: ${hotel.roomRatePublic}/NIGHT
          </text>
        </svg>

        {/* Floating View Toggles */}
        <div style={{ position: 'absolute', bottom: 12, right: 12, display: 'flex', gap: 4 }}>
          <button
            onClick={() => setSelectedWing('both')}
            style={{
              background: selectedWing === 'both' ? '#334155' : 'rgba(15, 23, 42, 0.8)',
              border: '1px solid #475569',
              borderRadius: 6,
              padding: '4px 8px',
              fontSize: 10.5,
              color: '#f8fafc',
              cursor: 'pointer',
            }}
          >
            Show Both
          </button>
          <button
            onClick={() => setSelectedWing('waypoint')}
            style={{
              background: selectedWing === 'waypoint' ? '#047857' : 'rgba(15, 23, 42, 0.8)',
              border: '1px solid #10b981',
              borderRadius: 6,
              padding: '4px 8px',
              fontSize: 10.5,
              color: '#34d399',
              cursor: 'pointer',
            }}
          >
            Waypoint Suite Only
          </button>
        </div>
      </div>

      {/* Side-by-Side Architectural Ledger */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
          gap: 12,
          marginBottom: 16,
        }}
      >
        {/* Left: DIY OTA Room */}
        <div
          style={{
            background: '#161b22',
            border: '1px solid #30363d',
            borderRadius: 12,
            padding: '16px',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
            <span style={{ fontSize: 11, fontWeight: 700, color: '#f85149', textTransform: 'uppercase' }}>
              Standard OTA Booking (Expedia/Booking)
            </span>
            <span style={{ fontSize: 10.5, color: '#8b949e' }}>Entry Floor</span>
          </div>
          <div style={{ fontSize: 14, fontWeight: 700, color: '#f0f6fc', marginBottom: 6 }}>
            {hotel.otaRoom.category}
          </div>
          <div style={{ fontSize: 12, color: '#8b949e', display: 'flex', flexDirection: 'column', gap: 6 }}>
            <div>📐 Area: <strong style={{ color: '#c9d1d9' }}>{hotel.otaRoom.areaSqm} m²</strong></div>
            <div>🪟 View: <strong style={{ color: '#c9d1d9' }}>{hotel.otaRoom.view}</strong></div>
            <div>🥐 Breakfast: <strong style={{ color: '#f85149' }}>+$90/person per day</strong></div>
            <div>💳 Folio Credit: <strong style={{ color: '#f85149' }}>$0 (None)</strong></div>
          </div>
        </div>

        {/* Right: Waypoint Virtuoso Suite */}
        <div
          style={{
            background: 'rgba(52, 211, 153, 0.05)',
            border: '1px solid rgba(52, 211, 153, 0.3)',
            borderRadius: 12,
            padding: '16px',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
            <span style={{ fontSize: 11, fontWeight: 700, color: '#34d399', textTransform: 'uppercase' }}>
              Waypoint Preferred Partner Suite
            </span>
            <span style={{ fontSize: 10.5, fontWeight: 700, color: '#34d399' }}>✓ Virtuoso Desk</span>
          </div>
          <div style={{ fontSize: 14, fontWeight: 700, color: '#f0f6fc', marginBottom: 6 }}>
            {hotel.waypointSuite.category}
          </div>
          <div style={{ fontSize: 12, color: '#cbd5e1', display: 'flex', flexDirection: 'column', gap: 6 }}>
            <div>📐 Area: <strong style={{ color: '#34d399' }}>{hotel.waypointSuite.areaSqm} m² (2x Space)</strong></div>
            <div>🪟 View: <strong style={{ color: '#34d399' }}>{hotel.waypointSuite.view}</strong></div>
            <div>🥐 Breakfast: <strong style={{ color: '#34d399' }}>Free Daily for Two ($270 Value)</strong></div>
            <div>💳 Folio Credit: <strong style={{ color: '#34d399' }}>+$100 USD Dining/Spa Credit</strong></div>
          </div>
        </div>
      </div>

      {/* Claim Action */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: 12,
          padding: '14px 18px',
          borderRadius: 12,
          background: 'linear-gradient(135deg, rgba(52, 211, 153, 0.12) 0%, rgba(14, 165, 233, 0.12) 100%)',
          border: '1px solid rgba(52, 211, 153, 0.3)',
        }}
      >
        <div style={{ fontSize: 12.5, color: '#cbd5e1', lineHeight: 1.5 }}>
          <strong style={{ color: '#34d399' }}>Zero Booking Fee Arbitrage:</strong> Waypoint partners book directly with hotel general managers at the exact price you already selected, appending all VIP suite privileges for free.
        </div>
        {onClaim ? (
          <button
            onClick={onClaim}
            style={{
              background: '#34d399',
              color: '#022c22',
              border: 'none',
              borderRadius: 8,
              padding: '8px 18px',
              fontSize: 12.5,
              fontWeight: 800,
              cursor: 'pointer',
              whiteSpace: 'nowrap',
            }}
          >
            Claim Suite Upgrades →
          </button>
        ) : null}
      </div>
    </div>
  );
}
