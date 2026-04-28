# Agency Marketplace & Storefront — Platform Architecture

> Research document for public-facing agency storefront platform, multi-tenant hosting, and storefront infrastructure.

---

## Key Questions

1. **What's the architecture for a public-facing agency storefront?**
2. **How do we host multiple agency storefronts on one platform?**
3. **What's the custom domain strategy for storefronts?**
4. **How do storefronts connect to the agent workbench?**
5. **What's the performance model for storefronts?**

---

## Research Areas

### Storefront Architecture

```typescript
interface StorefrontConfig {
  agencyId: string;
  storefrontId: string;
  domain: string;                     // travel.acme.com or acmetravel.com
  status: StorefrontStatus;
  branding: StorefrontBranding;
  features: StorefrontFeatures;
  seo: SEOConfig;
  analytics: StorefrontAnalytics;
}

type StorefrontStatus =
  | 'draft'                           // Being designed, not live
  | 'preview'                         // Preview mode, not indexed
  | 'live'                            // Publicly accessible
  | 'maintenance'                     // Temporarily offline
  | 'suspended';                      // Suspended for policy violation

interface StorefrontBranding {
  agencyName: string;
  tagline: string;
  logo: string;
  heroImage: string;
  primaryColor: string;
  fontFamily: string;
  favicon: string;
  socialSharingImage: string;         // OG image for social media
  contactInfo: {
    phone: string;
    email: string;
    whatsapp: string;
    address: string;
  };
  socialLinks: SocialLink[];
}

// Storefront pages:
// 1. Homepage — Hero, featured trips, search, trust signals
// 2. Trip Catalog — Browse all published trips, filter, search
// 3. Trip Detail — Full itinerary, pricing, photos, reviews, book
// 4. Destination Pages — Destination info, available trips, guides
// 5. About Us — Agency story, team, certifications, testimonials
// 6. Contact — Contact form, WhatsApp link, office location
// 7. Blog — Travel articles, destination guides, tips (SEO)
// 8. FAQ — Common questions, policies, payment info
//
// Storefront vs. Workbench relationship:
// Storefront (public-facing):
//   - Customers browse and book trips
//   - No login required to browse
//   - Login for saved trips, booking history, preferences
//   - SEO-optimized, indexed by search engines
//   - Read-heavy, CDN-cacheable
//
// Workbench (agent-facing):
//   - Agents manage trips, customers, and bookings
//   - Login required
//   - Not indexed by search engines
//   - Write-heavy, real-time
//
// Data flow:
// Agent creates trip in Workbench → Publishes to Storefront
//   → Customer browses on Storefront → Inquires or books
//   → Inquiry appears in Workbench inbox → Agent responds
//   → Booking confirmed in Workbench → Customer notified

interface StorefrontFeatures {
  enableSearch: boolean;
  enableOnlineBooking: boolean;
  enableWhatsApp: boolean;
  enableBlog: boolean;
  enableReviews: boolean;
  enableDestinations: boolean;
  enableCompare: boolean;
  enableWishlist: boolean;
  enableCustomPages: boolean;
  maxPublishedTrips: number;
}

// Feature tiers:
// Starter: 10 published trips, basic pages, WhatsApp contact
// Professional: 50 published trips, online booking, blog, reviews
// Enterprise: Unlimited trips, custom pages, API access, white-label
```

### Multi-Tenant Storefront Hosting

```typescript
interface StorefrontHosting {
  model: HostingModel;
  routing: DomainRouting;
  deployment: StorefrontDeployment;
  cdn: CDNConfig;
  ssl: SSLConfig;
}

type HostingModel =
  | 'subdomain'                       // agency.travelplatform.com
  | 'custom_domain'                   // travel.acme.com
  | 'path_based';                     // travelplatform.com/acme (not recommended)

// Domain routing:
// 1. Customer visits travel.acme.com
// 2. DNS CNAME → travelplatform.com (our infrastructure)
// 3. Edge server resolves domain → agencyId
// 4. Load agency storefront config
// 5. Render storefront with agency branding
// 6. Serve from CDN (static assets) + Edge (dynamic content)
//
// Technical implementation:
// - Edge routing: Cloudflare Workers / Vercel Edge Functions
// - Storefront config: Loaded from Redis (sub-millisecond lookup)
// - Static assets: CDN (agency logos, hero images, fonts)
// - Dynamic content: Next.js ISR (Incremental Static Regeneration)
// - Revalidation: 60 seconds for trip listings, on-demand for updates
//
// SSL management:
// - Subdomain: Wildcard SSL (*.travelplatform.com)
// - Custom domain: Let's Encrypt auto-provisioned per domain
// - SSL renewal: Automated 30 days before expiry
// - HTTP → HTTPS redirect: Enforced
// - HSTS headers: Enabled

interface StorefrontDeployment {
  build: StorefrontBuild;
  caching: StorefrontCaching;
  performance: PerformanceConfig;
}

// Build and deployment:
// - Single Next.js application serves all storefronts
// - Agency config loaded at request time (not build time)
// - Static pages pre-built for SEO (ISR)
// - Dynamic pages rendered at edge (personalized content)
//
// Performance targets:
// - Time to First Byte (TTFB): <200ms (CDN edge)
// - Largest Contentful Paint (LCP): <2.5s
// - First Input Delay (FID): <100ms
// - Cumulative Layout Shift (CLS): <0.1
// - Lighthouse Performance: >90
//
// Caching strategy:
// - Static assets (CSS, JS, images): 1 year, content-hash
// - Trip listing pages: ISR, 60-second revalidation
// - Trip detail pages: ISR, on-demand revalidation on publish
// - API responses: 5-minute cache, stale-while-revalidate
// - Search results: No cache (always fresh)
// - Agency config: Redis, 5-minute TTL
```

### Storefront-Workbench Bridge

```typescript
interface StorefrontWorkbenchBridge {
  inquiryFlow: InquiryFlow;
  bookingFlow: BookingFlow;
  tripSync: TripSync;
  inventorySync: InventorySync;
}

interface InquiryFlow {
  source: 'storefront_form' | 'storefront_whatsapp' | 'storefront_call';
  destination: WorkbenchDestination;
  enrichment: InquiryEnrichment;
}

// Inquiry flow:
// 1. Customer fills inquiry form on storefront
//    - Name, phone, email, travel dates, destinations, budget, travelers
// 2. Inquiry enriched with source data
//    - UTM parameters (campaign tracking)
//    - Referrer page (which trip/destination page)
//    - Device and location
//    - Time on site, pages viewed
// 3. Inquiry creates packet in Workbench inbox
//    - Auto-tagged with source: "Storefront"
//    - Pre-filled with customer data
//    - Linked to trip template if inquiring about specific trip
// 4. Agent receives notification (in-app + WhatsApp)
// 5. Agent responds from Workbench (reply goes to customer's WhatsApp/email)

interface TripSync {
  publishTrip(tripId: string): StorefrontTrip;
  unpublishTrip(tripId: string): void;
  updatePricing(tripId: string, pricing: Pricing): void;
  updateAvailability(tripId: string, availability: Availability): void;
}

// Trip publishing workflow:
// Agent creates trip in Workbench
//   → Reviews trip details and pricing
//   → Clicks "Publish to Storefront"
//   → Chooses storefront-specific settings:
//     - Display price: "Starting from ₹XX,XXX" or exact pricing
//     - Availability: Available dates, inventory count
//     - Custom description: Marketing copy (different from internal notes)
//     - Photos: Upload marketing photos (different from supplier photos)
//     - SEO: Meta title, description, keywords
//   → Trip appears on storefront within 60 seconds
//   → Agent can unpublish or update at any time
//
// Price display options:
// - "Starting from ₹45,000 per person" (for template trips)
// - Exact price per date (for fixed-departure trips)
// - "Contact for pricing" (for complex/custom trips)
// - Price range (₹45,000 - ₹65,000 per person)

interface BookingFlow {
  mode: BookingMode;
  steps: BookingStep[];
  payment: BookingPayment;
  confirmation: BookingConfirmation;
}

type BookingMode =
  | 'full_online'                     // Complete booking and payment online
  | 'inquiry_only'                    // Customer inquires, agent finalizes
  | 'hybrid';                         // Customer books, agent confirms

// Booking flow (full online):
// 1. Customer selects trip on storefront
// 2. Chooses dates, travelers, options
// 3. Reviews itinerary and pricing
// 4. Enters traveler details (name, age, passport)
// 5. Payment (Razorpay/PhonePe gateway)
// 6. Booking confirmed (provisional)
// 7. Agent reviews in Workbench
// 8. Agent confirms or requests changes
// 9. Customer receives confirmation (email + WhatsApp)
//
// Booking flow (inquiry only):
// 1. Customer browses trips
// 2. Clicks "Get Quote" or "Contact Us"
// 3. Fills inquiry form (name, phone, requirements)
// 4. Inquiry appears in Workbench
// 5. Agent responds with customized quote
// 6. Booking proceeds via Workbench
//
// Agency chooses mode per trip or globally
```

### Storefront Analytics

```typescript
interface StorefrontAnalytics {
  traffic: TrafficAnalytics;
  conversion: ConversionAnalytics;
  engagement: EngagementAnalytics;
  seo: SEOAnalytics;
}

interface TrafficAnalytics {
  totalVisitors: number;
  uniqueVisitors: number;
  pageViews: number;
  bounceRate: number;
  avgSessionDuration: string;
  topSources: TrafficSource[];
  topPages: PageAnalytics[];
  deviceBreakdown: DeviceBreakdown;
  geoBreakdown: GeoBreakdown;
}

// Traffic tracking:
// - Google Analytics 4 integration (agency's own GA property)
// - Privacy-compliant tracking (no PII, consent banner)
// - UTM parameter tracking for marketing campaigns
// - Conversion tracking: Visit → Inquiry → Booking
//
// Key conversion metrics:
// Visit to inquiry rate: 5-10% (industry average for travel)
// Inquiry to booking rate: 15-25% (agency-dependent)
// Visit to booking rate: 0.75-2.5% (compound conversion)
// Average order value: ₹45,000-2,00,000 (trip-dependent)
// Cart abandonment: 60-70% (travel industry average)
//
// Funnel visualization:
// ┌──────────────────────────────────────┐
// │  Storefront Conversion Funnel         │
// │                                      │
// │  Visits:        10,000  ████████████ │
// │  Trip Views:     4,500  ██████████   │
// │  Inquiries:        450  ████         │
// │  Quotes Sent:      315  ███          │
// │  Bookings:          95  █            │
// │                                      │
// │  Visit→Inquiry: 4.5%                 │
// │  Inquiry→Book:  21.1%                │
// │  Overall:       0.95%                │
// └──────────────────────────────────────┘
```

---

## Open Problems

1. **SEO at scale** — 100 agency storefronts competing for the same keywords. Need strategies for differentiation without cannibalization.

2. **Content quality** — Agencies vary wildly in marketing capability. Some storefronts will look professional; others will look amateur. Need templates and guardrails.

3. **Payment liability** — Online bookings through storefront create payment liability. Who holds the money — platform or agency? Escrow model needed.

4. **Performance isolation** — One agency's traffic spike (marketing campaign) shouldn't slow down other agency storefronts. Need per-tenant rate limiting.

5. **Data ownership** — Customer browsing data on the storefront — does it belong to the agency or the platform? Need clear data ownership terms.

---

## Next Steps

- [ ] Design multi-tenant storefront hosting architecture
- [ ] Build storefront-workbench bridge for trip publishing and inquiries
- [ ] Create storefront analytics dashboard with conversion tracking
- [ ] Design custom domain provisioning and SSL management
- [ ] Study storefront platforms (Shopify, Squarespace, Wix, Book Like A Boss)
