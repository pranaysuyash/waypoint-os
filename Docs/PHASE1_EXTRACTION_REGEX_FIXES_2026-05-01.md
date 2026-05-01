# Phase 1: Extraction Regex Fixes — Completion Record

**Date**: 2026-05-01
**Approval**: Approved with caveat

## Files Changed

| File | Change |
|------|--------|
| `src/intake/extractors.py` | 9 edits: stop words, origin postposition, destination truncation, budget 5th pattern, date `ya`, party `bachhe`, Hinglish origin extraction, lowercase fallback |
| `tests/test_extraction_fixes.py` | +6 test classes, +30 new tests |
| `src/intake/geography.py` | +1 entry `United Arab Emirates` to `_COUNTRY_DESTINATIONS` |

## Before/After

| Input | BEFORE | AFTER |
|-------|--------|-------|
| `3L` | None | min=300000, max=300000 |
| `3L tk` | None | min=300000, max=300000 |
| `300k` | None | min=300000, max=300000 |
| `Bangalore se Sri Lanka` | dest=['Bangalore', 'Sri', 'Lanka'] | dest=['Sri Lanka'], origin=Bangalore |
| `Bangalore ru Sri Lanka` | dest=['Bangalore', 'Sri', 'Lanka'] | dest=['Sri Lanka'], origin=Bangalore |
| `2 adults 2 bachhe` | size=2, comp={adults:2} | size=4, comp={adults:2, children:2} |
| `March ya April 2026` | None | 'window' confidence |
| `singapore jana hai` | [] | ['Singapore'] definite |
| `Andaman Sri Lanka Bangalore se 2 adults 2 bachhe 3L March ya April` (full pipeline) | dest=[], origin=None, budget=None, dates=None | dest=['Sri Lanka', 'Andaman'], origin=Bangalore, budget=3L, dates='window' |

## Known Limitations

### `tak` budget semantics
`"3L tak"` parses as exact budget `min=max=300000`. Correct semantic meaning is upper-bound budget (`max=300000, min=None`). Not fixed because the current `Normalizer.parse_budget()` schema uses `min`/`max` always paired for single values. Requires future schema support for `upper_bound` / `ceiling_modifier` / `budget_semantics`.

### Multi-word destination via DB truncation
The fix uses right-to-left truncation within each capitalized word chain matched by `_DESTINATION_RE`. This works correctly for known destinations in the geography DB but does not handle unknown multi-word names.

### Lowercase destinations
Single-word only. Does not handle lowercase multi-word destinations (unlikely in practice).

## Test Results
- 174 tests pass across: `test_extraction_fixes.py`, `test_block3_extraction.py`, `test_geography.py`, `test_geography_regression.py`, `test_intake_pipeline_hardening.py`, `test_singapore_canonical_regression.py`
- Zero regressions from existing 110 baseline tests
