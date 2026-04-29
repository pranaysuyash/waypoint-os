# Multi-Language & Internationalization — Master Index

> Navigation guide for the I18N research document series, covering architecture, localization, language support tiers, and content workflow for Indian travel agency context.

---

## Series Overview

**Topic:** Multi-Language & Internationalization for Indian Travel Agency
**Status:** Complete (5 of 5 documents)
**Last Updated:** 2026-04-28
**Scope:** Research and exploration documents (not implementation code). Focused on the unique challenges of supporting 10+ Indian languages in a Next.js travel agency platform.

---

## Key Themes

1. **India-first approach.** Unlike generic i18n guides, this series is grounded in Indian market realities: Hinglish as a primary locale, lakh/crore number formatting, landmark-based addressing, Devanagari/Tamil/Bengali script rendering, and cultural sensitivity across religions and regions.

2. **Tiered language strategy.** Not all languages are equal. Tier 1 (English, Hindi, Hinglish) gets native-reviewed translations. Tier 2 (Marathi, Tamil, Bengali, Telugu) gets professional translation. Tier 3 (Kannada, Malayalam, Gujarati, Punjabi) starts with machine translation.

3. **Hinglish as a first-class locale.** Hinglish (Hindi vocabulary in Latin script) is the dominant communication style for urban Indian internet users. This series treats it as a distinct locale with its own translation guidelines.

4. **Practical over ideal.** Every recommendation considers the constraint of a growing startup: limited translator budget, small team, need for automation. We favor "good enough with automation" over "perfect but expensive."

---

## Document Series

| # | Document | File | Focus | Status |
|---|----------|------|-------|--------|
| 1 | [Architecture](#i18n-01-architecture) | `I18N_01_ARCHITECTURE.md` | Framework selection, URL strategy, fallback chains, font rendering | Complete |
| 2 | [Localization](#i18n-02-localization) | `I18N_02_LOCALIZATION.md` | Currency, dates, numbers, addresses, phone, measurement units | Complete |
| 3 | [Language Tiers](#i18n-03-language-tiers) | `I18N_03_LANGUAGES.md` | Tier strategy, quality levels, Hinglish, transliteration, fonts | Complete |
| 4 | [Content Workflow](#i18n-04-content-workflow) | `I18N_04_CONTENT_WORKFLOW.md` | Translation pipeline, QA, glossary, cultural review, RTL testing | Complete |
| 5 | [Master Index](#i18n-master-index) | `I18N_MASTER_INDEX.md` | Series navigation, technology stack, cross-references | Complete |

---

## Document Summaries

### I18N_01: Architecture

**File:** `I18N_01_ARCHITECTURE.md`

Covers the technical foundation for multi-language support:

- **Framework comparison** — next-intl vs i18next vs paraglide-next for Next.js App Router
- **Translation file structure** — 13 namespaces, ~1,960 keys per language, JSON format
- **Locale detection** — URL path > user profile > cookie > Accept-Language > Geo-IP
- **URL strategy** — Path prefix (`/hi/trips`) recommended over subdomain or query params
- **Fallback chains** — Hindi to Hinglish to English; Marathi to Hindi to English
- **Translation pipeline** — 7 stages from string freeze to deployed translation
- **RTL support** — CSS logical properties for future Arabic/Urdu support
- **Indian script rendering** — Devanagari conjuncts, Tamil vowel signs, Bengali matras, font loading strategy

**Key data model:** `I18nConfig`, `LocaleDefinition`, `TranslationEntry`, `LocaleChangeEvent`

---

### I18N_02: Localization

**File:** `I18N_02_LOCALIZATION.md`

Covers localization beyond translation — formatting, forms, and regional adaptation:

- **Currency** — Indian lakh/crore grouping (`₹1,25,000`), compact notation (`₹1.25L`, `₹2.5Cr`)
- **Dates** — DD/MM/YYYY, IST single timezone, Indian fiscal year (April-March), festival calendars
- **Numbers** — Indian grouping pattern, distance in km, temperature in Celsius
- **Addresses** — Indian format with landmark field, PIN code lookup, state/UT dropdown
- **Phone numbers** — +91 country code, 5+5 mobile grouping, landline area codes
- **Name fields** — Flexible single-field with optional expansion, regional naming conventions
- **Regional content** — Destination descriptions in native scripts, cultural imagery guidelines
- **Measurement units** — Metric system defaults, context-dependent secondary units

**Key data model:** `LocalizationConfig`, `IndianAddress`, `LocalizedDestination`, `FormattedOutput`

---

### I18N_03: Language Tiers

**File:** `I18N_03_LANGUAGES.md`

Covers language prioritization, quality strategy, and script-specific challenges:

- **Tier 1 (Must Have):** English, Hindi, Hinglish — 80%+ of users, native-reviewed quality
- **Tier 2 (Should Have):** Marathi, Tamil, Bengali, Telugu — professional translation
- **Tier 3 (Nice to Have):** Kannada, Malayalam, Gujarati, Punjabi — machine translation
- **Quality levels** — Machine (₹0.01/word) → Professional (₹2-5/word) → Native reviewed (₹5-10/word)
- **Hinglish strategy** — Separate `hi-Latn` locale with conversational tone guidelines
- **Transliteration** — AI4Bharat IndicTrans2 for search, browser IME for form input
- **Font rendering** — Per-script test cases for Devanagari conjuncts, Tamil vowel signs, line-height adjustments
- **Typography rules** — Size and line-height adjustments per Indic script

**Key data model:** `LanguageTiers`, `PlatformLanguageConfig`, `QualityMatrix`, `UserLanguagePreference`

---

### I18N_04: Content Workflow

**File:** `I18N_04_CONTENT_WORKFLOW.md`

Covers the operational side of translation management:

- **7-stage pipeline** — String freeze → Extract → Classify → Translate → Review → Merge → Deploy
- **Translator model** — Hybrid: in-house (3 people, 7 languages) + agency + community + machine
- **Translation memory** — Domain-specific reuse for travel terms, fuzzy matching
- **Glossary** — 50+ terms with Hindi translations, brand terms that must not be translated
- **Automated QA** — 10 checks: placeholder preservation, HTML integrity, length ratio, glossary adherence
- **Content sync** — Source change detection via hashing, stale translation dashboard
- **RTL testing** — Dev tool with pseudo-localization, automated CSS property checks
- **Cultural review** — 6 categories: religious sensitivity, food/dietary, clothing, geographic, social, economic

**Key data model:** `TranslationWorkflowEntry`, `TranslationProject`, `WorkflowMetrics`, `CulturalReviewChecklist`

---

## Technology Stack

| Component | Recommended | Alternatives Considered | Rationale |
|-----------|-------------|------------------------|-----------|
| **i18n Framework** | next-intl | i18next, paraglide-next | First-class Next.js App Router, lightweight |
| **Translation Platform** | Lokalise or Phrase | Transifex, Crowdin | Indian language support, API, TM/glossary |
| **Machine Translation** | Google Cloud Translation + AI4Bharat | DeepL, Azure Translator | Best Indic language coverage |
| **Fonts** | Google Noto Sans family | Custom fonts, Adobe Fonts | Free, comprehensive Indic coverage |
| **Font Loading** | next/font/google | Self-hosted, TypeKit | Automatic optimization, subsetting |
| **Number Formatting** | Intl.NumberFormat('en-IN') | Custom formatter | Native lakh/crore grouping |
| **Date Formatting** | Intl.DateTimeFormat | date-fns, dayjs | Locale-aware, no extra dependency |
| **Phone Formatting** | libphonenumber-js | Custom regex | Google's phone metadata, India-specific |
| **Transliteration** | AI4Bharat IndicTrans2 | Google Input Tools | Open-source, offline-capable |
| **RTL Support** | CSS Logical Properties | rtlcss, postcss-rtl | Future-proof, no build overhead |
| **String Extraction** | i18next-parser | custom AST scanner | Mature, configurable |
| **QA Automation** | Custom checks + translation platform | None available off-shelf | Domain-specific checks needed |

---

## Cross-References

### Related Series in This Repository

| Series | Directory | Relationship |
|--------|-----------|--------------|
| **Internationalization** | `INTERNATIONALIZATION_0*.md` | Original i18n series (global scope, English/Spanish/French focus). Complements this series which focuses on Indian languages. |
| **Design System** | `DESIGN_0*.md`, `DESIGN_SYSTEM_*.md` | Component-level i18n patterns, RTL-aware components, typography tokens for Indic scripts |
| **Payment Processing** | `PAYMENT_PROCESSING_*.md` | Multi-currency, GST formatting, Indian payment methods (UPI, NET banking) |
| **Content Management** | `CONTENT_MANAGEMENT_*.md` | CMS with localized fields, destination content management |
| **Accessibility** | `A11Y_0*.md`, `ACCESSIBILITY_*.md` | Screen reader support for Indic languages, WCAG compliance in multilingual context |
| **Search Architecture** | `SEARCH_ARCHITECTURE_*.md` | Transliteration in search, multi-language search indexing |
| **Error Handling** | `ERROR_HANDLING_*.md` | Localized error messages, per-locale error formatting |
| **Analytics** | `ANALYTICS_*.md` | Language preference analytics, locale-specific dashboards |

### External References

| Resource | Use |
|----------|-----|
| CLDR (Unicode Common Locale Data Repository) | Locale data for Indian languages |
| BCP 47 | Language tag standard (`hi`, `ta`, `hi-Latn`) |
| ISO 15924 | Script codes (Deva, Taml, Beng, Latn) |
| AI4Bharat (IIT Madras) | Open-source Indic NLP and transliteration |
| Google Noto Fonts | Free, comprehensive Indic script fonts |
| India Post PIN Code API | Address auto-completion |
| RBI reference rates | Currency conversion for travel |

---

## Key Decisions Summary

| Decision | Choice | Status |
|----------|--------|--------|
| i18n framework | next-intl (with i18next for translation management) | Recommended, not finalized |
| URL strategy | Path prefix (`/hi/`, `/ta/`) | Recommended |
| Hinglish locale code | `hi-Latn` (non-standard but practical) | Proposed |
| Font loading | Google Noto Sans via `next/font/google` | Recommended |
| Number formatting | `Intl.NumberFormat('en-IN')` for lakh/crore | Recommended |
| Translation platform | Lokalise or Phrase (pending evaluation) | To be decided |
| Default locale | `en` (English) | Agreed |
| Fallback chain | Locale → related language → English | Recommended |
| RTL readiness | CSS logical properties from Day 1 | Recommended |
| Cultural review | Checklist-based, per destination | Proposed |

---

## Open Issues Across Series

Issues that span multiple documents and need cross-cutting resolution:

1. **Hinglish BCP 47 compliance** — `hi-Latn` is not standard. May cause issues with `Intl` APIs and third-party tools. (I18N_01, I18N_03)

2. **Font loading budget** — Loading 10+ Indic fonts is 1MB+. Need a concrete strategy for preloading, lazy loading, and fallback fonts. (I18N_01, I18N_03)

3. **Translation cost estimation** — At ~2,000 keys across 10 languages, professional translation costs ₹2-4 lakh initial + ₹50K/month ongoing. Budget needs business approval. (I18N_03, I18N_04)

4. **SSR hydration mismatch** — Server-detected locale vs. client-saved preference mismatch in Next.js App Router. Technical spike needed. (I18N_01)

5. **Content ownership** — Who owns translation quality per language? Need designated language owners. (I18N_03, I18N_04)

6. **Cultural review bandwidth** — Every destination page needs cultural review across multiple sensitivities. Current team does not have bandwidth. (I18N_04)

---

## Implementation Priority

Suggested implementation order based on business impact and dependencies:

```
Phase 1 (Month 1): Foundation
  ├── Framework spike (next-intl vs i18next)
  ├── URL strategy implementation (/en/, /hi/)
  ├── Translation file structure + CI extraction
  └── Hindi Tier 1 translations (50 most-used keys)

Phase 2 (Month 2): Core Localization
  ├── Currency/date/number formatting service
  ├── Indian address form component
  ├── Phone input component
  └── Hindi full coverage (all UI strings)

Phase 3 (Month 3): Language Expansion
  ├── Hinglish locale + translations
  ├── Tamil Tier 2 translations
  ├── Bengali Tier 2 translations
  └── Font loading optimization for Devanagari + Tamil

Phase 4 (Month 4-6): Scale
  ├── Translation memory + glossary
  ├── Content sync pipeline
  ├── Marathi, Telugu Tier 2
  ├── Kannada, Malayalam, Gujarati, Punjabi Tier 3
  └── Cultural review process
```

---

## Glossary

| Term | Definition |
|------|------------|
| **i18n** | Internationalization (18 letters between i and n) |
| **l10n** | Localization (10 letters between l and n) |
| **Hinglish** | Hindi-English code-switching in Latin script |
| **Locale** | Language + Region (e.g., `hi-IN`, `ta-IN`) |
| **BCP 47** | Standard for language tags (e.g., `hi`, `hi-Latn`) |
| **ISO 15924** | Standard for script codes (e.g., `Deva`, `Taml`) |
| **CLDR** | Unicode Common Locale Data Repository |
| **Lakh** | Indian number unit: 1 lakh = 100,000 (written `1,00,000`) |
| **Crore** | Indian number unit: 1 crore = 10,000,000 (written `1,00,00,000`) |
| **PIN Code** | Postal Index Number: 6-digit Indian postal code |
| **IST** | Indian Standard Time: UTC+5:30 (single timezone for all of India) |
| **TM** | Translation Memory: database of previously translated strings |
| **RTL** | Right-to-left text direction (Arabic, Urdu, Hebrew) |
| **ICU** | International Components for Unicode (message format standard) |
| **NFC** | Unicode Normalization Form C (composed characters) |
| **Conjunct** | Two or more consonants merged into a single glyph in Indic scripts |
| **Matra** | Vowel sign attached to a consonant in Indic scripts |
| **Shirorekha** | Top-line connecting Devanagari characters |
| **TCS** | Tax Collected at Source (Indian tax on overseas travel packages) |
| **GST** | Goods and Services Tax (Indian consumption tax) |

---

**Last Updated:** 2026-04-28

**Current Progress:** 5 of 5 documents complete (100%)
