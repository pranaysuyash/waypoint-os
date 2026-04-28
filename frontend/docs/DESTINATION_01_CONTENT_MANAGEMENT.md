# Travel Content & Destination Intelligence — Content Management

> Research document for destination data modeling, content authoring workflows, multilingual guide management, and content infrastructure.

---

## Key Questions

1. **How do we model destination data for both search and rich display?**
2. **What content authoring workflows support agency-created guides?**
3. **How do we manage multilingual destination content at scale?**
4. **What's the content delivery architecture for fast page loads?**
5. **How do we keep destination content fresh and accurate?**

---

## Research Areas

### Destination Data Model

```typescript
interface Destination {
  id: string;                          // "dest_kerala_india"
  slug: string;                        // "kerala-backwaters"
  name: DestinationName;
  geography: GeographyInfo;
  classification: DestinationClassification;
  content: DestinationContent;
  media: MediaGallery;
  practical: PracticalInfo;
  metadata: DestinationMetadata;
}

interface DestinationName {
  primary: string;                     // "Kerala"
  aliases: string[];                   // ["God's Own Country", "Keralam"]
  localName: string;                   // "കേരളം"
  transliterations: Record<string, string>;  // Hindi: "केरल"
}

interface GeographyInfo {
  country: string;                     // "India"
  region: string;                      // "South India"
  subRegion: string;                   // "Malabar Coast"
  coordinates: { lat: number; lng: number };
  timeZone: string;                    // "Asia/Kolkata"
  altitude?: number;                   // meters (for hill stations)
  area: number;                        // sq km
  borders: string[];                   // ["Tamil Nadu", "Karnataka", "Arabian Sea"]
  climate: ClimateInfo;
}

interface ClimateInfo {
  type: string;                        // "Tropical monsoon"
  averageTemps: MonthlyTemp[];         // By month
  rainySeason: string;                 // "June-September (Southwest monsoon)"
  bestTimeToVisit: string;             // "September to March"
  humidity: string;                    // "High (70-90%)"
}

// Temperature model:
// Month: { min: 23, max: 32, unit: "celsius" }
// Jan: 23-32°C, Feb: 24-33°C, ..., Dec: 22-31°C
//
// Best time composite:
// Weather: 8/10
// Crowd: 7/10
// Price: 6/10
// Overall: 7/10
// Recommendation: "September to March — pleasant weather, post-monsoon greenery"

interface DestinationClassification {
  types: DestinationType[];            // ["beach", "backwater", "hill_station", "ayurveda"]
  tags: string[];                      // ["honeymoon", "family", "adventure", "wellness"]
  popularity: number;                  // 1-10 scale
  indiaRank?: number;                  // Rank among Indian destinations
  seasonality: SeasonalityPattern[];
  targetAudience: TravelerType[];
}

type DestinationType =
  | 'beach'                            // Goa, Kerala, Andaman
  | 'hill_station'                     // Shimla, Ooty, Darjeeling
  | 'heritage'                         // Jaipur, Agra, Hampi
  | 'pilgrimage'                       // Varanasi, Tirupati, Amritsar
  | 'wildlife'                         // Ranthambore, Jim Corbett
  | 'backwater'                        // Alleppey, Kumarakom
  | 'adventure'                        // Rishikesh, Ladakh, Spiti
  | 'metro'                            // Mumbai, Delhi, Bangalore
  | 'island'                           // Andaman, Lakshadweep
  | 'desert'                           // Jaisalmer, Rajasthan
  | 'wellness'                         // Kerala (Ayurveda), Rishikesh (Yoga)
  | 'international';                   // Singapore, Thailand, Dubai

type TravelerType =
  | 'solo' | 'couple' | 'family' | 'group'
  | 'honeymoon' | 'senior' | 'corporate'
  | 'backpacker' | 'luxury' | 'adventure';

// Seasonality:
// Peak: December-January (weddings, holidays)
// High: October-November, February-March
// Shoulder: April-May, September
// Low: June-August (monsoon, but some prefer it)
// Pricing multiplier by season: Peak 1.4x, High 1.2x, Shoulder 1.0x, Low 0.7x

interface DestinationContent {
  summary: string;                     // 2-3 sentence overview
  description: string;                 // Rich text, 500-1000 words
  highlights: Highlight[];             // Top things to see/do
  history: string;                     // Brief historical context
  culture: string;                     // Cultural notes
  cuisine: CuisineInfo;                // Local food guide
  gettingThere: TransportInfo[];       // How to reach
  gettingAround: TransportInfo[];      // Local transport
  neighborhoods: Neighborhood[];       // Areas within destination
  dayTrips: DayTrip[];                 // Nearby excursions
  practicalTips: PracticalTip[];       // Dos and don'ts
}

// Highlight model:
// name: "Alleppey Houseboat"
// category: "experience"
// description: "Cruise through backwaters on a traditional kettuvallam"
// duration: "Full day to overnight"
// bestTime: "Year-round, best Sep-Mar"
// priceRange: "₹5,000 - ₹25,000 per night"
// rating: 4.7
// photos: [MediaRef]
// tips: ["Book in advance during peak season", "Opt for overnight stay"]

interface CuisineInfo {
  signature: Dish[];                   // Must-try dishes
  restaurants: Restaurant[];           // Recommended restaurants
  streetFood: string[];                // Street food highlights
  dietaryNotes: string[];              // Vegetarian/vegan options
}

// Dish model:
// name: "Kerala Sadya"
// description: "Traditional vegetarian feast served on banana leaf"
// type: "vegetarian"
// where: "Available across Kerala, especially during Onam"
// spiceLevel: "Medium"

interface PracticalInfo {
  languages: string[];                 // ["Malayalam", "English", "Hindi"]
  currency: string;                    // "INR"
  emergencyNumbers: Record<string, string>;
  visaRequirements: string;            // For international tourists
  vaccinationRequirements: string[];
  safetyRating: number;                // 1-5
  lgbtqFriendly: boolean;
  wheelchairAccessible: boolean;       // General accessibility
  connectivity: ConnectivityInfo;      // Internet, phone coverage
  electricity: string;                 // "230V, 50Hz, Type C/D/M plugs"
  tippingCulture: string;              // "10% at restaurants, round up taxis"
  bargainingCulture: string;           // "Expected at markets, not at malls"
}

interface DestinationMetadata {
  createdAt: Date;
  updatedAt: Date;
  lastVerifiedAt: Date;
  contentQuality: number;              // 1-100 score
  completeness: number;                // % of fields filled
  views: number;                       // Page views
  bookings: number;                    // Trips booked involving this destination
  averageRating: number;               // User ratings
  reviewCount: number;
  contentOwner: string;                // Agent/team responsible
  sources: ContentSource[];
}

interface ContentSource {
  name: string;                        // "India Tourism Board"
  url: string;
  lastChecked: Date;
  reliability: number;                 // 1-5
}
```

### Content Authoring Workflow

```typescript
interface ContentAuthoringWorkflow {
  roles: ContentRole[];
  stages: ContentStage[];
  review: ReviewProcess;
  publishing: PublishingFlow;
}

type ContentRole =
  | 'content_writer'                   // Writes destination guides
  | 'photographer'                     // Manages media gallery
  | 'destination_expert'               // Subject matter expert review
  | 'editor'                           // Editorial review and polish
  | 'translator'                       // Multilingual content
  | 'publisher';                       // Final publish approval

// Content lifecycle:
// DRAFT → REVIEW → REVISION → APPROVED → PUBLISHED → ARCHIVED
//
// Draft:
// - Writer creates new destination or updates existing
// - Can save as draft, preview, and submit for review
// - System auto-checks: completeness, spell check, SEO score
//
// Review:
// - Destination expert reviews factual accuracy
// - Editor reviews language quality and style guide compliance
// - Photographer reviews media quality and captions
// - All reviewers can approve, request changes, or reject
//
// Revision:
// - Writer addresses feedback
// - Re-submit for review cycle
//
// Approved:
// - Content passes all checks
// - Scheduled for publication (immediate or scheduled)
//
// Published:
// - Live on agency storefront
// - Available in trip builder destination search
// - Pushed to SEO indexing
// - Monitors for freshness (auto-flag if > 6 months old)
//
// Archival:
// - Destination no longer relevant (closed, renamed)
// - Redirect to replacement destination

interface ContentQualityCheck {
  completeness: CompletenessCheck;
  seo: SEOCheck;
  accessibility: AccessibilityCheck;
  factual: FactualCheck;
  media: MediaQualityCheck;
}

// Quality scoring:
// Completeness: All required fields filled = 100 points
//   - Must have: name, description, highlights, getting there, photos
//   - Nice to have: cuisine, history, day trips, neighborhoods
//
// SEO: Keyword optimization score
//   - Title under 60 chars, description under 160 chars
//   - H1, H2 hierarchy correct
//   - Alt text on all images
//   - Internal links to related destinations
//   - Schema.org markup (TouristDestination, Place)
//
// Accessibility:
//   - Plain language (reading level ≤ 8th grade)
//   - Alt text on all images
//   - Descriptive link text
//   - Video captions if present
//
// Factual:
//   - Currency matches country
//   - Timezone matches coordinates
//   - Emergency numbers valid format
//   - No contradictory information
//
// Media:
//   - Min 5 photos per destination
//   - Each photo has alt text and caption
//   - Hero image minimum 1920x1080
//   - No watermarked images
//   - Image compression < 200KB per image

// Content style guide:
// Voice: Enthusiastic but factual, not overly promotional
// Tense: Present tense ("Kerala offers...", not "Kerala will offer...")
// Measurements: Metric (km, °C) with imperial in parentheses for international
// Currency: ₹ for domestic, local currency + ₹ equivalent for international
// Length: Description 500-1000 words, highlights 100-200 words each
// Structure: Inverted pyramid (most important info first)
// Grammar: Active voice, short sentences, no jargon
```

### Multilingual Content Management

```typescript
interface MultilingualContent {
  primaryLanguage: string;             // "en-IN" (English India)
  supportedLanguages: LanguageConfig[];
  translationWorkflow: TranslationWorkflow;
  localizationRules: LocalizationRule[];
}

interface LanguageConfig {
  code: string;                        // "hi-IN", "ta-IN", "ml-IN"
  name: string;                        // "Hindi", "Tamil", "Malayalam"
  direction: 'ltr' | 'rtl';           // Left-to-right or right-to-left
  status: 'complete' | 'partial' | 'planned';
  coverage: number;                    // % of content translated
  machineTranslation: boolean;         // Auto-translated (not human-reviewed)
  lastUpdated: Date;
}

// Language priority for Indian travel platform:
// Tier 1 (Must-have): English, Hindi
// Tier 2 (High-value): Tamil, Telugu, Kannada, Malayalam (South India travel)
// Tier 3 (Regional): Bengali, Marathi, Gujarati, Punjabi
// International: Arabic (Dubai), Thai, Mandarin (future)
//
// Translation approach:
// 1. Machine translation for initial draft (Google Translate API)
// 2. Human review for Tier 1 languages
// 3. Community corrections for Tier 2/3
// 4. Fallback to English if translation not available
//
// Localization rules:
// Currency formatting: ₹1,25,000 (Indian) vs ₹125,000 (international)
// Date formatting: 15/12/2026 (Indian) vs December 15, 2026 (international)
// Number formatting: 1,25,000 (Indian lakh) vs 125,000 (international)
// Address formatting: Local format with landmarks ("Near City Mall, MG Road")
// Phone formatting: +91 98765 43210
// Measurement: km (not miles), °C (not °F)
//
// Cultural localization:
// Hindi: "शुभ यात्रा" (Happy Journey) greetings
// Tamil: Respectful address ("நீங்கள்" formal you)
// Muslim-majority areas: Halal food indicators
// Pilgrimage destinations: Religious etiquette notes

interface TranslationWorkflow {
  sourceContent: string;               // Content ID
  targetLanguage: string;
  status: TranslationStatus;
  translator?: string;
  machineTranslated?: boolean;
  humanReviewed?: boolean;
  reviewScore?: number;
}

type TranslationStatus =
  | 'pending'                          // Needs translation
  | 'machine_translated'               // Auto-translated, needs review
  | 'in_review'                        // Human translator reviewing
  | 'reviewed'                         // Reviewed, ready for publish
  | 'published'                        // Published
  | 'outdated';                        // Source changed, translation stale

// Translation management:
// - Detect source content changes
// - Flag outdated translations
// - Prioritize: Home page > Popular destinations > All destinations
// - Track: Translation coverage by language
// - Cost estimate: ₹2-5 per word for human translation
//   Average destination: 2000 words = ₹4,000-10,000 per language
//   500 destinations × 5 languages = ₹1-2.5 crore total
```

### Content Delivery Architecture

```typescript
interface ContentDelivery {
  storage: ContentStorage;
  caching: CacheConfig;
  cdn: CDNConfig;
  api: ContentAPI;
}

interface ContentStorage {
  primary: 'supabase';                 // PostgreSQL with full-text search
  media: 'supabase-storage';           // S3-compatible object storage
  search: 'meilisearch';               // Full-text search engine
  cache: 'redis';                      // Content cache layer
}

// Content delivery flow:
// 1. Author publishes content → Written to PostgreSQL
// 2. Content change event → Trigger search index update
// 3. Search index updated → Meilisearch re-indexes
// 4. Media uploaded → Processed (resize, compress, WebP)
// 5. Media processed → Uploaded to CDN
// 6. CDN invalidated → Fresh content served
//
// API design:
// GET /api/destinations — List destinations (paginated, filterable)
// GET /api/destinations/:slug — Full destination details
// GET /api/destinations/:slug/highlights — Highlights only
// GET /api/destinations/search?q=kerala&type=beach — Search
// GET /api/destinations/:slug/media — Media gallery
// GET /api/destinations/:slug/tips — Practical tips
//
// Response caching strategy:
// Destination list: Cache 1 hour (changes infrequently)
// Destination detail: Cache 4 hours (changes rarely)
// Search results: Cache 15 minutes (more dynamic)
// Media gallery: Cache 24 hours (very stable)
//
// Cache invalidation:
// On content publish: Invalidate specific destination cache
// On bulk update: Invalidate list and search caches
// On media change: Invalidate media CDN cache
//
// Performance targets:
// Destination list API: < 200ms (cached)
// Destination detail API: < 150ms (cached)
// Search API: < 100ms (Meilisearch)
// Media gallery load: < 500ms first image, lazy load rest
// Page load (with content): < 2s including media

// Content versioning:
// Every edit creates a new version
// Versions stored in content_versions table
// Rollback: Restore any previous version
// Diff: Show changes between versions
// Audit trail: Who changed what, when, and why
```

---

## Open Problems

1. **Content freshness at scale** — 500+ destinations need regular updates. Automated monitoring for outdated content (prices, transport info, visa rules) is essential but hard to verify programmatically.

2. **Photo licensing and rights management** — Destination photos need proper licensing. Stock photos are generic; authentic photos require photographer agreements, model releases, and attribution tracking.

3. **Multilingual quality assurance** — Machine translation is fast but error-prone for travel content (place names, cultural nuances). Human review at scale is expensive and slow.

4. **Content uniqueness vs. standardization** — Each destination is unique but the data model must be standardized for search and comparison. Balancing structured data with rich narrative content.

5. **User-generated content integration** — Customer photos and reviews enhance destination pages but need moderation, quality filtering, and legal compliance (consent, copyright).

---

## Next Steps

- [ ] Design destination content database schema and API
- [ ] Build content authoring interface with quality scoring
- [ ] Set up multilingual translation workflow with machine + human review
- [ ] Implement content delivery caching and CDN strategy
- [ ] Study destination content platforms (Lonely Planet API, TripAdvisor Content, Google Places)
