# Template & Quick-Start System — Component Library

> Research document for reusable itinerary components, building blocks, and modular trip assembly.

---

## Key Questions

1. **What are the reusable building blocks for trip assembly?**
2. **How do components compose into full itineraries?**
3. **What's the component versioning model?**
4. **How do we handle component dependencies (transfer requires hotel)?**
5. **What's the component marketplace model?**

---

## Research Areas

### Component Model

```typescript
interface ItineraryComponent {
  componentId: string;
  name: string;
  type: ComponentType;
  description: string;
  duration: string;                  // "Half day", "Full day", "2 hours"
  location: ComponentLocation;
  inclusions: string[];
  exclusions: string[];
  requirements: ComponentRequirement[];
  compatibleWith: string[];          // Component IDs that pair well
  pricing: ComponentPricing;
  rating: number;
  tags: string[];
}

type ComponentType =
  | 'accommodation'                  // Hotel, resort, homestay
  | 'activity'                       // Tour, experience, workshop
  | 'transfer'                       // Airport transfer, inter-city
  | 'meal'                           // Restaurant, food tour, cooking class
  | 'flight'                         // Flight segment
  | 'insurance'                      // Travel insurance package
  | 'visa_service'                   // Visa assistance package
  | 'connectivity'                   // SIM/eSIM package
  | 'guide'                          // Local guide service
  | 'transport'                      // Car rental, chauffeur
  | 'event'                          // Show, concert, festival
  | 'wellness'                       // Spa, yoga, retreat
  | 'shopping'                       // Shopping tour, market visit
  | 'day_package';                   // Pre-assembled day plan

// Component composition:
// A "Singapore Day Package" component:
//   - Morning: Gardens by the Bay (activity)
//   - Afternoon: Marina Bay Sands (activity)
//   - Lunch: Lau Pa Sat food court (meal)
//   - Transfer: Hotel → Gardens → MBS → Hotel (transfer)
//
// Components can nest: day_package contains activities + meals + transfers
```

### Component Pricing

```typescript
interface ComponentPricing {
  model: PricingModel;
  basePrice: number;
  pricePerPerson: boolean;
  childPrice?: number;               // Discounted price for children
  infantFree: boolean;
  groupDiscounts?: GroupDiscount[];
  seasonalPricing: SeasonalPrice[];
  currency: string;
}

type PricingModel =
  | 'per_person'                     // Price × number of travelers
  | 'per_room'                       // Price × number of rooms
  | 'per_vehicle'                    // Price per transfer/vehicle
  | 'flat_rate'                      // Fixed price regardless of group size
  | 'tiered'                         // Price varies by group size tier
  | 'dynamic';                       // Price varies by demand/availability

interface GroupDiscount {
  minTravelers: number;
  discountPercent: number;
}

interface SeasonalPrice {
  months: number[];
  price: number;
  reason: string;
}

// Component pricing examples:
// "Universal Studios Singapore" → per_person, ₹4,500/adult, ₹3,500/child
// "Singapore Zoo" → per_person, ₹2,800/adult, ₹1,800/child (3-12)
// "Airport Transfer (Sedan)" → per_vehicle, ₹2,500 (up to 4 pax)
// "Airport Transfer (Van)" → per_vehicle, ₹4,000 (up to 8 pax)
// "Singapore Food Tour" → per_person, ₹3,000 (min 2 pax)
// "Private Guide (Half Day)" → flat_rate, ₹6,000 (any group size)
```

### Component Dependencies

```typescript
interface ComponentRequirement {
  type: RequirementType;
  description: string;
  autoResolve: boolean;              // Can the system auto-add this?
}

type RequirementType =
  | 'prerequisite'                   // Must have component X before this
  | 'co_requisite'                   // Must have component X with this
  | 'location'                       // Must be at location X
  | 'timing'                         // Must be within time window
  | 'group_size'                     // Min/max travelers
  | 'season'                         // Only available in certain months
  | 'advance_booking'                // Must book X days in advance
  | 'physical_fitness'               // Fitness level required
  | 'age_restriction'                // Min/max age
  | 'document';                      // Requires visa, ID, etc.

// Dependency resolution:
// Agent adds "Universal Studios Singapore":
//   → Prerequisite: Transfer from hotel (auto-resolve: suggest transfer)
//   → Timing: Opens 10:00, closes 19:00
//   → Age restriction: Some rides have height requirements
//
// Agent adds "Bali Temple Visit":
//   → Co-requisite: Sarong rental (auto-resolve: add to package)
//   → Location: Must be in Bali
//   → Document: No entry without sarong
//   → Timing: Best visited morning (avoid crowds)
//
// Agent adds "Singapore to Bali Flight":
//   → Prerequisite: Singapore hotel check-out same day
//   → Prerequisite: Bali hotel check-in same or next day
//   → Auto-resolve: Suggest airport transfers both ends
```

### Component Versioning

```typescript
interface ComponentVersion {
  componentId: string;
  version: number;
  updatedAt: Date;
  updatedBy: string;
  changes: string;
  pricingChange: boolean;
  breakingChange: boolean;
}

// Version management:
// Minor updates (description, tags) → Auto-versioned
// Pricing changes → Major version, notify agents using this component
// Breaking changes (discontinued, location change) → Major version, flag trips

// Trip-component linkage:
// When a component is updated:
// 1. Find all draft trips using this component
// 2. If pricing changed → Alert agent, show new price
// 3. If breaking change → Alert agent, suggest alternatives
// 4. Confirmed trips → No auto-update, log the change for reference
// 5. Agent decides: Update component, keep old version, or swap
```

---

## Open Problems

1. **Component quality variance** — A "half-day city tour" varies wildly in quality across suppliers. Need quality scoring per supplier per component.

2. **Component overlap** — "Singapore City Tour" from supplier A overlaps with "Singapore Highlights" from supplier B. Need deduplication or clear differentiation.

3. **Real-time pricing** — Component prices change (hotel rates, flight prices). Templates with components need real-time price refresh, not stale prices.

4. **Custom component creation** — Agents should be able to create custom components (unique local experience they discovered). Need easy component creation tools.

5. **Component licensing** — If an agency creates a popular component template, can other agencies use it? Need a sharing/licensing model.

---

## Next Steps

- [ ] Design component data model with dependency resolution
- [ ] Build component pricing engine with seasonal adjustments
- [ ] Create component discovery and search
- [ ] Design component versioning with trip impact analysis
- [ ] Study modular content systems (Lego, WordPress blocks, Notion databases)
