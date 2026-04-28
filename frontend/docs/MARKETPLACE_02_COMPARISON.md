# Travel Marketplace & Aggregator — Comparison & Matching

> Research document for side-by-side trip comparison, feature matching, value scoring algorithms, and comparison UX for agents and customers.

---

## Key Questions

1. **How do we present multi-option comparisons without overwhelming users?**
2. **What feature matching algorithms normalize across different suppliers?**
3. **How does value scoring account for qualitative factors beyond price?**
4. **What comparison UX patterns work for travel products?**
5. **How do we handle "apples to oranges" comparison scenarios?**

---

## Research Areas

### Comparison Data Model

```typescript
interface ComparisonEngine {
  session: ComparisonSession;
  items: ComparisonItem[];
  dimensions: ComparisonDimension[];
  scoring: ValueScoring;
  recommendation: ComparisonRecommendation;
}

interface ComparisonSession {
  id: string;
  type: ComparisonType;
  createdBy: string;                   // Agent or customer ID
  createdAt: Date;
  status: 'active' | 'shared' | 'archived';
  shareLink?: string;                  // Share with customer for review
  notes?: string;                      // Agent notes for customer
}

interface ComparisonItem {
  id: string;
  source: string;                      // "Option A", "Option B"
  type: 'trip' | 'hotel' | 'flight' | 'package';
  data: ComparisonData;
  pricing: ComparisonPricing;
  features: ComparisonFeature[];
  pros: string[];
  cons: string[];
  images: MediaRef[];
}

// Comparison types:
//
// 1. SAME HOTEL, DIFFERENT SUPPLIERS:
//    Taj Palace Mumbai from Hotelbeds vs. TBO vs. Direct Connect
//    Compare: Rate, meal plan, cancellation, commission, room type
//
// 2. DIFFERENT HOTELS, SAME DESTINATION:
//    Taj Palace vs. Oberoi vs. Trident (Mumbai)
//    Compare: Rate, location, rating, amenities, room size
//
// 3. SAME ITINERARY, DIFFERENT PACKAGES:
//    Kerala 5N from Supplier A vs. Supplier B vs. Custom build
//    Compare: Total price, hotels, inclusions, transport quality
//
// 4. DIFFERENT DESTINATIONS, SAME BUDGET:
//    Goa vs. Kerala vs. Rajasthan for ₹50,000 per person
//    Compare: Value for money, experiences, weather, season
//
// 5. SAME TRIP, DIFFERENT SEASONS:
//    Kerala in October vs. December vs. March
//    Compare: Price, weather, crowd, availability, events

interface ComparisonDimension {
  name: string;                        // "Price", "Location", "Rating"
  type: 'quantitative' | 'qualitative' | 'categorical' | 'boolean';
  unit?: string;                       // "₹", "km", "stars", "points"
  weight: number;                      // 0-1, for composite scoring
  direction: 'higher_better' | 'lower_better';  // For quantitative
  normalizer?: NormalizationRule;
}

// Comparison dimensions for hotels:
// QUANTITATIVE:
//   Price per night: Lower better, ₹, weight: 0.25
//   Star rating: Higher better, 1-5 stars, weight: 0.10
//   User rating: Higher better, 1-10, weight: 0.15
//   Distance to center: Lower better, km, weight: 0.08
//   Room size: Higher better, sq ft, weight: 0.05
//   Review count: Higher better, count, weight: 0.02
//
// CATEGORICAL:
//   Meal plan: Room only < Breakfast < HB < FB < AI
//   Room type: Standard < Superior < Deluxe < Suite
//   Cancellation: Non-refundable < 24h < 48h < Free cancel
//
// BOOLEAN:
//   Pool: Yes/No
//   Gym: Yes/No
//   Spa: Yes/No
//   Restaurant: Yes/No
//   Parking: Yes/No
//   WiFi: Yes/No
//   Airport shuttle: Yes/No
//
// QUALITATIVE:
//   Location description: "Waterfront" vs. "City center" vs. "Suburban"
//   Ambiance: "Business hotel" vs. "Boutique" vs. "Resort"
//   Breakfast quality: Agent review notes
//
// Comparison dimensions for full trips:
//   Total price per person: ₹, weight: 0.30
//   Hotel quality: Average star rating, weight: 0.15
//   Inclusions: Count of included items, weight: 0.10
//   Transport quality: Category (shared/private/luxury), weight: 0.10
//   Activities: Count of included activities, weight: 0.08
//   Flexibility: Cancellation terms score, weight: 0.07
//   Guide quality: Rating if included, weight: 0.05
//   Meal plan: Category (room only → all inclusive), weight: 0.05
//   Reviews: Aggregate rating, weight: 0.05
//   Agent margin: ₹ commission, weight: 0.05 (agent-internal)

interface ValueScoring {
  algorithm: 'weighted_sum' | 'topsis' | 'analytic_hierarchy';
  weights: ScoringWeights;
  result: ValueScore[];
}

// TOPSIS-based value scoring:
// Technique for Order Preference by Similarity to Ideal Solution
// 1. Normalize all dimensions to 0-1 scale
// 2. Calculate weighted normalized values
// 3. Determine ideal best and ideal worst for each dimension
// 4. Calculate Euclidean distance from ideal best and worst
// 5. Calculate relative closeness to ideal (score = 0-1)
// 6. Rank by relative closeness
//
// Example: 3 hotels compared
//              Price    Rating   Location   Pool   Breakfast
// Hotel A      ₹8,500   4.5      0.5km     Yes    Included
// Hotel B      ₹6,200   4.0      2.3km     No     Not incl.
// Hotel C      ₹12,000  4.8      0.2km     Yes    Included
//
// After TOPSIS scoring (weights: price 40%, rating 25%, location 15%, pool 10%, breakfast 10%):
// Hotel A: 0.82 (best value — good price, great rating, close, has pool)
// Hotel B: 0.54 (cheapest but compromises on location and amenities)
// Hotel C: 0.71 (best quality but expensive)
//
// Recommendation: "Hotel A offers the best value for money.
//   Great rating (4.5/5), close to city center, includes breakfast and pool access."

interface ComparisonRecommendation {
  bestOverall: ComparisonItem;         // Highest value score
  bestValue: ComparisonItem;           // Best price-to-quality ratio
  bestQuality: ComparisonItem;         // Highest quality regardless of price
  budgetPick: ComparisonItem;          // Cheapest acceptable option
  agentRecommendation?: ComparisonItem; // Agent's manual pick
  rationale: string;                   // AI-generated comparison summary
}

// Comparison recommendation output:
// "Based on your preferences (4-star, central location, ₹8,000-10,000 budget):
//
//  BEST OVERALL: Hotel A (Taj Residency) — ₹8,500/night
//  ✅ Excellent rating (4.5/5, 1,200 reviews)
//  ✅ Central location (500m from MG Road)
//  ✅ Includes breakfast, pool, gym
//  ✅ Free cancellation up to 24h before
//
//  BEST VALUE: Hotel B (Treebo Trend) — ₹6,200/night
//  ✅ Clean, modern rooms
//  ✅ Great location
//  ⚠️ No pool, breakfast not included (+₹800)
//  ⚠️ 3-star category
//
//  LUXURY PICK: Hotel C (Taj Palace) — ₹12,000/night
//  ✅ Best-in-class rating (4.8/5)
//  ✅ Waterfront location
//  ✅ All amenities included
//  ⚠️ 42% above budget"
```

### Comparison UX Patterns

```typescript
interface ComparisonUX {
  layouts: ComparisonLayout[];
  interactions: ComparisonInteraction[];
  sharing: ComparisonSharing;
  export: ComparisonExport;
}

type ComparisonLayout =
  | 'side_by_side'                     // 2-3 items, columns
  | 'overlay'                          // Items stacked, tap to reveal details
  | 'table'                            // Rows = dimensions, columns = items
  | 'card_stack'                       // Swipeable cards
  | 'checklist';                       // Feature checklist with checkmarks

// Layout selection by comparison type:
// 2-3 hotels: Side-by-side cards (desktop) or card stack (mobile)
// 3-5 options: Table layout with expandable rows
// Full trips: Table layout with grouped sections
// Same hotel different suppliers: Compact table (price, terms, commission)
//
// Comparison table UX for 3 hotels:
// ┌──────────────────┬──────────────┬──────────────┬──────────────┐
// │                  │  Taj Residency│  Treebo Trend│  Taj Palace  │
// ├──────────────────┼──────────────┼──────────────┼──────────────┤
// │ Price/night      │  ₹8,500 ✨   │  ₹6,200 💰   │  ₹12,000 💎 │
// │ Star rating      │  ★★★★☆      │  ★★★☆☆      │  ★★★★★      │
// │ User rating       │  4.5/5      │  4.0/5       │  4.8/5       │
// │ Location          │  0.5km ✨   │  2.3km       │  0.2km ✨    │
// │ Breakfast         │  ✅ Included │  ❌ +₹800    │  ✅ Included │
// │ Pool              │  ✅          │  ❌          │  ✅ + Spa    │
// │ WiFi              │  ✅ Free     │  ✅ Free     │  ✅ Free     │
// │ Cancellation      │  24h free ✨│  48h free    │  24h free ✨ │
// │ Room size         │  350 sq ft  │  220 sq ft   │  450 sq ft ✨│
// │ Value score       │  82/100 🏆 │  54/100      │  71/100      │
// │ Agent commission  │  ₹1,275     │  ₹930        │  ₹1,800     │
// └──────────────────┴──────────────┴──────────────┴──────────────┘
//
// ✨ = Best in category   🏆 = Recommended   💰 = Cheapest   💎 = Premium

// Comparison interactions:
// - Click dimension: Expand for detailed explanation
// - Hover item: Highlight corresponding row in all columns
// - Toggle dimensions: Show/hide comparison criteria
// - Reorder items: Drag columns to rearrange
// - Add to comparison: Search and add more options
// - Remove from comparison: Swipe to remove
// - Highlight differences: Toggle to dim identical values
// - Agent notes: Add notes to specific cells
//
// Sharing comparison:
// - Generate shareable link for customer review
// - Customer sees comparison without agent pricing (commission hidden)
// - Customer can add comments/questions on each option
// - Agent sees customer comments in real-time
// - Customer can "favorite" options to indicate preference
//
// Export comparison:
// - PDF report: Professional comparison document with branding
// - WhatsApp message: Condensed comparison with key highlights
// - Email: HTML formatted comparison table
// - Excel: Raw data for customer analysis
```

---

## Open Problems

1. **Qualitative comparison** — Comparing "ambiance" or "location vibe" across hotels is subjective. Structured dimensions don't capture the feel of a place. Combining structured data with agent commentary is the best approach.

2. **Commission transparency** — Showing agent commission in comparison is useful for agents but must be hidden from customers. The comparison tool needs dual views (agent view and customer view) from the same data.

3. **Comparison fatigue** — Presenting 10+ dimensions across 5+ options creates cognitive overload. Smart dimension selection (show only dimensions where items differ) reduces noise.

4. **Real-time price accuracy** — Comparison prices are snapshots at search time. By the time a customer reviews and decides, prices may have changed. Showing "price last updated X minutes ago" manages expectations.

5. **Cross-category comparison** — Comparing a Goa beach trip with a Rajasthan heritage trip is comparing fundamentally different experiences. Value scoring helps but can't fully capture experiential differences.

---

## Next Steps

- [ ] Build comparison data model with multi-dimensional scoring
- [ ] Create TOPSIS-based value scoring algorithm for travel products
- [ ] Design comparison UX with side-by-side and table layouts
- [ ] Implement customer-facing comparison sharing with dual views
- [ ] Study comparison tools (Trivago, Kayak, Google Hotels, Skyscanner)
