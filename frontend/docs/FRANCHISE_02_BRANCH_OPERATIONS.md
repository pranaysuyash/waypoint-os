# Agency Network & Franchise Management 02: Branch Operations

> Research document for branch-level operations, independent P&L management, inter-branch trip transfers, branch performance metrics, resource sharing, and branch communication protocols.

---

## Key Questions

1. **How does each branch operate with independent P&L while sharing network resources?**
2. **What happens when a trip needs to transfer between branches mid-lifecycle?**
3. **What performance metrics differentiate high-performing branches from struggling ones?**
4. **How are agents, inventory, and supplier contracts shared across branches?**
5. **What communication protocols keep branches aligned without creating bottlenecks?**
6. **How do branch operations differ between corporate-owned and franchised locations?**

---

## Research Areas

### A. Branch Operational Model

```typescript
interface BranchOperations {
  branchId: string;
  networkId: string;
  branchType: BranchType;
  staffing: BranchStaffing;
  financials: BranchFinancials;
  inventory: BranchInventory;
  operatingHours: OperatingSchedule;
  capabilities: BranchCapability[];
}

type BranchType =
  | 'headquarters'                     // Main office, full capabilities
  | 'full_service_branch'              // Corporate branch, all services
  | 'franchise_branch'                 // Franchised location
  | 'satellite_office'                 // Small office / counter
  | 'home_office'                      // Agent working from home
  | 'airport_counter'                  // Airport / railway station counter
  | 'kiosk';                           // Mall / exhibition kiosk

// Branch operational capabilities matrix:
//
// ┌───────────────────────┬──────┬──────┬──────┬──────┬──────┬──────┐
// │ Capability            │  HQ  │ Full │ Fran.│ Sat. │ Home │ Kiosk│
// ├───────────────────────┼──────┼──────┼──────┼──────┼──────┼──────┤
// │ Flight ticketing      │  Y   │  Y   │  Y   │  L   │  Y   │  N   │
// │ Hotel booking         │  Y   │  Y   │  Y   │  Y   │  Y   │  N   │
// │ Visa processing       │  Y   │  Y   │  Y   │  N   │  L   │  N   │
// │ Forex services        │  Y   │  Y   │  L   │  N   │  N   │  N   │
// │ Group tours           │  Y   │  Y   │  Y   │  N   │  L   │  N   │
// │ Corporate travel      │  Y   │  Y   │  L   │  N   │  N   │  N   │
// │ Customer walk-ins     │  Y   │  Y   │  Y   │  Y   │  N   │  L   │
// │ Cash handling         │  Y   │  Y   │  Y   │  L   │  N   │  N   │
// │ Supplier negotiation  │  Y   │  L   │  L   │  N   │  N   │  N   │
// │ IATA ticketing        │  Y   │  Y   │  L   │  N   │  L   │  N   │
// │ Insurance issuance    │  Y   │  Y   │  Y   │  Y   │  Y   │  N   │
// │ Document delivery     │  Y   │  Y   │  Y   │  N   │  N   │  N   │
// └───────────────────────┴──────┴──────┴──────┴──────┴──────┴──────┘
// Y = Yes, L = Limited, N = No
```

### B. Independent P&L Per Branch

```typescript
interface BranchFinancials {
  branchId: string;
  period: FinancialPeriod;
  revenue: BranchRevenue;
  costs: BranchCosts;
  allocations: CorporateAllocations;
  interBranch: InterBranchTransactions;
  profitability: BranchProfitability;
}

interface BranchRevenue {
  tripRevenue: Money;                   // Revenue from trips booked at branch
  serviceFees: Money;                   // Visa, forex, insurance commissions
  ancillaryIncome: Money;               // Travel accessories, SIM cards
  referralIncome: Money;                // Commission from referrals to other branches
  corporateOverride: Money;             // Manager/team lead override commission
  totalRevenue: Money;
}

interface BranchCosts {
  // Direct costs
  supplierPayments: Money;              // Hotels, flights, activities
  gstPaid: Money;                       // GST on services
  commissionPaid: Money;                // Agent commissions
  documentCosts: Money;                 // Printing, courier, visa fees

  // Operating costs
  rent: Money;                          // Office rent
  utilities: Money;                     // Internet, phone, electricity
  salaries: Money;                      // Staff salaries
  marketing: Money;                     // Local marketing spend

  // Network costs (if franchise)
  royaltyPaid: Money;                   // Royalty to franchisor
  marketingFund: Money;                 // National marketing contribution
  technologyFee: Money;                 // Platform usage fee
  trainingCost: Money;                  // Training and certification fees

  totalCosts: Money;
}

interface CorporateAllocations {
  // Costs allocated from HQ to branch
  sharedSupplierContracts: Money;       // Pro-rata share of supplier deals
  nationalMarketingShare: Money;        // Share of national campaigns
  technologyPlatformShare: Money;       // IT infrastructure allocation
  insurancePremiumShare: Money;         // Professional indemnity insurance
  auditFeeShare: Money;                 // Annual audit cost allocation
}

// Branch P&L example:
//
// TravelEase Pune Branch — November 2026
// ┌──────────────────────────────────────────────────┐
// │ REVENUE                              ₹           │
// │   Trip revenue (net of GST)        18,50,000     │
// │   Service fees (visa, forex)        1,20,000     │
// │   Insurance commission                 45,000     │
// │   Referral income (Mumbai branch)      15,000     │
// │   Total Revenue                    20,30,000     │
// │                                                  │
// │ DIRECT COSTS                         ₹           │
// │   Supplier payments              (14,80,000)     │
// │   Agent commissions                (2,22,000)    │
// │   Branch manager override           (40,000)     │
// │   Total Direct Costs             (17,42,000)     │
// │                                                  │
// │ GROSS PROFIT                      2,88,000       │
// │ Gross Margin:                      14.2%         │
// │                                                  │
// │ OPERATING COSTS                     ₹            │
// │   Rent                              (75,000)     │
// │   Salaries (3 agents + manager)    (3,50,000)    │
// │   Utilities                          (25,000)    │
// │   Local marketing                    (30,000)    │
// │   Total Operating Costs           (4,80,000)     │
// │                                                  │
// │ NETWORK COSTS                        ₹           │
// │   Royalty (6% of revenue)           (1,21,800)   │
// │   Technology fee                      (15,000)   │
// │   Marketing fund                      (40,600)   │
// │   Total Network Costs             (1,77,400)     │
// │                                                  │
// │ NET OPERATING PROFIT              (3,69,400)     │
// │ Net Margin:                        -18.2%        │
// │                                                  │
// │ ALLOCATIONS FROM HQ                  ₹           │
// │   Shared supplier benefit            85,000      │
// │   National marketing impact          40,000      │
// │                                                  │
// │ ADJUSTED NET PROFIT              (2,44,400)      │
// │ Adjusted Margin:                   -12.0%        │
// │                                                  │
// │ Note: Branch in growth phase (month 6).          │
// │ Break-even expected at month 10-12.              │
// └──────────────────────────────────────────────────┘
```

### C. Inter-Branch Trip Transfers

```typescript
interface InterBranchTransfer {
  transferId: string;
  tripId: string;
  sourceBranchId: string;
  targetBranchId: string;
  transferReason: TransferReason;
  revenueSplit: RevenueSplit;
  status: TransferStatus;
  initiatedBy: string;
  approvedBy: string[];
  timeline: TransferTimeline;
}

type TransferReason =
  | 'customer_relocation'              // Customer moved to different city
  | 'specialization'                    // Trip needs expertise at target branch
  | 'capacity'                          // Source branch overloaded
  | 'customer_request'                 // Customer wants different branch
  | 'territory_compliance'             // Trip belongs to target territory
  | 'supplier_relationship';           // Target branch has better supplier terms

type TransferStatus =
  | 'requested'
  | 'under_review'
  | 'approved'
  | 'rejected'
  | 'in_progress'
  | 'completed'
  | 'reversed';

// Inter-branch transfer workflow:
//
// ┌──────────┐    request     ┌──────────┐    approve    ┌──────────┐
// │ Source   │───────────────>│ Target   │──────────────>│ Both     │
// │ Branch   │                │ Branch   │               │ Branches │
// │ (Delhi)  │                │ (Mumbai) │               │          │
// └──────────┘                └──────────┘               └──────────┘
//      │                           │                          │
//      │  1. Delhi agent creates   │  2. Mumbai manager       │
//      │     transfer request      │     reviews & accepts    │
//      │                           │                          │
//      │  3. Revenue split         │  4. Mumbai agent         │
//      │     calculated            │     assigned to trip     │
//      │                           │                          │
//      │  5. Trip data & docs      │  6. Mumbai takes over    │
//      │     transferred           │     customer comm        │
//      │                           │                          │
//      └───────────────────────────┴──────────────────────────┘

interface RevenueSplit {
  tripId: string;
  transferId: string;
  splitRules: SplitRule[];
  totalRevenue: Money;
  sourceShare: Money;
  targetShare: Money;
  networkShare: Money;                  // If franchisor takes a cut
}

interface SplitRule {
  component: string;                    // "agent_commission", "branch_revenue"
  sourcePercentage: number;             // 0-100
  targetPercentage: number;             // 0-100
  rationale: string;
}

// Revenue split examples:
//
// SCENARIO 1: Customer relocation (Delhi → Mumbai)
// Trip: ₹1,50,000 Kerala honeymoon package
// Delhi did: Initial consultation, hotel booking (70% complete)
// Mumbai does: Flight ticketing, activity booking, customer hand-holding
//
// Split:
//   Agent commission: Delhi 40% / Mumbai 60%
//   Branch revenue:   Delhi 30% / Mumbai 70%
//   Rationale: Most value in ongoing customer relationship (Mumbai)
//
// SCENARIO 2: Specialization transfer (general → luxury branch)
// Trip: ₹8,50,000 Europe luxury tour
// Pune did: Intake and initial planning
// Delhi (luxury specialist) does: Full itinerary, supplier negotiation
//
// Split:
//   Agent commission: Pune 20% / Delhi 80%
//   Branch revenue:   Pune 15% / Delhi 85%
//   Rationale: Specialized expertise drives margin (Delhi)
//
// SCENARIO 3: Territory compliance (HQ → franchise territory)
// Trip: ₹2,00,000 Rajasthan tour
// Delhi HQ website booking, customer is in Jaipur (franchise territory)
// Jaipur franchise does: Local supplier management, on-ground support
//
// Split:
//   Referral fee: Delhi 15%
//   Agent commission: Jaipur 100%
//   Branch revenue: Delhi 15% / Jaipur 85%
//   Rationale: Territory rules, Jaipur does the real work
```

### D. Branch Performance Metrics

```typescript
interface BranchPerformance {
  branchId: string;
  period: PerformancePeriod;
  kpis: BranchKPIs;
  benchmarks: BranchBenchmarks;
  trends: PerformanceTrends;
  alerts: PerformanceAlert[];
}

interface BranchKPIs {
  // Revenue metrics
  totalRevenue: Money;
  revenuePerAgent: Money;
  revenuePerSqft: Money;               // Revenue per sq ft of office space
  averageBookingValue: Money;
  revenueGrowthMonthOverMonth: number;  // Percentage

  // Volume metrics
  tripsBooked: number;
  tripsCompleted: number;
  tripsCancelled: number;
  cancellationRate: number;            // Percentage
  averageTripsPerAgentPerMonth: number;

  // Profitability metrics
  grossMargin: number;                 // Percentage
  netMargin: number;                   // Percentage
  costPerBooking: Money;
  royaltyAsPercentageOfRevenue: number;

  // Customer metrics
  customerSatisfactionScore: number;   // 1-5
  npsScore: number;                    // -100 to +100
  repeatCustomerRate: number;          // Percentage
  complaintRate: number;               // Complaints per 100 trips
  averageResponseTime: number;         // Hours to first response

  // Operational metrics
  averageTripBuildTime: number;        // Hours from intake to proposal
  conversionRate: number;              // Inquiries to confirmed bookings
  documentDeliveryOnTime: number;      // Percentage
  supplierPaymentTimeliness: number;   // Percentage on-time

  // Compliance metrics
  brandComplianceScore: number;        // 0-100
  gstFilingTimeliness: number;         // Percentage on-time
  trainingCompletionRate: number;      // Percentage of agents trained
  auditScore: number;                  // 0-100
}

// Branch performance dashboard (ASCII mockup):
//
// ┌───────────────────────────────────────────────────────────┐
// │ TRAVELEASE PUNE — Branch Performance Dashboard            │
// │ November 2026                                            │
// ├───────────────────────────────────────────────────────────┤
// │                                                          │
// │ ┌─── Revenue ────┐  ┌─── Volume ────┐  ┌─── Margin ───┐ │
// │ │ ₹20.3L        │  │ 87 trips      │  │ 14.2% gross  │ │
// │ │ ▲ 12% vs Oct  │  │ ▲ 8% vs Oct   │  │ ▲ 1.2% vs Oct│ │
// │ │ Target: ₹22L  │  │ Target: 90    │  │ Target: 15%  │ │
// │ └───────────────┘  └───────────────┘  └──────────────┘ │
// │                                                          │
// │ ┌─── Customer ─────────┐  ┌─── Operational ───────────┐ │
// │ │ CSAT: 4.3/5          │  │ Avg build time: 4.2 hrs   │ │
// │ │ NPS: +42             │  │ Conversion: 34%            │ │
// │ │ Repeat: 28%          │  │ Doc delivery: 96% on-time  │ │
// │ │ Complaints: 1.2/100  │  │ GST filing: 100% on-time   │ │
// │ └──────────────────────┘  └────────────────────────────┘ │
// │                                                          │
// │ ┌─── Alerts ────────────────────────────────────────────┐ │
// │ │ ⚠ Cancellation rate 8.5% (network avg: 5%)           │ │
// │ │ ⚠ Agent Sunil below target (7/10 trips)              │ │
// │ │ ✓ Brand compliance score: 94/100                     │ │
// │ │ ✓ Training completion: 100%                          │ │
// │ └───────────────────────────────────────────────────────┘ │
// └───────────────────────────────────────────────────────────┘
```

### E. Resource Sharing Across Branches

```typescript
interface SharedResources {
  networkId: string;
  agents: SharedAgentPool;
  inventory: SharedInventoryPool;
  supplierContracts: SharedContracts;
  knowledge: SharedKnowledgeBase;
}

interface SharedAgentPool {
  networkId: string;
  agents: NetworkAgent[];
  sharingRules: AgentSharingRule[];
  utilization: AgentUtilization;
}

interface AgentSharingRule {
  ruleId: string;
  scenario: SharingScenario;
  conditions: SharingCondition[];
  approvalRequired: boolean;
  revenueSplit: RevenueSplit;
}

type SharingScenario =
  | 'overflow'                         // Branch overloaded, needs extra agent
  | 'specialization'                   // Customer needs niche expertise
  | 'emergency'                        // Agent unavailable, urgent trip
  | 'training'                         // Agent shadowing at another branch
  | 'cross_territory';                 // Agent supporting customer in another territory

// Agent sharing example:
//
// SCENARIO: Pune branch overloaded during Diwali season
//
// Pune: 3 agents, 45 active trips, 12 new inquiries (capacity = 30 trips)
// Mumbai: 4 agents, 22 active trips, 5 new inquiries (capacity = 40 trips)
//
// Solution: Mumbai agent Priya (Goa specialist) handles 8 Pune Goa inquiries
//
// Revenue split:
//   Priya's commission: 100% (she does the work)
//   Mumbai branch revenue: 60% (her home branch)
//   Pune branch referral: 40% (customer came from Pune territory)
//   Royalty: Mumbai pays (Priya's branch)
//
// Customer experience:
//   Customer sees: TravelEase agent (brand consistent)
//   Communication: From TravelEase Pune WhatsApp (territory consistent)
//   Documents: TravelEase branded (brand consistent)
//   Agent: Priya introduces as "TravelEase colleague"

interface SharedInventoryPool {
  networkId: string;
  hotelAllotments: SharedAllotment[];
  groupTourSeats: SharedGroupSeats[];
  contractedRates: SharedContractedRates[];
}

interface SharedAllotment {
  hotelId: string;
  roomType: string;
  season: string;
  totalAllotment: number;               // Rooms across network
  branchAllocations: BranchAllocation[];
  overflowPool: number;                  // Unallocated rooms available to all
  bookingWindow: number;                 // Days before release back to hotel
}

// Allotment sharing example:
//
// Taj Fort Aguada, Goa — December 2026 (Peak Season)
// Network allotment: 20 rooms/night
//
// ┌──────────────────┬───────────┬───────────┬───────────┐
// │ Branch           │ Allocated │ Booked    │ Overflow  │
// ├──────────────────┼───────────┼───────────┼───────────┤
// │ Delhi HQ         │ 8 rooms   │ 6 booked  │ 2 release │
// │ Mumbai Branch    │ 5 rooms   │ 5 booked  │ 0         │
// │ Pune Franchise   │ 3 rooms   │ 1 booked  │ 2 release │
// │ Overflow Pool    │ 4 rooms   │ 2 booked  │ 2 avail   │
// └──────────────────┴───────────┴───────────┴───────────┘
// Release rule: Unallocated rooms released 14 days before check-in
// Overflow: Any branch can book from overflow pool (first-come)
// Priority: Booking branch with highest network contribution gets priority
```

### F. Branch Communication Protocols

```typescript
interface BranchCommunication {
  networkId: string;
  channels: CommunicationChannel[];
  protocols: CommunicationProtocol[];
  escalationMatrix: EscalationMatrix;
}

interface CommunicationProtocol {
  protocolId: string;
  type: ProtocolType;
  participants: ProtocolParticipant[];
  sla: CommunicationSLA;
  channel: string;
}

type ProtocolType =
  | 'customer_handoff'                 // Transferring customer to another branch
  | 'supplier_issue'                   // Supplier problem affecting multiple branches
  | 'inventory_request'                // Requesting shared inventory
  | 'knowledge_share'                  // Sharing destination/supplier intel
  | 'escalation'                       // Escalating issue to HQ/network
  | 'daily_standup'                    // Daily operational sync
  | 'weekly_review'                    // Weekly performance review
  | 'monthly_business_review';         // Monthly P&L and strategy review

// Communication channel hierarchy:
//
// ┌───────────────────────────────────────────────────────┐
// │ L1: In-App Messaging (Real-time)                       │
// │ Agent-to-agent direct messaging within platform       │
// │ Use: Quick questions, status updates, coordination    │
// │ SLA: Response within 30 minutes during business hours │
// ├───────────────────────────────────────────────────────┤
// │ L2: Branch Channel (Async)                            │
// │ Branch-level discussion channel (like Slack channel)  │
// │ Use: Inventory sharing, knowledge exchange, alerts    │
// │ SLA: Acknowledge within 2 hours                      │
// ├───────────────────────────────────────────────────────┤
// │ L3: Network Broadcast (One-way + Ack)                 │
// │ HQ → All branches announcements                       │
// │ Use: Policy changes, supplier updates, promotions    │
// │ SLA: Read acknowledgment within 24 hours             │
// ├───────────────────────────────────────────────────────┤
// │ L4: Formal Request (Workflow)                         │
// │ Structured request with approval workflow             │
// │ Use: Trip transfer, inventory request, exception     │
// │ SLA: Initial response within 4 hours                 │
// ├───────────────────────────────────────────────────────┤
// │ L5: Escalation (Urgent)                               │
// │ Priority channel to HQ / network operations           │
// │ Use: Customer emergency, supplier failure, dispute   │
// │ SLA: Response within 15 minutes                      │
// └───────────────────────────────────────────────────────┘
```

---

## Open Problems

### 1. Real-Time Inventory Sharing at Scale
When 50+ branches share hotel allotments during peak season (December Goa, summer Ladakh), concurrent booking conflicts are inevitable. Optimistic locking with graceful fallback ("room just taken, here's an alternative") is needed without over-complicating the booking flow.

### 2. Fair Revenue Allocation for Multi-Branch Trips
A single trip may involve 3 branches: intake in Pune, ticketing through Delhi (IATA), on-ground support in Kochi. Attributing revenue fairly requires tracking every touchpoint. The "who gets credit" question causes more inter-branch conflict than any other operational issue.

### 3. Branch Health Early Warning
By the time a branch shows negative net margin, the problem is months old. Need leading indicators (inquiry volume drop, agent utilization decline, customer response time increase) that trigger proactive intervention before financial distress.

### 4. Asymmetric Resource Sharing
Corporate branches share resources willingly (same P&L). Franchisees view resource sharing as giving away competitive advantage. The platform needs incentive structures that make sharing mutually beneficial, not just "nice to have."

### 5. Communication Overload
With 20+ branches, agents get bombarded with cross-branch messages. Need intelligent filtering — agents should only see communications relevant to their active trips, territory, and expertise. Otherwise, important messages get lost in noise.

---

## Next Steps

1. **Design inter-branch ledger system** — Build a double-entry ledger for tracking inter-branch financial obligations (commissions owed, inventory used, referral fees)
2. **Prototype branch performance dashboard** — Create the branch-level analytics view with KPIs, benchmarks against network average, and early warning alerts
3. **Build trip transfer workflow** — End-to-end UI for initiating, approving, and executing inter-branch trip transfers with automated revenue splitting
4. **Research shared inventory locking strategies** — Compare pessimistic vs. optimistic locking for shared hotel allotments, evaluate Redis-based distributed locks
5. **Design communication filtering engine** — Rule-based system that routes inter-branch messages to relevant agents only, with priority scoring and digest mode
6. **Study Indian agency branch operations** — Interview 3-5 multi-branch agencies (Thomas Cook, SOTC, local chains) on real operational workflows and pain points

---

**Series:** Agency Network & Franchise Management
**Document:** 2 of 4 (Branch Operations)
**Last Updated:** 2026-04-28
**Status:** Research Exploration
