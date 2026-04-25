# INBOX_01_TECHNICAL_DEEP_DIVE

> Part 1 of Inbox Management Deep Dive
>
> **Series:** Trip Listing, Sorting, Filtering, and Prioritization
>
> **Next:** [INBOX_02_UX_UI_DEEP_DIVE](./INBOX_02_UX_UI_DEEP_DIVE.md)

---

## Technical Architecture Overview

The inbox is the primary workspace for agents — their dashboard for managing all active trips. It must be fast, intuitive, and powerful enough to handle thousands of trips efficiently.

---

## Table of Contents

1. [System Architecture](#1-system-architecture)
2. [Data Model & Indexing](#2-data-model--indexing)
3. [Sorting Engine](#3-sorting-engine)
4. [Filtering System](#4-filtering-system)
5. [Prioritization Logic](#5-prioritization-logic)
6. [Real-Time Updates](#6-real-time-updates)
7. [Performance Optimization](#7-performance-optimization)

---

## 1. System Architecture

### 1.1 Component Hierarchy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           INBOX ARCHITECTURE                               │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────────────┐
    │                         InboxProvider                               │
    │  (Data fetching, caching, real-time updates)                       │
    └─────────────────────────────┬───────────────────────────────────────┘
                                  │
              ┌───────────────────┼───────────────────┐
              │                   │                   │
              ▼                   ▼                   ▼
    ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
    │  InboxToolbar   │ │  InboxList      │ │  InboxSidebar   │
    │  (Search,       │ │  (Trip cards)    │ │  (Filters,       │
    │   Actions)      │ │                 │ │   Views)         │
    └─────────────────┘ └────────┬────────┘ └─────────────────┘
                                 │
                    ┌────────────┼────────────┐
                    │            │            │
                    ▼            ▼            ▼
            ┌──────────┐  ┌──────────┐  ┌──────────┐
            │TripCard  │  │TripCard  │  │TripCard  │
            │(Compact) │  │(Compact) │  │(Compact) │
            └──────────┘  └──────────┘  └──────────┘
```

### 1.2 Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             INBOX DATA FLOW                                │
└─────────────────────────────────────────────────────────────────────────────┘

    USER OPENS INBOX
            │
            ▼
    ┌──────────────────┐
    │  Fetch Initial    │ ◄── Cache check first
    │  Trip List       │
    └──────────┬───────┘
               │
               ▼
    ┌──────────────────┐
    │  Apply Filters   │ ◄── User's saved/default filters
    │  & Sorting      │
    └──────────┬───────┘
               │
               ▼
    ┌──────────────────┐
    │  Calculate       │ ◄── Priority, urgency, due dates
    │  Scores         │
    └──────────┬───────┘
               │
               ▼
    ┌──────────────────┐
    │  Render Trip     │ ◄── Virtual scrolling for performance
    │  Cards          │
    └──────────┬───────┘
               │
               ▼
    ┌──────────────────┐
    │  Listen for      │ ◄── WebSocket/EventBus
    │  Updates        │
    └──────────────────┘
```

### 1.3 Core Interfaces

```typescript
/**
 * Inbox configuration
 */
interface InboxConfig {
  /** User ID whose inbox this is */
  userId: string;

  /** Agency ID */
  agencyId: string;

  /** Default view settings */
  defaults: {
    view: InboxView;
    sortBy: TripSortField;
    sortOrder: 'asc' | 'desc';
    filters: FilterPreset;
    groupBy?: TripGroupField;
  };

  /** Available views */
  availableViews: InboxView[];

  /** Permissions */
  permissions: {
    canDelete: boolean;
    canArchive: boolean;
    canAssign: boolean;
    canExport: boolean;
  };
}

/**
 * Inbox state
 */
interface InboxState {
  /** Current trips being displayed */
  trips: TripSummary[];

  /** Total trip count (for pagination) */
  totalCount: number;

  /** Loading state */
  loading: boolean;

  /** Current filters */
  filters: ActiveFilters;

  /** Current sorting */
  sort: SortConfig;

  /** Current view */
  view: InboxView;

  /** Grouping */
  groupBy?: TripGroupField;

  /** Search query */
  searchQuery?: string;

  /** Selected trip IDs */
  selectedTripIds: string[];

  /** Real-time update connection */
  wsConnected: boolean;
}

/**
 * Trip summary for inbox display
 */
interface TripSummary {
  id: string;
  name: string;
  status: TripStatus;

  /** Primary customer */
  customer: {
    id: string;
    name: string;
    avatar?: string;
    isNew: boolean;
  };

  /** Trip dates */
  dates: {
    start: Date;
    end: Date;
    isFlexible: boolean;
  };

  /** Destinations */
  destinations: {
    primary: string;
    count: number;
    thumbnail?: string;
  };

  /** Priority score */
  priority: {
    score: number;
    level: 'urgent' | 'high' | 'normal' | 'low';
  };

  /** Activity indicators */
  activity: {
    lastUpdated: Date;
    unreadCount: number;
    hasUnseenChanges: boolean;
    dueSoon: boolean;
    overdue: boolean;
  };

  /** Assignment */
  assignment: {
    ownerId?: string;
    ownerName?: string;
  };

  /** Tags/labels */
  tags: string[];

  /** Budget */
  budget?: {
    amount: number;
    currency: string;
  };
}
```

---

## 2. Data Model & Indexing

### 2.1 Trip Query Model

```typescript
/**
 * Trip query for inbox
 */
interface TripQuery {
  /** Base filters */
  filters: {
    /** Status filter */
    status?: TripStatus[];

    /** Customer filter */
    customerIds?: string[];

    /** Date range filter */
    dateRange?: {
      field: 'createdAt' | 'updatedAt' | 'departureDate';
      start: Date;
      end: Date;
    };

    /** Assignment filter */
    assignedTo?: string[];

    /** Destination filter */
    destinations?: string[];

    /** Tag filter */
    tags?: string[];

    /** Budget range filter */
    budgetRange?: {
      min: number;
      max: number;
      currency: string;
    };
  };

  /** Search query */
  search?: {
    query: string;
    fields: SearchField[];
  };

  /** Sorting */
  sort: {
    field: TripSortField;
    order: 'asc' | 'desc';
  };

  /** Pagination */
  pagination: {
    page: number;
    pageSize: number;
  };

  /** Includes (related data to fetch) */
  includes?: string[];
}

/**
 * Search fields for full-text search
 */
enum SearchField {
  TRIP_NAME = 'tripName',
  CUSTOMER_NAME = 'customerName',
  CUSTOMER_EMAIL = 'customerEmail',
  DESTINATION_NAME = 'destinationName',
  BOOKING_REF = 'bookingRef',
  TAGS = 'tags',
  NOTES = 'notes'
}

/**
 * Sort fields
 */
enum TripSortField {
  CREATED_AT = 'createdAt',
  UPDATED_AT = 'updatedAt',
  DEPARTURE_DATE = 'departureDate',
  CUSTOMER_NAME = 'customerName',
  PRIORITY_SCORE = 'priorityScore',
  STATUS = 'status',
  BUDGET = 'budget',
  NAME = 'name'
}

/**
 * Group fields
 */
enum TripGroupField {
  STATUS = 'status',
  ASSIGNEE = 'assignee',
  DEPARTURE_MONTH = 'departureMonth',
  PRIORITY = 'priority',
  DESTINATION = 'destination',
  SOURCE = 'source'
}
```

### 2.2 Database Indexing Strategy

```sql
-- Core inbox query indexes
CREATE INDEX idx_trips_status_updated ON trips(status, updated_at DESC);
CREATE INDEX idx_trips_assigned_to ON trips(assigned_to) WHERE assigned_to IS NOT NULL;
CREATE INDEX idx_trips_departure_date ON trips(departure_date) WHERE departure_date IS NOT NULL;
CREATE INDEX idx_trips_customer_id ON trips(customer_id);

-- Composite indexes for common filter combinations
CREATE INDEX idx_trips_status_assigned ON trips(status, assigned_to, updated_at DESC);
CREATE INDEX idx_trips_departure_status ON trips(departure_date, status) WHERE departure_date IS NOT NULL;

-- Full-text search index
CREATE INDEX idx_trips_fts ON trips USING GIN(
  to_tsvector('english',
    COALESCE(name, '') || ' ' ||
    COALESCE(notes, '') || ' ' ||
    COALESCE(tags, '')
  )
);

-- Priority calculation (computed column or materialized view)
CREATE MATERIALIZED VIEW mv_trip_priority AS
SELECT
  t.id,
  (
    -- Urgency based on departure date
    CASE
      WHEN t.departure_date <= NOW() + INTERVAL '3 days' THEN 100
      WHEN t.departure_date <= NOW() + INTERVAL '7 days' THEN 75
      WHEN t.departure_date <= NOW() + INTERVAL '30 days' THEN 50
      ELSE 25
    END
    +
    -- Status urgency
    CASE
      WHEN t.status = 'inquiry' THEN 30
      WHEN t.status = 'quoted' THEN 25
      WHEN t.status = 'confirmed' THEN 20
      WHEN t.status = 'deposit_paid' THEN 15
      ELSE 10
    END
    +
    -- New customer bonus
    CASE WHEN c.is_new_customer THEN 20 ELSE 0 END
    +
    -- Inactivity penalty
    CASE
      WHEN t.updated_at < NOW() - INTERVAL '7 days' THEN -20
      WHEN t.updated_at < NOW() - INTERVAL '30 days' THEN -40
      ELSE 0
    END
  ) AS priority_score,
  t.updated_at
FROM trips t
JOIN customers c ON t.customer_id = c.id
WHERE t.status NOT IN ('completed', 'cancelled');

CREATE INDEX idx_priority_score ON mv_trip_priority(priority_score DESC, updated_at DESC);
```

### 2.3 Cache Strategy

```typescript
/**
 * Inbox cache configuration
 */
interface InboxCacheConfig {
  /** TTL for cached trip lists */
  ttl: {
    /** Hot trips (actively being worked on) */
    hot: number; // 30 seconds

    /** Warm trips (recent activity) */
    warm: number; // 5 minutes

    /** Cold trips (inactive) */
    cold: number; // 1 hour
  };

  /** Max cache size */
  maxSize: number;

  /** Cache key prefix */
  keyPrefix: string;

  /** Invalidate on events */
  invalidateOn: string[];
}

/**
 * Cache service for inbox
 */
class InboxCacheService {
  private cache: Map<string, CachedData> = new Map();
  private config: InboxCacheConfig = {
    ttl: {
      hot: 30 * 1000,
      warm: 5 * 60 * 1000,
      cold: 60 * 60 * 1000
    },
    maxSize: 100,
    keyPrefix: 'inbox:',
    invalidateOn: ['trip.created', 'trip.updated', 'trip.deleted', 'trip.status_changed']
  };

  /**
   * Get cached inbox data
   */
  get(userId: string, query: TripQuery): TripSummary[] | null {
    const key = this.buildKey(userId, query);
    const cached = this.cache.get(key);

    if (!cached) return null;

    // Check if still valid
    if (Date.now() - cached.timestamp > this.getTTL(query)) {
      this.cache.delete(key);
      return null;
    }

    return cached.data;
  }

  /**
   * Set cached inbox data
   */
  set(userId: string, query: TripQuery, data: TripSummary[]): void {
    const key = this.buildKey(userId, query);

    // Enforce max size
    if (this.cache.size >= this.config.maxSize) {
      // Remove oldest entry
      const oldestKey = this.cache.keys().next().value;
      this.cache.delete(oldestKey);
    }

    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      query
    });
  }

  /**
   * Invalidate cache for user
   */
  invalidate(userId: string): void {
    const prefix = `${this.config.keyPrefix}${userId}:`;
    for (const key of this.cache.keys()) {
      if (key.startsWith(prefix)) {
        this.cache.delete(key);
      }
    }
  }

  /**
   * Invalidate specific trip across all caches
   */
  invalidateTrip(tripId: string): void {
    for (const [key, cached] of this.cache.entries()) {
      if (cached.data.some(t => t.id === tripId)) {
        this.cache.delete(key);
      }
    }
  }

  /**
   * Build cache key
   */
  private buildKey(userId: string, query: TripQuery): string {
    const hash = this.hashQuery(query);
    return `${this.config.keyPrefix}${userId}:${hash}`;
  }

  /**
   * Hash query for cache key
   */
  private hashQuery(query: TripQuery): string {
    // Simple hash implementation - use proper hash in production
    return JSON.stringify(query);
  }

  /**
   * Get TTL based on query
   */
  private getTTL(query: TripQuery): number {
    // Hot trips (recently updated, urgent status)
    if (query.filters.status?.includes('inquiry') ||
        query.filters.status?.includes('quoted')) {
      return this.config.ttl.hot;
    }

    // Active trips
    if (query.sort.field === TripSortField.PRIORITY_SCORE) {
      return this.config.ttl.warm;
    }

    // Cold queries
    return this.config.ttl.cold;
  }
}

interface CachedData {
  data: TripSummary[];
  timestamp: number;
  query: TripQuery;
}
```

---

## 3. Sorting Engine

### 3.1 Sort Strategies

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          SORTING STRATEGIES                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PRIORITY SORT                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Algorithm: Weighted score calculation                                │   │
│  │ Factors:                                                             │   │
│  │   • Departure proximity (soonest = highest)                         │   │
│  │   • Status urgency (inquiry > quoted > confirmed)                   │   │
│  │   • New customer flag                                               │   │
│  │   • Inactivity penalty                                              │   │
│  │   • Unseen changes count                                            │   │
│  │                                                                     │   │
│  │ Score range: 0-150                                                  │   │
│  │ Urgent: 100+ │ High: 75-99 │ Normal: 40-74 │ Low: <40              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DEPARTURE DATE SORT                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Primary: Departure date                                             │   │
│  │ Secondary: Creation date (for same departure)                      │   │
│  │ Null handling: No departure date → last                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ACTIVITY SORT                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Primary: Last updated timestamp                                     │   │
│  │ Secondary: Unseen changes count                                    │   │
│  │ Effect: Most recently touched trips first                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  CUSTOMER NAME SORT                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Primary: Customer last name (alphabetical)                         │   │
│  │ Secondary: Customer first name                                     │   │
│  │ Null handling: No customer → "Unassigned" at top                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  STATUS SORT                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Order: Custom priority order                                        │   │
│  │   1. inquiry                                                        │   │
│  │   2. quoted                                                         │   │
│  │   3. confirmed                                                      │   │
│  │   4. deposit_paid                                                   │   │
│  │   5. fully_paid                                                     │   │
│  │   6. booked                                                         │   │
│  │   7. in_progress                                                    │   │
│  │   8. completed                                                      │   │
│  │   9. cancelled                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Priority Scoring

```typescript
/**
 * Priority score calculator
 */
class PriorityScorer {
  /**
   * Calculate priority score for a trip
   */
  calculateScore(trip: Trip): number {
    let score = 0;

    // Departure urgency (max 50 points)
    score += this.calculateDepartureUrgency(trip);

    // Status urgency (max 30 points)
    score += this.calculateStatusUrgency(trip);

    // New customer bonus (max 20 points)
    score += this.calculateNewCustomerBonus(trip);

    // Inactivity penalty (max -40 points)
    score += this.calculateInactivityPenalty(trip);

    // Unseen changes bonus (max 15 points)
    score += this.calculateUnseenChangesBonus(trip);

    // Overdue penalty (max -30 points)
    score += this.calculateOverduePenalty(trip);

    return Math.max(0, Math.min(150, score));
  }

  /**
   * Calculate departure urgency
   */
  private calculateDepartureUrgency(trip: Trip): number {
    if (!trip.departureDate) return 0;

    const now = new Date();
    const daysUntil = Math.ceil((trip.departureDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));

    if (daysUntil <= 0) return 50; // Already departed or departing today
    if (daysUntil <= 3) return 45;
    if (daysUntil <= 7) return 35;
    if (daysUntil <= 14) return 25;
    if (daysUntil <= 30) return 15;
    if (daysUntil <= 60) return 10;
    if (daysUntil <= 90) return 5;
    return 0;
  }

  /**
   * Calculate status urgency
   */
  private calculateStatusUrgency(trip: Trip): number {
    const urgencyMap: Record<TripStatus, number> = {
      inquiry: 30,
      quoted: 25,
      confirmed: 20,
      deposit_paid: 15,
      fully_paid: 10,
      booked: 10,
      in_progress: 5,
      completed: 0,
      cancelled: 0
    };

    return urgencyMap[trip.status] || 0;
  }

  /**
   * Calculate new customer bonus
   */
  private calculateNewCustomerBonus(trip: Trip): number {
    // Check if customer has previous trips
    const previousTrips = trip.customer.previousTripCount || 0;

    if (previousTrips === 0) return 20;
    if (previousTrips <= 2) return 10;
    return 0;
  }

  /**
   * Calculate inactivity penalty
   */
  private calculateInactivityPenalty(trip: Trip): number {
    const now = new Date();
    const daysSinceUpdate = Math.ceil((now.getTime() - trip.updatedAt.getTime()) / (1000 * 60 * 60 * 24));

    // Don't penalize completed/cancelled trips
    if (trip.status === 'completed' || trip.status === 'cancelled') {
      return 0;
    }

    if (daysSinceUpdate >= 30) return -40;
    if (daysSinceUpdate >= 14) return -25;
    if (daysSinceUpdate >= 7) return -15;
    if (daysSinceUpdate >= 3) return -5;
    return 0;
  }

  /**
   * Calculate unseen changes bonus
   */
  private calculateUnseenChangesBonus(trip: Trip): number {
    const unseenCount = trip.activity.unseenChangesCount || 0;

    if (unseenCount === 0) return 0;
    if (unseenCount >= 5) return 15;
    if (unseenCount >= 3) return 10;
    return 5;
  }

  /**
   * Calculate overdue penalty
   */
  private calculateOverduePenalty(trip: Trip): number {
    // Check for overdue actions
    const overdueActions = this.getOverdueActions(trip);

    if (overdueActions.critical > 0) return -30;
    if (overdueActions.high > 0) return -20;
    if (overdueActions.medium > 0) return -10;
    return 0;
  }

  /**
   * Get overdue action counts
   */
  private getOverdueActions(trip: Trip): {
    critical: number;
    high: number;
    medium: number;
  } {
    // Check for overdue deposits, payments, documents, etc.
    const now = new Date();
    const overdue = { critical: 0, high: 0, medium: 0 };

    // Check payment due dates
    for (const payment of trip.payments || []) {
      if (payment.dueDate && payment.dueDate < now && !payment.paid) {
        if (payment.amount > 5000) overdue.critical++;
        else if (payment.amount > 1000) overdue.high++;
        else overdue.medium++;
      }
    }

    // Check document expiry
    for (const doc of trip.requiredDocuments || []) {
      if (doc.status === 'missing') {
        overdue.medium++;
      }
    }

    return overdue;
  }

  /**
   * Get priority level from score
   */
  getPriorityLevel(score: number): 'urgent' | 'high' | 'normal' | 'low' {
    if (score >= 100) return 'urgent';
    if (score >= 75) return 'high';
    if (score >= 40) return 'normal';
    return 'low';
  }
}
```

---

## 4. Filtering System

### 4.1 Filter Types

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FILTER TYPES                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  STATUS FILTER                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Type: Multi-select                                                  │   │
│  │ Options: All trip statuses                                          │   │
│  │ Presets:                                                             │   │
│  │   • Active (inquiry, quoted, confirmed, deposit_paid)               │   │
│  │   • Booked (booked, in_progress)                                   │   │
│  │   • Completed (completed)                                           │   │
│  │   • Needs Action (inquiry, quoted)                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DATE RANGE FILTER                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Type: Date range picker                                            │   │
│  │ Fields: Departure date, Created date, Updated date                 │   │
│  │ Presets:                                                             │   │
│  │   • Today                                                            │   │
│  │   • Next 7 days                                                      │   │
│  │   • Next 30 days                                                     │   │
│  │   • This month                                                        │   │
│  │   • Next 3 months                                                    │   │
│  │   • Custom range                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ASSIGNMENT FILTER                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Type: Multi-select (agents)                                         │   │
│  │ Options: All agency agents                                          │   │
│  │ Presets:                                                             │   │
│  │   • Assigned to me                                                   │   │
│  │   • Unassigned                                                       │   │
│  │   • All agents                                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  CUSTOMER FILTER                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Type: Search + multi-select                                        │   │
│  │ Search: By name, email, phone                                      │   │
│  │ Recent: Last 10 customers interacted with                           │   │
│  │ Presets:                                                             │   │
│  │   • New customers (first trip)                                     │   │
│  │   • Returning customers (2+ trips)                                 │   │
│  │   • VIP customers                                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DESTINATION FILTER                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Type: Search + multi-select                                        │   │
│  │ Search: By city, country, region                                   │   │
│  │ Group by: Country, Region, Type                                    │   │
│  │ Recent: Last 10 destinations booked                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  TAG FILTER                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Type: Multi-select                                                  │   │
│  │ Options: All agency tags                                            │   │
│  │ Color-coded by category                                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  BUDGET FILTER                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Type: Range slider                                                  │   │
│  │ Fields: Total budget, Per person                                   │   │
│  │ Currency: User's preferred currency                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  SOURCE FILTER                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Type: Multi-select                                                  │   │
│  │ Options: website, instagram, facebook, whatsapp, email, phone,     │   │
│  │          referral, repeat, other                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Filter Presets

```typescript
/**
 * Filter preset definitions
 */
interface FilterPreset {
  id: string;
  name: string;
  description?: string;
  icon?: string;
  filters: ActiveFilters;
  sort?: SortConfig;
  isDefault?: boolean;
  isSystem?: boolean;
}

/**
 * System filter presets
 */
const SYSTEM_FILTER_PRESETS: FilterPreset[] = [
  {
    id: 'all_active',
    name: 'All Active',
    description: 'All trips that need attention',
    icon: 'inboxes',
    filters: {
      status: ['inquiry', 'quoted', 'confirmed', 'deposit_paid', 'fully_paid', 'booked', 'in_progress']
    },
    sort: { field: TripSortField.PRIORITY_SCORE, order: 'desc' },
    isDefault: true,
    isSystem: true
  },
  {
    id: 'needs_action',
    name: 'Needs Action',
    description: 'Trips awaiting your response',
    icon: 'alert-circle',
    filters: {
      status: ['inquiry', 'quoted'],
      assignedTo: ['me']
    },
    sort: { field: TripSortField.UPDATED_AT, order: 'asc' },
    isSystem: true
  },
  {
    id: 'departing_soon',
    name: 'Departing Soon',
    description: 'Trips departing in the next 7 days',
    icon: 'calendar',
    filters: {
      status: ['confirmed', 'deposit_paid', 'fully_paid', 'booked', 'in_progress'],
      dateRange: {
        field: 'departureDate',
        start: new Date(),
        end: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000)
      }
    },
    sort: { field: TripSortField.DEPARTURE_DATE, order: 'asc' },
    isSystem: true
  },
  {
    id: 'new_inquiries',
    name: 'New Inquiries',
    description: 'Trips in inquiry status from new customers',
    icon: 'sparkles',
    filters: {
      status: ['inquiry'],
      newCustomers: true
    },
    sort: { field: TripSortField.CREATED_AT, order: 'desc' },
    isSystem: true
  },
  {
    id: 'awaiting_payment',
    name: 'Awaiting Payment',
    description: 'Trips with pending payments',
    icon: 'credit-card',
    filters: {
      status: ['quoted', 'confirmed', 'deposit_paid'],
      pendingPayment: true
    },
    sort: { field: TripSortField.PRIORITY_SCORE, order: 'desc' },
    isSystem: true
  },
  {
    id: 'my_trips',
    name: 'My Trips',
    description: 'All trips assigned to you',
    icon: 'user',
    filters: {
      assignedTo: ['me']
    },
    sort: { field: TripSortField.PRIORITY_SCORE, order: 'desc' },
    isSystem: true
  },
  {
    id: 'unassigned',
    name: 'Unassigned',
    description: 'Trips not assigned to anyone',
    icon: 'user-minus',
    filters: {
      assignedTo: ['unassigned']
    },
    sort: { field: TripSortField.CREATED_AT, order: 'desc' },
    isSystem: true
  }
];

/**
 * Active filters state
 */
interface ActiveFilters {
  status?: TripStatus[];
  customerIds?: string[];
  assignedTo?: ('me' | 'unassigned' | string)[];
  destinations?: string[];
  tags?: string[];
  dateRange?: {
    field: 'createdAt' | 'updatedAt' | 'departureDate';
    start: Date;
    end: Date;
  };
  budgetRange?: {
    min: number;
    max: number;
    currency: string;
  };
  newCustomers?: boolean;
  pendingPayment?: boolean;
  overdue?: boolean;
}
```

---

## 5. Prioritization Logic

### 5.1 Urgency Indicators

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          URGENCY INDICATORS                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  CRITICAL (Requires immediate attention)                                    │
│  ────────────────────────────────────────                                   │
│  🔴 Departure within 48 hours                                            │
│  🔴 Payment overdue                                                      │
│  🔴 Critical document missing (passport/visa)                             │
│  🔴 Booking failure                                                       │
│  🔴 Customer complaint                                                    │
│                                                                             │
│  HIGH (Action needed today)                                                │
│  ────────────────────────────────                                           │
│  🟠 Departure within 7 days                                              │
│  🟠 Payment due within 3 days                                            │
│  🟠 Quoted > 24 hours ago (no response)                                  │
│  🟠 Inquiry > 4 hours old                                                │
│  🟠 Document expiring soon                                               │
│                                                                             │
│  NORMAL (Regular workflow)                                                 │
│  ────────────────────────────                                               │
│  🟢 Active trip with upcoming departure (30+ days)                       │
│  🟢 Payment due in 7+ days                                               │
│  🟢 Waiting for customer response                                        │
│                                                                             │
│  LOW (Can wait)                                                            │
│  ──────────────────                                                       │
│  ⚪ Departure > 60 days away                                              │
│  ⚪ Early planning stage                                                  │
│  ⚪ Awaiting customer-initiated action                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Priority Display

```typescript
/**
 * Priority badge component props
 */
interface PriorityBadgeProps {
  level: 'urgent' | 'high' | 'normal' | 'low';
  score?: number;
  reasons?: string[];
  showScore?: boolean;
}

/**
 * Priority indicator configuration
 */
const PRIORITY_CONFIG = {
  urgent: {
    color: 'red',
    label: 'Urgent',
    icon: 'alert-circle',
    bgColor: 'bg-red-50',
    textColor: 'text-red-700',
    borderColor: 'border-red-200'
  },
  high: {
    color: 'orange',
    label: 'High',
    icon: 'trending-up',
    bgColor: 'bg-orange-50',
    textColor: 'text-orange-700',
    borderColor: 'border-orange-200'
  },
  normal: {
    color: 'blue',
    label: 'Normal',
    icon: 'circle',
    bgColor: 'bg-blue-50',
    textColor: 'text-blue-700',
    borderColor: 'border-blue-200'
  },
  low: {
    color: 'gray',
    label: 'Low',
    icon: 'arrow-down',
    bgColor: 'bg-gray-50',
    textColor: 'text-gray-700',
    borderColor: 'border-gray-200'
  }
};

/**
 * Get priority reasons for display
 */
function getPriorityReasons(trip: Trip): string[] {
  const reasons: string[] = [];
  const now = new Date();

  // Departure urgency
  if (trip.departureDate) {
    const daysUntil = Math.ceil((trip.departureDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
    if (daysUntil <= 2) reasons.push('Departing within 48 hours');
    else if (daysUntil <= 7) reasons.push('Departing within 7 days');
  }

  // Payment urgency
  for (const payment of trip.payments || []) {
    if (payment.dueDate && payment.dueDate < now && !payment.paid) {
      reasons.push(`Payment overdue: ${formatCurrency(payment.amount)}`);
    } else if (payment.dueDate && payment.dueDate <= new Date(now.getTime() + 3 * 24 * 60 * 60 * 1000) && !payment.paid) {
      reasons.push(`Payment due soon: ${formatCurrency(payment.amount)}`);
    }
  }

  // Status urgency
  if (trip.status === 'inquiry') {
    const hoursSinceUpdate = (now.getTime() - trip.updatedAt.getTime()) / (1000 * 60 * 60);
    if (hoursSinceUpdate > 4) reasons.push(`Inquiry waiting ${Math.floor(hoursSinceUpdate)}h`);
  }

  if (trip.status === 'quoted') {
    const daysSinceQuote = (now.getTime() - trip.updatedAt.getTime()) / (1000 * 60 * 60 * 24);
    if (daysSinceQuote > 1) reasons.push(`Quote pending ${Math.floor(daysSinceQuote)}d`);
  }

  // Document urgency
  for (const doc of trip.requiredDocuments || []) {
    if (doc.status === 'missing' && doc.requiredBy) {
      const daysUntil = Math.ceil((doc.requiredBy.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
      if (daysUntil <= 7) reasons.push(`Document needed: ${doc.name}`);
    }
  }

  // New customer
  if (trip.customer.isNewCustomer) {
    reasons.push('New customer');
  }

  return reasons;
}
```

---

## 6. Real-Time Updates

### 6.1 WebSocket Integration

```typescript
/**
 * Inbox real-time update handler
 */
class InboxRealtimeHandler {
  private ws: WebSocket;
  private subscriptions: Set<string> = new Set();
  private updateCallbacks: Map<string, (update: TripUpdate) => void> = new Map();

  /**
   * Subscribe to trip updates
   */
  subscribe(userId: string, filters: ActiveFilters): void {
    const channel = this.buildChannel(userId, filters);
    this.subscriptions.add(channel);

    this.ws.send(JSON.stringify({
      action: 'subscribe',
      channel
    }));
  }

  /**
   * Unsubscribe from updates
   */
  unsubscribe(userId: string): void {
    for (const channel of this.subscriptions) {
      if (channel.startsWith(`user:${userId}`)) {
        this.ws.send(JSON.stringify({
          action: 'unsubscribe',
          channel
        }));
        this.subscriptions.delete(channel);
      }
    }
  }

  /**
   * Handle incoming update
   */
  private handleUpdate(update: TripUpdate): void {
    const { tripId, type } = update;

    // Notify subscribers
    for (const [callbackId, callback] of this.updateCallbacks) {
      callback(update);
    }

    // Invalidate cache for affected trip
    cache.invalidateTrip(tripId);
  }

  /**
   * Build subscription channel
   */
  private buildChannel(userId: string, filters: ActiveFilters): string {
    const parts = ['user', userId];

    if (filters.assignedTo?.includes('me')) {
      parts.push('assigned');
    }

    return parts.join(':');
  }
}

/**
 * Trip update event
 */
interface TripUpdate {
  tripId: string;
  type: 'created' | 'updated' | 'deleted' | 'status_changed';
  data?: Partial<Trip>;
  timestamp: Date;
  actor?: {
    id: string;
    name: string;
  };
}
```

### 6.2 Optimistic Updates

```typescript
/**
 * Optimistic update handler
 */
class OptimisticUpdateHandler {
  /**
   * Apply optimistic update to local state
   */
  applyOptimisticUpdate(
    trips: TripSummary[],
    tripId: string,
    update: Partial<Trip>
  ): TripSummary[] {
    return trips.map(trip => {
      if (trip.id !== tripId) return trip;

      // Apply the update
      return {
        ...trip,
        ...this.mergeUpdate(trip, update)
      };
    });
  }

  /**
   * Revert optimistic update on error
   */
  revertOptimisticUpdate(
    trips: TripSummary[],
    tripId: string,
    originalState: TripSummary
  ): TripSummary[] {
    return trips.map(trip =>
      trip.id === tripId ? originalState : trip
    );
  }

  /**
   * Merge update with existing trip
   */
  private mergeUpdate(trip: TripSummary, update: Partial<Trip>): TripSummary {
    const merged: TripSummary = { ...trip };

    if (update.status) merged.status = update.status;
    if (update.name) merged.name = update.name;
    if (update.customer) merged.customer = { ...trip.customer, ...update.customer };
    if (update.dates) merged.dates = { ...trip.dates, ...update.dates };
    if (update.assignment) merged.assignment = { ...trip.assignment, ...update.assignment };
    if (update.tags) merged.tags = update.tags;

    return merged;
  }
}
```

---

## 7. Performance Optimization

### 7.1 Virtual Scrolling

```typescript
/**
 * Virtual scrolling configuration for inbox
 */
interface VirtualScrollConfig {
  /** Item height (pixels) */
  itemHeight: number;

  /** Buffer size (items) */
  bufferSize: number;

  /** Overscan (items) */
  overscan: number;
}

/**
 * Virtual scroll hook for inbox list
 */
function useInboxVirtualScroll(config: VirtualScrollConfig) {
  const [visibleRange, setVisibleRange] = useState({ start: 0, end: 20 });
  const containerRef = useRef<HTMLDivElement>(null);

  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    const container = e.currentTarget;
    const scrollTop = container.scrollTop;
    const containerHeight = container.clientHeight;

    const start = Math.floor(scrollTop / config.itemHeight);
    const visibleCount = Math.ceil(containerHeight / config.itemHeight);
    const end = start + visibleCount;

    setVisibleRange({
      start: Math.max(0, start - config.overscan),
      end: end + config.overscan
    });
  }, [config]);

  return {
    visibleRange,
    containerRef,
    onScroll: handleScroll
  };
}
```

### 7.2 Pagination Strategy

```typescript
/**
 * Pagination configuration
 */
interface PaginationConfig {
  /** Initial page size */
  initialPageSize: number;

  /** Page size options */
  pageSizeOptions: number[];

  /** Max pages to keep in memory */
  maxCachedPages: number;

  /** Prefetch threshold (items from bottom) */
  prefetchThreshold: number;
}

/**
 * Infinite scroll hook
 */
function useInfiniteScroll(query: TripQuery, config: PaginationConfig) {
  const [trips, setTrips] = useState<TripSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [page, setPage] = useState(0);

  const loadMore = useCallback(async () => {
    if (loading || !hasMore) return;

    setLoading(true);
    try {
      const newTrips = await fetchTrips({
        ...query,
        pagination: { page: page + 1, pageSize: config.initialPageSize }
      });

      if (newTrips.length < config.initialPageSize) {
        setHasMore(false);
      }

      setTrips(prev => [...prev, ...newTrips]);
      setPage(p => p + 1);
    } finally {
      setLoading(false);
    }
  }, [query, page, loading, hasMore, config]);

  return {
    trips,
    loading,
    hasMore,
    loadMore
  };
}
```

---

## Summary

The Inbox Management system provides:

- **Efficient data model** with optimized database indexes
- **Smart sorting** with priority scoring based on multiple factors
- **Flexible filtering** with system and custom presets
- **Real-time updates** via WebSocket subscriptions
- **Performance optimization** through caching, virtual scrolling, and pagination
- **Prioritization logic** that considers urgency, status, and activity

---

**Next:** [INBOX_02_UX_UI_DEEP_DIVE](./INBOX_02_UX_UI_DEEP_DIVE.md) — UI patterns and interaction design
