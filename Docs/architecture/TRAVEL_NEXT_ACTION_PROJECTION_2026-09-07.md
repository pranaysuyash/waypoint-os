# Travel Next-Best-Action Projection (E-NBA)

**Status:** exploration package E-NBA (PER-0443) — design ratified into code the same day.  
**Problem (AT-07):** `DecisionResult.next_best_action` is CRM (`SEND_FOLLOWUP`, `CLOSE_LOST`). Nineteen product agents each stamp trip-level `operator_next_action`. Last supervisor pass wins, so a weather tick can erase a disruption review.  
**Doctrine:** one canonical path, explicit ownership, human approval by consequence (PER-0443), ADR-008 rungs.

---

## 1. Principle

There are **two** next actions, never one overloaded field:

| Field | Owner | Meaning |
|---|---|---|
| `commercial_next_action` | intake `decide_commercial_action` | CRM: follow-up, nurture, close-lost |
| `travel_next_action` | projector `src/orchestration/travel_next_action.py` | What a human or bounded agent should do to the **journey** next |

`DecisionResult.next_best_action` is retained as the **commercial** value for existing tests and BFF adapters. It is no longer the travel OS action.

`operator_next_action` on a trip becomes an **alias of the winning travel action** so PacketPanel keeps working. Agents may still record a proposal inside their own snapshot (`flight_status_snapshot.operator_next_action`).

## 2. Priority (higher wins; equal priority: newer source wins)

| Band | Priority | Examples |
|---:|---|---|
| Safety | 100 | `human_safety_review` |
| Disruption | 90 | `review_flight_disruption` |
| Booking integrity | 80 | `human_booking_review`, `collect_booking_details` |
| Documents | 70 | `verify_documents` |
| Money/quote | 60 | `revalidate_quote_before_payment` |
| Proposal | 50 | `revise_proposal_before_review`, `operator_review_proposal` |
| Feasibility / intel | 40 | `human_feasibility_review`, `review_weather_pivots` |
| Monitor | 20 | `monitor_flights`, `monitor_weather` |
| Commercial (never wins over travel) | 10 | `SEND_FOLLOWUP` and other CRM tokens |
| Unknown | 15 | anything not listed |

A lower-priority agent **must not** clobber a higher stored `travel_next_action_priority`.

## 3. Intake-time travel action

Derived from `decision_state`, not from ghost-risk:

| decision_state | travel_next_action |
|---|---|
| ASK_FOLLOWUP | `collect_missing_facts` |
| STOP_NEEDS_REVIEW | `human_review` |
| BRANCH_OPTIONS / PROCEED_* | `continue_proposal` |

## 4. Enforcement seam

`NextActionAwareTripRepo` wraps the supervisor trip repo and runs `merge_next_action_updates` on every `update_trip` that includes `operator_next_action`. Unit tests that inject a raw repo still see identity merge when the trip has no stored winner.

## 5. What this package does not do

Does not send messages, rebook, or charge. Fleet authority strings stay: “Do not book, ticket, charge.” Does not replace PacketPanel; it feeds it a stable alias.
