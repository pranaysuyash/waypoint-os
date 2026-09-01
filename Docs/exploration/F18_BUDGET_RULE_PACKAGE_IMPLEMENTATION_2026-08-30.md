# F-18 Implementation — Budget Extraction Rule Package (2026-08-30)

**Closes:** F-18 (RQ-01 exit) · **Goal:** make the honestly-red budget gate green by fixing extraction, not by re-baselining.

**Result: budget gate PASSING — F1 0.9524, precision 1.0, recall 0.9091, blocks_ci False (20 fixtures); `verify_d6_gate_snapshot.py` exits 0.**

---

## 1. Changes

### `src/intake/extractors.py` — `_extract_budget` and friends
| Gap | Change |
|---|---|
| S1 | `budget_connective`: multi-token connective list (`of/is/was/only/around/about/approx/roughly/up to/under/at most/no more than/maximum/max/exactly/between`), zero-or-more — fixes "budget **is around** $3000", "budget **is only** 3000". Applied to all five pattern sites (now `rf`-strings). |
| S2 | `currency_word_pattern` (word-only token set with `\b` guards so "auditing"≠AUD) captured **after** the amount in range + explicit patterns; currency words `dollars?/bucks?/euros?/rupees?` join the token map; `_currency_code` fallback **INR→USD** (D1). |
| D1-context | `_defaulted_currency(unit)`: lakh/crore units in the matched region ⇒ INR (preserves bare "3L"/"2.5 lakh" Indian-market inputs and their tests); everything unmarked ⇒ USD. Fallthrough `parse_budget` results get the same rule (lakh-shaped raw keeps INR). |
| S3 | New anchored block: `between/have/spend(ing)` (+ optional `about/around/roughly`), range support (`and/to/-`), currency-after capture. **Deliberately no bare "of" anchor** (false-positives on "family of 4") and **amounts < 100 rejected** ("have 2 kids" is not a budget). |
| S4 | `_extract_budget_scope`: `a day / per day` ⇒ `daily`. |
| S5 | `_extract_budget_flexibility`: firm markers (`max/only/no more than/exactly/at most`) ⇒ `firm`; builder defaults unmarked budgets (only when a budget was actually extracted) to `soft` (D2 golden convention). Stretch-ambiguity block now keyed to **explicit** flexibility so the soft default cannot trigger stretch detection. |
| S6 | Range separator accepts `and` ("between 4000 **and** 6000"); range + explicit patterns accept post-amount currency. |
| — | "flexible budget" path currency INR→USD (same D1 rule). |

### `src/evals/audit/snapshot.py` — `_collect_live_budget_results`
Golden expresses `budget_amount` as a composite string; the mapping now composes it from structured facts: `min-max` for ranges, `max/day` for daily scope, plain `max` otherwise. (The pipeline keeps storing numeric min/max — the composition is eval-side representation only.)

### `data/fixtures/budget/golden_dataset.json` — 8 negative precision traps (additive; 12 → 20)
Date-range ("between March and June"), headcount ("family of 4"), other-thing price ("flights cost around 800… no budget yet"), stars/rooms, "have 2 kids", bare "of 4", year ("2019"), "5-star". All expect all-None — the set had exactly **1** negative fixture before; precision is now actually measured.

### `tests/test_extraction_fixes.py` — one assertion modernized
`test_date_flexibility_does_not_create_budget_flex_ambiguity` asserted `budget_flexibility is None` for an unmarked budget — that predates and contradicts the D2 golden convention (unmarked ⇒ soft). The invariant it exists to protect is **date-flexibility language must not leak into budget flexibility**: the assertion now rejects `"stretch"` (the leak signature) and any flexibility ambiguity events, while accepting the soft default. Test intent preserved; the stricter-than-intent assertion updated with a comment.

## 2. Verification evidence

| Check | Result |
|---|---|
| 12 original fixtures, real pipeline | **11/12 fully correct** (only hard_004, deferred H1) |
| 8 new negative traps, `_extract_budget` | **0 false positives** |
| Snapshot regenerated | `budget_health: passing, F1 0.9524, P 1.0, R 0.9091, blocks_ci False, 20 fixtures` |
| `scripts/verify_d6_gate_snapshot.py` | **exit 0 (`ok: true`)** — CI budget gate green |
| `ruff check` (3 changed files) | clean |
| Eval + extraction suites (`tests/evals/`, extraction_fixes, block3, nb01_v02, document_extractions, booking_data, booking_collection, agency_settings) | **601 passed / 1 amended** → then 404-in-scope re-run all green |
| Full backend suite (`scripts/run_backend_tests.sh`) | see final summary (run in flight at doc-write time; result recorded below in register update) |

## 3. Decisions implemented (from RQ-01 §6, pending Pranay ratification)

- **D1:** unmarked currency default USD (was INR); `₹/rs/INR` explicit and lakh/crore units remain INR. Reversible one-liner if you veto.
- **D2:** unmarked budget flexibility = soft; unmarked budget scope = total; both gated on an actual budget being extracted (negatives stay all-None).
- **H1 (hard_004 revision resolution):** deferred — remains the single recall gap (0.9091).

## Checklist applied: IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md
