# Extraction safety closure — X-01, X-02, X-03, X-07, X-08

Date: 2026-09-04\
Scope owner: extraction-safety lane\
Canonical implementation: `src/intake/extractors.py` (with the validation
warning contract in `src/intake/validation.py`)\
Focused tests: `tests/test_extraction_safety_x01_x08.py`

## Decision

Accept and implement the extraction-side fixes as an additive, fail-closed
boundary:

1. Normalize Unicode and remove unsafe zero-width, bidi, and control
   characters from the deterministic extraction view. Remove instruction-like
   role/clause spans from that view, while preserving the original
   `SourceEnvelope.content` unchanged for provenance and audit.
2. Keep years out of party-size parsing with a bounded numeric count parser.
3. Treat a known place before a month/trip marker as a destination-shaped
   statement when there is no verb. Preserve explicit years and classify past
   or implausibly distant years as derived signals; validation emits warnings
   rather than silently changing the date.
4. Reject season names as destination candidates, preserve all known members
   of a city set when the final member has a trailing time, and avoid treating
   the contraction prefix in “Let's” as a city.
5. Validate structured destination/origin/budget values through the canonical
   geography/safety boundary. Malformed traveler rows and non-mapping payloads
   abstain without crashing; valid structured rows remain importable.

This is intentionally not a general natural-language sanitizer or SQL parser.
It is a narrow intake contract: untrusted text cannot acquire authority, and
ambiguous or malformed structured values do not become canonical facts.

## Evidence and affected findings

| Finding | Previous failure | Implemented contract | Focused evidence |
| --- | --- | --- | --- |
| X-01 | `SYSTEM`/instruction prose could win budget and destination extraction | Trusted extraction view strips instruction clauses/role spans; original envelope retained | Injection regression asserts only `Bali`, budget `5000`, no `Cancun`, safety metadata present |
| X-02 | `June 2027` could be captured as party size `2027` | Numeric party count is bounded and traveler/date patterns remain separate | Bullet fixture asserts `party_size == 2`, never `2027` |
| X-03 | `Bali in June 2027` could be demoted to origin; year bounds were not surfaced | Verb-less known destination inference; derived `date_year_status`; validation warnings `past_year`/`implausible_year` | Bare destination and 2019/2099 regressions |
| X-07 | Season homonym, trailing time, and “Let's do japan” produced false/truncated candidates | Season blacklist; trailing-time cleanup; contraction-safe destination regex | Kyoto/spring, Tokyo+Kyoto+Osaka at 7pm, Japan regressions |
| X-08 | Malformed structured values crashed or admitted SQL-shaped strings | Shape checks, scalar/list validation, canonical geography resolution, SQL-shaped value rejection | malformed relationship/string/SQL payloads and non-mapping payload regression |

## Verification plan

Run from the repository root:

```bash
.venv/bin/pytest tests/test_extraction_safety_x01_x08.py -q
.venv/bin/pytest tests/test_extraction_safety_x01_x08.py tests/test_extraction_fixes.py tests/test_deterministic_extraction_traps_suite.py -q
.venv/bin/ruff check src/intake/extractors.py src/intake/validation.py tests/test_extraction_safety_x01_x08.py
```

The focused tests are deterministic, local, and expected to complete in under
one minute. A green local test is S1/S2 implementation evidence only; it is not
provider, browser, production, or customer evidence.

## Residuals and explicit non-goals

- The planning horizon is a conservative five years from the runtime year;
  policy owners may change that threshold in a future doctrine-backed task.
- Year warnings do not erase or rewrite the traveler's stated date.
- Structured input rejection is observable in packet metadata but does not
  manufacture an error fact; downstream validation should request correction
  through the existing unknown-field path.
- This lane does not modify decision policy, provider integrations, SQL
  execution, or release/Git state.
