# Output Panel: Template System Deep Dive

> Template architecture, inheritance, customization, and branding

---

## Part 1: Template Philosophy

### 1.1 The Template Challenge

**Problem:** Travel agencies need professional documents that:
- Reflect their brand identity
- Vary by trip type and customer segment
- Stay consistent across all agents
- Can be updated centrally
- Allow for customizations when needed

**Traditional Approaches Fail:**
- **Rigid Templates:** Can't adapt to different needs
- **Fully Custom:** No brand consistency
- **Manual Files:** Version control nightmares
- **Design Software:** Requires specialist skills

### 1.2 Our Template Philosophy

```
Core Principles:

1. Brand First
   - Agency identity is non-negotiable
   - Logo, colors, typography locked
   - Agents can't break brand

2. Flexible Structure
   - Same template, multiple layouts
   - Optional sections show/hide based on context
   - Responsive to data availability

3. Inheritance Over Duplication
   - Base template contains brand essentials
   - Child templates inherit and extend
   - Update once, propagate everywhere

4. Progressive Enhancement
   - Start with agency default
   - Allow trip-type specific overrides
   - Enable one-off customizations

5. Preview-Driven
   - See changes instantly
   - Test before finalizing
   - Rollback if needed
```

---

## Part 2: Template Architecture

### 2.1 Template Inheritance Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                    SYSTEM BASE TEMPLATE                     │
│  (Platform defaults, core components, helper functions)     │
└────────────────────────┬────────────────────────────────────┘
                         │ inherits
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                     AGENCY MASTER TEMPLATE                  │
│  (Agency brand: logo, colors, fonts, footer, disclaimers)   │
└────────────────────────┬────────────────────────────────────┘
                         │ inherits
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   BUNDLE TYPE TEMPLATES                     │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐       │
│  │   Quote      │ │  Itinerary   │ │   Voucher    │       │
│  │  Template    │ │  Template    │ │  Template    │       │
│  └──────────────┘ └──────────────┘ └──────────────┘       │
└────────────────────────┬────────────────────────────────────┘
                         │ inherits
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                 TRIP TYPE VARIANTS                          │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐       │
│  │  Honeymoon   │ │  Adventure   │ │   Luxury     │       │
│  │    Quote     │ │    Quote     │ │    Quote     │       │
│  └──────────────┘ └──────────────┘ └──────────────┘       │
└────────────────────────┬────────────────────────────────────┘
                         │ can override
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  ONE-OFF CUSTOMIZATIONS                     │
│  (Per-bundle overrides, saved as new version if reused)     │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Template File Structure

```
templates/
├── system/
│   ├── base/
│   │   ├── layout.html              # Master layout
│   │   ├── components/
│   │   │   ├── header.html
│   │   │   ├── pricing-table.html
│   │   │   ├── itinerary-timeline.html
│   │   │   └── footer.html
│   │   └── helpers/
│   │       ├── currency.js
│   │       ├── date-format.js
│   │       └── conditional-render.js
│   └── defaults/
│       ├── quote-default.html
│       ├── itinerary-default.html
│       └── voucher-default.html
│
├── agency/
│   └── {agency_id}/
│       ├── master.html              # Agency brand template
│       ├── brand-assets/
│       │   ├── logo.svg
│       │   ├── colors.css
│       │   └── fonts.css
│       ├── overrides/
│       │   ├── components/
│       │   └── styles.css
│       └── variants/
│           ├── quote-honeymoon.html
│           ├── quote-adventure.html
│           └── quote-luxury.html
│
└── custom/
    └── {bundle_id}/
        └── custom.html              # One-off customization
```

### 2.3 Template Resolution Order

When rendering a bundle:

```
1. Check for one-off customization (custom/{bundle_id})
   └─ If found: Use this, skip to step 6

2. Check for trip-type variant (agency/{agency_id}/variants/)
   └─ If found: Load as base

3. Check for bundle-type template (agency/{agency_id}/)
   └─ If found: Load as base

4. Fall back to system default (system/defaults/)
   └─ Always exists: Use as base

5. Apply agency master template (agency/{agency_id}/master.html)
   └─ Override brand elements

6. Apply system base template (system/base/layout.html)
   └─ Apply final layout structure

7. Render with bundle data
```

---

## Part 3: Template Syntax & Features

### 3.1 Handlebars-Based Syntax

```handlebars
{{! system/base/layout.html }}

<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{{agency.name}} - {{destination}} {{bundle_type}}</title>
    <style>
        {{#if agency.custom_css}}
            {{agency.custom_css}}
        {{else}}
            {{> system_default_styles}}
        {{/if}}
    </style>
</head>
<body>
    {{#if agency.logo}}
        <div class="brand-logo">
            <img src="{{agency.logo}}" alt="{{agency.name}}">
        </div>
    {{/if}}

    {{> @partial-block }}
</body>
</html>
```

### 3.2 Built-in Helpers

| Helper | Syntax | Purpose |
|--------|--------|---------|
| **currency** | `{{currency price}}` | Format with symbol |
| **date** | `{{date startDate 'DD MMM YYYY'}}` | Format dates |
| **plural** | `{{plural count 'night' 'nights'}}` | Pluralize words |
| **percent** | `{{percent value}}` | Format as percentage |
| **cond** | `{{cond condition 'yes' 'no'}}` | Ternary operator |
| **lookup** | `{{lookup items 'id'}}` | Find in array |
| **sum** | `{{sum items 'price'}}` | Sum property |
| **avg** | `{{avg ratings 'score'}}` | Average property |

### 3.3 Conditional Rendering

```handlebars
{{!-- Show section only if data exists --}}
{{#if customer.phone}}
    <div class="contact-phone">
        Phone: {{customer.phone}}
    </div>
{{/if}}

{{!-- Show different content for different trip types --}}
{{#if (eq trip.type 'honeymoon')}}
    <div class="honeymoon-special">
        Complimentary champagne on arrival!
    </div>
{{else if (eq trip.type 'adventure')}}
    <div class="adventure-note">
        Travel insurance mandatory
    </div>
{{/if}}

{{!-- Loop through items --}}
{{#each itinerary.days}}
    <div class="day-item">
        <h3>Day {{@index}}: {{title}}</h3>
        {{#if activities}}
            <ul>
                {{#each activities}}
                    <li>{{this}}</li>
                {{/each}}
            </ul>
        {{/if}}
    </div>
{{/each}}
```

### 3.4 Component System

```handlebars
{{!-- Use a component --}}
{{> pricing_table
    data=pricing
    currency=currency
    show_taxes=true
    show_disclaimers=true
}}

{{!-- Component with custom content --}}
{{> section_wrapper
    title='Flight Details'
    color='primary'
}}
    <div class="flight-info">
        {{flight.airline}} {{flight.number}}
    </div>
{{/section_wrapper}}
```

---

## Part 4: Brand Customization

### 4.1 Brand Identity Elements

| Element | Template Variable | Override Level |
|---------|-------------------|----------------|
| **Logo** | `agency.logo` | Agency master |
| **Primary Color** | `agency.colors.primary` | Agency master |
| **Secondary Color** | `agency.colors.secondary` | Agency master |
| **Font Family** | `agency.typography.font_family` | Agency master |
| **Font Sizes** | `agency.typography.sizes` | Agency master |
| **Spacing** | `agency.layout.spacing` | Agency master |
| **Footer Text** | `agency.footer.text` | Agency master |
| **Disclaimer** | `agency.legal.disclaimer` | Agency master |

### 4.2 Brand Token System

```css
/* agency/{agency_id}/brand-assets/colors.css */

:root {
    /* Brand Colors */
    --brand-primary: {{agency.colors.primary}};
    --brand-secondary: {{agency.colors.secondary}};
    --brand-accent: {{agency.colors.accent}};

    /* Derived Colors */
    --brand-primary-light: color-mix(
        in oklch,
        var(--brand-primary) 80%,
        white 20%
    );
    --brand-primary-dark: color-mix(
        in oklch,
        var(--brand-primary) 80%,
        black 20%
    );

    /* Neutral Palette (tinted toward brand) */
    --neutral-50: oklch(98% 0.005 {{agency.colors.primary_hue}});
    --neutral-100: oklch(95% 0.008 {{agency.colors.primary_hue}});
    --neutral-200: oklch(90% 0.01 {{agency.colors.primary_hue}});
    --neutral-300: oklch(80% 0.015 {{agency.colors.primary_hue}});
    --neutral-400: oklch(65% 0.02 {{agency.colors.primary_hue}});
    --neutral-500: oklch(50% 0.025 {{agency.colors.primary_hue}});
    --neutral-600: oklch(40% 0.03 {{agency.colors.primary_hue}});
    --neutral-700: oklch(30% 0.035 {{agency.colors.primary_hue}});
    --neutral-800: oklch(20% 0.04 {{agency.colors.primary_hue}});
    --neutral-900: okolch(10% 0.045 {{agency.colors.primary_hue}});

    /* Semantic Colors */
    --color-text: var(--neutral-700);
    --color-text-muted: var(--neutral-500);
    --color-bg: var(--neutral-50);
    --color-bg-card: white;
    --color-border: var(--neutral-200);
    --color-accent: var(--brand-primary);
    --color-accent-hover: var(--brand-primary-dark);
}
```

### 4.3 Typography System

```css
/* agency/{agency_id}/brand-assets/fonts.css */

:root {
    /* Font Families */
    --font-display: '{{agency.typography.display_font}}', system-ui;
    --font-body: '{{agency.typography.body_font}}', system-ui;
    --font-mono: '{{agency.typography.mono_font}}', monospace;

    /* Type Scale */
    --text-xs: clamp(0.75rem, 0.7rem + 0.25vw, 0.875rem);
    --text-sm: clamp(0.875rem, 0.8rem + 0.375vw, 1rem);
    --text-base: clamp(1rem, 0.9rem + 0.5vw, 1.125rem);
    --text-lg: clamp(1.125rem, 1rem + 0.625vw, 1.25rem);
    --text-xl: clamp(1.25rem, 1.1rem + 0.75vw, 1.5rem);
    --text-2xl: clamp(1.5rem, 1.25rem + 1.25vw, 2rem);
    --text-3xl: clamp(1.875rem, 1.5rem + 1.875vw, 2.5rem);
    --text-4xl: clamp(2.25rem, 1.75rem + 2.5vw, 3rem);

    /* Font Weights */
    --font-light: 300;
    --font-normal: 400;
    --font-medium: 500;
    --font-semibold: 600;
    --font-bold: 700;

    /* Line Heights */
    --leading-tight: 1.25;
    --leading-normal: 1.5;
    --leading-relaxed: 1.75;
    --leading-loose: 2;
}
```

### 4.4 Logo Management

```handlebars
{{!-- Logo component with fallbacks --}}

<div class="brand-header">
    {{#if agency.logo.svg}}
        {{!-- SVG logo: preferred for quality --}}
        <img
            class="brand-logo"
            src="{{agency.logo.svg}}"
            alt="{{agency.name}}"
            width="{{agency.logo.width}}"
            height="{{agency.logo.height}}"
        >
    {{else if agency.logo.png}}
        {{!-- PNG fallback --}}
        <img
            class="brand-logo"
            src="{{agency.logo.png}}"
            alt="{{agency.name}}"
            width="{{agency.logo.width}}"
            height="{{agency.logo.height}}"
        >
    {{else}}
        {{!-- Text fallback --}}
        <div class="brand-logo-text">
            {{agency.name}}
        </div>
    {{/if}}
</div>
```

---

## Part 5: Template Variants

### 5.1 Trip-Type Variants

```
Variants inherit from bundle-type template
and modify for specific trip characteristics.

┌─────────────────────────────────────────────────────────────┐
│                    QUOTE TEMPLATE                          │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  Honeymoon   │ │  Adventure   │ │   Luxury     │
│    Quote     │ │    Quote     │ │    Quote     │
│              │ │              │ │              │
│ • Romantic   │ │ • Activity   │ │ • Premium    │
│   imagery    │ │   focus      │ │   materials  │
│ • Couple     │ │ • Safety     │ │ • Exclusive  │
│   language   │ │   emphasis   │ │   benefits   │
│ • Special    │ │ • Gear list  │ │ • Concierge  │
│   offers     │ │ • Fitness    │ │   services   │
│              │ │   notes      │ │              │
└──────────────┘ └──────────────┘ └──────────────┘
```

### 5.2 Seasonal Variants

```
Templates can adapt to seasons:

┌─────────────────────────────────────────────────────────────┐
│                     SEASONAL THEMES                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Summer (Apr-Jun)    Monsoon (Jul-Sep)    Winter (Oct-Mar)  │
│  ┌──────────────┐   ┌──────────────┐    ┌──────────────┐   │
│  │ Beach themes │   │ Rain-ready   │    │ Snow/mountain │   │
│  │ Bright colors│   │ Indoor opts  │    │ Cozy vibes    │   │
│  │ Sun safety   │   │ Flexibility  │    │ Warm tones    │   │
│  └──────────────┘   └──────────────┘    └──────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 5.3 Customer Segment Variants

```
Templates adapt to customer type:

┌─────────────────────────────────────────────────────────────┐
│                   CUSTOMER SEGMENTS                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Family              Corporate               Couples        │
│  ┌──────────────┐   ┌──────────────┐     ┌──────────────┐ │
│  │ Kid-friendly │   │ Invoice #    │     │ Romantic     │ │
│  │ Safety info  │   │ Cost codes   │     │ Intimate     │ │
│  │ Activities   │   │ Approval flow│     │ Experiences  │ │
│  │ Room types   │   │ Policy ref   │     │ Privacy      │ │
│  └──────────────┘   └──────────────┘     └──────────────┘ │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Part 6: Template Editor

### 6.1 Editor Interface

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Template Editor: Agency Master                                  [Save] │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────┐  ┌───────────────────────────────────────────┐  │
│  │   ELEMENTS      │  │  EDITOR                                  │  │
│  │                 │  │                                           │  │
│  │  Brand          │  │  ┌─────────────────────────────────────┐ │  │
│  │  ├─ Logo        │  │  │ <div class="brand-header">           │ │  │
│  │  ├─ Colors      │  │  │   {{#if agency.logo}}               │ │  │
│  │  └─ Typography  │  │  │     <img src="{{agency.logo}}"      │ │  │
│  │                 │  │  │          alt="{{agency.name}}">     │ │  │
│  │  Layout         │  │  │   {{else}}                          │ │  │
│  │  ├─ Header      │  │  │     <div class="brand-logo-text">   │ │  │
│  │  ├─ Sections    │  │  │       {{agency.name}}              │ │  │
│  │  └─ Footer      │  │  │     </div>                         │ │  │
│  │                 │  │  │   {{/if}}                          │ │  │
│  │  Content        │  │  │ </div>                              │ │  │
│  │  ├─ Pricing     │  │  │                                     │ │  │
│  │  ├─ Itinerary   │  │  │                                     │ │  │
│  │  └─ Terms       │  │  │                                     │ │  │
│  │                 │  │  └─────────────────────────────────────┘ │  │
│  │  [+ Add]        │  │                                           │  │
│  │                 │  │  [Variables Guide] [Helper Reference]     │  │
│  └─────────────────┘  └───────────────────────────────────────────┘  │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  [Preview] [Test Data] [Version History] [Publish]              │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Visual Template Builder

For non-technical users:

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Visual Template Builder                                        [Save] │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Drag elements to build your template:                                │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                                                                  │   │
│  │  ┌──────────────────────────────────────────────────────────┐  │   │
│  │  │                    YOUR QUOTE                            │  │   │
│  │  │                                                            │  │   │
│  │  │  ┌──────────────────────────────────────────────────┐    │  │   │
│  │  │  │ 📋 LOGO                  [Position] [Size]       │    │  │   │
│  │  │  └──────────────────────────────────────────────────┘    │  │   │
│  │  │                                                            │  │   │
│  │  │  ┌──────────────────────────────────────────────────┐    │  │   │
│  │  │  │ 📄 TITLE                 [Edit Text] [Style]     │    │  │   │
│  │  │  │    Thailand Honeymoon Package                     │    │  │   │
│  │  │  └──────────────────────────────────────────────────┘    │  │   │
│  │  │                                                            │  │   │
│  │  │  ┌──────────────────────────────────────────────────┐    │  │   │
│  │  │  │ 👤 CUSTOMER DETAILS      [+ Section] [- Remove]  │    │  │   │
│  │  │  └──────────────────────────────────────────────────┘    │  │   │
│  │  │                                                            │  │   │
│  │  │  ┌──────────────────────────────────────────────────┐    │  │   │
│  │  │  │ 💰 PRICING               [Reorder] [Customize]   │    │  │   │
│  │  │  └──────────────────────────────────────────────────┘    │  │   │
│  │  │                                                            │  │   │
│  │  │  [+ ADD SECTION]                                         │  │   │
│  │  │                                                            │  │   │
│  │  └────────────────────────────────────────────────────────┘  │   │
│  │                                                                  │   │
│  │  [Drag new sections here]                                       │   │
│  │                                                                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  Available Sections:                                                   │
│  [Pricing Table] [Itinerary] [Flight Details] [Hotel Info]             │
│  [Inclusions] [Exclusions] [Terms] [Map] [Gallery]                     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 6.3 Template Testing

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Test Template: Agency Master Quote                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Select test data scenario:                                           │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  ○ Honeymoon - Thailand - 2 Adults - ₹2,00,000                │   │
│  │  ○ Adventure - Ladakh - 4 Friends - ₹1,50,000                │   │
│  │  ○ Family - Dubai - 2 Adults 2 Kids - ₹3,00,000             │   │
│  │  ○ Corporate - Goa - 10 People - ₹5,00,000                  │   │
│  │  ○ Custom Data...                                              │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  [Test All Scenarios] [Test Edge Cases] [Validate Syntax]              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Part 7: Template Versioning

### 7.1 Version Control System

```
Template Version History:

┌─────────────────────────────────────────────────────────────┐
│  Agency Master Quote Template                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  v2.1  Current  │ Apr 23, 2026  │ Active                    │
│                 │               │ Added GST breakdown        │
│  ├─ v2.0        │ Apr 10, 2026  │ Redesigned pricing table   │
│  ├─ v1.3        │ Mar 15, 2026  │ Fixed footer alignment     │
│  ├─ v1.2        │ Feb 28, 2026  │ Added WhatsApp button      │
│  ├─ v1.1        │ Feb 10, 2026  │ Updated disclaimer         │
│  └─ v1.0        │ Jan 01, 2026  │ Initial version            │
│                                                              │
│  [Rollback to v2.0] [Compare with v1.0] [Create Draft]       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 Draft & Publishing Workflow

```
┌─────────────────────────────────────────────────────────────┐
│  Template Workflow                                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Draft ──► Review ──► Approved ──► Published ──► Active      │
│   │          │           │             │                    │
│   │          │           │             └─► All new bundles │
│   │          │           │                 use this version │
│   │          │           │                                  │
│   │          │           └─► Scheduled publish              │
│   │          │                                          (set date) │
│   │          │                                             │
│   │          └─► Request changes                            │
│   │                                                          │
│   └─► Edit, test, preview                                  │
│      (only visible to editor)                              │
│                                                              │
│  Existing bundles: Continue with their version              │
│  New bundles: Use published version                          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 7.3 Template Rollback

```
Scenarios requiring rollback:

1. Critical Bug
   - Pricing calculation error
   - Missing legal disclaimer
   - Broken layout

2. Brand Issue
   - Wrong logo displayed
   - Color mismatch
   - Typography error

3. Content Error
   - Outdated terms
   - Wrong contact info
   - Inaccurate information

Rollback Process:
1. Select previous version
2. Preview to verify
3. One-click rollback
4. All new bundles use rolled-back version
5. Existing bundles unaffected
```

---

## Part 8: Template Marketplace

### 8.1 Template Library

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Template Marketplace                                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Browse by category:                                                   │
│  [All] [Quote] [Itinerary] [Voucher] [Invoice] [Custom]               │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  ┌────────────────────┐  ┌────────────────────┐                │   │
│  │  │                    │  │                    │                │   │
│  │  │  ✨ MODERN MINIMAL  │  │  🏝️ TROPICAL VIBES│                │   │
│  │  │                    │  │                    │                │   │
│  │  │  Clean, professional│  │  Vibrant colors,   │                │   │
│  │  │  design for         │  │  beach themes      │                │   │
│  │  │  premium packages   │  │                    │                │   │
│  │  │                    │  │                    │                │   │
│  │  │  [Preview] [Use]    │  │  [Preview] [Use]   │                │   │
│  │  │                     │  │                    │                │   │
│  │  └────────────────────┘  └────────────────────┘                │   │
│  │                                                                  │   │
│  │  ┌────────────────────┐  ┌────────────────────┐                │   │
│  │  │                    │  │                    │                │   │
│  │  │  💎 LUXURY GOLD     │  │  🎒 ADVENTURE PRO  │                │   │
│  │  │                    │  │                    │                │   │
│  │  │  Elegant design     │  │  Activity-focused  │                │   │
│  │  │  with gold accents  │  │  with bold layouts │                │   │
│  │  │                    │  │                    │                │   │
│  │  │  [Preview] [Use]    │  │  [Preview] [Use]   │                │   │
│  │  │                     │  │                    │                │   │
│  │  └────────────────────┘  └────────────────────┘                │   │
│  │                                                                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  [Load More]                                                           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 8.2 Template Customization Levels

| Level | Description | Use Case |
|-------|-------------|----------|
| **As-Is** | Use marketplace template directly | Quick start, brand-neutral |
| **Brand-Apply** | Apply agency brand to marketplace template | Professional look, fast setup |
| **Modify** | Customize layout and sections | Tailored to agency needs |
| **Create** | Build from scratch | Complete customization |

### 8.3 Template Sharing

```
Agency-to-agency template sharing:

┌─────────────────────────────────────────────────────────────┐
│  Share Template: Honeymoon Quote                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Share your template with other agencies:                   │
│                                                              │
│  ○ Private - Only my agency                                 │
│  ○ Organization - My agency network                         │
│  ○ Public - Template marketplace (earn royalties)            │
│                                                              │
│  Royalty settings (Public templates):                       │
│  - Free: Share for brand visibility                         │
│  - Paid: Earn ₹X per use                                    │
│  - Custom: Negotiate per-license                            │
│                                                              │
│  [Publish to Marketplace]                                    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Part 9: Template Performance

### 9.1 Caching Strategy

```
Template Caching Layers:

┌─────────────────────────────────────────────────────────────┐
│  Cache Layer 1: Compiled Templates                          │
│  ─────────────────────────────────────────                  │
│  Store: Memory (Redis)                                      │
│  TTL: 24 hours                                              │
│  Invalidation: Template update                              │
│  Purpose: Skip Handlebars compilation                       │
│                                                              │
│  Cache Layer 2: Rendered Output                             │
│  ─────────────────────────────────                          │
│  Store: S3/Cloud Storage                                    │
│  TTL: 7 days                                                │
│  Invalidation: Data change, template update                 │
│  Purpose: Skip rendering for identical bundles              │
│                                                              │
│  Cache Layer 3: Generated PDFs                              │
│  ───────────────────────────────────                        │
│  Store: S3/Cloud Storage                                    │
│  TTL: 30 days                                               │
│  Invalidation: Manual                                       │
│  Purpose: Skip PDF generation                               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 9.2 Template Optimization

| Optimization | Technique | Impact |
|--------------|-----------|--------|
| **Pre-compilation** | Compile templates at deploy | 50-100ms saved |
| **Minification** | Remove whitespace from HTML | 20-30% smaller |
| **Inline CSS** | Critical CSS in template | Faster render |
| **Lazy Sections** | Load heavy sections only if needed | 40% faster |
| **Image Optimization** | WebP, responsive sizes | 60-80% smaller |

### 9.3 Performance Benchmarks

```
Template Rendering Performance:

┌─────────────────────────────────────────────────────────────┐
│  Metric                    │ Before  │ After   │ Improvement│
├─────────────────────────────────────────────────────────────┤
│  Template compilation       │ 150ms   │ 0ms     │ 100%       │
│  (cached)                  │         │         │            │
│  Data rendering             │ 80ms    │ 60ms    │ 25%        │
│  HTML generation            │ 50ms    │ 30ms    │ 40%        │
│  PDF generation             │ 2000ms  │ 1500ms  │ 25%        │
│  ───────────────────────────────────────────────────────────│
│  Total time                 │ 2280ms  │ 1590ms  │ 30%        │
└─────────────────────────────────────────────────────────────┘
```

---

## Part 10: Template Analytics

### 10.1 Template Performance Tracking

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Template Analytics                                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Performance by Template:                                              │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Template           │ Uses │ Open Rate │ Conversion │ Time     │   │
│  ├─────────────────────────────────────────────────────────────────┤   │
│  │  Modern Minimal     │ 245  │ 78%       │ 32%       │ 2:15     │   │
│  │  Tropical Vibes     │ 189  │ 82%       │ 28%       │ 2:45     │   │
│  │  Luxury Gold        │ 156  │ 71%       │ 41%       │ 3:20     │   │
│  │  Adventure Pro      │ 98   │ 69%       │ 25%       │ 1:50     │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  Insights:                                                             │
│  • Luxury Gold converts best despite lower open rate                   │
│  • Tropical Vibes has highest engagement but avg conversion            │
│  • Adventure Pro has shortest read time (may be too simple)            │
│                                                                         │
│  [A/B Test] [Optimize] [Create Variant]                                │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 10.2 A/B Testing Templates

```
┌─────────────────────────────────────────────────────────────┐
│  A/B Test: Quote Template Layout                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Variant A: Pricing on Top (Current)                        │
│  - Uses: 50                                                 │
│  - Open Rate: 76%                                           │
│  - Conversion: 29%                                         │
│  - Avg Read Time: 2:15                                     │
│                                                              │
│  Variant B: Itinerary First (Challenger)                    │
│  - Uses: 50                                                 │
│  - Open Rate: 82% (+8%)                                     │
│  - Conversion: 34% (+17%) ✅                                 │
│  - Avg Read Time: 2:45 (+29%)                               │
│                                                              │
│  Winner: Variant B                                           │
│  Confidence: 94%                                            │
│  Impact: +5 percentage point conversion lift                 │
│                                                              │
│  [Set as Default] [Continue Test] [Create New Variant]      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Part 11: Template Governance

### 11.1 Approval Workflows

```
┌─────────────────────────────────────────────────────────────┐
│  Template Approval Workflow                                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Agent creates template change                               │
│  └─► Draft status                                           │
│      └─► Submit for review                                  │
│          │                                                  │
│          ├─► Manager Review                                 │
│          │   ├─ Approve ──► Owner Approval                  │
│          │   │                      ├─ Approve ──► Publish │
│          │   │                      └─ Reject ──► Return   │
│          │   └─ Reject ──► Return with feedback            │
│          │                                                  │
│          └─► Auto-publish (if agent has permission)         │
│                                                              │
│  Permission Levels:                                         │
│  - Agent: Create drafts, submit for review                  │
│  - Manager: Review, auto-publish within guidelines          │
│  - Owner: Full control, approve any template                 │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 11.2 Brand Compliance Rules

```javascript
// Brand compliance validator

const brandRules = {
    // Colors must use brand tokens
    colors: {
        allowed: ['var(--brand-primary)', 'var(--brand-secondary)', ...],
        forbidden: ['#000', '#fff', 'rgb()', 'hsl()'], // No hardcoded colors
    },

    // Fonts must use brand variables
    fonts: {
        allowed: ['var(--font-display)', 'var(--font-body)'],
        forbidden: ['Arial', 'Times', 'Courier'], // No system fonts
    },

    // Logo must be from brand assets
    logo: {
        allowedSources: ['agency.logo.svg', 'agency.logo.png'],
        forbidden: ['external urls', 'data URIs'],
    },

    // Legal sections must be present
    required: {
        sections: ['disclaimer', 'terms', 'contact'],
        fields: ['agency.license', 'agency.gst', 'agency.address'],
    },

    // Size and formatting limits
    limits: {
        maxFileSize: '500KB', // PDF target
        maxImageSize: '100KB', // Per image
        maxPages: 10, // For quotes
    },
};
```

---

## Part 12: Template Migration

### 12.1 Importing Existing Templates

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Import Templates                                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Import from:                                                          │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  📄 Upload File                                                 │   │
│  │                                                                   │   │
│  │  Supported formats: HTML, DOCX, PDF                              │   │
│  │                                                                   │   │
│  │  [Choose File] [Upload]                                          │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  🔗 URL Import                                                  │   │
│  │                                                                   │   │
│  │  Enter URL of existing template:                                 │   │
│  │  [https://example.com/template.html                 ]           │   │
│  │                                                                   │   │
│  │  [Import] [Test]                                                 │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  📋 Paste HTML                                                  │   │
│  │                                                                   │   │
│  │  Paste your HTML template code:                                  │   │
│  │  ┌─────────────────────────────────────────────────────────────┐ │   │
│  │  │                                                             │ │   │
│  │  │ <!DOCTYPE html>                                             │ │   │
│  │  │ <html>                                                     │ │   │
│  │  │ ...                                                        │ │   │
│  │  │                                                             │ │   │
│  │  └─────────────────────────────────────────────────────────────┘ │   │
│  │                                                                   │   │
│  │  [Import] [Auto-Convert Variables]                              │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 12.2 Variable Mapping

When importing templates, auto-map common variables:

| Existing Pattern | Our Variable | Notes |
|-----------------|--------------|-------|
| `{{customer_name}}` | `{{customer.name}}` | Simple rename |
| `{DATE}` | `{{date startDate 'DD MMM YYYY'}}` | Format conversion |
| `{{price}}` | `{{currency pricing.total}}` | Add formatting |
| `logo.png` | `{{agency.logo}}` | Dynamic replacement |
| `+91 1234567890` | `{{agency.phone}}` | Static to dynamic |

---

## Summary

### Key Takeaways

| Aspect | Key Decision |
|--------|--------------|
| **Architecture** | Inheritance-based: System → Agency → Type → Variant |
| **Customization** | Progressive: Brand locked, layout flexible, content adaptable |
| **Editor** | Dual mode: Code editor for technical, visual builder for non-technical |
| **Versioning** | Full history with rollback, draft before publish |
| **Marketplace** | Community templates with brand application |
| **Performance** | Multi-layer caching, pre-compilation |
| **Governance** | Approval workflows, brand compliance rules |
| **Analytics** | Per-template performance tracking, A/B testing |

### Template System Benefits

1. **Brand Consistency:** Enforced at system level, agents can't break
2. **Flexibility:** Inheritance allows customization without duplication
3. **Scalability:** New trip types, seasons, segments without rework
4. **Performance:** Cached and optimized for sub-2-second generation
5. **Analytics:** Data-driven template optimization
6. **Governance:** Controlled updates with approval workflows

---

**Status:** Template System deep dive complete.
**Version:** 1.0
**Last Updated:** 2026-04-23

**Next:** Delivery Methods Deep Dive (OUTPUT_06)
