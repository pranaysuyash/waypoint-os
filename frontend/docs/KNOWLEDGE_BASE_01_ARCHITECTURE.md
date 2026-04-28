# Knowledge Base & Internal Wiki — Architecture & Content

> Research document for internal knowledge management, destination guides, and agent reference materials.

---

## Key Questions

1. **What knowledge do agents need to access during trip building?**
2. **What's the content model for destination guides, supplier info, and procedures?**
3. **How do we keep knowledge content fresh and accurate?**
4. **What's the search and discovery model for knowledge?**
5. **How do agents contribute to the knowledge base?**

---

## Research Areas

### Knowledge Content Model

```typescript
interface KnowledgeEntry {
  entryId: string;
  title: string;
  type: KnowledgeType;
  category: KnowledgeCategory;
  content: string;                   // Rich text (markdown)
  tags: string[];
  author: string;
  lastUpdated: Date;
  version: number;
  status: 'draft' | 'published' | 'archived';
  views: number;
  rating: number;
  relatedEntries: string[];
}

type KnowledgeType =
  | 'destination_guide'              // City/country travel guide
  | 'supplier_profile'               // Supplier details and procedures
  | 'procedure'                      // Step-by-step process
  | 'policy'                         // Company policy or rule
  | 'faq'                            // Frequently asked question
  | 'best_practice'                  // Recommended approach
  | 'troubleshooting'                // How to fix common issues
  | 'regulation'                     // Legal/compliance requirement
  | 'product_guide'                  // How to use platform features
  | 'sales_script'                   // Customer conversation templates
  | 'competitor intel'               // Competitor comparison
  | 'seasonal_guide';                // Season-specific recommendations

type KnowledgeCategory =
  | 'destinations'
  | 'suppliers'
  | 'operations'
  | 'sales'
  | 'compliance'
  | 'training'
  | 'products'
  | 'internal';

// Destination guide structure:
interface DestinationGuide {
  destination: string;
  country: string;
  overview: string;
  bestTimeToVisit: SeasonInfo[];
  gettingThere: FlightInfo[];
  visaRequirements: VisaInfo;
  weather: WeatherInfo[];
  topAttractions: Attraction[];
  hotelRecommendations: HotelRec[];
  restaurantRecommendations: RestaurantRec[];
  localTips: string[];
  culturalNotes: string[];
  safetyAdvisory: string;
  emergencyContacts: EmergencyContact[];
  sampleItinerary: string[];         // Day-by-day suggestions
  estimatedBudget: BudgetRange;
  popularFrom: string[];             // Cities with direct flights
}
```

### Content Lifecycle

```typescript
interface ContentLifecycle {
  creation: ContentCreation;
  review: ContentReview;
  publishing: ContentPublishing;
  maintenance: ContentMaintenance;
  retirement: ContentRetirement;
}

interface ContentCreation {
  author: string;
  source: 'original' | 'ai_generated' | 'community' | 'supplier_provided';
  template: string;
  reviewRequired: boolean;
}

interface ContentReview {
  reviewers: string[];
  criteria: ReviewCriteria[];
  approvedBy?: string;
  feedback: string[];
}

interface ContentMaintenance {
  reviewSchedule: string;            // "every 6 months"
  lastReviewedAt?: Date;
  nextReviewBy: Date;
  stalenessIndicator: number;        // 0-100, how stale the content is
}

// Content staleness detection:
// Visa requirements: Review every 3 months (regulations change)
// Supplier profiles: Review every 6 months
// Destination guides: Review every 12 months
// Platform how-tos: Review on every UI change
// Pricing policies: Review every 3 months
// Cultural notes: Review every 12 months

// AI-assisted content:
// 1. Auto-draft destination guides from public data (Wikipedia, travel sites)
// 2. Flag outdated content (prices from 2024 in a 2026 guide)
// 3. Suggest related content based on trip context
// 4. Auto-translate to Hindi for regional agents
// 5. Summarize long articles into quick-reference cards
```

### Search & Discovery

```typescript
interface KnowledgeSearch {
  query: string;
  filters: KnowledgeFilter[];
  context?: SearchContext;
}

interface SearchContext {
  currentPage?: string;
  currentTrip?: string;
  customerSegment?: string;
  destination?: string;
  agentRole?: string;
}

// Search features:
// 1. Full-text search with fuzzy matching
// 2. Context-aware: If agent is building a Singapore trip, Singapore guides rank higher
// 3. Autocomplete: Show suggestions as agent types
// 4. Recent searches: Remember last 10 searches
// 5. Popular articles: "Most viewed this week"
// 6. AI-suggested: Based on trip context, suggest relevant articles

// Knowledge surfacing:
// Proactive: When agent starts building a Singapore trip:
// → Show "Singapore Guide" card in the workbench sidebar
// → Show "Singapore visa requirements" if Indian travelers
// → Show "Popular activities in Singapore" for activity selection
//
// Reactive: When agent searches:
// → Full search results with relevance ranking
// → Filter by type (guides, procedures, suppliers)
// → "Did you mean?" for typos
// → "No results? Ask the community" link
```

---

## Open Problems

1. **Content volume vs. quality** — 500 destination guides are useless if half are outdated. Need content quality over quantity.

2. **Knowledge silos** — Experienced agents have knowledge in their heads, not in the system. Incentivizing knowledge sharing is hard.

3. **Destination guide accuracy** — Restaurant closures, new attractions, price changes. Keeping guides current for 100+ destinations is a full-time job.

4. **Search relevance** — "Singapore" could mean the country, the city, the airport, or the airline. Context-aware search is essential.

5. **Content contribution friction** — If contributing knowledge takes more than 5 minutes, agents won't do it. Need frictionless contribution tools.

---

## Next Steps

- [ ] Design knowledge content model with type templates
- [ ] Build context-aware search for knowledge base
- [ ] Create content lifecycle management with staleness detection
- [ ] Design AI-assisted content generation for destination guides
- [ ] Study knowledge management (Notion, Confluence, GitBook)
