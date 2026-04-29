# Multi-Language & Internationalization — Content Workflow

> Research document for translation workflow management, translator management, translation memory, quality assurance, content synchronization, RTL testing, and cultural review processes.

---

## Key Questions

1. **What is the end-to-end workflow from string freeze to translated deployment?**
2. **Should we use in-house translators, an agency, community translators, or a hybrid model?**
3. **How do we build and maintain a translation memory and glossary for Indian travel terminology?**
4. **What automated quality checks can we run on translations before they reach users?**
5. **When the English source changes, how do we identify and update affected translations?**
6. **How do we test RTL layouts without hiring Arabic/Urdu-speaking testers?**
7. **What is the cultural review process to avoid offensive or insensitive content?**

---

## Research Areas

### Translation Workflow Pipeline

```typescript
interface TranslationWorkflowStage {
  name: string;
  owner: string;
  inputs: string[];
  outputs: string[];
  automation: 'full' | 'semi' | 'manual';
  tools: string[];
  sla: string;                     // Time budget
  qualityGate: string;             // What must pass before next stage
}

// End-to-end translation workflow:
//
// ┌─────────────┐    ┌─────────────┐    ┌──────────────┐
// │  1. STRING  │───▶│  2. EXTRACT │───▶│ 3. CLASSIFY  │
// │    FREEZE   │    │    KEYS     │    │   & ROUTE    │
// └─────────────┘    └─────────────┘    └──────────────┘
//       │                                       │
//  Developer marks   CI scans codebase    Route to machine
//  feature complete  for new/changed      or professional
//                    translation keys     based on tier/content
//
//                    ┌─────────────┐    ┌──────────────┐
//                    │  5. REVIEW  │◀───│  4. TRANSLATE│
//                    │    & QA     │    │              │
//                    └──────┬──────┘    └──────────────┘
//                           │
//                    ┌──────▼──────┐    ┌──────────────┐
//                    │  6. MERGE   │───▶│  7. DEPLOY   │
//                    │  & VALIDATE │    │   & VERIFY   │
//                    └─────────────┘    └──────────────┘
//
// Stage 1: STRING FREEZE
//   - Developer marks PR as "string frozen" (no more text changes)
//   - CI checks: no hardcoded strings, all text uses t() function
//   - Tools: eslint i18n plugin, custom AST scanner
//   - SLA: Before merge
//   - Quality gate: 0 hardcoded strings detected
//
// Stage 2: EXTRACT KEYS
//   - Scan codebase for t('key') calls
//   - Compare against existing translation files
//   - Generate delta: {new: [...], changed: [...], deleted: [...]}
//   - Tools: i18next-parser, custom extraction script
//   - SLA: < 5 minutes (automated in CI)
//   - Quality gate: No broken ICU patterns, no duplicate keys
//
// Stage 3: CLASSIFY & ROUTE
//   - New keys classified by:
//     a) Content type (UI string, email, notification, help text)
//     b) Language tier (Tier 1 → professional, Tier 3 → machine)
//     c) Priority (P0 = visible on homepage, P1 = inner pages, P2 = error states)
//   - Route to appropriate translation channel
//   - SLA: < 1 minute (automated)
//
// Stage 4: TRANSLATE
//   - Tier 1 + UI strings → Professional translation (Lokalise/Phrase)
//   - Tier 2 + content → Machine translation + professional spot review
//   - Tier 3 → Machine translation only (Google Translate / DeepL)
//   - Hinglish → Specialist translator (not machine-translatable)
//   - SLA: 24h (P0), 48h (P1), 1 week (P2)
//   - Quality gate: Translation memory match rate > 30% (indicative of consistency)
//
// Stage 5: REVIEW & QA
//   - Automated checks: placeholder preservation, length limits, HTML integrity
//   - Native speaker review for Tier 1
//   - Spot check (10% sample) for Tier 2
//   - Cultural review for destination content
//   - SLA: 24h after translation delivery
//   - Quality gate: All automated checks pass, reviewer approval
//
// Stage 6: MERGE & VALIDATE
//   - Merge translations into JSON files
//   - Validate JSON syntax
//   - Check key completeness (100% for Tier 1)
//   - TypeScript compilation check (type-safe translation keys)
//   - SLA: < 10 minutes (automated)
//   - Quality gate: Build succeeds, no missing keys for Tier 1
//
// Stage 7: DEPLOY & VERIFY
//   - Deploy translation bundles to CDN
//   - Smoke test: load each locale, verify key pages render
//   - Monitor: translation error rate in production logs
//   - SLA: < 15 minutes
//   - Quality gate: 0 translation errors in smoke test

interface WorkflowConfig {
  trigger: 'string_freeze' | 'continuous' | 'scheduled';
  // Recommended: continuous for Tier 1 (translate as keys appear)
  //              scheduled for Tier 2/3 (batch weekly)
  stringFreezeSchedule: string;    // e.g., 'every sprint Tuesday'
  translationDeadline: string;     // e.g., '2 days before release'
  emergencyFastTrack: string;      // Process for urgent translations (< 4h)
}

// Emergency fast-track process:
//   For critical issues (legal text, payment error, safety notice):
//   1. Developer tags key as 'P0-emergency'
//   2. System alerts on-call translator immediately
//   3. Translator delivers within 2 hours
//   4. Auto-review + deploy (skip normal review queue)
//   5. Post-hoc review within 24 hours
```

### Translator Management

```typescript
interface TranslatorModel {
  type: 'in_house' | 'agency' | 'community' | 'machine';
  costPerWord: string;
  qualityLevel: TranslationQuality;
  turnaroundTime: string;
  scalability: 'low' | 'medium' | 'high';
  languages: string[];
  bestFor: string;
}

// Translator model comparison:
//
// ┌──────────────┬───────────────┬──────────────┬───────────────┬──────────────┐
// │              │  In-House     │   Agency     │  Community    │   Machine    │
// ├──────────────┼───────────────┼──────────────┼───────────────┼──────────────┤
// │ Cost/word    │ ₹5-10         │ ₹3-8         │ ₹0-2          │ ₹0.01        │
// │ Quality      │ Native rev.   │ Professional │ Variable      │ Machine      │
// │ Turnaround   │ Same day      │ 24-48h       │ 1-7 days      │ < 1 sec      │
// │ Scalability  │ Low (hiring)  │ High         │ Medium        │ Unlimited    │
// │ Languages    │ 2-3 max       │ 10+          │ Any           │ 100+         │
// │ Context      │ Best (domain) │ Good         │ Variable      │ None         │
// │ Best for     │ Tier 1 UI     │ Tier 1+2     │ Tier 3        │ All tiers    │
// └──────────────┴───────────────┴──────────────┴───────────────┴──────────────┘
//
// Recommended hybrid model:
//
// IN-HOUSE (2-3 translators):
//   - 1 Hindi translator (Hindi + Hinglish + Marathi — all Devanagari)
//   - 1 Tamil translator (Tamil + Kannada + Malayalam — Dravidian family)
//   - 1 Bengali translator (Bengali + Assamese — Eastern family)
//   Coverage: 7 languages with 3 people
//   Focus: UI strings, emails, customer-facing content
//
// AGENCY (contracted):
//   - Professional translation agency with Indian language expertise
//   - Used for: destination content, help articles, legal/compliance text
//   - SLA: 48 hours standard, 24 hours expedited
//   - Quality: Professional + agency QA
//
// COMMUNITY (crowd-sourced):
//   - Regional travel agents and guides who are native speakers
//   - Incentive: early access to features, recognition on platform
//   - Used for: destination descriptions, cultural notes, travel tips
//   - Quality: Community moderator reviews
//
// MACHINE (always-on):
//   - Google Cloud Translation API (primary)
//   - DeepL API (for higher quality where available)
//   - AI4Bharat IndicTrans2 (for Indian language pairs)
//   - Used for: Tier 3 initial translation, drafts for human review

interface TranslatorProfile {
  id: string;
  name: string;
  languages: TranslatorLanguage[];
  specializations: string[];       // 'ui_strings', 'legal', 'marketing', 'destination_content'
  availability: 'full_time' | 'part_time' | 'on_demand';
  qualityScore: number;            // 1-5 based on review feedback
  turnaroundHours: number;
  rate: { currency: string; perWord: number };
}

interface TranslatorLanguage {
  from: string;                    // Source language
  to: string;                      // Target language
  proficiency: 'native' | 'professional' | 'fluent';
  domainExpertise: string[];       // 'travel', 'legal', 'finance'
}
```

### Translation Memory and Glossary

```typescript
interface TranslationMemoryEntry {
  id: string;
  sourceText: string;
  sourceLocale: string;
  targetText: string;
  targetLocale: string;
  similarity: number;              // 1.0 for exact match
  context: string;                 // Where this string appears
  createdAt: Date;
  usageCount: number;              // How many times reused
  lastUsed: Date;
  quality: TranslationQuality;
}

interface TranslationMemoryConfig {
  enabled: boolean;
  matchingThreshold: number;       // 0.8 = 80% similarity minimum
  maxSuggestions: number;          // Show top N matches to translator
  autoSuggest: boolean;            // Auto-fill when > 95% match
  storeApproved: boolean;          // Store all approved translations
  deduplication: boolean;          // Merge similar entries
}

// Translation memory for Indian travel domain:
//
// High-reuse strings (expect 80%+ TM match rate):
//   - "Check-in: 2:00 PM" → varies only by time
//   - "₹{{amount}} per night" → varies only by amount
//   - "Cancellation free before {{date}}" → template with variable
//   - Status labels: "Confirmed", "Pending", "Cancelled"
//
// Domain-specific glossary entries:
//
// English → Hindi:
//   "itinerary" → "यात्रा कार्यक्रम" (not "यात्रा विवरण")
//   "booking" → "बुकिंग" (not "आरक्षण" — too formal)
//   "checkout" → "चेक-आउट" (not transliterated differently)
//   "package" → "पैकेज" (not "संपुट")
//   "destination" → "गंतव्य" (not "मंजिल" in formal context)
//   "hotel" → "होटल" (not "आवास")
//   "flight" → "फ़्लाइट" (not "उड़ान" in booking context)
//   "cancellation" → "रद्दीकरण" (formal) or "cancel" (informal)
//   "refund" → "रिफ़ंड" (not "वापसी")
//   "visa" → "वीज़ा" (not "अनुमति")
//   "insurance" → "बीमा" (standard Hindi word)
//   "GST" → "GST" (never translate)
//   "TCS" → "TCS" (never translate)
//   "PAN" → "PAN" (never translate)
//   "Aadhaar" → "आधार" (in Hindi context)
//
// Brand terms (never translate, always English):
//   - Product names: "Waypoint OS", "Trip Builder"
//   - Feature names: "Inbox", "Workspace", "Timeline"
//   - Legal terms: "GST", "TCS", "PAN", "Aadhaar"
//   - Technical terms: "API", "URL", "PDF"

interface GlossaryEntry {
  id: string;
  term: string;                    // English source term
  translations: Record<string, {
    translation: string;
    doNotTranslate: boolean;       // true for brand/legal terms
    notes: string;                 // Usage notes for translators
    alternatives: string[];        // Other acceptable translations
  }>;
  category: 'brand' | 'legal' | 'technical' | 'travel' | 'general';
  doNotTranslate: boolean;         // Global: keep in English across all languages
  notes: string;                   // Guidelines for translators
}

interface GlossaryConfig {
  enforced: boolean;               // Block translations that violate glossary
  suggestions: boolean;            // Suggest glossary terms to translators
  reviewFlag: boolean;             // Flag non-glossary translations for review
}
```

### Quality Assurance for Translations

```typescript
interface TranslationQAConfig {
  automatedChecks: AutomatedCheck[];
  humanReview: HumanReviewConfig[];
  reporting: QAReportingConfig;
}

interface AutomatedCheck {
  name: string;
  description: string;
  severity: 'error' | 'warning' | 'info';
  fixable: boolean;                // Can auto-fix (e.g., placeholder restore)
}

// Automated QA checks for translations:
const AUTOMATED_CHECKS: AutomatedCheck[] = [
  {
    name: 'placeholder_preservation',
    description: 'All {{variable}} placeholders must be present in translation',
    severity: 'error',
    fixable: false,
    // Example:
    //   EN: "Hello {{name}}, your trip to {{destination}} is confirmed"
    //   HI: "नमस्ते {{name}}, आपकी {{destination}} यात्रा कन्फर्म है"  ✓
    //   HI: "नमस्ते, आपकी यात्रा कन्फर्म है"                        ✗ (missing {{name}}, {{destination}})
  },
  {
    name: 'html_tag_preservation',
    description: 'All HTML tags must be preserved in translation',
    severity: 'error',
    fixable: false,
    // Example:
    //   EN: "<strong>Important:</strong> Your booking expires in <em>24 hours</em>"
    //   HI: "<strong>ज़रूरी:</strong> आपकी बुकिंग <em>24 घंटे</em> में expire होगी"  ✓
  },
  {
    name: 'length_ratio',
    description: 'Translation length should be within 2x of English source',
    severity: 'warning',
    fixable: false,
    // Indian languages are typically 20-50% longer than English
    // Hindi: ~1.3x, Tamil: ~1.4x, Bengali: ~1.3x
    // Flag if > 2x (likely excessive or includes garbage text)
  },
  {
    name: 'glossary_adherence',
    description: 'Brand and legal terms must not be translated',
    severity: 'error',
    fixable: false,
    // "GST", "TCS", "PAN", "Aadhaar", product names must stay in English
  },
  {
    name: 'same_language_detection',
    description: 'Translation should not be identical to source (unless intentional)',
    severity: 'warning',
    fixable: false,
    // If Hindi translation == English source, likely untranslated
  },
  {
    name: 'empty_translation',
    description: 'Translation must not be empty',
    severity: 'error',
    fixable: false,
  },
  {
    name: 'unicode_normalization',
    description: 'Text must be in NFC normalization form',
    severity: 'info',
    fixable: true,
    // Normalize all Indic text to prevent duplicate entries
  },
  {
    name: 'profanity_check',
    description: 'Translation must not contain profanity or offensive terms',
    severity: 'error',
    fixable: false,
    // Use profanity lists per language (Limited availability for Indian languages)
  },
  {
    name: 'number_preservation',
    description: 'Numeric values must match source',
    severity: 'error',
    fixable: false,
    // "₹25,000" → "₹25,000" (numbers stay, format may change)
  },
  {
    name: 'url_preservation',
    description: 'URLs and email addresses must not be modified',
    severity: 'error',
    fixable: false,
  },
];

interface HumanReviewConfig {
  type: 'native_review' | 'spot_check' | 'cultural_review';
  sampleRate: number;              // Percentage of translations to review
  reviewers: string[];             // Reviewer IDs or team names
  turnaroundHours: number;
  criteria: string[];
}

// Human review matrix:
//
// Tier 1 (en, hi, Hinglish):
//   - Native review: 100% of UI strings, 50% of content
//   - Spot check: 10% of emails/notifications
//   - Cultural review: 100% of destination content
//   - Reviewers: In-house translators
//
// Tier 2 (mr, ta, bn, te):
//   - Native review: 25% of UI strings
//   - Spot check: 10% of all translations
//   - Cultural review: 50% of destination content
//   - Reviewers: Agency translators + community moderators
//
// Tier 3 (kn, ml, gu, pa):
//   - Native review: None (rely on automated checks)
//   - Spot check: 5% sample quarterly
//   - Cultural review: None initially
//   - Reviewers: Community volunteers (when available)
```

### Content Synchronization

```typescript
interface ContentSyncConfig {
  // When English source changes, which translations update?
  strategy: 'immediate' | 'batched' | 'on_demand';
  staleDetection: 'hash' | 'version' | 'timestamp';
  autoUpdate: AutoUpdateRule[];
  notificationTargets: string[];
}

interface AutoUpdateRule {
  changeType: 'added' | 'modified' | 'deleted' | 'context_changed';
  sourcePriority: 'P0' | 'P1' | 'P2';
  targetTiers: number[];           // Which tiers to auto-update
  action: 'auto_translate' | 'queue_for_translation' | 'mark_stale' | 'ignore';
}

// Content sync strategy:
//
// Source change detection:
//   Each English translation key has a hash of its value.
//   When the hash changes, the key is marked as "source changed."
//
// Sync rules by change type:
//
// NEW KEY ADDED:
//   Tier 1 → Immediate professional translation (24h SLA)
//   Tier 2 → Batch with next weekly translation cycle
//   Tier 3 → Immediate machine translation
//
// SOURCE KEY MODIFIED:
//   All tiers → Mark existing translations as "stale"
//   Tier 1 → Re-queue for professional translation
//   Tier 2 → Re-translate with machine, flag for review
//   Tier 3 → Machine re-translate immediately
//
// SOURCE KEY DELETED:
//   All tiers → Remove translation entry
//   Keep in translation memory for future reuse
//
// CONTEXT CHANGED (screenshot/notes updated):
//   All tiers → Flag for re-review (translation may still be valid)
//   Notify translator: "Context for this key has changed"

interface StaleTranslation {
  key: string;
  namespace: string;
  locale: string;
  currentTranslation: string;
  englishSource: string;
  englishSourceHash: string;
  translationHash: string;         // Hash when translation was created
  staleness: 'minor' | 'major';   // Minor = typo fix, Major = meaning change
  detectedAt: Date;
  assignedTo?: string;
  status: 'detected' | 'assigned' | 'in_progress' | 'resolved';
}

// Staleness dashboard:
//
// ┌─────────────────────────────────────────────────┐
// │ Translation Sync Status                          │
// ├──────────┬─────────┬─────────┬──────────────────┤
// │ Language │ Current │  Stale  │ Coverage         │
// ├──────────┼─────────┼─────────┼──────────────────┤
// │ English  │  1,960  │    0    │ 100% (source)    │
// │ Hindi    │  1,920  │   15    │  97.9%           │
// │ Tamil    │  1,850  │   45    │  94.3%           │
// │ Bengali  │  1,800  │   60    │  91.8%           │
// │ Kannada  │  1,650  │  120    │  84.1%           │
// └──────────┴─────────┴─────────┴──────────────────┘
```

### RTL Testing

```typescript
interface RTLTestPlan {
  // Even if Arabic/Urdu is not a launch language,
  // we should build RTL-ready to avoid future rework.
  //
  // RTL testing strategy:

  approach: 'css_logical_properties' | 'rtl_override' | 'hybrid';
  testEnvironments: RTLTestEnvironment[];
  automatedChecks: RTLAutoCheck[];
  manualTestCases: RTLManualTestCase[];
}

interface RTLTestEnvironment {
  browser: string;
  os: string;
  language: string;                // 'ar', 'ur', 'he'
  device: 'desktop' | 'mobile' | 'tablet';
}

// RTL automated checks (can run without Arabic/Urdu speakers):
const RTL_AUTO_CHECKS: RTLAutoCheck[] = [
  {
    name: 'no_physical_properties',
    description: 'CSS should use logical properties (margin-inline-start) not physical (margin-left)',
    detection: 'Parse CSS for left/right properties that should be inline-start/end',
  },
  {
    name: 'no_hardcoded_text_align',
    description: 'No text-align: left/right without dir attribute check',
    detection: 'Find text-align: left/right in CSS',
  },
  {
    name: 'icon_direction',
    description: 'Directional icons (arrows, chevrons) should flip in RTL',
    detection: 'Find arrow/chevron icons and verify CSS transform or RTL variant',
  },
  {
    name: 'form_label_position',
    description: 'Form labels should align correctly in RTL',
    detection: 'Screenshot comparison LTR vs RTL',
  },
  {
    name: 'flex_direction',
    description: 'Flexbox rows should reverse in RTL',
    detection: 'Find display: flex without appropriate RTL handling',
  },
];

interface RTLManualTestCase {
  page: string;
  element: string;
  expectedBehavior: string;
  notes: string;
}

// Manual RTL test cases (hire 1 Arabic speaker for 1 day):
//
// 1. Booking flow: complete booking in Arabic, verify all steps
// 2. Trip detail page: verify itinerary, pricing, photos layout
// 3. Search results: verify filter panel, result cards
// 4. Forms: verify name, address, payment forms
// 5. Navigation: verify breadcrumbs, sidebar, tabs
// 6. Modals/dialogs: verify close button position, action buttons
// 7. Tables: verify column order, sorting indicators
// 8. Date picker: verify calendar layout, day order (Saturday first in Arabic)
// 9. Notifications: verify toast position, close button
// 10. Print itinerary: verify PDF output layout

interface RTLDevTool {
  // Development tool for RTL testing without Arabic content:
  //
  // Add a dev-only toggle that:
  //   1. Sets dir="rtl" on <html>
  //   2. Replaces all text with pseudo-localized versions:
  //      "Hello World" → "Hello World [RTL_TEST]"
  //      Or use: "WolrolH Hello" (reversed for visual testing)
  //   3. Adds visual indicators for broken RTL:
  //      Red outline: Uses physical CSS properties
  //      Yellow outline: May need RTL adjustment
  //      Green outline: Uses logical properties (correct)
  //
  // This allows any developer to test RTL without knowing Arabic.
}
```

### Cultural Review Process

```typescript
interface CulturalReviewConfig {
  // Cultural review prevents offensive or insensitive content
  // from reaching users. Critical for Indian market with
  // diverse religious and cultural sensitivities.

  reviewCategories: CulturalReviewCategory[];
  reviewers: CulturalReviewer[];
  escalationPath: string[];
}

interface CulturalReviewCategory {
  category: string;
  description: string;
  examples: string[];
  severity: 'block' | 'warn' | 'info';
}

// Cultural review categories for Indian travel content:
//
// 1. RELIGIOUS SENSITIVITY
//    - Temple visit descriptions must mention dress codes
//    - Non-Hindu temples may have entry restrictions (mention respectfully)
//    - Mosque visit timing (avoid during prayer times)
//    - Church visit on Sunday (mention mass timing)
//    - Gurudwara: mention head covering requirement
//    - Never show images of deities in casual/disrespectful context
//    Severity: BLOCK
//
// 2. FOOD & DIETARY
//    - Always mention vegetarian options prominently
//    - Mark restaurants with "Pure Veg" (no onion/garlic for Jain)
//    - Halal certification for Muslim travelers
//    - Beef: Avoid mentioning in Hindi-belt destinations
//    - Pork: Avoid mentioning in Muslim-majority areas
//    - Alcohol: Mention only for relevant venues, not family content
//    Severity: BLOCK
//
// 3. CLOTHING & DRESS
//    - Beach destinations: conservative imagery for family segment
//    - Temple visits: mention modest clothing requirements
//    - Hill stations: warm clothing advisory
//    - Rajasthan/Goa: respect local dress norms
//    Severity: WARN
//
// 4. GEOGRAPHIC & POLITICAL
//    - Jammu & Kashmir: Use "Jammu & Kashmir" (not "Indian Kashmir")
//    - Northeast India: Avoid "exotic" stereotypes
//    - Border areas: Check current travel advisories
//    - International: Verify destination names are politically current
//    Severity: BLOCK
//
// 5. SOCIAL & CASTE
//    - Avoid reinforcing stereotypes about any community
//    - Use "differently abled" not "disabled"
//    - Gender-inclusive language
//    - Avoid caste references entirely
//    Severity: BLOCK
//
// 6. ECONOMIC SENSITIVITY
//    - Price ranges should be appropriate for target segment
//    - Avoid "cheap" or "budget" when describing luxury to affluent customers
//    - Avoid "expensive" when targeting value-conscious segment
//    - "Value for money" is safe across segments
//    Severity: WARN

interface CulturalReviewer {
  id: string;
  name: string;
  expertise: string[];             // 'hinduism', 'islam', 'sikhism', 'food', 'geography'
  languages: string[];
  regions: string[];               // States they have cultural knowledge of
}

interface CulturalReviewChecklist {
  contentId: string;
  contentType: 'destination' | 'package' | 'email' | 'notification';
  reviewers: string[];
  checks: CulturalCheck[];
  status: 'pending' | 'approved' | 'flagged' | 'blocked';
}

interface CulturalCheck {
  category: string;
  question: string;
  result: 'pass' | 'flag' | 'fail';
  notes?: string;
}

// Example checklist for a Kerala destination page:
//
// [ ] Religious sites: Dress code mentioned for temples?
// [ ] Religious sites: Temple entry restrictions noted?
// [ ] Food: Vegetarian options mentioned?
// [ ] Food: No beef imagery in Kerala content? (Kerala allows beef, but pan-India audience)
// [ ] Food: Seafood prominent (Kerala specialty)?
// [ ] Images: Diverse representation (not just light-skinned)?
// [ ] Images: Women in appropriate attire for Kerala context?
// [ ] Language: No stereotypes about "God's Own Country" being overused?
// [ ] Geography: Correct district/region names?
// [ ] Seasonal: Monsoon advisory included?
// [ ] Pricing: Range appropriate for target segment?
// [ ] Accessibility: Mention wheelchair accessibility where available?
```

### Data Models for Content Workflow

```typescript
/**
 * Translation workflow state machine
 */
type TranslationWorkflowState =
  | 'source_created'
  | 'extracted'
  | 'routed'
  | 'in_translation'
  | 'translated'
  | 'in_review'
  | 'review_passed'
  | 'review_failed'
  | 'merged'
  | 'deployed'
  | 'source_changed'
  | 'stale';

interface TranslationWorkflowEntry {
  id: string;
  key: string;
  namespace: string;
  sourceLocale: string;
  targetLocale: string;
  sourceText: string;
  targetText?: string;
  state: TranslationWorkflowState;
  tier: 1 | 2 | 3;
  priority: 'P0' | 'P1' | 'P2';
  quality: TranslationQuality;
  assignedTranslator?: string;
  assignedReviewer?: string;
  sourceHash: string;
  translationHash?: string;
  qaResults: QAResult[];
  history: WorkflowHistoryEntry[];
  createdAt: Date;
  updatedAt: Date;
}

interface WorkflowHistoryEntry {
  from: TranslationWorkflowState;
  to: TranslationWorkflowState;
  timestamp: Date;
  actor: string;
  notes?: string;
}

interface QAResult {
  checkName: string;
  passed: boolean;
  severity: 'error' | 'warning' | 'info';
  message: string;
  autoFixed: boolean;
}

/**
 * Translation project (batch of keys for a release)
 */
interface TranslationProject {
  id: string;
  name: string;
  releaseTarget: string;
  status: 'open' | 'in_progress' | 'review' | 'complete';
  keys: TranslationWorkflowEntry[];
  deadline: Date;
  progress: {
    total: number;
    translated: number;
    reviewed: number;
    approved: number;
    deployed: number;
  };
}

/**
 * Workflow analytics
 */
interface WorkflowMetrics {
  averageTranslationTime: Record<string, number>;  // Per locale, in hours
  averageReviewTime: Record<string, number>;
  qualityPassRate: number;         // Percentage passing automated QA
  humanRejectionRate: number;      // Percentage rejected by human reviewers
  translationMemoryHitRate: number; // Percentage of keys with TM matches
  staleTranslationCount: number;
  coverageByLocale: Record<string, number>; // Per locale coverage percentage
}
```

---

## Open Problems

1. **Hinglish translation is not automatable.** Machine translation produces formal Hindi in Latin script (like "aapakee"), not natural Hinglish ("aapki"). Hinglish translations must be written by someone who actually speaks it, which means we cannot use standard MT for our third most important locale.

2. **Cultural review scaling.** With 10+ languages and hundreds of destination pages, cultural review is a bottleneck. A single Kerala destination page needs review for Hindu, Muslim, Christian, and secular sensitivities, across multiple languages. We need a way to make cultural review proportional to risk.

3. **Translation memory for Indian language pairs.** Most TM systems are optimized for English-to-European language pairs. Indian languages have different morphological complexity (agglutinative Dravidian languages, gendered Hindi conjugation) that reduces fuzzy match effectiveness. Standard Levenshtein distance overestimates similarity for morphologically rich languages.

4. **Glossary enforcement at scale.** With 10+ languages, each with 50-100 glossary terms, manual enforcement is impractical. We need automated glossary checking integrated into the translation platform, but the tools for Indian language glossary matching are immature.

5. **RTL testing without native speakers.** We want to build RTL-ready infrastructure, but hiring Arabic/Urdu speakers just for testing is expensive for a feature with uncertain timeline. The dev-tool approach (pseudo-localization + visual checks) catches layout issues but misses text-related problems (Arabic character joining, Urdu Nastaliq rendering).

6. **Content sync priority conflicts.** When English source changes frequently (agile development), translations are perpetually stale. We need a prioritization framework: which changes warrant immediate re-translation (legal text, payment errors) vs. which can wait (help text, tooltips).

7. **Community translator quality.** Community-sourced translations (from regional agents and guides) are variable quality. We need a lightweight review workflow that does not burden the community volunteers but still catches errors before deployment.

---

## Next Steps

1. **Select translation platform.** Evaluate Lokalise, Phrase, Transifex, and Crowdin for Indian language support, translation memory, glossary management, and API integration. Shortlist 2 and run a 2-week trial with Hindi and Tamil.

2. **Build translation extraction CI pipeline.** Create a GitHub Action that runs on every PR: extracts new/changed translation keys, generates a delta report, and posts it as a PR comment. Integrate with the chosen translation platform via API.

3. **Define initial glossary.** Create the first 50 glossary entries for travel-specific terms (English → Hindi, Tamil, Bengali). Include brand terms that must not be translated. Publish to the translation platform.

4. **Implement automated QA checks.** Build the 10 automated checks defined above as a post-translation hook. Run on every translation submission. Block deployment for errors, warn for warnings.

5. **Set up cultural review checklist.** Create a cultural review checklist template for destination content. Recruit 2-3 internal reviewers with diverse regional knowledge. Define the escalation path for flagged content.

6. **RTL dev tool prototype.** Build a browser extension or Next.js dev tool that toggles RTL mode with pseudo-localized text. Use it to audit the top 10 pages for RTL readiness. Document findings.

7. **Pilot translation project.** Run a pilot: translate the trip detail page and booking flow into Hindi (Tier 1) and Tamil (Tier 2). Measure: time per key, QA pass rate, translator feedback. Use results to refine the workflow.

---

**End of Document**

**Next:** [Master Index](I18N_MASTER_INDEX.md)
