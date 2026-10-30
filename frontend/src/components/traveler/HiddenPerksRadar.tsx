'use client';

import React, { useState } from 'react';

export interface LuxuryPropertyPerk {
  hotelName: string;
  city: string;
  nights: number;
  partnershipDesk: string; // e.g. 'Virtuoso / Marriott STARS', 'Rocco Forte Knights'
  estimatedTotalValue: number;
  perks: {
    icon: string;
    label: string;
    estimatedValue: number;
    description: string;
  }[];
}

interface HiddenPerksRadarProps {
  properties?: LuxuryPropertyPerk[];
  onClaimPerks?: () => void;
}

const DEFAULT_PROPERTIES: LuxuryPropertyPerk[] = [
  {
    hotelName: 'The Ritz Paris',
    city: 'Paris, France',
    nights: 3,
    partnershipDesk: 'Virtuoso & The Leading Hotels of the World Leaders Club',
    estimatedTotalValue: 640,
    perks: [
      { icon: '🥐', label: 'Daily American Breakfast for Two', estimatedValue: 270, description: 'Complimentary full breakfast daily at Bar Vendôme for 3 nights' },
      { icon: '💳', label: 'Food & Beverage / Spa Credit', estimatedValue: 100, description: '100 EUR credit applied directly to room folio during stay' },
      { icon: '⬆️', label: 'Priority Room Category Upgrade', estimatedValue: 220, description: 'Upgrade upon arrival subject to availability' },
      { icon: '⏰', label: 'Early Check-in & 4:00 PM Late Checkout', estimatedValue: 50, description: 'Guaranteed flexible check-in/out priority' },
    ],
  },
  {
    hotelName: 'Hotel de Russie',
    city: 'Rome, Italy',
    nights: 2,
    partnershipDesk: 'Rocco Forte Knights / Virtuoso Preferred',
    estimatedTotalValue: 480,
    perks: [
      { icon: '🥐', label: 'Daily Buffet Breakfast in Garden', estimatedValue: 160, description: 'Complimentary breakfast for two at Le Jardin de Russie' },
      { icon: '💳', label: 'On-Property Dining Credit', estimatedValue: 100, description: '100 USD food & beverage credit per stay' },
      { icon: '⬆️', label: 'Room Category Upgrade', estimatedValue: 170, description: 'Upgraded to Deluxe Garden View upon check-in' },
      { icon: '🍾', label: 'Welcome Italian Wine & Fruit', estimatedValue: 50, description: 'Personalized welcome amenities from General Manager' },
    ],
  },
];

export function HiddenPerksRadar({
  properties = DEFAULT_PROPERTIES,
  onClaimPerks,
}: HiddenPerksRadarProps) {
  const [selectedPropIndex, setSelectedPropIndex] = useState<number>(0);

  const totalPerkValue = properties.reduce((acc, p) => acc + p.estimatedTotalValue, 0);
  const selectedProperty = properties[selectedPropIndex] || properties[0];

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
              VIP Rate Parity · Money on the Table Radar
            </span>
          </div>
          <h3 style={{ fontSize: 18, fontWeight: 700, margin: 0, color: '#f0f6fc', letterSpacing: '-0.02em' }}>
            Unclaimed Luxury Perks & Amenities Value
          </h3>
          <p style={{ fontSize: 13, color: '#8b949e', margin: '4px 0 0 0' }}>
            DIY & OTA bookings pay the exact same room rate but leave complimentary VIP amenities on the table.
          </p>
        </div>

        {/* Tally Pill */}
        <div
          style={{
            background: 'rgba(57,208,216,0.08)',
            border: '1px solid rgba(57,208,216,0.25)',
            borderRadius: 12,
            padding: '10px 18px',
            textAlign: 'right',
          }}
        >
          <div style={{ fontSize: 22, fontWeight: 800, color: '#39d0d8', fontFamily: "'JetBrains Mono', monospace" }}>
            +${totalPerkValue.toLocaleString()}
          </div>
          <div style={{ fontSize: 11, color: '#8b949e' }}>Unclaimed VIP Value</div>
        </div>
      </div>

      {/* Property Selector Tabs */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 16, overflowX: 'auto', paddingBottom: 4 }}>
        {properties.map((prop, i) => {
          const isSelected = selectedPropIndex === i;
          return (
            <button
              key={prop.hotelName}
              onClick={() => setSelectedPropIndex(i)}
              style={{
                background: isSelected ? '#161b22' : 'transparent',
                border: `1px solid ${isSelected ? '#39d0d8' : '#30363d'}`,
                borderRadius: 10,
                padding: '10px 16px',
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                cursor: 'pointer',
                color: isSelected ? '#f0f6fc' : '#8b949e',
                fontSize: 13,
                fontWeight: 600,
                transition: 'all 0.15s ease',
                whiteSpace: 'nowrap',
              }}
            >
              <span>🏨</span>
              <div style={{ textAlign: 'left' }}>
                <div>{prop.hotelName}</div>
                <div style={{ fontSize: 11, color: isSelected ? '#39d0d8' : '#6e7681' }}>
                  +${prop.estimatedTotalValue} value ({prop.nights}n)
                </div>
              </div>
            </button>
          );
        })}
      </div>

      {/* Selected Property Perk Breakdown */}
      {selectedProperty ? (
        <div
          style={{
            background: '#161b22',
            borderRadius: 14,
            border: '1px solid #30363d',
            padding: '20px',
            marginBottom: 20,
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
            <div>
              <div style={{ fontSize: 15, fontWeight: 700, color: '#f0f6fc' }}>
                {selectedProperty.hotelName} ({selectedProperty.city})
              </div>
              <div style={{ fontSize: 11.5, color: '#8b949e', marginTop: 2 }}>
                Eligible Desk: <strong style={{ color: '#c9d1d9' }}>{selectedProperty.partnershipDesk}</strong>
              </div>
            </div>
            <div style={{ fontSize: 13, fontWeight: 700, color: '#39d0d8', fontFamily: "'JetBrains Mono', monospace" }}>
              +${selectedProperty.estimatedTotalValue} / stay
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 10 }}>
            {selectedProperty.perks.map((perk, idx) => (
              <div
                key={idx}
                style={{
                  background: '#0d1117',
                  border: '1px solid #21262d',
                  borderRadius: 10,
                  padding: '12px 14px',
                  display: 'flex',
                  gap: 12,
                }}
              >
                <span style={{ fontSize: 20 }}>{perk.icon}</span>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: 12, fontWeight: 600, color: '#f0f6fc' }}>{perk.label}</span>
                    <span style={{ fontSize: 11, fontWeight: 700, color: '#3fb950', fontFamily: "'JetBrains Mono', monospace" }}>
                      +${perk.estimatedValue}
                    </span>
                  </div>
                  <div style={{ fontSize: 11, color: '#8b949e', marginTop: 4, lineHeight: 1.4 }}>
                    {perk.description}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {/* Action Banner */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: 14,
          padding: '14px 18px',
          borderRadius: 12,
          background: 'linear-gradient(135deg, rgba(37,99,235,0.1) 0%, rgba(57,208,216,0.1) 100%)',
          border: '1px solid rgba(57,208,216,0.25)',
        }}
      >
        <div style={{ fontSize: 12.5, color: '#c9d1d9', lineHeight: 1.5 }}>
          <strong style={{ color: '#f0f6fc' }}>Guaranteed Rate Parity:</strong> Waypoint partner advisors book direct with hotel management at the same public rate you see online, attaching VIP amenities without markup or fees.
        </div>
        {onClaimPerks ? (
          <button
            onClick={onClaimPerks}
            style={{
              background: '#39d0d8',
              color: '#07090b',
              border: 'none',
              borderRadius: 8,
              padding: '8px 18px',
              fontSize: 12.5,
              fontWeight: 700,
              cursor: 'pointer',
              whiteSpace: 'nowrap',
              transition: 'opacity 0.15s ease',
            }}
          >
            Claim My Amenities →
          </button>
        ) : null}
      </div>
    </div>
  );
}
