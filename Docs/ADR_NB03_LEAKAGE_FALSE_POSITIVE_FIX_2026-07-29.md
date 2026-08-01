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
