# E7 — AuthorityTier Shadow-Mode Design (audit-only adoption path before enforcement)

**Status:** Exploration / design brief — no implementation performed (READ-ONLY task).
**Filename date note:** File name carries the E-wave date (2026-09-02) per task spec; verification pass against the live tree performed 2026-09-04. All path:line citations re-checked against the working tree on that date.
**Convention:** `[VERIFIED]` = read directly from code in this pass. `[INFERRED]` = design judgment or extrapolation, flagged inline.

---

## 1. Question

The dormant `AuthorityTier` matrix (`src/schemas/boundary_contracts.py`) has an agreed adoption path: run it in **audit-only "shadow" mode** — evaluate what the matrix *would* deny/allow at each consequential action, LOG the verdict without affecting behavior, for one release cycle — then flip to enforce. This doc designs:

1. What exists today (dormant matrix, live gates, audit substrate).
2. The shadow machinery: config flag, evaluation hook points, event payload, volume/cost caps.
3. The weekly report the review reads.
4. The rollout ladder (shadow → tune → enforce) and flip criteria.

---

## 2. Current state

### 2.1 The dormant matrix surface — `[VERIFIED]`

| Surface | Location | State |
|---|---|---|
| `AuthorityTier` (TIER_0_AUTONOMOUS … TIER_4_DUAL_CONTROL) | `src/schemas/boundary_contracts.py:26-33` | Enum exists; **zero pipeline callers** |
| `TrustZone` (5 zones), `CapabilityScope` (6 scopes) | `src/schemas/boundary_contracts.py:17-43` | Enum exist; referenced only by boundary engine + router + tests |
| `BoundaryContract` (zone-transition contract incl. `authority_tier`, `audit_event_type`) | `src/schemas/boundary_contracts.py:45-54` | 5 contracts bootstrapped in `BoundaryEngine._bootstrap_standard_contracts` (`src/services/boundary_engine.py:52-100`); **nothing evaluates them at runtime** |
| `ScopedCapabilityToken` (HMAC-SHA256 signed `token_id.b64payload.signature`) | `src/schemas/boundary_contracts.py:57-70`; engine `src/services/boundary_engine.py:110-223` | Issue/verify/revoke implemented and tested; token store is **in-memory dict** (`self._tokens`, `boundary_engine.py:41`) — issuance/revocation state is lost on process restart |
| Token endpoints | `spine_api/routers/boundaries.py:33-126` | `POST /tokens/issue` (agency-auth'd), `GET /tokens/{token}/verify` (**no auth dependency**), `POST /tokens/{token}/revoke` (agency-auth'd) |
| `AuthorityGateKeeper.AUTHORITY_CATALOG` — 9 actions with tier, roles, dual-approval flags | `src/services/boundary_engine.py:233-281` | The actual "matrix": e.g. `dispatch_proposal_to_client` → TIER_2, `accept_travel_agreement`/`authorize_credit_card_charge` → TIER_3, `issue_refund_above_threshold`/`override_safety_restriction` → TIER_4 dual control |
| `AuthorityGateKeeper.evaluate_action_authority(action, actor_role, dual_approver_role)` | `src/services/boundary_engine.py:283-307` | **Only caller is `tests/test_boundary_engine.py:107-145`** (5 tests: tier-role allow/deny, dual-control separation). No production enforcement caller. |
| `GET /authority-matrix` (read-only catalog) | `spine_api/routers/boundaries.py:129-145` | Live; frontend references the boundaries routes in `frontend/src/lib/route_map.ts` and `frontend/src/app/(agency)/workbench/PersonaCouncilPanel.tsx` (route-map registration; not an enforcement consumer) `[VERIFIED: referenced; INFERRED: display-only]` |

**Net:** the matrix evaluator is complete, tested, and unwired. Shadow mode is the correct bridge because it exercises the *evaluator and its catalog against real traffic* without changing any decision.

### 2.2 What would eventually bind — the enforcement landscape — `[VERIFIED]`

There are **two** candidate enforcement points, and the task framing needs one correction:

1. **`evaluate_autonomy_dispatch_gate`** (`spine_api/services/autonomy_gates.py:30-109`) — heuristic over `(total_package_usd, has_non_refundable_deposit, destination_risk_rating, unverified_suppliers_count, advisor_override)`; ≥$10k → HIGH, non-refundable → MEDIUM, ELEVATED/HIGH destination → HIGH, unverified suppliers → HIGH; any HIGH or ≥2 factors → human sign-off. **It has zero production callers** — only `tests/test_intelligence_and_governance.py:66,76`. It is implemented and unit-tested, but *not wired into the pipeline*. So "live heuristic" is accurate in the sense of "living, tested code," not in the sense of "in the request path."
2. **The actually-live autonomy gate** is the NB02 policy layer: `NB02JudgmentGate.evaluate()` (`src/intake/gates.py:156-253`) → `AutonomyOutcome` (`src/intake/gates.py:47-92`: `raw_verdict`, `effective_action ∈ {auto, review, block}`, `approval_required`, `rule_source` e.g. `approval_gates:PROCEED` / `safety_invariant` / `mode_override:*` / `warning_policy`), driven by `AgencySettings.autonomy.approval_gates` / `mode_overrides` / `auto_proceed_with_warnings`, with the STOP_NEEDS_REVIEW safety invariant. This flows into `SpineRunResponse.autonomy_outcome` (`spine_api/contract.py:42-50,132`) and is surfaced at `src/intake/orchestration.py:451`.

Shadow mode should bind **both**: the live NB02 outcome (real traffic today) and the dispatch heuristic at the moment it gets wired (so the matrix and the heuristic are tuned from the same corpus of shadow events).

Money-adjacent endpoints that would carry tier requirements `[VERIFIED: endpoints exist; tier assignment INFERRED from catalog]`:

| Endpoint | File | Catalog action / tier candidate |
|---|---|---|
| `POST /send` (outbound proposal message to traveler) | `spine_api/routers/messaging.py:47` | `dispatch_proposal_to_client` → TIER_2 |
| `POST /public/proposals/{token}/accept` (traveler e-sign) | `spine_api/routers/public_proposals.py:702` | `accept_travel_agreement` → TIER_3 |
| `POST /api/v1/price-lock/{trip_id}/audit-rate`, `/{trip_id}/re-lock` | `spine_api/routers/price_lock.py:140,187` | `commit_supplier_price_lock` → TIER_2 |
| `POST /api/v1/financial-settlement/vcc/issue`, `/fx/calculate-quote`, `/schedules/build`, `/commission/split` | `spine_api/routers/financial_settlement.py:102-167` | payment-adjacent; VCC issue → TIER_3/4 candidate; others are DETERMINISTIC_PREVIEW computations (preview envelope, `_preview_envelope`) |
| `POST /{advisor_id}/request-payout` | `spine_api/routers/subagent_payouts.py:37` | money-out → TIER_2/4 candidate |
| Booking-data accept/reject from customer, payment tracking update | `spine_api/server.py:3310,3335,2973` | low-tier (TIER_0/1) bookkeeping |
| Refunds | — | **No refund endpoint exists today.** `issue_refund_above_threshold` (TIER_4) and `ISSUE_REFUND` scope have no implementation. Shadow mode can still log the *rule* for future wiring. |

### 2.3 The audit substrate to reuse — `[VERIFIED]`

Two hash-chained ledgers exist, plus a dual-write bridge:

1. **File ledger — `AuditStore`** (`spine_api/persistence.py:2257-2490`):
   - JSONL at `data/audit/events.jsonl`; `log_event(event_type, user_id, details)` (line 2397).
   - Chain: `current_hash = sha256(f"{event_id}:{event_type}:{user_id}:{previous_hash}:{timestamp}:{json.dumps(details, sort_keys=True)}")`; genesis = `"GENESIS_BLOCK_HASH"`. Cross-process `file_lock` covers read-last-hash → append (lines 2400-2434); `verify_chain()` (2445+).
   - **Cost characteristics that matter for shadow volume:** every `log_event` **reads the whole file** to find the last hash (line 2408) → O(n) per append; `MAX_EVENTS = 10000` with periodic trim to the last 10k lines (lines 2270, 2364-2391). A shadow flood would (a) degrade append latency as the file grows toward the cap and (b) **evict real operational audit history** to make room.
   - **Post-trim chain caveat:** after trim, `verify_chain()` seeds from `GENESIS_BLOCK_HASH` (2459), but the first retained event's `previous_hash` points at an evicted event → guaranteed index-0 "predecessor mismatch." Report tooling must tolerate this. `[VERIFIED from code; consequence INFERRED]`
   - **No `agency_id` field.** The `user_id` slot carries heterogeneous values in practice: pipeline events pass `"system"` (`src/analytics/logger.py:347,413,503`), literals like `"operator"`/`"owner"` (`spine_api/server.py:2493`, `persistence.py:2929`), agency IDs as user (`spine_api/services/trip_lifecycle_service.py:186`, `spine_api/routers/messaging.py:61`), or `"public_client"` (`public_proposals.py:713`). **This is the actor-attribution caveat referenced by the E-4 finding: shadow events cannot inherit a trustworthy actor from the ledger — actor fields must be explicit payload members.** `[VERIFIED examples; named as "E-4 caveat" per task brief]`
2. **SQL ledger — `AuditLog` table** (`spine_api/models/audit.py:62-129`) with `AuditContext.log()` (`spine_api/core/audit.py:68-134`): agency-scoped, JWT-resolved agency/user (`audit_logger()`, `core/audit.py:158-209`), RULE_015 chain mirroring the file semantics, controlled `AuditAction` vocabulary (16 actions — includes `RUN_BLOCKED`, `OVERRIDE`; **no authority/gate action exists yet — adding one is additive**).
3. **Bridge — `spine_api/core/audit_bridge.py:39-73`**: sync `audit()` dual-writes file + SQL (Phase 1 of a documented 3-phase migration: Phase 2 moves reads to SQL, Phase 3 retires file writes). **A shadow event written via the bridge rides BOTH chains for free** and survives the file→SQL migration.
4. **Read paths** — `spine_api/routers/trip_observability.py`: `GET /trips/{id}/agent-events` (line 37), `GET /api/trips/{id}/timeline` (line 54; `TimelineEventMapper` maps events by type — a new shadow event type needs an additive mapper entry to surface in the UI timeline; the fallback mapper at lines 106-138 only shows events whose `details` carry `trip_id`), SSE stream `GET /api/trips/{id}/events/stream` (line 148) polls `AuditStore.get_events_for_trip` every second — shadow events with a `trip_id` would stream to the workbench automatically.

**Can a would-be-denial event ride the same chain?** Yes. `AuditStore.log_event` accepts arbitrary `event_type` + structured `details`; the bridge dual-writes both chains. The design below deliberately *partially rides* it (see §3.4 for why the shadow ledger should be separate).

---

## 3. Shadow-mode design

### 3.1 Config flag

`[INFERRED — design recommendation]`

Three-state **env var**, not a boolean — because shadow and enforce must never be confusable and the default must be inert:

```text
AUTHORITY_TIER_MODE = "off" | "shadow" | "enforce"   # default: "off"
```

- **Why env, not RealityTier-linked:** this is an operator safety/kill-switch control over a *platform-wide enforcement posture*, not a per-feature capability claim. The repo's existing precedent for this class of switch is env (`SPINE_API_DISABLE_AUTH`, `TRIPSTORE_BACKEND`, `EXTRACTION_PROVIDER`).
- **Why ALSO RealityTier-registered:** add `authority_tier_gate` to `FEATURE_REGISTRY` (`spine_api/core/feature_gates.py`) at `RealityTier.DETERMINISTIC_PREVIEW` while in shadow, `REAL` only when enforcing — and have the enforce flip assert `can_mutate_booking_state` via `assert_tier_capability` (`spine_api/core/reality_tier.py:112-130`). This keeps the honesty doctrine: the registry says what the system actually does, and the two flags can't drift silently (a startup check fails loudly if `AUTHORITY_TIER_MODE=enforce` while the registry tier disallows mutation).
- Optional per-agency dimming for the future: `details.shadow_enabled_agencies` list inside the settings store — not needed for the first cycle; single-tenant focus.

### 3.2 Evaluation hook — one chokepoint, three binding surfaces

`[INFERRED — design recommendation, surfaces VERIFIED to exist]`

New module `spine_api/services/authority_shadow.py` (additive; no existing route changes required for shadow), exposing:

```python
def evaluate_shadow_authority(
    action_name: str,            # AUTHORITY_CATALOG key
    actor_role: str,             # "agent" | "operator" | "owner" | "public_client" | "agent_ai"
    dual_approver_role: str | None,
    risk_inputs: dict,           # amount_usd, has_non_refundable_deposit, destination_risk_rating, ...
    actor: ActorRef,             # explicit actor fields (see §3.3) — never inferred from ledger
    trip_id: str | None,
    agency_id: str | None,
    run_id: str | None,
    rule_source: str | None,     # e.g. "approval_gates:PROCEED" when bound to NB02 outcome
) -> ShadowVerdict | None        # None when mode=off (zero-cost no-op)
```

It calls the **dormant evaluators verbatim** — `AuthorityGateKeeper.evaluate_action_authority` and, where a wired heuristic exists, `evaluate_autonomy_dispatch_gate` — so the shadow log measures *exactly the code that will enforce*. No shadow-specific rule fork (that would tune a different system than the one that flips).

Binding surfaces, in order of value:

1. **NB02 outcome boundary** — in `src/intake/orchestration.py` immediately after `NB02JudgmentGate` produces the `AutonomyOutcome` (`orchestration.py:451` area). Mapping `[INFERRED, needs sign-off]`: `auto → TIER_0/TIER_1`, `review → TIER_2 (dispatch_proposal_to_client)`, `block → TIER_2+` (escalated). This binds the matrix to 100% of real pipeline traffic from day one of shadow.
2. **Money-adjacent endpoints** (§2.2 table): one line per endpoint calling `evaluate_shadow_authority` before the mutation; in `off`/`shadow` modes the return value is discarded (endpoint behavior unchanged); in `enforce` the same call's `would_deny` becomes the gate.
3. **The dispatch heuristic, when wired** — any future caller of `evaluate_autonomy_dispatch_gate` wraps through the same chokepoint so its verdicts enter the same ledger and the same tuning report.

### 3.3 Event payload

Event type: `authority_tier_shadow_evaluated`. Written through `audit_bridge.audit(...)` so it lands on both chains. `changes`/`details` schema:

```jsonc
{
  "shadow": true,                          // never absent — makes the event self-identifying
  "action_name": "dispatch_proposal_to_client",
  "tier_required": "TIER_2_OPERATOR_SIGNOFF",
  "tier_observed": "TIER_0_AUTONOMOUS",    // effective authority the actor/process actually held
  "would_deny": true,
  "deny_reasons": ["HIGH_TRANSACTION_VALUE"],
  "matrix_allowed": false,                 // AuthorityGateKeeper.evaluate_action_authority result
  "dual_approval_required": false,
  "risk_inputs": {                          // the dispatch-gate inputs, when applicable
    "amount_usd": 12400.0,
    "has_non_refundable_deposit": true,
    "destination_risk_rating": "LOW",
    "unverified_suppliers_count": 0
  },
  // E-4 actor caveat: attribution is explicit, never inherited from ledger user_id
  "actor_kind": "ai_pipeline" | "human_operator" | "public_client",
  "actor_id": "<user id or run id>",
  "actor_role": "agent",
  "rule_source": "approval_gates:PROCEED",  // verbatim from AutonomyOutcome when bound to NB02
  "trip_id": "...", "agency_id": "...", "run_id": "...",
  "sampled": false,                         // true when this allow was logged under sampling
  "eval_source": "authority_gatekeeper_v1"  // which evaluator produced the verdict
}
```

Rationale per the E-4 caveat `[VERIFIED problem, INFERRED remedy]`: because the file ledger's `user_id` slot is semantically overloaded (§2.3), the shadow payload carries `actor_kind/actor_id/actor_role` explicitly so the weekly report can split AI-initiated from human-initiated attempts — the single most important cut for "is the matrix denying the right actor?" SQL-side, `agency_id` also goes into the real column via the bridge.

### 3.4 Volume & cost caps (the "shadow events cost money" risk)

`[INFERRED]` Costs, concretely: the shadow evaluation itself is deterministic and free (no LLM). The real costs are (a) **audit I/O** — each file `log_event` is an O(n) read + fsync under a global lock; (b) **ledger eviction** — the 10k trim will happily evict real operational history to make room for shadow spam; (c) **UI noise** — any `trip_id`-bearing event streams into workbench timelines via SSE. Cap design:

1. **Separate shadow ledger file, `events_shadow.jsonl`, own hash chain, own `MAX_EVENTS` (e.g. 50k)** — *not* the operational chain. A subclassed `AuditStore`-style writer (`ShadowAuditStore`) reusing the same chain math. This is the single most important cap: shadow volume can never evict `events.jsonl` history, and the O(n)-read cost applies to a file that only shadow writes touch. The chain is still tamper-evident and independently `verify_chain()`-able.
2. **Asymmetric logging:** log **100% of would-deny events** (they are the signal and will be rare); **sample allows** at a configurable rate (default 10%) just enough to compute a deny-rate denominator; **never log** `mode=off` evaluations (function returns `None` before any I/O).
3. **Hard per-process rate cap:** `SHADOW_MAX_EVENTS_PER_HOUR` (default 500) enforced by a trivial counter; when exceeded, only would-denies pass. Prevents pathological loops (e.g. a retry storm hitting an endpoint with the hook) from doing the eviction/latency damage described above.
4. **Amount threshold filter for allow-sampling** (optional, default off): `SHADOW_ALLOW_SAMPLE_AMOUNT_MIN_USD` — if set, allow-events below the amount are never logged even within the sample, since low-value allows are the least informative rows.
5. **SQL side cap:** dual-write the would-deny subset only (the `audit()` bridge call is made conditionally), keeping AuditLog row growth proportional to the signal, not to traffic.
6. **Denoise the UI:** shadow events do **not** carry a mapper entry in `TimelineEventMapper` during the shadow cycle (they stay report-visible, workbench-invisible); flipping on a timeline badge is a deliberate later task.

### 3.5 What enforcement mode reuses

In `enforce`, the identical `evaluate_shadow_authority` call returns the verdict and the *endpoint/pipeline* acts on it (403 / escalate to review), while the same event is logged with `shadow: false`. Zero new evaluator code at flip time — the flip is a config change plus the decision-consumption if-branch that ships dormant from day one.

---

## 4. Report / query design (what the weekly review reads)

`[INFERRED — tool spec]` New reusable CLI: `tools/authority_shadow_report.py` (per the reusable-tools doctrine; documented in `tools/README.md`).

Input: `events_shadow.jsonl` (+ SQL AuditLog for the would-deny subset), `--window 7d`, `--agency <id>`.

Output (markdown + JSON):

1. **Denial counts by rule and action** — `would_deny` grouped by `deny_reasons[]` × `action_name` × `tier_required` × `actor_kind`. Headline: "the matrix would have blocked N actions this week; M of them were AI-initiated."
2. **False-positive candidates** — would-deny events where the action subsequently completed anyway (correlate by `trip_id` with operator `OVERRIDE` / proceed events in the operational ledger, and with `advisor_override=true` heuristics). Each is a named review item: "operator proceeded despite HIGH_TRANSACTION_VALUE at $10.2k — threshold or rule wrong?"
3. **Threshold tuning signals** — for `HIGH_TRANSACTION_VALUE`: a histogram of denied `amount_usd` around the $10k ceiling (a mass in $10k–$12k ⇒ ceiling too low); for destination risk: deny rate per rating bucket; for dual-control: projected Tier-4 approval demand per week (ops-staffing signal).
4. **Deny-rate denominator** — allows-sampled counts by action ⇒ would-deny rate per action on legitimate flows, the number the flip criteria (§5) read.
5. **Ledger health** — `verify_chain()` on the shadow ledger (tolerating post-trim genesis mismatch per §2.3), events/hour vs cap, sampled fraction.
6. **Matrix drift check** — deny verdicts from `eval_source` runs across the cycle; a change in distribution with unchanged code flags an upstream input change (e.g. amounts inflating).

All six are derivable from the §3.3 payload with no joins beyond trip_id/time correlation against the operational ledger.

---

## 5. Rollout + flip criteria

`[INFERRED — proposed ladder]`

**Phase 0 — Shadow on (one release cycle, target 2–4 weeks of traffic).**
Ship `authority_shadow.py`, the three bindings, caps, and the report tool with `AUTHORITY_TIER_MODE=shadow` as the committed default for the dev environment. Endpoint behavior provably unchanged (tests assert identical responses with mode on/off).

**Phase 1 — Tune (in shadow).**
Run the weekly report each cycle. Adjust the catalog/actors/mappings only where the report names a false-positive class: e.g. raise/lower the $10k ceiling, move an endpoint's tier, add `advisor_override` semantics, fix actor attribution gaps. Tuning edits are code changes with tests — not silent ledger edits.

**Phase 2 — Enforce flip.**
`AUTHORITY_TIER_MODE=enforce` + `FEATURE_REGISTRY` tier → `REAL`. Flip criteria (all must hold over the full tuning window):

- **Would-deny rate on legitimate flows < 1%** for the cycle, and < 0.1% for TIER_0/TIER_1 actions (these should essentially never fire). `INFERRED numbers — the exact X is a decision point, see §7.`
- **Zero unresolved false-positive candidates** from §4.2 (each either fixed by Phase-1 tuning or explicitly accepted in writing).
- **Deny reasons trace to code:** every observed `deny_reasons` value maps to a shipped rule; no verdicts from stale `eval_source`.
- **Actor attribution complete** for ≥ 95% of events (the E-4 caveat is closed in practice, not just in schema).
- **Chain health:** shadow ledger `verify_chain` clean; report tooling deterministic across two consecutive runs.
- **Rollback story rehearsed:** flipping back to `shadow` mid-cycle must be a one-env-var restart with no data migration (verified by a test, not asserted).

**Residual risk register** (in addition to cost caps in §3.4): `[INFERRED]`

- The in-memory token store (`BoundaryEngine._tokens`) means enforce-mode revocation semantics are process-local until persistence exists — enforcement should bind to tier/role checks first, token-revocation checks later, and the flip review must state this explicitly.
- Shadow adds one synchronous ledger write per would-deny inside request paths; the per-hour cap + separate file bound this, but the enforce flip should re-measure p95 latency of the bound endpoints (pyinstrument pass per repo profiling doctrine).

---

## 6. Sized next tasks

| # | Task | Size | Notes |
|---|---|---|---|
| T1 | `spine_api/services/authority_shadow.py` — evaluator chokepoint calling `AuthorityGateKeeper` + dispatch heuristic; 3-state env flag; startup consistency check vs `FEATURE_REGISTRY` | M (~0.5d) | Pure additive; `off` path is a no-op |
| T2 | `ShadowAuditStore` (`events_shadow.jsonl`, own chain, caps §3.4.1–3) + would-deny-only dual-write via bridge | M (~0.5d) | Reuses chain math; independent `verify_chain` |
| T3 | Bindings: NB02 outcome hook (`orchestration.py`), 5–6 money-adjacent endpoints (§2.2 table); tests asserting shadow-mode response-identity | M (~0.5–1d) | The response-identity test suite is the enforce-flip safety net |
| T4 | `tools/authority_shadow_report.py` + `tools/README.md` entry | M (~0.5d) | §4 report; JSON + markdown |
| T5 | First shadow cycle + weekly report runs; Phase-1 tuning decisions | 1 release cycle | Needs live traffic; dev-environment default `shadow` |
| T6 | Enforce-flip branch (decision consumption at bound points) + flip-criteria test | S (~0.25d) | Ships dormant in T1–T3 |

Dependency order: T1 → T2 → T3 → T4 → T5 → T6. Nothing here touches existing routes' behavior in `off`/`shadow`.

---

## 7. Decision needed

1. **Tier mapping for NB02 outcomes** (`auto/review/block` → TIER_0/2/2+). §3.2's mapping is inferred, not derived from any doc of record. Without sign-off, the shadow report's headline numbers are provisional.
2. **Separate shadow ledger vs riding `events.jsonl`.** This doc recommends a separate chain (§3.4.1) purely because of the 10k-trim eviction math `[VERIFIED]`. If the team prefers one unified ledger (simpler mental model, one `verify_chain`), the trim cap must be raised and the eviction risk accepted — that is a data-retention decision, not an implementation detail.
3. **Flip threshold X** (§5: proposed <1% would-deny on legitimate flows, <0.1% on Tier-0/1). Business tolerance for blocking a $12k auto-dispatch is a product call, not an engineering call.
4. **Is `evaluate_autonomy_dispatch_gate` wired at all before matrix adoption?** It is currently unwired `[VERIFIED]`. If the answer is "never — the NB02 policy gate supersedes it," shadow mode should bind only the policy gate + endpoints, and the heuristic should be archived per the supersession workflow rather than tuned. The shadow cycle doubles as the evidence either way.
5. **Endpoint auth gap while we're here:** `GET /tokens/{token}/verify` has no auth dependency (`spine_api/routers/boundaries.py:70`) — fine for token verification semantics, but worth an explicit decision before enforce mode elevates the boundaries surface's importance. Flagged, not blocked on.

---

*Verified against: `src/schemas/boundary_contracts.py`, `src/services/boundary_engine.py`, `spine_api/routers/boundaries.py`, `spine_api/services/autonomy_gates.py`, `src/intake/gates.py`, `src/intake/orchestration.py`, `spine_api/contract.py`, `spine_api/persistence.py` (AuditStore), `spine_api/models/audit.py`, `spine_api/core/audit.py`, `spine_api/core/audit_bridge.py`, `spine_api/core/reality_tier.py`, `spine_api/core/feature_gates.py`, `spine_api/routers/trip_observability.py`, `spine_api/routers/{messaging,public_proposals,price_lock,financial_settlement,subagent_payouts,trip_lifecycle}.py`, `tests/test_boundary_engine.py`, `tests/test_intelligence_and_governance.py`, `Docs/exploration/MASTER_FINDINGS_TASKS_INVENTORY_2026-09-02.md`, `Docs/exploration/C02_WIRE_OR_ARCHIVE_DOSSIERS_2026-09-02.md`.*
