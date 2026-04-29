# User Guidance & Helper System — Help Content Strategy & Accessibility

> Research document for help content authoring, multilingual support, accessibility compliance, and content lifecycle management.

---

## Key Questions

1. **How is help content authored, reviewed, and maintained?**
2. **What multilingual support is needed for India's diverse agent base?**
3. **How do help features comply with accessibility standards?**
4. **What content lifecycle ensures help stays current?**
5. **How do we measure help content effectiveness?**

---

## Research Areas

### Help Content Management

```typescript
interface HelpContentSystem {
  authoring: ContentAuthoring;
  review: ContentReview;
  publishing: ContentPublishing;
  lifecycle: ContentLifecycle;
  analytics: ContentAnalytics;
}

interface ContentAuthoring {
  formats: ContentFormat[];
  templates: ContentTemplate[];
  media: MediaLibrary;
  versioning: ContentVersioning;
}

type ContentFormat =
  | 'article'                          // Standard help article
  | 'tutorial'                         // Step-by-step guide
  | 'faq'                              // Question and answer
  | 'video'                            // Screen recording
  | 'gif_walkthrough'                  // Animated walkthrough
  | 'infographic'                      // Visual reference
  | 'cheat_sheet'                      // Quick reference card
  | 'troubleshooting';                 // Problem-solution pairs

// Content templates:
//
// ARTICLE TEMPLATE:
// - Title (max 60 chars)
// - Summary (1-2 sentences, shown in search results)
// - Prerequisites (what you need before starting)
// - Steps (numbered, with screenshots)
// - Tips (optional pro tips)
// - Related articles (3-5 links)
// - Feedback ("Was this helpful?")
//
// TUTORIAL TEMPLATE:
// - Title
// - Duration (estimated time)
// - Learning objectives (what you'll learn)
// - Prerequisites
// - Interactive steps (linked to guided tour)
// - Practice exercise (optional)
// - Assessment quiz (optional)
// - Next tutorial suggestion
//
// TROUBLESHOOTING TEMPLATE:
// - Problem statement
// - Symptoms (how to identify this issue)
// - Cause (why it happens)
// - Solution steps (with screenshots)
// - Prevention (how to avoid in future)
// - Escalation (when to contact support)
//
// Content authoring workflow:
// ┌─────────────────────────────────────────┐
// │  Help Content Editor                      │
// │                                            │
// │  Title: How to confirm a trip              │
// │  Category: [Trip Management ▼]            │
// │  Audience: [All Agents ▼]                 │
// │                                            │
// │  Summary:                                  │
// │  [Confirming a trip moves it from pending  │
// │   to confirmed status and triggers         │
// │   notifications to the customer.]          │
// │                                            │
// │  Steps:                                    │
// │  1. [Screenshot: Status dropdown]          │
// │     Open the status dropdown in the        │
// │     trip header...                         │
// │  2. [Screenshot: Confirm dialog]           │
// │     Select "Confirmed" from the list...    │
// │                                            │
// │  [Add Step] [Add Media] [Preview]          │
// │                                            │
// │  [Save Draft] [Submit for Review]          │
// └─────────────────────────────────────────────┘

interface ContentReview {
  // Review process:
  // 1. Author submits draft
  // 2. Reviewer assigned (product team member)
  // 3. Review checklist:
  //    ☐ Accuracy: Steps match current UI
  //    ☐ Completeness: All scenarios covered
  //    ☐ Clarity: Easy to understand
  //    ☐ Screenshots: Current and annotated
  //    ☐ Links: All links working
  //    ☐ SEO: Title and summary optimized
  //    ☐ Accessibility: Alt text on images
  //    ☐ Localization: Translation-ready
  // 4. Feedback → Author revises
  // 5. Approved → Published
  //
  // Auto-review checks:
  // - Screenshot freshness: Compare UI screenshots to current version
  // - Link validity: Check all links are not broken
  // - Content age: Flag articles older than 90 days for review
  // - Feedback score: Flag articles with <70% helpful rating
}

interface ContentLifecycle {
  // Content states:
  // DRAFT → REVIEW → PUBLISHED → STALE → ARCHIVED
  //
  // DRAFT: Being written
  // REVIEW: Pending approval
  // PUBLISHED: Live and visible
  // STALE: Flagged for update (UI changed, process changed)
  // ARCHIVED: Removed from search (still accessible via direct link)
  //
  // Staleness detection:
  // - UI change detected: Screenshot selector no longer matches
  // - Feature flag changed: Feature was enabled/disabled
  // - Process change: Related workflow was updated
  // - Time-based: Article not reviewed in 90 days
  // - User feedback: Helpfulness score dropped below threshold
  //
  // Auto-stale detection flow:
  // 1. Deployment includes UI changes
  // 2. System identifies affected help articles (by CSS selectors)
  // 3. Articles auto-flagged as "Needs Review"
  // 4. Notification sent to content owner
  // 5. Content owner reviews, updates, re-publishes
  // 6. If not updated in 7 days → Escalate to content team lead
}
```

### Multilingual Help System

```typescript
interface MultilingualHelp {
  languages: SupportedLanguage[];
  translation: TranslationWorkflow;
  delivery: LocalizedDelivery;
  fallback: LanguageFallback;
}

interface SupportedLanguage {
  code: string;                        // "en", "hi", "mr", "ta", "te", "bn"
  name: string;                        // "English", "Hindi", "Marathi"
  nativeName: string;                  // "English", "हिन्दी", "मराठी"
  coverage: number;                    // % of content translated
  quality: 'native' | 'professional' | 'machine';
  readDirection: 'ltr' | 'rtl';
}

// India language priority:
// Tier 1 (must have):
// - English (default, universal in travel industry)
// - Hindi (43.6% of India, most agents)
// - Hinglish (Romanized Hindi, common in informal communication)
//
// Tier 2 (should have):
// - Marathi (Maharashtra, Mumbai-based agencies)
// - Tamil (Tamil Nadu, Chennai agencies)
// - Bengali (West Bengal, Kolkata agencies)
// - Telugu (Telangana/Andhra, Hyderabad agencies)
//
// Tier 3 (nice to have):
// - Kannada, Malayalam, Gujarati, Punjabi
//
// Translation workflow:
// 1. Content authored in English
// 2. Machine translation (baseline)
// 3. Professional review for Tier 1 languages
// 4. Community review for Tier 2 languages
// 5. Published with quality badge:
//    ✅ Verified translation (human reviewed)
//    🤖 Machine translation (may have inaccuracies)
//
// Localization considerations:
// - Currency formatting: ₹15,000 (Indian) not INR 15,000
// - Date format: DD/MM/YYYY (Indian standard)
// - Number formatting: 1,00,000 (Indian lakh) not 100,000
// - Phone: +91-XXXXX-XXXXX format
// - Examples: Use Indian names, destinations, hotels
// - Legal references: Indian laws (DPDP, GST, etc.)
//
// Language fallback chain:
// User language: Marathi
// → Article exists in Marathi? → Show Marathi
// → No → Hindi version exists? → Show Hindi
// → No → Show English (always available)
// → Banner: "This article is in English. [हिन्दी version available]"
```

### Help Accessibility

```typescript
interface HelpAccessibility {
  wcag: WCAGCompliance;
  screenReader: ScreenReaderSupport;
  keyboard: KeyboardNavigation;
  cognitive: CognitiveAccessibility;
}

// WCAG 2.2 compliance for help system:
//
// PERCEIVABLE:
// - All images have alt text (screenshots described in detail)
// - Color not the only indicator (icons + text for help types)
// - Minimum contrast ratio 4.5:1 for help text
// - Respects system font size settings
// - Video captions for all tutorial videos
// - Audio descriptions for visual walkthroughs
//
// OPERABLE:
// - All help features keyboard-accessible
// - Tab order: Help button → Help panel → Search → Results → Article
// - Escape closes help panel and returns focus to trigger
// - Arrow keys navigate search results
// - Enter opens selected article
// - Tour navigation with Tab and Enter
//
// UNDERSTANDABLE:
// - Plain language (no jargon without explanation)
// - Consistent help icon across all pages
// - Predictable help panel location (always right side)
// - Clear labels on all help actions
// - Error recovery guidance for every error state
//
// ROBUST:
// - Semantic HTML for all help content
// - ARIA attributes for dynamic help elements
// - Help panel announced by screen readers
// - Tour steps announced as they appear
// - Loading states announced ("Loading help article...")

// Screen reader tour experience:
// [Tour step appears]
// Screen reader announces:
// "Tour step 3 of 8: Confirming the trip.
//  Click the Confirm button to change trip status to confirmed.
//  Press Enter to proceed to the next step, or Escape to skip."
//
// [Tooltip appears]
// Screen reader announces:
// "Tip: This field accepts markup percentage between 0 and 50.
//  Default is 12 percent. Press Escape to dismiss."

// Cognitive accessibility:
// - Simple, scannable content (short paragraphs, bullet points)
// - Progressive disclosure (summary first, details on expand)
// - Consistent patterns (all articles follow same structure)
// - Visual hierarchy (headings, numbered steps, callout boxes)
// - No auto-playing videos or animations
// - Option to reduce help density in settings
// - "I need more help" always available as escalation
```

### Content Effectiveness Measurement

```typescript
interface ContentAnalytics {
  metrics: ContentMetrics;
  insights: ContentInsight[];
  reports: AnalyticsReport[];
}

interface ContentMetrics {
  // Per-article metrics:
  views: number;
  uniqueReaders: number;
  avgTimeOnPage: number;               // Seconds
  helpfulRate: number;                 // 👍 / (👍 + 👎)
  bounceRate: number;                  // Opened and immediately closed
  completionRate: number;              // Read to end (scrolled past 80%)
  escalationRate: number;              // Led to support contact
  searchAppearanceRate: number;        // How often it appears in search
  searchClickRate: number;             // Clicked when appeared in search
  lastUpdated: Date;
  daysSinceReview: number;
}

interface ContentInsight {
  type: 'gap' | 'stale' | 'popular' | 'unhelpful' | 'trending';
  articleId?: string;
  description: string;
  recommendation: string;
  priority: 'low' | 'medium' | 'high';
}

// Content insight examples:
//
// GAP (no article exists for common question):
// "15 users searched for 'how to handle visa rejection' last week.
//  No matching article exists. Recommend creating one."
//
// STALE (article may be outdated):
// "Article 'Creating a trip' hasn't been reviewed in 120 days.
//  The trip creation flow was updated 2 weeks ago.
//  Recommend review and update."
//
// POPULAR (heavily used, worth investing in):
// "Article 'GST on travel packages' has 500+ views/week
//  and 92% helpful rate. Consider expanding with examples."
//
// UNHELPFUL (needs improvement):
// "Article 'Custom views' has 38% helpful rate (avg: 72%).
//  Common feedback: 'Too complex, need simpler explanation.'
//  Recommend rewrite with more screenshots."
//
// TRENDING (sudden spike in views):
// "Article 'Cancellation policies' views up 300% this week.
//  Likely due to monsoon season cancellations.
//  Ensure content covers weather-related cancellations."

// Monthly content report:
// ┌─────────────────────────────────────────┐
// │  Help Content Report — April 2026        │
// │                                            │
// │  Overview                                  │
// │  Total articles: 145 (+12 new)            │
// │  Total views: 12,450 (+15%)              │
// │  Avg helpful rate: 74% (+2%)             │
// │                                            │
// │  Top 5 Articles                            │
// │  1. Confirming a trip — 890 views (91%)   │
// │  2. GST on packages — 756 views (88%)     │
// │  3. WhatsApp integration — 623 views (82%)│
// │  4. Trip templates — 534 views (79%)      │
// │  5. Payment links — 498 views (85%)       │
// │                                            │
// │  Needs Attention                           │
// │  • 3 articles flagged stale               │
// │  • 2 articles below 50% helpful rate      │
// │  • 1 content gap identified               │
// │                                            │
// │  Content Gaps (searched, no result)        │
// │  • "How to handle visa rejection" (15x)   │
// │  • "Group booking discount rules" (12x)   │
// │  • "TCS on international packages" (10x)  │
// │                                            │
// │  [View Full Report] [Export Data]          │
// └─────────────────────────────────────────────┘
```

---

## Open Problems

1. **Content-authoring bottleneck** — Product team members are busy building features; writing help articles competes for their time. AI-assisted drafting (generate article from code changes) can help but requires human review.

2. **Translation quality at scale** — Tier 2 and 3 languages rely on machine translation, which often produces unnatural phrasing for UI instructions. Professional translation for 10+ languages is expensive and slow.

3. **Screenshot staleness** — Help articles with screenshots become outdated with every UI change. Automated screenshot comparison and re-capture is technically complex but necessary for accuracy.

4. **Accessibility testing coverage** — Testing all help content (articles, tours, tooltips, AI responses) with screen readers and keyboard-only navigation is time-consuming. Automated accessibility testing catches some issues but not all.

5. **Help content vs. product velocity** — Fast-moving product development outpaces help content updates. Features ship before documentation is ready. Embedding help content creation into the development workflow is essential but resisted by engineering teams.

---

## Next Steps

- [ ] Build help content management system with authoring, review, and publishing workflow
- [ ] Implement multilingual content delivery with Tier 1/2/3 language support
- [ ] Ensure WCAG 2.2 compliance for all help features (tooltips, tours, AI assistant)
- [ ] Create content effectiveness analytics with gap detection and staleness alerts
- [ ] Study help content platforms (GitBook, ReadMe, Zendesk Guide, Confluence, Notion)
