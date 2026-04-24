# FIELD_04_CHANGE_TRACKING_DEEP_DIVE

> Part 4 of SmartCombobox & Field Editing Deep Dive
>
> **Previous:** [FIELD_03_DATA_DICT_DEEP_DIVE](./FIELD_03_DATA_DICT_DEEP_DIVE.md)
>
> **Series Complete:** See [FIELD_DEEP_DIVE_MASTER_INDEX](./FIELD_DEEP_DIVE_MASTER_INDEX.md)

---

## Change Tracking & Audit Trail System

Every change to trip data, customer information, and bookings must be tracked for compliance, debugging, and collaboration. This document covers the complete change tracking implementation.

---

## Table of Contents

1. [Tracking Architecture](#1-tracking-architecture)
2. [Change Record Structure](#2-change-record-structure)
3. [Capture Strategies](#3-capture-strategies)
4. [Audit Trail Display](#4-audit-trail-display)
5. [Compliance & Export](#5-compliance--export)
6. [Implementation](#6-implementation)

---

## 1. Tracking Architecture

### 1.1 System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CHANGE TRACKING ARCHITECTURE                        │
└─────────────────────────────────────────────────────────────────────────────┘

    USER ACTION
         │
         ▼
    ┌────────────────┐
    │  Field Change  │
    └────────┬───────┘
             │
             ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │                         CHANGE CAPTURE LAYER                        │
    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐│
    │  │ Auto Track  │  │ Manual      │  │ Bulk        │  │ System      ││
    │  │ (Forms)     │  │ Track       │  │ Import     │  │ Events      ││
    │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘│
    └─────────────────────────────────────────────────────────────────────┘
                          │
                          ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │                         CHANGE PROCESSING                           │
    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐│
    │  │ Normalize   │  │ Validate    │  │ Enrich     │  │ Compress    ││
    │  │ Value       │  │ Change      │  │ Context    │  │ Deltas      ││
    │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘│
    └─────────────────────────────────────────────────────────────────────┘
                          │
         ┌────────────────┼────────────────┐
         │                │                │
         ▼                ▼                ▼
    ┌─────────┐    ┌─────────┐    ┌─────────┐
    │ Memory  │    │ Indexed │    │ Archive │
    │ Store   │    │ Store   │    │ Store   │
    │(Recent) │    │(Search) │    │(Cold)   │
    └────┬────┘    └────┬────┘    └────┬────┘
         │              │              │
         └──────────────┼──────────────┘
                        │
                        ▼
              ┌─────────────────────┐
              │   CHANGE DISPLAY    │
              │  ┌───────────────┐  │
              │  │ Timeline View │  │
              │  │ Diff View     │  │
              │  │ History Panel │  │
              │  └───────────────┘  │
              └─────────────────────┘
```

### 1.2 Storage Strategy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CHANGE STORAGE STRATEGY                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  HOT STORE (Recent Changes)                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Retention: 30 days                                                  │   │
│  │ Access: In-memory cache + Redis                                      │   │
│  │ Index: By entity, user, timestamp                                    │   │
│  │ Purpose: Fast UI display, undo/redo                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  WARM STORE (Searchable History)                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Retention: 1 year                                                   │   │
│  │ Access: PostgreSQL with GIN index                                   │   │
│  │ Index: By entity, user, date range, change type                     │   │
│  │ Purpose: Audit trail search, compliance reports                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  COLD STORE (Archived)                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Retention: 7 years (or as required by law)                          │   │
│  │ Access: S3/Google Storage with compressed JSON                       │   │
│  │ Index: By entity, year                                               │   │
│  │ Purpose: Long-term compliance, data retention                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Change Record Structure

### 2.1 Core Change Schema

```typescript
/**
 * Change record structure
 */
interface ChangeRecord {
  /** Unique change identifier */
  id: string;

  /** Entity being changed */
  entity: {
    type: EntityType;
    id: string;
    name?: string;
  };

  /** Change metadata */
  metadata: {
    /** When the change occurred */
    timestamp: Date;

    /** Who made the change */
    actor: {
      id: string;
      name: string;
      type: 'user' | 'system' | 'api' | 'integration';
    };

    /** How the change was made */
    source: ChangeSource;

    /** Related session/correlation */
    correlationId?: string;

    /** IP address (for user changes) */
    ipAddress?: string;

    /** User agent */
    userAgent?: string;
  };

  /** The actual change */
  change: {
    /** Field or path that changed */
    path: string[];

    /** Previous value */
    previous: any;

    /** New value */
    current: any;

    /** Type of change */
    type: ChangeType;

    /** Whether this is part of a batch */
    batchId?: string;

    /** Related changes (e.g., cascading updates) */
    relatedChanges?: string[];
  };

  /** Additional context */
  context?: {
    /** Reason for change */
    reason?: string;

    /** Related entity (e.g., trip for booking change) */
    relatedEntity?: {
      type: EntityType;
      id: string;
    };

    /** Business context */
    businessContext?: Record<string, any>;

    /** UI context where change was made */
    uiContext?: {
      page: string;
      component: string;
      action: string;
    };
  };
}

/**
 * Entity types that can be tracked
 */
enum EntityType {
  CUSTOMER = 'customer',
  TRIP = 'trip',
  BOOKING = 'booking',
  BOOKING_FLIGHT = 'booking_flight',
  BOOKING_HOTEL = 'booking_hotel',
  BOOKING_ACTIVITY = 'booking_activity',
  SUPPLIER = 'supplier',
  AGENCY = 'agency',
  USER = 'user',
  QUOTE = 'quote',
  INVOICE = 'invoice',
  DOCUMENT = 'document'
}

/**
 * Change sources
 */
enum ChangeSource {
  /** User form input */
  USER_INPUT = 'user_input',

  /** User action (button click, drag-drop) */
  USER_ACTION = 'user_action',

  /** API call from external system */
  API = 'api',

  /** Integration (supplier sync, etc.) */
  INTEGRATION = 'integration',

  /** Automated system process */
  SYSTEM = 'system',

  /** Bulk import */
  IMPORT = 'import',

  /** Data migration */
  MIGRATION = 'migration',

  /** Batch operation */
  BATCH = 'batch',

  /** Undo operation */
  UNDO = 'undo',

  /** Redo operation */
  REDO = 'redo'
}

/**
 * Change types
 */
enum ChangeType {
  /** Create new entity */
  CREATE = 'create',

  /** Update existing value */
  UPDATE = 'update',

  /** Delete entity */
  DELETE = 'delete',

  /** Add to array */
  ADD = 'add',

  /** Remove from array */
  REMOVE = 'remove',

  /** Reorder array */
  REORDER = 'reorder',

  /** Restore deleted */
  RESTORE = 'restore',

  /** Bulk update */
  BULK_UPDATE = 'bulk_update'
}
```

### 2.2 Change Aggregation

```typescript
/**
 * Aggregated changes for display
 */
interface AggregatedChanges {
  /** Time window for aggregation */
  window: {
    start: Date;
    end: Date;
  };

  /** User who made changes */
  actor: {
    id: string;
    name: string;
  };

  /** Total changes in window */
  totalCount: number;

  /** Changes grouped by entity */
  byEntity: {
    entityType: EntityType;
    entityId: string;
    entityName?: string;
    changes: ChangeRecord[];
  }[];

  /** Changes grouped by type */
  byType: {
    changeType: ChangeType;
    count: number;
  }[];

  /** Fields that were changed */
  changedFields: string[];
}

/**
 * Change batch for related changes
 */
interface ChangeBatch {
  id: string;

  /** When batch was created */
  createdAt: Date;

  /** User who created batch */
  createdBy: string;

  /** Batch description */
  description?: string;

  /** All changes in batch */
  changes: ChangeRecord[];

  /** Batch status */
  status: 'pending' | 'applied' | 'failed' | 'rolled_back';
}
```

---

## 3. Capture Strategies

### 3.1 Automatic Capture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        AUTOMATIC CHANGE CAPTURE                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FORM FIELD CHANGES                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Trigger: onChange event                                              │   │
│  │ Capture: Before/after values                                         │   │
│  │ Debounce: 500ms (to avoid excessive records during typing)           │   │
│  │ Context: Form ID, field path                                         │   │
│  │                                                                     │   │
│  │ Exception: Password fields (never captured)                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  COMBOBOX SELECTIONS                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Trigger: onSelect                                                   │   │
│  │ Capture: Previous selection ID/name, new selection ID/name          │   │
│  │ Context: Search query, filters used                                 │   │
│  │                                                                     │   │
│  │ Special: Capture if "create new" option was selected               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ARRAY OPERATIONS                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Trigger: onAdd, onRemove, onReorder                                 │   │
│  │ Capture: Index, affected item, array state before/after            │   │
│  │ Context: Parent field, array type                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DRAG & DROP                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Trigger: onDrop                                                     │   │
│  │ Capture: Old index, new index, affected items                      │   │
│  │ Context: Container ID, drop zone                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  STATUS TRANSITIONS                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Trigger: Status change                                              │   │
│  │ Capture: Old status, new status, trigger/transition                │   │
│  │ Context: Entity type, workflow state                               │   │
│  │                                                                     │   │
│  │ Special: Always capture status changes regardless of other tracking │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Manual Capture

```typescript
/**
 * Manual change tracking for special operations
 */
class ManualChangeTracker {
  /**
   * Record a manual change with full context
   */
  async recordManualChange(options: {
    entityType: EntityType;
    entityId: string;
    field: string;
    previous: any;
    current: any;
    reason: string;
    actorId: string;
  }): Promise<ChangeRecord> {
    const change: ChangeRecord = {
      id: generateId(),
      entity: {
        type: options.entityType,
        id: options.entityId
      },
      metadata: {
        timestamp: new Date(),
        actor: {
          id: options.actorId,
          name: await this.getUserName(options.actorId),
          type: 'user'
        },
        source: ChangeSource.USER_ACTION
      },
      change: {
        path: [options.field],
        previous: options.previous,
        current: options.current,
        type: ChangeType.UPDATE
      },
      context: {
        reason: options.reason
      }
    };

    await this.saveChange(change);
    return change;
  }

  /**
   * Record a batch of changes as a single unit
   */
  async recordBatch(options: {
    entityType: EntityType;
    entityId: string;
    changes: Array<{
      field: string;
      previous: any;
      current: any;
    }>;
    reason: string;
    actorId: string;
  }): Promise<ChangeBatch> {
    const batchId = generateId();

    const changes: ChangeRecord[] = await Promise.all(
      options.changes.map(change =>
        this.recordManualChange({
          entityType: options.entityType,
          entityId: options.entityId,
          field: change.field,
          previous: change.previous,
          current: change.current,
          reason: options.reason,
          actorId: options.actorId
        })
      )
    );

    // Link all changes to the batch
    for (const change of changes) {
      change.change.batchId = batchId;
      change.change.relatedChanges = changes
        .filter(c => c.id !== change.id)
        .map(c => c.id);
    }

    const batch: ChangeBatch = {
      id: batchId,
      createdAt: new Date(),
      createdBy: options.actorId,
      description: options.reason,
      changes,
      status: 'applied'
    };

    await this.saveBatch(batch);
    return batch;
  }
}
```

### 3.3 System Event Capture

```typescript
/**
 * System event change tracker
 */
class SystemEventTracker {
  /**
   * Capture automated system changes
   */
  async recordSystemChange(options: {
    entityType: EntityType;
    entityId: string;
    field: string;
    previous: any;
    current: any;
    reason: string;
    systemComponent: string;
  }): Promise<ChangeRecord> {
    const change: ChangeRecord = {
      id: generateId(),
      entity: {
        type: options.entityType,
        id: options.entityId
      },
      metadata: {
        timestamp: new Date(),
        actor: {
          id: 'system',
          name: options.systemComponent,
          type: 'system'
        },
        source: ChangeSource.SYSTEM
      },
      change: {
        path: [options.field],
        previous: options.previous,
        current: options.current,
        type: ChangeType.UPDATE
      },
      context: {
        reason: options.reason,
        businessContext: {
          automated: true,
          component: options.systemComponent
        }
      }
    };

    await this.saveChange(change);
    return change;
  }

  /**
   * Capture integration/sync changes
   */
  async recordIntegrationChange(options: {
    entityType: EntityType;
    entityId: string;
    changes: Record<string, { previous: any; current: any }>;
    integrationName: string;
    externalReference?: string;
  }): Promise<ChangeRecord[]> {
    const records: ChangeRecord[] = [];

    for (const [field, values] of Object.entries(options.changes)) {
      const change: ChangeRecord = {
        id: generateId(),
        entity: {
          type: options.entityType,
          id: options.entityId
        },
        metadata: {
          timestamp: new Date(),
          actor: {
            id: options.integrationName,
            name: options.integrationName,
            type: 'integration'
          },
          source: ChangeSource.INTEGRATION,
          correlationId: options.externalReference
        },
        change: {
          path: [field],
          previous: values.previous,
          current: values.current,
          type: ChangeType.UPDATE
        },
        context: {
          reason: `Synced from ${options.integrationName}`,
          businessContext: {
            integration: options.integrationName,
            externalReference: options.externalReference
          }
        }
      };

      records.push(change);
    }

    await Promise.all(records.map(c => this.saveChange(c)));
    return records;
  }
}
```

---

## 4. Audit Trail Display

### 4.1 Timeline View

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          AUDIT TRAIL TIMELINE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        Trip History                                   │   │
│  │                                [Filter] [Export]                     │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │                                                                     │   │
│  │  ┌─────────────────────────────────────────────────────────────┐    │   │
│  │  │ 🕐 Today, 2:34 PM                                            │    │   │
│  │  │ ┌─────────────────────────────────────────────────────────┐  │    │   │
│  │  │ │ John Doe updated trip status                             │  │    │   │
│  │  │ │ ┌─────────────────────────────────────────────────────┐ │  │    │   │
│  │  │ │ │ Status: quoted → confirmed                            │ │  │    │   │
│  │  │ │ └─────────────────────────────────────────────────────┘ │  │    │   │
│  │  │ └─────────────────────────────────────────────────────────┘  │    │   │
│  │  └─────────────────────────────────────────────────────────────┘    │   │
│  │                                                                     │   │
│  │  ┌─────────────────────────────────────────────────────────────┐    │   │
│  │  │ 🕐 Today, 2:30 PM                                            │    │   │
│  │  │ ┌─────────────────────────────────────────────────────────┐  │    │   │
│  │  │ │ John Doe added booking                                    │  │    │   │
│  │  │ │ Flight: AI 301 • Delhi to Mumbai                          │  │    │   │
│  │  │ └─────────────────────────────────────────────────────────┘  │    │   │
│  │  │                [View Details]                                │    │   │
│  │  └─────────────────────────────────────────────────────────────┘    │   │
│  │                                                                     │   │
│  │  ┌─────────────────────────────────────────────────────────────┐    │   │
│  │  │ 🕐 Today, 2:15 PM                                            │    │   │
│  │  │ ┌─────────────────────────────────────────────────────────┐  │    │   │
│  │  │ │ System updated traveler ages                              │  │    │   │
│  │  │ │ ┌─────────────────────────────────────────────────────┐ │  │    │   │
│  │  │ │ │ John Smith: 34 → 35 years                             │ │  │    │   │
│  │  │ │ │ Jane Smith: 32 → 33 years                             │ │  │    │   │
│  │  │ │ └─────────────────────────────────────────────────────┘ │  │    │   │
│  │  │ └─────────────────────────────────────────────────────────┘  │    │   │
│  │  │                [View Details]                                │    │   │
│  │  └─────────────────────────────────────────────────────────────┘    │   │
│  │                                                                     │   │
│  │  ┌─────────────────────────────────────────────────────────────┐    │   │
│  │  │ 🕐 Today, 11:45 AM                                           │    │   │
│  │  │ ┌─────────────────────────────────────────────────────────┐  │    │   │
│  │  │ │ Jane Smith updated destinations                            │  │    │   │
│  │  │ │ ┌─────────────────────────────────────────────────────┐ │  │    │   │
│  │  │ │ │ Added: Paris, France                                  │ │  │    │   │
│  │  │ │ │ Removed: London, United Kingdom                        │ │  │    │   │
│  │  │ │ └─────────────────────────────────────────────────────┘ │  │    │   │
│  │  │ └─────────────────────────────────────────────────────────┘  │    │   │
│  │  └─────────────────────────────────────────────────────────────┘    │   │
│  │                                                                     │   │
│  │  ┌─────────────────────────────────────────────────────────────┐    │   │
│  │  │ 🕐 Yesterday, 4:20 PM                                        │    │   │
│  │  │ ┌─────────────────────────────────────────────────────────┐  │    │   │
│  │  │ │ System created trip                                       │  │    │   │
│  │  │ │ Trip: Summer Vacation 2024                                │  │    │   │
│  │  │ └─────────────────────────────────────────────────────────┘  │    │   │
│  │  └─────────────────────────────────────────────────────────────┘    │   │
│  │                                                                     │   │
│  │                                     [Load More]                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Diff View

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             CHANGE DIFF VIEW                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Change Details: Trip Budget Updated                                   │   │
│  │                                                                     │   │
│  │ ┌─────────────────────────────────────────────────────────────────┐ │   │
│  │ │ Actor: John Doe                           Today, 2:15 PM        │ │   │
│  │ │ Source: Manual update                                             │ │   │
│  │ └─────────────────────────────────────────────────────────────────┘ │   │
│  │                                                                     │   │
│  │ ┌─────────────────────────────────────────────────────────────────┐ │   │
│  │ │ Field Changes                                                     │ │   │
│  │ ├─────────────────────────────────────────────────────────────────┤ │   │
│  │ │ ┌─────────────────────────────────────────────────────────────┐ │ │   │
│  │ │ │ trip.budget.amount                                           │ │ │   │
│  │ │ │ ┌─────────────────────────┐  ┌─────────────────────────┐     │ │ │   │
│  │ │ │ │ Before                 │  │ After                  │     │ │ │   │
│  │ │ │ │ $10,000.00 USD         │  │ $12,500.00 USD         │     │ │ │   │
│  │ │ │ └─────────────────────────┘  └─────────────────────────┘     │ │ │   │
│  │ │ └─────────────────────────────────────────────────────────────┘ │ │   │
│  │ │                                                                 │ │   │
│  │ │ ┌─────────────────────────────────────────────────────────────┐ │ │   │
│  │ │ │ trip.budget.perPerson                                        │ │ │   │
│  │ │ │ ┌─────────────────────────┐  ┌─────────────────────────┐     │ │ │   │
│  │ │ │ │ Before                 │  │ After                  │     │ │ │   │
│  │ │ │ │ $5,000.00 USD          │  │ $6,250.00 USD          │     │ │ │   │
│  │ │ │ └─────────────────────────┘  └─────────────────────────┘     │ │ │   │
│  │ │ └─────────────────────────────────────────────────────────────┘ │ │   │
│  │ └─────────────────────────────────────────────────────────────────┘ │   │
│  │                                                                     │   │
│  │ ┌─────────────────────────────────────────────────────────────────┐ │   │
│  │ │ Context                                                           │ │   │
│  │ │ Reason: Customer requested budget increase for better hotels     │ │   │
│  │ │ UI: Trip Settings page → Budget section                         │   │
│  │ └─────────────────────────────────────────────────────────────────┘ │   │
│  │                                                                     │   │
│  │                              [Revert Change] [Export]               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.3 Field History Panel

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          FIELD HISTORY PANEL                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 📋 Trip Budget — History                              [Close]       │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │                                                                     │   │
│  │ Current Value: $12,500.00 USD                                        │   │
│  │ Last Updated: Today, 2:15 PM by John Doe                             │   │
│  │ Total Changes: 4                                                     │   │
│  │                                                                     │   │
│  │ ┌─────────────────────────────────────────────────────────────────┐ │   │
│  │ │ Change Timeline                                                  │ │   │
│  │ ├─────────────────────────────────────────────────────────────────┤ │   │
│  │ │                                                                 │ │   │
│  │ │  ●──────────────────────────────────────────────────────────    │ │   │
│  │ │  │ Today, 2:15 PM                                               │ │   │
│  │ │  │ $10,000 → $12,500 USD                                       │ │   │
│  │ │  │ John Doe: "Customer requested increase"                     │ │   │
│  │ │  │                                                             │ │   │
│  │ │  │                                                            │ │   │
│  │ │  ●──────────────────────────────────────────────────────────    │ │   │
│  │ │  │ Yesterday, 5:30 PM                                           │ │   │
│  │ │  │ $8,000 → $10,000 USD                                        │ │   │
│  │ │  │ Jane Smith: "Added buffer for activities"                    │ │   │
│  │ │  │                                                             │ │   │
│  │ │  │                                                            │ │   │
│  │ │  ●──────────────────────────────────────────────────────────    │ │   │
│  │ │  │ Apr 20, 3:45 PM                                             │ │   │
│  │ │  │ $7,500 → $8,000 USD                                         │ │   │
│  │ │  │ System: "Auto-adjusted for 3rd traveler"                     │ │   │
│  │ │  │                                                             │ │   │
│  │ │  │                                                            │ │   │
│  │ │  ●──────────────────────────────────────────────────────────    │ │   │
│  │ │  │ Apr 20, 11:00 AM                                            │ │   │
│  │ │  │ Initial value: $7,500 USD                                    │ │   │
│  │ │  │ John Doe: "Created trip"                                    │ │   │
│  │ │  │                                                             │ │   │
│  │ └─────────────────────────────────────────────────────────────────┘ │   │
│  │                                                                     │   │
│  │                              [Export Full History]                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.4 Component Specification

```typescript
/**
 * Change timeline component props
 */
interface ChangeTimelineProps {
  /** Entity to show changes for */
  entity: {
    type: EntityType;
    id: string;
  };

  /** Filter options */
  filters?: {
    /** Change types to include */
    types?: ChangeType[];

    /** Actors to include */
    actors?: string[];

    /** Date range */
    dateRange?: {
      start: Date;
      end: Date;
    };

    /** Fields to include */
    fields?: string[];
  };

  /** Display options */
  options?: {
    /** Show inline diffs */
    showDiffs?: boolean;

    /** Group by actor */
    groupByActor?: boolean;

    /** Max items to show */
    maxItems?: number;

    /** Enable load more */
    enableLoadMore?: boolean;
  };

  /** Callbacks */
  callbacks?: {
    /** When change is clicked */
    onChangeClick?: (change: ChangeRecord) => void;

    /** When revert is requested */
    onRevert?: (change: ChangeRecord) => void;
  };
}

/**
 * Change detail view props
 */
interface ChangeDetailProps {
  /** Change to display */
  change: ChangeRecord;

  /** Related changes (for batch) */
  relatedChanges?: ChangeRecord[];

  /** Display mode */
  mode?: 'modal' | 'drawer' | 'inline';

  /** Enable revert */
  enableRevert?: boolean;

  /** Callbacks */
  callbacks?: {
    onRevert?: (change: ChangeRecord) => void;
    onClose?: () => void;
  };
}

/**
 * Field history panel props
 */
interface FieldHistoryProps {
  /** Entity containing the field */
  entity: {
    type: EntityType;
    id: string;
  };

  /** Field path */
  fieldPath: string[];

  /** Display mode */
  mode?: 'panel' | 'popover' | 'modal';

  /** Max history items */
  maxItems?: number;
}
```

---

## 5. Compliance & Export

### 5.1 Export Formats

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          AUDIT TRAIL EXPORT OPTIONS                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  CSV EXPORT                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Columns:                                                             │   │
│  │ • Timestamp                                                          │   │
│  │ • Actor Name                                                         │   │
│  │ • Actor Type                                                         │   │
│  │ • Entity Type                                                        │   │
│  │ • Entity ID                                                          │   │
│  │ • Field Path                                                         │   │
│  │ • Change Type                                                        │   │
│  │ • Previous Value                                                     │   │
│  │ • Current Value                                                      │   │
│  │ • Reason/Context                                                    │   │
│  │                                                                     │   │
│  │ Use case: Data analysis, spreadsheet review                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  JSON EXPORT                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Structure: Full ChangeRecord objects                                 │   │
│  │                                                                     │   │
│  │ {                                                                   │   │
│  │   "entity": { "type": "trip", "id": "TRP-2024..." },              │   │
│  │   "changes": [                                                      │   │
│  │     { "id": "...", "change": {...}, "metadata": {...} },            │   │
│  │     ...                                                              │   │
│  │   ],                                                                │   │
│  │   "exportedAt": "2024-04-24T12:00:00Z"                              │   │
│  │ }                                                                   │   │
│  │                                                                     │   │
│  │ Use case: API consumption, data migration                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  PDF EXPORT                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Format: Formatted document with                                      │   │
│  │   • Entity information header                                       │   │
│  │   • Timeline view                                                  │   │
│  │   • Diff highlights                                                 │   │
│  │   • Actor signatures                                                │   │
│  │                                                                     │   │
│  │ Use case: Legal documentation, compliance records                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  AUDIT REPORT                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Format: Structured report with                                       │   │
│  │   • Executive summary                                               │   │
│  │   • Change statistics                                               │   │
│  │   • Actor activity summary                                           │   │
│  │   • Entity change timeline                                          │   │
│  │   • Detailed change log                                             │   │
│  │   • Compliance notes                                                │   │
│  │                                                                     │   │
│  │ Use case: Management review, audit requests                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Retention Policies

```typescript
/**
 * Change retention policy
 */
interface RetentionPolicy {
  /** Hot store retention */
  hot: {
    duration: number; // days
    maxSize: number; // MB
  };

  /** Warm store retention */
  warm: {
    duration: number; // days
    compression: boolean;
  };

  /** Cold store retention */
  cold: {
    duration: number; // days
    storageClass: string;
  };

  /** Per-entity type overrides */
  overrides?: {
    entityType: EntityType;
    retention: number; // days
  }[];
}

/**
 * Default retention policies
 */
const DEFAULT_RETENTION: RetentionPolicy = {
  hot: {
    duration: 30,
    maxSize: 1024 // 1GB
  },
  warm: {
    duration: 365,
    compression: true
  },
  cold: {
    duration: 2555, // 7 years
    storageClass: 'glacier'
  },
  overrides: [
    {
      entityType: EntityType.CUSTOMER,
      retention: 3650 // 10 years for customer data
    },
    {
      entityType: EntityType.INVOICE,
      retention: 3650 // 10 years for financial records
    },
    {
      entityType: EntityType.DOCUMENT,
      retention: 3650 // 10 years for legal documents
    }
  ]
};
```

### 5.3 Compliance Features

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          COMPLIANCE FEATURES                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  IMMUTABLE RECORDS                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Once written, change records cannot be:                              │   │
│  │ • Modified                                                            │   │
│  │ • Deleted (except through retention policy)                          │   │
│  │ • Altered in any way                                                  │   │
│  │                                                                     │   │
│  │ Technical implementation:                                            │   │
│  │ • Write-once storage (S3 Object Lock)                                │   │
│  │ • Cryptographic hashing of records                                   │   │
│  │ • Append-only log structure                                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  CHAIN OF CUSTODY                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Each change record includes:                                         │   │
│  │ • Actor authentication proof                                         │   │
│  │ • Timestamp with server time                                        │   │
│  │ • IP address for user actions                                        │   │
│  │ • Session/correlation ID linking                                    │   │
│  │ • Digital signature for critical changes                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  TAMPER-EVIDENT STORAGE                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ • Daily integrity checks using hash verification                    │   │
│  │ • Tamper alerts sent to security team                               │   │
│  │ • Backup copies stored separately                                   │   │
│  │ • Audit log of all export/access operations                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ACCESS LOGGING                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ All access to change history is logged:                             │   │
│  │ • Who accessed                                                       │   │
│  │ • When accessed                                                      │   │
│  │ • What was viewed/exported                                           │   │
│  │ • Purpose of access (if specified)                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Implementation

### 6.1 Change Tracking Service

```typescript
/**
 * Main change tracking service
 */
class ChangeTrackingService {
  private hotStore: ChangeStore;
  private warmStore: ChangeStore;
  private coldStore: ChangeStore;
  private retention: RetentionPolicy;

  /**
   * Record a new change
   */
  async record(change: Omit<ChangeRecord, 'id' | 'metadata'>): Promise<ChangeRecord> {
    const record: ChangeRecord = {
      id: generateId(),
      metadata: {
        timestamp: new Date(),
        actor: change.metadata.actor,
        source: change.metadata.source,
        correlationId: change.metadata.correlationId,
        ipAddress: change.metadata.ipAddress,
        userAgent: change.metadata.userAgent
      },
      entity: change.entity,
      change: change.change,
      context: change.context
    };

    // Determine which store to use
    const store = this.selectStore(record);

    // Save to store
    await store.save(record);

    // Trigger real-time updates if needed
    await this.emitChangeEvent(record);

    return record;
  }

  /**
   * Query changes for an entity
   */
  async query(options: ChangeQueryOptions): Promise<ChangeRecord[]> {
    const { entityType, entityId, dateRange, limit, offset } = options;

    // Try hot store first
    let records = await this.hotStore.query({
      entityType,
      entityId,
      dateRange,
      limit,
      offset
    });

    // If not enough, check warm store
    if (records.length < (limit || 50)) {
      const warmRecords = await this.warmStore.query({
        entityType,
        entityId,
        dateRange,
        limit: (limit || 50) - records.length,
        offset
      });

      records = [...records, ...warmRecords];
    }

    // Sort by timestamp descending
    records.sort((a, b) =>
      b.metadata.timestamp.getTime() - a.metadata.timestamp.getTime()
    );

    return records;
  }

  /**
   * Get changes for a specific field
   */
  async getFieldHistory(
    entityType: EntityType,
    entityId: string,
    fieldPath: string[]
  ): Promise<ChangeRecord[]> {
    const allChanges = await this.query({
      entityType,
      entityId,
      limit: 1000
    });

    return allChanges.filter(change =>
      this.pathsMatch(change.change.path, fieldPath)
    );
  }

  /**
   * Revert a specific change
   */
  async revertChange(
    changeId: string,
    actorId: string,
    reason: string
  ): Promise<void> {
    const change = await this.getById(changeId);
    if (!change) {
      throw new Error('Change not found');
    }

    // Apply the reverse of the change
    const revertChange: Omit<ChangeRecord, 'id' | 'metadata'> = {
      entity: change.entity,
      change: {
        ...change.change,
        previous: change.change.current,
        current: change.change.previous,
        type: ChangeType.UPDATE
      },
      context: {
        reason: `Reverting change ${changeId}: ${reason}`,
        relatedEntity: {
          type: change.entity.type,
          id: change.entity.id
        }
      }
    };

    await this.record({
      ...revertChange,
      metadata: {
        actor: {
          id: actorId,
          name: await this.getUserName(actorId),
          type: 'user'
        },
        source: ChangeSource.UNDO,
        correlationId: changeId
      }
    });

    // Actually apply the revert to the entity
    await this.applyRevert(change, actorId);
  }

  /**
   * Export changes
   */
  async export(options: ExportOptions): Promise<ExportResult> {
    const { entityType, entityId, format, dateRange } = options;

    const changes = await this.query({
      entityType,
      entityId,
      dateRange,
      limit: 10000
    });

    let result: ExportResult;

    switch (format) {
      case 'csv':
        result = {
          format: 'csv',
          data: this.toCSV(changes),
          filename: `${entityType}_${entityId}_changes.csv`
        };
        break;

      case 'json':
        result = {
          format: 'json',
          data: JSON.stringify(changes, null, 2),
          filename: `${entityType}_${entityId}_changes.json`
        };
        break;

      case 'pdf':
        result = {
          format: 'pdf',
          data: await this.toPDF(changes),
          filename: `${entityType}_${entityId}_changes.pdf`
        };
        break;

      case 'audit':
        result = {
          format: 'audit',
          data: await this.toAuditReport(changes),
          filename: `${entityType}_${entityId}_audit_report.pdf`
        };
        break;

      default:
        throw new Error(`Unsupported format: ${format}`);
    }

    // Log the export
    await this.logExport(options);

    return result;
  }

  /**
   * Select appropriate store based on change age
   */
  private selectStore(change: ChangeRecord): ChangeStore {
    const age = Date.now() - change.metadata.timestamp.getTime();
    const hotRetention = this.retention.hot.duration * 24 * 60 * 60 * 1000;
    const warmRetention = this.retention.warm.duration * 24 * 60 * 60 * 1000;

    if (age < hotRetention) {
      return this.hotStore;
    } else if (age < warmRetention) {
      return this.warmStore;
    } else {
      return this.coldStore;
    }
  }

  /**
   * Check if two paths match
   */
  private pathsMatch(path1: string[], path2: string[]): boolean {
    if (path1.length !== path2.length) return false;
    return path1.every((segment, i) => segment === path2[i]);
  }

  /**
   * Get change by ID
   */
  private async getById(id: string): Promise<ChangeRecord | null> {
    // Try hot, then warm, then cold
    const stores = [this.hotStore, this.warmStore, this.coldStore];

    for (const store of stores) {
      const change = await store.getById(id);
      if (change) return change;
    }

    return null;
  }

  /**
   * Emit real-time change event
   */
  private async emitChangeEvent(change: ChangeRecord): Promise<void> {
    // Publish to WebSocket/EventBus for real-time UI updates
    await this.eventBus.publish('change.recorded', {
      entityType: change.entity.type,
      entityId: change.entity.id,
      changeId: change.id,
      timestamp: change.metadata.timestamp
    });
  }

  /**
   * Apply revert to entity
   */
  private async applyRevert(change: ChangeRecord, actorId: string): Promise<void> {
    // Entity-specific revert logic
    switch (change.entity.type) {
      case EntityType.TRIP:
        await this.tripService.updateField(
          change.entity.id,
          change.change.path.join('.'),
          change.change.previous,
          actorId
        );
        break;

      case EntityType.CUSTOMER:
        await this.customerService.updateField(
          change.entity.id,
          change.change.path.join('.'),
          change.change.previous,
          actorId
        );
        break;

      // ... other entity types
    }
  }

  /**
   * Log export for compliance
   */
  private async logExport(options: ExportOptions): Promise<void> {
    await this.complianceService.logEvent({
      type: 'change_export',
      entityType: options.entityType,
      entityId: options.entityId,
      format: options.format,
      dateRange: options.dateRange,
      timestamp: new Date()
    });
  }

  /**
   * Convert changes to CSV
   */
  private toCSV(changes: ChangeRecord[]): string {
    const headers = [
      'Timestamp',
      'Actor',
      'Actor Type',
      'Entity Type',
      'Entity ID',
      'Field',
      'Change Type',
      'Previous Value',
      'Current Value',
      'Reason'
    ];

    const rows = changes.map(change => [
      change.metadata.timestamp.toISOString(),
      change.metadata.actor.name,
      change.metadata.actor.type,
      change.entity.type,
      change.entity.id,
      change.change.path.join('.'),
      change.change.type,
      this.formatValue(change.change.previous),
      this.formatValue(change.change.current),
      change.context?.reason || ''
    ]);

    return [headers, ...rows]
      .map(row => row.map(cell => `"${cell}"`).join(','))
      .join('\n');
  }

  /**
   * Format value for CSV
   */
  private formatValue(value: any): string {
    if (value === null) return '';
    if (value === undefined) return '';
    if (typeof value === 'object') return JSON.stringify(value);
    return String(value);
  }

  /**
   * Generate PDF report
   */
  private async toPDF(changes: ChangeRecord[]): Promise<Buffer> {
    // PDF generation implementation
    throw new Error('Not implemented');
  }

  /**
   * Generate audit report
   */
  private async toAuditReport(changes: ChangeRecord[]): Promise<Buffer> {
    // Audit report generation implementation
    throw new Error('Not implemented');
  }

  /**
   * Get user name
   */
  private async getUserName(userId: string): Promise<string> {
    // User service lookup
    return userId;
  }
}

/**
 * Change query options
 */
interface ChangeQueryOptions {
  entityType: EntityType;
  entityId: string;
  dateRange?: {
    start: Date;
    end: Date;
  };
  limit?: number;
  offset?: number;
}

/**
 * Export options
 */
interface ExportOptions {
  entityType: EntityType;
  entityId: string;
  format: 'csv' | 'json' | 'pdf' | 'audit';
  dateRange?: {
    start: Date;
    end: Date;
  };
  includeRelated?: boolean;
}

/**
 * Export result
 */
interface ExportResult {
  format: string;
  data: string | Buffer;
  filename: string;
}
```

### 6.2 React Hook Integration

```typescript
/**
 * React hook for field change tracking
 */
function useFieldChangeTracking(
  entityType: EntityType,
  entityId: string,
  fieldPath: string[]
) {
  const [history, setHistory] = useState<ChangeRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const trackingService = useChangeTrackingService();

  useEffect(() => {
    loadHistory();
  }, [entityType, entityId, fieldPath]);

  const loadHistory = useCallback(async () => {
    setLoading(true);
    try {
      const records = await trackingService.getFieldHistory(
        entityType,
        entityId,
        fieldPath
      );
      setHistory(records);
    } catch (err) {
      setError(err as Error);
    } finally {
      setLoading(false);
    }
  }, [entityType, entityId, fieldPath, trackingService]);

  const revert = useCallback(async (changeId: string, reason: string) => {
    await trackingService.revertChange(changeId, await getCurrentUserId(), reason);
    await loadHistory();
  }, [trackingService, loadHistory]);

  return {
    history,
    loading,
    error,
    revert,
    refresh: loadHistory
  };
}

/**
 * React hook for entity change timeline
 */
function useEntityChangeTimeline(
  entityType: EntityType,
  entityId: string,
  options?: {
    limit?: number;
    types?: ChangeType[];
    actors?: string[];
  }
) {
  const [changes, setChanges] = useState<ChangeRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);

  const trackingService = useChangeTrackingService();
  const offset = useRef(0);

  const loadChanges = useCallback(async () => {
    setLoading(true);
    try {
      const records = await trackingService.query({
        entityType,
        entityId,
        limit: options?.limit || 50,
        offset: offset.current
      });

      // Filter by type if specified
      let filtered = records;
      if (options?.types?.length) {
        filtered = filtered.filter(r => options.types!.includes(r.change.type));
      }

      // Filter by actor if specified
      if (options?.actors?.length) {
        filtered = filtered.filter(r =>
          options.actors!.includes(r.metadata.actor.id)
        );
      }

      setChanges(prev => [...prev, ...filtered]);
      offset.current += filtered.length;
      setHasMore(filtered.length >= (options?.limit || 50));
    } finally {
      setLoading(false);
    }
  }, [entityType, entityId, options, trackingService]);

  useEffect(() => {
    loadChanges();
  }, [loadChanges]);

  return {
    changes,
    loading,
    hasMore,
    loadMore: loadChanges
  };
}
```

---

## Summary

The Change Tracking system provides:

- **Automatic capture** of all field changes with debouncing
- **Manual tracking** for special operations
- **System event capture** for automated processes
- **Multiple storage tiers** (hot/warm/cold) for optimal performance
- **Timeline view** for visual change history
- **Diff view** for detailed before/after comparison
- **Field history panel** for per-field audit trails
- **Export options** (CSV, JSON, PDF, audit reports)
- **Compliance features** (immutable records, chain of custody, access logging)
- **Revert capability** for undoing specific changes

---

**Series Complete:** See [FIELD_DEEP_DIVE_MASTER_INDEX](./FIELD_DEEP_DIVE_MASTER_INDEX.md) for the complete Field Editing & SmartCombobox deep dive series.
