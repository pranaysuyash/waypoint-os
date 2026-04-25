# INBOX_04: Personalization Deep Dive

> Inbox Management System — Custom Views, Preferences, and Agent Personalization

---

## Table of Contents

1. [Overview](#overview)
2. [Personalization Philosophy](#personalization-philosophy)
3. [Saved Views System](#saved-views-system)
4. [User Preferences](#user-preferences)
5. [Agent Workflow Customization](#agent-workflow-customization)
6. [Smart Defaults](#smart-defaults)
7. [Collaborative Features](#collaborative-features)
8. [Implementation Architecture](#implementation-architecture)

---

## Overview

The Inbox personalization system enables each agent to tailor their workspace to their role, workflow, and preferences while maintaining team consistency and operational efficiency.

### Personalization Dimensions

```
┌────────────────────────────────────────────────────────────────────────────┐
│                      INBOX PERSONALIZATION LAYERS                          │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │  LAYER 1: GLOBAL DEFAULTS                                            │ │
│  │  • Agency-wide defaults                                              │ │
│  │  • Admin-configured settings                                         │ │
│  │  • Minimum viable configuration for new users                        │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                  │                                         │
│                                  ▼                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │  LAYER 2: ROLE-BASED OVERRIDES                                       │ │
│  │  • Senior Agent vs Junior Agent presets                              │ │
│  │  • Specialist vs Generalist settings                                 │ │
│  │  • Team-specific configurations                                      │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                  │                                         │
│                                  ▼                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │  LAYER 3: INDIVIDUAL PREFERENCES                                     │ │
│  │  • User-chosen settings                                              │ │
│  │  • Custom saved views                                                │ │
│  │  • Personal workflow configurations                                  │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                  │                                         │
│                                  ▼                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │  LAYER 4: CONTEXT-AWARE ADAPTATIONS                                  │ │
│  │  • Time-of-day adjustments                                           │ │
│  │  • Workload-based suggestions                                        │ │
│  │  • Learned patterns                                                  │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│  Resolution Priority: Individual > Role > Global (Context always applies) │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Personalization Philosophy

### Core Principles

```
┌────────────────────────────────────────────────────────────────────────────┐
│                     PERSONALIZATION DESIGN PRINCIPLES                      │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  1. Sane Defaults, Optional Customization                                  │
│     ┌─────────────────────────────────────────────────────────────────┐  │
│     │ • System works great out of the box                             │  │
│     │ • No configuration required for basic use                       │  │
│     │ • Power users can dive deep when needed                         │  │
│     └─────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  2. Discoverable, Not Hidden                                               │
│     ┌─────────────────────────────────────────────────────────────────┐  │
│     │ • Customization options are visible, not buried                 │  │
│     │ • Clear visual indicators when something is customized          │  │
│     │ • Easy to return to defaults                                    │  │
│     └─────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  3. Shareable, Not Siloed                                                  │
│     ┌─────────────────────────────────────────────────────────────────┐  │
│     │ • Saved views can be shared across team                         │  │
│     │ • Team templates for common workflows                           │  │
│     │ • Learn from others' configurations                             │  │
│     └─────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  4. Adaptive, Not Static                                                   │
│     ┌─────────────────────────────────────────────────────────────────┐  │
│     │ • System learns from usage patterns                            │  │
│     │ • Suggestions based on workflow                                │  │
│     │ • Gradual enhancement vs. configuration overload               │  │
│     └─────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  5. Respects Cognitive Load                                                │
│     ┌─────────────────────────────────────────────────────────────────┐  │
│     │ • Don't overwhelm with options                                  │  │
│     │ • Progressive disclosure of advanced features                   │  │
│     │ • Clear grouping of related settings                            │  │
│     └─────────────────────────────────────────────────────────────────┘  │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### What Gets Personalized

| Category | Elements | Default Behavior |
|----------|----------|------------------|
| **View Mode** | List, Table, Kanban, Timeline, Calendar | List (compact) |
| **Sort Order** | Priority, Date, Customer, Duration | Smart Sort (priority score) |
| **Filters** | Status, Priority, Channel, Assignee | None (show all active) |
| **Columns** | Visible fields, column order | Default set (7 columns) |
| **Density** | Compact, Comfortable, Spacious | Comfortable |
| **Theme** | Light, Dark, System | System |
| **Notifications** | Desktop, Mobile, Email | Agency defaults |
| **Quick Actions** | Pinned actions, shortcuts | Default set |

---

## Saved Views System

### View Definition

```typescript
// types/views.ts
interface SavedView {
  id: string;
  name: string;
  description?: string;
  owner: {
    type: 'user' | 'team' | 'agency';
    id: string;
    name: string;
  };
  visibility: 'private' | 'team' | 'agency';

  // View configuration
  config: ViewConfig;

  // Metadata
  createdAt: Date;
  updatedAt: Date;
  lastUsedAt?: Date;
  usageCount: number;
  isDefault: boolean;
  isPinned: boolean;
  tags: string[];
}

interface ViewConfig {
  // Core view settings
  mode: ViewMode;
  density: 'compact' | 'comfortable' | 'spacious';

  // Sorting
  sortBy: SortField;
  sortOrder: 'asc' | 'desc';
  secondarySort?: {
    sortBy: SortField;
    sortOrder: 'asc' | 'desc';
  };

  // Filtering
  filters: ViewFilter[];
  quickFilter?: string; // Search query

  // Display options (mode-specific)
  displayOptions: DisplayOptions;

  // Actions available in this view
  allowedActions: string[];
}

type ViewMode = 'list' | 'table' | 'kanban' | 'timeline' | 'calendar';

type SortField =
  | 'priority_score'
  | 'created_at'
  | 'updated_at'
  | 'customer_name'
  | 'departure_date'
  | 'duration'
  | 'agent_assigned'
  | 'status';

interface ViewFilter {
  field: string;
  operator: FilterOperator;
  value: FilterValue;
  enabled: boolean;
}

type FilterOperator =
  | 'equals'
  | 'not_equals'
  | 'contains'
  | 'not_contains'
  | 'starts_with'
  | 'ends_with'
  | 'in'
  | 'not_in'
  | 'between'
  | 'greater_than'
  | 'less_than'
  | 'is_empty'
  | 'is_not_empty'
  | 'before'
  | 'after'
  | 'within_last'
  | 'within_next';

type FilterValue = string | number | boolean | string[] | DateFilter;

interface DateFilter {
  unit: 'minutes' | 'hours' | 'days' | 'weeks' | 'months';
  value: number;
}

interface DisplayOptions {
  // Table/List mode
  columns?: ColumnConfig[];

  // Kanban mode
  groupBy?: 'status' | 'priority' | 'agent' | 'channel';
  collapsedGroups?: string[];

  // Timeline mode
  timeScale?: 'day' | 'week' | 'month';
  showWeekends?: boolean;

  // Calendar mode
  calendarView?: 'month' | 'week' | 'day';

  // All modes
  showArchived?: boolean;
  maxResults?: number;
}

interface ColumnConfig {
  field: string;
  label: string;
  width?: number;
  visible: boolean;
  sortable: boolean;
  format?: ColumnFormat;
}

type ColumnFormat =
  | 'text'
  | 'number'
  | 'currency'
  | 'date'
  | 'datetime'
  | 'duration'
  | 'percentage'
  | 'badge'
  | 'avatar';
```

### Predefined Views

```typescript
// views/predefined.ts
export const PREDEFINED_VIEWS: Omit<SavedView, 'id' | 'createdAt' | 'updatedAt'>[] = [
  // === Core Views ===
  {
    name: 'All Trips',
    description: 'All active trips in your inbox',
    owner: { type: 'agency', id: 'system', name: 'System' },
    visibility: 'agency',
    config: {
      mode: 'list',
      density: 'comfortable',
      sortBy: 'priority_score',
      sortOrder: 'desc',
      filters: [
        { field: 'status', operator: 'in', value: ['new', 'assigned', 'in_progress'], enabled: true },
      ],
      displayOptions: {},
      allowedActions: ['view', 'assign', 'archive', 'escalate'],
    },
    isDefault: true,
    isPinned: true,
    usageCount: 0,
    tags: ['core'],
  },
  {
    name: 'My Assignments',
    description: 'Trips assigned to you',
    owner: { type: 'agency', id: 'system', name: 'System' },
    visibility: 'agency',
    config: {
      mode: 'list',
      density: 'comfortable',
      sortBy: 'priority_score',
      sortOrder: 'desc',
      filters: [
        { field: 'assigned_to', operator: 'equals', value: '{{currentUser.id}}', enabled: true },
        { field: 'status', operator: 'in', value: ['assigned', 'in_progress'], enabled: true },
      ],
      displayOptions: {},
      allowedActions: ['view', 'start', 'complete', 'escalate'],
    },
    isDefault: false,
    isPinned: true,
    usageCount: 0,
    tags: ['core', 'mine'],
  },
  {
    name: 'Unassigned',
    description: 'Trips waiting for assignment',
    owner: { type: 'agency', id: 'system', name: 'System' },
    visibility: 'agency',
    config: {
      mode: 'list',
      density: 'comfortable',
      sortBy: 'priority_score',
      sortOrder: 'desc',
      filters: [
        { field: 'assigned_to', operator: 'is_empty', value: null, enabled: true },
        { field: 'status', operator: 'equals', value: 'new', enabled: true },
      ],
      displayOptions: {},
      allowedActions: ['view', 'claim', 'assign'],
    },
    isDefault: false,
    isPinned: true,
    usageCount: 0,
    tags: ['core', 'unassigned'],
  },

  // === Priority Views ===
  {
    name: 'Critical',
    description: 'Urgent trips requiring immediate attention',
    owner: { type: 'agency', id: 'system', name: 'System' },
    visibility: 'agency',
    config: {
      mode: 'list',
      density: 'compact',
      sortBy: 'created_at',
      sortOrder: 'asc',
      filters: [
        { field: 'priority', operator: 'equals', value: 'critical', enabled: true },
        { field: 'status', operator: 'not_in', value: ['closed', 'archived'], enabled: true },
      ],
      displayOptions: {},
      allowedActions: ['view', 'start', 'escalate'],
    },
    isDefault: false,
    isPinned: true,
    usageCount: 0,
    tags: ['priority'],
  },
  {
    name: 'High Priority',
    description: 'High-priority trips',
    owner: { type: 'agency', id: 'system', name: 'System' },
    visibility: 'agency',
    config: {
      mode: 'list',
      density: 'comfortable',
      sortBy: 'priority_score',
      sortOrder: 'desc',
      filters: [
        { field: 'priority', operator: 'equals', value: 'high', enabled: true },
        { field: 'status', operator: 'not_in', value: ['closed', 'archived'], enabled: true },
      ],
      displayOptions: {},
      allowedActions: ['view', 'start', 'complete'],
    },
    isDefault: false,
    isPinned: false,
    usageCount: 0,
    tags: ['priority'],
  },

  // === Status Views ===
  {
    name: 'Stalled',
    description: 'Trips with no activity for 3+ days',
    owner: { type: 'agency', id: 'system', name: 'System' },
    visibility: 'agency',
    config: {
      mode: 'list',
      density: 'comfortable',
      sortBy: 'updated_at',
      sortOrder: 'asc',
      filters: [
        { field: 'updated_at', operator: 'within_last', value: { unit: 'days', value: -3 }, enabled: true },
        { field: 'status', operator: 'in', value: ['assigned', 'in_progress'], enabled: true },
      ],
      displayOptions: {},
      allowedActions: ['view', 'nudge', 'reassign', 'escalate'],
    },
    isDefault: false,
    isPinned: false,
    usageCount: 0,
    tags: ['status', 'attention'],
  },
  {
    name: 'Awaiting Customer',
    description: 'Trips waiting for customer response',
    owner: { type: 'agency', id: 'system', name: 'System' },
    visibility: 'agency',
    config: {
      mode: 'list',
      density: 'comfortable',
      sortBy: 'updated_at',
      sortOrder: 'asc',
      filters: [
        { field: 'awaiting_customer', operator: 'equals', value: true, enabled: true },
      ],
      displayOptions: {},
      allowedActions: ['view', 'follow_up', 'close'],
    },
    isDefault: false,
    isPinned: false,
    usageCount: 0,
    tags: ['status'],
  },

  // === Type Views ===
  {
    name: 'Quote Requests',
    description: 'New quote requests',
    owner: { type: 'agency', id: 'system', name: 'System' },
    visibility: 'agency',
    config: {
      mode: 'table',
      density: 'comfortable',
      sortBy: 'created_at',
      sortOrder: 'desc',
      filters: [
        { field: 'trip_type', operator: 'equals', value: 'quote_request', enabled: true },
        { field: 'status', operator: 'equals', value: 'new', enabled: true },
      ],
      displayOptions: {
        columns: [
          { field: 'customer_name', label: 'Customer', visible: true, sortable: true },
          { field: 'destination', label: 'Destination', visible: true, sortable: true },
          { field: 'departure_date', label: 'Departure', visible: true, sortable: true, format: 'date' },
          { field: 'duration', label: 'Duration', visible: true, sortable: true },
          { field: 'budget', label: 'Budget', visible: true, sortable: true, format: 'currency' },
          { field: 'created_at', label: 'Created', visible: true, sortable: true, format: 'datetime' },
          { field: 'priority', label: 'Priority', visible: true, sortable: true, format: 'badge' },
        ],
      },
      allowedActions: ['view', 'start', 'assign'],
    },
    isDefault: false,
    isPinned: false,
    usageCount: 0,
    tags: ['type'],
  },
  {
    name: 'Bookings',
    description: 'Active booking requests',
    owner: { type: 'agency', id: 'system', name: 'System' },
    visibility: 'agency',
    config: {
      mode: 'kanban',
      density: 'comfortable',
      sortBy: 'priority_score',
      sortOrder: 'desc',
      filters: [
        { field: 'trip_type', operator: 'in', value: ['booking_request', 'booking_in_progress'], enabled: true },
      ],
      displayOptions: {
        groupBy: 'status',
        columns: [
          { field: 'customer_name', label: 'Customer', visible: true, sortable: true },
          { field: 'destination', label: 'Destination', visible: true, sortable: true },
          { field: 'departure_date', label: 'Departure', visible: true, sortable: true, format: 'date' },
        ],
      },
      allowedActions: ['view', 'update_status', 'complete'],
    },
    isDefault: false,
    isPinned: false,
    usageCount: 0,
    tags: ['type'],
  },

  // === Specialized Views ===
  {
    name: 'Today\'s Departures',
    description: 'Trips with departures in the next 24 hours',
    owner: { type: 'agency', id: 'system', name: 'System' },
    visibility: 'agency',
    config: {
      mode: 'list',
      density: 'compact',
      sortBy: 'departure_date',
      sortOrder: 'asc',
      filters: [
        { field: 'departure_date', operator: 'within_next', value: { unit: 'days', value: 1 }, enabled: true },
      ],
      displayOptions: {
        columns: [
          { field: 'customer_name', label: 'Customer', visible: true, sortable: true },
          { field: 'destination', label: 'Destination', visible: true, sortable: true },
          { field: 'departure_date', label: 'Departs', visible: true, sortable: true, format: 'datetime' },
          { field: 'agent_assigned', label: 'Agent', visible: true, sortable: true },
        ],
      },
      allowedActions: ['view', 'contact'],
    },
    isDefault: false,
    isPinned: false,
    usageCount: 0,
    tags: ['temporal', 'attention'],
  },
  {
    name: 'International',
    description: 'International trips requiring special handling',
    owner: { type: 'agency', id: 'system', name: 'System' },
    visibility: 'agency',
    config: {
      mode: 'table',
      density: 'comfortable',
      sortBy: 'departure_date',
      sortOrder: 'asc',
      filters: [
        { field: 'is_international', operator: 'equals', value: true, enabled: true },
        { field: 'status', operator: 'not_in', value: ['closed', 'archived'], enabled: true },
      ],
      displayOptions: {
        columns: [
          { field: 'customer_name', label: 'Customer', visible: true, sortable: true },
          { field: 'destination', label: 'Destination', visible: true, sortable: true },
          { field: 'departure_date', label: 'Departure', visible: true, sortable: true, format: 'date' },
          { field: 'passport_status', label: 'Passport', visible: true, sortable: true, format: 'badge' },
          { field: 'visa_status', label: 'Visa', visible: true, sortable: true, format: 'badge' },
        ],
      },
      allowedActions: ['view', 'check_documents', 'start'],
    },
    isDefault: false,
    isPinned: false,
    usageCount: 0,
    tags: ['specialized'],
  },
];

// views/template.ts
export const VIEW_TEMPLATES: Record<string, Partial<ViewConfig>> = {
  // Role-based templates
  senior_agent: {
    mode: 'table',
    density: 'comfortable',
    sortBy: 'priority_score',
    sortOrder: 'desc',
    displayOptions: {
      columns: [
        { field: 'priority', label: 'Priority', visible: true, sortable: true, format: 'badge' },
        { field: 'customer_name', label: 'Customer', visible: true, sortable: true },
        { field: 'destination', label: 'Destination', visible: true, sortable: true },
        { field: 'trip_type', label: 'Type', visible: true, sortable: true },
        { field: 'departure_date', label: 'Departure', visible: true, sortable: true, format: 'date' },
        { field: 'assigned_to', label: 'Assigned To', visible: true, sortable: true },
        { field: 'status', label: 'Status', visible: true, sortable: true, format: 'badge' },
        { field: 'updated_at', label: 'Last Activity', visible: true, sortable: true, format: 'datetime' },
      ],
    },
  },
  junior_agent: {
    mode: 'list',
    density: 'comfortable',
    sortBy: 'priority_score',
    sortOrder: 'desc',
    filters: [
      { field: 'priority', operator: 'not_equals', value: 'critical', enabled: true },
      { field: 'is_complex', operator: 'equals', value: false, enabled: true },
    ],
  },
  specialist: {
    mode: 'table',
    density: 'compact',
    sortBy: 'created_at',
    sortOrder: 'asc',
    filters: [
      { field: 'requires_specialist', operator: 'equals', value: true, enabled: true },
    ],
  },
};
```

### View Management

```typescript
// services/view_service.ts
class ViewService {
  constructor(
    private db: Database,
    private cache: Cache,
    private eventBus: EventBus
  ) {}

  async getViewsForUser(userId: string): Promise<SavedView[]> {
    const cacheKey = `views:${userId}`;

    const cached = await this.cache.get<SavedView[]>(cacheKey);
    if (cached) return cached;

    const views = await this.db.query<SavedView>(`
      SELECT v.*,
        COALESCE(vu.is_default, false) as is_default,
        COALESCE(vu.is_pinned, false) as is_pinned,
        vu.last_used_at,
        vu.usage_count
      FROM saved_views v
      LEFT JOIN user_views vu ON v.id = vu.view_id AND vu.user_id = $1
      WHERE v.visibility IN ('agency', 'team')
         OR v.owner_id = $1
         OR v.id IN (
           SELECT view_id FROM user_views WHERE user_id = $1
         )
      ORDER BY
        vu.is_pinned DESC,
        v.is_default DESC,
        vu.last_used_at DESC NULLS LAST,
        v.name ASC
    `, [userId]);

    await this.cache.set(cacheKey, views, { ttl: 300 });
    return views;
  }

  async saveView(userId: string, view: Omit<SavedView, 'id' | 'createdAt' | 'updatedAt'>): Promise<SavedView> {
    const id = crypto.randomUUID();
    const now = new Date();

    const newView: SavedView = {
      ...view,
      id,
      createdAt: now,
      updatedAt: now,
    };

    await this.db.transaction(async (trx) => {
      // Create view
      await trx.query(`
        INSERT INTO saved_views (id, name, description, owner_type, owner_id, visibility, config, tags)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
      `, [id, view.name, view.description, view.owner.type, view.owner.id, view.visibility, JSON.stringify(view.config), view.tags]);

      // Link to user
      await trx.query(`
        INSERT INTO user_views (user_id, view_id, is_default, is_pinned, usage_count)
        VALUES ($1, $2, $3, $4, $5)
        ON CONFLICT (user_id, view_id) DO UPDATE SET
          is_default = EXCLUDED.is_default,
          is_pinned = EXCLUDED.is_pinned
      `, [userId, id, view.isDefault, view.isPinned, 0]);
    });

    // Invalidate cache
    await this.cache.delete(`views:${userId}`);

    // Emit event
    this.eventBus.emit('view.created', { userId, viewId: id });

    return newView;
  }

  async updateView(userId: string, viewId: string, updates: Partial<SavedView>): Promise<SavedView> {
    const existing = await this.getViewForUser(userId, viewId);
    if (!existing) {
      throw new Error('View not found');
    }

    // Check ownership
    if (existing.owner.type === 'user' && existing.owner.id !== userId) {
      throw new Error('Cannot modify view owned by another user');
    }

    const updated: SavedView = {
      ...existing,
      ...updates,
      id: viewId,
      updatedAt: new Date(),
    };

    await this.db.query(`
      UPDATE saved_views
      SET name = $2, description = $3, config = $4, tags = $5, updated_at = NOW()
      WHERE id = $1
    `, [viewId, updated.name, updated.description, JSON.stringify(updated.config), updated.tags]);

    // Update user relationship
    if (updates.isDefault !== undefined || updates.isPinned !== undefined) {
      await this.db.query(`
        INSERT INTO user_views (user_id, view_id, is_default, is_pinned, usage_count)
        VALUES ($1, $2, $3, $4, (
          SELECT COALESCE(usage_count, 0) FROM user_views WHERE user_id = $1 AND view_id = $2
        ))
        ON CONFLICT (user_id, view_id) DO UPDATE SET
          is_default = COALESCE(EXCLUDED.is_default, user_views.is_default),
          is_pinned = COALESCE(EXCLUDED.is_pinned, user_views.is_pinned)
      `, [userId, viewId, updates.isDefault ?? false, updates.isPinned ?? false]);
    }

    // Invalidate cache
    await this.cache.delete(`views:${userId}`);

    return updated;
  }

  async deleteView(userId: string, viewId: string): Promise<void> {
    const view = await this.getViewForUser(userId, viewId);
    if (!view) {
      throw new Error('View not found');
    }

    // Only owner can delete
    if (view.owner.type === 'user' && view.owner.id !== userId) {
      throw new Error('Cannot delete view owned by another user');
    }

    await this.db.query('DELETE FROM saved_views WHERE id = $1', [viewId]);
    await this.db.query('DELETE FROM user_views WHERE view_id = $1', [viewId]);

    // Invalidate cache
    await this.cache.delete(`views:${userId}`);

    // Emit event
    this.eventBus.emit('view.deleted', { userId, viewId });
  }

  async shareView(userId: string, viewId: string, shareWith: 'team' | 'agency'): Promise<SavedView> {
    const view = await this.getViewForUser(userId, viewId);
    if (!view) {
      throw new Error('View not found');
    }

    // Only owner can share
    if (view.owner.type === 'user' && view.owner.id !== userId) {
      throw new Error('Cannot share view owned by another user');
    }

    const updated = await this.updateView(userId, viewId, { visibility: shareWith });

    // Emit event
    this.eventBus.emit('view.shared', { userId, viewId, visibility: shareWith });

    return updated;
  }

  async trackViewUsage(userId: string, viewId: string): Promise<void> {
    await this.db.query(`
      INSERT INTO user_views (user_id, view_id, usage_count, last_used_at)
      VALUES ($1, $2, 1, NOW())
      ON CONFLICT (user_id, view_id) DO UPDATE SET
        usage_count = user_views.usage_count + 1,
        last_used_at = NOW()
    `, [userId, viewId]);

    // Invalidate cache
    await this.cache.delete(`views:${userId}`);
  }

  private async getViewForUser(userId: string, viewId: string): Promise<SavedView | null> {
    const views = await this.getViewsForUser(userId);
    return views.find(v => v.id === viewId) || null;
  }
}
```

---

## User Preferences

### Preference Schema

```typescript
// types/preferences.ts
interface UserPreferences {
  userId: string;

  // Display preferences
  display: DisplayPreferences;

  // Notification preferences
  notifications: NotificationPreferences;

  // Workflow preferences
  workflow: WorkflowPreferences;

  // Accessibility preferences
  accessibility: AccessibilityPreferences;

  // Keyboard shortcuts
  shortcuts: KeyboardShortcuts;
}

interface DisplayPreferences {
  // Theme
  theme: 'light' | 'dark' | 'system';
  accentColor: string;

  // Density
  density: 'compact' | 'comfortable' | 'spacious';

  // Default view mode
  defaultViewMode: ViewMode;

  // Columns (table mode)
  defaultColumns: string[];
  columnWidths: Record<string, number>;

  // Card size (list/kanban mode)
  cardSize: 'small' | 'medium' | 'large';

  // Timestamp format
  timestampFormat: 'relative' | 'absolute' | 'both';
  timezone: string;
}

interface NotificationPreferences {
  // Desktop notifications
  desktop: {
    enabled: boolean;
    newTrip: boolean;
    tripAssigned: boolean;
    tripEscalated: boolean;
    customerMessage: boolean;
    mention: boolean;
    quietHours: {
      enabled: boolean;
      start: string; // HH:MM
      end: string;   // HH:MM
      timezone: string;
    };
  };

  // Mobile notifications
  mobile: {
    enabled: boolean;
    newTrip: boolean;
    tripAssigned: boolean;
    tripEscalated: boolean;
    customerMessage: boolean;
    mention: boolean;
    quietHours: {
      enabled: boolean;
      start: string;
      end: string;
      timezone: string;
    };
  };

  // Email notifications
  email: {
    enabled: boolean;
    dailyDigest: boolean;
    weeklyDigest: boolean;
    immediateEscalations: boolean;
  };

  // In-app notifications
  inApp: {
    enabled: boolean;
    sound: boolean;
    position: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
  };
}

interface WorkflowPreferences {
  // Auto-assignment behavior
  autoAssignment: {
    enabled: boolean;
    maxConcurrent: number;
    acceptFrom: ('auto' | 'manual')[];
  };

  // Default actions
  defaultActions: {
    onTripComplete: 'archive' | 'stay' | 'next_unassigned';
    onTripAssign: 'open' | 'notify' | 'both';
  };

  // Bulk actions
  bulkActions: {
    confirmBefore: boolean;
    showProgress: boolean;
  };

  // Tab behavior
  openTabsIn: 'same_tab' | 'new_tab' | 'sidebar';

  // Quick actions
  quickActions: string[]; // Action IDs shown in quick action menu
}

interface AccessibilityPreferences {
  // Font size
  fontSize: 'small' | 'medium' | 'large' | 'extra-large';

  // High contrast mode
  highContrast: boolean;

  // Reduced motion
  reducedMotion: boolean;

  // Screen reader
  screenReader: boolean;

  // Keyboard navigation
  keyboardMode: boolean;

  // Focus indicators
  focusIndicators: 'subtle' | 'normal' | 'prominent';
}

interface KeyboardShortcuts {
  // Global shortcuts
  global: Record<string, string>; // action -> key combination

  // Context-specific shortcuts
  inbox: Record<string, string>;
  tripDetail: Record<string, string>;
  timeline: Record<string, string>;
}

// Default preferences
export const DEFAULT_PREFERENCES: UserPreferences = {
  userId: '', // Set when loading
  display: {
    theme: 'system',
    accentColor: '#3b82f6',
    density: 'comfortable',
    defaultViewMode: 'list',
    defaultColumns: ['priority', 'customer', 'destination', 'departure', 'status'],
    columnWidths: {},
    cardSize: 'medium',
    timestampFormat: 'relative',
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
  },
  notifications: {
    desktop: {
      enabled: true,
      newTrip: true,
      tripAssigned: true,
      tripEscalated: true,
      customerMessage: true,
      mention: true,
      quietHours: { enabled: false, start: '22:00', end: '08:00', timezone: 'UTC' },
    },
    mobile: {
      enabled: true,
      newTrip: true,
      tripAssigned: true,
      tripEscalated: true,
      customerMessage: true,
      mention: true,
      quietHours: { enabled: true, start: '22:00', end: '08:00', timezone: 'UTC' },
    },
    email: {
      enabled: false,
      dailyDigest: false,
      weeklyDigest: true,
      immediateEscalations: true,
    },
    inApp: {
      enabled: true,
      sound: true,
      position: 'top-right',
    },
  },
  workflow: {
    autoAssignment: {
      enabled: true,
      maxConcurrent: 10,
      acceptFrom: ['auto', 'manual'],
    },
    defaultActions: {
      onTripComplete: 'stay',
      onTripAssign: 'open',
    },
    bulkActions: {
      confirmBefore: true,
      showProgress: true,
    },
    openTabsIn: 'same_tab',
    quickActions: ['assign_to_me', 'archive', 'escalate', 'message_customer'],
  },
  accessibility: {
    fontSize: 'medium',
    highContrast: false,
    reducedMotion: false,
    screenReader: false,
    keyboardMode: false,
    focusIndicators: 'normal',
  },
  shortcuts: {
    global: {
      'search': 'CmdOrCtrl+K',
      'new_view': 'CmdOrCtrl+B',
      'toggle_sidebar': 'CmdOrCtrl+\\',
      'notifications': 'CmdOrCtrl+Shift+N',
    },
    inbox: {
      'navigate_up': 'K',
      'navigate_down': 'J',
      'open_trip': 'Enter',
      'assign_to_me': 'A',
      'archive': 'E',
      'escalate': 'X',
      'refresh': 'R',
    },
    tripDetail: {
      'save': 'CmdOrCtrl+S',
      'close': 'Escape',
      'next_trip': 'CmdOrCtrl+]',
      'previous_trip': 'CmdOrCtrl+[',
      'add_note': 'N',
      'send_message': 'M',
    },
    timeline: {
      'zoom_in': '=',
      'zoom_out': '-',
      'fit_to_screen': 'F',
      'toggle_event_type': 'T',
    },
  },
};
```

### Preference Management

```typescript
// services/preference_service.ts
class PreferenceService {
  constructor(
    private db: Database,
    private cache: Cache
  ) {}

  async getPreferences(userId: string): Promise<UserPreferences> {
    const cached = await this.cache.get<UserPreferences>(`prefs:${userId}`);
    if (cached) return cached;

    const stored = await this.db.query<{ preferences: string }>(
      'SELECT preferences FROM user_preferences WHERE user_id = $1',
      [userId]
    );

    if (stored.length === 0) {
      return this.getDefaultPreferences(userId);
    }

    const preferences = this.mergeWithDefaults(
      userId,
      JSON.parse(stored[0].preferences)
    );

    await this.cache.set(`prefs:${userId}`, preferences, { ttl: 600 });
    return preferences;
  }

  async updatePreferences(
    userId: string,
    updates: Partial<UserPreferences>
  ): Promise<UserPreferences> {
    const current = await this.getPreferences(userId);
    const merged = this.deepMerge(current, updates);

    await this.db.query(`
      INSERT INTO user_preferences (user_id, preferences, updated_at)
      VALUES ($1, $2, NOW())
      ON CONFLICT (user_id) DO UPDATE SET
        preferences = EXCLUDED.preferences,
        updated_at = NOW()
    `, [userId, JSON.stringify(merged)]);

    await this.cache.delete(`prefs:${userId}`);

    return merged;
  }

  async resetPreferences(userId: string, category?: keyof UserPreferences): Promise<UserPreferences> {
    const current = await this.getPreferences(userId);

    if (category) {
      const defaults = DEFAULT_PREFERENCES[category];
      const reset = { ...current, [category]: defaults };
      return await this.updatePreferences(userId, reset);
    }

    return this.getDefaultPreferences(userId);
  }

  private getDefaultPreferences(userId: string): UserPreferences {
    return {
      ...DEFAULT_PREFERENCES,
      userId,
    };
  }

  private mergeWithDefaults(userId: string, stored: unknown): UserPreferences {
    return this.deepMerge(this.getDefaultPreferences(userId), stored);
  }

  private deepMerge<T>(target: T, source: Partial<T>): T {
    const output = { ...target };

    for (const key in source) {
      if (source[key] instanceof Object && key in target) {
        output[key] = this.deepMerge(target[key], source[key]);
      } else {
        output[key] = source[key];
      }
    }

    return output;
  }
}
```

---

## Agent Workflow Customization

### Workflow Profiles

```typescript
// types/workflow.ts
interface WorkflowProfile {
  id: string;
  name: string;
  description: string;

  // Who this profile is for
  targetRole?: 'senior_agent' | 'junior_agent' | 'specialist' | 'manager';
  targetTeam?: string;

  // Workflow configuration
  config: WorkflowConfig;

  // Metadata
  isDefault: boolean;
  isActive: boolean;
}

interface WorkflowConfig {
  // Inbox behavior
  inbox: {
    defaultView: string; // view ID
    autoRefresh: boolean;
    refreshInterval: number; // seconds
    showEmptyStates: boolean;
    showQuickFilters: boolean;
  };

  // Trip handling
  tripHandling: {
    autoOpenOnAssign: boolean;
    confirmBeforeClose: boolean;
    allowReopen: boolean;
    requireNoteOnClose: boolean;
    requireNoteOnReassign: boolean;
  };

  // Assignment behavior
  assignment: {
    autoAccept: boolean;
    maxCapacity: number;
    releaseOnIdle: boolean;
    idleTimeout: number; // minutes
  };

  // Prioritization
  prioritization: {
    customWeights?: Partial<PriorityWeights>;
    respectGlobalWeights: boolean;
  };

  // Quick actions
  quickActions: QuickActionConfig[];

  // Notifications
  notifications: {
    soundEnabled: boolean;
    desktopEnabled: boolean;
    mobileEnabled: boolean;
    priorityThreshold: 'low' | 'medium' | 'high' | 'critical';
  };
}

interface QuickActionConfig {
  id: string;
  label: string;
  icon: string;
  action: string;
  shortcut?: string;
  confirm: boolean;
  position: number;
}

interface PriorityWeights {
  newCustomer: number;
  vipCustomer: number;
  nearDeparture: number;
  highValue: number;
  complexItinerary: number;
  stalled: number;
  escalated: number;
  mentioned: number;
}

// Predefined workflow profiles
export const WORKFLOW_PROFILES: WorkflowProfile[] = [
  {
    id: 'senior_agent',
    name: 'Senior Agent',
    description: 'Optimized for experienced agents handling complex trips',
    targetRole: 'senior_agent',
    config: {
      inbox: {
        defaultView: 'all',
        autoRefresh: true,
        refreshInterval: 60,
        showEmptyStates: false,
        showQuickFilters: true,
      },
      tripHandling: {
        autoOpenOnAssign: true,
        confirmBeforeClose: false,
        allowReopen: true,
        requireNoteOnClose: false,
        requireNoteOnReassign: false,
      },
      assignment: {
        autoAccept: true,
        maxCapacity: 15,
        releaseOnIdle: false,
        idleTimeout: 0,
      },
      prioritization: {
        respectGlobalWeights: true,
      },
      quickActions: [
        { id: 'assign', label: 'Assign', icon: 'user-plus', action: 'assign', confirm: false, position: 1 },
        { id: 'escalate', label: 'Escalate', icon: 'arrow-up', action: 'escalate', confirm: true, position: 2 },
        { id: 'close', label: 'Close', icon: 'check', action: 'close', confirm: true, position: 3 },
      ],
      notifications: {
        soundEnabled: true,
        desktopEnabled: true,
        mobileEnabled: true,
        priorityThreshold: 'high',
      },
    },
    isDefault: false,
    isActive: true,
  },
  {
    id: 'junior_agent',
    name: 'Junior Agent',
    description: 'Guided workflow for newer agents',
    targetRole: 'junior_agent',
    config: {
      inbox: {
        defaultView: 'my_assignments',
        autoRefresh: true,
        refreshInterval: 30,
        showEmptyStates: true,
        showQuickFilters: true,
      },
      tripHandling: {
        autoOpenOnAssign: true,
        confirmBeforeClose: true,
        allowReopen: false,
        requireNoteOnClose: true,
        requireNoteOnReassign: true,
      },
      assignment: {
        autoAccept: false,
        maxCapacity: 8,
        releaseOnIdle: true,
        idleTimeout: 30,
      },
      prioritization: {
        customWeights: {
          newCustomer: 0.5, // Lower weight for new customers
          complexItinerary: 0.3, // Avoid complex trips
        },
        respectGlobalWeights: true,
      },
      quickActions: [
        { id: 'start', label: 'Start', icon: 'play', action: 'start', confirm: false, position: 1 },
        { id: 'help', label: 'Get Help', icon: 'question', action: 'escalate', confirm: false, position: 2 },
        { id: 'complete', label: 'Complete', icon: 'check', action: 'close', confirm: true, position: 3 },
      ],
      notifications: {
        soundEnabled: true,
        desktopEnabled: true,
        mobileEnabled: true,
        priorityThreshold: 'medium',
      },
    },
    isDefault: true,
    isActive: true,
  },
  {
    id: 'specialist',
    name: 'Destination Specialist',
    description: 'For specialists handling specific regions/types',
    targetRole: 'specialist',
    config: {
      inbox: {
        defaultView: 'international',
        autoRefresh: true,
        refreshInterval: 120,
        showEmptyStates: false,
        showQuickFilters: false,
      },
      tripHandling: {
        autoOpenOnAssign: true,
        confirmBeforeClose: false,
        allowReopen: true,
        requireNoteOnClose: false,
        requireNoteOnReassign: false,
      },
      assignment: {
        autoAccept: true,
        maxCapacity: 20,
        releaseOnIdle: false,
        idleTimeout: 0,
      },
      prioritization: {
        customWeights: {
          complexItinerary: 1.5, // Prefer complex trips
        },
        respectGlobalWeights: false,
      },
      quickActions: [
        { id: 'check_docs', label: 'Check Documents', icon: 'file-text', action: 'check_documents', confirm: false, position: 1 },
        { id: 'send_visa', label: 'Send Visa Info', icon: 'send', action: 'send_visa_info', confirm: false, position: 2 },
        { id: 'close', label: 'Close', icon: 'check', action: 'close', confirm: true, position: 3 },
      ],
      notifications: {
        soundEnabled: false,
        desktopEnabled: true,
        mobileEnabled: false,
        priorityThreshold: 'critical',
      },
    },
    isDefault: false,
    isActive: true,
  },
];
```

### Custom Quick Actions

```typescript
// types/quick_actions.ts
interface CustomQuickAction {
  id: string;
  userId: string;
  name: string;
  description?: string;
  icon: string;
  color: string;

  // Action definition
  action: QuickActionDefinition;

  // When to show
  showWhen: {
    statuses?: string[];
    priorities?: string[];
    tripTypes?: string[];
  };

  // Confirmation
  requireConfirmation: boolean;
  confirmationMessage?: string;

  // Ordering
  order: number;
}

type QuickActionDefinition =
  | { type: 'assign'; assignTo: 'me' | 'unassigned' | { userId: string } }
  | { type: 'change_status'; status: string }
  | { type: 'change_priority'; priority: string }
  | { type: 'send_message'; template?: string }
  | { type: 'add_note'; template?: string }
  | { type: 'escalate'; to: 'senior' | 'manager' | 'owner' }
  | { type: 'archive' }
  | { type: 'unarchive' }
  | { type: 'clone' }
  | { type: 'set_field'; field: string; value: unknown }
  | { type: 'custom'; handler: string }; // References a registered handler

// Example custom quick actions
export const EXAMPLE_QUICK_ACTIONS: Omit<CustomQuickAction, 'id' | 'userId'>[] = [
  {
    name: 'Claim & Start',
    description: 'Assign to me and mark as in progress',
    icon: 'zap',
    color: 'blue',
    action: {
      type: 'custom',
      handler: 'claim_and_start',
    },
    showWhen: {
      statuses: ['new'],
      priorities: ['medium', 'high'],
    },
    requireConfirmation: false,
    order: 1,
  },
  {
    name: 'Send Quick Quote',
    description: 'Send a pre-written quote template',
    icon: 'file-text',
    color: 'green',
    action: {
      type: 'send_message',
      template: 'quick_quote',
    },
    showWhen: {
      statuses: ['assigned', 'in_progress'],
      tripTypes: ['quote_request'],
    },
    requireConfirmation: true,
    confirmationMessage: 'Send quick quote template?',
    order: 2,
  },
  {
    name: 'Request Documents',
    description: 'Request missing documents from customer',
    icon: 'file',
    color: 'orange',
    action: {
      type: 'send_message',
      template: 'request_documents',
    },
    showWhen: {
      tripTypes: ['booking_request'],
    },
    requireConfirmation: false,
    order: 3,
  },
  {
    name: 'Mark as VIP',
    description: 'Elevate trip to VIP priority',
    icon: 'star',
    color: 'yellow',
    action: {
      type: 'set_field',
      field: 'is_vip',
      value: true,
    },
    showWhen: {},
    requireConfirmation: true,
    confirmationMessage: 'Mark this customer as VIP?',
    order: 4,
  },
];
```

---

## Smart Defaults

### Context-Aware Defaults

```typescript
// services/smart_defaults.ts
class SmartDefaultsService {
  constructor(
    private preferenceService: PreferenceService,
    private viewService: ViewService,
    private analyticsService: AnalyticsService
  ) {}

  async getRecommendedView(userId: string, context: RequestContext): Promise<SavedView | null> {
    const factors = await this.analyzeContext(userId, context);

    // Time-based recommendations
    if (factors.timeOfDay === 'morning') {
      // Morning: start with unassigned
      return this.viewService.getViewByName('Unassigned');
    }

    // Workload-based recommendations
    if (factors.workload === 'high') {
      // High workload: focus on critical
      return this.viewService.getViewByName('Critical');
    }

    // Pattern-based recommendations
    if (factors.usualPattern) {
      return factors.usualPattern;
    }

    // Default to all trips
    return this.viewService.getDefaultView(userId);
  }

  async getRecommendedDensity(userId: string): Promise<'compact' | 'comfortable' | 'spacious'> {
    const preferences = await this.preferenceService.getPreferences(userId);

    // Check screen size
    const screenSize = this.getScreenSize();
    if (screenSize === 'small') return 'compact';
    if (screenSize === 'large') return 'spacious';

    // Check workload
    const workload = await this.getCurrentWorkload(userId);
    if (workload > 15) return 'compact';
    if (workload < 5) return 'spacious';

    return preferences.display.density;
  }

  async getRecommendedSort(userId: string, viewId: string): Promise<SortConfig> {
    const view = await this.viewService.getView(viewId);

    // Learn from user behavior
    const behavior = await this.analyticsService.getUserBehavior(userId, 30);

    if (behavior.preferredSort) {
      return behavior.preferredSort;
    }

    // View-specific defaults
    const viewSortDefaults: Record<string, SortConfig> = {
      'critical': { sortBy: 'created_at', sortOrder: 'asc' },
      'my_assignments': { sortBy: 'priority_score', sortOrder: 'desc' },
      'stalled': { sortBy: 'updated_at', sortOrder: 'asc' },
    };

    return viewSortDefaults[view.name] || view.config;
  }

  private async analyzeContext(userId: string, context: RequestContext): Promise<ContextFactors> {
    const hour = new Date().getHours();
    const workload = await this.getCurrentWorkload(userId);
    const pattern = await this.analyticsService.getTypicalViewForTime(userId, hour);

    return {
      timeOfDay: hour < 12 ? 'morning' : hour < 17 ? 'afternoon' : 'evening',
      workload: workload > 10 ? 'high' : workload > 5 ? 'medium' : 'low',
      usualPattern: pattern,
    };
  }

  private async getCurrentWorkload(userId: string): Promise<number> {
    // Query for active trips assigned to user
    return 0; // Placeholder
  }

  private getScreenSize(): 'small' | 'medium' | 'large' {
    // Would come from client context
    return 'medium';
  }
}

interface RequestContext {
  timestamp: Date;
  screenSize?: 'small' | 'medium' | 'large';
  referrer?: string;
}

interface ContextFactors {
  timeOfDay: 'morning' | 'afternoon' | 'evening';
  workload: 'low' | 'medium' | 'high';
  usualPattern?: SavedView;
}

interface SortConfig {
  sortBy: string;
  sortOrder: 'asc' | 'desc';
}
```

### Learning from Behavior

```typescript
// services/behavior_learning.ts
class BehaviorLearningService {
  constructor(
    private db: Database,
    private eventBus: EventBus
  ) {
    this.setupEventListeners();
  }

  private setupEventListeners(): void {
    this.eventBus.on('view.applied', this.trackViewUsage.bind(this));
    this.eventBus.on('filter.applied', this.trackFilterUsage.bind(this));
    this.eventBus.on('sort.changed', this.trackSortUsage.bind(this));
    this.eventBus.on('trip.action', this.trackActionPattern.bind(this));
  }

  private async trackViewUsage(event: { userId: string; viewId: string; context: unknown }): Promise<void> {
    await this.db.query(`
      INSERT INTO view_usage (user_id, view_id, used_at, context)
      VALUES ($1, $2, NOW(), $3)
    `, [event.userId, event.viewId, JSON.stringify(event.context)]);

    // Trigger pattern analysis periodically
    await this.analyzeViewPatterns(event.userId);
  }

  private async trackFilterUsage(event: { userId: string; filter: ViewFilter; context: unknown }): Promise<void> {
    await this.db.query(`
      INSERT INTO filter_usage (user_id, filter_field, filter_operator, filter_value, used_at)
      VALUES ($1, $2, $3, $4, NOW())
      ON CONFLICT (user_id, filter_field, filter_operator, filter_value)
      DO UPDATE SET use_count = filter_usage.use_count + 1, last_used_at = NOW()
    `, [event.userId, event.filter.field, event.filter.operator, JSON.stringify(event.filter.value)]);
  }

  private async trackSortUsage(event: { userId: string; sortBy: string; sortOrder: string }): Promise<void> {
    await this.db.query(`
      INSERT INTO sort_usage (user_id, sort_by, sort_order, use_count, last_used_at)
      VALUES ($1, $2, $3, 1, NOW())
      ON CONFLICT (user_id, sort_by, sort_order)
      DO UPDATE SET use_count = sort_usage.use_count + 1, last_used_at = NOW()
    `, [event.userId, event.sortBy, event.sortOrder]);
  }

  private async trackActionPattern(event: { userId: string; action: string; tripContext: unknown }): Promise<void> {
    // Track sequences of actions to predict next actions
    await this.db.query(`
      INSERT INTO action_sequence (user_id, action, trip_context, timestamp)
      VALUES ($1, $2, $3, NOW())
    `, [event.userId, event.action, JSON.stringify(event.tripContext)]);
  }

  private async analyzeViewPatterns(userId: string): Promise<void> {
    // Find most used views by time of day
    const patterns = await this.db.query(`
      WITH hourly_usage AS (
        SELECT
          EXTRACT(HOUR FROM used_at) as hour,
          view_id,
          COUNT(*) as usage_count
        FROM view_usage
        WHERE user_id = $1
          AND used_at > NOW() - INTERVAL '30 days'
        GROUP BY hour, view_id
      )
      SELECT
        hour,
        view_id,
        usage_count,
        ROW_NUMBER() OVER (PARTITION BY hour ORDER BY usage_count DESC) as rank
      FROM hourly_usage
    `, [userId]);

    // Store learned patterns
    for (const pattern of patterns) {
      if (pattern.rank === 1) {
        await this.db.query(`
          INSERT INTO learned_preferences (user_id, preference_type, key, value, confidence)
          VALUES ($1, 'view_by_hour', $2, $3, $4)
          ON CONFLICT (user_id, preference_type, key)
          DO UPDATE SET value = EXCLUDED.value, confidence = EXCLUDED.confidence,
                       updated_at = NOW()
        `, [userId, pattern.hour, pattern.view_id, Math.min(pattern.usage_count / 10, 1)]);
      }
    }
  }

  async getTypicalViewForTime(userId: string, hour: number): Promise<SavedView | null> {
    const learned = await this.db.query<{ value: string }>(
      `SELECT value FROM learned_preferences
       WHERE user_id = $1 AND preference_type = 'view_by_hour' AND key = $2
       AND confidence > 0.5`,
      [userId, hour]
    );

    if (learned.length > 0) {
      return this.viewService.getView(learned[0].value);
    }

    return null;
  }
}
```

---

## Collaborative Features

### Shared Views

```typescript
// services/shared_views.ts
interface SharedView extends SavedView {
  // Sharing metadata
  sharedBy: string;
  sharedAt: Date;
  shareWith: 'team' | 'agency';

  // Collaboration
  collaborators: Collaborator[];
  comments: ViewComment[];
  likes: number;
  isLikedByMe: boolean;
}

interface Collaborator {
  userId: string;
  name: string;
  role: 'owner' | 'editor' | 'viewer';
  addedAt: Date;
}

interface ViewComment {
  id: string;
  userId: string;
  userName: string;
  content: string;
  createdAt: Date;
  updatedAt: Date;
}

class SharedViewService {
  async shareView(
    userId: string,
    viewId: string,
    shareWith: 'team' | 'agency',
    collaborators?: string[]
  ): Promise<SharedView> {
    const view = await this.viewService.getView(viewId);

    // Update view visibility
    await this.viewService.updateView(userId, viewId, {
      visibility: shareWith,
    });

    // Add collaborators if specified
    if (collaborators) {
      for (const collaboratorId of collaborators) {
        await this.addCollaborator(userId, viewId, collaboratorId, 'viewer');
      }
    }

    // Notify team
    await this.notificationService.notifyTeam({
      type: 'view_shared',
      viewId,
      viewName: view.name,
      sharedBy: userId,
      shareWith,
    });

    return this.getSharedView(viewId);
  }

  async addCollaborator(
    userId: string,
    viewId: string,
    collaboratorId: string,
    role: 'editor' | 'viewer'
  ): Promise<void> {
    await this.db.query(`
      INSERT INTO view_collaborators (view_id, user_id, role, added_by, added_at)
      VALUES ($1, $2, $3, $4, NOW())
      ON CONFLICT (view_id, user_id) DO UPDATE SET role = EXCLUDED.role
    `, [viewId, collaboratorId, role, userId]);

    // Notify collaborator
    await this.notificationService.notify(collaboratorId, {
      type: 'added_to_view',
      viewId,
      addedBy: userId,
    });
  }

  async addComment(
    userId: string,
    viewId: string,
    content: string
  ): Promise<ViewComment> {
    const id = crypto.randomUUID();
    const now = new Date();

    await this.db.query(`
      INSERT INTO view_comments (id, view_id, user_id, content, created_at, updated_at)
      VALUES ($1, $2, $3, $4, $5, $5)
    `, [id, viewId, userId, content, now]);

    // Notify collaborators
    const collaborators = await this.getCollaborators(viewId);
    for (const collaborator of collaborators) {
      if (collaborator.userId !== userId) {
        await this.notificationService.notify(collaborator.userId, {
          type: 'new_comment',
          viewId,
          commentId: id,
          commentBy: userId,
        });
      }
    }

    return {
      id,
      userId,
      userName: '', // Fetched from join
      content,
      createdAt: now,
      updatedAt: now,
    };
  }

  async toggleLike(userId: string, viewId: string): Promise<number> {
    const liked = await this.db.query<{ exists: boolean }>(`
      SELECT EXISTS(
        SELECT 1 FROM view_likes WHERE view_id = $1 AND user_id = $2
      ) as exists
    `, [viewId, userId]);

    if (liked[0].exists) {
      await this.db.query('DELETE FROM view_likes WHERE view_id = $1 AND user_id = $2', [viewId, userId]);
    } else {
      await this.db.query('INSERT INTO view_likes (view_id, user_id, liked_at) VALUES ($1, $2, NOW())', [viewId, userId]);
    }

    const count = await this.db.query<{ count: bigint }>(
      'SELECT COUNT(*) as count FROM view_likes WHERE view_id = $1',
      [viewId]
    );

    return Number(count[0].count);
  }

  private async getCollaborators(viewId: string): Promise<Collaborator[]> {
    return this.db.query<Collaborator>(`
      SELECT
        vc.user_id,
        u.name,
        vc.role,
        vc.added_at
      FROM view_collaborators vc
      JOIN users u ON u.id = vc.user_id
      WHERE vc.view_id = $1
    `, [viewId]);
  }
}
```

### Team Templates

```typescript
// services/team_templates.ts
interface TeamTemplate {
  id: string;
  teamId: string;
  name: string;
  description: string;
  category: 'workflow' | 'view' | 'quick_actions';

  // Template content
  content: TeamTemplateContent;

  // Metadata
  createdBy: string;
  createdAt: Date;
  isDefault: boolean;
  adoptionCount: number;
}

type TeamTemplateContent =
  | { type: 'view'; config: ViewConfig }
  | { type: 'workflow'; config: WorkflowConfig }
  | { type: 'quick_actions'; actions: QuickActionConfig[] };

class TeamTemplateService {
  async createTemplate(
    teamId: string,
    name: string,
    content: TeamTemplateContent,
    createdBy: string
  ): Promise<TeamTemplate> {
    const id = crypto.randomUUID();

    await this.db.query(`
      INSERT INTO team_templates (id, team_id, name, content, created_by, created_at)
      VALUES ($1, $2, $3, $4, $5, NOW())
    `, [id, teamId, name, JSON.stringify(content), createdBy]);

    // Notify team
    await this.notificationService.notifyTeam(teamId, {
      type: 'new_template',
      templateId: id,
      templateName: name,
      createdBy,
    });

    return this.getTemplate(id);
  }

  async adoptTemplate(userId: string, templateId: string): Promise<void> {
    const template = await this.getTemplate(templateId);

    // Apply template based on type
    switch (template.content.type) {
      case 'view':
        await this.viewService.saveView(userId, {
          name: template.name,
          description: template.description,
          owner: { type: 'user', id: userId, name: '' },
          visibility: 'private',
          config: template.content.config,
          isDefault: false,
          isPinned: false,
          tags: ['team-template'],
        });
        break;

      case 'workflow':
        await this.workflowService.applyWorkflow(userId, template.content.config);
        break;

      case 'quick_actions':
        await this.quickActionsService.addActions(userId, template.content.actions);
        break;
    }

    // Track adoption
    await this.db.query(`
      INSERT INTO template_adoption (template_id, user_id, adopted_at)
      VALUES ($1, $2, NOW())
      ON CONFLICT (template_id, user_id) DO UPDATE SET adopted_at = NOW()
    `, [templateId, userId]);
  }

  async getPopularTemplates(teamId: string): Promise<TeamTemplate[]> {
    return this.db.query<TeamTemplate>(`
      SELECT t.*,
        COUNT(a.user_id) as adoption_count
      FROM team_templates t
      LEFT JOIN template_adoption a ON a.template_id = t.id
      WHERE t.team_id = $1
      GROUP BY t.id
      ORDER BY adoption_count DESC, t.created_at DESC
      LIMIT 10
    `, [teamId]);
  }

  private async getTemplate(templateId: string): Promise<TeamTemplate> {
    const templates = await this.db.query<TeamTemplate>(
      'SELECT * FROM team_templates WHERE id = $1',
      [templateId]
    );
    return templates[0];
  }
}
```

---

## Implementation Architecture

### Database Schema

```sql
-- Saved views
CREATE TABLE saved_views (
  id UUID PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  owner_type VARCHAR(20) NOT NULL, -- 'user', 'team', 'agency'
  owner_id VARCHAR(255) NOT NULL,
  visibility VARCHAR(20) NOT NULL DEFAULT 'private', -- 'private', 'team', 'agency'
  config JSONB NOT NULL,
  tags TEXT[] DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_views_owner ON saved_views(owner_type, owner_id);
CREATE INDEX idx_views_visibility ON saved_views(visibility);
CREATE INDEX idx_views_tags ON saved_views USING GIN(tags);

-- User view relationships
CREATE TABLE user_views (
  user_id VARCHAR(255) NOT NULL,
  view_id UUID NOT NULL REFERENCES saved_views(id) ON DELETE CASCADE,
  is_default BOOLEAN DEFAULT false,
  is_pinned BOOLEAN DEFAULT false,
  last_used_at TIMESTAMPTZ,
  usage_count INTEGER DEFAULT 0,
  PRIMARY KEY (user_id, view_id)
);

CREATE INDEX idx_user_views_default ON user_views(user_id, is_default) WHERE is_default = true;
CREATE INDEX idx_user_views_pinned ON user_views(user_id, is_pinned) WHERE is_pinned = true;

-- User preferences
CREATE TABLE user_preferences (
  user_id VARCHAR(255) PRIMARY KEY,
  preferences JSONB NOT NULL DEFAULT '{}',
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Workflow profiles
CREATE TABLE workflow_profiles (
  id VARCHAR(100) PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  target_role VARCHAR(50),
  target_team VARCHAR(100),
  config JSONB NOT NULL,
  is_default BOOLEAN DEFAULT false,
  is_active BOOLEAN DEFAULT true
);

-- User workflow assignments
CREATE TABLE user_workflows (
  user_id VARCHAR(255) PRIMARY KEY,
  workflow_id VARCHAR(100) REFERENCES workflow_profiles(id),
  assigned_at TIMESTAMPTZ DEFAULT NOW(),
  assigned_by VARCHAR(255)
);

-- Custom quick actions
CREATE TABLE custom_quick_actions (
  id UUID PRIMARY KEY,
  user_id VARCHAR(255) NOT NULL,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  icon VARCHAR(50),
  color VARCHAR(50),
  action JSONB NOT NULL,
  show_when JSONB DEFAULT '{}',
  require_confirmation BOOLEAN DEFAULT false,
  confirmation_message TEXT,
  position INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_custom_actions_user ON custom_quick_actions(user_id);

-- Shared views collaboration
CREATE TABLE view_collaborators (
  view_id UUID NOT NULL REFERENCES saved_views(id) ON DELETE CASCADE,
  user_id VARCHAR(255) NOT NULL,
  role VARCHAR(20) NOT NULL, -- 'owner', 'editor', 'viewer'
  added_by VARCHAR(255),
  added_at TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (view_id, user_id)
);

-- View comments
CREATE TABLE view_comments (
  id UUID PRIMARY KEY,
  view_id UUID NOT NULL REFERENCES saved_views(id) ON DELETE CASCADE,
  user_id VARCHAR(255) NOT NULL,
  content TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_view_comments_view ON view_comments(view_id, created_at DESC);

-- View likes
CREATE TABLE view_likes (
  view_id UUID NOT NULL REFERENCES saved_views(id) ON DELETE CASCADE,
  user_id VARCHAR(255) NOT NULL,
  liked_at TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (view_id, user_id)
);

-- Team templates
CREATE TABLE team_templates (
  id UUID PRIMARY KEY,
  team_id VARCHAR(100) NOT NULL,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  category VARCHAR(50) NOT NULL,
  content JSONB NOT NULL,
  created_by VARCHAR(255) NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  is_default BOOLEAN DEFAULT false
);

CREATE INDEX idx_team_templates_team ON team_templates(team_id, category);

-- Template adoption
CREATE TABLE template_adoption (
  template_id UUID NOT NULL REFERENCES team_templates(id) ON DELETE CASCADE,
  user_id VARCHAR(255) NOT NULL,
  adopted_at TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (template_id, user_id)
);

-- Learning data
CREATE TABLE view_usage (
  user_id VARCHAR(255) NOT NULL,
  view_id UUID NOT NULL REFERENCES saved_views(id),
  used_at TIMESTAMPTZ DEFAULT NOW(),
  context JSONB
);

CREATE INDEX idx_view_usage_user_time ON view_usage(user_id, used_at DESC);

CREATE TABLE filter_usage (
  user_id VARCHAR(255) NOT NULL,
  filter_field VARCHAR(100) NOT NULL,
  filter_operator VARCHAR(50) NOT NULL,
  filter_value JSONB NOT NULL,
  use_count INTEGER DEFAULT 1,
  last_used_at TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (user_id, filter_field, filter_operator, filter_value)
);

CREATE TABLE sort_usage (
  user_id VARCHAR(255) NOT NULL,
  sort_by VARCHAR(100) NOT NULL,
  sort_order VARCHAR(10) NOT NULL,
  use_count INTEGER DEFAULT 1,
  last_used_at TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (user_id, sort_by, sort_order)
);

CREATE TABLE learned_preferences (
  user_id VARCHAR(255) NOT NULL,
  preference_type VARCHAR(50) NOT NULL,
  key VARCHAR(100) NOT NULL,
  value JSONB NOT NULL,
  confidence FLOAT DEFAULT 0.5,
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (user_id, preference_type, key)
);

CREATE INDEX idx_learned_prefs_type ON learned_preferences(user_id, preference_type);
```

### API Endpoints

```typescript
// api/views.ts
router.get('/views', authenticate, async (req, res) => {
  const views = await viewService.getViewsForUser(req.user.id);
  res.json(views);
});

router.post('/views', authenticate, async (req, res) => {
  const view = await viewService.saveView(req.user.id, req.body);
  res.status(201).json(view);
});

router.put('/views/:id', authenticate, async (req, res) => {
  const view = await viewService.updateView(req.user.id, req.params.id, req.body);
  res.json(view);
});

router.delete('/views/:id', authenticate, async (req, res) => {
  await viewService.deleteView(req.user.id, req.params.id);
  res.status(204).send();
});

router.post('/views/:id/share', authenticate, async (req, res) => {
  const view = await viewService.shareView(
    req.user.id,
    req.params.id,
    req.body.shareWith
  );
  res.json(view);
});

router.post('/views/:id/like', authenticate, async (req, res) => {
  const count = await sharedViewService.toggleLike(req.user.id, req.params.id);
  res.json({ likes: count });
});

router.post('/views/:id/comments', authenticate, async (req, res) => {
  const comment = await sharedViewService.addComment(
    req.user.id,
    req.params.id,
    req.body.content
  );
  res.status(201).json(comment);
});

// Preferences
router.get('/preferences', authenticate, async (req, res) => {
  const prefs = await preferenceService.getPreferences(req.user.id);
  res.json(prefs);
});

router.put('/preferences', authenticate, async (req, res) => {
  const prefs = await preferenceService.updatePreferences(req.user.id, req.body);
  res.json(prefs);
});

router.post('/preferences/reset', authenticate, async (req, res) => {
  const prefs = await preferenceService.resetPreferences(
    req.user.id,
    req.body.category
  );
  res.json(prefs);
});

// Quick actions
router.get('/quick-actions', authenticate, async (req, res) => {
  const actions = await quickActionsService.getForUser(req.user.id);
  res.json(actions);
});

router.post('/quick-actions', authenticate, async (req, res) => {
  const action = await quickActionsService.create(req.user.id, req.body);
  res.status(201).json(action);
});

// Templates
router.get('/templates/:teamId', authenticate, async (req, res) => {
  const templates = await teamTemplateService.getPopularTemplates(req.params.teamId);
  res.json(templates);
});

router.post('/templates', authenticate, async (req, res) => {
  const template = await teamTemplateService.createTemplate(
    req.body.teamId,
    req.body.name,
    req.body.content,
    req.user.id
  );
  res.status(201).json(template);
});

router.post('/templates/:id/adopt', authenticate, async (req, res) => {
  await teamTemplateService.adoptTemplate(req.user.id, req.params.id);
  res.status(204).send();
});
```

---

**This completes the Inbox Management deep dive series.**

**Series Summary:**
- INBOX_01: Technical architecture, data model, priority scoring, filtering
- INBOX_02: UX/UI patterns, layouts, card design, view modes
- INBOX_03: Analytics, metrics, funnels, dashboards, alerting
- INBOX_04: Personalization, saved views, preferences, collaborative features

**Next exploration area:** Customer Portal, Communication Hub, or Agency Settings
