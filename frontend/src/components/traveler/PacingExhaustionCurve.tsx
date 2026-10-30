'use client';

import React, { useState } from 'react';

export interface DayPacingData {
  dayNumber: number;
  label: string;
  activitiesCount: number;
  estimatedSteps: number;
  standingHours: number;
  exhaustionScore: number; // 0 to 100
  notes: string;
}

interface PacingExhaustionCurveProps {
  days?: DayPacingData[];
  hasElderlyOrKids?: boolean;
}

const DEFAULT_DAYS: DayPacingData[] = [
  {
    dayNumber: 1,
    label: 'Arrival & Jet Lag',
    activitiesCount: 2,
    estimatedSteps: 8500,
    standingHours: 3.5,
    exhaustionScore: 55,
    notes: 'JFK → LHR → CDG transfer + hotel check-in at The Ritz. Fatigue from 5-hour time shift.',
  },
  {
    dayNumber: 2,
    label: 'Paris Highlights',
    activitiesCount: 3,
    estimatedSteps: 14200,
    standingHours: 6.5,
    exhaustionScore: 78,
    notes: 'Louvre Museum, Tuileries gardens, Seine evening cruise. Heavy standing fatigue.',
  },
  {
    dayNumber: 3,
    label: 'Paris Free & Transit',
    activitiesCount: 2,
    estimatedSteps: 9100,
    standingHours: 4.0,
    exhaustionScore: 48,
    notes: 'Marais exploration + packing for high-speed train to Rome.',
  },
  {
    dayNumber: 4,
    label: 'Rome Mega-Day (Burnout)',
    activitiesCount: 5,
    estimatedSteps: 21500,
    standingHours: 9.5,
    exhaustionScore: 96,
    notes: 'Colosseum (8am), Vatican (11am), Borghese (2pm), Trastevere (5pm). Critical over-scheduling!',
  },
  {
    dayNumber: 5,
    label: 'Departure Fatigue',
    activitiesCount: 2,
    estimatedSteps: 11000,
    standingHours: 5.0,
    exhaustionScore: 72,
    notes: 'Spanish Steps morning, hotel checkout, transfer to FCO airport.',
  },
];

export function PacingExhaustionCurve({
  days = DEFAULT_DAYS,
  hasElderlyOrKids = true,
}: PacingExhaustionCurveProps) {
  const [selectedDayIndex, setSelectedDayIndex] = useState<number>(3); // Day 4 selected by default

  const selectedDay = days[selectedDayIndex] || days[0];
  const maxScore = 100;
  const burnoutThreshold = hasElderlyOrKids ? 70 : 85;

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
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 20 }}>
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
                background: 'rgba(210,153,34,0.12)',
                color: '#d29922',
                border: '1px solid rgba(210,153,34,0.25)',
              }}
            >
              Circadian Physics · Energy & Fatigue Wave
            </span>
            {hasElderlyOrKids ? (
              <span
                style={{
                  fontSize: 10.5,
                  fontWeight: 600,
                  padding: '3px 8px',
                  borderRadius: 6,
                  background: 'rgba(248,81,73,0.12)',
                  color: '#f85149',
                  border: '1px solid rgba(248,81,73,0.25)',
                }}
              >
                ♿ Elderly / Multi-Gen Pace Threshold
              </span>
            ) : null}
          </div>
          <h3 style={{ fontSize: 18, fontWeight: 700, margin: 0, color: '#f0f6fc', letterSpacing: '-0.02em' }}>
            Day-by-Day Pacing & Exhaustion Curve
          </h3>
          <p style={{ fontSize: 13, color: '#8b949e', margin: '4px 0 0 0' }}>
            Generic AI packs calendars without considering biological stamina. Plots physical load vs. human recovery limits.
          </p>
        </div>
      </div>

      {/* Interactive Chart Container */}
      <div
        style={{
          background: '#161b22',
          borderRadius: 14,
          border: '1px solid #30363d',
          padding: '24px 20px 16px 20px',
          marginBottom: 20,
        }}
      >
        {/* SVG Curve */}
        <div style={{ width: '100%', height: '170px', position: 'relative' }}>
          <svg
            viewBox="0 0 500 150"
            preserveAspectRatio="none"
            style={{ width: '100%', height: '100%', overflow: 'visible' }}
          >
            <defs>
              <linearGradient id="exhaustionArea" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stopColor="#f85149" stopOpacity="0.35" />
                <stop offset="60%" stopColor="#d29922" stopOpacity="0.15" />
                <stop offset="100%" stopColor="#3fb950" stopOpacity="0.02" />
              </linearGradient>
            </defs>

            {/* Burnout Danger Threshold Zone Line */}
            {(() => {
              const thresholdY = 150 - (burnoutThreshold / maxScore) * 130;
              return (
                <g>
                  <line
                    x1="20"
                    y1={thresholdY}
                    x2="480"
                    y2={thresholdY}
                    stroke="#f85149"
                    strokeWidth="1.5"
                    strokeDasharray="4, 4"
                    opacity="0.6"
                  />
                  <text
                    x="485"
                    y={thresholdY + 3}
                    fill="#f85149"
                    fontSize="9.5"
                    fontWeight="600"
                    textAnchor="start"
                  >
                    Burnout Ceiling ({burnoutThreshold}%)
                  </text>
                </g>
              );
            })()}

            {/* Coordinates for days */}
            {(() => {
              const points = days.map((d, i) => {
                const x = 40 + i * (420 / Math.max(1, days.length - 1));
                const y = 140 - (d.exhaustionScore / maxScore) * 120;
                return { x, y, data: d };
              });

              const pathD = points.reduce((acc, p, i) => {
                if (i === 0) return `M ${p.x} ${p.y}`;
                const prev = points[i - 1];
                const cx1 = prev.x + (p.x - prev.x) / 2;
                const cx2 = cx1;
                return `${acc} C ${cx1} ${prev.y}, ${cx2} ${p.y}, ${p.x} ${p.y}`;
              }, '');

              const areaD = `${pathD} L ${points[points.length - 1].x} 145 L ${points[0].x} 145 Z`;

              // Waypoint Optimized Pace Line (Green dashed line that tops out at safe ~60%)
              const optimizedPoints = days.map((d, i) => {
                const x = 40 + i * (420 / Math.max(1, days.length - 1));
                const optScore = Math.min(60, d.exhaustionScore * 0.65);
                const y = 140 - (optScore / maxScore) * 120;
                return { x, y };
              });

              const optPathD = optimizedPoints.reduce((acc, p, i) => {
                if (i === 0) return `M ${p.x} ${p.y}`;
                const prev = optimizedPoints[i - 1];
                const cx = prev.x + (p.x - prev.x) / 2;
                return `${acc} C ${cx} ${prev.y}, ${cx} ${p.y}, ${p.x} ${p.y}`;
              }, '');

              return (
                <g>
                  {/* Raw user plan area fill */}
                  <path d={areaD} fill="url(#exhaustionArea)" />
                  {/* Raw user plan stroke */}
                  <path d={pathD} fill="none" stroke="#f85149" strokeWidth="2.5" />

                  {/* Waypoint Optimized reference curve */}
                  <path
                    d={optPathD}
                    fill="none"
                    stroke="#3fb950"
                    strokeWidth="2"
                    strokeDasharray="5, 5"
                  />

                  {/* Data points */}
                  {points.map((p, i) => {
                    const isSelected = selectedDayIndex === i;
                    const isDanger = p.data.exhaustionScore >= burnoutThreshold;
                    const dotColor = isDanger ? '#f85149' : p.data.exhaustionScore > 65 ? '#d29922' : '#3fb950';

                    return (
                      <g
                        key={p.data.dayNumber}
                        onClick={() => setSelectedDayIndex(i)}
                        style={{ cursor: 'pointer' }}
                      >
                        <circle
                          cx={p.x}
                          cy={p.y}
                          r={isSelected ? 7 : 5}
                          fill="#0d1117"
                          stroke={dotColor}
                          strokeWidth={isSelected ? 3 : 2}
                        />
                        {isSelected ? (
                          <circle cx={p.x} cy={p.y} r="3" fill="#ffffff" />
                        ) : null}
                        <text
                          x={p.x}
                          y={p.y - 12}
                          textAnchor="middle"
                          fill={dotColor}
                          fontSize="10"
                          fontWeight="700"
                          fontFamily="'JetBrains Mono', monospace"
                        >
                          {p.data.exhaustionScore}%
                        </text>
                        <text
                          x={p.x}
                          y="155"
                          textAnchor="middle"
                          fill={isSelected ? '#f0f6fc' : '#8b949e'}
                          fontSize="10.5"
                          fontWeight={isSelected ? '700' : '500'}
                        >
                          Day {p.data.dayNumber}
                        </text>
                      </g>
                    );
                  })}
                </g>
              );
            })()}
          </svg>
        </div>

        {/* Legend */}
        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            justifyContent: 'center',
            gap: 20,
            marginTop: 18,
            fontSize: 11.5,
            color: '#8b949e',
            borderTop: '1px solid #21262d',
            paddingTop: 10,
          }}
        >
          <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ width: 14, height: 3, background: '#f85149', borderRadius: 2 }} />
            Your Raw Plan (Peak Fatigue)
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ width: 14, height: 3, borderTop: '2px dashed #3fb950' }} />
            Waypoint Human-Paced Rhythm
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#f85149' }} />
            Burnout Zone ({burnoutThreshold}%+ load)
          </span>
        </div>
      </div>

      {/* Selected Day Breakdown Card */}
      {selectedDay ? (
        <div
          style={{
            background: '#161b22',
            borderRadius: 12,
            border: `1px solid ${selectedDay.exhaustionScore >= burnoutThreshold ? 'rgba(248,81,73,0.3)' : '#30363d'}`,
            padding: '16px',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ fontSize: 13, fontWeight: 700, color: '#f0f6fc' }}>
                Day {selectedDay.dayNumber}: {selectedDay.label}
              </span>
              {selectedDay.exhaustionScore >= burnoutThreshold ? (
                <span
                  style={{
                    fontSize: 10.5,
                    padding: '2px 7px',
                    borderRadius: 4,
                    background: 'rgba(248,81,73,0.18)',
                    color: '#f85149',
                    fontWeight: 700,
                  }}
                >
                  ⚠️ Fatigue Spike
                </span>
              ) : null}
            </div>

            <span
              style={{
                fontSize: 12,
                fontWeight: 700,
                color: selectedDay.exhaustionScore >= burnoutThreshold ? '#f85149' : '#3fb950',
                fontFamily: "'JetBrains Mono', monospace",
              }}
            >
              Physical Load: {selectedDay.exhaustionScore}%
            </span>
          </div>

          <p style={{ margin: '0 0 12px 0', fontSize: 12.5, color: '#c9d1d9', lineHeight: 1.5 }}>
            {selectedDay.notes}
          </p>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
              gap: 10,
              padding: '10px 12px',
              borderRadius: 8,
              background: '#0d1117',
              border: '1px solid #21262d',
              fontSize: 11.5,
            }}
          >
            <div>
              <span style={{ color: '#8b949e' }}>Walking:</span>{' '}
              <strong style={{ color: selectedDay.estimatedSteps > 15000 ? '#f85149' : '#f0f6fc' }}>
                {selectedDay.estimatedSteps.toLocaleString()} steps
              </strong>
            </div>
            <div>
              <span style={{ color: '#8b949e' }}>Standing:</span>{' '}
              <strong style={{ color: selectedDay.standingHours > 6 ? '#f85149' : '#f0f6fc' }}>
                {selectedDay.standingHours} hours
              </strong>
            </div>
            <div>
              <span style={{ color: '#8b949e' }}>Attractions:</span>{' '}
              <strong style={{ color: '#f0f6fc' }}>{selectedDay.activitiesCount} booked</strong>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
