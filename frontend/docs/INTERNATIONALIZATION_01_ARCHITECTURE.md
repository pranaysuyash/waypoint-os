# Internationalization Architecture — Technical Deep Dive

> Comprehensive guide to i18n architecture for the Travel Agency Agent platform

---

## Document Metadata

**Series:** Internationalization
**Document:** 1 of 4 (Architecture)
**Last Updated:** 2026-04-26
**Status:** ✅ Complete

---

## Table of Contents

1. [Overview](#overview)
2. [Framework Selection](#framework-selection)
3. [Locale Detection and Routing](#locale-detection-and-routing)
4. [Translation Architecture](#translation-architecture)
5. [Component-Level i18n](#component-level-i18n)
6. [API Localization](#api-localization)
7. [Content Management](#content-management)
8. [Implementation](#implementation)
9. [Testing Scenarios](#testing-scenarios)
10. [API Specification](#api-specification)
11. [Metrics and Monitoring](#metrics-and-monitoring)

---

## Overview

Internationalization (i18n) enables the Travel Agency Agent platform to serve customers across different regions and languages. This is critical for travel agencies serving international clients.

### Business Requirements

- **Multi-language Support:** English, Spanish, French, German, Portuguese, Arabic, Hindi
- **Regional Formatting:** Dates, times, numbers, currencies per locale
- **RTL Support:** Right-to-left languages (Arabic, Hebrew)
- **SEO:** Localized URLs for each language
- **Performance:** Fast loading regardless of locale

### Technical Objectives

- **Scalability:** Easy to add new languages
- **Maintainability:** Simple translation workflow
- **Type Safety:** Catch missing translations at build time
- **Fallback:** Graceful degradation for missing translations
- **Developer Experience:** Simple API for developers

---

## Framework Selection

### i18next with React Integration

```typescript
/**
 * i18next configuration
 */
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import Backend from 'i18next-http-backend';
import ICU from 'i18next-icu';

// Supported locales
export const SUPPORTED_LOCALES = [
  'en-US',    // English (United States)
  'en-GB',    // English (United Kingdom)
  'es-ES',    // Spanish (Spain)
  'es-MX',    // Spanish (Mexico)
  'fr-FR',    // French (France)
  'fr-CA',    // French (Canada)
  'de-DE',    // German (Germany)
  'pt-BR',    // Portuguese (Brazil)
  'ar-SA',    // Arabic (Saudi Arabia)
  'hi-IN'     // Hindi (India)
] as const;

export type SupportedLocale = typeof SUPPORTED_LOCALES[number];

// Default locale
export const DEFAULT_LOCALE: SupportedLocale = 'en-US';

// RTL locales
export const RTL_LOCALES: Set<SupportedLocale> = new Set([
  'ar-SA'
  // Add more RTL locales as needed
]);

/**
 * Initialize i18next
 */
i18n
  // Load translations from public/locales
  .use(Backend)
  // Detect user language
  .use(LanguageDetector)
  // Pass i18n instance to react-i18next
  .use(initReactI18next)
  // ICU message format
  .use(ICU)
  // Init i18next
  .init({
    // Default language
    lng: DEFAULT_LOCALE,
    fallbackLng: DEFAULT_LOCALE,
    supportedLngs: SUPPORTED_LOCALES,

    // Whitelist languages
    whitelist: SUPPORTED_LOCALES,

    // Load only needed languages
    load: 'languageOnly',

    // Namespace configuration
    ns: ['common', 'trips', 'bookings', 'customers', 'suppliers', 'settings', 'errors'],
    defaultNS: 'common',

    // Backend configuration
    backend: {
      loadPath: '/locales/{{lng}}/{{ns}}.json',
      addPath: '/locales/{{lng}}/{{ns}}.json' // For missing keys
    },

    // Detection options
    detection: {
      order: ['path', 'localStorage', 'htmlTag', 'cookie'],
      caches: ['localStorage', 'cookie'],
      lookupFromPathIndex: 0,
      checkWhitelist: true
    },

    // Interpolation
    interpolation: {
      escapeValue: false, // React already escapes
      formatSeparator: ',',
      format: (value, format) => {
        if (format === 'uppercase') return value.toUpperCase();
        if (format === 'lowercase') return value.toLowerCase();
        if (format === 'currency') return formatCurrency(value);
        return value;
      }
    },

    // React options
    react: {
      useSuspense: true,
      bindI18n: 'languageChanged',
      bindI18nStore: 'added removed'
    },

    // Save missing keys
    saveMissing: true,
    saveMissingTo: 'current',
    missingKeyHandler: (lng, ns, key) => {
      // Report missing translation keys
      reportMissingKey(lng, ns, key);
    },

    debug: process.env.NODE_ENV === 'development'
  });

export default i18n;
```

### Locale Configuration

```typescript
/**
 * Locale metadata and configuration
 */
interface LocaleConfig {
  code: SupportedLocale;
  name: string;
  nativeName: string;
  region: string;
  language: string;
  flag: string;           // Emoji flag
  rtl: boolean;
  dateFormat: string;
  timeFormat: '12h' | '24h';
  firstDayOfWeek: 0 | 1 | 6; // 0 = Sunday, 1 = Monday, 6 = Saturday
  currency: string;
  numberFormat: {
    decimalSeparator: string;
    thousandSeparator: string;
  };
}

/**
 * Locale configurations
 */
export const LOCALE_CONFIGS: Record<SupportedLocale, LocaleConfig> = {
  'en-US': {
    code: 'en-US',
    name: 'English (United States)',
    nativeName: 'English (United States)',
    region: 'US',
    language: 'en',
    flag: '🇺🇸',
    rtl: false,
    dateFormat: 'MM/DD/YYYY',
    timeFormat: '12h',
    firstDayOfWeek: 0,
    currency: 'USD',
    numberFormat: {
      decimalSeparator: '.',
      thousandSeparator: ','
    }
  },
  'en-GB': {
    code: 'en-GB',
    name: 'English (United Kingdom)',
    nativeName: 'English (United Kingdom)',
    region: 'GB',
    language: 'en',
    flag: '🇬🇧',
    rtl: false,
    dateFormat: 'DD/MM/YYYY',
    timeFormat: '24h',
    firstDayOfWeek: 1,
    currency: 'GBP',
    numberFormat: {
      decimalSeparator: '.',
      thousandSeparator: ','
    }
  },
  'es-ES': {
    code: 'es-ES',
    name: 'Spanish (Spain)',
    nativeName: 'Español (España)',
    region: 'ES',
    language: 'es',
    flag: '🇪🇸',
    rtl: false,
    dateFormat: 'DD/MM/YYYY',
    timeFormat: '24h',
    firstDayOfWeek: 1,
    currency: 'EUR',
    numberFormat: {
      decimalSeparator: ',',
      thousandSeparator: '.'
    }
  },
  'es-MX': {
    code: 'es-MX',
    name: 'Spanish (Mexico)',
    nativeName: 'Español (México)',
    region: 'MX',
    language: 'es',
    flag: '🇲🇽',
    rtl: false,
    dateFormat: 'DD/MM/YYYY',
    timeFormat: '12h',
    firstDayOfWeek: 0,
    currency: 'MXN',
    numberFormat: {
      decimalSeparator: '.',
      thousandSeparator: ','
    }
  },
  'fr-FR': {
    code: 'fr-FR',
    name: 'French (France)',
    nativeName: 'Français (France)',
    region: 'FR',
    language: 'fr',
    flag: '🇫🇷',
    rtl: false,
    dateFormat: 'DD/MM/YYYY',
    timeFormat: '24h',
    firstDayOfWeek: 1,
    currency: 'EUR',
    numberFormat: {
      decimalSeparator: ',',
      thousandSeparator: ' '
    }
  },
  'fr-CA': {
    code: 'fr-CA',
    name: 'French (Canada)',
    nativeName: 'Français (Canada)',
    region: 'CA',
    language: 'fr',
    flag: '🇨🇦',
    rtl: false,
    dateFormat: 'YYYY-MM-DD',
    timeFormat: '12h',
    firstDayOfWeek: 0,
    currency: 'CAD',
    numberFormat: {
      decimalSeparator: ',',
      thousandSeparator: ' '
    }
  },
  'de-DE': {
    code: 'de-DE',
    name: 'German (Germany)',
    nativeName: 'Deutsch (Deutschland)',
    region: 'DE',
    language: 'de',
    flag: '🇩🇪',
    rtl: false,
    dateFormat: 'DD.MM.YYYY',
    timeFormat: '24h',
    firstDayOfWeek: 1,
    currency: 'EUR',
    numberFormat: {
      decimalSeparator: ',',
      thousandSeparator: '.'
    }
  },
  'pt-BR': {
    code: 'pt-BR',
    name: 'Portuguese (Brazil)',
    nativeName: 'Português (Brasil)',
    region: 'BR',
    language: 'pt',
    flag: '🇧🇷',
    rtl: false,
    dateFormat: 'DD/MM/YYYY',
    timeFormat: '24h',
    firstDayOfWeek: 0,
    currency: 'BRL',
    numberFormat: {
      decimalSeparator: ',',
      thousandSeparator: '.'
    }
  },
  'ar-SA': {
    code: 'ar-SA',
    name: 'Arabic (Saudi Arabia)',
    nativeName: 'العربية (المملكة العربية السعودية)',
    region: 'SA',
    language: 'ar',
    flag: '🇸🇦',
    rtl: true,
    dateFormat: 'DD/MM/YYYY',
    timeFormat: '12h',
    firstDayOfWeek: 0,
    currency: 'SAR',
    numberFormat: {
      decimalSeparator: '٫', // Arabic decimal separator
      thousandSeparator: '٬' // Arabic thousand separator
    }
  },
  'hi-IN': {
    code: 'hi-IN',
    name: 'Hindi (India)',
    nativeName: 'हिन्दी (भारत)',
    region: 'IN',
    language: 'hi',
    flag: '🇮🇳',
    rtl: false,
    dateFormat: 'DD/MM/YYYY',
    timeFormat: '12h',
    firstDayOfWeek: 0,
    currency: 'INR',
    numberFormat: {
      decimalSeparator: '.',
      thousandSeparator: ','
    }
  }
};
```

---

## Locale Detection and Routing

### Locale-Based Routing

```typescript
/**
 * Locale-aware routing configuration
 */
import { createBrowserRouter } from 'react-router-dom';

/**
 * Create locale-aware router
 */
function createLocaleRouter() {
  const routes = generateLocaleRoutes();

  return createBrowserRouter([
    {
      path: '/',
      element: <LocaleLayout />,
      children: [
        // Redirect root to default locale
        {
          index: true,
          loader: () => redirect(`/${DEFAULT_LOCALE}`)
        },
        // Locale-prefixed routes
        ...routes
      ]
    }
  ]);
}

/**
 * Generate routes for each locale
 */
function generateLocaleRoutes() {
  return SUPPORTED_LOCALES.flatMap(locale => [
    {
      path: `${locale}/*`,
      element: <LocaleBoundary locale={locale} />,
      children: [
        { index: true, element: <HomePage /> },
        { path: 'trips', element: <TripsPage /> },
        { path: 'trips/:id', element: <TripDetailPage /> },
        { path: 'bookings', element: <BookingsPage /> },
        { path: 'customers', element: <CustomersPage /> },
        { path: 'settings', element: <SettingsPage /> }
      ]
    }
  ]);
}

/**
 * Locale boundary component
 */
function LocaleBoundary({ locale, children }: { locale: string; children: React.ReactNode }) {
  const { i18n } = useTranslation();

  useEffect(() => {
    // Change i18n language when route changes
    if (i18n.language !== locale) {
      i18n.changeLanguage(locale);
    }
  }, [locale, i18n]);

  // Update document direction for RTL
  const config = LOCALE_CONFIGS[locale as SupportedLocale];
  useEffect(() => {
    document.documentElement.dir = config.rtl ? 'rtl' : 'ltr';
    document.documentElement.lang = locale;
  }, [locale, config]);

  return <>{children}</>;
}
```

### Locale Detection Hook

```typescript
/**
 * Locale detection and management
 */
class LocaleDetector {
  /**
   * Detect user's preferred locale
   */
  detectLocale(request?: Request): SupportedLocale {
    // Priority order:
    // 1. URL path
    // 2. User preference (from auth)
    // 3. Cookie/localStorage
    // 4. Accept-Language header
    // 5. Browser language
    // 6. Default locale

    // Check URL path
    if (request) {
      const urlLocale = this.extractLocaleFromURL(request.url);
      if (urlLocale && this.isSupportedLocale(urlLocale)) {
        return urlLocale;
      }
    }

    // Check user preference (would come from auth context)
    const userPreference = this.getUserLocalePreference();
    if (userPreference) {
      return userPreference;
    }

    // Check cookie
    const cookieLocale = this.getLocaleFromCookie();
    if (cookieLocale) {
      return cookieLocale;
    }

    // Check Accept-Language header
    const headerLocale = this.getLocaleFromAcceptLanguage(request);
    if (headerLocale) {
      return headerLocale;
    }

    // Fall back to default
    return DEFAULT_LOCALE;
  }

  /**
   * Extract locale from URL path
   */
  private extractLocaleFromURL(url: string): SupportedLocale | null {
    const match = url.match(/^\/([a-z]{2}-[A-Z]{2})(\/|$)/);
    if (match && this.isSupportedLocale(match[1])) {
      return match[1] as SupportedLocale;
    }
    return null;
  }

  /**
   * Get locale from Accept-Language header
   */
  private getLocaleFromAcceptLanguage(request?: Request): SupportedLocale | null {
    if (!request) return null;

    const acceptLanguage = request.headers.get('accept-language');
    if (!acceptLanguage) return null;

    // Parse Accept-Language header
    const languages = acceptLanguage
      .split(',')
      .map(lang => {
        const [code, q] = lang.trim().split(';q=');
        return { code: code.split('-')[0], quality: parseFloat(q) || 1 };
      })
      .sort((a, b) => b.quality - a.quality);

    // Find best matching supported locale
    for (const lang of languages) {
      const match = SUPPORTED_LOCALES.find(l =>
        l.toLowerCase().startsWith(lang.code.toLowerCase())
      );
      if (match) return match;
    }

    return null;
  }

  /**
   * Check if locale is supported
   */
  private isSupportedLocale(locale: string): locale is SupportedLocale {
    return SUPPORTED_LOCALES.includes(locale as SupportedLocale);
  }

  /**
   * Get user's saved locale preference
   */
  private getUserLocalePreference(): SupportedLocale | null {
    // Would fetch from user profile
    return null;
  }

  /**
   * Get locale from cookie
   */
  private getLocaleFromCookie(): SupportedLocale | null {
    if (typeof document === 'undefined') return null;

    const match = document.cookie.match(/locale=([^;]+)/);
    if (match && this.isSupportedLocale(match[1])) {
      return match[1] as SupportedLocale;
    }
    return null;
  }

  /**
   * Save locale preference
   */
  saveLocalePreference(locale: SupportedLocale): void {
    // Save to cookie (expires in 1 year)
    document.cookie = `locale=${locale}; path=/; max-age=${365 * 24 * 60 * 60}; SameSite=Lax`;

    // Also save to localStorage
    localStorage.setItem('locale', locale);
  }
}

export const localeDetector = new LocaleDetector();
```

### Locale Switcher Component

```typescript
/**
 * Locale switcher UI component
 */
function LocaleSwitcher() {
  const { i18n } = useTranslation();
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);

  const currentLocale = i18n.language as SupportedLocale;
  const currentConfig = LOCALE_CONFIGS[currentLocale];

  /**
   * Change locale and navigate to localized route
   */
  const changeLocale = (newLocale: SupportedLocale) => {
    // Save preference
    localeDetector.saveLocalePreference(newLocale);

    // Get current path without locale prefix
    const currentPath = window.location.pathname;
    const pathWithoutLocale = currentPath.replace(/^\/[a-z]{2}-[A-Z]{2}/, '') || '/';

    // Navigate to new locale path
    navigate(`/${newLocale}${pathWithoutLocale}`);

    setIsOpen(false);
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-2 rounded hover:bg-gray-100"
        aria-label="Change language"
      >
        <span className="text-xl">{currentConfig.flag}</span>
        <span className="hidden sm:inline">{currentLocale}</span>
      </button>

      {isOpen && (
        <div className="absolute top-full right-0 mt-1 bg-white border rounded-lg shadow-lg py-1 z-50">
          {SUPPORTED_LOCALES.map(locale => {
            const config = LOCALE_CONFIGS[locale];
            return (
              <button
                key={locale}
                onClick={() => changeLocale(locale)}
                className={`w-full flex items-center gap-3 px-4 py-2 text-left hover:bg-gray-50 ${
                  locale === currentLocale ? 'bg-gray-100' : ''
                }`}
              >
                <span className="text-xl">{config.flag}</span>
                <div>
                  <div className="font-medium">{config.nativeName}</div>
                  <div className="text-sm text-gray-500">{config.name}</div>
                </div>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
```

---

## Translation Architecture

### Translation File Structure

```
public/
└── locales/
    ├── en-US/
    │   ├── common.json
    │   ├── trips.json
    │   ├── bookings.json
    │   ├── customers.json
    │   ├── suppliers.json
    │   ├── settings.json
    │   └── errors.json
    ├── es-ES/
    │   ├── common.json
    │   ├── trips.json
    │   └── ...
    ├── fr-FR/
    │   └── ...
    └── ...
```

### Translation Key Naming Convention

```typescript
/**
 * Translation key structure
 *
 * Format: {namespace}.{category}.{item}.{variant?}
 *
 * Examples:
 * - common.buttons.save
 * - common.buttons.save.primary
 * - trips.list.title
 * - trips.detail.sections.itinerary
 * - errors.validation.required
 * - errors.http.404
 */

/**
 * Type-safe translation keys
 */
export type TranslationKey =
  | `common.${CommonKey}`
  | `trips.${TripsKey}`
  | `bookings.${BookingsKey}`
  | `customers.${CustomersKey}`
  | `suppliers.${SuppliersKey}`
  | `settings.${SettingsKey}`
  | `errors.${ErrorsKey}`;

/**
 * Common translations
 */
type CommonKey =
  | `buttons.${string}`
  | `labels.${string}`
  | `actions.${string}`
  | `messages.${string}`
  | `navigation.${string}`;

/**
 * Trip translations
 */
type TripsKey =
  | `list.${string}`
  | `detail.${string}`
  | `form.${string}`
  | `status.${string}`;

/**
 * Use translations with type safety
 */
function useTypedTranslation() {
  const { t } = useTranslation();

  return {
    t: (key: TranslationKey, params?: Record<string, unknown>) =>
      t(key, params)
  };
}
```

### Translation File Example

```json
// public/locales/en-US/common.json
{
  "buttons": {
    "save": "Save",
    "cancel": "Cancel",
    "delete": "Delete",
    "edit": "Edit",
    "create": "Create",
    "search": "Search",
    "filter": "Filter",
    "export": "Export",
    "import": "Import",
    "confirm": "Confirm",
    "back": "Back",
    "next": "Next",
    "previous": "Previous",
    "submit": "Submit",
    "close": "Close"
  },
  "labels": {
    "name": "Name",
    "email": "Email",
    "phone": "Phone",
    "address": "Address",
    "date": "Date",
    "time": "Time",
    "price": "Price",
    "status": "Status",
    "description": "Description",
    "notes": "Notes"
  },
  "actions": {
    "createTrip": "Create Trip",
    "addCustomer": "Add Customer",
    "sendQuote": "Send Quote",
    "generateItinerary": "Generate Itinerary",
    "cancelBooking": "Cancel Booking",
    "refundPayment": "Refund Payment"
  },
  "messages": {
    "noResults": "No results found",
    "loading": "Loading...",
    "success": "Success",
    "error": "An error occurred",
    "confirmDelete": "Are you sure you want to delete this item?",
    "unsavedChanges": "You have unsaved changes. Are you sure you want to leave?"
  },
  "navigation": {
    "home": "Home",
    "trips": "Trips",
    "bookings": "Bookings",
    "customers": "Customers",
    "suppliers": "Suppliers",
    "reports": "Reports",
    "settings": "Settings"
  }
}

// public/locales/es-ES/common.json
{
  "buttons": {
    "save": "Guardar",
    "cancel": "Cancelar",
    "delete": "Eliminar",
    "edit": "Editar",
    "create": "Crear",
    "search": "Buscar",
    "filter": "Filtrar",
    "export": "Exportar",
    "import": "Importar",
    "confirm": "Confirmar",
    "back": "Atrás",
    "next": "Siguiente",
    "previous": "Anterior",
    "submit": "Enviar",
    "close": "Cerrar"
  },
  "labels": {
    "name": "Nombre",
    "email": "Correo electrónico",
    "phone": "Teléfono",
    "address": "Dirección",
    "date": "Fecha",
    "time": "Hora",
    "price": "Precio",
    "status": "Estado",
    "description": "Descripción",
    "notes": "Notas"
  },
  "actions": {
    "createTrip": "Crear Viaje",
    "addCustomer": "Agregar Cliente",
    "sendQuote": "Enviar Cotización",
    "generateItinerary": "Generar Itinerario",
    "cancelBooking": "Cancelar Reserva",
    "refundPayment": "Reembolsar Pago"
  },
  "messages": {
    "noResults": "No se encontraron resultados",
    "loading": "Cargando...",
    "success": "Éxito",
    "error": "Ocurrió un error",
    "confirmDelete": "¿Estás seguro de que deseas eliminar este elemento?",
    "unsavedChanges": "Tienes cambios sin guardar. ¿Estás seguro de que deseas salir?"
  },
  "navigation": {
    "home": "Inicio",
    "trips": "Viajes",
    "bookings": "Reservas",
    "customers": "Clientes",
    "suppliers": "Proveedores",
    "reports": "Reportes",
    "settings": "Configuración"
  }
}
```

---

## Component-Level i18n

### Translated Component Pattern

```typescript
/**
 * Base component with i18n support
 */
interface TranslatedComponentProps {
  translationPrefix?: string;
}

/**
 * Higher-order component for translation
 */
function withTranslation<P extends object>(
  Component: React.ComponentType<P & { t: (key: string, params?: object) => string }>,
  namespace: string
) {
  return function TranslatedComponent(props: P) {
    const { t } = useTranslation(namespace);

    // Create prefixed translation function
    const tp = (key: string, params?: object) => {
      const fullKey = `${namespace}.${key}`;
      return t(fullKey, params);
    };

    return <Component {...props} t={tp} />;
  };
}

/**
 * Example: Trip status badge with translations
 */
interface TripStatusBadgeProps {
  status: TripStatus;
}

function TripStatusBadge({ status }: TripStatusBadgeProps) {
  const { t } = useTranslation('trips');

  const statusConfig: Record<TripStatus, { label: string; color: string }> = {
    draft: { label: t('status.draft'), color: 'gray' },
    quote: { label: t('status.quote'), color: 'blue' },
    confirmed: { label: t('status.confirmed'), color: 'green' },
    in_progress: { label: t('status.in_progress'), color: 'yellow' },
    completed: { label: t('status.completed'), color: 'green' },
    cancelled: { label: t('status.cancelled'), color: 'red' }
  };

  const config = statusConfig[status];

  return (
    <span className={`badge badge-${config.color}`}>
      {config.label}
    </span>
  );
}

/**
 * Example: Form with translated labels
 */
function TripForm() {
  const { t } = useTranslation('trips');

  return (
    <form>
      <FormField
        name="destination"
        label={t('form.destination.label')}
        placeholder={t('form.destination.placeholder')}
        required
      />
      <FormField
        name="startDate"
        label={t('form.startDate.label')}
        type="date"
      />
      <FormField
        name="endDate"
        label={t('form.endDate.label')}
        type="date"
      />
      <Button type="submit">
        {t('form.submit')}
      </Button>
    </form>
  );
}
```

### Dynamic Content Translation

```typescript
/**
 * Service for translating dynamic content
 */
class ContentTranslationService {
  private cache: Map<string, Map<string, string>>;

  constructor() {
    this.cache = new Map();
  }

  /**
   * Translate a piece of dynamic content
   */
  async translate(
    content: string,
    targetLocale: SupportedLocale,
    sourceLocale: SupportedLocale = DEFAULT_LOCALE
  ): Promise<string> {
    // Check cache
    const cacheKey = `${sourceLocale}-${targetLocale}:${content}`;
    const targetCache = this.cache.get(targetLocale);
    if (targetCache?.has(cacheKey)) {
      return targetCache.get(cacheKey)!;
    }

    // If same locale, return as-is
    if (sourceLocale === targetLocale) {
      return content;
    }

    // Try to get from database (human translations)
    const translation = await this.getDatabaseTranslation(
      content,
      sourceLocale,
      targetLocale
    );

    if (translation) {
      this.setCache(targetLocale, cacheKey, translation);
      return translation;
    }

    // Fall back to machine translation
    const machineTranslation = await this.machineTranslate(
      content,
      sourceLocale,
      targetLocale
    );

    // Store for review
    await this.storePendingTranslation(content, sourceLocale, targetLocale, machineTranslation);

    this.setCache(targetLocale, cacheKey, machineTranslation);
    return machineTranslation;
  }

  /**
   * Get human translation from database
   */
  private async getDatabaseTranslation(
    content: string,
    sourceLocale: SupportedLocale,
    targetLocale: SupportedLocale
  ): Promise<string | null> {
    const result = await db.query.translations.findFirst({
      where: and(
        eq(translations.sourceText, content),
        eq(translations.sourceLocale, sourceLocale),
        eq(translations.targetLocale, targetLocale),
        eq(translations.status, 'approved')
      )
    });

    return result?.targetText || null;
  }

  /**
   * Machine translate content
   */
  private async machineTranslate(
    content: string,
    sourceLocale: SupportedLocale,
    targetLocale: SupportedLocale
  ): Promise<string> {
    // Integration with translation service (e.g., Google Translate, DeepL)
    const response = await fetch('/api/translate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text: content,
        source: sourceLocale,
        target: targetLocale
      })
    });

    const { translatedText } = await response.json();
    return translatedText;
  }

  /**
   * Store translation pending human review
   */
  private async storePendingTranslation(
    sourceText: string,
    sourceLocale: SupportedLocale,
    targetLocale: SupportedLocale,
    targetText: string
  ): Promise<void> {
    await db.insert(translations).values({
      id: generateId(),
      sourceText,
      sourceLocale,
      targetLocale,
      targetText,
      status: 'pending',
      createdAt: new Date()
    }).onConflictDoNothing();
  }

  /**
   * Set cache entry
   */
  private setCache(locale: SupportedLocale, key: string, value: string): void {
    if (!this.cache.has(locale)) {
      this.cache.set(locale, new Map());
    }
    this.cache.get(locale)!.set(key, value);
  }

  /**
   * Warm up cache for a locale
   */
  async warmupCache(locale: SupportedLocale): Promise<void> {
    const translations = await db.query.translations.findMany({
      where: and(
        eq(translations.targetLocale, locale),
        eq(translations.status, 'approved')
      ),
      limit: 1000
    });

    for (const translation of translations) {
      const key = `${translation.sourceLocale}-${translation.targetLocale}:${translation.sourceText}`;
      this.setCache(locale, key, translation.targetText);
    }
  }
}

export const contentTranslationService = new ContentTranslationService();
```

---

## API Localization

### Localized API Responses

```typescript
/**
 * Localized API middleware
 */
function localizedApiMiddleware(
  request: Request,
  response: Response,
  next: NextFunction
): void {
  // Get locale from request
  const locale = getLocaleFromRequest(request);

  // Attach to response context
  response.locals.locale = locale;

  next();
}

/**
 * Get locale from API request
 */
function getLocaleFromRequest(request: Request): SupportedLocale {
  // Check Accept-Language header
  const acceptLanguage = request.headers.get('accept-language');
  if (acceptLanguage) {
    const detector = new LocaleDetector();
    const detected = detector.getLocaleFromAcceptLanguage({ headers: request.headers } as any);
    if (detected) return detected;
  }

  // Check query parameter
  const url = new URL(request.url);
  const localeParam = url.searchParams.get('locale');
  if (localeParam && SUPPORTED_LOCALES.includes(localeParam as SupportedLocale)) {
    return localeParam as SupportedLocale;
  }

  // Check header
  const localeHeader = request.headers.get('X-Locale');
  if (localeHeader && SUPPORTED_LOCALES.includes(localeHeader as SupportedLocale)) {
    return localeHeader as SupportedLocale;
  }

  return DEFAULT_LOCALE;
}

/**
 * Localized response helper
 */
function localizedResponse<T>(
  data: T,
  locale: SupportedLocale
): LocalizedResponse<T> {
  return {
    data,
    locale,
    currency: LOCALE_CONFIGS[locale].currency,
    dateFormat: LOCALE_CONFIGS[locale].dateFormat,
    numberFormat: LOCALE_CONFIGS[locale].numberFormat
  };
}

/**
 * Example API handler with localization
 */
async function getTripsHandler(
  request: Request,
  response: Response
): Promise<void> {
  const locale = response.locals.locale as SupportedLocale;

  // Fetch trips
  const trips = await db.query.trips.findMany();

  // Localize trip data
  const localizedTrips = trips.map(trip => ({
    ...trip,
    status: localizeTripStatus(trip.status, locale),
    destination: localizeDestination(trip.destination, locale)
  }));

  response.json(localizedResponse(localizedTrips, locale));
}

/**
 * Localize enum values
 */
function localizeTripStatus(status: string, locale: SupportedLocale): string {
  const statusTranslations: Record<string, Record<SupportedLocale, string>> = {
    draft: {
      'en-US': 'Draft',
      'es-ES': 'Borrador',
      'fr-FR': 'Brouillon'
    },
    confirmed: {
      'en-US': 'Confirmed',
      'es-ES': 'Confirmado',
      'fr-FR': 'Confirmé'
    }
    // ... more statuses
  };

  return statusTranslations[status]?.[locale] || status;
}

/**
 * Localize destination names
 */
async function localizeDestination(
  destinationId: string,
  locale: SupportedLocale
): Promise<string> {
  const destination = await db.query.destinations.findFirst({
    where: eq(destinations.id, destinationId)
  });

  if (!destination) return destinationId;

  // Get localized name
  const localized = await db.query.destinationTranslations.findFirst({
    where: and(
      eq(destinationTranslations.destinationId, destinationId),
      eq(destinationTranslations.locale, locale)
    )
  });

  return localized?.name || destination.name;
}
```

### Error Message Localization

```typescript
/**
 * Localized error messages
 */
class LocalizedErrorHandler {
  /**
   * Create localized error response
   */
  handleError(error: Error, locale: SupportedLocale): LocalizedError {
    const errorKey = this.getErrorKey(error);

    return {
      code: errorKey,
      message: this.translateError(errorKey, locale, error),
      details: this.getErrorDetails(error, locale)
    };
  }

  /**
   * Map error to translation key
   */
  private getErrorKey(error: Error): string {
    const errorMap: Record<string, string> = {
      'ValidationError': 'validation.error',
      'NotFoundError': 'not_found',
      'UnauthorizedError': 'unauthorized',
      'ForbiddenError': 'forbidden',
      'RateLimitError': 'rate_limit_exceeded',
      'PaymentError': 'payment.failed'
    };

    return errorMap[error.name] || 'unknown_error';
  }

  /**
   * Translate error message
   */
  private translateError(
    key: string,
    locale: SupportedLocale,
    error: Error
  ): string {
    const { t } = i18n;

    // Try to translate with error context
    let message = t(`errors.${key}`, {
      defaultValue: t('errors.unknown')
    });

    // Add specific error details if available
    if (error instanceof ValidationError && error.details) {
      message += ': ' + error.details.map(d =>
        t(`errors.validation.${d.field}`)
      ).join(', ');
    }

    return message;
  }

  /**
   * Get localized error details
   */
  private getErrorDetails(error: Error, locale: SupportedLocale): Record<string, unknown> {
    const details: Record<string, unknown> = {};

    if (error instanceof ValidationError) {
      details.fields = error.details;
    }

    if (error instanceof RateLimitError) {
      details.retryAfter = error.retryAfter;
      details.limit = error.limit;
    }

    return details;
  }
}

interface LocalizedError {
  code: string;
  message: string;
  details: Record<string, unknown>;
}
```

---

## Content Management

### Translation Management System

```typescript
/**
 * Translation management service
 */
class TranslationManagementService {
  /**
   * Get all translations for a locale
   */
  async getTranslations(locale: SupportedLocale): Promise<TranslationMap> {
    const translations = await db.query.translations.findMany({
      where: eq(translations.targetLocale, locale)
    });

    const map: TranslationMap = {};

    for (const translation of translations) {
      if (!map[translation.namespace]) {
        map[translation.namespace] = {};
      }
      map[translation.namespace][translation.key] = translation.targetText;
    }

    return map;
  }

  /**
   * Update translation
   */
  async updateTranslation(
    id: string,
    updates: {
      targetText: string;
      status?: 'pending' | 'approved' | 'rejected';
      reviewerId?: string;
    }
  ): Promise<void> {
    await db.update(translations)
      .set({
        ...updates,
        reviewedAt: new Date()
      })
      .where(eq(translations.id, id));
  }

  /**
   * Get pending translations for review
   */
  async getPendingTranslations(locale: SupportedLocale): Promise<PendingTranslation[]> {
    const translations = await db.query.translations.findMany({
      where: and(
        eq(translations.targetLocale, locale),
        eq(translations.status, 'pending')
      ),
      orderBy: [translations.createdAt],
      limit: 100
    });

    return translations.map(t => ({
      id: t.id,
      sourceText: t.sourceText,
      sourceLocale: t.sourceLocale,
      targetLocale: t.targetLocale,
      targetText: t.targetText,
      context: t.context,
      createdAt: t.createdAt
    }));
  }

  /**
   * Import translations from file
   */
  async importTranslations(
    locale: SupportedLocale,
    namespace: string,
    translations: Record<string, string>
  ): Promise<void> {
    await db.transaction(async (tx) => {
      for (const [key, value] of Object.entries(translations)) {
        await tx.insert(translations).values({
          id: generateId(),
          namespace,
          key,
          sourceText: key,
          sourceLocale: DEFAULT_LOCALE,
          targetLocale: locale,
          targetText: value,
          status: 'approved',
          createdAt: new Date()
        }).onConflictDoUpdate({
          target: [translations.namespace, translations.key, translations.targetLocale],
          set: {
            targetText: value,
            status: 'approved',
            updatedAt: new Date()
          }
        });
      }
    });
  }

  /**
   * Export translations to file
   */
  async exportTranslations(
    locale: SupportedLocale,
    namespace: string
  ): Promise<Record<string, string>> {
    const translations = await db.query.translations.findMany({
      where: and(
        eq(translations.targetLocale, locale),
        eq(translations.namespace, namespace),
        eq(translations.status, 'approved')
      )
    });

    return translations.reduce((acc, t) => {
      acc[t.key] = t.targetText;
      return acc;
    }, {} as Record<string, string>);
  }

  /**
   * Get translation statistics
   */
  async getStatistics(locale: SupportedLocale): Promise<TranslationStatistics> {
    const [total, pending, approved, rejected] = await Promise.all([
      db.query.translations.findMany({
        where: eq(translations.targetLocale, locale)
      }),
      db.query.translations.findMany({
        where: and(
          eq(translations.targetLocale, locale),
          eq(translations.status, 'pending')
        )
      }),
      db.query.translations.findMany({
        where: and(
          eq(translations.targetLocale, locale),
          eq(translations.status, 'approved')
        )
      }),
      db.query.translations.findMany({
        where: and(
          eq(translations.targetLocale, locale),
          eq(translations.status, 'rejected')
        )
      })
    ]);

    // Calculate coverage by namespace
    const namespaces = ['common', 'trips', 'bookings', 'customers', 'suppliers', 'settings'];
    const coverage: Record<string, number> = {};

    for (const ns of namespaces) {
      const nsTotal = await db.query.translations.findMany({
        where: and(
          eq(translations.targetLocale, locale),
          eq(translations.namespace, ns)
        )
      });

      const nsApproved = await db.query.translations.findMany({
        where: and(
          eq(translations.targetLocale, locale),
          eq(translations.namespace, ns),
          eq(translations.status, 'approved')
        )
      });

      coverage[ns] = nsTotal.length > 0 ? (nsApproved.length / nsTotal.length) * 100 : 0;
    }

    return {
      locale,
      total: total.length,
      pending: pending.length,
      approved: approved.length,
      rejected: rejected.length,
      coveragePercent: total.length > 0 ? (approved.length / total.length) * 100 : 0,
      coverageByNamespace: coverage
    };
  }
}

interface TranslationMap {
  [namespace: string]: {
    [key: string]: string;
  };
}

interface PendingTranslation {
  id: string;
  sourceText: string;
  sourceLocale: SupportedLocale;
  targetLocale: SupportedLocale;
  targetText: string;
  context?: string;
  createdAt: Date;
}

interface TranslationStatistics {
  locale: SupportedLocale;
  total: number;
  pending: number;
  approved: number;
  rejected: number;
  coveragePercent: number;
  coverageByNamespace: Record<string, number>;
}
```

---

## Implementation

### Complete i18n Service

```typescript
/**
 * Complete i18n service
 */
class I18nService {
  private detector: LocaleDetector;
  private contentTranslator: ContentTranslationService;
  private translationManager: TranslationManagementService;
  private errorHandler: LocalizedErrorHandler;

  constructor() {
    this.detector = new LocaleDetector();
    this.contentTranslator = new ContentTranslationService();
    this.translationManager = new TranslationManagementService();
    this.errorHandler = new LocalizedErrorHandler();
  }

  /**
   * Initialize i18n for server-side
   */
  async initialize(request?: Request): Promise<void> {
    const locale = this.detector.detectLocale(request);
    await i18n.changeLanguage(locale);
    await this.contentTranslator.warmupCache(locale);
  }

  /**
   * Get current locale
   */
  getLocale(): SupportedLocale {
    return i18n.language as SupportedLocale;
  }

  /**
   * Get locale config
   */
  getLocaleConfig(locale?: SupportedLocale): LocaleConfig {
    return LOCALE_CONFIGS[locale || this.getLocale()];
  }

  /**
   * Check if RTL
   */
  isRTL(locale?: SupportedLocale): boolean {
    return this.getLocaleConfig(locale).rtl;
  }

  /**
   * Format date
   */
  formatDate(date: Date, locale?: SupportedLocale): string {
    const config = this.getLocaleConfig(locale);
    return new Intl.DateTimeFormat(locale, {
      dateStyle: 'medium'
    }).format(date);
  }

  /**
   * Format number
   */
  formatNumber(num: number, locale?: SupportedLocale): string {
    return new Intl.NumberFormat(locale).format(num);
  }

  /**
   * Format currency
   */
  formatCurrency(amount: number, currency?: string, locale?: SupportedLocale): string {
    const config = this.getLocaleConfig(locale);
    return new Intl.NumberFormat(locale, {
      style: 'currency',
      currency: currency || config.currency
    }).format(amount);
  }
}

export const i18nService = new I18nService();
```

---

## Testing Scenarios

```typescript
describe('i18n Architecture', () => {
  describe('Locale Detection', () => {
    it('should detect locale from URL', () => {
      const detector = new LocaleDetector();
      const locale = detector.extractLocaleFromURL('/es-ES/trips');
      expect(locale).toBe('es-ES');
    });

    it('should fallback to default for unsupported locale', () => {
      const detector = new LocaleDetector();
      const request = new Request('https://example.com', {
        headers: { 'accept-language': 'zh-CN' }
      });
      const locale = detector.detectLocale(request);
      expect(locale).toBe(DEFAULT_LOCALE);
    });
  });

  describe('Translation Loading', () => {
    it('should load translations for namespace', async () => {
      const { t } = await i18nService;
      await i18n.loadNamespaces('trips');
      expect(t('trips.list.title')).toBeDefined();
    });
  });

  describe('Content Translation', () => {
    it('should translate dynamic content', async () => {
      const service = new ContentTranslationService();
      const translated = await service.translate('Hello, world!', 'es-ES');
      expect(translated).toBe('¡Hola, mundo!');
    });
  });

  describe('RTL Support', () => {
    it('should detect RTL locales', () => {
      expect(i18nService.isRTL('ar-SA')).toBe(true);
      expect(i18nService.isRTL('en-US')).toBe(false);
    });
  });
});
```

---

## API Specification

```yaml
paths:
  /api/i18n/locales:
    get:
      summary: Get supported locales
      responses:
        '200':
          description: List of supported locales
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/LocaleConfig'

  /api/i18n/translations/{locale}:
    get:
      summary: Get translations for locale
      parameters:
        - name: locale
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Translation map

  /api/i18n/translate:
    post:
      summary: Translate text
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
          description: Translated text

components:
  schemas:
    LocaleConfig:
      type: object
      properties:
        code:
          type: string
        name:
          type: string
        nativeName:
          type: string
        flag:
          type: string
        rtl:
          type: boolean
        currency:
          type: string
```

---

## Metrics and Monitoring

```typescript
interface I18nMetrics {
  totalTranslations: number;
  translationsByLocale: Record<string, number>;
  pendingTranslations: number;
  missingKeys: number;
  cacheHitRate: number;
  averageLoadTime: number;
}
```

---

**End of Document**

**Next:** [Localization Management Deep Dive](INTERNATIONALIZATION_02_LOCALIZATION.md)
