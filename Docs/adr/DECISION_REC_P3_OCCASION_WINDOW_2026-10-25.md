# Decision Record — P-3: occasion anchor seeds a date-window hypothesis

**Date:** 2026-10-25 · **Decided by:** ZCode (delegated reversible design
decision) · **Status:** ADOPTED, implemented · **Origin:** Sim #3 audit U4;
Sim #2 F5 constraint class ("trip must COVER april 14 no matter what").

## Context

An occasion anchor ("45th anniversary on november 18th") is extracted as an
`occasion` fact, but nothing connects it to the travel window — `date_window`
stays unknown and the ask says nothing about the anchor. The traveler's real
constraint is *coverage*: the trip must span the occasion date, while exact
check-in/check-out dates remain theirs to confirm.

## Chosen path

When an occasion anchor exists and no `date_window` fact was extracted, seed
`date_window` as a **SOFT_HYPOTHESIS** (confidence 0.3, DERIVED):
`"window covering november 18th (anniversary)"`. Consequences by design:

- The unknown **stays blocking** (a hypothesis is not a fact), so the ask
  loop still requests exact dates — but the question can now carry the
  anchor as a suggested value via the decision stage's hypothesis-fed
  `suggested_values`.
- No gate is bypassed, no quote math consumes an unconfirmed window.
- A real extracted date_window always wins (seeding is skipped).

## Tradeoffs / risks / rollback

- Risk: a downstream consumer reading hypotheses as facts — none found
  (hypotheses are a separate packet section; consumers read `facts`).
- Risk: anchor has no year ("november 18th") — year confirmation stays with
  the traveler; the hypothesis deliberately does not invent one.
- Rollback: delete the seeding block; no data migration.

## Validation

- `run_spine_once` on the Sen note: occasion fact present, date_window
  hypothesis present with anchor text, date_window still unknown (ask fires),
  follow-up question emitted (ESCALATE floor).
- Regression: Sim #3 extraction + follow-up-wiring suites.
- Revisit trigger: if a consumer starts treating date_window hypotheses as
  facts, or occasion anchors gain year resolution.
