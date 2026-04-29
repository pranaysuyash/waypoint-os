# Customer Segmentation 04: Customer Retention

> Loyalty tiers, churn prediction, win-back campaigns, referral programs, and India-specific retention

---

## Document Overview

**Focus:** Segment-based retention strategies, churn prediction, and customer lifetime value
**Status:** Research Exploration
**Last Updated:** 2026-04-28

---

## Key Questions

### Retention Strategy
- How do loyalty tiers drive retention across segments?
- What win-back campaigns work for churned customers?
- How do re-engagement sequences differ by segment?

### Churn Prediction
- What signals indicate a customer is about to churn?
- How do we detect decreased trip frequency, support complaints, and price sensitivity?
- What is the lead time between churn signals and actual churn?
- How accurate can a churn prediction model be?

### Referral Programs
- How do referral programs work differently by segment?
- What incentives drive referrals in the Indian market?
- How do we track and attribute referrals?

### India-Specific Retention
- How do festive offers, referral bonuses, and group discounts affect retention?
- What role do relationships and trust play in Indian travel agency loyalty?
- How does word-of-mouth differ in the Indian context?

### Customer Success Metrics
- What are the right retention metrics for a travel agency?
- How do we measure customer health across segments?
- What dashboards and alerts do agents need?

---

## Research Areas

### A. Loyalty Tiers & Retention

**Loyalty Tier Structure:**

| Tier | Qualification | Benefits | Retention Focus | Research Needed |
|------|--------------|----------|-----------------|-----------------|
| **Platinum** | > INR 5L/yr or 5+ trips | Dedicated agent, priority service, exclusive previews, airport lounge access, free cancellations | Prevent churn — immediate intervention | Platinum retention rate? |
| **Gold** | INR 2-5L/yr or 3-4 trips | Preferred agent, early access to deals, flexible payment, complimentary upgrades | Nurture and upgrade to Platinum | Gold-to-Platinum upgrade rate? |
| **Silver** | INR 50K-2L/yr or 2 trips | Standard service, birthday offers, seasonal deals | Increase trip frequency | Silver-to-Gold conversion? |
| **Bronze** | < INR 50K/yr or 1 trip | Self-service, promotional offers, festival deals | Convert to repeat customer | Bronze repeat rate? |
| **New** | First interaction | Welcome package, first-booking incentive, onboarding | Convert to first booking | New-to-first booking rate? |

**Tier-Based Retention Playbook:**

| Tier | Risk Signal | Response | Timeline | Research Needed |
|------|------------|----------|----------|-----------------|
| **Platinum** | No booking in 6 months | Agent calls personally, exclusive offer | Within 48 hours of detection | Platinum personal call ROI? |
| **Gold** | No booking in 9 months | Semi-personal outreach, curated offer | Within 1 week | Gold outreach effectiveness? |
| **Silver** | No booking in 12 months | Automated re-engagement sequence | Within 2 weeks | Silver automation conversion? |
| **Bronze** | No booking in 15 months | Automated win-back with strong incentive | Within 1 month | Bronze win-back rate? |
| **Any** | Support complaint | Immediate agent follow-up + recovery offer | Within 24 hours | Service recovery success rate? |

### B. Churn Prediction Model

**Churn Signal Framework:**

```
+---------------------------------------------------+
|            CHURN SIGNAL DETECTION                  |
+---------------------------------------------------+
|                                                     |
|  EARLY WARNING (90-180 days before)                |
|  |-- Decreased trip frequency                      |
|  |-- Shorter booking lead time (impulsive)         |
|  |-- Reduced spend per trip                        |
|  |-- Less engagement with communications           |
|  |-- Stopped opening WhatsApp messages             |
|  |                                                  |
|  MEDIUM RISK (60-90 days before)                   |
|  |-- No booking inquiry in expected period          |
|  |-- Price comparison questions (switching intent)  |
|  |-- Browsing competitor sites (detected via       |
|  |   search engine referral data)                  |
|  |-- Cancelled a booking without rebooking         |
|  |-- Skipped usual seasonal trip                   |
|  |                                                  |
|  HIGH RISK (30-60 days before)                     |
|  |-- Support complaint (unresolved)                |
|  |-- Negative review or social media post          |
|  |-- Unsubscribed from communications              |
|  |-- Removed from WhatsApp broadcast list          |
|  |-- Asked for data deletion (DPDP Act)            |
|  |                                                  |
|  CRITICAL (0-30 days)                              |
|  |-- Active booking with competitor (detected)     |
|  |-- Explicit statement of leaving                 |
|  |-- Account deletion request                      |
|  |-- Payment dispute or chargeback                 |
|                                                     |
+---------------------------------------------------+
```

**Churn Prediction Data:**

| Signal Category | Specific Signals | Data Source | Weight (Est.) | Research Needed |
|-----------------|-----------------|-------------|---------------|-----------------|
| **Frequency decline** | Months since last trip, gap vs. historical frequency | Booking engine | 0.30 | Frequency decay function? |
| **Engagement decline** | Email/WhatsApp open rate drop, no click-through | Communication logs | 0.20 | Engagement threshold? |
| **Price sensitivity** | Increased negotiation, more discount requests, comparing quotes | Agent notes, CRM | 0.15 | Price sensitivity scoring? |
| **Support complaints** | Number of complaints, unresolved tickets, CSAT score | Help desk | 0.15 | Complaint-to-churn correlation? |
| **Competitor signals** | Search behavior, mentioned competitor, shared competitor quote | Agent notes, analytics | 0.10 | Detection reliability? |
| **Seasonal miss** | Did not book expected seasonal trip | Booking history, calendar | 0.10 | Seasonal pattern reliability? |

**Churn Prediction Model Options:**

| Model | Complexity | Accuracy Target | Data Needed | Research Needed |
|-------|-----------|-----------------|-------------|-----------------|
| **Rule-based** | Low | 60-70% | RFM + simple rules | Baseline accuracy? |
| **Logistic regression** | Medium | 70-80% | Structured signals | Feature engineering? |
| **Random forest** | Medium | 75-85% | Structured + behavioral | Feature importance? |
| **Gradient boosting (XGBoost)** | High | 80-90% | All available signals | Hyperparameter tuning? |
| **Neural network** | Very high | 85-92% | All signals + sequences | Training data quantity? |
| **Ensemble** | Very high | 88-95% | All of the above | Ensemble composition? |

### C. Win-Back Campaigns

**Win-Back Strategy by Segment:**

| Segment | Win-Back Approach | Incentive | Channel | Duration | Research Needed |
|---------|------------------|-----------|---------|----------|-----------------|
| **Churned Platinum** | Personal call from senior agent | Exclusive comeback offer, status match | Phone + WhatsApp | 30-day sequence | Platinum win-back rate? |
| **Churned Gold** | Personal message from known agent | Special discount + loyalty point bonus | WhatsApp + Email | 30-day sequence | Gold win-back rate? |
| **Churned Silver** | Automated personalized sequence | Festival-specific offer + flexible payment | WhatsApp + Email | 60-day sequence | Silver win-back rate? |
| **Churned Bronze** | Automated generic sequence | Strong discount on popular package | Email + SMS | 90-day sequence | Bronze win-back rate? |
| **Any (complaint-driven)** | Agent apology + service recovery | Full service recovery, complimentary add-on | Phone (mandatory) | Immediate | Service recovery ROI? |

**Win-Back Sequence:**

```
Day 0:   [Trigger: Churn detected]
         |
Day 1:   [Message 1] "We noticed you haven't traveled recently"
         |   Channel: Segment-preferred
         |   Tone: Warm, no-pressure
         |
Day 5:   [Message 2] "Here's something special just for you"
         |   Channel: Segment-preferred
         |   Content: Personalized offer based on past preferences
         |
Day 12:  [Message 3] "Your favorite destination has new experiences"
         |   Channel: Alternative channel
         |   Content: Destination-specific content
         |
Day 20:  [Message 4] "Limited-time offer: X% off your next trip"
         |   Channel: Segment-preferred
         |   Content: Strong incentive, urgency
         |
Day 30:  [Message 5] "Last chance — exclusive offer expiring"
         |   Channel: All available channels
         |   Content: Final incentive
         |
Day 35:  [Evaluate]
         |   Converted? -> Back in active segment
         |   Not converted? -> Move to "dormant" list
         |   Annual re-attempt during festival seasons
```

### D. Referral Program by Segment

**Referral Program Design:**

| Segment | Referral Motivation | Referrer Reward | Referee Reward | Tracking Method | Research Needed |
|---------|--------------------|-----------------|---------------|-----------------|-----------------|
| **Budget Family** | Social currency (helped family/friends save) | INR 2,000 credit + next trip discount | INR 1,000 off first booking | Referral code + WhatsApp share link | Family referral rate? |
| **Luxury Honeymooner** | Exclusive access | Upgrade on next booking + complimentary experience | Welcome gift + priority service | Personalized referral link | Luxury referral rate? |
| **Corporate Exec** | Professional networking | Corporate account discount | First business trip at reduced rate | Corporate referral program | Corporate referral ROI? |
| **Pilgrim** | Community service (helped others with pilgrimage) | Group discount for next pilgrimage | First pilgrimage guidance + discount | Community referral code | Pilgrim referral chain length? |
| **Adventure** | Social sharing (brag-worthy trips) | Free activity add-on | Discount on first adventure trip | Social media share + code | Adventure referral conversion? |
| **NRI** | Helping family back home | Dual-currency reward (India credit + home country) | Special NRI welcome package | NRI referral program with dual reward | NRI referral value? |

**Referral Mechanics:**

```
+---------------------------------------------------+
|            REFERRAL FLOW                           |
+---------------------------------------------------+
|                                                     |
|  [Customer shares referral link/code]              |
|     |  Via WhatsApp, email, social media            |
|     v                                               |
|  [New prospect lands on agency]                    |
|     |  Referral code captured at first contact     |
|     v                                               |
|  [Prospect makes first inquiry]                    |
|     |  Referred-by tracked in CRM                  |
|     v                                               |
|  [Prospect books first trip]                       |
|     |  Referral conversion event                    |
|     v                                               |
|  [Both parties rewarded]                           |
|     |  Referrer: Credit applied to account         |
|     |  Referee: Discount applied to booking        |
|     v                                               |
|  [Referral metrics updated]                        |
|     |  Source, segment, conversion, revenue        |
|     v                                               |
|  [Referral chain tracking]                         |
|     |  Multi-hop attribution for viral loops       |
|                                                     |
+---------------------------------------------------+
```

### E. India-Specific Retention

**Festive Offer Strategy:**

| Festival | Offer Type | Segment Target | Example Offer | Research Needed |
|----------|-----------|---------------|---------------|-----------------|
| **Diwali** | Gift-voucher + discount | All | "Diwali gift card: INR 5,000 off your next family trip" | Diwali offer redemption rate? |
| **Summer** | Early-bird + EMI | BUD_FAM | "Book summer vacation by March — pay in 6 EMIs" | Summer booking conversion? |
| **Wedding season** | Honeymoon package + group discount | LUX_HNY, families | "Honeymoon special: Book within wedding season, get couples spa free" | Wedding season package uptake? |
| **Republic Day / Independence Day** | Patriotic tourism + discount | All domestic | "Explore India sale: 15% off domestic packages" | Patriotic offer resonance? |
| **Pongal / Makar Sankranti** | Regional packages | Regional segments | "South India temple tour — Pongal special" | Regional festival uptake? |

**Relationship-Based Retention (India Context):**

| Factor | Description | Agency Action | Research Needed |
|--------|-------------|---------------|-----------------|
| **Personal relationship** | Indian customers value personal rapport with their agent | Assign consistent agent per customer, remember family details | Agent-switching tolerance? |
| **Trust** | Trust built through reliability, honesty, and responsiveness | Transparent pricing, proactive communication during disruptions | Trust-to-loyalty correlation? |
| **Festival gifting** | Gift-giving culture during festivals | Agency sends festival greetings + small token (e-cards, discount vouchers) | Gifting ROI? |
| **Family occasions** | Birthdays, anniversaries, children's milestones | Personalized messages, milestone gifts (e.g., child's first trip) | Occasion message impact? |
| **Community** | Word-of-mouth is king in India | Invest in referral programs, community events, WhatsApp groups | Community-driven booking rate? |
| **Group dynamics** | Travel decisions often made in family/friend groups | Offer group discounts, multi-family packages, group coordination | Group size patterns? |

### F. Customer Success Metrics

**Retention KPIs by Segment:**

| Metric | Definition | Target (Example) | Segment Variation | Research Needed |
|--------|-----------|-------------------|-------------------|-----------------|
| **Repeat booking rate** | % who book 2+ trips within 12 months | 40% overall | Platinum: 80%, Bronze: 15% | Segment-specific targets? |
| **Net Promoter Score (NPS)** | Likelihood to recommend | > 50 overall | By segment | NPS by segment baseline? |
| **Customer lifetime value** | Predicted total spend | Segment-dependent | By value tier | CLV model accuracy? |
| **Churn rate** | % who stop booking annually | < 20% overall | By segment | Churn rate benchmark? |
| **Time between trips** | Average gap between bookings | < 6 months | By segment | Segment gap benchmarks? |
| **Referral rate** | % who refer new customers | > 15% | By segment | Referral rate by segment? |
| **Trip satisfaction (CSAT)** | Post-trip satisfaction score | > 4.5/5 | By segment | CSAT benchmarks? |
| **Service recovery score** | Satisfaction after issue resolution | > 4.0/5 | By segment | Recovery score benchmark? |

**Customer Health Score:**

```typescript
// Composite health score model

interface CustomerHealthScore {
  customerId: string;
  calculatedAt: Date;

  // Overall score (0-100)
  healthScore: number;
  healthCategory: HealthCategory;

  // Components
  engagementScore: number;      // 0-100 — communication interaction
  transactionScore: number;     // 0-100 — booking frequency and value
  satisfactionScore: number;    // 0-100 — CSAT, reviews, feedback
  loyaltyScore: number;         // 0-100 — tier, referrals, longevity
  riskScore: number;            // 0-100 — churn signals (inverted)

  // Trends
  trendDirection: 'improving' | 'stable' | 'declining';
  daysSinceLastTrip: number;
  daysUntilExpectedNextTrip: number;

  // Actions
  recommendedActions: RecommendedAction[];
}

type HealthCategory =
  | 'thriving'     // 80-100 — actively engaged, high-value
  | 'healthy'      // 60-79  — regular engagement, stable
  | 'watch'        // 40-59  — some risk signals
  | 'at_risk'      // 20-39  — significant churn signals
  | 'critical';    // 0-19   — imminent churn

interface RecommendedAction {
  actionId: string;
  type: ActionType;
  priority: 'high' | 'medium' | 'low';
  description: string;
  assignTo: 'agent' | 'system';
  deadline: Date;
}

type ActionType =
  | 'personal_call'
  | 'send_offer'
  | 'upgrade_tier'
  | 'service_recovery'
  | 'referral_request'
  | 're_engagement_sequence'
  | 'feedback_request'
  | 'anniversary_recognition';
```

**Agent Dashboard Metrics:**

```
+-----------------------------------------------------------+
|              RETENTION DASHBOARD                            |
+-----------------------------------------------------------+
|                                                             |
|  HEALTH OVERVIEW                                            |
|  +--------+--------+--------+--------+--------+           |
|  |Thrivng |Healthy | Watch  |At Risk |Critical|           |
|  |  35%   |  28%   |  18%   |  12%   |   7%   |           |
|  +--------+--------+--------+--------+--------+           |
|                                                             |
|  ALERTS                                                     |
|  +-----------------------------------------------------+  |
|  | ! Platinum customer "Sharma" — 180 days since trip  |  |
|  | ! 3 customers with unresolved complaints            |  |
|  | ! 8 customers in "declining" health trend            |  |
|  +-----------------------------------------------------+  |
|                                                             |
|  UPCOMING ACTIONS                                           |
|  +-----------------------------------------------------+  |
|  | [Today] Call Kapoor family — win-back attempt        |  |
|  | [Today] Send Diwali offers to Silver tier            |  |
|  | [Tomorrow] Follow up with Patel complaint resolution |  |
|  +-----------------------------------------------------+  |
|                                                             |
|  SEGMENT RETENTION                                          |
|  +-----------------------------------------------------+  |
|  | Platinum: 92% | Gold: 78% | Silver: 65% | Bronze: 45%|  |
|  +-----------------------------------------------------+  |
|                                                             |
+-----------------------------------------------------------+
```

---

## Data Model Sketch

```typescript
// Research-level model — not final

interface LoyaltyTier {
  tierId: string;
  agencyId: string;
  name: string;
  code: ValueTier;

  // Qualification
  minimumSpend?: number;      // INR/year
  minimumTrips?: number;      // trips/year
  qualificationPeriod: 'rolling_12_months' | 'calendar_year';

  // Benefits
  benefits: TierBenefit[];
  serviceModel: ServiceModel;
  responseSLA: number; // minutes

  // Retention
  retentionPlaybook: RetentionPlaybookId;
  churnThreshold: number; // days without booking before alert

  // Visual
  color: string;
  iconUrl?: string;
  displayPriority: number;
}

interface TierBenefit {
  benefitId: string;
  type: BenefitType;
  name: string;
  description: string;
  value?: number; // INR value of benefit
}

type BenefitType =
  | 'dedicated_agent'
  | 'priority_service'
  | 'lounge_access'
  | 'free_cancellation'
  | 'complimentary_upgrade'
  | 'discount_percentage'
  | 'emi_interest_free'
  | 'early_access'
  | 'exclusive_events'
  | 'birthday_bonus';

// --- Churn Prediction ---

interface ChurnPrediction {
  customerId: string;
  predictionDate: Date;

  // Result
  churnProbability: number; // 0-1
  churnRiskLevel: ChurnRiskLevel;
  estimatedChurnDate?: Date;

  // Model
  modelVersion: string;
  modelType: CLVModelType;
  confidence: number;

  // Contributing signals
  signals: ChurnSignal[];
  topSignalCategory: string;

  // Recommended actions
  recommendedInterventions: ChurnIntervention[];
}

type ChurnRiskLevel =
  | 'low'       // 0-0.2
  | 'medium'    // 0.2-0.4
  | 'high'      // 0.4-0.7
  | 'critical'; // 0.7-1.0

interface ChurnSignal {
  signalType: string;
  currentValue: any;
  baselineValue: any;
  deviation: number;    // How far from normal
  weight: number;       // Contribution to churn score
  detectedAt: Date;
  source: string;
}

interface ChurnIntervention {
  interventionId: string;
  type: ActionType;
  priority: 'immediate' | 'within_48h' | 'within_week' | 'within_month';
  description: string;
  estimatedImpact: number; // Expected reduction in churn probability
  estimatedCost: number;   // INR cost of intervention
  assignedTo?: string;     // Agent ID
}

// --- Win-Back Campaign ---

interface WinBackCampaign {
  campaignId: string;
  customerId: string;

  // Context
  previousSegment: string;
  previousTier: ValueTier;
  churnDate: Date;       // When they were classified as churned
  churnReason?: string;

  // Strategy
  strategy: WinBackStrategy;
  steps: WinBackStep[];

  // Status
  status: 'active' | 'won_back' | 'lost' | 'expired';
  startedAt: Date;
  completedAt?: Date;
  resultingBookingId?: string;
}

interface WinBackStrategy {
  strategyId: string;
  name: string;
  targetSegment: string;
  incentiveType: 'discount' | 'upgrade' | 'credit' | 'experience' | 'flexible_payment';
  incentiveValue: number;
  maxSteps: number;
  durationDays: number;
}

interface WinBackStep {
  stepId: string;
  order: number;
  delayDays: number;

  // Content
  channel: ChannelType;
  templateId: string;
  incentiveOffered?: string;

  // Outcome
  executedAt?: Date;
  customerResponse?: string;
  converted: boolean;
}

// --- Referral Program ---

interface ReferralProgram {
  programId: string;
  agencyId: string;
  name: string;

  // Configuration
  segmentRules: ReferralSegmentRule[];
  globalReward: ReferralReward;

  // Tracking
  totalReferrals: number;
  totalConversions: number;
  conversionRate: number;

  // Status
  active: boolean;
  startDate: Date;
  endDate?: Date;
}

interface ReferralSegmentRule {
  segmentCode: string;
  referrerReward: ReferralReward;
  refereeReward: ReferralReward;
  maxReferrals?: number; // per period
  doubleRewardPeriod?: TimeWindow; // e.g., festival season
}

interface ReferralReward {
  type: 'credit' | 'discount' | 'upgrade' | 'experience' | 'dual_currency';
  value: number;
  unit: 'INR' | 'percent' | 'points';
  expiryDays: number;
  description: string;
}

interface Referral {
  referralId: string;
  referrerCustomerId: string;
  referralCode: string;

  // Tracking
  channel: 'whatsapp' | 'email' | 'link' | 'code' | 'social';
  referredAt: Date;

  // Referee
  refereeCustomerId?: string;
  refereeName?: string;
  refereePhone?: string;

  // Conversion
  converted: boolean;
  convertedAt?: Date;
  bookingId?: string;
  bookingValue?: number;

  // Rewards
  referrerRewardClaimed: boolean;
  refereeRewardClaimed: boolean;

  // Chain
  sourceReferralId?: string; // Multi-hop tracking
  chainDepth: number;
}

// --- Retention Metrics ---

interface RetentionMetrics {
  agencyId: string;
  period: 'monthly' | 'quarterly' | 'yearly';
  date: Date;

  // Overall
  totalCustomers: number;
  repeatBookingRate: number;
  averageTimeBetweenTrips: number; // days
  churnRate: number;
  nps: number;

  // By segment
  bySegment: Record<string, SegmentRetentionMetrics>;

  // By tier
  byTier: Record<ValueTier, TierRetentionMetrics>;

  // Win-back
  winBackAttempted: number;
  winBackSuccessful: number;
  winBackRate: number;

  // Referral
  totalReferrals: number;
  referralConversionRate: number;
  referralRevenue: number;
}

interface SegmentRetentionMetrics {
  segmentCode: string;
  customerCount: number;
  repeatRate: number;
  averageCLV: number;
  churnRate: number;
  nps: number;
  averageHealthScore: number;
  topChurnSignal: string;
}

interface TierRetentionMetrics {
  tier: ValueTier;
  customerCount: number;
  retentionRate: number;
  upgradeRate: number;
  downgradeRate: number;
  averageRevenue: number;
}
```

---

## Open Problems

### 1. Churn Definition for Travel
**Challenge:** Travel is inherently episodic — is a customer who travels once a year really "churned" after 12 months?

**Options:**
- Segment-specific churn thresholds (pilgrim: 18 months, corporate: 6 months)
- Expected frequency-based definition (churned = 2x expected interval without booking)
- Engagement-based definition (churned = disengaged across all channels)
- Hybrid: frequency + engagement combined

**Research:** What is the right churn definition for each Indian travel persona?

### 2. Win-Back Cost vs. Benefit
**Challenge:** Win-back incentives can be expensive; not all churned customers are worth winning back

**Options:**
- CLV-based triage: only win-back customers with predicted future value > win-back cost
- Segment-based priority: win-back Platinum first, then Gold, etc.
- ROI scoring for each potential win-back
- Automated cost-benefit calculation

**Research:** What is the average win-back cost and subsequent CLV for recovered customers?

### 3. Referral Attribution in India
**Challenge:** Indian customers often refer via word-of-mouth, WhatsApp forwards, and informal channels that are hard to track

**Options:**
- Simple referral codes shared via WhatsApp
- Agent-assisted attribution (agent asks "how did you hear about us?")
- Phone number matching (new customer's phone matched to referrer's contacts)
- Referral code on printed materials for walk-in customers

**Research:** What percentage of referrals are currently unattributed?

### 4. Loyalty Tier Gamification
**Challenge:** Keeping customers engaged with tier progression without devaluing the program

**Options:**
- Points-based progression with tier milestones
- Surprise tier upgrades for exceptional engagement
- Tier matching with airline/hotel programs
- Tier benefits that increase in value without increasing cost (e.g., priority service)

**Research:** What gamification mechanics resonate with Indian travelers?

### 5. Cultural Sensitivity in Retention
**Challenge:** Some retention tactics (aggressive discounting, urgency messaging) may not suit all segments

**Options:**
- Segment-aware retention tone (respectful for pilgrims, exciting for adventure seekers)
- Cultural calendar awareness (no win-back during mourning periods, respectful during festivals)
- Relationship-first approach for segments that value personal connection

**Research:** Which retention tactics are culturally appropriate for each Indian segment?

### 6. Predicting Group Churn
**Challenge:** When one family member switches agencies, the whole family often follows

**Options:**
- Family-level churn prediction (not just individual)
- Group retention incentives (family discount, group loyalty tier)
- Early detection of group decision-maker switching signals

**Research:** How does group churn cascade in family travel?

---

## Next Steps

1. Define segment-specific churn thresholds based on historical data
2. Build customer health score calculation service
3. Design retention playbook for each loyalty tier
4. Create referral program mechanics and tracking
5. Build churn prediction model MVP (rule-based + logistic regression)
6. Design win-back campaign templates for each segment
7. Implement agent-facing retention dashboard
8. Plan festival-based retention calendar for next 12 months
9. Set up referral attribution tracking across channels
10. Benchmark retention metrics against industry standards

---

**Series:** [Customer Segmentation & Personalization](./SEGMENT_MASTER_INDEX.md)
**Previous:** [SEGMENT_03_COMMUNICATION.md](./SEGMENT_03_COMMUNICATION.md) — Segment-Based Communication
