# Institutional Memory Layer Synthesis (2026-04-14 IST)

## Sources Ingested

### A) New local reference file
- `/Users/pranay/Downloads/Thinking-about-agentic-flow (5).html` (`2026-04-14 17:53 IST`)

### B) External reference repo
- [andrewjiang/palantir-for-family-trips](https://github.com/andrewjiang/palantir-for-family-trips/tree/master)
- Specific files reviewed:
  - `README.md`
  - `src/tripData.js`
  - `src/tripModel.js`
  - `src/App.jsx`

### C) Additional discussion notes (provided in-session)
- Missing angles for agency operations beyond NB01-NB03 transaction flow.
- Emphasis on reusable institutional memory vs rebuilding from scratch each trip.

## Core Gap Clarified

Current architecture is strong on **transaction intelligence** (intake, decisions, execution guidance), but weak on **compounding organizational memory**.

Without memory layers, agencies repeatedly:
- rebuild similar itineraries
- re-evaluate suppliers from memory
- re-price on gut feel
- re-learn customer preferences
- re-handle the same incidents ad hoc

## New Angles We Were Missing

### 1) Template Genome (Trip DNA)
- Store and evolve reusable trip templates by destination + traveler profile + budget tier.
- Track usage, satisfaction, margin, common issues, successful customizations.
- Goal: NB02 recommends a proven baseline, agent customizes only delta.

### 2) Supplier Intelligence Graph
- Persist supplier reliability, issue rates, trip-type fit, commission and relationship strength.
- Rank suppliers by context (family vs corporate vs honeymoon), not just price.
- Goal: move supplier choice from tribal memory to evidence-backed selection.

### 3) Pricing Memory Engine
- Compare quoted vs actual costs + margin over time with seasonality.
- Surface margin compression, supplier inflation, and quote guardrails.
- Goal: stop re-pricing from scratch and reduce hidden profitability drift.

### 4) Customer Genome
- Persist repeat-customer preferences, complaint history, life-stage evolution, LTV and referral value.
- Goal: avoid treating repeat customers as net-new every time.

### 5) Playbook Engine
- Codify recurring disruptions (driver no-show, hotel check-in delays, visa urgency, etc.).
- Track resolution steps, success rates, and best alternatives.
- Goal: execute known issue workflows consistently and faster.

### 6) Content Block Library
- Modular, versioned communication blocks (visa rules, packing advisories, payment reminders).
- Goal: eliminate repetitive rewriting and improve consistency/compliance.

### 7) Team Ownership and Coverage Graph
- Track active load, expertise, backup assignees, and handoff readiness.
- Goal: resilient operations during leave, escalations, or role changes.

### 8) Post-Trip Learning Loop
- Structured retrospectives that feed back into templates, supplier scores, and pricing.
- Goal: convert each completed trip into measurable system improvement.

## Repeatable vs Fresh Work Split

### Should be repeatable (systematize)
- baseline itinerary structures by segment
- supplier selection order and fallbacks
- pricing envelopes and margin floors
- standard communication modules
- disruption response sequences
- handoff packet structure

### Must stay fresh per trip (customize)
- traveler-specific constraints and preferences
- real-time inventory/availability
- live disruptions and schedule shifts
- exceptional events (medical/legal/weather)
- bespoke experiences and upsell choices

## Operational Activities by Cadence

### Daily
- next-action queue by SLA/risk
- traveling-now incident triage
- unread/last-touch follow-ups
- owner/escalation dispatch checks

### Weekly
- template performance review (adoption + outcome)
- supplier reliability updates
- repeat-customer reactivation opportunities
- open issue pattern review

### Monthly
- margin and pricing drift analysis
- supplier renegotiation shortlist
- playbook effectiveness review
- team load and routing adjustments

### Quarterly
- template pruning/versioning
- strategic supplier portfolio reset
- quality KPI review and operating policy updates

## Concrete Additive Data Model Direction (No Breaking Change)

Target file for integration planning:
- `/Users/pranay/Projects/travel_agency_agent/src/intake/packet_models.py`

Proposed additive fields on `CanonicalPacket`:
- `template_id: Optional[str]`
- `template_match: Optional[TemplateMatch]`
- `template_customizations: List[TemplateCustomization]`
- `supplier_bookings: Dict[str, SupplierBooking]`
- `customer_profile_ref: Optional[str]`
- `playbook_events: List[PlaybookExecution]`

Companion model groups to add in separate modules:
- `template_models.py` (TemplateGenome, TemplateMatch, TemplateCustomization)
- `supplier_models.py` (SupplierProfile, SupplierPerformance, SupplierBooking)
- `pricing_models.py` (QuoteHistory, MarginDriftSignal)
- `customer_models.py` (CustomerGenome)
- `playbook_models.py` (Playbook, PlaybookExecution, ResolutionOutcome)

## What the Palantir Reference Specifically Adds (Useful Here)

From `palantir-for-family-trips`, keep these transferable patterns:
- explicit mission timeline and day/slot operational playback
- readiness scoring + checklist state
- linked entity inspection rail (`getLinkedEntities`-style context jump)
- operations-first views (itinerary/stay/meals/activities/expenses/families)

Do **not** copy directly:
- family-trip-specific UI metaphors as product identity
- purely demo/sanitized data assumptions

## Priority Actions

## Do now (P0)
- Add this memory-layer scope to roadmap and tests (fixture scenarios for repeatability).
- Define minimal `TemplateGenome` + `SupplierProfile` schemas.
- Add packet-level references (`template_id`, `supplier_bookings`) as additive fields.
- Draft one operational playbook (`driver_no_show`) with measurable outcomes.

## Do next (P1)
- Implement template matching in NB02 with confidence and customization hints.
- Implement supplier ranking in NB03 by context reliability and issue rate.
- Add pricing memory tables and monthly drift report.

## Discuss before coding
- Which metrics define “template success” in v1 (satisfaction, margin, issue rate weighting)?
- Auto-blacklist thresholds vs manual approval for supplier demotion.
- Customer profile privacy boundaries and retention policy.

## Date Validation
- Environment date/time verified before update: `2026-04-14 17:56:53 IST +0530`.
