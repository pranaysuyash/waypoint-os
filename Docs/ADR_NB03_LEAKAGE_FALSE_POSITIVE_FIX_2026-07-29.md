# ADR: NB03 Leakage Guard False-Positive Fix

**Status**: Accepted  
**Date**: 2026-07-29  
**Context**: Leakage guard blocker analysis from Month 6 retention audit

---

## Context

The `check_no_leakage()` function in `src/intake/safety.py` scans traveler-facing
content for internal pipeline vocabulary before export. The function uses
`FORBIDDEN_TRAVELER_CONCEPTS` — a set of bare internal terms — with word-boundary
regex matching.

**Problem**: Legitimate travel copy containing these base words was triggering
false-positive leakage blocks, preventing proposal export:

- `"unknown beaches of Goa"` → flagged on `"unknown"`
- `"some ambiguity about visa dates"` → flagged on `"ambiguity"`
- `"no blockers on your itinerary"` → flagged on `"blockers"`

These blocks were preventing agents from sending proposals to clients without
manual intervention, causing operational friction.

**Root cause**: The leakage guard was designed for data-field scanning (where
`unknown` in a `decision_state` field is always suspicious) but was applied to
free-text prose where the same words have natural meaning.

---

## Decision

Implemented a 3-gate context-aware matching strategy in `check_no_leakage()`:

### Gate 1: Word-boundary match (unchanged)
Same regex pattern `\b<term>\b` to avoid substring matches.

### Gate 2: `INTERNAL_CONCEPT_FIELD_MARKERS` override (new)
Pattern: `_INTERNAL_FIELD_MARKER_PATTERN`
- Checks 80-char window around the match for internal field name patterns
  (e.g. `decision_state`, `confidence_score`, `hypothesis_stack`)
- When an internal marker is present → **always hard-flag** regardless of phrase context
- This catches real leakage: `"decision_state: unknown"` is flagged even if
  `"unknown"` would otherwise be in an allowed phrase

### Gate 3: `ALLOWED_TRAVEL_PHRASES` allowlist (new)
Set: `ALLOWED_TRAVEL_PHRASES`
- 120-char window around the match checked for known-safe collocations
- Examples: `"unknown beaches"`, `"some ambiguity"`, `"no blockers"`
- If an allowed phrase is found → **skip flagging** (false positive avoided)

**Evaluation order**: Gate 2 runs BEFORE Gate 3, so real leakage with internal
markers is never exempted by an allowed phrase.

---

## Alternatives Considered

### Alt 1: Remove "unknown" from FORBIDDEN_TRAVELER_CONCEPTS
- Rejected: `unknown` is genuinely diagnostic for leakage in field contexts
  (e.g. `budget: unknown`, `destination: unknown`)

### Alt 2: Use sentence-level NLP to classify intent
- Rejected for this layer: overkill for what is fundamentally a field-name vs.
  prose detection problem; NLP is used in Layer 2 of privacy_guard.py for
  entity detection, not concept scanning

### Alt 3: Split FORBIDDEN_TRAVELER_CONCEPTS into field-only vs. prose categories
- Deferred: a valid long-term improvement, but adds maintenance overhead
  without immediate benefit given Gate 2+3 cover the real cases

---

## Consequences

**Positive**:
- Eliminates false-positive proposal export blocks for common travel phrases
- Preserves hard detection of real internal field leakage (Gate 2 override)
- Zero new dependencies

**Negative / watch**:
- `ALLOWED_TRAVEL_PHRASES` must be maintained as product vocabulary expands
- Gate 2 radius (80 chars) is a heuristic; edge cases with long field names
  far from the forbidden term may still produce false negatives
- `test_safety_false_positives.py` regression suite added to catch regressions

---

## References

- `src/intake/safety.py` — implementation
- `tests/test_safety_false_positives.py` — 29-test regression suite
- Month 6 retention audit blocked-export analysis

## November 25, 2026 amendment for repeated terms

The original guard stopped after the first occurrence of each term in a field. An exempt “unknown beaches of Goa” could hide “the final status is unknown” several sentences later. Within the old 120-character window, an allowed phrase could also suppress an unrelated term such as “hypothesis.” Both examples reproduced before the change.

Policy revision 2 walks occurrences until it finds the first violation for each term in each field. An exemption must contain the occurrence being examined. Plural travel phrasing such as “unknown islands” and the existing internal-marker override remain covered. The diagnostic excerpt now includes the occurrence that triggered it.

The Workbench persists the policy revision with the digest of the draft it checked. Revision 1 was introduced earlier in this local implementation and can exist in replay data. Reopening a trip or replaying a saved inbound response with an earlier revision withholds the scoped result. Processing the inquiry again produces fresh evidence. Historical aggregate diagnostics remain available.

The two previously missed examples, an all-allowed control, and old-receipt invalidation pass in the scanner and draft-check regression suites. The broader local run covering those suites, NB03, the frozen end-to-end cases, privacy, the pipeline, inbound and state contracts completed with 282 passes.

### Editing and reopening a checked inquiry

An edit invalidates the earlier draft check immediately. An agency with automatic reassessment enabled can subsequently receive another pass even when the generated traveler wording is identical. The new run must have checked a draft for the edited source. Comparing the two wording digests alone cannot establish that.

The authenticated trip PATCH saves the edit and the accepted run ID in one conditional write before dispatch. The run ledger records the accepted trip revision. A superseded worker stops before assessment, and an edit during computation is protected by the existing conditional result write. The trip GET resolves the pending ID through the same tenant’s run ledger. Workbench subscribes to that run through its existing bounded monitor, then fetches the saved trip once on completion. A successful run has to supply a current receipt to light the green control. Failed or interrupted runs, and edits with reassessment switched off, leave the control unverified. Separately edited notes, itinerary text, structured inputs or run settings invalidate the editor’s displayed check.

The regression suites covered the PATCH aliases, reopening during a queued run, supersession, terminal failure, interrupted polling, the draft autosave race and separately edited inputs. The local authenticated SQL browser replay recorded a new run ID, the retained edited text and a pass that appeared without manual reload on desktop and in a mobile viewport. The mobile recording used browser emulation. [Desktop replay receipt](evidence/itinerary-diversity-2026-11-24/language-saved-auto-desktop-9230.json) and [mobile emulation replay receipt](evidence/itinerary-diversity-2026-11-24/language-saved-auto-mobile-emulation-143b.json).

The same run selection controls itinerary findings in the header, Risk Review, Trip Details and Decision. Removing the hotel from a mixed itinerary reduced the count from three to two and removed the hotel cutoff question. The rail transfer and step-free boarding questions remained. The operator saved the change in Workbench and saw the count and detail update without reloading. [Desktop edit replay](evidence/itinerary-diversity-2026-11-24/supplier-edit-desktop-94a8.json) and [mobile emulation edit replay](evidence/itinerary-diversity-2026-11-24/supplier-edit-mobile-emulation-2d08.json).
