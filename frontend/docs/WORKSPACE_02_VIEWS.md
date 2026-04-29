# Workspace Customization & Agent Productivity — Saved Views & Smart Filters

> Research document for saved view persistence, complex filter composition, smart filter suggestions, and view sharing across teams.

---

## Key Questions

1. **How do agents build and persist complex filtered views of their work?**
2. **What filter composition system supports diverse agent workflows?**
3. **How do smart filters anticipate what agents need?**
4. **How do shared views work across teams with personalization?**
5. **What performance strategies keep filtered views fast at scale?**

---

## Research Areas

### Saved View Architecture

```typescript
interface SavedView {
  id: string;
  name: string;                        // "My Hot Leads", "Kerala Season Queue"
  description?: string;
  icon?: string;                       // Custom emoji or icon
  color?: string;                      // Label color for sidebar
  owner: string;                       // Agent ID
  type: ViewType;
  filters: FilterGroup;
  sort: SortConfig;
  columns: ColumnState[];
  groupBy?: GroupByConfig;
  layout: ViewLayout;
  scope: ViewScope;
  stats: ViewStats;
  schedule?: ViewSchedule;            // Scheduled report generation
  createdAt: Date;
  updatedAt: Date;
}

type ViewType =
  | 'inbox'                            // Trip listing (default)
  | 'customer_list'                    // Customer directory
  | 'message_queue'                    // Communication inbox
  | 'task_list'                        // Task management
  | 'calendar'                         // Calendar view
  | 'kanban'                           // Pipeline board
  | 'map'                              // Geographic view
  | 'timeline'                         // Chronological timeline
  | 'analytics';                       // Dashboard widget view

type ViewLayout =
  | 'table'                            // Standard tabular
  | 'card_grid'                        // Card-based grid
  | 'compact_list'                     // Dense list (more items visible)
  | 'kanban_board'                     // Columns by status/stage
  | 'split_pane'                       // List + detail side by side
  | 'calendar_month'                   // Monthly calendar
  | 'calendar_week'                    // Weekly calendar
  | 'map_cluster';                     // Map with clustered pins

interface ViewScope {
  visibility: 'private' | 'team' | 'organization' | 'public';
  sharedWith?: string[];               // Team member IDs
  editableBy?: string[];               // Who can modify the view
  mandatory?: boolean;                 // Cannot be hidden (compliance)
  sourceViewId?: string;               // If derived from shared view
  personalOverrides?: PersonalOverride; // Local customizations to shared view
}

interface PersonalOverride {
  columns?: ColumnState[];             // Personal column selection
  sort?: SortConfig;                   // Personal sort preference
  filters?: FilterGroup;               // Additional personal filters
  // Inherited from shared view:
  // - Core filters (mandatory, not overridable)
  // - Name, icon, color
  // - View type
}

interface ViewStats {
  lastUsedAt: Date;
  usageCount: number;
  avgSessionDuration: number;          // Seconds
  lastResultCount: number;             // How many items matched
  lastLoadTime: number;                // Ms to render
}

interface ViewSchedule {
  enabled: boolean;
  frequency: 'daily' | 'weekly' | 'monthly';
  dayOfWeek?: number;                  // For weekly
  dayOfMonth?: number;                 // For monthly
  time: string;                        // "09:00" in agent's timezone
  format: 'email' | 'slack' | 'pdf';
  recipients: string[];
}

// View lifecycle:
// CREATE: Agent builds filters → Previews results → Names and saves
// USE: Click in sidebar → Load view → Apply filters → Render
// EDIT: Modify filters/sort → Auto-save (if owned) or "Save As" (if shared)
// SHARE: Set visibility → Invite team → Handle conflicts
// ARCHIVE: Unused for 30 days → Suggest archive → Remove from sidebar
// DELETE: Explicit action → Confirmation → Remove permanently

// View sidebar organization:
// ┌─────────────────────────────────────────┐
// │  Saved Views                              │
// │                                            │
// │  ★ My Active Trips (default)         [42] │
// │  🔴 Urgent Follow-ups                 [8] │
// │  🟢 Confirmed This Week              [12] │
// │  💰 High Value Pending                [5] │
// │                                            │
// │  Shared by Team                           │
// │  📋 Peak Season Queue (Rahul)        [23] │
// │  🏖️ Kerala December (Priya)          [15] │
// │                                            │
// │  Mandatory                                │
// │  ⚠️ Compliance Flags                 [2]  │
// │                                            │
// │  [+ Save Current View]                    │
// └─────────────────────────────────────────────┘
```

### Complex Filter Composition

```typescript
interface FilterGroup {
  operator: 'AND' | 'OR';
  conditions: FilterCondition[];
  groups?: FilterGroup[];              // Nested groups
}

interface FilterCondition {
  id: string;
  field: string;                       // "status", "destination", "price"
  operator: FilterOperator;
  value: any;
  negated: boolean;                    // NOT this condition
}

type FilterOperator =
  // Comparison
  | 'eq' | 'neq'
  | 'gt' | 'gte' | 'lt' | 'lte'
  | 'between'
  // Set
  | 'in' | 'not_in'
  // Text
  | 'contains' | 'not_contains'
  | 'starts_with' | 'ends_with'
  | 'matches_regex'
  // Date
  | 'relative_date'                    // "today", "this_week", "next_7_days"
  | 'absolute_date'                    // Specific date
  | 'date_between'
  | 'older_than'                       // "7d", "30d", "90d"
  // Existence
  | 'is_empty' | 'is_not_empty'
  | 'is_null' | 'is_not_null'
  // Special
  | 'assigned_to_me'
  | 'created_by_me'
  | 'in_my_team'
  | 'has_flag'                         // Has any flag of type
  | 'has_note';                        // Has agent notes

// Filterable fields by view type:
//
// INBOX (Trip listing):
// ─────────────────────────────────────
// Status           | eq, in, neq         | draft, pending, confirmed, cancelled
// Destination      | eq, in, contains    | "Kerala", "Goa", "Rajasthan"
// Trip Type        | eq, in              | honeymoon, family, adventure, corporate
// Price            | gt, lt, between     | ₹ range
// Assigned Agent   | eq, in, assigned_to_me
// Customer         | contains, eq        | Name search
// Created Date     | relative, between   | "today", "this_week", date range
// Updated Date     | relative, older_than| "last_24h", "7d"
// Last Message     | relative, older_than| When last customer message
// Source           | eq, in              | whatsapp, email, web, phone
// Priority         | eq, in              | 1-5
// Trip Dates       | between, relative   | Travel date range
// Duration         | gt, lt, between     | Number of nights
// Has Follow-up    | eq                  | true/false
// Has Flag         | has_flag            | urgent, vip, compliance, custom
// Has Note         | has_note            | Agent added notes
// Tags             | in, contains        | Custom tags
//
// CUSTOMER LIST:
// ─────────────────────────────────────
// Name             | contains            | Name search
// Email            | contains, eq        | Email search
// Phone            | contains, eq        | Phone search
// Total Trips      | gt, lt, between     | Trip count
// Total Spent      | gt, lt, between     | Lifetime value
// Last Trip Date   | relative, older_than| When last trip
// Customer Tier    | eq, in              | bronze, silver, gold, platinum
// Source           | eq, in              | How acquired
// Location         | contains, eq        | City, state
//
// MESSAGE QUEUE:
// ─────────────────────────────────────
// Channel          | eq, in              | whatsapp, email, sms, phone
// Direction        | eq                  | inbound, outbound
// Status           | eq, in              | unread, pending_reply, replied
// Customer         | contains, eq        | Name search
// Trip             | eq                  | Linked trip ID
// Priority         | eq, in              | auto-assigned or manual
// Age              | older_than          | "1h", "4h", "24h"
// Has Attachment   | eq                  | true/false
// Assigned Agent   | eq, assigned_to_me  | Who's handling

// Filter builder UI:
// ┌─────────────────────────────────────────┐
// │  Filter Builder                      [×] │
// │                                            │
// │  Match [ALL ▼] of the following:          │
// │                                            │
// │  ┌──────────────────────────────────────┐ │
// │  │ [Status ▼] [is ▼] [Pending ▼]   [×] │ │
// │  │ [Destination ▼] [is one of ▼]       │ │
// │  │   [Kerala, Goa, Rajasthan]       [×] │ │
// │  │ [Price ▼] [is greater than ▼]       │ │
// │  │   [₹50,000 ▼]                   [×] │ │
// │  │                                      │ │
// │  │ ┌─ OR group ──────────────────────┐  │ │
// │  │ │ [Last Message ▼] [older than ▼] │  │ │
// │  │ │   [24 hours ▼]              [×] │  │ │
// │  │ │ [Has Flag ▼] [is ▼] [Urgent]   │  │ │
// │  │ │                              [×] │  │ │
// │  │ └──────────────────────────────────┘  │ │
// │  │                                      │ │
// │  │ [+ Add Condition] [+ Add Group]      │ │
// │  └──────────────────────────────────────┘ │
// │                                            │
// │  Showing 23 of 156 trips                  │
// │  [Save as View] [Apply Once] [Reset]      │
// └─────────────────────────────────────────────┘
//
// Filter UX features:
// - Inline preview: Show result count as filters are built
// - Autosuggest: Suggest field values from actual data
// - Recent values: Show recently used values for each field
// - Filter chips: Applied filters shown as removable chips
// - Quick toggle: Click chip to negate (strikethrough = NOT)
// - Drag to reorder: Change AND/OR group nesting
// - Collapse groups: Nested OR groups can be collapsed
```

### Smart Filter Suggestions

```typescript
interface SmartFilterEngine {
  suggestions: FilterSuggestion[];
  contextFilters: ContextFilter[];
  autoViews: AutoView[];
}

interface FilterSuggestion {
  id: string;
  name: string;                        // "Follow-ups needed"
  description: string;                 // "3 trips haven't been replied to in 24h"
  filters: FilterGroup;
  relevance: number;                   // 0-1, how relevant right now
  trigger: SuggestionTrigger;
}

type SuggestionTrigger =
  | 'time_based'                       // "It's Monday morning → show weekend inquiries"
  | 'pattern_based'                    // "You always check Kerala trips at 10am"
  | 'anomaly_based'                    // "3 urgent flags appeared in the last hour"
  | 'workload_based'                   // "You have 5 trips with pending actions"
  | 'seasonal';                        // "Goa season starts in 2 weeks"

// Smart suggestion examples:
//
// TIME-BASED:
// Monday 9:00 AM:
// → "Weekend inquiries (12 new)" — trips created Sat-Sun without response
// → Show trips: createdAt BETWEEN Saturday AND Sunday AND lastMessageAt = null
//
// End of month:
// → "Closing soon (8 trips)" — trips with dates in next 2 weeks, not confirmed
// → Show trips: tripDates WITHIN next_14_days AND status != confirmed
//
// PATTERN-BASED:
// Agent always checks Kerala trips first:
// → "Your Kerala queue (6 trips)" — Suggest at login
// → Show trips: destination = Kerala AND assignedAgent = me AND status != confirmed
//
// Agent typically handles high-value trips in the morning:
// → "High value morning queue" — Appears at 10am
// → Show trips: price >= 100000 AND status = pending AND assignedAgent = me
//
// ANOMALY-BASED:
// Sudden spike in cancellations:
// → "Cancellation spike (4 today)" — Alert-worthy
// → Show trips: status = cancelled AND updatedAt = today
//
// VIP customer submitted inquiry:
// → "VIP inquiry from Rajesh K." — High priority customer
// → Show trips: customer.tier = platinum AND status = draft
//
// WORKLOAD-BASED:
// Agent has 15 pending trips (above normal):
// → "Workload: 15 pending" — Suggest prioritization
// → Show trips: status = pending AND assignedAgent = me
// → Sort by: price DESC, lastMessageAt ASC
//
// SEASONAL:
// December Kerala season approaching:
// → "Kerala December bookings (23 trips)" — Seasonal awareness
// → Show trips: destination = Kerala AND tripDates IN December

// Context filters (always available, one-click):
interface ContextFilter {
  id: string;
  label: string;                       // "My trips", "Today's"
  icon: string;
  filter: FilterCondition;
  shortcut?: string;                   // Keyboard shortcut
}

// Default context filters:
// [1] My Trips        → assignedAgent = me
// [2] Unassigned      → assignedAgent = null
// [3] Today's         → createdAt = today
// [4] This Week       → createdAt = this_week
// [5] Needs Reply     → lastMessageInbound = true AND repliedTo = false
// [6] Urgent          → priority >= 4 OR hasFlag = urgent
// [7] High Value      → price >= 100000
// [8] Closing Soon    → tripDates WITHIN next_14_days AND status != confirmed

// Auto-views (generated from patterns):
interface AutoView {
  id: string;
  name: string;                        // "Your typical morning"
  generatedFrom: UsagePattern;
  filters: FilterGroup;
  suggestedAt: Date;
  accepted: boolean;
}

interface UsagePattern {
  timeOfDay: string;                   // "09:00-11:00"
  dayOfWeek: number[];                 // [1,2,3,4,5] = weekdays
  topFilters: string[];                // Most used filter combinations
  avgResultCount: number;
  confidence: number;                  // 0-1, how consistent the pattern is
}

// Auto-view generation:
// 1. Track agent's filter usage for 2 weeks
// 2. Cluster similar filter combinations
// 3. Find time-based patterns (morning vs afternoon)
// 4. Generate auto-view with confidence score
// 5. If confidence > 0.7: Suggest as "Quick View"
// 6. Agent accepts → Becomes saved view
// 7. Agent ignores → Remove suggestion after 3 dismissals
```

### View Sharing & Team Coordination

```typescript
interface ViewSharingEngine {
  sharing: ViewSharing;
  coordination: TeamCoordination;
  conflictResolution: ViewConflictResolution;
}

interface ViewSharing {
  shareView(viewId: string, target: SharingTarget): SharedView;
  revokeAccess(viewId: string, targetId: string): void;
  updateSharedView(viewId: string, changes: Partial<SavedView>): SharedViewVersion;
}

interface SharingTarget {
  type: 'team' | 'individual' | 'role' | 'organization';
  id: string;
  permissions: SharingPermission;
}

type SharingPermission =
  | 'view_only'                        // Can use, can't modify
  | 'can_copy'                         // Can use and duplicate
  | 'can_edit_filters'                 // Can modify filters
  | 'full_edit';                       // Can modify everything

interface SharedViewVersion {
  viewId: string;
  version: number;
  changedBy: string;
  changedAt: Date;
  changes: string[];                   // What changed
  personalizationsAffected: number;    // How many agents had local overrides
}

// View sharing scenarios:
//
// SCENARIO 1: Manager creates "Peak Season Queue"
// Manager builds view → Shares with "Sales Team" (view_only)
// All team members see it in their sidebar under "Shared by Team"
// Manager updates filters → All team members get update notification
// Team members can sort/column-customize locally (personal overrides)
//
// SCENARIO 2: Agent creates useful view
// Agent Priya creates "Kerala Honeymoon" filter
// She shares with Rahul (can_copy)
// Rahul copies it → Gets his own version → Modifies for his style
// Original and copy are independent
//
// SCENARIO 3: Compliance-mandated view
// Admin creates "Regulatory Flags" view
// Set as mandatory: true
// All agents MUST see it, cannot hide or remove
// View pinned to sidebar with warning icon
// Any trip with compliance flag appears here
//
// SCENARIO 4: View update conflict
// Manager updates shared "Urgent Follow-ups" view:
// - Adds new filter: source IN (whatsapp, email)
// - 5 agents had the view with personal sort overrides
// - Each agent gets notification:
//   "Shared view 'Urgent Follow-ups' updated by Manager.
//    Your personal sort preference is preserved.
//    New filter added: Source is WhatsApp or Email.
//    [View Changes] [Dismiss]"
// - Personal overrides preserved; core filters updated

interface TeamCoordination {
  workloadBalance: WorkloadView;
  tripDistribution: DistributionView;
  handoffViews: HandoffView[];
}

// Workload balance view (manager):
// ┌─────────────────────────────────────────┐
// │  Team Workload                            │
// │                                            │
// │  Agent     Active  Pending  Confirmed  ▼  │
// │  ─────────────────────────────────────────│
// │  Priya     ●●●●●●●●● 12    5       18    │
// │  Rahul     ●●●●●●      6    8       15    │
// │  Amit      ●●●●●●●●●● 14    3       22    │ ← Overloaded
// │  Sana      ●●●●        4    4        8    │ ← Under-utilized
// │                                            │
// │  ⚠️ Amit has 14 pending (team avg: 9)     │
// │  💡 Consider reassigning 5 trips to Sana  │
// │  [Rebalance] [View Details]               │
// └─────────────────────────────────────────────┘
//
// Trip distribution view:
// Shows how trips are distributed across agents
// Group by: destination, status, source, customer tier
// Helps managers spot imbalance and reallocate

interface HandoffView {
  id: string;
  fromAgent: string;
  toAgent: string;
  reason: 'shift_end' | 'vacation' | 'sick' | 'reassignment';
  trips: HandoffTrip[];
  notes: string;
  createdAt: Date;
}

// Shift handoff view:
// When agent ends shift → Generate handoff summary:
// ┌─────────────────────────────────────────┐
// │  Shift Handoff: Priya → Rahul            │
// │                                            │
// │  Summary:                                  │
// │  12 trips handled, 8 confirmed, 2 pending │
// │                                            │
// │  Needs attention:                          │
// │  • TRV-45678: Rajesh, Kerala — Price nego │
// │  • TRV-45680: Amit, Goa — Awaiting visa   │
// │  • TRV-45682: Sana, Rajasthan — VIP alert │
// │                                            │
// │  In progress:                              │
// │  • TRV-45679: Kerala itinerary draft ready │
// │  • TRV-45681: Thailand quotes requested    │
// │                                            │
// │  Notes:                                    │
// │  "Rajesh wants discount on Kerala trip.    │
// │   Check with manager for 10% approval."    │
// │                                            │
// │  [Accept Handoff] [Review All Trips]       │
// └─────────────────────────────────────────────┘
```

### View Performance at Scale

```typescript
interface ViewPerformance {
  caching: ViewCache;
  precomputation: PrecomputedView;
  pagination: SmartPagination;
  indexing: FilterIndex;
}

interface ViewCache {
  // Client-side cache (IndexedDB):
  // - Last view results cached locally
  // - Show cached results instantly while fetching fresh
  // - Cache invalidated by: trip update, filter change, manual refresh
  // - Max cache size: 50 MB
  //
  // Server-side cache (Redis):
  // - Popular views pre-computed and cached
  // - Cache key: viewId + agentId + filter hash
  // - TTL: 30 seconds for active views, 5 minutes for idle
  // - Invalidation: Trip CRUD events invalidate relevant caches
  // - Warm-up: Pre-compute top 20 most-used views on schedule

  strategy: 'cache_first' | 'network_first' | 'stale_while_revalidate';
  maxAge: number;
  staleWhileRevalidate: boolean;
}

// Precomputed views for common filters:
// Pre-compute and materialize:
// 1. "My Active Trips" — Every agent's default view
//    Refresh: Every 30 seconds
//    Storage: Redis sorted set by updatedAt
//
// 2. "Status counts" — For badges in sidebar
//    Refresh: Every 15 seconds
//    Storage: Redis hash {status: count}
//
// 3. "Urgent flags" — Compliance-mandated
//    Refresh: Immediate on flag change
//    Storage: Redis set + change stream
//
// 4. "Team workload" — Manager dashboard
//    Refresh: Every 60 seconds
//    Storage: Redis sorted set per agent

interface SmartPagination {
  // Cursor-based pagination (not offset-based):
  // - Offset pagination slow on large datasets (skip 5000 rows)
  // - Cursor: Last seen sort value + ID
  // - Stable across inserts/deletes
  //
  // Adaptive page size:
  // - Default: 25 items
  // - Fast connection: 50 items
  // - Slow connection: 10 items
  // - Mobile: 10 items
  //
  // Prefetch:
  // - When user is on page 1, prefetch page 2 in background
  // - If user scrolls near bottom, prefetch next page
  //
  // Infinite scroll vs pagination:
  // - Inbox: Infinite scroll (trip list)
  // - Reports: Pagination (documented navigation)
  // - Calendar: Date-based (not page-based)

  mode: 'cursor' | 'offset' | 'date_range';
  pageSize: number;
  prefetchPages: number;
}

interface FilterIndex {
  // Database indexes for common filter combinations:
  // 1. (status, assignedAgent, updatedAt) — Default inbox sort
  // 2. (destination, status, tripDates) — Destination-based queries
  // 3. (customer.tier, status) — VIP customer queries
  // 4. (price, status) — High-value queries
  // 5. (source, createdAt) — Source-based queries
  // 6. (lastMessageAt, status) — Follow-up queries
  // 7. (priority, assignedAgent) — Priority queries
  // 8. GIN index on tags — Tag-based queries
  //
  // Full-text search:
  // - PostgreSQL tsvector on: customer name, destination, trip notes
  // - Trigram index on: customer name (fuzzy search)
  // - Search across: trips, customers, messages, documents
  //
  // Performance targets:
  // - Filtered view with 10K trips: <200ms
  // - Simple filter (status + agent): <50ms
  // - Full-text search: <100ms
  // - Badge count refresh: <30ms
}
```

---

## Open Problems

1. **Filter complexity ceiling** — Non-technical agents may struggle with nested AND/OR groups. A guided filter builder with natural language ("show me urgent Kerala trips from this week") could help, but translating NL to structured filters is imperfect.

2. **Shared view personalization conflicts** — When a manager updates a shared view's core filters, agents who had added personal filters on top may get unexpected results. A layered override system (base + personal) requires clear UX to show what's inherited vs. personal.

3. **Smart suggestion accuracy** — Pattern-based suggestions require 2+ weeks of usage data to be meaningful. New agents get generic suggestions, which may be unhelpful. Bootstrapping from team patterns could work but raises privacy questions.

4. **View explosion** — Agents creating dozens of saved views leads to sidebar clutter. Auto-archiving unused views and smart grouping helps, but determining "unused" is tricky — a seasonal view used once a year is still valuable.

5. **Cross-view consistency** — A trip appearing in multiple views (e.g., "Urgent" and "Kerala") may be acted on in one view but the other view doesn't update immediately. Real-time cross-view synchronization is expensive but necessary for avoiding duplicate work.

---

## Next Steps

- [ ] Design saved view persistence layer with server-side storage and client caching
- [ ] Build filter composition engine with nested AND/OR support
- [ ] Implement smart filter suggestion engine with usage pattern learning
- [ ] Create view sharing system with layered personalization
- [ ] Study saved views in Linear, Notion, ClickUp, Airtable, Salesforce list views
