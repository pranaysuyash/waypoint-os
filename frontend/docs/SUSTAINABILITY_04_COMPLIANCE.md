# Sustainability & Green Travel — Compliance & Reporting

> Research document for sustainability regulatory compliance, ESG reporting, and environmental governance.

---

## Key Questions

1. **What regulatory sustainability requirements apply to travel platforms?**
2. **How do we support corporate ESG reporting for travel?**
3. **What sustainability data retention and audit requirements exist?**
4. **How do we handle carbon tax and emission trading regulations?**
5. **What industry sustainability standards must we align with?**

---

## Research Areas

### Regulatory Landscape

```typescript
interface SustainabilityRegulation {
  regulationId: string;
  name: string;
  jurisdiction: string;
  applicability: RegulationApplicability;
  requirements: RegulationRequirement[];
  complianceDeadline: Date;
  penalties: string;
}

type RegulationApplicability =
  | 'mandatory_all'                   // Applies to all businesses
  | 'mandatory_listed'                // Only listed companies
  | 'mandatory_threshold'             // Revenue/size threshold
  | 'voluntary';                      // Recommended but not required

// India sustainability regulations:
//
// 1. BRSR (Business Responsibility and Sustainability Reporting):
//    - Mandatory for top 1,000 listed companies (by market cap)
//    - SEBI requirement since FY 2022-23
//    - Covers environmental, social, and governance disclosures
//    - Includes Scope 1, 2, and 3 emissions reporting
//    - Travel emissions fall under Scope 3 for corporate clients
//    - Applicability: Our corporate clients need this data from us
//
// 2. Energy Conservation (Amendment) Act, 2022:
//    - Establishes Indian Carbon Market (ICM)
//    - Carbon Credit Trading Scheme (CCTS) framework
//    - Applies to entities consuming >5,000 TOE (tonnes of oil equivalent)
//    - Travel platforms likely below threshold initially
//    - Future: May apply as platform scales
//
// 3. National Green Tribunal (NGT) Guidelines:
//    - Environmental impact assessment for tourism projects
//    - Waste management regulations for hospitality
//    - Noise and pollution standards near eco-sensitive zones
//    - Applicability: Relevant for destination sustainability
//
// 4. GST on Carbon Offsets:
//    - Currently no specific GST rate for carbon offsets
//    - Carbon credits may be treated as "goods" or "services"
//    - Advance Ruling needed for clarity
//    - Best practice: Show offset as separate line item
//
// International regulations (for global operations):
// - EU Corporate Sustainability Reporting Directive (CSRD)
// - CORSIA (aviation carbon offset scheme)
// - UK SECR (Streamlined Energy and Carbon Reporting)
// - Singapore Carbon Pricing Act
// - California Climate Corporate Data Accountability Act

interface RegulationRequirement {
  requirement: string;
  category: 'reporting' | 'disclosure' | 'target' | 'offset' | 'tax';
  frequency: 'annual' | 'quarterly' | 'per_booking' | 'on_demand';
  dataPoints: string[];
  responsibleParty: 'platform' | 'agency' | 'supplier';
}
```

### ESG Reporting Framework

```typescript
interface ESGReporting {
  reportType: ESGReportType;
  period: DateRange;
  dataCollection: DataCollectionPlan;
  reporting: ESGReport;
  verification: ESGVerification;
}

type ESGReportType =
  | 'brsr'                            // SEBI BRSR filing
  | 'ghg_protocol'                    // GHG Protocol emissions
  | 'gri'                             // Global Reporting Initiative
  | 'tcfd'                            // Task Force on Climate-related Financial Disclosures
  | 'cdp'                             // Carbon Disclosure Project
  | 'custom';                         // Custom corporate report

interface ESGReport {
  organizationId: string;
  reportPeriod: DateRange;
  executive: ESGExecutiveSummary;
  environmental: EnvironmentalReport;
  social: SocialReport;
  governance: GovernanceReport;
}

interface EnvironmentalReport {
  scope1Emissions: EmissionValue;     // Direct emissions (office, vehicles)
  scope2Emissions: EmissionValue;     // Indirect (electricity, heating)
  scope3Emissions: Scope3Breakdown;   // Value chain (travel, supply chain)
  emissionIntensity: EmissionIntensity;
  reductionTargets: EmissionTarget[];
  offsetActivity: OffsetReport;
  environmentalCompliance: ComplianceStatus;
}

interface Scope3Breakdown {
  businessTravel: EmissionValue;      // Employee business travel
  purchasedGoods: EmissionValue;      // Purchased goods and services
  upstreamTransport: EmissionValue;   // Upstream transportation
  downstreamTransport: EmissionValue; // Downstream (customer travel)
  wasteGenerated: EmissionValue;
  totalScope3: EmissionValue;
}

// Scope 3 travel emissions breakdown (for corporate client):
//
// Employee business travel:
//   - Flights: 45,000 km × 0.187 kg CO2e/km = 8,415 kg CO2e
//   - Hotels: 120 room-nights × 20.1 kg CO2e = 2,412 kg CO2e
//   - Ground transport: 3,000 km × 0.18 kg CO2e/km = 540 kg CO2e
//   Total employee travel: ~11,367 kg CO2e
//
// Customer-facing (downstream):
//   - If platform facilitates 10,000 trips/year
//   - Average trip emission: 2,500 kg CO2e
//   - Total facilitated: 25,000,000 kg CO2e (25,000 tonnes)
//   - This is the platform's Scope 3 downstream impact
//   - BRSR reporting: Disclose total facilitated emissions
//   - Reduction: Promote green alternatives, increase offset adoption

interface EmissionTarget {
  targetYear: number;
  baselineYear: number;
  baselineEmissions: EmissionValue;
  targetReduction: number;            // % reduction from baseline
  currentProgress: number;            // % achieved so far
  annualMilestones: AnnualMilestone[];
}

// Science Based Targets initiative (SBTi) alignment:
// Near-term: 42% reduction by 2030 (from 2020 baseline)
// Long-term: Net-zero by 2050
// For travel: Focus on reducing emission intensity per trip
//             Increase offset adoption rate
//             Shift toward sustainable transport options

// Corporate emission target tracking dashboard:
// ┌──────────────────────────────────────────────┐
// │  ESG Dashboard — FY 2025-26                  │
// │                                              │
// │  Scope 3 Travel Emissions                    │
// │  Target: 15% reduction from FY 2023-24       │
// │  Current: 8.2% reduction (55% of target)     │
// │  ████████████░░░░░░░░░░ 55%                 │
// │                                              │
// │  Trips with offset: 34% (target: 50%)        │
// │  Eco-certified stays: 28% (target: 40%)      │
// │  Green transport: 12% (target: 25%)          │
// │                                              │
// │  Department Breakdown:                        │
// │  Engineering: 2,100 kg CO2e ↓ 12%            │
// │  Sales: 4,800 kg CO2e ↓ 8%                   │
// │  Leadership: 6,200 kg CO2e ↑ 3% ⚠️          │
// │                                              │
// │  [Export BRSR Data] [Download PDF Report]    │
// └──────────────────────────────────────────────┘
```

### Carbon Tax & Trading

```typescript
interface CarbonTaxCompliance {
  jurisdiction: string;
  scheme: CarbonPricingScheme;
  applicability: TaxApplicability;
  reporting: TaxReporting;
  credits: CarbonCredit[];
}

interface CarbonPricingScheme {
  name: string;
  type: 'tax' | 'cap_trade' | 'offset_mandate';
  pricePerTonne: Money;
  currency: string;
  annualIncrease: number;             // % annual price increase
}

// Carbon pricing by jurisdiction:
// - EU ETS: €90-100/tonne CO2e (aviation included since 2012)
// - UK ETS: £65-75/tonne CO2e
// - Singapore: S$25/tonne CO2e (rising to S$50-80 by 2030)
// - India (CCTS): To be determined (expected ₹1,500-3,000/tonne)
// - CORSIA: Offset-based, not carbon tax
//
// Impact on travel pricing:
// EU flights: Carbon cost already embedded in ticket prices (~€5-50)
// India: No carbon tax on travel yet (CCTS may change this)
// Corporate: Internal carbon pricing (₹500-2,000/tonne) increasingly common

interface TaxReporting {
  reportFrequency: string;
  dataPoints: string[];
  filingMethod: string;
  deadline: string;
}

// Reporting requirements:
// - Track emissions per flight, per hotel, per trip
// - Allocate emissions to cost centers / departments
// - Maintain audit trail of emission calculations
// - Support multiple reporting frameworks (BRSR, GRI, CDP)
// - Export in standard formats (XBRL, CSV, PDF)
// - Retention: 8 years (India Companies Act requirement)
```

### Sustainability Data Governance

```typescript
interface SustainabilityDataGovernance {
  dataOwnership: DataOwnershipPolicy;
  dataQuality: DataQualityFramework;
  auditTrail: AuditTrailConfig;
  retention: RetentionPolicy;
  thirdPartySharing: DataSharingPolicy;
}

interface DataQualityFramework {
  emissionFactors: EmissionFactorSource[];
  updateFrequency: string;            // How often factors are updated
  validationRules: ValidationRule[];
  uncertaintyReporting: UncertaintyPolicy;
}

interface EmissionFactorSource {
  source: string;                     // e.g., "DEFRA 2024", "ICAO 2024"
  category: string;                   // e.g., "aviation", "hotels"
  lastUpdated: Date;
  nextUpdate: Date;
  reliability: 'official' | 'industry' | 'estimated';
}

// Emission factor sources (prioritized by reliability):
// 1. DEFRA (UK Government) — Most comprehensive, updated annually
// 2. ICAO Carbon Emissions Calculator — Aviation-specific
// 3. GHG Protocol — Standard methodology
// 4. Indian Bureau of Energy Efficiency (BEE) — India-specific
// 5. Cornell Hotel Sustainability Benchmarking — Hotels
// 6. EcoPassenger — Rail and road transport
// 7. Supplier self-reported data — Use with verification

// Data quality rules:
// - Emission factors updated annually (DEFRA releases in June)
// - Supplier data refreshed every 6 months
// - Calculation methodology documented per trip
// - Uncertainty range reported (±15% for calculated, ±30% for estimated)
// - Third-party verification for corporate reports
// - Data retention: 8 years (aligned with financial records)

interface AuditTrailConfig {
  calculationTracking: boolean;       // Track every emission calculation
  factorVersionTracking: boolean;     // Track which emission factors were used
  offsetTracking: boolean;            // Track offset purchases and retirement
  changeLog: boolean;                 // Log all sustainability data changes
}

// Audit requirements:
// Every emission calculation must be reproducible:
//   - Trip ID + Component ID
//   - Emission factor version used
//   - Calculation methodology applied
//   - Input parameters (distance, duration, class, etc.)
//   - Result (kg CO2e)
//   - Confidence level (measured/calculated/estimated)
//
// For BRSR filing:
//   - External auditor can request methodology documentation
//   - Must show calculation chain from raw data to reported figure
//   - Factor changes between years must be documented
//   - Any estimates must be flagged with methodology
```

---

## Open Problems

1. **Regulatory uncertainty** — India's carbon trading scheme (CCTS) rules are still being formulated. Can't design compliance for regulations that don't exist yet.

2. **Scope 3 attribution** — How much of a facilitated trip's emissions "belong" to the platform vs. the agency vs. the traveler? No standard attribution model.

3. **Cross-border complexity** — A trip from India to Singapore involves Indian, Singapore, and international aviation regulations. Emission reporting jurisdiction is unclear.

4. **Small agency burden** — BRSR and ESG reporting are designed for large corporates. Small travel agencies can't bear the compliance cost. Need right-sized reporting.

5. **Offset integrity** — Carbon offset markets have credibility issues. Double-counting, non-additional projects, and expired credits. Need robust verification.

---

## Next Steps

- [ ] Design ESG reporting framework aligned with BRSR and GRI
- [ ] Build Scope 3 travel emission tracking for corporate clients
- [ ] Create carbon tax compliance module with jurisdiction rules
- [ ] Design sustainability data governance with audit trail
- [ ] Study sustainability reporting platforms (Watershed, Persefoni, Salesforce Net Zero Cloud)
