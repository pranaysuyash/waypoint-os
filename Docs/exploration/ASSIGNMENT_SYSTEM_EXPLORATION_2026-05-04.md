# Assignment System Exploration

**Date:** 2026-05-04  
**Status:** Exploration notes — not implemented  
**Context:** Raised during trip assignment implementation on 2026-05-04  

---

## 1. Draft ID Lifecycle

Inquiries arrive before trips exist. The system should assign a **draft ID** to the raw inquiry, which gets attached to the trip when it's created.

**Current state:** No draft ID system exists. Raw inquiries go through `POST /run` → spine processing → trip creation. There's no pre-trip entity.

**What would be needed:**
- A `DraftInquiry` table/model with: `id`, `raw_note`, `status`, `created_at`, `agency_id`
- A `draft_inquiry_id` FK on the `Trip` model
- API to create drafts, list drafts, convert draft to trip
- The inbox might show both trips and drafts

**Research needed:**
- How do inquiries arrive? (web form, email, API, internal creation)
- Should drafts be visible in the inbox alongside trips?
- What's the conversion trigger? (manual "process" button, auto on submit?)

## 2. Self-Assignment

Agents should be able to assign trips to themselves directly.

**Current state:** The `POST /inbox/assign` primitive accepts any `assignTo` user ID. Self-assignment is: the current user's ID is `assignTo`. The endpoint doesn't verify this yet.

**What would be needed:**
- The endpoint would need `get_current_user` dependency to compare
- The UI could have a "Take it" or "Assign to me" button that calls `assignTrips` with the current user's ID
- The BFF/auth layer would need to expose the current user's ID to the frontend

**Not blocking current implementation:** The primitive works; self-assignment is a UI wiredown.

## 3. Auto-Assignment Rules

Automatic assignment of inbox trips to agents based on rules.

### Possible rule types:

| Rule | Description | Implementation |
|------|-------------|----------------|
| **Random** | Distribute trips randomly among available agents | Weighted random selection from active agent list |
| **Round-robin** | Cycle through agents in order | Counter per agency, increment on each assign |
| **Skill-based** | Match trip type/region to agent specialization | Trip metadata → agent skill matrix matching |
| **Capacity-based** | Assign to agent with fewest active trips | `COUNT(*) WHERE assigned_to_id = agent_id AND status = 'assigned'` per agent |
| **Performance-weighted** | Weight by agent's historical metrics | Conversion rate, avg response time, customer satisfaction |
| **Owner-defined** | Manual rules set in agency settings | Config stored in `agency.settings` |

### Current state:
- No auto-assignment exists
- The `POST /inbox/assign` primitive is the low-level building block
- An `AutoAssignService` would call `TripStore.update_trip` for each auto-assigned trip

### What would be needed:
- `AutoAssignService` with configurable rule
- `Agency.settings` schema for `auto_assign_rule` config
- Agent availability/capacity tracking
- UI in agency settings to configure the rule

### Design principle (from 2026-05-04 discussion):
> "The assign primitive should be a simple `set assigned_to_id + status = assigned` operation. Auto-assignment is a higher-level service that calls this primitive. This separation allows the auto-assignment rules to evolve independently."

## 4. Architecture Decision Record

**Decision:** Keep `POST /inbox/assign` as a general primitive. Do not build auto-assignment or draft system in the first pass.

**Rationale:**
- The draft system is a pre-trip concern with its own data model
- Auto-assignment rules need agent capacity, skill data, and agency settings — none of which exist yet
- The primitive is the foundation; higher-level logic can be layered on top

**Future integration point:**
- Auto-assignment service → `TripStore.update_trip(trip_id, {"assigned_to_id": agent_id, "status": "assigned"})`
- Draft system → `Trip.draft_inquiry_id` FK + `DraftInquiry` table

---

**See also:**
- `spine_api/server.py` — `POST /inbox/assign` endpoint (the primitive)
- `spine_api/persistence.py` — `TripStore.update_trip` (the atomic write operation)
- `spine_api/models/trips.py` — `Trip.assigned_to_id` column
- `spine_api/services/inbox_projection.py` — reads `assigned_to_id` for inbox presentation
