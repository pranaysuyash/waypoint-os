# Agency Marketplace & Storefront — Trip Catalog & Listings

> Research document for trip catalog management, search and discovery, trip detail pages, and listing optimization.

---

## Key Questions

1. **How do we structure the trip catalog for browsing and search?**
2. **What information appears on trip listing and detail pages?**
3. **How do we handle pricing display for published trips?**
4. **What filtering and sorting options do customers need?**
5. **How do we optimize trip listings for conversion?**

---

## Research Areas

### Trip Catalog Model

```typescript
interface StorefrontTrip {
  tripId: string;
  agencyId: string;
  storefrontId: string;
  status: 'published' | 'draft' | 'archived' | 'sold_out';
  slug: string;                       // URL-friendly: kerala-backwaters-5-days
  title: string;
  subtitle: string;
  type: TripListingType;
  category: TripCategory[];
  destination: TripDestination[];
  duration: TripDuration;
  pricing: StorefrontPricing;
  itinerary: StorefrontItinerary;
  media: TripMedia[];
  inclusions: string[];
  exclusions: string[];
  terms: TripTerms;
  reviews: TripReviewSummary;
  seo: TripSEO;
  publishedAt: Date;
  updatedAt: Date;
}

type TripListingType =
  | 'fixed_departure'                 // Specific dates, group tour
  | 'flexible_date'                   // Customer chooses dates
  | 'customizable'                    // Template that can be modified
  | 'on_request';                     // Inquire for custom quote

interface TripCategory {
  primary: string;                    // "Beach", "Adventure", "Pilgrimage"
  secondary: string[];                // "Honeymoon", "Family", "Weekend Getaway"
  tags: string[];                     // "Budget-Friendly", "All-Inclusive", "Luxury"
}

// Popular trip categories in India:
// By theme: Beach, Hill Station, Adventure, Pilgrimage, Wildlife, Heritage
// By audience: Honeymoon, Family, Solo, Group, Senior Citizens
// By duration: Weekend Getaway (2-3 days), Short Trip (4-5 days),
//              Week-Long (6-8 days), Extended (9+ days)
// By budget: Budget (< ₹10,000), Mid-range (₹10-30,000),
//            Premium (₹30-75,000), Luxury (> ₹75,000 per person)

interface TripDestination {
  primary: string;                    // "Kerala"
  secondary: string[];                // ["Alleppey", "Munnar", "Kochi", "Thekkady"]
  region: string;                     // "South India"
  country: string;                    // "India"
  geo: { lat: number; lng: number };
}

interface TripDuration {
  nights: number;
  days: number;
}

// Trip listing card (search results):
// ┌──────────────────────────────────────────┐
// │  [Photo Carousel: 5 images]              │
// │                                          │
// │  📍 Kerala · 5N/6D · Flexible Dates     │
// │  Kerala Backwaters & Hills               │
// │  Alleppey · Munnar · Kochi · Thekkady    │
// │                                          │
// │  ★★★★☆ (4.3) · 89 reviews              │
// │  🏷️ Honeymoon · Nature · Relaxation     │
// │                                          │
// │  ₹18,500 per person                      │
// │  ₹22,000 value · 16% off                 │
// │                                          │
// │  [View Details]  [WhatsApp Inquiry]      │
// └──────────────────────────────────────────┘
```

### Trip Detail Page

```typescript
interface TripDetailPage {
  trip: StorefrontTrip;
  hero: TripHeroSection;
  overview: TripOverview;
  itinerary: DayByDayItinerary;
  pricing: PricingSection;
  inclusions: InclusionsSection;
  accommodation: AccommodationPreview[];
  gallery: PhotoGallery;
  reviews: ReviewSection;
  faq: FAQSection;
  cta: CTASection;
  related: RelatedTrip[];
}

// Trip detail page structure:
//
// 1. HERO SECTION (top of page)
//    - Full-width photo carousel (5-10 images)
//    - Trip title + subtitle overlay
//    - Duration, destination, rating badge
//    - Price indicator + CTA button
//    - "Share" + "Save to Wishlist" buttons
//
// 2. OVERVIEW SECTION
//    - Trip highlights (4-6 bullet points with icons)
//    - Quick info: Duration, Destinations, Group Size, Difficulty
//    - Map preview with route and stops
//    - Best time to visit
//
// 3. DAY-BY-DAY ITINERARY
//    - Expandable accordion per day
//    - Day title, destination, activity summary
//    - Accommodation for the night
//    - Meals included (B/L/D)
//    - Photo per day
//    - "Download full itinerary" PDF button
//
// 4. PRICING SECTION
//    - Price per person (based on twin sharing)
//    - Price table by room type (Standard, Deluxe, Luxury)
//    - Child pricing (with/without bed)
//    - Single supplement
//    - Group discount tiers (4+, 6+, 10+ people)
//    - What's included / excluded
//
// 5. ACCOMMODATION PREVIEW
//    - Hotel cards with photos, ratings, amenities
//    - "Similar hotels available" note
//    - Room type per hotel
//
// 6. PHOTO GALLERY
//    - Grid layout with lightbox
//    - Filter by: All, Hotels, Activities, Food, Scenic
//    - 20-50 photos per trip
//    - Video support (YouTube/Vimeo embed)
//
// 7. REVIEWS SECTION
//    - Overall rating + breakdown
//    - Top 5 verified reviews
//    - Filter by: Recent, Highest, Lowest
//    - "Read all reviews" link
//
// 8. FAQ SECTION
//    - 5-10 common questions
//    - Custom per trip (set by agent)
//    - "Have more questions? WhatsApp us"
//
// 9. CTA SECTION (bottom sticky on mobile)
//    - "Book Now" / "Check Availability" / "Get Quote"
//    - WhatsApp quick-contact button
//    - Phone call button
//    - "Customize This Trip" button

interface StorefrontPricing {
  displayMode: PricingDisplayMode;
  startingPrice: Money;
  exactPrice?: Money;
  pricePerPerson: boolean;
  priceBasis: string;                 // "per person on twin sharing"
  rooms: RoomPricing[];
  childPolicy: ChildPolicy;
  groupDiscounts: GroupDiscount[];
  seasonalPricing?: SeasonalPricing[];
  earlyBirdDiscount?: Discount;
  lastMinuteDiscount?: Discount;
}

type PricingDisplayMode =
  | 'starting_from'                   // "Starting from ₹18,500"
  | 'exact'                           // "₹18,500 per person"
  | 'range'                           // "₹18,500 - ₹35,000"
  | 'on_request';                     // "Contact for best price"

interface RoomPricing {
  roomType: string;                   // "Standard", "Deluxe", "Luxury"
  pricePerPerson: Money;
  singleSupplement: Money;
  description: string;
}

interface GroupDiscount {
  minPeople: number;
  discountPercent: number;
  description: string;
}

// Pricing display example:
// ┌──────────────────────────────────────────┐
// │  💰 Pricing                               │
// │                                          │
// │  Starting from ₹18,500 per person        │
// │  (Twin sharing, Standard Room)           │
// │                                          │
// │  Standard: ₹18,500  Deluxe: ₹24,000     │
// │  Luxury:  ₹35,000  Premium: ₹52,000     │
// │                                          │
// │  Single Supplement: +₹6,500              │
// │  Child (5-11 yrs, with bed): ₹12,000     │
// │  Child (5-11 yrs, without bed): ₹8,000   │
// │  Infant (<5 yrs): Free                    │
// │                                          │
// │  🏷️ Group Discounts:                     │
// │  4-5 people: 5% off                      │
// │  6-9 people: 8% off                      │
// │  10+ people: 12% off                     │
// │                                          │
// │  Select Date: [Calendar]                 │
// │  Travelers: [2 Adults] [0 Children]      │
// │                                          │
// │  Total: ₹37,000                          │
// │  [Book Now]  [Customize Trip]            │
// └──────────────────────────────────────────┘
```

### Search & Filtering

```typescript
interface StorefrontSearch {
  query?: string;
  filters: SearchFilters;
  sort: SearchSort;
  pagination: Pagination;
}

interface SearchFilters {
  destination?: string[];
  category?: string[];
  duration?: DurationFilter;
  priceRange?: PriceRange;
  rating?: number;                    // Minimum rating
  travelDates?: DateRange;
  groupSize?: number;
  tripType?: TripListingType[];
  amenities?: string[];
}

interface DurationFilter {
  min?: number;                       // Minimum nights
  max?: number;                       // Maximum nights
  preset?: DurationPreset;
}

type DurationPreset =
  | 'weekend'                         // 1-3 nights
  | 'short'                           // 3-5 nights
  | 'week'                            // 5-7 nights
  | 'extended';                       // 7+ nights

type SearchSort =
  | 'relevance'                       // Default, based on search query
  | 'price_low'                       // Lowest price first
  | 'price_high'                      // Highest price first
  | 'rating'                          // Highest rated first
  | 'newest'                          // Recently published first
  | 'popular';                        // Most booked/viewed first

// Search experience:
// ┌──────────────────────────────────────────────────────┐
// │  🔍 Search destinations, trips, experiences...        │
// │                                                      │
// │  Popular Searches: Kerala | Goa | Thailand | Dubai   │
// │                                                      │
// │  Recent Searches: Singapore 5N/6D                    │
// │                                                      │
// │  Trending: Manali Weekend | Bali Honeymoon |...      │
// └──────────────────────────────────────────────────────┘
//
// Search results page:
// ┌──────────────────────────────────────────────────────┐
// │  "Kerala" · 24 trips found                           │
// │                                                      │
// │  Filters:                    Sort: [Relevance ▼]     │
// │  ┌──────────┐              ┌────────────────────┐   │
// │  │ Duration │              │                    │   │
// │  │ □ 1-3N   │              │  Trip Card 1       │   │
// │  │ ☑ 4-6N   │              │  Trip Card 2       │   │
// │  │ □ 7+N    │              │  Trip Card 3       │   │
// │  │          │              │                    │   │
// │  │ Budget   │              │                    │   │
// │  │ □ <10K   │              │                    │   │
// │  │ ☑ 10-25K │              │                    │   │
// │  │ □ 25-50K │              │                    │   │
// │  │ □ >50K   │              │                    │   │
// │  │          │              │                    │   │
// │  │ Type     │              │                    │   │
// │  │ □ Group  │              │                    │   │
// │  │ ☑ Custom │              │                    │   │
// │  └──────────┘              └────────────────────┘   │
// └──────────────────────────────────────────────────────┘
```

### Listing Optimization

```typescript
interface ListingOptimization {
  photos: PhotoOptimization;
  copy: CopyOptimization;
  pricing: PricingOptimization;
  seo: ListingSEO;
}

interface PhotoOptimization {
  required: number;                   // Minimum photos (recommended: 15+)
  heroPhoto: PhotoSpec;
  galleryPhotos: PhotoSpec;
  hotelPhotos: PhotoSpec;
  activityPhotos: PhotoSpec;
}

// Photo requirements:
// Hero photo: 1920x1080 minimum, <500KB, vibrant, destination-focused
// Gallery: 20-50 photos, mix of: scenic (40%), activities (30%),
//          accommodation (20%), food (10%)
// Hotel photos: 3-5 per hotel, showing room, lobby, pool/amenities
// Activity photos: Action shots, people enjoying, cultural moments
//
// Photo quality score (0-100):
// - Resolution: High-res gets higher score
// - Composition: AI quality assessment
// - Diversity: Multiple aspects of trip covered
// - Authenticity: Real photos > stock photos (verified via EXIF)
// - Recency: Photos <12 months old preferred

interface CopyOptimization {
  titleLength: { min: number; max: number };   // 40-70 characters
  subtitleLength: { min: number; max: number }; // 80-150 characters
  descriptionLength: { min: number; max: number }; // 500-2000 characters
  highlightsCount: { min: number; max: number }; // 4-8 highlights
  dayDescriptionLength: { min: number; max: number }; // 100-300 characters
}

// Listing quality checklist:
// [ ] Title is descriptive and includes destination
// [ ] Subtitle creates interest and includes key selling point
// [ ] At least 15 high-quality photos
// [ ] Every day of itinerary has description and photo
// [ ] Inclusions and exclusions clearly listed
// [ ] Pricing is transparent and complete
// [ ] FAQ covers common questions
// [ ] Terms and conditions present
// [ ] At least 3 verified reviews
// [ ] SEO meta title and description set

// Conversion optimization:
// - "Starting from" pricing gets 23% more clicks than exact pricing
// - Photos with people get 38% more engagement than scenery-only
// - Trips with reviews get 45% more inquiries
// - WhatsApp CTA gets 3x more inquiries than form CTA (India)
// - Video content increases booking rate by 30%
```

---

## Open Problems

1. **Content creation burden** — Creating compelling trip listings (photos, copy, itinerary details) is time-consuming. Agents aren't copywriters. Need templates and AI assistance.

2. **Price transparency vs. negotiation** — Indian travel often involves negotiation. Fixed pricing on storefronts may conflict with agency pricing culture.

3. **Inventory management** — Published trip pricing may go stale. Hotel prices change, flight prices fluctuate. Need real-time pricing or "starting from" ranges.

4. **Duplicate content** — Multiple agencies in the same region may publish similar trips. Need differentiation tools, not just price competition.

5. **Mobile-first browsing** — 80%+ of Indian internet traffic is mobile. Trip detail pages must be exceptional on mobile, not just responsive desktop pages.

---

## Next Steps

- [ ] Design trip catalog model with listing types and categories
- [ ] Build trip detail page with modular sections
- [ ] Create search and filtering system optimized for travel
- [ ] Design listing optimization tools and quality scoring
- [ ] Study trip listing platforms (TourRadar, GetYourGuide, Klook, TripAdvisor)
