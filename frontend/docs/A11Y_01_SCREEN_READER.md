# Accessibility & Assistive Technology — Screen Reader Support

> Research document for ARIA implementation, screen reader compatibility, semantic HTML, and assistive technology testing.

---

## Key Questions

1. **How do we ensure the platform works with screen readers?**
2. **What ARIA roles and attributes are needed for travel UI components?**
3. **Which screen readers do we need to support?**
4. **How do we test screen reader compatibility?**
5. **What are the common accessibility anti-patterns in travel platforms?**

---

## Research Areas

### Screen Reader Compatibility

```typescript
interface ScreenReaderSupport {
  targetReaders: ScreenReaderTarget[];
  semanticHTML: SemanticHTMLStandard;
  ariaImplementation: ARIAConfig;
  testingStrategy: ScreenReaderTesting;
}

interface ScreenReaderTarget {
  name: string;
  platform: string;
  marketShare: number;                // % of Indian screen reader users
  testingPriority: 'P0' | 'P1' | 'P2';
}

// Screen reader targets (India market):
//
// Desktop:
// - NVDA + Chrome/Firefox (Windows) — 40% of Indian SR users, P0
// - JAWS + Chrome (Windows) — 25%, enterprise/government, P1
// - VoiceOver + Safari (macOS) — 10%, premium users, P1
//
// Mobile:
// - TalkBack + Chrome (Android) — 15%, most common mobile SR in India, P0
// - VoiceOver + Safari (iOS) — 10%, P1
//
// India-specific considerations:
// - Hindi language screen reader support (NVDA Hindi voice)
// - Low-bandwidth: Screen readers + heavy web apps = slow experience
// - Mobile-first: Most Indian users with disabilities access via mobile
// - Govt mandate: RPWD Act 2016 requires digital accessibility

interface SemanticHTMLStandard {
  landmarks: LandmarkMap[];
  headings: HeadingStructure;
  forms: FormAccessibility;
  tables: TableAccessibility;
  media: MediaAccessibility;
}

// Landmark structure for travel platform:
// <header> — Agency logo, navigation, search
// <nav> — Main navigation (Inbox, Workbench, Settings)
// <main> — Primary content area
// <aside> — Context panel, trip summary
// <section> — Distinct content sections within main
// <footer> — Status bar, version info
//
// Heading hierarchy:
// h1: Page title ("Trip: Kerala Backwaters")
// h2: Major sections ("Itinerary", "Pricing", "Travelers")
// h3: Sub-sections ("Day 1: Kochi", "Hotel Options")
// h4: Details ("Room Types", "Cancellation Policy")
//
// NEVER skip heading levels (no h1 → h3)
// NEVER use heading for visual styling alone

// ARIA live regions for dynamic content:
// aria-live="polite" — Updates announced when user is idle
//   Use for: New inbox items, chat messages, status updates
// aria-live="assertive" — Updates announced immediately
//   Use for: Error alerts, booking confirmations, warnings
// aria-live="off" — Updates not announced
//   Use for: Background refreshes, analytics
//
// Example: Trip builder panel updates
// <div aria-live="polite" aria-atomic="true">
//   Trip total updated: ₹55,000 for 2 adults
// </div>
//
// Example: Booking confirmation
// <div role="alert" aria-live="assertive">
//   Booking confirmed! Reference: TRV-45678
// </div>
```

### ARIA Implementation for Travel Components

```typescript
interface TravelARIAComponents {
  tripBuilder: TripBuilderARIA;
  inbox: InboxARIA;
  calendar: CalendarARIA;
  pricing: PricingARIA;
  search: SearchARIA;
  chat: ChatARIA;
}

// Trip Builder accessibility:
// - Each trip component is a draggable card
// - aria-grabbed="true/false" for drag state
// - aria-dropletffect="move" for drop targets
// - Keyboard alternative: Arrow keys to reorder components
// - Screen reader: "Day 1: Hotel Trident, Kochi.
//    Position 1 of 5. Use arrow keys to reorder."
//
// Panel navigation:
// - Tab panel pattern (ARIA tabs)
// - Each panel: role="tabpanel", aria-labelledby="tab-label"
// - Tab list: role="tablist"
// - Each tab: role="tab", aria-selected="true/false"
// - Arrow keys navigate between tabs
// - Screen reader: "Intake panel selected. Showing 3 inquiry items."
//
// Trip timeline:
// - role="list" for timeline container
// - role="listitem" for each event
// - aria-label for event description
// - aria-current="step" for current trip stage
// - Screen reader: "Step 3 of 6: Booking Confirmed.
//    Previous: Quoted. Next: Documents Sent."

interface InboxARIA {
  listPattern: string;                // ARIA listbox pattern
  itemPattern: string;                // ARIA option pattern
  statusAnnouncement: string;         // Live region for status changes
  filterPattern: string;              // ARIA combobox for filters
}

// Inbox accessibility:
// - role="listbox" for trip list
// - role="option" for each trip card
// - aria-selected for currently focused trip
// - aria-label for each trip: "Kerala Backwaters, Rajesh Sharma,
//    In Progress, Last updated 2 hours ago"
// - Filter: role="combobox" with aria-expanded
// - Sort: role="radiogroup" with aria-checked
// - Status badges: aria-label="High Priority" (not just color)
//
// Live region for new trips:
// <div aria-live="polite">
//   New inquiry received: Singapore trip, Priya Mehta
// </div>

// Pricing panel accessibility:
// - Price breakdown: Semantic table with proper headers
// - scope="row" for row headers, scope="col" for column headers
// - Price changes: aria-live region announces updates
// - Currency: Always include currency symbol in aria-label
// - "Price per person: rupees eighteen thousand five hundred"
// - NOT: "₹18,500" (screen readers may mispronounce)
//
// Table accessibility for pricing:
// <table>
//   <caption>Price breakdown for Kerala Backwaters trip</caption>
//   <thead>
//     <tr>
//       <th scope="col">Component</th>
//       <th scope="col">Description</th>
//       <th scope="col">Amount</th>
//     </tr>
//   </thead>
//   <tbody>
//     <tr>
//       <th scope="row">Hotel</th>
//       <td>Trident, 3 nights</td>
//       <td>₹18,000</td>
//     </tr>
//   </tbody>
// </table>
```

### Screen Reader Testing Strategy

```typescript
interface ScreenReaderTesting {
  automated: AutomatedTest[];
  manual: ManualTest[];
  userTesting: UserTestConfig[];
  regression: RegressionTestConfig[];
}

// Automated testing tools:
// - axe-core (npm package): Automated WCAG checks, CI integration
// - Lighthouse Accessibility audit: Part of Chrome DevTools
// - jest-axe: Jest integration for component-level a11y testing
// - eslint-plugin-jsx-a11y: Catch ARIA issues in JSX
// - Target: 0 critical/serious violations in CI
//
// Manual testing checklist (per page):
// [ ] Turn off monitor, complete primary task with screen reader only
// [ ] All interactive elements reachable via Tab key
// [ ] All content readable via screen reader (no empty labels)
// [ ] Dynamic content updates announced (live regions)
// [ ] Forms submit correctly using keyboard only
// [ ] Modal dialogs trap focus correctly
// [ ] Escape key closes overlays/dialogs
// [ ] Skip-to-content link works
// [ ] Heading hierarchy is logical
// [ ] Images have meaningful alt text (or alt="" for decorative)
//
// Screen reader user testing (quarterly):
// - Recruit 3-5 users who use screen readers daily
// - Test core workflows: Create trip, manage inbox, process inquiry
// - Observe where users struggle, get stuck, or get confused
// - Document findings, prioritize fixes
// - Budget: ₹15,000-30,000 per session (India rates)
//
// Regression testing:
// - Automated: axe-core runs on every PR (CI/CD)
// - Weekly: Manual spot-check of top 10 pages with NVDA
// - Monthly: Full manual test with TalkBack (Android)
// - Quarterly: User testing session with screen reader users
```

---

## Open Problems

1. **Complex travel UI components** — Drag-and-drop itinerary builders, multi-panel workbenches, and interactive maps are inherently difficult to make accessible. Need alternative interaction patterns.

2. **Data visualization accessibility** — Pricing charts, timeline visualizations, and dashboards need text alternatives that convey the same information. Not just "chart" alt text.

3. **Real-time updates** — The workbench has frequent real-time updates (new messages, status changes, pricing changes). Screen reader users can be overwhelmed by live region announcements.

4. **Third-party component accessibility** — Map components, date pickers, and rich text editors from third-party libraries often have poor accessibility. Need accessible alternatives or wrappers.

5. **Hindi screen reader support** — Hindi NVDA voice quality is lower than English. Hindi text with English terms (common in Indian travel) causes pronunciation issues.

---

## Next Steps

- [ ] Implement ARIA landmarks and heading hierarchy across all pages
- [ ] Build accessible trip builder with keyboard-only alternative
- [ ] Create screen reader testing suite with axe-core CI integration
- [ ] Design live region announcement strategy for dynamic content
- [ ] Study accessible web apps (GitHub, Slack, Gmail accessibility implementations)
