# Inbox Architecture Refactor — Design Document

**Date:** 2026-05-04  
**Author:** Agent  
**Status:** Design Complete → Implementation Ready  
**Scope:** Full-stack refactor of `/inbox` data pipeline  

---

## 1. Problem Statement

The current Inbox implementation has a fundamental architecture flaw: **the frontend owns the filtering contract** despite the backend holding all the data. This inversion of architecture causes every layer to compensate:

| Layer | Current Behavior | Why It’s Wrong |
|-------|-------------------|----------------|
| **Backend** (`spine_api/server.py`) | Returns raw DB dicts. No typed contract. filterCounts are wrong (`at_risk` and `unassigned` return `total`). | Backend cannot count or filter by computed fields (SLA, priority, customer name). The DB schema has no `sla_status`, `priority`, `assigned_to`, `customer_name` columns. |
| **BFF** (`frontend/src/lib/bff-trip-adapters.ts`) | 509 lines of fragile JSON extraction per trip (`getNestedValue`, `extractedValue`, `transformSpineTripToInboxTrip`). | O(n) deserialization per trip. Breaks silently when nested JSON shape changes. Re-implements business logic (SLA computation, customer name extraction). |
| **Frontend** (`inbox/page.tsx`) | Client-side filtering for tabs (`at_risk`, `incomplete`, `unassigned`). Sort is faked. | Only filters the fetched page. Tab counts diverge from reality. No way to paginate accurately. |
| **Tests** (`TripCard.test.tsx`) | Asserts a removed "Assign" button. | UI was redesigned (v2 card with checkbox + View link) but tests were not updated. |

**Result:** The system is technically functional but architecturally broken. Every new feature requires working around this inversion.

---

## 2. First-Principles Architecture

### Core Insight

The Inbox is a **read model** — a specialized view over `trips`.

- The backend holds the canonical trip data.
- The Inbox view is a **projection**: computed fields (SLA, priority, flags, customer name) derived from source data.
- The projection should be **owned by the service layer**, not the UI layer.
- The API contract should return a **typed, self-contained `InboxTrip`** — the frontend should not need to understand internal JSON structures.

### Principles

1. **Single source of truth for Inbox:** The backend defines the Inbox schema. The frontend trusts it.
2. **Zero client-side filtering:** The frontend renders what the backend gives it. Filter/sort/page are server concerns.
3. **Thin BFF:** Pass-through proxy. No JSON extraction. No business logic.
4. **Computed fields are first-class:** If a field is needed for filtering/sorting/counting, it must be computable in the service layer.

---

## 3. Proposed Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│  CLIENT (Next.js App)                                                │
│  ┌──────────────┐  ┌──────────────┐                                   │
│  │ InboxPage    │──│ useInboxTrips│                                   │
│  │ (render only)│  │ (thin hook)  │                                   │
│  └──────────────┘  └──────┬───────┘                                   │
│                           │ fetch JSON                                │
│                           ▼                                           │
│  ┌──────────────┐        ┌──────────────────┐                         │
│  │ TripCard     │        │ BFF /api/inbox   │   THIN PASS-THROUGH    │
│  │ (display)    │        │ (just proxies)   │   No extraction        │
│  └──────────────┘        └──────┬───────────┘                         │
└────────────────────────────────│─────────────────────────────────────┘
                                 │ GET /inbox?page=N&limit=20&filter=at_risk
                                 │
┌────────────────────────────────▼─────────────────────────────────────┐
│  BACKEND (FastAPI)                                                   │
│  ┌────────────────────────┐  ┌──────────────────────────────────────┐  │
│  │ /inbox endpoint        │──│ InboxProjectionService             │  │
│  │ - parses query params  │  │ - computes InboxTrip fields         │  │
│  │ - calls projection     │  │ - filter/sort/search/paginate       │  │
│  │ - returns typed JSON   │  │ - produces accurate filterCounts    │  │
│  └────────────────────────┘  └──────────┬───────────────────────────┘  │
│                                         │                             │
│  ┌──────────────────────────────────────▼──────────────┐              │
│  │ TripStore.list_trips() / count_trips()             │              │
│  │ (SQLAlchemy, agency_id + status filters)         │              │
│  └─────────────────────────────────────────────────────┘              │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 4. Changes Required

### 4.1 Backend: New `InboxProjectionService` (`spine_api/services/inbox_projection.py`)

**Responsibility:** Compute `InboxTrip` fields; filter/sort/page/query/count over a dataset of trip dicts.

**Key Methods:**
- `project_all(trip_dicts: List[dict]) -> List[InboxTripView]` — compute derived fields for all trips in one pass.
- `filter(trips: List[InboxTripView], criteria: InboxFilter) -> List[InboxTripView]` — apply server-side filter.
- `sort(trips: List[InboxTripView], sort_key: str, direction: str) -> List[InboxTripView]` — server-side sort.
- `search(trips: List[InboxTripView], query: str) -> List[InboxTripView]` — fuzzy search on customer name, destination, reference.
- `paginate(trips: List[InboxTripView], page: int, limit: int) -> Tuple[List[InboxTripView], int, int, bool]` — return slice + total + offset + hasMore.
- `filter_counts(trips: List[InboxTripView]) -> FilterCounts` — accurate counts over the FULL unfiltered dataset.

**Why not DB columns?**  
The DB already indexes `status` and `agency_id`. Adding columns for `sla_status`, `priority`, `customer_name`, `assigned_to` would require a migration system we don't have, and these are derived fields. The correct approach for now: compute them in the service layer, filter/sort in Python over the FULL dataset. Later, if scale demands it, persist a materialized view or index computed columns. This is a **strategic postponement** — the architecture supports it.

**Why compute over the full dataset?**  
Because `filterCounts` must count ALL items, not just the current page. The full dataset for an agency is bounded (<10k trips). O(n) with n=10k is trivial. Scales to 100k with lazy loading.

### 4.2 Backend: Update `/inbox` Endpoint (`spine_api/server.py`)

**Current:**
```python
@app.get("/inbox", response_model=InboxResponse)
def get_inbox(page=1, limit=20, agency=...):
    items = TripStore.list_trips(status=..., limit=..., offset=...)
    total = TripStore.count_trips(status=..., agency_id=...)
    filter_counts = {"all": total, "at_risk": total, ...}  # WRONG
    return {"items": items, "total": total, "hasMore": ..., "filterCounts": filter_counts}
```

**New:**
```python
@app.get("/inbox", response_model=InboxResponse)
def get_inbox(page=1, limit=20, filter=None, sort='priority', dir='desc', q=None, agency=...):
    # 1. Fetch ALL inbox trips for the agency (bounded set)
    raw_trips = TripStore.list_trips(status=_INBOX_STATUSES, limit=5000, agency_id=agency.id)
    
    # 2. Project to InboxTripView (computed fields)
    project = InboxProjectionService()
    full_dataset = project.project_all(raw_trips, agency=agency)
    
    # 3. Filter by tab (if active filter is not 'all')
    filtered = project.apply_filter(full_dataset, filter_key=filter)
    
    # 4. Search (if q parameter)
    searched = project.apply_search(filtered, query=q)
    
    # 5. Sort
    sorted_trips = project.apply_sort(searched, sort_key=sort, direction=dir)
    
    # 6. Paginate
    page_items, total = project.paginate(sorted_trips, page=page, limit=limit)
    
    # 7. Counts from full dataset (not paginated subset)
    filter_counts = project.filter_counts(full_dataset)
    
    return {"items": page_items, "total": total, "hasMore": ..., "filterCounts": filter_counts}
```

**Key change:** Fetch all trips (bounded), project them, then filter/sort/page/count in memory. This is O(n) where n = inbox size. For agencies with <10k trips, this is instant (<50ms). The DB query remains a single indexed scan.

### 4.3 Backend: New Contract Types (`spine_api/contract.py`)

**Current:**
```python
class FilterCounts(BaseModel):
    all: int
    at_risk: int
    incomplete: int
    unassigned: int

class InboxResponse(BaseModel):
    items: List[Dict[str, Any]]   # ← UNTYPED
    total: int
    hasMore: bool
    filterCounts: FilterCounts
```

**New:**
```python
class InboxTripItem(BaseModel):
    id: str
    reference: str
    destination: str
    tripType: str
    partySize: int
    dateWindow: str
    value: int
    priority: str  # 'low' | 'medium' | 'high' | 'critical'
    priorityScore: int
    stage: str
    stageNumber: int
    assignedTo: Optional[str]
    assignedToName: Optional[str]
    submittedAt: str
    lastUpdated: str
    daysInCurrentStage: int
    slaStatus: str  # 'on_track' | 'at_risk' | 'breached'
    customerName: str
    flags: List[str]

class InboxResponse(BaseModel):
    items: List[InboxTripItem]   # ← TYPED. FastAPI enforces shape.
    total: int
    hasMore: bool
    filterCounts: FilterCounts
```

**Why typed?** FastAPI validates and serializes. The frontend contract is guaranteed. No silent field drift.

### 4.4 BFF: Thin Pass-Through (`frontend/src/app/api/inbox/route.ts`)

**Current:** 509 lines of JSON extraction in `bff-trip-adapters.ts`.

**New:**
```typescript
export async function GET(request: NextRequest) {
    const query = request.nextUrl.searchParams.toString();
    const url = `${SPINE_API_URL}/inbox?${query}`;
    const res = await fetch(url, bffFetchOptions(request, "GET"));
    if (!res.ok) throw ...;
    const data = await res.json();
    return bffJson(data);  // ← NO EXTRACTION. Straight pass-through.
}
```

**Result:** The BFF is 8 lines plus error handling.

### 4.5 Frontend: Zero Client-Side Logic (`inbox/page.tsx`)

**Remove:**
- Client-side filtering code (`tripMatchesFilter` style functions — already mostly removed, finish the job)
- Client-side sort code (already removed, backend drives it via `sort`/`dir` params)
- Client-side filter count computation (already removed, reads `filterCounts` from API → now correct)
- URL `filter` param must actually reach the backend as query param

**Keep:**
- UI state (selected trips, search input, sort dropdown open/close)
- URL sync (page, limit, sort, dir, q, filter ← all forwarded to backend)
- Pagination controls (render what backend says)

### 4.6 Frontend: Fix Tests (`TripCard.test.tsx`)

**Current:** Asserts a removed "Assign" button that was never wired.

**New:** Remove that test. Add test for checkbox selection (already exists, keep). Update to match v2 TripCard reality (accent bar, contextual SLA, flags, View link, checkbox).

---

## 5. Data Flow (After)

```
User → clicks "At Risk" tab
    → URL: ?filter=at_risk&page=1&limit=20
    → Frontend useInboxTrips calls /api/inbox?filter=at_risk&page=1&limit=20
    → BFF proxies to /inbox?filter=at_risk&page=1&limit=20
    → Backend: fetch ALL inbox trips → project all → filter at_risk → sort → page 1 → return
    ← Frontend receives: {items: [...], total: 4, hasMore: false, filterCounts: {all: 55, at_risk: 4, incomplete: 12, unassigned: 8}}
    → Frontend renders 4 TripCards. Filter bar shows correct counts.
```

**Before vs After:**
| Concern | Before | After |
|---------|--------|-------|
| filterCounts | Backend returns `total` for `at_risk` and `unassigned` | Backend computes accurate counts from projected data |
| Filtering | Client-side on fetched page (incomplete/buggy) | Server-side over full dataset (correct) |
| Sorting | Client-side faked | Server-side over full dataset |
| Search | Not implemented | Server-side fuzzy on customer, destination, reference |
| BFF complexity | ~509 lines of JSON extraction | ~20 lines of pass-through |
| Type safety | None (Dict[str,Any] everywhere) | Full (InboxTripItem in contract) |
| Testing | Fragile (tests broken by UI redesign) | Stable (backend contract guarantees shape) |

---

## 6. Verification Plan

1. **Unit tests:** InboxProjectionService handles filter/sort/search/paginate correctly. Edge cases: empty, single item, all filters return zero.
2. **Integration tests:** `/inbox` endpoint returns correct filtered items and counts with real DB data.
3. **Frontend tests:** TripCard.test.tsx passes (no Assign button assertion). useGovernance.test.tsx passes.
4. **Build:** No TypeScript errors.
5. **Runtime:** Browse to /inbox. Verify tab counts match displayed cards. Verify sort and paging work.
6. **Full suite:** All tests green.

---

## 7. Rollback

- The change is additive: new service + endpoint changes. No DB schema changes.
- If needed, revert `server.py` changes, keep old endpoint as `@app.get("/inbox")` — it already exists.
- The refactor is **non-destructive**: old BFF extraction code can be deleted after verification.

---

**Next Action:** Start implementing InboxProjectionService and updating endpoint.
