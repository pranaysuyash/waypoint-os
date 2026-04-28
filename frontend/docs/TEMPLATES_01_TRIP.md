# Template & Quick-Start System — Trip Templates

> Research document for trip templates, reusable itinerary patterns, and quick-start workflows.

---

## Key Questions

1. **What trip templates dramatically reduce agent setup time?**
2. **How do templates handle personalization vs. standardization?**
3. **What's the template creation and sharing model?**
4. **How do templates adapt to different customer segments?**
5. **What's the relationship between templates and pricing?**

---

## Research Areas

### Template Model

```typescript
interface TripTemplate {
  templateId: string;
  name: string;
  description: string;
  category: TemplateCategory;
  origin: TemplateOrigin;
  author: string;
  version: number;
  createdAt: Date;
  usageCount: number;
  rating: number;                    // Agent ratings (1-5)
  status: 'draft' | 'published' | 'archived';
  tags: string[];
  itinerary: TemplateItinerary;
  pricing: TemplatePricing;
  requirements: TemplateRequirements;
  customizationPoints: CustomizationPoint[];
}

type TemplateCategory =
  | 'destination'                    // "Singapore 5N/6D", "Kerala Backwaters 4N/5D"
  | 'segment'                        // "Honeymoon Special", "Family Adventure"
  | 'theme'                          // "Spiritual India", "Adventure Nepal"
  | 'duration'                       // "Weekend Getaway", "2-Week Europe"
  | 'budget'                         // "Budget Thailand", "Luxury Maldives"
  | 'season'                         // "Summer Escape", "Winter Wonderland"
  | 'corporate'                      // "Team Offsite", "Client Entertainment"
  | 'mice'                           // "Conference Package", "Incentive Trip"
  | 'group'                          // "School Trip", "Pilgrimage Group"
  | 'quick_getaway';                 // "Last Minute Deals", "Long Weekend"

type TemplateOrigin =
  | 'system'                         // Pre-built by platform
  | 'agency'                         // Created by agency admin
  | 'agent'                          // Created by an agent
  | 'community'                      // Shared by other agencies
  | 'converted';                     // Converted from a successful trip

// Template usage flow:
// 1. Agent selects template (or system suggests based on customer needs)
// 2. Template creates a new trip with pre-filled itinerary
// 3. Agent customizes: dates, travelers, hotel preferences, activities
// 4. System adjusts pricing based on actual dates and selections
// 5. Agent reviews and sends quote to customer
```

### Template Itinerary

```typescript
interface TemplateItinerary {
  duration: number;                  // Number of nights
  days: TemplateDay[];
  inclusions: string[];              // What's included in base price
  exclusions: string[];              // What's NOT included
  bestSeason: string[];              // Best months to travel
  minimumTravelers: number;
  maximumTravelers: number;
}

interface TemplateDay {
  dayNumber: number;
  title: string;                     // "Arrival & City Tour"
  location: string;                  // "Singapore"
  activities: TemplateActivity[];
  meals: MealPlan;
  transferDescription?: string;
  notes: string;
}

interface TemplateActivity {
  activityType: ActivityType;
  title: string;
  description: string;
  duration: string;                  // "2 hours"
  isOptional: boolean;
  isCustomizable: boolean;
  alternatives: string[];            // Swap options
  category: 'must_do' | 'recommended' | 'optional' | 'premium_upsell';
}

type ActivityType =
  | 'sightseeing' | 'adventure' | 'cultural' | 'shopping'
  | 'beach' | 'nature' | 'food' | 'nightlife'
  | 'wellness' | 'religious' | 'educational' | 'entertainment';

interface MealPlan {
  breakfast: boolean;
  lunch: boolean;
  dinner: boolean;
  specialNotes: string;              // "Vegetarian options available"
}

// Example: "Singapore Family Fun 5N/6D"
// Day 1: Arrival + Marina Bay + Gardens by the Bay
// Day 2: Universal Studios (full day)
// Day 3: Sentosa Island + Adventure Cove
// Day 4: Singapore Zoo + River Safari
// Day 5: Shopping (Orchard Road) + Night Safari
// Day 6: Departure
//
// Customization points:
// - Hotel: Budget 3-star ↔ Premium 5-star (3 options)
// - Universal Studios ↔ Disneyland (swap)
// - Zoo ↔ Bird Park (swap)
// - Add: River Cruise (+₹2,000), Cooking Class (+₹3,500)
```

### Template Pricing

```typescript
interface TemplatePricing {
  basePrice: PriceRange;             // Per person, before customization
  priceBreakdown: PriceBreakdownItem[];
  seasonalAdjustment: SeasonalAdjustment[];
  customizationPricing: CustomizationPricing;
  margin: MarginConfig;
}

interface PriceRange {
  min: number;                       // Budget option
  standard: number;                  // Standard option
  premium: number;                   // Premium option
  currency: string;
}

interface SeasonalAdjustment {
  months: number[];
  adjustmentPercent: number;         // +20% for peak, -10% for off-season
  reason: string;
}

interface CustomizationPricing {
  hotelUpgrades: Record<string, number>;
  activitySwaps: Record<string, number>;
  addOns: Record<string, number>;
  transportUpgrades: Record<string, number>;
}

// Pricing approach:
// 1. Template has a base price range (budget/standard/premium)
// 2. Agent selects tier → Base pricing established
// 3. Customizations adjust price up or down
// 4. Seasonal adjustment applied automatically
// 5. Agent can manually adjust margin within allowed range
// 6. Final price = base + customizations + seasonal ± margin adjustment
```

### Template Discovery

```typescript
interface TemplateSearch {
  query?: string;
  filters: TemplateFilter[];
  sortBy: 'relevance' | 'popularity' | 'rating' | 'newest';
}

interface TemplateFilter {
  field: string;
  operator: 'eq' | 'in' | 'range';
  value: unknown;
}

// Smart template suggestion:
// Based on customer inquiry, system suggests templates:
// 1. Match destination (Singapore → Singapore templates)
// 2. Match budget range (₹50K → filter out luxury)
// 3. Match traveler profile (family with kids → family templates)
// 4. Match duration (5 nights → 4-6 night templates)
// 5. Ranked by: agent usage + rating + conversion rate

// Template marketplace vision:
// - Platform provides 50+ base templates
// - Agencies create and share templates
// - Best-rated templates rise to the top
// - Agents can fork and customize templates
// - Usage analytics show which templates convert best
```

---

## Open Problems

1. **Template staleness** — Prices, availability, and activities change. Templates need periodic refresh or clear "prices as of X date" disclaimers.

2. **Over-standardization** — If agents rely too heavily on templates, every Singapore trip looks the same. Need to encourage creative customization.

3. **Template quality control** — Community templates may have errors (impossible logistics, wrong timings). Need quality scoring and review.

4. **Copyright and IP** — An agent's creative itinerary is their intellectual work. If shared as a template, who owns it? Need clear licensing.

5. **Template-to-trip friction** — Converting a template to a live trip requires filling in actual dates, checking availability, confirming pricing. Need streamlined conversion.

---

## Next Steps

- [ ] Design trip template data model with customization points
- [ ] Build template pricing engine with seasonal adjustments
- [ ] Create template discovery and recommendation system
- [ ] Design template creation tool for agents
- [ ] Study template UX (TourRadar, Expedia Packages, TravelTriangle)
