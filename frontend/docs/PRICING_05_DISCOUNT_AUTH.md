# Pricing Engine 05: Discount Authorization & Margin Protection

> Research document for discount approval workflows, margin floors, discount authorization matrices, and revenue protection controls that prevent unauthorized discounting.

---

## Key Questions

1. **How should discount authorization work across the agency hierarchy?**
2. **What margin floors prevent value destruction?**
3. **How do commission structures interact with discounting?**
4. **What audit trails are needed for discount compliance?**

---

## Research Areas

### Discount Authorization Matrix

```typescript
interface DiscountAuthorization {
  // Who can approve what level of discount:
  matrix: {
    agent: {
      max_discount_pct: 3,               // Agent can give up to 3% without approval
      max_discount_flat: 1000,            // Or ₹1,000, whichever is lower
      requires_approval_above: true,
      approval_from: "team_lead"
    };
    team_lead: {
      max_discount_pct: 5,
      max_discount_flat: 5000,
      requires_approval_above: true,
      approval_from: "branch_manager"
    };
    branch_manager: {
      max_discount_pct: 10,
      max_discount_flat: 15000,
      requires_approval_above: true,
      approval_from: "regional_head"
    };
    regional_head: {
      max_discount_pct: 15,
      max_discount_flat: 50000,
      requires_approval_above: true,
      approval_from: "director"
    };
    director: {
      max_discount_pct: null,             // Unlimited with board notification
      max_discount_flat: null,
      notification_threshold_pct: 20,
      notification_to: "board"
    };
  };
}
```

### Margin Floor Protection

```typescript
interface MarginFloor {
  // Minimum acceptable margins by service type:
  floors: {
    flights: {
      domestic: { min_margin_pct: 2, min_margin_flat: 200 },
      international: { min_margin_pct: 3, min_margin_flat: 1000 },
      group_booking: { min_margin_pct: 1.5, min_margin_flat: 500 }
    };
    hotels: {
      domestic: { min_margin_pct: 10, min_margin_flat: 500 },
      international: { min_margin_pct: 12, min_margin_flat: 1500 },
      luxury: { min_margin_pct: 15, min_margin_flat: 3000 }
    };
    packages: {
      domestic: { min_margin_pct: 8, min_margin_flat: 2000 },
      international: { min_margin_pct: 10, min_margin_flat: 5000 },
      honeymoon: { min_margin_pct: 12, min_margin_flat: 8000 },
      group: { min_margin_pct: 6, min_margin_flat: 1000 }
    };
    services: {
      visa: { min_margin_pct: 20, min_margin_flat: 500 },
      forex: { min_margin_pct: 0.5, min_margin_flat: 100 },
      insurance: { min_margin_pct: 15, min_margin_flat: 200 }
    };
  };

  // Hard floor: Cannot be overridden (regulatory/contractual minimum)
  // Soft floor: Can be overridden with approval chain
  // Strategic floor: Below cost allowed only with director approval (loss leader)

  floor_types: {
    hard: "System blocks — no override possible",
    soft: "Requires approval per authorization matrix",
    strategic: "Director approval + justification + board notification"
  };
}
```

### Discount Types & Controls

```typescript
interface DiscountTypes {
  // Categories of discounts and their controls:
  types: {
    early_bird: {
      description: "Book 60+ days in advance",
      typical_pct: "5-10%",
      auto_approved: true,
      stackable: false                  // Cannot combine with other discounts
    };
    loyalty: {
      description: "Repeat customer discount",
      typical_pct: "3-5%",
      auto_approved: true,
      stackable: true,                  // Can combine with one other discount
      max_stack_total: "8%"
    };
    group: {
      description: "6+ travelers discount",
      typical_pct: "5-8%",
      auto_approved: true,
      stackable: false
    };
    referral: {
      description: "Referred by existing customer",
      typical_flat: "₹1,000-2,000",
      auto_approved: true,
      stackable: true,
      max_stack_total: "8%"
    };
    seasonal: {
      description: "Off-season promotion",
      typical_pct: "10-15%",
      auto_approved: false,             // Requires manager approval
      requires_campaign_code: true,
      stackable: false
    };
    competitor_match: {
      description: "Price match competitor quote",
      typical_pct: "Varies",
      auto_approved: false,             // Requires manager + proof
      requires_competitor_quote: true,
      max_match_to: "net_price"          // Match net price, not fake discounts
    };
    relationship: {
      description: "VIP/long-term client discount",
      typical_pct: "3-7%",
      auto_approved: false,             // Requires manager approval
      requires_customer_tenure: "3+ bookings",
      stackable: true,
      max_stack_total: "10%"
    };
  };
}
```

### Audit Trail

```typescript
interface DiscountAuditTrail {
  // Every discount must be traceable:
  record: {
    booking_id: string;
    original_price: number;
    discount_amount: number;
    discount_pct: number;
    discount_type: string;
    margin_after_discount: number;
    margin_floor: number;

    // Authorization
    requested_by: string;               // Agent who applied discount
    approved_by: string | null;         // Manager who approved (null if auto-approved)
    approval_time: string | null;       // Timestamp of approval
    justification: string | null;       // Why discount was given

    // Compliance
    within_authorization_matrix: boolean;
    margin_floor_breached: boolean;
    margin_floor_type: "none" | "soft" | "hard" | "strategic";
  };

  // Reports:
  reports: {
    discount_summary: "Weekly summary of all discounts by agent, type, margin impact",
    margin_leakage: "Revenue lost to discounts vs. list price",
    authorization_violations: "Discounts given without proper approval",
    top_discount_agents: "Agents giving highest average discount",
    margin_recovery: "Opportunities where discount was given but customer would have paid more"
  };
}
```

---

## Open Problems

### 1. Dynamic Discounting vs. Fixed Approval
Airlines and hotels change prices in real-time. A 5% discount on a ₹50,000 package today might be a 2% discount tomorrow if the base price drops. Should the platform recalculate discount % on live pricing?

### 2. Customer-Specific Pricing
VIP customers expect consistent discounts. Storing per-customer discount entitlements (e.g., "Mr. Sharma always gets 7% off") creates consistency but may conflict with margin floors on low-margin products.

### 3. Group Discount Fairness
In a group booking, one organizer negotiates the price but 10 travelers pay. If the organizer gets a 10% discount but individuals would have paid 5% more, is the discount fair or is the organizer profiting off the group?

---

## Next Steps

- [ ] Add discount authorization to booking pipeline (pre-confirmation stage)
- [ ] Build margin floor enforcement engine
- [ ] Create discount approval workflow with mobile push notifications
- [ ] Design discount audit dashboard for managers
- [ ] Implement discount stacking rules engine

---

**Created:** 2026-05-01
**Series:** Pricing Engine (PRICING_05)
