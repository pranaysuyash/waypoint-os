# Draft System — Master Index

> Research on the Draft as a first-class persistent workspace — architecture, lifecycle, multi-agent collaboration, and UI design for the Waypoint OS Workbench.

---

## Series Overview

This series covers the Draft system — transforming the Workbench from an ephemeral, refresh-loses-everything experience into a persistent workspace where agents can save incomplete work, return later, resume seamlessly, and have a full audit trail from the moment they start.

**Target Audience:** Backend engineers, frontend engineers, product managers

**Key Insight:** The `draft_id` was invisible plumbing. Making it a first-class entity with its own lifecycle, storage, API, and UI transforms the agent experience from fragile to resilient.

---

## Documents

| # | Document | Focus |
|---|----------|-------|
| 1 | [DRAFT_SYS_01_ARCHITECTURE.md](DRAFT_SYS_01_ARCHITECTURE.md) | Data model, hybrid storage (SQL + JSON), API surface, system integration |
| 2 | [DRAFT_SYS_02_LIFECYCLE.md](DRAFT_SYS_02_LIFECYCLE.md) | State machine, auto-save design, naming logic, promotion workflow, draft-era events |
| 3 | [DRAFT_SYS_03_COLLABORATION.md](DRAFT_SYS_03_COLLABORATION.md) | Multi-agent scenarios, duplicate detection, draft merging, trip linking, transfers |
| 4 | [DRAFT_SYS_04_UI_UX.md](DRAFT_SYS_04_UI_UX.md) | Sidebar section, drafts list, workbench header, save indicator, URL routing, status badges |

---

## Key Themes

### 1. Persistence Over Ephemerality
Every keystroke, every run, every blocked validation is saved. Agents can close their laptop, return tomorrow, and pick up exactly where they left off. The URL `?draft=abc123` is a shareable, refresh-proof link to their work.

### 2. Audit Trail from Day One
The audit trail starts the moment a draft is created — not when a trip is promoted. This gives full visibility into the agent's journey: what they tried, what failed, what they fixed, and how long it took.

### 3. Hybrid Storage (First Principles)
SQL for metadata (listing, filtering, status queries) + JSON for payload (large customer messages, structured data). This follows the existing TripStore dual-backend pattern while adding the relational queries that JSON files alone cannot provide.

### 4. Multi-Agent Awareness
Duplicate detection prevents two agents from independently working on the same customer. Draft transfer handles agent absences. Draft merging combines parallel work. These collaborative features are essential for agency operations.

---

## Design Decisions Record

See [DRAFT_SYS_DECISION_TRAIL.md](DRAFT_SYS_DECISION_TRAIL.md) for the full discussion trail including:
- Storage: Hybrid SQL + JSON (not JSON-only)
- Auto-save: 5s debounce with content guards + explicit Save Draft button
- Naming: Auto-generate from first line (customer message → agent notes → timestamp), always editable
- UI: New "Drafts" section in left sidebar (Option B)
- Merging: Users can attach/link existing drafts and trips

---

## Cross-References

| Related Series | Connection |
|---------------|------------|
| Process Log (PROCESS_LOG_*) | Draft-era events captured in process log |
| Domain Events (DOMAIN_03_*) | Draft events extend the domain event taxonomy |
| Timeline (TIMELINE_*) | Draft-era events merge into trip timeline on promotion |
| Audit Trail (AUDIT_*) | Draft events promoted to audit trail |
| Workforce Management (WORKFORCE_*) | Draft transfer for agent availability |
| CRM (CRM_*) | Customer matching for duplicate detection |

---

## Implementation Phases

| Phase | Scope | Impact |
|-------|-------|--------|
| 1 | Backend plumbing: DraftStore, API, audit integration, draft_id in runs | Foundation — enables persistence |
| 2 | Frontend wire: Workbench loads/saves via API, URL routing, auto-save | Agent can refresh without losing work |
| 3 | Drafts UI: Sidebar section, drafts list page, status badges | Drafts visible and manageable |
| 4 | Collaboration: Duplicate detection, merging, linking, transfer | Multi-agent workflows |

---

**Created:** 2026-04-29
