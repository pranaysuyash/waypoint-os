# User Guidance & Helper System — Contextual Help & Tooltips

> Research document for in-app contextual help, smart tooltips, help panels, and always-available assistance for agents and customers.

---

## Key Questions

1. **How do agents get help exactly when and where they need it?**
2. **What tooltip and popover system provides just-in-time guidance?**
3. **How does contextual help adapt to the user's experience level?**
4. **What help panel system provides deep assistance without leaving the page?**
5. **How do we help users recover from errors and dead-ends?**

---

## Research Areas

### Contextual Help Architecture

```typescript
interface ContextualHelpSystem {
  tooltips: TooltipEngine;
  helpPanel: HelpPanel;
  emptyStates: EmptyStateGuidance;
  errorGuidance: ErrorGuidance;
  smartHints: SmartHintEngine;
}

interface HelpContext {
  page: string;                        // Current page/route
  panel?: string;                      // Active panel within page
  component?: string;                  // Specific UI component
  action?: string;                     // Current action being performed
  userLevel: 'novice' | 'competent' | 'proficient' | 'expert';
  recentActions: string[];             // Last N actions for context
  errors: HelpError[];                 // Current error states
  timeOnPage: number;                  // Seconds on current page
  hoverTarget?: string;                // What user is hovering over
}

// Contextual help philosophy:
// - Right help, right place, right time
// - Never blocking — always dismissible
// - Progressive: Brief → Detailed → Full article
// - Adaptive: Less help for experts, more for novices
// - Searchable: Every help item is in the help index
// - Trackable: Know which help items are used most
//
// Help density by experience level:
// NOVICE:
// - All tooltips active
// - Frequent smart hints ("Did you know you can...")
// - Help panel auto-suggests relevant articles
// - Empty states include detailed guidance
// - Error messages include step-by-step fix instructions
//
// EXPERT:
// - Minimal tooltips (only for new features)
// - No proactive hints
// - Help panel only on explicit request (?)
// - Empty states are concise
// - Error messages are technical + actionable
```

### Tooltip & Popover System

```typescript
interface TooltipEngine {
  tooltips: Tooltip[];
  popovers: Popover[];
  behavior: TooltipBehavior;
  analytics: TooltipAnalytics;
}

interface Tooltip {
  id: string;
  target: string;                      // CSS selector or component ref
  title?: string;
  content: string;
  type: TooltipType;
  trigger: TooltipTrigger;
  position: 'top' | 'bottom' | 'left' | 'right' | 'auto';
  priority: number;                    // 1-10, higher = more important
  dismissible: boolean;
  showOnce: boolean;                   // Only show once per user
  showUntil?: string;                  // Show until condition met (e.g., "user.clicked.target")
  conditions?: TooltipCondition[];     // When to show
}

type TooltipType =
  | 'info'                             // Informational (blue i icon)
  | 'tip'                              // Pro tip (lightbulb icon)
  | 'warning'                          // Caution (yellow warning)
  | 'new_feature'                      // New feature announcement (sparkle)
  | 'keyboard_shortcut'                // Keyboard shortcut hint
  | 'required'                         // Required field indicator
  | 'validation';                      // Validation error explanation

type TooltipTrigger =
  | 'hover'                            // Show on hover (default)
  | 'focus'                            // Show on focus (form fields)
  | 'click'                            // Show on click (info icons)
  | 'appear'                           // Show when element appears
  | 'idle'                             // Show after inactivity
  | 'error';                           // Show on validation error

// Tooltip examples:
//
// FORM FIELD TOOLTIP (hover/focus):
// ┌─────────────────────────────────────────┐
// │  Markup (%): [___12___] [ℹ]              │
// │                          ┌──────────────┐│
// │                          │ 💡 Markup     ││
// │                          │              ││
// │                          │ Your profit  ││
// │                          │ margin over   ││
// │                          │ cost. Default ││
// │                          │ is 12%.       ││
// │                          │              ││
// │                          │ Range: 0-50% ││
// │                          │ [Learn more] ││
// │                          └──────────────┘│
// └─────────────────────────────────────────┘
//
// NEW FEATURE TOOLTIP (appear):
// ┌─────────────────────────────────────────┐
// │  [Save View ▼]                           │
// │  ┌──────────────────────────────────┐    │
// │  │ ✨ New Feature                    │    │
// │  │                                  │    │
// │  │ You can now save your custom     │    │
// │  │ filtered views for quick access. │    │
// │  │                                  │    │
// │  │ Try it: Build a filter, then     │    │
// │  │ click this button to save it.    │    │
// │  │                                  │    │
// │  │ [Show Me How] [Got It]          │    │
// │  └──────────────────────────────────┘    │
// └─────────────────────────────────────────┘
//
// KEYBOARD SHORTCUT HINT (idle, after 3 uses):
// ┌─────────────────────────────────────────┐
// │  [Status: Pending ▼]                     │
// │          ┌──────────────────────────┐    │
// │          │ ⌨️ Speed Tip              │    │
// │          │                          │    │
// │          │ Press 's' to quickly     │    │
// │          │ cycle trip status.       │    │
// │          │                          │    │
// │          │ [s] Draft → Pending →   │    │
// │          │     Confirmed            │    │
// │          └──────────────────────────┘    │
// └─────────────────────────────────────────┘
//
// VALIDATION TOOLTIP (error):
// ┌─────────────────────────────────────────┐
// │  Price (₹): [___15000___]                │
// │  ┌──────────────────────────────────┐    │
// │  │ ⚠️ Price seems low               │    │
// │  │                                  │    │
// │  │ This Kerala trip is priced at    │    │
// │  │ ₹15,000. Similar trips average  │    │
// │  │ ₹35,000-45,000.                 │    │
// │  │                                  │    │
// │  │ Did you forget to include:       │    │
// │  │ • Hotel (₹8,000/night × 5)     │    │
// │  │ • Activities (₹5,000)           │    │
// │  │ • Flights                        │    │
// │  │                                  │    │
// │  │ [Update Price] [This is correct]│    │
// │  └──────────────────────────────────┘    │
// └─────────────────────────────────────────┘

interface Popover {
  id: string;
  target: string;
  title: string;
  content: string;                     // Markdown supported
  actions: PopoverAction[];
  width: 'narrow' | 'medium' | 'wide';
  dismissible: boolean;
  backdrop: boolean;                   // Dim background
}

interface PopoverAction {
  label: string;
  action: 'link' | 'tour' | 'dismiss' | 'custom';
  value?: string;                      // URL, tour ID, or custom action
  primary?: boolean;
}

// Popover examples:
// - Quick reference card: Hover on destination → Show key facts
// - Customer mini-profile: Hover on customer name → Show profile card
// - Trip summary: Hover on trip ID → Show mini summary
// - Template preview: Hover on template → Show preview card
```

### Help Panel System

```typescript
interface HelpPanel {
  trigger: HelpPanelTrigger;
  search: HelpSearch;
  sections: HelpSection[];
  feedback: HelpFeedback;
}

// Help panel — always accessible via ? button or ctrl+shift+h:
// ┌──────────┬──────────────────────────────────┐
// │ [Main]   │  Help                             │
// │ [Work-   │                                   │
// │  space]  │  🔍 Search help...                │
// │          │                                   │
// │          │  ── Context: Trip Detail ────────  │
// │          │                                   │
// │          │  📖 Related Articles               │
// │          │  ├ How to confirm a trip           │
// │          │  ├ How to generate itinerary       │
// │          │  ├ How to send payment link        │
// │          │  └ How to modify a booking         │
// │          │                                   │
// │          │  ⌨️ Keyboard Shortcuts              │
// │          │  ├ s — Change status               │
// │          │  ├ m — Send message                │
// │          │  ├ ctrl+s — Save trip              │
// │          │  └ [View All Shortcuts]            │
// │          │                                   │
// │          │  🎓 Tutorials                      │
// │          │  ├ Trip Builder Basics (5 min)     │
// │          │  ├ Document Generation (4 min)     │
// │          │  └ Advanced Pricing (6 min)        │
// │          │                                   │
// │          │  💬 Ask a Question                  │
// │          │  Type your question here...         │
// │          │                                   │
// │          │  📞 Contact Support                 │
// │          │  Chat with team · 24/7 available    │
// └──────────┴──────────────────────────────────┘

// Help search:
// - Searches: Articles, tutorials, FAQs, shortcuts
// - Fuzzy matching: "how confirm trip" → "How to confirm a trip"
// - Context-boosted: Articles related to current page ranked higher
// - Recent searches stored per user
// - Popular searches shown as suggestions
//
// Search result ranking:
// 1. Exact title match
// 2. Context-boosted (related to current page)
// 3. Recent help items (user has viewed before)
// 4. Popularity (most viewed by all agents)
// 5. Relevance (text matching score)

interface HelpSection {
  id: string;
  title: string;
  icon: string;
  type: 'contextual' | 'shortcuts' | 'tutorials' | 'faq' | 'recent' | 'popular';
  items: HelpItem[];
  collapsible: boolean;
  defaultExpanded: boolean;
}

interface HelpItem {
  id: string;
  title: string;
  type: 'article' | 'tutorial' | 'shortcut' | 'faq' | 'video';
  estimatedTime?: string;              // "3 min read"
  tags: string[];
  lastUpdated: Date;
  viewCount: number;
}

// Contextual articles — auto-selected based on current page:
// Page: inbox → "Managing your inbox", "Filtering trips", "Keyboard shortcuts"
// Page: trip_detail → "Confirming trips", "Document generation", "Trip timeline"
// Page: messages → "Message templates", "Quick reply", "WhatsApp integration"
// Page: analytics → "Reading dashboards", "Custom reports", "Export data"
// Page: settings → "Workspace customization", "Notification preferences", "Integrations"

interface HelpFeedback {
  // After viewing help article:
  // "Was this helpful? [👍 Yes] [👎 No]"
  // If No → "What was missing?" [free text]
  //
  // Feedback used for:
  // 1. Ranking improvement (helpful articles ranked higher)
  // 2. Content gaps (frequently unhelpful → needs rewrite)
  // 3. New article suggestions (common "No" reasons → new article)
  //
  // Analytics:
  // - Help item view count
  // - Helpfulness score (yes/total)
  // - Search success rate (% of searches that ended in a click)
  // - Time to resolution (time from help open to action completion)
  // - Deflection rate (% of support tickets avoided by help articles)
}
```

### Empty State Guidance

```typescript
interface EmptyStateGuidance {
  states: EmptyState[];
  illustrations: EmptyStateIllustration;
  actions: EmptyStateAction[];
}

// Empty states appear when there's no content in a section.
// Every empty state should:
// 1. Explain what goes here (what is this space for?)
// 2. Why it's empty (normal? need to create something?)
// 3. How to fill it (clear next action)
// 4. Alternative help (link to learn more)

// Empty state examples:
//
// EMPTY INBOX:
// ┌─────────────────────────────────────────┐
// │                                            │
// │          📭                                 │
// │                                            │
// │    No trips in your inbox                  │
// │                                            │
// │    When customers submit inquiries,        │
// │    they'll appear here.                    │
// │                                            │
// │    [Create Test Trip] [Import Sample Data] │
// │                                            │
// │    📖 How trips enter your inbox           │
// └─────────────────────────────────────────────┘
//
// EMPTY TRIP TIMELINE:
// ┌─────────────────────────────────────────┐
// │                                            │
// │    📋 No activity yet                      │
// │                                            │
// │    The timeline shows every action on      │
// │    this trip — messages, status changes,   │
// │    document generation, and more.          │
// │                                            │
// │    Start by confirming the trip to         │
// │    generate the first timeline events.     │
// │                                            │
// │    [Confirm Trip]                          │
// │                                            │
// │    📖 What the timeline tracks             │
// └─────────────────────────────────────────────┘
//
// EMPTY SEARCH RESULTS:
// ┌─────────────────────────────────────────┐
// │                                            │
// │    🔍 No trips match "Kerala December"     │
// │                                            │
// │    Try:                                    │
// │    • Removing some filters                 │
// │    • Checking spelling                     │
// │    • Using broader terms ("Kerala" only)   │
// │                                            │
// │    [Clear All Filters] [Search All Trips]  │
// └─────────────────────────────────────────────┘
//
// EMPTY MESSAGES:
// ┌─────────────────────────────────────────┐
// │                                            │
// │    💬 No messages yet                      │
// │                                            │
// │    Start a conversation with the           │
// │    customer about this trip.               │
// │                                            │
// │    [Send Message] [Use Template]           │
// │                                            │
// │    💡 Tip: Use / to quickly insert a       │
// │    message template.                       │
// └─────────────────────────────────────────────┘
//
// FIRST TIME EMPTY STATE (never had content):
// - More detailed explanation
// - Video tutorial link
// - "Create sample" option
// - Link to onboarding guide
//
// FILTERED EMPTY STATE (had content, filters removed all):
// - Explain which filters are active
// - Show count of total items before filters
// - "Clear filters" as primary action
// - Suggest adjusting filter values
//
// ARCHIVED EMPTY STATE (all items archived):
// - Explain items were intentionally removed
// - "View archived" link
// - Confirm this is expected, not a bug

interface EmptyStateAction {
  label: string;
  action: 'create' | 'import' | 'learn' | 'clear_filters' | 'view_archived';
  primary: boolean;
  shortcut?: string;
}
```

### Error Guidance & Recovery

```typescript
interface ErrorGuidance {
  messages: ErrorMessage[];
  recovery: ErrorRecovery[];
  deadEnds: DeadEndResolution[];
}

interface ErrorMessage {
  code: string;                        // Error code for tracking
  title: string;                       // Human-readable title
  description: string;                 // What happened
  cause: string;                       // Why it happened
  solution: string;                    // How to fix it
  actions: ErrorAction[];
  severity: 'info' | 'warning' | 'error' | 'critical';
  recoverable: boolean;
}

// Error message design principles:
// 1. Never show raw error codes to users
// 2. Always explain what happened in plain language
// 3. Always offer a next step (retry, fix, contact)
// 4. For critical errors, explain data safety ("Your work is saved")
// 5. For recoverable errors, offer one-click fix
//
// ERROR: Network failure while saving trip
// ┌─────────────────────────────────────────┐
// │  ⚠️ Couldn't save changes                 │
// │                                            │
// │  Your internet connection was interrupted  │
// │  while saving. Don't worry — your changes  │
// │  are stored locally.                       │
// │                                            │
// │  [Try Again] [Save as Draft]               │
// │                                            │
// │  Changes will auto-sync when you're back   │
// │  online.                                   │
// └─────────────────────────────────────────────┘
//
// ERROR: Payment gateway timeout
// ┌─────────────────────────────────────────┐
// │  ⚠️ Payment processing delayed             │
// │                                            │
// │  The payment gateway is taking longer      │
// │  than usual. This can happen during        │
// │  peak hours.                               │
// │                                            │
// │  The payment is still being processed.     │
// │  Please don't refresh or retry.            │
// │                                            │
// │  [Check Payment Status] [View Trip]        │
// │                                            │
// │  If not resolved in 10 minutes, contact    │
// │  support. Ref: PAY-ERR-45678               │
// └─────────────────────────────────────────────┘
//
// ERROR: Trip not found (deleted or wrong ID)
// ┌─────────────────────────────────────────┐
// │  🚫 Trip not found                        │
// │                                            │
// │  This trip may have been deleted,          │
// │  archived, or the link is incorrect.       │
// │                                            │
// │  What you can do:                          │
// │  [Go to Inbox] [Search Trips]             │
// │  [Contact Support]                         │
// │                                            │
// │  If you were looking for a specific        │
// │  trip, try searching by customer name      │
// │  or destination.                           │
// └─────────────────────────────────────────────┘
//
// VALIDATION ERROR: Required field missing
// ┌─────────────────────────────────────────┐
// │  Customer phone number is required         │
// │                                            │
// │  We need a phone number to send booking    │
// │  confirmations and trip updates via        │
// │  WhatsApp.                                 │
// │                                            │
// │  [Add Phone Number ←] [Skip for Now]      │
// │                                            │
// │  ⚠️ Without a phone number, you won't be   │
// │  able to send WhatsApp updates.            │
// └─────────────────────────────────────────────┘

interface ErrorRecovery {
  errorPattern: string;                // Regex or error code
  strategy: RecoveryStrategy;
  autoRetry: boolean;
  maxRetries: number;
  fallbackAction: string;
}

type RecoveryStrategy =
  | 'retry'                            // Try the same action again
  | 'refresh'                          // Refresh data from server
  | 'offline_queue'                    // Queue for later (offline)
  | 'alternative_flow'                 // Use different approach
  | 'escalate';                        // Send to support

// Dead-end resolution:
// When a user reaches a state where they can't proceed:
//
// DEAD END: No search results for destination
// → "Kerala not found in supplier inventory"
// → Suggest: Check spelling, try alternate name, contact supplier
//
// DEAD END: All hotels sold out for dates
// → "No availability for Dec 15-20 in Kerala"
// → Suggest: Try different dates, nearby locations, waitlist
//
// DEAD END: Customer profile locked by another agent
// → "This customer is being edited by Rahul"
// → Suggest: Wait and retry, send message to Rahul, view-only mode
```

### Smart Hint Engine

```typescript
interface SmartHintEngine {
  rules: HintRule[];
  delivery: HintDelivery;
  tracking: HintTracking;
}

interface HintRule {
  id: string;
  name: string;
  trigger: HintTrigger;
  condition: HintCondition;
  hint: HintContent;
  frequency: HintFrequency;
  priority: number;
}

type HintTrigger =
  | 'action_count'                     // After doing X N times
  | 'time_on_page'                     // After spending X seconds
  | 'action_pattern'                   // Detect suboptimal workflow
  | 'error_count'                      // After X errors
  | 'feature_unused'                   // Feature available but not used
  | 'milestone';                       // After reaching a milestone

// Smart hint examples:
//
// ACTION COUNT (after 10 manual status changes):
// "💡 Tip: Press 's' to quickly cycle through trip statuses.
//  You've been clicking the dropdown — keyboard is 3x faster!
//  [Show Keyboard Shortcuts] [Dismiss]"
//
// TIME ON PAGE (stuck on trip detail for 5+ minutes without action):
// "Need help with this trip?
//  [Generate Itinerary] [Send to Customer] [Ask AI Copilot]"
//
// ACTION PATTERN (agent copies text from trip to message):
// "💡 You can drag trip details directly into messages.
//  Try dragging the hotel name into your message composer."
//
// FEATURE UNUSED (agent has never used templates):
// "You've created 15 trips manually. Templates can save you
//  ~30 minutes per trip. Browse our template library?
//  [View Templates] [Maybe Later]"
//
// MILESTONE (first trip confirmed):
// "🎉 Great job! Your first trip is confirmed.
//  Next step: Generate the itinerary for your customer.
//  [Generate Itinerary]"

type HintFrequency =
  | 'once_ever'                        // Show once, never again
  | 'once_per_session'                 // Show once per session
  | 'once_per_day'                     // Show once per day
  | 'every_nth_time'                   // Show every Nth time
  | 'until_dismissed'                  // Keep showing until dismissed
  | 'until_actioned';                  // Keep showing until user acts

interface HintDelivery {
  // Where hints appear:
  // 1. Inline: Below the relevant UI element
  // 2. Toast: Bottom-right notification (non-blocking)
  // 3. Banner: Top of page (for important hints)
  // 4. Help panel: Added to contextual help section
  // 5. Modal: Only for critical guidance (rare)
  //
  // Hint display rules:
  // - Max 1 hint visible at a time
  // - Never show hint during active typing
  // - Never show hint during drag operation
  // - Lower priority hints yield to higher priority
  // - Hints dismissed by user are blacklisted for 7 days
  // - Hints acted on (user follows suggestion) boost similar hints
  // - Max 3 hints per session to avoid annoyance
}

interface HintTracking {
  // Track hint effectiveness:
  // - Shown count: How many times hint was displayed
  // - Dismissed rate: % of times dismissed without action
  // - Action rate: % of times user followed the suggestion
  // - Time to dismiss: How long before user dismissed
  // - Never show again rate: % of times "Don't show again" clicked
  //
  // Use tracking to:
  // - Remove unhelpful hints (high dismiss rate)
  // - Improve wording of hints (medium dismiss rate)
  // - Promote helpful hints (high action rate)
  // - Identify new hint opportunities (support ticket patterns)
}
```

---

## Open Problems

1. **Tooltip fatigue** — Too many tooltips overwhelm users, especially on complex pages. Aggressive tooltip dismissal (never show again) may cause users to miss important guidance. A smart frequency system with per-user learning is needed.

2. **Help search quality** — Help search needs to understand travel domain jargon, abbreviations (TRV, PNR, GST, TCS), and common misspellings. Domain-specific search tuning is essential for relevance.

3. **Context detection accuracy** — Detecting what the user is trying to do (their intent) from page state and recent actions is imperfect. A user might be on the trip detail page but actually looking for a message — contextual help based on page alone would be wrong.

4. **Error message tone** — Error messages need to be helpful without being condescending. "Don't worry!" is comforting to some users but annoying to experienced agents who just want the fix. Tone should adapt to experience level.

5. **Help content maintenance** — Help articles become stale as the product evolves. An automated system to flag outdated articles (compare article screenshots to current UI) would help but is complex to build.

---

## Next Steps

- [ ] Design contextual help architecture with adaptive help density by experience level
- [ ] Build tooltip engine with smart triggers, frequency controls, and dismissal tracking
- [ ] Create help panel with search, contextual articles, and feedback system
- [ ] Implement smart hint engine with usage pattern detection
- [ ] Study in-app help systems (Intercom, Pendo, UserGuiding, Appcues, WhatFix)
