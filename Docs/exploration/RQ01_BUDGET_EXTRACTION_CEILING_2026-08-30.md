# RQ-01 — Is Deterministic Budget Extraction the Right Ceiling? (2026-08-30)

**Question:** Budget extraction F1 is 0.2857 (precision 1.0, recall 0.1667). Is the ceiling a *tuning* problem, a *rule-coverage* problem, or a *paradigm* problem (the deterministic boundary itself is wrong)?

**Verdict: rule-coverage problem. The falsifier is NOT triggered** — of 12 golden fixtures, exactly **1** (8%) requires more-than-rule-based reasoning, far below the 50% threshold that would force a hybrid redesign. **The deterministic boundary is not the ceiling.** A ~90-minute prototype of amended rules takes fixture-level accuracy from **2/12 (0.167, the current F1 driver) to 11/12 (0.917)** without touching architecture.

**Consequence for CI:** the honest red budget gate should be fixed by implementing the rule package (§5), not by re-baselining the threshold downward.

---

## 1. Method (executed evidence)

1. Reproduced the baseline field-by-field: ran `_collect_live_budget_results()` (`src/evals/audit/snapshot.py`) over all 12 fixtures in `data/fixtures/budget/golden_dataset.json`. Result: **TP=7/FN=41 at field level; only 2 fixtures fully correct** (incl. the negative fixture `budget_hard_001`, correctly extracting nothing) — consistent with the snapshot's recall 0.1667 / F1 0.2857.
2. Read the extraction path end-to-end: `_extract_budget` (`src/intake/extractors.py:821`) + `Normalizer.parse_budget`.
3. Categorized every failed field; validated the "tunable" bucket by prototyping amended rules (`tmp/rq01_prototype.py`, kept as evidence) and scoring all 12 fixtures.

## 2. Per-fixture failure taxonomy

| Fixture | Diff | Current result | Category | Root cause |
|---|---|---|---|---|
| budget_simple_001 | easy | amount+currency+flex missed | **Tunable (S1)** | "Budget **is around** $3000" — only ONE connective token allowed by the regex; "is around" breaks it. `$` prefix otherwise supported. |
| budget_simple_002 | easy | currency INR≠USD, flex missed | **Tunable (S2, S5)** | `_currency_code(None)` defaults to **INR**; golden expects USD. "about" should imply soft — no rule exists. |
| budget_simple_003 | easy | currency INR≠USD, flex missed | **Tunable (S2, S5)** | "5000 USD" — currency is only captured *before* the amount, never after. "Max" should imply firm — no rule. |
| budget_medium_001 | medium | amount only "4000", range missed, flex | **Tunable (S3, S5)** | "between 4000 and 6000 **to spend**" — no budget keyword, no keyword-free anchor; range+separator not handled; "between"→soft missing. |
| budget_medium_002 | medium | everything missed | **Tunable (S2, S3)** | "have about 7500 **dollars**" — "dollars" is a currency word, not in the unit list; no "have" anchor. |
| budget_medium_003 | medium | everything missed | **Tunable (S1)** | "Budget **is around** €2500" — same double-connective fragility. |
| budget_hard_001 | hard | correct (all None) | ✅ true negative | "something affordable" — correctly extracts nothing. |
| budget_hard_002 | hard | everything missed | **Tunable (S1, S2)** | "budget is **only** 3000 dollars" — "only" not a connective; trailing "dollars" not captured. |
| budget_hard_003 | hard | everything missed | **Tunable (S2, S3, S4)** | "spend about 200 **bucks a day**" — "bucks" not a currency word; no "spend" anchor; no daily scope; golden format `200/day`. |
| budget_hard_004 | hard | everything missed | **Needs-LLM (H1)** | "Originally I was thinking 5000 **but** … 8000 is more realistic" — requires revision resolution (discarding the first number). No deterministic rule without real false-positive risk. |
| budget_easy_001 | easy | scope+flex missed | **Tunable (S5)** | amount+currency already correct; "unmarked → soft" convention not implemented. |
| budget_easy_002 | easy | scope+flex missed | **Tunable (S3, S5)** | "We have 3500 **to spend**" — no anchor; unmarked→soft. |

**Tally: 10 tunable (systemic rule gaps S1–S5) · 1 needs-LLM (H1) · 1 already correct.**

## 3. The six systemic gaps (all deterministic-extractable)

- **S1 — single-connective fragility:** the budget-keyword patterns accept exactly one connective from `(of|is|around|about|approx)`. Natural phrasing uses two ("is around", "is only"). Fix: `(?:\s+(?:of|is|was|only|around|about|approx(?:imately)?|roughly|up\s+to|under|no\s+more\s+than|maximum|max(?:imum)?|exactly|at\s+most))*`.
- **S2 — currency capture & default:** currency tokens are only matched *before* the amount; "5000 USD", "7500 dollars", "200 bucks" are invisible. `_currency_code(None)` **defaults to INR** while every golden fixture without an explicit marker expects USD — a code-vs-spec contract conflict (see §6 decision D1). Currency words (`dollars?`, `bucks?`, `euros?`) need to join the token map.
- **S3 — keyword-free anchors:** "to spend", "have", "between X and Y" phrasings have no anchor at all. ⚠️ **Precision warning from the prototype itself:** a loose `of\s+` anchor false-positived on "family **of 4** to visit Costa Rica" — anchors must stay tight (spend/have/between + optional around/about/roughly), never bare prepositions.
- **S4 — scope rules:** `per day / a day` → `daily` (amount formatted `200/day` per golden); `per person` → `per_person`; else `total`.
- **S5 — flexibility rules:** currently only the literal "flexible budget" regex exists. Golden convention: firm from `max/only/no more than/exactly/at most`; soft from `around/about/approx/roughly/between`; **unmarked → soft** (11 of 12 fixtures encode this).
- **S6 — range separators:** "between 4000 and 6000" — the high-bound group must sit *before* the greedy unit/`\s*` segments or the separator gets swallowed (prototype bug we hit and fixed; same hazard exists in the shipped regexes).

## 4. Prototype validation

`tmp/rq01_prototype.py` (kept as evidence, not shipped):

| Metric | Current pipeline | Prototype rules |
|---|---|---|
| Fixture-level fully-correct | 2/12 (0.167) | **11/12 (0.917)** |
| Field-level recall | 7/48 (0.146) | **44/48 (0.917)** |
| Precision | 1.0 | 1.0 on these fixtures (but see §6 warning) |

Remaining prototype miss: `budget_hard_004` only (H1).

## 5. Falsifier application & verdict

Backlog falsifier: *"If >50% of failures are 'needs-LLM', the deterministic boundary must be redrawn deliberately."* Actual: **1/12 = 8% needs-LLM.** The deterministic core survives; the F1 0.2857 measured rule coverage, not the paradigm. **Go/no-go: GO on deterministic extraction; no-go on hybrid extraction for budget.**

## 6. Decision points & risks

- **D1 — currency default (needs ratification):** change `_currency_code` fallback INR→USD, keeping INR for `₹/rs/lakh/crore` inputs. Golden is the spec; today's INR default silently mislabels all unmarked Western-currency trips. Recommend: change default to USD.
- **D2 — unmarked flexibility = soft:** golden encodes this convention; implement as default, not as per-keyword inference only.
- **Precision pressure is unmeasured:** the golden set has exactly **1 negative fixture**. Loosening anchors (S3) will raise recall; nothing currently verifies precision didn't regress. Before/with the rule package, **expand the negative set** (≈8 fixtures: dates, headcounts, prices-of-other-things, "family of 4"-style traps — the prototype already tripped on one).
- **H1 (hard_004 revision resolution):** defer. A narrow rule (number following "but … realistic/actually/now") is possible but was the only case with genuine ambiguity; revisit only if stakeholders require 12/12.

## 7. Exit — becomes implementation task

Registered as **F-18** in `Docs/review/FINDINGS_TASKS_CONSOLIDATED_2026-08-30.md`: implement rule package S1–S5 (+S6) in `_extract_budget`, resolve D1/D2, expand negative fixtures, and target the budget gate green. Estimated effort: ~1 day including negative fixtures and gate verification.

## Checklist applied: IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md
