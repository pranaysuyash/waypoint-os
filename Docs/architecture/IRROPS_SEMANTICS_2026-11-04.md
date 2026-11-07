# IRROPS Semantics — disruption trigger taxonomy & decision-desk mapping (2026-11-04)

**Status:** Active — the R2-H gate doc. The watcher-trigger generalization
(`TicketPriceWatchAgent` tranche) extends THIS taxonomy; it does not invent
its own.

## 1. Trigger taxonomy (closed vocabulary)

| Kind | Meaning | Severity inputs | Regulatory hook |
|---|---|---|---|
| `cancellation` | flight cancelled by carrier | — | EC261/UK261 rerouting-or-refund duty; DOT significant-damage rule |
| `delay` | departure/arrival delay | delay_minutes (comp-relevant ≥180 under EC261/UK261 distance bands) | EC261 Art.6 / UK261; DOT tarmac rules |
| `schedule_change` | carrier-initiated pre-departure time change | delta_minutes, notice_hours | carrier contract of carriage; EC261 when rebooking degrades |
| `diversion` | diverted arrival airport | — | EC261 arrival-at-destination principle |
| `denial_of_boarding` | involuntary bump | — | EC261 Art.4 immediate compensation |

Severity is a deterministic function of the kind + its numeric inputs (see
`spine_api/services/irrops.py`), never an LLM opinion. Unknown kinds are
rejected at ingest — a trigger that is not in this table does not exist.

## 2. Signal sources (truth discipline)

- **Now (honest interim):** operator-reported. `POST /api/v1/disruption-radar/{trip_id}/report`
  writes `trip["active_disruption"]` with `source: "operator_reported"` and a
  basis string. The disruption radar (which already surfaces stored
  `active_disruption` rows — F-38 honesty rule) renders them with no
  fabrication path.
- **Next (provider feeds):** schedule-change/cancellation feeds ride the B6/B7
  producer lane (DP-04a) — they are launch-blocker-gated, never simulated.
  When a feed lands, its rows carry `source: "provider_observed"` and the SAME
  taxonomy; severity derivation is reused unchanged.
- **Never:** LLM-inferred disruption from message tone, or fabricated alerts
  on empty state (F-38 ruling stands).

## 3. Decision-desk mapping (the same desk shape as fare drops)

| After detection | Surface | Next action |
|---|---|---|
| Compensation eligibility | `passenger_rights` `/evaluate` (EU261/UK261/US_DOT — statutory calc, no money movement) | operator sends claim letter (`/generate-letter`) |
| Re-accommodation | `disruption-radar /{trip_id}/rebook-options` → `/rebook` (preview rebooking options; sandbox posture per ADR-008) | operator books; nothing auto-purchases |
| Traveler comms | existing ask/proposal channels (honest NOT_CONFIGURED without creds) | operator shares link |
| Money | payout/commission machinery only — a disruption NEVER auto-refunds; refunds are recorded payouts through the durable store | operator action |

`fare_drop_disposition.compute_fare_drop_options` remains the pricing-desk
pattern; IRROPS disposition options follow it (quantified options, human
approval, calc-only boundary).

## 4. Watcher taxonomy extension plan (the R2-H tranche)

`TicketPriceWatchAgent` generalizes AFTER this doc (adjudication ruling):
add trigger kinds `schedule_change` and `cancellation` to the watch loop,
reusing the marker/idempotency contract (one alert per trip+trigger-marker
until the marker changes) and the failure contract (stale/tool failures →
unknown-risk revalidation alert; never fabricate). Live-feed absence keeps
those triggers operator-fed until DP-04a lands. Sequencing recorded: next
watcher tranche, post-DP-04a or on first pilot demand signal.

## 5. Known gap carried from the audit register

`Journey Dependency Graph for IROPS` (register P2): multi-leg disruption
propagation (missed connections cascading across segments) is NOT modeled in
this doc. Single-segment semantics only. The JDG slice is a prerequisite for
cascading severity — recorded as the next expedition, not silently skipped.

## 6. Falsifiers

- A provider feed contradicts operator-reported rows → provider_observed wins
  (authority precedence), documented at the report endpoint.
- A jurisdiction review finds delay thresholds wrong per distance band → the
  severity table row is amended with a source citation; no silent edits.
- EC261 exceptional-circumstances defence: the engine evaluates statutory
  compensation, not liability adjudication — a claim evaluation is not a
  guarantee; the claim letter states the traveler's statutory position.
