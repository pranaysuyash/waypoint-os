# Accessibility — Inclusive UX Design Patterns

> Research document for inclusive design patterns specific to travel platform interfaces.

---

## Key Questions

1. **What UX patterns work best for presenting accessibility information without othering?**
2. **How do we make the intake/booking flow accessible to agents with disabilities?**
3. **What's the right level of accessibility detail in search results?**
4. **How do we support cognitive accessibility (clear language, predictable layouts)?**
5. **What assistive technology testing matrix should we maintain?**

---

## Research Areas

### Inclusive Design Principles for Travel

```typescript
interface InclusiveDesignPrinciple {
  principle: string;
  description: string;
  travelSpecificExamples: string[];
  implementationGuidelines: string[];
}

// 1. Recognize exclusion — Don't assume "normal" traveler profiles
// 2. Solve for one, extend to many — Curb cuts help everyone
// 3. Learn from diversity — Involve travelers with disabilities in design
// 4. Provide multiple ways to complete tasks — Click, type, speak, drag
// 5. Maintain consistent patterns — Predictable navigation reduces cognitive load
```

### Search Results Accessibility UX

```typescript
interface AccessibleSearchResult {
  // Don't bury accessibility in a filter — show it prominently
  accessibilitySummary: string;      // "Fully wheelchair accessible"
  accessibilityBadge: BadgeType;     // Visual indicator
  detailLevel: 'summary' | 'detailed' | 'full_report';
  // Progressive disclosure
  expandableDetails: AccessibilityDetail[];
}

type BadgeType =
  | 'fully_verified'       // Third-party verified
  | 'self_reported'        // Supplier says accessible
  | 'partially_accessible' // Some features available
  | 'unknown';             // No data

// UX patterns:
// - Accessibility icon next to hotel name ( wheelchair symbol)
// - Click/hover reveals accessibility summary
// - Full details available in property detail page
// - Filter sidebar includes accessibility options
// - Sort by "best accessibility match" when profile is active
```

### Agent Workbench Accessibility

**Keyboard navigation map:**

```typescript
interface WorkbenchKeyboardMap {
  // Global shortcuts
  global: {
    'Cmd+K': 'command_palette';
    'Cmd+/': 'keyboard_shortcuts_help';
    'Tab': 'next_panel';
    'Shift+Tab': 'previous_panel';
    'Escape': 'close_modal';
  };
  // Panel-specific
  intake: {
    'Cmd+Enter': 'submit_intake';
    'Cmd+S': 'save_draft';
    'Up/Down': 'navigate_form_fields';
  };
  // List navigation
  trip_list: {
    'J/K': 'next/previous_trip';
    'Enter': 'open_trip';
    'X': 'close_trip';
    'S': 'star_trip';
  };
}
```

### Cognitive Accessibility

**Clear language guidelines for travel platform:**

```typescript
interface CognitiveAccessibilityGuideline {
  area: string;
  rules: string[];
  examples: { bad: string; good: string }[];
}

// Areas:
// 1. Plain language — Avoid jargon, use short sentences
// 2. Clear status indicators — Use words + icons, not just color
// 3. Predictable layouts — Same elements in same places
// 4. Error prevention — Confirm destructive actions, show clear errors
// 5. Time allowances — No auto-submits, extendable timeouts
// 6. Progressive disclosure — Don't show everything at once
// 7. Wayfinding — Clear breadcrumbs, page titles, progress indicators

// Example:
// BAD: "Your PNR has been TTL'd by the GDS due to TKT time limit"
// GOOD: "Your flight reservation will expire in 2 hours. Please confirm your booking."
```

### Testing Matrix

```typescript
interface AccessibilityTestMatrix {
  assistiveTechnologies: AssistiveTech[];
  browsers: BrowserTarget[];
  devices: DeviceTarget[];
  testTypes: TestType[];
}

interface AssistiveTech {
  name: string;
  platform: string;
  usageShare: number;
  testPriority: 'must' | 'should' | 'nice';
}

// Must-test:
// - VoiceOver (macOS/iOS) — largest screen reader share in our market
// - NVDA (Windows) — most common free screen reader
// - Keyboard-only navigation — universal baseline
// - Zoom to 200% — common for low vision
// Should-test:
// - JAWS (Windows) — enterprise screen reader
// - TalkBack (Android) — mobile screen reader
// - Voice Control (macOS/iOS) — motor disability
// Nice:
// - Switch Access (Android/iOS) — severe motor disability
// - Magnifier (Windows/macOS) — low vision
```

---

## Open Problems

1. **Complex data tables** — Itinerary comparison tables with pricing, duration, and amenities are hard to make screen-reader friendly. Need alternative presentations.

2. **Map interactions** — Map-based destination browsing is inherently visual. Need text-based alternatives that provide equivalent functionality.

3. **Rich media content** — Destination photos and videos need alt text, captions, and audio descriptions. This is expensive at scale.

4. **Third-party widget accessibility** — Payment gateways, chat widgets, and booking engines embedded from third parties may not be accessible. We inherit their accessibility debt.

5. **Accessibility vs. visual richness** — The workbench is designed to be visually information-dense. Making it accessible may require different layouts that feel "simpler" — which may actually benefit all users.

---

## Next Steps

- [ ] Audit current workbench for keyboard navigation gaps
- [ ] Create accessible component library wrapper (on top of existing UI library)
- [ ] Design accessibility detail page for supplier profiles
- [ ] Write plain-language guidelines for all customer-facing copy
- [ ] Set up automated accessibility testing in CI (axe-core)
- [ ] Design cognitive accessibility checklist for UX reviews
