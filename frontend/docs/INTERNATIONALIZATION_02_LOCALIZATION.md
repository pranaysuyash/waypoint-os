# Localization Management — Technical Deep Dive

> Comprehensive guide to localization implementation for the Travel Agency Agent platform

---

## Document Metadata

**Series:** Internationalization
**Document:** 2 of 4 (Localization)
**Last Updated:** 2026-04-26
**Status:** ✅ Complete

---

## Table of Contents

1. [Overview](#overview)
2. [Translation Management Workflow](#translation-management-workflow)
3. [RTL (Right-to-Left) Support](#rtl-right-to-left-support)
4. [Date and Time Formatting](#date-and-time-formatting)
5. [Number and Currency Formatting](#number-and-currency-formatting)
6. [Pluralization Rules](#pluralization-rules)
7. [Gender and Grammar](#gender-and-grammar)
8. [Image and Asset Localization](#image-and-asset-localization)
9. [Implementation](#implementation)
10. [Testing Scenarios](#testing-scenarios)
11. [API Specification](#api-specification)
12. [Metrics and Monitoring](#metrics-and-monitoring)

---

## Overview

Localization (l10n) is the process of adapting internationalized software for a specific region or language by translating text and adding locale-specific components.

### Localization Scope

- **UI Translation:** All interface strings
- **Content Translation:** Dynamic content (trips, destinations, itineraries)
- **Format Adaptation:** Dates, times, numbers, currencies
- **Layout Adaptation:** RTL languages, text expansion
- **Asset Adaptation:** Images, icons, documents
- **Cultural Adaptation:** Colors, symbols, conventions

### Quality Goals

- **Translation Coverage:** 100% of UI strings
- **Accuracy:** Professional quality translations
- **Consistency:** Terminology consistency across languages
- **Performance:** No performance impact from i18n
- **Maintainability:** Easy translation updates

---

## Translation Management Workflow

### Translation Lifecycle

```typescript
/**
 * Translation status lifecycle
 */
enum TranslationStatus {
  PENDING = 'pending',       // Awaiting translation
  IN_REVIEW = 'in_review',   // Under review
  APPROVED = 'approved',     // Approved for use
  REJECTED = 'rejected',     // Needs revision
  DEPRECATED = 'deprecated'  // No longer used
}

/**
 * Translation workflow manager
 */
class TranslationWorkflowManager {
  /**
   * Create new translation request
   */
  async createTranslationRequest(request: {
    sourceText: string;
    sourceLocale: SupportedLocale;
    targetLocale: SupportedLocale;
    namespace: string;
    key: string;
    context?: string;
    priority?: 'low' | 'normal' | 'high';
    dueDate?: Date;
  }): Promise<TranslationRequest> {
    const translationRequest = await db.insert(translationRequests).values({
      id: generateId(),
      ...request,
      status: TranslationStatus.PENDING,
      createdAt: new Date()
    }).returning().then(rows => rows[0]);

    // Notify translators
    await this.notifyTranslators(translationRequest);

    return translationRequest;
  }

  /**
   * Submit translation
   */
  async submitTranslation(
    requestId: string,
    translatorId: string,
    targetText: string,
    notes?: string
  ): Promise<void> {
    await db.update(translationRequests)
      .set({
        targetText,
        translatorId,
        translatorNotes: notes,
        status: TranslationStatus.IN_REVIEW,
        submittedAt: new Date()
      })
      .where(eq(translationRequests.id, requestId));

    // Notify reviewers
    await this.notifyReviewers(requestId);
  }

  /**
   * Approve translation
   */
  async approveTranslation(
    requestId: string,
    reviewerId: string,
    notes?: string
  ): Promise<void> {
    await db.transaction(async (tx) => {
      const request = await tx.query.translationRequests.findFirst({
        where: eq(translationRequests.id, requestId)
      });

      if (!request) throw new Error('Request not found');

      // Update request status
      await tx.update(translationRequests)
        .set({
          status: TranslationStatus.APPROVED,
          reviewerId,
          reviewerNotes: notes,
          reviewedAt: new Date()
        })
        .where(eq(translationRequests.id, requestId));

      // Publish translation
      await tx.insert(translations).values({
        id: generateId(),
        namespace: request.namespace,
        key: request.key,
        sourceText: request.sourceText,
        sourceLocale: request.sourceLocale,
        targetLocale: request.targetLocale,
        targetText: request.targetText,
        context: request.context,
        status: 'approved',
        createdAt: new Date()
      }).onConflictDoUpdate({
        target: [translations.namespace, translations.key, translations.targetLocale],
        set: {
          targetText: request.targetText,
          status: 'approved',
          updatedAt: new Date()
        }
      });

      // Invalidate translation cache
      await this.invalidateCache(request.targetLocale);
    });
  }

  /**
   * Reject translation
   */
  async rejectTranslation(
    requestId: string,
    reviewerId: string,
    reason: string
  ): Promise<void> {
    await db.update(translationRequests)
      .set({
        status: TranslationStatus.REJECTED,
        reviewerId,
        rejectionReason: reason,
        reviewedAt: new Date()
      })
      .where(eq(translationRequests.id, requestId));

    // Return to translator for revision
    await this.notifyTranslatorRevision(requestId);
  }

  /**
   * Get translation statistics for locale
   */
  async getTranslationStatistics(locale: SupportedLocale): Promise<LocaleStatistics> {
    const [total, approved, pending, inReview] = await Promise.all([
      db.query.translationRequests.findMany({
        where: eq(translationRequests.targetLocale, locale)
      }),
      db.query.translationRequests.findMany({
        where: and(
          eq(translationRequests.targetLocale, locale),
          eq(translationRequests.status, TranslationStatus.APPROVED)
        )
      }),
      db.query.translationRequests.findMany({
        where: and(
          eq(translationRequests.targetLocale, locale),
          eq(translationRequests.status, TranslationStatus.PENDING)
        )
      }),
      db.query.translationRequests.findMany({
        where: and(
          eq(translationRequests.targetLocale, locale),
          eq(translationRequests.status, TranslationStatus.IN_REVIEW)
        )
      })
    ]);

    // Calculate coverage by namespace
    const namespaces = ['common', 'trips', 'bookings', 'customers', 'suppliers', 'settings'];
    const coverage: Record<string, { total: number; approved: number; percent: number }> = {};

    for (const ns of namespaces) {
      const nsTotal = await db.query.translationRequests.findMany({
        where: and(
          eq(translationRequests.targetLocale, locale),
          eq(translationRequests.namespace, ns)
        )
      });

      const nsApproved = await db.query.translationRequests.findMany({
        where: and(
          eq(translationRequests.targetLocale, locale),
          eq(translationRequests.namespace, ns),
          eq(translationRequests.status, TranslationStatus.APPROVED)
        )
      });

      coverage[ns] = {
        total: nsTotal.length,
        approved: nsApproved.length,
        percent: nsTotal.length > 0 ? (nsApproved.length / nsTotal.length) * 100 : 0
      };
    }

    return {
      locale,
      totalRequests: total.length,
      approved: approved.length,
      pending: pending.length,
      inReview: inReview.length,
      coveragePercent: total.length > 0 ? (approved.length / total.length) * 100 : 0,
      coverageByNamespace: coverage
    };
  }

  private async notifyTranslators(request: TranslationRequest): Promise<void> {
    // Send notification to available translators
  }

  private async notifyReviewers(requestId: string): Promise<void> {
    // Send notification to reviewers
  }

  private async notifyTranslatorRevision(requestId: string): Promise<void> {
    // Send notification to translator for revision
  }

  private async invalidateCache(locale: SupportedLocale): Promise<void> {
    // Clear translation cache for locale
  }
}

interface TranslationRequest {
  id: string;
  sourceText: string;
  sourceLocale: SupportedLocale;
  targetLocale: SupportedLocale;
  namespace: string;
  key: string;
  context?: string;
  priority: 'low' | 'normal' | 'high';
  dueDate?: Date;
  status: TranslationStatus;
  targetText?: string;
  translatorId?: string;
  translatorNotes?: string;
  reviewerId?: string;
  reviewerNotes?: string;
  rejectionReason?: string;
  createdAt: Date;
  submittedAt?: Date;
  reviewedAt?: Date;
}

interface LocaleStatistics {
  locale: SupportedLocale;
  totalRequests: number;
  approved: number;
  pending: number;
  inReview: number;
  coveragePercent: number;
  coverageByNamespace: Record<string, { total: number; approved: number; percent: number }>;
}
```

### Translation Memory

```typescript
/**
 * Translation memory for reuse
 */
class TranslationMemory {
  /**
   * Find similar translations
   */
  async findSimilar(
    text: string,
    sourceLocale: SupportedLocale,
    targetLocale: SupportedLocale,
    threshold = 0.8
  ): Promise<Array<{ text: string; translation: string; similarity: number }>> {
    // Get all translations for the language pair
    const translations = await db.query.translations.findMany({
      where: and(
        eq(translations.sourceLocale, sourceLocale),
        eq(translations.targetLocale, targetLocale),
        eq(translations.status, 'approved')
      )
    });

    const results: Array<{ text: string; translation: string; similarity: number }> = [];

    for (const translation of translations) {
      const similarity = this.calculateSimilarity(text, translation.sourceText);

      if (similarity >= threshold) {
        results.push({
          text: translation.sourceText,
          translation: translation.targetText,
          similarity
        });
      }
    }

    // Sort by similarity descending
    results.sort((a, b) => b.similarity - a.similarity);

    return results.slice(0, 10); // Return top 10
  }

  /**
   * Calculate similarity between two texts
   */
  private calculateSimilarity(text1: string, text2: string): number {
    // Levenshtein distance
    const distance = this.levenshteinDistance(
      text1.toLowerCase(),
      text2.toLowerCase()
    );

    const maxLen = Math.max(text1.length, text2.length);
    return maxLen > 0 ? 1 - (distance / maxLen) : 0;
  }

  /**
   * Levenshtein distance calculation
   */
  private levenshteinDistance(str1: string, str2: string): number {
    const matrix: number[][] = [];

    for (let i = 0; i <= str2.length; i++) {
      matrix[i] = [i];
    }

    for (let j = 0; j <= str1.length; j++) {
      matrix[0][j] = j;
    }

    for (let i = 1; i <= str2.length; i++) {
      for (let j = 1; j <= str1.length; j++) {
        if (str2.charAt(i - 1) === str1.charAt(j - 1)) {
          matrix[i][j] = matrix[i - 1][j - 1];
        } else {
          matrix[i][j] = Math.min(
            matrix[i - 1][j - 1] + 1,
            matrix[i][j - 1] + 1,
            matrix[i - 1][j] + 1
          );
        }
      }
    }

    return matrix[str2.length][str1.length];
  }

  /**
   * Store translation in memory
   */
  async store(
    sourceText: string,
    targetText: string,
    sourceLocale: SupportedLocale,
    targetLocale: SupportedLocale,
    context?: string
  ): Promise<void> {
    await db.insert(translationMemory).values({
      id: generateId(),
      sourceText,
      targetText,
      sourceLocale,
      targetLocale,
      context,
      createdAt: new Date()
    }).onConflictDoNothing();
  }

  /**
   * Get translation from memory
   */
  async get(
    sourceText: string,
    sourceLocale: SupportedLocale,
    targetLocale: SupportedLocale
  ): Promise<string | null> {
    const result = await db.query.translationMemory.findFirst({
      where: and(
        eq(translationMemory.sourceText, sourceText),
        eq(translationMemory.sourceLocale, sourceLocale),
        eq(translationMemory.targetLocale, targetLocale)
      )
    });

    return result?.targetText || null;
  }
}
```

---

## RTL (Right-to-Left) Support

### RTL Detection and Layout

```typescript
/**
 * RTL utilities
 */
class RTLUtils {
  /**
   * Check if locale is RTL
   */
  isRTL(locale: SupportedLocale): boolean {
    return RTL_LOCALES.has(locale);
  }

  /**
   * Get text direction for locale
   */
  getDirection(locale: SupportedLocale): 'rtl' | 'ltr' {
    return this.isRTL(locale) ? 'rtl' : 'ltr';
  }

  /**
   * Get text alignment for locale
   */
  getAlignment(locale: SupportedLocale): 'left' | 'right' {
    return this.isRTL(locale) ? 'right' : 'left';
  }

  /**
   * Get opposite alignment
   */
  getOppositeAlignment(align: 'left' | 'right'): 'left' | 'right' {
    return align === 'left' ? 'right' : 'left';
  }

  /**
   * Flip margin/padding for RTL
   */
  flipSpacing(value: string): string {
    // Convert CSS spacing value for RTL
    const match = value.match(/^(\d+px)(\s+(\d+px))?(\s+(\d+px))?(\s+(\d+px))?$/);
    if (!match) return value;

    const top = match[1];
    const right = match[3] || top;
    const bottom = match[5] || top;
    const left = match[7] || right;

    return `${top} ${left} ${bottom} ${right}`;
  }

  /**
   * Flip position for RTL
   */
  flipPosition(value: string): string {
    const map: Record<string, string> = {
      'left': 'right',
      'right': 'left',
      'top-left': 'top-right',
      'top-right': 'top-left',
      'bottom-left': 'bottom-right',
      'bottom-right': 'bottom-left'
    };

    return map[value] || value;
  }
}

export const rtlUtils = new RTLUtils();
```

### RTL-Aware Components

```typescript
/**
 * RTL-aware layout component
 */
function RTLLayout({ children, locale }: { children: React.ReactNode; locale: SupportedLocale }) {
  const isRTL = rtlUtils.isRTL(locale);
  const direction = rtlUtils.getDirection(locale);

  return (
    <div dir={direction} className={isRTL ? 'rtl' : 'ltr'}>
      {children}
    </div>
  );
}

/**
 * RTL-aware button with icon
 */
function IconicButton({
  icon,
  children,
  variant = 'primary'
}: {
  icon: React.ReactNode;
  children: React.ReactNode;
  variant?: 'primary' | 'secondary';
}) {
  const { i18n } = useTranslation();
  const isRTL = rtlUtils.isRTL(i18n.language as SupportedLocale);

  return (
    <button className={`btn btn-${variant}`}>
      {isRTL ? (
        <>
          {children}
          <span className="icon-end">{icon}</span>
        </>
      ) : (
        <>
          <span className="icon-start">{icon}</span>
          {children}
        </>
      )}
    </button>
  );
}

/**
 * RTL-aware navigation
 */
function Navigation() {
  const { i18n } = useTranslation();
  const isRTL = rtlUtils.isRTL(i18n.language as SupportedLocale);

  return (
    <nav className={`flex ${isRTL ? 'flex-row-reverse' : 'flex-row'}`}>
      <NavLink to="/trips">{t('navigation.trips')}</NavLink>
      <NavLink to="/bookings">{t('navigation.bookings')}</NavLink>
      <NavLink to="/customers">{t('navigation.customers')}</NavLink>
    </nav>
  );
}
```

### RTL CSS Support

```css
/* RTL CSS support using logical properties */

/* Instead of margin-left, use margin-inline-start */
.nav-item {
  margin-inline-start: 1rem;
  padding-inline-start: 1rem;
  border-inline-start: 2px solid transparent;
}

/* Instead of text-align: left/right, use start/end */
.text-align-start {
  text-align: start;
}

.text-align-end {
  text-align: end;
}

/* Border radius with logical properties */
.card {
  border-start-start-radius: 8px;
  border-start-end-radius: 8px;
  border-end-start-radius: 8px;
  border-end-end-radius: 8px;
}

/* Absolute positioning with logical properties */
.sidebar {
  position: absolute;
  inset-inline-start: 0;
  inset-inline-end: auto;
}

/* RTL-specific overrides */
[dir='rtl'] .icon-arrow {
  transform: scaleX(-1);
}

[dir='rtl'] .flex-row {
  flex-direction: row-reverse;
}

/* For legacy browser support */
@supports not (margin-inline-start: 1px) {
  [dir='rtl'] .nav-item {
    margin-left: 0;
    margin-right: 1rem;
    border-left: none;
    border-right: 2px solid transparent;
  }

  [dir='ltr'] .nav-item {
    margin-left: 1rem;
    margin-right: 0;
    border-left: 2px solid transparent;
    border-right: none;
  }
}
```

---

## Date and Time Formatting

### Locale-Aware Date Formatting

```typescript
/**
 * Date formatter
 */
class DateFormatter {
  /**
   * Format date according to locale
   */
  formatDate(date: Date, locale: SupportedLocale, options?: {
    style?: 'full' | 'long' | 'medium' | 'short';
    timeZone?: string;
  }): string {
    const config = LOCALE_CONFIGS[locale];

    return new Intl.DateTimeFormat(locale, {
      dateStyle: options?.style || 'medium',
      timeZone: options?.timeZone
    }).format(date);
  }

  /**
   * Format time according to locale
   */
  formatTime(date: Date, locale: SupportedLocale, options?: {
    style?: 'full' | 'long' | 'medium' | 'short';
    timeZone?: string;
    hour12?: boolean;
  }): string {
    const config = LOCALE_CONFIGS[locale];

    return new Intl.DateTimeFormat(locale, {
      timeStyle: options?.style || 'short',
      hour12: options?.hour12 ?? (config.timeFormat === '12h'),
      timeZone: options?.timeZone
    }).format(date);
  }

  /**
   * Format date and time
   */
  formatDateTime(date: Date, locale: SupportedLocale, options?: {
    dateStyle?: 'full' | 'long' | 'medium' | 'short';
    timeStyle?: 'full' | 'long' | 'medium' | 'short';
    timeZone?: string;
  }): string {
    return new Intl.DateTimeFormat(locale, {
      dateStyle: options?.dateStyle || 'medium',
      timeStyle: options?.timeStyle || 'short',
      timeZone: options?.timeZone
    }).format(date);
  }

  /**
   * Format date range
   */
  formatDateRange(
    start: Date,
    end: Date,
    locale: SupportedLocale,
    options?: {
      dateStyle?: 'full' | 'long' | 'medium' | 'short';
      timeZone?: string;
    }
  ): string {
    const formatter = new Intl.DateTimeFormat(locale, {
      dateStyle: options?.dateStyle || 'medium',
      timeZone: options?.timeZone
    });

    // Format start and end dates
    const startFormatted = formatter.format(start);
    const endFormatted = formatter.format(end);

    // Use range format if available
    if (formatter.formatRange) {
      return formatter.formatRange(start, end);
    }

    // Fall back to manual range
    return `${startFormatted} - ${endFormatted}`;
  }

  /**
   * Format relative date (e.g., "3 days ago")
   */
  formatRelative(date: Date, locale: SupportedLocale, baseDate = new Date()): string {
    const rtf = new Intl.RelativeTimeFormat(locale, { numeric: 'auto' });

    const diffInSeconds = (date.getTime() - baseDate.getTime()) / 1000;
    const diffInDays = Math.round(diffInSeconds / (60 * 60 * 24));

    const absDays = Math.abs(diffInDays);

    if (absDays < 1) {
      const diffInHours = Math.round(diffInSeconds / (60 * 60));
      return rtf.format(diffInHours, 'hour');
    }

    if (absDays < 30) {
      return rtf.format(diffInDays, 'day');
    }

    if (absDays < 365) {
      const diffInMonths = Math.round(diffInDays / 30);
      return rtf.format(diffInMonths, 'month');
    }

    const diffInYears = Math.round(diffInDays / 365);
    return rtf.format(diffInYears, 'year');
  }

  /**
   * Parse date from locale string
   */
  parseDate dateString: string, locale: SupportedLocale): Date | null {
    try {
      const config = LOCALE_CONFIGS[locale];

      // Parse based on locale format
      const parts = dateString.split(/[/\-.]/);

      if (config.dateFormat === 'MM/DD/YYYY' || config.dateFormat === 'MM-DD-YYYY') {
        const [month, day, year] = parts.map(Number);
        return new Date(year, month - 1, day);
      }

      if (config.dateFormat === 'DD/MM/YYYY' || config.dateFormat === 'DD-MM-YYYY') {
        const [day, month, year] = parts.map(Number);
        return new Date(year, month - 1, day);
      }

      if (config.dateFormat === 'YYYY-MM-DD' || config.dateFormat === 'YYYY/MM/DD') {
        const [year, month, day] = parts.map(Number);
        return new Date(year, month - 1, day);
      }

      if (config.dateFormat === 'DD.MM.YYYY') {
        const [day, month, year] = parts.map(Number);
        return new Date(year, month - 1, day);
      }

      // Fall back to Date.parse
      const parsed = new Date(dateString);
      return isNaN(parsed.getTime()) ? null : parsed;

    } catch {
      return null;
    }
  }
}

export const dateFormatter = new DateFormatter();
```

---

## Number and Currency Formatting

### Number Formatting

```typescript
/**
 * Number formatter
 */
class NumberFormatter {
  /**
   * Format number according to locale
   */
  formatNumber(
    value: number,
    locale: SupportedLocale,
    options?: {
      minimumFractionDigits?: number;
      maximumFractionDigits?: number;
      style?: 'decimal' | 'currency' | 'percent' | 'unit';
    }
  ): string {
    return new Intl.NumberFormat(locale, options).format(value);
  }

  /**
   * Format percentage
   */
  formatPercent(value: number, locale: SupportedLocale, options?: {
    minimumFractionDigits?: number;
    maximumFractionDigits?: number;
  }): string {
    return new Intl.NumberFormat(locale, {
      style: 'percent',
      minimumFractionDigits: options?.minimumFractionDigits || 0,
      maximumFractionDigits: options?.maximumFractionDigits || 2
    }).format(value / 100);
  }

  /**
   * Format currency
   */
  formatCurrency(
    amount: number,
    locale: SupportedLocale,
    currency?: string,
    options?: {
      minimumFractionDigits?: number;
      maximumFractionDigits?: number;
      displaySymbol?: 'symbol' | 'narrowSymbol' | 'code' | 'name';
    }
  ): string {
    const config = LOCALE_CONFIGS[locale];
    const targetCurrency = currency || config.currency;

    return new Intl.NumberFormat(locale, {
      style: 'currency',
      currency: targetCurrency,
      currencyDisplay: options?.displaySymbol || 'symbol',
      minimumFractionDigits: options?.minimumFractionDigits,
      maximumFractionDigits: options?.maximumFractionDigits || 2
    }).format(amount);
  }

  /**
   * Parse number from locale string
   */
  parseNumber(numberString: string, locale: SupportedLocale): number | null {
    try {
      const config = LOCALE_CONFIGS[locale];

      // Remove thousand separators
      let normalized = numberString.replace(
        new RegExp(`\\${config.numberFormat.thousandSeparator}`, 'g'),
        ''
      );

      // Replace decimal separator with period
      normalized = normalized.replace(
        new RegExp(`\\${config.numberFormat.decimalSeparator}`, 'g'),
        '.'
      );

      return parseFloat(normalized);
    } catch {
      return null;
    }
  }

  /**
   * Format file size
   */
  formatFileSize(bytes: number, locale: SupportedLocale): string {
    const units = ['bytes', 'KB', 'MB', 'GB', 'TB'];
    let size = bytes;
    let unitIndex = 0;

    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }

    return new Intl.NumberFormat(locale, {
      style: 'unit',
      unit: units[unitIndex] as any,
      unitDisplay: 'short',
      maximumFractionDigits: 1
    }).format(size);
  }

  /**
   * Format phone number
   */
  formatPhoneNumber(phone: string, locale: SupportedLocale): string {
    // Remove non-numeric characters
    const cleaned = phone.replace(/\D/g, '');

    // Format based on locale
    const config = LOCALE_CONFIGS[locale];

    switch (config.region) {
      case 'US':
        if (cleaned.length === 10) {
          return `(${cleaned.slice(0, 3)}) ${cleaned.slice(3, 6)}-${cleaned.slice(6)}`;
        }
        break;

      case 'GB':
        if (cleaned.length === 11) {
          return `${cleaned.slice(0, 4)} ${cleaned.slice(4, 7)} ${cleaned.slice(7)}`;
        }
        break;

      case 'DE':
      case 'FR':
      case 'ES':
        // European format: +XX XX XX XX XX
        if (cleaned.length > 5) {
          const parts: string[] = [];
          for (let i = 0; i < cleaned.length; i += 2) {
            parts.push(cleaned.slice(i, i + 2));
          }
          return parts.join(' ');
        }
        break;

      case 'IN':
        // Indian format: +XX XXXXX XXXXX
        if (cleaned.length === 10) {
          return `${cleaned.slice(0, 5)} ${cleaned.slice(5)}`;
        }
        break;
    }

    // Return original if no format matches
    return phone;
  }
}

export const numberFormatter = new NumberFormatter();
```

---

## Pluralization Rules

### ICU Message Format Plurals

```typescript
/**
 * Pluralization support
 */
class PluralizationManager {
  /**
   * Get plural form for count
   */
  getPluralForm(count: number, locale: SupportedLocale): 'zero' | 'one' | 'two' | 'few' | 'many' | 'other' {
    const pluralRules = new Intl.PluralRules(locale);
    return pluralRules.select(count);
  }

  /**
   * Translate with pluralization
   */
  translatePlural(
    key: string,
    count: number,
    locale: SupportedLocale,
    params?: Record<string, unknown>
  ): string {
    const { t } = i18n;
    const pluralForm = this.getPluralForm(count, locale);

    // Try plural key first
    const pluralKey = `${key}_${pluralForm}`;
    const translation = t(pluralKey, { count, ...params });

    // Fall back to singular if plural not found
    if (translation === pluralKey) {
      return t(key, { count, ...params });
    }

    return translation;
  }
}

export const pluralizationManager = new PluralizationManager();

/**
 * Usage examples in translation files:
 */
/*
// en-US/common.json
{
  "items": {
    "zero": "No items",
    "one": "1 item",
    "other": "{{count}} items"
  },
  "customers": {
    "one": "{{count}} customer",
    "other": "{{count}} customers"
  }
}

// es-ES/common.json
{
  "items": {
    "zero": "Sin elementos",
    "one": "1 elemento",
    "other": "{{count}} elementos"
  },
  "customers": {
    "one": "{{count}} cliente",
    "other": "{{count}} clientes"
  }
}

// ar-SA/common.json (Arabic has complex pluralization)
{
  "items": {
    "zero": "لا عناصر",
    "one": "عنصر واحد",
    "two": "عنصران",
    "few": "{{count}} عناصر",
    "many": "{{count}} عنصر",
    "other": "{{count}} عنصر"
  }
}
*/
```

### Plural Component

```typescript
/**
 * Plural-aware text component
 */
function PluralText({
  count,
  i18nKey,
  params
}: {
  count: number;
  i18nKey: string;
  params?: Record<string, unknown>;
}) {
  const { i18n } = useTranslation();
  const locale = i18n.language as SupportedLocale;

  const text = pluralizationManager.translatePlural(i18nKey, count, locale, params);

  return <span>{text}</span>;
}

// Usage
<PluralText
  count={customers.length}
  i18nKey="customers"
  params={{ count: customers.length }}
/>
// Displays: "5 customers" (en-US), "5 clientes" (es-ES)
```

---

## Gender and Grammar

### Gender-Aware Translations

```typescript
/**
 * Gender-aware translation manager
 */
class GenderTranslationManager {
  /**
   * Translate with gender context
   */
  translateWithGender(
    key: string,
    gender: 'masculine' | 'feminine' | 'neutral',
    locale: SupportedLocale,
    params?: Record<string, unknown>
  ): string {
    const { t } = i18n;

    // Try gender-specific key first
    const genderKey = `${key}_${gender}`;
    const translation = t(genderKey, params);

    // Fall back to neutral if gender-specific not found
    if (translation === genderKey) {
      return t(`${key}_neutral`, params) || t(key, params);
    }

    return translation;
  }

  /**
   * Detect gender from user profile
   */
  async detectUserGender(userId: string): Promise<'masculine' | 'feminine' | 'neutral'> {
    const user = await db.query.users.findFirst({
      where: eq(users.id, userId)
    });

    // Would come from user profile or preferences
    return user?.gender || 'neutral';
  }
}

export const genderTranslationManager = new GenderTranslationManager();

/**
 * Usage in translation files:
 */
/*
// Spanish (gendered language)
{
  "welcome": "Bienvenido",
  "welcome_masculine": "Bienvenido",
  "welcome_feminine": "Bienvenida",
  "welcome_neutral": "Bienvenide",

  "confirm": "Confirmado",
  "confirm_masculine": "Confirmado",
  "confirm_feminine": "Confirmada",
  "confirm_neutral": "Confirmado"
}

// French (gendered language)
{
  "welcome": "Bienvenue",
  "welcome_masculine": "Bienvenue",
  "welcome_feminine": "Bienvenue",
  "welcome_neutral": "Bienvenue",

  "confirm": "Confirmé",
  "confirm_masculine": "Confirmé",
  "confirm_feminine": "Confirmée",
  "confirm_neutral": "Confirmé"
}

// English (mostly gender-neutral)
{
  "welcome": "Welcome",
  "welcome_masculine": "Welcome",
  "welcome_feminine": "Welcome",
  "welcome_neutral": "Welcome",

  "confirm": "Confirmed",
  "confirm_masculine": "Confirmed",
  "confirm_feminine": "Confirmed",
  "confirm_neutral": "Confirmed"
}
*/
```

---

## Image and Asset Localization

### Localized Asset Management

```typescript
/**
 * Localized asset manager
 */
class LocalizedAssetManager {
  /**
   * Get localized image URL
   */
  getImageURL(
    imagePath: string,
    locale: SupportedLocale,
    fallback = true
  ): string {
    // Check for locale-specific version
    const localizedPath = this.insertLocaleInPath(imagePath, locale);

    // Try to load localized version
    if (this.assetExists(localizedPath)) {
      return localizedPath;
    }

    // Try language-specific version (without region)
    const language = locale.split('-')[0];
    const languagePath = this.insertLocaleInPath(imagePath, language);

    if (this.assetExists(languagePath)) {
      return languagePath;
    }

    // Fall back to default
    if (fallback) {
      return imagePath;
    }

    return localizedPath;
  }

  /**
   * Get localized asset URL
   */
  getAssetURL(
    assetPath: string,
    locale: SupportedLocale,
    type: 'image' | 'document' | 'video' = 'image'
  ): string {
    const base = this.getAssetBase(type);
    const localizedPath = this.getImageURL(assetPath, locale);

    return `${base}${localizedPath}`;
  }

  /**
   * Insert locale into file path
   */
  private insertLocaleInPath(path: string, locale: string): string {
    const parts = path.split('/');
    const filename = parts.pop()!;
    const [name, ...ext] = filename.split('.');

    parts.push(`${name}_${locale}.${ext.join('.')}`);

    return parts.join('/');
  }

  /**
   * Check if asset exists
   */
  private assetExists(path: string): boolean {
    // In a real implementation, this would check the filesystem or CDN
    // For now, assume existence
    return true;
  }

  /**
   * Get asset base URL
   */
  private getAssetBase(type: 'image' | 'document' | 'video'): string {
    const bases = {
      image: '/assets/images',
      document: '/assets/documents',
      video: '/assets/videos'
    };

    return bases[type];
  }
}

export const localizedAssetManager = new LocalizedAssetManager();

/**
 * Localized image component
 */
function LocalizedImage({
  src,
  alt,
  locale,
  ...props
}: {
  src: string;
  alt: string;
  locale?: SupportedLocale;
  [key: string]: unknown;
}) {
  const { i18n } = useTranslation();
  const currentLocale = locale || (i18n.language as SupportedLocale);

  const localizedSrc = localizedAssetManager.getImageURL(src, currentLocale);
  const localizedAlt = i18n.t(alt);

  return <img src={localizedSrc} alt={localizedAlt} {...props} />;
}

// Usage
<LocalizedImage
  src="/hero-banner.jpg"
  alt="home.hero.title"
  locale="es-ES"
/>
// Loads: /assets/images/hero-banner_es-ES.jpg
```

### Document Localization

```typescript
/**
 * Localized document manager
 */
class LocalizedDocumentManager {
  /**
   * Get localized document URL
   */
  getDocumentURL(
    documentId: string,
    locale: SupportedLocale,
    type: 'terms' | 'privacy' | 'invoice' | 'itinerary'
  ): string {
    // Try to get localized version from database
    const document = db.query.localizedDocuments.findFirst({
      where: and(
        eq(localizedDocuments.documentId, documentId),
        eq(localizedDocuments.locale, locale),
        eq(localizedDocuments.type, type)
      )
    });

    if (document) {
      return document.url;
    }

    // Fall back to default locale
    const defaultDoc = db.query.localizedDocuments.findFirst({
      where: and(
        eq(localizedDocuments.documentId, documentId),
        eq(localizedDocuments.locale, DEFAULT_LOCALE),
        eq(localizedDocuments.type, type)
      )
    });

    return defaultDoc?.url || '';
  }

  /**
   * Generate localized PDF
   */
  async generateLocalizedPDF(
    templateId: string,
    data: Record<string, unknown>,
    locale: SupportedLocale
  ): Promise<string> {
    // Load template with locale-specific formatting
    const template = await this.loadTemplate(templateId, locale);

    // Render with data
    const html = this.renderTemplate(template, data, locale);

    // Generate PDF
    const pdf = await this.htmlToPDF(html, locale);

    // Store and return URL
    const url = await this.storePDF(pdf, templateId, locale);

    return url;
  }

  /**
   * Load localized template
   */
  private async loadTemplate(
    templateId: string,
    locale: SupportedLocale
  ): Promise<string> {
    // Try locale-specific template
    let template = await db.query.documentTemplates.findFirst({
      where: and(
        eq(documentTemplates.id, templateId),
        eq(documentTemplates.locale, locale)
      )
    });

    // Fall back to default locale template
    if (!template) {
      template = await db.query.documentTemplates.findFirst({
        where: and(
          eq(documentTemplates.id, templateId),
          eq(documentTemplates.locale, DEFAULT_LOCALE)
        )
      });
    }

    return template?.content || '';
  }

  /**
   * Render template with data and locale
   */
  private renderTemplate(
    template: string,
    data: Record<string, unknown>,
    locale: SupportedLocale
  ): string {
    // Process template with locale-specific formatting
    const config = LOCALE_CONFIGS[locale];

    // Replace placeholders
    let html = template;

    // Date placeholders
    html = html.replace(/\{\{date:(\w+)\}\}/g, (_, key) => {
      const date = data[key] as Date;
      return dateFormatter.formatDate(date, locale);
    });

    // Currency placeholders
    html = html.replace(/\{\{currency:(\w+)\}\}/g, (_, key) => {
      const amount = data[key] as number;
      return numberFormatter.formatCurrency(amount, locale);
    });

    // Number placeholders
    html = html.replace(/\{\{number:(\w+)\}\}/g, (_, key) => {
      const value = data[key] as number;
      return numberFormatter.formatNumber(value, locale);
    });

    // Regular placeholders
    html = html.replace(/\{\{(\w+)\}\}/g, (_, key) => {
      return String(data[key] || '');
    });

    return html;
  }

  private async htmlToPDF(html: string, locale: SupportedLocale): Promise<Buffer> {
    // PDF generation implementation
    return Buffer.from('');
  }

  private async storePDF(pdf: Buffer, templateId: string, locale: SupportedLocale): Promise<string> {
    // Store PDF and return URL
    return '';
  }
}

export const localizedDocumentManager = new LocalizedDocumentManager();
```

---

## Implementation

```typescript
/**
 * Complete localization service
 */
class LocalizationService {
  private workflow: TranslationWorkflowManager;
  private translationMemory: TranslationMemory;
  private pluralization: PluralizationManager;
  private genderTranslation: GenderTranslationManager;
  private assetManager: LocalizedAssetManager;
  private documentManager: LocalizedDocumentManager;

  constructor() {
    this.workflow = new TranslationWorkflowManager();
    this.translationMemory = new TranslationMemory();
    this.pluralization = new PluralizationManager();
    this.genderTranslation = new GenderTranslationManager();
    this.assetManager = new LocalizedAssetManager();
    this.documentManager = new LocalizedDocumentManager();
  }

  /**
   * Get localized text
   */
  getText(key: string, locale: SupportedLocale, params?: Record<string, unknown>): string {
    const { t } = i18n;
    return t(key, params);
  }

  /**
   * Get localized text with pluralization
   */
  getPluralText(
    key: string,
    count: number,
    locale: SupportedLocale,
    params?: Record<string, unknown>
  ): string {
    return this.pluralization.translatePlural(key, count, locale, params);
  }

  /**
   * Get localized text with gender
   */
  getGenderedText(
    key: string,
    gender: 'masculine' | 'feminine' | 'neutral',
    locale: SupportedLocale,
    params?: Record<string, unknown>
  ): string {
    return this.genderTranslation.translateWithGender(key, gender, locale, params);
  }

  /**
   * Format data for locale
   */
  format(
    value: Date | number | string,
    type: 'date' | 'time' | 'datetime' | 'currency' | 'percent' | 'phone',
    locale: SupportedLocale,
    options?: Record<string, unknown>
  ): string {
    switch (type) {
      case 'date':
        return dateFormatter.formatDate(value as Date, locale, options as any);
      case 'time':
        return dateFormatter.formatTime(value as Date, locale, options as any);
      case 'datetime':
        return dateFormatter.formatDateTime(value as Date, locale, options as any);
      case 'currency':
        return numberFormatter.formatCurrency(value as number, locale, options as any);
      case 'percent':
        return numberFormatter.formatPercent(value as number, locale, options as any);
      case 'phone':
        return numberFormatter.formatPhoneNumber(value as string, locale);
      default:
        return String(value);
    }
  }

  /**
   * Get localized asset
   */
  getAsset(path: string, locale: SupportedLocale): string {
    return this.assetManager.getImageURL(path, locale);
  }

  /**
   * Get localized document
   */
  async getDocument(
    documentId: string,
    locale: SupportedLocale,
    type: 'terms' | 'privacy' | 'invoice' | 'itinerary'
  ): Promise<string> {
    return this.documentManager.getDocumentURL(documentId, locale, type);
  }
}

export const localizationService = new LocalizationService();
```

---

## Testing Scenarios

```typescript
describe('Localization', () => {
  describe('Pluralization', () => {
    it('should handle English plurals', () => {
      const manager = new PluralizationManager();
      expect(manager.getPluralForm(0, 'en-US')).toBe('other');
      expect(manager.getPluralForm(1, 'en-US')).toBe('one');
      expect(manager.getPluralForm(2, 'en-US')).toBe('other');
    });

    it('should handle Arabic plurals', () => {
      const manager = new PluralizationManager();
      expect(manager.getPluralForm(0, 'ar-SA')).toBe('zero');
      expect(manager.getPluralForm(1, 'ar-SA')).toBe('one');
      expect(manager.getPluralForm(2, 'ar-SA')).toBe('two');
      expect(manager.getPluralForm(5, 'ar-SA')).toBe('few');
      expect(manager.getPluralForm(11, 'ar-SA')).toBe('many');
    });
  });

  describe('RTL Support', () => {
    it('should detect RTL locales', () => {
      expect(rtlUtils.isRTL('ar-SA')).toBe(true);
      expect(rtlUtils.isRTL('en-US')).toBe(false);
    });

    it('should flip spacing for RTL', () => {
      expect(rtlUtils.flipSpacing('10px 20px 30px 40px')).toBe('10px 40px 30px 20px');
    });
  });

  describe('Number Formatting', () => {
    it('should format currency for locale', () => {
      const formatter = new NumberFormatter();
      expect(formatter.formatCurrency(1234.56, 'en-US')).toContain('$');
      expect(formatter.formatCurrency(1234.56, 'es-ES')).toContain('€');
    });
  });
});
```

---

## API Specification

```yaml
paths:
  /api/i18n/translations/pending:
    get:
      summary: Get pending translations
      parameters:
        - name: locale
          in: query
          schema:
            type: string
      responses:
        '200':
          description: Pending translations

  /api/i18n/translations/{id}/approve:
    post:
      summary: Approve translation
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                notes:
                  type: string
      responses:
        '200':
          description: Translation approved

  /api/i18n/translations/{id}/reject:
    post:
      summary: Reject translation
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [reason]
              properties:
                reason:
                  type: string
      responses:
        '200':
          description: Translation rejected

  /api/i18n/translate:
    post:
      summary: Translate text using translation memory
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [text, targetLocale]
              properties:
                text:
                  type: string
                sourceLocale:
                  type: string
                targetLocale:
                  type: string
      responses:
        '200':
          description: Translation result

  /api/i18n/assets/{path}:
    get:
      summary: Get localized asset
      parameters:
        - name: path
          in: path
          required: true
          schema:
            type: string
        - name: locale
          in: query
          schema:
            type: string
      responses:
        '200':
          description: Localized asset
```

---

## Metrics and Monitoring

```typescript
interface LocalizationMetrics {
  translationCoverage: Record<string, number>;
  pendingTranslations: number;
  translationQualityScore: number;
  cacheHitRate: number;
  averageTranslationTime: number;
  rtlUsage: number;
  localeDistribution: Record<string, number>;
}
```

---

**End of Document**

**Next:** [Currency and Payments Deep Dive](INTERNATIONALIZATION_03_CURRENCY.md)
