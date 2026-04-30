# Multi-Branch Operations — Multi-Location Agency Management

> Research document for multi-branch travel agency operations, branch performance tracking, centralized booking management, inter-branch coordination, and unified customer experience across locations for the Waypoint OS platform.

---

## Key Questions

1. **How does the platform manage multiple agency branches?**
2. **How are bookings and customers shared across branches?**
3. **What performance metrics apply to individual branches?**
4. **How is branding and customer experience kept consistent?**

---

## Research Areas

### Multi-Branch Architecture

```typescript
interface MultiBranchOperations {
  // Managing a travel agency with multiple office locations
  branch_model: {
    ORGANIZATION_HIERARCHY: {
      description: "Agency organizational structure for multi-branch operations";
      levels: {
        HEAD_OFFICE: {
          role: "Strategic control — pricing, supplier contracts, marketing, brand";
          controls: ["Supplier negotiations", "Marketing campaigns", "Brand guidelines", "Policy setting"];
          visibility: "All branch data, consolidated financials, cross-branch analytics";
        };
        REGIONAL_BRANCH: {
          role: "Operational execution — customer acquisition, booking, service";
          autonomy: "Customer relationship, day-to-day operations, local marketing";
          constraints: "Must use approved suppliers, follow pricing guidelines, use centralized system";
        };
        FRANCHISE_BRANCH: {
          role: "Independent operator using agency brand and platform";
          autonomy: "Higher operational autonomy than company branches";
          constraints: "Brand compliance, platform usage, revenue sharing agreement";
        };
      };
    };

    DATA_ISOLATION: {
      description: "What data is shared vs. isolated between branches";
      shared: {
        customer_database: "Customer who visits Branch A is recognized at Branch B";
        supplier_contracts: "All branches use same negotiated supplier rates";
        booking_system: "Centralized booking engine — no branch can have separate system";
        financial_ledger: "Consolidated accounting with branch-level sub-ledgers";
      };
      isolated: {
        branch_pnl: "Each branch tracks its own revenue, costs, and profitability";
        agent_commissions: "Branch-specific commission structures and payouts";
        local_marketing: "Branch-level marketing spend and campaign tracking";
      };
    };
  };

  // ── Multi-branch dashboard (owner view) ──
  // ┌─────────────────────────────────────────────────────┐
  // │  Multi-Branch Overview · Waypoint Travel                    │
  // │  4 branches · 18 agents · 340 active trips                │
  // │                                                       │
  // │  Branch Performance (this month):                     │
  // │                                                       │
  // │  🏢 Andheri (HQ)    Bookings: 45  Revenue: ₹52L          │
  // │     Agents: 6 · Avg/agent: ₹8.7L · Margin: 18.2%        │
  // │     ✅ On target (92% of monthly goal)                    │
  // │                                                       │
  // │  🏢 Bandra           Bookings: 32  Revenue: ₹41L          │
  // │     Agents: 5 · Avg/agent: ₹8.2L · Margin: 16.8%        │
  // │     ⚠️ Below target (78% of monthly goal)                 │
  // │                                                       │
  // │  🏢 Thane            Bookings: 28  Revenue: ₹33L          │
  // │     Agents: 4 · Avg/agent: ₹8.3L · Margin: 17.5%        │
  // │     ✅ On target (88% of monthly goal)                    │
  // │                                                       │
  // │  🏢 Pune (franchise) Bookings: 21  Revenue: ₹27L          │
  // │     Agents: 3 · Avg/agent: ₹9.0L · Margin: 15.1%        │
  // │     ✅ On target (95% of monthly goal)                    │
  // │                                                       │
  // │  Consolidated:                                        │
  // │  Total bookings: 126 · Revenue: ₹1.53Cr                  │
  // │  Avg margin: 17.2% · Top branch: Andheri                  │
  // │                                                       │
  // │  [Branch Comparison] [Transfer Agent] [Add Branch]        │
  // └─────────────────────────────────────────────────────────┘
}
```

### Cross-Branch Coordination

```typescript
interface CrossBranchCoordination {
  // How branches work together
  coordination_areas: {
    CUSTOMER_HANDOFF: {
      description: "Customer moves between branches (e.g., relocates, closer branch)";
      protocol: {
        context_transfer: "Full customer profile, trip history, preferences transferred instantly";
        agent_assignment: "New branch assigns appropriate agent based on customer profile";
        continuity: "Customer experience is seamless — no repeated information";
      };
      rule: "Customer's 'home branch' is wherever they last interacted; any branch can serve";
    };

    GROUP_BOOKING_SPLIT: {
      description: "Large group booking split across branches for capacity";
      example: "Corporate trip for 50 people: HQ handles flights + hotel, branch handles local activities";
      revenue_split: "Revenue split by effort/proportional contribution to the booking";
    };

    AGENT_TRANSFER: {
      description: "Agent moves between branches (transfer or temporary assignment)";
      protocol: "Agent profile, customer assignments, and commission history transfer with agent";
      use_case: "Agent relocates to Pune → transfers to Pune branch with existing customer relationships intact";
    };

    INVENTORY_SHARING: {
      description: "Branch can use another branch's supplier allotments";
      example: "Andheri branch has committed 20 hotel rooms for peak season → Bandra branch can use 5 from that allotment";
      tracking: "Inter-branch inventory transfers tracked with settlement accounting";
    };
  };

  brand_consistency: {
    UNIFIED_CUSTOMER_EXPERIENCE: {
      requirements: [
        "Same WhatsApp number + IVR routing to nearest branch",
        "Same website with branch selector",
        "Same email templates and branding",
        "Same pricing (no branch undercuts another)",
        "Same service quality standards",
      ];
    };

    QUALITY_CONTROL: {
      measures: [
        "Mystery shopper audits (quarterly) at each branch",
        "Customer satisfaction scores by branch (target: 4.5+/5)",
        "Booking accuracy rate by branch (target: 99%+)",
        "Response time SLA compliance by branch",
      ];
    };
  };
}
```

### Branch Financial Management

```typescript
interface BranchFinancialManagement {
  // Financial tracking and management per branch
  financial_structure: {
    REVENUE_ATTRIBUTION: {
      rules: [
        "Booking revenue attributed to branch where agent operates",
        "Online bookings attributed to nearest branch to customer's address",
        "Referral bookings attributed to originating branch",
      ];
    };

    COST_ALLOCATION: {
      branch_costs: ["Rent", "Staff salaries", "Local marketing", "Utilities", "Office supplies"];
      shared_costs: ["Platform subscription", "Central marketing", "Supplier relationship management", "Head office overhead"];
      allocation_method: "Shared costs allocated pro-rata by branch revenue contribution";
    };

    PROFITABILITY_ANALYSIS: {
      branch_pnl: {
        revenue: "Total booking revenue attributed to branch";
        cogs: "Supplier payments for branch bookings";
        gross_margin: "Revenue minus COGS (target: 15-20%)";
        operating_costs: "Branch-specific costs + allocated shared costs";
        net_margin: "Gross margin minus operating costs (target: 8-12%)";
      };
      comparison: "Rank branches by net margin, revenue per agent, customer satisfaction";
    };

    INTER_BRANCH_SETTLEMENT: {
      description: "Financial settlement between branches for shared resources";
      examples: [
        "HQ procured hotel allotment → Branch B used 5 rooms → Branch B pays HQ at cost",
        "Agent from Branch A closed a deal for Branch B's customer → commission split between branches",
      ];
      frequency: "Monthly settlement with quarterly reconciliation";
    };
  };
}
```

---

## Open Problems

1. **Branch autonomy vs. central control** — Too much centralization makes branches slow; too much autonomy leads to inconsistency. Finding the right balance requires clear policy boundaries: central controls pricing and brand, branches control customer relationships and local marketing.

2. **Franchise compliance** — Franchise branches may resist using the central platform if they have their own systems. Contractual platform-usage requirements plus making the platform genuinely better than alternatives is the solution.

3. **Cannibalization** — Two branches in the same city may compete for the same customers. Need territory definitions or customer assignment rules to prevent internal competition.

4. **Data quality across branches** — Branch B may enter customer data differently than Branch A, causing fragmented customer profiles. Standardized data entry and validation rules must be enforced platform-wide.

5. **Scale ceiling** — Multi-branch operations add management overhead. At 10+ branches, a regional management layer may be needed between head office and branches.

---

## Next Steps

- [ ] Build multi-branch management dashboard with consolidated view
- [ ] Implement branch-level P&L tracking with inter-branch settlement
- [ ] Create customer handoff protocol for cross-branch transfers
- [ ] Design branch performance comparison analytics
- [ ] Implement brand consistency monitoring across branches
