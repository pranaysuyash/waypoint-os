# Progressive Commitment on the Journey Graph (E-commit)

**Status:** exploration package E-commit (PER-0443) — design ratified into code the same day.  
**Problem (AT-02 / AT-01 / AT-03):** search, hold, book, and ticket are collapsed inside `fulfill_accepted_proposal`. The sandbox adapter returns `TICKETED_CONFIRMED`. A second POST issues another VCC/PNR. The JDG schema exists but was not the runtime itinerary.  
**Doctrine:** Architecture §1 (ownership), §8 (failure is design), Operating §11 (idempotency), §13 (claim reality), ADR-008 R1 on money.

---

## 1. Principle

A travel commitment is a **state of a journey node**, not a side effect of a function. The physical itinerary (JDG) is the source of truth. Trip JSON `booking_confirmation` is a projection. Search/hold/book/ticket are distinct rungs; auto-ticket without a hold is a simulation and must stay labeled as one.

## 2. Node commitment states

| State | Meaning | May auto? | Writer |
|---|---|---|---|
| `quoted` | Offer assembled, not inventory-held | R3 compile | proposal compiler (simulated inventory) |
| `held` | Fare/room held with expiry | R2 propose, R1 persist | price-lock when a real source exists (today: preview, so unused) |
| `booked` | Supplier accepted, not ticketed | R1 | fulfillment (future live GDS) |
| `ticketed` | Irreversible travel document | R1 | fulfillment (today: simulated + labeled) |
| `void` | Commitment reversed | R1 | confirmation void path |

Illegal: `quoted` → `ticketed` in one unlabeled step **as if live**. Allowed today only as `deterministic_preview` with `provider_connected: false`.

Illegal: overwriting `ticketed`/`booked` nodes with a compiler re-run.

## 3. Once-booked

If `booking_confirmation.pnr_locator` exists, fulfillment **replays** the stored result (`idempotent_replay: true`) and does not issue a second VCC/PNR. The 60s lease is a split-brain fence, not a uniqueness constraint. Uniqueness is the confirmation record.

## 4. Persistence

`JourneyDependencyGraph.to_stored_payload()` writes `journey_graph_nodes` + `journey_graph_edges` on the trip. Public/tenant GET already read those fields (PA-01 abstain if missing). Compiler may persist `quoted` nodes onto an **existing** trip only; it never mints a trip and never overwrites ticketed nodes.

## 5. What this package does not decide

Live GDS connectivity, mandate default-on (ADR-008 §6), SQL `BookingConfirmation` as the only store (AT-04 residual). Those remain DECIDE / later IMPLEMENT.

## 6. Tests

`tests/test_booking_fulfillment_lifecycle.py` — persist graph + replay.  
`tests/test_journey_graph.py` / hydration — abstain without nodes.
