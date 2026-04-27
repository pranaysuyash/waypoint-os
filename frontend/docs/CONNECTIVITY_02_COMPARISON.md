# SIM Cards & Connectivity 02: Comparison & Recommendations

> Comparing connectivity options and recommending best choices

---

## Document Overview

**Focus:** How customers compare and select connectivity options
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions to Answer

### 1. Comparison Framework
- How do we compare roaming vs. local SIM vs. eSIM?
- What factors matter most to customers?
- How do we weight price vs. convenience vs. coverage?
- What about edge cases? (Business travelers, families, etc.)

### 2. Recommendation Engine
- How do we recommend the best option?
- What data do we need about the customer?
- How do we handle different travel patterns?
- What about device limitations?

### 3. Transparency
- How do we show total cost?
- What about hidden fees? (Taxes, card fees, etc.)
- How do we explain technical limitations?
- What about fair use policies?

### 4. Trust & Reviews
- How do customers trust our recommendations?
- Do we show network quality reviews?
- What about independent tests?
- How do we handle conflicts of interest?

---

## Research Areas

### A. Option Comparison

**eSIM vs. Physical SIM vs. Roaming:**

| Factor | eSIM | Physical SIM | Roaming |
|--------|------|--------------|---------|
| **Convenience** | High (instant) | Low (delivery/wait) | High (already on phone) |
| **Price** | Medium | Low (local) | High |
| **Coverage** | Good | Varies | Best (home carrier) |
| **Device support** | Limited | Universal | Universal |
| **Activation** | QR code | Insert, call | App/USSD |
| **Support** | Online | Varies | Carrier |

**Research:**
- Which option wins for which use case?
- How do we present this clearly?

### B. Use Case Segmentation

| Use Case | Recommended Option | Why? |
|----------|-------------------|------|
| **Short leisure trip** | eSIM | Convenience, no delivery |
| **Long-term travel** | Local SIM | Best value |
| **Business trip** | Roaming or eSIM | Reliability, support |
| **Multi-country** | Regional eSIM | One plan for all |
| **Cruise** | Specialized SIM | Ports coverage |
| **Remote areas** | Satellite? | Coverage needed |

**Research:**
- What are the common use cases?
- How do we detect use case from trip details?

### C. Pricing Comparison

**True Cost Calculation:**

```
Base price
+ Taxes/fees
+ Card processing fee
+ Shipping (if physical SIM)
+ Activation fee
= Total cost

Per GB cost = Total cost / GB
Per day cost = Total cost / days
```

**Research:**
- What fees are commonly hidden?
- How do we get accurate pricing?
- What about currency conversion?

### D. Network Quality

**Quality Metrics:**

| Metric | How to Measure | Source |
|--------|---------------|--------|
| **Speed** | Mbps tests | Independent, user reports |
| **Coverage** | Geographic | Provider maps, user reports |
| **Reliability** | Uptime | User reports |
| **Congestion** | Speed variance | User reports |

**Research:**
- Where do we get this data?
- How do we present it simply?
- How do we keep it current?

---

## Recommendation Logic

```
Input: Trip details, device info, customer preferences

1. Check device compatibility
   - eSIM supported? → include eSIM options
   - else → physical SIM or roaming only

2. Analyze trip pattern
   - Single country? → Local options
   - Multi-country? → Regional options
   - Duration? → Plan validity needs

3. Match to plans
   - Filter by coverage
   - Filter by validity
   - Filter by budget

4. Rank options
   - Price
   - Convenience
   - Quality
   - Match to preferences

5. Present recommendations
   - Best overall
   - Best value
   - Most convenient
   - Backup options
```

---

## Data Model for Recommendations

```typescript
interface ConnectivityRecommendation {
  tripId: string;
  customerPreferences: CustomerPrefs;

  // Device compatibility
  device: {
    esimCompatible: boolean;
    model?: string;
  };

  // Options considered
  options: RankedOption[];

  // Top recommendations
  recommendations: {
    bestOverall: string;  // plan ID
    bestValue: string;
    mostConvenient: string;
  };
}

interface RankedOption {
  plan: ConnectivityPlan;
  rank: number;
  score: number;
  reasons: string[];
  warnings: string[];
}

interface CustomerPrefs {
  budget?: PriceRange;
  priority: 'price' | 'convenience' | 'quality';
  dataNeeds: 'low' | 'medium' | 'high';
  voiceNeeded: boolean;
}
```

---

## Presentation Strategy

**Comparison Table:**

| Column | Content |
|--------|---------|
| Option | Provider, plan name |
| Data | GB included, validity |
| Price | Total cost, per GB |
| Pros | Key benefits |
| Cons | Key limitations |
| Score | Our rating |

**Badges:**
- "Best Value"
- "Fastest Activation"
- "Best Coverage"
- "Editor's Choice"

**Warnings:**
- "Requires eSIM-compatible device"
- "No tethering allowed"
- "Fair use policy applies"

---

## Open Problems

### 1. Conflicting Recommendations
**Challenge:** One option is cheapest, another is most convenient

**Options:**
- Present trade-offs clearly
- Let customer choose priority
- Make a judgment call

**Research:** What do customers prefer?

### 2. Dynamic Pricing
**Challenge:** Prices change frequently

**Options:**
- Real-time pricing (API dependent)
- Cached pricing with disclaimer
- Price ranges

**Research:** How often do prices change?

### 3. Network Quality Claims
**Challenge:** Providers claim 5G, reality is 3G

**Options:**
- Use independent data
- User reviews
- Caveats and disclaimers

**Research:** Where to get reliable data?

### 4. Roaming Complexity
**Challenge:** Carrier roaming plans are complex

**Options:**
- Simplify presentation
- Link to carrier details
- Exclude roaming (too complex)

**Research:** How do others present roaming?

---

## Competitor Research Needed

| Competitor | Comparison UX | Notable Patterns |
|------------|---------------|------------------|
| **Airalo** | ? | ? |
| **Nomad** | ? | ? |
| **Travel sites** | ? | ? |

---

## Experiments to Run

1. **Preference survey:** What do customers value most?
2. **A/B test:** How to present comparisons?
3. **Accuracy test:** How accurate are our recommendations?
4. **Conversion tracking:** Which recommendations convert?

---

## References

- [Activities - Search](./ACTIVITIES_02_SEARCH.md) — Similar comparison patterns
- [Insurance - Quoting](./INSURANCE_02_QUOTING.md) — Recommendation logic

---

## Next Steps

1. Build recommendation algorithm
2. Design comparison UI
3. Gather network quality data
4. Test with real trips
5. Iterate based on feedback

---

**Status:** Research Phase — Comparison framework unknown

**Last Updated:** 2026-04-27
