# Lead Lifecycle and Retention

## Purpose
Unify repeat-customer handling, ghosting detection, window-shopper detection, and churn prevention into one explicit commercial lifecycle layer.

This complements trip-planning intelligence (NB01/NB02/NB03) and defines how lead/customer state is tracked, scored, and acted on.

## Why This Exists
Current documentation contains repeat/ghost/scope-creep ideas in multiple places, but they are fragmented. This doc defines:
- one lifecycle state model
- one lifecycle schema block
- deterministic v1 scoring heuristics
- intervention playbooks
- integration points in notebook/runtime flow

## Lifecycle State Machine
Primary state path:

`NEW_LEAD -> ACTIVE_DISCOVERY -> QUOTE_IN_PROGRESS -> QUOTE_SENT -> ENGAGED_AFTER_QUOTE -> GHOST_RISK -> WON -> BOOKING_IN_PROGRESS -> TRIP_CONFIRMED -> TRIP_ACTIVE -> TRIP_COMPLETED -> REVIEW_PENDING -> RETENTION_WINDOW -> REPEAT_BOOKED -> DORMANT -> LOST`

Use `loss_reason` and `at_risk_reason` as separate dimensions; do not overload `status`.

### `loss_reason` examples
- `price_mismatch`
- `no_response`
- `booked_elsewhere`
- `too_many_revisions_no_commitment`
- `poor_fit_quote`
- `slow_response`

## Lifecycle Schema Block (Additive)
Add this to canonical packet as `lifecycle`:

```json
{
  "lifecycle": {
    "lead_id": "uuid",
    "customer_id": "uuid_or_phone",
    "trip_thread_id": "uuid",
    "status": "NEW_LEAD",
    "created_at": "ISO8601",
    "last_customer_message_at": "ISO8601",
    "last_agent_message_at": "ISO8601",
    "last_meaningful_engagement_at": "ISO8601",
    "quote_sent_at": "ISO8601",
    "quote_opened": true,
    "quote_open_count": 2,
    "revision_count": 3,
    "days_since_last_reply": 2,
    "payment_stage": "none",
    "commitment_signals": ["shared_passport"],
    "risk_signals": ["silent_72h_after_quote"],
    "intent_scores": {
      "ghost_risk": 0.7,
      "window_shopper_risk": 0.6,
      "repeat_likelihood": 0.5,
      "churn_risk": 0.4
    },
    "loss_reason": null,
    "win_reason": null,
    "last_trip_completed_at": "ISO8601",
    "next_best_action": "SEND_TARGETED_FOLLOWUP",
    "next_action_due_at": "ISO8601"
  }
}
```

## Signal Definitions (Do Not Merge)
1. Ghosting
- Had engagement and then silence after quote/decision milestone.

2. Window shopper
- High advisory consumption and revisions with low commitment signals.

3. Customer churn
- Previously won customer does not return within expected cycle.

4. Lead loss
- Opportunity lost before booking.

## Deterministic v1 Heuristics
Prefer rules first; ML later.

### Ghost risk
Add:
- `+0.35` quote opened, no reply in 72h
- `+0.15` repeated views of one option
- `+0.10` clicked itinerary/hotel links
- `+0.15` no response 48h after follow-up

Subtract:
- `-0.25` concrete booking question
- `-0.30` docs shared (passport/names)
- `-0.20` asked hold/payment plan

Thresholds:
- `>=0.70` high
- `0.40-0.69` medium
- `<0.40` low

### Window-shopper risk
Add:
- `+0.20` `revision_count >= 3`
- `+0.20` destination flipped >=2x
- `+0.15` persistent infeasible budget contradiction
- `+0.15` broad comparison requests without narrowing
- `+0.20` no token/docs/payment despite high effort
- `+0.10` elapsed >14 days with no commitment

Subtract:
- `-0.30` planning fee paid
- `-0.25` dates+origin locked
- `-0.20` traveler docs provided

Thresholds:
- `>=0.75` high
- `0.50-0.74` medium
- `<0.50` low

### Repeat likelihood
Add:
- `+0.30` prior completed trip
- `+0.15` positive post-trip feedback
- `+0.10` historically fast response
- `+0.15` known seasonal repeat pattern
- `+0.10` valid stored profile/preferences
- `+0.10` referral history

Subtract:
- `-0.25` unresolved complaint
- `-0.20` cancellation dispute
- `-0.15` prior severe price objection + no win

Thresholds:
- `>=0.70` strong repeat
- `0.45-0.69` nurture
- `<0.45` low

### Churn risk (won customers only)
Add:
- `+0.30` no engagement in expected next-trip window
- `+0.20` no review/feedback captured
- `+0.15` issue/complaint on last trip
- `+0.15` no reactivation sent
- `+0.10` price objection on last quote

Subtract:
- `-0.25` positive review
- `-0.20` referral made
- `-0.20` detected new seasonal intent

Thresholds:
- `>=0.65` high
- `0.40-0.64` medium
- `<0.40` low

## Commercial Action Policy
Add second decision family:

- `TRIP_DECISION`: `PROCEED | ASK_FOLLOWUP | PRESENT_BRANCHES | ESCALATE`
- `COMMERCIAL_DECISION`: `SEND_FOLLOWUP | SET_BOUNDARY | REQUEST_TOKEN | MOVE_TO_NURTURE | REACTIVATE_REPEAT | CLOSE_LOST | ESCALATE_RECOVERY`

`COMMERCIAL_DECISION` should not mutate planning facts directly; it controls operator/customer action next step.

## Playbooks
1. High ghost risk
- Send one targeted follow-up based on viewed option.
- If silent after 48h, move to nurture and stop repeated manual chase.

2. High window-shopper risk
- Cap variants to two lanes.
- Require commitment gate (token/planning fee) after threshold.

3. High repeat likelihood
- Send personalized reactivation using stored preferences/history.

4. High churn risk
- Start with recovery/feedback touchpoint before hard sell.

## Runtime Integration
### NB01
- Capture lifecycle facts and raw risk signals.
- Preserve evidence/provenance for all lifecycle updates.

### NB02
- Compute `intent_scores`.
- Set `COMMERCIAL_DECISION` and `next_best_action`.

### NB03/NB04 (response + operations)
- Generate action-aligned messages.
- Emit escalation packets for owner/senior when thresholds hit.

## Metrics
- Quote-to-reply rate
- Quote-to-book rate
- Silent-after-quote rate
- Average revisions before win/loss
- Planning-fee conversion rate
- Repeat booking rate
- Reactivation conversion rate
- Churn rate (won-customer cohort)
- Loss-reason distribution

## Scenario Mapping
This layer must explicitly back:
- ghost customer follow-up
- scope creep / revision loops
- repeat-customer recall
- post-trip review request
- quote-disaster recovery
- referral and reactivation paths

## Implementation Status (2026-04-15)
Implemented in code (additive):
- `CanonicalPacket.lifecycle` support via `LifecycleInfo` in `src/intake/packet_models.py`
- NB02 deterministic lifecycle scoring in `src/intake/decision.py`
- NB02 commercial routing outputs:
  - `commercial_decision`
  - `intent_scores`
  - `next_best_action`
- Validation tests in `tests/test_lifecycle_retention.py`

Current known gap (separate from this implementation):
- Notebook test import-path issue (`ModuleNotFoundError: intake`) still affects full-suite collection and is tracked separately.
