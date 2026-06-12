# Seasonal Campaign Planner — Contracts & KPIs

> Contract-first implementation layer for campaign metadata, budget governance, risk control, and measurable outcomes.

## 1) Canonical data models

```ts
export type SeasonCode =
  | 'PEAK_SUMMER'
  | 'PEAK_FESTIVAL'
  | 'SHOULDER_WEDDING'
  | 'SHOULDER_PREPEAK'
  | 'OFF_MONSOON';

export type CampaignType =
  | 'EARLY_BIRD'
  | 'LAST_MINUTE'
  | 'SPOTLIGHT'
  | 'MONSOON_ESCAPE'
  | 'REFERRAL_BOOST'
  | 'FLASH_CLEARANCE';

export interface SeasonalCampaignContract {
  campaignId: string;
  seasonCode: SeasonCode;
  campaignType: CampaignType;
  objective: 'acquire' | 'convert' | 'upgrade' | 'utilize_inventory';
  geographyScope: {
    market: 'INDIA'
    | 'INTERNATIONAL_ROUTES';
    topDestinations: string[];
  };
  schedule: {
    planStartDate: string;
    launchAt: string;
    closeAt: string;
    timezone: 'Asia/Kolkata';
    decisionCadenceHours: 6 | 12 | 24;
  };
  economics: {
    targetMarginPercent: number;
    floorMarginPercent: number;
    maxDiscountPercent: number;
    targetCACRupees: number;
    maxSpendPercentOfRevenue: number;
    maxCACSpikePercent: number;
  };
  inventory: {
    maxUnits: number;
    source: 'pre_committed' | 'contingent' | 'open';
    fallbackDestinationList: string[];
    cancelationSupportLevel: 'standard' | 'priority';
  };
  segments: {
    include: string[];
    exclude?: string[];
    personalizationRules?: string[];
  };
  channels: Array<'whatsapp' | 'email' | 'instagram' | 'app' | 'website'>;
  owners: {
    ownerId: string;
    approverId: string;
    riskOwnerId: string;
  };
  rollout: {
    requiredChecksPassed: string[];
    canAutoPause: boolean;
    stopCriteria: string[];
  };
}

export interface SeasonalKPIEnvelope {
  bookingsTarget: number;
  revenueTargetRupees: number;
  marginTargetPercent: number;
  channelROASTarget: {
    whatsapp: number;
    email: number;
    instagram: number;
    app: number;
  };
  quality: {
    avgBookingConfidenceScore: number;
    trustFlags: string[];
    supportEscalationRateMaxPercent: number;
  };
  reportingWindowDays: number;
}

export interface CampaignExecutionSnapshot {
  asOf: string;
  campaignId: string;
  spendRupees: number;
  leads: number;
  booked: number;
  avgOrderValueRupees: number;
  realizedMarginPercent: number;
  unitsRemaining: number;
  riskScore: number; // 0-100
}
```

## 2) KPI definition and validation

### KPI dictionary

- **Bookings (count):** successful confirmed bookings attributed to campaign.
- **Revenue (₹):** gross booking value at campaign close.
- **Margin (%):** total gross margin percentage after channel and fulfillment adjustments.
- **CAC (₹):** campaign-specific spend per confirmed booking.
- **ROAS (per channel):** attributed revenue ÷ spend.
- **Trust score:** complaints + support escalations normalized to bookings.
- **Forecast variance:** actual vs planned bookings over window.

### Formula sheet

- `margin = (revenue - campaign_attributed_costs - campaign_attributed_operating_cost) / revenue`
- `riskScore = clamp(100 * (supportEscalations + inventoryAnomalies + policyViolations) / max(1, bookings), 0, 100)`
- `forecastVariancePercent = ((actualBookings - plannedBookings) / plannedBookings) * 100`

### Hard guards

- Do not launch if any required check fails.
- Auto-pause if:
  - margin falls below floor for two consecutive decision cycles, or
  - trust score breaches threshold, or
  - inventory anomalies remain unresolved beyond 12 hours.

## 3) Campaign object templates

### Early Bird template

```json
{
  "campaignId": "SB-2026-SUMMER-EB-01",
  "seasonCode": "PEAK_SUMMER",
  "campaignType": "EARLY_BIRD",
  "objective": "acquire",
  "economics": {
    "targetMarginPercent": 14,
    "floorMarginPercent": 10,
    "maxDiscountPercent": 15,
    "targetCACRupees": 2200,
    "maxSpendPercentOfRevenue": 12,
    "maxCACSpikePercent": 20
  },
  "inventory": {
    "maxUnits": 80,
    "source": "pre_committed",
    "fallbackDestinationList": ["Bali", "Kashmir", "Dubai"],
    "cancelationSupportLevel": "priority"
  }
}
```

### Monsoon Escape template

```json
{
  "campaignId": "SP-2026-MONSOON-01",
  "seasonCode": "OFF_MONSOON",
  "campaignType": "MONSOON_ESCAPE",
  "objective": "convert",
  "economics": {
    "targetMarginPercent": 11,
    "floorMarginPercent": 9,
    "maxDiscountPercent": 22,
    "targetCACRupees": 1600,
    "maxSpendPercentOfRevenue": 14,
    "maxCACSpikePercent": 30
  },
  "inventory": {
    "maxUnits": 120,
    "source": "open",
    "fallbackDestinationList": ["Goa", "Kerala", "Udaipur"],
    "cancelationSupportLevel": "standard"
  }
}
```

## 4) Completion standards

- [x] Canonical contracts defined.
- [x] KPI formulas standardized.
- [x] Guardrails enforced with explicit stop criteria.
- [x] Templates added for flagship archetypes.

## 5) Versioning and long-term contract hygiene

- Use versioned contract IDs for all live campaigns (`YYYY-SEAS-CODE-SEQ`).
- Never mutate historical contract payloads in place; create next revision.
- Retire obsolete campaign templates via migration notes, not silent edits.
