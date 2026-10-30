'use client';

import React, { useState, useMemo } from 'react';
import type { RunStatusResponse } from '@/types/spine';
import { LayoverStressGauge, type LayoverSegment } from './LayoverStressGauge';
import { RouteArcRibbon, type RouteStop, type RouteLeg } from './RouteArcRibbon';
import { PacingExhaustionCurve, type DayPacingData } from './PacingExhaustionCurve';
import { BeforeAfterComparison, type ComparisonItem } from './BeforeAfterComparison';
import { HiddenPerksRadar, type LuxuryPropertyPerk } from './HiddenPerksRadar';
import { IsometricAirportCutaway } from './IsometricAirportCutaway';
import { Interactive3DGlobeFlightArc } from './Interactive3DGlobeFlightArc';
import { IsometricHotelSanctuary } from './IsometricHotelSanctuary';

interface WedgeVisualShowcaseProps {
  analysis?: RunStatusResponse | null;
  onAdvisorHelp?: () => void;
}

type TabType = 'stress' | 'isoAirport' | 'globe3d' | 'route' | 'pacing' | 'isoHotel' | 'comparison' | 'perks';

export function WedgeVisualShowcase({ analysis, onAdvisorHelp }: WedgeVisualShowcaseProps) {
  const [activeTab, setActiveTab] = useState<TabType>('stress');

  // Derive intelligent, dynamic data from the live analysis packet
  const packet = (analysis?.packet as Record<string, any> | null | undefined) ?? null;
  const facts = packet?.facts as Record<string, any> | undefined;

  // 1. Geography & Stops
  const { stops, legs } = useMemo(() => {
    const rawCandidates = facts?.destination_candidates?.value;
    const candidates: string[] = Array.isArray(rawCandidates)
      ? rawCandidates.filter((c: any) => typeof c === 'string' && c.length > 2 && c.toLowerCase() !== 'day')
      : ['Paris', 'Rome'];

    const origin = typeof facts?.origin_city?.value === 'string' ? facts.origin_city.value : 'JFK';

    const generatedStops: RouteStop[] = [
      { id: '1', code: origin.slice(0, 3).toUpperCase(), city: origin, country: 'Departure', highlight: 'Trip Origin' },
      { id: '2', code: 'LHR', city: 'London', country: 'UK', highlight: 'Transatlantic Hub' },
    ];

    candidates.slice(0, 2).forEach((dest, idx) => {
      const code = dest.slice(0, 3).toUpperCase();
      generatedStops.push({
        id: String(idx + 3),
        code: code === 'PAR' ? 'CDG' : code === 'ROM' ? 'FCO' : code,
        city: dest,
        country: idx === 0 ? 'France' : 'Italy',
        stayDays: idx === 0 ? 3 : 2,
        highlight: idx === 0 ? 'The Ritz Paris' : 'Hotel de Russie',
      });
    });

    const generatedLegs: RouteLeg[] = [];
    for (let i = 0; i < generatedStops.length - 1; i++) {
      const from = generatedStops[i];
      const to = generatedStops[i + 1];
      const isHub = to.code === 'LHR';
      const isTrain = i >= 2;

      generatedLegs.push({
        fromId: from.id,
        toId: to.id,
        mode: isTrain ? 'train' : 'flight',
        durationText: isHub ? '7h 10m' : isTrain ? '3h 15m' : '1h 20m',
        notes: isHub
          ? 'Overnight transatlantic flight'
          : isTrain
            ? `High-speed rail connection between ${from.city} and ${to.city}`
            : `Connecting flight: ${from.city} → ${to.city} with tight transfer buffer`,
        status: isHub ? 'verified' : isTrain ? 'optimized' : 'warning',
      });
    }

    return { stops: generatedStops, legs: generatedLegs };
  }, [facts]);

  // 2. Layover Segment
  const layoverSegment: LayoverSegment = useMemo(() => {
    return {
      inboundFlight: `${stops[0]?.code ?? 'JFK'} → ${stops[1]?.code ?? 'LHR'}`,
      connectingFlight: `${stops[1]?.code ?? 'LHR'} → ${stops[2]?.code ?? 'CDG'}`,
      transitHub: `${stops[1]?.city ?? 'London Heathrow'} (${stops[1]?.code ?? 'LHR'})`,
      scheduledMinutes: 50,
      minimumSafeMinutes: 90,
      terminalFrom: 'Terminal 5',
      terminalTo: 'Terminal 3',
    };
  }, [stops]);

  // 3. Pacing Data
  const hasElderlyOrKids = useMemo(() => {
    const composition = facts?.party_composition?.value;
    if (composition && typeof composition === 'object') {
      return Boolean(composition.elderly || composition.children || composition.infant);
    }
    return true; // Default to heightened awareness for family trips
  }, [facts]);

  // 4. Luxury Hotel Perks
  const luxuryProperties: LuxuryPropertyPerk[] = useMemo(() => {
    const entityChecks = packet?.public_checker_entity_checks as Array<Record<string, any>> | undefined;
    const foundEntities = Array.isArray(entityChecks) ? entityChecks : [];

    const parsedProps: LuxuryPropertyPerk[] = [];
    if (foundEntities.length > 0) {
      foundEntities.forEach((item) => {
        const name = String(item.name || 'Luxury Hotel').replace(/for$/i, '').trim();
        parsedProps.push({
          hotelName: name,
          city: stops[2]?.city ?? 'Paris',
          nights: 3,
          partnershipDesk: 'Virtuoso & Preferred Partner Direct Desk',
          estimatedTotalValue: 640,
          perks: [
            { icon: '🥐', label: 'Daily Breakfast for Two', estimatedValue: 270, description: 'Complimentary full breakfast daily' },
            { icon: '💳', label: 'Hotel Credit', estimatedValue: 100, description: 'USD 100 equivalent property credit' },
            { icon: '⬆️', label: 'Room Category Upgrade', estimatedValue: 220, description: 'Subject to check-in availability' },
            { icon: '⏰', label: 'Flexible Checkout', estimatedValue: 50, description: '4:00 PM late checkout guarantee' },
          ],
        });
      });
    }

    if (parsedProps.length === 0) {
      parsedProps.push(
        {
          hotelName: 'The Ritz Paris',
          city: 'Paris, France',
          nights: 3,
          partnershipDesk: 'Virtuoso Preferred Desk',
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
      );
    }
    return parsedProps;
  }, [packet, stops]);

  return (
    <div style={{ marginTop: 28, marginBottom: 28 }}>
      {/* Visual Navigation Pill Tabs */}
      <div
        style={{
          display: 'flex',
          gap: 6,
          background: '#0d1117',
          padding: '6px',
          borderRadius: 14,
          border: '1px solid #21262d',
          marginBottom: 16,
          overflowX: 'auto',
          WebkitOverflowScrolling: 'touch',
        }}
      >
        <button
          onClick={() => setActiveTab('stress')}
          style={{
            flex: '1 1 auto',
            minWidth: 140,
            padding: '9px 12px',
            borderRadius: 9,
            border: activeTab === 'stress' ? '1px solid #f85149' : '1px solid transparent',
            background: activeTab === 'stress' ? 'rgba(248,81,73,0.12)' : 'transparent',
            color: activeTab === 'stress' ? '#f85149' : '#8b949e',
            fontSize: 12.5,
            fontWeight: 600,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 6,
            transition: 'all 0.15s ease',
            whiteSpace: 'nowrap',
          }}
        >
          <span>⏱️</span> Connection Stress
        </button>

        <button
          onClick={() => setActiveTab('isoAirport')}
          style={{
            flex: '1 1 auto',
            minWidth: 155,
            padding: '9px 12px',
            borderRadius: 9,
            border: activeTab === 'isoAirport' ? '1px solid #38bdf8' : '1px solid transparent',
            background: activeTab === 'isoAirport' ? 'rgba(56,189,248,0.14)' : 'transparent',
            color: activeTab === 'isoAirport' ? '#38bdf8' : '#8b949e',
            fontSize: 12.5,
            fontWeight: 700,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 6,
            transition: 'all 0.15s ease',
            whiteSpace: 'nowrap',
          }}
        >
          <span>🏗️</span> 2.5D Airport Cutaway
        </button>

        <button
          onClick={() => setActiveTab('globe3d')}
          style={{
            flex: '1 1 auto',
            minWidth: 150,
            padding: '9px 12px',
            borderRadius: 9,
            border: activeTab === 'globe3d' ? '1px solid #60a5fa' : '1px solid transparent',
            background: activeTab === 'globe3d' ? 'rgba(96,165,250,0.14)' : 'transparent',
            color: activeTab === 'globe3d' ? '#60a5fa' : '#8b949e',
            fontSize: 12.5,
            fontWeight: 700,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 6,
            transition: 'all 0.15s ease',
            whiteSpace: 'nowrap',
          }}
        >
          <span>🌐</span> 3D Globe Flight Arc
        </button>

        <button
          onClick={() => setActiveTab('route')}
          style={{
            flex: '1 1 auto',
            minWidth: 140,
            padding: '9px 12px',
            borderRadius: 9,
            border: activeTab === 'route' ? '1px solid #39d0d8' : '1px solid transparent',
            background: activeTab === 'route' ? 'rgba(57,208,216,0.12)' : 'transparent',
            color: activeTab === 'route' ? '#39d0d8' : '#8b949e',
            fontSize: 12.5,
            fontWeight: 600,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 6,
            transition: 'all 0.15s ease',
            whiteSpace: 'nowrap',
          }}
        >
          <span>🗺️</span> Route Arc Ribbon
        </button>

        <button
          onClick={() => setActiveTab('pacing')}
          style={{
            flex: '1 1 auto',
            minWidth: 140,
            padding: '9px 12px',
            borderRadius: 9,
            border: activeTab === 'pacing' ? '1px solid #d29922' : '1px solid transparent',
            background: activeTab === 'pacing' ? 'rgba(210,153,34,0.12)' : 'transparent',
            color: activeTab === 'pacing' ? '#d29922' : '#8b949e',
            fontSize: 12.5,
            fontWeight: 600,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 6,
            transition: 'all 0.15s ease',
            whiteSpace: 'nowrap',
          }}
        >
          <span>⚡</span> Pacing Curve
        </button>

        <button
          onClick={() => setActiveTab('isoHotel')}
          style={{
            flex: '1 1 auto',
            minWidth: 155,
            padding: '9px 12px',
            borderRadius: 9,
            border: activeTab === 'isoHotel' ? '1px solid #34d399' : '1px solid transparent',
            background: activeTab === 'isoHotel' ? 'rgba(52,211,153,0.14)' : 'transparent',
            color: activeTab === 'isoHotel' ? '#34d399' : '#8b949e',
            fontSize: 12.5,
            fontWeight: 700,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 6,
            transition: 'all 0.15s ease',
            whiteSpace: 'nowrap',
          }}
        >
          <span>🏨</span> 2.5D Suite Cutaway
        </button>

        <button
          onClick={() => setActiveTab('comparison')}
          style={{
            flex: '1 1 auto',
            minWidth: 140,
            padding: '9px 12px',
            borderRadius: 9,
            border: activeTab === 'comparison' ? '1px solid #58a6ff' : '1px solid transparent',
            background: activeTab === 'comparison' ? 'rgba(88,166,255,0.12)' : 'transparent',
            color: activeTab === 'comparison' ? '#58a6ff' : '#8b949e',
            fontSize: 12.5,
            fontWeight: 600,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 6,
            transition: 'all 0.15s ease',
            whiteSpace: 'nowrap',
          }}
        >
          <span>⚖️</span> Before vs. After
        </button>

        <button
          onClick={() => setActiveTab('perks')}
          style={{
            flex: '1 1 auto',
            minWidth: 140,
            padding: '9px 12px',
            borderRadius: 9,
            border: activeTab === 'perks' ? '1px solid #3fb950' : '1px solid transparent',
            background: activeTab === 'perks' ? 'rgba(63,185,80,0.12)' : 'transparent',
            color: activeTab === 'perks' ? '#3fb950' : '#8b949e',
            fontSize: 12.5,
            fontWeight: 600,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 6,
            transition: 'all 0.15s ease',
            whiteSpace: 'nowrap',
          }}
        >
          <span>💎</span> Perks Radar
        </button>
      </div>

      {/* Render Active Visual Moment */}
      {activeTab === 'stress' ? (
        <LayoverStressGauge segment={layoverSegment} onAdvisorHelp={onAdvisorHelp} />
      ) : null}

      {activeTab === 'isoAirport' ? (
        <IsometricAirportCutaway
          transitHub={layoverSegment.transitHub}
          inboundFlight={layoverSegment.inboundFlight}
          connectingFlight={layoverSegment.connectingFlight}
          scheduledMinutes={layoverSegment.scheduledMinutes}
        />
      ) : null}

      {activeTab === 'globe3d' ? (
        <Interactive3DGlobeFlightArc />
      ) : null}

      {activeTab === 'route' ? (
        <RouteArcRibbon stops={stops} legs={legs} />
      ) : null}

      {activeTab === 'pacing' ? (
        <PacingExhaustionCurve hasElderlyOrKids={hasElderlyOrKids} />
      ) : null}

      {activeTab === 'isoHotel' ? (
        <IsometricHotelSanctuary onClaim={onAdvisorHelp} />
      ) : null}

      {activeTab === 'comparison' ? (
        <BeforeAfterComparison />
      ) : null}

      {activeTab === 'perks' ? (
        <HiddenPerksRadar properties={luxuryProperties} onClaimPerks={onAdvisorHelp} />
      ) : null}
    </div>
  );
}
