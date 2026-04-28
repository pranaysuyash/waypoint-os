# Agency Marketplace & Storefront — SEO & Marketing

> Research document for storefront SEO, social sharing, content marketing, and customer acquisition strategies.

---

## Key Questions

1. **How do we optimize agency storefronts for search engines?**
2. **What social sharing and viral features drive customer acquisition?**
3. **How do we use content marketing (blog, guides) for organic traffic?**
4. **What's the UTM and campaign tracking model?**
5. **How do we help agencies with limited marketing expertise?**

---

## Research Areas

### SEO Architecture

```typescript
interface StorefrontSEO {
  technical: TechnicalSEO;
  onPage: OnPageSEO;
  local: LocalSEO;
  content: ContentSEO;
  analytics: SEOAnalytics;
}

interface TechnicalSEO {
  sitemap: SitemapConfig;
  robotsTxt: RobotsTxtConfig;
  structuredData: StructuredDataConfig;
  pageSpeed: PageSpeedConfig;
  mobileOptimization: MobileSEOConfig;
  internationalization: InternationalSEOConfig;
}

// Technical SEO requirements:
//
// Sitemap:
// - Auto-generated sitemap.xml per agency storefront
// - Includes: Homepage, trip listings, trip details, destinations, blog posts
// - Priority: Homepage (1.0), Trip details (0.8), Destinations (0.7), Blog (0.6)
// - Update frequency: Daily for trip listings, Weekly for blog posts
// - Submitted to Google Search Console automatically
//
// Structured Data (JSON-LD):
// - Trip: Product schema with offers, ratings, availability
// - Agency: LocalBusiness schema with name, address, phone, hours
// - Reviews: AggregateRating schema on trip pages
// - FAQ: FAQPage schema for trip FAQ sections
// - Breadcrumbs: BreadcrumbList schema for navigation
// - Blog: Article schema with author, dateModified, image
//
// Page speed:
// - Core Web Vitals must pass (LCP < 2.5s, FID < 100ms, CLS < 0.1)
// - Image optimization: WebP with fallback, lazy loading, srcset
// - Code splitting: Per-page bundles, shared vendor chunk
// - Font optimization: Preload critical fonts, font-display: swap
// - Critical CSS: Inline above-fold CSS, async load rest
//
// Mobile:
// - Mobile-first indexing (Google indexes mobile version)
// - Touch-friendly UI (minimum 44px touch targets)
// - No interstitials or pop-ups that block content
// - Fast loading on 4G connections (< 3s)
// - AMP not required (responsive is sufficient)

interface OnPageSEO {
  titleTemplates: TitleTemplate[];
  metaDescriptionTemplates: MetaDescriptionTemplate[];
  urlStructure: URLStructure;
  headingStructure: HeadingStructure;
  imageOptimization: ImageSEOConfig;
  internalLinking: InternalLinkingConfig;
}

// SEO templates (auto-generated from trip data):
//
// Title templates:
// Homepage: "{Agency Name} — Trusted Travel Agency in {City}"
// Trip listing: "{Trip Name} | {Duration} | {Agency Name}"
// Trip detail: "{Trip Name} — {Destination} Tour Package | {Agency Name}"
// Destination: "Best {Destination} Tour Packages | {Agency Name}"
// Blog: "{Blog Title} | {Agency Name} Travel Blog"
//
// Meta description templates:
// Trip: "Book {Trip Name} ({Duration}) starting from ₹{Price}. {Highlights}. Trusted by {ReviewCount}+ travelers. Book now with {Agency Name}!"
// Destination: "Explore {Destination} with curated tour packages from {Agency Name}. {Description}. Best prices guaranteed."
//
// URL structure:
// Homepage: travel.agency.com/
// Trips: travel.agency.com/trips/{trip-slug}
// Destinations: travel.agency.com/destinations/{destination-slug}
// Blog: travel.agency.com/blog/{post-slug}
// Category: travel.agency.com/trips/{category-slug}

interface LocalSEO {
  googleBusinessProfile: GBPConfig;
  localKeywords: string[];
  localContent: LocalContentStrategy;
  reviews: ReviewStrategy;
}

// Local SEO (critical for Indian travel agencies):
// Google Business Profile:
//   - Verified business listing
//   - Accurate address, phone, hours
//   - Trip photos uploaded regularly
//   - Respond to all reviews within 24 hours
//   - Post updates (new trips, offers) weekly
//   - Q&A section monitored
//
// Local keywords to target:
//   - "travel agency in {city}"
//   - "tour packages from {city}"
//   - "{destination} tour from {city}"
//   - "honeymoon packages {city}"
//   - "visa agent {city}"
//   - "flight booking {city}"
//   - "best travel agency {city}"
//
// Example: Agency in Delhi
//   - "travel agency in Delhi"
//   - "Kerala tour packages from Delhi"
//   - "honeymoon packages Delhi"
//   - "Goa tour package from Delhi"
//   - "international tour packages Delhi"
```

### Social Sharing & Virality

```typescript
interface SocialSharing {
  platforms: SocialPlatform[];
  shareContent: ShareContentConfig;
  referral: ReferralProgram;
  viralFeatures: ViralFeature[];
}

type SocialPlatform =
  | 'whatsapp'                        // Primary in India
  | 'instagram'                       // Visual travel content
  | 'facebook'                        // Family/group sharing
  | 'twitter'                         // Quick shares
  | 'linkedin'                        // Corporate travel
  | 'telegram';                       // Group coordination

interface ShareContentConfig {
  tripShare: TripShareContent;
  bookingShare: BookingShareContent;
  reviewShare: ReviewShareContent;
  blogShare: BlogShareContent;
}

interface TripShareContent {
  title: string;                      // "Check out this Kerala trip!"
  description: string;                // Auto-generated from trip highlights
  image: string;                      // Hero image with agency branding
  link: string;                       // Deep link to trip page
  whatsappMessage: string;            // Pre-filled WhatsApp message
}

// WhatsApp sharing (primary channel in India):
// Pre-filled message: "Hey! Check out this Kerala Backwaters trip I found on {Agency}. 5 nights, starting from ₹18,500! {link}"
//
// Instagram sharing:
// Trip image → Instagram Story with swipe-up link
// Story template: Trip photo + "Swipe up to book" + agency branding
//
// WhatsApp Status:
// "Just booked my Kerala trip with {Agency}! 5 days of backwaters and hills 🌴🛶 {link}"

interface ReferralProgram {
  enabled: boolean;
  reward: ReferralReward;
  mechanics: ReferralMechanics;
  tracking: ReferralTracking;
}

interface ReferralReward {
  referrerReward: ReferralRewardType;
  refereeReward: ReferralRewardType;
}

type ReferralRewardType =
  | { type: 'discount'; amount: Money; applicableTo: string[] }
  | { type: 'cashback'; amount: Money }
  | { type: 'upgrade'; description: string };

// Referral program:
// "Refer a friend, both get ₹1,000 off"
// Referrer shares unique link with friend
// Friend books through link → Both get ₹1,000 discount
// Referral code tracked in URL: ?ref=SHARE123
// Limit: 5 referrals per customer per year
// Reward applies to next booking only
//
// Referral analytics:
// - Total referral links generated
// - Clicks per link
// - Conversion rate (click → booking)
// - Revenue from referrals
// - Top referrers leaderboard

interface ViralFeature {
  feature: string;
  trigger: string;
  reward?: string;
}

// Viral features:
// 1. "Trip Countdown" — Customer shares trip countdown on social media
//    Trigger: 7 days before departure
//    Reward: ₹500 add-on credit for each share
//
// 2. "Group Booking Invite" — Customer invites friends to join group trip
//    Trigger: Customer starts group booking
//    Reward: ₹1,000 discount per friend who joins
//
// 3. "Review with Photo" — Customer posts trip review with photos
//    Trigger: Post-trip review request
//    Reward: ₹500 credit for photo review, ₹200 for text-only
//
// 4. "Travel Story" — Customer creates mini-blog of their trip
//    Trigger: Post-trip engagement email
//    Reward: Feature on agency homepage + ₹1,000 credit
```

### Content Marketing

```typescript
interface ContentMarketing {
  blog: BlogPlatform;
  destinationGuides: DestinationGuide[];
  emailMarketing: EmailMarketingConfig;
  socialContent: SocialContentCalendar;
}

interface BlogPlatform {
  enabled: boolean;
  posts: BlogPost[];
  categories: BlogCategory[];
  authors: BlogAuthor[];
  scheduling: BlogSchedule;
}

// Blog content strategy:
// Categories: Destination Guides, Travel Tips, Visa Info, Budget Travel,
//             Luxury Travel, Family Travel, Honeymoon, Adventure, Food & Culture
//
// Content calendar (per agency):
// 2-4 blog posts per month (manageable for agents)
//
// Post types:
// 1. Destination deep-dive (1500-2000 words)
//    "Complete Guide to Kerala Backwaters: Best Time, Routes, Houseboats"
//    SEO value: High (targets "Kerala backwaters guide")
//
// 2. Listicle (800-1200 words)
//    "10 Best Honeymoon Destinations in India Under ₹50,000"
//    SEO value: Medium (targets "honeymoon destinations India")
//
// 3. How-to guide (1000-1500 words)
//    "How to Apply for Schengen Visa from India: Step-by-Step Guide"
//    SEO value: High (targets "Schengen visa India")
//
// 4. Trip report (800-1200 words)
//    "Our Customer's Bali Honeymoon: Day-by-Day Experience"
//    SEO value: Medium (social sharing value)
//
// AI-assisted content creation:
// Agent provides: Destination, topic, key points
// AI generates: Draft blog post with SEO optimization
// Agent reviews: Edits, adds personal experience, approves
// Platform optimizes: Meta tags, internal links, schema markup

interface DestinationGuide {
  destinationId: string;
  slug: string;
  title: string;
  sections: GuideSection[];
  seo: GuideSEO;
  relatedTrips: string[];             // Link to published trips
}

type GuideSection =
  | { type: 'overview'; content: string }
  | { type: 'best_time'; monthlyBreakdown: MonthlyInfo[] }
  | { type: 'how_to_reach'; options: TransportOption[] }
  | { type: 'top_attractions'; attractions: Attraction[] }
  | { type: 'food_guide'; restaurants: RestaurantRec[] }
  | { type: 'itinerary_suggestions'; itineraries: SuggestedItinerary[] }
  | { type: 'tips'; tips: TravelTip[] }
  | { type: 'photos'; gallery: PhotoGalleryConfig }
  | { type: 'faqs'; questions: FAQ[] }

// Destination guides serve dual purpose:
// 1. SEO: Rank for "Kerala travel guide" → Drive organic traffic
// 2. Sales: Guide links to agency's published trips → Convert visitors
//
// Guide → Trip conversion:
// "Kerala Travel Guide" page includes:
// - "Ready to visit Kerala? Check out our curated trips:"
//   [Kerala Backwaters 5N] [Kerala Hills & Beaches 7N] [Kerala Honeymoon 6N]
// - "Not sure which trip? WhatsApp us for personalized recommendations"
```

### Campaign Tracking

```typescript
interface CampaignTracking {
  utm: UTMConfig;
  campaigns: MarketingCampaign[];
  attribution: AttributionModel;
  roi: CampaignROI;
}

interface UTMConfig {
  templates: UTMTemplate[];
  autoTagging: boolean;
  shortLinks: boolean;
  qrCodes: boolean;
}

// UTM templates:
// Google Ads: utm_source=google&utm_medium=cpc&utm_campaign={trip_type}_{city}
// Facebook Ads: utm_source=facebook&utm_medium=social&utm_campaign={offer}
// WhatsApp: utm_source=whatsapp&utm_medium=chat&utm_campaign={referral_code}
// Instagram: utm_source=instagram&utm_medium=social&utm_campaign={destination}
// Email: utm_source=email&utm_medium=newsletter&utm_campaign={campaign_name}
//
// Short links:
// travel.agency.com/go/kerela-offer → travel.agency.com/trips/kerala-backwaters?utm_...
// QR codes: For print materials, business cards, brochures
// Each short link tracks: clicks, device, location, conversion

interface AttributionModel {
  model: AttributionType;
  window: number;                     // Attribution window in days
  touchpoints: Touchpoint[];
}

type AttributionType =
  | 'first_touch'                     // Credit to first channel
  | 'last_touch'                      // Credit to last channel (simplest)
  | 'linear'                          // Equal credit to all touchpoints
  | 'time_decay';                     // More credit to recent touchpoints

// Customer journey tracking:
// Touchpoint 1: Google search "Kerala tour packages" → Visits storefront
// Touchpoint 2: Reads "Kerala Travel Guide" blog post
// Touchpoint 3: WhatsApp inquiry about Kerala trip
// Touchpoint 4: WhatsApp follow-up from agent
// Touchpoint 5: Returns to storefront via email link → Books trip
//
// Attribution: Which channel gets credit for the ₹37,000 booking?
// Last-touch: Email (final click before booking)
// First-touch: Google (initial discovery)
// Linear: Equal credit to all 5 touchpoints
// Time-decay: More credit to WhatsApp and email (recent)
//
// Recommended: Time-decay model (most accurate for travel decisions)

// Campaign ROI dashboard:
// ┌──────────────────────────────────────────────┐
// │  Marketing ROI — This Month                   │
// │                                              │
// │  Channel    Spend   Revenue   ROI   Bookings │
// │  Google     ₹15K    ₹1.8L    12x    8       │
// │  Facebook   ₹8K     ₹0.9L    11x    4       │
// │  WhatsApp   ₹0      ₹2.1L    ∞     11       │
// │  Instagram  ₹5K     ₹0.4L    8x     2       │
// │  Referrals  ₹2K     ₹1.2L    60x    6       │
// │  Email      ₹0      ₹0.7L    ∞     3        │
// │                                              │
// │  Total      ₹30K    ₹7.1L    23.7x  34      │
// │                                              │
// │  [Best Performing: Referrals]                │
// │  [Needs Attention: Instagram]                │
// └──────────────────────────────────────────────┘
```

---

## Open Problems

1. **SEO cannibalization** — Multiple agencies targeting the same keywords ("Kerala tour packages"). Platform needs to avoid internal competition in search results.

2. **Content quality at scale** — 100 agencies writing blog posts means 100 potential content quality levels. Need quality gate without being gatekeeper.

3. **WhatsApp as marketing channel** — WhatsApp has strict anti-spam policies. Business API has template restrictions. Can't send unsolicited marketing messages.

4. **Attribution complexity** — Travel purchase decisions involve multiple touchpoints over weeks. Simple last-touch attribution undervalies awareness channels.

5. **Local language SEO** — Hindi, Tamil, Bengali SEO for regional agencies. Content in local languages ranks differently and has different keyword volumes.

---

## Next Steps

- [ ] Design SEO architecture with structured data and sitemaps
- [ ] Build social sharing with WhatsApp-first strategy
- [ ] Create content marketing platform with AI-assisted blog writing
- [ ] Design campaign tracking with attribution modeling
- [ ] Study travel SEO (MakeMyTrip SEO strategy, TripAdvisor content, Booking.com SEO)
