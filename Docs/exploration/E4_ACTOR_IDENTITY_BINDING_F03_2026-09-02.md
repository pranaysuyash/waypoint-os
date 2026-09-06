# E4 — Actor Identity Binding on Provenance/Audit Surfaces (jointly with F-03)

**Date:** 2026-09-02 (written 2026-09-04)
**Type:** EXPLORE (read-only research; no implementation)
**Tracks:** F-03 in `Docs/review/FINDINGS_REGISTER_2026-08-31.md` ("`team_workflows`/`corporate_policy` store client-supplied signoff; who-authorized is self-asserted", **open**, P1)
**Scope:** FastAPI spine_api + src/. Every claim below is marked **[VERIFIED]** (read from code at the cited path) or **[INFERRED]** (reasoned from verified facts).

---

## 1. The Question

This wave shipped actor-labeled trails that are all **self-asserted**: the client tells the server who performed an action, and the server records the claim as fact. The design question:

> What is the design for binding actors to JWT-subject + artifact-hash, built **jointly** with F-03's approval-identity fix — never separately?

The "never separately" constraint is the point: fixing F-03 by merely swapping `body.reviewer_id` for `membership.user_id` in one router leaves the same defect in four other surfaces, and adding artifact signing without fixing the identity source signs a lie. They are one work package.

---

## 2. Current State — Self-Asserted Surface Map

All paths relative to repo root. All **[VERIFIED]** with file:line.

### 2.1 Money-touching signoffs (F-03 core)

| Surface | What is stored | Source | Cite |
|---|---|---|---|
| `POST /api/v1/team/review-signoff` | `trip["reviewer_id"] = body.reviewer_id` into trip JSON | request body (`ReviewSignoffRequest.reviewer_id: str`, required) | `spine_api/routers/team_workflows.py:86`; contract `spine_api/contract.py:1507-1511` |
| same | audit event `user_id=agency_id` — the agency UUID, not the human | `AuditStore.log_event(..., user_id=agency_id)` | `spine_api/routers/team_workflows.py:91-100` |
| `POST /api/v1/corporate/approve-policy-override/{trip_id}` | `trip["corporate_policy_override"]["approved_by"] = body.approver_name` — a free-text **name**, not even an ID | request body (`OverrideRequest.approver_name: str`) | `spine_api/routers/corporate_policy.py:123-128` |
| same | audit `user_id=agency_id`, details include `approver_name` | `AuditStore.log_event(...)` | `spine_api/routers/corporate_policy.py:132-140` |

**Adjacent finding (worse than self-assertion) [VERIFIED]:** both `corporate_policy` routes take identity/tenancy from `X-Agency-ID` header with `TEST_AGENCY_ID` fallback and have **no JWT dependency at all** (`spine_api/routers/corporate_policy.py:59-65, 110-117`). `auth.py` explicitly documents that `X-Agency-ID` is respected only under pytest/auth-bypass (`spine_api/core/auth.py:182-186`); `corporate_policy.py` does not gate on that condition. An unauthenticated caller can approve a policy override for any agency id it names. This is adjacent to F-03 and should close in the same package.

### 2.2 Trip packet field provenance (optimistic-sync)

- `POST /inbound/optimistic-sync/{trip_id}` records `_field_provenance[field] = {actor, actor_id, at, superseded}` where `actor_id` comes from `body.actor_id` and `actor` (precedence role) from `body.actor_role` — both client-supplied **[VERIFIED]**: `spine_api/routers/inbound.py:304-310`, `spine_api/contract.py:1340-1355`, `spine_api/services/field_merge.py:224-229`.
- The audit event repeats the self-assertion: `"actor": body.actor_id or "agency_agent"` (`inbound.py:398-399`), with `user_id=agency_id` (`inbound.py:391`).
- Consequence: the merge-precedence engine (`field_merge.py:177-219`) — which decides whether a *customer* may overwrite an *operator's* commercial value — trusts the client's declaration of which side it is. A caller declaring `actor_role="operator"` gets operator precedence. **[VERIFIED]** mechanism; forgery risk is **[INFERRED]** but direct.
- The `/parse` route hardcodes actor labels `"agent"` / `"chrome_extension" if body.channel == "chrome_extension" else "agency_agent"` (`inbound.py:143, 227`) — not self-asserted per se, but fabricated rather than JWT-derived **[VERIFIED]**.

### 2.3 Status history — actor-less by design

- `record_status_transition` appends `{from, to, at}` only (`spine_api/core/trip_status.py:108-128`); the SQL store seeds/folds the same three-key shape into `analytics._extra.status_history` (`spine_api/persistence.py:53-67, 1274-1331`). No actor field exists anywhere in the chain **[VERIFIED]**. This is a *gap*, not a lie: the trail says what changed but can never say who.

### 2.4 Audit events — agency-substituted identity

- The sync bridge writes `AuditLog(agency_id=..., user_id=user_id or "system", ...)` (`spine_api/core/audit_bridge.py:39-73, 140-150`). Callers throughout pass `user_id=agency_id` (team_workflows, corporate_policy, inbound above; also `spine_api/routers/customer_memory.py:413` passes `actor_id=agency_id` into memory provenance). So the audit trail's `user_id` column routinely holds a **tenant id**, making "who did it" unrecoverable from the audit table alone **[VERIFIED]**.

### 2.5 Other actor-bearing envelopes (noted, out of F-03 blast radius)

- `product_b_events.py:66-77` and `spine_api/routers/public_checker.py:36-48` accept client-supplied `actor_id`/`actor_type` in traveler-facing event envelopes; `public_checker` is an unauthenticated public endpoint by design **[VERIFIED]**. Traveler-side identity is a separate (currently unsolved) problem — see Decision Needed §8.
- `spine_api/services/confirmation_service.py:290-536` and `booking_task_service.py` accept `created_by/updated_by/verified_by/voided_by/completed_by` parameters — but their **router callers already bind these to the JWT membership** (see §3.3). The service layer is fine; the parameters are server-filled **[VERIFIED]**.

### 2.6 What does NOT exist

- No frontend caller for `review-signoff`, `approve-policy-override`, or `optimistic-sync` exists outside generated types (`frontend/src/types/generated/spine-api.ts:645, 854, 861`; `frontend/src/lib/api-client.ts:1906` is a read-side timeline event type only) **[VERIFIED — searched `frontend/src` excluding generated]**. The self-asserted write surfaces are currently API/test-only. **This makes the retrofit cheap: there is no UI contract to break yet.**

---

## 3. Auth Substrate Facts

All **[VERIFIED]**.

### 3.1 JWT payload

`create_access_token(user_id, agency_id, role)` builds HS256 tokens carrying exactly: `sub`=user_id, `agency_id`, `role`, `iat`, `exp` (15 min), `type="access"`; refresh tokens carry `sub` only (7 days) — `spine_api/core/security.py:20-99`.

### 3.2 Server-side resolution chain

- `get_current_user` validates the token, resolves `sub` → `User` row (email, name, platform_role), caches on `request.state` — `spine_api/core/auth.py:35-108`.
- `get_current_membership` resolves the JWT `agency_id` → `Membership` row with a `role` column (`owner/admin/senior_agent/junior_agent/viewer`, `spine_api/models/tenant.py:98-111`), sets the RLS context, and is returned by the `require_permission()` dependency factory — `spine_api/core/auth.py:120-168, 230-255`.
- The permission matrix (`ROLE_PERMISSIONS`, `auth.py:208-227`) already encodes the entitlement ladder the signoff gates need (e.g. `trips:escalate` is admin+; senior_agent has write but not escalate).

### 3.3 The canonical in-repo pattern already exists

The codebase already solves this problem correctly in two places — F-03 is a failure of *application* of an existing pattern, not a missing capability:

- `spine_api/routers/assignments.py:100-161`: every mutation takes `membership=require_permission(...)` and passes `assigned_by=membership.user_id`, `claimer_id=membership.user_id`, `escalated_by=membership.user_id` into `routing_service`, whose history log records `by_user_id` (`spine_api/services/routing_service.py:60-67, 118-286`). The `TripRoutingState` model even has a real FK `reviewer_id → users.id` (`spine_api/models/routing.py:63-66`).
- `spine_api/routers/confirmations.py` (money-adjacent confirmations): `created_by=membership.user_id` (:182), `recorded_by=membership.user_id` (:239), `verified_by=membership.user_id` (:261), `voided_by=membership.user_id` (:283, :470) — all server-derived **[VERIFIED]**.

`team_workflows.py` and `corporate_policy.py` are pre-pattern routers that read from the body instead of the membership.

### 3.4 Existing crypto utilities to reuse

- **HMAC-SHA256 verification with constant-time compare**, Stripe-style `t=,v1=` header parsing: `spine_api/providers/stripe_issuing_adapter.py:129-192`. An in-repo reference implementation for signing schemes **[VERIFIED]**.
- **SHA-256 canonical-JSON integrity hash over (provenance_id, source_type, source_ref_id, actor_id, recorded_at, payload)**: `MemoryProvenance.compute_integrity_hash`, `src/memory/models.py:64-67`, orchestrated by `src/memory/provenance.py` — the in-repo provenance lineage pattern to mirror for approval artifacts **[VERIFIED]**.
- **SHA-256 token hashing**: `spine_api/services/membership_service.py:85` **[VERIFIED]**.
- **Audit file hash-chain** with `previous_hash`/`current_hash` per event and `AuditStore.verify_chain()` (`spine_api/persistence.py:2446`+, genesis `"GENESIS_BLOCK_HASH"`) — tamper-*evidence* only, unsigned, and tracked separately as F-06 **[VERIFIED]**.

---

## 4. Three Candidate Designs

| | **A. Server-side actor injection** (JWT-subject capture) | **B. Signed approval artifacts** (hash + HMAC) | **C. Entitlement-gated delegation** (membership role checks) |
|---|---|---|---|
| **What it does** | Every audit/provenance write sources `actor_id = membership.user_id`, `actor_role = membership.role` from auth dependencies; body-supplied actor fields demoted to display-only `claimed_*` | New `ApprovalArtifact` record: `{artifact_id, trip_id, actor_user_id (JWT sub), actor_role, artifact_hash = sha256(canonical_json(decided payload)), signature = HMAC-SHA256(key, artifact_id\|actor\|hash\|at), at}`; verifier recomputes | `require_permission()` gates on each signoff route (new `trips:approve_signoff` on senior_agent+; escalate-level on corporate override); membership.role recorded beside sub |
| **Surface area** | 4 routers (`team_workflows`, `corporate_policy`, `inbound.optimistic_sync`, `audit_bridge` callers) + contract model edits + `field_merge` signature | 1 new model + 1 service module + wiring in 2 signoff routers | `auth.py` matrix + same 4 routers |
| **Retrofit cost** | **Low** — canonical pattern already proven in `assignments.py`/`confirmations.py`; no frontend callers exist (§2.6) | **Medium** — new persistence, canonicalization spec, verify path, tests | **Low** — one matrix row + decorators |
| **Forgery resistance** | Eliminates *identity* forgery (body can no longer claim who). Does NOT bind the record to the decided content, and DB rows remain mutable | Binds who + what + when; tamper-evident post-write even against direct DB edits (given key hygiene); supports later external anchoring (ties into F-06) | Eliminates *entitlement* forgery (a junior cannot approve); makes "who was ALLOWED to authorize" auditable |
| **Failure mode if shipped alone** | An unauthorized (but authenticated) senior_agent-less user could still approve; content of approval unbound to artifact | Signs whatever identity you give it — garbage in, cryptographically sealed garbage out | Correct gate, still records no verifiable identity if paired with self-asserted bodies |

**[VERIFIED]** for all surface/cost rows (file evidence above); **[INFERRED]** for threat-model rows.

These are complementary, not alternatives: A answers *who*, C answers *who was entitled*, B answers *what exactly was approved, provably*.

---

## 5. Recommendation

Ship **A + C as one package (this IS the F-03 fix)**, then **B scoped to money-touching signoffs only**.

1. **A+C jointly** (never separately): extend `team_workflows.py` and `corporate_policy.py` to the `assignments.py`/`confirmations.py` pattern — `membership=require_permission(...)` in, `membership.user_id`/`membership.role` recorded. Add JWT auth to the two `corporate_policy` routes (closes the unauthenticated-header hole, §2.1). For `optimistic_sync`, resolve `actor_id = membership.user_id`; keep `body.actor_role` **only** where it legitimately encodes traveler-vs-operator semantics (customer-side updates arrive through unauthenticated channels today — see §8), and bind operator-side precedence to `membership.role` instead of a body flag. Mirror the same fields into `_field_provenance` (`field_merge.py`) and into `AuditStore.log_event(user_id=membership.user_id, ...)` — stop passing `agency_id` as `user_id` (add `agency_id` as its own field; the bridge already has one, `audit_bridge.py:42-47`).
2. **B for high-value gate + corporate override** (the two money-touching signoffs of this wave): an `ApprovalArtifact` carrying `artifact_hash` over the canonical decided payload (recommendation, amount, decision, gate version) + HMAC signature, reusing the Stripe-adapter HMAC idiom (`stripe_issuing_adapter.py:184-190`) and the memory-provenance canonical-JSON hash idiom (`src/memory/models.py:64-67`). When F-04 (payment mandate ledger) lands, payment consents reuse the same artifact type rather than inventing a second one.
3. **Enrich, don't fork, `status_history`**: extend `{from, to, at}` to `{from, to, at, actor_user_id?, actor_role?, source}` — additive keys; existing readers ignore unknown keys (both stores already round-trip arbitrary key dicts) **[INFERRED from the fold-anything-into-`_extra` design, `persistence.py:1274-1331`]**.

Why not B-first: signing self-asserted identities launders them. Why not A-only: an operator-less audit trail that records a user_id but never checks entitlement, and never binds the approval to the quote it approved, is only half the trail F-03 exists to demand.

---

## 6. Legacy-Data Policy

Existing rows already contain self-asserted values (trip JSON `reviewer_id`, `corporate_policy_override.approved_by`, `_field_provenance.actor_id`, audit rows with `user_id=agency_id`).

- **Do not rewrite history.** The audit file hash-chain (`persistence.py verify_chain`) and the append-only `status_history`/`_field_provenance` invariants mean retroactive edits would break chain verification and the superseded-value semantics **[VERIFIED for chain; VERIFIED for append-only shape]**.
- **Trust-label instead** — additive only: new writes get `actor_binding: "jwt_bound" | "self_asserted"` (or a `provenance_binding_version: 0|1`) stamped at write time; legacy rows are labeled `self_asserted` on read (timestamp-cut: rows created before the migration commit are treated as unbound **[INFERRED — simplest cut; commit-hash cut is an alternative]**).
- **Re-attestation, narrowly:** only for *live gating* signoffs — an active trip currently sitting behind the ≥$10k high-value gate or an unexpired corporate override can be asked to re-confirm under the new bound flow on next action. Closed/historical approvals are never re-attested; they are simply labeled. **[INFERRED — policy choice]**
- No DELETE/TRUNCATE anywhere (also mandated by repo data-safety rules, `AGENTS.md` test-data section).

---

## 7. Sized Next Tasks

| # | Task | Size | Notes |
|---|---|---|---|
| T1 | Bind `team_workflows.py` + `corporate_policy.py` to membership: add `membership=require_permission(...)`; replace `body.reviewer_id`/`body.approver_name` with `membership.user_id` (body values demoted to `reviewer_display_name`, optional); **add JWT dependency to corporate_policy routes** (removes `X-Agency-ID`/`TEST_AGENCY_ID` identity path) | S (~0.5d incl. tests) | Contract edits in `contract.py` (:1507-1521) + `corporate_policy.py` models; mirror `assignments.py` pattern |
| T2 | Bind `optimistic_sync` actor: `membership.user_id` as canonical `actor_id`; operator-side `actor_role` derived from membership.role; body `actor_id` → `claimed_actor_id` (recorded, non-authoritative); same fields into `_field_provenance` + optimistic_sync audit event | S–M | Touches `inbound.py:304-310, 398-399`, `field_merge.py` signature; customer-lane precedence unchanged (see §8) |
| T3 | Stop identity substitution in audit: `AuditStore.log_event`/`audit()` callers pass real `user_id` (+ new optional `actor_role`); `audit_bridge` gains `actor_subject` passthrough (additive `AuditLog` columns) | S | Additive model change; fixes agency-UUID-in-user_id across ~6 call sites |
| T4 | `ApprovalArtifact` model + sign/verify service (canonical-JSON sha256 + HMAC), wired into high-value gate and corporate override; verify on read/export paths | M | New table + service; reuse `stripe_issuing_adapter.py` HMAC idiom and `src/memory/models.py:64-67` hash shape; decide key strategy (§8) |
| T5 | `status_history` actor enrichment (additive keys, both stores) | S | Signature change on `record_status_transition` + plumbing from `persistence.py` seeds |
| T6 | Legacy trust labeling (additive `actor_binding` stamp at write; read-side fallback label) | S | No rewrites; pairs with T1 rollout commit |

Sequencing: T1+T3 land together (they are the F-03 closure evidence); T2 next; T4 once the identity source is bound; T5/T6 anytime after T1. Each task is independently verifiable; T1 without T4 still eliminates identity forgery on the worst surface.

---

## 8. Decision Needed

1. **Customer-side identity scope:** traveler/`public_checker` events (`public_checker.py:36-48`, `product_b_events.py`) are unauthenticated by product design. Do we (a) leave traveler actors self-asserted-but-labeled (`actor_binding: "unauthenticated_claim"`), or (b) introduce traveler session auth now? This doc recommends (a) for F-03 scope — the merge engine's customer-vs-operator precedence can tolerate an unauthenticated customer lane precisely *because* operator identity is bound server-side — but this is a trust-model decision, not a code decision.
2. **Signing key strategy for T4:** reuse `JWT_SECRET` (zero new config, but key-purpose conflation — a leaked JWT secret then forges approvals) vs. a dedicated `APP_SIGNING_SECRET` (one more env var, proper key separation). Recommendation: dedicated secret with JWT_SECRET fallback explicitly logged as degraded. Needs an owner.
3. **Accept adjacency:** the unauthenticated `X-Agency-ID` path on `corporate_policy` routes (§2.1) is strictly worse than F-03 itself; confirm it joins the F-03 closure rather than being filed separately.

---

**Verification note:** all file:line citations were read directly in this session (2026-09-04) against the working tree; no runtime probes were executed (read-only task). The [INFERRED] threat-model claims (§4 forgery rows, §6 policy) follow directly from the cited [VERIFIED] mechanics but were not exercised against a live server.
