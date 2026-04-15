# Issue Review: Hedging Signals and Destination Extraction Bugs

**Date**: 2026-04-15
**Status**: Resolved
**Severity**: Medium-High
**Related**: `travel_agency_process_issue_review_2026-04-15.md` (Gap 1 fix)

## Root Cause Investigation

Following the fix for the "Andaman or Sri Lanka" multi-candidate bug, fresh verification
revealed three additional problems in the destination extraction and severity pipeline.

### Bug 1: "maybe Singapore" classified as `definite` instead of `semi_open`

**Reproduction**: `ExtractionPipeline.extract("maybe Singapore from Bangalore, 4 people...")`

```
destination_candidates: value=['Singapore'], confidence=0.5, status=definite
```

**Root cause**: `_extract_destination_candidates()` (extractors.py:187-193) correctly
detects "maybe X" and returns `status="semi_open"`. But `_extract_from_freeform()`
(extractors.py:726-733) sets `packet.facts["destination_status"]` using the raw
return from `_extract_destination_candidates`. The problem is that `_extract_destination_candidates`
returns `"semi_open"` for the "maybe" match on line 193, BUT the code on line 726
only checks `if dest_candidates or dest_status in ("open", "undecided")`. When
`dest_candidates=["Singapore"]` and `dest_status="semi_open"`, the condition is True
because `dest_candidates` is truthy, and `confidence` is correctly set to 0.7 on
line 729. Wait, let me re-check...

Actually, line 729: `0.7 if dest_status == "semi_open" else 0.5`. For "maybe Singapore",
`dest_status` IS "semi_open" (from line 193), so confidence should be 0.7. But the
trace shows confidence=0.5 and status="definite". Let me re-trace...

The trace output was:
```
maybe Singapore: candidates=['Singapore'], conf=0.5, status=definite
```

But `_extract_destination_candidates("maybe Singapore from Bangalore, 4 people...")`
returns `(["Singapore"], "semi_open", "maybe Singapore")`.

Line 729: confidence = 0.7 if semi_open else 0.5. So it should be 0.7.

The issue is that `_extract_destination_candidates` processes the FULL text. The regex
for "maybe" on line 188-193 checks `text_lower` which is the full input. Let me check
what the actual extraction flow produces...

**Actually**: On re-reading the trace, I see `conf=0.5` and `status=definite`. This
means the "maybe" regex on line 188 may be getting beaten by the single-destination
regex on line 165-184, which runs FIRST and finds "Singapore" directly, returning
`(["Singapore"], "definite", "Singapore")`. The "maybe" check on line 188 only runs
if the earlier pattern didn't match.

This is the real bug: the single-destination regex (line 165-184) matches "Singapore"
before the "maybe" pattern can add the hedging context. "maybe Singapore" → regex finds
"Singapore" → returns definite → "maybe" is never checked.

### Bug 2: `destination_candidates=["We"]` from "We want to go somewhere nice"

**Reproduction**: `_extract_destination_candidates("We want to go somewhere nice from Bangalore")`

```
candidates=['We'], status=definite, raw=We
```

**Root cause**: `_DESTINATION_RE` matches "We" as a capitalized word, and
`is_known_destination("We")` presumably returns True (or the check doesn't filter
it). The "We" pronoun gets treated as a destination name.

### Bug 3: `value_vague` on `destination_candidates` classified as `advisory` instead of `blocking`

**Reproduction**: Packet with `destination_candidates=["Singapore"]` and ambiguity
`(destination_candidates, value_vague, "maybe Singapore")`, all blockers filled.

```
decision_state: PROCEED_TRAVELER_SAFE
ambiguity severity: advisory
```

**Root cause**: `AMBIGUITY_SEVERITY` (decision.py:209-220) has no explicit entry for
`("destination_candidates", "value_vague")`. It falls through to the default "advisory".
But a hedged destination ("maybe Singapore") should be treated like an unresolved
alternative — you cannot proceed as if the destination is confirmed.

When a traveler says "maybe Singapore", they haven't committed. The system should ask
for confirmation, not proceed as if the destination is locked in at low confidence.

## Architectural Analysis

These are all NB01 problems, consistent with the pattern from Gap 1:

1. **Bug 1** is an extraction-ordering problem in `_extract_destination_candidates()`.
   The single-destination regex matches "Singapore" and returns early with "definite"
   status before the "maybe" context can be captured. The hedging signal is partially
   captured as a `value_vague` ambiguity, but the destination itself is marked
   "definite" with 0.5 confidence, which fills the blocker.

2. **Bug 2** is a geography filter problem. `_DESTINATION_RE` should not match
   personal pronouns. `is_known_destination("We")` should return False.

3. **Bug 3** is a severity classification gap. `value_vague` on a destination field
   is functionally equivalent to `unresolved_alternatives` — the traveler hasn't
   committed. It should be blocking, not advisory.

## Proposed Fixes

### Fix 1: Reorder extraction — check hedging patterns before single-destination match

In `_extract_destination_candidates()`, move the "maybe" and "or" pattern checks
BEFORE the single-destination regex. When "maybe Singapore" is detected, extract it
as `(["Singapore"], "semi_open", "maybe Singapore")` with the proper confidence.

The current order is:
1. "or" pattern (semi_open)
2. Multi-destination regex (semi_open)
3. Single-destination regex (definite) ← matches "Singapore" before "maybe" can
4. "maybe" pattern (semi_open) ← never reached

Proposed order:
1. "or" pattern (semi_open)
2. "maybe" pattern (semi_open)
3. "somewhere/open" patterns (open)
4. Multi-destination regex (semi_open if 2+, definite if 1)
5. Single-destination regex (definite, fallback)

This also means we should check the FULL context around a match for hedging signals,
not just the isolated "maybe" at start of text.

### Fix 2: Add pronoun and common-word filter to destination extraction

Add a stop list (`_DESTINATION_STOP_WORDS`) of capitalized words that should never
be treated as destinations: "We", "I", "My", "Our", "The", "This", "That", etc.
Apply before `is_known_destination()`.

Also, `is_known_destination("We")` should return False. Check the geography filter.

### Fix 3: Add `("destination_candidates", "value_vague")` as `blocking` to AMBIGUITY_SEVERITY

In `decision.py:209-220`, add:
```python
("destination_candidates", "value_vague"): "blocking",
```

This ensures that a hedged destination ("maybe Singapore") with a `value_vague` ambiguity
triggers ASK_FOLLOWUP, not PROCEED_TRAVELER_SAFE.

## Priority Assessment

| Bug | Impact | Effort | Priority |
|-----|--------|--------|----------|
| Bug 1: maybe→definite | Medium (traveler sees wrong confidence) | Medium (reorder extraction) | P1 |
| Bug 2: "We" as destination | Low (rare, obvious) | Low (add stop words) | P3 |
| Bug 3: value_vague→advisory | High (proceeds on unconfirmed destination) | Low (1-line config change) | P0 |

Fix 3 is the highest impact and lowest effort — a single config line change.
Fix 1 is important but touches extraction ordering which has knock-on effects.
Fix 2 is low priority but easy to add while we're in the extraction code.

## Proposed Sequence

1. **Fix 3 first** (P0, 1 line, immediate safety improvement)
2. **Fix 1 second** (P1, extraction reordering with tests)
3. **Fix 2 third** (P3, stop words, easy add-on while touching extraction)

## Resolution

All three fixes implemented and verified. 127 tests pass, 0 regressions.

### Fix 3: `("destination_candidates", "value_vague")` → blocking

`decision.py:210-211` — Added `("destination_candidates", "value_vague"): "blocking"` to `AMBIGUITY_SEVERITY`.

Now when NB01 flags "maybe Singapore" as `value_vague`, NB02 blocks progression to `PROCEED_TRAVELER_SAFE`. The system asks "Where would you like to go?" instead of assuming Singapore is confirmed.

### Fix 1: Hedging patterns checked before general destination regex

`extractors.py:126-197` — Reordered `_extract_destination_candidates()`:
- "maybe X" pattern (line 147-152) now runs BEFORE the general single/multi-destination regex
- "thinking about/perhaps/considering" hedging patterns (line 154-160) added and checked before general regex
- Both return `status="semi_open"` which triggers NB01's `value_vague` ambiguity detection downstream

This means "maybe Singapore" now extracts as `(["Singapore"], "semi_open", "maybe Singapore")` instead of `(["Singapore"], "definite", "Singapore")`.

### Fix 2: Stop-word filter prevents pronoun extraction

`extractors.py:175-176` — Added `_DESTINATION_STOP_WORDS` set (`{"we", "i", "my", "our", "the", "this", "that", "it", "they", "he", "she", "us"}`) filtered before `is_known_destination()`.

"We want to go somewhere nice" now returns `([], "open")` instead of `(["We"], "definite")`.

### Regression tests

`tests/test_nb01_v02.py::TestHedgingExtractionOrder` (5 tests):
- `test_maybe_pattern_produces_semi_open`
- `test_thinking_about_pattern_produces_semi_open`
- `test_perhaps_pattern_produces_semi_open`
- `test_definite_destination_still_definite`
- `test_or_pattern_still_sem_open`

`tests/test_nb01_v02.py::TestStopWordFilter` (2 tests):
- `test_we_pronoun_filtered`
- `test_real_destination_after_pronoun`

`tests/test_nb02_v02.py::TestDestinationAmbiguitySynthesis` (4 tests from Gap 1 fix):
- `test_multi_candidate_destination_never_proceeds_traveler_safe`
- `test_single_candidate_destination_no_synthesis`
- `test_existing_ambiguity_no_duplicate_synthesis`
- `test_candidate_aware_question_for_destination`