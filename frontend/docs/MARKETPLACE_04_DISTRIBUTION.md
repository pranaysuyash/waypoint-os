# Travel Marketplace & Aggregator — Distribution & API

> Research document for deal distribution channels, affiliate deal feeds, API marketplace for partners, and multi-channel deal delivery.

---

## Key Questions

1. **How do we distribute deals across multiple channels efficiently?**
2. **What affiliate deal feed formats and APIs are needed?**
3. **How do we build a travel API marketplace for partners?**
4. **What revenue models apply to deal distribution?**
5. **How do we track deal attribution across channels?**

---

## Research Areas

### Multi-Channel Deal Distribution

```typescript
interface DealDistribution {
  channels: DistributionChannel[];
  feed: DealFeed;
  scheduling: DistributionSchedule;
  tracking: AttributionTracking;
}

interface DistributionChannel {
  id: string;
  name: string;
  type: ChannelType;
  format: ChannelFormat;
  audience: ChannelAudience;
  metrics: ChannelMetrics;
}

type ChannelType =
  | 'agency_storefront'                // Own website/app
  | 'whatsapp'                         // WhatsApp Business broadcast
  | 'email'                            // Email newsletter
  | 'affiliate_website'                // Partner travel websites
  | 'social_media'                     // Instagram, Facebook
  | 'api_partner'                      // API-consuming partners
  | 'google_hotels'                    // Google Hotels integration
  | 'meta_search'                      // Skyscanner, Kayak, Trivago
  | 'mobile_push';                     // Push notification

// Channel distribution strategy:
//
// 1. AGENCY STOREFRONT (owned):
//    - Deal section on agency website
//    - Homepage hero deal rotation
//    - Deal category pages (flights, hotels, packages)
//    - Personalized deals based on browsing/search history
//    Conversion rate: 3-5% (highest — warm, targeted audience)
//
// 2. WHATSAPP (owned, high engagement in India):
//    - Deal broadcast to segmented lists
//    - Rich message with image + price + book button
//    - Interactive catalog for browsing deals
//    - Quick reply templates for deal inquiries
//    Conversion rate: 2-4% (high engagement, personal channel)
//
// 3. EMAIL (owned):
//    - Weekly "Travel Deals" newsletter
//    - Personalized deal alerts (based on past searches)
//    - Flash deal alerts (time-sensitive)
//    - Seasonal deal roundups
//    Conversion rate: 1-2% (lower, but scalable)
//
// 4. SOCIAL MEDIA (owned):
//    - Instagram: Deal carousel posts, Reels for flash deals
//    - Facebook: Deal posts, targeted ads to lookalike audiences
//    - YouTube: Deal announcement shorts
//    Conversion rate: 0.5-1% (discovery, broad reach)
//
// 5. META-SEARCH (earned/paid):
//    - Google Hotels: Direct booking integration
//    - Skyscanner: Flight + hotel deals
//    - Trivago: Hotel price comparison
//    - Kayak: Deal inclusion
//    Conversion rate: 0.3-0.8% (high volume, low conversion)
//    Cost: CPC or commission per booking
//
// 6. API PARTNERS (partner):
//    - JSON/XML deal feed for affiliate websites
//    - White-label deal widget for partner embedding
//    - Webhook for real-time deal notifications
//    Conversion rate: 0.5-1.5% (varies by partner quality)

interface DealFeed {
  format: FeedFormat;
  schema: DealFeedSchema;
  delivery: FeedDelivery;
  authentication: FeedAuth;
}

type FeedFormat = 'json' | 'xml' | 'rss' | 'csv';

// Deal feed schema (JSON):
// {
//   "feed_version": "2.1",
//   "generated_at": "2026-04-28T10:00:00Z",
//   "expires_at": "2026-04-28T22:00:00Z",
//   "total_deals": 47,
//   "deals": [
//     {
//       "id": "deal_kerala_5n_oct",
//       "type": "package",
//       "title": "Kerala Backwaters 5N — ₹35,000/person",
//       "description": "5 nights covering Kochi, Munnar, Alleppey...",
//       "original_price": 48000,
//       "deal_price": 35000,
//       "currency": "INR",
//       "savings": 13000,
//       "savings_percent": 27,
//       "valid_from": "2026-04-28",
//       "valid_to": "2026-05-15",
//       "travel_by": "2026-09-30",
//       "destinations": ["kochi", "munnar", "alleppey"],
//       "inclusions": ["5 nights accommodation", "breakfast", "houseboat", "transfers"],
//       "images": ["https://cdn.../kerala_hero.webp"],
//       "book_url": "https://agency.com/deals/kerala-5n?ref=affiliate_123",
//       "terms": "Min 2 travelers. Select dates only. Non-refundable.",
//       "urgency": "high",
//       "inventory_remaining": 12,
//       "categories": ["honeymoon", "family", "nature"]
//     }
//   ]
// }

// Feed delivery options:
// 1. Pull: Partner fetches feed URL every 15 minutes
// 2. Push (webhook): System POSTs new deals to partner endpoint
// 3. Streaming: WebSocket for real-time deal updates
// 4. API: RESTful endpoints for filtered deal queries
//
// Feed update frequency:
// Hot deals (flash sale): Every 5 minutes
// Standard deals: Every 15 minutes
// Price updates: Every 30 minutes
// Full feed refresh: Every 6 hours
```

### Affiliate Program Architecture

```typescript
interface AffiliateProgram {
  partners: AffiliatePartner[];
  tracking: AffiliateTracking;
  commissions: CommissionStructure;
  tools: AffiliateTools;
  fraudPrevention: AffiliateFraudPrevention;
}

interface AffiliatePartner {
  id: string;
  name: string;
  type: AffiliateType;
  website: string;
  traffic: number;                     // Monthly unique visitors
  conversionRate: number;
  status: 'pending' | 'active' | 'suspended' | 'terminated';
  joinedAt: Date;
  commissionsEarned: number;
  commissionsPaid: number;
}

type AffiliateType =
  | 'travel_blog'                      // Travel content website
  | 'deal_aggregator'                  // Deal comparison site
  | 'corporate_portal'                 // Company intranet travel section
  | 'influencer'                       // Social media influencer
  | 'sub_agent'                        // Sub-agent / referral partner
  | 'loyalty_program'                  // Points/miles program integration
  | 'media_partner';                   // Newspaper, magazine, media

// Affiliate commission structure:
// Travel blog: 5% of booking value (content-driven, high intent)
// Deal aggregator: 3% of booking value (price-driven, lower intent)
// Corporate portal: 4% of booking value (steady volume)
// Influencer: 7% of booking value (lower volume, higher trust)
// Sub-agent: 8-12% of booking value (highest, ongoing relationship)
//
// Commission tiers (performance-based):
// Bronze: <10 bookings/month → Base rate
// Silver: 10-50 bookings/month → Base + 1%
// Gold: 50-200 bookings/month → Base + 2%
// Platinum: 200+ bookings/month → Base + 3% + dedicated account manager
//
// Cookie duration: 30 days (last-click attribution)
// Conversion window: Booking completed within 30 days of click
// Multi-touch: First-click gets 30%, last-click gets 70% (if enabled)

interface AffiliateTracking {
  methods: TrackingMethod[];
  attribution: AttributionModel;
  validation: ConversionValidation;
  reporting: AffiliateReporting;
}

// Tracking methods:
// 1. Referral link: Unique URL with partner ID parameter
//    https://agency.com/deals/kerala?ref=aff_123&utm_source=partner_name
//
// 2. Coupon code: Unique discount code per partner
//    "PARTNER10" → 10% off + ₹200 commission to partner
//    Tracks redemption without cookie dependency
//
// 3. Pixel tracking: Post-booking pixel on confirmation page
//    Partner places pixel, fires on successful booking
//    Used for conversion validation
//
// 4. Deep link: Direct link to specific deal/hotel
//    https://agency.com/hotel/taj-palace-mumbai?ref=aff_123
//
// 5. API attribution: Partner makes booking via API with their credentials
//    Commission automatically tracked in API key

// Affiliate fraud prevention:
// - Self-referral detection: Same person clicking own affiliate link
// - Cookie stuffing: Prevent fraudulent cookie insertion
// - Click spamming: Detect abnormal click patterns
// - Fake booking: Cancel after commission credited (hold 30 days)
// - Brand bidding: Prevent affiliates bidding on agency brand keywords
// - Verification: Cross-reference bookings with actual travel
//
// Affiliate tools:
// - Deal widget: Embeddable deal carousel for partner websites
// - Search widget: Inline flight/hotel search form
// - Banner ads: Pre-designed promotional banners
// - Deep link generator: Create tracked links for any page
// - Dashboard: Real-time clicks, conversions, commissions
// - API: Full deal search and booking API for technical partners
```

### API Marketplace for Partners

```typescript
interface TravelAPIMarketplace {
  apis: TravelAPI[];
  access: APIAccess;
  billing: APIBilling;
  documentation: APIDocumentation;
  sandbox: APISandbox;
}

interface TravelAPI {
  name: string;                        // "Deal Search API"
  version: string;                     // "v2"
  description: string;
  endpoints: APIEndpoint[];
  rateLimit: RateLimit;
  pricing: APIPricing;
  sla: SLAConfig;
}

// API marketplace endpoints:
//
// DEAL SEARCH:
// GET /api/v2/deals?destination=kerala&type=package&min_savings=20
// Response: Paginated list of active deals
// Rate limit: 100 requests/minute
// Pricing: Free (basic), ₹0.10/request (premium with real-time)
//
// HOTEL SEARCH:
// GET /api/v2/hotels?city=mumbai&checkin=2026-10-15&checkout=2026-10-16
// Response: Hotel list with rates from all sources
// Rate limit: 60 requests/minute
// Pricing: ₹0.05/search, ₹0.50/booked (success-based)
//
// FLIGHT SEARCH:
// GET /api/v2/flights?origin=DEL&destination=BOM&date=2026-10-15
// Response: Flight options with fares
// Rate limit: 30 requests/minute
// Pricing: ₹0.10/search (GDS fees passed through)
//
// BOOKING:
// POST /api/v2/bookings
// Body: Hotel/flight booking details
// Response: Booking confirmation
// Pricing: ₹25 per successful booking
//
// PRICE ALERTS:
// POST /api/v2/alerts
// Body: Alert configuration
// Response: Alert ID + webhook for notifications
// Pricing: Free (up to 100 alerts), ₹0.01/alert after
//
// DESTINATION CONTENT:
// GET /api/v2/destinations/:slug
// Response: Full destination guide data
// Pricing: Free (basic), ₹0.02/request (full content)

// API access tiers:
// Free: 1,000 requests/month, standard rate limits
// Starter: ₹5,000/month, 10,000 requests, priority rate limits
// Growth: ₹15,000/month, 50,000 requests, dedicated support
// Enterprise: ₹50,000/month, unlimited, SLA, dedicated infrastructure
//
// API documentation:
// Interactive API explorer (Swagger UI)
// Code samples in Python, JavaScript, PHP, cURL
// Webhook event catalog
// SDK: npm package, PyPI package
// Changelog and versioning policy
//
// API sandbox:
// Full API mirror with test data
// Simulated booking confirmations
// Error simulation for testing
// No rate limits in sandbox
// Free for all registered developers
```

---

## Open Problems

1. **Attribution accuracy** — Multi-touch attribution across channels (affiliate click → Google search → direct visit → booking) is complex. Last-click attribution is standard but unfair to top-of-funnel channels.

2. **API pricing sustainability** — API costs (GDS fees, infrastructure, support) must be covered by API revenue. Pricing too high limits adoption; pricing too low loses money on heavy users.

3. **Partner quality control** — Low-quality affiliate sites can damage brand reputation through misleading deal presentation, fake reviews, or poor user experience. Vetting and monitoring partners is essential but labor-intensive.

4. **Deal distribution latency** — Flash deals need to reach all channels within minutes. Batch-based distribution (email, RSS) introduces delays. Real-time push (webhooks, WebSocket) is needed for time-sensitive deals.

5. **Cross-border deal distribution** — Deals targeting Indian travelers may appear on international partner sites. Currency conversion, localization, and regulatory compliance (advertising standards) must be handled per market.

---

## Next Steps

- [ ] Build multi-channel deal distribution pipeline with real-time push
- [ ] Create affiliate program with tracking, commission, and fraud prevention
- [ ] Design API marketplace with tiered access and billing
- [ ] Implement attribution tracking across channels
- [ ] Study distribution platforms (Travelpayouts, CJ Affiliate, PartnerStack, RapidAPI)
