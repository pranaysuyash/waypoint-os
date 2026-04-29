# Multi-Language & Internationalization — Content Localization

> Research document for localization beyond translation: currency, dates, numbers, addresses, phone formatting, UI patterns, regional content, and measurement units for Indian travel agency context.

---

## Key Questions

1. **How do we format prices using the Indian lakh/crore system alongside the Rupee symbol?**
2. **What date format is most natural for Indian users — DD/MM/YYYY or something else?**
3. **How do we handle Indian address formats that differ from Western assumptions (no postal codes in many rural areas, area/landmark-based addressing)?**
4. **What form field patterns work for Indian names (which may not follow first/middle/last conventions)?**
5. **How do we localize destination content (descriptions, cultural notes) for regional Indian audiences?**
6. **Should we use Celsius or Fahrenheit, kilometers or miles, and how do we let users choose?**
7. **How do we format Indian phone numbers (+91 country code, 10-digit mobile, varied landline formats)?**

---

## Research Areas

### Currency Formatting

```typescript
interface CurrencyFormattingConfig {
  locale: string;
  currency: string;               // ISO 4217: 'INR', 'USD', 'EUR'
  symbol: string;                  // Display symbol: '₹', '$', '€'
  symbolPosition: 'prefix' | 'suffix';
  decimalDigits: number;
  groupSeparator: string;          // ',' or '.'
  decimalSeparator: string;        // '.' or ','
  groupingPattern: 'western' | 'indian';  // '##,###,###' vs '##,##,###'
}

interface IndianCurrencyFormatting {
  // Indian number grouping (lakh/crore system):
  //
  // Western:     1,000,000  (million)
  // Indian:     10,00,000  (ten lakh)
  //
  // Western:     100,000,000  (hundred million)
  // Indian:   1,00,00,000  (one crore)
  //
  // Pattern: First group of 3 digits from right,
  //          then groups of 2 digits
  //
  // Examples:
  //   ₹500                        ₹ 500
  //   ₹1,200                      ₹ 1,200
  //   ₹12,500                     ₹ 12,500
  //   ₹1,25,000                   ₹ 1,25,000  (one lakh twenty-five thousand)
  //   ₹12,50,000                  ₹ 12,50,000 (twelve lakh fifty thousand)
  //   ₹1,25,00,000                ₹ 1,25,00,000 (one crore twenty-five lakh)
  //
  // JavaScript Intl.NumberFormat with 'en-IN' locale:
  //   new Intl.NumberFormat('en-IN', {
  //     style: 'currency',
  //     currency: 'INR'
  //   }).format(125000)
  //   → "₹1,25,000.00"
  //
  // For spoken/written amounts in Hindi:
  //   ₹1,25,000 = "एक लाख पच्चीस हज़ार" (ek lakh pachees hazaar)
  //   These should appear in translated price breakdowns
}

interface CurrencyDisplayOptions {
  showSymbol: boolean;
  showCode: boolean;               // Show 'INR' alongside ₹
  compactNotation: boolean;        // ₹1.25L instead of ₹1,25,000
  spokenForm: boolean;             // "ek lakh pachees" in Hindi
  roundingRule: 'standard' | 'round_up' | 'round_down' | 'nearest_10' | 'nearest_100';
}

// Compact notation for Indian prices:
//   ₹500        → ₹500
//   ₹1,500      → ₹1.5K
//   ₹25,000     → ₹25K
//   ₹1,25,000   → ₹1.25L  (L = Lakh)
//   ₹12,50,000  → ₹12.5L
//   ₹1,25,00,000 → ₹1.25Cr (Cr = Crore)
//
// Note: 'L' for lakh and 'Cr' for crore are widely understood
// abbreviations in India, even in English-language content.

interface MultiCurrencyScenario {
  // Indian travel agency scenarios:
  //
  // 1. Domestic booking:
  //    Customer pays in INR, supplier prices in INR
  //    → Single currency, Indian formatting
  //
  // 2. International booking (outbound):
  //    Customer pays in INR, hotel in Thailand quotes in THB
  //    → Show both: "฿15,000 (≈ ₹33,750)" with live conversion
  //
  // 3. NRI customer:
  //    Customer in US wants to book India trip for parents
  //    → Show in USD with INR secondary
  //
  // 4. Corporate booking:
  //    MNC employee in India, billing to US HQ
  //    → Invoice in USD, receipt in INR (GST compliance)
  //
  // Currency display rules:
  //   - Primary currency: based on user's billing address country
  //   - Secondary currency: based on destination country
  //   - Conversion rate: show "rate as of [date]" disclaimer
  //   - Rounding: always round in customer's favor (floor for charges)
}
```

### Date and Time Formatting

```typescript
interface DateFormattingConfig {
  locale: string;
  shortFormat: string;             // 'DD/MM/YYYY'
  mediumFormat: string;            // 'DD MMM YYYY'
  longFormat: string;              // 'DD MMMM YYYY'
  timeFormat: '12h' | '24h';
  firstDayOfWeek: number;          // 0=Sun, 1=Mon
  weekendDays: number[];           // [0, 6] = Sat+Sun or [5, 6] = Fri+Sat
  calendarType: 'gregorian' | 'islamic' | 'hindu';
}

// Indian date formatting conventions:
//
// Standard: DD/MM/YYYY (most common in India)
//   28/04/2026
//
// Alternative: DD-MM-YYYY
//   28-04-2026
//
// With month name: DD MMM YYYY or DD MMMM YYYY
//   28 Apr 2026 or 28 April 2026
//
// Hindi date format:
//   28 अप्रैल 2026
//   Or using Hindi month names: 28 चैत्र 2026 (Vikram Samvat calendar)
//
// Fiscal year in India: April 1 to March 31
//   FY2026 = April 1, 2025 to March 31, 2026
//   Important for: GST filing, TCS reporting, corporate billing
//
// Time in India:
//   IST (UTC+5:30) — single timezone for entire country
//   12-hour format most common: 3:30 PM
//   24-hour format used in: railways, airlines, military
//
// Travel-specific date considerations:
//   - Hotel check-in: usually 2:00 PM IST
//   - Hotel check-out: usually 12:00 PM IST
//   - Flight times: always 24-hour format in tickets
//   - Train times: 24-hour format (Indian Railways)
//   - Tour start times: 12-hour with AM/PM
//
// Festival calendar (affects pricing and availability):
//   - Diwali: Hindu lunar calendar (Oct/Nov, dates vary)
//   - Eid: Islamic calendar (dates vary)
//   - Christmas: December 25 (fixed)
//   - Holi: Hindu lunar calendar (March, dates vary)
//   - Onam: Malayalam calendar (Aug/Sep)
//   - Pongal: Tamil solar calendar (January 14)

interface DateFormattingStrategy {
  defaultFormat: 'DD/MM/YYYY';
  travelContextFormats: {
    hotelDates: string;            // "28 Apr – 02 May 2026"
    flightTimes: string;           // "14:30 IST" (24h)
    itineraryDays: string;         // "Day 1 — Monday, 28 April"
    bookingConfirmation: string;   // "28/04/2026 at 3:30 PM IST"
    invoiceDate: string;           // "28-Apr-2026" (GST format)
  };
  relativeFormats: {
    daysAgo: string;               // "3 din pehle" (Hindi) / "3 days ago"
    tomorrow: string;              // "kal" / "tomorrow"
    nextWeek: string;              // "agle hafte" / "next week"
  };
}
```

### Number Formatting

```typescript
interface IndianNumberFormatting {
  // The Indian numbering system:
  //
  // Western:  thousand → million → billion → trillion
  // Indian:   hazār (thousand) → lakh (100K) → crore (10M) → arab (1B)
  //
  // Digit grouping:
  //   Western:  100,000    (hundred thousand)
  //   Indian:   1,00,000   (one lakh)
  //
  //   Western:  10,000,000 (ten million)
  //   Indian:   1,00,00,000 (one crore)
  //
  // JavaScript Intl.NumberFormat('en-IN') handles this correctly:
  //   new Intl.NumberFormat('en-IN').format(100000)
  //   → "1,00,000"
  //
  //   new Intl.NumberFormat('en-IN').format(10000000)
  //   → "1,00,00,000"
}

interface NumberFormattingConfig {
  locale: string;
  decimalSeparator: '.' | ',';
  groupSeparator: ',' | '.' | ' ' | "'";
  groupingPattern: 'western' | 'indian';
  decimalPlaces: {
    currency: number;              // 2 for INR
    distance: number;              // 1 for km
    temperature: number;           // 0 for Celsius
    percentage: number;            // 1 for commission
  };
}

// Travel-specific number formatting:
//
// Distances:
//   India uses kilometers (not miles)
//   "Mumbai to Goa: 580 km"
//   "Airport to hotel: 15 km (approx. 45 min by car)"
//
// Temperature:
//   India uses Celsius
//   "Kerala in December: 25-32°C"
//   "Shimla in January: -2 to 8°C"
//
// Weights:
//   India uses kilograms
//   Baggage allowance: "23 kg check-in, 7 kg cabin"
//
// Percentages:
//   Commission: "12.5% margin on hotel booking"
//   Tax: "5% GST on hotel, 18% GST on services"
//   Discount: "15% early bird discount"
//
// Special Indian travel numbers:
//   PNR (Passenger Name Record): 10-digit alphanumeric
//   PNR for Indian Railways: 10-digit numeric
//   PAN (tax ID): 10-character alphanumeric (ABCDE1234F format)
//   Aadhaar: 12-digit numeric (often shown as XXXX XXXX XXXX)
//   GSTIN: 15-character alphanumeric
```

### Address Formatting

```typescript
interface IndianAddress {
  // Indian addresses do NOT follow Western "street, city, state, zip" patterns.
  // Common Indian address format:
  //
  // [House/Flat No], [Building Name]
  // [Street/Area/Locality]
  // [Landmark]                     ← Unique to India, very important
  // [City/Town/Village]
  // [District]
  // [State] [PIN Code]
  //
  // Example:
  //   Flat 302, Sapphire Heights
  //   MG Road, Indiranagar
  //   Near Metro Station
  //   Bengaluru
  //   Karnataka 560038

  houseFlat: string;               // "Flat 302" or "H.No. 15-2-3"
  buildingName?: string;           // "Sapphire Heights"
  streetArea: string;              // "MG Road, Indiranagar"
  landmark?: string;               // "Near Metro Station" — critical for delivery
  cityTownVillage: string;         // "Bengaluru" or "Gadwal (village)"
  district?: string;               // "Bengaluru Urban"
  state: string;                   // "Karnataka"
  pinCode: string;                 // 6-digit: "560038"
}

interface AddressFormConfig {
  fields: AddressField[];
  layout: 'indian' | 'western' | 'adaptive';
  pinCodeLookup: boolean;          // Auto-fill city/state from PIN
  landmarkSuggestion: boolean;     // Suggest nearby landmarks
  stateList: string[];             // 28 states + 8 UTs
  validatePinCode: boolean;
}

interface AddressField {
  name: string;
  label: {
    en: string;
    hi: string;
    native: Record<string, string>;  // Per-locale labels
  };
  required: boolean;
  type: 'text' | 'select' | 'lookup';
  placeholder: string;
  maxLength: number;
  helpText?: string;
}

// Address form field comparison:
//
// Western form:                    Indian form:
// ┌─────────────────────┐         ┌─────────────────────┐
// │ First Name          │         │ Full Name            │
// ├─────────────────────┤         │ (or First/Last)      │
// │ Last Name           │         ├─────────────────────┤
// ├─────────────────────┤         │ Flat/House No.       │
// │ Address Line 1      │         ├─────────────────────┤
// ├─────────────────────┤         │ Building/Apartment   │
// │ Address Line 2      │         ├─────────────────────┤
// ├─────────────────────┤         │ Area/Locality        │
// │ City                │         ├─────────────────────┤
// ├─────────────────────┤         │ Landmark             │
// │ State               │         │ (e.g., near temple)  │
// ├─────────────────────┤         ├─────────────────────┤
// │ ZIP Code            │         │ City/Town            │
// └─────────────────────┘         ├─────────────────────┤
//                                  │ State               │
//                                  ├─────────────────────┤
//                                  │ PIN Code (6 digits) │
//                                  └─────────────────────┘
//
// India PIN code system:
//   6 digits: XXXXXX
//   First digit: postal region (1-8)
//   First 3 digits: sorting district
//   Last 3 digits: specific post office
//   API: India Post PIN code lookup (or Google Geocoding)
//
// States/UTs dropdown:
//   28 states + 8 Union Territories
//   Should be translated: "Karnataka" → "ಕರ್ನಾಟಕ" (Kannada)
//   Sort order: alphabetical in user's language
```

### Phone Number Formatting

```typescript
interface IndianPhoneFormatting {
  // Indian phone number formats:
  //
  // Mobile (most common):
  //   +91 XXXXX XXXXX            (with country code)
  //   0XXXXX XXXXX               (with trunk prefix)
  //   XXXXX XXXXX                (local, 10 digits)
  //
  // Landline:
  //   +91 XX XXXX XXXX           (area code + number)
  //   0XX XXXX XXXX              (with trunk prefix)
  //   Area codes: 2-4 digits
  //     Mumbai: 22, Delhi: 11, Bengaluru: 80, Chennai: 44
  //     Hyderabad: 40, Kolkata: 33, Pune: 20
  //
  // Toll-free:
  //   1800 XXX XXXX              (1-800 numbers)
  //   1860 XXX XXXX              (1-860 numbers)
  //
  // Mobile number validation:
  //   Starts with: 6, 7, 8, or 9 (TRAI allocation)
  //   Total: 10 digits
  //   Do Not Call registry check for marketing
}

interface PhoneFormattingConfig {
  defaultCountryCode: '+91';
  displayFormat: {
    mobile: '+91 XXXXX XXXXX';
    landline: '+91 XX XXXX XXXX';
    tollFree: '1800 XXX XXXX';
  };
  inputFormat: 'national' | 'international' | 'e164';
  validation: {
    mobilePattern: string;         // /^[6-9]\d{9}$/
    landlinePattern: string;
  };
  countries: CountryCodeConfig[];
}

interface CountryCodeConfig {
  code: string;                    // '+91'
  iso: string;                     // 'IN'
  name: string;                    // 'India'
  flag: string;                    // Emoji flag
  mobileLength: number;            // 10
}

// Phone input UX for Indian users:
//
// ┌─────────────────────────────────────┐
// │ 🇮🇳 +91 │ XXXXX XXXXX              │
// │         │                           │
// │ [dropdown to change country code]   │
// └─────────────────────────────────────┘
//
// Features:
//   - Default to +91 for Indian users
//   - Auto-format as user types (5+5 grouping for mobile)
//   - Country code dropdown with flag and search
//   - Validate first digit (6-9 for Indian mobile)
//   - Handle paste with or without +91 prefix
//   - Support for NRI customers: show US/UK/etc. codes
//
// Travel-specific phone scenarios:
//   - Customer mobile: primary contact for booking updates
//   - Emergency contact: during trip
//   - Hotel phone: displayed in itinerary
//   - Agent direct line: for customer support
//   - Supplier contact: for operational coordination
//   - International roaming: show country code prominently
```

### Localized UI Patterns

```typescript
interface IndianNameFormat {
  // Indian naming conventions vary dramatically by region:
  //
  // North India (Hindi belt):
  //   [Given Name] [Surname/Family Name]
  //   Example: Rahul Sharma, Priya Gupta
  //   Some use: [Given Name] [Father's Name]
  //
  // South India:
  //   Tamil: [Initial]. [Given Name] or [Given Name] [Initial].
  //     Example: R. Rajinikanth or Rajinikanth R.
  //     Initial = father's name initial or village name
  //   Telugu: [Given Name] [Father's Name] or [Surname] [Given Name]
  //   Kannada: Similar to Telugu
  //   Malayalam: [Given Name] [Father's Name/House Name]
  //
  // Bengal:
  //   [Given Name] [Surname]
  //   Example: Subrata Banerjee, Ananya Chatterjee
  //
  // Gujarat:
  //   [Given Name] [Father's Name] [Surname]
  //   Example: Narendra Damodardas Modi
  //   Or: [First] [Middle] [Last]
  //
  // Sikh:
  //   Singh (male) / Kaur (female) as middle or last name
  //   Example: Harpreet Singh, Gurleen Kaur
  //
  // Single name users:
  //   Some rural or tribal users may have only one name
  //   Some historical/cultural figures: single name
  //   Some international travelers: single name on passport
}

interface NameFieldConfig {
  mode: 'western' | 'indian' | 'single' | 'flexible';
  fields: NameField[];
  validation: NameValidation;
  culturalNotes: string[];
}

interface NameField {
  name: string;                    // 'fullName' | 'givenName' | 'surname' etc.
  label: Record<string, string>;   // Per-locale labels
  required: boolean;
  maxLength: number;
  helpText?: Record<string, string>;
  placeholder?: Record<string, string>;
}

// Recommended: Flexible name input
//
// ┌─────────────────────────────────────┐
// │ Full Name *                         │
// │ [                                    ] │
// │ Enter your name as on your passport  │
// ├─────────────────────────────────────┤
// │ ▸ Add more name details (optional)   │
// │   First Name: [         ]            │
// │   Last Name:  [         ]            │
// └─────────────────────────────────────┘
//
// Single "Full Name" field is most inclusive.
// Optional expansion for first/last when needed (passport, billing).

interface IndianFormPatterns {
  // Common Indian form patterns:
  //
  // 1. Aadhaar number (12 digits):
  //    XXXX XXXX XXXX
  //    Masked display: XXXX XXXX X123
  //
  // 2. PAN card (10 chars):
  //    ABCDE1234F
  //    Format: 5 letters + 4 digits + 1 letter
  //
  // 3. GSTIN (15 chars):
  //    22AAAAA0000A1Z5
  //    Format: 2 digits (state) + 10 (PAN) + 1 + 1 + 1
  //
  // 4. Date of birth:
  //    DD/MM/YYYY format
  //    Some forms ask for age directly (rural users)
  //
  // 5. Gender:
  //    Male / Female / Other (Transgender — legally recognized in India)
  //    Hindi: पुरुष / महिला / अन्य
  //
  // 6. Marital status:
  //    Single / Married / Divorced / Widowed
  //    Relevant for: visa applications, insurance
}
```

### Regional Content Adaptation

```typescript
interface RegionalContentConfig {
  // Destination descriptions should be available in regional languages:
  //
  // Example: Kerala Backwaters
  //
  // English:
  //   "Experience the serene backwaters of Kerala aboard
  //    a traditional houseboat. Cruise through palm-lined
  //    canals and enjoy freshly caught seafood."
  //
  // Hindi:
  //   "केरल के शांत बैकवाटर में पारंपरिक हाउसबोट पर
  //    अद्भुत अनुभव करें। ताड़ के पेड़ों से घिरी नहरों
  //    से होते हुए ताज़ी समुद्री मछली का आनंद लें।"
  //
  // Hinglish:
  //   "Kerala ke backwaters mein traditional houseboat pe
  //    cruise karo. Palm trees se ghiri canals se hote hue
  //    fresh seafood enjoy karo."
  //
  // Tamil (relevant since Kerala borders Tamil Nadu):
  //   "கேரளாவின் அமைதியான பின்னணி நீர்வழிகளில்
  //    பாரம்பரிய வீட்டுப்படகில் பயணிக்கவும்."
}

interface ContentLocalizationStrategy {
  staticContent: {
    // UI strings, labels, buttons → translation files
    strategy: 'translation_keys';
  };
  semiDynamicContent: {
    // Destination descriptions, package details → CMS with localized fields
    strategy: 'cms_localized_fields';
  };
  dynamicContent: {
    // AI-generated itineraries, chat responses → real-time translation
    strategy: 'machine_translation_with_review';
  };
  userGeneratedContent: {
    // Reviews, Q&A → translate on demand, show original + translation
    strategy: 'on_demand_translation';
  };
}

// Cultural sensitivity in imagery:
//
// Images should reflect Indian cultural context:
//   - Family groups (multi-generational travel is common in India)
//   - Diverse Indian ethnicities and skin tones
//   - Indian clothing (sarees, kurtas) alongside Western wear
//   - Religious sites with respectful imagery
//   - Indian cuisine (vegetarian options prominently shown)
//   - Festival celebrations (Diwali, Holi, Onam)
//
// Avoid:
//   - Beef imagery (cultural sensitivity for Hindu customers)
//   - Pork imagery (cultural sensitivity for Muslim customers)
//   - Alcohol in family-friendly content
//   - Revealing clothing at religious destinations
//   - Romantic imagery that may not resonate in all segments
//
// Adapt by region:
//   - North India: Hill stations, temples, Mughal architecture
//   - South India: Temples, backwaters, beaches
//   - West India: Beaches, forts, desert
//   - East India: Tea gardens, mountains, temples
//   - Northeast India: Adventure, nature, tribal culture
```

### Measurement Units

```typescript
interface MeasurementUnits {
  distance: 'km' | 'miles';
  temperature: 'celsius' | 'fahrenheit';
  weight: 'kg' | 'lbs';
  area: 'sqft' | 'sqm';
  volume: 'liters' | 'gallons';
}

interface IndianMeasurementDefaults {
  // India uses the metric system officially:
  distance: 'km';
  temperature: 'celsius';
  weight: 'kg';
  area: 'sqft';                    // Real estate uses sqft in India
  volume: 'liters';
  // Note: Some Indians (especially NRIs or older generation)
  //       may prefer imperial for certain contexts
}

interface MeasurementDisplayStrategy {
  primary: MeasurementUnits;
  secondary?: MeasurementUnits;    // Show in parentheses
  userPreference: boolean;         // Allow user override
  contexts: MeasurementContext[];
}

interface MeasurementContext {
  context: string;                 // 'driving_distance', 'temperature', etc.
  primary: string;                 // 'km'
  secondary?: string;              // 'miles' (for US-destination trips)
  format: string;                  // '{value} {unit}'
}

// Travel-specific measurement scenarios:
//
// Driving distance:
//   "Delhi to Agra: 230 km (approx. 3.5 hours)"
//   Show: hours+minutes (not decimal hours)
//
// Temperature (destination):
//   "Goa in March: 32°C" (no secondary needed for Indian destinations)
//   "New York in March: 5°C / 41°F" (show both for international)
//
// Hotel room:
//   "Deluxe Room: 350 sq.ft." (India uses sq.ft.)
//
// Baggage:
//   "Check-in: 23 kg, Cabin: 7 kg"
//   Show in kg for domestic, both for international
//
// Altitude:
//   "Shimla: 2,276 m above sea level"
//   Mountain destinations show altitude in meters
//
// Travel time:
//   Always show in hours and minutes: "2h 30m"
//   Never decimal: NOT "2.5 hours"
//   For long routes: "14h 20m" or "1 day 2h"
```

### Data Models for Localization

```typescript
/**
 * Complete localization configuration
 */
interface LocalizationConfig {
  locale: string;
  currency: CurrencyFormattingConfig;
  date: DateFormattingConfig;
  number: NumberFormattingConfig;
  address: AddressFormConfig;
  phone: PhoneFormattingConfig;
  name: NameFieldConfig;
  measurement: MeasurementDisplayStrategy;
  content: ContentLocalizationStrategy;
}

/**
 * Localized travel content model
 */
interface LocalizedDestination {
  id: string;
  slug: string;
  names: Record<string, string>;           // { en: 'Kerala', hi: 'केरल', ta: 'கேரளா' }
  descriptions: Record<string, string>;    // Per-locale long description
  shortDescriptions: Record<string, string>; // Per-locale short description
  taglines: Record<string, string>;        // Marketing taglines
  highlights: Record<string, string[]>;    // Per-locale highlight points
  bestTimeToVisit: Record<string, string>; // Per-locale seasonal info
  culturalNotes: Record<string, string>;   // Cultural context per locale
  images: LocalizedImage[];
}

interface LocalizedImage {
  url: string;
  alt: Record<string, string>;             // Per-locale alt text
  caption: Record<string, string>;         // Per-locale caption
  culturalContext?: string;                // Notes on cultural appropriateness
}

/**
 * Formatted output for display
 */
interface FormattedOutput {
  currency: (amount: number, options?: CurrencyFormatOptions) => string;
  date: (date: Date, format: string) => string;
  number: (value: number, options?: NumberFormatOptions) => string;
  distance: (km: number, context?: string) => string;
  temperature: (celsius: number, context?: string) => string;
  phone: (raw: string) => string;
  address: (addr: IndianAddress) => string;  // Formatted multi-line
}

interface CurrencyFormatOptions {
  showCode?: boolean;
  compact?: boolean;              // Use L/Cr notation
  rounding?: string;
}

interface NumberFormatOptions {
  style?: 'decimal' | 'percent' | 'unit';
  maximumFractionDigits?: number;
}
```

---

## Open Problems

1. **Lakh/crore in input fields.** Users may type "1.5L" or "1.5 lakh" in price input fields. We need to parse these informal notations into numeric values. This is especially relevant for agent-facing UIs where agents type customer budgets quickly.

2. **PIN code auto-fill reliability.** India Post's PIN code API has limited coverage for rural areas. Google's Geocoding API is more reliable but costs money. We need a fallback strategy when PIN lookup fails -- likely manual state/city selection with the PIN as optional.

3. **Name field design for forms going to external systems.** Our internal system can use a single "Full Name" field, but external APIs (airline GDS, hotel CRS, visa applications) require split names (first/middle/last/title). We need a smart name parser or ask users to provide both formats.

4. **Regional calendar integration.** Hindu, Islamic, and regional (Tamil, Bengali, Malayalam) calendars affect travel planning (festivals, auspicious dates). Showing dates in multiple calendar systems is technically possible with libraries like `calendar-widgets` but the UX complexity is significant.

5. **Temperature and distance preference detection.** Should we default to Celsius/km for all Indian users, or detect based on user's travel history (if they frequently travel to the US, show Fahrenheit alongside)? The preference is individual, not purely locale-based.

6. **Address geocoding for rural India.** Many Indian addresses use landmarks ("near Shiva temple", "opposite bus stand") which are not geocodable. For travel pickups and hotel locations, we need to handle both precise coordinates and landmark-based approximate locations.

7. **Currency formatting consistency across components.** Different parts of the UI (trip builder, booking confirmation, invoice, customer-facing itinerary) may format the same amount differently. We need a single shared formatting service to ensure `₹1,25,000.00` is consistent everywhere.

---

## Next Steps

1. **Create shared formatting service.** Implement a `useLocaleFormatter()` React hook that provides currency, date, number, distance, temperature, and phone formatting functions based on the current locale. Use `Intl.NumberFormat('en-IN')` and `Intl.DateTimeFormat` as the foundation.

2. **Build Indian address form component.** Create a `<IndianAddressForm>` component with PIN code lookup, landmark field, state/UT dropdown, and auto-formatting. Test with real addresses from different states.

3. **Implement lakh/crore compact notation.** Add a `formatIndianCurrency()` function that produces "₹1.25L" and "₹2.5Cr" for compact displays (cards, summaries) while keeping full notation for invoices and confirmations.

4. **Design flexible name field.** Build a `<NameInput>` component that starts with "Full Name" and optionally expands to first/last/title fields. Validate against passport name requirements for booking integration.

5. **Locale-aware measurement display.** Create a `<DistanceDisplay>`, `<TemperatureDisplay>` component pair that shows the right units based on destination country (km for India, both for international) with user preference override.

6. **Regional content authoring workflow.** Set up CMS fields for destination content in Tier 1 languages (en, hi). Create translation templates for destination descriptions, highlights, and cultural notes.

7. **Phone input with country code selector.** Build or integrate a phone input component (consider `react-phone-number-input` or `libphonenumber-js`) that defaults to +91, auto-formats as user types, and validates Indian mobile number rules.

---

**End of Document**

**Next:** [Language Support Tiers](I18N_03_LANGUAGES.md)
