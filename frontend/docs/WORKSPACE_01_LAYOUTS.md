# Workspace Customization & Agent Productivity — Layouts & Views

> Research document for agent workspace personalization, saved views, dashboard configuration, and workspace preset management.

---

## Key Questions

1. **How do agents customize their workspace layout for maximum productivity?**
2. **What saved view and filter system supports diverse workflows?**
3. **How do workspace presets enable shared configurations across teams?**
4. **What responsive layout system adapts to different screen sizes and roles?**
5. **How do we persist and sync workspace preferences across devices?**

---

## Research Areas

### Workspace Layout System

```typescript
interface WorkspaceLayout {
  id: string;
  agentId: string;
  name: string;                        // "My Daily Driver", "Weekend Warrior"
  panels: PanelConfig[];
  sidebar: SidebarConfig;
  toolbar: ToolbarConfig;
  keyboard: KeyboardProfile;
  theme: ThemeConfig;
  createdAt: Date;
  updatedAt: Date;
}

interface PanelConfig {
  id: string;
  type: PanelType;
  position: PanelPosition;
  size: PanelSize;
  visible: boolean;
  pinned: boolean;
  collapsed: boolean;
}

type PanelType =
  | 'inbox'                            // Trip listing with filters
  | 'intake'                           // Customer inquiry packet
  | 'trip_builder'                      // Trip assembly workspace
  | 'timeline'                          // Trip activity timeline
  | 'decision'                          // Decision and risk panel
  | 'output'                            // Document generation
  | 'messages'                          // Communication hub
  | 'customer_profile'                  // Customer detail sidebar
  | 'analytics'                         // Mini analytics dashboard
  | 'calendar'                          // Trip calendar view
  | 'tasks'                             // Task list
  | 'knowledge'                         // Knowledge base quick search
  | 'notes';                            // Personal scratchpad

interface PanelPosition {
  zone: 'main' | 'left' | 'right' | 'bottom';
  order: number;                       // Within zone
  tab?: number;                        // Tab index within panel group
}

interface PanelSize {
  width: string;                       // "400px", "30%", "flex"
  height: string;
  minWidth: string;
  maxWidth: string;
  resizable: boolean;
}

// Workspace layout presets:
//
// PRESET 1: "Inbox Focus" (Default for new agents)
// ┌──────────────────────────────────────────────────────┐
// │ [Sidebar]  │         Inbox (Full Width)              │
// │            │                                          │
// │ Inbox ●    │  Trip list with filters                 │
// │ Trips      │  ┌─────────────────────────────────────┐│
// │ Customers  │  │ TRV-45678 Kerala  │ Confirmed  │ ₹48K││
// │ Calendar   │  │ TRV-45679 Goa     │ Pending    │ ₹32K││
// │ Analytics  │  │ TRV-45680 Rajasthan│ Draft     │ --  ││
// │ Settings   │  └─────────────────────────────────────┘│
// └──────────────────────────────────────────────────────┘
//
// PRESET 2: "Trip Builder" (Active trip editing)
// ┌──────────┬──────────────────────┬──────────────────┐
// │ [Inbox]  │   Trip Builder       │  Customer Info   │
// │          │                      │                  │
// │ 3 new    │  Kerala Trip         │  Rajesh Sharma   │
// │          │  Hotel: Taj Palace   │  📞 +91-98765... │
// │          │  Flight: AI-123      │  Past trips: 3   │
// │          │  Activities: ...     │  Preferences:    │
// │          │                      │   Beach, Luxury  │
// │          │  [Save] [Publish]    │  Budget: ₹50K    │
// └──────────┴──────────────────────┴──────────────────┘
//
// PRESET 3: "Power Agent" (3-panel, experienced agents)
// ┌──────────┬──────────────────────┬──────────────────┐
// │ Inbox    │   Active Panel       │  Context Panel   │
// │ (compact)│   (tabbed)           │  (tabbed)        │
// │          │                      │                  │
// │ j/k nav  │  [Intake|Trip|Out]   │  [Msg|Cust|Note] │
// │          │                      │                  │
// │ 12 trips │  Current tab content │  Context info    │
// └──────────┴──────────────────────┴──────────────────┘
//
// PRESET 4: "Communication Hub" (High message volume)
// ┌──────────────────────────────────────────────────────┐
// │ [Sidebar]  │         Messages (Full Width)           │
// │            │                                          │
// │ Inbox      │  ┌─────────────────────────────────────┐│
// │ Messages ● │  │ WhatsApp: Rajesh (3 new)            ││
// │ Trips      │  │ Email: Priya (booking query)        ││
// │            │  │ SMS: Amit (flight change)            ││
// │            │  ├─────────────────────────────────────┤│
// │            │  │ Conversation thread                  ││
// │            │  │ [Reply with template] [Create trip]  ││
// └────────────┴──┴─────────────────────────────────────┘│
//
// PRESET 5: "Split Screen" (Dual monitor)
// ┌─────────────────────┬─────────────────────────────┐
// │  Monitor 1          │  Monitor 2                   │
// │  Inbox + Customer   │  Trip Builder + Documents    │
// │                     │                              │
// │  Trip list on left  │  Full trip editing on right  │
// │  Customer sidebar   │  Output generation panel     │
// └─────────────────────┴─────────────────────────────┘
//
// Layout persistence:
// - Saved per agent in user preferences
// - Synced across devices (laptop, desktop, tablet)
// - Auto-save on layout changes (panel resize, reorder)
// - Named presets: Agent can create multiple and switch
// - Team presets: Manager can share layout with team
// - Device-aware: Different layout for laptop vs. desktop

interface SidebarConfig {
  position: 'left' | 'right' | 'hidden';
  width: 'narrow' | 'standard' | 'wide'; // 48px, 240px, 320px
  collapsed: boolean;
  items: SidebarItem[];
  quickActions: QuickAction[];
}

interface SidebarItem {
  id: string;
  type: 'navigation' | 'filter' | 'widget' | 'separator';
  icon: string;
  label: string;
  badge?: number;                      // Unread count, pending tasks
  shortcut?: string;                   // Keyboard shortcut
  route?: string;
  visible: boolean;
  pinned: boolean;
}

// Sidebar customization:
// Default items:
// 1. Inbox (trips) — Badge: 5 new
// 2. Messages — Badge: 3 unread
// 3. Calendar — Today's trips
// 4. Tasks — Badge: 2 pending
// 5. Customers — Quick search
// 6. Analytics — Mini charts
// 7. Knowledge Base — Search
// 8. Settings — Config
//
// Agents can:
// - Reorder items (drag-and-drop)
// - Hide items they don't use
// - Add custom quick filters as sidebar items
// - Pin favorite trips to sidebar for quick access
//
// Quick actions (bottom of sidebar):
// [+] New Trip | [💬] New Message | [📋] Templates
// Customizable: Agent picks their top 3 quick actions
```

### Saved Views & Filters

```typescript
interface SavedView {
  id: string;
  name: string;                        // "My Hot Leads"
  description?: string;
  type: ViewType;
  filters: FilterConfig[];
  sort: SortConfig;
  columns: ColumnConfig[];
  groupBy?: string;
  color?: string;                      // Visual label color
  icon?: string;                       // Custom icon
  isDefault: boolean;
  isShared: boolean;                   // Shared with team
  sharedWith?: string[];               // Team member IDs
  lastUsedAt: Date;
  usageCount: number;
}

type ViewType =
  | 'inbox'                            // Trip listing view
  | 'customer_list'                    // Customer listing
  | 'message_queue'                    // Communication queue
  | 'task_list'                        // Task management
  | 'calendar'                         // Calendar view
  | 'analytics';                       // Analytics dashboard

interface FilterConfig {
  field: string;                       // "status", "destination", "assignedAgent"
  operator: FilterOperator;
  value: any;
  AND?: FilterConfig[];
  OR?: FilterConfig[];
}

type FilterOperator =
  | 'eq' | 'neq' | 'gt' | 'gte' | 'lt' | 'lte'
  | 'in' | 'not_in' | 'contains' | 'starts_with'
  | 'between' | 'is_empty' | 'is_not_empty'
  | 'relative_date';                   // "today", "this_week", "next_7_days"

// Saved view examples:
//
// "My Active Trips" (personal default):
// Filters: assignedAgent = me AND status IN (draft, pending, confirmed)
// Sort: updatedAt DESC
// Columns: Customer, Destination, Dates, Status, Price, Actions
//
// "Urgent Follow-ups" (shared with team):
// Filters: status = pending AND (lastMessageAt < -24h OR flag = urgent)
// Sort: lastMessageAt ASC (oldest first — tackle overdue first)
// Color: Red
// Badge: Count of matching trips
//
// "Honeymoon Kerala December" (seasonal filter):
// Filters: destination = Kerala AND type = honeymoon AND dates = December
// Sort: price DESC
// Shared: Yes (whole team uses during Kerala season)
//
// "High-Value Pending" (manager view):
// Filters: status = pending AND price >= 100000
// Sort: price DESC
// Columns: Customer, Trip, Price, Assigned Agent, Days Pending
//
// "New This Week" (pipeline view):
// Filters: createdAt >= this_week
// Sort: createdAt DESC
// Group by: assignedAgent (see distribution across team)

interface ColumnConfig {
  field: string;
  label: string;
  width: string;                       // "auto", "120px", "15%"
  visible: boolean;
  sortable: boolean;
  sticky?: 'left' | 'right';          // Fixed column on scroll
  format?: ColumnFormat;
}

type ColumnFormat =
  | 'text' | 'number' | 'currency' | 'date' | 'relative_time'
  | 'status_badge' | 'avatar' | 'progress_bar' | 'tags'
  | 'rating' | 'priority';

// Column configuration for inbox:
// Available columns (agent picks which to show):
// ☐ Checkbox (bulk select)
// ☐ Priority (1-5 colored dots)
// ☐ Status badge (Draft/Pending/Confirmed/Cancelled)
// ☐ Customer name + avatar
// ☐ Destination
// ☐ Trip dates
// ☐ Duration (nights)
// ☐ Price (₹)
// ☐ Assigned agent + avatar
// ☐ Last message (relative: "2h ago")
// ☐ Last updated
// ☐ Created date
// ☐ Trip type (honeymoon, family, adventure)
// ☐ Source (WhatsApp, Email, Web)
// ☐ Tags
// ☐ Quick actions (archive, assign, reply)
//
// Mobile columns (limited to 3):
// Customer name, destination, status badge
// Tap to expand full trip detail

// View sharing and team presets:
interface TeamPreset {
  id: string;
  name: string;                        // "Standard Agent Setup"
  createdBy: string;                   // Manager ID
  views: SavedView[];
  layout: WorkspaceLayout;
  sidebar: SidebarConfig;
  mandatory: boolean;                  // Agents can't customize (compliance)
}

// Team preset scenarios:
// 1. Manager creates "Onboarding" preset for new agents:
//    - Simplified sidebar (fewer items)
//    - "My Trips" view as default
//    - Knowledge base pinned
//    - Mentor's calendar visible
//
// 2. Manager creates "Peak Season" preset:
//    - Communication-heavy layout
//    - "Urgent Follow-ups" view pinned
//    - Template quick access
//    - Analytics widget for booking pace
//
// 3. Compliance-mandated "Audit View":
//    - Mandatory: All trips with compliance flags
//    - Cannot be hidden or modified
//    - Required for regulatory agencies
```

### Dashboard Widgets

```typescript
interface DashboardWidget {
  id: string;
  type: WidgetType;
  title: string;
  position: WidgetPosition;
  size: WidgetSize;
  config: WidgetConfig;
  refreshInterval: number;             // Seconds (0 = manual)
  dataSource: string;
}

type WidgetType =
  | 'metric_card'                      // Single number + trend
  | 'mini_chart'                       // Small line/bar chart
  | 'trip_pipeline'                    // Kanban-style trip stages
  | 'recent_messages'                  // Latest messages feed
  | 'upcoming_trips'                   // Calendar-style next trips
  | 'revenue_tracker'                  // Revenue vs. target
  | 'task_list'                        // Personal tasks
  | 'quick_actions'                    // Customizable action buttons
  | 'leaderboard'                      // Agent performance ranking
  | 'destination_popularity'           // Trending destinations
  | 'conversion_funnel'                // Inquiry → Booking funnel
  | 'clock';                           // World clock for destinations

// Widget examples:
//
// METRIC CARD: "Trips This Month"
// ┌─────────────────────┐
// │  Trips This Month    │
// │  42                  │
// │  ↑ 12% vs last month│
// │  Target: 50 (84%)    │
// └─────────────────────┘
//
// MINI CHART: "Revenue Trend"
// ┌─────────────────────┐
// │  Revenue (30 days)   │
// │  ▁▂▃▅▇█▇▅▆▇██▇▅▃  │
// │  ₹18.2L this month  │
// └─────────────────────┘
//
// TRIP PIPELINE: "My Pipeline"
// ┌─────────────────────┐
// │  Draft: 5 → Pending: 8 → Confirmed: 12 │
// │  ●●●●●  ●●●●●●●●  ●●●●●●●●●●●● │
// └─────────────────────┘
//
// UPCOMING TRIPS: "Next 7 Days"
// ┌─────────────────────┐
// │  Tue: Rajesh → Goa  │
// │  Thu: Priya → Kerala│
// │  Sat: Amit → Jaipur │
// └─────────────────────┘
//
// Dashboard layout:
// Agents drag-and-drop widgets onto a grid
// Grid: 4 columns on desktop, 2 on tablet, 1 on mobile
// Widgets snap to grid cells (1x1, 2x1, 2x2, 4x1 sizes)
// Each widget configurable (data source, refresh rate, display options)
```

---

## Open Problems

1. **Layout complexity vs. simplicity** — Too many customization options overwhelm new agents. Too few frustrate power users. A progressive disclosure approach (basic layout for new agents, advanced options unlock over time) is needed.

2. **Cross-device layout sync** — A layout optimized for a 27" monitor doesn't work on a 13" laptop or tablet. Auto-adapting layouts (responsive breakpoints) while preserving the agent's intent is challenging.

3. **View performance at scale** — Complex saved views with multiple filters on 10,000+ trips can be slow. Pre-computing view results or using database materialized views may be needed for popular filters.

4. **Shared view conflicts** — When a manager updates a shared view, all team members see the change. If an agent had personalized the shared view, their customizations may be lost. Version-aware sharing is needed.

5. **Widget data freshness** — Real-time widgets (messages, pipeline) need frequent updates, impacting performance. Balancing freshness with API load requires intelligent polling (only refresh visible widgets).

---

## Next Steps

- [ ] Build workspace layout system with drag-and-drop panel management
- [ ] Create saved view engine with complex filter support
- [ ] Design dashboard widget framework with grid layout
- [ ] Implement team preset sharing with progressive disclosure
- [ ] Study workspace customization (Linear, Notion, ClickUp, Jira dashboards, Salesforce Lightning)
