'use client';

import React, { useState } from 'react';

export interface ComparisonItem {
  dimension: string;
  before: {
    title: string;
    description: string;
    riskBadge: string;
  };
  after: {
    title: string;
    description: string;
    advantageBadge: string;
  };
}

interface BeforeAfterComparisonProps {
  items?: ComparisonItem[];
}

const DEFAULT_COMPARISON_ITEMS: ComparisonItem[] = [
  {
    dimension: 'Flight Connection & Hub Transfer',
    before: {
      title: '50-minute tight connection at LHR T5',
      description: 'Minimum connection time broken. High probability of lost baggage or missed European connection.',
      riskBadge: '68% Bag Miss Risk',
    },
    after: {
      title: 'Re-timed connection with 110m cushion & VIP meet',
      description: 'Protected through-ticket with airside assistance. Seamless lounge transit with zero terminal stress.',
      advantageBadge: 'Protected Connection',
    },
  },
  {
    dimension: 'Sightseeing & Museum Access',
    before: {
      title: 'Vatican & Colosseum in same 4-hour window',
      description: 'Standard public queue (2+ hours standing). Overlapping entry times mean missing reserved slots.',
      riskBadge: 'Public Queue Trap',
    },
    after: {
      title: 'Keyholder / Before-Hours Private Access',
      description: 'Private historian entrance 45 minutes before public opening. Spaced across 2 relaxed mornings.',
      advantageBadge: 'VIP Keyholder Entry',
    },
  },
  {
    dimension: 'Hotel Privileges & Rates',
    before: {
      title: 'Standard OTA booking (Expedia / Booking.com)',
      description: 'Bottom-tier room allocation, no breakfast ($90/day extra per couple), strict non-refundable cancellation.',
      riskBadge: 'Zero Perks Unlocked',
    },
    after: {
      title: 'Virtuoso / Preferred Partner Direct Desk',
      description: 'Identical room rate with $100 resort credit, daily full breakfast for two, and priority upgrade on check-in.',
      advantageBadge: '+$650 Value Unlocked',
    },
  },
  {
    dimension: 'Disruption & Irregular Operations',
    before: {
      title: 'DIY Traveler stranded on customer service hold',
      description: 'Airline bot disconnects call; traveler spends night on airport bench paying out-of-pocket for new tickets.',
      riskBadge: 'Zero Support Net',
    },
    after: {
      title: '24/7 Dedicated Human Crisis & Rebooking Desk',
      description: 'Flight monitor alerts advisor before the traveler even deplanes; backup seats held automatically.',
      advantageBadge: 'Guaranteed Recovery',
    },
  },
];

export function BeforeAfterComparison({ items = DEFAULT_COMPARISON_ITEMS }: BeforeAfterComparisonProps) {
  const [activeView, setActiveView] = useState<'split' | 'before' | 'after'>('split');

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
      <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center', gap: 12, marginBottom: 20 }}>
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
                background: 'rgba(88,166,255,0.12)',
                color: '#58a6ff',
                border: '1px solid rgba(88,166,255,0.25)',
              }}
            >
              Transformation · Raw DIY vs. Waypoint Flow
            </span>
          </div>
          <h3 style={{ fontSize: 18, fontWeight: 700, margin: 0, color: '#f0f6fc', letterSpacing: '-0.02em' }}>
            Before vs. After: What Professional Advisory Changes
          </h3>
          <p style={{ fontSize: 13, color: '#8b949e', margin: '4px 0 0 0' }}>
            Compare the invisible vulnerabilities of generic planning against a hardened, partner-backed itinerary.
          </p>
        </div>

        {/* View Toggle */}
        <div
          style={{
            display: 'flex',
            background: '#161b22',
            padding: 3,
            borderRadius: 8,
            border: '1px solid #30363d',
          }}
        >
          <button
            onClick={() => setActiveView('split')}
            style={{
              background: activeView === 'split' ? '#21262d' : 'transparent',
              color: activeView === 'split' ? '#f0f6fc' : '#8b949e',
              border: 'none',
              borderRadius: 6,
              padding: '6px 12px',
              fontSize: 11.5,
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            Side-by-Side
          </button>
          <button
            onClick={() => setActiveView('before')}
            style={{
              background: activeView === 'before' ? 'rgba(248,81,73,0.15)' : 'transparent',
              color: activeView === 'before' ? '#f85149' : '#8b949e',
              border: 'none',
              borderRadius: 6,
              padding: '6px 12px',
              fontSize: 11.5,
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            Raw DIY Only
          </button>
          <button
            onClick={() => setActiveView('after')}
            style={{
              background: activeView === 'after' ? 'rgba(57,208,216,0.15)' : 'transparent',
              color: activeView === 'after' ? '#39d0d8' : '#8b949e',
              border: 'none',
              borderRadius: 6,
              padding: '6px 12px',
              fontSize: 11.5,
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            Waypoint Protected
          </button>
        </div>
      </div>

      {/* Comparison Grid */}
      <div style={{ display: 'grid', gap: 14 }}>
        {items.map((item, index) => {
          return (
            <div
              key={index}
              style={{
                borderRadius: 12,
                border: '1px solid #30363d',
                background: '#161b22',
                overflow: 'hidden',
              }}
            >
              {/* Category Bar */}
              <div
                style={{
                  padding: '8px 16px',
                  background: '#0d1117',
                  borderBottom: '1px solid #21262d',
                  fontSize: 11,
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  letterSpacing: '0.06em',
                  color: '#8b949e',
                  display: 'flex',
                  justifyContent: 'space-between',
                }}
              >
                <span>{item.dimension}</span>
                <span>Audit checkpoint #{index + 1}</span>
              </div>

              {/* Columns */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: activeView === 'split' ? 'repeat(auto-fit, minmax(260px, 1fr))' : '1fr',
                }}
              >
                {/* Before (DIY) */}
                {activeView === 'split' || activeView === 'before' ? (
                  <div
                    style={{
                      padding: '16px',
                      background: 'rgba(248,81,73,0.03)',
                      borderRight: activeView === 'split' ? '1px solid #21262d' : 'none',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                      <span style={{ fontSize: 11, fontWeight: 700, color: '#f85149', textTransform: 'uppercase' }}>
                        Your Raw Plan
                      </span>
                      <span
                        style={{
                          fontSize: 10.5,
                          fontWeight: 600,
                          padding: '2px 7px',
                          borderRadius: 4,
                          background: 'rgba(248,81,73,0.15)',
                          color: '#f85149',
                        }}
                      >
                        ⚠️ {item.before.riskBadge}
                      </span>
                    </div>
                    <div style={{ fontSize: 13.5, fontWeight: 600, color: '#f0f6fc', marginBottom: 4 }}>
                      {item.before.title}
                    </div>
                    <div style={{ fontSize: 12, color: '#8b949e', lineHeight: 1.5 }}>
                      {item.before.description}
                    </div>
                  </div>
                ) : null}

                {/* After (Waypoint) */}
                {activeView === 'split' || activeView === 'after' ? (
                  <div
                    style={{
                      padding: '16px',
                      background: 'rgba(57,208,216,0.03)',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                      <span style={{ fontSize: 11, fontWeight: 700, color: '#39d0d8', textTransform: 'uppercase' }}>
                        Waypoint Optimized
                      </span>
                      <span
                        style={{
                          fontSize: 10.5,
                          fontWeight: 600,
                          padding: '2px 7px',
                          borderRadius: 4,
                          background: 'rgba(57,208,216,0.15)',
                          color: '#39d0d8',
                        }}
                      >
                        ✓ {item.after.advantageBadge}
                      </span>
                    </div>
                    <div style={{ fontSize: 13.5, fontWeight: 600, color: '#f0f6fc', marginBottom: 4 }}>
                      {item.after.title}
                    </div>
                    <div style={{ fontSize: 12, color: '#8b949e', lineHeight: 1.5 }}>
                      {item.after.description}
                    </div>
                  </div>
                ) : null}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
