# Pricing Engine — Margin Calculation & Optimization

> Research document for margin tracking, cost analysis, and profitability optimization.

---

## Key Questions

1. **How do we calculate true margin per booking (revenue minus all costs)?**
2. **What cost components are hidden or often missed in margin calculations?**
3. **How do we set margin targets per product, segment, and channel?**
4. **What's the margin waterfall from gross revenue to net profit per booking?**
5. **How do we detect and address margin erosion?**

---

## Research Areas

### Margin Waterfall Model

```typescript
interface MarginWaterfall {
  bookingId: string;
  // Revenue side
  grossRevenue: number;           // What customer paid
  discounts: number;              // Promotional discounts
  netRevenue: number;
  // Cost side
  supplierCost: number;           // What we pay suppliers
  paymentProcessingFee: number;   // Gateway fees (1.5-3%)
  commissionPaid: number;         // Agent commission
  platformCost: number;           // Allocated platform cost per booking
  supportCost: number;            // Customer service cost allocation
  insuranceCost: number;          // Travel insurance premium (if included)
  // Result
  grossMargin: number;            // netRevenue - supplierCost
  operatingMargin: number;        // grossMargin - all operational costs
  marginPercent: number;          // operatingMargin / netRevenue * 100
}

// Typical travel agency margin waterfall:
// Customer pays:     ₹100,000
// Supplier cost:     -₹78,000  (78%)
// Payment fees:      -₹2,000   (2%)
// Agent commission:  -₹5,000   (5%)
// Platform cost:     -₹1,500   (1.5%)
// Support cost:      -₹1,000   (1%)
//                    --------
// Operating margin:   ₹12,500   (12.5%)
```

### Cost Allocation Model

```typescript
interface CostAllocation {
  // Direct costs (per booking)
  directCosts: DirectCost[];
  // Indirect costs (allocated)
  indirectCosts: IndirectCost[];
  // Overhead allocation method
  allocationMethod: 'per_booking' | 'revenue_percent' | 'activity_based';
}

interface DirectCost {
  type: 'supplier' | 'payment_fee' | 'insurance' | 'document_delivery';
  amount: number;
  description: string;
}

interface IndirectCost {
  type: 'platform' | 'support' | 'office' | 'marketing' | 'management';
  totalMonthlyCost: number;
  allocationPercent: number;       // How much to allocate per booking
  calculatedPerBooking: number;
}
```

### Margin Targets by Segment

```typescript
interface MarginTarget {
  segment: string;
  product: string;
  channel: string;
  targetMarginPercent: number;
  minimumMarginPercent: number;
  maximumMarkupPercent: number;    // Competitive ceiling
  volumeDiscount: VolumeDiscount[];
}

interface VolumeDiscount {
  threshold: number;                // Bookings per month
  marginAdjustment: number;        // Reduce margin by this %
  reason: string;                  // "Volume incentive"
}
```

### Margin Erosion Detection

```typescript
interface MarginAlert {
  alertId: string;
  type: MarginAlertType;
  bookingId?: string;
  detectedAt: Date;
  details: string;
  impact: number;
  recommendation: string;
}

type MarginAlertType =
  | 'below_minimum_margin'       // Booking margin below threshold
  | 'margin_declining_trend'     // Segment margins trending down
  | 'hidden_cost_discovery'      // New cost component identified
  | 'supplier_rate_increase'     // Supplier raised rates without notice
  | 'commission_spike'           // Commission higher than expected
  | 'payment_fee_increase'       // Payment gateway raised fees
  | 'discount_abuse';            // Excessive discounting
```

---

## Open Problems

1. **Indirect cost allocation** — How to fairly allocate platform, support, and overhead costs per booking? Activity-based costing is accurate but complex.

2. **Margin on bundled products** — A package (flight + hotel + transfer) has blended margin. Individual components may have negative margin while the package is profitable.

3. **Time-based margin** — An agent spends 5 hours on a complex booking vs. 30 minutes on a simple one. The simple booking has better margin per hour of agent time.

4. **Customer lifetime margin** — A low-margin first booking may lead to high-margin repeat business. Per-booking margin analysis misses lifetime value.

5. **Opportunity cost** — Time spent on a low-margin complex booking could have been used for multiple high-margin simple bookings. How to factor opportunity cost?

---

## Next Steps

- [ ] Design margin calculation engine with full cost allocation
- [ ] Map direct and indirect cost components for current operations
- [ ] Set margin targets by product and segment
- [ ] Build margin erosion detection alerts
- [ ] Study activity-based costing for travel agency operations
