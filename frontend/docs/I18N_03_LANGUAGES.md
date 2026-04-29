# Multi-Language & Internationalization — Language Support Tiers & Strategy

> Research document for language tier strategy, translation quality levels, Hinglish support, transliteration, and font/rendering considerations for Indian scripts.

---

## Key Questions

1. **How do we prioritize which Indian languages to support, and in what order?**
2. **What is the right quality level for each tier — machine translation, professional, or native-reviewed?**
3. **How do we support Hinglish (code-switching between Hindi and English) which is the dominant communication style for urban Indians?**
4. **Can we offer transliteration — user types in Latin script, we convert to Devanagari/Tamil/etc.?**
5. **What font and rendering issues arise with Indian scripts (ligatures, vowel signs, matras)?**
6. **How do we measure translation quality for languages where our team may not have native speakers?**

---

## Research Areas

### Language Support Tiers

```typescript
interface LanguageTier {
  tier: 1 | 2 | 3;
  name: string;
  description: string;
  languages: LanguageDefinition[];
  qualityTarget: TranslationQuality;
  launchCriteria: string;
}

interface LanguageDefinition {
  code: string;                    // BCP 47: 'hi', 'ta', 'hi-Latn'
  name: string;                    // English name
  nativeName: string;              // Name in its own script
  script: string;                  // ISO 15924: 'Deva', 'Taml', 'Latn'
  speakers: number;                // Approximate speakers in India (millions)
  internetUsers: number;           // Internet users preferring this language
  travelRelevance: string;         // Why relevant for travel agency
  regions: string[];               // Indian states where dominant
  scriptComplexity: 'low' | 'medium' | 'high';
}

// Language Tier Strategy:
//
// ┌─────────────────────────────────────────────────────────┐
// │  TIER 1: Must Have (Launch Blockers)                    │
// │  Languages: English, Hindi, Hinglish                     │
// │  Quality: Professional + Native Reviewed                 │
// │  Coverage: 100% of UI strings, 100% of key content       │
// │  Timeline: Day 1 of multi-language launch                │
// │  Rationale: 80%+ of Indian internet users                │
// └─────────────────────────────────────────────────────────┘
//
// ┌─────────────────────────────────────────────────────────┐
// │  TIER 2: Should Have (First Quarter)                    │
// │  Languages: Marathi, Tamil, Bengali, Telugu              │
// │  Quality: Professional Translation                       │
// │  Coverage: 100% of UI strings, key content machine+review│
// │  Timeline: Within 3 months of launch                     │
// │  Rationale: Next 15% of users, major state languages     │
// └─────────────────────────────────────────────────────────┘
//
// ┌─────────────────────────────────────────────────────────┐
// │  TIER 3: Nice to Have (Second Quarter+)                 │
// │  Languages: Kannada, Malayalam, Gujarati, Punjabi        │
// │  Quality: Machine Translation + Spot Review              │
// │  Coverage: 100% of UI strings, content machine only      │
// │  Timeline: 6+ months, community-driven                   │
// │  Rationale: Long tail, shows commitment to all India     │
// └─────────────────────────────────────────────────────────┘

type LanguageTiers = {
  tier1: LanguageDefinition[];
  tier2: LanguageDefinition[];
  tier3: LanguageDefinition[];
};

// Detailed language definitions:
const LANGUAGE_TIERS: LanguageTiers = {
  tier1: [
    {
      code: 'en',
      name: 'English',
      nativeName: 'English',
      script: 'Latn',
      speakers: 125,               // ~125M English speakers in India
      internetUsers: 350,           // Most Indian internet users read English
      travelRelevance: 'Primary language for travel booking in India',
      regions: ['Pan-India', 'Urban centers'],
      scriptComplexity: 'low',
    },
    {
      code: 'hi',
      name: 'Hindi',
      nativeName: 'हिन्दी',
      script: 'Deva',
      speakers: 600,               // ~600M Hindi speakers
      internetUsers: 200,           // Growing rapidly with cheap data
      travelRelevance: 'Largest language group, domestic travel',
      regions: ['UP', 'Bihar', 'MP', 'Rajasthan', 'Jharkhand', 'Chhattisgarh', 'Haryana', 'Delhi NCR'],
      scriptComplexity: 'medium',
    },
    {
      code: 'hi-Latn',
      name: 'Hinglish',
      nativeName: 'Hinglish',
      script: 'Latn',
      speakers: 400,               // ~400M use Hinglish regularly
      internetUsers: 300,           // Dominant in social media, chat
      travelRelevance: 'Actual communication style of most young Indians',
      regions: ['Pan-India urban', 'Youth demographic'],
      scriptComplexity: 'low',
    },
  ],
  tier2: [
    {
      code: 'mr',
      name: 'Marathi',
      nativeName: 'मराठी',
      script: 'Deva',
      speakers: 83,
      internetUsers: 35,
      travelRelevance: 'Maharashtra (Mumbai, Pune) — top travel market',
      regions: ['Maharashtra', 'Goa'],
      scriptComplexity: 'medium',
    },
    {
      code: 'ta',
      name: 'Tamil',
      nativeName: 'தமிழ்',
      script: 'Taml',
      speakers: 75,
      internetUsers: 30,
      travelRelevance: 'Tamil Nadu tourism, Singapore/Malaysia packages',
      regions: ['Tamil Nadu', 'Puducherry'],
      scriptComplexity: 'high',
    },
    {
      code: 'bn',
      name: 'Bengali',
      nativeName: 'বাংলা',
      script: 'Beng',
      speakers: 100,
      internetUsers: 25,
      travelRelevance: 'East India market, Bangladesh cross-border tourism',
      regions: ['West Bengal', 'Tripura', 'Assam'],
      scriptComplexity: 'medium',
    },
    {
      code: 'te',
      name: 'Telugu',
      nativeName: 'తెలుగు',
      script: 'Telu',
      speakers: 85,
      internetUsers: 28,
      travelRelevance: 'Andhra/Telangana — growing outbound travel market',
      regions: ['Andhra Pradesh', 'Telangana'],
      scriptComplexity: 'high',
    },
  ],
  tier3: [
    {
      code: 'kn',
      name: 'Kannada',
      nativeName: 'ಕನ್ನಡ',
      script: 'Knda',
      speakers: 45,
      internetUsers: 15,
      travelRelevance: 'Karnataka (Bengaluru tech hub, Mysore, Coorg)',
      regions: ['Karnataka'],
      scriptComplexity: 'high',
    },
    {
      code: 'ml',
      name: 'Malayalam',
      nativeName: 'മലയാളം',
      script: 'Mlym',
      speakers: 38,
      internetUsers: 18,
      travelRelevance: 'Kerala tourism (top destination), Gulf migration',
      regions: ['Kerala', 'Lakshadweep'],
      scriptComplexity: 'high',
    },
    {
      code: 'gu',
      name: 'Gujarati',
      nativeName: 'ગુજરાતી',
      script: 'Gujr',
      speakers: 60,
      internetUsers: 20,
      travelRelevance: 'Gujarat business travel, Diu/Kutch tourism',
      regions: ['Gujarat', 'Daman and Diu'],
      scriptComplexity: 'medium',
    },
    {
      code: 'pa',
      name: 'Punjabi',
      nativeName: 'ਪੰਜਾਬੀ',
      script: 'Guru',
      speakers: 35,
      internetUsers: 12,
      travelRelevance: 'Punjab tourism, Sikh pilgrimage (Golden Temple)',
      regions: ['Punjab', 'Chandigarh'],
      scriptComplexity: 'medium',
    },
  ],
};
```

### Translation Quality Levels

```typescript
type TranslationQuality = 'machine' | 'professional' | 'native_reviewed';

interface TranslationQualityConfig {
  level: TranslationQuality;
  description: string;
  process: string[];
  turnaroundTime: string;
  costPerWord: string;             // Approximate INR
  errorRate: string;               // Acceptable error percentage
  useCase: string;
}

// Translation quality matrix:
//
// ┌──────────────┬────────────────┬────────────────┬────────────────┐
// │              │   Machine      │  Professional  │ Native Reviewed│
// ├──────────────┼────────────────┼────────────────┼────────────────┤
// │ Process      │ API call       │ Human + tool   │ Human + review │
// │ Turnaround   │ < 1 second     │ 24-48 hours    │ 3-5 days       │
// │ Cost/word    │ ~₹0.01         │ ~₹2-5          │ ~₹5-10         │
// │ Error rate   │ 10-15%         │ 3-5%           │ < 1%           │
// │ Best for     │ Tier 3, drafts │ Tier 2, content│ Tier 1, UI     │
// │ Machine       │ Google/DeepL   │ Lokalise       │ Lokalise +     │
// │ Translation   │ + Indic NLP    │ + translators  │ native speaker │
// └──────────────┴────────────────┴────────────────┴────────────────┘
//
// Quality level per tier per content type:
//
//                  UI Strings    Content    Emails     Notifications
// Tier 1 (en/hi):  native_rev    native_rev  prof+rev   native_rev
// Tier 2 (mr/ta):  professional  prof+review prof       machine+review
// Tier 3 (kn/ml):  machine+rev   machine     machine    machine

interface QualityMeasurement {
  method: 'bleu' | 'human_eval' | 'ab_testing' | 'user_feedback';
  threshold: number;
  frequency: string;
}

// Quality measurement approaches:
//
// 1. BLEU Score (automated):
//    - Compare machine translation against reference human translation
//    - Threshold: > 0.4 acceptable, > 0.6 good, > 0.8 excellent
//    - Run on every translation batch
//
// 2. Human Evaluation (periodic):
//    - Native speakers rate translations: 1-5 scale
//    - Dimensions: accuracy, fluency, cultural appropriateness
//    - Monthly for Tier 1, quarterly for Tier 2
//
// 3. A/B Testing (continuous):
//    - Show different translations to different users
//    - Measure: task completion rate, time to complete, error rate
//    - Ongoing for high-traffic pages
//
// 4. User Feedback (continuous):
//    - "Report incorrect translation" button on pages
//    - Feedback loop to translation team
//    - Priority queue for reported strings
```

### Hinglish Support Strategy

```typescript
interface HinglishStrategy {
  // Hinglish = Hindi vocabulary + English structure, written in Latin script
  // This is the dominant communication style for:
  //   - Urban Indians aged 18-40
  //   - Social media users
  //   - Chat/WhatsApp communication
  //   - Customer service interactions
  //
  // Examples:
  //
  // English:    "Book your trip to Goa"
  // Hindi:      "गोवा की अपनी यात्रा बुक करें"
  // Hinglish:   "Goa trip book karo" or "Apni Goa trip book karo"
  //
  // English:    "Your booking is confirmed"
  // Hindi:      "आपकी बुकिंग कन्फर्म हो गई है"
  // Hinglish:   "Aapki booking confirm ho gayi hai"
  //
  // English:    "Total price: ₹25,000"
  // Hindi:      "कुल मूल्य: ₹25,000"
  // Hinglish:   "Total price: ₹25,000" (numbers stay in English)
  //
  // Challenges with Hinglish:
  //   1. No standard spelling — "karo" / "karro" / "kar do" are all valid
  //   2. Hindi-English mixing ratio varies by speaker
  //   3. Grammar is inconsistent — some Hindi, some English rules
  //   4. Regional variation — Delhi Hinglish ≠ Mumbai Hinglish
  //   5. Not a BCP 47 registered locale
  //   6. No spell-check or grammar tools available
}

interface HinglishLocaleConfig {
  code: 'hi-Latn';                // Using BCP 47 private use or extended
  name: 'Hinglish';
  nativeName: 'Hinglish';
  script: 'Latn';
  direction: 'ltr';
  parentLocale: 'en';             // Falls back to English, not Hindi
  // Reason: Hinglish readers can read English better than Devanagari
  // Hindi readers who prefer Devanagari will select 'hi', not 'hi-Latn'
}

interface HinglishTranslationApproach {
  // Approach 1: Separate hi-Latn locale (RECOMMENDED)
  //
  // Create a full set of Hinglish translations alongside Hindi.
  // This gives the best user experience but doubles the Hindi workload.
  //
  // public/locales/hi-Latn/common.json:
  // {
  //   "buttons": {
  //     "save": "Save karo",
  //     "cancel": "Cancel karo",
  //     "book_now": "Abhi book karo",
  //     "search": "Search karo"
  //   },
  //   "labels": {
  //     "destination": "Destination",
  //     "check_in": "Check-in date",
  //     "guests": "Kitne log?",
  //     "budget": "Budget"
  //   },
  //   "messages": {
  //     "booking_confirmed": "Aapki booking confirm ho gayi!",
  //     "payment_success": "Payment ho gaya! Booking confirm hai.",
  //     "trip_reminder": "Kal aapki trip hai! Packing complete karo."
  //   }
  // }
  //
  // Approach 2: Hybrid transliteration
  //
  // Don't store Hinglish translations. Instead, transliterate Hindi
  // translations from Devanagari to Latin script at runtime.
  //
  // Pros: No extra translation work
  // Cons: Transliteration quality is inconsistent, produces
  //       "formal" romanization (like "aapakee" instead of "aapki")
  //
  // Recommendation: Approach 1 for Tier 1, Approach 2 as fallback

  approach: 'separate_locale';
  fallbackToEnglish: boolean;     // true — if Hinglish key missing, show English
  transliterationAssist: boolean; // false initially, add later as UX enhancement
}

interface HinglishToneGuidelines {
  // Tone guidelines for Hinglish translations:
  //
  // 1. Use conversational Hindi vocabulary:
  //    ✓ "trip book karo" (not "yatra abhilekhit karo")
  //    ✓ "payment karo" (not "bhugtan karo")
  //    ✓ "check-in karo" (not "prayas pravesh karo")
  //
  // 2. English for technical/travel terms:
  //    ✓ "booking", "check-in", "check-out", "itinerary"
  //    ✓ "flight", "hotel", "package", "deal"
  //    ✓ "GST", "invoice", "refund"
  //
  // 3. Hindi for emotional/casual content:
  //    ✓ "Aapki trip amazing hogi!" (excitement)
  //    ✓ "Koi baat nahi, next time" (reassurance)
  //    ✓ "Jaldi book karo, limited seats!" (urgency)
  //
  // 4. Numbers and currency: Always English numerals and ₹
  //    ✓ "₹25,000" (not "₹२५,०००" or "pacchees hazaar")
  //
  // 5. Avoid overly formal Hindi words:
  //    ✗ "suvichar" (use "message")
  //    ✗ "sarvang" (use "full body" or skip)
  //    ✗ "prayas" (use "try")
}
```

### Transliteration Support

```typescript
interface TransliterationConfig {
  // Transliteration = converting Latin script input to native script
  // Example: user types "namaste" → system suggests "नमस्ते"
  //
  // Use cases in travel agency:
  //   1. Search: User types "goa" in Latin → search in Hindi content
  //   2. Forms: User types name in Latin → show in Devanagari/Tamil
  //   3. Chat: Agent receives Hinglish → auto-transliterate for records
  //   4. Content: Destination name typed in Latin → show in native script

  enabled: boolean;
  supportedPairs: TransliterationPair[];
  library: string;
  realTime: boolean;
}

interface TransliterationPair {
  from: 'Latn';                    // Always Latin to native
  to: string;                      // 'Deva' | 'Taml' | 'Beng' | etc.
  languages: string[];             // ['hi', 'mr'] for Devanagari
  quality: 'high' | 'medium' | 'low';
}

// Transliteration libraries for Indian languages:
//
// 1. Google Input Tools (API):
//    + Best accuracy for all Indian scripts
//    + Context-aware suggestions
//    - Requires API call per keystroke (latency)
//    - Paid service
//
// 2. AI4Bharat IndicTrans2 (open-source):
//    + Free, offline-capable
//    + Good accuracy for Devanagari, Tamil, Bengali, Telugu
//    + Can run on server or client-side (ONNX)
//    - Model size: ~50-100MB per language pair
//    - Not real-time for client-side without WASM
//
// 3. Libindic (open-source):
//    + Lightweight
//    + Multiple Indian languages
//    - Lower accuracy than ML-based approaches
//    - Rule-based, no context awareness
//
// 4. Razorpay's powering-transliteration:
//    + Built for Indian fintech (similar UX needs)
//    + Uses Google Input Tools under the hood
//    + Open-source wrapper
//
// Recommendation:
//   - Search: Use AI4Bharat IndicTrans2 on server-side
//   - Form input: Use browser-native input methods (IME)
//   - Chat/communication: Post-processing transliteration
//   - Don't force transliteration on users who prefer Latin

interface TransliterationUX {
  // UX pattern for transliteration in search:
  //
  // ┌─────────────────────────────────────────┐
  // │ 🔍 Search destinations...               │
  // │                                         │
  // │ User types: "kera"                      │
  // │ Suggestions:                             │
  // │   📍 Kerala (केरल)                      │
  // │   📍 Keralapura (केरलपुर)               │
  // │                                         │
  // │ User types: "mum"                       │
  // │ Suggestions:                             │
  // │   📍 Mumbai (मुंबई)                     │
  // │   📍 Mount Abu (माउंट आबू)              │
  // └─────────────────────────────────────────┘
  //
  // Show both scripts in search results so users
  // can identify the right result regardless of
  // which script they typed in.
}
```

### Font and Rendering Considerations

```typescript
interface IndicFontConfig {
  script: string;
  primaryFont: string;
  fallbackFonts: string[];
  sizeAdjust: number;              // Multiplier relative to Latin (1.0 = same)
  lineHeightAdjust: number;        // Multiplier for line-height
  renderTestCases: RenderTestCase[];
}

interface RenderTestCase {
  description: string;
  input: string;                   // Unicode string
  expectedBehavior: string;
  commonFailures: string[];
}

// Font and rendering matrix for Indian scripts:
//
// ┌────────────┬──────────────────┬──────────┬────────┬──────────┐
// │ Script     │ Primary Font     │ Size Adj │ LH Adj │ Complexity│
// ├────────────┼──────────────────┼──────────┼────────┼──────────┤
// │ Devanagari │ Noto Sans Deva.  │ 1.05x    │ 1.3x   │ Medium   │
// │ Tamil      │ Noto Sans Tamil  │ 1.05x    │ 1.4x   │ High     │
// │ Bengali    │ Noto Sans Bengali│ 1.05x    │ 1.3x   │ Medium   │
// │ Telugu     │ Noto Sans Telugu │ 1.05x    │ 1.3x   │ High     │
// │ Kannada    │ Noto Sans Kannada│ 1.05x    │ 1.3x   │ High     │
// │ Malayalam  │ Noto Sans Mal.   │ 1.10x    │ 1.4x   │ High     │
// │ Gujarati   │ Noto Sans Gujar. │ 1.05x    │ 1.3x   │ Medium   │
// │ Gurmukhi   │ Noto Sans Gurm.  │ 1.05x    │ 1.3x   │ Medium   │
// └────────────┴──────────────────┴──────────┴────────┴──────────┘

// Devanagari rendering test cases:
const DEVANAGARI_TESTS: RenderTestCase[] = [
  {
    description: 'Basic conjunct with halant',
    input: 'क्ष',
    expectedBehavior: 'क् + ष → single conjunct glyph क्ष',
    commonFailures: ['Shows as क्‌ष (visible halant)', 'Glyph overlap'],
  },
  {
    description: 'Three-consonant conjunct',
    input: 'त्र्य',
    expectedBehavior: 'त् + र् + य → compact conjunct',
    commonFailures: ['Stacking breaks', 'Vertical overflow'],
  },
  {
    description: 'Top matra with conjunct',
    input: 'क्षि',
    expectedBehavior: 'क्ष + ि (i-matra) → i-matra above conjunct',
    commonFailures: ['Matra placed above wrong glyph', 'Matra clipped'],
  },
  {
    description: 'Shirorekha (top line) continuity',
    input: 'नमस्ते',
    expectedBehavior: 'Continuous top line across all characters',
    commonFailures: ['Broken top line between certain character pairs'],
  },
  {
    description: 'Nukta characters',
    input: 'क़ ख़ ग़ ज़ ड़ ढ़ फ़',
    expectedBehavior: 'Base character with dot below',
    commonFailures: ['Nukta dot misplaced', 'Character not recognized'],
  },
  {
    description: 'Number formatting',
    input: '१,२५,०००',
    expectedBehavior: 'Devanagari digits with Indian grouping',
    commonFailures: ['Digits render as Latin', 'Grouping ignored'],
  },
];

// Tamil rendering test cases:
const TAMIL_TESTS: RenderTestCase[] = [
  {
    description: 'Vowel sign au (ஔ)',
    input: 'கௌ',
    expectedBehavior: 'க + ௌ → composite glyph with side and top marks',
    commonFailures: ['Marks separated', 'Overlap with adjacent character'],
  },
  {
    description: 'Complex compound character',
    input: 'க்ஷ',
    expectedBehavior: 'க் + ஷ → ligature form',
    commonFailures: ['Not all fonts support this ligature'],
  },
  {
    description: 'Virama (pulli) suppression',
    input: 'கல்லு',
    expectedBehavior: 'Pulli (dot) suppressed at morpheme boundary',
    commonFailures: ['Pulli visible when it should be hidden'],
  },
  {
    description: 'Sri ligature',
    input: 'ஶ்ரீ',
    expectedBehavior: 'Special ligature form for ஶ்ரீ',
    commonFailures: ['Renders as separate glyphs in some fonts'],
  },
];

// Font loading strategy for Indian scripts:
interface IndicFontLoadingStrategy {
  // Challenge: Each Indic font is 50-200kB.
  // Loading all fonts = 400-1600kB. Unacceptable.
  //
  // Strategy: Load only the user's selected language font
  //
  // Step 1: Determine user's locale
  // Step 2: Preload primary font for that locale
  // Step 3: Lazy-load fonts for other locales on switch
  //
  // Implementation:
  //
  // // next.config.js font optimization
  // // Use next/font/google for automatic optimization
  //
  // import { Noto_Sans_Devanagari, Noto_Sans_Tamil } from 'next/font/google';
  //
  // const notoDevanagari = Noto_Sans_Devanagari({
  //   subsets: ['devanagari'],
  //   display: 'swap',
  //   variable: '--font-devanagari',
  // });
  //
  // const notoTamil = Noto_Sans_Tamil({
  //   subsets: ['tamil'],
  //   display: 'swap',
  //   variable: '--font-tamil',
  // });
  //
  // CSS custom properties for font switching:
  //   --font-primary: var(--font-devanagari) for Hindi
  //   --font-primary: var(--font-tamil) for Tamil
  //   etc.
  //
  // Preload only current locale's font in <head>:
  //   <link rel="preload" href="/fonts/noto-sans-devanagari.woff2" as="font" type="font/woff2" crossorigin>
}

// Line-height and vertical spacing for Indic scripts:
interface IndicTypographyRules {
  // Indic scripts typically need more line-height than Latin:
  //
  // Latin:    line-height: 1.5
  // Devanagari: line-height: 1.65  (top line + matras above)
  // Tamil:    line-height: 1.7    (tall vowel signs)
  // Bengali:  line-height: 1.65   (matras above and below)
  // Telugu:   line-height: 1.65
  // Malayalam: line-height: 1.7   (tall glyphs)
  //
  // Font size adjustments:
  //   Indic text at the same font-size as Latin often appears smaller
  //   due to the top-line/matras consuming vertical space.
  //   Consider: body text 16px for Latin, 17px for Indic.
  //
  // Paragraph spacing:
  //   Some Indic scripts benefit from extra paragraph spacing
  //   to prevent matra collision between lines.
}
```

### Data Models for Language Support

```typescript
/**
 * Language configuration for the platform
 */
interface PlatformLanguageConfig {
  tiers: LanguageTiers;
  defaultLanguage: string;
  qualityMatrix: QualityMatrix;
  transliteration: TransliterationConfig;
  fonts: Record<string, IndicFontConfig>;
  hinglishStrategy: HinglishTranslationApproach;
}

/**
 * Quality matrix: which quality level for which content type in which tier
 */
interface QualityMatrix {
  [tier: string]: {
    [contentType: string]: TranslationQuality;
  };
}

// Example:
// {
//   tier1: {
//     ui_strings: 'native_reviewed',
//     destination_content: 'native_reviewed',
//     emails: 'professional',
//     notifications: 'native_reviewed',
//     error_messages: 'native_reviewed',
//   },
//   tier2: {
//     ui_strings: 'professional',
//     destination_content: 'machine',       // Machine + spot review
//     emails: 'machine',
//     notifications: 'professional',
//     error_messages: 'professional',
//   },
//   tier3: {
//     ui_strings: 'machine',
//     destination_content: 'machine',
//     emails: 'machine',
//     notifications: 'machine',
//     error_messages: 'machine',
//   }
// }

/**
 * Translation coverage report
 */
interface TranslationCoverage {
  locale: string;
  tier: 1 | 2 | 3;
  totalKeys: number;
  translatedKeys: number;
  coveragePercent: number;
  qualityBreakdown: {
    native_reviewed: number;
    professional: number;
    machine: number;
    missing: number;
  };
  lastUpdated: Date;
  staleKeys: number;               // Keys where English source changed
}

/**
 * Language preference for a user
 */
interface UserLanguagePreference {
  userId: string;
  primaryLanguage: string;         // Selected UI language
  contentLanguage: string;         // Preferred content language (may differ)
  // Example: UI in English, destination content in Hindi
  transliterationEnabled: boolean;
  hinglishPreferred: boolean;      // Show Hinglish for Hindi content
  measurementSystem: 'metric' | 'imperial';
  numberFormat: 'indian' | 'western';  // Lakh/crore vs million/billion
}
```

---

## Open Problems

1. **Hinglish is not a standard locale.** BCP 47 does not officially recognize `hi-Latn` as a locale. Libraries like `Intl.NumberFormat` and `Intl.DateTimeFormat` will not format for it. We need to treat it as a translation-only locale with formatting inherited from `en-IN`.

2. **Transliteration accuracy vs. speed.** Real-time transliteration (type Latin, see native script suggestions) requires either a server round-trip (latency) or a client-side ML model (bundle size). The AI4Bharat models are accurate but heavy. We need to find the right trade-off, possibly using a hybrid approach (common words cached locally, rare words via API).

3. **Tamil script rendering inconsistencies.** Tamil has several Unicode normalization issues where the same visual character can be encoded multiple ways. This affects search (finding destinations by name) and translation matching. We need to normalize all Tamil text to a canonical form (NFC) at ingest time.

4. **Malayalam script variant selection.** Malayalam has a traditional and reformed script variant (post-1971 reform). Older users may prefer traditional glyphs while younger users expect reformed. Font choice determines which variant appears, but we cannot detect user preference automatically.

5. **Translation quality measurement for low-resource languages.** For Tier 3 languages (Kannada, Malayalam, Gujarati, Punjabi), we may not have in-house native speakers to evaluate translation quality. Crowd-sourced evaluation has reliability issues. We need a practical QA approach that does not require native speakers on staff.

6. **Font subsetting granularity.** Google Fonts provides pre-split subsets (Latin, Latin-ext, Devanagari, etc.) but these subsets include all characters for that script. For a travel agency, we might only need 500-800 unique Devanagari characters (travel vocabulary) out of the 1,200+ in the full subset. Custom subsetting could save 30-50% font size but requires a build pipeline.

7. **Code-switching in a single string.** Indian users frequently mix scripts mid-sentence: "Kerala ke backwaters bahut beautiful hain." Rendering this correctly requires proper font fallback stacks and CSS `unicode-range` declarations. The browser needs to switch fonts mid-text seamlessly.

---

## Next Steps

1. **Language tier decision document.** Confirm Tier 1/2/3 language groupings with product and business teams. Validate speaker/Internet user numbers against latest census and IAMAI data.

2. **Hinglish locale prototype.** Create a `hi-Latn` locale with ~50 common UI strings in Hinglish. Test with 5-10 Hindi-speaking users to validate tone and comprehensibility. Iterate on tone guidelines.

3. **Font rendering test suite.** Set up automated screenshot comparison for all 8 Indic scripts across Chrome, Firefox, Safari. Use the render test cases defined above. Run on BrowserStack.

4. **Transliteration POC.** Integrate AI4Bharat IndicTrans2 for search transliteration (Latin → native script). Measure latency, accuracy, and user satisfaction with A/B test against non-transliterated search.

5. **Translation quality framework.** Define the quality matrix for each tier × content type. Set up BLEU score reporting in CI for machine translations. Recruit 1-2 native speakers per Tier 1 language for review capacity.

6. **Font loading performance benchmark.** Measure page load with and without Indic fonts for Hindi, Tamil, and Bengali. Target: < 100ms FCP impact from font loading. Test `next/font/google` optimization.

7. **Line-height and typography audit.** Test all Indic scripts at the proposed line-height adjustments. Create a typography reference page showing all scripts at all sizes (12px, 14px, 16px, 18px, 24px, 32px) for design sign-off.

---

**End of Document**

**Next:** [Content Workflow](I18N_04_CONTENT_WORKFLOW.md)
