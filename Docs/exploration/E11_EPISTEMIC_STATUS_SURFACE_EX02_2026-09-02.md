# E11 — Epistemic Status as an Operator-Facing Surface (EX-02)

**Date:** 2026-09-02 (written 2026-09-04)
**Type:** Exploration / research only — no implementation.
**Register linkage:** EX-02 (epistemic UI), NEW-01 (inverted evidence apparatus), F-22 (authority/epistemic mislabeling), NEW-02 (silently-wrong extraction, 4x commercial error class), GM-01 (honesty fix on the demo panel).
**Evidence convention:** **[VERIFIED]** = read directly from code or produced by a runtime check in this repo on 2026-09-04. **[INFERRED]** = reasoned conclusion from verified facts, not directly observed.

---

## The Question

Ambiguity in a traveler conversation — "around Oct 5", "budget flexible **if** the hotel is special", "probably 4 of us" — is **accurate data about the conversation**, not missing data. The packet layer already carries `epistemic_status` per slot and defines an `AssumptionRecord`; the merge layer already carries actor provenance and conflicts. What does it take for the operator surface to preserve and display this truth-state, and which decision consumers must refuse to silently consume assumed values?

---

## 1. Current State — What Exists, What's Patchy

### 1.1 The packet layer primitives exist and are sound [VERIFIED]

- `src/intake/packet_models.py:91-96` — `EpistemicStatus(StrEnum)`: `FACT | INFERRED | ASSUMED | UNKNOWN` (PER-0922/0923).
- `src/intake/packet_models.py:99-119` — `AssumptionRecord` dataclass: `slot_name`, `assumed_value`, `rationale`, `criticality: Literal["critical","preference","advisory"]`, `acknowledged_by_operator: bool`, `operator_notes`. This is a complete acknowledgment workflow model — **including the operator-acknowledgment fields the UI would need**.
- `src/intake/packet_models.py:164` — `Slot.epistemic_status: Optional[str]`; serialized in `Slot.to_dict()` (:179-180) whenever set.
- `src/intake/packet_models.py:463` — `CanonicalPacket.assumptions: List[AssumptionRecord]`.
- `src/intake/extractors.py:2381-2394` — `_epistemic_for_authority()` maps `AuthorityLevel` → `EpistemicStatus`; `_make_slot()` (:2396-2413) stamps it on every slot by default, so the *plumbing* is uniform.
- The merge layer precedent [VERIFIED]: `spine_api/services/field_merge.py:36` (`PROVENANCE_KEY = "_field_provenance"`), `resolve_field_merge()` (:152-245) returns `MergeConflict` records with kept/rejected values and actor attribution; `spine_api/routers/inbound.py:250-437` (`/inbound/optimistic-sync/{trip_id}`) returns `conflicts`, `applied_fields`, `_field_provenance`-carrying packet.

### 1.2 The wiring is patchy — only 2 of ~30 fact slots carry honest epistemic status [VERIFIED by runtime check]

Ran `ExtractionPipeline` on the topic's exact hedge phrases:

> Input: `"Trip around Oct 5 for probably 4 of us to Kyoto. Budget is 5000 if the hotel is special, otherwise flexible."`

| Slot | Value | Confidence | Authority | Epistemic |
|---|---|---|---|---|
| `party_size` | `4` ("**probably** 4 of us") | 0.9 | `explicit_user` | **FACT** |
| `budget_min` | `5000` ("if the hotel is special") | 0.9 | `explicit_user` | **FACT** |
| `budget_max` | `5000` | 0.9 | `explicit_user` | **FACT** |
| `budget_flexibility` | `"soft"` | 0.7 | `explicit_user` | **ASSUMED** ✅ |
| `budget_scope` | `"total"` | 0.7 | `explicit_user` | **ASSUMED** ✅ |
| date slots | — | — | — | **absent entirely** ("around Oct 5" produced no `date_*` slots; a control run shows plain "Oct 5" also produces none — a separate date-year extraction gap, DEMO02-class) |
| `packet.ambiguities` | `[]` | | | no ambiguity captured for either hedge |
| `packet.assumptions` | `[]` | | | **nothing registered** |

Findings:

1. **The only epistemic-honest slots in production are `budget_flexibility` and `budget_scope`** (`src/intake/extractors.py:2562` and `:2577`, the D2/RQ-01 golden convention). Everything else defaults through the authority mapping, which stamps `FACT` whenever authority is `explicit_user` — this is F-22/NEW-01 exactly: the hedge "probably" and the conditional "if the hotel is special" are both laundered into FACT.
2. Even the two honest slots carry `authority_level=explicit_user` while `epistemic_status=ASSUMED` — internally contradictory stamps (authority tier lies, epistemic tier tells the truth). **[VERIFIED runtime output]**
3. **The `AssumptionRecord` register is dead.** `rg 'AssumptionRecord('` finds zero production instantiation; only `tests/test_epistemic_integrity.py:65,90` populates it. **[VERIFIED]**

### 1.3 There is a dead consumer waiting for the register [VERIFIED]

`src/intake/decision.py:1351-1365` implements the `unacknowledged_critical_assumption` risk flag — it filters `packet.assumptions` for `criticality == "critical"` and `not acknowledged_by_operator`. Because the register is never populated, this policy check has **never fired on a real trip**. The enforcement point for "assumptions need operator eyes" exists and is inert.

### 1.4 There are two `EpistemicStatus` enums with divergent vocabularies [VERIFIED]

- Packet layer (`packet_models.py:91`): `FACT | INFERRED | ASSUMED | UNKNOWN`
- Arbiter layer (`src/intake/epistemic_arbiter.py:18-23`): `FACT | ASSUMED | EXTRACTED | CONFLICTED | UNKNOWN` — no `INFERRED`, adds `CONFLICTED` and `EXTRACTED`.
- The arbiter has real deterministic logic (turn-conflict detection, implicit/negative constraints, JSON-LD proof graph) exposed at `spine_api/routers/epistemic.py` (`/api/v1/epistemic/*`), but **operates on caller-supplied slots, not canonical pipeline data**.
- The frontend surface for it, `frontend/src/app/(agency)/workbench/EpistemicPanel.tsx`, is an explicitly `SimulatedBadge`-labeled demo with **hardcoded** conflict and proof-graph data (the GM-01 honesty comment at :7-11 says exactly this). [VERIFIED]

### 1.5 Merge conflicts are shipped backend-side but have no operator surface [VERIFIED]

`/inbound/optimistic-sync` returns `conflicts` and provenance, but:

- `rg "optimistic-sync|_field_provenance"` across `frontend/src` finds **zero references**. No BFF route, no store, no component consumes them.
- The only frontend "conflict" surfaces are unrelated: `DataIntakeZone.tsx:342-352` renders the 409 `stale_packet_version` save-conflict banner (session clobbering, not precedence conflicts), and `api-client.ts:1621-1624` defines `ApplyConflict` for document-extraction apply (referenced only by its own contract test).

So the "precedent" for surfacing disagreement exists as **data plumbing without a display**, and the simulated EpistemicPanel exists as a **display without data**. EX-02 is the bridge between them.

---

## 2. The Loss Points — Where Epistemic Truth Dies on the Way to the Operator

Tracing packet → trip record → BFF → workbench [VERIFIED at each hop]:

| # | Hop | Status | Detail |
|---|---|---|---|
| L1 | **Producer** (`src/intake/extractors.py`) | ❌ LOSS | Only 2 slots stamped `ASSUMED`; hedges/conditionals collapse to `FACT`; no `AssumptionRecord` created; ambiguities not recorded for epistemic hedges. |
| L2 | **Serializer** (`src/intake/packet_models.py:768-795`) | ❌ LOSS | `CanonicalPacket.to_dict()` serializes facts/derived_signals/hypotheses/ambiguities/unknowns/contradictions/events/metadata — **but not `assumptions`**. Even a populated register would be dropped before persistence. Runtime check: `'assumptions' in p.to_dict()` → `False`. |
| L3 | **Persistence** (`spine_api/persistence.py:2157`) | ✅ OK | `trip["extracted"] = packet` lands in a dedicated encrypted column (`_PII_KEY_FIELDS`, :1198). Per-slot `epistemic_status` **does survive storage** via `Slot.to_dict()`. |
| L4 | **Trip response → BFF** (`frontend/src/lib/bff-trip-adapters.ts:503`) | ✅ mostly OK | `packet: trip.extracted ?? undefined` passes the whole packet through — slot-level `epistemic_status` is in the payload today. |
| L5 | **Type contract** (`frontend/src/types/spine.ts:287-294`) | ❌ LOSS | `SlotValue` has **no `epistemic_status` field**. The data is present and the type pretends it doesn't exist — the classic mocked-contract failure mode this repo's discipline explicitly forbids. |
| L6 | **Display** (`frontend/src/components/workspace/panels/PacketPanel.tsx`) | ❌ LOSS | The "Extracted Information" table renders Field / Value / Confidence / Authority (~:163-186) — **no epistemic column**. Nobody can see `ASSUMED` even when the payload carries it. |
| L7 | **Display re-stamping** (`PacketPanel.tsx:46-53, 150-157`) | ❌ NEW LOSS | `_makeCanonicalSlot()` synthesizes fallback slots from top-level trip display fields with `confidence: 1, authority_level: "explicit_user"` and **spreads them over the real packet facts** (`{...packetFacts, ...canonicalTripFacts}`). This is the F-22 mislabel class **recreated at the UI layer**: the workbench actively re-brands whatever the backend says into explicit-user truth for origin, destination, budget, dates, party_size — including `party_size`, the NEW-02 4x-error field. |

**Net:** per-slot epistemic status survives storage and transport (L3, L4) but is invisible by type (L5), invisible by rendering (L6), actively falsified for the seven display-canonical fields (L7), and the assumption register never even reaches the serializer (L1, L2).

---

## 3. Surface Design Options + Recommendation

### Option A — Epistemic badges on existing packet fields (chips/column)

Add `epistemic_status` to `SlotValue`; add an **Epistemic** column (or a badge beside Authority) in the PacketPanel facts table; a small `ASSUMED`/`INFERRED`/`UNKNOWN` chip on the six summary cards (Destination, Dates, Budget, Party). Remove `_makeCanonicalSlot`'s hardcoded `explicit_user`/`confidence:1` stamping so the fallback slots inherit honest (or absent) labels.

- Effort: **S** — one type field, one column, one helper fix. Backend data already flows (L3/L4 pass).
- Honesty property: displays only what already exists. Crucially, with today's labels it would mostly show `FACT` everywhere — see Dependency Order.

### Option B — "What we're assuming" panel

A dedicated workbench section aggregating every `ASSUMED` slot plus all `AssumptionRecord`s, each with `rationale`, `criticality`, and an **Acknowledge** action writing `acknowledged_by_operator`/`operator_notes`. The `AssumptionRecord` model already defines this workflow and `decision.py:1351` already escalates on unacknowledged critical assumptions.

- Effort: **M** — requires fixing L1 (extractors emit records), L2 (`to_dict` serializes them), plus a small acknowledge endpoint (`PATCH` on the packet or a reserved-key update through the existing optimistic-sync merge).
- This is the panel that converts ambiguity from "displayed" to "worked off".

### Option C — Unified epistemic ledger (consolidation)

One surface merging: slot epistemic status, `AssumptionRecord`s, packet `contradictions` (already structured with a DETECTED→OPEN→RESOLVED lifecycle, `packet_models.py:619-660`), merge conflicts from `_field_provenance`/optimistic-sync, and arbiter turn-conflicts — retiring the simulated `EpistemicPanel.tsx` and giving the operator a single "what do we believe and why" view.

- Effort: **L** — multi-source aggregation, interaction design genuinely undetermined (EX-02's own exit criterion is an interaction proposal with operator observation, Tier 4).

### Recommendation: A → B → C, with A gated behind label honesty

**A is the smallest honest slice** and is nearly free (the data is already in the payload). But shipping A against today's labels would render `party_size=4 — FACT` with a confident green badge — lies with better branding. So A must land together with the L7 fix (stop re-stamping) and, at minimum, the extractor-side ASSUMED stamping for hedged party/date values (the F-22/NEW-01 fix). B is the highest-value increment because it activates the already-written escalation policy. C is the destination, not the first step; it should *replace* the simulated panel rather than coexist with it (no duplicate surfaces — same doctrine as routes).

---

## 4. Policy Linkage — Which Consumers May/May Not Trust Assumed Values

**[INFERRED from verified code paths; the classification itself is a policy proposal]**

| Consumer | May consume ASSUMED? | Rationale / current state |
|---|---|---|
| Follow-up question generation (NB01 decision, `ASK_FOLLOWUP` paths) | ✅ Yes — indeed *should* | Assumed slots are exactly the follow-up targets. Today the ambiguity machinery does this for `Ambiguity` entries but not for `ASSUMED` stamps. |
| Draft strategy / internal drafts (`build_session_strategy`) | ⚠️ Yes, labeled | Drafts are internal; assumptions acceptable if surfaced. `strategy.py:684-693` already documents draft assumptions as strings — should be fed from `AssumptionRecord`s. |
| **Commercial quoting/pricing** (budget_min/max, per-person vs total, currency) | ❌ **Never silently** | NEW-02's ~4x error class: `party=1 × trip-total` vs truth `4 × per-person`. Runtime check above shows hedged/conditional budgets stamped `FACT @0.9` — the worst case. |
| **Party-size-dependent bookings** (rooms, flights, rooming lists) | ❌ **Never silently** | Same error class; "probably 4 of us" is currently `FACT`. |
| Booking-commit paths (NB03 / approval gates) | ❌ Hard-block on unacknowledged `critical` assumptions | `decision.py:1351` is the intended enforcement point; it is dead today because the register is empty (L1/L2). |
| Traveler-facing proposals | ❌ Not without operator acknowledgment | A proposal quoting against an assumed headcount converts an internal uncertainty into a customer commitment. |
| Merge precedence (`field_merge.py`) | ⚠️ Blind today [VERIFIED] | Precedence is actor-based only; an `ASSUMED` value stored with no attribution gets operator-conservative protection (:196-221) and can lock out a *customer correcting an assumption*. An epistemic-aware merge (assumed values should be cheap to overturn by any actor) is the natural extension. |

Enforcement shape [INFERRED]: the cheapest true gate is at the **NB01→NB02 / NB02 judgment layer** (`src/intake/gates.py:101+`): any `critical`-criticality assumption on `party_size|budget_*|date_*` with `acknowledged_by_operator=False` forces `ASK_FOLLOWUP`/escalation instead of `READY_FOR_STRATEGY` for auto-quote paths. This turns the dead risk flag into a structural gate rather than a soft advisory.

---

## 5. Dependency Order — F-22 / NEW-01 First

**The labeling fix is a hard upstream prerequisite for the surface.** [INFERRED, from verified state]

1. Today's data would render almost everything `FACT` (runtime evidence in §1.2), and the UI layer *re-stamps* display fields as `explicit_user/confidence 1` (L7). A badge surface built now would faithfully display wrong labels — an honesty surface that launders dishonesty.
2. Conversely, the surface work (A) contains one change the labeling fix needs anyway: **L7** — `_makeCanonicalSlot` must not fabricate `explicit_user`. Doing it inside task A avoids touching PacketPanel twice.
3. The two `EpistemicStatus` enums must converge into one vocabulary before badges ship (a UI cannot show two spellings of "assumed"). Recommended: keep the packet-layer 4-value StrEnum as canonical (it's what slots carry), treat the arbiter's `CONFLICTED` as a *conflict record*, not a slot status — that maps cleanly onto the existing contradiction lifecycle. **[INFERRED design judgment]**

Suggested sequence:

```text
F-22/NEW-01 (honest per-field stamps in extractors)
        │
        ├─→ A: SlotValue.epistemic_status + PacketPanel column + L7 fix   (can start in parallel; merge after labels honest)
        │
        ├─→ L2 fix: serialize assumptions in to_dict()                     (independent, additive)
        │
        └─→ B: AssumptionRecord production + acknowledge endpoint + panel → activates decision.py:1351
                │
                └─→ Policy gate: critical assumptions block auto-quote (NEW-02 linkage)
                        │
                        └─→ C: unified ledger; retire simulated EpistemicPanel
```

---

## 6. Sized Next Tasks

| # | Task | Size | Files | Notes |
|---|---|---|---|---|
| 1 | Add `epistemic_status` to `SlotValue` + Epistemic column/badges in PacketPanel + remove `_makeCanonicalSlot` falsification (L5, L6, L7) | S | `frontend/src/types/spine.ts`, `frontend/src/components/workspace/panels/PacketPanel.tsx` | Backend payload already carries the field; contract-test with real API shape per API Contract Verification rule. |
| 2 | Serialize `assumptions` in `CanonicalPacket.to_dict()` | S | `src/intake/packet_models.py:768-795` | Additive; `[a.to_dict() for a in self.assumptions]`. No consumer breaks (currently always empty). |
| 3 | Emit `AssumptionRecord`s wherever `ASSUMED` is stamped (start: `budget_flexibility`, `budget_scope`; then hedge-aware party/date from the F-22 fix) | M | `src/intake/extractors.py` | Criticality table: `party_size`/`budget_*` = critical, preferences = advisory. |
| 4 | Acknowledge endpoint (operator `acknowledged_by_operator`/`operator_notes`) + "What we're assuming" panel; surface optimistic-sync `conflicts` in the same panel area | M | `spine_api/routers/inbound.py` (extend optimistic-sync — one route per resource), BFF route, new panel component | Activates `decision.py:1351` escalation for free. Do **not** create a parallel sync route. |
| 5 | Policy gate: unacknowledged critical assumptions block auto-quote / `READY_FOR_STRATEGY` promotion on commercial paths | M | `src/intake/gates.py`, `src/intake/decision.py` | Ties to NEW-02 remediation; needs negative tests ("probably 4 of us" must not reach READY_FOR_STRATEGY unacknowledged). |
| 6 | Unify `EpistemicStatus` vocabularies; retire simulated `EpistemicPanel.tsx` into the real ledger (Option C) | L | `src/intake/epistemic_arbiter.py`, `packet_models.py`, `spine_api/routers/epistemic.py`, frontend | Supersession Workflow applies — the demo panel is superseded, not preserved; document removal per repo rules. |

Tasks 1 and 2 are independently shippable and riskless; 3–5 form the value core; 6 is consolidation.

---

## Decision Needed

1. **First slice:** proceed with A (badges + L7 fix + `SlotValue` type) merged only after/with the F-22/NEW-01 honest-stamp fix, or ship A immediately as a scaffold that visibly shows today's (wrong) FACT labels to force the labeling fix? (My recommendation: after/with — see §5.)
2. **Policy posture:** should unacknowledged `critical` assumptions *block* `READY_FOR_STRATEGY`/auto-quoting (structural gate in NB02/gates), or only surface in the risk list (P2 advisory as EX-02 is scoped today)? This is a product risk decision, not a UI decision.
3. **Enum unification:** adopt the packet-layer 4-value `EpistemicStatus` as canonical and model arbiter `CONFLICTED` as a conflict record — or extend to a shared 5-value enum? Needed before any badge vocabulary ships.
4. **Operator observation:** EX-02's exit criterion is an interaction proposal validated by operator observation (Tier 4). Decide whether task 4's panel ships behind a flag for observation before the policy gate (task 5) is enforced.

---

*All file paths are absolute under `/Users/pranay/Projects/travel_agency_agent/`. Runtime evidence produced via `ExtractionPipeline` on 2026-09-04 with hedged and control inputs (§1.2).*
