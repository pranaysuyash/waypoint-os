# Itinerary Checker GTM Wedge (2026-04-14 IST)

## Sources
- User-provided GTM strategy and rule set in this session.
- `/Users/pranay/Downloads/Thinking-about-agentic-flow (6).html` (`17:59 IST`)
- `/Users/pranay/Downloads/Thinking-about-agentic-flow (7).html` (`18:03 IST`)

## Strategic Thesis

Build a free consumer-facing **itinerary stress-test tool** powered by a simplified NB01-NB03 pipeline.

Positioning:
- "Find what your travel plan missed."
- "Upload. Analyze. Travel confident."

Why this wedge works:
- Users already have itineraries (agency, OTA, self-planned).
- Anxiety is high before payment/travel.
- Fast risk detection creates immediate trust and lead intent.

## Flywheel

1. User uploads itinerary (free).
2. NB01-NB03 Lite returns score + top risks.
3. User captures email / requests paid fix / asks for better quote.
4. System captures structured demand + competitor quote patterns.
5. Captured data improves:
   - Template Genome
   - Supplier Graph
   - Pricing Memory
   - Playbooks

This turns external itinerary traffic into:
- lead generation
- revenue
- compounding training data moat

## Product Scope

## Free tier (hook)
- Overall score (0-10)
- Top critical + warning issues
- Basic extraction summary (dates, destination, hotels, flights)
- CTA to paid fix / quote comparison

## Paid fix tier (₹999 concept)
- Full rule set analysis
- Detailed fixes and alternatives
- Cost impact and risk explanation
- Human+AI turnaround SLA

## Quote improvement flow
- Optional lead routing to partner agencies
- Performance-based monetization (commission/lead fee model)

## NB01-NB03 Lite Mapping

## NB01 (Extraction)
- Inputs:
  - PDF itinerary
  - image/screenshot
  - pasted text
- Outputs:
  - normalized trip facts (flights/hotels/transfers/visa mentions/inclusions/exclusions)

## NB02 (Validation)
- Start with a constrained ruleset (15 initial checks) across:
  - timing
  - logistics
  - visa/docs
  - hidden costs
  - pace/experience

## NB03 (Report)
- Render plain-language findings with:
  - severity
  - explanation
  - suggested fix
  - cost impact
  - confidence

## Initial 15-Rule Seed (v1)

## Critical
- `CONN_001` international connection too tight
- `CONN_002` domestic connection too tight
- `TRF_001` transfer missing for far hotel
- `VISA_001` visa likely required but missing/unclear
- `INS_001` insurance missing for international itinerary
- `CHK_001` check-out/check-in buffer too small

## Warnings
- `HOT_001` hotel location risk (distance/friction)
- `HOT_002` excessive hotel changes
- `PACE_001` over-packed day cadence
- `MEAL_001` meal coverage ambiguity
- `FEE_001` hidden fee exposure
- `BUF_001` no event/cruise buffer
- `TRF_002` prolonged transfer without break
- `WEATHER_001` season/weather mismatch risk

## Info (paid emphasis)
- route optimization opportunities
- hotel optimization opportunities
- cost optimization opportunities

## Scoring Model (starter)

`score = clamp(10 - (critical*2.0) - (warning*1.0) - (info*0.3), 0, 10)`

This should be calibrated after first 100-300 analyzed itineraries.

## API Contract Draft (MVP)

## `POST /api/v1/analyze`
- Input:
  - `file` (optional)
  - `text` (optional)
  - `email` (optional, for follow-up)
- Output:
  - `analysis_id`
  - `score` + category breakdown
  - `issues[]` with severity/fix/cost impact/confidence
  - `extracted` trip summary

## `POST /api/v1/fix-request`
- Input:
  - `analysis_id`
  - contact fields
  - urgency
- Output:
  - payment or booking link
  - ETA/SLA
  - order/request id

## Implementation Plan (2-week MVP target)

## Week 1 (engine + backend)
- ingestion handler (pdf/image/text)
- NB01 structured extraction adapter
- initial 15 checks in NB02
- scoring and analysis API

## Week 2 (GTM delivery)
- landing + upload UX
- result card UX + CTA
- email capture + payment integration
- lead routing workflow
- instrumentation

## Key Metrics

Top funnel:
- visitor -> upload rate
- upload -> email capture rate

Monetization:
- upload -> paid fix conversion
- upload -> quote-request conversion

Data moat:
- itineraries analyzed / month
- destinations covered
- extracted competitor pricing points
- recurring issue distribution

Quality:
- false-positive complaint rate
- issue precision by rule
- fix outcome satisfaction

## Risks and Controls

Risk: false positives reduce trust  
Control: confidence thresholding + conservative critical rules first

Risk: legal/compliance on advice framing  
Control: explicit disclaimer ("guidance, not legal travel guarantee"), policy-reviewed copy

Risk: low-quality OCR/extraction  
Control: fallback uncertainty messaging + "needs manual review" branch

Risk: data/privacy concern  
Control: data minimization, retention policy, and clear upload consent

## How This Connects to Core Platform

The checker is not a side product. It is a top-of-funnel mode for the same core intelligence stack.

Data from this wedge should feed:
- Template Genome discovery
- Pricing Memory baselines
- playbook priorities
- destination demand signals

Cross-reference:
- `Docs/context/INSTITUTIONAL_MEMORY_LAYER_SYNTHESIS_2026-04-14.md`

## Decision

Proceed with the wedge as **GTM + data acquisition layer**, using strict scope:
- v1: 15 checks + clear CTAs + instrumentation
- defer advanced personalization until precision and conversion stabilize

## Date Validation
- Environment date/time verified before update: `2026-04-14 18:04:24 IST +0530`.
