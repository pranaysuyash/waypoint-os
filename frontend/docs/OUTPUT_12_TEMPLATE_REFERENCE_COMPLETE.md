# Output Panel 12: Complete Template Reference

> Comprehensive guide to template syntax, helpers, components, and best practices

---

## Part 1: Template System Overview

### 1.1 Technology Stack

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        TEMPLATE ENGINE STACK                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  LAYER 1: Base Engine                                               │   │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │   │
│  │  Handlebars.js (v4.7+)                                               │   │
│  │  - Logicless templates                                              │   │
│  │  - Safe by default (auto-escaping)                                  │   │
│  │  - Custom helpers                                                   │   │
│  │  - Partials support                                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  LAYER 2: Custom Extensions                                         │   │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │   │
│  │  Travel-Specific Helpers                                            │   │
│  │  - Date formatting (timezones, durations)                           │   │
│  │  - Currency conversion & formatting                                 │   │
│  │  - Number formatting (Indian numbering)                             │   │
│  │  - Conditional rendering for travel logic                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  LAYER 3: Component Library                                         │   │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │   │
│  │  Reusable Partials                                                  │   │
│  │  - Header/Footer                                                   │   │
│  │  - Pricing tables                                                  │   │
│  │  - Flight segments                                                 │   │
│  │  - Hotel cards                                                      │   │
│  │  - Timeline components                                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  LAYER 4: PDF Generation                                            │   │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │   │
│  │  Puppeteer + HTML-to-PDF                                            │   │
│  │  - Chrome headless rendering                                       │   │
│  │  - Print CSS optimization                                          │   │
│  │  - Page break control                                              │   │
│  │  - Header/footer templates                                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Template Inheritance Hierarchy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    TEMPLATE RESOLUTION ORDER                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Request: Generate Quote for Agency ABC, Trip Type: Honeymoon              │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  1. CHECK: One-off customization?                                   │   │
│  │     ─────────────────────────────────────────────────────────────   │   │
│  │     templates/agency-abc/quote/honeymoon-custom.hbs                 │   │
│  │                                                                      │   │
│  │     IF FOUND → Use this template (highest priority)                  │   │
│  │     IF NOT FOUND → Continue to step 2                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                   │                                         │
│                                   ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  2. CHECK: Trip-type variant?                                       │   │
│  │     ─────────────────────────────────────────────────────────────   │   │
│  │     templates/agency-abc/quote/honeymoon.hbs                        │   │
│  │     templates/system/quote/honeymoon.hbs                            │   │
│  │                                                                      │   │
│  │     IF FOUND → Use this template                                     │   │
│  │     IF NOT FOUND → Continue to step 3                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                   │                                         │
│                                   ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  3. CHECK: Bundle-type template?                                    │   │
│  │     ─────────────────────────────────────────────────────────────   │   │
│  │     templates/agency-abc/quote/default.hbs                          │   │
│  │     templates/system/quote/default.hbs                              │   │
│  │                                                                      │   │
│  │     IF FOUND → Use this template                                     │   │
│  │     IF NOT FOUND → Continue to step 4                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                   │                                         │
│                                   ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  4. CHECK: Agency master template?                                  │   │
│  │     ─────────────────────────────────────────────────────────────   │   │
│  │     templates/agency-abc/master.hbs                                 │   │
│  │                                                                      │   │
│  │     IF FOUND → Apply as wrapper                                      │   │
│  │     IF NOT FOUND → Continue to step 5                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                   │                                         │
│                                   ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  5. FALLBACK: System base template                                  │   │
│  │     ─────────────────────────────────────────────────────────────   │   │
│  │     templates/system/base.hbs                                       │   │
│  │                                                                      │   │
│  │     ALWAYS EXISTS → Use as final wrapper                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Final Render: Base Layout → Agency Master → Bundle Template → Content     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Part 2: Handlebars Syntax Reference

### 2.1 Basic Syntax

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    HANDLEBARS SYNTAX QUICK REFERENCE                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  VARIABLES                                                           │   │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │   │
│  │  {{customerName}}              → Escape & render                     │   │
│  │  {{{customerName}}}             → Render raw (unescaped)             │   │
│  │  {{customerName.firstName}}    → Nested property                    │   │
│  │  {{../../agency.name}}          → Parent path (../)                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  COMMENTS                                                            │   │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │   │
│  │  {{!-- This is a comment --}}                                       │   │
│  │  {{! This is also a comment }}                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  CONDITIONALS                                                        │   │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │   │
│  │  {{#if customer.gstIn}}                                             │   │
│  │    GSTIN: {{customer.gstIn}}                                        │   │
│  │  {{else}}                                                           │   │
│  │    GSTIN: N/A                                                       │   │
│  │  {{/if}}                                                            │   │
│  │                                                                      │   │
│  │  {{#unless items}}                                                 │   │
│  │    No items found                                                   │   │
│  │  {{/unless}}                                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ITERATORS                                                           │   │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │   │
│  │  {{#each days}}                                                     │   │
│  │    Day {{@index}}: {{this.title}}                                   │   │
│  │  {{/each}}                                                          │   │
│  │                                                                      │   │
│  │  {{#each items}}                                                    │   │
│  │    {{@key}}: {{this}}              → Object iteration               │   │
│  │  {{/each}}                                                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  PARTIALS                                                            │   │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │   │
│  │  {{> components/header}}                                            │   │
│  │  {{> 'components/flight-card' flight=segment}}                      │   │
│  │  {{> (lookupPartial 'custom-type') bundleType=type}}                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Built-in Block Helpers

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      BUILT-IN BLOCK HELPERS                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  {{#if condition}}                                                         │
│    Content when condition is truthy                                        │
│  {{else if otherCondition}}                                                │
│    Content when otherCondition is truthy                                   │
│  {{else}}                                                                  │
│    Content when all conditions are falsy                                   │
│  {{/if}}                                                                   │
│                                                                             │
│  {{#unless condition}}                                                     │
│    Content when condition is falsy (inverse of if)                         │
│  {{/unless}}                                                               │
│                                                                             │
│  {{#each array}}                                                           │
│    {{@index}}       → Current iteration index (0-based)                    │
│    {{@key}}         → Current key (for objects)                            │
│    {{@first}}       → true on first iteration                              │
│    {{@last}}        → true on last iteration                               │
│    {{this}}         → Current item                                        │
│  {{/each}}                                                                  │
│                                                                             │
│  {{#with object}}                                                          │
│    {{property}}     → Access object.property directly                      │
│  {{/with}}                                                                  │
│                                                                             │
│  {{customHelper}}                                                          │
│    → Custom helper invocation                                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Part 3: Custom Helpers Reference

### 3.1 Date & Time Helpers

```handlebars
{{formatDate date}}
{{formatDate date format="DD MMM YYYY"}}
{{formatDate date format="DD/MM/YYYY" timezone="Asia/Kolkata"}}
```

**Parameters:**
- `date` (Date|string): Date to format
- `format` (string): Format string (default: "DD MMM YYYY")
- `timezone` (string): IANA timezone (default: system timezone)

**Format Tokens:**
| Token | Output | Example |
|-------|--------|---------|
| `DD` | Day with leading zero | 01, 15, 31 |
| `D` | Day without zero | 1, 15, 31 |
| `MMM` | Short month | Jan, Feb, Dec |
| `MMMM` | Full month | January, February |
| `YY` | 2-digit year | 24, 25 |
| `YYYY` | 4-digit year | 2024, 2025 |
| `ddd` | Short weekday | Mon, Tue, Fri |
| `dddd` | Full weekday | Monday, Tuesday |

```handlebars
{{formatTime time}}
{{formatTime time format="HH:mm" timezone="Asia/Dubai"}}
```

**Parameters:**
- `time` (Date|string): Time to format
- `format` (string): Format string (default: "HH:mm")
- `timezone` (string): IANA timezone

```handlebars
{{formatDateTime dateTime}}
{{formatDateTime dateTime format="DD MMM YYYY, HH:mm"}}
```

```handlebars
{{dateRange startDate endDate}}
{{dateRange startDate endDate format="DD MMM" separator=" - "}}
```

**Output examples:**
- `20 Jan 2025 - 25 Jan 2025`
- `20 - 25 Jan 2025`
- `20 Jan - 05 Feb 2025`

```handlebars
{{duration nights days}}
{{duration nights=5 days=6}}
```

**Output:** "5 Nights / 6 Days"

```handlebars
{{timeBetween startDate endDate unit="days"}}
{{timeBetween startDate endDate unit="nights"}}
```

**Parameters:**
- `unit`: "days", "nights", "hours", "minutes"

```handlebars
{{addDays date days=7}}
{{subtractMonths date months=3}}
```

```handlebars
{{isAfter date1 date2}}
{{isBefore date1 date2}}
{{isSameOrAfter date1 date2}}
```

**Returns:** Boolean for conditional use

---

### 3.2 Currency & Number Helpers

```handlebars
{{formatCurrency amount}}
{{formatCurrency amount currency="INR"}}
{{formatCurrency amount currency="USD" locale="en-US"}}
```

**Output examples:**
- `₹1,54,690` (INR, Indian numbering)
- `$1,850.00` (USD, Western numbering)
- `€1.234,56` (EUR, European numbering)

```handlebars
{{formatNumber number}}
{{formatNumber number decimals=0}}
{{formatNumber number decimals=2 locale="en-IN"}}
```

**Indian Numbering System:**
```handlebars
{{formatIndianNumber 1234567}}    → 12,34,567
{{formatIndianNumber 10000000}}   → 1,00,00,000
{{formatIndianNumber 154690 decimals=0}}   → 1,54,690
```

```handlebars
{{convertCurrency amount from="USD" to="INR" rate=83.5}}
{{convertCurrency amount from="EUR" to="USD" rate=1.08}}
```

```handlebars
{{currencySymbol currency}}
{{currencySymbol "INR"}}    → ₹
{{currencySymbol "USD"}}    → $
{{currencySymbol "EUR"}}    → €
```

```handlebars
{{perPerson amount pax=3}}
{{perPerson totalPrice divideBy=3}}
```

**Output:** Formats amount as per-person value

---

### 3.3 String Helpers

```handlebars
{{uppercase string}}
{{lowercase string}}
{{capitalize string}}
{{titleCase string}}
```

```handlebars
{{truncate string length=50}}
{{truncate string length=30 suffix="..."}}
```

```handlebars
{{default value fallback="N/A"}}
{{default customer.gstIn fallback="N/A"}}
```

```handlebars
{{concat string1 string2}}
{{join array separator=", "}}
```

```handlebars
{{replace string search="foo" replace="bar"}}
{{replaceAll string search="foo" replace="bar"}}
```

---

### 3.4 Conditional Helpers

```handlebars
{{eq value1 value2}}
{{eq trip.type "international"}}
{{#if (eq trip.type "international")}}
  <!-- Content for international trips -->
{{/if}}
```

```handlebars
{{ne value1 value2}}
{{gt value1 value2}}
{{gte value1 value2}}
{{lt value1 value2}}
{{lte value1 value2}}
```

```handlebars
{{and condition1 condition2}}
{{or condition1 condition2}}
{{not condition}}
```

```handlebars
{{contains array value}}
{{#if (contains trip.types "honeymoon")}}
  🎊 Honeymoon Special
{{/if}}
```

```handlebars
{{in value array}}
{{#if (eq destination.country (in "UAE" "Singapore" "Thailand"))}}
  Visa required
{{/if}}
```

---

### 3.5 Array Helpers

```handlebars
{{first array count=1}}
{{last array count=3}}
```

```handlebars
{{length array}}
{{length items}}
```

```handlebars
{{sum array property="price"}}
{{avg array property="rating"}}
```

```handlebars
{{filter array by="status" value="confirmed"}}
{{reject array by="status" value="cancelled"}}
```

```handlebars
{{sort array by="date" order="desc"}}
{{sortBy array property="name"}}
```

```handlebars
{{groupBy array by="category"}}
{{countBy array by="type"}}
```

```handlebars
{{slice array start=0 end=5}}
{{paginate array page=1 pageSize=10}}
```

---

### 3.6 Travel-Specific Helpers

```handlebars
{{flightDuration departure arrival}}
{{flightDuration "06:00" "09:30"}}    → 3h 30m
```

```handlebars
{{nightsBetween checkIn checkOut}}
{{nightsBetween "2025-01-20" "2025-01-25"}}    → 5
```

```handlebars
{{ageFromDob dob}}
{{ageFromDob "1990-05-15"}}    → 35
```

```handlebars
{{passportExpiryStatus expiryDate}}
{{passportExpiryStatus "2029-03-15"}}    → Valid
{{passportExpiryStatus "2025-02-01"}}    → Expiring Soon
{{passportExpiryStatus "2024-11-01"}}    → Expired
```

```handlebars
{{visaRequired nationality destination}}
{{visaRequired "IN" "AE"}}    → Yes
{{visaRequired "IN" "NP"}}    → No
```

```handlebars
{{timezoneCode city}}
{{timezoneCode "Dubai"}}    → GST (GMT+4)
{{timezoneCode "New York"}}    → EST (GMT-5)
```

```handlebars
{{airportCode airportName}}
{{airportCode "Dubai International Airport"}}    → DXB
{{airportCode "Indira Gandhi International"}}    → DEL
```

```handlebars
{{airlineName flightCode}}
{{airlineName "6E 1475"}}    → IndiGo
{{airlineName "EK 506"}}     → Emirates
```

---

### 3.7 Conditional Display Helpers

```handlebars
{{statusBadge status}}
{{statusBadge "confirmed"}}    → ✅ Confirmed
{{statusBadge "pending"}}      → ⏳ Pending
{{statusBadge "cancelled"}}    → ❌ Cancelled
```

```handlebars
{{icon type}}
{{icon "flight"}}        → ✈️
{{icon "hotel"}}         → 🏨
{{icon "transfer"}}      → 🚗
{{icon "activity"}}      → 🎫
{{icon "meal"}}          -> 🍽️
```

```handlebars
{{flag countryCode}}
{{flag "IN"}}    → 🇮🇳
{{flag "AE"}}    → 🇦🇪
{{flag "US"}}    → 🇺🇸
{{flag "GB"}}    → 🇬🇧
```

```handlebars
{{rating value max=5}}
{{rating 4.5}}    → ★★★★½
```

```handlebars
{{progress percentage}}
{{progress 75}}    → ████████████████░░░░░░░░ 75%
```

---

### 3.8 Calculation Helpers

```handlebars
{{multiply a b}}
{{divide a b}}
{{add a b}}
{{subtract a b}}
```

```handlebars
{{percentage value total}}
{{percentage 38673 154690}}    → 25
```

```handlebars
{{gst amount rate=18}}
{{gst 100000 rate=18}}    → 18000
```

```handlebars
{{discount amount percentage}}
{{discount 5000 percentage=10}}    → 500
```

```handlebars
{{totalWithTax amount taxRate}}
{{totalWithTax 100000 taxRate=18}}    → 118000
```

---

### 3.9 Validation Helpers

```handlebars
{{isValidEmail email}}
{{isValidPhone phone}}
{{isValidGstin gstin}}
{{isValidPan pan}}
{{isValidPassport passport}}
```

**Returns:** Boolean

```handlebars
{{luhnCheck number}}
{{luhnCheck "4532015112830366"}}    → true (valid credit card)
```

---

### 3.10 Utility Helpers

```handlebars
{{json object}}
{{json bundle pretty=true}}
```

```handlebars
{{log value}}
{{debug context}}
```

```handlebars
{{uniqueId prefix="ref"}}
{{uniqueId}}    → random_abc123
```

```handlebars
{{random min=1 max=100}}
{{oneOf array}}
```

---

## Part 4: Component Library (Partials)

### 4.1 Layout Components

#### Base Layout (`layouts/base.hbs`)

```handlebars
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{title}} | {{agency.name}}</title>
    <style>
        /* CSS will be injected */
        {{{styles}}}
    </style>
</head>
<body>
    <div class="document-container">
        {{#if agency.logo}}
        <div class="agency-header">
            <img src="{{agency.logo}}" alt="{{agency.name}}" class="agency-logo">
        </div>
        {{/if}}

        <main class="document-content">
            {{> @partial-block }}
        </main>

        <footer class="document-footer">
            {{> components/footer}}
        </footer>
    </div>
</body>
</html>
```

#### Quote Layout (`layouts/quote.hbs`)

```handlebars
{{#> layouts/base title="Quote"}}
    {{#> components/header}}
        Quote #{{quoteNumber}}
    {{/components/header}}

    <div class="quote-content">
        {{> sections/customer-info}}
        {{> sections/trip-overview}}
        {{> sections/price-breakdown}}
        {{> sections/inclusions-exclusions}}
        {{> sections/terms-conditions}}
    </div>

    {{#> components/agency-footer}}
        {{agency.name}}
    {{/components/agency-footer}}
{{/layouts/base}}
```

---

### 4.2 Header Components

#### Document Header (`components/header.hbs`)

```handlebars
<header class="doc-header">
    <div class="doc-header__top">
        <div class="doc-header__title">
            <h1>{{@root.title}}</h1>
            {{#if subtitle}}
            <p class="doc-header__subtitle">{{subtitle}}</p>
            {{/if}}
        </div>
        <div class="doc-header__meta">
            {{#if referenceNumber}}
            <div class="meta-item">
                <span class="meta-label">Reference:</span>
                <span class="meta-value">{{referenceNumber}}</span>
            </div>
            {{/if}}
            {{#if date}}
            <div class="meta-item">
                <span class="meta-label">Date:</span>
                <span class="meta-value">{{formatDate date}}</span>
            </div>
            {{/if}}
        </div>
    </div>
</header>
```

#### Customer Header (`components/customer-header.hbs`)

```handlebars
<div class="customer-header">
    <h2>{{title}}</h2>
    <div class="customer-details">
        <div class="customer-name">{{customer.name}}</div>
        {{#if customer.email}}
        <div class="customer-email">{{customer.email}}</div>
        {{/if}}
        {{#if customer.phone}}
        <div class="customer-phone">{{customer.phone}}</div>
        {{/if}}
        {{#if customer.reference}}
        <div class="customer-ref">Ref: {{customer.reference}}</div>
        {{/if}}
    </div>
</div>
```

---

### 4.3 Flight Components

#### Flight Card (`components/flight-card.hbs`)

```handlebars
<div class="flight-card {{#if international}}international{{/if}}">
    <div class="flight-card__header">
        <span class="flight-carrier">{{airline}}</span>
        <span class="flight-number">{{flightNumber}}</span>
    </div>

    <div class="flight-card__route">
        <div class="flight-departure">
            <div class="flight-code">{{from.code}}</div>
            <div class="flight-city">{{from.city}}</div>
            <div class="flight-time">{{formatTime departure format="HH:mm"}}</div>
            {{#if from.terminal}}
            <div class="flight-terminal">Terminal {{from.terminal}}</div>
            {{/if}}
        </div>

        <div class="flight-duration">
            <div class="flight-line"></div>
            <div class="flight-duration-text">{{flightDuration departure arrival}}</div>
            {{#if stops}}
            <div class="flight-stops">{{stops}} stop{{#if (gt stops 1)}}s{{/if}}</div>
            {{else}}
            <div class="flight-stops">Non-stop</div>
            {{/if}}
        </div>

        <div class="flight-arrival">
            <div class="flight-code">{{to.code}}</div>
            <div class="flight-city">{{to.city}}</div>
            <div class="flight-time">{{formatTime arrival format="HH:mm" timezone=to.timezone}}</div>
            {{#if to.terminal}}
            <div class="flight-terminal">Terminal {{to.terminal}}</div>
            {{/if}}
        </div>
    </div>

    <div class="flight-card__footer">
        <div class="flight-class">{{class}}</div>
        <div class="flight-pnr">PNR: {{pnr}}</div>
        {{#if status}}
        <div class="flight-status {{statusClass}}">{{statusBadge status}}</div>
        {{/if}}
    </div>
</div>
```

#### Flight Segment (Simple) (`components/flight-segment.hbs`)

```handlebars
<div class="flight-segment">
    <div class="segment-dep">
        <span class="segment-time">{{depTime}}</span>
        <span class="segment-city">{{depCity}}</span>
        <span class="segment-code">{{depCode}}</span>
    </div>
    <div class="segment-arrow">→</div>
    <div class="segment-arr">
        <span class="segment-time">{{arrTime}}</span>
        <span class="segment-city">{{arrCity}}</span>
        <span class="segment-code">{{arrCode}}</span>
    </div>
</div>
```

---

### 4.4 Hotel Components

#### Hotel Card (`components/hotel-card.hbs`)

```handlebars
<div class="hotel-card">
    <div class="hotel-card__main">
        <div class="hotel-name">{{hotel.name}}</div>
        {{#if hotel.address}}
        <div class="hotel-address">{{hotel.address}}</div>
        {{/if}}
        {{#if hotel.rating}}
        <div class="hotel-rating">
            {{rating hotel.rating max=5}}
            {{#if hotel.category}}
            <span class="hotel-category">{{hotel.category}}</span>
            {{/if}}
        </div>
        {{/if}}
    </div>

    <div class="hotel-card__stay">
        <div class="stay-dates">
            <span class="stay-label">Check-in:</span>
            <span class="stay-value">{{formatDate checkIn format="DD MMM YYYY"}}, {{checkInTime}}</span>
        </div>
        <div class="stay-dates">
            <span class="stay-label">Check-out:</span>
            <span class="stay-value">{{formatDate checkOut format="DD MMM YYYY"}}, {{checkOutTime}}</span>
        </div>
        <div class="stay-nights">{{nightsBetween checkIn checkOut}} Nights</div>
    </div>

    <div class="hotel-card__room">
        <div class="room-type">{{roomType}}</div>
        {{#if bedType}}
        <div class="room-bed">{{bedType}}</div>
        {{/if}}
        {{#if boardBasis}}
        <div class="room-board">{{boardBasis}}</div>
        {{/if}}
    </div>

    <div class="hotel-card__meta">
        {{#if confirmationNumber}}
        <div class="hotel-confirm">
            <span class="confirm-label">Confirmation:</span>
            <span class="confirm-value">{{confirmationNumber}}</span>
        </div>
        {{/if}}
        {{#if paymentStatus}}
        <div class="hotel-payment">
            <span class="payment-label">Payment:</span>
            <span class="payment-value {{paymentStatus}}">{{statusBadge paymentStatus}}</span>
        </div>
        {{/if}}
    </div>
</div>
```

---

### 4.5 Pricing Components

#### Price Table (`components/price-table.hbs`)

```handlebars
<table class="price-table">
    <thead>
        <tr>
            <th>Description</th>
            <th class="text-right">Amount</th>
        </tr>
    </thead>
    <tbody>
        {{#each items}}
        <tr class="price-row">
            <td class="price-desc">
                {{description}}
                {{#if notes}}
                <div class="price-notes">{{notes}}</div>
                {{/if}}
            </td>
            <td class="price-amount">{{formatCurrency amount currency=@root.currency}}</td>
        </tr>
        {{/each}}
    </tbody>
    <tfoot>
        {{#if showTaxBreakdown}}
        <tr class="price-subtotal">
            <td>Subtotal</td>
            <td class="text-right">{{formatCurrency subtotal currency=@root.currency}}</td>
        </tr>
        {{#each taxes}}
        <tr class="price-tax">
            <td>{{name}} ({{rate}}%)</td>
            <td class="text-right">{{formatCurrency amount currency=@root.currency}}</td>
        </tr>
        {{/each}}
        {{/if}}
        <tr class="price-total">
            <td class="total-label">Grand Total</td>
            <td class="total-amount">{{formatCurrency total currency=@root.currency}}</td>
        </tr>
        {{#if perPerson}}
        <tr class="price-perperson">
            <td class="perperson-label">Per Person ({{paxCount}})</td>
            <td class="perperson-amount">{{formatCurrency perPerson currency=@root.currency}}</td>
        </tr>
        {{/if}}
    </tfoot>
</table>
```

#### Price Summary (`components/price-summary.hbs`)

```handlebars
<div class="price-summary">
    <div class="price-summary__row">
        <span class="price-label">Base Cost</span>
        <span class="price-value">{{formatCurrency baseCost currency=currency}}</span>
    </div>
    {{#if taxes}}
    <div class="price-summary__row">
        <span class="price-label">Taxes</span>
        <span class="price-value">{{formatCurrency taxes currency=currency}}</span>
    </div>
    {{/if}}
    {{#if fees}}
    <div class="price-summary__row">
        <span class="price-label">Fees</span>
        <span class="price-value">{{formatCurrency fees currency=currency}}</span>
    </div>
    {{/if}}
    <div class="price-summary__row price-summary__total">
        <span class="price-label total-label">Total</span>
        <span class="price-value total-amount">{{formatCurrency total currency=currency}}</span>
    </div>
</div>
```

---

### 4.6 Itinerary Components

#### Day Card (`components/day-card.hbs`)

```handlebars
<div class="day-card" id="day-{{dayNumber}}">
    <div class="day-card__header">
        <h3 class="day-title">Day {{dayNumber}}</h3>
        {{#if date}}
        <span class="day-date">{{formatDate date format="dddd, DD MMM YYYY"}}</span>
        {{/if}}
        {{#if title}}
        <span class="day-subtitle">{{title}}</span>
        {{/if}}
    </div>

    {{#if description}}
    <p class="day-description">{{description}}</p>
    {{/if}}

    <div class="day-timeline">
        {{#each timeline}}
        {{> components/timeline-item}}
        {{/each}}
    </div>

    {{#if meals}}
    <div class="day-meals">
        {{#if meals.breakfast}}
        <div class="meal-item meal-breakfast">
            <span class="meal-icon">🍳</span>
            <span class="meal-label">Breakfast:</span>
            <span class="meal-value">{{meals.breakfast}}</span>
        </div>
        {{/if}}
        {{#if meals.lunch}}
        <div class="meal-item meal-lunch">
            <span class="meal-icon">🍽️</span>
            <span class="meal-label">Lunch:</span>
            <span class="meal-value">{{meals.lunch}}</span>
        </div>
        {{/if}}
        {{#if meals.dinner}}
        <div class="meal-item meal-dinner">
            <span class="meal-icon">🍽️</span>
            <span class="meal-label">Dinner:</span>
            <span class="meal-value">{{meals.dinner}}</span>
        </div>
        {{/if}}
    </div>
    {{/if}}

    {{#if notes}}
    <div class="day-notes">
        {{#each notes}}
        <p class="note-item">• {{this}}</p>
        {{/each}}
    </div>
    {{/if}}
</div>
```

#### Timeline Item (`components/timeline-item.hbs`)

```handlebars
<div class="timeline-item type-{{type}}">
    <div class="timeline-marker">
        <span class="marker-icon">{{icon type}}</span>
    </div>

    <div class="timeline-content">
        <div class="timeline-time">{{time}}</div>
        <div class="timeline-activity">{{activity}}</div>
        {{#if details}}
        <div class="timeline-details">{{details}}</div>
        {{/if}}
        {{#if location}}
        <div class="timeline-location">📍 {{location}}</div>
        {{/if}}
        {{#if duration}}
        <div class="timeline-duration">⏱️ {{duration}}</div>
        {{/if}}
        {{#if bookingReference}}
        <div class="timeline-ref">Ref: {{bookingReference}}</div>
        {{/if}}
        {{#if status}}
        <div class="timeline-status status-{{status}}">{{statusBadge status}}</div>
        {{/if}}
    </div>
</div>
```

---

### 4.7 Summary Table Components

#### Flights Summary Table (`components/summary-flights.hbs`)

```handlebars
<table class="summary-table summary-flights">
    <thead>
        <tr>
            <th>Route</th>
            <th>Flight</th>
            <th>Date</th>
            <th>Time</th>
            <th>Class</th>
            <th>PNR</th>
            <th>Status</th>
        </tr>
    </thead>
    <tbody>
        {{#each flights}}
        <tr>
            <td>
                <div class="route-display">
                    <span>{{from.code}}</span>
                    <span class="route-arrow">→</span>
                    <span>{{to.code}}</span>
                </div>
            </td>
            <td>{{airline}} {{flightNumber}}</td>
            <td>{{formatDate date format="DD MMM YYYY"}}</td>
            <td>{{formatTime departure format="HH:mm"}}</td>
            <td>{{class}}</td>
            <td><code>{{pnr}}</code></td>
            <td>{{statusBadge status}}</td>
        </tr>
        {{/each}}
    </tbody>
</table>
```

#### Hotels Summary Table (`components/summary-hotels.hbs`)

```handlebars
<table class="summary-table summary-hotels">
    <thead>
        <tr>
            <th>Hotel</th>
            <th>Check-in</th>
            <th>Check-out</th>
            <th>Room</th>
            <th>Ref</th>
            <th>Status</th>
        </tr>
    </thead>
    <tbody>
        {{#each hotels}}
        <tr>
            <td>
                <div class="hotel-name">{{name}}</div>
                {{#if address}}
                <div class="hotel-address-small">{{address}}</div>
                {{/if}}
            </td>
            <td>{{formatDate checkIn format="DD MMM"}}<br>{{checkInTime}}</td>
            <td>{{formatDate checkOut format="DD MMM"}}<br>{{checkOutTime}}</td>
            <td>{{roomType}}</td>
            <td><code>{{confirmationNumber}}</code></td>
            <td>{{statusBadge status}}</td>
        </tr>
        {{/each}}
    </tbody>
</table>
```

---

### 4.8 Contact & Info Components

#### Contact Block (`components/contact-block.hbs`)

```handlebars
<div class="contact-block">
    <h4 class="contact-title">{{title}}</h4>
    <div class="contact-items">
        {{#if phone}}
        <div class="contact-item">
            <span class="contact-icon">📞</span>
            <span class="contact-value">{{phone}}</span>
        </div>
        {{/if}}
        {{#if email}}
        <div class="contact-item">
            <span class="contact-icon">📧</span>
            <span class="contact-value">{{email}}</span>
        </div>
        {{/if}}
        {{#if website}}
        <div class="contact-item">
            <span class="contact-icon">🌐</span>
            <span class="contact-value">{{website}}</span>
        </div>
        {{/if}}
        {{#if address}}
        <div class="contact-item">
            <span class="contact-icon">📍</span>
            <span class="contact-value">{{address}}</span>
        </div>
        {{/if}}
    </div>
</div>
```

#### Important Info Box (`components/important-info.hbs`)

```handlebars
<div class="important-info {{#if (eq type 'warning')}}warning{{/if}}">
    <div class="important-info__icon">
        {{#if (eq type 'warning')}}⚠️{{/if}}
        {{#if (eq type 'info')}}ℹ️{{/if}}
        {{#if (eq type 'success')}}✅{{/if}}
        {{#if (eq type 'error')}}❌{{/if}}
    </div>
    <div class="important-info__content">
        {{#if title}}
        <h4 class="important-info__title">{{title}}</h4>
        {{/if}}
        <div class="important-info__body">
            {{#each items}}
            <p>{{this}}</p>
            {{/each}}
        </div>
    </div>
</div>
```

---

### 4.9 QR & Barcode Components

#### QR Code (`components/qr-code.hbs`)

```handlebars
<div class="qr-code-container">
    <img src="{{qrCodeUrl data}}" alt="QR Code" class="qr-code">
    {{#if label}}
    <div class="qr-label">{{label}}</div>
    {{/if}}
</div>
```

---

### 4.10 Footer Components

#### Document Footer (`components/footer.hbs`)

```handlebars
<footer class="doc-footer">
    <div class="footer-content">
        {{#if @root.agency}}
        <div class="footer-agency">
            {{#if @root.agency.logo}}
            <img src="{{@root.agency.logo}}" alt="{{@root.agency.name}}" class="footer-logo">
            {{/if}}
            {{#if @root.agency.name}}
            <div class="footer-name">{{@root.agency.name}}</div>
            {{/if}}
        </div>
        {{/if}}

        <div class="footer-contact">
            {{#if @root.agency.contact.phone}}
            <div class="footer-contact-item">
                <span class="contact-icon">📞</span>
                <span>{{@root.agency.contact.phone}}</span>
            </div>
            {{/if}}
            {{#if @root.agency.contact.email}}
            <div class="footer-contact-item">
                <span class="contact-icon">📧</span>
                <span>{{@root.agency.contact.email}}</span>
            </div>
            {{/if}}
            {{#if @root.agency.contact.website}}
            <div class="footer-contact-item">
                <span class="contact-icon">🌐</span>
                <span>{{@root.agency.contact.website}}</span>
            </div>
            {{/if}}
        </div>
    </div>

    {{#if generatedAt}}
    <div class="footer-generated">
        Generated on {{formatDateTime generatedAt format="DD MMM YYYY, HH:mm"}}
    </div>
    {{/if}}
</footer>
```

---

## Part 5: Template Data Structure

### 5.1 Quote Data Context

```typescript
interface QuoteTemplateData {
  // Layout
  title: string;
  subtitle?: string;

  // Agency
  agency: {
    name: string;
    logo?: string;
    contact: {
      phone: string;
      email: string;
      website?: string;
      address?: string;
    };
    gstin?: string;
    pan?: string;
  };

  // Document metadata
  quoteNumber: string;
  referenceNumber: string;
  date: Date;
  validFrom: Date;
  validUntil: Date;

  // Customer
  customer: {
    name: string;
    email?: string;
    phone?: string;
    reference?: string;
    gstin?: string;
    pan?: string;
  };

  // Trip
  trip: {
    type: string;
    destination: string;
    destinationCountry?: string;
    duration: number;
    travelDates: {
      from: Date;
      to: Date;
    };
    pax: {
      adults: number;
      children: number;
      infants: number;
      total: number;
    };
  };

  // Pricing
  pricing: {
    currency: string;
    baseCost: number;
    taxes: number;
    fees: number;
    total: number;
    perPerson?: number;
    breakdown: PricingItem[];
  };

  // Items (for detailed breakdown)
  items?: {
    flights?: FlightItem[];
    hotels?: HotelItem[];
    transfers?: TransferItem[];
    activities?: ActivityItem[];
  };

  // Inclusions/Exclusions
  inclusions: string[];
  exclusions: string[];

  // Terms
  terms: {
    validityNote: string;
    cancellationPolicy: string;
    paymentSchedule: string[];
    modificationPolicy: string;
  };
}
```

### 5.2 Itinerary Data Context

```typescript
interface ItineraryTemplateData {
  // Layout
  title: string;

  // Agency (same as Quote)
  agency: AgencyInfo;

  // Document metadata
  itineraryNumber: string;
  bookingReference: string;
  bookingDate: Date;
  generatedAt: Date;

  // Customer
  customer: {
    name: string;
    email?: string;
    phone?: string;
    emergencyContact?: {
      name: string;
      relationship: string;
      phone: string;
    };
  };

  // Travelers (with passport details)
  travelers: {
    name: string;
    type: 'adult' | 'child' | 'infant';
    passport?: {
      number: string;
      expiry: Date;
      issueDate?: Date;
    };
    dob?: Date;
  }[];

  // Trip summary
  trip: {
    name: string;
    destination: string;
    type: string;
    duration: number;
    travelDates: {
      from: Date;
      to: Date;
    };
    pax: PaxSummary;
  };

  // Detailed itinerary
  days: ItineraryDay[];

  // Summary tables
  summary: {
    flights: FlightSummary[];
    hotels: HotelSummary[];
    transfers: TransferSummary[];
    activities: ActivitySummary[];
  };

  // Important information
  importantInfo: {
    visaRequirements?: VisaInfo;
    insurance?: InsuranceInfo;
    weather?: WeatherInfo;
    currency?: CurrencyInfo;
    language?: string[];
    emergencyContacts: EmergencyContact[];
    packingTips?: string[];
  };

  // Vendor contacts
  vendorContacts: VendorContact[];
}
```

### 5.3 Invoice Data Context

```typescript
interface InvoiceTemplateData {
  // Layout
  title: string;

  // Agency
  agency: {
    name: string;
    logo?: string;
    address: string;
    gstin: string;
    pan: string;
    state: string;
    stateCode: string;
  };

  // Document metadata
  invoiceNumber: string;
  invoiceType: 'PROFORMA' | 'TAX_INVOICE' | 'COMMERCIAL';
  invoiceDate: Date;
  dueDate?: Date;

  // Billing
  billTo: {
    name: string;
    address: string;
    gstin?: string;
    pan?: string;
    phone: string;
    email: string;
  };

  // Trip reference
  tripReference: {
    bookingNumber: string;
    itineraryNumber?: string;
    destination: string;
    travelDates: string;
  };

  // Line items
  items: {
    srNo: number;
    description: string;
    sacCode?: string;
    quantity: number;
    unit: string;
    unitPrice: number;
    taxableValue: number;
    taxRate?: number;
    taxAmount?: number;
    total: number;
  }[];

  // Tax summary
  taxSummary: {
    cgst?: { rate: number; amount: number };
    sgst?: { rate: number; amount: number };
    igst?: { rate: number; amount: number };
    totalTax: number;
  };

  // Payment summary
  paymentSummary: {
    totalInvoiceValue: number;
    amountPaid: number;
    amountDue: number;
    paymentStatus: 'PAID' | 'PARTIAL' | 'PENDING';
  };

  // Payment details
  paymentDetails?: {
    bankName: string;
    accountNumber: string;
    accountName: string;
    ifscCode: string;
    branch: string;
    upiId?: string;
  };

  // Terms
  terms: string[];

  // Signatory
  authorizedSignatory: {
    name: string;
    designation: string;
  };
}
```

---

## Part 6: Best Practices

### 6.1 Template Design Principles

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      TEMPLATE DESIGN PRINCIPLES                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. MODULARITY                                                              │
│  ────────────────────────────────────────────────────────────────────────  │
│  • Break down into reusable components                                     │
│  • Each partial should have a single responsibility                        │
│  • Use partials for repeated UI patterns                                   │
│                                                                             │
│  2. SEPARATION OF CONCERNS                                                 │
│  ────────────────────────────────────────────────────────────────────────  │
│  • Layout: Structure and wrapper                                           │
│  • Component: Reusable UI elements                                         │
│  • Section: Content blocks specific to document type                       │
│  • Helper: Business logic and formatting                                   │
│                                                                             │
│  3. DEFENSIVE TEMPLATING                                                   │
│  ────────────────────────────────────────────────────────────────────────  │
│  • Always check for existence before accessing properties                   │
│  • Use {{default}} helper for optional values                              │
│  • Provide fallbacks for arrays and objects                                │
│                                                                             │
│  4. ACCESSIBILITY                                                           │
│  ────────────────────────────────────────────────────────────────────────  │
│  • Use semantic HTML elements                                              │
│  • Include proper alt text for images                                      │
│  • Ensure sufficient color contrast                                        │
│  • Use table headers for data tables                                       │
│                                                                             │
│  5. PRINT OPTIMIZATION                                                     │
│  ────────────────────────────────────────────────────────────────────────  │
│  • Use CSS print media queries                                             │
│  • Avoid page breaks inside components                                     │
│  • Test print output regularly                                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Common Patterns

#### Pattern 1: Optional Field Display

```handlebars
{{!-- GOOD: Using default helper --}}
<div class="customer-gst">
  GSTIN: {{default customer.gstin fallback="N/A"}}
</div>

{{!-- GOOD: Using if/else --}}
{{#if customer.gstIn}}
  <div class="customer-gst">GSTIN: {{customer.gstIn}}</div>
{{/if}}

{{!-- AVOID: Direct access without check --}}
<div class="customer-gst">GSTIN: {{customer.gstIn}}</div>
```

#### Pattern 2: Conditional List Rendering

```handlebars
{{!-- GOOD: Check array before iterating --}}
{{#if (gt items.length 0)}}
  <ul class="items-list">
    {{#each items}}
    <li>{{this}}</li>
    {{/each}}
  </ul>
{{else}}
  <p>No items available</p>
{{/if}}

{{!-- GOOD: Using custom helper --}}
{{#if (notEmpty items)}}
  <!-- render items -->
{{/if}}
```

#### Pattern 3: Nested Object Access

```handlebars
{{!-- GOOD: Use with for context --}}
{{#with customer.address}}
  <div class="address">
    {{street}}, {{city}} - {{pincode}}
    {{#if state}}, {{state}}{{/if}}
  </div>
{{/with}}

{{!-- GOOD: Explicit path --}}
<div class="address">
  {{customer.address.street}}, {{customer.address.city}}
</div>
```

#### Pattern 4: Loop Indexing

```handlebars
{{!-- GOOD: Using @index --}}
{{#each days}}
  <div class="day-number">Day {{add @index 1}}</div>
{{/each}}

{{!-- GOOD: Adding custom index to data --}}
{{#each days}}
  <div class="day-number">Day {{dayNumber}}</div>
{{/each}}
```

### 6.3 Performance Guidelines

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        PERFORMANCE GUIDELINES                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DO:                                                                        │
│  • Pre-compile templates for reuse                                         │
│  • Cache compiled templates in memory                                       │
│  • Use partials for repeated content                                        │
│  • Minimize nested iterations                                               │
│  • Use pagination for large arrays                                          │
│                                                                             │
│  DON'T:                                                                      │
│  • Compile templates on every request                                       │
│  • Create deeply nested iterations (3+ levels)                              │
│  • Put complex logic in templates (move to helpers)                         │
│  • Use expensive helpers in loops                                           │
│  • Include unnecessary data in context                                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Part 7: Helper Registration

### 7.1 Registration Pattern

```typescript
// helpers/date.ts
import { HelperDelegate } from 'handlebars';

export const formatDate: HelperDelegate = function(
  date: Date | string,
  options?: { hash?: { format?: string; timezone?: string } }
): string {
  const format = options?.hash?.format || 'DD MMM YYYY';
  const timezone = options?.hash?.timezone;
  // Implementation...
  return formattedDate;
};

// helpers/index.ts
import { formatDate, formatTime, formatDateTime } from './date';
import { formatCurrency, formatIndianNumber } from './currency';
// ... other helpers

export function registerHelpers(handlebars: typeof Handlebars): void {
  // Date helpers
  handlebars.registerHelper('formatDate', formatDate);
  handlebars.registerHelper('formatTime', formatTime);
  handlebars.registerHelper('formatDateTime', formatDateTime);

  // Currency helpers
  handlebars.registerHelper('formatCurrency', formatCurrency);
  handlebars.registerHelper('formatIndianNumber', formatIndianNumber);

  // ... more helpers
}
```

### 7.2 Custom Helper Template

```typescript
// Helper template for new travel-specific helpers
import { HelperDelegate } from 'handlebars';

interface HelperOptions {
  hash?: Record<string, any>;
}

export const yourCustomHelper: HelperDelegate = function(
  value: any,
  options?: HelperOptions
): string {
  // Extract named parameters from options.hash
  const param1 = options?.hash?.param1;
  const param2 = options?.hash?.param2;

  // Your logic here
  const result = processValue(value, param1, param2);

  // Return string for template rendering
  return String(result);
};
```

---

## Part 8: Testing Templates

### 8.1 Template Test Structure

```typescript
// tests/templates/quote.test.ts
import { compileTemplate } from '@/lib/template-engine';
import { QuoteTemplateData } from '@/types/template-data';

describe('Quote Template', () => {
  const mockData: QuoteTemplateData = {
    // Full mock data
  };

  it('renders customer name', () => {
    const html = compileTemplate('quote', mockData);
    expect(html).toContain('Rajesh Kumar');
  });

  it('formats currency correctly', () => {
    const html = compileTemplate('quote', mockData);
    expect(html).toContain('₹1,54,690');
  });

  it('renders all pricing items', () => {
    const html = compileTemplate('quote', mockData);
    expect(html).toContain('Flights');
    expect(html).toContain('Hotels');
    expect(html).toContain('Transfers');
  });

  it('handles missing optional fields', () => {
    const dataWithoutGst = { ...mockData, customer: { ...mockData.customer, gstin: undefined } };
    const html = compileTemplate('quote', dataWithoutGst);
    expect(html).toContain('GSTIN: N/A');
  });
});
```

### 8.2 Snapshot Testing

```typescript
it('matches snapshot for standard quote', () => {
  const html = compileTemplate('quote', mockData);
  expect(html).toMatchSnapshot();
});
```

---

## Part 9: Troubleshooting

### 9.1 Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| **Data not rendering** | Path mismatch | Check nested property path, use `{{log}}` to debug |
| **HTML escaped** | Auto-escaping behavior | Use `{{{triple}}}` braces for raw HTML |
| **Helper not found** | Not registered | Check helper registration order |
| **Partial not found** | Path incorrect | Use absolute path or register with name |
| **Date formatting wrong** | Invalid date string | Ensure ISO format or Date object |
| **Currency symbols wrong** | Locale mismatch | Specify locale parameter explicitly |
| **Page breaks bad** | CSS print issue | Use `page-break-inside: avoid` on components |
| **QR code broken** | Data too large | Limit data length, use URL instead |

### 9.2 Debug Mode

```handlebars
{{!-- Debug: Print entire context --}}
{{log this}}

{{!-- Debug: Print specific value --}}
{{log customer}}

{{!-- Debug: Print with label --}}
{{log "Customer name:" customer.name}}
```

---

## Summary

This reference provides:

1. **Template System Overview** — Handlebars engine with custom extensions
2. **Syntax Reference** — Basic Handlebars syntax and built-in helpers
3. **Custom Helpers** — 50+ travel-specific helpers for dates, currency, formatting
4. **Component Library** — Reusable partials for all common UI patterns
5. **Data Structures** — Complete TypeScript interfaces for template contexts
6. **Best Practices** — Design principles, common patterns, performance
7. **Helper Registration** — Pattern for adding custom helpers
8. **Testing** — Unit test patterns for templates
9. **Troubleshooting** — Common issues and solutions

**Next Document**: OUTPUT_13_API_SPECIFICATION_COMPLETE.md — Complete API specification for bundle generation endpoints

---

**Document**: OUTPUT_12_TEMPLATE_REFERENCE_COMPLETE.md
**Series**: Output Panel & Bundle Generation Deep Dive
**Status**: ✅ Complete
**Last Updated**: 2026-04-23
