# Agency Network & Franchise Management 03: Franchise Onboarding & Lifecycle

> Research document for new franchise/branch setup process, brand compliance enforcement, training and certification requirements, franchisee portal, royalty and fee management, compliance auditing, and franchise renewal/termination.

---

## Key Questions

1. **What is the end-to-end process for onboarding a new franchisee?**
2. **How is brand compliance enforced across independent franchisees?**
3. **What training and certification is required before a franchisee goes live?**
4. **What does the franchisee portal look like and what self-service capabilities does it offer?**
5. **How are royalties, fees, and financial obligations tracked and collected?**
6. **What does the compliance audit framework look like?**
7. **What triggers renewal, non-renewal, or termination of a franchise agreement?**

---

## Research Areas

### A. Franchise Onboarding Process

```typescript
interface FranchiseOnboarding {
  onboardingId: string;
  franchiseeId: string;
  franchisorId: string;
  stage: OnboardingStage;
  stages: OnboardingStageDetail[];
  timeline: OnboardingTimeline;
  checklist: OnboardingChecklist[];
  assignedCoach: string;                // Onboarding manager
  status: OnboardingStatus;
}

type OnboardingStage =
  | 'inquiry'                          // Initial franchise inquiry
  | 'qualification'                     // Financial and background check
  | 'agreement'                         // Legal agreement execution
  | 'setup'                             // Infrastructure and tech setup
  | 'training'                          // Agent and manager training
  | 'soft_launch'                       // Limited operations (trial period)
  | 'go_live'                           // Full operations
  | 'post_launch_support';              // First 90 days support

// Franchise onboarding journey:
//
// Week 1-2: INQUIRY & QUALIFICATION
// ┌────────────────────────────────────────────────────────┐
// │ 1. Franchise inquiry form (website / referral)         │
// │ 2. Initial call with franchisor BD team                │
// │ 3. Information packet sent (brochure, FDD, projections)│
// │ 4. Franchisee application form                         │
// │    - Personal details, financial capacity               │
// │    - Travel industry experience                        │
// │    - Proposed territory and premises                   │
// │    - Business plan (revenue targets, marketing)        │
// │ 5. Background verification                            │
// │    - Credit check (CIBIL score)                        │
// │    - Reference checks                                  │
// │    - Legal / criminal verification                     │
// │ 6. Qualification decision (approve / reject / hold)    │
// └────────────────────────────────────────────────────────┘
//
// Week 3-4: AGREEMENT & LEGAL
// ┌────────────────────────────────────────────────────────┐
// │ 7. Franchise Disclosure Document (FDD) review          │
// │    - Business model, fees, obligations                 │
// │    - Financial performance representations             │
// │    - List of existing franchisees (for reference)      │
// │    - Litigation history                                │
// │ 8. Territory mapping and exclusivity agreement         │
// │ 9. Franchise agreement execution                       │
// │    - Franchise fee payment: ₹5,00,000                 │
// │    - Security deposit: ₹2,00,000                      │
// │    - Agreement signing (digital + physical)            │
// │ 10. Legal entity setup support                         │
// │    - GST registration (new entity)                     │
// │    - Shop & Establishment license                     │
// │    - Trade license (municipal)                         │
// │    - PAN / TAN registration                            │
// │    - Bank account opening (current account)            │
// └────────────────────────────────────────────────────────┘
//
// Week 5-8: SETUP & TRAINING
// ┌────────────────────────────────────────────────────────┐
// │ 11. Platform account provisioning                      │
// │    - Tenant setup with franchisee config               │
// │    - Brand theme applied                               │
// │    - Territory boundaries configured                   │
// │    - Supplier contract access provisioned              │
// │ 12. Office setup guidance                              │
// │    - Interior design guidelines (brand compliance)     │
// │    - Technology setup (computers, printers, internet)  │
// │    - Signage and branding materials                    │
// │ 13. Team hiring support                                │
// │    - Job descriptions for agents                       │
// │    - Interview guidelines                              │
// │    - Background verification templates                 │
// │ 14. Training program (4 weeks)                         │
// │    - Week 1: Platform training (hands-on)              │
// │    - Week 2: Supplier and product training             │
// │    - Week 3: Customer service and sales training       │
// │    - Week 4: Shadowing at existing branch              │
// │ 15. IATA sub-agent registration (if applicable)        │
// │    - Application through franchisor's IATA accreditation│
// │    - BSP billing setup                                 │
// │    - GDS access provisioned                            │
// └────────────────────────────────────────────────────────┘
//
// Week 9-12: SOFT LAUNCH & GO LIVE
// ┌────────────────────────────────────────────────────────┐
// │ 16. Soft launch (first 2 weeks)                        │
// │    - Limited customer intake (friends, family, referrals)│
// │    - Coach reviews every trip for quality              │
// │    - Daily standup with onboarding manager             │
// │    - Issue tracking and rapid resolution               │
// │ 17. Go-live certification                              │
// │    - Platform proficiency test (score > 80%)           │
// │    - Brand compliance walkthrough (score > 90%)        │
// │    - Financial processes verification                  │
// │    - Emergency procedures test                         │
// │ 18. Full launch                                        │
// │    - Territory marketing activation                    │
// │    - Lead routing from national campaigns              │
// │    - Customer portal live with local branch page       │
// │    - Monitoring enters regular cadence                 │
// └────────────────────────────────────────────────────────┘

interface OnboardingChecklist {
  itemId: string;
  category: string;
  task: string;
  requiredBy: 'go_live' | 'week_4' | 'week_8' | 'soft_launch';
  status: 'pending' | 'in_progress' | 'completed' | 'waived';
  assignee: string;
  evidence?: string;                    // Document / screenshot link
  verifiedBy?: string;
  verifiedDate?: Date;
}
```

### B. Brand Compliance Enforcement

```typescript
interface BrandCompliance {
  franchiseeId: string;
  overallScore: number;                 // 0-100
  categories: ComplianceCategory[];
  audits: ComplianceAudit[];
  violations: ComplianceViolation[];
  improvementPlan?: ImprovementPlan;
}

interface ComplianceCategory {
  category: string;
  weight: number;                       // Percentage weight in overall score
  score: number;                        // 0-100
  items: ComplianceItem[];
}

interface ComplianceItem {
  itemId: string;
  requirement: string;
  assessment: 'pass' | 'fail' | 'partial' | 'not_assessed';
  evidence: string;
  lastChecked: Date;
  severity: 'critical' | 'major' | 'minor';
}

// Brand compliance categories and weights:
//
// ┌──────────────────────────┬────────┬──────────────────────────────┐
// │ Category                 │ Weight │ Key Checks                    │
// ├──────────────────────────┼────────┼──────────────────────────────┤
// │ Visual Identity          │  20%   │ Logo usage, colors, fonts,    │
// │                          │        │ signage, office branding      │
// ├──────────────────────────┼────────┼──────────────────────────────┤
// │ Communication Standards  │  20%   │ Email templates, WhatsApp     │
// │                          │        │ messages, phone greetings     │
// ├──────────────────────────┼────────┼──────────────────────────────┤
// │ Document Quality         │  15%   │ Itinerary format, invoice     │
// │                          │        │ layout, quotation standards   │
// ├──────────────────────────┼────────┼──────────────────────────────┤
// │ Service Standards        │  20%   │ Response time SLA, customer   │
// │                          │        │ │ greeting, follow-up cadence │
// ├──────────────────────────┼────────┼──────────────────────────────┤
// │ Pricing Compliance       │  10%   │ Markup within approved range, │
// │                          │        │ │ no unauthorized discounting │
// ├──────────────────────────┼────────┼──────────────────────────────┤
// │ Technology Usage         │  10%   │ Platform adoption, data entry │
// │                          │        │ │ quality, mandatory fields   │
// ├──────────────────────────┼────────┼──────────────────────────────┤
// │ Regulatory Compliance    │   5%   │ GST filing, license currency, │
// │                          │        │ │ consumer protection display │
// └──────────────────────────┴────────┴──────────────────────────────┘
//
// Scoring:
//   90-100: Excellent — Full compliance, eligible for awards
//   75-89:  Good — Minor improvements needed
//   60-74:  Needs Improvement — Remediation plan required
//   40-59:  Poor — Formal warning, intensified audits
//   <40:    Critical — Suspension risk, immediate intervention

interface ComplianceViolation {
  violationId: string;
  franchiseeId: string;
  category: string;
  severity: 'critical' | 'major' | 'minor';
  description: string;
  detectedDate: Date;
  detectedBy: 'audit' | 'automated' | 'customer_complaint' | 'mystery_shopper';
  remediationDeadline: Date;
  status: 'open' | 'remediation_in_progress' | 'resolved' | 'escalated';
  penalty?: CompliancePenalty;
}

interface CompliancePenalty {
  type: 'warning' | 'fine' | 'training_mandatory' | 'suspension' | 'termination';
  amount?: Money;                       // Fine amount
  description: string;
}

// Automated compliance checks (platform-enforced):
//
// PLATFORM-ENFORCED (cannot violate):
// - Email templates: Locked, cannot edit without franchisor approval
// - Invoice format: Auto-generated, brand-compliant
// - Itinerary design: Template-based, brand colors auto-applied
// - Customer communication: Approved templates with variable fields
// - Pricing floor: Cannot markup below minimum margin
//
// AUDIT-ENFORCED (checked periodically):
// - Office signage and branding
// - Agent greeting and phone manner
// - Response time to customer inquiries
// - Document delivery quality
// - Social media content compliance
//
// SELF-REPORTED (franchisee attests, spot-checked):
// - Staff dress code adherence
// - Office cleanliness and maintenance
// - Customer feedback review process
// - Emergency procedures posted
```

### C. Training & Certification

```typescript
interface TrainingProgram {
  programId: string;
  franchiseeId: string;
  participants: TrainingParticipant[];
  modules: TrainingModule[];
  schedule: TrainingSchedule;
  certifications: Certification[];
  status: TrainingStatus;
}

interface TrainingModule {
  moduleId: string;
  title: string;
  category: TrainingCategory;
  duration: string;                     // "4 hours", "2 days"
  format: TrainingFormat;
  mandatory: boolean;
  assessmentRequired: boolean;
  passingScore: number;                 // Percentage
}

type TrainingCategory =
  | 'platform_usage'                    // How to use the platform
  | 'product_knowledge'                 // Destinations, suppliers, packages
  | 'sales_techniques'                  // Consultative selling, upselling
  | 'customer_service'                  // Communication, complaint handling
  | 'compliance'                        // GST, IATA, consumer protection
  | 'operations'                        // Booking flow, document delivery
  | 'emergency'                         // Crisis management, safety protocols
  | 'leadership';                       // Branch management, team building

type TrainingFormat =
  | 'e_learning'                        // Self-paced online modules
  | 'live_virtual'                      // Live video training session
  | 'in_person'                         // On-site at HQ or branch
  | 'shadowing'                         // Follow experienced agent
  | 'simulation'                        // Platform sandbox with test scenarios
  | 'assessment';                       // Test / certification exam

// Training curriculum for new franchisee:
//
// MODULE          │ FORMAT     │ DURATION │ ASSESSMENT
// ────────────────┼────────────┼──────────┼───────────
// Platform 101    │ E-learning │ 8 hours  │ Quiz (80%)
// Platform 201    │ Simulation │ 4 hours  │ Practical
// Destination     │ E-learning │ 12 hours │ Quiz (75%)
//   Knowledge     │            │          │
// Supplier        │ Live virt. │ 4 hours  │ Quiz (80%)
//   Integration   │            │          │
// Sales Process   │ In-person  │ 8 hours  │ Role play
// Customer        │ E-learning │ 4 hours  │ Quiz (85%)
//   Service       │            │          │
// GST & Tax       │ E-learning │ 2 hours  │ Quiz (90%)
// IATA Ticketing  │ Live virt. │ 8 hours  │ Practical
// Emergency       │ In-person  │ 4 hours  │ Drill
//   Procedures    │            │          │
// Branch          │ Shadowing  │ 40 hours │ Observation
//   Operations    │ (1 week)   │          │
// ────────────────┴────────────┴──────────┴───────────
// Total: ~94 hours (approximately 2.5 weeks)

interface Certification {
  certificationId: string;
  agentId: string;
  module: string;
  score: number;
  certifiedDate: Date;
  expiryDate: Date;                     // Annual recertification
  status: 'active' | 'expired' | 'suspended';
}
```

### D. Franchisee Portal

```typescript
interface FranchiseePortal {
  franchiseeId: string;
  sections: PortalSection[];
  selfService: SelfServiceCapabilities;
}

type PortalSection =
  | 'dashboard'                         // Overview: KPIs, alerts, tasks
  | 'financials'                        // P&L, royalties, invoices
  | 'operations'                        // Trips, agents, inventory
  | 'compliance'                        // Audit scores, violations, training
  | 'support'                           // Help desk, knowledge base, tickets
  | 'communication'                     // HQ messages, network updates
  | 'resources'                         // Brand assets, templates, guidelines
  | 'agreement'                         // Franchise agreement, terms, renewals
  | 'training';                         // Training modules, certifications

// Franchisee portal dashboard (ASCII mockup):
//
// ┌───────────────────────────────────────────────────────────┐
// │ TRAVELEASE FRANCHISE PORTAL                    Pune       │
// ├───────────────────────────────────────────────────────────┤
// │                                                          │
// │ ┌─── Quick Stats ──────────────────────────────────────┐ │
// │ │ Revenue (MTD): ₹18.5L  │ Trips: 87  │ Agents: 4     │ │
// │ │ Royalty Due: ₹1.11L    │ CSAT: 4.3  │ Compliance: 94│ │
// │ └───────────────────────────────────────────────────────┘ │
// │                                                          │
// │ ┌─── Action Items ─────────────────────────────────────┐ │
// │ │ □ Royalty payment due: Nov 30 (₹1,11,000)           │ │
// │ │ □ Agent training: Sunil — Destination quiz overdue  │ │
// │ │ □ Compliance audit: Scheduled Dec 15                │ │
// │ │ □ GST filing: GSTR-3B due Dec 20                    │ │
// │ └───────────────────────────────────────────────────────┘ │
// │                                                          │
// │ ┌─── HQ Updates ───────────────────────────────────────┐ │
// │ │ 📢 New Goa hotel contract — 15% better rates         │ │
// │ │ 📢 Diwali campaign materials available for download  │ │
// │ │ 📢 Platform update v3.2 — New itinerary builder      │ │
// │ └───────────────────────────────────────────────────────┘ │
// │                                                          │
// │ ┌─── Performance Trend ────────────────────────────────┐ │
// │ │ Revenue:  ████████████████░░░░  84% of target        │ │
// │ │ Trips:    ██████████████░░░░░░  78% of target        │ │
// │ │ Margin:   ██████████████████░░  92% of target        │ │
// │ └───────────────────────────────────────────────────────┘ │
// └───────────────────────────────────────────────────────────┘

interface SelfServiceCapabilities {
  downloadBrandAssets: boolean;         // Logos, templates, guidelines
  submitSupportTicket: boolean;         // Raise issues to franchisor
  viewAgreement: boolean;               // Read franchise agreement
  requestTerritoryChange: boolean;      // Request territory modification
  requestInventoryTransfer: boolean;     // Request shared inventory
  downloadReports: boolean;             // Financial and operational reports
  manageAgentTraining: boolean;         // Assign training to agents
  viewInvoices: boolean;                // Royalty and fee invoices
  disputeCharge: boolean;               // Dispute a royalty calculation
}
```

### E. Royalty & Fee Management

```typescript
interface RoyaltyManagement {
  franchiseeId: string;
  agreement: FranchiseAgreement;
  billing: RoyaltyBilling[];
  payments: RoyaltyPayment[];
  disputes: RoyaltyDispute[];
  statements: MonthlyStatement[];
}

interface RoyaltyBilling {
  billingId: string;
  franchiseeId: string;
  period: BillingPeriod;
  lineItems: BillingLineItem[];
  totalDue: Money;
  dueDate: Date;
  status: BillingStatus;
}

type BillingStatus =
  | 'draft'
  | 'issued'
  | 'paid'
  | 'partially_paid'
  | 'overdue'
  | 'disputed';

interface BillingLineItem {
  type: FeeType;
  description: string;
  calculation: string;                  // "Revenue ₹18.5L × 6% = ₹1,11,000"
  amount: Money;
  gst: Money;                          // GST on royalty (18%)
  total: Money;
}

type FeeType =
  | 'royalty'                           // Revenue-based royalty
  | 'technology_fee'                    // Platform usage
  | 'marketing_fund'                    // National marketing contribution
  | 'training_fee'                      // Training and certification
  | 'minimum_guarantee_shortfall'       // If royalty below minimum
  | 'late_fee'                          // Penalty for late payment
  | 'audit_fee';                        // Compliance audit cost share

// Monthly royalty statement example:
//
// ┌──────────────────────────────────────────────────────────┐
// │ TRAVELEASE INDIA — ROYALTY STATEMENT                     │
// │ Franchisee: TravelEase Pune (PVT-001)                    │
// │ Period: November 2026                                    │
// ├──────────────────────────────────────────────────────────┤
// │                                                          │
// │ REVENUE BASIS:                          ₹ 18,50,000      │
// │ (Net revenue per franchise agreement definition)          │
// │                                                          │
// │ LINE ITEMS:                              ₹                │
// │                                                          │
// │ Royalty (6% of ₹18.5L)                 ₹ 1,11,000       │
// │ Technology fee (monthly)                  ₹   15,000      │
// │ Marketing fund (2% of ₹18.5L)            ₹   37,000      │
// │ Minimum guarantee shortfall              ₹        0       │
// │ (Min. guarantee ₹40K vs royalty ₹1.11L — No shortfall)  │
// │                                                          │
// │ SUBTOTAL                                 ₹ 1,63,000      │
// │ GST (18%)                                ₹   29,340      │
// │                                                          │
// │ TOTAL DUE                                ₹ 1,92,340      │
// │                                                          │
// │ DUE DATE: November 30, 2026                             │
// │ Payment method: Auto-debit (NACH mandate)                │
// │                                                          │
// │ ADJUSTMENTS:                                             │
// │ Performance bonus (Oct overachievement)   ₹  -8,500      │
// │ Late fee (Oct payment 3 days late)        ₹   2,000      │
// │                                                          │
// │ NET PAYABLE                              ₹ 1,85,840      │
// └──────────────────────────────────────────────────────────┘
//
// Payment collection methods:
// 1. NACH mandate (auto-debit) — Preferred, mandated in agreement
// 2. NEFT/RTGS — Manual transfer before due date
// 3. UPI — For smaller amounts (training fees, late fees)
// 4. Cheque — Legacy, discouraged (clearance delay)

// RBI compliance for franchise fee collection:
// - NACH mandate: Registered with franchisee's bank
// - Maximum debit: As per agreement (no variable auto-debit beyond stated terms)
// - Dispute window: Franchisee can dispute within 7 days of debit
// - Refund timeline: T+3 business days for disputed debits
// - TDS: Franchisor must deduct TDS on training fees paid to external trainers
//   Franchisee must deduct TDS (10% u/s 194J) on royalty paid to franchisor
```

### F. Compliance Audit Framework

```typescript
interface ComplianceAudit {
  auditId: string;
  franchiseeId: string;
  auditType: AuditType;
  auditor: AuditorDetail;
  schedule: AuditSchedule;
  scope: AuditScope;
  findings: AuditFinding[];
  score: number;                        // 0-100
  status: AuditStatus;
}

type AuditType =
  | 'scheduled_quarterly'               // Quarterly routine audit
  | 'annual_comprehensive'              // Full annual review
  | 'mystery_shopper'                   // Anonymous customer experience test
  | 'triggered'                         // Triggered by complaint or KPI drop
  | 'pre_renewal'                       // Before agreement renewal
  | 'follow_up';                        // Follow-up after previous findings

// Audit calendar example:
//
// ┌──────────────────┬───────────┬──────────────────────────────┐
// │ Quarter          │ Type      │ Focus Areas                   │
// ├──────────────────┼───────────┼──────────────────────────────┤
// │ Q1 (Apr-Jun)     │ Scheduled │ Brand compliance, training    │
// │                  │           │ status, document quality      │
// ├──────────────────┼───────────┼──────────────────────────────┤
// │ Q2 (Jul-Sep)     │ Mystery   │ Customer experience, phone    │
// │                  │ Shopper   │ greeting, response time       │
// ├──────────────────┼───────────┼──────────────────────────────┤
// │ Q3 (Oct-Dec)     │ Scheduled │ Financial compliance, GST     │
// │                  │           │ filing, pricing adherence     │
// ├──────────────────┼───────────┼──────────────────────────────┤
// │ Q4 (Jan-Mar)     │ Annual    │ Comprehensive all-area audit  │
// │                  │ Review    │ + pre-renewal assessment      │
// └──────────────────┴───────────┴──────────────────────────────┘

interface AuditFinding {
  findingId: string;
  category: string;
  severity: 'critical' | 'major' | 'minor' | 'observation';
  description: string;
  evidence: string;                     // Photo, document, screenshot
  remediation: string;                  // What needs to be fixed
  remediationDeadline: Date;
  status: 'open' | 'in_progress' | 'resolved' | 'overdue';
}
```

### G. Franchise Renewal & Termination

```typescript
interface FranchiseRenewal {
  renewalId: string;
  agreementId: string;
  currentTerm: AgreementTerm;
  renewalAssessment: RenewalAssessment;
  decision: RenewalDecision;
  newTerms?: AgreementTerm;
}

interface RenewalAssessment {
  financialPerformance: number;         // 0-100 score
  complianceScore: number;              // 0-100
  customerSatisfaction: number;         // 1-5
  brandCompliance: number;              // 0-100
  royaltyPaymentTimeliness: number;     // Percentage on-time
  growthTrajectory: number;             // Revenue trend score
  overallRecommendation: 'renew' | 'renew_with_conditions' | 'non_renew';
  conditions?: string[];                // Conditions for conditional renewal
}

type RenewalDecision =
  | 'auto_renewed'                      // Met all criteria, auto-renewed
  | 'renewed_with_conditions'           // Renewed with remediation conditions
  | 'renewed_with_modified_terms'       // Renewed but terms changed (royalty, territory)
  | 'non_renewed_mutual'                // Both parties agree not to renew
  | 'non_renewed_franchisor'            // Franchisor decides not to renew
  | 'non_renewed_franchisee';           // Franchisee decides not to renew

// Termination triggers:
//
// IMMEDIATE TERMINATION (Breach):
// - Brand fraud (using brand for unauthorized services)
// - Financial fraud (misreporting revenue, GST evasion)
// - Safety violation (endangering customers)
// - Criminal activity at franchise location
// - Operating outside territory without authorization
//
// TERMINATION WITH NOTICE (Performance):
// - Consistent compliance score < 40 for 2 consecutive quarters
// - Royalty payment default > 60 days
// - Customer satisfaction < 2.5/5 for 3 consecutive months
// - Revenue < 50% of minimum guarantee for 6 consecutive months
// - Failed remediation plan after formal warning
//
// MUTUAL TERMINATION:
// - Franchisee wants to exit (business reasons)
// - Territorial realignment (franchisor restructuring)
// - Acquisition (franchisor buys back successful franchise)
// - Retirement / succession failure
//
// Termination process:
// 1. Notice period (3-6 months per agreement)
// 2. Customer migration plan (transfer active trips to HQ/other branch)
// 3. Financial settlement (deposits, pending royalties, adjustments)
// 4. Brand de-commissioning (signage removal, digital asset revocation)
// 5. Non-compete enforcement (12 months per agreement)
// 6. Data handover (customer data per agreement terms and DPDP Act)
// 7. Platform access revocation (phased over notice period)
```

---

## Open Problems

### 1. Automated Compliance Monitoring
Manual audits are expensive and infrequent. Need automated compliance checks: platform-embedded email template enforcement, automated response time tracking, AI-powered document quality scoring, and image-based office branding verification.

### 2. Fair Pre-Renewal Assessment
Renewal decisions affect livelihoods. The assessment must be transparent, data-driven, and appeal-able. Franchisees who invest in a territory for 5 years should not face surprise non-renewal. Need a scoring rubric that franchisees can see and self-assess against year-round.

### 3. Smooth Customer Migration on Termination
When a franchise terminates, active trips (some with customers mid-trip) need seamless handling. The customer should not experience disruption. This requires real-time trip reassignment, agent reassignment, and communication continuity planning.

### 4. Royalty Calculation Disputes
Revenue definition disagreements are the #1 franchise dispute globally. "What counts as revenue?" differs by interpretation (gross vs. net, including GST or not, including cancelled bookings). The platform must have a transparent, auditable royalty calculation that both parties can verify.

### 5. Non-Compete Enforcement
Indian courts have limited non-compete enforcement post-employment/contract. A departing franchisee who opens an independent agency in the same territory is hard to prevent. Platform-level protection (data portability restrictions, customer data ownership clauses) is the practical enforcement mechanism.

---

## Next Steps

1. **Build franchisee onboarding wizard** — Multi-step guided setup in the platform that covers legal, technical, and training milestones with progress tracking
2. **Design automated compliance engine** — Platform-level checks that enforce brand standards automatically (locked templates, pricing floors, response time monitoring)
3. **Prototype royalty billing engine** — Extend the existing finance module to support franchise-specific billing cycles, minimum guarantees, and automated NACH collection
4. **Create renewal assessment dashboard** — Visual scoring rubric showing franchisee where they stand against renewal criteria at any point in the agreement term
5. **Design termination playbook UI** — Step-by-step workflow for managing franchise termination including customer migration, financial settlement, and brand de-commissioning
6. **Research Indian franchise law cases** — Study landmark franchise termination cases in India to understand legal precedent for non-compete, territory disputes, and data ownership

---

**Series:** Agency Network & Franchise Management
**Document:** 3 of 4 (Franchise Onboarding & Lifecycle)
**Last Updated:** 2026-04-28
**Status:** Research Exploration
