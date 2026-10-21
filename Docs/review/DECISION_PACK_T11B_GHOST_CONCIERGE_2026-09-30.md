# Decision Pack — T11b: Ghost Concierge (FND-0261 lane) — WIRED as composition

**Date:** 2026-09-30
**Status:** ☑ Decision made — **WIRE**, as a composition layer over the existing
IROPS healer, not a second recovery engine. Tranche build queued.
**Decision owner:** Pranay ("wire it, isnt that the doctrines aligned, long
term 1st principles").
**Tracker:** `Docs/review/LAUNCH_READINESS_TASK_INVENTORY_2026-09-29.md` row
T11/T11b; council condition on wiring: "Jev-drafted re-engagement copy with
FND-0286-style gates before any send."

## 1. What the engine is (verified in-tree)

`spine_api/services/ghost_concierge.py` (144 lines): flight-telemetry
evaluation → connection-cascade risk → proactive recovery actions. Claims an
autonomic in-trip guardian role.

**Reality at decision time:** zero serving-path callers (only its own test
imports it); `POST /frontier/ghost/workflows` creates rows tagged
`"simulated autonomic workflow (no provider execution)"` that nothing ever
advances; FE toggle `enable_ghost_concierge` already defaulted false (T11a).

## 2. Supersession check (mandatory before wiring — done 2026-09-30)

- `src/orchestration/irops_healer.py` **already computes real-time disruption
  ripple cascades** on the stored journey graph and chains statutory claims
  (EU261/US-DOT) — the exact "connection cascade" niche ghost_concierge
  sketches. Wiring ghost_concierge as its own recovery engine would duplicate
  a live system (the repo's cardinal defect).
- `disruption_radar.py` is reactive/operator-facing and preview-only ("no
  live feed is connected") — different lane (alerts + rebook review), not a
  duplicate of the proactive trigger.

**Verdict:** wire ghost_concierge as **composition**: it becomes the
proactive trigger + telemetry evaluation layer that *feeds the existing
healer* and the honest messaging lane — never a parallel recovery engine.

## 3. The first-principles wiring (why it does not wait for the provider gate)

Telemetry has three honest sources, two of which exist **today**:

1. **Traveler messages** (T1/T6, live): "my flight got cancelled" arriving
   through `/a/[token]` → message store IS disruption telemetry, attributed.
2. **Operator status updates** (live): operator marks a flight delayed/
   cancelled on the trip surface.
3. **Provider adapter seam** (2026-10-06 gate): a narrow
   `FlightStatusProvider` interface; the live feed is one implementation
   behind it. The engine is wired and useful on sources 1–2 before the gate
   opens; the provider is an upgrade, not a prerequisite.

## 4. Wired behavior (tranche scope)

1. `FlightStatusProvider` seam + `OperatorReportedProvider` (sources 1–2)
   implemented; live provider stubbed behind the gate.
2. Monitoring entry-point in the trip lifecycle: evaluates ghost_concierge
   risk when flight facts change; on risk, chains `irops_healer` cascade.
3. Recovery output = **drafted, gated traveler re-engagement copy** +
   operator action items through the existing honest dispatch
   (`message_dispatch` NOT_CONFIGURED adapters stay honest until E1).
   Autonomy rung: **proposes, never sends** (ADR-008 §7).
4. `/frontier/ghost/workflows` rows become real: created by actual
   evaluations, status advances, reality tier upgrades from PLANNED only when
   attributed data exists; the "simulated" metadata is retired for wired rows.
5. No money movement (T10 invariant class), no autonomous sends.

## 5. Doctrine alignment

- FND-0261 serving-path rule: wiring creates real callers.
- Honesty gates: council's own condition honored (FND-0286-style gates).
- Autonomy: ADR-008 §7 decision-support rung.
- No duplicates: composition with irops_healer (§2).
- Honesty-class: the fabricated-workflow rows are either made real or
  retired — no third state.

## 6. Falsifier / revisit

If the provider gate opens (10-06) and live telemetry shows the
operator/traveler-fed evaluation produced negligible true-positive risk
detections across a pilot cohort, revisit whether the proactive lane earns
its surface (re-archive with that data).

---

## 7. Implementation record

**Shipped 2026-09-30 (step 1 — seam + evaluation + truth-up payload):**
`spine_api/services/ghost_concierge_monitor.py` — `FlightStatusProvider`
protocol + `OperatorReportedProvider`; telemetry built from
`trip["flight_status_updates"]` (operator-entered, validated against
reportable statuses — unreportable/blank records dropped, never guessed);
`traveler_disruption_signals()` (first-party T1/T6 message markers,
best-effort); `monitor_evaluate_trip()` (None when no telemetry — the engine
is never fed invented data; provider seam extends operator facts);
`workflow_from_report()` — real-evaluation workflow payload where every
intervention is `DRAFT_AWAITING_OPERATOR` (propose-never-send) and the
reality note names its data source. Tests
`tests/test_ghost_concierge_monitor.py` 7/7 (+2 pre-existing engine tests)
— ruff clean.

**Step 2a shipped 2026-09-30:** `run_ghost_concierge_for_trip()` — serving-path
entry that evaluates, persists the truth-up workflow on the trip record
(`trip["ghost_concierge"]`), audit-logs, and chains
`irops_healer.execute_healing_protocol` when the disrupted flight maps to a
stored journey node; both no-graph and no-node abstentions are recorded
honestly (`healer not chained: …`). Hermetic file-store fixtures only
(data-safety rule). Suite 11/11, ruff clean.

**Remaining (step 2b — API hooks + surface):**
(a) lifecycle entry: run `monitor_evaluate_trip` when flight facts or
traveler disruption messages change; (b) on DISRUPTED/DEGRADED, persist the
workflow payload via the ghost-workflow store and chain
`irops_healer.execute_healing_protocol` for operator review; (c) surface
drafted interventions to the operator (workbench surface, same honesty
pattern as ClaimDispositionCard); (d) retire the fabricated
`POST /frontier/ghost/workflows` PLANNED-row path in favor of the real one;
(e) parity snapshot regen via `.venv/bin/python` if routes change.

---

## 8. Implementation record (step 2b–contract, 2026-09-30)

**Shipped:** `PATCH /trips/{trip_id}` now accepts
`flight_status_updates` (added to `TripPatchRequest` — the canonical mutable
contract) and, on flight-fact changes, runs the monitor end-to-end:
evaluate → persist truth-up → chain healer when a journey node matches →
return the ledger in the response. `TripResponse.ghost_concierge` added to
the contract (the response was silently dropping the field — third instance
of the silent-strip class; parity test extended to catch these at the schema
level going forward is queued with 2d).

**Three real defects the endpoint test flushed out, fixed in-pass:**
1. `AuthMiddleware` rejects before routing — the repo's hermetic
   disable-auth env pattern applied (dependency overrides can't bypass it).
2. Persistence backends that don't round-trip non-column keys would starve
   the monitor — the hook passes the reported facts via an explicit merged
   view and copies the resulting ledger back onto the response trip.
3. `TripResponse` had no field for the ledger (silent-strip, as above).

**Evidence:** monitor suite 10/10 (incl. the real PATCH→monitor→response
integration test); consolidated batch 33/33 across ghost-concierge, claim
disposition, passenger-rights, parity; ruff clean on all changed files.

**Remaining (2c–2d):** operator surface for drafted interventions;
retire the fabricated `POST /frontier/ghost/workflows` path + parity regen
(`.venv/bin/python`); messaging-webhook telemetry hook (traveler "cancelled"
messages) — the seam (`traveler_disruption_signals`) already exists.

**Step 2c shipped 2026-09-30:** `GhostConciergeCard` (parcel-truth pattern)
mounted on the trip decision page beside the ClaimDispositionCard — renders
real evaluations only (stable/unevaluated trips render nothing), interventions
severity-sorted CRITICAL-first, and the operator-gate note ("nothing is sent
automatically") with the healer abstention reason. Trip type extended; card
tests 6/6; typecheck clean.

**Step 2d shipped 2026-09-30 — tranche COMPLETE:**
- Fabricated `POST|GET /frontier/ghost/workflows` routes RETIRED (rows were
  simulated PLANNED and never advanced); GhostWorkflow Create/Response models
  removed from the router; DB model retained for migration provenance.
  Cross-tenant probe test for that surface retired with an explanatory note.
- Webhook telemetry hook live: `process_inbound_traveler_message` now runs
  the monitor best-effort after trip resolution — traveler "cancelled/delayed"
  messages feed real evaluations; monitoring never breaks message processing.
- Parity snapshot regenerated via `.venv/bin/python` (356→354 paths; ghost
  paths gone). Final batch: 28 passed across ghost-concierge, claim
  disposition, parity, cross-tenant probes; ruff clean; all imports green.

**T11b COMPLETE.** The engine is wired as composition (decision pack §2),
fed by honest sources, operator-gated at every output, with the fabricated
surface fully retired.

## 9. Council falsifier — live journey record (2026-10-03)

Journey executed: signup (isolated user) → run cbbff4a8 (vague Europe request)
→ completed ASK_FOLLOWUP w/ 3 questions → ask link minted via
/followups/{trip}/send (dispatch UNSUPPORTED for link channel = honest) →
public /a/{token} page served all 3 questions → traveler submitted 3 answers
(recorded:true) → **answers LOST on read-back** → FND-0307 opened (P1):
public_asks sync routes write via the FileTripStore-only facade while the
trip lives in SQL. The falsifier did exactly its job: T1 was verified on the
file backend; the SQL production path was never end-to-end tested until now.

What the journey PROVED working: run→ASK_FOLLOWUP pipeline, ask-link minting,
token-gated public ask page (3/3 questions), answer submission API contract,
and the honest UNSUPPORTED dispatch. The P1 write-path split-brain is the one
break, precisely located (persistence.py:677 vs 1543), with the fix path
documented in FND-0307.

## 10. Falsifier after-action (FND-0307, 2026-10-03 cont.)

Root cause corrected during fix: NOT split-brain — the facade dispatches
correctly; the confirmed break was **TripResponse lacking
`traveler_answers`** (4th silent-strip instance). Fixed with dual-source
surfacing (top-level + analytics._extra fold) + regression pin.
Honest residuals: (a) the live S2 re-journey needs a server under a KNOWN
env — my nohup start failed silently and the previous server exited;
(b) which store the exited process used is unknown (DB at .env URL has zero
trips — worth an ops look before the next live session).

## 11. S2 + storage-tier verification COMPLETE (2026-10-05)

The full chain is verified end-to-end on the production posture (SQL +
FORCE-RLS + fold-backed answers): live PATCH journey → answers recorded →
folded into `analytics._extra` on the SQL row (verified through the tenant
GUC, transaction-scoped) → unfolded by the fixed `from_dict` → surfaced in
`GET /trips` (3/3 answers). **FND-0307 S2 closed.**

Ops lesson recorded: the `trips` table has FORCE RLS — raw DB probes without
`set_config('app.current_agency_id', …)` inside a transaction are RLS-blind
and will report zero rows. The earlier "zero trips in SQL" observations were
probe artifacts, not data loss.
