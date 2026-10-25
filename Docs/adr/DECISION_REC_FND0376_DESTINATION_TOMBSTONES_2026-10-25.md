# Decision Record — FND-0376: destination lists on reprocess (precedence + operator tombstones)

**Date:** 2026-10-25 · **Decided by:** ZCode (owner delegated reversible
design decisions to doctrine-guided agents; revisable per the process below)
· **Status:** ADOPTED, implemented · **Finding:** FND-0376 (P3)

## Context

On reprocess, the pipeline re-extracts a fresh destination-candidates list.
Two humans can disagree with it: the traveler (new note → new intent) and the
operator (hand-curation — corrections, removals). Three candidate rules:

1. **Precedence (replace):** re-extracted list wins. Correct when the
   traveler changed their mind; wrong when the operator was correcting an
   extraction error — deterministic re-extraction re-commits the same error
   over the operator's fix.
2. **Merge (union):** operator curation survives; wrong when the operator
   *removed* a candidate — union resurrects the removal (the
   clear-destination path regresses).
3. **Precedence + operator tombstones (ADOPTED):** re-extracted list wins,
   except candidates an operator previously removed (or displaced by a
   hand-set destination) are filtered out — unless the traveler's own new
   note explicitly re-names that candidate, in which case the tombstone
   yields to the customer (canonical customer>operator).

## Chosen path

Operator destination edits via `PATCH /trips/{id}` record **tombstones**:
the displaced/removed destination value is appended to the trip's
`destination_tombstones` list. At reprocess-save,
`_preserve_authoritative_facts` filters the fresh re-extracted
`destination_candidates` through the tombstones. A tombstone is voided when
the new `raw_note` names that candidate explicitly (the traveler overrode
it — their words, their latest intent).

## Tradeoffs / assumptions / risks

- Assumption: the scalar `destination` hand-edit and candidate-list edits are
  the operator surfaces that matter (verified: `TripPatchRequest.destination`).
- Risk: tombstone list grows unbounded — bounded in practice (one entry per
  operator edit); revisit if trips show >32 entries.
- Risk: tombstones could hide a re-extracted *correction* — mitigated by the
  raw_note-override rule above.
- Rollback: filter is additive and isolated in
  `_preserve_authoritative_facts`; disabling the filter restores pre-change
  behavior with no data migration.

## Validation plan + revisit trigger

- Unit tests: tombstone filters re-extracted garbage; traveler re-naming
  voids the tombstone; no tombstones → behavior unchanged (FND-0309 merge
  intact); operator carry-forward coexists.
- Regression: persistence + extraction suites.
- Revisit trigger: any operator report of a vanished re-extracted candidate,
  or a design change to the clear-destination path (server.py sync seam).
