# Product contract decision package — D-01 / D-02 / D-03

**Date:** 2026-09-04\
**Status:** research and recommendation complete; implementation is gated on
contract ratification\
**Persona lens:** PER-0164 — Assumption Auditor\
**Related evidence:** `Docs/exploration/MISC_PROBES_N06_N09_D04_F05_2026-09-02.md`,
`Docs/exploration/MASTER_FINDINGS_TASKS_INVENTORY_2026-09-02.md`\
**Owner decision gate:** product owner must ratify the canonical wire contract
before schema/API/UI changes are promoted.

## Why this package exists

The current system contains several compatible-looking duration and destination
representations. A consumer can therefore appear to work while silently
changing the meaning of a trip. These are product semantics, not formatting
details: nights versus calendar days affect pricing and visa rules; flight
inclusiveness affects budget truth; country scope versus city candidates affects
supplier, visa, and duty-of-care decisions.

The package records what is observed, what the first-principles contract should
be, what can be implemented additively, and what must not be guessed.

## Executable evidence snapshot (2026-09-04)

The pre-ratification boundary is covered by
`tests/test_product_contract_decisions_d01_d03.py`. It is deliberately a
current-state probe: the assertions make the missing contract visible without
promoting compatibility behavior into a new product promise.

Command:

```text
PYTHONPATH=. .venv/bin/pytest -q tests/test_product_contract_decisions_d01_d03.py
```

Result: **6 passed** (1.46s), followed by a clean Ruff check for the probe.

Observed outputs from the same live checkout:

| Probe | Current output | Contract implication |
|---|---|---|
| `2026-10-01` → `2026-10-06` | `date_start` and `date_end` are emitted; no `trip_nights`, `trip_days`, `duration_amount`, or `duration_unit` | Date interval exists, but no canonical duration projection exists. |
| Structured `{ "duration": 5, ... }` | `facts["duration"] == 5` | A unitless compatibility fact is accepted; it is not safe to use as nights or calendar days. |
| `including`, `excluding`, or `not sure ... includes flights` | budget fields are emitted; no `flights_inclusiveness` fact | Flight scope is currently lost from the typed packet and must not be inferred downstream. |
| `10 days in Japan, you pick` | `destination_candidates == ["Japan"]` | Country scope is currently coerced into the city/candidate slot. |
| `Japan, thinking Tokyo + Kyoto` | `destination_candidates == ["Japan", "Tokyo", "Kyoto"]`, status `semi_open` | Country and city/place concepts still collide in one list; no independent scope or containment fact exists. |
| `Tokyo + Kyoto` | `destination_candidates == ["Tokyo", "Kyoto"]`, status `semi_open` | City-set extraction is useful, but remains unresolved candidate intent rather than committed routing. |

The probe command is local deterministic evidence (S1/S2 depending on the
consumer); it is not provider, hosted, browser, customer, or production proof.

## D-01 — trip duration

### Observed state

- Free-form extraction and structured imports use `duration` in some paths.
- Decision/cache and policy code consume `duration_days`.
- Suitability and fees consume `trip_duration_nights` or `duration_nights`.
- Date extraction already produces `date_start` and `date_end` in supported
  cases.
- The same integer can therefore be interpreted as nights, calendar days, or a
  user-entered duration string depending on the consumer.

### Recommended canonical contract

1. `date_start` and `date_end` are the authoritative interval when observed.
2. `trip_nights` is derived as `(date_end - date_start).days` and must be a
   positive integer.
3. `trip_days` is derived as `trip_nights + 1` only for a stay whose arrival
   and departure dates are both inclusive; it must never be inferred from a
   free-form integer without a unit.
4. An explicitly stated duration without dates is retained as
   `duration_amount` plus `duration_unit` (`nights`, `days`, or `unknown`) and
   remains unresolved until the operator or traveler confirms the unit.
5. Existing `duration_days`, `duration_nights`, and `trip_duration_nights`
   consumers must become compatibility projections from this canonical model,
   not independent sources of truth.

### Implementation sequence

- Add a typed duration value/provenance object to the canonical packet schema.
- Normalize date-derived values first; preserve source excerpts and authority.
- Update fees, policy, cache keys, suitability, and frontend labels to consume
  the canonical projection.
- Add contradiction tests for `5 nights` versus a six-date interval and for
  unitless `5 days` text.
- Remove or deprecate ambiguous aliases only after all call sites are migrated
  and the generated schema/types pass.

## D-02 — flight inclusiveness

### D-02 — Observed state

Budget notes commonly say that flights may or may not be included, and some
existing documents model this as a binary field. The evidence does not justify
turning an omitted or hedged statement into either inclusion or exclusion.

### D-02 — Recommended canonical contract

Use a tri-state value:

```text
included | excluded | unknown
```

The slot must also retain:

- the exact source excerpt;
- confidence and authority;
- an ambiguity record when the text contains “not sure,” “maybe,” or a
  conflicting later statement.

`unknown` is the safe default. It must not be rendered as “flights included,”
used to pass a budget check, or used to issue a supplier/payment action.

### D-02 — Implementation sequence

- Add a typed enum/slot and preserve the existing raw budget text.
- Map explicit phrases (`includes flights`, `excluding airfare`) to the two
  determinate states.
- Map hedged, omitted, or contradictory phrases to `unknown` plus a follow-up
  question.
- Update budget, quote, and frontend copy to render “not confirmed” instead of
  inventing a binary value.
- Add regression cases for explicit, omitted, hedged, and contradictory text.

## D-03 — country versus city multi-destination semantics

### Observed evidence

The existing city-set pass correctly extracts examples such as
`Tokyo + Kyoto`, but a note such as “Japan — thinking Tokyo + Kyoto” returns
country and cities in one untyped list. Country-only cases currently return the
country as a destination candidate, while flight, supplier, visa, and route
consumers have no independent country-scope slot. The probe record therefore
recommends retaining country as a containing fact while keeping city candidates
separately. An earlier probe briefly observed a missing `Kyoto` result while the
shared checkout was changing; that transient output is not treated as current
truth and is retained only as a warning against relying on incidental candidate
completeness.

### D-03 — Recommended canonical contract

Store three separate concepts:

1. `destination_countries`: explicitly named country/region scope;
2. `destination_candidates`: independently resolved city/place candidates;
3. `destination_status`: `definite`, `semi_open`, or `open` for the candidate
   set, with an ambiguity record when country scope and city candidates conflict.

Examples:

| Input | Country scope | City candidates | Status |
|---|---|---|---|
| `10 days in Japan, you pick` | Japan | `[]` | open |
| `Japan, thinking Tokyo + Kyoto` | Japan | Tokyo, Kyoto | semi_open |
| `Tokyo + Kyoto` | `[]` | Tokyo, Kyoto | semi_open |
| `Japan and Thailand, Tokyo + Bangkok` | Japan, Thailand | Tokyo, Bangkok | semi_open + scope conflict |

Country containment should suppress a false cross-country ambiguity when a known
city belongs to the named country. A city list must not erase the country
scope, and a country-only request must not be fabricated into a city.

### D-03 — Implementation sequence

- Add a country extraction branch using the canonical geography dataset and
  preserve the source span.
- Set `destination_countries` independently of the existing city-set return
  value; keep the current three-value helper signature for compatibility while
  the packet gains the additional slots.
- Use `get_city_country` to classify containment and generate a typed scope
  ambiguity only when countries and cities disagree.
- Add structured-import support and generated type/schema coverage.
- Require operator/traveler confirmation before supplier or visa actions when
  scope remains `open` or conflicting.

## Alignment decision

These recommendations are first-principles aligned because they preserve the
traveler's actual statement, separate observed facts from derived projections,
and fail closed when unit or scope is unknown. They are long-term aligned
because one canonical interval, enum, and destination-scope model can feed
pricing, policy, supplier, UI, and audit consumers without parallel meanings.
They are doctrine aligned because the recommendation is documented separately
from implementation, evidence excerpts are retained, and no local test is
represented as hosted/provider proof.

## Decision gate and evidence required

The product owner should ratify the three canonical contracts above (or record
an explicit alternative) before implementation. After ratification, the
implementation slice must include schema migration, extractor/structured
input updates, generated types, consumer migration, focused regressions, full
backend/frontend gates, and a browser copy check. Until then, D-01/D-02/D-03
remain **DECIDE → IMPLEMENT**, not silently closed.

## Atomic post-ratification implementation package

No code path should begin this package until the product owner records the
chosen contract (or an explicit alternative) in this document and the decision
log. Once ratified, execute in this order:

1. **Schema/value objects:** add one canonical duration value with amount,
   unit, interval derivation, provenance, and contradiction state; add a
   `flights_inclusiveness` enum/slot; add independently typed country scope,
   place candidates, status, and scope-conflict records. Update the canonical
   packet schema and generated mirrors in the same change.
2. **Extraction/import:** map explicit date intervals and explicit duration
   units; retain unitless duration as unresolved; map explicit flight phrases
   and hedges to `included`/`excluded`/`unknown`; extract country scope without
   removing city candidates; preserve source spans and authority for every new
   slot. Structured imports must accept only the ratified shape.
3. **Consumer migration:** migrate fee, cache-key, suitability, visa,
   itinerary, quote, proposal, supplier, and frontend projections to one
   canonical resolver. Keep legacy aliases as read-only compatibility
   projections until call-site inventory and generated-type checks are green.
4. **Safety gates:** block supplier, visa, payment, and traveler-facing
   assertions when duration unit, flight scope, or destination scope is
   unknown/conflicting. Add explicit follow-up questions and operator-review
   transitions rather than silently selecting defaults.
5. **Verification:** add contradiction/ambiguity fixtures, independent
   producers, structured round-trip tests, mutation tests, full backend and
   frontend gates, authenticated browser copy checks, and an audit receipt that
   distinguishes local deterministic evidence from hosted/provider evidence.
6. **Promotion/recovery:** define migration/backfill behavior, replay and
   rollback semantics, compatibility sunset criteria, and a release owner. No
   legacy alias is removed until the supersession workflow has field-by-field
   and call-site evidence.

### Owner-ratification questions

- For an explicit “5 days” without dates, does the business mean five nights,
  five calendar days, or an unresolved value requiring follow-up?
- Is the budget's flight scope allowed to remain `unknown` through shortlist,
  or does a particular stage require a blocking follow-up?
- Are country-only requests intentionally open over cities, and can a named
  country plus named cities be treated as containment when every city resolves
  into that country? What is the policy when they conflict?
- Which owner is responsible for accepting the compatibility migration and its
  release/rollback decision?

No Git staging, commit, push, reset, checkout, stash, or cleanup was performed.
