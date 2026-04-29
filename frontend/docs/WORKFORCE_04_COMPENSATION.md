# Agent Performance & Workforce Management — Compensation & Incentives

> Research document for compensation structures, commission calculation engine, bonus triggers, team incentives, ESOP/profit sharing, and India-specific statutory compliance (PF, ESI, TDS on commissions).

---

## Key Questions

1. **What compensation model (base + commission + bonus) works best for Indian travel agents at different career stages?**
2. **How do we design a commission calculation engine that accounts for trip value, destination, customer tier, and agent level?**
3. **What bonus triggers and team incentive structures drive the right behaviors?**
4. **How do ESOP and profit-sharing models work for Indian travel startups?**
5. **What are the PF, ESI, TDS, and statutory compliance requirements for variable compensation?**

---

## Research Areas

### Compensation Structure

```typescript
interface CompensationStructure {
  agentId: string;
  role: AgentRole;
  level: AgentLevel;
  components: CompensationComponents;
  effectiveDate: Date;
  approvedBy: string;
}

interface CompensationComponents {
  fixed: FixedCompensation;
  variable: VariableCompensation;
  benefits: BenefitsValue;
  totalCTC: number;                    // Annual CTC in INR
}

interface FixedCompensation {
  basicSalary: MonthlyAmount;         // 40-50% of CTC
  houseRentAllowance: MonthlyAmount;   // 40-50% of basic (metro), 20-30% (non-metro)
  specialAllowance: MonthlyAmount;     // Balancing component
  conveyanceAllowance: MonthlyAmount;  // ₹1,600/month (₹19,200/year, tax-exempt)
  medicalAllowance: MonthlyAmount;     // ₹1,250/month (₹15,000/year)
  leaveTravelAllowance: AnnualAmount;  // 2 trips in 4-year block
}

interface VariableCompensation {
  commission: CommissionStructure;
  performanceBonus: BonusStructure;
  spotAwards: SpotAwardStructure;
  retentionBonus: RetentionBonusStructure;
  annualIncentive: AnnualIncentiveStructure;
}

// Compensation model by role:
//
// MODEL A: "High Variable" (Junior Agents, L1-L2)
// Fixed: 60% of CTC | Variable: 40% of CTC
// Rationale: Junior agents need base security + high commission incentive to learn selling
// Risk: Income instability in off-season
// Mitigation: Monthly minimum guarantee (70% of fixed component)
//
// MODEL B: "Balanced" (Senior Agents, L3-L4)
// Fixed: 70% of CTC | Variable: 30% of CTC
// Rationale: Established agents have predictable pipeline, reward performance without volatility
// Risk: Commission may not be motivating enough
// Mitigation: Higher commission rates on premium/international bookings
//
// MODEL C: "Fixed Heavy" (Team Lead, Branch Manager)
// Fixed: 80% of CTC | Variable: 20% of CTC
// Rationale: Managers should optimize team performance, not individual bookings
// Risk: Manager may optimize personal bookings over team
// Mitigation: Variable tied to TEAM metrics, not individual
//
// MODEL D: "Commission Only" (Freelance / Seasonal)
// Fixed: 0% | Variable: 100%
// Rationale: No overhead commitment, pay purely for results
// Risk: Loyalty, quality control, brand representation
// Mitigation: Quality gates, minimum CSAT threshold, training required before activation

// Salary bands by level (CTC, annual, INR):
//
// L1 Trainee:     ₹2.4-3.6 LPA  → Fixed ₹1.44-2.16L + Variable ₹0.96-1.44L
// L2 Junior:      ₹3.6-5.4 LPA  → Fixed ₹2.16-3.24L + Variable ₹1.44-2.16L
// L3 Mid:         ₹5.4-8.4 LPA  → Fixed ₹3.78-5.88L + Variable ₹1.62-2.52L
// L4 Senior:      ₹8.4-14.4 LPA → Fixed ₹5.88-10.08L + Variable ₹2.52-4.32L
// L5 Lead/Expert: ₹14.4-24 LPA  → Fixed ₹11.52-19.20L + Variable ₹2.88-4.80L
// Branch Manager: ₹18-36 LPA    → Fixed ₹14.40-28.80L + Variable ₹3.60-7.20L
//
// Metro premium: +15-20% on base bands
// Specialist premium: +10% for certified specialists
// Language premium: +5% for regional language + English fluency
```

### Commission Calculation Engine

```typescript
interface CommissionEngine {
  rules: CommissionRule[];
  calculator: CommissionCalculator;
  overrides: CommissionOverride[];
  settlement: CommissionSettlement;
}

interface CommissionRule {
  id: string;
  name: string;                       // "International Package Commission"
  priority: number;                   // Higher = evaluated first
  conditions: CommissionCondition[];
  rate: CommissionRate;
  caps: CommissionCap;
  exclusions: string[];               // Booking types excluded from this rule
}

interface CommissionCondition {
  field: string;                      // "tripValue", "destination", "agentLevel"
  operator: 'eq' | 'neq' | 'gt' | 'gte' | 'lt' | 'lte' | 'in' | 'between';
  value: any;
}

interface CommissionRate {
  type: 'percentage' | 'fixed_amount' | 'tiered' | 'slab';
  value: number | TieredRate[];
}

// Commission rate structure:
//
// TYPE: PERCENTAGE
// Example: 2% of trip revenue
// Simple, scales with value
//
// TYPE: FIXED AMOUNT
// Example: ₹500 per confirmed booking
// Predictable, doesn't scale with value
//
// TYPE: TIERED (recommended)
// Rate changes at thresholds
// Example: 1.5% on first ₹50K, 2% on ₹50K-1L, 2.5% above ₹1L
// Encourages higher-value bookings
//
// TYPE: SLAB
// Different rates for different categories
// Example: Domestic 1.5%, SE Asia 2%, Europe 3%, Luxury 3.5%
// Rewards complex/difficult bookings

interface TieredRate {
  min: number;                        // Trip value lower bound (INR)
  max: number | null;                 // Upper bound (null = no limit)
  rate: number;                       // Commission percentage
}

// COMMISSION RULES (example for L3 Mid-level agent):
//
// RULE 1: "Domestic Package"
// Conditions: tripType = "package" AND destinationTier = "domestic"
// Rate: 1.5% of trip revenue
// Cap: ₹15,000 per booking
//
// RULE 2: "International Package — SE Asia"
// Conditions: tripType = "package" AND destination IN ("Thailand", "Bali", "Singapore", "Malaysia", "Vietnam")
// Rate: Tiered — 2% first ₹50K, 2.5% ₹50K-1L, 3% above ₹1L
// Cap: ₹25,000 per booking
//
// RULE 3: "International Package — Europe/Middle East"
// Conditions: tripType = "package" AND destinationTier = "europe" OR "middle_east"
// Rate: 3% of trip revenue
// Cap: ₹40,000 per booking
//
// RULE 4: "Flight Only"
// Conditions: tripType = "flight_only"
// Rate: Fixed ₹200 per segment per passenger
// Rationale: Low margin, high volume, fixed effort
//
// RULE 5: "Ancillary — Insurance"
// Conditions: component = "insurance"
// Rate: 10% of insurance premium
// Rationale: High margin add-on, easy to sell
//
// RULE 6: "Ancillary — Forex"
// Conditions: component = "forex"
// Rate: 0.5% of forex amount (spread commission)
//
// RULE 7: "Ancillary — Visa"
// Conditions: component = "visa"
// Rate: Fixed ₹300 per visa processed
//
// RULE 8: "Group Tour" (>10 pax)
// Conditions: groupSize > 10
// Rate: 2% + ₹100 per passenger above 10
// Rationale: More work per booking, reward volume handling
//
// RULE 9: "Repeat Customer"
// Conditions: customerBookings > 1
// Rate: +0.5% on top of base commission
// Rationale: Reward customer retention
//
// RULE 10: "Upsell Bonus"
// Conditions: actualTripValue > originalQuote * 1.2
// Rate: Additional 1% on the upsell amount
// Rationale: Reward upselling capability

interface CommissionCap {
  maxPerBooking: number;              // INR
  maxPerMonth: number;                // INR (0 = no monthly cap)
  maxPerQuarter: number;              // INR
  maxPerYear: number;                 // INR
}

// Monthly commission caps by level:
// L1: ₹30,000/month max commission
// L2: ₹50,000/month
// L3: ₹75,000/month
// L4: ₹1,00,000/month
// L5: ₹1,50,000/month
// (Caps protect agency from excessive payouts on unusually large bookings)

interface CommissionCalculator {
  agentId: string;
  bookingId: string;
  booking: BookingDetails;
  matchedRules: CommissionRule[];
  calculation: CommissionCalculation;
}

interface BookingDetails {
  bookingId: string;
  agentId: string;
  customerTier: CustomerTier;
  tripValue: number;                  // Total booking value (INR)
  components: BookingComponent[];
  destination: string;
  destinationTier: DestinationTier;
  tripType: TripType;
  groupSize: number;
  customerBookings: number;           // Previous bookings by this customer
  isRepeatCustomer: boolean;
  quotedValue: number;                // Original quote (to detect upsells)
}

type CustomerTier =
  | 'standard'                        // First-time or infrequent
  | 'premium'                         // 3+ bookings or high-value
  | 'vip';                            // Corporate / high-net-worth

type DestinationTier =
  | 'domestic'
  | 'south_east_asia'
  | 'middle_east'
  | 'europe'
  | 'far_east'
  | 'exotic';                         // Maldives, Mauritius, Seychelles

interface BookingComponent {
  type: 'flight' | 'hotel' | 'activity' | 'insurance' | 'forex' | 'visa' | 'transfer' | 'package';
  value: number;                      // INR
  margin: number;                     // Agency margin (%)
  supplier: string;
}

interface CommissionCalculation {
  bookingId: string;
  lineItems: CommissionLineItem[];
  totalCommission: number;            // INR
  effectiveRate: number;              // % of trip value
  capApplied: boolean;
  cappedAmount?: number;
}

interface CommissionLineItem {
  ruleId: string;
  ruleName: string;
  basis: number;                      // Amount commission is calculated on
  rate: number;                       // Commission rate
  commission: number;                 // Calculated commission (INR)
  note: string;                       // "2% on ₹1,20,000 international package"
}

// Commission calculation example:
//
// Booking: Kerala Honeymoon, ₹1,45,000
// Agent: L3 Mid-level, Kerala Silver certified
// Customer: Premium tier, 2nd booking
//
// Line items:
// 1. Domestic Package commission: 1.5% × ₹1,45,000 = ₹2,175
// 2. Kerala specialist bonus: +0.5% × ₹1,45,000 = ₹725
// 3. Repeat customer bonus: +0.5% × ₹1,45,000 = ₹725
// 4. Insurance sold (₹8,500): 10% × ₹8,500 = ₹850
// 5. Visa processing (2 pax): ₹300 × 2 = ₹600
//
// Total: ₹5,075
// Effective rate: 3.5% of trip value
// Cap check: ₹5,075 < ₹75,000 monthly cap → No cap applied
```

### Bonus Triggers & Team Incentives

```typescript
interface BonusStructure {
  individual: IndividualBonus[];
  team: TeamBonus[];
  agency: AgencyBonus[];
}

interface IndividualBonus {
  id: string;
  name: string;                       // "Monthly Revenue Target"
  trigger: BonusTrigger;
  payout: BonusPayout;
  frequency: 'monthly' | 'quarterly' | 'annual';
}

interface BonusTrigger {
  type: 'threshold' | 'milestone' | 'streak' | 'ranking' | 'event';
  condition: string;
  measurement: string;
  value: number;
}

// Individual bonus triggers:
//
// 1. REVENUE TARGET BONUS (Monthly)
//    Trigger: Monthly revenue ≥ 100% of target
//    Payout: ₹3,000 (at target), ₹5,000 (at 120%), ₹8,000 (at 150%)
//    Budget: ₹36,000-96,000/year per agent
//
// 2. CONVERSION STREAK BONUS
//    Trigger: 5 consecutive leads converted
//    Payout: ₹1,000 spot bonus + recognition
//    Purpose: Reward consistent conversion
//
// 3. HIGH NPS BONUS (Quarterly)
//    Trigger: Personal NPS ≥ 60 for the quarter (min 10 reviews)
//    Payout: ₹5,000
//    Purpose: Incentivize quality, not just volume
//
// 4. CERTIFICATION BONUS
//    Trigger: Complete destination specialist certification (Gold+)
//    Payout: ₹10,000 + permanent +0.5% commission boost
//    Purpose: Invest in skill development
//
// 5. ZERO ERROR MONTH
//    Trigger: No document/booking errors for entire month
//    Payout: ₹2,000
//    Purpose: Reward accuracy
//
// 6. CUSTOMER REFERRAL BONUS
//    Trigger: Existing customer refers new customer who books
//    Payout: ₹500 per referral booking
//    Purpose: Incentivize word-of-mouth
//
// 7. PEAK SEASON HERO (Oct-Dec)
//    Trigger: Handle 50+ bookings during peak season quarter
//    Payout: ₹10,000 end-of-season bonus
//    Purpose: Retain agents during high-pressure period

interface TeamBonus {
  id: string;
  name: string;                       // "Team Revenue Target"
  teamId: string;
  trigger: BonusTrigger;
  distribution: TeamDistribution;
  payout: BonusPayout;
}

interface TeamDistribution {
  method: 'equal' | 'proportional' | 'tiered';
  eligibleRoles: AgentRole[];
}

// Team bonus structures:
//
// 1. TEAM REVENUE TARGET (Quarterly)
//    Trigger: Team combined revenue ≥ 100% of quarterly target
//    Payout: ₹2,000 per team member (equal), or proportional to individual contribution
//    Eligible: All team members (including support staff)
//
// 2. BRANCH NPS TARGET (Quarterly)
//    Trigger: Branch average NPS ≥ 50
//    Payout: Team outing budget (₹500/person) + ₹1,000 per person
//    Purpose: Team-wide focus on customer experience
//
// 3. ZERO ESCALATION MONTH
//    Trigger: No customer escalations to management for entire month
//    Payout: ₹1,000 per team member
//    Purpose: Encourage proactive problem resolution

interface AgencyBonus {
  id: string;
  name: string;                       // "Annual Profit Share"
  trigger: BonusTrigger;
  distribution: AgencyDistribution;
}

// Agency-wide bonus:
//
// 1. ANNUAL PROFIT SHARING
//    Trigger: Agency hits annual revenue + profitability targets
//    Pool: 5% of net profit distributed to employees
//    Distribution: Proportional to tenure + performance rating
//    Eligible: All employees with 1+ year tenure
//
// 2. DIWALI BONUS (Customary in India)
//    Trigger: Annual (October/November)
//    Payout: 1 month's basic salary (customary, not statutory for most states)
//    Note: Some states mandate bonus under Payment of Bonus Act (8.33% of annual salary)
```

### ESOP / Profit Sharing for Startups

```typescript
interface ESOPStructure {
  planName: string;                   // "Waypoint ESOP Plan 2026"
  totalPool: string;                  // "10% of issued equity"
  vestingSchedule: VestingSchedule;
  exerciseRules: ExerciseRules;
  grants: ESOPGrant[];
  compliance: ESOPCompliance;
}

interface VestingSchedule {
  type: 'standard_4_year' | 'performance_based' | 'hybrid';
  cliffPeriod: number;                // Months (typically 12)
  vestingFrequency: 'monthly' | 'quarterly' | 'annual';
  totalVestingYears: number;          // Typically 4 years
  accelerationClause?: string;        // "Double-trigger on acquisition"
}

// Standard Indian startup ESOP:
// - 10-15% of equity reserved for ESOP pool
// - 4-year vesting with 1-year cliff
//   Year 0-1: 0% vested (cliff)
//   Year 1: 25% vested
//   Year 2-4: 6.25% vested per quarter (remaining 75%)
// - Exercise window: 90 days after leaving (or 5 years for listed companies per new rules)
// - Strike price: Fair market value (FMV) at time of grant
//   For Indian startups: FMV per SEBI/Companies Act guidelines
//
// Grant sizes by role (typical for Series A travel startup):
// L3 Agent: 0.02-0.05% of company
// L4 Senior: 0.05-0.10%
// L5 Lead: 0.10-0.20%
// Branch Manager: 0.15-0.30%
// VP/Director: 0.30-1.00%
//
// ESOP value scenario:
// Company valued at ₹50 crore at grant
// Agent granted 0.05% → ₹2.5 lakh worth at grant
// Company grows 5x in 4 years → ₹12.5 lakh value at vesting
// Tax impact: Perquisite tax at exercise + capital gains at sale

interface ExerciseRules {
  exerciseWindow: string;             // "90 days post-termination"
  exercisePriceMethod: string;        // "FMV at grant date" (per Companies Act)
  buybackPolicy?: string;            // "Company may buy back vested options at FMV"
  transferability: boolean;           // Whether options can be transferred
}

interface ESOPGrant {
  employeeId: string;
  numberOfOptions: number;
  strikePrice: number;                // INR per option
  grantDate: Date;
  cliffEndDate: Date;
  vestingEndDate: Date;
  vested: number;                     // Options vested so far
  exercised: number;                  // Options exercised so far
  forfeited: number;                  // Options forfeited (left before cliff)
}

interface ESOPCompliance {
  // India ESOP compliance requirements:
  // 1. Companies Act, 2013: Section 62(1)(b) for listed, 62(1)(c) for unlisted
  // 2. SEBI (Share Based Employee Benefits) Regulations, 2014 (for listed companies)
  // 3. Companies (Share Capital and Debentures) Rules, 2014
  // 4. Shareholder approval: Special resolution at general meeting
  // 5. Valuation: Registered valuer for FMV determination
  // 6. Reporting: Form MGT-7 (annual return), Form MBP-2 (register of ESOP)
  // 7. Taxation (employee):
  //    - No tax at grant
  //    - Perquisite tax at exercise: (FMV at exercise - exercise price) × options × tax rate
  //    - Capital gains tax at sale: FMV at exercise as cost basis
  //    - New rule (2024): Deferred tax for startups (DPIIT-recognized) up to 5 years
  // 8. Tax deduction (employer): Under Section 37(1) for employer's cost
}
```

### Statutory Compliance — PF, ESI, TDS

```typescript
interface StatutoryCompliance {
  providentFund: PFCompliance;
  esi: ESICompliance;
  tds: TDSCompliance;
  professionalTax: PTCompliance;
  gratuity: GratuityCompliance;
  bonusAct: BonusActCompliance;
}

interface PFCompliance {
  establishmentCode: string;          // EPFO establishment code
  uanPrefix: string;                  // Universal Account Number prefix
  rate: {
    employee: number;                 // 12% of basic + DA
    employer: number;                 // 12% of basic + DA (3.67% EPF + 8.33% EPS)
    adminCharges: number;             // 0.5% of basic + DA
    edli: number;                     // 0.5% of basic + DA (Employee Deposit Linked Insurance)
  };
  wageCeiling: number;                // ₹15,000/month basic (mandatory for all ≤ this)
  voluntaryHigher: boolean;           // VPF (Voluntary Provident Fund) allowed
  filingSchedule: {
    monthlyDeposit: string;           // 15th of following month
    monthlyReturn: string;            // ECR filing by 15th
    annualReturn: string;             // March 31st
  };
  // Key considerations:
  // - PF is calculated on basic + dearness allowance + retaining allowance
  // - Commission/variable pay: PF applicability debated; safer to include if part of regular wage
  // - For travel agencies: Include commission in PF wages if paid monthly as part of salary
  //   Exclude if paid as separate reimbursement/allowance
  // - New establishment: Register within 30 days of hiring 20th employee
}

interface ESICompliance {
  establishmentCode: string;          // ESIC establishment code
  applicable: boolean;                // True if 10+ employees (most states) or 20+ (some)
  rate: {
    employee: number;                 // 0.75% of gross wages
    employer: number;                 // 3.25% of gross wages
  };
  wageCeiling: number;                // ₹21,000/month gross
  filingSchedule: {
    monthlyDeposit: string;           // 15th of following month
    halfYearlyReturn: string;         // January and July
  };
  // Key considerations:
  // - Gross wages = basic + HRA + special allowance + overtime + commission
  // - ESIC covers: Medical, sickness, maternity, disability, dependant benefits
  // - Cash benefits: Sickness (70% of wages), Maternity (full wages)
  // - Commission inclusion: If paid monthly as part of wages → include for ESI
  //   If paid quarterly/annually → may be excluded (consult ESIC local office)
}

interface TDSCompliance {
  // TDS on salary (Section 192):
  salaryTDS: {
    applicable: boolean;              // Always applicable if salary > basic exemption
    rate: 'slab';                     // Based on employee's tax slab
    exemptionLimit: number;           // ₹2,50,000 (general), ₹3,00,000 (senior citizen)
    newRegimeDefault: boolean;        // New tax regime is default from FY 2023-24
    quarterlyDeduction: boolean;      // Deduct monthly, deposit by 7th of following month
    form16: string;                   // Issue by June 15th of following year
    form24Q: string;                  // Quarterly TDS return
  };

  // TDS on commission (Section 194H):
  commissionTDS: {
    applicable: boolean;              // Yes, if commission paid to agent > ₹15,000/year
    rate: number;                     // 5% (resident), 10% (no PAN), 20% (non-resident)
    threshold: number;                // ₹15,000/year (no TDS below this)
    panMandatory: boolean;            // Yes, else 20% TDS
    depositDeadline: string;          // 7th of following month
    returnFiling: string;             // Form 26Q quarterly
    certificate: string;              // Form 16A (quarterly, to deductee)
  };

  // TCS on overseas tour packages (Section 206C(1G)):
  tcsOverseas: {
    applicable: boolean;              // Yes, for overseas tour packages
    rate: number;                     // 5% (up to ₹7 lakh), 10% (above ₹7 lakh)
    collectedBy: string;              // Travel agent selling overseas package
    customerType: 'individual' | 'corporate';
    panOfCustomer: boolean;           // Mandatory for TCS collection
    returnFiling: string;             // Form 27EQ quarterly
    // Note: TCS is collected FROM customer, not deducted from agent commission
    // Agent collects TCS from customer and deposits with government
  };

  // Tax regime comparison for agents (FY 2026-27):
  //
  // NEW REGIME (Default):
  // 0 - 3L:    0%
  // 3L - 7L:   5% (rebate up to ₹25,000 for income ≤ 7L)
  // 7L - 10L:  10%
  // 10L - 12L: 15%
  // 12L - 15L: 20%
  // Above 15L: 30%
  // Standard deduction: ₹75,000
  // No HRA, LTA, 80C deductions
  //
  // OLD REGIME (Opt-in):
  // 0 - 2.5L:  0%
  // 2.5 - 5L:  5% (rebate under 87A for income ≤ 5L)
  // 5 - 10L:   20%
  // Above 10L: 30%
  // Standard deduction: ₹50,000
  // HRA, LTA, 80C (₹1.5L), 80D (health insurance) deductions available
  //
  // Agent tax planning:
  // Agents earning <₹7L: New regime is almost always better
  // Agents earning ₹7-12L: Depends on deductions (HRA + 80C can make old regime better)
  // Agents earning >₹12L: Old regime usually better IF claiming full HRA + 80C + LTA
}

interface PTCompliance {
  // Professional Tax (state-level):
  applicableStates: string[];         // All states except Delhi, UTs
  rate: {
    monthly: number;                  // Typically ₹200/month (varies by state)
    annual: number;                   // ₹2,500/year max (constitutional limit)
  };
  collectionMethod: 'employer_deduct' | 'direct';
  filingFrequency: 'monthly' | 'annual'; // Depends on state
  // State-wise rates:
  // Maharashtra: ₹200/month (salary > ₹10,000)
  // Karnataka: ₹200/month (salary > ₹15,000)
  // Tamil Nadu: ₹208/month (salary > ₹21,000)
  // West Bengal: ₹200/month (salary > ₹40,000)
  // Gujarat: ₹200/month (salary > ₹12,000)
}

interface GratuityCompliance {
  // Payment of Gratuity Act, 1972:
  applicable: boolean;                // 10+ employees
  formula: string;                    // (15 × last drawn salary × years of service) / 26
  maxAmount: number;                  // ₹20 lakh (2026, government ceiling)
  vestingPeriod: number;              // 5 years continuous service
  // Note: "Last drawn salary" = basic + dearness allowance
  // For agents with high commission: Gratuity is on basic + DA, NOT commission
  // This is an important design consideration for salary structure
  taxExemption: string;              // Max ₹20 lakh exempt (Section 10(10))
}

interface BonusActCompliance {
  // Payment of Bonus Act, 1965:
  applicable: boolean;                // 20+ employees, salary ≤ ₹21,000/month
  minBonus: number;                   // 8.33% of annual salary (statutory minimum)
  maxBonus: number;                   // 20% of annual salary
  allocableSurplus: string;           // 60% of gross profit (companies), 67% (non-companies)
  setOnSetOff: string;               // "On" and "Off" set for surplus/deficit years
  paymentDeadline: string;            // Within 8 months of financial year end (by November)
  // Financial year: April 1 - March 31
  // Most Indian agencies pay Diwali bonus (October/November) to coincide
}
```

### Commission Settlement Workflow

```typescript
interface CommissionSettlement {
  period: SettlementPeriod;
  calculations: SettlementCalculation[];
  approvals: SettlementApproval[];
  payout: SettlementPayout[];
  reconciliation: SettlementReconciliation;
}

interface SettlementPeriod {
  type: 'monthly' | 'quarterly';
  month?: number;                     // For monthly settlement
  quarter?: string;                   // "Q1 FY27" = Apr-Jun 2026
  startDate: Date;
  endDate: Date;
  cutoffDate: Date;                   // Bookings confirmed by this date are included
  settlementDate: Date;               // When payout happens
}

// Settlement workflow:
// 1. SYSTEM: Auto-calculate commissions for all bookings in period
//    - Match each booking to commission rules
//    - Apply caps and adjustments
//    - Generate preliminary calculation sheet
//
// 2. MANAGER REVIEW: Manager reviews calculations
//    - Verify high-value commissions (>₹10,000)
//    - Check for anomalies (unusually high/low commissions)
//    - Apply manual adjustments (disputes, overrides, corrections)
//
// 3. FINANCE APPROVAL: Finance team approves payout
//    - Verify against revenue recognition
//    - Check TDS calculations
//    - Ensure PF/ESI deductions on commission (if applicable)
//    - Budget check (total commission ≤ allocated budget)
//
// 4. PAYOUT: Commission deposited to agent account
//    - Added to monthly salary (if same employer)
//    - Or separate bank transfer (if freelancer)
//    - Payslip includes commission breakdown
//
// 5. RECONCILIATION: Post-payout reconciliation
//    - Match commission payout to booking revenue
//    - Handle cancellations (clawback commission if trip cancelled)
//    - Handle modifications (recalculate if trip value changed)
//
// Commission clawback rules:
// Trip cancelled by customer (>30 days before departure): Full clawback
// Trip cancelled by customer (15-30 days): 50% clawback
// Trip cancelled by customer (<15 days): No clawback (agent did the work)
// Trip cancelled by agency error: No clawback from agent
// Trip modified (value reduced): Recalculate and clawback difference
// Trip modified (value increased): Pay additional commission in next cycle

interface SettlementPayout {
  agentId: string;
  period: SettlementPeriod;
  components: {
    commission: number;               // Total commission earned
    bonus: number;                    // Bonuses earned in period
    adjustments: number;              // Manual adjustments (+/-)
    clawbacks: number;                // Clawbacks from cancellations
    grossPayout: number;              // Before deductions
    tds: number;                      // TDS deducted (Section 194H or 192)
    pfDeduction: number;              // PF on commission (if applicable)
    esiDeduction: number;             // ESI on commission (if applicable)
    netPayout: number;                // Amount deposited to agent account
  };
  payoutMethod: 'salary_add' | 'bank_transfer' | 'separate_cheque';
  payoutDate: Date;
  payslipId: string;
}
```

---

## Open Problems

1. **Commission on multi-agent bookings** — When two agents collaborate on a complex booking (e.g., one handles flights, another handles hotels), splitting commission is subjective. Need a contribution-tracking mechanism that agents find fair.

2. **Seasonal commission normalization** — Peak season agents earn significantly more commission than off-season agents, even with identical skill. A seasonal adjustment factor (higher commission rates in lean periods) may be needed to retain agents year-round.

3. **PF/ESI on variable commission** — Indian labor law is ambiguous about whether PF/ESI applies to commission. Including commission inflates employer costs (additional 16-17%). Not including it risks non-compliance. Each agency must get a legal opinion for their specific structure.

4. **TDS compliance for freelancers** — Freelance agents (commission-only) need TDS at 5% (Section 194H). Managing PAN verification, threshold tracking (₹15,000/year), and quarterly returns for 50+ freelancers is administratively heavy.

5. **ESOP valuation for unlisted startups** — Private travel startups need annual FMV determination by a registered valuer. The process is expensive (₹1-3 lakh per valuation) and the result directly impacts employee tax liability.

6. **Commission clawback disputes** — When a trip is cancelled and commission is claw back, agents feel penalized for factors outside their control (supplier bankruptcy, customer personal emergency). A fair clawback policy needs nuance beyond simple rules.

---

## Next Steps

- [ ] Design commission rule engine with configurable tiers, caps, and overrides
- [ ] Build commission calculation algorithm with multi-rule matching and priority resolution
- [ ] Model compensation structures for all levels with fixed/variable breakdown
- [ ] Create TDS, PF, ESI compliance workflow for salary + commission payouts
- [ ] Design bonus trigger system with individual and team incentives
- [ ] Research ESOP management platforms ( Vega, Trustio, ESOP Direct)
- [ ] Study payroll systems for Indian startups (RazorpayX Payroll, Zoho Payroll, Keka, Darwinbox)
- [ ] Integrate with WORKFORCE_01_PERFORMANCE for performance-linked compensation
- [ ] Integrate with WORKFORCE_02_SCHEDULING for overtime compensation calculations
