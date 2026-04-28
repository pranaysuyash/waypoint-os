# Template & Quick-Start System — Marketplace & Sharing

> Research document for template marketplace, sharing across agencies, and community-driven content.

---

## Key Questions

1. **How do we create a marketplace where agents discover and share templates?**
2. **What's the quality control model for community templates?**
3. **How do we incentivize template creation and sharing?**
4. **What's the licensing model for shared templates?**
5. **How do we track template effectiveness (conversion rate, customer satisfaction)?**

---

## Research Areas

### Marketplace Model

```typescript
interface TemplateMarketplace {
  templates: MarketplaceTemplate[];
  categories: MarketplaceCategory[];
  featured: string[];                 // Featured template IDs
  topRated: string[];
  trending: string[];
  recentlyAdded: string[];
}

interface MarketplaceTemplate {
  templateId: string;
  name: string;
  author: MarketplaceAuthor;
  category: string;
  subcategory: string;
  description: string;
  highlights: string[];
  previewImages: string[];
  sampleItinerary: string;           // Summary view (no full details)
  pricing: MarketplacePricing;
  stats: TemplateStats;
  reviews: TemplateReview[];
  status: MarketplaceStatus;
}

interface MarketplaceAuthor {
  authorId: string;
  name: string;
  type: 'platform' | 'agency' | 'agent';
  verified: boolean;
  templateCount: number;
  totalUsageCount: number;
  averageRating: number;
}

type MarketplaceStatus =
  | 'submitted'                      // Submitted for review
  | 'under_review'                   // Being reviewed by platform
  | 'published'                      // Live on marketplace
  | 'flagged'                        // Quality concern flagged
  | 'deprecated';                    // No longer maintained

// Marketplace categories:
// By Destination: India, Southeast Asia, Europe, Middle East, Americas
// By Theme: Honeymoon, Adventure, Family, Spiritual, Luxury, Budget
// By Duration: Weekend (2-3N), Short (4-5N), Medium (6-8N), Long (9N+)
// By Segment: Corporate, MICE, Group, Solo, Senior Citizen
```

### Template Quality Control

```typescript
interface TemplateQualityReview {
  reviewId: string;
  templateId: string;
  reviewer: string;
  reviewType: ReviewType;
  criteria: QualityCriterion[];
  overallScore: number;
  approved: boolean;
  feedback: string;
  reviewedAt: Date;
}

type ReviewType =
  | 'initial_review'                 // Before marketplace publication
  | 'periodic_review'                // Quarterly quality check
  | 'flag_review'                    // After user flag/report
  | 'version_review';                // After major template update

interface QualityCriterion {
  criterion: string;
  score: number;                     // 1-5
  notes: string;
}

// Quality criteria:
// 1. Itinerary feasibility (Can this actually be done in the stated time?)
//    - Travel times between activities are realistic
//    - Opening hours for activities are correct
//    - Meal times are accounted for
//
// 2. Pricing accuracy (Are prices reasonable and current?)
//    - Prices within ±20% of market rate
//    - Seasonal adjustments documented
//    - No hidden costs
//
// 3. Completeness (Is everything needed included?)
//    - All transfers accounted for
//    - Meal plan specified
//    - Visa requirements noted
//    - Inclusions/exclusions clear
//
// 4. Documentation (Is the template well-documented?)
//    - Clear day-by-day description
//    - Customization points explained
//    - Special notes for agents
//
// 5. Customer experience (Would customers enjoy this?)
//    - Pacing is reasonable (not too rushed)
//    - Variety of activities
//    - Cultural sensitivity
```

### Template Analytics

```typescript
interface TemplateAnalytics {
  templateId: string;
  usage: TemplateUsageStats;
  conversion: TemplateConversionStats;
  quality: TemplateQualityStats;
  revenue: TemplateRevenueStats;
}

interface TemplateUsageStats {
  views: number;
  downloads: number;                  // Agents who used it
  tripsCreated: number;
  tripsCompleted: number;
  activeUsers: number;                // Agents currently using it
}

interface TemplateConversionStats {
  viewToUseRate: number;             // % of viewers who use the template
  useToQuoteRate: number;            // % of uses that become quotes
  quoteToBookRate: number;           // % of quotes that become bookings
  overallConversionRate: number;     // View → Booking
}

interface TemplateQualityStats {
  averageCustomerRating: number;
  averageAgentRating: number;
  complaintRate: number;             // Issues per 100 uses
  revisionRate: number;              // How often agents modify it
  commonModifications: string[];     // What agents typically change
}

interface TemplateRevenueStats {
  totalRevenueGenerated: number;
  averageTripValue: number;
  averageMargin: number;
  repeatBookingRate: number;         // % of customers who book again
}

// Analytics dashboard for template marketplace:
// 1. Most popular templates (by usage and conversion)
// 2. Highest rated templates (by agents and customers)
// 3. Best revenue generators
// 4. Templates that need updates (declining conversion)
// 5. Template usage trends (seasonal patterns)
// 6. Agent leaderboard (who creates the best templates)
```

### Incentive & Licensing

```typescript
interface TemplateLicensing {
  licenseType: LicenseType;
  permissions: LicensePermission[];
  attribution: boolean;
  commercialUse: boolean;
  modifications: boolean;
}

type LicenseType =
  | 'platform_open'                   // Free for all, platform-owned
  | 'agency_private'                  // Agency-specific, not shared
  | 'agency_shared'                   // Shared with specific agencies
  | 'marketplace_free'                // Free on marketplace
  | 'marketplace_paid'                // Premium template (agency pays)
  | 'revenue_share';                  // Creator gets % of booking revenue

// Incentive models:
// 1. Revenue share: Template creator earns 0.5-1% of bookings using their template
// 2. Recognition: "Top Contributor" badges, leaderboard placement
// 3. Performance credits: Template usage counts toward agent KPIs
// 4. Exclusive access: High-rated creators get early access to new features
// 5. Training credit: Creating templates counts toward training requirements

// Anti-spam measures:
// - Templates below quality threshold are rejected
// - Duplicate templates merged (credited to original creator)
// - Template farms (low-quality mass creation) detected and blocked
// - Rating manipulation detected and reversed
```

---

## Open Problems

1. **Template competitive advantage** — Agencies may not want to share their best templates with competitors. Need private-by-default with opt-in sharing.

2. **Pricing transparency** — Marketplace templates show approximate pricing. Actual pricing depends on dates, availability, and negotiation. Managing expectations is key.

3. **Template updates propagation** — When a marketplace template is updated, trips based on the old version aren't automatically updated. Need version communication.

4. **Cultural sensitivity** — A template appropriate for one culture may be insensitive for another. Need cultural review for templates used across regions.

5. **Marketplace governance** — Who decides what goes on the marketplace? Need clear governance with appeal process for rejected templates.

---

## Next Steps

- [ ] Design template marketplace UI and discovery
- [ ] Build template quality review process
- [ ] Create template analytics dashboard
- [ ] Design incentive model for template creators
- [ ] Study marketplace patterns (ThemeForest, Shopify Themes, Notion Templates)
