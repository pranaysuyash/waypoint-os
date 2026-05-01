# Itinerary Checker Parallel Beta Strategy

**Date:** 2026-05-01  
**Context:** GTM wedge for a free traveler-facing itinerary checker that can also feed internal learning, without confusing the product with the agency workspace.

## 1. Objective

Build a public, low-friction itinerary checker that accepts either:

- uploaded itinerary files
- pasted itinerary text
- manually typed travel plans

Then:

- parse the content with OCR or direct text extraction first
- normalize entities, dates, people, destinations, and trip structure
- call live data sources for risk checks
- score the itinerary across multiple criteria
- explain the findings in plain language
- save raw inputs, extracted artifacts, and outcomes when consent allows
- reuse the same canonical engine internally without creating a second product path

The wedge must be fast to launch, cheap to run, and clearly positioned as a helper for travelers and agents, not a replacement for agencies.

## 2. Current Repo State

The repo already has enough surface area to support this as a parallel beta, but not a full persistent product yet.

### What already exists

- A public traveler-facing page at `frontend/src/app/(traveler)/itinerary-checker/page.tsx`.
- A marketing CTA to that page from `frontend/src/app/page.tsx`.
- A canonical intake pipeline with source envelopes, packet models, extraction, validation, decisioning, and suitability logic under `src/intake/` and `src/decision/`.
- Existing field support for itinerary text and raw notes in `src/intake/packet_models.py` and `frontend/src/app/api/trips/route.ts`.
- Existing extraction heuristics that already recognize traveler plans and existing itineraries in `src/intake/extractors.py`.
- Existing downstream risk logic for party composition, pacing, destination, and itinerary coherence in `src/decision/rules/` and `src/suitability/integration.py`.

### What is still missing

- The public upload flow is still a static demo experience, not a real persisted ingestion path.
- `frontend/src/app/api/trips/route.ts` currently returns a mock trip instead of calling the spine pipeline.
- There is no canonical public artifact store for uploaded files, extracted text, parsed entities, scored findings, and user consent state.
- There is no explicit public-vs-agency brand separation contract in code or docs.
- There is no current end-to-end flow that proves uploaded itineraries become durable training data with consent and retention controls.

## 3. Recommendation: Parallel Beta, Not Core Product Rebuild

Keep this as a **parallel beta** with one shared engine and two surfaces:

- **Public surface:** the free itinerary checker for travelers
- **Agency surface:** the existing workspace and intake flow for operators

The public surface should do just enough to feel useful immediately:

1. accept upload or pasted text
2. parse and normalize
3. score and explain
4. offer a shareable result
5. offer an agency handoff CTA, not a replacement CTA

The agency surface should keep ownership of:

- trip operations
- pipeline control
- booking execution
- internal notes
- advanced overrides

This avoids a duplicate product stack and protects the B2B2B motion.

## 4. Architecture Choice

### Canonical path

Use the existing intake pipeline as the shared backend truth. Do not fork a second analysis engine.

Recommended sequence:

1. ingest source envelope
2. extract text from PDF/image if needed
3. normalize into the canonical packet
4. run validation and decision layers
5. compute public-safe findings
6. persist source, extracted data, and report metadata
7. emit a shareable result

### Preferred implementation pattern

For the public beta, extend the current intake contract instead of introducing a separate route family.

- If the current `/api/trips` path is going to stay the public entry point, make it call the real spine pipeline and persist the result.
- If the public checker needs its own API namespace, keep it as one resource with one canonical route and one validation stack.
- Do not create a parallel `route-v2` or duplicate ingestion stack.

### Data to save

Store the following as first-class artifacts:

- uploaded file metadata
- OCR output or direct text extraction
- normalized itinerary text
- extracted entities and facts
- scoring output
- live data lookups used in scoring
- user corrections / edits
- consent state for retention and model improvement
- version metadata for prompts, extraction, and scoring logic

### Data to avoid over-saving by default

Do not automatically expose or repurpose:

- raw uploads to the public web
- personally identifying details without consent
- agent-internal notes in the traveler view
- model-training exports without opt-in

## 5. Cost-Effective Parsing Stack

The cheapest reliable shape is:

1. **Text first** for pasted itineraries and digital PDFs.
2. **Local OCR second** for scanned documents or screenshots.
3. **LLM normalization third** for entity resolution, nuance, and structured summaries.
4. **Live data checks last** for only the pieces that materially change risk.

### Good low-cost building blocks

- `Tesseract` for OCR on images and scanned PDFs. Official docs describe it as an open-source OCR engine with support for many languages and multiple output formats.
- `OCRmyPDF` for converting scanned PDFs into searchable PDFs with an OCR text layer.
- A lightweight parser for dates, destination names, party size, and route patterns before any LLM call.

### Why this order matters

- OCR is deterministic and cheap enough to run locally.
- Most itineraries are mostly text, so OCR should be a fallback, not the default.
- LLM cost stays bounded if it is used only after text is extracted and chunked.
- Live external lookups should only happen for items that are high value or high risk.

## 6. Live Data Checks To Prioritize

The first beta should check only the signals that are easy to explain and directly actionable.

### High-value checks

- weather seasonality and disruption windows
- visa and entry rules
- connection risk and pacing density
- multi-generational / elderly / child pacing compatibility
- document completeness and trip readiness
- obvious cost leaks such as resort fees or baggage assumptions

### Example

If the itinerary says “Hong Kong in August” for a group with elders and a child, the checker should be able to explain that August sits in the Hong Kong tropical cyclone season and that pace, weather contingency, and indoor backup planning matter.

Official sources used for this research:

- NOAA says Atlantic hurricane season runs from June 1 to November 30.
- Hong Kong Observatory publishes tropical cyclone statistics showing warning-signal activity concentrated in the summer and early autumn months.

## 7. Scoring Model

The public beta should expose a small set of visible scores instead of one opaque number.

Recommended score buckets:

- trip completeness
- seasonality risk
- pacing / fatigue risk
- document / visa risk
- logistics coherence
- cost surprise risk

Each score should have:

- a number
- a label
- 1 to 3 reasons
- a concrete suggested improvement

The report should always answer:

- what is wrong
- why it matters
- what to change
- whether the traveler should send it to an agent

## 8. Messaging and Brand Guardrails

This part matters as much as the code.

### Positioning

Use language like:

- “itinerary ATS”
- “check your itinerary”
- “find missed risks”
- “get a second pass”
- “share this with your agent”
- “upgrade what you already have”
- “bring your plan, we score it”

Avoid language that sounds like:

- “we replace your agent”
- “book without an agency”
- “competitor to agencies”
- “we build your itinerary from scratch”
- “send us nothing, we will plan everything”

### Visual and tonal direction

- Keep the public page clearly separated from the workspace UI.
- Make the public checker lighter, more self-serve, and more traveler-safe.
- Make the agency workspace more operational, denser, and task-oriented.
- Keep one design language family, but do not make the public tool look like an internal back office screen.

### Commercial boundary

The free checker should funnel trust back into the agency motion:

- traveler gets value immediately
- agency gets a better-formed lead
- the product learns from the correction loop

That is a parallel beta, not cannibalization.

### Do not eat our own customers

The checker must not be positioned as a replacement for the agency service that already earns revenue.

- Do not market it as a full itinerary replacement engine.
- Do not make it look like a cheaper alternate agent.
- Do not encourage agency clients to bypass the agency for the same booking work.
- Do not frame the output as “we will do your agent’s job for free.”

The right message is:

- “bring your existing plan”
- “get a better brief”
- “help your agent help you better”
- “upgrade the itinerary before you spend more time or money”

### Clear mental model

Think of it like an `ATS` for resumes, but for itineraries:

- the user uploads or pastes their existing plan
- a traveler can self-check their own plan
- an agent can run the same checker before sending a brief
- the checker scans for weak points, missing coverage, and hidden risks
- the user gets upgrade suggestions and a stronger brief
- the agent gets a cleaner, higher-quality input

It is not:

- a new itinerary factory
- a concierge replacement
- a shadow agency workflow

## 9. Monetization Without Product Drift

The checker can monetize without becoming the main business.

### Low-friction options

- **Donations / tip jar:** voluntary support after the report is generated.
- **Pay-what-you-want upgrade:** optional advanced export, branded PDF, or deeper checks.
- **Affiliate handoff:** only when a report points to a booking need and the traveler opts in.
- **Advisor referral:** “send to my agent” as the primary conversion path.

### Guardrails

- Keep the base checker genuinely useful for free.
- Never block the core risk report behind a paywall.
- Keep monetization visually secondary to the analysis.
- Do not insert affiliate offers into sensitive risk warnings.
- Do not let revenue prompts interfere with trust or clarity.

## 10. Data, Learning, and Consent

This is the part that turns the wedge into a compounding asset.

### What to keep

- original uploads
- extracted text
- entity graph
- user edits to extracted entities
- final score report
- live lookup results
- version metadata for reproducibility

### What to require

- explicit consent for retention beyond a short default window
- explicit opt-in for model training or internal benchmarking reuse
- a deletion path for user requests
- a clear privacy explanation on the public page

### Suggested storage split

- **hot store:** recent sessions and reports
- **cold archive:** opt-in retained examples
- **training set export:** normalized, consented, redacted examples only

## 11. Parallel Beta Release Plan

### Phase 1: Live in public, thin but real

- keep the current public route
- replace the mock response path with the real pipeline
- support paste input first
- support PDF/image upload with local OCR fallback
- show a simple report with 4 to 6 scores
- add a “send to your agent” CTA

### Phase 2: Capture and retention

- persist uploaded inputs and extracted outputs
- add correction capture
- add consent controls
- store versioned score results
- add replayable examples for improvement

### Phase 3: Improvement loop

- measure false positives and false negatives
- learn from edits and shared reports
- expand live data sources selectively
- add richer itinerary structure and deeper explanations

## 12. Requirement-to-Evidence Checklist

| Requirement from goal | Current evidence | Status | Next step |
| --- | --- | --- | --- |
| Free traveler-facing tool | `frontend/src/app/(traveler)/itinerary-checker/page.tsx` | Partial | Keep as public beta surface |
| Upload itinerary or type plan | `UploadCard` in the same page | Partial | Wire to real ingestion |
| OCR or direct text parse first | `src/intake/extractors.py`, `src/intake/packet_models.py` | Partial | Add file/text intake wrapper |
| Understand entities and nuances | `src/intake/extractors.py`, `src/decision/rules/`, `src/suitability/integration.py` | Present | Route public inputs through canonical engine |
| Live data checks | No public checker backend yet | Missing | Add weather / visa / pacing lookups |
| Multiple scoring criteria | `src/analytics/engine.py` and decision/risk modules | Present | Expose public-safe scorecards |
| Save uploaded files and extracted data | No persisted public store yet | Missing | Add consented artifact storage |
| Improve algorithms and train models | No explicit public feedback loop yet | Missing | Add opt-in correction and export flow |
| Easy to deploy and cost effective | Static demo page only | Partial | Use local OCR, bounded LLM calls, cached live lookups |
| Protect B2B2B motion | Marketing page and workspace exist separately | Partial | Keep public checker as a sidecar, not the main workspace |
| Messaging and imagery should not feel competitive | Current page is traveler-facing and light-weight | Partial | Keep CTA pointed toward advisor handoff |
| Document the goal prompt | This file | Present | Keep updating as implementation lands |

## 13. Current Decision

**Recommendation:** ship this as a parallel beta with a shared canonical engine, separate public positioning, and explicit consent-based retention.

**Not recommended:** building a separate hidden product path or a second analysis stack.

**Why this is the right split:**

- fastest path to live
- cheapest to maintain
- easiest to improve iteratively
- least likely to confuse or compete with agency customers
- best foundation for future model improvement

## 14. Sources Used

- `frontend/src/app/(traveler)/itinerary-checker/page.tsx`
- `frontend/src/app/page.tsx`
- `frontend/src/app/api/trips/route.ts`
- `src/intake/packet_models.py`
- `src/intake/orchestration.py`
- `src/intake/extractors.py`
- `src/decision/rules/composition_risk.py`
- `src/suitability/integration.py`
- NOAA hurricane season reference
- Hong Kong Observatory tropical cyclone references
- Tesseract OCR documentation
- OCRmyPDF documentation
