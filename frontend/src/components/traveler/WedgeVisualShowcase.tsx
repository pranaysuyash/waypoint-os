'use client';

import React, { useId, useState, useMemo } from 'react';
import { handleListNavigation, tabPanelProps, tabProps } from '@/lib/accessibility';
import {
  Activity,
  BedDouble,
  Building2,
  Clock,
  Globe,
  Route,
  Scale,
  Sparkles,
  type LucideIcon,
} from 'lucide-react';
import type { RunStatusResponse } from '@/types/spine';
import { LayoverStressGauge, type LayoverSegment } from './LayoverStressGauge';
import { RouteArcRibbon, type RouteStop, type RouteLeg } from './RouteArcRibbon';
import { PacingExhaustionCurve, type DayPacingData } from './PacingExhaustionCurve';
import { BeforeAfterComparison, type ComparisonItem } from './BeforeAfterComparison';
import { HiddenPerksRadar, type LuxuryPropertyPerk } from './HiddenPerksRadar';
import { IsometricAirportCutaway } from './IsometricAirportCutaway';
import { Interactive3DGlobeFlightArc, type GlobeWaypoint } from './Interactive3DGlobeFlightArc';
import { IsometricHotelSanctuary, type RoomTierComparison } from './IsometricHotelSanctuary';

export type WedgeScenarioKey =
  | 'tokyo_kyoto'
  | 'amalfi_rome'
  | 'dubai_desert'
  | 'singapore_family'
  | 'swiss_alps';

export interface WedgeScenarioBundle {
  key: WedgeScenarioKey;
  badge: string;
  title: string;
  windowLabel: string;
  routeSummary: string;
  partySummary: string;
  budgetSummary: string;
  score: number;
  statusLabel: string;
  criticalCount: number;
  warningCount: number;
  infoCount: number;
  weatherSummary: string;
  stopsSummary: string;
  flowSummary: string;
  perksValueSummary: string;
  samplePasteText: string;
  findings: {
    sev: 'Critical' | 'Warning' | 'Info';
    label: string;
    body: string;
  }[];
  dossierRows: {
    label: string;
    value: string;
  }[];
  stops: RouteStop[];
  legs: RouteLeg[];
  globeWaypoints: GlobeWaypoint[];
  activeLegTitle: string;
  layoverSegment: LayoverSegment;
  pacingDays: DayPacingData[];
  hasElderlyOrKids: boolean;
  sanctuaryHotel: RoomTierComparison;
  luxuryProperties: LuxuryPropertyPerk[];
  comparisonItems: ComparisonItem[];
}

export const WEDGE_SCENARIO_CATALOG: Record<WedgeScenarioKey, WedgeScenarioBundle> = {
  tokyo_kyoto: {
    key: 'tokyo_kyoto',
    badge: 'Tokyo & Kyoto · Oct',
    title: 'Autumn Honeymoon in Tokyo & Kyoto',
    windowLabel: 'Oct 12–22, 2026 · 10 Days',
    routeSummary: 'SFO → LAX → NRT → KYO → HND',
    partySummary: '2 adults · honeymoon',
    budgetSummary: '$14,000 total',
    score: 58,
    statusLabel: 'Tight Hub & Day 4 Overload',
    criticalCount: 1,
    warningCount: 2,
    infoCount: 1,
    weatherSummary: '19°C crisp autumn · low rain',
    stopsSummary: 'Aman Tokyo + Kyoto + Nara',
    flowSummary: 'Day 4 has 4 shrines in 8h',
    perksValueSummary: '+$1,240 Virtuoso perks',
    samplePasteText:
      'Origin city: San Francisco (SFO)\nTrip window: October 12-22, 2026\n2 travelers, honeymoon trip to Tokyo & Kyoto\nBudget: $14,000 total\nDay 1: SFO -> NRT via LAX (47m layover at LAX), check in Aman Tokyo\nDay 4: Shinkansen to Kyoto, Fushimi Inari + Arashiyama + Gion + Nara in one day\nDay 7: Check in The Ritz-Carlton Kyoto, kaiseki dinner',
    findings: [
      {
        sev: 'Critical',
        label: '47-minute LAX connection is below international MCT',
        body: 'Terminal 7 to Tom Bradley International Terminal requires 90m minimum buffer. High probability of missed NRT long-haul departure.',
      },
      {
        sev: 'Warning',
        label: 'Day 4 Kyoto stacks 4 cross-city districts after Shinkansen',
        body: 'Fushimi Inari (south), Arashiyama (west), Nara (45m rail), and Gion in one day exceeds 22,000 steps with 3.5h transit overhead.',
      },
      {
        sev: 'Warning',
        label: 'Unclaimed Virtuoso & STARS perks at Aman Tokyo & Ritz-Carlton',
        body: 'Direct partner booking unlocks daily breakfast for two, $200 property credits, and priority suite upgrade (+$1,240 value) at identical rate.',
      },
      {
        sev: 'Info',
        label: 'Shinkansen oversized baggage reservation required',
        body: 'Tokaido Shinkansen requires pre-reserved oversized luggage seats for suitcases over 160cm total dimensions.',
      },
    ],
    dossierRows: [
      { label: 'Duration', value: '10 days · 4 rail/air legs · 2 luxury hotels' },
      { label: 'Travelers', value: '2 adults · honeymoon pace' },
      { label: 'Hub Risk', value: 'LAX 47m transfer (needs 90m+ MCT)' },
      { label: 'VIP Value', value: '+$1,240 unclaimed hotel credits & breakfast' },
    ],
    stops: [
      { id: '1', code: 'SFO', city: 'San Francisco', country: 'USA', highlight: 'Origin departure' },
      { id: '2', code: 'LAX', city: 'Los Angeles', country: 'USA', highlight: '47m tight T7 → TBIT hub' },
      { id: '3', code: 'NRT', city: 'Tokyo', country: 'Japan', stayDays: 4, highlight: 'Aman Tokyo (Otemachi)' },
      { id: '4', code: 'KYO', city: 'Kyoto', country: 'Japan', stayDays: 5, highlight: 'The Ritz-Carlton Kyoto' },
    ],
    legs: [
      { fromId: '1', toId: '2', mode: 'flight', durationText: '1h 35m', notes: 'Short-haul feeder into LAX Terminal 7', status: 'verified' },
      { fromId: '2', toId: '3', mode: 'flight', durationText: '11h 15m', notes: 'Transpacific NH5 — Critical 47m LAX TBIT transfer', status: 'warning' },
      { fromId: '3', toId: '4', mode: 'train', durationText: '2h 15m', notes: 'Nozomi Shinkansen Tokyo → Kyoto Station', status: 'optimized' },
    ],
    globeWaypoints: [
      { id: '1', code: 'SFO', city: 'San Francisco', lat: 37.6213, lng: -122.379, isOrigin: true },
      { id: '2', code: 'LAX', city: 'Los Angeles', lat: 33.9416, lng: -118.4085 },
      { id: '3', code: 'NRT', city: 'Tokyo', lat: 35.772, lng: 140.3929 },
      { id: '4', code: 'KIX', city: 'Kyoto / Osaka', lat: 35.0116, lng: 135.7681 },
    ],
    activeLegTitle: 'SFO → LAX → NRT → KYO',
    layoverSegment: {
      inboundFlight: 'UA 1492 (SFO → LAX)',
      connectingFlight: 'NH 005 (LAX → NRT)',
      transitHub: 'Los Angeles International (LAX T7 → TBIT)',
      scheduledMinutes: 47,
      minimumSafeMinutes: 90,
      terminalFrom: 'Terminal 7',
      terminalTo: 'Tom Bradley Intl (TBIT)',
    },
    pacingDays: [
      {
        dayNumber: 1,
        label: 'Transpacific Arrival',
        activitiesCount: 2,
        estimatedSteps: 7200,
        standingHours: 3.0,
        exhaustionScore: 52,
        notes: 'LAX connection sprint + 11h flight to NRT + private transfer to Aman Tokyo.',
      },
      {
        dayNumber: 2,
        label: 'Tokyo Tsukiji & Ginza',
        activitiesCount: 3,
        estimatedSteps: 13400,
        standingHours: 5.5,
        exhaustionScore: 68,
        notes: 'Outer market tasting, TeamLab Planets, and omakase dinner in Ginza.',
      },
      {
        dayNumber: 3,
        label: 'Meiji Shrine & Shibuya',
        activitiesCount: 3,
        estimatedSteps: 11800,
        standingHours: 4.5,
        exhaustionScore: 58,
        notes: 'Morning forest walk at Meiji Jingu, Omotesando architecture, Aman spa recovery.',
      },
      {
        dayNumber: 4,
        label: 'Kyoto 4-District Burnout',
        activitiesCount: 5,
        estimatedSteps: 22800,
        standingHours: 9.8,
        exhaustionScore: 96,
        notes: 'Shinkansen + Fushimi Inari + Arashiyama Bamboo Grove + Nara deer park + Gion in one day. Critical overload!',
      },
      {
        dayNumber: 5,
        label: 'Kamogawa River & Tea',
        activitiesCount: 2,
        estimatedSteps: 9400,
        standingHours: 3.8,
        exhaustionScore: 49,
        notes: 'Private Uji matcha ceremony and riverside stroll from Ritz-Carlton Kyoto.',
      },
    ],
    hasElderlyOrKids: false,
    sanctuaryHotel: {
      hotelName: 'Aman Tokyo',
      city: 'Otemachi Tower, Tokyo',
      consortiaProgram: 'Virtuoso & Aman Private Preferred Desk',
      roomRatePublic: 1850,
      otaRoom: {
        category: 'Deluxe Room (Standard Floor)',
        areaSqm: 71,
        view: 'City Grid Side View',
        breakfastCost: 110,
        credits: 0,
        cancellation: 'Strict 14-day penalty',
        upgradeEligible: false,
      },
      waypointSuite: {
        category: 'Premier Suite Imperial Palace View',
        areaSqm: 141,
        view: 'Imperial Palace Gardens & Mt. Fuji Horizon',
        breakfastCost: 0,
        credits: 100,
        cancellation: 'Flexible advisory hold & priority terms',
        upgradeEligible: true,
        amenitiesValue: 740,
      },
    },
    luxuryProperties: [
      {
        hotelName: 'Aman Tokyo',
        city: 'Tokyo, Japan',
        nights: 4,
        partnershipDesk: 'Virtuoso & Aman Preferred Partner Desk',
        estimatedTotalValue: 740,
        perks: [
          { icon: '🍱', label: 'Daily Japanese or Western Breakfast', estimatedValue: 360, description: 'Complimentary full breakfast for two daily at Arva or in-suite' },
          { icon: '💳', label: 'Aman Spa & Dining Credit', estimatedValue: 100, description: '100 USD equivalent credit applied to folio' },
          { icon: '⬆️', label: 'Priority Room Category Upgrade', estimatedValue: 230, description: 'Upgrade to Palace Garden View upon arrival subject to availability' },
          { icon: '⏰', label: 'Early Check-in & 4:00 PM Late Checkout', estimatedValue: 50, description: 'Guaranteed flexible arrival/departure handling' },
        ],
      },
      {
        hotelName: 'The Ritz-Carlton Kyoto',
        city: 'Kyoto, Japan',
        nights: 4,
        partnershipDesk: 'Marriott STARS & Virtuoso Preferred',
        estimatedTotalValue: 500,
        perks: [
          { icon: '🥐', label: 'Pierre Hermé Daily Breakfast for Two', estimatedValue: 240, description: 'Famous Pierre Hermé croissant & washoku breakfast daily' },
          { icon: '💳', label: 'Property Dining Credit', estimatedValue: 100, description: '100 USD credit for Mizuki kaiseki or tempura dining' },
          { icon: '⬆️', label: 'Kamogawa River View Upgrade', estimatedValue: 160, description: 'Priority upgrade to Luxury River View category' },
        ],
      },
    ],
    comparisonItems: [
      {
        dimension: 'LAX Transpacific Hub Transfer',
        before: {
          title: '47-minute terminal sprint (LAX T7 → TBIT)',
          description: 'Separate domestic feeder tightness leaves zero margin for gate hold or inter-terminal walkway.',
          riskBadge: '74% Misconnect Risk',
        },
        after: {
          title: 'Direct SFO → HND nonstop or 125m protected LAX cushion',
          description: 'Single ticketed Star Alliance/oneworld itinerary with tarmac luggage protection.',
          advantageBadge: 'Zero Hub Stress',
        },
      },
      {
        dimension: 'Kyoto Shrine & Bamboo Pacing',
        before: {
          title: 'Fushimi Inari + Arashiyama + Nara + Gion on Day 4',
          description: '3.5 hours spent crisscrossing Kyoto & Nara by train during peak midday crowds (11am–3pm).',
          riskBadge: '96% Burnout Spike',
        },
        after: {
          title: 'East vs. West geographic clustering across 2 mornings',
          description: 'Dawn 6:30am private car to Arashiyama on Day 4; Fushimi Inari + Gion paired on Day 5.',
          advantageBadge: 'Crowd-Free Flow',
        },
      },
      {
        dimension: 'Aman Tokyo & Ritz-Carlton Kyoto Booking',
        before: {
          title: 'Standard online direct/OTA room-only rate',
          description: 'Pays $110/day extra for breakfast and receives entry-tier city view allocation.',
          riskBadge: '$1,240 Left Unclaimed',
        },
        after: {
          title: 'Virtuoso & Marriott STARS Partner Rate Parity',
          description: 'Same public nightly rate with daily breakfast for two, $200 credits, and Palace/River view upgrade priority.',
          advantageBadge: '+$1,240 VIP Value',
        },
      },
    ],
  },
  amalfi_rome: {
    key: 'amalfi_rome',
    badge: 'Rome & Amalfi · Jun',
    title: 'Italian Coast & Rome Heritage Escape',
    windowLabel: 'Jun 08–18, 2026 · 10 Days',
    routeSummary: 'JFK → LHR → FCO → NAP → Ravello',
    partySummary: '4 travelers · family',
    budgetSummary: '$18,500 total',
    score: 62,
    statusLabel: 'LHR 50m Risk & Day 4 Overload',
    criticalCount: 1,
    warningCount: 2,
    infoCount: 1,
    weatherSummary: '28°C Mediterranean sun',
    stopsSummary: 'Rome + Positano + Ravello',
    flowSummary: 'Vatican + Colosseum stacked',
    perksValueSummary: '+$1,120 Rocco Forte & Belmond',
    samplePasteText:
      'Origin city: New York (JFK)\nTrip window: June 8-18, 2026\n4 travelers, family trip to Rome and Amalfi Coast\nBudget: $18,500 total\nDay 1: JFK -> FCO via London Heathrow (50m layover at LHR T5 to T3), check in Hotel de Russie\nDay 4: Vatican Museums (9am) + Colosseum (12pm) + Borghese Gallery (3pm) + Trastevere dinner\nDay 6: High-speed train to Naples, check in Belmond Hotel Caruso in Ravello',
    findings: [
      {
        sev: 'Critical',
        label: '50-minute London Heathrow (T5 → T3) connection is below 90m MCT',
        body: 'Switching from British Airways T5 arrival to T3 departure requires airside bus + security re-screening (75m minimum physical time).',
      },
      {
        sev: 'Warning',
        label: 'Day 4 Rome stacks Vatican, Colosseum, and Borghese in 30°C heat',
        body: '21,500 steps across three major security-screened monuments with <30m transit slack between timed entry tickets.',
      },
      {
        sev: 'Warning',
        label: 'Unclaimed Rocco Forte Knights & Belmond Bellini Club perks',
        body: 'Hotel de Russie and Belmond Hotel Caruso include +$1,120 in complimentary garden breakfasts, dining credits, and suite upgrades.',
      },
      {
        sev: 'Info',
        label: 'Naples Afragola vs. Napoli Centrale private transfer alignment',
        body: 'Verify driver meet-and-greet station so family luggage avoids stairs at Circumvesuviana platforms.',
      },
    ],
    dossierRows: [
      { label: 'Duration', value: '10 days · 4 segments · 2 luxury hotels' },
      { label: 'Travelers', value: '4 travelers · multi-generational family' },
      { label: 'Hub Risk', value: 'LHR T5 → T3 50m connection (35m deficit)' },
      { label: 'VIP Value', value: '+$1,120 Rocco Forte & Belmond Bellini perks' },
    ],
    stops: [
      { id: '1', code: 'JFK', city: 'New York', country: 'USA', highlight: 'Departure origin' },
      { id: '2', code: 'LHR', city: 'London', country: 'UK', highlight: '50m tight T5 → T3 hub' },
      { id: '3', code: 'FCO', city: 'Rome', country: 'Italy', stayDays: 4, highlight: 'Hotel de Russie' },
      { id: '4', code: 'NAP', city: 'Amalfi / Ravello', country: 'Italy', stayDays: 5, highlight: 'Belmond Hotel Caruso' },
    ],
    legs: [
      { fromId: '1', toId: '2', mode: 'flight', durationText: '7h 05m', notes: 'Overnight transatlantic BA178 into LHR T5', status: 'verified' },
      { fromId: '2', toId: '3', mode: 'flight', durationText: '2h 35m', notes: 'Short-haul LHR → FCO — Tight 50m terminal change', status: 'warning' },
      { fromId: '3', toId: '4', mode: 'train', durationText: '1h 10m + 1h car', notes: 'Frecciarossa Rome → Naples + private cliffside Mercedes V-Class', status: 'optimized' },
    ],
    globeWaypoints: [
      { id: '1', code: 'JFK', city: 'New York', lat: 40.6413, lng: -73.7781, isOrigin: true },
      { id: '2', code: 'LHR', city: 'London', lat: 51.47, lng: -0.4543 },
      { id: '3', code: 'FCO', city: 'Rome', lat: 41.8003, lng: 12.2389 },
      { id: '4', code: 'NAP', city: 'Amalfi Coast', lat: 40.6333, lng: 14.6029 },
    ],
    activeLegTitle: 'JFK → LHR → FCO → NAP',
    layoverSegment: {
      inboundFlight: 'BA 178 (JFK → LHR)',
      connectingFlight: 'BA 548 (LHR → FCO)',
      transitHub: 'London Heathrow (LHR T5 → T3)',
      scheduledMinutes: 50,
      minimumSafeMinutes: 90,
      terminalFrom: 'Terminal 5',
      terminalTo: 'Terminal 3',
    },
    pacingDays: [
      {
        dayNumber: 1,
        label: 'Arrival & Piazza del Popolo',
        activitiesCount: 2,
        estimatedSteps: 8500,
        standingHours: 3.5,
        exhaustionScore: 55,
        notes: 'JFK → LHR → FCO transfer + check-in at Hotel de Russie. Light Pincio garden stroll.',
      },
      {
        dayNumber: 2,
        label: 'Historic Center & Pantheon',
        activitiesCount: 3,
        estimatedSteps: 13200,
        standingHours: 5.5,
        exhaustionScore: 71,
        notes: 'Pantheon, Piazza Navona, and private evening golf-cart tour.',
      },
      {
        dayNumber: 3,
        label: 'Villa Farnesina & Leisure',
        activitiesCount: 2,
        estimatedSteps: 8900,
        standingHours: 3.5,
        exhaustionScore: 46,
        notes: 'Relaxed morning fresco tour + afternoon rest at Le Jardin de Russie.',
      },
      {
        dayNumber: 4,
        label: 'Rome Mega-Day (Burnout)',
        activitiesCount: 5,
        estimatedSteps: 21500,
        standingHours: 9.5,
        exhaustionScore: 96,
        notes: 'Vatican (9am), Colosseum (12pm), Borghese (3pm), Trastevere (7pm). Critical summer heat & queue burnout!',
      },
      {
        dayNumber: 5,
        label: 'Frecciarossa to Ravello',
        activitiesCount: 2,
        estimatedSteps: 9200,
        standingHours: 3.8,
        exhaustionScore: 52,
        notes: 'High-speed rail to Naples + cliffside transfer to Belmond Hotel Caruso infinity pool.',
      },
    ],
    hasElderlyOrKids: true,
    sanctuaryHotel: {
      hotelName: 'Hotel de Russie',
      city: 'Via del Babuino, Rome',
      consortiaProgram: 'Rocco Forte Knights & Virtuoso Preferred',
      roomRatePublic: 1620,
      otaRoom: {
        category: 'Classic Room (Street Side)',
        areaSqm: 32,
        view: 'Internal Alley View',
        breakfastCost: 95,
        credits: 0,
        cancellation: 'Non-refundable 14-day lock',
        upgradeEligible: false,
      },
      waypointSuite: {
        category: 'Deluxe Suite Secret Garden View',
        areaSqm: 64,
        view: 'Terraced Secret Garden & Pincian Hill',
        breakfastCost: 0,
        credits: 100,
        cancellation: 'Flexible advisory terms',
        upgradeEligible: true,
        amenitiesValue: 640,
      },
    },
    luxuryProperties: [
      {
        hotelName: 'Hotel de Russie',
        city: 'Rome, Italy',
        nights: 4,
        partnershipDesk: 'Rocco Forte Knights / Virtuoso Preferred',
        estimatedTotalValue: 640,
        perks: [
          { icon: '🥐', label: 'Daily Buffet Breakfast in Secret Garden', estimatedValue: 260, description: 'Complimentary breakfast daily at Le Jardin de Russie' },
          { icon: '💳', label: 'Stravinskij Bar & Dining Credit', estimatedValue: 100, description: '100 EUR food & beverage credit applied to folio' },
          { icon: '⬆️', label: 'Garden View Room Category Upgrade', estimatedValue: 230, description: 'Priority upgrade upon check-in' },
          { icon: '⏰', label: 'Early Check-in & 4:00 PM Late Checkout', estimatedValue: 50, description: 'Flexible arrival and departure priority' },
        ],
      },
      {
        hotelName: 'Belmond Hotel Caruso',
        city: 'Ravello, Amalfi Coast',
        nights: 4,
        partnershipDesk: 'Belmond Bellini Club & Virtuoso',
        estimatedTotalValue: 480,
        perks: [
          { icon: '🥐', label: 'Daily Cliffside Terrace Breakfast', estimatedValue: 200, description: 'Full Neapolitan & buffet breakfast overlooking Amalfi sea' },
          { icon: '💳', label: 'Belvedere Restaurant Credit', estimatedValue: 100, description: '100 EUR credit for cliffside dining or boat charter' },
          { icon: '⬆️', label: 'Sea-View Category Upgrade', estimatedValue: 180, description: 'Bellini Club priority room upgrade on arrival' },
        ],
      },
    ],
    comparisonItems: [
      {
        dimension: 'Flight Connection & Hub Transfer',
        before: {
          title: '50-minute tight connection at LHR T5 → T3',
          description: 'Minimum connection time broken. High probability of lost baggage or missed Rome flight.',
          riskBadge: '68% Bag Miss Risk',
        },
        after: {
          title: 'Direct JFK → FCO nonstop or 115m protected LHR buffer',
          description: 'Eliminates UK transit security re-screening or provides VIP airside escort.',
          advantageBadge: 'Protected Arrival',
        },
      },
      {
        dimension: 'Rome Monument Pacing',
        before: {
          title: 'Vatican, Colosseum & Borghese in one 30°C day',
          description: 'Overlapping timed-entry windows across opposite sides of the Tiber with zero heat recovery.',
          riskBadge: '96% Heat Burnout',
        },
        after: {
          title: '7:30am Vatican Keyholder + Colosseum Underground next morning',
          description: 'Private before-hours entry spaced across 2 mornings with afternoon pool/garden downtime.',
          advantageBadge: 'VIP Keyholder Pace',
        },
      },
      {
        dimension: 'Hotel de Russie & Belmond Caruso Privileges',
        before: {
          title: 'Standard OTA room-only booking',
          description: 'Courtyard room allocation, $95/day extra breakfast charges, zero property credits.',
          riskBadge: '$1,120 Unclaimed',
        },
        after: {
          title: 'Rocco Forte Knights & Belmond Bellini Club Desk',
          description: 'Same public rate with daily garden/sea breakfast, $200 credits, and priority view upgrades.',
          advantageBadge: '+$1,120 Unlocked',
        },
      },
    ],
  },
  dubai_desert: {
    key: 'dubai_desert',
    badge: 'Dubai & Desert · Jun',
    title: 'Dubai Skyline & Al Maha Desert Reserve',
    windowLabel: 'Jun 14–21, 2026 · 7 Days',
    routeSummary: 'LHR → IST → DXB → Al Maha',
    partySummary: '2 travelers · couple',
    budgetSummary: '$11,500 total',
    score: 59,
    statusLabel: '42°C Midday Heat & 55m IST Hub',
    criticalCount: 1,
    warningCount: 2,
    infoCount: 1,
    weatherSummary: '41°C peak midday · UV 11+',
    stopsSummary: 'Atlantis The Royal + Al Maha',
    flowSummary: 'Outdoor desert safari at 1pm',
    perksValueSummary: '+$980 Virtuoso & STARS perks',
    samplePasteText:
      'Origin city: London (LHR)\nTrip window: June 14-21, 2026\n2 travelers for Dubai around June next year\nBudget: $11,500 total\nDay 1: LHR -> DXB via Istanbul (55m layover at IST), check in Atlantis The Royal\nDay 3: Old Dubai Gold Souk walking tour (12pm) + Miracle Garden + Desert Dune Safari (2pm) + Burj Khalifa\nDay 5: Transfer to Al Maha Desert Resort & Spa',
    findings: [
      {
        sev: 'Critical',
        label: 'Day 3 schedules outdoor Gold Souk & Desert Dunes at 12pm–3pm in 41°C June heat',
        body: 'Midday June surface temperatures exceed 42°C (108°F), and Dubai Miracle Garden is seasonally closed May–September.',
      },
      {
        sev: 'Warning',
        label: '55-minute Istanbul (IST) transfer requires 1.4km concourse walk',
        body: 'IST mega-terminal gates span up to 28 minutes walking time plus international transit security check.',
      },
      {
        sev: 'Warning',
        label: 'Unclaimed Virtuoso & Marriott STARS perks at Atlantis The Royal & Al Maha',
        body: 'Partner desk attaches daily Gastronomy breakfast, $200 resort credits, and Aquaventure VIP access (+$980 value).',
      },
      {
        sev: 'Info',
        label: 'Shift desert wildlife drives to 5:45am dawn and 5:30pm sundowner slots',
        body: 'Al Maha Arabian oryx and falconry experiences operate in cool twilight windows to avoid extreme thermal load.',
      },
    ],
    dossierRows: [
      { label: 'Duration', value: '7 days · 3 segments · Palm Jumeirah + Desert' },
      { label: 'Travelers', value: '2 adults · luxury couple getaway' },
      { label: 'Climate Flag', value: '41°C June midday — shift outdoor stops to dawn/dusk' },
      { label: 'VIP Value', value: '+$980 Atlantis The Royal & Al Maha perks' },
    ],
    stops: [
      { id: '1', code: 'LHR', city: 'London', country: 'UK', highlight: 'Origin departure' },
      { id: '2', code: 'IST', city: 'Istanbul', country: 'Turkey', highlight: '55m mega-terminal transit' },
      { id: '3', code: 'DXB', city: 'Dubai (Palm)', country: 'UAE', stayDays: 4, highlight: 'Atlantis The Royal' },
      { id: '4', code: 'DWC', city: 'Al Maha Reserve', country: 'UAE', stayDays: 3, highlight: 'Al Maha Desert Resort' },
    ],
    legs: [
      { fromId: '1', toId: '2', mode: 'flight', durationText: '3h 50m', notes: 'TK1980 LHR → IST arrival at Concourse B', status: 'verified' },
      { fromId: '2', toId: '3', mode: 'flight', durationText: '4h 30m', notes: 'TK760 IST → DXB — 55m long-walk terminal transfer', status: 'warning' },
      { fromId: '3', toId: '4', mode: 'transfer', durationText: '50m SUV', notes: 'Private climate-controlled Range Rover into Dubai Desert Conservation Reserve', status: 'optimized' },
    ],
    globeWaypoints: [
      { id: '1', code: 'LHR', city: 'London', lat: 51.47, lng: -0.4543, isOrigin: true },
      { id: '2', code: 'IST', city: 'Istanbul', lat: 41.2753, lng: 28.7519 },
      { id: '3', code: 'DXB', city: 'Dubai', lat: 25.2532, lng: 55.3657 },
      { id: '4', code: 'AUH', city: 'Al Maha Reserve', lat: 24.8317, lng: 55.6611 },
    ],
    activeLegTitle: 'LHR → IST → DXB → AL MAHA',
    layoverSegment: {
      inboundFlight: 'TK 1980 (LHR → IST)',
      connectingFlight: 'TK 760 (IST → DXB)',
      transitHub: 'Istanbul Airport (IST Concourse B → F)',
      scheduledMinutes: 55,
      minimumSafeMinutes: 90,
      terminalFrom: 'Concourse B',
      terminalTo: 'Concourse F',
    },
    pacingDays: [
      {
        dayNumber: 1,
        label: 'DXB Arrival & Palm Check-in',
        activitiesCount: 2,
        estimatedSteps: 7400,
        standingHours: 2.8,
        exhaustionScore: 48,
        notes: 'Arrival at DXB VIP Majlis lounge + check-in at Atlantis The Royal Cloud 22.',
      },
      {
        dayNumber: 2,
        label: 'Indoor Museum of the Future',
        activitiesCount: 3,
        estimatedSteps: 10200,
        standingHours: 4.2,
        exhaustionScore: 56,
        notes: 'Climate-controlled Museum of the Future, Dubai Mall aquarium, dinner at Nobu by the Beach.',
      },
      {
        dayNumber: 3,
        label: '41°C Midday Souk & Dune Burnout',
        activitiesCount: 5,
        estimatedSteps: 19400,
        standingHours: 8.5,
        exhaustionScore: 95,
        notes: '12pm outdoor Gold Souk + closed Miracle Garden + 2pm desert dunes in 41°C heat. Critical thermal stress!',
      },
      {
        dayNumber: 4,
        label: 'Al Maha Private Pool Villa',
        activitiesCount: 2,
        estimatedSteps: 6100,
        standingHours: 2.2,
        exhaustionScore: 38,
        notes: 'Transfer to Al Maha Bedouin Suite with temperature-cooled private desert plunge pool.',
      },
      {
        dayNumber: 5,
        label: 'Dawn Falconry & Sundowner',
        activitiesCount: 2,
        estimatedSteps: 6800,
        standingHours: 2.5,
        exhaustionScore: 42,
        notes: '5:45am falconry in cool desert breeze + 6:00pm camel sundowner.',
      },
    ],
    hasElderlyOrKids: false,
    sanctuaryHotel: {
      hotelName: 'Atlantis The Royal',
      city: 'Palm Jumeirah, Dubai',
      consortiaProgram: 'Virtuoso Ultraluxe & Royal Club Desk',
      roomRatePublic: 1280,
      otaRoom: {
        category: 'Seascape King Room (Low Floor)',
        areaSqm: 55,
        view: 'Partial Palm Road View',
        breakfastCost: 96,
        credits: 0,
        cancellation: 'Non-refundable summer rate',
        upgradeEligible: false,
      },
      waypointSuite: {
        category: 'Sky Terrace Suite with Skyline Panorama',
        areaSqm: 108,
        view: 'Full Dubai Marina Skyline & Arabian Gulf',
        breakfastCost: 0,
        credits: 100,
        cancellation: 'Flexible advisory hold',
        upgradeEligible: true,
        amenitiesValue: 580,
      },
    },
    luxuryProperties: [
      {
        hotelName: 'Atlantis The Royal',
        city: 'Dubai, UAE',
        nights: 4,
        partnershipDesk: 'Virtuoso Ultraluxe Preferred Desk',
        estimatedTotalValue: 580,
        perks: [
          { icon: '🥐', label: 'Daily Gastronomy Buffet Breakfast', estimatedValue: 260, description: 'Complimentary breakfast for two at Gastronomy (17 live stations)' },
          { icon: '💳', label: 'Celebrity Chef Dining Credit', estimatedValue: 100, description: '100 USD credit at Dinner by Heston, Milos, or Jaleo' },
          { icon: '⬆️', label: 'Palm Skyline View Upgrade', estimatedValue: 170, description: 'Priority upgrade upon check-in' },
          { icon: '🌊', label: 'Cloud 22 & Aquaventure Priority', estimatedValue: 50, description: 'Complimentary cabana/admission priority' },
        ],
      },
      {
        hotelName: 'Al Maha, a Luxury Collection Desert Resort',
        city: 'Dubai Desert Reserve, UAE',
        nights: 3,
        partnershipDesk: 'Marriott STARS & Virtuoso',
        estimatedTotalValue: 400,
        perks: [
          { icon: '🐪', label: 'Full Board + 2 Daily Desert Activities', estimatedValue: 200, description: 'Breakfast, lunch, dinner + private falconry & dune drives included' },
          { icon: '💳', label: 'Timeless Spa Treatment Credit', estimatedValue: 100, description: '100 USD spa credit per stay' },
          { icon: '⏰', label: 'Guaranteed 4:00 PM Late Checkout', estimatedValue: 100, description: 'Stay in cooled Bedouin pool villa until evening flight' },
        ],
      },
    ],
    comparisonItems: [
      {
        dimension: 'Summer Thermal Pacing (June 41°C)',
        before: {
          title: '12:00 PM outdoor Souk + Miracle Garden (closed in summer)',
          description: 'Generic AI schedules outdoor walking at solar noon and includes attractions closed May–September.',
          riskBadge: 'Seasonal & Heat Error',
        },
        after: {
          title: 'Twilight-inverted schedule + private cooled SUV transfers',
          description: 'Indoor architectural icons 11am–4pm; desert falconry at 5:45am and Creek abra dinner at 7:30pm.',
          advantageBadge: 'Climate-Calibrated',
        },
      },
      {
        dimension: 'Flight Routing & DXB Arrival',
        before: {
          title: '55-minute Istanbul mega-hub sprint',
          description: '1.4km concourse walk at IST risks bags missing the connecting DXB flight.',
          riskBadge: 'Tight Mega-Hub',
        },
        after: {
          title: 'Direct LHR → DXB nonstop + Ahlan VIP Fast-Track',
          description: 'Direct widebody arrival with airside buggy meet-and-greet through DXB immigration in 10 minutes.',
          advantageBadge: 'VIP Tarmac Fast-Track',
        },
      },
      {
        dimension: 'Atlantis The Royal & Al Maha Perks',
        before: {
          title: 'Standard OTA booking without breakfast or spa credit',
          description: 'Pays $96/day extra at Gastronomy and loses late-checkout villa access before night flight.',
          riskBadge: '$980 Value Lost',
        },
        after: {
          title: 'Virtuoso & Marriott STARS Direct Desk',
          description: 'Includes daily Gastronomy breakfast, $200 credits, and 4:00 PM late villa checkout.',
          advantageBadge: '+$980 VIP Perks',
        },
      },
    ],
  },
  singapore_family: {
    key: 'singapore_family',
    badge: 'Singapore · Late May',
    title: 'Multi-Gen Family Trip to Singapore',
    windowLabel: 'May 20–26, 2026 · 6 Days',
    routeSummary: 'SFO → TPE → SIN → Sentosa',
    partySummary: '5 travelers · 2 elders, 1 toddler',
    budgetSummary: '$12,800 total',
    score: 62,
    statusLabel: 'Elder Humidity Pace & Sentosa Split',
    criticalCount: 1,
    warningCount: 2,
    infoCount: 1,
    weatherSummary: '32°C · 84% tropical humidity',
    stopsSummary: 'Marina Bay + Sentosa + Mandai',
    flowSummary: 'Universal + Night Safari same day',
    perksValueSummary: '+$920 Raffles & Capella perks',
    samplePasteText:
      'Origin city: San Francisco (SFO)\nTrip window: late May 2026\n5 travelers: 2 adults, 2 elders (grandparents), 1 toddler\nTrip purpose: Family trip to Singapore\nBudget: $12,800 total\nDay 1: SFO -> SIN via Taipei (50m layover at TPE), check in Raffles Singapore\nDay 3: Universal Studios Sentosa (10am) + S.E.A. Aquarium + Mandai Night Safari (7:30pm) in one day\nDay 4: Gardens by the Bay + Marina Bay Sands SkyPark, check in Capella Singapore',
    findings: [
      {
        sev: 'Critical',
        label: 'Day 3 pairs Sentosa Universal Studios (south) with Mandai Night Safari (north) for 2 elders & 1 toddler',
        body: '11 hours of tropical heat (32°C / 84% humidity) plus 90m cross-island transfers breaches multi-generational stamina limits.',
      },
      {
        sev: 'Warning',
        label: '50-minute Taipei (TPE T1 → T2) transfer with wheelchair/stroller assistance',
        body: 'Gate-checked stroller retrieval adds 15m at the jetbridge, leaving only 35m before connecting gate cutoff.',
      },
      {
        sev: 'Warning',
        label: 'Unclaimed Virtuoso perks at Raffles Singapore & Capella Sentosa',
        body: 'Direct advisor booking unlocks daily Tiffin Room breakfast, $200 property credits, and connecting suite priority (+$920 value).',
      },
      {
        sev: 'Info',
        label: 'SG Arrival Card (SGAC) required within 3 days prior to landing',
        body: 'Mandatory digital health & arrival declaration at Changi (SIN) — free via official ICA portal.',
      },
    ],
    dossierRows: [
      { label: 'Duration', value: '6 days · 3 segments · Marina Bay + Sentosa' },
      { label: 'Travelers', value: '5 guests · 2 grandparents + 1 toddler' },
      { label: 'Pacing Flag', value: 'Split Sentosa & Mandai Night Safari across 2 days' },
      { label: 'VIP Value', value: '+$920 Raffles Butler & Capella Virtuoso perks' },
    ],
    stops: [
      { id: '1', code: 'SFO', city: 'San Francisco', country: 'USA', highlight: 'Origin departure' },
      { id: '2', code: 'TPE', city: 'Taipei', country: 'Taiwan', highlight: '50m stroller/elder transfer' },
      { id: '3', code: 'SIN', city: 'Marina Bay', country: 'Singapore', stayDays: 3, highlight: 'Raffles Singapore' },
      { id: '4', code: 'SEN', city: 'Sentosa Island', country: 'Singapore', stayDays: 3, highlight: 'Capella Singapore' },
    ],
    legs: [
      { fromId: '1', toId: '2', mode: 'flight', durationText: '13h 20m', notes: 'Transpacific BR17 SFO → TPE', status: 'verified' },
      { fromId: '2', toId: '3', mode: 'flight', durationText: '4h 35m', notes: 'TPE → SIN — Tight 50m gate-check stroller retrieval', status: 'warning' },
      { fromId: '3', toId: '4', mode: 'transfer', durationText: '20m MPV', notes: 'Private Toyota Alphard with car seat to Sentosa', status: 'optimized' },
    ],
    globeWaypoints: [
      { id: '1', code: 'SFO', city: 'San Francisco', lat: 37.6213, lng: -122.379, isOrigin: true },
      { id: '2', code: 'TPE', city: 'Taipei', lat: 25.0797, lng: 121.2342 },
      { id: '3', code: 'SIN', city: 'Singapore', lat: 1.3644, lng: 103.9915 },
      { id: '4', code: 'SEN', city: 'Sentosa', lat: 1.2494, lng: 103.8303 },
    ],
    activeLegTitle: 'SFO → TPE → SIN → SENTOSA',
    layoverSegment: {
      inboundFlight: 'BR 017 (SFO → TPE)',
      connectingFlight: 'BR 215 (TPE → SIN)',
      transitHub: 'Taipei Taoyuan (TPE Terminal 2)',
      scheduledMinutes: 50,
      minimumSafeMinutes: 85,
      terminalFrom: 'Terminal 2 North',
      terminalTo: 'Terminal 2 South',
    },
    pacingDays: [
      {
        dayNumber: 1,
        label: 'Changi Arrival & Raffles',
        activitiesCount: 2,
        estimatedSteps: 6400,
        standingHours: 2.5,
        exhaustionScore: 48,
        notes: 'Jewel Changi Rain Vortex look + private Alphard transfer to Raffles Courtyard Suite.',
      },
      {
        dayNumber: 2,
        label: 'Cooled Conservatories',
        activitiesCount: 3,
        estimatedSteps: 9200,
        standingHours: 3.8,
        exhaustionScore: 56,
        notes: 'Cloud Forest & Flower Dome (23°C indoor cooled domes) + afternoon nap for grandparents & toddler.',
      },
      {
        dayNumber: 3,
        label: 'Sentosa + Night Safari Burnout',
        activitiesCount: 5,
        estimatedSteps: 19800,
        standingHours: 9.0,
        exhaustionScore: 94,
        notes: 'Universal Studios (10am) + S.E.A. Aquarium + 45km drive to Mandai Night Safari (7:30pm). Over-packed for elders/toddler!',
      },
      {
        dayNumber: 4,
        label: 'Capella Sentosa Pool & Beach',
        activitiesCount: 2,
        estimatedSteps: 5800,
        standingHours: 2.0,
        exhaustionScore: 36,
        notes: 'Check in Capella Manor Villa, peacock garden walk, Palawan beach sunset.',
      },
      {
        dayNumber: 5,
        label: 'Private Bumboat River Cruise',
        activitiesCount: 2,
        estimatedSteps: 7100,
        standingHours: 2.8,
        exhaustionScore: 44,
        notes: 'Seated electric bumboat cruise from Clarke Quay to Marina Bay + Jumbo Chili Crab dinner.',
      },
    ],
    hasElderlyOrKids: true,
    sanctuaryHotel: {
      hotelName: 'Raffles Singapore',
      city: '1 Beach Road, Singapore',
      consortiaProgram: 'Virtuoso & Accor HERA Butler Desk',
      roomRatePublic: 1390,
      otaRoom: {
        category: 'Studio Suite (Standard Allocation)',
        areaSqm: 46,
        view: 'Outer Street Wing',
        breakfastCost: 92,
        credits: 0,
        cancellation: 'Non-refundable 7-day lock',
        upgradeEligible: false,
      },
      waypointSuite: {
        category: 'Palm Court Suite with Verandah & 24h Butler',
        areaSqm: 72,
        view: 'Historic Palm Court Lush Gardens',
        breakfastCost: 0,
        credits: 100,
        cancellation: 'Flexible family cancellation terms',
        upgradeEligible: true,
        amenitiesValue: 540,
      },
    },
    luxuryProperties: [
      {
        hotelName: 'Raffles Singapore',
        city: 'Marina Bay, Singapore',
        nights: 3,
        partnershipDesk: 'Virtuoso & Accor HERA Preferred',
        estimatedTotalValue: 540,
        perks: [
          { icon: '🥐', label: 'Daily Tiffin Room Breakfast', estimatedValue: 220, description: 'Complimentary full breakfast daily at historic Tiffin Room' },
          { icon: '💳', label: 'Butcher’s Block / Spa Credit', estimatedValue: 100, description: '100 USD dining or Raffles Spa credit' },
          { icon: '⬆️', label: 'Palm Court Suite Upgrade', estimatedValue: 170, description: 'Priority suite category upgrade + 24h Raffles Butler' },
          { icon: '⏰', label: 'Early Check-in & 4:00 PM Checkout', estimatedValue: 50, description: 'Guaranteed rest window for toddler nap schedule' },
        ],
      },
      {
        hotelName: 'Capella Singapore',
        city: 'Sentosa Island, Singapore',
        nights: 3,
        partnershipDesk: 'Virtuoso & Leading Hotels Leaders Club',
        estimatedTotalValue: 380,
        perks: [
          { icon: '🥐', label: 'Daily Knolls Garden Breakfast', estimatedValue: 180, description: 'Complimentary breakfast overlooking cascading pools' },
          { icon: '💳', label: 'Cassia & Auriga Spa Credit', estimatedValue: 100, description: '100 USD resort credit applied to folio' },
          { icon: '⬆️', label: 'Sea-View Premier Upgrade', estimatedValue: 100, description: 'Priority room upgrade + Culturist family programming' },
        ],
      },
    ],
    comparisonItems: [
      {
        dimension: 'Multi-Generational Humidity Pacing',
        before: {
          title: 'Universal Studios + Mandai Night Safari on Day 3',
          description: '11-hour day crisscrossing Singapore with 2 grandparents and 1 toddler in 84% humidity.',
          riskBadge: '94% Family Exhaustion',
        },
        after: {
          title: 'Midday 1pm–4pm villa rest + Private Night Safari tram',
          description: 'Splits Sentosa and Mandai across separate days with private chartered buggy at Night Safari.',
          advantageBadge: 'Elder & Toddler Safe',
        },
      },
      {
        dimension: 'Transpacific Flight & Stroller Handling',
        before: {
          title: '50-minute TPE transit with gate-checked stroller',
          description: 'Waiting 15m for jetbridge stroller delivery leaves perilous 35m sprint to SIN gate.',
          riskBadge: 'Stroller Delay Trap',
        },
        after: {
          title: 'Direct SFO → SIN Singapore Airlines nonstop',
          description: 'Eliminates connection entirely; bassinet/family bulkhead seats pre-assigned.',
          advantageBadge: 'Nonstop Comfort',
        },
      },
      {
        dimension: 'Raffles & Capella Family Suites',
        before: {
          title: 'Disconnected OTA rooms without breakfast',
          description: 'No guarantee of adjacent rooms for grandparents and extra $92/day breakfast charges.',
          riskBadge: '$920 Perks Missed',
        },
        after: {
          title: 'Virtuoso Confirmed Connecting/Palm Court Suite',
          description: 'Guaranteed family proximity, daily Tiffin Room & Knolls breakfast, and $200 resort credits.',
          advantageBadge: '+$920 Family Perks',
        },
      },
    ],
  },
  swiss_alps: {
    key: 'swiss_alps',
    badge: 'Swiss Alps · Jul',
    title: 'Glacier Express: Zermatt to St. Moritz',
    windowLabel: 'Jul 04–12, 2026 · 8 Days',
    routeSummary: 'ORD → FRA → ZRH → Zermatt → St. Moritz',
    partySummary: '2 adults · scenic rail',
    budgetSummary: '$15,200 total',
    score: 65,
    statusLabel: 'FRA 45m Schengen Border & Rail Seat Lock',
    criticalCount: 1,
    warningCount: 2,
    infoCount: 1,
    weatherSummary: '18°C alpine sun · crisp peaks',
    stopsSummary: 'Zermatt + Glacier Express + St. Moritz',
    flowSummary: '4-pass rail transfer day',
    perksValueSummary: '+$1,050 Virtuoso Alpine perks',
    samplePasteText:
      'Origin city: Chicago (ORD)\nTrip window: July 4-12, 2026\n2 travelers, scenic rail trip to Zermatt and St. Moritz\nBudget: $15,200 total\nDay 1: ORD -> ZRH via Frankfurt (45m layover at FRA Concourse Z to A), train to Zermatt, check in The Omnia\nDay 4: Gornergrat railway + Matterhorn Glacier Paradise + 5-Seenweg hike + Zermatt village in one day\nDay 5: Glacier Express 8-hour panoramic train to St. Moritz, check in Badrutt\'s Palace',
    findings: [
      {
        sev: 'Critical',
        label: '45-minute Frankfurt (FRA Z → A) transfer requires Schengen passport control',
        body: 'Entering the Schengen zone at FRA Concourse Z to A requires border control + tunnel walk. Minimum safe connection is 85 minutes.',
      },
      {
        sev: 'Warning',
        label: 'Day 4 combines two 3,000m+ cableways (Gornergrat + Glacier Paradise) plus 5-Seenweg hike',
        body: 'Rapid altitude gain to 3,883m plus 11km alpine trail on the same day creates altitude fatigue and misses last valley cable car.',
      },
      {
        sev: 'Warning',
        label: 'Glacier Express Excellence Class requires 90-day advance seat allocation',
        body: 'Swiss Travel Pass covers base fare, but mandatory panoramic window seat reservations sell out months ahead.',
      },
      {
        sev: 'Info',
        label: 'SBB Door-to-Door luggage transfer eliminates carrying bags across 3 rail changes',
        body: 'Send heavy trunks directly from Zurich Airport to Zermatt & St. Moritz hotels so rail transfers stay hands-free.',
      },
    ],
    dossierRows: [
      { label: 'Duration', value: '8 days · 4 rail/air legs · 2 alpine palaces' },
      { label: 'Travelers', value: '2 adults · panoramic rail & hiking' },
      { label: 'Hub Risk', value: 'FRA 45m Schengen border transfer (40m deficit)' },
      { label: 'VIP Value', value: '+$1,050 Badrutt’s Palace & Omnia perks' },
    ],
    stops: [
      { id: '1', code: 'ORD', city: 'Chicago', country: 'USA', highlight: 'Origin departure' },
      { id: '2', code: 'FRA', city: 'Frankfurt', country: 'Germany', highlight: '45m Schengen border hub' },
      { id: '3', code: 'ZRH', city: 'Zermatt (via ZRH)', country: 'Switzerland', stayDays: 4, highlight: 'The Omnia Zermatt' },
      { id: '4', code: 'SMV', city: 'St. Moritz', country: 'Switzerland', stayDays: 3, highlight: "Badrutt's Palace" },
    ],
    legs: [
      { fromId: '1', toId: '2', mode: 'flight', durationText: '8h 15m', notes: 'Overnight LH431 ORD → FRA Concourse Z', status: 'verified' },
      { fromId: '2', toId: '3', mode: 'flight', durationText: '55m flight + 3h rail', notes: 'FRA → ZRH — Critical 45m Schengen passport queue', status: 'warning' },
      { fromId: '3', toId: '4', mode: 'train', durationText: '7h 45m', notes: 'Glacier Express Panoramic Train across Oberalp Pass & Landwasser Viaduct', status: 'optimized' },
    ],
    globeWaypoints: [
      { id: '1', code: 'ORD', city: 'Chicago', lat: 41.9742, lng: -87.9073, isOrigin: true },
      { id: '2', code: 'FRA', city: 'Frankfurt', lat: 50.0379, lng: 8.5622 },
      { id: '3', code: 'ZRH', city: 'Zermatt / Zurich', lat: 46.0207, lng: 7.7491 },
      { id: '4', code: 'SMV', city: 'St. Moritz', lat: 46.4908, lng: 9.8355 },
    ],
    activeLegTitle: 'ORD → FRA → ZRH → ST. MORITZ',
    layoverSegment: {
      inboundFlight: 'LH 431 (ORD → FRA)',
      connectingFlight: 'LH 1186 (FRA → ZRH)',
      transitHub: 'Frankfurt Airport (FRA Concourse Z → A)',
      scheduledMinutes: 45,
      minimumSafeMinutes: 85,
      terminalFrom: 'Concourse Z (Non-Schengen)',
      terminalTo: 'Concourse A (Schengen)',
    },
    pacingDays: [
      {
        dayNumber: 1,
        label: 'Zurich to Car-Free Zermatt',
        activitiesCount: 2,
        estimatedSteps: 7800,
        standingHours: 3.2,
        exhaustionScore: 54,
        notes: 'ZRH rail station platform transfer via Visp to Zermatt rock-tunnel elevator at The Omnia.',
      },
      {
        dayNumber: 2,
        label: 'Gornergrat Ridge Panorama',
        activitiesCount: 3,
        estimatedSteps: 11500,
        standingHours: 4.5,
        exhaustionScore: 62,
        notes: 'Cogwheel railway to 3,089m, Riffelsee Matterhorn reflection walk, fondue lunch at Chez Vrony.',
      },
      {
        dayNumber: 3,
        label: 'Alpine Spa & Sunnegga',
        activitiesCount: 2,
        estimatedSteps: 8900,
        standingHours: 3.5,
        exhaustionScore: 45,
        notes: 'Relaxed gourmet valley walk and indoor/outdoor heated pool overlooking the Matterhorn.',
      },
      {
        dayNumber: 4,
        label: 'Dual 3,883m Peak + 5-Lakes Overload',
        activitiesCount: 5,
        estimatedSteps: 23400,
        standingHours: 9.2,
        exhaustionScore: 93,
        notes: 'Gornergrat + Matterhorn Glacier Paradise (3,883m) + full 5-Seenweg hike in one day. High-altitude fatigue risk!',
      },
      {
        dayNumber: 5,
        label: 'Glacier Express to St. Moritz',
        activitiesCount: 2,
        estimatedSteps: 5400,
        standingHours: 2.0,
        exhaustionScore: 41,
        notes: 'Seated 5-course Excellence Class panoramic journey across 291 bridges to Badrutt’s Palace.',
      },
    ],
    hasElderlyOrKids: false,
    sanctuaryHotel: {
      hotelName: "Badrutt's Palace Hotel",
      city: 'Via Serlas, St. Moritz',
      consortiaProgram: 'Virtuoso & Leading Hotels Leaders Club',
      roomRatePublic: 1580,
      otaRoom: {
        category: 'Superior Single/Double (Village Side)',
        areaSqm: 35,
        view: 'Rear Village Street',
        breakfastCost: 98,
        credits: 0,
        cancellation: 'Strict 14-day alpine policy',
        upgradeEligible: false,
      },
      waypointSuite: {
        category: 'Deluxe Lake & Engadin Mountain Suite',
        areaSqm: 70,
        view: 'Lake St. Moritz & Engadin Peaks',
        breakfastCost: 0,
        credits: 120,
        cancellation: 'Flexible advisory terms + Rolls-Royce station transfer',
        upgradeEligible: true,
        amenitiesValue: 680,
      },
    },
    luxuryProperties: [
      {
        hotelName: "Badrutt's Palace Hotel",
        city: 'St. Moritz, Switzerland',
        nights: 3,
        partnershipDesk: 'Virtuoso & Leading Hotels Leaders Club',
        estimatedTotalValue: 680,
        perks: [
          { icon: '🥐', label: 'Daily Le Grand Hall Harp Breakfast', estimatedValue: 260, description: 'Full champagne & alpine buffet breakfast daily' },
          { icon: '💳', label: 'Palace Wellness & Dining Credit', estimatedValue: 120, description: '120 CHF credit for Matsuhisa or Palace Spa' },
          { icon: '⬆️', label: 'Lake St. Moritz View Upgrade', estimatedValue: 220, description: 'Priority upgrade to Lake View category + butler service' },
          { icon: '🚘', label: 'Rolls-Royce Rail Station Transfer', estimatedValue: 80, description: 'Complimentary chauffeur pickup from St. Moritz station' },
        ],
      },
      {
        hotelName: 'The Omnia Mountain Lodge',
        city: 'Zermatt, Switzerland',
        nights: 4,
        partnershipDesk: 'Virtuoso & Swiss Deluxe Hotels Desk',
        estimatedTotalValue: 370,
        perks: [
          { icon: '🥐', label: 'Daily Alpine Artisanal Breakfast', estimatedValue: 190, description: 'Complimentary breakfast overlooking Matterhorn valley' },
          { icon: '💳', label: 'Michelin-Starred Dining Credit', estimatedValue: 100, description: '100 CHF food & beverage credit' },
          { icon: 'car', label: 'Private Electric Taxi & Cavern Lift', estimatedValue: 80, description: 'Private electric vehicle meet at Zermatt station' },
        ],
      },
    ],
    comparisonItems: [
      {
        dimension: 'Schengen Border Hub & Swiss Rail Sync',
        before: {
          title: '45-minute FRA Concourse Z → A passport sprint',
          description: 'Transatlantic arrival into Frankfurt requires Schengen border queue before ZRH feeder flight.',
          riskBadge: '71% Border Delay Risk',
        },
        after: {
          title: 'Direct ORD → ZRH Swiss International nonstop',
          description: 'Lands directly at Zurich Airport with basement rail station escalator straight to Visp/Zermatt.',
          advantageBadge: 'Direct Rail-Air Sync',
        },
      },
      {
        dimension: 'Glacier Express & Luggage Logistics',
        before: {
          title: 'Hauling 4 suitcases across 3 mountain train changes',
          description: 'Standard 2nd class seat without panoramic reservation; manual bag lifting at Brig and Visp.',
          riskBadge: 'Platform Stress',
        },
        after: {
          title: 'Excellence Class Window + SBB Door-to-Door Luggage',
          description: 'Guaranteed single-row panoramic seat with 5-course wine pairing; bags delivered room-to-room.',
          advantageBadge: 'Hands-Free Luxury Rail',
        },
      },
      {
        dimension: "Badrutt's Palace & The Omnia Privileges",
        before: {
          title: 'Standard OTA village-side room allocation',
          description: 'Faces rear street instead of Lake St. Moritz / Matterhorn and excludes $98/day breakfast.',
          riskBadge: '$1,050 Left Unclaimed',
        },
        after: {
          title: 'Virtuoso & Leading Hotels Preferred Desk',
          description: 'Lake/Matterhorn view upgrade priority, daily breakfast, Rolls-Royce station pickup, and $220 credits.',
          advantageBadge: '+$1,050 Unlocked',
        },
      },
    ],
  },
};

export const WEDGE_SCENARIO_LIST: WedgeScenarioBundle[] = [
  WEDGE_SCENARIO_CATALOG.tokyo_kyoto,
  WEDGE_SCENARIO_CATALOG.amalfi_rome,
  WEDGE_SCENARIO_CATALOG.dubai_desert,
  WEDGE_SCENARIO_CATALOG.singapore_family,
  WEDGE_SCENARIO_CATALOG.swiss_alps,
];

interface CityGeoProfile {
  code: string;
  city: string;
  country: string;
  lat: number;
  lng: number;
  defaultHubCode: string;
  defaultHubCity: string;
  defaultHubLat: number;
  defaultHubLng: number;
  defaultHotel: string;
  defaultConsortia: string;
  defaultRate: number;
  defaultHighlight: string;
}

const CITY_GEO_DIRECTORY: Record<string, CityGeoProfile> = {
  tokyo: {
    code: 'NRT',
    city: 'Tokyo',
    country: 'Japan',
    lat: 35.772,
    lng: 140.3929,
    defaultHubCode: 'LAX',
    defaultHubCity: 'Los Angeles',
    defaultHubLat: 33.9416,
    defaultHubLng: -118.4085,
    defaultHotel: 'Aman Tokyo',
    defaultConsortia: 'Virtuoso & Aman Preferred Desk',
    defaultRate: 1850,
    defaultHighlight: 'Otemachi & Imperial Gardens',
  },
  kyoto: {
    code: 'KYO',
    city: 'Kyoto',
    country: 'Japan',
    lat: 35.0116,
    lng: 135.7681,
    defaultHubCode: 'NRT',
    defaultHubCity: 'Tokyo',
    defaultHubLat: 35.772,
    defaultHubLng: 140.3929,
    defaultHotel: 'The Ritz-Carlton Kyoto',
    defaultConsortia: 'Marriott STARS & Virtuoso',
    defaultRate: 1420,
    defaultHighlight: 'Kamogawa River & Gion',
  },
  dubai: {
    code: 'DXB',
    city: 'Dubai',
    country: 'UAE',
    lat: 25.2532,
    lng: 55.3657,
    defaultHubCode: 'IST',
    defaultHubCity: 'Istanbul',
    defaultHubLat: 41.2753,
    defaultHubLng: 28.7519,
    defaultHotel: 'Atlantis The Royal',
    defaultConsortia: 'Virtuoso Ultraluxe Desk',
    defaultRate: 1280,
    defaultHighlight: 'Palm Jumeirah & Desert Reserve',
  },
  singapore: {
    code: 'SIN',
    city: 'Singapore',
    country: 'Singapore',
    lat: 1.3644,
    lng: 103.9915,
    defaultHubCode: 'TPE',
    defaultHubCity: 'Taipei',
    defaultHubLat: 25.0797,
    defaultHubLng: 121.2342,
    defaultHotel: 'Raffles Singapore',
    defaultConsortia: 'Virtuoso & Accor HERA',
    defaultRate: 1390,
    defaultHighlight: 'Marina Bay & Sentosa',
  },
  sentosa: {
    code: 'SEN',
    city: 'Sentosa',
    country: 'Singapore',
    lat: 1.2494,
    lng: 103.8303,
    defaultHubCode: 'SIN',
    defaultHubCity: 'Singapore Changi',
    defaultHubLat: 1.3644,
    defaultHubLng: 103.9915,
    defaultHotel: 'Capella Singapore',
    defaultConsortia: 'Virtuoso & Leading Hotels',
    defaultRate: 1180,
    defaultHighlight: 'Capella Manor & Palawan Beach',
  },
  paris: {
    code: 'CDG',
    city: 'Paris',
    country: 'France',
    lat: 49.0097,
    lng: 2.5479,
    defaultHubCode: 'LHR',
    defaultHubCity: 'London',
    defaultHubLat: 51.47,
    defaultHubLng: -0.4543,
    defaultHotel: 'The Ritz Paris',
    defaultConsortia: 'Virtuoso & Leading Hotels Leaders Club',
    defaultRate: 1650,
    defaultHighlight: 'Place Vendôme & Louvre',
  },
  rome: {
    code: 'FCO',
    city: 'Rome',
    country: 'Italy',
    lat: 41.8003,
    lng: 12.2389,
    defaultHubCode: 'LHR',
    defaultHubCity: 'London',
    defaultHubLat: 51.47,
    defaultHubLng: -0.4543,
    defaultHotel: 'Hotel de Russie',
    defaultConsortia: 'Rocco Forte Knights & Virtuoso',
    defaultRate: 1540,
    defaultHighlight: 'Piazza del Popolo & Vatican',
  },
  amalfi: {
    code: 'NAP',
    city: 'Amalfi Coast',
    country: 'Italy',
    lat: 40.6333,
    lng: 14.6029,
    defaultHubCode: 'FCO',
    defaultHubCity: 'Rome',
    defaultHubLat: 41.8003,
    defaultHubLng: 12.2389,
    defaultHotel: 'Belmond Hotel Caruso',
    defaultConsortia: 'Belmond Bellini Club',
    defaultRate: 1720,
    defaultHighlight: 'Ravello Cliffside Sanctuary',
  },
  london: {
    code: 'LHR',
    city: 'London',
    country: 'UK',
    lat: 51.47,
    lng: -0.4543,
    defaultHubCode: 'JFK',
    defaultHubCity: 'New York',
    defaultHubLat: 40.6413,
    defaultHubLng: -73.7781,
    defaultHotel: 'The Connaught',
    defaultConsortia: 'Virtuoso Maybourne Preferred',
    defaultRate: 1480,
    defaultHighlight: 'Mayfair & Hyde Park',
  },
  zermatt: {
    code: 'ZRH',
    city: 'Zermatt',
    country: 'Switzerland',
    lat: 46.0207,
    lng: 7.7491,
    defaultHubCode: 'FRA',
    defaultHubCity: 'Frankfurt',
    defaultHubLat: 50.0379,
    defaultHubLng: 8.5622,
    defaultHotel: 'The Omnia Zermatt',
    defaultConsortia: 'Virtuoso & Swiss Deluxe Hotels',
    defaultRate: 1350,
    defaultHighlight: 'Matterhorn Ridge & Glacier Express',
  },
  bali: {
    code: 'DPS',
    city: 'Bali (Ubud & Uluwatu)',
    country: 'Indonesia',
    lat: -8.7482,
    lng: 115.1672,
    defaultHubCode: 'SIN',
    defaultHubCity: 'Singapore',
    defaultHubLat: 1.3644,
    defaultHubLng: 103.9915,
    defaultHotel: 'Mandapa, a Ritz-Carlton Reserve',
    defaultConsortia: 'Marriott STARS & Virtuoso',
    defaultRate: 1320,
    defaultHighlight: 'Ayung River Valley Sanctuary',
  },
  maldives: {
    code: 'MLE',
    city: 'Maldives (Baa Atoll)',
    country: 'Maldives',
    lat: 4.1918,
    lng: 73.5291,
    defaultHubCode: 'DOH',
    defaultHubCity: 'Doha',
    defaultHubLat: 25.2731,
    defaultHubLng: 51.6081,
    defaultHotel: 'Soneva Fushi',
    defaultConsortia: 'Virtuoso Ultraluxe Seaplane Desk',
    defaultRate: 2150,
    defaultHighlight: 'Overwater Reserve & Seaplane Transfer',
  },
  hong_kong: {
    code: 'HKG',
    city: 'Hong Kong',
    country: 'Hong Kong',
    lat: 22.308,
    lng: 113.9185,
    defaultHubCode: 'TPE',
    defaultHubCity: 'Taipei',
    defaultHubLat: 25.0797,
    defaultHubLng: 121.2342,
    defaultHotel: 'Rosewood Hong Kong',
    defaultConsortia: 'Rosewood Elite & Virtuoso',
    defaultRate: 1190,
    defaultHighlight: 'Victoria Harbour & Peak Tram',
  },
};

const ORIGIN_GEO_DIRECTORY: Record<string, { code: string; city: string; lat: number; lng: number }> = {
  sfo: { code: 'SFO', city: 'San Francisco', lat: 37.6213, lng: -122.379 },
  'san francisco': { code: 'SFO', city: 'San Francisco', lat: 37.6213, lng: -122.379 },
  lax: { code: 'LAX', city: 'Los Angeles', lat: 33.9416, lng: -118.4085 },
  'los angeles': { code: 'LAX', city: 'Los Angeles', lat: 33.9416, lng: -118.4085 },
  jfk: { code: 'JFK', city: 'New York', lat: 40.6413, lng: -73.7781 },
  'new york': { code: 'JFK', city: 'New York', lat: 40.6413, lng: -73.7781 },
  nyc: { code: 'JFK', city: 'New York', lat: 40.6413, lng: -73.7781 },
  ord: { code: 'ORD', city: 'Chicago', lat: 41.9742, lng: -87.9073 },
  chicago: { code: 'ORD', city: 'Chicago', lat: 41.9742, lng: -87.9073 },
  lhr: { code: 'LHR', city: 'London', lat: 51.47, lng: -0.4543 },
  london: { code: 'LHR', city: 'London', lat: 51.47, lng: -0.4543 },
  bos: { code: 'BOS', city: 'Boston', lat: 42.3656, lng: -71.0096 },
  boston: { code: 'BOS', city: 'Boston', lat: 42.3656, lng: -71.0096 },
  mia: { code: 'MIA', city: 'Miami', lat: 25.7959, lng: -80.287 },
  miami: { code: 'MIA', city: 'Miami', lat: 25.7959, lng: -80.287 },
  sea: { code: 'SEA', city: 'Seattle', lat: 47.4502, lng: -122.3088 },
  seattle: { code: 'SEA', city: 'Seattle', lat: 47.4502, lng: -122.3088 },
  yyz: { code: 'YYZ', city: 'Toronto', lat: 43.6777, lng: -79.6248 },
  toronto: { code: 'YYZ', city: 'Toronto', lat: 43.6777, lng: -79.6248 },
  syd: { code: 'SYD', city: 'Sydney', lat: -33.9399, lng: 151.1753 },
  sydney: { code: 'SYD', city: 'Sydney', lat: -33.9399, lng: 151.1753 },
  sin: { code: 'SIN', city: 'Singapore', lat: 1.3644, lng: 103.9915 },
  dxb: { code: 'DXB', city: 'Dubai', lat: 25.2532, lng: 55.3657 },
};

export function resolveDynamicWedgeScenario(
  analysis?: RunStatusResponse | null,
  rawPlanText?: string | null,
  scenarioKey?: WedgeScenarioKey | null,
): WedgeScenarioBundle {
  // 1. If a specific scenarioKey is requested and there is no live analysis overriding it, return catalog preset
  if (scenarioKey && !analysis && !rawPlanText) {
    return WEDGE_SCENARIO_CATALOG[scenarioKey] ?? WEDGE_SCENARIO_CATALOG.tokyo_kyoto;
  }

  const packet = (analysis?.packet as Record<string, any> | null | undefined) ?? null;
  const facts = packet?.facts as Record<string, any> | undefined;
  const liveChecks = packet?.public_checker_live_checks as Record<string, any> | undefined;

  const combinedText = [
    rawPlanText ?? '',
    typeof liveChecks?.destination === 'string' ? liveChecks.destination : '',
    Array.isArray(facts?.destination_candidates?.value) ? facts.destination_candidates.value.join(' ') : '',
    typeof facts?.destination?.value === 'string' ? facts.destination.value : '',
    typeof facts?.origin_city?.value === 'string' ? facts.origin_city.value : '',
  ]
    .join(' ')
    .toLowerCase();

  // Check if combined text matches one of our 5 high-precision catalog scenarios first,
  // and then overlay any explicit layover minutes / origin / hotel from the user's text!
  let baseScenario: WedgeScenarioBundle = WEDGE_SCENARIO_CATALOG.amalfi_rome;
  if (/tokyo|kyoto|nrt|hnd|shinkansen|osaka|inari|arashiyama|gion|nara|japan/.test(combinedText)) {
    baseScenario = WEDGE_SCENARIO_CATALOG.tokyo_kyoto;
  } else if (/dubai|dxb|al maha|abu dhabi|atlantis|burj|uae|emirates/.test(combinedText)) {
    baseScenario = WEDGE_SCENARIO_CATALOG.dubai_desert;
  } else if (/singapore|sentosa|changi|marina bay|mandai|universal studios/.test(combinedText)) {
    baseScenario = WEDGE_SCENARIO_CATALOG.singapore_family;
  } else if (/zermatt|st\.?\s*moritz|glacier express|zurich|zrh|swiss|switzerland|matterhorn|omnia|badrutt/.test(combinedText)) {
    baseScenario = WEDGE_SCENARIO_CATALOG.swiss_alps;
  } else if (/rome|amalfi|positano|ravello|paris|london|lhr|cdg|fco|vatican|colosseum|connaught|russie|caruso/.test(combinedText)) {
    baseScenario = WEDGE_SCENARIO_CATALOG.amalfi_rome;
  } else if (scenarioKey && WEDGE_SCENARIO_CATALOG[scenarioKey]) {
    baseScenario = WEDGE_SCENARIO_CATALOG[scenarioKey];
  }

  // If no custom analysis or raw text was provided, return the baseScenario directly
  if (!analysis && !rawPlanText) {
    return baseScenario;
  }

  // Dynamic overrides from user's raw text + extracted facts
  const layoverMinutesMatch = (rawPlanText ?? '').match(/(\d{2,3})\s*(?:m|min|minute|minutes)\s+layover(?:\s+(?:at|in)\s+([A-Za-z ]+(?:\([A-Za-z]{3}\))?))?/i);
  const parsedLayoverMins = layoverMinutesMatch ? Number(layoverMinutesMatch[1]) : null;
  const parsedLayoverHubRaw = layoverMinutesMatch?.[2]?.trim();

  // Origin resolution
  const rawOriginFact =
    typeof facts?.origin_city?.value === 'string'
      ? facts.origin_city.value
      : (rawPlanText ?? '').match(/origin(?:\s+city)?\s*[:\-]\s*([^\n\r|,]+)/i)?.[1]?.trim() ?? null;

  let resolvedOrigin = baseScenario.globeWaypoints[0];
  if (rawOriginFact) {
    const lowerOrigin = rawOriginFact.toLowerCase();
    const matchedOriginKey = Object.keys(ORIGIN_GEO_DIRECTORY).find((k) => lowerOrigin.includes(k));
    if (matchedOriginKey) {
      const geo = ORIGIN_GEO_DIRECTORY[matchedOriginKey];
      resolvedOrigin = { id: '1', code: geo.code, city: geo.city, lat: geo.lat, lng: geo.lng, isOrigin: true };
    } else {
      const codeMatch = rawOriginFact.match(/\b([A-Z]{3})\b/);
      const cleanCity = rawOriginFact.replace(/\([A-Z]{3}\)/g, '').trim();
      resolvedOrigin = {
        id: '1',
        code: codeMatch ? codeMatch[1] : cleanCity.slice(0, 3).toUpperCase(),
        city: cleanCity || rawOriginFact,
        lat: baseScenario.globeWaypoints[0].lat,
        lng: baseScenario.globeWaypoints[0].lng,
        isOrigin: true,
      };
    }
  }

  // Destination resolution for non-catalog cities (e.g. Bali, Maldives, Hong Kong, Paris)
  const matchedDestKeys = Object.keys(CITY_GEO_DIRECTORY).filter((k) =>
    combinedText.includes(k.replace('_', ' ')),
  );

  let stops = [...baseScenario.stops];
  let legs = [...baseScenario.legs];
  let globeWaypoints = [...baseScenario.globeWaypoints];
  let activeLegTitle = baseScenario.activeLegTitle;
  let layoverSegment = { ...baseScenario.layoverSegment };
  let sanctuaryHotel = { ...baseScenario.sanctuaryHotel };
  let luxuryProperties = [...baseScenario.luxuryProperties];

  // Update Origin in stops and globeWaypoints
  stops[0] = {
    ...stops[0],
    code: resolvedOrigin.code,
    city: resolvedOrigin.city,
  };
  globeWaypoints[0] = resolvedOrigin;

  // If custom destination from CITY_GEO_DIRECTORY not already covered by baseScenario's primary city
  if (matchedDestKeys.length > 0 && !combinedText.includes(baseScenario.stops[2]?.city.toLowerCase() ?? '')) {
    const primaryGeo = CITY_GEO_DIRECTORY[matchedDestKeys[0]];
    const secondaryGeo = matchedDestKeys[1] ? CITY_GEO_DIRECTORY[matchedDestKeys[1]] : null;

    stops = [
      { id: '1', code: resolvedOrigin.code, city: resolvedOrigin.city, country: 'Origin', highlight: 'Departure origin' },
      { id: '2', code: primaryGeo.defaultHubCode, city: primaryGeo.defaultHubCity, country: 'Transit Hub', highlight: `${parsedLayoverMins ?? 50}m tight transfer hub` },
      { id: '3', code: primaryGeo.code, city: primaryGeo.city, country: primaryGeo.country, stayDays: 4, highlight: primaryGeo.defaultHotel },
    ];
    if (secondaryGeo) {
      stops.push({
        id: '4',
        code: secondaryGeo.code,
        city: secondaryGeo.city,
        country: secondaryGeo.country,
        stayDays: 3,
        highlight: secondaryGeo.defaultHotel,
      });
    }

    globeWaypoints = [
      resolvedOrigin,
      { id: '2', code: primaryGeo.defaultHubCode, city: primaryGeo.defaultHubCity, lat: primaryGeo.defaultHubLat, lng: primaryGeo.defaultHubLng },
      { id: '3', code: primaryGeo.code, city: primaryGeo.city, lat: primaryGeo.lat, lng: primaryGeo.lng },
    ];
    if (secondaryGeo) {
      globeWaypoints.push({ id: '4', code: secondaryGeo.code, city: secondaryGeo.city, lat: secondaryGeo.lat, lng: secondaryGeo.lng });
    }

    legs = stops.slice(0, -1).map((from, idx) => {
      const to = stops[idx + 1];
      const isHub = idx === 1;
      return {
        fromId: from.id,
        toId: to.id,
        mode: idx >= 2 ? 'train' : 'flight',
        durationText: idx === 0 ? '7h 40m' : idx === 1 ? '4h 15m' : '2h 10m',
        notes: isHub
          ? `Connecting flight ${from.code} → ${to.code} with tight ${parsedLayoverMins ?? 50}m buffer`
          : `Scheduled leg ${from.city} → ${to.city}`,
        status: isHub ? 'warning' : idx === 0 ? 'verified' : 'optimized',
      };
    });

    sanctuaryHotel = {
      ...sanctuaryHotel,
      hotelName: primaryGeo.defaultHotel,
      city: `${primaryGeo.city}, ${primaryGeo.country}`,
      consortiaProgram: primaryGeo.defaultConsortia,
      roomRatePublic: primaryGeo.defaultRate,
    };
  }

  // Apply explicit layover minutes & hub if present in user text
  if (parsedLayoverMins !== null) {
    layoverSegment.scheduledMinutes = parsedLayoverMins;
  }
  if (parsedLayoverHubRaw) {
    const hubRaw = parsedLayoverHubRaw.replace(/[()]/g, ' ').replace(/\s+/g, ' ').trim();
    const bareCode = /^[A-Za-z]{3}$/.test(hubRaw);
    const embeddedCode = parsedLayoverHubRaw.match(/\(([A-Za-z]{3})\)/)?.[1];
    const hubCode = (bareCode ? hubRaw : embeddedCode ?? stops[1]?.code ?? 'HUB').toUpperCase();
    const cleanCity = hubRaw.replace(new RegExp(`\\b${hubCode}\\b`, 'i'), '').replace(/\s+/g, ' ').trim();
    stops[1] = {
      ...stops[1],
      code: hubCode,
      city: cleanCity || stops[1].city,
      highlight: `${layoverSegment.scheduledMinutes}m tight transit hub`,
    };
    layoverSegment.transitHub = `${stops[1].city} (${hubCode})`;
  }

  layoverSegment.inboundFlight = `${stops[0]?.code ?? 'ORIG'} → ${stops[1]?.code ?? 'HUB'}`;
  layoverSegment.connectingFlight = `${stops[1]?.code ?? 'HUB'} → ${stops[2]?.code ?? 'DEST'}`;
  activeLegTitle = stops.map((s) => s.code).join(' → ');

  // Entity checks from live packet for luxury properties
  const entityChecks = packet?.public_checker_entity_checks as Array<Record<string, any>> | undefined;
  if (Array.isArray(entityChecks) && entityChecks.length > 0) {
    const dynamicProps: LuxuryPropertyPerk[] = entityChecks.slice(0, 3).map((item, idx) => {
      const cleanName = String(item.name || 'Preferred Partner Hotel').replace(/\bfor$/i, '').trim();
      const targetCity = stops[Math.min(stops.length - 1, idx + 2)]?.city ?? stops[2]?.city ?? 'Destination';
      return {
        hotelName: cleanName,
        city: targetCity,
        nights: 3,
        partnershipDesk: 'Virtuoso & Preferred Partner Direct Desk',
        estimatedTotalValue: 640,
        perks: [
          { icon: '🥐', label: 'Daily Full Breakfast for Two', estimatedValue: 260, description: `Complimentary daily breakfast at ${cleanName}` },
          { icon: '💳', label: 'Property Dining & Spa Credit', estimatedValue: 100, description: '100 USD equivalent resort folio credit' },
          { icon: '⬆️', label: 'Priority Room Category Upgrade', estimatedValue: 230, description: 'Confirmed or priority upgrade upon check-in' },
          { icon: '⏰', label: 'Early Check-in & 4:00 PM Late Checkout', estimatedValue: 50, description: 'Flexible arrival and departure handling' },
        ],
      };
    });
    if (dynamicProps.length > 0) {
      luxuryProperties = dynamicProps;
      sanctuaryHotel = {
        ...sanctuaryHotel,
        hotelName: dynamicProps[0].hotelName,
        city: dynamicProps[0].city,
      };
    }
  }

  // Check party composition for elderly or kids
  const composition = facts?.party_composition?.value;
  const hasElderlyOrKids =
    (composition && typeof composition === 'object' && Boolean(composition.elderly || composition.children || composition.infant)) ||
    /elder|grandparent|toddler|child|kid|infant|family of [4-9]/i.test(combinedText) ||
    baseScenario.hasElderlyOrKids;

  return {
    ...baseScenario,
    stops,
    legs,
    globeWaypoints,
    activeLegTitle,
    layoverSegment,
    hasElderlyOrKids,
    sanctuaryHotel,
    luxuryProperties,
  };
}

interface WedgeVisualShowcaseProps {
  analysis?: RunStatusResponse | null;
  rawPlanText?: string | null;
  scenarioKey?: WedgeScenarioKey | null;
  onAdvisorHelp?: () => void;
}

type TabType = 'stress' | 'isoAirport' | 'globe3d' | 'route' | 'pacing' | 'isoHotel' | 'comparison' | 'perks';

const SHOWCASE_TABS: {
  key: TabType;
  icon: LucideIcon;
  label: string;
  sublabel: string;
  accent: string;
  bgActive: string;
}[] = [
  {
    key: 'stress',
    icon: Clock,
    label: 'Connection Stress',
    sublabel: 'Hub buffer & delay check',
    accent: '#f85149',
    bgActive: 'rgba(248,81,73,0.12)',
  },
  {
    key: 'isoAirport',
    icon: Building2,
    label: 'Terminal Transfer',
    sublabel: 'Gate & baggage transit path',
    accent: '#38bdf8',
    bgActive: 'rgba(56,189,248,0.14)',
  },
  {
    key: 'globe3d',
    icon: Globe,
    label: '3D Route Arc',
    sublabel: 'Multi-leg flight trajectory',
    accent: '#60a5fa',
    bgActive: 'rgba(96,165,250,0.14)',
  },
  {
    key: 'route',
    icon: Route,
    label: 'Stop Sequence',
    sublabel: 'Air & rail leg breakdown',
    accent: '#39d0d8',
    bgActive: 'rgba(57,208,216,0.12)',
  },
  {
    key: 'pacing',
    icon: Activity,
    label: 'Daily Pacing',
    sublabel: 'Step load & recovery margin',
    accent: '#d29922',
    bgActive: 'rgba(210,153,34,0.12)',
  },
  {
    key: 'isoHotel',
    icon: BedDouble,
    label: 'Room vs. Partner Tier',
    sublabel: 'OTA allocation vs. direct desk',
    accent: '#34d399',
    bgActive: 'rgba(52,211,153,0.14)',
  },
  {
    key: 'comparison',
    icon: Scale,
    label: 'Before vs. After',
    sublabel: 'Self-planned vs. advisor-backed',
    accent: '#58a6ff',
    bgActive: 'rgba(88,166,255,0.12)',
  },
  {
    key: 'perks',
    icon: Sparkles,
    label: 'Hotel Perks Check',
    sublabel: 'Rate-parity credits & breakfast',
    accent: '#3fb950',
    bgActive: 'rgba(63,185,80,0.12)',
  },
];

export function WedgeVisualShowcase({
  analysis,
  rawPlanText,
  scenarioKey,
  onAdvisorHelp,
}: WedgeVisualShowcaseProps) {
  const [activeTab, setActiveTab] = useState<TabType>('stress');
  const showcaseId = useId();
  const panelId = `${showcaseId}-panel`;

  const resolved = useMemo(
    () => resolveDynamicWedgeScenario(analysis, rawPlanText, scenarioKey),
    [analysis, rawPlanText, scenarioKey],
  );

  return (
    <div style={{ marginTop: 24, marginBottom: 28 }}>
      {analysis ? (
        <div
          style={{
            marginBottom: 12,
            padding: '10px 14px',
            borderRadius: 10,
            background: '#0d1117',
            border: '1px solid #21262d',
            fontSize: 12,
            color: '#8b949e',
            lineHeight: 1.5,
          }}
        >
          Route and hub nodes reflect your submitted itinerary; terminal transit times, pacing load curves, and
          hotel perk figures are illustrative partner benchmarks unless explicitly listed in your findings above.
        </div>
      ) : null}
      {/* Visual Navigation Grid — all 8 modules visible without horizontal clipping */}
      <div
        role="tablist"
        aria-label="Interactive travel diagnostic views"
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(185px, 1fr))',
          gap: 8,
          background: '#0d1117',
          padding: 8,
          borderRadius: 16,
          border: '1px solid #21262d',
          marginBottom: 16,
        }}
      >
        {SHOWCASE_TABS.map((tab, index) => {
          const isActive = activeTab === tab.key;
          const Icon = tab.icon;
          return (
            <button
              key={tab.key}
              type="button"
              {...tabProps(`${showcaseId}-${tab.key}`, isActive, panelId)}
              onClick={() => setActiveTab(tab.key)}
              onKeyDown={(event) => {
                const next = handleListNavigation(event, index, SHOWCASE_TABS.length);
                if (next === null) return;
                const nextTab = SHOWCASE_TABS[next].key;
                setActiveTab(nextTab);
                event.currentTarget.ownerDocument.getElementById(`${showcaseId}-${nextTab}`)?.focus();
              }}
              style={{
                padding: '10px 12px',
                borderRadius: 10,
                border: isActive ? `1px solid ${tab.accent}` : '1px solid rgba(48,54,61,0.55)',
                background: isActive ? tab.bgActive : 'rgba(22,27,34,0.45)',
                color: isActive ? '#f0f6fc' : '#8b949e',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                textAlign: 'left',
                transition: 'all 0.15s ease',
              }}
            >
              <span style={{
                width: 28,
                height: 28,
                borderRadius: 8,
                background: isActive ? `${tab.accent}22` : 'rgba(255,255,255,0.03)',
                border: `1px solid ${isActive ? `${tab.accent}44` : 'rgba(48,54,61,0.6)'}`,
                color: isActive ? tab.accent : '#8b949e',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
              }}>
                <Icon size={14} strokeWidth={1.9} />
              </span>
              <div style={{ minWidth: 0 }}>
                <div
                  style={{
                    fontSize: 12,
                    fontWeight: 700,
                    color: isActive ? tab.accent : '#e6edf3',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                  }}
                >
                  {tab.label}
                </div>
                <div
                  style={{
                    fontSize: 10.5,
                    color: '#6e7681',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    marginTop: 1,
                  }}
                >
                  {tab.sublabel}
                </div>
              </div>
            </button>
          );
        })}
      </div>

      {/* Render Active Visual Moment with locked minHeight to prevent tab-switch CLS */}
      <div {...tabPanelProps(panelId, `${showcaseId}-${activeTab}`)} style={{ minHeight: 780 }}>
      {activeTab === 'stress' ? (
        <LayoverStressGauge segment={resolved.layoverSegment} onAdvisorHelp={onAdvisorHelp} />
      ) : null}

      {activeTab === 'isoAirport' ? (
        <IsometricAirportCutaway
          transitHub={resolved.layoverSegment.transitHub}
          inboundFlight={resolved.layoverSegment.inboundFlight}
          connectingFlight={resolved.layoverSegment.connectingFlight}
          scheduledMinutes={resolved.layoverSegment.scheduledMinutes}
        />
      ) : null}

      {activeTab === 'globe3d' ? (
        <Interactive3DGlobeFlightArc
          waypoints={resolved.globeWaypoints}
          activeLegTitle={resolved.activeLegTitle}
        />
      ) : null}

      {activeTab === 'route' ? (
        <RouteArcRibbon stops={resolved.stops} legs={resolved.legs} />
      ) : null}

      {activeTab === 'pacing' ? (
        <PacingExhaustionCurve
          days={resolved.pacingDays}
          hasElderlyOrKids={resolved.hasElderlyOrKids}
        />
      ) : null}

      {activeTab === 'isoHotel' ? (
        <IsometricHotelSanctuary
          hotel={resolved.sanctuaryHotel}
          onClaim={onAdvisorHelp}
        />
      ) : null}

      {activeTab === 'comparison' ? (
        <BeforeAfterComparison items={resolved.comparisonItems} />
      ) : null}

      {activeTab === 'perks' ? (
        <HiddenPerksRadar
          properties={resolved.luxuryProperties}
          onClaimPerks={onAdvisorHelp}
        />
      ) : null}
      </div>
    </div>
  );
}
