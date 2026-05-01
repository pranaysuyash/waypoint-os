# Itinerary Checker Parallel Beta Implementation Plan

**Date:** 2026-05-01  
**Scope:** Convert the parallel-beta strategy into a build sequence that can ship quickly without becoming the core agency product.

## 1. Build Goal

Ship a free traveler-facing itinerary checker that:

- accepts pasted text, typed text, uploaded PDFs, screenshots, and images
- extracts itinerary facts with OCR or direct text parsing first
- resolves entities, dates, party composition, and trip structure
- calls live data sources for actionable risk checks
- produces multiple scores and concrete suggestions
- stores consented inputs and outputs for future improvement
- keeps the agency workspace and core B2B motion clearly separate
- allows optional monetization without gating the core report

## 2. Non-Negotiables

1. One shared canonical engine.
2. No duplicate route family.
3. No separate hidden product stack.
4. Free core report.
5. Consent-based persistence and reuse.
6. Public messaging must not read as “we replace your agent.”
7. Keep deployment and runtime costs low.
8. Do not position the checker as a cheaper substitute for agency work the company already sells.

## 3. Build Order

### Phase A: Public Intake

Deliverables:

- public upload / paste UI
- file type handling
- text extraction path
- source envelope creation

Acceptance:

- a traveler can submit an itinerary without needing the agency workspace
- the system preserves raw input and source type

### Phase B: Parsing and Normalization

Deliverables:

- OCR fallback for scanned PDFs/images
- direct text parsing for digital PDFs and pasted text
- entity extraction for destination, dates, people, and itinerary structure
- confidence and ambiguity capture

Acceptance:

- the checker can summarize the itinerary into a structured internal packet
- the checker can explain what was inferred and what remains ambiguous

### Phase C: Live Risk Checks

Deliverables:

- weather seasonality lookup
- visa / entry rule lookup
- pacing / density checks
- group composition / age-mix checks
- connection and logistics checks

Acceptance:

- the report ties each warning to a concrete trip attribute
- the report includes the reason, not just the score

### Phase D: Reporting

Deliverables:

- multi-score output
- plain-language suggestions
- shareable summary
- advisor handoff CTA

Acceptance:

- the user can understand what to fix and why
- the user can forward the report to an agent

### Phase E: Consent and Retention

Deliverables:

- retention consent controls
- model-improvement opt-in
- deletion request path
- version metadata for extraction and scoring

Acceptance:

- the system can store the report and extracted data only with explicit consent
- the system can exclude records from training exports

### Phase F: Monetization

Deliverables:

- donation or tip jar
- optional pay-what-you-want upgrade
- optional affiliate handoff

Acceptance:

- core value remains free
- monetization never blocks the main result

## 4. Current State vs Needed Work

| Area | Current state | Needed |
| --- | --- | --- |
| Public traveler page | Exists | Connect to real backend |
| Upload / paste entry | Demo-only | Wire to persistence and pipeline |
| OCR | Not wired in public flow | Add local OCR fallback |
| Entity extraction | Exists in core intake | Expose through public checker |
| Live data checks | Exists in other modules | Selectively call for public reports |
| Scoring | Exists in internal logic | Render public-safe scorecards |
| Persistence | No public artifact store | Add consent-based retention |
| Monetization | Not present | Add optional secondary rails |
| Brand separation | Implicit only | Make explicit in UI and docs |

## 5. Suggested Data Model

Persist these objects for each public report:

- `submission`
- `extracted_text`
- `structured_packet`
- `risk_findings`
- `scores`
- `live_checks`
- `user_edits`
- `consent_flags`
- `report_version`

## 6. Suggested API Shape

Prefer extending the existing public intake path rather than adding a parallel stack.

Minimum contract:

- `POST` submit itinerary
- `GET` fetch report
- `POST` add user correction
- `POST` record consent
- `DELETE` request deletion

## 7. Suggested UI Language

Use:

- itinerary ATS
- check your itinerary
- find missed risks
- get a second pass
- improve what you already have
- share with your agent
- score my itinerary
- upgrade this plan

Avoid:

- replace your agent
- book direct instead
- bypass agencies
- build me a new itinerary
- plan my trip from scratch

## 8. Product Analogy

The checker should feel like an ATS for itineraries:

- user brings an existing itinerary or rough plan
- the tool checks structure, gaps, and risks
- the tool suggests upgrades and better framing
- the result helps the user get a better deal from their agent or improve the plan themselves

This framing keeps the feature aligned with the agency workflow instead of competing with it.

## 9. Commercial Boundary

The checker should improve the quality of the itinerary conversation, not replace the conversation.

- It should help a traveler bring a cleaner brief to an agent.
- It should help a self-planner catch misses before they spend more.
- It should help an agent run the same check before sending a proposal.
- It should not be sold as a full-service itinerary desk.
- It should not be framed as a bypass for the company’s agency customers.

## 10. Risks

- confusing the public checker with the agency workspace
- adding too much LLM cost too early
- collecting data without clear consent
- creating a second analysis engine
- using monetization that harms trust

## 11. Next Coding Step

Implement the public checker as a real pipeline-backed path, starting with:

1. submit itinerary
2. parse and score
3. return a shareable report
4. persist consented artifacts
