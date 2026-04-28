# Accessibility & Assistive Technology — Inclusive Design & WCAG Compliance

> Research document for WCAG 2.2 compliance, color contrast, font scaling, cognitive accessibility, and inclusive design patterns.

---

## Key Questions

1. **What WCAG 2.2 compliance level should we target?**
2. **How do we handle color contrast across themes and brands?**
3. **What cognitive accessibility considerations apply to travel platforms?**
4. **How do we support font scaling and responsive layouts?**
5. **What's the accessibility testing and compliance workflow?**

---

## Research Areas

### WCAG 2.2 Compliance Framework

```typescript
interface WCAGCompliance {
  targetLevel: ConformanceLevel;
  principles: WCAGPrinciple[];
  auditChecklist: AuditChecklist;
  testingProtocol: TestingProtocol;
  remediation: RemediationWorkflow;
}

type ConformanceLevel =
  | 'A'                               // Minimum (legal requirement in some jurisdictions)
  | 'AA'                              // Standard target (recommended)
  | 'AAA';                            // Enhanced (aspirational for key workflows)

// WCAG 2.2 principles for travel platform:
//
// 1. PERCEIVABLE
//    1.1 Text Alternatives: All non-text content has text alternatives
//    1.2 Time-Based Media: Audio/video has captions, transcripts
//    1.3 Adaptable: Content is presentable in different ways
//    1.4 Distinguishable: Content is easy to see and hear
//
// 2. OPERABLE
//    2.1 Keyboard Accessible: Fully operable via keyboard
//    2.2 Enough Time: Users have enough time to read and use content
//    2.3 Seizures: Content does not cause seizures
//    2.4 Navigable: Content is easy to navigate and find
//    2.5 Input Modalities: Input beyond keyboard supported
//
// 3. UNDERSTANDABLE
//    3.1 Readable: Text is readable and understandable
//    3.2 Predictable: Content appears and operates predictably
//    3.3 Input Assistance: Users are helped to avoid and correct mistakes
//
// 4. ROBUST
//    4.1 Compatible: Content works with current and future assistive tech

// Priority WCAG criteria for travel platform:
//
// CRITICAL (must-have, legal risk):
// - 1.1.1 Non-text Content (A): All images have alt text
// - 1.3.1 Info and Relationships (A): Semantic HTML
// - 1.4.3 Contrast (AA): 4.5:1 text, 3:1 large text
// - 2.1.1 Keyboard (A): Everything keyboard accessible
// - 2.4.1 Bypass Blocks (A): Skip links
// - 2.4.3 Focus Order (A): Logical tab order
// - 2.4.6 Headings and Labels (AA): Descriptive headings
// - 3.3.1 Error Identification (A): Form errors identified
// - 3.3.2 Labels (A): All inputs labeled
// - 4.1.2 Name, Role, Value (A): ARIA properly used
//
// HIGH (should-have, user impact):
// - 1.4.1 Use of Color (A): Info not conveyed by color alone
// - 1.4.11 Non-text Contrast (AA): UI components 3:1 contrast
// - 2.4.2 Page Titled (A): Descriptive page titles
// - 2.4.7 Focus Visible (AA): Keyboard focus indicator
// - 2.5.5 Target Size (AAA): Minimum 44px touch targets
// - 3.2.2 On Input (A): No unexpected context changes
// - 3.3.3 Error Suggestion (AA): Suggest corrections
//
// MEDIUM (nice-to-have):
// - 1.2.2 Captions (A): Video captions
// - 1.3.5 Identify Input Purpose (AA): Autocomplete attributes
// - 1.4.12 Text Spacing (AA): Content works with custom spacing
// - 2.3.1 Three Flashes (A): No more than 3 flashes per second
// - 2.4.8 Location (AAA): Breadcrumbs, sitemap
// - 2.5.3 Label in Name (A): Accessible name contains visible label text

// India legal context:
// RPWD Act 2016 (Rights of Persons with Disabilities):
// - Section 40: Mandates accessibility standards
// - Section 46: Accessibility in information and communication technology
// - Guidelines for Indian Government Websites (GIGW) 3.0
// - Aligns with WCAG 2.1 AA (minimum)
// - Enforcement: Limited currently, but increasing
// - Penalty: Up to ₹5 lakh for non-compliance (under discussion)
//
// Travel-specific accessibility requirements:
// - Air travel: DGCA Civil Aviation Requirement (CAR) for disabled passengers
// - Rail: IRCTC accessibility guidelines
// - Hotels: Accessible India Campaign (Sugamya Bharat Abhiyan)
```

### Color & Contrast

```typescript
interface ColorAccessibility {
  contrastRatios: ContrastRequirement[];
  themeContrast: ThemeContrastConfig;
  colorBlindness: ColorBlindnessSupport;
  testing: ContrastTesting;
}

interface ContrastRequirement {
  element: string;
  normalText: number;                 // Minimum contrast ratio
  largeText: number;                  // 18pt+ or 14pt+ bold
  uiComponents: number;               // Buttons, borders, icons
}

// Contrast requirements (WCAG 2.2):
// Normal text (< 18pt): 4.5:1 minimum (AA), 7:1 (AAA)
// Large text (≥ 18pt or ≥ 14pt bold): 3:1 minimum (AA), 4.5:1 (AAA)
// UI components and graphical objects: 3:1 minimum (AA)
// Disabled elements: No contrast requirement
//
// Platform color palette contrast audit:
// Primary (#2563EB) on White (#FFFFFF):
//   Normal text: 4.6:1 ✅ AA pass, AAA fail
//   → For AAA compliance, darken primary to #1D4ED8: 5.8:1
//
// Secondary (#64748B) on White:
//   Normal text: 4.6:1 ✅ AA pass
//
// Error (#EF4444) on White:
//   Normal text: 3.1:1 ❌ AA fail
//   → Darken to #DC2626: 4.6:1 ✅ AA pass
//
// Success (#22C55E) on White:
//   Normal text: 2.9:1 ❌ AA fail
//   → Darken to #16A34A: 3.8:1 (large text AA, normal text fail)
//   → Use text: "Completed" with icon, don't rely on green alone
//
// Brand theme contrast challenge:
// White-label agencies provide custom brand colors
// Must validate contrast for every custom theme
// Auto-reject themes that don't meet AA contrast
// Provide suggestions: "Your primary color doesn't meet contrast requirements.
//   Suggested alternatives: [Darker shade], [Darker shade]"

interface ColorBlindnessSupport {
  types: ColorBlindnessType[];
  designRules: ColorBlindnessRule[];
  testing: ColorBlindnessTest;
}

type ColorBlindnessType =
  | 'protanopia'                      // Red-blind (1% males)
  | 'deuteranopia'                    // Green-blind (1% males)
  | 'tritanopia'                      // Blue-blind (rare)
  | 'achromatopsia';                  // Complete color blindness (very rare)

// Color blindness design rules:
// 1. Never use color alone to convey information
//    Bad: Red text for "Cancelled", green for "Confirmed"
//    Good: ✅ Confirmed, ❌ Cancelled (icon + text)
//
// 2. Status indicators: Icon + text + color
//    Confirmed: ✅ checkmark + "Confirmed" + green badge
//    Pending: ⏳ clock + "Pending" + yellow badge
//    Cancelled: ❌ cross + "Cancelled" + red badge
//
// 3. Charts and graphs: Use patterns/textures + color
//    Revenue bars: Solid blue + diagonal stripes
//    Cost bars: Solid orange + dots
//    Each bar labeled with value text
//
// 4. Error states: Icon + message + red outline
//    Not just red border on input field
//    Also: Error icon + "Please enter a valid email"
```

### Cognitive Accessibility

```typescript
interface CognitiveAccessibility {
  readingLevel: ReadingLevelConfig;
  layout: CognitiveLayoutConfig;
  forms: CognitiveFormConfig;
  timePressure: TimePressureConfig;
  errorRecovery: ErrorRecoveryConfig;
}

interface ReadingLevelConfig {
  targetLevel: string;                // "8th grade" (target for consumer apps)
  languageSimplicity: string;         // Plain language guidelines
}

// Cognitive accessibility for travel platform:
//
// 1. Reading level:
// Target: 8th grade reading level (accessible to widest audience)
// - Use short sentences (max 20 words)
// - Use common words (avoid jargon)
// - Active voice ("We will book your hotel" not "Your hotel will be booked")
// - Explain travel terms: "Itinerary (your day-by-day plan)"
// - Avoid abbreviations: "GST (Goods and Services Tax)" first time
//
// 2. Layout and information density:
// - One task per screen (don't overwhelm)
// - Clear visual hierarchy (most important info first)
// - Consistent layout across pages (predictable)
// - White space: 20%+ of page area (breathing room)
// - Max 7 items in any list (Miller's Law)
// - Group related information visually
// - Progressive disclosure: Show details on demand, not all at once
//
// 3. Form design:
// - One field per row (mobile)
// - Clear labels above inputs (not placeholder text as labels)
// - Inline validation (error appears next to field immediately)
// - Error messages: Specific and actionable
//   Bad: "Invalid input"
//   Good: "Please enter a valid phone number (10 digits)"
// - Success messages: Confirm what happened
//   "Booking confirmed! Your reference is TRV-45678"
// - Required vs. optional: Mark required fields (not optional ones)
//
// 4. Time pressure:
// - No auto-advancing carousels or sliders
// - No countdown timers on standard pages
//   (Exception: Genuine limited-time offers, clearly explained)
// - Session timeout: Warn 5 minutes before, allow extension
//   "Your session will expire in 5 minutes due to inactivity.
//    [Continue Working]"
// - Form auto-save: Don't lose entered data on timeout
//
// 5. Error recovery:
// - Clear undo for destructive actions
//   "Trip archived. [Undo]"
// - Confirmation before irreversible actions
//   "Are you sure you want to cancel this booking?
//    This action cannot be undone. [Cancel Booking] [Go Back]"
// - Auto-save drafts frequently (every 30 seconds)
// - Navigation away warning for unsaved changes
//   "You have unsaved changes. Leave anyway? [Leave] [Stay]"

interface CognitiveLayoutConfig {
  maxInformationDensity: number;       // Max elements per viewport
  taskFlowPattern: TaskFlowPattern;
  navigationPattern: NavigationPattern;
}

// Task flow for common operations (step-by-step, not all-at-once):
// Create trip:
//   Step 1: "Where to?" → Destination
//   Step 2: "When?" → Dates
//   Step 3: "Who's traveling?" → Travelers
//   Step 4: "What's the plan?" → Itinerary
//   Step 5: "Review & Save" → Summary
//
// Each step: One question, clear answer format, progress indicator
// Progress: "Step 2 of 5 — Dates"
// Back button: Always available
// Skip: Allow optional fields to be skipped
```

### Font Scaling & Responsive Design

```typescript
interface FontScalingSupport {
  baseFontSize: string;               // "16px" (browser default)
  scaleFactors: ScaleFactor[];
  responsiveBreakpoints: Breakpoint[];
  zoomSupport: ZoomConfig;
}

interface ScaleFactor {
  name: string;                       // "Default", "Large", "Extra Large"
  multiplier: number;                 // 1.0, 1.25, 1.5
  example: string;
}

// Font scaling requirements:
// - All text must scale to 200% without loss of content or function
// - Use relative units (rem, em) not fixed units (px) for font-size
// - Container widths: Use max-width, not fixed width
// - Text wrapping: Allow text to wrap, don't truncate with ellipsis on critical content
// - Test at: 100%, 125%, 150%, 200% browser zoom
//
// Responsive breakpoints:
// Mobile: 320px-767px (primary target for India)
// Tablet: 768px-1023px
// Desktop: 1024px-1440px
// Large: 1440px+
//
// At 200% zoom on 1440px desktop:
// - Effective viewport: 720px (tablet width)
// - Layout must adapt gracefully
// - No horizontal scrolling
// - All content accessible
// - Navigation collapses to hamburger menu
//
// India-specific considerations:
// - Many users on 720p-1080p screens (budget laptops)
// - Mobile screens: 360px-412px width common
// - Browser zoom: Common for older users (150-200%)
// - Font preferences: Hindi text may need 10-15% larger base size
//
// Text spacing (WCAG 1.4.12):
// Content must work when users override text spacing:
// - Line height: 1.5× font size
// - Paragraph spacing: 2× font size
// - Letter spacing: 0.12× font size
// - Word spacing: 0.16× font size
// Test: Apply these overrides and verify no content is hidden or overlapping
```

### Accessibility Testing Workflow

```typescript
interface AccessibilityTestingWorkflow {
  automated: AutomatedTesting;
  manual: ManualTesting;
  userTesting: UserTestingConfig;
  compliance: ComplianceReporting;
}

// Testing workflow:
//
// Phase 1: Automated (every PR)
// - axe-core: 0 critical violations
// - eslint-plugin-jsx-a11y: No warnings
// - Lighthouse accessibility: Score > 90
// - Color contrast checker: All color pairs pass AA
// - CI gate: PR blocked if violations found
//
// Phase 2: Manual (weekly)
// - Keyboard-only testing: Complete all primary workflows
// - Screen reader testing: NVDA + Chrome (top 5 pages)
// - Zoom testing: 200% zoom on all pages
// - Mobile testing: TalkBack on Android (top 5 pages)
// - Form testing: All forms submit correctly with screen reader
//
// Phase 3: User testing (quarterly)
// - Recruit users with various disabilities
// - Vision: Screen reader users, low vision users, color blind users
// - Motor: Keyboard-only users, voice control users
// - Cognitive: Users with learning disabilities
// - Test core workflows, document findings, prioritize fixes
//
// Phase 4: Compliance audit (annually)
// - External accessibility audit by certified auditor
// - WCAG 2.2 AA conformance report
// - VPAT (Voluntary Product Accessibility Template)
// - Remediation plan for any gaps
// - Publish accessibility statement on platform
//
// Accessibility statement (required):
// - What standards we conform to
// - Known accessibility gaps and timeline for fixes
// - How to report accessibility issues
// - Contact for accessibility support
// - Date of last audit
```

---

## Open Problems

1. **White-label contrast compliance** — Agencies provide custom brand colors that may not meet contrast requirements. Must validate and auto-correct themes.

2. **Third-party component accessibility** — Map components, date pickers, and rich text editors from third-party libraries often have poor accessibility. Building custom accessible components is expensive.

3. **Dynamic content accessibility** — Real-time updates (new messages, pricing changes, status updates) must be announced to screen reader users without overwhelming them.

4. **Accessibility vs. animation** — Micro-interactions and animations improve UX for most users but can be problematic for users with vestibular disorders. Need `prefers-reduced-motion` support.

5. **Cost of compliance** — Full WCAG 2.2 AA compliance requires significant development investment (estimated 15-20% additional effort). ROI is hard to quantify for small agencies.

---

## Next Steps

- [ ] Build WCAG 2.2 AA compliance testing suite with CI integration
- [ ] Create color contrast validation for white-label themes
- [ ] Design cognitive-accessible forms with progressive disclosure
- [ ] Implement font scaling and responsive layout testing
- [ ] Study accessibility frameworks (Deque axe, WAVE, Accessibility Insights, PA11Y)
