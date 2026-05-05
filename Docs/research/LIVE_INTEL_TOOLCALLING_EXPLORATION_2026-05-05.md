# Live Intel Toolcalling Exploration — 2026-05-05

## Purpose

Document a long-term, scalable exploration path for adding low-cost, real-time tool-calling intelligence to travel-agent operations without creating a parallel pipeline.

This exploration is anchored to the canonical runtime and feasibility/proposal/booking checks already implemented in:

- `src/agents/runtime.py`
- `src/agents/live_tools.py`

## Why This Matters

The product value is not only extracting trip data, but proactively reducing operator error and traveler risk by detecting dynamic changes:

- weather disruption shifts,
- flight status disruptions,
- quote/fare drift,
- entry-rule changes,
- destination safety advisories.

These signals are time-sensitive and cannot be fully solved by static rules.

## Candidate Live Data Providers (Cost-Aware)

### TinyFish (broad real-time search/fetch)

- Exploration value: generic live web retrieval for policy/news/alerts and edge-case checks.
- Notes (as of 2026-05-05): public pricing indicates free starter credits and free/low-threshold search/fetch usage for prototyping.
- Role in architecture: fallback evidence channel for checks where no structured API is available.

### Open-Meteo (weather)

- Already integrated in repository for weather intelligence paths.
- Continue as primary low-cost weather source for destination-intelligence and weather-pivot checks.

### Flight/safety/price providers

- Keep existing pluggable adapters in `src/agents/live_tools.py`.
- Prefer structured APIs for stable machine-readable fields.
- Use TinyFish search/fetch as secondary evidence/redundancy when structured providers are unavailable or degraded.

## Architecture Constraints (Non-Negotiable)

1. **No duplicate route/pipeline**
   - Extend canonical runtime agents only.
   - Do not create a second scenario-handling engine.

2. **Fail-closed risk semantics**
   - On stale/failing live checks, emit `unknown` risk states with clear operator next action.
   - Never auto-book/rebook/cancel/send customer messages from these checks.

3. **Evidence-first outputs**
   - Every live signal should include:
     - source,
     - fetched timestamp,
     - freshness state,
     - confidence,
     - query reference.

4. **Stage-aware call budgeting**
   - Discovery/intake: minimal calls.
   - Proposal/booking readiness: moderate calls.
   - In-trip disruption windows: high-priority refresh with strict quotas.

5. **Cache and TTL discipline**
   - Enforce per-signal TTL and dedupe by idempotency markers.
   - Avoid repeated calls for unchanged trip markers.

## High-Impact Scenarios To Add

1. Monsoon/storm season check before proposal send.
2. Elderly/toddler route comfort with live transfer disruption context.
3. Quote revalidation before payment if fare drift risk rises.
4. Entry-rule drift check before booking handoff.
5. Safety advisory change detection for destination and transit points.
6. Tight-connection/misconnect risk escalation for multi-leg itineraries.
7. Activity risk pivots (outdoor/water/trek) using fresh weather conditions.

## Proposed Phased Rollout

### Phase 1 — Provider Abstraction Hardening

- Add optional TinyFish-backed provider wrappers in `src/agents/live_tools.py` behind env flags.
- Keep existing provider interfaces unchanged (`WeatherTool`, `FlightStatusTool`, `PriceWatchTool`, `SafetyAlertTool` style contracts).
- Normalize TinyFish outputs into existing `ToolResult`.

### Phase 2 — Canonical Agent Wiring

- Wire optional TinyFish evidence augmentation into:
  - `DestinationIntelligenceAgent`
  - `SafetyAlertAgent`
  - (optionally) `ConstraintFeasibilityAgent` for entry-rule/live-risk enrichments
- Preserve existing deterministic behavior when TinyFish is disabled.

### Phase 3 — Risk Taxonomy Convergence

- Map live signals into consistent risk categories:
  - `weather`, `routing`, `activity`, `safety`, `entry_rules`, `pricing`
- Ensure proposal/booking readiness consumes these in a consistent way.

### Phase 4 — Observability and Guardrails

- Add runtime metrics:
  - call count by provider/stage,
  - freshness hit rate,
  - unknown-risk fallback rate,
  - cost/credits burn estimate.
- Add alert thresholds for provider outages or stale-heavy operation.

## Testing and Verification Plan

1. Unit tests for provider adapters:
   - success path,
   - malformed payload,
   - stale evidence,
   - timeout/error fallback.

2. Runtime agent tests:
   - no regressions when provider disabled,
   - enriched outputs when provider enabled,
   - fail-closed `unknown` path correctness.

3. Contract tests:
   - verify output schemas for destination/safety/feasibility packets remain backward compatible.

4. Scenario tests:
   - monsoon-risk destination with alternate-month recommendation,
   - elderly + multi-leg + disruption context,
   - toddler + extreme activity + adverse weather.

## Current Status (2026-05-05)

- Existing runtime already has live weather/flight/price/safety agent patterns and tool contracts.
- Scenario-handling gap for:
  - elderly + 4-flight fatigue,
  - toddler + extreme activity
  has been implemented in canonical feasibility checks.
- This document captures the next expansion area for broader low-cost live intelligence.

## Decision

Track this as an active exploration and implementation stream, but execute incrementally through the canonical runtime architecture only.
