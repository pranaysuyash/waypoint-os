# Product B Wedge Discussion Log (2026-05-07)

Date: 2026-05-07
Scope: Product B wedge measurement and loop-closure discussion
Status: Documented for continuity and implementation handoff

## 1) What was asked
User asked for clarity on:
- How the event schema helps the app
- What direct user value it provides
- Where it fits in the closed loop
- What happens to agents/prompts/checks
- How to track outcomes when users do not return with revised/final feedback

## 2) Decisions captured

### A. Event schema role
Decision:
- Treat event schema as the measurement spine, not a replacement for execution agents.
- Preserve existing backend checking agents/prompts; use telemetry to tune them.

Rationale:
- Prevents proxy-metric self-deception.
- Enables proof-driven optimization and kill/scale decisions.

### B. KPI hierarchy
Decision:
- Primary proof KPI remains observed agency revision behavior.
- Proxy actions (copy/share) remain leading indicators only.

Rationale:
- Keeps wedge success tied to behavior change, not vanity usage.

### C. Closed-loop model
Decision:
- Canonical loop remains: intake -> audit -> evidence interaction -> action packet share -> agency revision -> re-audit -> Product A pull-through -> prompt/rule updates.

Rationale:
- Explicitly aligns Product B output with Product A demand generation.

### D. Non-returning users measurement policy
Decision:
- Use confidence tiers, not forced binary outcomes:
  1) Observed
  2) Inferred
  3) Unknown
- Keep observed as primary KPI for launch decisions.
- Report inferred/unknown as companion diagnostics.

Derived metrics:
- dark_funnel_rate = unknown outcomes / action_packet_shared
- inferred_revision_rate = inferred outcomes / action_packet_shared

Guardrail:
- Never treat inferred outcomes as equivalent to observed outcomes in go/no-go decisions.

### E. Loop-closure instrumentation additions
Decision:
- Add one-tap status links in action packet:
  - Agent updated my itinerary
  - Agent refused / no change
  - Still waiting
- Attach share_token_id for delayed attribution.
- Add 24h/72h follow-up nudges.
- Track passive return events as inferred only.

## 3) Artifacts updated in this discussion
- Docs/PRODUCTB_EVENT_SCHEMA_V1_2026-05-07.md
  - Added value/benefit/closed-cycle/agents sections
  - Added non-returning-user handling section with confidence tiers and decision rules

## 4) Operating implications
- If dark_funnel_rate remains high: prioritize loop-closure UX before traffic scale.
- If observed low but inferred high: prioritize feedback capture mechanics.
- If observed and inferred both low: treat as wedge weakness and revisit core value proposition.

## 5) Next implementation move
- Wire event emission for the defined v1 events in backend/frontend boundaries.
- Add attribution-safe storage for observed/inferred/unknown classification.
- Build reporting surface that always displays observed + inferred + unknown together.
