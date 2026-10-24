# Long-Term Structural Roadmap — the five invariants (2026-10-23)

**Author:** ZCode · **Status:** Proposed — phased plan, owner-gated items marked
**Derivation:** the complete Sim #2/#3/#4 arc, the 2026-10-12 council audit
(AUD-01..20), and the 2026-10-12/23 remediation waves. Every finding registered
across those arcs clusters into five structural invariants the system keeps
violating. The point fixes are landed and closed (see
`Docs/sims/SIM4_META_AUDIT_AND_PLAN_2026-10-21.md` §5–§8); this roadmap is the
work that makes each *class* impossible rather than repeatedly patched.

**Doctrine anchors:** truth taxonomy (§2), one canonical store per fact, "no
number without a basis" (§13 claim reality), verify intent not just function,
additive-better-comprehensive, failure-becomes-fixture.

---

## Invariant 1 — One persistence boundary: privacy is a storage property

**Evidence:** FND-0326 (P0 — guard covers TripStore only; run ledger + drafts +
messages persist refused PII), FND-0327 (key rotation bricked reads), FND-0315
lineage, the group-invite 422 (same root on a new door).
**Invariant:** the same traveler note lands in three stores (DraftStore, run
ledger, TripStore); the boundary must cover ALL of them or none is real.

**Long-term shape (option B of DP-03a — recommended):**
1. Encryption-at-rest becomes the boundary: run-ledger packets, draft bodies,
   and message bodies get the same `_PII_FIELDS` treatment as trips (Fernet +
   `kid` v2 blobs — the FND-0327 machinery already landed).
2. The privacy guard is demoted to a **dev tripwire** (it already fails closed
   in dogfood; beta mode keeps the audit-log scan).
3. Key management as ops: rotation runbook = `tools/reencrypt_trip_rows.py`
   (landed) + the `kid` check at boot (startup assertion extension: warn when
   rows carry a `kid` ≠ active key).
4. GUC-less-session RLS audit: FORCE RLS on trips made GUC-less scans see
   nothing (FND-0366); every capability-token lookup needs the per-agency scan
   pattern (landed) or a dedicated token table (R-03 — indexed
   `(token_hash, agency_id, trip_id, purpose, expires_at)`, one table for
   proposals + asks + group + collection, replacing four full-scan lookups).

**Effort:** L (boundary encryption M, token table M, boot checks S).
**Dependencies:** DP-03a (posture call) gates step 1's mode; steps 2–4 are
unblocked. **DP touchpoints:** DP-03a, DP-03b (PAN redact-at-ingest rides the
same ingest seam).

---

## Invariant 2 — One fact store with authority-ranked merge

**Evidence:** FND-0328/0351 (answers recorded, not consumed; lossy reassess),
0331 (runner artifact — but the loss class is real: extraction replaced facts),
0332 (display columns lag the packet → gate dead-end), 0343/0344 (same lag in
party/budget display), U13 (memory never informs intake — Sim #3 P7 residual).
**Invariant:** `extracted.facts` is the canonical truth; every writer (re-
extraction, traveler answers, operator PATCH, inbound attach, memory hydrate)
is just a writer with an authority rank, and every reader (gate, quotes,
analytics, FE, follow-ups) reads one view.

**Long-term shape:**
1. Generalize `resolve_field_merge` (spine_api/services/field_merge.py) to the
   packet-fact layer: a single `merge_facts(existing, incoming, actor)` used by
   run saves, answer writes, operator PATCHes, and inbound attach. The
   `_preserve_authoritative_facts` guard (landed) becomes its preservation rule;
   the answers' slot shape (landed) becomes its slot contract.
2. **Retire the display-column folds:** `budget`/`origin`/`destination`/`party`
   top-level columns become a projection built at read time from facts (one
   server-side view function), so lag is structurally impossible and the FE
   reads one shape.
3. **Memory→intake wiring (U13):** a returning-guest signal — the run path
   consults `CustomerMemoryProfile` by resolved contact identity (the
   `_resolve_existing_lead` identity harvest already computes it) and injects
   `authority_level: "profile"` slots below explicit_user, above system.
4. Follow-ups/unknowns computed ONLY from the merged view (already true post-
   0351 — keep it as the invariant test).

**Effort:** L (merge generalization M, projection M, memory wire S).
**Dependencies:** none outstanding; sequencing AFTER invariant 3's schema work
is cleaner (facts slots gain basis fields once).
**DP touchpoints:** none — pure engineering.

---

## Invariant 3 — No number without a basis, enforced at the contract

> **Phase 1 first slice LANDED (2026-10-23):** `TripQuoteView` basis fields
> are now REQUIRED and vocabulary-checked at construction
> (`contract.py _BASIS_VOCABULARY`, derived from the real producers in
> commercial_agreement.py/quotes.py) — a writer who cannot name where a
> number came from cannot construct the response. Quotes suite matches HEAD's
> pre-existing failure set exactly (the two trip_version tests — FND-0359
> note); the enforcement added zero new failures. Remaining slices below.

**Evidence:** FND-0337 (1240% take-rate "feasible"), 0339 (invented E_VISA on
registry miss), 0338 (violation from an estimated baseline), 0345 (capped
totals as tenant totals), 0331/0336 (empty Art.15 export), plus every
`reality_tier`/`cost_basis` label the system already carries.
**Invariant:** every monetary, legal, or statistical assertion carries a
machine-readable basis + reality tier, and the schema REJECTS assertions
without one. Honesty becomes a type error, not a review catch.

**Long-term shape:**
1. Schema-level rule: response models for money/legal surfaces require paired
   `*_basis` fields (Pydantic `model_validator`): a `gross_price` without
   `cost_basis`, a `visa_type_required` without `registry_match`, a
   `totalInquiries` without `count_basis` fails response construction.
2. Roll the pattern across the surfaces the arcs flagged: quotes (has labels —
   make them required), corporate audit (0338 fix — make the
   estimate→warning-only rule a validator), visa radar (0339 — required
   `registry_match`), analytics (0345 — `count_basis: "paged_total" |
   "capped_sample"`), claims (framework resolver already single-authority —
   require it), compiler (budget_check required when trip has facts).
3. Eval gate: the honesty fields join the D6/eval assertions — a fixture whose
   expected output carries `within_budget: null` must fail if an endpoint
   returns a fabricated boolean.
4. UX: FE renders basis badges from the same fields (the T4 labels already
   do; extend to the new surfaces).

**Effort:** M per surface cluster (money M, visa/policy S, analytics S).
**Dependencies:** pairs well with invariant 2's schema pass (one edit session
per response model).
**DP touchpoints:** none.

---

## Invariant 4 — Shipped = reachable AND consumed, enforced in CI

**Evidence:** FND-0340 (46-route parity gap), 0332 (gate over carried facts),
0328 (answers with zero readers), AUD-06/07 lineage. A door can be reachable
and still not change anything downstream.
**Long-term shape:**
1. The parity gate is landed (`tests/test_bff_parity_gate.py` + snapshot) —
   DP-03c shrinks the snapshot per door.
2. **Closed-loop assertions** per launch-tranche feature: a test that proves
   the OUTPUT surface changes when the INPUT surface is exercised (ask answer
   clears the ask — landed as the door-2 S2; claim letter cites the resolver's
   framework — landed in Sim3 wave; inbound message lands on the lead's
   timeline — landed in the 0334 fix). Pattern: seed → exercise input →
   assert the downstream surface changed. Institutionalize as the
   `tests/closed_loop/` suite, one file per tranche, named after the door.
3. Launch inventory ties feature-list status to the closed-loop suite: a
   feature is LIVE only when its closed-loop test passes (replaces
   hand-maintained SHIPPED claims — the exact failure the 10-12 council
   prosecuted).

**Effort:** M (suite scaffolding S, one file per tranche ~S each).
**Dependencies:** parity gate (landed). **DP touchpoints:** DP-03c.

---

## Invariant 5 — The failure flywheel, institutionalized

**Evidence:** the sim-voice→fixture pattern (0329 destination fixtures,
injection notes, party voices — all landed as tests); acceptance probes
(Sim3/Sim4); the store's evidence-first registration. But fixtures live in
sim-land and probes in tools/ — not one system.
**Long-term shape:**
1. At `findings.py open` time with a reproducing input, the CLI offers to
   append the verbatim input to the adversarial corpus
   (`data/fixtures/adversarial/`) — registration and fixture-ation are one
   action, evidence tier carried into the fixture metadata.
2. The Sim4 acceptance probes fold into `tests/closed_loop/` (invariant 4).
3. Sim #5 then measures new doors only.

**Effort:** S–M. **Dependencies:** none. **DP touchpoints:** none.

---

## Sequencing (dependency-aware)

| Phase | Work | Why this order | Owner-gated? |
|-------|------|----------------|--------------|
| 0 | DP-03a–e decisions | gate the biggest levers | **Yes — all five** |
| 1 | Invariant 3 (schema honesty enforcement) — money cluster first | smallest effort per unit of trust; independent | No |
| 2 | Invariant 2 (fact-store merge + projection) | largest defect-class engine; schema pass rides phase 1 | No |
| 3 | Invariant 1 (boundary encryption + token table) | needs DP-03a; ops-heavy | Partially (DP-03a/b) |
| 4 | Invariant 4 (closed-loop suite + launch inventory) | consumes the stabilized surfaces | DP-03c for mapping doors |
| 5 | Invariant 5 (flywheel CLI) | anytime; rides the store CLI | No |

Cross-cutting residuals tracked in the store: FND-0358 (booking_data
exposure), FND-0359 (suite pollution + `component_key`-class migration drift),
FND-0366 deferred residual (deleter bisection), FND-0321 reopened residual
(loop-keyed store audit), FND-0341 (currency default, = DP-03d).

## Acceptance criteria (per invariant — "done" means)

1. A GUC'd visit to any store shows zero plaintext PII outside the sanctioned
   encrypted fields; the boot kid-check warns on foreign-`kid` rows.
2. Deleting any single writer (answers/PATCH/re-extract) cannot change a fact
   slot's authority-ranked outcome; the invariant test set proves it.
3. Stripping any `*_basis` field from a response model fails its own tests.
4. Every launch-tranche feature has a passing closed-loop test; feature-list
   LIVE status is derived from it.
5. A finding registered with a reproducing input appears in the adversarial
   corpus in the same action.

## Explicitly out of scope (recorded)

LLM-lane posture flips (X-09 — topic 49 exploration owns it), provider
integrations (Amadeus live, OCR, Timatic — each is a producer decision, not
structural), and any weakening of R-15 (forbidden).
