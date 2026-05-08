# Phase 5A: Booking Execution Workflow

## Context

Phase 4F (closed 2026-05-08) completed the extraction ops layer: attempt history, retry, smoke test, quality report. The system now has complete booking_data collection, document management, extraction with multi-model fallback, and readiness assessment.

Phase 5A adds the execution control layer: what the agent must do next to safely execute the booking.

**This is internal execution control only. No payments, supplier APIs, email automation, or customer portal.**

---

## Scope

1. Booking task model and table
2. Task state machine with 7 statuses and enforced backend transitions
3. Explicit task generation from booking readiness + document state
4. Task reconciliation: refresh blocker state for active system-generated tasks on each generate call
5. Manual task creation and editing
6. Task ownership and due dates
7. Task blockers referencing state (refs only, no PII values)
8. Safe title/description policy: template-only for system tasks, no PII
9. OpsPanel Booking Execution section
10. Metadata-only audit events
11. Idempotent generation with scoped hash

---

## Part 1: Data Model

### Table: `booking_tasks`

```python
class BookingTask(Base):
    __tablename__ = "booking_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    trip_id: Mapped[str] = mapped_column(String(36), nullable=False)
    agency_id: Mapped[str] = mapped_column(ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False)

    # Task identity
    task_type: Mapped[str] = mapped_column(String(40), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)  # template-only for system tasks, free-text for custom
    description: Mapped[str] = mapped_column(String(500), nullable=True)  # null for system tasks in Phase 5A

    # State
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="not_started")
    priority: Mapped[str] = mapped_column(String(20), nullable=False, server_default="medium")

    # Ownership
    owner_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    due_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Blocker
    blocker_code: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    blocker_refs: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # refs only, no PII

    # Source tracking
    source: Mapped[str] = mapped_column(String(30), nullable=False, server_default="agent_created")
    generation_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # idempotency

    # Audit
    created_by: Mapped[str] = mapped_column(String(36), nullable=False)
    completed_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_bt_trip_id", "trip_id"),
        Index("ix_bt_agency_id", "agency_id"),
        Index("ix_bt_status", "status"),
        Index("ix_bt_task_type", "task_type"),
        Index("ix_bt_trip_status", "trip_id", "status"),
        Index("ix_bt_generation_hash", "generation_hash"),
    )
```

### Status constants

```python
TASK_STATUSES = ("not_started", "blocked", "ready", "in_progress", "waiting_on_customer", "completed", "cancelled")

TASK_TYPES = (
    "verify_traveler_details",
    "verify_passport",
    "verify_visa",
    "verify_insurance",
    "confirm_flights",
    "confirm_hotels",
    "collect_payment_proof",
    "send_final_confirmation",
    "custom",
)

TASK_SOURCES = (
    "system_suggested",
    "agent_created",
    "readiness_generated",
    "document_generated",
    "extraction_generated",
)

TASK_PRIORITIES = ("low", "medium", "high", "critical")

BLOCKER_CODES = (
    "missing_booking_data",
    "missing_document",
    "missing_extraction",
    "extraction_not_reviewed",
    "document_not_accepted",
    "missing_passport_field",
    "missing_visa_field",
    "missing_insurance_field",
    "manual_block",
)
```

---

## Part 2: Task State Machine

```
                    ┌──────────────────┐
                    │   not_started    │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              v              v              v
        ┌──────────┐  ┌──────────┐  ┌────────────┐
        │ blocked  │  │  ready   │  │ cancelled  │
        └────┬─────┘  └────┬─────┘  └────────────┘
             │              │
             v              v
        ┌──────────┐  ┌──────────────┐
        │  ready   │  │ in_progress  │
        └──────────┘  └──────┬───────┘
                            │
                  ┌─────────┼─────────┐
                  v         v         v
           ┌──────────┐ ┌──────────┐ ┌──────────┐
           │completed │ │ waiting  │ │ cancelled│
           │          │ │ _on_cust │ │          │
           └──────────┘ └────┬─────┘ └──────────┘
                             │
                             v
                       ┌──────────┐
                       │in_progress│
                       └──────────┘
```

### Transition rules (backend-enforced)

The service layer validates every status transition. Invalid transitions raise 409.

```python
VALID_TRANSITIONS: dict[str, set[str]] = {
    "not_started": {"ready", "blocked", "cancelled"},
    "blocked": {"ready", "cancelled"},
    "ready": {"in_progress", "blocked", "cancelled"},
    "in_progress": {"completed", "waiting_on_customer", "cancelled"},
    "waiting_on_customer": {"in_progress", "cancelled"},
    "completed": set(),  # terminal
    "cancelled": set(),  # terminal (only reopened via force regeneration)
}
```

Rules:

| From | To | Trigger | Enforced by |
|:-----|:---|:--------|:------------|
| not_started | ready | Agent marks ready or reconciliation unblocks | update_task |
| not_started | blocked | Reconciliation detects missing dependency | generate endpoint |
| blocked | ready | Reconciliation resolves blocker | generate endpoint |
| ready | in_progress | Agent starts work | update_task |
| ready | blocked | Reconciliation detects new blocker | generate endpoint |
| in_progress | completed | Agent marks complete | complete endpoint |
| in_progress | waiting_on_customer | Agent marks waiting | update_task |
| in_progress | cancelled | Agent cancels | cancel endpoint |
| waiting_on_customer | in_progress | Agent resumes | update_task |
| any non-terminal | cancelled | Agent cancels | cancel endpoint |
| completed | (none) | Terminal, no transitions | service raises 409 |
| cancelled | (none) | Terminal, only recreated via force regeneration | service raises 409 |

Terminal states: `completed`, `cancelled`. No automatic reopening. Completion is allowed manually on any non-blocked task. Blocked tasks must be unblocked or reconciled first (no force-complete in Phase 5A).

---

## Part 3: Task Generation Rules

### Generation trigger

Explicit only. POST endpoint with idempotency:

```
POST /trips/{trip_id}/booking-tasks/generate
```

No automatic generation. Agent clicks "Generate execution checklist" in OpsPanel.

### Generation logic

```python
async def generate_booking_tasks(db, trip_id: str, agency_id: str, generated_by: str, force: bool = False) -> list[BookingTask]:
    """
    Generate booking tasks from current trip state.

    Rules:
    1. For each traveler, check required documents and fields.
    2. For each required document type, check if accepted document exists.
    3. For each accepted document, check if extraction exists and is reviewed.
    4. Create tasks for missing items.
    5. Skip if active task with same generation_hash exists.
    6. Reconcile blocker state for all active system-generated tasks.
    """
```

### Generation steps

1. **Fetch trip state**: booking_data, documents, extractions, readiness.
2. **Generate tasks per traveler**:
   - `verify_traveler_details` — if any traveler missing full_name or date_of_birth.
   - `verify_passport` — if any traveler missing passport_number or passport_expiry, or no accepted passport document, or passport extraction not reviewed.
   - `verify_visa` — if destination requires visa and no accepted visa document.
   - `verify_insurance` — if no accepted insurance document.
3. **Generate booking-level tasks**:
   - `confirm_flights` — always suggested when trip has booking_data (no flight verification API yet).
   - `confirm_hotels` — always suggested when trip has booking_data.
   - `collect_payment_proof` — always suggested when trip has booking_data.
   - `send_final_confirmation` — always suggested, blocked until all other tasks completed.
4. **Compute generation_hash per task**: SHA-256 of `agency_id + trip_id + source + task_type + traveler_id + normalized blocker_ref keys`.
5. **Check idempotency**: skip if active (not completed/cancelled) task with same `generation_hash` exists.
6. **Set blockers**: if dependency data is missing, set `status=blocked` with `blocker_code` and `blocker_refs`.

### Idempotency strategy

- Each generated task gets a `generation_hash` = hash of `agency_id + trip_id + source + task_type + traveler_id + normalized blocker_ref keys`.
- Before creating: query for existing active tasks with same `generation_hash`.
- If found, skip creation.
- Cancelled tasks are NOT recreated unless `force=true`.
- Completed tasks are never reopened automatically.

### Task reconciliation

Booking state changes after tasks are generated. The generate endpoint performs both creation AND reconciliation on every call.

```python
async def generate_booking_tasks(db, trip_id, agency_id, generated_by, force=False):
    """
    Two-phase operation:
    Phase 1: Create missing suggested tasks (idempotent).
    Phase 2: Reconcile blocker state for all active system-generated tasks.
    """
```

**Reconciliation rules:**

| Current task status | Condition | Reconciliation action |
|:--------------------|:----------|:----------------------|
| blocked | All blockers resolved (data now present) | Move to `ready`, clear `blocker_code` and `blocker_refs` |
| ready | New blocker detected (data removed or new gap found) | Move to `blocked`, set `blocker_code` and `blocker_refs` |
| not_started | New blocker detected | Move to `blocked`, set `blocker_code` and `blocker_refs` |
| not_started | No blockers | Move to `ready` |
| in_progress | Any blocker change | Do NOT auto-downgrade. Task is being actively worked. |
| waiting_on_customer | Any blocker change | Do NOT auto-change. Agent must explicitly reconcile. |
| completed | Any | Never modify. Terminal state. |
| cancelled | Any | Never modify. Only recreated via force=true. |

**Key constraint:** Reconciliation only applies to system-generated tasks (source != "agent_created"). Custom tasks are never auto-modified.

**Why reconciliation matters:** Without it, a task blocked on "missing passport extraction" stays blocked even after the agent accepts the OCR extraction. The next generate call detects the extraction now exists and moves the task to ready.

### Blocker reference format

Blocker refs use structured keys pointing to state, never PII values:

```json
// Good: references to state
{
  "traveler_id": "tv-123",
  "field": "passport_number",
  "document_type": "passport"
}

{
  "document_type": "visa",
  "reason": "no_accepted_document"
}

{
  "extraction_id": "ext-456",
  "reason": "not_reviewed"
}
```

Blocker refs never contain: passport numbers, DOB, traveler names, document filenames, extracted field values.

---

## Part 4: API Endpoints

### List tasks

```
GET /trips/{trip_id}/booking-tasks
```

Response:
```json
{
  "trip_id": "...",
  "tasks": [
    {
      "id": "...",
      "task_type": "verify_passport",
      "title": "Verify passport for Traveler 1",
      "description": null,
      "status": "blocked",
      "priority": "high",
      "owner_id": null,
      "due_at": null,
      "blocker_code": "missing_document",
      "blocker_refs": {"traveler_id": "tv-1", "document_type": "passport"},
      "source": "readiness_generated",
      "created_by": "...",
      "completed_by": null,
      "completed_at": null,
      "cancelled_at": null,
      "created_at": "...",
      "updated_at": "..."
    }
  ],
  "summary": {
    "total": 8,
    "blocked": 2,
    "ready": 1,
    "in_progress": 1,
    "waiting_on_customer": 0,
    "completed": 3,
    "cancelled": 1
  }
}
```

### Create task

```
POST /trips/{trip_id}/booking-tasks
```

Body:
```json
{
  "task_type": "custom",
  "title": "Call hotel to confirm late checkout",
  "description": "Guest requested late checkout",
  "priority": "medium",
  "owner_id": null,
  "due_at": null
}
```

### Generate tasks (also reconciles)

```
POST /trips/{trip_id}/booking-tasks/generate
```

Body (optional):
```json
{
  "force": false
}
```

This endpoint performs two phases:
1. **Create missing tasks** — idempotent generation from current trip state.
2. **Reconcile active system tasks** — recompute blocker state for all active system-generated tasks.

Response:
```json
{
  "created": [...],
  "skipped": ["task-id-1", "task-id-2"],
  "reconciled": [
    {"task_id": "...", "old_status": "blocked", "new_status": "ready"},
    {"task_id": "...", "old_status": "ready", "new_status": "blocked"}
  ]
}
```

### Update task

```
PATCH /trips/{trip_id}/booking-tasks/{task_id}
```

Body (partial):
```json
{
  "title": "Updated title",
  "priority": "high",
  "owner_id": "agent-1",
  "due_at": "2026-05-15T17:00:00Z",
  "status": "in_progress"
}
```

Status transitions validated against state machine rules.

### Complete task

```
POST /trips/{trip_id}/booking-tasks/{task_id}/complete
```

Sets `status=completed`, `completed_by=current_user`, `completed_at=now`.

### Cancel task

```
POST /trips/{trip_id}/booking-tasks/{task_id}/cancel
```

Sets `status=cancelled`, `cancelled_at=now`.

---

## Part 5: Task Generation from Readiness

The generation function inspects current trip state and creates tasks for each gap:

### Mapping: readiness gap -> task

| Readiness signal | Task type | Blocker code |
|:-----------------|:----------|:-------------|
| Traveler missing full_name or dob | `verify_traveler_details` | `missing_booking_data` |
| Traveler missing passport fields | `verify_passport` | `missing_passport_field` |
| No accepted passport document for traveler | `verify_passport` | `missing_document` |
| Passport extraction not reviewed | `verify_passport` | `extraction_not_reviewed` |
| Destination requires visa, no accepted doc | `verify_visa` | `missing_document` |
| No accepted insurance document | `verify_insurance` | `missing_document` |
| Has booking_data, flights unconfirmed | `confirm_flights` | null (ready) |
| Has booking_data, hotels unconfirmed | `confirm_hotels` | null (ready) |
| Has booking_data, no payment proof | `collect_payment_proof` | null (ready) |
| All other tasks completed | `send_final_confirmation` | `missing_booking_data` (blocked until others done) |

### Per-traveler task fan-out

For `verify_passport`, `verify_visa`, `verify_insurance`, `verify_traveler_details`: one task per traveler in booking_data. Title uses traveler ordinal: "Verify passport for Traveler 1".

### Safe title/description policy

System-generated task titles are template-only and contain no PII:

```python
TASK_TITLE_TEMPLATES = {
    "verify_traveler_details": "Verify traveler details for Traveler {ordinal}",
    "verify_passport": "Verify passport for Traveler {ordinal}",
    "verify_visa": "Verify visa for Traveler {ordinal}",
    "verify_insurance": "Verify insurance for Traveler {ordinal}",
    "confirm_flights": "Confirm flights",
    "confirm_hotels": "Confirm hotels",
    "collect_payment_proof": "Collect payment proof",
    "send_final_confirmation": "Send final confirmation",
}
```

Rules:
- System tasks: title generated from template + ordinal. Description is null.
- Custom tasks: title is free-text entered by agent. Treated as private agent text.
- Audit logs never include raw title or description. Only `title_present: bool` if needed.
- No free-text description for system tasks in Phase 5A.

### Generation hash computation

```python
def _generation_hash(agency_id: str, trip_id: str, task_type: str, source: str,
                     traveler_id: str | None, blocker_refs: dict | None) -> str:
    parts = [agency_id, trip_id, task_type, source]
    if traveler_id:
        parts.append(f"tv:{traveler_id}")
    if blocker_refs:
        for k in sorted(blocker_refs.keys()):
            parts.append(f"{k}:{blocker_refs[k]}")
    return hashlib.sha256(":".join(parts).encode()).hexdigest()[:32]
```

Hash scope includes agency_id + trip_id + source to prevent cross-trip collisions and support future multi-tenant migrations safely.

---

## Part 6: Service Layer

### File: `spine_api/services/booking_task_service.py`

```python
async def generate_tasks(db, trip_id, agency_id, generated_by, force=False) -> GenerateResult
async def _reconcile_active_tasks(db, trip_id, agency_id) -> list[ReconciliationResult]
async def list_tasks(db, trip_id, agency_id) -> TaskListResult
async def create_task(db, trip_id, agency_id, created_by, data) -> BookingTask
async def update_task(db, task_id, agency_id, data) -> BookingTask
async def complete_task(db, task_id, agency_id, completed_by) -> BookingTask
async def cancel_task(db, task_id, agency_id) -> BookingTask
```

### Endpoint integration

Add to `spine_api/server.py` following existing patterns (session_client auth, agency scoping, Pydantic models for request/response).

---

## Part 7: Migration

### File: `alembic/versions/add_booking_tasks.py`

```python
down_revision = 'add_extraction_attempts_and_pdf'  # Phase 4E migration

def upgrade():
    if not _has_table("booking_tasks"):
        op.create_table(
            "booking_tasks",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("trip_id", sa.String(36), nullable=False),
            sa.Column("agency_id", sa.String(36), sa.ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False),
            sa.Column("task_type", sa.String(40), nullable=False),
            sa.Column("title", sa.String(200), nullable=False),
            sa.Column("description", sa.String(500), nullable=True),
            sa.Column("status", sa.String(20), nullable=False, server_default="not_started"),
            sa.Column("priority", sa.String(20), nullable=False, server_default="medium"),
            sa.Column("owner_id", sa.String(36), nullable=True),
            sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("blocker_code", sa.String(40), nullable=True),
            sa.Column("blocker_refs", sa.JSON, nullable=True),
            sa.Column("source", sa.String(30), nullable=False, server_default="agent_created"),
            sa.Column("generation_hash", sa.String(64), nullable=True),
            sa.Column("created_by", sa.String(36), nullable=False),
            sa.Column("completed_by", sa.String(36), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_bt_trip_id", "booking_tasks", ["trip_id"])
        op.create_index("ix_bt_agency_id", "booking_tasks", ["agency_id"])
        op.create_index("ix_bt_status", "booking_tasks", ["status"])
        op.create_index("ix_bt_task_type", "booking_tasks", ["task_type"])
        op.create_index("ix_bt_trip_status", "booking_tasks", ["trip_id", "status"])
        op.create_index("ix_bt_generation_hash", "booking_tasks", ["generation_hash"])
```

No backfill — this is a new table with no pre-existing data to migrate.

---

## Part 8: Frontend API Types

### File: `frontend/src/lib/api-client.ts`

```typescript
export interface BookingTask {
  id: string;
  task_type: string;
  title: string;
  description: string | null;
  status: 'not_started' | 'blocked' | 'ready' | 'in_progress' | 'waiting_on_customer' | 'completed' | 'cancelled';
  priority: 'low' | 'medium' | 'high' | 'critical';
  owner_id: string | null;
  due_at: string | null;
  blocker_code: string | null;
  blocker_refs: Record<string, string> | null;
  source: string;
  created_by: string;
  completed_by: string | null;
  completed_at: string | null;
  cancelled_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface BookingTaskListResponse {
  trip_id: string;
  tasks: BookingTask[];
  summary: {
    total: number;
    blocked: number;
    ready: number;
    in_progress: number;
    waiting_on_customer: number;
    completed: number;
    cancelled: number;
  };
}

export async function getBookingTasks(tripId: string): Promise<BookingTaskListResponse>
export async function createBookingTask(tripId: string, data: CreateBookingTaskRequest): Promise<BookingTask>
export async function generateBookingTasks(tripId: string, force?: boolean): Promise<{ created: BookingTask[], skipped: string[] }>
export async function updateBookingTask(tripId: string, taskId: string, data: Partial<BookingTask>): Promise<BookingTask>
export async function completeBookingTask(tripId: string, taskId: string): Promise<BookingTask>
export async function cancelBookingTask(tripId: string, taskId: string): Promise<BookingTask>
```

---

## Part 9: OpsPanel Booking Execution Section

### Placement

After the Documents section (after line ~1125 in current OpsPanel.tsx), before the closing div.

### Component: `BookingExecutionPanel.tsx`

```
┌─────────────────────────────────────────────────────┐
│ Booking Execution                    [Generate] [+] │
│ 8 tasks · 2 blocked · 1 ready · 3 completed        │
├─────────────────────────────────────────────────────┤
│                                                      │
│ BLOCKED (2)                                          │
│ ├─ Verify passport for Traveler 1                   │
│ │  missing_document · passport · high priority      │
│ │                                                    │
│ └─ Verify passport for Traveler 2                   │
│    missing_document · passport · high priority      │
│                                                      │
│ READY (1)                                            │
│ └─ Confirm flights                                  │
│    no owner · medium priority                       │
│                                                      │
│ IN PROGRESS (1)                                      │
│ └─ Verify insurance                                 │
│    owner: agent-1 · due: May 15                     │
│                                                      │
│ COMPLETED (3)                                        │
│ ├─ Verify traveler details          completed May 9│
│ ├─ Confirm hotels                   completed May 9│
│ └─ Collect payment proof            completed May 9│
│                                                      │
│ CANCELLED (1)                                        │
│ └─ Send final confirmation          cancelled May 9│
└─────────────────────────────────────────────────────┘
```

### Props

```typescript
interface BookingExecutionPanelProps {
  tripId: string;
  tripStage?: string;
}
```

### Behavior

- Fetches tasks on mount via `getBookingTasks(tripId)`.
- "Generate" button calls `generateBookingTasks(tripId)` and refreshes list.
- "Generate" button disabled when `tripStage` is not `proposal` or `booking`.
- "+" button opens a simple form for custom task creation.
- Each task row shows: title, status, blocker_code (not refs), priority, owner, due date.
- Blocked tasks show `blocker_code` text, not blocker_refs values.
- Task actions: Start (-> in_progress), Complete, Cancel, Waiting on customer.
- Completed/cancelled sections collapsed by default.
- Summary counts shown in header.

### Styling

- Follow existing panel patterns from `ExtractionHistoryPanel.tsx` and `ChangeHistoryPanel.tsx`.
- Status badge colors: blocked=red, ready=blue, in_progress=amber, waiting_on_customer=purple, completed=green, cancelled=gray.
- Priority badges: low=gray, medium=default, high=amber, critical=red.

---

## Part 10: Audit Events

### Event shapes

```python
BOOKING_TASK_EVENTS = {
    "booking_task_generated": {
        "task_id": str,
        "task_type": str,
        "source": str,
        "generation_hash": str,
    },
    "booking_task_created": {
        "task_id": str,
        "task_type": str,
        "source": str,
    },
    "booking_task_updated": {
        "task_id": str,
        "task_type": str,
        "changes": list[str],  # e.g. ["priority", "owner_id"]
    },
    "booking_task_assigned": {
        "task_id": str,
        "task_type": str,
        "owner_id": str,
    },
    "booking_task_completed": {
        "task_id": str,
        "task_type": str,
        "completed_by": str,
    },
    "booking_task_cancelled": {
        "task_id": str,
        "task_type": str,
    },
    "booking_task_blocked": {
        "task_id": str,
        "task_type": str,
        "blocker_code": str,
        "blocker_ref_count": int,  # count only, not refs themselves
    },
    "booking_task_unblocked": {
        "task_id": str,
        "task_type": str,
    },
}
```

### Audit policy

Audit fields allowed:
- `trip_id`, `task_id`, `task_type`, `status`, `priority`, `owner_id`
- `blocker_code`, `blocker_ref_count` (count, not contents)
- `source`, `generation_hash`

Forbidden:
- passport number, DOB, traveler name, document filename
- extracted field values, `blocker_refs` contents
- raw `title` or `description` text (audit `title_present: bool` if needed)
- free-text notes (no notes field in Phase 5A)

---

## Part 11: Privacy Boundaries

| Surface | PII? | Notes |
|:--------|:-----|:------|
| Task list API response | No | task_type, template title, status, blocker_code, refs (IDs only) |
| Task title (system) | No | Template-generated: "Verify passport for Traveler 1" |
| Task title (custom) | Yes (private) | Agent-entered free text, treated as private. Not in audit logs. |
| Task description | No | Null for system tasks. Agent text for custom, same as title policy. |
| Task generation logic | Reads PII internally | Reads booking_data to detect gaps, but never stores PII in task rows |
| Blocker refs | No | Structured keys: traveler_id, document_type, field name. No values. |
| Reconciliation | Reads PII internally | Re-checks booking_data state to resolve blockers. No PII stored. |
| Audit events | No | Metadata only: IDs, types, counts. Never title/description text. |
| OpsPanel task display | No | Shows title, status, blocker_code, priority, owner |

---

## Part 12: Test Plan

### Backend tests

1. **generate_tasks from incomplete booking_data** — travelers missing passport fields -> verify_passport tasks created with blocked status.
2. **generation is idempotent** — calling generate twice with same state creates no duplicate tasks.
3. **completed tasks not reopened** — completing a task then generating again does not create a new task for same gap.
4. **cancelled tasks not recreated** — cancelling then generating without force=true skips that task.
5. **cancelled tasks recreated with force** — force=true recreates cancelled tasks.
6. **task blockers contain refs, not PII** — blocker_refs has traveler_id and document_type, never passport_number value.
7. **audit logs metadata only** — audit event for task completion has task_id and task_type, no traveler data, no title/description text.
8. **trip GET excludes tasks** — GET /trips/{id} does not include booking_tasks; must use dedicated endpoint.
9. **status transitions valid** — cannot go from completed to in_progress; cannot go from cancelled to ready; 409 on invalid transition.
10. **per-traveler fan-out** — 3 travelers -> 3 verify_passport tasks if all missing.
11. **generation_hash uniqueness** — same task_type + same traveler_id + same blocker_refs = same hash.
12. **reconciliation: resolved blocker moves blocked to ready** — generate after agent applies extraction moves blocked verify_passport task to ready.
13. **reconciliation: completed task not reopened when blocker reappears** — completed task stays completed even if dependency regresses.
14. **reconciliation: in_progress task not auto-downgraded** — task stays in_progress even if new blocker detected.
15. **reconciliation: custom tasks never auto-modified** — agent_created tasks keep their status regardless of state changes.
16. **system task title contains no PII** — title is template-generated ("Verify passport for Traveler 1"), never contains name/DOB/passport.
17. **audit does not log title/description/blocker values** — audit event has task_id, task_type, blocker_ref_count but not blocker_refs contents or title text.
18. **blocked task cannot be completed** — complete endpoint returns 409 when status is blocked. Must reconcile or manually unblock first.

### Frontend tests

1. **Booking Execution section renders tasks** — panel shows tasks grouped by status.
2. **Generate checklist calls API and refreshes** — clicking Generate calls generateBookingTasks, then getBookingTasks.
3. **Generate disabled outside proposal/booking** — button disabled when stage is discovery or shortlist.
4. **Blocked tasks show blocker code, not PII** — displays "missing_document" text, not document contents or traveler name.
5. **Complete/cancel actions update UI** — clicking Complete calls API, refreshes list, task moves to completed section.
6. **Reconciliation feedback visible** — after Generate, blocked task that moved to ready is updated in UI without full page reload.

---

## Part 13: Non-Goals

- Payments integration or payment gateway
- Supplier booking APIs (airline, hotel GDS)
- Email or WhatsApp notification/sending
- Calendar reminders or scheduling
- Customer portal task view
- Automatic task completion (system never marks tasks completed)
- Drag-and-drop task reordering
- Task dependencies or subtasks
- Task templates beyond the built-in types
- Task comments or notes (encrypted or otherwise)
- Multi-trip task aggregation

---

## Implementation Order

1. DB model (`spine_api/models/tenant.py` — add `BookingTask`)
2. Migration (`alembic/versions/add_booking_tasks.py`)
3. Service layer (`spine_api/services/booking_task_service.py` — CRUD + generation + reconciliation)
4. API endpoints (`spine_api/server.py` — add 6 endpoints)
5. Frontend types (`frontend/src/lib/api-client.ts`)
6. BookingExecutionPanel component
7. OpsPanel integration
8. Backend tests (18 tests)
9. Frontend tests (6 tests)

---

## Dependencies

- Phase 4F closed (it is — 2026-05-08)
- Existing readiness computation (`src/intake/readiness.py`)
- Existing booking_data structure
- Existing document/extraction tables for blocker detection
- Alembic migration chain follows `add_extraction_attempts_and_pdf`

---

## Files Changed

| File | Action | Notes |
|:-----|:-------|:------|
| `spine_api/models/tenant.py` | Update | Add BookingTask model |
| `alembic/versions/add_booking_tasks.py` | New | Create table with indexes |
| `spine_api/services/booking_task_service.py` | New | Task CRUD + generation |
| `spine_api/server.py` | Update | Add 6 API endpoints |
| `frontend/src/lib/api-client.ts` | Update | Add BookingTask types + 6 API functions |
| `frontend/src/components/workspace/panels/BookingExecutionPanel.tsx` | New | Task list UI |
| `frontend/src/app/(agency)/workbench/OpsPanel.tsx` | Update | Add BookingExecutionPanel section |
| `tests/test_booking_tasks.py` | New | Backend tests (18 tests) |
| `frontend/src/components/workspace/panels/__tests__/BookingExecutionPanel.test.tsx` | New | Frontend tests (6 tests) |
