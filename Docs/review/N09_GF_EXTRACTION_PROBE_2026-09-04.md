# N-09 / GF-01 / GF-03 Extraction Probe — 2026-09-04

**Owner lane:** deterministic intake extractor probes and narrowly scoped
regressions\
**Review lens:** N-09 / GF-01 / GF-03, first-principles extraction truth\
**Evidence boundary:** local source, in-process helper probes, and focused
pytest only. No provider, database, hosted runtime, or external service was
used.

## Scope

This slice re-verified three previously open or partially verified behaviors:

1. salutations must not become destination entities;
2. colon budget connectives must preserve the amount and currency;
3. inline Destinations: labels with parenthetical night counts must compose
   with the city-set extractor without leaking nights or duplicating a later
   city set.

The probe also exercised two adjacent N-09 regressions already exposed by the
same city-set path: honorific salutations and a trailing season-scale date
phrase.

## Current implementation evidence

- src/intake/extractors.py:200-205 strips leading greetings and now accepts a
  narrow honorific set (Mr, Mrs, Ms, Miss, Mx, Dr, Prof) before the salutation
  name.
- src/intake/extractors.py:491-500 keeps scheduling-tail regexes separate from
  destination validation.
- src/intake/extractors.py:901-904 strips a trailing season window from a
  city-set element before resolving it, just as the existing time-tail
  handling does.
- src/intake/extractors.py:958-964 strips parentheticals from an explicit
  Destination(s): label and recursively uses the canonical destination helper.
- src/intake/extractors.py:1356-1360 accepts colon/connective forms such as
  Budget: Around ...

## Probe results

The following read-only probe ran through the destination and budget helpers:

| Case | Input | Result | Verdict |
|---|---|---|---|
| GF-01 basic | Hi Sam! we want to go to Bali in June | destination ['Bali'], definite | PASS |
| GF-01 honorific | Hello Dr. Rao! we want to go to Bali in June | destination ['Bali'], definite | PASS after narrow honorific fix |
| GF-02 colon connective | Budget: Around $14,000 total | min=max=14000, USD | PASS |
| GF-02 symbol range | Budget: $4,000 to $6,000 total | min=max=4000, USD | FOLLOW-UP; repeated symbol is not accepted by current range matcher |
| GF-03 parenthetical label | Destinations: Tokyo (4 nights) and Kyoto (6 nights) | ['Tokyo', 'Kyoto'], semi_open, raw tokyo, kyoto | PASS |
| GF-03 later city set | label above plus Also covering Osaka and Nara | ['Tokyo', 'Kyoto'], no accidental union/duplicates | PASS |
| N-09 season tail | We are covering Tokyo and Kyoto next spring | ['Tokyo', 'Kyoto'], semi_open | PASS after narrow schedule-tail fix |

The direct probe observed:

~~~text
GF-01-basic DEST= (['Bali'], 'definite', 'Bali') BUDGET= None
GF-01-honorific DEST= (['Bali'], 'definite', 'Bali') BUDGET= None
GF-02-colon-around DEST= ([], 'undecided', None) BUDGET= {'raw_text': 'budget: around $14,000', 'min': 14000, 'max': 14000, 'currency': 'USD'}
GF-02-colon-range-symbol DEST= ([], 'undecided', None) BUDGET= {'raw_text': 'budget: $4,000', 'min': 4000, 'max': 4000, 'currency': 'USD'}
GF-03-parenthetical DEST= (['Tokyo', 'Kyoto'], 'semi_open', 'tokyo, kyoto') BUDGET= None
GF-03-parenthetical-later-set DEST= (['Tokyo', 'Kyoto'], 'semi_open', 'tokyo, kyoto') BUDGET= None
N-09-season-tail DEST= (['Tokyo', 'Kyoto'], 'semi_open', 'we are covering tokyo, kyoto') BUDGET= None
~~~

## Narrow implementation

Two small additive changes were made:

1. Salutation parsing now allows a bounded honorific before the salutation
   name. It does not generalize into arbitrary person-name NER.
2. City-set parsing removes a trailing qualified season phrase (next/this/
   coming/in spring|summer|fall|autumn|winter) before resolving the final
   element. The date extractor remains responsible for the date window.

The explicit-label behavior was already present and required no change. It
removes (4 nights)/(6 nights) before recursively invoking the canonical
destination helper and intentionally returns the explicit label's city set
without unioning later prose.

## Focused tests

New focused file:

~~~text
tests/test_n09_gf_extraction_truth_boundary.py
~~~

Verification:

~~~bash
PYTHONPATH=. .venv/bin/pytest -q \
  tests/test_n09_gf_extraction_truth_boundary.py \
  tests/test_extraction_safety_x01_x08.py \
  tests/test_extraction_fixes.py
~~~

Result on 2026-09-04: **274 passed**.

The focused new tests cover:

- basic and honorific salutation exclusion;
- colon budget connective parsing;
- parenthetical night stripping;
- explicit-label precedence over a later city set;
- trailing season preservation in a multi-city set.

## Register reconciliation

The original register entries should be updated as follows:

- **GF-01:** the reported Hi Sam! behavior is verified and the honorific
  variant is now covered; retain only broader name-boundary research if desired.
- **GF-02:** Budget: Around $14,000 is verified and already closed by the
  existing register entry. The repeated-currency range variant is a separate
  follow-up, not evidence that the colon connective fix failed.
- **GF-03:** inline parenthetical labels and city-set composition are verified;
  the explicit-label early return is intentional and tested.
- **N-09:** the adjacent trailing-season city-set truncation is corrected and
  covered. Country-vs-city containment and lowercase or semantics remain
  separate design work and are not closed by this slice.

## Currency-symbol range follow-up — implemented 2026-09-04

Budget: $4,000 to $6,000 total previously returned a single 4,000 value. The
range matcher now accepts a repeated symbol or currency code before the high
amount and accepts a unit before the separator (`$4k-$6k`). The implementation
also rejects mixed-currency ranges rather than silently converting them. Tests
cover:

- $4,000 to $6,000;
- $4k-$6k;
- USD 4,000 to USD 6,000;
- mixed-symbol/currency ambiguity and malformed ranges.

Verification: `tests/test_budget_currency_ranges_2026_09_04.py` plus the
N-09/extraction safety tranche, **278 tests passed**. The parser still does not
silently infer a range from arbitrary numeric prose; it preserves raw text and
abstains when currency evidence conflicts.

## Safety and ownership

No unrelated extractor architecture was rewritten. The worktree remains dirty
with concurrent changes; all unrelated paths, untracked files, and prior
documentation were preserved. No Git staging, commit, push, reset, checkout,
stash, or clean operation was performed.
