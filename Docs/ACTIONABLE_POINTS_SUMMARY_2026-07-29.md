# Actionable Implementation Roadmap (Waypoint OS)

**Date**: 2026-07-29  
**Governing Standard**: `motto_v4.md` & `Docs/FIRST_PRINCIPLES_MOTTO_V4_DOCTRINE.md`  
**Status**: Active Execution Plan  

---

## 1. Engineering & Architecture Actionables (`motto_v4.md`)

1. **Enforce Third-Layer Decoupling (Rule 0.15)**
   - **Model Layer (`src/llm/`)**: Restrict LLM usage strictly to nuance extraction, narrative phrasing, and follow-up tone calibration.
   - **Pipeline Layer (`spine_api/routers/`)**: Keep flow control, decision gate state machines (`PROCEED`, `ASK_FOLLOWUP`, `ESCALATE`), and fallback logic strictly code-driven.
   - **Data/Config Layer (`src/intake/geography.py`, rate dictionaries)**: Treat rate tables, airport codes, tax rules, and normalization maps as production code (versioned, typed, linter-audited).

2. **Deterministic Constraint Supremacy**
   - Hard constraints (dates, max budget, pax count, mobility bounds) can **never** be overridden by LLM output without an explicit operator override envelope.

3. **Eliminate Duplicate Pipelines (Rule 0)**
   - All client channels (Chrome extension, Next.js workbench, WhatsApp webhooks) must route through unified FastAPI endpoints (`spine_api/routers/`).

---

## 1.1 Understanding "Shadow Pipelines" (`motto_v4.md` Section 0 & 0.15)

A **shadow pipeline** is any parallel, ad-hoc, or duplicate code path that bypasses the canonical backend architecture to process data, call models, or mutate state independently.

* **Examples of Shadow Pipelines**:
  1. *Direct Client-to-LLM Calls*: Frontend JS or extension scripts calling OpenAI/Gemini directly, bypassing `spine_api/routers/inbound.py`.
  2. *Duplicate Logic*: Implementing separate parsing/scoring rules in Streamlit scripts, CLI tools, and FastAPI backend endpoints.
  3. *Un-Audited State Mutation*: Editing database models directly without passing through canonical decision state machines (`src/intake/decision.py`).
* **Why Eliminating Shadow Pipelines is Mandatory**:
  - Eliminates logic drift between web, mobile, and browser extension apps.
  - Ensures 100% of inputs pass through deterministic validation gates, PII filters, and audit provenance logging.

---

## 1.1.1 Architectural Decision Record: Client-Side Fallback Policy (2026-07-29)

* **Decision**: **Do NOT keep direct client-side LLM invocations as a fallback.**
* **Rationale**:
  1. **Security & Key Protection**: Direct client-side calls require exposing raw provider API keys in browser/extension memory.
  2. **Safety & Policy Integrity**: Client-side LLM calls bypass PII scrubbers, budget constraint gates, schema normalization, and immutable audit logs.
  3. **Correct Fallback Standard**: Fallbacks must occur **server-side** inside the backend pipeline layer (Primary Model → Secondary Provider → Deterministic Default Packet). If network is completely offline, the client queues operations locally in IndexedDB/Zustand until reconnection.

---

## 1.2 The Single Biggest Unblock: Priority #1 (Native Ingestion & State Sync)

From first principles, the single biggest operational unblock for Waypoint OS is **Priority #1 (Native Ingestion Chrome Extension + Optimistic SSE State Engine)**.

* **Why This Unblocks Everything First**:
  1. **Removes the "WhatsApp Void" Friction**: 85%+ of travel agency inquiries arrive via unstructured WhatsApp chats. Forcing planners to manually copy-paste text into a web app creates an unbearable data-entry tax. 1-click capture inside WhatsApp Web eliminates this friction instantly.
  2. **Restores Operational Trust**: Optimistic UI state updates and SSE event streams guarantee that when a planner inputs a budget or date, the UI state machine updates in real time (`NEEDS_BUDGET` → `READY_FOR_STRATEGY`) with zero page refreshes.
  3. **Unlocks Downstream Pipeline**: Native ingestion populates the structured `TripPacket`, which immediately powers automated follow-ups (Priority #2), trust scorecards (Priority #3), and proposal links (Priority #5).

---

## 2. Priority Product Rollout Actionables (#1 through #8)

### Phase 1: Immediate Retention & Ingestion (Weeks 1–4)
- **Action 1 (Priority #1)**: Distribute Chrome Companion Extension for 1-click inquiry capture from WhatsApp Web/Gmail into `POST /api/v1/inbound/stream-parse`.
- **Action 2 (Priority #1)**: Wire Zustand/React optimistic mutation hooks on the frontend to update UI trip state instantly via Server-Sent Events (SSE).
- **Action 3 (Priority #2)**: Connect `POST /api/v1/followups/generate` to auto-generate 1-click personalized WhatsApp/email re-engagement copy for stale leads.

### Phase 2: Proposal Trust & Omnichannel Dispatch (Weeks 5–8)
- **Action 4 (Priority #3 & #5)**: Replace static PDF proposals with dynamic web links (`/api/v1/proposals/{trip_id}/web-link`) featuring suitability match %, safety badges, and price lock guarantees.
- **Action 5 (Priority #4)**: Provision WhatsApp Business Cloud API & SendGrid credentials to enable automated outbound message dispatch and delivery webhooks.

### Phase 3: Commercial Yield & Operations (Weeks 9–12)
- **Action 6 (Priority #6)**: Deploy Yield Arbitrage Dashboard (`/api/v1/arbitrage/opportunities`) to highlight higher-commission supplier alternatives before proposals lock.
- **Action 7 (Priority #7 & #8)**: Enable Ghost Concierge autonomic flight/hotel disruption monitoring and enforce senior planner review signoff for quotes >$10,000.

---

## 3. Verification & Governance Actionables

1. **Tier 3+ Evidence Gate Before Handoff (Sections 0.5 & 0.6)**
   - Require end-to-end integration test runs (`uv run pytest tests/test_* -v`) for all changes touching auth, pricing, or status transitions.
2. **Living Documentation & Decision Traceability (Sections 0.3 & 0.12)**
   - Record every architecture decision in `Docs/` and maintain 100% synchronization with `Docs/INDEX.md`.
