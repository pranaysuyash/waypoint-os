# Workspace Customization & Agent Productivity — Productivity Tools & Quick Actions

> Research document for keyboard-first workflows, quick actions, batch operations, templates, and productivity features that accelerate agent work.

---

## Key Questions

1. **How do power agents work faster with keyboard-first workflows?**
2. **What quick actions reduce clicks for common tasks?**
3. **How do batch operations handle multiple trips efficiently?**
4. **What template and snippet system accelerates repetitive work?**
5. **How do productivity analytics help agents improve?**

---

## Research Areas

### Keyboard-First Workflow System

```typescript
interface KeyboardSystem {
  profiles: KeyboardProfile[];
  contexts: ContextualBindings;
  navigation: KeyboardNavigation;
  commandPalette: CommandPalette;
  custom: CustomBindings;
}

interface KeyboardProfile {
  id: string;
  name: string;                        // "Vim-style", "Default", "Custom"
  description: string;
  bindings: KeyBinding[];
  conflicts: BindingConflict[];
}

interface KeyBinding {
  id: string;
  keys: string;                        // "j", "shift+j", "ctrl+enter"
  action: string;                      // "navigate_down", "trip.confirm"
  context: BindingContext;
  when?: string;                       // Condition: "trip.selected AND !modal.open"
  repeatable: boolean;                 // Hold to repeat (e.g., j/k navigation)
}

type BindingContext =
  | 'global'                           // Works everywhere
  | 'inbox'                            // Trip list view
  | 'trip_detail'                      // Trip workspace
  | 'modal'                            // Any open modal
  | 'editor'                           // Text editor (message, notes)
  | 'filter';                          // Filter builder

// Default keyboard bindings (Vim-inspired):
//
// GLOBAL:
// ?          → Show keyboard help
// /          → Open command palette
// ctrl+k     → Command palette (alternative)
// ctrl+/     → Toggle sidebar
// 1-9        → Switch workspace tabs
// esc        → Close modal / deselect
//
// INBOX NAVIGATION:
// j / ↓      → Next trip
// k / ↑      → Previous trip
// gg         → First trip
// G          → Last trip
// enter      → Open selected trip
// o          → Open in new tab
// x          → Select/deselect trip (multi-select)
// *          → Select all trips in view
//
// INBOX ACTIONS (on selected trip):
// e          → Quick edit
// r          → Reply to customer
// s          → Change status (cycle: draft → pending → confirmed)
// a          → Assign/reassign agent
// f          → Flag trip (urgent, vip, follow-up)
// t          → Add tag
// n          → Add note
// m          → Send message
// #          → Delete trip (with confirmation)
//
// TRIP DETAIL:
// 1-6        → Switch panels (intake, timeline, decision, output, messages, notes)
// ctrl+s     → Save trip
// ctrl+enter → Confirm/publish
// ctrl+z     → Undo
// [ / ]      → Previous/next section within panel
// { / }      → Collapse/expand section
//
// EDITOR (message, notes):
// ctrl+b     → Bold
// ctrl+i     → Italic
// ctrl+enter → Send message
// ctrl+shift+v → Paste without formatting
// tab        → Indent / accept autocomplete
// shift+tab  → Outdent
// @          → Mention (agent, customer, trip)
// /          → Insert template/snippet
// :          → Insert emoji
//
// FILTER:
// ctrl+f     → Focus filter bar
// enter      → Apply filter
// esc        → Clear filter
// ctrl+s     → Save current filter as view

// Command palette:
// ┌─────────────────────────────────────────┐
// │  > Kerala honeymoon template...          │
// │                                            │
// │  Recent Commands                           │
// │  ├ Assign to Rahul                    [⌘⇧A]│
// │  ├ Status → Confirmed                 [s]  │
// │  └ Send WhatsApp message              [m]  │
// │                                            │
// │  Actions                                   │
// │  ├ Create new trip                    [c]  │
// │  ├ Quick quote                             │
// │  ├ Search customers                        │
// │  ├ Generate itinerary                      │
// │  └ Export trip report                      │
// │                                            │
// │  Navigation                                │
// │  ├ Go to inbox                             │
// │  ├ Go to calendar                          │
// │  ├ Go to analytics                         │
// │  └ Go to settings                          │
// │                                            │
// │  Views                                     │
// │  ├ My Active Trips                         │
// │  ├ Urgent Follow-ups                       │
// │  └ Kerala December                        │
// └─────────────────────────────────────────────┘
//
// Command palette features:
// - Fuzzy search: "kerhoney" → "Kerala honeymoon template"
// - Recently used commands at top
// - Shows keyboard shortcut if exists
// - Context-aware: Different commands for inbox vs trip detail
// - Custom commands: Agents can add their own shortcuts
```

### Quick Actions & Command Bar

```typescript
interface QuickActionSystem {
  actions: QuickAction[];
  floatingBar: FloatingActionBar;
  contextMenu: ContextMenu;
  swipeActions: SwipeAction[];
}

interface QuickAction {
  id: string;
  name: string;                        // "Quick Quote"
  icon: string;
  shortcut?: string;
  category: ActionCategory;
  availability: ActionAvailability;
  handler: ActionHandler;
}

type ActionCategory =
  | 'trip'                             // Trip-related actions
  | 'communication'                    // Messages and calls
  | 'document'                         // Document generation
  | 'customer'                         // Customer management
  | 'navigation'                       // Navigation actions
  | 'custom';                          // User-defined actions

interface ActionAvailability {
  contexts: BindingContext[];
  conditions?: string[];               // "trip.status = pending"
  permissions?: string[];              // Required permissions
}

// Key quick actions:
//
// TRIP ACTIONS:
// ┌─────────────────────────────────────────┐
// │  Quick Actions (on selected trip)         │
// │                                            │
// │  📋 Quick Quote                            │
// │     Generate instant quote with default    │
// │     margins → Opens in side panel          │
// │                                            │
// │  ✅ Confirm Trip                           │
// │     One-click confirm → Sends notification │
// │     to customer + creates tasks            │
// │                                            │
// │  🔄 Duplicate Trip                        │
// │     Clone for same customer → Edit dates   │
// │                                            │
// │  📤 Share Trip                             │
// │     Generate shareable link or PDF         │
// │                                            │
// │  🏷️ Apply Template                        │
// │     Apply saved trip template              │
// │                                            │
// │  ⚡ Quick Edit                             │
// │     Inline edit: dates, price, destination │
// │                                            │
// │  📞 Call Customer                          │
// │     Initiate call via Exotel               │
// │                                            │
// │  💬 Send Update                            │
// │     Template-based status update to cust.  │
// └─────────────────────────────────────────────┘
//
// COMMUNICATION ACTIONS:
// - Quick Reply: Template-based reply in 2 clicks
// - Schedule Follow-up: Set reminder for this trip
// - Forward to Expert: Route to destination specialist
// - Escalate: Flag to manager with context
//
// DOCUMENT ACTIONS:
// - Generate Itinerary: Full trip itinerary PDF
// - Generate Invoice: Invoice with GST breakdown
// - Generate Voucher: Booking-specific voucher
// - Export to Excel: Trip data in spreadsheet

// Floating action bar (appears on trip selection):
// ┌─────────────────────────────────────────┐
// │  TRV-45678 · Kerala · Rajesh Sharma      │
// │  [Confirm] [Reply] [Quote] [More ▼]      │
// └─────────────────────────────────────────────┘
// Appears at bottom of screen when trip is selected
// Primary actions visible, "More" reveals secondary actions
// Keyboard shortcuts shown on hover
// Dismisses on deselection or escape

// Context menu (right-click or long-press):
// ┌─────────────────────────────────────────┐
// │  Open Trip                          ↵    │
// │  Open in New Tab                    ⌘↵   │
// │  ─────────────────────────────────────── │
// │  Confirm                            s    │
// │  Send Message                       m    │
// │  Generate Quote                     q    │
// │  ─────────────────────────────────────── │
// │  Assign To...                       a    │
// │  Add Flag                           f    │
// │  Add Tag                            t    │
// │  Add Note                           n    │
// │  ─────────────────────────────────────── │
// │  Duplicate Trip                          │
// │  Archive Trip                           │
// │  Delete Trip                       ⌫    │
// └─────────────────────────────────────────────┘
//
// Mobile swipe actions:
// ← Swipe right: Quick confirm (primary action)
// → Swipe left: Delete / Archive
// ↑ Swipe up: Reply to customer
// Actions customizable: Agent picks their swipe actions

// Bulk action confirmation:
// ┌─────────────────────────────────────────┐
// │  Bulk Action: Confirm 5 Trips             │
// │                                            │
// │  ⚠️ This will:                            │
// │  • Send confirmation to 5 customers        │
// │  • Create booking tasks for 5 trips        │
// │  • Trigger payment requests                │
// │                                            │
// │  Trips affected:                           │
// │  • TRV-45678 Kerala — Rajesh (₹48,000)    │
// │  • TRV-45679 Goa — Priya (₹32,000)        │
// │  • TRV-45680 Rajasthan — Amit (₹55,000)   │
// │  • TRV-45681 Kerala — Sana (₹42,000)      │
// │  • TRV-45682 Thailand — Vikram (₹78,000)  │
// │                                            │
// │  [Confirm All 5] [Review Each] [Cancel]   │
// └─────────────────────────────────────────────┘
```

### Batch Operations

```typescript
interface BatchOperationSystem {
  selection: BatchSelection;
  operations: BatchOperation[];
  progress: BatchProgress;
  undo: BatchUndo;
}

interface BatchSelection {
  // Selection methods:
  // 1. Click checkbox: Individual trip
  // 2. Shift+click: Range select (trip 3 to trip 7)
  // 3. ctrl/cmd+click: Multi-select (discontiguous)
  // 4. ctrl+A: Select all in current view
  // 5. "Select all matching filter": All trips in current filtered view
  //
  // Selection state:
  // - Selected trips shown with highlight
  // - Count badge: "5 selected"
  // - Floating action bar appears
  // - Select all checkbox: [✓] 5 of 23 selected
  //   - Click: Select all 23
  //   - "Select all 156 trips matching filter"

  selectedIds: string[];
  totalMatching: number;
  allSelected: boolean;
}

type BatchOperation =
  | { type: 'status_change'; status: TripStatus }
  | { type: 'assign'; agentId: string }
  | { type: 'tag'; tags: string[]; mode: 'add' | 'remove' }
  | { type: 'flag'; flag: string; mode: 'set' | 'clear' }
  | { type: 'send_message'; template: string }
  | { type: 'export'; format: 'csv' | 'excel' | 'pdf' }
  | { type: 'archive' }
  | { type: 'delete' }
  | { type: 'merge_customers'; targetCustomerId: string }
  | { type: 'apply_template'; templateId: string };

interface BatchProgress {
  operationId: string;
  total: number;
  completed: number;
  failed: number;
  errors: BatchError[];
  startedAt: Date;
  estimatedCompletion: Date;
}

// Batch progress UI:
// ┌─────────────────────────────────────────┐
// │  Batch: Send Payment Reminder (12 trips)  │
// │                                            │
// │  ████████████████░░░░  9/12 complete       │
// │                                            │
// │  ✅ TRV-45678 Rajesh — Sent               │
// │  ✅ TRV-45679 Priya — Sent                │
// │  ✅ TRV-45680 Amit — Sent                 │
// │  ❌ TRV-45681 Sana — Failed (no phone)    │
// │  ⏳ TRV-45682 Vikram — Sending...          │
// │                                            │
// │  [Cancel Remaining] [Retry Failed] [Done]  │
// └─────────────────────────────────────────────┘

interface BatchUndo {
  operationId: string;
  reversible: boolean;
  undoUntil: Date;                     // Time limit for undo
  affectedTrips: string[];
}

// Batch operations safety:
// - Destructive operations (delete, status change) require confirmation
// - Show preview of affected trips before executing
// - Max batch size: 100 trips per operation
// - Rate limiting: Max 5 batch operations per minute
// - Undo window: 30 seconds for non-destructive, 5 minutes for destructive
// - Admin operations: Unlimited batch size, no rate limit
```

### Templates & Snippets

```typescript
interface TemplateSystem {
  tripTemplates: TripTemplate[];
  messageSnippets: MessageSnippet[];
  itineraryTemplates: ItineraryTemplate[];
  quickFill: QuickFillEngine;
}

interface TripTemplate {
  id: string;
  name: string;                        // "Standard Kerala Honeymoon 5N"
  description: string;
  destination: string;
  type: string;                        // honeymoon, family, adventure
  days: number;
  nights: number;
  inclusions: string[];                // What's included
  exclusions: string[];                // What's not
  itinerary: TemplateDay[];
  pricing: TemplatePricing;
  category: 'agency' | 'team' | 'personal';
  usageCount: number;
  lastUsedAt: Date;
}

interface TemplateDay {
  day: number;
  title: string;                       // "Arrival & Backwater Day"
  activities: TemplateActivity[];
  meals: string[];                     // ["Breakfast", "Lunch", "Dinner"]
  transfers: string[];                 // ["Airport to Hotel (AC Sedan)"]
}

interface TemplateActivity {
  name: string;
  duration: string;                    // "2 hours"
  description: string;
  type: 'sightseeing' | 'adventure' | 'relaxation' | 'cultural' | 'shopping';
  optional: boolean;
  estimatedCost: number;
}

interface TemplatePricing {
  basePrice: number;                   // Per person
  priceVariants: PriceVariant[];       // By hotel category, season
  marginPercent: number;               // Default margin
  seasonalAdjustment: SeasonalAdjustment[];
}

// Template library:
// ┌─────────────────────────────────────────┐
// │  Trip Templates                    [+New]│
// │                                            │
// │  Agency Templates (28)                     │
// │  ├ 🏖️ Kerala Honeymoon 5N            [★4] │
// │  │   ₹35,000/pp · 847 uses · Last week    │
// │  ├ 🏖️ Goa Beach Break 3N             [★3] │
// │  │   ₹18,000/pp · 423 uses                │
// │  ├ 🏔️ Rajasthan Royal 6N             [★5] │
// │  │   ₹42,000/pp · 312 uses                │
// │  └ 🌴 Thailand Budget 4N             [★2] │
// │      ₹25,000/pp · 156 uses                │
// │                                            │
// │  My Templates (5)                          │
// │  ├ 💑 Luxury Kerala 7N                    │
// │  └ 👨‍👩‍👧‍👦 Family Goa 4N                         │
// │                                            │
// │  [Search templates...]                     │
// └─────────────────────────────────────────────┘
//
// Template application flow:
// 1. Agent selects trip or creates new
// 2. Opens template picker (ctrl+t or button)
// 3. Searches: "kerala honeymoon 5 nights"
// 4. Selects template → Preview shown
// 5. Customize: Adjust dates, swap hotels, modify activities
// 6. Apply → Trip populated with template data
// 7. Agent fine-tunes specific fields
// 8. Save → Template instance created

// Message snippets:
interface MessageSnippet {
  id: string;
  name: string;                        // "Payment Reminder"
  category: 'greeting' | 'follow_up' | 'payment' | 'confirmation'
           | 'itinerary' | 'feedback' | 'escalation' | 'custom';
  template: string;                    // Template with variables
  variables: SnippetVariable[];
  channel: 'whatsapp' | 'email' | 'sms' | 'any';
  language: string;                    // "en", "hi", "hinglish"
  attachments?: string[];
}

interface SnippetVariable {
  name: string;                        // "{{customer_name}}"
  source: 'trip' | 'customer' | 'agent' | 'custom';
  fallback: string;                    // Default if value missing
}

// Message snippet examples:
//
// PAYMENT REMINDER (WhatsApp):
// "Hi {{customer_name}}! 👋 Gentle reminder about your
//  {{destination}} trip ({{trip_id}}).
//  Balance of ₹{{balance_amount}} is due by {{due_date}}.
//  Payment link: {{payment_link}}
//  Questions? Reply here or call {{agent_phone}}."
//
// BOOKING CONFIRMATION (Email):
// "Dear {{customer_name}},
//  Your {{destination}} trip is confirmed! 🎉
//  Trip ID: {{trip_id}}
//  Dates: {{start_date}} to {{end_date}}
//  Hotel: {{hotel_name}}, {{hotel_room_type}}
//  I've attached your itinerary and vouchers.
//  Safe travels! — {{agent_name}}"
//
// FOLLOW-UP (WhatsApp, Hinglish):
// "Hi {{customer_name}}! Aapka {{destination}} trip ka
//  kya plan hai? {{days_until_travel}} din mein travel hai.
//  Koi changes chahiye toh bataiye! 🙏"
//
// ITINERARY READY (Email):
// "Hi {{customer_name}}, your {{destination}} itinerary
//  is ready for review! Please check and let me know if
//  you'd like any changes. [View Itinerary] button.
//  Best, {{agent_name}}"
//
// Snippet insertion:
// In message composer, type "/" to open snippet picker
// Fuzzy search: "/pay" → Payment Reminder
// Tab to insert → Variables auto-filled from trip context
// Missing variables highlighted for manual entry

// Quick fill engine:
interface QuickFillEngine {
  // Auto-fill trip fields from:
  // 1. Customer profile: Preferences, budget, contact, past trips
  // 2. Message context: Extract dates, destination, travelers from message
  // 3. Template data: Pre-fill from selected template
  // 4. Past trips: Copy from similar trip by same customer
  // 5. Market data: Auto-suggest hotels, activities for destination
  //
  // Quick fill suggestions appear as inline chips:
  // ┌─────────────────────────────────────────┐
  // │  Destination: [Kerala ▼]                 │
  // │  ┌──────────────────────────────────────┐ │
  // │  │ 💡 Based on customer message:         │ │
  // │  │ • Destination: Kerala                 │ │
  // │  │ • Dates: Dec 15-20                    │ │
  // │  │ • Travelers: 2 (couple)              │ │
  // │  │ • Budget: "around ₹50K"              │ │
  // │  │ [Apply All] [Apply Individual]        │ │
  // │  └──────────────────────────────────────┘ │
  // └─────────────────────────────────────────────┘
}
```

### Productivity Analytics

```typescript
interface ProductivityAnalytics {
  metrics: AgentMetrics;
  insights: ProductivityInsight[];
  goals: ProductivityGoal[];
  comparison: PeerComparison;
}

interface AgentMetrics {
  // Per-agent productivity tracking:
  tripsHandled: {
    daily: number;
    weekly: number;
    monthly: number;
    trend: 'up' | 'down' | 'stable';  // Compared to previous period
  };
  responseTime: {
    avgFirstResponse: number;          // Minutes from customer message
    avgFollowUpResponse: number;       // Minutes between exchanges
    target: number;                    // Agency-set target
  };
  conversionRate: {
    inquiryToQuote: number;            // % of inquiries that get quoted
    quoteToConfirm: number;            // % of quotes that confirm
    overall: number;                   // End-to-end conversion
  };
  revenue: {
    daily: number;
    monthly: number;
    averageTripValue: number;
    target: number;
    percentageToTarget: number;
  };
  efficiency: {
    tripsPerHour: number;              // Active working hours only
    averageHandlingTime: number;       // Minutes per trip
    reworkRate: number;                // % of trips needing major revision
    templateUsageRate: number;         // % of trips using templates
  };
  quality: {
    customerSatisfaction: number;      // NPS from post-trip surveys
    complaintRate: number;             // % of trips with complaints
    repeatCustomerRate: number;        // % of customers who return
  };
}

// Productivity dashboard (personal):
// ┌─────────────────────────────────────────┐
// │  Your Productivity · This Week            │
// │                                            │
// │  📊 Key Metrics                            │
// │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐    │
// │  │  18  │ │ 12m  │ │ 67%  │ │₹8.2L │    │
// │  │Trips │ │Reply │ │Conv. │ │Revenue│    │
// │  │ ↑15% │ │ ↓3m  │ │ ↑5%  │ │↑22%  │    │
// │  └──────┘ └──────┘ └──────┘ └──────┘    │
// │                                            │
// │  📈 Trends (4 weeks)                       │
// │  Revenue: ▁▂▃▅▇█  (↑22% this week)        │
// │  Trips:   ▂▃▃▄▅▅  (↑15% this week)        │
// │  Reply:   ▅▄▃▃▂▂  (↓3min this week)       │
// │                                            │
// │  💡 Insights                               │
// │  • You reply fastest to WhatsApp (8m avg)  │
// │  • Kerala trips convert 2x better for you  │
// │  • Template usage saved ~45 min this week   │
// │                                            │
// │  🎯 Goals                                  │
// │  Monthly target: ₹30L → ₹8.2L done (27%)  │
// │  ██████░░░░░░░░░░░░░░░░ 27%               │
// │                                            │
// │  [View Full Report] [Compare with Team]    │
// └─────────────────────────────────────────────┘

// Productivity insights:
// Generated weekly, personalized to agent's patterns:
//
// TIME INSIGHTS:
// "You're most productive between 10am-12pm.
//  Consider scheduling complex quotes during this window."
//
// CHANNEL INSIGHTS:
// "Your WhatsApp response time (8m) is 3x faster than email (24m).
//  Consider enabling WhatsApp Business API for all customers."
//
// DESTINATION INSIGHTS:
// "Your Kerala trips have 78% conversion vs. 45% for Goa.
//  Consider specializing in Kerala — your expertise shows."
//
// TEMPLATE INSIGHTS:
// "You've saved ~2.5 hours this month using templates.
//  Top template: 'Kerala Honeymoon 5N' (used 12 times).
//  Create templates for your top 3 trip types to save more."
//
// WORKLOAD INSIGHTS:
// "You handled 18 trips this week (team avg: 14).
//  Your reply time increased by 3min on Thursday/Friday.
//  Consider distributing load more evenly across the week."

// Peer comparison (anonymized, opt-in):
// "Your conversion rate: 67%
//  Team average: 58%
//  Team top quartile: 72%
//  You're in the top 30% of the team."
//
// Privacy note: Individual agents can't see other agents' exact numbers.
// Only see: own metrics, team average, team quartiles.
// Manager sees all individual metrics.
```

---

## Open Problems

1. **Keyboard shortcut discoverability** — Agents who don't use keyboard shortcuts miss significant productivity gains. Teaching shortcuts without being annoying requires subtle in-context hints ("Tip: Press 'j' to navigate faster" shown once, then in help only).

2. **Template rigidity vs. flexibility** — Templates that are too rigid don't fit real trip variations. Templates that are too flexible become as much work as building from scratch. Finding the right level of structure is an ongoing design challenge.

3. **Batch operation safety** — Bulk actions on 50+ trips can have significant consequences (50 customers getting wrong messages). Multi-step confirmation with preview is essential but adds friction that agents may try to bypass.

4. **Productivity metric gamification** — Public leaderboards and conversion metrics can drive unhealthy competition. Metrics should motivate improvement, not shame agents. Opt-in comparison and private dashboards are the baseline.

5. **Snippet quality in multilingual context** — Hinglish, Hindi, and regional language snippets need careful crafting. Auto-translated snippets often sound unnatural. A curated snippet library with native speaker review is needed.

---

## Next Steps

- [ ] Build keyboard shortcut system with configurable profiles and contextual bindings
- [ ] Create command palette with fuzzy search and recent commands
- [ ] Design batch operation engine with preview, progress, and undo
- [ ] Implement template and snippet library with variable interpolation
- [ ] Study productivity tools (Superhuman keyboard shortcuts, Linear command palette, Notion slash commands)
