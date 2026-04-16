# Workspace Routing Feature — Design

**Feature Name:** workspace-routing  
**Version:** 1.0.0  
**Date:** 2026-04-16  
**Status:** Design Phase

---

## 1. High-Level Architecture

### 1.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Workspace Shell                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    Trip Context Store (Zustand)           │  │
│  │  - currentTripId                                          │  │
│  │  - spineResult                                            │  │
│  │  - isLoading                                              │  │
│  │  - error                                                  │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    Tab Navigation                          │  │
│  │  - /intake  /packet  /decision  /strategy  /safety  /output│  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    Content Area                            │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │  Reusable Tab Components (from workbench/)          │  │  │
│  │  │  - IntakeTab  PacketTab  DecisionTab               │  │  │
│  │  │  - StrategyTab  SafetyTab  OutputTab               │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Data Flow

```
Inbox Card Click
       │
       ▼
  /workspace/[tripId]/intake
       │
       ▼
Load Trip Context (Zustand)
       │
       ├─► Check cache
       │   ├─ Hit → Use cached spineResult
       │   └─ Miss → Call /api/spine/run
       │
       ▼
Render Tab Component
       │
       ▼
Display Trip Data
```

### 1.3 Route Structure

```
/workspace/[tripId]/
├── layout.tsx        # Workspace shell with embedded tab navigation
├── page.tsx          # Default tab (intake) - renders IntakeTab
├── intake/page.tsx   # Intake tab
├── packet/page.tsx   # Packet tab
├── decision/page.tsx # Decision tab
├── strategy/page.tsx # Strategy tab
├── safety/page.tsx   # Safety tab
└── output/page.tsx   # Output tab
```

**Architecture Decision:**
- `layout.tsx` is the workspace shell containing tab navigation
- `page.tsx` is the default tab content (intake view)
- This separates navigation from content, following Next.js App Router conventions

---

## 2. Component Architecture

### 2.1 Workspace Shell (`/workspace/[tripId]/page.tsx`)

**Purpose:** Main layout container for trip workspace

**Props:**
- `params`: `{ tripId: string }`

**State:**
- `tripId`: From URL params
- `spineResult`: Cached from Zustand store
- `isLoading`: Loading state
- `error`: Error state

**Behavior:**
1. Extract `tripId` from URL params
2. Load trip context from Zustand store
3. If no cached data, trigger spine execution
4. Render tab navigation + content area

**Key Patterns:**
- Client component (needs interactivity)
- Uses `useParams` for trip ID
- Uses Zustand for state management

### 2.2 Tab Navigation (`/workspace/[tripId]/layout.tsx`)

**Purpose:** Provide tab navigation between workspace views

**Props:**
- `children`: Tab content

**Navigation Links:**
- `/workspace/[tripId]/intake`
- `/workspace/[tripId]/packet`
- `/workspace/[tripId]/decision`
- `/workspace/[tripId]/strategy`
- `/workspace/[tripId]/safety`
- `/workspace/[tripId]/output`

**Active State:**
- Uses `usePathname` to determine active tab
- Highlights current tab in navigation

### 2.3 Workspace Tab Components

**Location:** `frontend/src/app/workspace/[tripId]/`

**Components to Create (NEW - NOT reused from workbench):**
- `DisplayIntakeTab.tsx` - Display intake data from spineResult
- `DisplayPacketTab.tsx` - Display packet data from spineResult
- `DisplayDecisionTab.tsx` - Display decision data from spineResult
- `DisplayStrategyTab.tsx` - Display strategy data from spineResult
- `DisplaySafetyTab.tsx` - Display safety analysis from spineResult
- `DisplayOutputTab.tsx` - Display final output from spineResult

**Why New Components (Not Reuse):**
- Workbench `IntakeTab.tsx` is an INPUT form with trip selector, textareas, dropdowns
- Workspace tabs need to DISPLAY data from `spineResult` prop
- These are fundamentally different interfaces that cannot be reused
- Creating new components ensures clear separation of concerns

**Component Interface:**
```typescript
interface DisplayTabProps {
  spineResult: SpineResult;
  tripId: string;
}
```

---

## 3. State Management

### 3.1 Zustand Store (`frontend/src/lib/workspaceStore.ts`)

```typescript
interface WorkspaceState {
  currentTripId: string | null;
  spineResults: Record<string, SpineResult>;
  isLoading: boolean;
  error: string | null;
}

interface WorkspaceActions {
  setTripId: (tripId: string) => void;
  loadSpineResult: (tripId: string) => Promise<void>;
  getCachedResult: (tripId: string) => SpineResult | undefined;
  clearTrip: () => void;
}
```

### 3.2 State Operations

**setTripId(tripId):**
- Set current trip ID
- Load cached spine result if available
- Trigger spine execution if not cached

**loadSpineResult(tripId):**
- Call `/api/spine/run` with trip data
- Cache result in store
- Update loading state

**getCachedResult(tripId):**
- Return cached spine result
- Return undefined if not cached

**clearTrip():**
- Clear current trip ID
- Clear cached result

---

## 4. API Integration

### 4.1 Spine API Call

**Endpoint:** `/api/spine/run`

**Method:** POST

**Request Body:**
```json
{
  "tripId": "string",
  "envelopes": [
    {
      "content": "string",
      "content_type": "freeform_text",
      "source": "agency_notes",
      "actor": "agent"
    }
  ],
  "stage": "discovery",
  "operating_mode": "normal_intake"
}
```

**Response:** `SpineResult` (same as current workbench)

### 4.2 Trip Data Source

**Option A:** Extract from inbox trip card data
- Trip ID from card
- Raw notes from card metadata

**Option B:** Fetch trip details from API
- Call `/api/trips/[tripId]` to get trip details
- Use stored raw notes for spine execution

---

## 5. Navigation Strategy

### 5.1 Inbox to Workspace

**Current:** Click trip card → `/workbench`

**New:** Click trip card → `/workspace/[tripId]/intake`

**Implementation:**
- Update inbox trip card component
- Change link from `/workbench` to `/workspace/[tripId]/intake`
- Pass trip ID as URL parameter

### 5.2 Tab Navigation

**Pattern:** Next.js Link component

```tsx
<Link href={`/workspace/${tripId}/packet`}>
  <button>Packet</button>
</Link>
```

**Active State:**
- Use `usePathname()` to get current path
- Compare with tab path
- Apply active class if match

### 5.3 Browser History

**Behavior:** Native Next.js routing
- Back/forward works automatically
- URL updates on navigation
- Page refresh preserves trip context

---

## 6. Error Handling

### 6.1 Spine Execution Failure

**Scenario:** API call to `/api/spine/run` fails

**Response:**
- Show error message in workspace
- Allow retry button
- Show error details in console

**UI Pattern:**
```
┌─────────────────────────────────────┐
│  Error Loading Trip Data           │
│                                     │
│  Failed to load trip [tripId]      │
│  [Retry] [View Error Details]      │
└─────────────────────────────────────┘
```

### 6.2 Missing Trip Data

**Scenario:** Trip ID doesn't exist or has no data

**Response:**
- Show 404 or "Trip not found" message
- Link back to inbox

### 6.3 Navigation Error

**Scenario:** Invalid trip ID in URL

**Response:**
- Redirect to inbox
- Show error notification

---

## 7. Testing Strategy

### 7.1 Unit Tests

**Components:**
- Workspace shell renders correctly
- Tab navigation works
- Error states display properly

**Store:**
- State updates work correctly
- Cache operations function as expected

### 7.2 Integration Tests

**Workflows:**
- Navigate from inbox to workspace
- Switch between tabs
- Refresh page preserves context
- Browser back/forward works

**API:**
- Spine API called with correct params
- Cached results used when available
- Error handling works

### 7.3 E2E Tests

**Full Flow:**
- Click inbox card → workspace loads
- All tabs display data correctly
- Run Spine refreshes data
- Navigation history works

---

## 8. Performance Considerations

### 8.1 Caching Strategy

**Cache Locations:**
1. Zustand store (in-memory, session-scoped)
2. sessionStorage (persists across tab refreshes)
3. Browser cache (optional, for static assets)

**Cache Key Format:** `workspace:spine:${tripId}`

**Cache Invalidation:**
- On "Run Spine" button click
- On explicit cache clear button
- On session timeout (30 minutes of inactivity)
- On tab close (sessionStorage auto-clears)

**Session Timeout:**
- Value: 30 minutes of inactivity
- Action: Clear sessionStorage cache
- Trigger: Check on workspace route access

**Explicit Clear Triggers:**
- "Run Spine" button click
- "Clear Cache" button in workspace settings
- Tab close (sessionStorage auto-clears)

### 8.2 Loading States

**Phases:**
1. **Initial Load:** Show skeleton or spinner
2. **Data Fetch:** Show loading indicator
3. **Error:** Show error state
4. **Success:** Show data

**Optimistic UI:**
- Show cached data immediately
- Update when fresh data arrives

---

## 9. Security Considerations

### 9.1 Trip ID Validation

**Checks:**
- Validate trip ID format (UUID or alphanumeric)
- Check user has access to trip
- Sanitize trip ID before use

### 9.2 Trip Access Control

**Access Validation:**
- API call to `/api/trips/[tripId]/access` to validate user ownership
- JWT claims checked for agency membership
- Workspace route checks ownership before loading data

**Unauthorized Access:**
- If user navigates to another user's trip: redirect to `/inbox` with error notification
- If user lacks permission: show 403 Forbidden page
- All workspace routes validate access before rendering content

**Security Flow:**
```
/workspace/[tripId]
    │
    ├─► Validate trip ID format
    ├─► Check user access via API
    │   ├─ OK → Load trip data
    │   └─ FAIL → Redirect to /inbox
    │
    ▼
Render workspace content

---

## 10. Future Enhancements

### 10.1 Phase 2 Features

**Priority 1:**
- Trip search and filtering
- Bulk trip operations
- Trip comparison view

**Priority 2:**
- Real-time updates via WebSocket
- Collaborative editing
- Comment threads on trips

### 10.2 Phase 3 Features

**Priority 1:**
- Advanced analytics
- Predictive recommendations
- Automated workflows

---

## Appendix

### A. File Structure

```
frontend/src/app/workspace/
├── [tripId]/
│   ├── page.tsx              # Workspace shell
│   ├── layout.tsx            # Tab navigation
│   ├── intake/
│   │   └── page.tsx          # Intake tab
│   ├── packet/
│   │   └── page.tsx          # Packet tab
│   ├── decision/
│   │   └── page.tsx          # Decision tab
│   ├── strategy/
│   │   └── page.tsx          # Strategy tab
│   ├── safety/
│   │   └── page.tsx          # Safety tab
│   └── output/
│       └── page.tsx          # Output tab
└── lib/
    └── workspaceStore.ts     # Zustand store
```

### B. Type Definitions

**WorkspaceRouteParams:**
```typescript
interface WorkspaceRouteParams {
  tripId: string;
}
```

**WorkspaceRouteProps:**
```typescript
interface WorkspaceRouteProps {
  params: WorkspaceRouteParams;
}
```

### C. API Contracts

**SpineRunRequest:**
```typescript
interface SpineRunRequest {
  tripId: string;
  envelopes: SourceEnvelope[];
  stage: string;
  operating_mode: string;
}
```

**SpineRunResponse:**
```typescript
interface SpineRunResponse {
  packet: CanonicalPacket;
  validation: PacketValidationReport;
  decision: DecisionResult;
  strategy: SessionStrategy;
  internal_bundle: PromptBundle;
  traveler_bundle: PromptBundle;
  sanitized_view: SanitizedPacketView;
  leakage_result: Record<string, any>;
  run_timestamp: string;
}
```
