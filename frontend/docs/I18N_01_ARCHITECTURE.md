# Multi-Language & Internationalization — Architecture

> Research document for i18n framework selection, translation file structure, locale detection, URL strategy, fallback chains, RTL support, and Indian language script rendering.

---

## Key Questions

1. **Which i18n framework best fits our Next.js stack — i18next or next-intl?**
2. **How should we structure translation files for 10+ Indian languages with namespace isolation?**
3. **What URL strategy works best for multi-language in India — path prefix (/hi/, /ta/) or subdomain (hi.example.com)?**
4. **How do we implement a language fallback chain that accounts for regional dialects and Hinglish?**
5. **What is the end-to-end translation pipeline from developer string to deployed translation?**
6. **Do we need RTL support for Arabic/Urdu, and if so, what is the layout cost?**
7. **What are the font and rendering challenges for Devanagari, Tamil, Bengali, and other Indian scripts?**
8. **How do we handle locale detection for users in India who may prefer English UI but Hindi content?**

---

## Research Areas

### i18n Framework Comparison

```typescript
interface I18nFrameworkCandidate {
  name: string;
  nextJsSupport: 'native' | 'plugin' | 'manual';
  serverComponents: boolean;
  appRouter: boolean;
  bundleSize: string;            // kB gzipped
  icuMessageFormat: boolean;
  pluralRules: boolean;
  translationMemory: boolean;
  ssrPerformance: 'fast' | 'moderate' | 'slow';
  communitySize: 'large' | 'medium' | 'small';
}

type FrameworkDecision = {
  selected: 'next-intl' | 'i18next' | 'next-i18next' | 'paraglide-next';
  rationale: string;
  tradeoffs: string[];
};

// Framework comparison for Indian travel agency context:
//
// next-intl:
//   + Built for Next.js App Router (first-class)
//   + Server Component support out of the box
//   + Lightweight (~3kB)
//   + ICU message format built-in
//   - Fewer community plugins than i18next
//   - Less mature translation management ecosystem
//
// i18next + react-i18next:
//   + Largest ecosystem, most community resources
//   + Rich plugin system (backend, detector, post-processor)
//   + Translation management platforms integrate natively
//   + Battle-tested in production at scale
//   - Heavier bundle (~10kB + plugins)
//   - Server Component support requires workarounds
//   - Next.js App Router integration is not seamless
//
// paraglide-next:
//   + Compile-time i18n (zero runtime cost)
//   + Type-safe translations by default
//   + Excellent tree-shaking
//   - Newer project, smaller community
//   - Limited ICU/plural support
//   - Translation workflow tooling is immature
//
// Recommendation for Indian travel agency:
//   - Start with next-intl for App Router alignment
//   - Use i18next ecosystem for translation management (Lokalise, Phrase)
//   - Evaluate paraglide-next for performance-critical pages later
```

### Translation File Structure

```typescript
interface TranslationNamespace {
  namespace: string;
  description: string;
  estimatedKeys: number;
  owner: string;              // Team responsible
}

interface TranslationFileStructure {
  basePath: string;
  namespaces: TranslationNamespace[];
  fileFormat: 'json' | 'yaml' | 'po';
  nesting: 'flat' | 'nested';
  pluralSeparator: string;    // e.g., '_plural', '_zero', '_one'
  contextSeparator: string;   // e.g., '_male', '_female'
}

// Proposed namespace structure for travel agency:
//
// public/locales/
//   ├── en/                          // English (base)
//   │   ├── common.json              // Buttons, labels, messages (~200 keys)
//   │   ├── navigation.json          // Nav items, breadcrumbs (~50 keys)
//   │   ├── auth.json                // Login, signup, password (~80 keys)
//   │   ├── trips.json               // Trip listing, detail, builder (~300 keys)
//   │   ├── bookings.json            // Booking flow, confirmations (~200 keys)
//   │   ├── customers.json           // Customer profiles, history (~150 keys)
//   │   ├── suppliers.json           // Supplier management (~100 keys)
//   │   ├── itinerary.json           // Itinerary builder, day plans (~250 keys)
//   │   ├── payments.json            // Payment, invoicing, GST (~180 keys)
//   │   ├── search.json              // Search UI, filters, results (~120 keys)
//   │   ├── errors.json              // Error messages by category (~100 keys)
//   │   ├── emails.json              // Email templates (~150 keys)
//   │   └── notifications.json       // Push/notification templates (~80 keys)
//   │
//   ├── hi/                          // Hindi
//   │   ├── common.json
//   │   └── ...
//   │
//   ├── hi-Latn/                     // Hinglish (Hindi in Latin script)
//   │   ├── common.json
//   │   └── ...
//   │
//   ├── mr/                          // Marathi
//   ├── ta/                          // Tamil
//   ├── bn/                          // Bengali
//   ├── te/                          // Telugu
//   ├── kn/                          // Kannada
//   ├── ml/                          // Malayalam
//   ├── gu/                          // Gujarati
//   └── pa/                          // Punjabi
//
// Total estimated: ~1,960 keys per language
// With 11 languages: ~21,560 translation entries
```

### Locale Detection and Switching

```typescript
interface LocaleDetectionConfig {
  priority: LocaleDetectionSource[];
  persistMethod: 'cookie' | 'localStorage' | 'sessionStorage' | 'url';
  cookieName: string;
  cookieMaxAge: number;          // seconds
  fallbackChain: LocaleFallbackChain;
}

interface LocaleDetectionSource {
  type: 'url_path' | 'url_subdomain' | 'cookie' | 'accept_language' | 'user_profile' | 'geo_ip';
  weight: number;
  reliability: 'high' | 'medium' | 'low';
  description: string;
}

interface LocaleFallbackChain {
  // When a translation is missing in the target locale,
  // try these in order before showing the key itself.
  // Example for Hindi (hi):
  //   hi → hi-Latn (Hinglish) → en → key
  chains: Record<string, string[]>;
  defaultChain: string[];
}

// Locale detection priority for Indian travel agency:
//
// 1. URL path prefix (/hi/trips, /ta/trips) — highest priority, explicit
// 2. User profile preference (logged-in users) — persistent
// 3. Cookie (returning visitors) — lasts 1 year
// 4. Accept-Language header — browser preference
// 5. Geo-IP (optional) — suggest but do not force
//
// Fallback chains:
//   hi:     ['hi', 'hi-Latn', 'en']       // Hindi → Hinglish → English
//   mr:     ['mr', 'hi', 'en']             // Marathi → Hindi → English
//   ta:     ['ta', 'en']                   // Tamil → English
//   bn:     ['bn', 'en']                   // Bengali → English
//   te:     ['te', 'en']                   // Telugu → English
//   kn:     ['kn', 'en']                   // Kannada → English
//   ml:     ['ml', 'en']                   // Malayalam → English
//   gu:     ['gu', 'hi', 'en']             // Gujarati → Hindi → English
//   pa:     ['pa', 'hi', 'en']             // Punjabi → Hindi → English
//   hi-Latn: ['hi-Latn', 'hi', 'en']       // Hinglish → Hindi → English
//   default: ['en']                        // English is always final fallback

interface LocaleSwitchResult {
  fromLocale: string;
  toLocale: string;
  switchMethod: 'manual' | 'auto_detected' | 'url';
  urlChanged: boolean;
  translationsLoaded: boolean;
  loadTimeMs: number;
}

// Locale switcher UX considerations for India:
//
// - Language selector should show NATIVE names:
//     English, हिन्दी, मराठी, தமிழ், বাংলা, తెలుగు,
//     ಕನ್ನಡ, മലയാളം, ગુજરાતી, ਪੰਜਾਬੀ
//
// - Also show English transliteration for discoverability:
//     Hindi, Marathi, Tamil, Bengali, Telugu,
//     Kannada, Malayalam, Gujarati, Punjabi
//
// - Group by script family (Devanagari, Dravidian, etc.)
//   or alphabetically by English name
//
// - Persist choice immediately on selection
// - Show "Hinglish" option for Hindi-preferring users
//   who are more comfortable with Latin script
```

### URL Strategy for Multi-Language

```typescript
interface URLStrategy {
  pattern: 'path_prefix' | 'subdomain' | 'domain' | 'query_param' | 'cookie';
  example: string;
  seoImpact: 'positive' | 'neutral' | 'negative';
  implementationComplexity: 'low' | 'medium' | 'high';
  cachingBehavior: string;
  cdnSupport: 'native' | 'workaround' | 'unsupported';
}

interface URLStrategyDecision {
  selected: URLStrategy['pattern'];
  routes: LocalizedRoute[];
  redirects: LocaleRedirect[];
  sitemapStrategy: string;
}

// URL strategy comparison for Indian travel agency:
//
// Option A: Path prefix (RECOMMENDED)
//   /en/trips/kerala-backwaters
//   /hi/trips/kerala-backwaters
//   /ta/trips/kerala-backwaters
//
//   Pros:
//   + SEO-friendly (each language has unique URL)
//   + Easy to share specific-language links
//   + CDN caches per URL naturally
//   + Google can crawl and index all language variants
//   + hreflang tags map cleanly to URLs
//
//   Cons:
//   - Requires middleware for locale extraction
//   - Default locale prefix (/en/) may feel redundant
//   - Must handle root (/) redirect
//
// Option B: Subdomain
//   hi.example.com/trips/kerala-backwaters
//   ta.example.com/trips/kerala-backwaters
//
//   Pros:
//   + Clean path without prefix
//   + Separate CDN caching per subdomain
//
//   Cons:
//   - SSL certificates per subdomain
//   - Cookie sharing across subdomains needs configuration
//   - DNS configuration for 10+ subdomains
//   - Harder to set up in development
//
// Option C: Query parameter
//   /trips/kerala-backwaters?lang=hi
//
//   Pros:
//   + Simple implementation
//   + No route restructuring
//
//   Cons:
//   - NOT SEO-friendly (search engines ignore query params)
//   - URLs are not shareable (users lose ?lang=hi)
//   - Cannot use hreflang properly
//
// Decision: Path prefix with /en/ as default (not hidden)
//
// Route structure:
//   /[locale]/trips                    → Trip listing
//   /[locale]/trips/[tripId]           → Trip detail
//   /[locale]/bookings                 → Bookings
//   /[locale]/workspace/[tripId]       → Agent workspace
//   /[locale]/settings                 → Settings
//   /[locale]/help                     → Help center

interface LocalizedRoute {
  pattern: string;
  locales: string[];
  params: string[];
  isClientOnly: boolean;      // Does not need SSR locale handling
}

interface LocaleRedirect {
  from: string;
  to: string;
  type: 'permanent' | 'temporary';
  condition: string;
}
```

### Translation Pipeline

```typescript
interface TranslationPipelineStage {
  name: string;
  description: string;
  input: string;
  output: string;
  automation: 'full' | 'semi' | 'manual';
  tools: string[];
  estimatedTime: string;        // per sprint/release
}

interface TranslationPipeline {
  stages: TranslationPipelineStage[];
  trigger: 'string_freeze' | 'continuous' | 'on_demand';
  qualityGates: QualityGate[];
  rollbackStrategy: string;
}

// Translation pipeline for Indian travel agency:
//
// Stage 1: DEVELOPMENT
//   Developer writes: t('trips.detail.pricing.totalPrice')
//   Tool: i18next-scanner extracts keys from code
//   Output: en/common.json with new key + English default
//
// Stage 2: EXTRACTION
//   Tool scans codebase for new/changed translation keys
//   Compares against existing translations
//   Generates delta: new keys, changed keys, deleted keys
//   Automation: full (CI pipeline on PR)
//
// Stage 3: MACHINE TRANSLATION (Tier 2/3 languages)
//   New keys are machine-translated via:
//     - Google Translate API (baseline)
//     - DeepL API (better quality for some languages)
//     - Custom Indic NLP model (for Indian languages)
//   Output: Draft translations marked as 'machine' quality
//
// Stage 4: PROFESSIONAL TRANSLATION (Tier 1 languages)
//   Keys are sent to translation platform (Lokalise/Phrase)
//   Assigned to professional translators per language
//   SLA: 48 hours for standard, 24 hours for urgent
//
// Stage 5: REVIEW
//   Native speaker reviews translations
//   Checks: accuracy, tone, cultural sensitivity, brand voice
//   Tool: Translation platform review UI
//
// Stage 6: MERGE
//   Approved translations merged into translation files
//   JSON files validated (syntax, completeness)
//   Build-time type checking for missing keys
//
// Stage 7: DEPLOY
//   Translation bundles deployed to CDN
//   Cache invalidated per locale
//   A/B test new translations (optional)
//
// Automation levels:
//   Tier 1 (en, hi): full professional pipeline
//   Tier 2 (mr, ta, bn, te): machine + spot review
//   Tier 3 (kn, ml, gu, pa): machine only initially

interface QualityGate {
  name: string;
  check: string;
  threshold: number;
  blocking: boolean;
}

// Quality gates:
//   - completeness: 100% of Tier 1 keys translated
//   - no_placeholders_broken: All {{var}} preserved
//   - no_html_broken: All HTML tags preserved
//   - max_length_ratio: Translation <= 2x English length
//   - no_profanity: Cultural sensitivity check
//   - glossary_adherence: Brand terms match glossary
```

### Right-to-Left (RTL) Support

```typescript
interface RTLSupport {
  targetLanguages: string[];
  layoutStrategy: 'css_logical' | 'css_flip' | 'js_runtime';
  componentImpact: RTLComponentImpact[];
  testingEnvironments: RTLTestEnvironment[];
}

interface RTLComponentImpact {
  component: string;
  changes: string[];
  complexity: 'trivial' | 'moderate' | 'significant';
  notes: string;
}

// RTL languages relevant to Indian travel agency:
//
// Arabic (ar):
//   - Gulf tourists visiting India (UAE, Saudi, Qatar)
//   - Indian travelers to Middle East (Hajj, Umrah packages)
//   - Estimated 5-8% of customer base
//
// Urdu (ur):
//   - Written in Perso-Arabic script (RTL)
//   - Significant population in North India
//   - Linguistically close to Hindi but different script
//   - Consider: ur-Arab (Arabic script) vs ur-Deva (Devanagari)
//
// Layout changes for RTL:
//   - Flex direction: row → row-reverse
//   - Text alignment: left → right
//   - Margin/padding: swap left↔right
//   - Icons with direction (arrows): flip horizontally
//   - Navigation: RTL tab order
//   - Forms: label position, input alignment
//
// Recommended approach: CSS Logical Properties
//   margin-inline-start instead of margin-left
//   padding-inline-end instead of padding-right
//   text-align: start instead of text-align: left
//   inset-inline-start instead of left
//
// This eliminates the need for RTL-specific CSS overrides.

interface RTLTestEnvironment {
  browser: string;
  language: string;
  screenReader: string;
  platform: string;
  priority: 'P0' | 'P1' | 'P2';
}
```

### Indian Language Script Rendering

```typescript
interface IndicScriptConfig {
  script: string;
  isoCode: string;              // ISO 15924 script code
  languages: string[];
  fontRequirements: FontRequirement;
  renderingChallenges: string[];
  fallbackFonts: string[];
}

interface FontRequirement {
  primary: string;              // Web font name
  fallback: string;             // System fallback
  weight: string;               // Required weights
  size: string;                 // Approximate font file size
  subsetStrategy: 'full' | 'dynamic' | 'latin_plus';
}

// Indian script rendering considerations:
//
// Devanagari (Deva) — Hindi, Marathi, Sanskrit
//   Fonts: Noto Sans Devanagari (~180kB full, ~60kB subset)
//   Challenges:
//     - Conjunct characters (ligatures): क्ष, त्र, ज्ञ
//     - Matra positioning: का, कि, की, कु, कू
//     - Halant (virama) rendering: क् + ष = क्ष
//     - Top-line (shirorekha) must connect across conjuncts
//     - Font size may need to be 10-15% larger than Latin for readability
//
// Tamil (Taml) — Tamil
//   Fonts: Noto Sans Tamil (~150kB full, ~50kB subset)
//   Challenges:
//     - Vowel signs (uyir mei): க + ா = கா
//     - Complex ligatures: க்ஷ, ஶ்ரீ
//     - Grantha letters for Sanskrit loanwords
//     - Distinct glyph shapes compared to other Brahmic scripts
//     - Some Unicode points have dual rendering (old vs modern)
//
// Bengali (Beng) — Bengali
//   Fonts: Noto Sans Bengali (~160kB full, ~55kB subset)
//   Challenges:
//     - Complex conjuncts: ক্ষ, ত্র, জ্ঞ
//     - Matra positioning above and below base
//     - Distinctive headline (matra) at top
//
// Telugu (Telu) — Telugu
//   Fonts: Noto Sans Telugu (~170kB full)
//   Challenges:
//     - Vowel sign attachments: క + ై = కై
//     - Complex conjunct stacking
//     - Distinct rounder glyph shapes
//
// Kannada (Knda) — Kannada
//   Fonts: Noto Sans Kannada (~160kB full)
//   Challenges:
//     - Similar to Telugu but distinct glyphs
//     - Vowel signs can be above, below, left, or right of base
//
// Malayalam (Mlym) — Malayalam
//   Fonts: Noto Sans Malayalam (~165kB full)
//   Challenges:
//     - Two script variants: traditional and reformed
//     - Chillu letters (standalone consonant signs)
//     - Complex vowel sign combinations
//
// Gujarati (Gujr) — Gujarati
//   Fonts: Noto Sans Gujarati (~155kB full)
//   Challenges:
//     - Similar to Devanagari but without top-line
//     - Distinct numeral glyphs (optional, Latin often used)
//
// Punjabi/Gurmukhi (Guru) — Punjabi
//   Fonts: Noto Sans Gurmukhi (~155kB full)
//   Challenges:
//     - Similar to Devanagari structure
//     - Distinct nasalization marks (tippi, bindi)
//     - Addak (doubled consonant marker)

interface IndicRenderingStrategy {
  fontLoading: 'self_hosted' | 'google_fonts' | 'adobe_fonts';
  subsetting: 'static' | 'dynamic_unicode_range';
  fontDisplay: 'swap' | 'optional' | 'fallback';
  preloadCritical: boolean;
  fontStackStrategy: string;
}

// Recommended strategy:
//   1. Use Google Fonts (Noto Sans family) — free, well-maintained
//   2. Dynamic subsetting via unicode-range
//   3. font-display: swap (show fallback, swap when loaded)
//   4. Preload the primary language font in <head>
//   5. System font fallbacks: Mangal (Windows), Lohit (Linux),
//      Apple Color Emoji (macOS fallback for Indic)
//
// Performance budget per language:
//   - Critical font (subset): < 30kB
//   - Full font (lazy loaded): < 200kB
//   - Total for 3 most common languages: < 90kB critical path
```

### Data Models for i18n Architecture

```typescript
/**
 * Core i18n configuration type
 */
interface I18nConfig {
  defaultLocale: string;
  supportedLocales: LocaleDefinition[];
  fallbackChain: Record<string, string[]>;
  detection: LocaleDetectionConfig;
  urlStrategy: 'path_prefix' | 'subdomain';
  namespaces: NamespaceDefinition[];
  pipeline: TranslationPipeline;
  fonts: Record<string, FontRequirement>;
}

interface LocaleDefinition {
  code: string;                   // BCP 47: 'hi', 'ta', 'hi-Latn'
  name: string;                   // English: 'Hindi'
  nativeName: string;             // Native: 'हिन्दी'
  script: string;                 // ISO 15924: 'Deva', 'Taml', 'Latn'
  direction: 'ltr' | 'rtl';
  tier: 1 | 2 | 3;               // Support priority tier
  regions: string[];              // Primary regions: ['IN']
  fontStack: string[];            // CSS font-family stack
  dateFormat: string;             // Pattern: 'DD/MM/YYYY'
  numberFormat: {
    decimal: string;
    group: string;
    groupPattern: string;         // Indian: '##,##,###.##'
  };
  currency: string;               // ISO 4217: 'INR'
}

interface NamespaceDefinition {
  name: string;                   // 'trips', 'bookings', etc.
  description: string;
  estimatedKeys: number;
  updateFrequency: 'low' | 'medium' | 'high';
  owner: string;                  // Team name
}

/**
 * Translation entry with metadata
 */
interface TranslationEntry {
  key: string;
  namespace: string;
  locale: string;
  value: string;
  quality: 'machine' | 'professional' | 'native_reviewed';
  status: 'draft' | 'in_review' | 'approved' | 'rejected';
  lastModified: Date;
  modifiedBy: string;
  sourceHash: string;             // Hash of English source for change detection
  context?: string;               // Screenshot or description for translator
  pluralForm?: string;            // 'zero' | 'one' | 'few' | 'many' | 'other'
  genderForm?: string;            // 'masculine' | 'feminine' | 'neutral'
}

/**
 * Locale change event (for analytics)
 */
interface LocaleChangeEvent {
  userId: string;
  fromLocale: string;
  toLocale: string;
  trigger: 'manual' | 'auto_detected' | 'url' | 'login';
  timestamp: Date;
  page: string;                   // URL where switch happened
}
```

---

## Open Problems

1. **Hinglish as a locale.** Hinglish (Hindi written in Latin script) is the dominant communication style for millions of Indian internet users, but it has no BCP 47 tag and no formal grammar rules. We need to decide: is it a separate locale (`hi-Latn`), a variant of Hindi, or an informal overlay? How do we maintain consistency when Hinglish spelling varies by user?

2. **Indian number formatting (lakh/crore).** Standard `Intl.NumberFormat` with `en-IN` locale produces `1,23,456.78` (Indian grouping) but many Indian users also expect or prefer Western `123,456.78`. The grouping pattern itself is locale-dependent but the preference is individual. How do we handle this per-user without fragmenting locale codes?

3. **Font loading performance for 10+ scripts.** Each Indian script requires a separate font file (150-200kB each). If a user switches languages mid-session or if we show multiple languages on one page (e.g., destination names in native script), the cumulative font load could be 1MB+. Dynamic subsetting helps but is not a complete solution.

4. **SSR locale detection vs. client-side hydration mismatch.** If the server detects one locale (via Accept-Language or Geo-IP) and the client has a different saved preference (via cookie or localStorage), we get a hydration mismatch. This is especially tricky for Next.js App Router with React Server Components.

5. **Translation key exhaustion in CI.** With 1,960+ keys across 11 languages, the CI pipeline to check for missing translations could add 30+ seconds per build. We need a fast key-comparison strategy that does not slow down the PR feedback loop.

6. **Unicode normalization for Indian scripts.** The same visual string can have multiple Unicode representations (e.g., decomposed vs. composed characters in Devanagari). This affects string comparison, translation lookup, and search. We need to decide on a normalization form (NFC recommended) and enforce it.

7. **Mixed-script content.** Travel content often mixes scripts: "Kerala (केरल) backwaters" or "Mahabalipuram (மகாபலிபுரம்) temples." Rendering and line-breaking for mixed-script content requires careful CSS (`word-break`, `line-break`) and font fallback stacks.

---

## Next Steps

1. **Framework spike.** Build a proof-of-concept with next-intl on a single page (trip detail) to validate Server Component compatibility and bundle size. Compare with an i18next spike on the same page.

2. **URL strategy A/B test.** Set up `/en/` vs `/hi/` path-prefix routing in middleware. Verify that Next.js `generateStaticParams` works correctly with locale-prefixed routes and that hreflang tags render properly.

3. **Font loading benchmark.** Test Noto Sans fonts for Devanagari, Tamil, and Bengali with dynamic subsetting. Measure First Contentful Paint (FCP) and Largest Contentful Paint (LCP) impact with and without font preloading.

4. **Translation file schema.** Define the JSON schema for translation files with validation rules (no broken placeholders, consistent nesting, key naming conventions). Integrate into CI.

5. **Fallback chain prototype.** Implement the fallback chain for Hindi → Hinglish → English and test with intentionally incomplete Hindi translations to verify graceful degradation.

6. **RTL feasibility check.** Enable RTL layout on a single page using CSS logical properties. Document the effort estimate for converting the full UI to logical properties vs. adding `[dir='rtl']` overrides.

7. **Indic script rendering test matrix.** Set up BrowserStack / LambdaTest configurations for all 10 Indian scripts across Chrome, Firefox, Safari, and Samsung Internet. Capture screenshots for a baseline rendering reference.

---

**End of Document**

**Next:** [Content Localization](I18N_02_LOCALIZATION.md)
