# Multi-Brand & White Label — Reseller & Partner Network

> Research document for reseller programs, partner management, and multi-tier distribution.

---

## Key Questions

1. **How do we enable a reseller/partner network?**
2. **What's the revenue sharing model for resellers?**
3. **How do we manage partner performance and compliance?**
4. **What's the partner onboarding workflow?**
5. **How do we handle multi-tier distribution (platform → master partner → sub-partner)?**

---

## Research Areas

### Reseller Model

```typescript
interface ResellerConfig {
  resellerId: string;
  resellerType: ResellerType;
  parentReseller?: string;           // For sub-partners
  agencyId: string;
  branding: WhiteLabelConfig;
  revenueShare: RevenueShareConfig;
  limits: ResellerLimits;
  compliance: ResellerCompliance;
  onboarding: ResellerOnboarding;
}

type ResellerType =
  | 'direct'                         // Agency uses platform directly
  | 'reseller'                       // Resells platform to sub-agencies
  | 'master_partner'                 // Manages multiple resellers
  | 'technology_partner'             // Integrates platform into their product
  | 'referral';                      // Refers customers, earns commission

interface RevenueShareConfig {
  model: RevenueModel;
  split: RevenueSplit;
  paymentTerms: string;
  minimumPayout: Money;
}

type RevenueModel =
  | 'revenue_share'                   // % of platform fee
  | 'per_seat'                        // Fixed amount per agent seat
  | 'per_trip'                        // Fixed amount per completed trip
  | 'markup'                          // Reseller sets own pricing
  | 'tiered';                         // Volume-based pricing

interface RevenueSplit {
  platformPercent: number;
  resellerPercent: number;
  subResellerPercent?: number;
}

// Revenue sharing examples:
// Direct agency: Platform takes 100% of subscription fee
// Reseller: Platform 70%, Reseller 30% of subscription
// Master partner: Platform 60%, Master 20%, Sub-partner 20%
// Referral: Platform 95%, Referrer 5% (first year only)

// Markup model:
// Platform charges reseller ₹10,000/month
// Reseller charges sub-agency ₹15,000/month
// Reseller keeps ₹5,000 margin
// Platform doesn't control reseller pricing
```

### Partner Management

```typescript
interface PartnerNetwork {
  partners: Partner[];
  hierarchy: PartnerHierarchy;
  performance: PartnerPerformance[];
}

interface PartnerHierarchy {
  partnerId: string;
  level: number;
  parent?: string;
  children: string[];
  totalNetworkSize: number;
}

// Hierarchy examples:
// Platform (Level 0)
//   → Master Partner A (Level 1) — Manages North India
//     → Reseller 1 (Level 2) — Delhi region
//       → Agency 1 (Level 3) — 5 agents
//       → Agency 2 (Level 3) — 12 agents
//     → Reseller 2 (Level 2) — Punjab region
//       → Agency 3 (Level 3) — 8 agents
//   → Master Partner B (Level 1) — Manages South India
//     → Reseller 3 (Level 2) — Karnataka
//     → Reseller 4 (Level 2) — Tamil Nadu

interface PartnerPerformance {
  partnerId: string;
  metrics: PartnerMetric[];
  tier: PartnerTier;
  compliance: ComplianceStatus;
}

type PartnerTier =
  | 'silver'                          // 1-10 sub-agencies
  | 'gold'                            // 11-50 sub-agencies
  | 'platinum';                       // 50+ sub-agencies

interface PartnerMetric {
  metric: string;
  value: number;
  target: number;
  trend: 'up' | 'down' | 'stable';
}

// Partner KPIs:
// Sub-agencies onboarded
// Active sub-agencies (retention)
// Total trips processed across network
// Revenue generated
// Support ticket rate (lower = better)
// Compliance score
// Customer NPS across network
```

### Partner Onboarding

```typescript
interface PartnerOnboarding {
  partnerId: string;
  type: ResellerType;
  steps: PartnerOnboardingStep[];
  training: PartnerTraining[];
  complianceChecks: ComplianceCheck[];
  goLiveCriteria: GoLiveCriteria[];
}

// Partner onboarding (4-6 weeks):
// Week 1: Agreement & Setup
//   - Sign partnership agreement
//   - Revenue share terms agreed
//   - Brand assets provided
//   - Custom domain configured
//   - Test environment provisioned
//
// Week 2: Training
//   - Platform training (2 days)
//   - Admin panel training (1 day)
//   - Integration setup training (1 day)
//   - Sales playbook for selling the platform (1 day)
//
// Week 3: Configuration
//   - Brand theming applied
//   - Integration credentials configured
//   - Pricing and commission structure set
//   - Support channels configured
//
// Week 4: Testing
//   - End-to-end booking test
//   - Payment processing test
//   - Document generation test
//   - Customer portal test
//
// Week 5-6: Soft Launch
//   - Onboard first 3-5 agencies
//   - Monitor closely
//   - Iterate based on feedback
//
// Go-live criteria:
//   [ ] All training modules completed
//   [ ] Brand assets approved
//   [ ] End-to-end test passed
//   [ ] Compliance checks passed
//   [ ] Support escalation path defined
//   [ ] Billing setup confirmed
```

---

## Open Problems

1. **Revenue reconciliation** — Tracking revenue across 3 tiers (platform → master → reseller → agency) is complex. Each party needs transparent reporting.

2. **Support responsibility** — When an agency has an issue, who supports them? Platform or reseller? Need clear SLA boundaries.

3. **Data ownership** — The agency's customer data belongs to the agency, but the reseller manages the account. Who accesses what?

4. **Compliance liability** — A sub-agency violates GST regulations. Who's liable — the agency, reseller, master partner, or platform?

5. **Churn cascading** — A master partner churns. Their 50 sub-agencies are suddenly orphaned. Need continuity planning.

---

## Next Steps

- [ ] Design reseller hierarchy model with revenue sharing
- [ ] Build partner performance dashboard
- [ ] Create partner onboarding workflow with training
- [ ] Design revenue reconciliation and reporting per tier
- [ ] Study partner networks (Shopify Partners, HubSpot Solutions Partner, AWS Partner Network)
