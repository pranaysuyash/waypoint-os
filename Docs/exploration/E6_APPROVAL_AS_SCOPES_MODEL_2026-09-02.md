# E6 — Approval-as-Scopes: From One Approval Event to a Permission-Set Model

**Date:** 2026-09-02 (file written 2026-09-04; all path:line citations re-checked against the working tree on that date)
**Type:** EXPLORE (read-only research + design doc; no implementation performed)
**Series:** E-wave companion docs — depends on **E4** (actor identity binding, `Docs/exploration/E4_ACTOR_IDENTITY_BINDING_F03_2026-09-02.md`) for grantor provenance; complements **E7** (AuthorityTier shadow mode, `Docs/exploration/E7_AUTHORITYTIER_SHADOW_MODE_DESIGN_2026-09-02.md`) which owns the *tier posture* binding. E6 owns the *content of the grant* — what the customer actually approved.
**Convention:** `[VERIFIED]` = read directly from code/docs at the cited path in this pass. `[INFERRED]` = design judgment or extrapolation from verified facts, flagged inline.

---

## 1. The Question

The current approval model is **one boolean event per quote**: "customer approved." The outsider design review (L8 in `Docs/TPM_TRAINING_BLUEPRINT_PRODUCT_MAPPING_2026-09-01.md`) states the principle: **CHECK ≠ RESERVE ≠ PURCHASE** — cost-of-mistake determines autonomy. A real approval is not a state, it is a **permission set**:

> approved *for this airline*, *up to this fare ceiling*, *reserve-not-purchase*, *hotel-category-only*, *subject-to-cancellation*, *verbal-but-payment-pending*.

A single approval state falsely implies that **all** downstream actions are authorized. The design question:

> Should customer approval be re-modeled as **scoped grants** (dimension × bound × condition), and does that scope model — and only that scope model — make the dormant `AuthorityTier` matrix meaningful? An unenforceable tier with no lifecycle scope context is decoration; a tier evaluated *against a specific grant* is an authority system.

**Hypothesis to test (stated up front):** the repo already contains every primitive of a scope model — a dormant 6-scope capability enum, an in-memory token engine, a per-traveler payment splitter, a capability list on proposal links — but no place where a *grant* is written at approval time and *read* at action time. The gap is a missing caller, not a missing module (same verdict as TPM mapping §3).

---

## 2. Current State — Approval Surfaces and Their Consumers

### 2.1 The six disjoint approval-adjacent vocabularies `[VERIFIED]`

There is no single "approval" surface. There are **six** independent records that each encode a fragment of approval, keyed by the same `trip_id`, none referencing each other:

| # | Surface | What it encodes | Where | Lifetime/consumer |
|---|---|---|---|---|
| 1 | **Quote/negotiation status** `OPEN \| NEGOTIATING \| WON \| LOST` | Supplier-side negotiation outcome per supplier bid. Not a customer approval at all — it records whether *we won the price*. | `spine_api/contract.py:53-61` (`NegotiationLog.status`, the "quotes model" at :56); `src/intake/packet_models.py` mirrors the Literal | Presentation only; no consumer gates on `WON` `[VERIFIED: no non-presentation reader found]` |
| 2 | **Owner `review_status`** `pending/approved/rejected/escalated/revision_needed/recovery/resolved` | Internal owner sign-off that a trip is fit to deliver. On `approved`, the trip flips to `status="delivered"` and a mock feedback email fires. | `src/analytics/review.py:22` (`VALID_ACTIONS`), :99-108 (approve→delivered), :84-94 (`review_metadata.reviewed_by`, `owner_approved`); queue gating at `src/analytics/policy_rules.py:91`; escalation at :151 | Dashboard counts (`src/services/dashboard_aggregator.py:133-145`); judge scorer (`src/evals/judge/scorer.py:140`); recovery agent (`src/agents/recovery_agent.py:323`) |
| 3 | **Senior-planner high-value sign-off** `review_decision == "APPROVED"` | Operator gate for quotes ≥ $10,000, read from `packet.budget_max`. The approving human is **client-supplied** (`trip["reviewer_id"] = body.reviewer_id`) — F-03. | `spine_api/routers/team_workflows.py:116-145` (gate), :86 (`reviewer_id`), :91-100 (audit `user_id=agency_id`, not the human) | Read back by the same gate endpoint; `[INFERRED]` no frontend consumer of `high-value-gate-check` found in `frontend/src` |
| 4 | **Customer proposal acceptance (e-sign)** | One-shot binary accept: `signer_name`, `signer_email`, `e_signature_consent` → `status="accepted"`, audit `proposal_accepted` with `total_price_usd`. Option selection (pricing) and acceptance (consent) are separate calls — accepting does **not** capture per-option grants. | `spine_api/routers/public_proposals.py:89-93` (`AcceptProposalRequest`), :660-709 (`accept_proposal`; consent check :705-709; audit :713-727) | Acceptance state lives in the **process-local** `_PROPOSAL_REGISTRY` (:100); the durable record is the audit event only `[VERIFIED]`. No downstream booking/payment consumer `[VERIFIED: none found]` |
| 5 | **Traveler acceptance intent (1-click)** | Unauthenticated "acceptance intent": sets `trip["proposal_accepted_by_traveler"]=True`, `proposal_acceptance_intent="PROPOSAL_ACCEPTED_INTENT"`, explicitly "without illegally mutating booking stage". | `spine_api/routers/trust_scorecard.py:349-379` | Trip record; no enforcement consumer `[VERIFIED: none found]` |
| 6 | **Corporate policy override** `corporate_policy_override.approved_by` | Free-text approver name for policy exceptions (VP approval for business class <6h, hotel cap overruns) — F-03 again, and (per E4 §2.1) these routes have **no JWT dependency at all**. | `spine_api/routers/corporate_policy.py:122-128`, :143-148; validator `spine_api/services/corporate_policy.py:26-89` | Stored on trip; no scoped bound (e.g. "business class OK on this one leg only" is not representable) |

### 2.2 The dormant scope machinery `[VERIFIED]`

| Primitive | Location | State |
|---|---|---|
| `AuthorityTier` TIER_0_AUTONOMOUS … TIER_4_DUAL_CONTROL | `src/schemas/boundary_contracts.py:26-33` | **Zero pipeline callers** (callers: own module, `spine_api/routers/boundaries.py`, `tests/test_boundary_engine.py` only — verified by `rg` across `spine_api/`, `src/`, `tests/`) |
| `CapabilityScope`: `VIEW_ONLY, PROPOSE_EDIT, ACCEPT_QUOTE, AUTHORIZE_PAYMENT, OVERRIDE_SUPPLIER, ISSUE_REFUND` | `src/schemas/boundary_contracts.py:35-43` | Same — no caller outside the boundary engine |
| `ScopedCapabilityToken` (HMAC-SHA256, `traveler_role: primary_booker \| companion \| guest`, `allowed_scopes`, `expires_at`, `revoked`, `metadata`) | `src/schemas/boundary_contracts.py:57-70`; engine `src/services/boundary_engine.py:110-223` | Issue/verify/revoke implemented + tested; **token store is an in-memory dict** (`self._tokens`, `boundary_engine.py:41`) — lost on restart (E7 §2.1) |
| Bootstrap boundary contracts (`bc_client_accept_quote` → TIER_3/ACCEPT_QUOTE, `bc_client_payment` → TIER_3/AUTHORIZE_PAYMENT, `bc_operator_refund_dual` → TIER_4/ISSUE_REFUND) | `src/services/boundary_engine.py:52-100` | Nothing evaluates them at runtime |
| `AuthorityGateKeeper.AUTHORITY_CATALOG` — 9 actions incl. `dispatch_proposal_to_client` TIER_2, `commit_supplier_price_lock` TIER_2, `accept_travel_agreement`/`authorize_credit_card_charge` TIER_3, `issue_refund_above_threshold` TIER_4 dual | `src/services/boundary_engine.py:233-281` | `evaluate_action_authority` called only from tests |

### 2.3 The gate landscape — with one framing correction `[VERIFIED, per E7 §2.2]`

- `evaluate_autonomy_dispatch_gate` (`spine_api/services/autonomy_gates.py:30-109`): heuristic over `(total_package_usd ≥ 10_000 → HIGH)`, non-refundable deposit → MEDIUM, destination risk → HIGH, unverified suppliers → HIGH; any HIGH or ≥2 factors → `ADVISOR_REVIEW_REQUIRED`. **Zero production callers** — only `tests/test_intelligence_and_governance.py:66,76`. "Live" means living/tested code, not in the request path.
- The **actually-live** autonomy gate is NB02: `NB02JudgmentGate.evaluate()` (`src/intake/gates.py:156-253`) → `AutonomyOutcome` (`src/intake/gates.py:48-66`: `raw_verdict`, `effective_action ∈ {auto, review, block}`, `approval_required`, `rule_source` e.g. `approval_gates:PROCEED`, :238; STOP_NEEDS_REVIEW invariant :208-213), driven by per-agency `approval_gates` settings, surfaced in `SpineRunResponse.autonomy_outcome` (`spine_api/contract.py:42-50,132`).
- **Critical observation for this doc:** both gates evaluate *risk posture*, never *customer intent*. NB02 knows nothing that the traveler said yes to; the $10k heuristic is a global constant, not the customer's own bound.

### 2.4 An embryonic scope vocabulary that already exists `[VERIFIED]`

Two fragments prove the concept is latent in the codebase:

1. Proposal-link capabilities: `capabilities = ["view_itinerary", "accept_quote", "request_change"]` + optional `"select_room_upgrades"` (`spine_api/routers/trust_scorecard.py:261-263`). This is a per-token scope list — but it is **advisory metadata**; no endpoint checks it before accepting or recalculating `[VERIFIED]`.
2. Per-traveler payment shares: `TravelerPaymentShare(traveler_id, name, share_amount_usd, paid_amount_usd, payment_link_token, …)` (`spine_api/services/group_payments.py:13-34`). Payer identity per component of the bill already exists — the "someone else pays" primitive — but no approval is attached to a share.

### 2.5 Downstream consumers of "approval" today `[VERIFIED]`

| Consumer | What it consumes | What a scoped model would give it |
|---|---|---|
| Booking confirmations (operator-recorded): per-component `draft → recorded → verified/voided` with `recorded_by/verified_by/voided_by` | Nothing from approval — an operator can record a booking confirmation regardless of what (or whether) the customer accepted | A check: *does an active grant cover this component, this action class, this amount, at this time?* (`spine_api/services/confirmation_service.py:262, 318-319, 176-181`) |
| Payment queue / refunds | `PAYMENT_STATUSES`, `REFUND_STATUSES` incl. refund `"approved"` (`spine_api/services/payment_queue_service.py:11-45`) — note this "approved" is a **payments-ops workflow state**, unrelated to customer consent | Link each movement to the mandate that authorized it (F-04's ledger requirement) |
| Split deposits + `subagent_payouts.py` | Nothing — money moves with no consent artifact chained to the audit hash (F-04, `Docs/review/FINDINGS_REGISTER_2026-08-31.md:81`) | Grant-as-mandate: payer, amount, counterparty bound per movement |
| Proposal dispatch (NB02 + future dispatch gate) | Risk posture only | Customer ceiling replaces the global $10k constant: *autonomy within the grant, review outside it* |
| Freshness recheck | Price-lock sentinel exists (72h, `src/decision/price_lock.py`) with "no approval→execution binding" (TPM mapping L12) | Grants carry `expires_at` + recheck-before-purchase conditions; L12's missing binding is exactly a grant field |

### 2.6 Summary verdict

**The implicit model today: approval is a verb-less event.** Nothing anywhere records *for what* approval was given, at *what bound*, under *which conditions*, or *until when*; and nothing downstream asks. `[VERIFIED]` The dormant matrix cannot be woken by posture-binding alone (E7's job) because posture answers "who may do this class of thing" while the real-world question is "did *this customer* authorize *this spend* on *this component* under *these conditions*". Both are needed; E6 supplies the second.

---

## 3. Scope Model Design

### 3.1 Vocabulary: Grant = Dimension × Action-Class × Bound × Conditions × Provenance

One **ApprovalGrant** is the atomic unit of customer permission:

```python
class ApprovalDimension(str, Enum):        # the WHAT
    FLIGHTS = "flights"
    HOTELS = "hotels"
    TRANSFERS = "transfers"
    INSURANCE = "insurance"
    ACTIVITIES = "activities"
    TOTAL = "total"                        # aggregate budget ceiling across components

class ApprovalActionClass(str, Enum):      # the HOW-FAR — the CHECK/RESERVE/PURCHASE ladder (L8)
    CHECK = "check"                        # verify price/availability; zero commitment
    RESERVE = "reserve"                    # hold inventory, cancellable, no charge
    PURCHASE = "purchase"                  # money-committed / non-refundable exposure

class ApprovalCondition(str, Enum):        # the STRINGS ATTACHED
    REFUNDABLE_ONLY = "refundable_only"           # no non-refundable rates
    RESERVE_NOT_PURCHASE = "reserve_not_purchase" # force ceiling at RESERVE
    EXPIRES_AT = "expires_at"                     # grant TTL
    RECHECK_BEFORE_ACT = "recheck_before_act"     # bind price-lock sentinel (L12)
    PAYMENT_PENDING = "payment_pending"           # verbal/soft yes; PURCHASE blocked until
                                                  # mandate artifact exists (F-04 hook)
    SPECIFIC_SUPPLIER = "specific_supplier"       # "this airline only"
```

A grant record (storage shape below):

```python
@dataclass(slots=True)
class ApprovalGrant:
    grant_id: str
    trip_id: str
    quote_ref: Optional[str]          # NegotiationLog id or proposal token it came from
    dimension: ApprovalDimension
    action_class: ApprovalActionClass
    bound: Optional[Bound]            # amount_ceiling + currency + per_unit|aggregate;
                                      # class/cabin/category bound (e.g. "4-star max")
    conditions: list[ApprovalCondition]
    condition_payload: dict           # e.g. expires_at ISO, supplier name
    granted_by: ActorIdentity         # E4: JWT-subject-bound human/traveler, artifact hash
    granted_to: ActorPrincipal        # who may act: agency agent | AI dispatcher | traveler_role
    channel: str                      # e_sign | wa_message | call_transcript | portal_click
    status: str                       # active | consumed | expired | revoked | superseded
    consumed_by: list[str]            # audit-event ids that spent this grant
    created_at: str
```

**Semantics (all `[INFERRED]` design rules):**

- **Grants are additive and specific-beats-general.** A `TOTAL/PURCHASE/₹90k` grant plus `HOTELS/CHECK` grant means hotels may be checked but only purchased within the ₹90k remainder. A `REFUNDABLE_ONLY` condition on any covering grant blocks a non-refundable booking even if another grant would allow it (most restrictive wins — approval is permission, not obligation).
- **Action classes are a ladder with monotone cost.** `CHECK ⊂ RESERVE ⊂ PURCHASE` in exposure; autonomy posture per class maps 1:1 onto AuthorityTier (§3.4). A grant ceiling at RESERVE (`reserve_not_purchase`) makes PURCHASE *structurally impossible*, not merely discouraged — the invariant lives in the validation layer, not in prompts (Champion inversion, TPM mapping §3).
- **Spending is first-class.** `consumed_by` turns a grant into an auditable budget: "the hotel grant was spent by audit event X on date Y." This is what makes TIER_2/3/4 evaluation *traceable* rather than decorative.

### 3.2 Storage shape

`[INFERRED]`, constrained by verified repo facts:

- **Attach grants to the trip record** as `trip["approval_grants"]: list[dict]` (both `FileTripStore` and SQL store already round-trip arbitrary trip analytics/dicts — `[VERIFIED]` pattern: `review_metadata`, `corporate_policy_override` are stored the same way). This avoids a new store while the model is young; promotion to a first-class table mirrors the E2 JSONB migration path (`Docs/exploration/E2_ANALYTICS_JSON_TO_JSONB_MIGRATION_2026-09-02.md`) once querying by grant is real.
- **Write grants at every existing approval surface** (§2.1 surfaces 2–6), do **not** remove the legacy fields — legacy booleans become *derived views* computed from grants during the compat window (additive-first per AGENTS.md Code Preservation; supersession documented when retirement is approved).
- **Provenance via E4, not parallel:** `granted_by` must be the E4 actor identity (authenticated JWT subject + artifact-version hash), because a scope model with self-asserted grantors is a forgery surface with a nicer schema — F-03 closed *through* the grant writer, not beside it.
- **Durable by construction:** unlike `_PROPOSAL_REGISTRY` (process-local, `public_proposals.py:100`) and the boundary engine's in-memory token dict (`boundary_engine.py:41`), grants live on the trip record and survive restarts/replicas. Where a `ScopedCapabilityToken` is issued (CLIENT_DELEGATED zone), its `allowed_scopes`+`metadata` are *derived from* active grants at issue time — the grant is the source of truth, the token is transport.
- **Audit linkage:** every grant write/consume emits through the existing hash-chained `AuditStore` (`spine_api/models/audit.py:99-105`, per TPM L16) with `consumed_by` pointing at audit event ids.

### 3.3 Enforcement points — which gate reads which scopes

| EP | Surface | Reads | Enforces |
|---|---|---|---|
| EP-1 | Proposal accept endpoints (`public_proposals.py:660-709`, `trust_scorecard.py:349-379`) | — (writes) | Emits grants per accepted option + trip-level ceiling; replaces boolean accept |
| EP-2 | NB02 judgment gate (`src/intake/gates.py:156-253`) | `dimension/action_class` vs requested action | Auto-proceed only *within* active grants; anything uncovered keeps today's review/block posture. This is the **live** gate, so it is the first honest reader `[INFERRED — sequencing judgment, per E7's correction]` |
| EP-3 | Dispatch heuristic (`spine_api/services/autonomy_gates.py:30`) when wired | `bound.amount_ceiling` (replaces global $10k constant), `conditions.REFUNDABLE_ONLY` (sharpens the non-refundable MEDIUM into per-grant logic), `expires_at` | Autonomy ceiling becomes *the customer's own bound*, per component |
| EP-4 | High-value operator gate (`team_workflows.py:116-145`) | grants + tier catalog | Operator sign-off *binds scopes* ("approved for dispatch" becomes "approved for dispatch of X under grant Y") — and its `reviewer_id` becomes E4-bound |
| EP-5 | Booking confirmation record/verify (`confirmation_service.py:226-330`) | `action_class` (RESERVE/PURCHASE), `dimension`, `bound`, `status`, `consumed_by` | A confirmation for an uncovered component is rejected or downgraded to draft-with-warning |
| EP-6 | Payment movement points (`payment_queue_service.py`, `group_payments.py`, `subagent_payouts.py`) | `granted_by` vs payer share; `PAYMENT_PENDING` condition | Deferred behind F-04 mandate ledger — see §6 |

### 3.4 Map to AuthorityTier / CapabilityScope — extend, not replace

**Verdict: extend.** `[INFERRED, but strongly constrained by verified structure]`

- `AuthorityTier` is **orthogonal and necessary**: it answers *who/what posture may execute* (agent, operator sign-off, client authorization, dual control). Grants answer *what the customer authorized*. An action is allowed iff **tier posture permits the actor AND an active grant covers the content**. Neither alone is sufficient: a TIER_3 posture without a grant is an invitation to invent customer consent; a grant without tiers lets an agent execute a TIER_4 dual-control action on a fully-scoped approval.
- `CapabilityScope` (6 flat verbs) becomes the **coarse projection** of grants: `ACCEPT_QUOTE ≙ dimension∈{TOTAL} ∧ action_class∈{PURCHASE}` etc. Keep the enum for zone-transition contracts (they need coarse verbs); do **not** try to express ceilings/conditions in it — that would require breaking the enum's shape. `ScopedCapabilityToken.metadata` already exists as the free-form carrier for the grant projection (`boundary_contracts.py:57-70`) — no schema break.
- `AUTHORITY_CATALOG` gains **grant-aware entries** rather than new tiers: e.g. `commit_supplier_price_lock` (TIER_2 today, `boundary_engine.py:254-258`) evaluates as "TIER_2 posture ∧ active RESERVE-or-higher grant on that dimension". The CHECK/RESERVE/PURCHASE ladder maps onto TIER_0/2/3 respectively `[INFERRED mapping]`, with TIER_4 (refunds, safety overrides) intentionally outside grants — no customer can authorize what requires dual control.
- Nothing in `boundary_contracts.py` is deleted. The enum-and-token layer keeps its current shape; grants are the new lifecycle context that finally gives the tiers something to evaluate. (This is the "unenforceable tier without lifecycle scope context" thesis, answered structurally.)

---

## 4. Worked Examples

*(All three are expressible today in zero places; each maps to specific verified primitives.)* `[INFERRED scenarios, VERIFIED primitives]`

### 4.1 "Book the flights, but keep looking at hotels"

Today: one e-sign accept flips the whole proposal to `accepted` (`public_proposals.py:700-709`); "keep looking" is unrepresentable — the system cannot both commit and continue.

With grants: acceptance writes
`Grant(flights, PURCHASE, ceiling ₹62,000, conditions=[SPECIFIC_SUPPLIER:"IndiGo", RECHECK_BEFORE_ACT])` and
`Grant(hotels, CHECK, ceiling ₹28,000, conditions=[REFUNDABLE_ONLY])`.
EP-2/EP-3 let the agent auto-check hotels indefinitely (CHECK is autonomous, TIER_0 posture), while EP-5 rejects any `recorded` hotel confirmation (PURCHASE not granted). The operator dashboard can render exactly this state: *flights committed, hotels open*.

### 4.2 "Approved ₹90k total — but nothing non-refundable"

Today: `budget_max` feeds a $10k **global** heuristic (`team_workflows.py:127-128`) and `has_non_refundable_deposit` is one MEDIUM flag (`autonomy_gates.py:61-69`); the customer's actual ceiling and refundability constraint are never compared at action time.

With grants: `Grant(TOTAL, PURCHASE, bound={90_000 INR, aggregate}, conditions=[REFUNDABLE_ONLY, EXPIRES_AT:+72h, RECHECK_BEFORE_ACT])`.

- EP-3: package at ₹86k → within bound → the `HIGH_TRANSACTION_VALUE` trigger is evaluated against *the customer's* ceiling, not $10,000.
- A ₹12k non-refundable hotel rate violates `REFUNDABLE_ONLY` → blocked/escalated regardless of remaining budget (most-restrictive rule, §3.1).
- Price drift after 72h: `EXPIRES_AT` + `RECHECK_BEFORE_ACT` gives the price-lock sentinel (`src/decision/price_lock.py`) the approval→execution binding it lacks (TPM L12) — re-lock is no longer blind RMW; it consumes a fresh grant or escalates.

### 4.3 "Wife approved the hotel; husband pays"

Today: e-sign captures one `signer_name/signer_email` pair (`public_proposals.py:89-93`); consent and settlement are conflated. The primitives exist but are unjoined: `ScopedCapabilityToken.traveler_role` (`boundary_contracts.py:57-70`), per-traveler shares (`group_payments.py:13-34`).

With grants: wife (primary_booker) grants `Grant(hotels, PURCHASE, ceiling ₹40,000, conditions=[REFUNDABLE_ONLY], granted_to=agency_agent, …)` plus a **settlement directive**: `payment_settlement_party = husband.traveler_id`.

- EP-6 (when F-04 lands): the payment movement chains to grant_id as its mandate artifact — payer = husband's share row in `group_payments`, consent = wife's grant — closing exactly the "consent artifact not chained to the audit hash" gap F-04 names.
- If instead the husband should also *consent* (not merely pay), he simply holds no grant, and his own e-sign/grant is required — two distinct questions (who approves / who pays) that the single-signer model cannot ask.

---

## 5. Adoption Stages

Follows the agreed doctrine shape for dormant-asset adoption: shadow first, then enforce (TPM mapping §4 deferred table; E7's ladder). Each stage is independently shippable and reversible.

**Stage 1 — Shadow vocabulary (write-only, zero behavior change).** ~1.5–2 d

- Emit `ApprovalGrant` records at all existing approval surfaces (EP-1) alongside legacy fields; legacy booleans/strings remain authoritative.
- A read-only derivation shows what NB02/dispatch **would** decide under grants vs what they did decide; log divergences as `approval_grant_shadow` audit events.
- Register the grant model + one schema unit test. Exit criterion: 2 weeks of shadow events with zero grant-write failures and a divergence report the review can read.

**Stage 2 — Enforce at the dispatch/decision gate.** ~1–2 d *after* E4 identity binding lands (hard prerequisite: grants with self-asserted grantors must never gate).

- EP-2 (NB02) consumes grants: within-grant → auto, uncovered → today's posture. EP-3: `evaluate_autonomy_dispatch_gate` gets wired (per E7) with `bound.amount_ceiling` replacing the $10k constant for trips that carry grants (trips without grants keep the global constant — no behavioral cliff).
- Operator high-value gate (EP-4) binds sign-off to scopes; `reviewer_id` → E4 identity.
- Falsifier tests required: a grant cannot be spent twice without `consumed_by`; expired grants cannot gate auto-actions; REFUNDABLE_ONLY blocks non-refundable confirmation proposals.

**Stage 3 — Enforce per-component at the money/booking edge.** ~2–4 d, connectivity-gated in value

- EP-5: `confirmation_service` record/verify checks grant coverage per component; uncovered confirmations rejected or quarantined to draft.
- EP-6: payment movements chain to grants — **build only when F-04's mandate ledger lands and after the payment-rail negative space (EX-05) is reconciled**; before real rails, this stage enforces only the *recording* discipline, not actual money movement.
- Per-component grant consumption + confirmation staging gives the L13 saga its approval substrate (CONFIRMED/FAILED/NOT_STARTED per component, each tied to a grant).

---

## 6. What Stays Out of Scope

- **Payment execution rails.** Building card capture, ACH, escrow settlement, PCI scope here is explicitly the negative space (EX-05: "deliberately absent capabilities: payment execution, ticketing/GDS, … refund/chargeback flows", `Docs/review/FINDINGS_TASKS_CONSOLIDATED_2026-08-30.md:108`) and is connectivity-gated (NG-02/NG-03 re-open conditions, :115-116). E6 models the *authorization artifact*; it does not move money.
  - **Register-accuracy note:** the task brief labeled payment rails "NG-01". In the canonical registers, NG-01 is the **event-log-as-SSOT no-go** (:114) and NG-03 is the **JIT ticketing scheduler no-go** (:116); payment-rail absence is EX-05's negative-space row. Citing NG-01 for payments in downstream docs would misfile the re-open condition — flagged here so the next writer cites EX-05.
- **Refund/chargeback execution** (same EX-05 row); TIER_4 `issue_refund_above_threshold` remains dual-control and outside customer-grantable scope by design (§3.4).
- **Replacing the review_status / proposal-status vocabularies.** Legacy surfaces persist unchanged through Stages 1–2; retirement follows the Supersession Workflow with field-by-field comparison, not this doc.
- **A new token format.** `ScopedCapabilityToken` stays as-is; grants project into it via `allowed_scopes`+`metadata`.
- **Verbal-approval authentication strength.** `PAYMENT_PENDING` conditions mark soft consent; what evidentiary weight a WhatsApp "yes" carries is an F-04/mandate question, not a vocabulary question.

---

## 7. Sized Next Tasks

| # | Task | Size | Depends on | Register hook |
|---|---|---|---|---|
| 1 | Ratify grant vocabulary (dimension × action-class × bound × conditions) as the canonical approval representation; file register row via `scripts/check_findings_register.py` intake | 0.5 d ⚖ | this doc | new row, decision-gated |
| 2 | Stage 1: grant writer at both accept surfaces + corporate override; `trip["approval_grants"]` storage; shadow audit events; schema tests | 1.5–2 d 🛠 | #1 | same row, stage 1 |
| 3 | E4 actor binding on `granted_by` (joint work package — do not ship #2's enforcement without it) | tracked in E4 | E4 | F-03 (P1) |
| 4 | Stage 2: NB02 + dispatch-gate grant consumption; ceiling-from-grant; falsifier tests; wire dispatch heuristic per E7 | 1–2 d 🛠 | #2, #3 | E7 companion row |
| 5 | Stage 3: confirmation-service per-component enforcement | 2–3 d 🛠 | #4 | L13 saga row |
| 6 | Grant↔mandate ledger binding for payment movements (EP-6) | deferred | F-04, EX-05 reconciliation | F-04 (P1) |

Sequencing note: #1–#2 are safe now (write-only, additive). #4+ change live gate behavior and must ride E7's shadow corpus so the grant model and tier matrix are tuned from the same evidence base.

---

## 8. Decision Needed

1. **Adopt approval-as-scopes as the canonical approval model** — grants as source of truth, existing booleans/statuses as derived views during a compat window? (Alternatives: keep event-per-quote and bolt per-option checks onto the proposal accept — rejected here because it cannot express ceiling/condition/expiry and leaves the matrix unbound.)
2. **Extend, don't replace, `CapabilityScope`** — coarse enum stays for zone contracts; full expressiveness lives in `ApprovalGrant`; tokens carry projections via `metadata`. Confirm no parallel enum is wanted.
3. **Confirm the enforcement order**: Stage 2 lands at NB02 (the live gate) first, dispatch heuristic second — inverse of the intuitive order, justified by E7's finding that the dispatch gate has zero production callers.
4. **Hard prerequisite sign-off**: no grant *enforcement* (Stages 2+) ships before E4/F-03 identity binding, since a scope model with self-asserted grantors upgrades the existing honesty defect into a forgery surface.
5. **Correct the register citation** for payment-rail out-of-scope: EX-05 (not NG-01) per §6.
