# Product B Event Schema v1 (2026-05-07)

## Purpose
Canonical event schema for validating Product B as a wedge into Product A.

## Naming convention
- lowercase snake_case
- object_action format

## Global envelope (required on every event)
- event_name: string
- event_version: int (start with 1)
- event_id: string (uuid)
- occurred_at: string (ISO-8601 UTC)
- session_id: string
- inquiry_id: string
- trip_id: string | null
- actor_type: enum("traveler","system","operator")
- actor_id: string | null
- workspace_id: string | null
- channel: enum("web","mobile_web","api")
- locale: string | null
- currency: string | null

## Wedge-core events

### 1) intake_started
When user starts Product B input flow.
Properties:
- input_mode: enum("freeform_text","upload","mixed")
- has_destination: bool
- has_dates: bool
- has_budget_band: bool
- has_traveler_profile: bool

### 2) first_credible_finding_shown
First finding rendered that meets evidence+confidence threshold.
Properties:
- time_from_intake_start_ms: int
- finding_id: string
- finding_category: enum("cost","suitability","logistics","policy")
- severity: enum("must_fix","should_review","optional")
- confidence_score: float
- evidence_present: bool

### 3) finding_evidence_opened
User opens evidence drawer/snippet for a finding.
Properties:
- finding_id: string
- evidence_type: enum("source_snippet","rule_reference","model_rationale")
- open_index: int

### 4) action_packet_copied
User copies forward-ready packet/script.
Properties:
- packet_id: string
- packet_type: enum("agent_message","revision_checklist","question_list")
- finding_count: int
- had_manual_edits: bool

### 5) action_packet_shared
User shares/exports packet.
Properties:
- packet_id: string
- share_channel: enum("whatsapp","email","copy_paste","other")
- had_manual_edits: bool

### 6) agency_revision_reported
Traveler reports that agency revised quote/itinerary using findings.
Properties:
- revision_report_mode: enum("self_report","uploaded_revision")
- revision_outcome: enum("revised","no_change","rejected")
- time_from_share_ms: int | null

### 7) re_audit_started
Traveler starts re-audit with revised plan.
Properties:
- prior_packet_id: string
- revision_input_mode: enum("freeform_text","upload","mixed")

### 8) product_a_interest_signal
Agency-side pull-through signal attributable to Product B exposure.
Properties:
- signal_type: enum("demo_request","contact_request","trial_start")
- attribution_mode: enum("explicit_ref","inferred")
- source_inquiry_id: string | null

## Derived KPIs (from events)
- Time-to-first-credible-finding: first_credible_finding_shown.time_from_intake_start_ms (p50/p90)
- Forward-without-edit rate: action_packet_shared where had_manual_edits=false / action_packet_shared
- Agency revision rate (7d): agency_revision_reported(revised) within 7 days / action_packet_shared
- Product A pull-through: product_a_interest_signal / qualified inquiries

## Data quality rules
- Reject events missing global envelope fields.
- Reject first_credible_finding_shown if evidence_present=false.
- Deduplicate by event_id.
- Store raw + normalized event tables.

## Out of scope for v1
- bookings, payments, referrals, marketplace routing events.

## Why this helps the app
- It converts Product B from a "tool that seems useful" into a measurable behavior system.
- It distinguishes proxy activity (copy/share) from proof activity (agency revision, Product A pull-through).
- It exposes where the flow breaks: slow first value, weak evidence trust, low forwardability, no revision loop.
- It prevents roadmap drift by forcing every iteration to answer: did this increase revision behavior and Product A demand?

## User benefit
Traveler:
- Faster first credible finding.
- Clear, forward-ready language to use with existing agent.
- Evidence-backed outputs, not opaque AI claims.
- Re-audit feedback that shows whether revision actually improved the plan.

Agency:
- Clear inbound context from traveler concerns.
- Better quality revision conversations.
- More qualified demand that can map into Product A onboarding.

Operator/founder:
- Honest go/no-go signal for Product B wedge viability.
- Early warning on trust failure (high-noise findings, low evidence engagement).
- Concrete levers for improvement (latency, evidence quality, script quality).

## Closed cycle fit (the loop we are building)
1. Traveler submits plan (intake_started)
2. Audit pipeline produces evidence-backed findings (first_credible_finding_shown)
3. Traveler inspects evidence and forwards action packet (finding_evidence_opened, action_packet_shared)
4. Existing agent revises plan (agency_revision_reported)
5. Traveler re-runs audit on revised plan (re_audit_started)
6. Improvement is measured and attributed to wedge behavior
7. Agency-side pull-through into Product A is captured (product_a_interest_signal)
8. Findings feed model/prompt/rule iteration

This is the closed loop: audit -> action -> revision -> re-audit -> Product A demand -> system learning.

## What happens to agents/prompts/checks
- They do not disappear. The event schema is observability, not a replacement for the checking agents.
- Existing checks (policy, suitability, logistics, pricing, safety) still run through current pipeline/agents.
- Prompts/rules become tunable with evidence:
  - If first-value SLA misses, optimize prompt/tool sequence.
  - If evidence open rate is low, improve evidence formatting and grounding.
  - If forward-without-edit is low, improve negotiation script phrasing.
  - If revision rate is low, tighten finding specificity and severity calibration.
- Add guardrail automations on top of events:
  - Alert when p90 first-value exceeds threshold.
  - Alert when high-severity findings are frequently rejected/no-change.
  - Escalate for prompt/rule review when pull-through deteriorates.


## Handling non-returning users (when revised/final feedback is missing)
We track this with confidence tiers, not binary truth.

### Outcome confidence tiers
1. Observed outcome (highest confidence)
- We directly receive agency_revision_reported and/or re_audit_started.

2. Inferred outcome (medium confidence)
- We do not get explicit return feedback, but we see strong proxy signals:
  - action_packet_shared with high evidence engagement,
  - delayed revisit to view/compare findings,
  - same-session or next-session intent signals for Product A.
- Mark these separately as inferred_revision_likely=true (never merge into observed counts).

3. Unknown outcome (low confidence)
- No return events and no strong proxy chain inside attribution window.

### How we measure without polluting truth
- Primary KPI remains observed agency revision rate.
- Add two companion metrics:
  - dark_funnel_rate = unknown outcomes / action_packet_shared
  - inferred_revision_rate = inferred outcomes / action_packet_shared
- Report all three together: observed, inferred, unknown.
- Never use inferred outcomes alone for launch success decisions.

### Practical instrumentation to reduce unknowns
- Include one-click status links in action packet:
  - "Agent updated my itinerary"
  - "Agent refused / no change"
  - "Still waiting"
- Attach share_token_id to packet links so delayed returns can be attributed.
- Send time-boxed follow-up nudges (24h/72h) asking for one-tap status.
- Capture passive return signals (user opens compare view, starts re-audit) as inferred only.

### Decision rule
- If dark_funnel_rate stays high, fix loop closure UX before scaling traffic.
- If observed stays low but inferred high, prioritize feedback-capture mechanisms.
- If both observed and inferred are low, treat as wedge weakness, not measurement weakness.

