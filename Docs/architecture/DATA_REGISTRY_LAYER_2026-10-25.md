# Data Registry Layer — deterministic, data-based resolution for intake (2026-10-25)

## Principle (owner directive)

Whatever is deterministic and *can* have a data-based approach MUST have one —
the way cities do (GeoNames 590k gazetteer + `is_known_city_normalized`). Two
more domains now follow that precedent; both were previously ad-hoc logic or
absent entirely.

## Currency registry (`src/intake/currency_registry.py`)

**Problem it removes:** the token→ISO-4217 table lived as a closure literal
inside `_extract_budget` — private data, unsharable, second copies guaranteed to
fork (proposal compiler, commercial analytics).

**Shape:** one table (`CURRENCY_TOKENS`), one API (`resolve_currency_token`),
`None` = "not a currency marker". Crucially the POLICY (what an *unmarked*
amount means — FND-0341's agency-default answer) stays in the extractor/
orchestration; the registry is only what a marker IS. Data vs policy, separated.

**Migration:** `_extract_budget._currency_code` now delegates to the registry —
zero behavior change (11/11 currency tests), just the data moved to the shared
home where the next consumer (e.g. quote-vs-budget comparison) uses it without
forking.

## Holiday registry (`src/intake/holiday_registry.py`)

**Problem it removes:** festival references ("during Diwali", "after Dasara",
"plan by Christmas", "Bakrid pe jaana") produced *nothing* — the single
highest-signal date anchor in Indian travel talk was invisible to extraction.

**Shape (two data sources, clean separation):**
1. **Name data — curated** (`HOLIDAY_REGISTRY`): canonical festivals + aliases
   (regional spellings: deepavali/dipavali; Hinglish: bakrid, ramzaan;
   colloquial: meethi eid/big eid; global: xmas/nye) + country scope. One
   compiled alternation, longest-first, word-ish boundaries ("diwali party"
   matches; "diwaliskr" doesn't).
2. **Date data — the `holidays` package** (new dependency, 100+ countries):
   authoritative per-year computation *including lunar/movable holidays*
   (Diwali 2026 = Nov 8). Hand-rolling lunar math is the exact failure mode
   this replaces — the package-first rule (AGENTS.md) applies with force.

**Resolution contract** (`resolve_holiday_window`): package-computed exact date
for the nearest FUTURE occurrence within the sane intake window (current year
.. +3, matching `_classify_date_year`'s X-03 window) > curated approximate
window for month-scale festivals the package can't list (Ramadan, Navratri,
Onam) — always `approximate: True`, never a fake exact date > None (abstain
honestly). A past-this-year package date rolls to next year (future-only,
test-pinned).

**Extraction integration** (rides the P-3 occasion→window seam landed the same
day, `DECISION_REC_P3_OCCASION_WINDOW_2026-10-25.md`):
- `holiday_reference` derived signal (verified maturity) — the festival name(s).
- Multiple festivals recorded in `packet.metadata["holiday_references"]`.
- When NO real date_window exists: soft date_window *hypothesis* ("window
  covering 2026-11-08 (Diwali)") — never a fact; the traveler confirms exact
  dates and the ask still fires. Approximate festivals get lower confidence.
- A real extracted window always wins (test-pinned: "20-28 Dec trip around
  Christmas" → fact kept, no hypothesis).
- Fault-tolerant: registry failure cannot fail extraction (guarded import).

**"During/after/around" phrasing (SHIPPED same day):** `find_holiday_references`
captures the preposition before each reference as `relation` — during (default),
after, before (by/till/until fold in), around — and the date_window hypothesis
is shaped accordingly: "window **covering** 2026-11-08 (Diwali)" vs "window
**starting after** 2026-11-08" vs "window **ending by** 2026-12-25 (Christmas)".
The registry contract didn't change; the relation is derived at match time.

## Extending

- New festival/alias: add one entry to `HOLIDAY_REGISTRY` (aliases lowercase,
  countries ISO-2 or "*"); if the package lists it, give `hints` substrings;
  if month-scale only, give `approx`. `test_registry_hygiene` enforces
  uniqueness and hints.
- New currency token: one line in `CURRENCY_TOKENS`; `test_currency_registry_
  is_single_source_of_truth` pins the shared table.

## Verification (2026-10-25)

- `tests/test_holiday_registry.py` 12/12: alias matching, exact package
  resolution (Diwali 2026-11-08), future-only rollover (Diwali → 2027-10-29
  after Nov 2026 passes; Thanksgiving → 2028 from Dec 2027), honest
  approximate flag (Ramadan), abstention, registry hygiene (alias-collision
  guard), extraction closed loop incl. multi-festival + real-window-wins +
  generic-"holiday"-word no-false-positive.
- Currency tests 11/11 (unchanged behavior after registry migration).
- Extraction regression sweep: extraction/mandates, truthfulness, epistemic,
  traps, block3, adversarial corpus, confirmation — green (see session log).
- Package provenance: `holidays==0.107` added to the root pyproject.
