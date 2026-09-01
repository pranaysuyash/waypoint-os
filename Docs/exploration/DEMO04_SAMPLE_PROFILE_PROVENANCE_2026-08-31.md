# EX-DEMO-04 — Sample Profile Provenance & Stale Empty-State (DEMO-04, DEMO-08)

*Date: 2026-08-31. Source findings: `Docs/SIMULATED_PRODUCT_DEMO_TOOL_TASTER_2026-08-31.md` (finding 4, P1 trust/isolation optics) + `Docs/exploration/DEMO_FOLLOWUP_TASK_BRIEFS_2026-08-31.md` (DEMO-04, DEMO-08, IMP-03 dependency).*
*Mode: research-only. No product code touched. Read-only git used (`git log`/`git show`).*
*Checklist applied: IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md*

---

## 1. Executive Summary

- The "Alex Morgan — Repeat Client (3 Bookings) — Delta Diamond Medallion" panel is **100% a hardcoded front-end constant** inside `RepeatTravelerRecallCard.tsx` (lines 33–64), committed 2026-08-30 in `8ece02e` ("traveler memory architecture"). No API call, no DB row, no fixture import.
- It is rendered **unconditionally** by `IntakeTab.tsx:142` — no gating on tenant trip count, feature flag, or any query result. Every tenant, including a 0-trip fresh signup, sees it on the workbench intake tab.
- **Tenant isolation is NOT at risk**: no path exists where this component renders real cross-tenant data. It is a static simulated object; the only "risk" is trust optics (a privacy-minded evaluator reads it as a cross-tenant leak, exactly as the demo persona did).
- The empty-state copy bug is a **state-machine gap**: "Captured Details" shows its empty text whenever `trip == null` (`IntakeTab.tsx:134–138`), and a blocked draft never promotes to a trip (`draft_store.py:69,374–385`), so the copy co-exists with the fake profile and persists forever after a blocked run.
- A real production memory backend exists (`src/memory/` + `spine_api/routers/customer_memory.py`, mounted at `/api/v1/customers/*`), but the frontend never calls it — `frontend/src/lib/api-client.ts` has zero customer-memory functions.
- **Recommendation: Option B+** — keep the panel as a demo affordance but hard-gate it (render only when no real recall hit AND no trip, badge it "Sample data — illustrative", strip real-looking loyalty numbers), plus fix the empty-state copy with an explicit 4-state machine. Long-term (post-demo): wire the panel to the real `GET /api/v1/customers/memory` endpoint (Option A). Effort: ~0.5–1 day for B+, ~2–3 days for full A wiring.

---

## 2. Provenance Chain (cited)

### 2.1 Render tree

```
/ (agency)/workbench/PageClient.tsx
  └─ <IntakeTab trip={trip} />                      PageClient.tsx:50 (dynamic import), :1336
       ├─ "Captured Details" card                   IntakeTab.tsx:92–139
       │    ├─ trip != null → 6-field grid          IntakeTab.tsx:99–133
       │    └─ trip == null → empty-state copy      IntakeTab.tsx:134–138  ← "Captured details will appear here after processing the inquiry."
       └─ <RepeatTravelerRecallCard … />            IntakeTab.tsx:141–152  ← unconditional
            └─ hardcoded `traveler` object          RepeatTravelerRecallCard.tsx:33–64
```

### 2.2 The data origin

`frontend/src/app/(agency)/workbench/RepeatTravelerRecallCard.tsx`:

- **:32** — comment in code: `// Simulated repeat traveler memory match`
- **:33–64** — the entire "traveler" is an inline object literal:
  - `:34–37` `id: 'cust_alex_m'`, `name: 'Alex Morgan'`, `tripsCount: 3`, `vipStatus: 'Delta Diamond Medallion'`
  - `:40–46` pref_1 "Strict Vegan Meals…" (`isPermanent: true`, source `Direct Message (Trip #9842)`)
  - `:48–54` pref_2 "Aisle seat…" (`88% Fresh`, source `Verified Ticket Scan`)
  - `:56–62` pref_3 "Delta SkyMiles #928410294 · Marriott Bonvoy #48192041" (`95% Fresh`, source `Passport & Loyalty Sync`)
- **:106–108** — the trust claim is a static string: `Verified historical profile recalled from agency memory.`
- **:66–86** — "Apply to Proposal" and "Add Note → Save Fact" are **client-only theater**: `handleApply` pushes the hardcoded prefs into the Agent Notes textarea via the `onApplyPreferences` callback (`IntakeTab.tsx:144–151`); `handleSaveNew` (`:78–86`) fakes a save with a 400 ms `setTimeout` — nothing is persisted anywhere.
- The card accepts `customerMessage` as a prop (`:18, :23`) but **never reads it** — dead input that mimics reactivity.

### 2.3 Rendering conditions

`frontend/src/app/(agency)/workbench/IntakeTab.tsx:141–152` renders `<RepeatTravelerRecallCard>` **outside any conditional** — sibling to the `trip ? … : …` empty-state ternary at `:99/:134`. There is:

- **No** tenant trip-count check,
- **No** feature flag,
- **No** API query,
- **No** `trip != null` gate (the demo persona saw it *both* pre-processing and after a blocked run — consistent with unconditional render).

### 2.4 Same-pattern siblings (same commit, same risk class)

Other simulated panels introduced in the same commit `8ece02e` (2026-08-30, "implement strategic expansion waves, traveler memory architecture, and persona council workbench"):

- `frontend/src/app/(agency)/workbench/MemoryArchitectPanel.tsx:26,37` — defaults `'Alex Morgan (cust_alex_m)'` in GDPR/memory-architect tooling fields.
- `frontend/src/app/(agency)/workbench/CrisisEvacuationPanel.tsx:28` — hardcoded `passengers: ['Alex Morgan', 'Taylor Morgan']`.
- `frontend/src/app/(agency)/settings/components/MemorySettingsTab.tsx:30` — same default entity.

### 2.5 Git provenance

`git log --follow` on `RepeatTravelerRecallCard.tsx`: single commit **`8ece02e73c13c6581023c5cad59b631b946bdbb`** (2026-08-30). The commit message itself describes the backend as the real deliverable ("Traveler memory architecture (src/memory/): decay engine, GDPR engine, provenance chain, sanitizer, retriever, supersession, eligibility gate") — the front-end card is a showcase/mock of that architecture, shipped without a backend wiring or a gate.

---

## 3. Render-Condition Analysis

| Condition | Governing code | Fresh tenant (0 trips) | After blocked run |
|---|---|---|---|
| "Captured Details" grid | `IntakeTab.tsx:99` `trip ? …` | hidden | hidden (still no trip) |
| Empty-state copy | `IntakeTab.tsx:134–138` `: ( <p>Captured details will appear…` | **shown** | **shown** |
| Alex Morgan recall card | `IntakeTab.tsx:142` (unconditional) | **shown** | **shown** |

`trip` comes from `PageClient.tsx:224–236` (`completedTripId` state at `:224`, `resolvedTripId = tripId ?? completedTripId` at `:231`, `useTrip(resolvedTripId)` at `:232–236`). `completedTripId` is only ever set from `extractCompletedTripIdFromDraft` (`PageClient.tsx:132–157`, applied at `:351`), which reads `draft.promoted_trip_id` or a `trip_id` inside run snapshots. Per `spine_api/draft_store.py:69` the draft lifecycle is `open | processing | blocked | failed | promoted | merged | discarded`, and `:374–385` `promote()` is the only writer of `promoted_trip_id`. A **blocked draft never promotes**, so `trip` stays `null` on this surface → empty-state copy renders in all three observed states (pre-processing, processing, blocked).

---

## 4. Tenant-Isolation Verdict

**Verdict: no real cross-tenant data can render through this path. Purely a static demo artifact.**

- The component makes **zero network calls** (no `fetch`, no api-client import — verified: `frontend/src/lib/api-client.ts` contains no customer-memory endpoints). All data is inlined at `RepeatTravelerRecallCard.tsx:33–64`. Every tenant sees the identical bytes.
- The one trap to avoid: the card *implies* tenant-scoped provenance ("recalled from agency memory", "Trip #9842", "Passport & Loyalty Sync", plausible loyalty numbers). To a privacy-minded evaluator this is indistinguishable from a cross-tenant leak — the demo persona's exact reaction (demo doc §2 step 4, finding 4). The harm is **trust optics and false affordance**, not data exposure:
  1. It claims verified memory that does not exist on this account;
  2. "Apply to Proposal" writes fabricated facts (vegan/aisle/SkyMiles) into the user's own Agent Notes (`IntakeTab.tsx:144–151`), which then feed the pipeline — i.e., fake data can contaminate a real run;
  3. Real-looking loyalty numbers (`#928410294`, `#48192041`) could be mistaken for a real person's PII.
- Secondary flag: `get_customer_memory` in `spine_api/routers/customer_memory.py:162–189` accepts `agency_id` auth but the legacy lookup `_find_customer_profile` (`:138–155`) scans a process-global `CUSTOMER_MEMORY_STORE` dict (`:37`) with no per-agency partition. That endpoint is not wired to the frontend today, so this is latent — but the moment Option A wiring happens, that store must be agency-scoped or it becomes a genuine isolation hole.

---

## 5. Stale Empty-State Copy Analysis (DEMO-08)

**Why it co-renders:** the empty state and the recall card live in *different siblings* of the same parent. The empty state is gated on `trip == null` (`IntakeTab.tsx:134–138`); the recall card has no gate at all (`:141`). So "no captured details yet" and "here is Alex Morgan's verified history" display simultaneously — a contradiction visible on first paint.

**Why it persists after a blocked result:** the panel's only signal is trip existence. The run's real state (processing / blocked) lives in the workbench store (`store.draft_status`, spine run state — `PageClient.tsx:246–247` shows the store *does* know `blocked`/`failed`) but `IntakeTab` never receives or reads it. `IntakeTab.tsx` imports only `useWorkbenchStore` for the two textareas (`:53`), not `draft_status`. Missing condition: nothing transitions the panel out of the pre-processing message once `draft_status ∈ {processing, blocked, failed}` or a run is in flight. The fix condition is derivable in-place: `store.draft_status` (values per `draft_store.py:69`) — no new plumbing needed beyond reading what the store already holds.

**Correct state machine** (single owner for the whole "Captured Details" region):

| State | Condition (derivable today) | Copy/behavior |
|---|---|---|
| `pre_processing` | no draft, `trip == null`, `input_raw_note` empty | "Captured details will appear here after processing the inquiry." |
| `processing` | `draft_status === 'processing'` (or spine run in-flight) | "Processing… capturing destination, dates, party, budget…" |
| `blocked` | `draft_status === 'blocked'` | "Processing stopped — N fields need your input" + link to repair surface (pairs with IMP-05/DEMO-09) |
| `captured` | `trip != null` (draft promoted) | current 6-field grid (`IntakeTab.tsx:99–133`) |
| `failed` | `draft_status === 'failed'` | error copy + retry |

---

## 6. Options & Recommendation (IMP-03 dependency)

### Option A — Gate on real tenant-memory hit only
Render the recall card only when `GET /api/v1/customers/memory` returns a profile for the current tenant's customer context. Pros: honest by construction, showcases the real `src/memory/` architecture (the stated point of commit `8ece02e`). Cons: requires real wiring (api-client function + trigger point — there is no in-workbench "customer" concept until a trip/draft exists, so the pre-processing state would show *nothing*, which is actually correct for a 0-memory tenant); needs the agency-scoping fix in `CUSTOMER_MEMORY_STORE` first (§4); ~2–3 days.

### Option B — Keep it, badge as Sample data, strip real-looking numbers
Badge the card "Sample data — illustrative, not from your workspace"; replace loyalty numbers with obviously fake ones (e.g. `SKYMILES ****-SAMPLE` or `XX-000000`); neutralize the "Verified… recalled from agency memory" line ("Example of what recalled memory looks like"); make "Apply to Proposal" and "Save Fact" either disabled with tooltip or stop injecting fake facts into Agent Notes. Cons: still renders fabricated provenance on a fresh tenant; evaluator attention still spent on a mock. Effort: hours.

### Option C — Remove the card
Cleanest trust posture; loses the only visualization of the memory product story in the workbench. Effort: minutes (delete + remove import; supersession rules satisfied — no real capability removed since nothing is wired).

### Recommendation: **B+ now, A as the follow-through**

1. **Ship B+ for demo-grade** (targets IMP-03 acceptance): sample badge + de-realized numbers + honest copy + stop the fake apply-to-notes injection. Keep it a single component (no duplicate panel), per the brief.
2. **Sequence A immediately after**: fix `customer_memory.py` agency scoping → add `getCustomerMemory()` to `api-client.ts` → gate the card on a real 200-with-profile hit, falling back to the sample badge only in an explicit `?demo=1`-style mode. This converts the mock into the production surface the backend already implements (`/api/v1/customers/memory`, `/remember`, `/hydrate-trip/{trip_id}` — `customer_memory.py:162,192,288`), honoring the no-parallel-paths doctrine.
3. **Fix the empty state** with the 5-state machine in §5, driven by `store.draft_status` already in the workbench store. This is independent of A/B/C and should ship with it.

---

## 7. Intended Production Data Path (backend reality check)

The backend side is real and recently built (commit `8ece02e`):

- **Domain layer**: `src/memory/` — `store.py` (`MemoryStore`, durable JSON at `data/memory/`, `:35–41`), `retriever.py` (`HybridMemoryRetriever`, token-budgeted lexical retrieval, `:22`), plus `decay_engine.py`, `eligibility_gate.py`, `gdpr_engine.py`, `provenance.py`, `sanitizer.py`, `supersession.py`, `models.py`.
- **HTTP layer**: `spine_api/routers/customer_memory.py`, router prefix `/api/v1/customers` (`:31`), mounted in `spine_api/server.py:1333`. Endpoints: `GET /memory` (`:162`), `POST /remember` (`:192`), `POST /hydrate-trip/{trip_id}` (`:288` — auto-fills trip fields from remembered preferences), `POST /memory/ingest` (`:381`), `GET /memory/query` (`:422`), `GET /memory/entity/{entity_id}` (`:459`), `POST /memory/forget` GDPR erasure (`:478`).
- **Intended flow**: agent ingests verified facts (`/memory/ingest`, tiered Working/Episodic/Semantic/Procedural/Preference per module docstring `:1–11`) → on a new inquiry, `/hydrate-trip` or `/memory` recall surfaces them with provenance + freshness/decay — which is *precisely the UX the Alex Morgan card mock-ups* (category badges, "X% Fresh", "Permanent Safety", source citations). The card is a UI mock of a live backend it was never pointed at.
- **Gap**: frontend has zero calls into these endpoints (`api-client.ts` — no `customers/memory` references, verified). Also note `MemoryStore.DATA_DIR = data/memory/` is gitignored per the commit ("ignore runtime memory store (data/memory/)") — durable but file-based, consistent with the dual-store pattern flagged in AGENTS.md. **Agency keying of the durable `MemoryStore` is verified**: its in-memory cache is explicitly agency-partitioned (`src/memory/store.py:43` — `_memory_cache: Dict[str, List[BaseMemoryItem]]  # agency_id -> items`; load path keys entries by `item.agency_id` at `:63–66`; ingest takes `agency_id` at `:89`). The residual isolation hole is only the router-level legacy dict `CUSTOMER_MEMORY_STORE` (`customer_memory.py:37`), a process-global keyed by customer id with no agency partition, scanned by `_find_customer_profile` (`:138–155`, used by `/memory` `:162` and `/remember` `:192`) — that dict must be agency-scoped (or retired in favor of `_MEMORY_STORE`) before any frontend wiring (Option A) lands.

---

## 8. Effort Estimate

| Work item | Estimate |
|---|---|
| B+: sample badge + fake-ify loyalty numbers + honest copy + neutralize apply/save injection (single component) | 0.5 day incl. one frontend test |
| Empty-state 5-state machine in IntakeTab (reads existing `draft_status`) | 0.25–0.5 day |
| Agency-scope fix in `customer_memory.py` legacy store + tests | 0.5 day |
| Option A wiring: api-client fn + gate card on real recall + `?demo` escape hatch | 1–1.5 days incl. E2E check |
| **Total to full A** | **~2.5–3.5 days** |

Verification bar (per repo discipline): fresh-tenant E2E (signup → workbench → no profile or badged sample; process → blocked → empty-state replaced by blocked copy), plus backend pytest for the scoping fix; `uv run ruff check` clean.

---

## 9. Open Questions for Pranay

1. **Demo posture**: is the Alex Morgan card a deliberate sales-demo asset to keep reachable via an explicit demo mode, or scaffolding to be replaced by real wiring ASAP? (Drives whether B+ is a stopgap or the end state.)
2. **Option A trigger point**: memory recall needs a customer identity (email/phone/name). Pre-processing there is none — do we recall on raw-note name-match (`/memory?name=`), or only after first packet capture? Recommend the latter (identity verified by extraction) for both honesty and matching accuracy.
3. **Fake-facts injection**: "Apply to Proposal" currently writes fabricated preferences into Agent Notes and thus into real pipeline runs. Confirm this should be blocked entirely (my recommendation) vs. kept for demo storytelling.
4. **Backend scoping**: the legacy `CUSTOMER_MEMORY_STORE` router dict is unscoped (verified, §4/§7) while the durable `MemoryStore` is agency-keyed (verified, §7) — should IMP-03's follow-up retire/partition the legacy dict, or is a broader customer-memory cleanup planned? (Latent isolation hole once any frontend wiring lands.)
5. **Register**: upon ratification, DEMO-04 + DEMO-08 map to proposed F-2x rows; IMP-03 scope should absorb the empty-state machine (§5) since it's the same panel region.
