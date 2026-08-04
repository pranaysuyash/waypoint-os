# Waypoint OS
## Master Product Opportunity, Feature, Idea, Exploration, Research, and Roadmap Registry

**Edition:** 2026-08-04  
**Status:** Living exploration document, not yet canonical  
**Repository baseline:** `pranaysuyash/waypoint-os`, default branch `master`  
**Scope:** Repository-derived product truth, explicit documentation, implicit opportunities, external market and competitor research, adjacent-industry patterns, experiments, speculative ideas, and frontier work.  
**Purpose:** Preserve the entire opportunity space without pretending that every item should be built.

---

## 0. Document contract

This document is deliberately **not one undifferentiated roadmap**.

| Portfolio | Meaning |
|---|---|
| **Current product truth** | Code, routes, models, UI, tests, and runtime surfaces that appear to exist. Existence does not prove production completeness. |
| **Explicit product intent** | Features or directions clearly described in repository documentation. |
| **Competitive parity** | Capabilities increasingly expected because current products already provide them. |
| **Implicit opportunity** | Capabilities naturally suggested by Waypoint's architecture, data, or workflows. |
| **Strategic option** | A plausible direction that could create differentiation or open a market. |
| **Research question** | A customer, legal, market, technical, data, or operational unknown. |
| **Experiment** | A bounded test designed to create evidence, not a production commitment. |
| **Idea bank** | Worth preserving but not ready for prioritization. |
| **Frontier Lab** | Long-horizon or speculative work with no delivery date. |
| **Parked / rejected / superseded** | Preserved to avoid rediscovery or accidental revival. |
| **Candidate roadmap** | Only the selected, sequenced subset that passes evidence, dependency, economics, and risk review. |

### Evidence labels

- **`[CODE]`**: Supported by current repository surfaces.
- **`[DOC]`**: Explicitly described in repository documentation.
- **`[WEB]`**: Derived from external products, market material, standards, regulation, or research.
- **`[INFERENCE]`**: Reasoned expansion from existing primitives.
- **`[SPECULATIVE]`**: Open-ended idea or frontier concept.
- **`[PARKED]`**: Intentionally outside active execution.

### Non-negotiable distinctions

1. A route is not proof of a complete product flow.
2. A document is not proof of implementation.
3. A simulation is not production evidence.
4. A competitor feature is not automatically something Waypoint should copy.
5. An idea is not automatically a roadmap item.
6. A vertical should reuse canonical primitives rather than create a shadow product.
7. Autonomous financial, legal, safety, identity, or relationship-sensitive actions require explicit policy, verification, audit, reversibility, and human control.
8. Every claim of “done,” “production ready,” or “current” must be re-verified against the latest repository state.
9. Historical documents must remain preserved, but contradictions should be reconciled in a current registry rather than silently overwritten.
10. Nothing in the Frontier Lab receives a date or launch dependency unless explicitly promoted through a new decision.

---

## 1. Executive synthesis

Waypoint OS already behaves less like an itinerary generator and more like an emerging **travel decision, operations, revenue, and governance platform**.

The repository exposes a broad API surface spanning intake, drafts, trips, assignments, reviews, suitability, documents, extraction, booking data, confirmations, payments, analytics, proposals, messaging, yield, disruption monitoring, corporate policy, duty of care, agent runtime, and system integrity. The documentation is much larger still, with hundreds of scenarios and many overlapping roadmap, audit, product-feature, vertical, and frontier documents.

### Core strategic interpretation

Waypoint's strongest potential is not generic AI trip planning. It is a trusted system that can:

```text
Capture messy demand
→ create a canonical case
→ identify missing or conflicting information
→ evaluate feasibility, suitability, policy, and risk
→ search and compare supply
→ protect commercial constraints
→ generate internal and traveler-safe outputs
→ collect approvals, payments, data, and documents
→ coordinate fulfillment
→ monitor operations and disruptions
→ preserve evidence, memory, and learning
```

### The real product layers

1. Acquisition and intake.
2. Canonical trip, case, customer, household, and relationship memory.
3. Constraint, suitability, policy, and risk intelligence.
4. Destination, supplier, contract, and inventory intelligence.
5. Pricing, margin, revenue, commission, and settlement control.
6. Proposal, trust, collaboration, and conversion.
7. Booking, order, documents, payments, and fulfillment.
8. Traveler, group, attendee, and host experience.
9. Live operations, disruption, concierge, and duty of care.
10. Team governance, quality, training, and institutional knowledge.
11. Agentic automation with progressive autonomy and human takeover.
12. Analytics, evaluation, security, compliance, integration, and ecosystem infrastructure.

### External market signal

- Advisor products are converging on CRM, proposals, email, workflows, payments, commissions, reporting, and AI-assisted administration.
- Tour-operator and DMC systems compete on supplier contracts, rate loading, pricing, bookings, operations, and finance.
- Corporate platforms compete on policy, approvals, self-service, duty of care, disruption support, and expense integration.
- Event platforms connect registration, room blocks, travel, transfers, attendee communication, and reporting.
- Case-management systems treat a complex customer matter as a hierarchy of related work items, playbooks, SLAs, escalations, approvals, and evidence.
- Consumer platforms are absorbing conversational planning, social inspiration, natural-language search, maps, reviews, comparison, and booking.
- Airline retailing is moving from fragmented records toward richer offers and unified orders.
- AI ecosystems are moving toward tool and agent interoperability, while payment networks are developing explicit authorization layers for agentic commerce.

The defensible layer is therefore:

> **Constraint-aware, evidence-backed, commercially grounded, human-controlled travel execution.**

### AI reality check

Recent travel-agent benchmarks show large failures on joint constraint satisfaction, executable itineraries, multimodal evidence, and unstated traveler needs. Waypoint should therefore emphasize deterministic checks, typed infeasibility reasons, provenance, contradiction handling, and guarded autonomy rather than free-form generation alone.

---

## 2. Product architecture and opportunity map

### 2.1 Lifecycle

```text
Discover
→ Inquire
→ Capture
→ Structure
→ Clarify
→ Qualify
→ Research
→ Source
→ Price
→ Compare
→ Propose
→ Approve
→ Collect
→ Book
→ Confirm
→ Operate
→ Recover
→ Reconcile
→ Learn
→ Retain
```

### 2.2 Cross-cutting control planes

```text
Identity and delegated authority
Consent and privacy
Policy and suitability
Commercial controls
Human approvals
Audit and provenance
Security and compliance
Observability and evaluation
Automation and recovery
Integrations and interoperability
```

### 2.3 Durable platform primitives

- Canonical person, household, organization, group, trip, case, and relationship graph.
- Canonical supplier, product, contract, rate, inventory, offer, order, booking, and service graph.
- Canonical constraint, policy, evidence, decision, override, and approval model.
- Canonical payment, invoice, commission, payout, settlement, tax, and profitability model.
- Canonical event, task, timeline, incident, recovery, and audit model.
- Channel adapters for web, email, messaging, voice, browser extensions, mobile share sheets, social, and APIs.
- Supply adapters for GDS, NDC, CRS, bedbanks, channel managers, direct suppliers, spreadsheets, email, and manual operations.
- Payment adapters that preserve an explicit merchant-of-record and regulated-role boundary.
- Human-control boundaries for every consequential automated action.
- A source-of-truth architecture that prevents separate editable versions of the same customer, trip, order, or decision state.

### 2.4 Canonical product thesis candidates

These are alternatives to evaluate, not slogans to stack together:

1. **Agency Operations and Revenue OS**  
   For small and mid-market travel agencies that need to turn fragmented enquiries into profitable, executable, controlled trips.

2. **Travel Decision and Execution OS**  
   A constraint-aware layer that connects demand, policy, supply, commercial logic, fulfillment, and recovery.

3. **Human-Controlled Agentic Travel Infrastructure**  
   A platform through which humans and agents can safely research, decide, transact, and operate travel.

4. **Travel Case and Order Management Platform**  
   A shared operational record for customers, travelers, suppliers, orders, documents, money, incidents, and evidence.

The first is the most commercially understandable near-term framing. The others describe deeper platform direction.

---

## 3. Capability and opportunity registry

### 3.1 CAP-01: Acquisition, lead generation, and distribution

#### Current repository-backed surfaces `[CODE]`

- Public itinerary checker, event stream, result retrieval, and export.
- Social-message parsing and teaser unmasking.
- Direct inbound parsing.
- Tokenized public proposal links and acceptance.
- Public booking-data and document-collection links.
- Signup, join-code, invitation, and workspace-code flows.
- Seasonal campaign creation, simulation, preflight, and dispatch.
- Messaging provider webhooks and integration registry.

#### Explicit repository concepts `[DOC]`

- Chrome extension for WhatsApp Web and Gmail capture.
- Mobile share-sheet capture.
- Voice-note-to-enquiry conversion.
- Email-forwarding intake.
- Link-in-bio creator intake and branded creator links.
- Consumer itinerary-audit funnel.
- Audit-to-agency professional handoff.
- Free teaser followed by deposit-based unmasking.
- Agency website enquiry widgets.
- Host-agency white-label acquisition.
- DMC-to-agency referrals.
- Corporate offsite intake.
- Trade-community, association, referral, and content distribution.

#### External benchmark and market signals `[WEB]`

- Social inspiration is becoming transactional. Expedia Trip Matching converts Instagram travel content into trip ideas and bookable itineraries.
- Mindtrip for Business provides AI-guided discovery for tourism brands and DMOs using brand-controlled content.
- SquadTrip combines public trip pages, packages, add-ons, promo codes, legal documents, payments, and messaging.
- TrovaTrip demonstrates a three-sided marketplace among hosts, travelers, and operators.
- Expedia B2B and Spotnana illustrate embedded and white-label travel infrastructure.

#### Additional ideas and implicit expansion `[INFERENCE]`

- Embeddable enquiry widget SDK.
- QR-based offline enquiry capture for shops, events, trade fairs, partner desks, and printed campaigns.
- Affiliate, creator, partner, employee, sub-agency, and referral attribution.
- Campaign-to-enquiry, proposal, booking, margin, and repeat-trip attribution.
- Lead-source profitability.
- Duplicate-lead, household, company, and existing-client detection.
- Intent scoring and low-intent filtering.
- Lead routing by destination, value, language, specialty, availability, complexity, and regulatory requirement.
- Referral-fee and revenue-share accounting.
- Consent capture by acquisition source.
- Partner-branded landing-page generator.
- Destination feasibility calculators as SEO and AI-search acquisition surfaces.
- Visa, accessibility, budget, seasonality, and trip-risk checkers as acquisition surfaces.
- Shareable family and group preference collection links.
- Franchise, branch, territory, and multi-brand lead routing.
- AI-readable agency, service, and offer feeds for external assistants.
- GEO and machine-readable metadata for AI search and agentic commerce.
- Lead qualification agents that hand off to humans with a complete evidence packet.
- Request-for-trip marketplace where travelers publish structured briefs and vetted agencies respond.
- Agency referral exchange for destinations or trip types outside an agency's expertise.
- Destination-expert live consultation marketplace.
- Concierge callback scheduling.
- Planning-fee checkout embedded in first contact.
- Interactive lead magnet that exposes risks without giving away the full proprietary itinerary.
- Local partner co-marketing pages.
- Co-branded destination campaign kits.
- Agency microsite generator using canonical products, destination knowledge, and traveler-safe content.

#### Research questions, not commitments

- Which acquisition surfaces create qualified demand rather than free-tool usage?
- Which channels are stable, legal, and commercially accessible enough to automate?
- What data can be collected before explicit account creation?
- Which public tools create agency demand without disintermediating agencies?
- How much supplier detail can be shown before a planning fee, deposit, or verified commitment?
- Should Waypoint own a marketplace, enable agency-owned acquisition, or do both in separate modes?
- How will acquisition attribution survive cross-channel identity fragmentation?

**Sources:** [R01] [R10] [R12] [W12] [W13] [W45] [W46] [W47] [W48] [W49]

---

### 3.2 CAP-02: Omnichannel intake, stitching, extraction, and provenance

#### Current repository-backed surfaces `[CODE]`

- General inbound parse API.
- Social inbound parser.
- Optimistic trip-state synchronization.
- Server-sent trip-state event stream.
- Draft creation, restoration, promotion, events, and run association.
- Document extraction, attempts, retry, apply, reject, and version snapshots.
- Field and activity provenance foundations.

#### Explicit repository concepts `[DOC]`

- WhatsApp message stitching.
- Email-thread stitching.
- Voice-note transcription and extraction.
- Screenshot and image extraction.
- Passport, visa, ticket, confirmation, and rate-sheet OCR.
- Visual-intent extraction from inspiration images.
- Local PII detection and browser-side pre-scrubbing.
- Edge SLM or ONNX extraction.
- Offline capture queue.
- Progressive model pre-caching.
- Cross-channel identity stitching.
- Confidence-aware extraction.
- Agency-specific vocabulary and local-first fallbacks.

#### External benchmark and market signals `[WEB]`

- TravelJoy can convert forwarded supplier quotes into proposals.
- Tern Inbox Intelligence detects travel email, links it to the correct trip, and parses confirmations.
- Tern's AI Notetaker converts calls into transcripts, summaries, and actions.
- Travefy connects email directly to contact records.
- Consumer platforms are converting social, image, and natural-language inspiration into structured planning inputs.

#### Additional ideas and implicit expansion `[INFERENCE]`

- Attachment-bundle parsing across PDF, image, spreadsheet, document, audio, and video.
- Conversation reconstruction across dozens of messages and channels.
- Language detection, translation, and transliteration-aware matching.
- Contact, traveler, organization, supplier, property, airport, and destination entity resolution.
- Duplicate enquiry merging.
- Historical-value versus newly stated-value reconciliation.
- Per-field source, confidence, timestamp, extraction method, and inference rationale.
- Field-level correction feedback and learning.
- Channel-specific extraction quality metrics.
- Input-aware model routing.
- Sensitive-field redaction previews before upload.
- Low-confidence human-review queues.
- Bulk import from historical inboxes, drives, CRMs, and spreadsheets.
- Video and screen-recording intake.
- Live call copilot with explicit consent.
- Photo-board, mood-board, saved-post, and wish-list parsing.
- Supplier quote and contract diffing.
- Extraction integrity checks across message, attachment, and structured fields.
- Evidence bundle preserving original raw context for every applied change.
- Source priority rules by agency and field type.
- Agency dictionary for abbreviations, supplier nicknames, room codes, meal plans, and internal shorthand.
- Automatic splitting of one mixed conversation into multiple trips or requests.
- Detection of a trip update versus a new enquiry.
- Conversation timeline with changed facts highlighted.
- Contactless scan flow for passports and visas.
- Mobile camera capture with quality guidance.
- Browser extension that can capture selected text, full thread, attachments, or screenshot with explicit user action.
- Offline-first field intake for agents at fairs, hotels, destination visits, and sales events.
- Emailed supplier quote parser that maps line items into existing products and flags unknowns.
- Confirmation extraction that creates pending changes rather than silently updating canonical truth.

#### Research questions, not commitments

- What minimum evidence is required before a field changes canonical state?
- Which channels require official API access versus user-initiated capture?
- Which extraction tasks should remain local for privacy, cost, or latency?
- How should contradictory sources be ranked and surfaced?
- What correction rate is acceptable before automation becomes harmful?
- How should raw communication be retained, redacted, or deleted?
- Which inputs legally require participant consent?

**Sources:** [R01] [R08] [W01] [W03] [W05] [W06] [W49]

---

### 3.3 CAP-03: Identity, CRM, relationship memory, and household graph

#### Current repository-backed surfaces `[CODE]`

- Trip records and timelines.
- Inbox queues and follow-ups.
- Assignment ownership.
- Draft lifecycle and review events.
- Authentication, memberships, and agency roles.

#### Explicit repository concepts `[DOC]`

- Cross-trip customer memory.
- Repeat-customer preferences.
- Family and household memory.
- Mobility, dietary, health, hotel, room, airline, and brand preferences.
- Anniversary and milestone memory.
- Ghosted-lead and window-shopper handling.
- Churn and repeat-trip interventions.
- Customer-history browser.
- Revision history and scope-creep protection.
- What-changed-and-why comparison.

#### External benchmark and market signals `[WEB]`

- Tern can answer questions across complete CRM history and update linked family contacts from chat.
- Travefy stores preferences, loyalty numbers, passport data, trip history, custom fields, and integrated email.
- TravelJoy centralizes clients, tasks, reminders, forms, invoices, and trip context.
- Hospitality CRM platforms increasingly use complete guest profiles for proactive personalization and service recovery.

#### Additional ideas and implicit expansion `[INFERENCE]`

- Person, household, organization, group, advisor, supplier, and trip relationship graph.
- Contact merge, deduplication, and survivorship rules.
- Shared household addresses and preferences.
- Corporate traveler profile and delegated arranger relationship.
- Creator-audience traveler profile.
- Lifetime value and profitability.
- Recency-frequency-value analysis.
- Next-best-action and re-engagement recommendations.
- Relationship-strength and confidence scores.
- Consent-aware memory.
- Data expiry, forgetting, and re-confirmation controls.
- Advisor brand-voice and communication-style memory.
- Past objections and successful resolutions.
- Referral graph.
- Lost-deal reason history.
- Client portfolio transfer when staff leave.
- Client-specific approval, privacy, and service expectations.
- Preference source and last-confirmed timestamp.
- Household disagreement and consensus memory.
- Travel-companion compatibility memory.
- Loyalty, membership, status, and benefit wallet.
- Cross-brand identity where one operator runs multiple brands.
- Family organizer versus individual traveler visibility rules.
- Minor and guardian relationships.
- Caregiver, assistant, employer, sponsor, and emergency-contact relationships.
- Sensitive-trait handling that distinguishes explicit facts from prohibited inference.
- Preference confidence that decays over time.
- Memory confirmation at enquiry, proposal, booking, and post-trip stages.
- Relationship handover brief when a trip changes owner.
- Key-client service playbook.
- Client risk flags for fraud, abuse, payment, or operational complexity with strict governance.
- Corporate guest-traveler profiles without requiring employee accounts.
- Traveler portable profile that can be shared selectively with another agency or supplier.
- Customer data import and migration from spreadsheets, CRMs, itinerary tools, and email.

#### Research questions, not commitments

- Which memories are useful enough to justify retention?
- How should soft preferences decay or be re-confirmed?
- Which sensitive attributes should never be inferred?
- How should household members control shared versus private information?
- Can relationship memory improve conversion without becoming intrusive?
- What is agency-owned, traveler-owned, or jointly controlled?
- How should imported historical data be verified?

**Sources:** [R03] [R04] [R07] [W03] [W05] [W06] [W27]

---

### 3.4 CAP-04: Canonical trip case, state machine, collaboration, and work management

#### Current repository-backed surfaces `[CODE]`

- Trips, stages, timelines, and unified state.
- Inbox queues, bulk actions, and statistics.
- Assignments, claim, return, reassign, escalate, and unassign.
- Review actions, overrides, acknowledgements, and reassessment.
- Booking tasks, confirmations, and execution timelines.
- Audit events and agent events.

#### Explicit repository concepts `[DOC]`

- Trip Master Record.
- Single source of truth.
- Operator workbench.
- Family and group coordination.
- Supplier collaboration.
- Human signoff and review gates.
- Guided workflows.
- Owner command center.
- Operational dashboards.

#### External benchmark and market signals `[WEB]`

- ServiceNow models cases from multiple channels with assignment, workflows, playbooks, SLAs, escalation, major issues, and customer projects.
- ServiceNow case lines allow multiple related issues to progress independently under one parent case.
- Spotnana places traveler and servicing agents on the same underlying platform and data.
- Cvent connects registration, room blocks, flights, transfers, and follow-up communication.

#### Additional ideas and implicit expansion `[INFERENCE]`

- Trip as a parent case with independent order, traveler, supplier, document, payment, visa, incident, and approval lines.
- Case types for leisure, group, corporate, creator, wedding, retreat, education, and emergency travel.
- Configurable playbooks.
- SLA definitions by case type and severity.
- Milestone templates.
- Major-incident mode spanning many trips.
- Shift handover.
- Follow-the-sun operations.
- Customer-visible versus internal case views.
- Dependency graph between trip lines.
- Blocking and non-blocking task semantics.
- Conditional task generation.
- Human and agent work queues.
- Unified history across notes, changes, approvals, messages, documents, and transactions.
- Case health and readiness score.
- Cross-trip projects such as corporate offsites or destination weddings.
- Reusable operating templates by agency, destination, product, or customer segment.
- Transactional outbox and event sourcing for reliable state propagation.
- Temporal replay of any trip state.
- Field-level and line-level optimistic concurrency.
- Merge resolution for simultaneous human and agent edits.
- Watchers, followers, collaborators, and temporary participants.
- Project-level resource planning.
- Trip cloning with explicit carry-forward and reset rules.
- Bulk operations across trips, travelers, orders, or tasks.
- Escalation ladder by urgency, value, risk, and elapsed time.
- Case pause, archive, cancel, reopen, duplicate, merge, split, and transfer.
- Standardized case outcomes and loss reasons.
- Linked customer complaint, refund, and incident cases.
- Operational calendar combining tasks, deadlines, payments, bookings, and traveler events.

#### Research questions, not commitments

- Should Trip remain the top-level aggregate, or should a broader Case/Project aggregate own group and enterprise workflows?
- Which state transitions must be deterministic and which may be suggested by AI?
- How much workflow configurability can be exposed without becoming an unusable no-code platform?
- Which SLAs actually matter to agencies and travelers?
- Which state must be event-sourced versus stored as current snapshots?
- How should historical and operational records be separated?

**Sources:** [R01] [R06] [R09] [W20] [W23] [W25] [W26]

---

### 3.5 CAP-05: Constraint, suitability, policy, risk, and decision intelligence

#### Current repository-backed surfaces `[CODE]`

- Suitability evaluation and acknowledgement.
- Reassessment.
- Overrides and override histories.
- Agentic trip evaluation.
- Corporate policy audit.
- Trust scorecard.
- Gap identification and decision states.
- High-value review gates.
- Traveler-safe output boundary.

#### Explicit repository concepts `[DOC]`

- Visa and passport hard blockers.
- Budget feasibility.
- Mobility and accessibility constraints.
- Senior, toddler, and family pacing.
- Dietary requirements.
- Activity suitability.
- Group conflict detection.
- Fatigue and rest windows.
- Over-packed itinerary detection.
- Route and transfer feasibility.
- Weather and climate adaptation.
- Ethical and cultural sensitivity.
- Corporate policy compliance.
- Supplier-contract compliance.
- Cancellation and insurance risk.
- Proceed, ask, stop, and review gates.
- Grounded citations and confidence.

#### External benchmark and market signals `[WEB]`

- SAP Concur supports policy rules, approvals, exception handling, and enforcement modes.
- Navan combines spend controls, restricted destinations, group budgets, and duty of care.
- Mindtrip for Business allows brands and DMOs to impose geographic boundaries and authoritative content.
- Current research benchmarks show severe failures in multi-constraint, multimodal, and executable travel planning.

#### Additional ideas and implicit expansion `[INFERENCE]`

- Policy-as-code and policy-as-data.
- Agency-specific rule packs.
- Destination and nationality rule packs.
- Effective dates and rule versioning.
- Evidence and authority attached to every rule.
- Hard constraint, soft preference, aspiration, and unknown separation.
- Constraint-conflict explanations.
- Alternative generation after a blocker.
- Risk appetite and service-level configuration.
- Scenario comparison and counterfactual analysis.
- Cheapest feasible, best fit, lowest risk, and highest margin views.
- Group consensus and dissent tracking.
- Insurance-policy suitability.
- Accessibility verification confidence.
- Pre-booking red-team audit.
- Pre-departure and in-trip continuous reassessment.
- Post-trip outcome validation.
- Override reason capture and override-pattern analysis.
- Complaint and regret risk prediction.
- Commission-steering and commercial-bias audit.
- Fairness constraints for pricing and recommendation.
- Typed infeasibility reasons.
- Deterministic feasibility evaluator.
- Unstated-needs checklist without silently inferring sensitive traits.
- Multimodal evidence verification.
- Route topology and connection feasibility.
- Time-zone, opening-hours, travel-time, check-in, minimum-stay, age, and capacity validation.
- Visa admissibility and transit requirements.
- Health, vaccination, medication, altitude, climate, and insurance advisory layers with strict disclaimers.
- Cancellation concentration risk.
- Supplier dependency and single-point-of-failure detection.
- Traveler vulnerability and support-needs classification based only on explicit data.
- Corporate, school, group, and guardian policy inheritance.
- Decision trace showing facts, rules, evidence, alternatives, human changes, and final outcome.
- Outcome-based policy tuning using complaints, incidents, overrides, and post-trip feedback.

#### Research questions, not commitments

- Which decisions can be certified deterministically?
- How should unstated persona needs be handled without stereotyping?
- What evidence is sufficient for accessibility, safety, or legal claims?
- How can commercial optimization be exposed without steering or misleading the traveler?
- What accuracy threshold is required before a blocker becomes hard rather than advisory?
- Which policies are advisory, contractual, regulatory, or safety-critical?
- How should contradictory authoritative sources be handled?

**Sources:** [R03] [R04] [R05] [W19] [W46] [A01] [A02] [A03] [A04] [A05] [A06]

---
### 3.6 CAP-06: Research, destination intelligence, discovery, and content

#### Current repository-backed surfaces `[CODE]`

- Geography datasets.
- Activity provenance.
- Strategy and bundle generation.
- Knowledge-discovery cluster and digest endpoints.
- Intelligence reporting foundations.

#### Explicit repository concepts `[DOC]`

- Destination knowledge base.
- Reusable content library.
- Visual-intent extraction.
- Mood and taste graph.
- Budget feasibility tables.
- Visa and destination facts.
- Hotel and activity suitability.
- Visual search.
- Cultural etiquette.
- Community-host knowledge.
- Dynamic trip magazines.

#### External benchmark and market signals `[WEB]`

- Mindtrip combines AI with a large POI database, maps, photos, reviews, weather, saved inspiration, and brand-controlled authoritative content.
- Expedia is adding property comparison, property Q&A, package price insights, natural-language activity planning, and social in-feed planning.
- Booking.com uses natural-language filters, property Q&A, review summaries, and AI trip planning.
- Google is integrating travel Canvas, Maps, search, and partner booking.

#### Additional ideas and implicit expansion `[INFERENCE]`

- Evidence-ranked destination graph.
- Authoritative versus experiential source separation.
- Agency-owned destination playbooks.
- Supplier, guide, DMC, traveler, and local-expert contributions.
- Source freshness and contradiction detection.
- Seasonality, closure, strike, permit, and restriction monitoring.
- Neighborhood-level suitability.
- Experiential search such as quiet, authentic, design-led, family-friendly, low-friction, accessible, or nightlife-oriented.
- Review-theme extraction.
- Visual and video inspiration ingestion.
- Social trend detection.
- Event, festival, exhibition, sports, and school-holiday calendars.
- Local disruption and regulation feed.
- Content-rights and licensing ledger.
- Brand-safe image and content generation.
- Content localization.
- POI availability and booking confidence.
- Alternative discovery beyond crowded or over-touristed locations.
- Accessibility and sensory-environment descriptors.
- Sustainable and regenerative impact evidence.
- Destination knowledge contributions with review, confidence, and expiry.
- DMO and tourism-board content partnerships.
- AI-search visibility and structured destination content publishing.
- Destination comparison by cost, risk, weather, visa friction, pace, accessibility, and supplier strength.
- Route and gateway intelligence.
- Neighborhood-to-airport and attraction travel-time distributions.
- Property, room, bed, accessibility, and amenity evidence.
- Real versus marketing-claim discrepancy tracking.
- Local etiquette, dress, photography, safety, tipping, holiday, and cultural guidance.
- Content packs for proposals, pre-departure, in-trip, and post-trip communication.
- Agency-specific editorial approval and content overrides.
- Destination specialist knowledge capture from advisor conversations.
- Knowledge decay and revalidation workflows.
- Retrieval evaluation using real advisor questions.
- Source-level licensing and attribution controls.

#### Research questions, not commitments

- Which content sources are licensed and reliable enough for commercial use?
- How should agency expertise outrank generic web popularity?
- How can the product remain useful when real-time availability is absent?
- Can destination knowledge become a standalone B2B product for DMOs and operators?
- Which facts require continuous monitoring?
- Can traveler-generated feedback be used without exposing private or defamatory content?

**Sources:** [R05] [R10] [W45] [W46] [W47] [W49] [W50] [W51] [A02]

---

### 3.7 CAP-07: Supplier, contract, product, inventory, and connectivity

#### Current repository-backed surfaces `[CODE]`

- Integration registry.
- Yield opportunities.
- Supplier swap.
- Activity provenance.
- Strategy and bundle foundations.

#### Explicit repository concepts `[DOC]`

- Internal package library.
- Preferred supplier inventory.
- DMC and consortium inventory.
- Open-market fallback.
- CSV and Excel rate-sheet upload.
- AI column mapping.
- Supplier portal.
- Net and commissionable rates.
- Seasonal periods and blackout dates.
- Inventory allocation and soft holds.
- Supplier reliability and compliance.
- Supplier blacklist.
- Direct local and community-host orchestration.
- Supplier auction and negotiation.

#### External benchmark and market signals `[WEB]`

- Lemax centralizes product inventory, booking, package building, sales, supplier, and traveler workflows.
- Tourwriter includes supplier and rate databases, automatic pricing, bookings, and traveler payments.
- Tourplan models flexible products, complex contracts, multi-currency rates, inventory, operations, and finance.
- Tourplan can compare internal contracted rates with external dynamic supplier rates and confirm bookings in both systems.
- IATA NDC, ONE Order, and Travelport APIs are moving distribution toward richer offers, orders, and full servicing.

#### Additional ideas and implicit expansion `[INFERENCE]`

- Canonical supplier, contract, product, option, rate, inventory, offer, order, and service model.
- Supplier legal entity, trading name, branch, contact, and operating-area hierarchy.
- Contract versioning, approval, signature, and provenance.
- Contract expiry and renegotiation alerts.
- Rate validity, booking, cancellation, release, and payment windows.
- Occupancy, child, room, meal-plan, supplement, discount, allotment, free-sell, and promotion rules.
- Cancellation-policy normalization.
- Stop-sale, close-out, blackout, maintenance, and unavailable-service alerts.
- Supplier quote-request workflow.
- Response-time SLA and chase automation.
- Quote parsing from email and messaging.
- Supplier booking-request generation.
- Supplier quality, complaint, refund, and incident history.
- Reliability versus margin ranking.
- Agency-specific supplier weighting.
- Contracted, dynamic, GDS, bedbank, direct, and spot-rate comparison.
- Rate anomaly and stale-rate detection.
- Inventory freshness and source confidence.
- Duplicate product and supplier reconciliation.
- Content rights and image approvals.
- External GDS, CRS, bedbank, channel-manager, and direct API adapter layer.
- Offer and Order abstraction compatible with NDC and ONE Order.
- Supplier agent API and A2A capability card.
- Soft-hold negotiation.
- Waitlist and release management.
- Supplier onboarding, verification, compliance, banking, tax, and insurance.
- Supplier dispute and service-recovery workflow.
- Supplier portal, API, spreadsheet, email, and agent interfaces as interchangeable adapters.
- Multi-agency negotiated-contract support with strict tenant isolation.
- Contract rule testing against sample itineraries.
- Rate-load QA and four-eyes approval.
- Supplier product authoring and agency editorial override.
- Product taxonomy and mapping across inconsistent supplier schemas.
- Availability request and confirmation without full integration.
- Dynamic request-for-quote marketplace.
- Supplier performance score derived from response, confirmation, service, complaint, refund, and payout behavior.
- Preferred supplier program administration.
- Supplier credit limit, deposit, prepayment, and payment-term control.
- Destination-level supply coverage and concentration analysis.
- Backup supplier planning.
- Sustainability, accessibility, safety, licensing, and certification evidence.
- Direct contracting and community-host orchestration with local legal and tax checks.

#### Research questions, not commitments

- Which supplier category should be supported first?
- What contract complexity is required for the primary ICP?
- When should Waypoint integrate rather than store, quote, or book?
- How will stale rates and unavailable inventory be prevented from reaching travelers?
- What supplier data is proprietary and must never enter shared intelligence?
- What quality, verification, and dispute processes are needed before launching a marketplace?
- Can supplier onboarding be economical without human operations?

**Sources:** [R03] [R11] [W14] [W15] [W16] [W17] [W28] [W29] [W31]

---

### 3.8 CAP-08: Pricing, quotation, margin, yield, revenue, and commercial policy

#### Current repository-backed surfaces `[CODE]`

- Yield arbitrage by trip.
- Yield opportunity queue.
- Supplier swapping.
- Revenue analytics.
- Payment read model.
- High-value review gates.
- Trust-scorecard commercial signals.

#### Explicit repository concepts `[DOC]`

- Net, gross, markup, commission, and service-fee rules.
- Margin protection.
- Supplier comparison.
- Price locks.
- Creator and agency commission splits.
- Agent commissions.
- Multi-currency arbitrage.
- Deposits and payment plans.
- Supplier payouts.
- Commercial-fit optimization.
- Price-drop re-shopping.
- Resource futures and inventory hedging.
- Budget reality checks.

#### External benchmark and market signals `[WEB]`

- Tern and Travefy treat commission tracking and reconciliation as core workflow.
- Tourplan exposes sales, cost, and profitability by tour, agent, supplier, consultant, and market.
- WeTravel links traveler payments, supplier payouts, and controlled cards.
- IATA modern retailing is shifting toward dynamic offers and order-based financial flows.

#### Additional ideas and implicit expansion `[INFERENCE]`

- Quote versioning, approval, and expiry.
- Cost-to-sell waterfall.
- Item, trip, advisor, destination, supplier, channel, customer, and campaign profitability.
- Minimum-margin guard.
- Discount approval.
- Markup profiles by customer, product, market, season, channel, advisor, and agency branch.
- Planning, change, service, rush, cancellation, and after-hours fees.
- Cancellation and refund allocation.
- Deposit schedules and payment plans.
- FX spread, exposure, and lock visibility.
- Tax, GST, TDS, VAT, and e-invoice support.
- Commission accrual, reconciliation, dispute, payout, and unclaimed-commission detection.
- Supplier payment schedule.
- Expected versus actual margin.
- Revenue leakage detection.
- Quote expiry and repricing.
- Revenue and cash-flow forecasting.
- Profitability simulation before proposal.
- Traveler-fit optimization subject to commercial guardrails.
- Transparent commercial explanation modes.
- Commission-steering audit and counterfactual recommendation testing.
- Corporate negotiated-rate savings.
- Creator, affiliate, host, sub-agency, and advisor split engines.
- Dynamic packaging and bundle pricing.
- Inventory-risk pricing.
- Refund reserve and insolvency-protection accounting.
- Benchmark price range without revealing proprietary agency pricing.
- Cost confidence and source freshness.
- Price lock backed by supplier hold versus marketing countdown distinction.
- Group minimum viable size and break-even analysis.
- Tiered group pricing as enrollment changes.
- Single-room and occupancy supplement allocation.
- Complimentary traveler and tour-leader economics.
- Promotional and early-bird pricing.
- Fee waivers with approval.
- Corporate budget and cost-center guardrails.
- Multi-brand and franchise commercial policy.
- Revenue-share contracts with partners.
- Quote conversion analysis by price structure.
- Profitability impact of service recovery and disruption.
- Supplier rebates, overrides, and volume incentives.
- Net remittance and merchant models.
- Pricing ethics and disclosure modes.

#### Research questions, not commitments

- What commercial details should be visible to travelers?
- How should the system prove that recommendations are not improperly commission-steered?
- Which taxes, fees, settlement, and consumer-disclosure rules vary by market?
- Should payments be native, embedded, or partner-led?
- What pricing dimensions correlate with willingness to pay rather than internal complexity?
- Can automated pricing remain explainable and reversible?

**Sources:** [R03] [R05] [R10] [W05] [W07] [W08] [W09] [W10] [W16] [W29] [A06]

---

### 3.9 CAP-09: Proposal, trust, collaboration, acceptance, and conversion

#### Current repository-backed surfaces `[CODE]`

- Proposal-link generation.
- Tokenized proposal retrieval.
- Proposal acceptance.
- Trust scorecard.
- Public checker and export.
- Messaging and follow-up generation.
- Teaser unmasking.

#### Explicit repository concepts `[DOC]`

- Interactive mobile proposal.
- PDF export.
- Agency, creator, and partner branding.
- Price-lock countdown.
- Masked supplier and hotel names.
- Deposit-to-unmask.
- Suitability match.
- Verified supplier and cancellation badges.
- Risk and trade-off explanations.
- Traveler-safe output.
- Budget-versus-comfort comparison.
- One-click acceptance.

#### External benchmark and market signals `[WEB]`

- TravelJoy Smart Proposals support selectable options, approval, pricing, payments, and card authorization.
- Travefy and TravelJoy make polished mobile proposals and itineraries baseline advisor features.
- SquadTrip adds public trip pages, packages, add-ons, legal policies, and checkout.
- Expedia is investing in comparison, confidence, and price-insight surfaces.

#### Additional ideas and implicit expansion `[INFERENCE]`

- Side-by-side option comparison.
- Traveler comments and element-level annotations.
- Family and group voting.
- Advisor recommendation rationale.
- Revision requests attached to proposal elements.
- Proposal versions and diff.
- E-signature and terms acceptance.
- Privacy, disclosure, and consent acceptance.
- Open, read, share, and section-engagement analytics.
- Watermarking and intellectual-property protection.
- Expiring links and one-time access codes.
- Custom domains.
- Accessibility and localization modes.
- Automated reminder sequences.
- Proposal abandonment recovery.
- A/B testing and conversion experiments.
- Brand-template library.
- Proposal quality and completeness score.
- Transparent versus bundled price-display modes.
- Planning-fee or deposit collection.
- Booking and order creation after acceptance.
- Interactive what-if controls.
- Confidence and evidence drawer.
- Traveler understanding check.
- Explain why an option was excluded.
- Proposal agent API for external AI assistants.
- Group-specific package, room, date, airport, and add-on choices.
- Traveler-specific visibility within a shared group proposal.
- Approval hierarchy for family, corporate, school, or event decisions.
- Offer expiration and automatic stale-state warning.
- Reprice, withdraw, replace, and preserve-history controls.
- Advisor notes separated from traveler-safe copy.
- Comparison of price, pace, risk, cancellation flexibility, supplier confidence, and accessibility.
- Negotiation request and structured counteroffer.
- Proposal acceptance subject to unresolved conditions.
- Legal and regulatory disclosure blocks by market.
- Digital brochure and itinerary modes generated from the same source, not separate content.
- Co-branded agency and supplier presentation with controlled commercial visibility.
- Proposal accessibility audit.
- Conversion-support assistant that answers only from proposal and approved evidence.

#### Research questions, not commitments

- Which trust explanations increase conversion and which create confusion?
- How much choice is optimal?
- What should happen when supplier availability changes after publication?
- How should proposal IP be protected without reducing trust?
- Which acceptance actions create a binding contract or payment obligation?
- Does a traveler want evidence, simplicity, advisor confidence, or different modes by context?

**Sources:** [R01] [R12] [W01] [W02] [W04] [W12] [W47]

---

### 3.10 CAP-10: Booking, Order, fulfillment, confirmations, and operational execution

#### Current repository-backed surfaces `[CODE]`

- Booking-task generation, completion, and cancellation.
- Confirmation record, verification, and voiding.
- Execution timeline.
- Booking-data readiness.
- Documents and payments.
- Agent events, assignment, escalation, and review.

#### Explicit repository concepts `[DOC]`

- Booking readiness checklist.
- Supplier booking requests.
- Confirmation parsing.
- Trip Master Record.
- Pickup, transfer, rooming, flight, bus, and guide lists.
- Day-wise operations dashboard.
- Voucher generation.
- Service ordering.
- Local handoffs.
- Booking reconciliation.
- Supplier-response tracking.

#### External benchmark and market signals `[WEB]`

- Tourplan and Lemax connect enquiries, quotes, bookings, supplier communication, operations, and accounting.
- Cvent connects registration, housing, flight details, pickup, transfer, and hotel reporting.
- ONE Order points toward a unified customer order across booking, delivery, and accounting.
- Travelport APIs expose search, price, book, ticket, cancel, exchange, refund, ancillaries, and servicing.

#### Additional ideas and implicit expansion `[INFERENCE]`

- Order and reservation state machines.
- Request, quote, option, hold, confirm, ticket, service, cancel, refund, and close states.
- PNR, NDC Order, hotel, activity, transfer, rail, cruise, and local-service adapters.
- Supplier acknowledgment and deadline tracking.
- Deposit, cancellation, release, and ticketing deadlines.
- Resource conflicts and capacity management.
- Driver, guide, vehicle, room, equipment, venue, and attendee assignment.
- Operational run sheets.
- Calendar export and mobile field view.
- Offline manifests.
- Emergency contacts and local escalation.
- Booking evidence and receipts.
- Actual-versus-planned execution.
- No-show, failure, incident, and recovery records.
- Automatic post-service confirmation.
- Traveler arrival and welfare check.
- Shift and vendor handover.
- Order changes with line-level independent resolution.
- Single order abstraction across multiple suppliers.
- Fulfillment events and delivery proof.
- Settlement and accounting linkage.
- Trip digital twin reflecting current operational truth.
- Manual booking representation with the same evidence and status model as integrated bookings.
- Queue and servicing workbench for air changes.
- Traveler name and document validation before ticketing.
- Rooming and occupancy validation.
- Transfer manifest linked to live arrival information.
- Voucher versioning and traveler delivery.
- Supplier reconfirmation schedule.
- Pre-departure readiness gate.
- Post-booking changes and reissue history.
- Shared service dependencies across travelers or group sub-cohorts.
- Service acceptance and quality evidence.
- Field staff proof of pickup, delivery, check-in, or completion.
- Customer change request translated into impacted order lines, price changes, approvals, and supplier actions.
- Operational exceptions queue.
- Automatic identification of abandoned holds and unconfirmed services.
- Booking cloning and recurring group templates.

#### Research questions, not commitments

- What booking content and servicing should be integrated first?
- Can a shared Order abstraction survive GDS, NDC, direct, and manual supplier differences?
- Which fulfillment events are essential for the first operator segment?
- How will manual supplier actions be represented without breaking auditability?
- What is the minimum viable operations depth before Waypoint can replace spreadsheets?
- Which execution roles need mobile or offline access?

**Sources:** [R01] [R03] [W14] [W16] [W17] [W23] [W29] [W31]

---
### 3.11 CAP-11: Traveler data, documents, digital identity, visa, and verification

#### Current repository-backed surfaces `[CODE]`

- Public booking-data collection.
- Public document upload.
- Internal document storage and download.
- Document extraction, attempts, retry, apply, and reject.
- Booking-data review and payment data.
- Confirmation verification.

#### Explicit repository concepts `[DOC]`

- Passport, visa, insurance, waiver, and authorization collection.
- Destination and traveler-specific checklists.
- Missing-document reminders.
- Name and date mismatch detection.
- Expiry checks.
- Secure traveler vault.
- PII scrubbing.
- OCR and human verification.
- Distributed group collection.

#### External benchmark and market signals `[WEB]`

- WeTravel and SquadTrip collect registration data, documents, waivers, and payment details.
- IATA ONE Order and One ID direction points toward unified orders and stronger digital identity.
- Corporate platforms depend on accurate, current traveler profiles and location data.

#### Additional ideas and implicit expansion `[INFERENCE]`

- Document requirements by nationality, residence, age, route, transit point, destination, and trip type.
- Household document reuse with consent.
- Expiry and passport-validity calculations.
- Visa application, appointment, submission, biometrics, interview, and status tracking.
- Consent receipts.
- Fine-grained supplier sharing.
- Automatic redaction and selective disclosure.
- Malware and file-safety scanning.
- Duplicate, altered, or tampered document detection.
- Image-quality and completeness checks.
- Structured form filling.
- Minor and guardian consent.
- Medical document handling with stronger controls.
- Data-retention and deletion policies.
- Traveler self-export and self-delete.
- Versioned identity record.
- Document-to-booking reconciliation.
- Transliteration and name-order checking.
- Verifiable credentials.
- Digital identity wallet integration.
- Passkey and delegated identity.
- One-time document access.
- Admissibility checks and source provenance.
- Traveler profile completeness and readiness score.
- Multi-traveler group collection status.
- Document request by role, not indiscriminate upload.
- Safe document sharing with visa partners, DMCs, airlines, hotels, insurers, or employers.
- Time-bound access and automatic revocation.
- Evidence that a document was verified, by whom, when, and against what source.
- Document change impact analysis across bookings.
- Required re-verification after identity change.
- Digital consent for biometrics, health data, location, emergency contact, marketing, and partner sharing.
- Travel authorization and guardian approval rules.
- Automated reminders calibrated to processing lead time and trip urgency.
- Country-rule monitoring with effective dates.
- Human legal-advice boundary and explicit disclaimers.

#### Research questions, not commitments

- Which identity capabilities can be provided without becoming a regulated identity provider?
- Which documents should be stored versus tokenized or referenced?
- How should minors, guardians, and group organizers share control?
- What retention rules vary by market and booking role?
- Which document verification claims can Waypoint make?
- When does location or biometric processing become disproportionate?

**Sources:** [R01] [R05] [W09] [W12] [W29] [W36]

---

### 3.12 CAP-12: Payments, invoicing, accounting, commissions, settlement, and treasury

#### Current repository-backed surfaces `[CODE]`

- Payment read model.
- Booking payment data.
- Revenue analytics.
- Yield calculations.
- Booking collection flows.
- High-value gates.

#### Explicit repository concepts `[DOC]`

- Traveler payments and payment plans.
- Deposits.
- Multi-party and split payments.
- Creator, affiliate, and agent payouts.
- Supplier payments.
- Commission tracking.
- Invoice generation.
- GST and UPI support.
- Multi-currency.
- Accounts receivable and payable.
- Corporate consolidated invoicing.

#### External benchmark and market signals `[WEB]`

- WeTravel combines traveler payments, multi-currency checkout, supplier payouts, supplier verification, and controlled cards.
- Tern parses supplier statements and reconciles commissions to bookings and advisor payouts.
- TravelJoy and Travefy include invoicing, payments, authorization, and commission workflows.
- IATA BSP centralizes settlement between airlines and accredited agents.
- UPI supports instant merchant payments, QR, intent, collect, AutoPay, and conversational regional-language access.

#### Additional ideas and implicit expansion `[INFERENCE]`

- Double-entry operational ledger.
- Payment allocation to travelers, orders, suppliers, invoices, and fees.
- Installment schedules, dunning, retry, and failed-payment recovery.
- Refund and cancellation-fee workflows.
- Chargeback evidence.
- Trust-account and client-money handling.
- Supplier payable schedule and cash-flow forecast.
- Commission accrual, statement import, match, dispute, and payout.
- Host, sub-agency, creator, referral, and advisor split rules.
- Tax invoice, GST, e-invoice, credit note, and debit note.
- TDS and withholding support.
- Currency gains and losses.
- Accounting synchronization.
- Expense cards and single-use supplier cards.
- Trip, event, department, project, advisor, brand, and agency P&L.
- Cost-center and project allocation.
- Corporate budgets and actuals.
- Payment and financial approval workflows.
- Refund reserve and insolvency protection.
- Agentic payment mandates, limits, expiration, consume-once authorization, and audit.
- UPI payment links, QR, AutoPay installments, and UPI One World support.
- Payment-provider abstraction to avoid becoming merchant of record prematurely.
- Payment schedule templates by trip type.
- Group deposit thresholds and minimum-enrollment rules.
- Traveler payment ownership and organizer payment view.
- Payment reminders differentiated by traveler, organizer, corporate sponsor, or finance team.
- Supplier bank-detail verification and change-control workflow.
- Fraud and unusual-payment detection.
- Invoice reconciliation with accepted proposal and actual order.
- Refund status portal.
- Payment method surcharge and disclosure controls.
- Partial payment, overpayment, credit balance, wallet, and credit-note handling.
- Corporate billing, purchase order, cost center, approval, and consolidated statement.
- Payout release linked to service delivery or milestone.
- Escrow or protected-funds partner exploration.
- Automated commission statement request and chase.
- Missing commission recovery workflow.
- Payment and payout audit export.
- PCI scope minimization through tokenization and hosted payment pages.
- Revenue recognition and deferred revenue research.
- Multi-entity and multi-country accounting.

#### Research questions, not commitments

- Who should be merchant of record in each business model?
- Which money flows create licensing, KYC, AML, tax, trust-account, or insolvency obligations?
- Can supplier payouts be partner-led while Waypoint owns reconciliation?
- What payment authorization model is safe for autonomous agents?
- Which India and international payment rails fit the primary customer base?
- What gross margin remains after payment, support, AI, fraud, and compliance costs?

**Sources:** [W01] [W05] [W08] [W09] [W10] [W11] [W32] [W33] [W37] [W38] [W40] [W41] [W42] [W54] [W55]

---

### 3.13 CAP-13: Traveler, family, group, attendee, and guest experience

#### Current repository-backed surfaces `[CODE]`

- Public proposal and acceptance.
- Public checker.
- Booking collection and document upload.
- Messaging and concierge monitoring.
- Live event streams.
- Execution timeline and confirmations.

#### Explicit repository concepts `[DOC]`

- Traveler dashboard.
- Interactive itinerary.
- Group and creator portals.
- Family preference collection.
- Voting and shared itinerary.
- Split payments and payment tracking.
- Document sharing.
- Post-booking updates.
- Emergency contacts.
- Flight status and weather alerts.
- Local tips.
- Expense tracking.
- SOS and offline itinerary.

#### External benchmark and market signals `[WEB]`

- SquadTrip provides branded trip pages, checkout, registration, add-ons, legal documents, group chat, messages, and payment plans.
- WeTravel provides traveler login, manifests, documents, payments, and trip management.
- Cvent handles attendee registration, room blocks, roommate matching, travel requests, and personalized confirmations.
- Navan and Spotnana provide group-event booking and traveler self-service.

#### Additional ideas and implicit expansion `[INFERENCE]`

- Traveler PWA and native mobile clients.
- Wallet passes.
- Offline itinerary, documents, vouchers, and emergency information.
- Push notifications and calendar sync.
- Maps, navigation, meeting points, and transfer instructions.
- Local-language assistance.
- Time-zone-aware reminders.
- Group announcements and role-based visibility.
- Minor, guardian, companion, and caretaker access.
- Accessibility and low-vision modes.
- Packing lists and pre-departure tasks.
- In-trip polls, concierge requests, and issue reporting.
- Incident evidence upload.
- Expense and reimbursement capture.
- Travel journal and shared media.
- Post-trip memory confirmation.
- Referral and repeat-trip loops.
- Roommate matching.
- Room-block and sub-block management.
- Attendee registration and RSVP.
- Group leader and host controls.
- Traveler understanding and acknowledgment of material risks.
- Guest travel without corporate employee identity.
- Family or group decision workspace before proposal finalization.
- Individual traveler private fields within a group.
- Shared versus private payment and document status.
- Group consensus deadlines.
- Traveler preference conflicts and organizer decisions.
- Accessible itinerary variants.
- Dynamic day-of-travel view.
- Local contact, guide, driver, supplier, and support details.
- Real-time change acceptance.
- Traveler change request and impact estimate.
- Trip countdown and readiness checklist.
- Personal medication, dietary, mobility, and accessibility reminders with explicit user control.
- On-trip spending, tipping, and currency guidance.
- Safe offline emergency card.
- Destination risk and cultural guidance.
- Service rating by itinerary item.
- Lost property and complaint workflow.
- Post-trip photo, review, referral, and rebooking flows.
- Group community features that can be disabled for privacy or professional travel.
- White-label traveler experience per agency, creator, host network, or corporate client.

#### Research questions, not commitments

- Which traveler features reduce agency work rather than create another support surface?
- What should be available without login?
- How should group organizers and individual travelers divide control?
- Which in-trip features require native mobile access?
- How should traveler communication avoid becoming another noisy channel?
- Which accessibility and safety capabilities require specialist validation?

**Sources:** [R09] [R12] [W09] [W12] [W18] [W20] [W23] [W24]

---

### 3.14 CAP-14: Communications, follow-up, notification, and service orchestration

#### Current repository-backed surfaces `[CODE]`

- Message sending and provider webhooks.
- Follow-up generation and dashboard.
- Snooze, reschedule, and completion.
- Alert destinations and testing.
- Communication and support settings.
- Seasonal campaigns.

#### Explicit repository concepts `[DOC]`

- WhatsApp Cloud API.
- Email, SMS, and voice.
- Traveler-safe communication.
- Tone calibration.
- One-click copy generation.
- Post-booking and disruption updates.
- Group announcements.
- Agency brand voice.
- Multilingual communication.
- Communication playbooks.

#### External benchmark and market signals `[WEB]`

- Travel advisor suites are consolidating email, forms, reminders, and workflow inside the client and trip record.
- Tern is adding AI-triggered workflow actions and email sequences.
- Corporate platforms provide multi-channel proactive disruption care.
- Group platforms include message blasts, scheduled communication, and group chat.

#### Additional ideas and implicit expansion `[INFERENCE]`

- Unified inbox.
- Gmail, Outlook, IMAP, and calendar synchronization.
- Thread-to-trip and message-to-line association.
- Delivery, read, response, bounce, and failure status.
- Consent and opt-out management.
- Template and playbook library.
- Conditional sequences and behavioral triggers.
- Advisor approval and supervised send.
- Translation with human preview.
- Quiet hours and time-zone scheduling.
- Non-response escalation.
- Conversation sentiment and anxiety signals.
- Communication burden and responsiveness metrics.
- Workload-aware routing.
- Draft provenance and human-edit comparison.
- Brand consistency and compliance checks.
- Spam and platform-policy controls.
- Two-way emergency acknowledgment.
- Supplier, traveler, partner, and internal communication channels in one history.
- AI-generated call brief and post-call actions.
- Conversation-level sensitive-data controls.
- Context-specific tone for sales, support, crisis, documents, payments, and complaints.
- Channel fallback when delivery fails.
- Communication preference by traveler and relationship.
- Organizer-only versus all-traveler announcements.
- Automated pre-departure schedule.
- Service reminders based on actual booking state.
- Payment reminders linked to ledger truth.
- Supplier chase sequences.
- Post-trip feedback, review, referral, and reactivation campaigns.
- Approval request and decision notifications.
- Human escalation when sentiment, risk, value, or repeated failure crosses a threshold.
- In-message action cards for approve, pay, upload, choose, confirm, or acknowledge.
- Communication archive export.
- Call recording and transcription with jurisdiction-aware consent.
- AI assistant that answers only from approved trip state and evidence.
- Brand-voice testing and drift detection.

#### Research questions, not commitments

- Which communication channels are essential for each geography and persona?
- Where must a human approve before send?
- How will platform-policy changes be isolated from the core workflow?
- Can communication automation improve conversion without increasing complaints?
- Which channels support reliable identity, delivery, and consent evidence?
- How should AI-generated communication be disclosed, if at all?

**Sources:** [R01] [R12] [W03] [W05] [W06] [W12] [W22]

---

### 3.15 CAP-15: Disruption, concierge, duty of care, crisis, and recovery

#### Current repository-backed surfaces `[CODE]`

- Trip monitoring.
- Disruption listing.
- Auto-rebooking endpoint.
- Corporate duty-of-care cockpit.
- Execution timeline.
- Messaging, alerts, overrides, and review.

#### Explicit repository concepts `[DOC]`

- Ghost Concierge.
- Flight and hotel monitoring.
- Downstream schedule impact.
- Transfer rescheduling.
- Late-check-in notices.
- Group cascade analysis.
- Corporate offsite and creator-group monitoring.
- Live traveler updates.
- Zero-cost rebooking.
- Human approval for financial actions.
- Autonomy modes and takeover.
- Crisis orchestration.
- Geolocation safety and threat alerts.
- Climate-adaptive rerouting.
- Compensation and consumer-rights support.

#### External benchmark and market signals `[WEB]`

- Amex GBT combines automatic alerts, traveler contact, live agent support, location visibility, and proactive rebooking.
- Navan combines real-time traveler tracking, targeted notification, restricted destinations, and group travel controls.
- Spotnana emphasizes current trip data, duty-of-care integrations, and a shared agent/traveler servicing platform.
- IATA interline pilots show faster disruption rebooking through modern Offer and Order standards.

#### Additional ideas and implicit expansion `[INFERENCE]`

- Multi-source disruption ingestion.
- Impact graph across flights, hotels, transfers, activities, meetings, documents, and travelers.
- Recovery option search and ranking.
- Cost, risk, schedule, relationship, policy, accessibility, and traveler-impact comparison.
- Traveler prioritization and vulnerability rules.
- Group splitting and reunification.
- Emergency supplier sourcing.
- Crisis runbooks and major-incident command.
- Mass notification and acknowledgment.
- Duty-of-care check-ins and welfare status.
- Emergency contact escalation.
- Insurance claim and compensation packet generation.
- Refund and service-recovery tracking.
- Post-incident review.
- Supplier failure feedback.
- Autonomy threshold and financial-reserve configuration.
- Human takeover at trip, line, and action level.
- Complete action audit and rollback.
- Scenario simulation before action.
- Regional incident view across all active trips.
- Offline emergency access.
- Travel-assistance partner handoff.
- Crisis communication templates by severity and audience.
- Incident triage by urgency, affected travelers, downstream loss, and safety.
- Flight, rail, weather, strike, geopolitical, health, supplier, accommodation, and local-transport incident types.
- Group arrival-wave recalculation.
- Meeting, event, transfer, check-in, meal, and activity cascade updates.
- Pre-approved recovery budgets.
- Automated zero-cost actions only under verified conditions.
- Approval cards with exact financial and operational effects.
- Alternative supplier hold before cancellation.
- Traveler consent and preference for rebooking.
- Corporate security and HR notification rules.
- Incident timeline, evidence, decision, and outcome export.
- Root-cause and preventability analysis.
- Recovery playbook learning from completed incidents.
- SLA and support partner performance.
- Disaster-recovery mode for Waypoint itself.

#### Research questions, not commitments

- Which disruption sources are authoritative and commercially accessible?
- What actions are reversible, compensatable, or too risky to automate?
- How does Waypoint avoid presenting itself as a life-safety guarantee?
- What support coverage is needed before selling duty-of-care claims?
- Which jurisdictions regulate travel assistance, insurance, or emergency support?
- Can a small agency operationally fulfill the recovery options generated by the system?

**Sources:** [R05] [R11] [R12] [W18] [W20] [W21] [W22] [W29]

---
### 3.16 CAP-16: Team, workforce, training, review, knowledge, and organizational governance

#### Current repository-backed surfaces `[CODE]`

- Members, invitations, roles, and permissions.
- Team workload.
- Assignment, claim, reassign, return, escalate, and unassign.
- High-value gates and review signoff.
- Review queue and bulk actions.
- Agent analytics and audit trails.

#### Explicit repository concepts `[DOC]`

- Junior-agent guided workflows.
- Mandatory review gates.
- Training modules.
- Best-practices and knowledge libraries.
- Mistake-prevention warnings.
- Personal and agency templates.
- Performance scorecards.
- Capacity planning.
- Workforce gamification.
- Simulation-based training.
- Specialist-agent marketplace.
- Knowledge retention when employees leave.
- Owner visibility without micromanagement.

#### External benchmark and market signals `[WEB]`

- ServiceNow uses matching rules, playbooks, approvals, escalations, and case tasks.
- Tern differentiates agency-managed records, collaborator roles, owner reporting, and sub-agency commission workflows.
- Spotnana provides a shared servicing platform and automated task management.

#### Additional ideas and implicit expansion `[INFERENCE]`

- Skill, destination, language, complexity, value, relationship, and risk-based routing.
- Advisor capacity prediction.
- Fairness, leave, shift, and burnout constraints.
- On-call and weekend coverage.
- Risk-based QA sampling.
- Peer review and reviewer calibration.
- Coaching recommendations.
- Competency matrix.
- Training generated from actual errors.
- Certification and authorization levels.
- Shadow mode and progressive autonomy.
- Knowledge article recommendations.
- Expert escalation and internal source finding.
- Cross-agency specialist contracting.
- Role-specific dashboards.
- Commission and performance alignment.
- Workload versus revenue analysis.
- Succession and continuity planning.
- Human and AI workforce capacity in one planner.
- Agent action review and quality score.
- Standard operating procedure conformance.
- Organizational memory extraction from completed cases.
- Senior review reserved for high-risk or novel decisions.
- Advisor portfolio ownership and transfer.
- Team, department, branch, brand, legal entity, host, and sub-agency hierarchy.
- Temporary contractor and supplier access.
- Approval delegation and substitute approvers.
- Work queue prioritization by SLA, traveler impact, risk, value, and aging.
- Team communication and handoff notes inside the canonical case.
- Staff onboarding using realistic scenario replay.
- Skill-development plan tied to actual work.
- Knowledge gaps detected from repeated questions or overrides.
- Recognition for quality, service recovery, and knowledge contribution rather than only sales.
- Audit of AI use by staff.
- Separation of coaching analytics from disciplinary analytics.
- Field-operations workforce scheduling.
- Vendor and freelance specialist credential management.
- Agency-level configuration templates for roles and workflows.

#### Research questions, not commitments

- Which productivity metrics create useful coaching versus harmful surveillance?
- How should quality and commercial incentives be balanced?
- What permissions and workflows differ across host, sub-agency, DMC, and corporate structures?
- Can progressive autonomy measurably reduce training time?
- How much organizational hierarchy is required for the primary ICP?
- Which expertise should be internal, networked, or outsourced?

**Sources:** [R04] [R09] [W05] [W07] [W25] [W26]

---

### 3.17 CAP-17: Analytics, experimentation, evaluation, intelligence, and observability

#### Current repository-backed surfaces `[CODE]`

- Summary, pipeline, revenue, team, funnel, bottleneck, escalation, review, and agent analytics.
- Alerts and exports.
- Knowledge-discovery clusters and digest.
- Unified state and integrity issues.
- Runtime events and audit records.

#### Explicit repository concepts `[DOC]`

- Conversion and margin analysis.
- Supplier performance.
- Seasonal forecasting.
- Lead-lifecycle analytics.
- Autonomy performance.
- Prompt performance.
- Scenario replay.
- Experiment lineage and autoresearch.
- Wasted-spend detection.
- Market learning.

#### External benchmark and market signals `[WEB]`

- Tern provides advisor, agency, client, trip, sales, KPI, expected-commission, received-commission, and payout reporting.
- Tourplan exposes operational and profitability reporting.
- Phocuswright argues custom AI evaluations and clean data governance are prerequisites for scaling agentic systems.
- Travel-agent benchmarks show that soft LLM judging is inadequate for certifying executable travel plans.

#### Additional ideas and implicit expansion `[INFERENCE]`

- Cohort retention and seat activation.
- Time to first value, response, proposal, booking, and readiness.
- Percentage of real work captured versus completed outside Waypoint.
- Trip-stage velocity and revision burden.
- Advisor utilization and quality.
- Margin leakage and supplier failure.
- Document completion and error.
- Traveler self-service and support deflection.
- Communication burden.
- Disruption detection and recovery time.
- Model cost, latency, and quality by task.
- Human edit distance and correction rate.
- Override, false-positive, and blocked-output analysis.
- Champion-challenger and controlled experiments.
- Feature adoption and path analysis.
- Customer health, churn, and expansion prediction.
- Benchmarking with privacy constraints.
- Deterministic trip feasibility evaluation.
- Multimodal retrieval and factual verification.
- Commission-steering audit.
- Agent replay and action-level evaluation.
- Tool reliability scorecard.
- Data freshness and provenance coverage.
- Operational SLOs and error budgets.
- Acquisition source to contribution-margin attribution.
- Lead quality and qualification accuracy.
- Proposal engagement and abandonment.
- Reasons for human edits and overrides.
- Review queue precision and reviewer disagreement.
- Supplier response, confirmation, incident, complaint, refund, and payment performance.
- Payment collection, dunning, refund, and commission aging.
- Traveler readiness, issue, satisfaction, and repeat behavior.
- Incident preventability and recovery economics.
- Workflow cycle time and rework.
- Integration reliability and data-staleness monitoring.
- Tenant-level usage, costs, limits, and value realization.
- Agent autonomy readiness by workflow.
- Synthetic versus real evidence separation.
- Product-simulation workspace that never contaminates real metrics.
- Privacy budget and minimum cohort thresholds for shared benchmarks.
- Metric-definition registry and semantic layer.
- Data-quality checks and metric lineage.
- Experiment guardrails for safety, quality, and revenue.
- Executive, operator, advisor, finance, supplier, and product scorecards.

#### Research questions, not commitments

- Which metrics predict retention for the selected ICP?
- Which AI evaluations correlate with real operator trust?
- How should synthetic, simulated, and real production evidence be separated?
- What telemetry can be collected without creating privacy risk?
- Which benchmarks are actionable rather than vanity comparisons?
- How will metric definitions remain consistent across backend, frontend, exports, and reports?

**Sources:** [R06] [R07] [W07] [W16] [W43] [W44] [A01] [A02] [A03] [A04] [A06]

---

### 3.18 CAP-18: Platform, APIs, integrations, embedded products, and interoperability

#### Current repository-backed surfaces `[CODE]`

- Broad FastAPI surface.
- Frontend route registry.
- Integration provider registry.
- Settings and workspace APIs.
- Event streams.
- Agent runtime.

#### Explicit repository concepts `[DOC]`

- White label.
- API access.
- CRM, accounting, calendar, email, messaging, supplier, GDS, and payment integrations.
- Partner portals.
- Multi-agent runtime.
- Reusable capability libraries.

#### External benchmark and market signals `[WEB]`

- Spotnana and Expedia B2B offer composable and white-label Travel-as-a-Service infrastructure.
- Tourplan exposes APIs and host-to-host connectivity.
- MCP standardizes AI access to tools and data.
- A2A standardizes capability discovery and long-running collaboration between independent agents.
- Visa and Mastercard are creating agentic-commerce payment infrastructure.

#### Additional ideas and implicit expansion `[INFERENCE]`

- Public developer platform.
- OAuth apps and scoped service accounts.
- Webhooks, event subscriptions, replay, and delivery guarantees.
- Sandbox and test tenants.
- Versioned APIs and compatibility policy.
- Integration marketplace.
- Embedded intake, audit, proposal, booking collection, and traveler portal.
- MCP server for operator and partner tools.
- A2A agent cards for intake, research, sourcing, booking, payments, risk, visa, and support agents.
- Machine-readable product, offer, order, policy, and capability manifests.
- Partner SDKs.
- No-code workflow connectors.
- Data import, export, backup, and migration tools.
- Bulk APIs.
- Rate limits and metering.
- API monetization.
- Regional hosting and data routing.
- Tenant hierarchy and white-label brand inheritance.
- Extension points without shadow data models.
- Agent-ready merchant and inventory endpoints.
- Observability and conformance test kits.
- Integration health dashboard.
- Credential rotation and secret isolation.
- Partner-specific data scopes.
- Idempotency keys and webhook signatures.
- Long-running job and callback model.
- Async event bus and durable workflow support.
- Canonical adapter contracts for channels, suppliers, payments, identity, risk, CRM, accounting, and analytics.
- GraphQL or query layer only where it solves real partner needs.
- File-based interoperability for partners without APIs.
- Data mapping and transformation workspace.
- Integration test fixtures and certification.
- Embedded analytics and co-branded surfaces.
- Multi-brand domain, theme, email, and communication configuration.
- Headless travel decision and suitability API.
- Trip Audit API.
- Supplier Rate Intelligence API.
- Booking Readiness API.
- Traveler Communication API.
- Human approval and audit service exposed to external agents.

#### Research questions, not commitments

- Which primitives are valuable enough to expose as products?
- Can external agents act safely without bypassing policy and audit?
- What interoperability standards are mature enough to adopt now?
- How will ecosystem integrations avoid becoming a support burden?
- What should remain internal until schemas and behavior stabilize?
- Can a public platform monetize before the core operator product is excellent?

**Sources:** [R01] [R11] [W16] [W20] [W48] [W52] [W53] [W54] [W55]

---

### 3.19 CAP-19: Security, privacy, compliance, trust, and legal governance

#### Current repository-backed surfaces `[CODE]`

- Authentication and token refresh.
- Roles, permissions, memberships, and tenant-scoped access.
- Audit and routing-health triage.
- Unified-state integrity.
- LLM guard and per-agency settings.
- Approval and autonomy settings.
- Internal document download.
- Traveler-safe output separation.

#### Explicit repository concepts `[DOC]`

- Row-level tenant isolation.
- PII scrubbing and local extraction.
- GDPR and India DPDP.
- Audit-chain hashing.
- RAG citations.
- Prompt and model governance.
- Human takeover.
- Compliance hard gates.
- Data sovereignty.
- Self-sovereign identity.
- Biometric consent.
- AI governance.
- Consumer and package-travel compliance.

#### External benchmark and market signals `[WEB]`

- India DPDP Rules 2025 and the enforcement timeline create concrete privacy obligations.
- EU Package Travel Directive changes strengthen cancellation, refund, voucher, complaint, and insolvency requirements.
- PCI DSS applies to entities that store, process, transmit, or can affect cardholder data.
- IATA accreditation, BSP, and travel-agent handbooks impose operational and financial obligations.
- Agentic-commerce infrastructure emphasizes authorization, spending limits, identity, transparency, and user control.

#### Additional ideas and implicit expansion `[INFERENCE]`

- SSO, SCIM, MFA, and passkeys.
- Fine-grained resource and field permissions.
- Supplier and partner isolation.
- Delegated and temporary access.
- Purpose limitation and consent ledger.
- Data retention, export, correction, and deletion.
- Regional data residency.
- Encryption-key and secrets management.
- Model/provider data-routing policy.
- Sensitive-field access logging.
- Anomaly and fraud detection.
- Session and device management.
- Backup, restore, disaster recovery, and business-continuity verification.
- Incident response and vendor-risk management.
- SOC 2 and ISO 27001 control mapping.
- Penetration testing and secure SDLC.
- Legal hold and evidence export.
- Algorithmic decision explanation.
- Package-versus-standalone-service classification.
- Refund, voucher, complaint, and insolvency workflows.
- Seller-of-travel and jurisdiction rules.
- KYC and AML boundary analysis.
- AI action authorization with cryptographic mandates and consume-once semantics.
- Prompt-injection and tool-poisoning defenses.
- Commercial-bias disclosures.
- Data-processing inventory and records of processing.
- Data classification and handling policies.
- Security boundary between internal notes and traveler output.
- Policy requiring human review for legal, medical, safety, or financial claims.
- Third-party model and integration risk register.
- Tenant-configurable provider restrictions.
- Secure export, share, and download links.
- File malware, content, and metadata inspection.
- Audit immutability and chain verification.
- Regulatory evidence packages.
- Customer complaint, dispute, and remediation case.
- Terms, privacy notice, disclosure, and consent versioning.
- AI-generated content labeling where required.
- Privacy impact assessments for biometrics, location, health, minors, and agentic commerce.
- Cross-border transfer mechanism tracking.
- Controlled production access and support impersonation audit.
- Breach communication workflow.
- Supplier and partner compliance attestations.

#### Research questions, not commitments

- Which legal role does Waypoint assume in each business model?
- Which claims require licenses, guarantees, accreditation, insurance, or professional review?
- Which AI actions require explicit consent each time?
- What evidence must be retained for disputes and audits?
- What is the minimum security and compliance baseline for the primary ICP?
- Which regulated functions should always be performed by partners?

**Sources:** [R01] [R05] [W32] [W33] [W34] [W35] [W36] [W37] [W54] [W55] [A06]

---

### 3.20 CAP-20: Agentic runtime, autonomy, recovery, simulation, and human control

#### Current repository-backed surfaces `[CODE]`

- Agent runtime status, events, and run-once control.
- Recovery-agent foundations.
- Trip agent events.
- Agentic trip evaluation.
- Audit logs.
- LLM usage guard.
- Autonomy and approval settings.
- Overrides and signoff.
- Ghost workflow foundations.

#### Explicit repository concepts `[DOC]`

- Multi-agent orchestrator.
- Specialist shadow agents.
- Self-healing recovery.
- Prompt-tuning agent.
- Scenario replay.
- Autoresearch and feedback loops.
- Three-tier autonomy.
- Human takeover.
- Compliance blocks.
- Model and cost budgets.
- Fallbacks and grounding.
- High-concurrency benchmarks.
- Autonomic immune response.

#### External benchmark and market signals `[WEB]`

- Travel businesses are moving from generative-AI experiments toward agentic execution.
- MCP and A2A create standard tool and agent interoperability layers.
- Visa and Mastercard emphasize permissioned, transparent, controlled agentic payment.
- Current travel benchmarks show agents still fail frequently on tightly coupled constraints and multimodal evidence.

#### Additional ideas and implicit expansion `[INFERENCE]`

- Agent registry and capability manifest.
- Tool and data permissions per agent.
- Per-agent budget, model, latency, quality, and risk policy.
- Task-level autonomy rather than one global switch.
- Action simulation and dry run.
- Approval cards with exact proposed effects.
- Reversible actions and compensating transactions.
- Idempotency and concurrency controls.
- Retry, timeout, dead-letter, and recovery policies.
- Failure isolation.
- Agent, prompt, policy, and tool versioning.
- Shadow mode and champion-challenger.
- Human correction capture.
- Tool success and trust metrics.
- Trace inspection and replay.
- Safety case per action.
- Cross-agent conflict resolution.
- Sandboxed third-party agents.
- Customer-configurable agent teams.
- Agent-to-agent delegation through A2A.
- MCP tool access under central policy.
- Cryptographic authorization mandate for financial action.
- Human takeover at any hierarchy level.
- Autonomy earned from verified performance rather than enabled by marketing tier.
- Agent roles for intake, identity resolution, clarifications, research, sourcing, pricing, proposal, document verification, booking, payment, disruption, communications, QA, audit, and recovery.
- Deterministic validators surrounding model output.
- Explicit source-of-truth read before action.
- Stale-state check immediately before execution.
- Precondition and postcondition contracts.
- Rate and inventory freshness gate.
- Action approval expiration.
- Tool-call evidence and receipts.
- Multi-agent plan visualization.
- Agent work queue and capacity.
- Human operator ability to edit an agent's proposed plan before execution.
- Restricted action modes: read, draft, simulate, prepare, approve, execute, reconcile.
- Automatic downgrade to advisory mode after reliability, data, policy, or tool failure.
- Incident and rollback runbook for autonomous actions.
- Customer-facing explanation of what an agent did and why.
- Agent reputation based on verified task outcomes.
- Continuous evaluation against real corrections and incidents.

#### Research questions, not commitments

- Which workflows can become autonomous after enough evidence?
- What verification is required before executing a supplier or payment action?
- How should agents behave when tools disagree or data is stale?
- What autonomy metrics justify reducing human review?
- How should external agents be authenticated and authorized?
- What must remain impossible for an agent to do?

**Sources:** [R06] [R11] [R12] [W43] [W44] [W52] [W53] [W54] [W55] [A01] [A02] [A03]

---

### 3.21 CAP-21: Ecosystem, marketplaces, networks, and shared intelligence

#### Current repository-backed surfaces `[CODE]`

- Public checker lead surface.
- Integration registry.
- Supplier and yield foundations.
- Agency workspace and membership foundations.

#### Explicit repository concepts `[DOC]`

- Host-agency distribution.
- White-label agency platform.
- DMC supplier portal.
- Inter-agency specialist marketplace.
- Supplier marketplace and blacklist.
- Cross-agency intelligence pooling.
- Community hosts.
- Creator-agency-DMC collaboration.
- Supplier auctions and automated negotiation.
- Agency handoff and referral network.

#### External benchmark and market signals `[WEB]`

- TrovaTrip demonstrates a host-traveler-operator marketplace.
- WeTravel operates a verified supplier network and partner hub.
- Spotnana and Expedia B2B demonstrate embedded and partner-led travel infrastructure.
- IATA and GDS ecosystems demonstrate standardized identity, distribution, settlement, and partner connectivity.

#### Additional ideas and implicit expansion `[INFERENCE]`

- Agency specialization directory.
- Warm-lead marketplace.
- Destination-specialist and human-concierge marketplace.
- Guide, driver, ground-handler, visa, insurance, accessibility, and safety partner networks.
- Partner verification and reputation.
- Shared non-proprietary risk and accessibility intelligence.
- Shared destination feasibility baselines.
- Shared visa and document rule graph.
- Contributor incentives.
- Data clean room and privacy-preserving aggregation.
- Network dispute resolution.
- Referral and revenue-share accounting.
- Partner settlement.
- Capability marketplace for AI agents.
- White-label tenant marketplace.
- Supplier demand forecasting without exposing customer lists.
- Collective incident intelligence.
- Benchmark library with opt-in anonymized contributions.
- Portable supplier and agency credentials.
- Agency-to-agency trip transfer.
- Overflow operations marketplace.
- Expert review marketplace.
- Local emergency support network.
- Host-agency shared services.
- DMC and supplier request-for-quote exchange.
- Co-branded package marketplace.
- Verified content and itinerary module marketplace.
- Agency template marketplace.
- Training and certification marketplace.
- Reputation based on verified operational outcomes rather than unmoderated ratings.
- Network-level fraud and supplier-risk signals.
- Privacy-safe federated evaluation.
- Partner API access and metering.
- Multi-party contracting, commission, payout, and audit.
- Marketplace governance, suspension, appeal, and incident response.

#### Research questions, not commitments

- What shared data creates value without weakening participating agencies?
- How will marketplace quality be controlled?
- Which network side should be built first?
- Can network effects emerge before the standalone workflow product is excellent?
- What dispute, liability, payment, and consumer-protection obligations arise?
- Is Waypoint a software provider, marketplace operator, agent, reseller, or a configurable combination?

**Sources:** [R10] [R11] [R12] [W09] [W11] [W13] [W20] [W32]

---

### 3.22 CAP-22: Specialty, experimental, and frontier exploration

#### Current repository-backed surfaces `[CODE]`

- No broad production claim is made for this section. Some frontier-named routes and documents exist, but every capability requires separate verification.

#### Explicit repository concepts `[DOC]`

- Biometric wellness and jetlag mitigation.
- Predictive health and medical logistics.
- Emotional anxiety mitigation.
- Operational stress digital twin.
- Spatial pre-visualization, 3D, and AR.
- Dynamic trip magazines.
- Legacy and milestone travel.
- Climate-adaptive itineraries.
- Regenerative travel.
- Cultural etiquette.
- Community-host orchestration.
- Extreme-environment risk.
- Orbital and sub-orbital logistics.
- Diplomatic and legal shields.
- Post-quantum identity.
- Dark inventory.
- Autonomous resource futures.
- Deep-time cultural archives.
- Post-biological travel.
- Civilizational seed movement.
- Interstellar logistics.

#### External benchmark and market signals `[WEB]`

- Consumer platforms are expanding into social inspiration, multimodal planning, maps, reviews, and in-destination assistance.
- Airline retailing is moving toward dynamic offers, digital identity, and order-based servicing.
- Agentic-commerce infrastructure may eventually let agents transact with other agents and suppliers under explicit mandates.

#### Additional ideas and implicit expansion `[SPECULATIVE]`

- Frontier Lab with no delivery dates.
- Simulation-only prototypes.
- Research partnerships with universities, DMOs, accessibility groups, insurers, health providers, expedition operators, or standards bodies.
- Synthetic scenario corpora.
- Long-horizon operational digital twin.
- Embodied and ambient travel assistance.
- Wearable and sensor integration under explicit consent.
- Spatial accessibility verification.
- Carbon and regenerative-impact planning.
- Cultural and ethical impact assessment.
- Travel memory and heritage archive.
- Remote-presence and virtual-travel experiences.
- Space, polar, deep-sea, and extreme-environment planning simulations.
- Neurodiversity and sensory-aware travel research.
- Climate migration and temporary-relocation planning research.
- Autonomous mobility and robotics handoff.
- Post-quantum and self-sovereign travel credentials.
- Digital-twin simulation of destinations, groups, and operational stress.
- Community-owned tourism coordination.
- Destination carrying-capacity and overtourism simulation.
- Long-term traveler health and circadian planning.
- Life-event and legacy travel planning.
- Multigenerational family archive linked to travel history.

#### Research questions, not commitments

- What is intellectually interesting but commercially irrelevant?
- What evidence would move a frontier item into adjacency research?
- Which concepts create unacceptable medical, biometric, safety, or legal risk?
- How can frontier work improve the core without distracting delivery?
- Which partnerships can fund or validate research without committing product scope?
- What should be explicitly prohibited regardless of technical feasibility?

**Sources:** [R05] [R13] [W28] [W29] [W43] [W54] [W55]

---
## 4. Persona and stakeholder opportunity map

A feature should not be approved merely because a persona can use it. The persona must have a frequent, severe, monetizable problem, and Waypoint must have a credible right to solve it.

### 4.1 Agency and operator roles

| Persona | Primary pain | Relevant capability families |
|---|---|---|
| Solo advisor | Fragmented enquiries, memory load, slow response, no operational backup | Native capture, CRM memory, quick follow-up, reusable proposals, reminders, mobile mode, commission view |
| Junior advisor | Does not know what is missing, unsafe, infeasible, or commercially wrong | Guided workflow, hard gates, explanations, review, escalation, training |
| Senior advisor | Interrupted by avoidable reviews and exceptions | Risk-based queues, expert tools, delegation, reusable knowledge, exception handling |
| Agency owner | Quality variation, margin leakage, weak visibility, knowledge loss | Workload, reviews, policies, revenue, margins, retention, operational command center |
| Operations coordinator | Confirmations, suppliers, pickups, changes, deadlines | Booking tasks, confirmation control, manifests, supplier communication, timeline, incidents |
| Ticketing specialist | PNR, NDC, fare rules, exchanges, queues, and reissues | Air servicing adapter, fare-rule audit, queue and deadline workflows |
| Visa and document specialist | Changing requirements, missing or invalid documents | Rule graph, checklist, document vault, extraction, expiry, mismatch, status |
| Finance and accounts | Invoices, supplier payables, commissions, and reconciliation | Ledger, AR/AP, statement parsing, payouts, GST, accounting integration |
| Sales and marketing | Slow response, poor attribution, and lost leads | Lead scoring, sequences, campaigns, public tools, referrals, analytics |
| Quality reviewer | Hidden risk and inconsistent output | Audit queue, provenance, suitability, high-value gates, override history |
| Agency administrator | Permissions, policies, costs, integrations, compliance | RBAC, settings, SSO, usage guard, audit, data controls |
| Host-agency operator | Standardizing hundreds of independent advisors | Hierarchy, white label, training, shared supplier programs, consolidated reporting |
| Branch manager | Needs local control with central standards | Branch pipelines, permissions, targets, supplier access, review, performance |
| Product or contracting manager | Rates, products, contracts, content, and profitability | Supplier model, rate loading, QA, package authoring, content control, margin |
| Customer support specialist | Must resolve issues without complete context | Unified case, communication history, booking truth, escalation, recovery |
| Field operations lead | Coordinates guides, drivers, venues, and on-site changes | Mobile operations, manifests, assignments, incidents, proof of service |
| Independent contractor or sub-agent | Needs autonomy inside host rules | Scoped workspace, shared suppliers, commissions, approval, portable client work |
| Compliance or risk manager | Needs evidence that policy and controls are followed | Policy engine, audit, data controls, reviews, incident and complaint reporting |

### 4.2 Traveler, family, group, and attendee roles

| Persona | Primary pain | Relevant capability families |
|---|---|---|
| Prospective traveler | Slow answers, uncertainty, opaque options | Fast intake, feasibility, trust, comparison, interactive proposal |
| Primary family planner | Carries coordination and administration | Preference collection, voting, documents, payment tracking, announcements |
| Family or multi-generational traveler | Conflicting ages, pace, budgets, diets, and mobility | Group suitability, pacing, trade-off views, household memory |
| Senior or accessibility traveler | Generic plans ignore real constraints | Evidence-backed accessibility, route and fatigue validation |
| High-value traveler | Needs discretion, continuity, and human judgment | Relationship memory, privacy controls, concierge, trusted suppliers, human signoff |
| Independent traveler | Wants validation rather than full service | Public audit, optimization, professional handoff |
| In-trip traveler | Anxiety, disruption, unclear next action | Live itinerary, alerts, recovery options, support |
| Repeat traveler | Repeats preferences and context every trip | Cross-trip memory and proactive suggestions |
| Group attendee | Does not control the trip but needs personal clarity | Personal portal, payment, documents, itinerary, alerts, issue reporting |
| Group organizer or host | Collects money and details while managing social pressure | Registration, payment plans, roster, communication, host controls |
| Corporate traveler | Needs compliant self-service and support | Policy-aware options, profile, approval, duty of care, expense integration |
| Corporate guest traveler | Lacks employee identity but still needs travel service | Guest profile, sponsor, policy, approval, communication, support |
| Executive traveler | Needs discretion, delegated arrangement, and minimal friction | EA delegation, preference memory, private communication, recovery |
| Minor traveler | Requires guardian authority and additional safeguards | Guardian consent, document control, rooming, welfare, communication boundaries |
| Caregiver or companion | Needs visibility and coordination without owning the booking | Delegated access, traveler support needs, emergency and itinerary information |
| Event attendee | Needs registration, housing, travel, and personal schedule | Event project, attendee portal, room block, transfers, communication |
| Wedding guest | Needs a simple subset of a complex destination event | Guest cohort, room block, transfers, events, payment, support |
| Student or pilgrim group member | Depends on organizer and group operations | Roster, guardian or leader access, documents, payments, safety, announcements |

### 4.3 Partner and ecosystem roles

| Persona | Primary pain | Relevant capability families |
|---|---|---|
| DMC | Repeated rate distribution, manual quotes, slow agency response | Contract ingestion, inventory, quote and booking portal, yield, soft holds |
| Hotel or local supplier | Fragmented requests, confirmations, and payments | Product/rate management, booking requests, status, payout visibility |
| Guide, driver, or field coordinator | Last-minute changes and unclear run sheets | Mobile operations, manifests, assignments, alerts, proof of service |
| Consortium or host network | Member enablement and quality | White label, shared templates, preferred suppliers, governance |
| Creator or community host | DM lead loss, group chaos, commission opacity | Social intake, branded proposal, group portal, concierge, split payout |
| Corporate EA | Delegated multi-executive coordination | Act-on-behalf permissions, preferences, policies, synchronization, disruption |
| Corporate travel manager | Policy, spend, safety, reporting | Policy engine, duty of care, approvals, analytics |
| Corporate approver or finance | Exceptions, budgets, audit | Approval, cost center, invoice, expense integration |
| DMO or tourism board | Needs qualified demand and authoritative destination representation | Brand-controlled content, discovery, leads, analytics, partner network |
| Insurance or assistance provider | Needs incident, traveler, policy, and claim context | Risk, incident, evidence packet, handoff, status |
| Visa or immigration partner | Needs complete, accurate, permissioned traveler data | Document case, rule graph, secure sharing, deadlines, audit |
| Host agency | Needs compliant infrastructure for a distributed advisor network | Tenant hierarchy, shared suppliers, training, commission, oversight |
| GDS, NDC, CRS, or bedbank partner | Needs clean adapter boundaries and servicing context | Offer and Order model, API, credentials, audit, reconciliation |
| Payment or banking partner | Needs clear authorization and transaction context | Payment mandates, tokenization, ledger, reconciliation, fraud controls |
| Auditor, regulator, or insurer | Needs evidence and accountability | Immutable audit, provenance, consent, exports, incident history |
| Integration or agent partner | Needs stable access and extension points | API, webhooks, MCP, A2A, sandbox, scopes, metering |
| Marketplace moderator | Needs quality, dispute, fraud, and suspension controls | Verification, reputation, complaint, payout hold, governance |

### 4.4 Anti-personas and non-targets

- Travelers wanting only generic free inspiration with no professional-service intent.
- Agencies unwilling to move any operational truth out of private memory or spreadsheets.
- High-volume operators requiring immediate full GDS, ticketing, accounting, and global support replacement before adopting.
- Enterprises expecting complete expense, card, reimbursement, and global TMC capabilities from the first deployment.
- Suppliers unwilling to maintain rates, respond, or integrate in any supported format.
- Buyers seeking uncontrolled autonomous purchasing or rebooking.
- Use cases requiring medical, legal, immigration, security, or life-safety guarantees Waypoint cannot responsibly provide.
- Marketplace participants unwilling to accept verification, dispute, data, and commercial rules.

---

## 5. Pain-point taxonomy

### 5.1 Acquisition and sales

- A lead arrives in a channel the system cannot capture.
- Response is too slow.
- Lead intent is unknown.
- Critical requirements surface after hours of work.
- Follow-up is inconsistent.
- No source attribution or channel profitability.
- Proposal does not build enough trust to convert.
- Agency cannot protect itinerary intellectual property.
- Advisor repeats intake across CRM, proposal tool, supplier chats, and spreadsheets.
- Low-intent leads consume expensive research and quoting time.
- No consistent planning-fee or deposit process.
- Partner and referral leads are not tracked or compensated.

### 5.2 Knowledge and memory

- Client preferences live in the advisor's head.
- Staff departure removes relationship context.
- Supplier knowledge is scattered across chats and spreadsheets.
- Rules, rates, and cancellation policies become stale.
- Past mistakes are not converted into institutional learning.
- Nobody knows why a prior decision was made.
- Historical context cannot be trusted because source and date are absent.
- Knowledge is trapped in documents rather than available at the decision point.
- Agencies cannot distinguish proprietary expertise from generic web content.

### 5.3 Planning and decision quality

- Constraints conflict or remain unstated.
- Itinerary is physically impossible or too tiring.
- Price is not realistic.
- Supplier option is commercially poor or unreliable.
- Internal margin information leaks into traveler output.
- Recommendation cannot be explained or verified.
- AI produces plausible but non-executable content.
- Persona needs are stereotyped or silently inferred.
- Accessibility, visa, safety, or opening-hours evidence is missing or stale.
- Traveler and commercial goals conflict without an explicit policy.
- Human overrides occur without explanation or learning.

### 5.4 Supplier and commercial operations

- Rates are copied from stale files.
- Contract conditions are lost.
- Supplier responses are slow.
- Availability is uncertain.
- Quotes and invoices disagree.
- Commission or margin is untracked.
- Supplier performance is not learned.
- No one knows which supplier was chosen and why.
- Changes are not propagated to supplier bookings and traveler output.
- Agencies depend too heavily on one supplier without visibility.
- Rate loading is error-prone and lacks approval.

### 5.5 Booking and fulfillment

- Names, dates, and services mismatch.
- Tasks and deadlines are spread across people and tools.
- Supplier confirmations are not reconciled.
- Traveler documents arrive late or incomplete.
- Operations retype data from sales.
- Field staff do not have current information.
- Holds expire unnoticed.
- Reissues, refunds, or changes lose context.
- Traveler-facing vouchers and internal orders disagree.
- Manual bookings have less auditability than API bookings.

### 5.6 Traveler and group coordination

- One organizer carries the entire burden.
- Group members disagree or fail to respond.
- Payments and documents are incomplete.
- Travelers cannot find the current itinerary.
- Updates are fragmented.
- Travelers do not understand material risks or exclusions.
- Individuals cannot control private data inside a group.
- Rooming, transfer, and payment status are opaque.
- Event or group changes do not reach everyone consistently.
- Traveler self-service creates more support because state is incomplete.

### 5.7 Disruption and support

- A delay creates cascading failures.
- Affected travelers and downstream services are not identified quickly.
- Recovery options are not compared consistently.
- Support lacks current trip context.
- Financial and relationship consequences are not controlled.
- No structured post-incident learning.
- Travelers receive alerts but no executable next step.
- Agents are overwhelmed by simultaneous incidents.
- Recovery actions create new issues in unrelated trip lines.
- Duty-of-care claims exceed actual service capability.

### 5.8 Team and governance

- Junior staff make preventable mistakes.
- Owners lack visibility without micromanagement.
- Review burden is not risk-based.
- Workload is uneven.
- Automation acts without clear authority.
- Audit and evidence are incomplete.
- Different branches or advisors follow inconsistent processes.
- Experts answer the same questions repeatedly.
- Performance metrics reward sales while ignoring quality and operational burden.
- Staff cannot hand off cases cleanly.

### 5.9 Finance and compliance

- Client money, supplier payouts, commissions, and taxes are disconnected.
- Refunds and cancellations are handled manually.
- Card data expands security scope.
- Consent and data retention are unclear.
- Jurisdiction and package-travel obligations are not encoded.
- Commercial bias is hidden.
- Supplier bank-detail changes can create fraud risk.
- Commission statements cannot be matched to bookings.
- Corporate cost centers and approvals are disconnected from booking.
- Automated payment lacks clear user authority.

### 5.10 Platform and integration

- Every integration creates a new data model or shadow source of truth.
- Credentials expire without visibility.
- Webhook delivery failures silently lose state.
- Partner APIs are unstable or inconsistent.
- External agents can access tools without sufficient context or limits.
- Data exports are incomplete or non-portable.
- Tenant-specific configuration becomes hard-coded.
- Observability does not connect technical failures to traveler or revenue impact.

---

## 6. Vertical expansion map

| ID | Vertical | Portfolio classification | Why it matters |
|---|---|---|---|
| A1 | Mid-market outbound agencies, roughly 4–15 seats | Primary candidate | Highest overlap with current intake, assignment, review, proposal, and analytics core. |
| A2 | Boutique and specialist agencies | Primary-compatible | Luxury, family, honeymoon, senior, accessible, adventure, cruise, and destination specialists. |
| A3 | Inbound tour operators and DMCs | Closest expansion | Requires deeper contracts, products, inventory, operations, and finance. |
| A4 | Group and multi-day operators | Closest expansion | Requires storefront, registration, rosters, payments, payouts, manifests, and field operations. |
| A5 | Host agencies and consortia | Distribution expansion | Requires tenant hierarchy, white label, training, shared suppliers, and consolidated reporting. |
| B1 | Creator-led group travel | Reusable mode | Social acquisition, co-branding, group commerce, host controls, and commission splits. |
| B2 | Corporate offsites and executive travel | Reusable mode | Policy, delegated arrangers, group travel, duty of care, approvals, and invoicing. |
| B3 | MICE and event travel | Reusable mode | Attendee registration, venue and room blocks, approvals, travel, manifests, and budgets. |
| B4 | Destination weddings | Reusable mode | Guest cohorts, room blocks, transfers, events, documents, and payment plans. |
| B5 | Retreats and wellness travel | Reusable mode | Group sales, waivers, dietary and health constraints, field operations. |
| B6 | Educational and student travel | Reusable mode | Guardian consent, rooming, safety, documents, affordability, institutional approval. |
| B7 | Sports team and tournament travel | Reusable mode | Team rosters, equipment, schedules, rooms, transport, and medical needs. |
| B8 | Religious and pilgrimage travel | Reusable mode | Large groups, accessibility, documentation, cultural requirements, and operations. |
| B9 | Meetings and conferences | Reusable mode | Registration, air, housing, shuttles, agendas, cost centers, and attendee support. |
| B10 | Incentive travel | Reusable mode | Eligibility, invitation, group operations, premium experience, measurement, and sponsor reporting. |
| B11 | School reunions and affinity groups | Reusable mode | Community acquisition, deposits, group decisions, rooms, and communication. |
| B12 | Remote-team retreats | Reusable mode | Corporate policy, guest travelers, venues, travel, rooming, and reimbursement. |
| C1 | Medical travel | Specialist regulated | Requires stronger health-data governance and provider validation. |
| C2 | Adventure and expedition travel | Specialist regulated | Requires equipment, guide certification, insurance, evacuation, and safety protocols. |
| C3 | Cruise, yacht, and charter | Specialist | Requires cabin inventory, manifests, port rules, and complex changes. |
| C4 | Film, media, and production travel | Specialist | Crew, equipment, permits, production schedule, and cost centers. |
| C5 | Government, diplomatic, and VVIP travel | Specialist high-risk | Security, discretion, approvals, regional controls, and vetted supply. |
| C6 | Evacuation and emergency relocation | Specialist life-safety | Real-time capacity, crisis command, identity, and government coordination. |
| C7 | Sports fan and event packages | Specialist commercial | Event inventory, travel bundle, demand spikes, cancellation, and customer support. |
| C8 | Accessible travel specialist network | Specialist trust | Verified accessibility evidence, equipment, companions, providers, and risk controls. |
| C9 | Visa and relocation coordination | Adjacent case product | Document-heavy, rule-driven, deadline-sensitive workflows. |
| D1 | Digital nomad and extended stay | Deferred | Cross-cuts visas, housing, recurring services, taxation, and long-duration state. |
| D2 | Orbital, extreme-environment, post-biological, and interstellar travel | Frontier Lab | Preserve as research only. |

### 6.1 Vertical admission rule

A vertical should not enter active execution unless:

1. At least roughly 70% of its workflow can reuse shared primitives.
2. The buyer, daily user, pain, willingness to pay, and distribution path are identifiable.
3. Waypoint's legal, contractual, operational, and payment role is understood.
4. It does not require a parallel source of truth.
5. A bounded validation experiment can test the thesis before major build-out.
6. Required supplier, payment, identity, risk, or booking integrations are commercially accessible.
7. The support and service burden fits the intended business model.
8. The vertical strengthens rather than fragments the core architecture.

### 6.2 Vertical-mode principle

A vertical should usually be represented through:

- configuration;
- role and permission sets;
- policy packs;
- workflow playbooks;
- templates;
- data extensions;
- integrations;
- views and terminology;

not a separate application and database.

---

## 7. Horizontal and adjacent-industry exploration

| Analogy or adjacent market | Transferable insight | Waypoint implication |
|---|---|---|
| Case management | Travel resembles a complex multi-line case with intake, evidence, tasks, approvals, exceptions, and resolution. | Strengthen canonical case, playbooks, SLAs, and major incidents. |
| Order management and fulfillment | A trip is a bundle of offers and orders fulfilled by many suppliers. | Adopt offer, order-line, fulfillment-event, change, cancel, refund, and reconciliation thinking. |
| Logistics control tower | Trips require visibility, exception detection, downstream impact, and recovery. | Build impact graphs, operational truth, and incident command. |
| Event operations | Groups need registration, room blocks, attendee data, transfers, payments, and communication. | Reusable group and event project mode. |
| Hospitality CRM | Personalization depends on durable guest profiles and service recovery. | Make memory operational, not merely searchable. |
| Insurance claims | Evidence, coverage, incident, approval, payout, and dispute workflows mirror disruption and refund work. | Claims packet and compensation support. |
| Legal and immigration case management | Document-heavy cases have effective-date rules and human review. | Visa and document workflow with policy provenance. |
| Field service | Mobile workers need assignments, run sheets, proof of service, offline mode, and exception handling. | Guide, driver, meet-and-assist, and ground-operations app. |
| Financial operations | Commission reconciliation, settlements, client money, and supplier payouts are operational finance. | Ledger and reconciliation layer. |
| Marketplace trust and safety | Multi-sided ecosystems require verification, reputation, disputes, suspension, and controlled payouts. | Partner verification and network governance. |
| Digital identity and delegated authority | Advisors act for agencies, EAs act for employees, parents act for minors, and agents act for users. | Delegation, consent, identity wallet, and action mandate. |
| Agentic commerce | External AI agents will discover, compare, authorize, and transact. | Agent-ready offers, mandates, policy, and auditable actions. |
| Knowledge graph and decision intelligence | The moat is relationships among people, constraints, supply, policies, evidence, and outcomes. | Typed graph plus deterministic decision services. |
| Revenue operations | Lead source, proposal, booking, payment, margin, and retention form one commercial funnel. | Connect GTM, workflow, and profitability. |
| Customer support | Support quality depends on one complete customer and order history. | Shared traveler-agent state, unified case, and resolution playbooks. |
| Project portfolio management | Agencies operate many trips and events with competing resources and deadlines. | Portfolio, capacity, risk, and milestone views. |
| Contract lifecycle management | Supplier rates and conditions require versioning, approval, obligation, and expiry management. | Contract system instead of file storage alone. |
| Data clean rooms | Network learning must protect proprietary and personal data. | Privacy-preserving benchmarks and shared risk intelligence. |
| Cybersecurity policy engines | Access and action should be evaluated against identity, context, purpose, and risk. | Central authorization for humans, integrations, and agents. |
| Digital twin and simulation | Operational change should be simulated before execution. | Trip, group, and disruption impact simulation. |

### 7.1 Outside-travel reusable product theses

The architecture can later support adjacent products where the same pattern exists:

```text
Messy intake
→ structured case
→ missing-information analysis
→ constraint and policy evaluation
→ internal decision output
→ customer-safe output
→ approval
→ execution
→ audit
```

Potential adjacent domains:

- Immigration and relocation case coordination.
- Insurance brokerage and claims.
- Real-estate transaction coordination.
- Destination-event and wedding operations.
- Custom logistics and field-service coordination.
- Wealth-advisory onboarding.
- Legal intake and matter coordination.
- Healthcare-navigation administration.
- Education admissions and document cases.
- Corporate mobility.

These belong in an adjacent-opportunity appendix, not the active Waypoint roadmap.

---
## 8. Competitor and category landscape

Competitor analysis should be performed by complete user journey and operating model, not by counting features on landing pages.

### 8.1 Advisor CRM, itinerary, and proposal suites

**Examples:** TravelJoy, Travefy, Tern.

#### Capabilities becoming parity

- CRM and contact history.
- Email integration.
- Forms and structured client data collection.
- Tasks, reminders, and workflow automation.
- Branded proposals and itineraries.
- Client approval and selectable options.
- Payments, invoices, and card authorization.
- Group booking pages.
- Commission tracking and reconciliation.
- Advisor and agency reporting.
- AI-assisted email, notes, and confirmation parsing.
- Website and lead-capture tools.
- Collaboration and agency-managed client records.

#### Waypoint implication

Ordinary CRM, itinerary generation, or task automation is not a moat. Waypoint must differentiate through:

- constraint intelligence;
- evidence and provenance;
- supplier economics;
- commercial controls;
- operational truth;
- human-controlled execution;
- continuity from enquiry through post-trip.

**Sources:** [W01]–[W08]

### 8.2 Group and multi-day travel operating systems

**Examples:** WeTravel, SquadTrip, TrovaTrip.

#### Strong capabilities

- Public trip storefronts.
- Registration and traveler information.
- Packages, add-ons, promo codes, and legal terms.
- Deposits, installments, automatic billing, and multi-currency checkout.
- Traveler rosters, manifests, documents, and communication.
- Supplier payouts and supplier verification.
- Controlled cards.
- Creator or host-led travel.
- Marketplace orchestration among host, traveler, and operator.

#### Waypoint implication

A group-operator claim is not credible until commerce, roster, document, payout, and field-operation loops are complete. The opportunity is not to reproduce every storefront feature first. It is to connect those commerce and attendee flows to superior suitability, supplier intelligence, operations, and disruption handling.

**Sources:** [W09]–[W13]

### 8.3 Tour operator and DMC systems

**Examples:** Lemax, Tourwriter, Tourplan.

#### Strong capabilities

- Supplier and product databases.
- Contracted and dynamic rates.
- Complex rate conditions and multi-currency.
- Automatic pricing.
- Quoting and booking.
- Supplier communication.
- Operations and manifests.
- Accounting, settlements, and profitability.
- APIs and supplier connectivity.

#### Waypoint implication

Rate-sheet upload is only an entry point. Long-term commercial truth requires contract, product, inventory, offer, order, fulfillment, and finance models. Waypoint's advantage could be better intake, decisioning, explainability, modern UX, and agentic operations, but only if the operational core is real.

**Sources:** [W14]–[W17]

### 8.4 Corporate travel and Travel-as-a-Service

**Examples:** Navan, SAP Concur, Spotnana, Amex GBT.

#### Strong capabilities

- Policy configuration and booking-time enforcement.
- Approval and exception workflows.
- Global content and self-service.
- Traveler and agent on one platform.
- Group and event travel.
- Duty of care, traveler location, alerts, and support.
- Disruption servicing.
- Expense and reconciliation.
- Open, embedded, and white-label platforms.

#### Waypoint implication

Do not attempt a complete travel-and-expense replacement. The credible corporate adjacency is complex offsite, group, policy, delegated-arranger, and disruption orchestration integrated with existing enterprise systems.

**Sources:** [W18]–[W22]

### 8.5 Event and case-management systems

**Examples:** Cvent and ServiceNow.

#### Transferable strengths

- Registration, housing, room blocks, sub-blocks, roommates, transfers, and attendee communication.
- Case types, case lines, playbooks, SLAs, assignments, approvals, escalations, major incidents, and projects.
- Independent progress of related issues under one parent case.
- Customer-visible and operator-visible workflows.
- Matching, routing, knowledge, and automation.

#### Waypoint implication

A trip should be modeled as a parent case or project with independent but connected lines for travelers, orders, suppliers, documents, payments, approvals, and incidents.

**Sources:** [W23]–[W26]

### 8.6 Consumer and B2B AI travel

**Examples:** Mindtrip, Expedia, Booking.com, Google.

#### Direction of travel

- Conversational planning.
- Social inspiration ingestion.
- Natural-language search.
- Maps, reviews, images, and interactive itinerary workspaces.
- Comparison and confidence tools.
- AI-ready B2B components.
- Brand and DMO-controlled authoritative content.
- Direct booking and partner integration.

#### Waypoint implication

Consumer discovery is becoming platform infrastructure. Waypoint should not fight the largest consumer platforms on generic inspiration. It should make agency expertise, supply, policy, service, and execution accessible through current and future interfaces.

**Sources:** [W45]–[W51]

### 8.7 Airline retailing, distribution, and settlement

**Examples and standards:** IATA NDC, ONE Order, Business Reference Architecture, Travelport JSON APIs, accreditation, and BSP.

#### Direction of travel

- Richer, dynamic offers.
- Continuous pricing and ancillaries.
- Unified order records.
- Search, price, book, ticket, exchange, cancel, refund, and service APIs.
- Accredited distribution and settlement networks.

#### Waypoint implication

Waypoint should build a canonical Offer and Order layer and adapters, not duplicate distribution infrastructure. It must preserve manual and legacy records while remaining compatible with modern retailing.

**Sources:** [W28]–[W33]

### 8.8 Agentic infrastructure and payments

**Examples:** MCP, A2A, Visa Intelligent Commerce, Mastercard Agent Pay.

#### Direction of travel

- Standardized tool access.
- Agent capability discovery and collaboration.
- Explicit identity and authorization.
- Scoped spending controls.
- Tokenized credentials.
- Transparent agent-initiated transactions.

#### Waypoint implication

External agents should be treated as new channels and actors under the same policy, state, audit, and approval system. They must not bypass the canonical workflow.

**Sources:** [W52]–[W55]

---

## 9. Distribution-channel opportunity inventory

### 9.1 Product surfaces

- Operator web workbench.
- Traveler web portal and PWA.
- Native iOS and Android applications.
- Chrome and browser extension.
- Mobile share extension.
- Supplier portal.
- Corporate and event portal.
- Host-agency white-label portal.
- Field-operations mobile app.
- Public audit, calculator, and verification tools.
- Kiosk, QR, and assisted-sales capture.

### 9.2 Communication channels

- WhatsApp user-initiated capture.
- WhatsApp Business Cloud API.
- Gmail, Outlook, and IMAP.
- Email forwarding aliases.
- SMS.
- Voice calls and voice notes.
- Social DM copy, share, or paste.
- Web chat.
- Push notifications.
- Calendar events and reminders.

### 9.3 Embedded and partner distribution

- Embeddable website widgets.
- Link-in-bio and creator storefront.
- API and webhooks.
- MCP server.
- A2A agent interfaces.
- CRM and accounting marketplaces.
- GDS, NDC, CRS, bedbank, and supplier partners.
- Payment, banking, insurance, risk, identity, and visa partners.
- DMO and tourism-board partnerships.
- Host agencies and consortia.
- Franchise and branch networks.
- Corporate travel, event, and HR platforms.

### 9.4 GTM channels

- Travel trade groups and associations.
- Regional WhatsApp and Facebook groups.
- LinkedIn owner and operator outreach.
- Referral and affiliate programs.
- Supplier co-marketing.
- Host-agency partnerships.
- Destination specialist partnerships.
- Case studies and operational thought leadership.
- SEO and programmatic destination pages.
- Public risk, visa, accessibility, and feasibility tools.
- AI-search/GEO and machine-readable offer feeds.
- Conferences, trade fairs, workshops, and webinars.
- Migration offers from spreadsheets and incumbent tools.
- Managed onboarding using historical enquiries, clients, suppliers, and rate sheets.

### 9.5 Distribution questions

- Is the primary acquisition motion bottom-up advisor adoption, owner-led sales, host-agency distribution, supplier-led distribution, or embedded infrastructure?
- Which motion minimizes expensive implementation work?
- Which public tools create a qualified handoff rather than disintermediation?
- Which channels are reachable in India, North America, Europe, GCC, and other target markets?
- How much professional service is required to activate an agency?

---

## 10. Geography and market-specific opportunities

### 10.1 India

- UPI QR, intent, collect, and payment links.
- UPI AutoPay for installments where legally and commercially appropriate.
- Conversational and regional-language payment assistance.
- UPI One World guidance for foreign travelers in India.
- GST invoices, credit notes, debit notes, and e-invoice integration where applicable.
- DPDP-compliant notice, consent, access, correction, deletion, and grievance flows.
- Hindi and regional-language intake, translation, and transliteration.
- WhatsApp-first workflows.
- Domestic rail, bus, and local-mobility integration research.
- India-specific visa, passport, forex, TCS, TDS, and consumer-protection rules.
- Indian family, pilgrimage, wedding, education, medical, and group-travel modes.
- Offline and low-bandwidth traveler access.
- Cash, bank transfer, UPI, card, and corporate invoice reconciliation.
- Multi-branch agencies and informal sub-agent networks.
- GST-compliant supplier and customer master data.
- Regional operator and DMC marketplace.

### 10.2 European Union

- Package-versus-standalone-service classification.
- Updated cancellation, refund, voucher, complaint, and insolvency workflows.
- GDPR and regional processing controls.
- Multi-language, multi-currency, VAT, and consumer-rights support.
- Rail and multimodal travel.
- Sustainable travel reporting.
- Accessibility compliance.
- Cross-border seller and package-organizer role analysis.
- Stronger disclosure and complaint evidence.

### 10.3 United Kingdom

- Package Travel Regulations and ATOL role research.
- VAT and Tour Operators Margin Scheme research.
- Consumer and insolvency protection.
- Supplier and customer payment protection.
- UK host, homeworking, and consortium structures.

### 10.4 United States and Canada

- Seller-of-travel and state or provincial research.
- Host agency, sub-agency, independent contractor, and IATAN structures.
- Credit-card authorization, ACH, commission statements, and advisor payouts.
- Group, destination wedding, retreat, school, sports, and faith travel.
- Accessibility and consumer-disclosure requirements.
- Corporate guest travel and meeting programs.
- State tax and trust-account differences.

### 10.5 GCC

- Arabic localization.
- Family and luxury travel.
- Corporate and VVIP services.
- Visa, residency, and identity workflows.
- Sharia-sensitive payment and insurance research.
- High-touch concierge and privacy.
- Cross-border DMC and hotel contracting.

### 10.6 Southeast Asia, Africa, and Latin America

- DMC and inbound-operator orientation.
- Mobile and messaging-first operations.
- Local supplier networks.
- Multi-currency and cross-border payments.
- Connectivity and offline field operations.
- Local regulations, permits, safety, and community-host models.
- Cash and manual-supplier workflow support without losing auditability.

### 10.7 East Asia

- Chinese, Japanese, and Korean localization.
- Local payment, messaging, maps, and supplier ecosystems.
- Group, incentive, education, and corporate travel.
- Strong privacy, platform, and data-localization research.

### 10.8 Australia and New Zealand

- Adventure, inbound, educational, corporate, and long-haul group travel.
- Consumer-protection and supplier-insolvency controls.
- Remote-area risk and field operations.

### 10.9 Global enterprise

- SSO, SCIM, data residency, policy, cost center, delegated arranger, audit, API, and white label.
- Consistent global data model with local configuration.
- Partner-led booking, expense, risk, and payments rather than immediate full-stack replacement.
- Regional service, support, and incident-responsibility model.

**Sources:** [W34]–[W42]

---

## 11. Technology and industry-standard direction

### 11.1 Offer and Order architecture

IATA NDC enables richer airline offers across distribution channels. ONE Order aims to replace fragmented PNR, ticket, and EMD records with a single integrated order across fulfillment, delivery, and accounting.

#### Exploration implications

- Model offers separately from accepted orders.
- Preserve offer expiry and repricing.
- Treat every supplier line as fulfillable and serviceable.
- Separate source adapter from canonical order.
- Expect parallel legacy PNR, NDC Order, direct booking, and manual supplier records.
- Attach payment, delivery, change, cancel, and refund events to the order.
- Design for dynamic bundling and continuous pricing without hiding commercial logic.
- Maintain traveler, agency, supplier, and payment views of the same order.
- Allow one trip to contain many independently serviceable order lines.
- Reconcile external order state to internal operational truth.

**Sources:** [W28]–[W31]

### 11.2 AI tool and agent interoperability

MCP standardizes how AI applications access tools and data. A2A standardizes discovery and collaboration between independent agents.

#### Exploration implications

- Waypoint MCP server for safe operator and partner tools.
- A2A agents for research, supplier quote, booking, payment, risk, visa, and disruption.
- Capability cards and scoped credentials.
- Central policy and audit regardless of caller.
- Asynchronous and long-running task support.
- Conformance tests and observability.
- Treat external agent output as untrusted until verified.
- Bind agent action to trip, user, purpose, policy, and current state.
- Prevent an external agent from writing directly to canonical state without validation.

**Sources:** [W52] [W53]

### 11.3 Agentic commerce and payment authorization

Visa and Mastercard are building infrastructure for agent-initiated transactions with identity, permission, controls, transparency, and tokenized credentials.

#### Exploration implications

- Spending mandates and explicit purpose.
- Amount, supplier, category, trip, time, and retry limits.
- Consume-once or bounded authorization.
- Human approval for consequential action.
- Strong context binding.
- Payment-agent identity visible in audit.
- Fraud, replay, prompt injection, and steering defenses.
- Reversible or compensatable action design.
- User-visible action history and revocation.
- Partner-led payment processing until Waypoint's regulated role is clear.

**Sources:** [W54] [W55]

### 11.4 Verifiable travel-agent evaluation

Current research supports:

- Typed infeasibility reasons.
- Deterministic constraint checking.
- Multimodal evidence verification.
- Source freshness and contradiction handling.
- Persona-aware evaluation.
- Commission-steering audit.
- Long-horizon and tightly coupled scenario tests.
- Separation of plausible text quality from executable-plan quality.
- Evidence that an action or itinerary remains valid at execution time.

**Sources:** [A01]–[A06]

### 11.5 Architecture principles to preserve

- Canonical source of truth before automation.
- Zero shadow pipelines.
- Adapters around external systems.
- Event-driven state propagation with idempotency.
- Explicit pending state before uncertain extraction or external updates are applied.
- Human review attached to risk and evidence, not arbitrary page flows.
- Read, draft, simulate, approve, execute, and reconcile as distinct capabilities.
- API and UI as views over the same domain model.
- Historical facts and effective-date rules.
- Testable policies and deterministic validators.
- Every important action produces evidence.

---
## 12. Data, memory, and moat strategy

### 12.1 Data that should remain private by default

- Customer lists and relationship history.
- Supplier contracts and negotiated rates.
- Margin, markup, and pricing strategy.
- Advisor performance details.
- Sensitive traveler documents and identity.
- Proprietary destination playbooks.
- Private communications.
- Corporate policy and traveler location.
- Agent prompts, policies, and internal commercial reasoning.
- Supplier banking and tax data.
- Private complaints and dispute evidence.
- Individual traveler health, accessibility, and vulnerability data.
- Payment credentials and authorization mandates.

### 12.2 Data that may support shared intelligence with strong controls

- Public visa and documentation rules.
- Destination and route facts.
- Accessibility and suitability evidence.
- Aggregated supplier incident patterns.
- Budget feasibility baselines.
- Weather and disruption patterns.
- Non-proprietary service-quality signals.
- Anonymized operational benchmarks.
- Public regulatory and consumer-rights information.
- Aggregated processing-time and failure patterns.
- Public property and activity attributes with source evidence.
- Anonymized route, seasonality, and capacity patterns where legally and competitively acceptable.

### 12.3 Potential moats

1. **Canonical operational data**, not disconnected notes.
2. **Agency-specific relationship and supplier memory.**
3. **Constraint and policy graph with evidence and outcomes.**
4. **Human correction and override history.**
5. **End-to-end lifecycle feedback from enquiry through post-trip.**
6. **Operational reliability and recovery data.**
7. **Privacy-preserving shared risk and feasibility intelligence.**
8. **Integration and agent ecosystem.**
9. **Trusted brand built on transparent, controlled automation.**
10. **Migration and workflow depth that embeds Waypoint in daily agency operations.**
11. **Supplier contract and performance data accumulated under each agency's control.**
12. **Decision and execution traces that improve deterministic policies and evaluations.**

### 12.4 Anti-moats

- Generic generated itinerary text.
- Undifferentiated chat UI.
- Model choice without proprietary workflow data.
- Large unverified document corpus.
- Number of speculative agents.
- Number of routes without complete user journeys.
- Features that can be copied without data, process, integration, or distribution advantage.
- A marketplace with no verified supply or demand quality.
- White label without durable underlying workflow value.
- Proprietary formats that trap customers but do not improve outcomes.

### 12.5 Data product candidates

These require strict legal, privacy, sample-size, and competitive review:

- Destination feasibility index.
- Accessibility evidence index.
- Supplier reliability and incident trends.
- Visa and documentation rule graph.
- Travel disruption and recovery benchmark.
- Agency operational benchmark.
- Proposal conversion benchmark.
- Rate freshness and market range signals.
- Trip complexity score.
- Traveler readiness score.
- Supplier response and confirmation benchmark.
- Commission recovery benchmark.
- Public itinerary-audit API.

### 12.6 Data-governance requirements

- Clear data owner and purpose.
- Source, freshness, confidence, and effective date.
- Tenant and field-level access.
- Consent and lawful basis where applicable.
- Retention and deletion rules.
- Provenance and correction.
- Minimum cohort and anonymization threshold for aggregation.
- Explicit prohibited-use list.
- No silent training on customer data.
- Separation between simulation, benchmark, and production data.
- Export and portability.
- Data-quality monitoring.
- Audit of model and agent access.

**Source:** [R10]

---

## 13. Business-model and monetization idea bank

### 13.1 Core SaaS models

- Per-seat SaaS.
- Per-active-trip SaaS.
- Per-enquiry or per-proposal usage.
- Agency tier based on volume and capabilities.
- Hybrid base subscription plus usage.
- Branch or legal-entity pricing.
- Host-agency or consortium licensing.
- White-label platform licensing.

### 13.2 Usage and infrastructure models

- AI and document-extraction usage.
- API metering.
- Embedded intake, audit, proposal, or traveler-portal pricing.
- Integration connector pricing.
- Premium data, destination, or supplier intelligence.
- Storage and document vault tiers.
- Advanced observability, audit, and compliance tiers.
- Dedicated regional deployment.

### 13.3 Transaction and commerce models

- Payment revenue share.
- Supplier payout revenue share.
- Planning-fee and deposit infrastructure.
- Commission reconciliation and recovery fee.
- Referral and lead fee.
- Marketplace take rate.
- Creator, host, or affiliate revenue share.
- Supplier promoted placement only with strict transparency and no hidden steering.
- Booking or service fee.
- FX or payment-partner revenue share where legally and ethically acceptable.

### 13.4 Service models

- Managed onboarding and data migration.
- Supplier contract and rate loading.
- Custom integrations.
- Workflow and policy implementation.
- Agency operations transformation.
- Managed human concierge through partners.
- Incident support service.
- Training and certification.
- Enterprise support and SLA.
- Data cleanup and CRM consolidation.

### 13.5 Ecosystem models

- Supplier portal subscription.
- Partner marketplace membership.
- Expert marketplace commission.
- DMO and destination-intelligence licensing.
- Host-agency shared-service revenue.
- API or agent capability marketplace.
- Certified integration program.
- Anonymized benchmark subscription using only permitted data.

### 13.6 Monetization decision tests

- Who pays?
- What measurable value do they receive?
- What variable drives Waypoint's cost?
- What variable correlates with customer value?
- Does pricing punish adoption or collaboration?
- Does the model create a regulated money-movement role?
- Does it bias recommendations?
- Can a partner perform the regulated layer?
- Is gross margin acceptable after AI, support, integration, payment, and operational costs?
- Does the model support the primary ICP before enterprise custom work?
- Does the model create a conflict between traveler fit and Waypoint revenue?
- Can the customer predict and control cost?
- Does the model scale without extensive manual onboarding or support?

---

## 14. Portfolio classification: what belongs where

### 14.1 Current product truth

Use only for features verified against current code, tests, and usable flows. Required evidence:

- code path;
- API or UI surface;
- data model;
- relevant tests;
- real end-to-end behavior;
- failure behavior;
- current verification date.

### 14.2 Launch and retention candidates

Potential examples, not yet approved sequencing:

- Reliable omnichannel capture.
- State trust and provenance.
- Cross-trip client memory.
- Supplier and rate ingestion.
- Proposal conversion.
- Team assignment and review.
- Booking readiness.
- Document collection.
- Commission and margin visibility.
- Core observability and security.

### 14.3 Competitive parity backlog

- CRM depth.
- Integrated email.
- Forms.
- Proposal editing and mobile itinerary.
- Payments and invoices.
- Commission tracking.
- Reporting.
- Group booking page.
- Basic workflows.
- Website and lead capture.
- Calendar and task automation.

Parity should be obtained through focused implementation, integration, or deliberate exclusion. It should not consume the entire product thesis.

### 14.4 Strategic options

- DMC supplier mode.
- Multi-day group operator mode.
- Host-agency white label.
- Creator host mode.
- Corporate offsite mode.
- Embedded decision and audit APIs.
- Agent-ready travel infrastructure.
- Partner and supplier ecosystem.
- Event and housing management mode.
- India-first payments and compliance package.

### 14.5 Research queue

- Primary ICP evidence.
- Supplier category and contract complexity.
- Payment and legal role.
- Traveler self-service burden reduction.
- Autonomy thresholds.
- Data-sharing willingness.
- Channel stability.
- Regulatory requirements by market.
- Unit economics.
- Migration cost.
- Support and service model.
- Partner accessibility and commercial terms.

### 14.6 Experiment queue

Examples:

- Ten real enquiry imports across channels.
- Five rate sheets from different suppliers.
- Proposal trust-explanation A/B test.
- Cross-trip memory recall evaluation.
- Human versus deterministic suitability review.
- Supplier quote and confirmation parser.
- Group document-collection pilot.
- Commission statement reconciliation.
- Disruption impact simulation.
- AI-agent shadow mode with no execution.
- External-agent MCP or A2A sandbox.
- One host-agency workflow pilot.
- One DMC contract and booking pilot.
- One event housing and traveler-registration pilot.
- One UPI payment-link and reconciliation pilot.
- One end-to-end trip from enquiry to post-trip using real artifacts.

### 14.7 Idea bank

Everything worth preserving but lacking evidence, dependency resolution, or a current buyer. Idea-bank entries must not receive delivery dates.

### 14.8 Frontier Lab

No dates, launch dependency, or implied commitment. Frontier work should be justified by:

- learning value;
- reusable technical progress;
- research partnership;
- data or benchmark contribution;
- brand value;
- grant, sponsor, or customer-funded exploration.

### 14.9 Parked, rejected, and superseded

Every parked decision should record:

- why it was considered;
- why it was not selected;
- what evidence would reopen it;
- what existing work it supersedes;
- whether any code or data must be preserved;
- whether it creates a future migration concern.

### 14.10 Promotion gates

An item moves from idea or research to candidate roadmap only when:

1. A real persona and frequent pain are identified.
2. Current workflow and workaround are observed.
3. Desired outcome and metric are defined.
4. Dependencies and source of truth are known.
5. Legal, data, security, and operational roles are understood.
6. Build-versus-buy-versus-integrate options are compared.
7. A bounded validation test exists.
8. It strengthens the platform model.
9. It has clear kill or park criteria.

---

## 15. Candidate execution sequence, subject to confirmation

This section is the only part resembling a roadmap. It is deliberately much smaller than the opportunity inventory.

### Gate 0: Truth and launch integrity

- Build the canonical feature registry.
- Verify every current feature claim.
- Map complete user journeys.
- Reconcile stale and contradictory documents.
- Instrument usage and outcome metrics.
- Close deployment, security, backup, observability, and support gaps.
- Select one primary ICP and activation loop.
- Define the exact operational and legal role Waypoint assumes.
- Identify functionality that appears in routes but lacks a complete UI or real integration.
- Separate simulations, fixtures, and production evidence.

### Gate 1: Habitual operator workflow

- Native channel capture.
- Draft and canonical-state trust.
- Field provenance and correction.
- Follow-up and assignment.
- Cross-trip relationship memory.
- Reliable, editable traveler-safe output.
- Risk-based review and owner visibility.
- Search and retrieval over customer, trip, supplier, and agency knowledge.
- Fast correction without losing source evidence.

### Gate 2: Commercial truth

- Supplier and rate ingestion.
- Contract and product model.
- Margin and commission visibility.
- Quote versions.
- Proposal acceptance and deposit or fee.
- Supplier response and confirmation tracking.
- Cost and availability confidence.
- Financial approval policy.

### Gate 3: Lead-to-fulfillment

- Traveler booking data and document collection.
- Booking tasks and readiness.
- Confirmation and order state.
- Payments, invoices, commission reconciliation, and supplier payouts through appropriate partners.
- Traveler portal.
- Field operations.
- Disruption and recovery.
- Post-trip feedback and memory.

### Gate 4: Adjacent modes

Recommended investigation order, not automatic build:

1. DMC and supplier.
2. Multi-day group operator.
3. Host agency and white label.
4. Creator group host.
5. Corporate EA and offsite.
6. MICE, wedding, retreat, education, sports, and faith.

### Gate 5: Platform and ecosystem

- Public API and webhooks.
- Embedded products.
- Integration marketplace.
- Supplier and partner network.
- MCP and A2A interfaces.
- Privacy-preserving shared intelligence.
- Agentic payment and fulfillment only after safety evidence.
- Regional and enterprise deployment options.

### Gate 6: Frontier Lab

Research only.

### Candidate primary ICP default

**Mid-market outbound and specialist agencies with roughly 4–15 seats.**

Why:

- Daily enquiry and coordination pain.
- Team, review, and institutional-memory need.
- Enough volume to pay for workflow compression.
- Less dependent than very large agencies on immediate full GDS and enterprise replacement.
- Strong reuse of current code and documented product thesis.

This remains a hypothesis until supported by actual interviews, observed workflows, and willingness-to-pay evidence.

---

## 16. Metrics and evidence

### 16.1 Acquisition

- Qualified lead rate.
- Capture completion.
- Cost per qualified agency.
- Public-tool to agency conversion.
- Partner and referral conversion.
- Lead-source profitability.
- Time to first human response.
- Planning-fee or deposit conversion.

### 16.2 Activation

- Time to first imported enquiry.
- Time to first structured case.
- Time to first useful follow-up.
- Time to first sent proposal.
- Percentage reaching first value without support.
- Percentage using a real enquiry rather than sample data.
- Number of external tools required to complete the first workflow.

### 16.3 Habit and retention

- Percentage of real enquiries captured.
- Enquiries processed per active advisor.
- Weekly active advisors.
- Work completed outside Waypoint.
- 30, 90, and 180-day agency retention.
- Seat retention.
- Active workflows per agency.
- Expansion revenue.
- Share of trip lifecycle managed in Waypoint.
- Time saved only where measured from observed workflow.

### 16.4 Quality and trust

- Extraction correction rate.
- Missing-constraint recall.
- Suitability precision.
- Proposal human-edit distance.
- Confirmation mismatch rate.
- Document error rate.
- Override frequency.
- False-positive safety blocks.
- Evidence and provenance coverage.
- State-reconciliation failures.
- Human confidence and willingness to rely on state.

### 16.5 Commercial

- Proposal turnaround and conversion.
- Average trip contribution margin.
- Margin leakage prevented.
- Planning-fee or deposit conversion.
- Commission recovery.
- Revenue per advisor and agency.
- Supplier response and confirmation time.
- Quote accuracy.
- Expected versus actual profit.
- Payment collection and refund cycle time.

### 16.6 Operations

- Booking-readiness time.
- Confirmation completion.
- Document completion.
- Disruption detection and recovery.
- Traveler support volume.
- Human intervention rate.
- SLA adherence.
- Field-service completion and incidents.
- Expired hold and missed-deadline rate.
- Rework and duplicate-data entry.

### 16.7 AI and automation

- Cost and latency per task.
- Deterministic pass rate.
- Human correction.
- Tool-call success.
- Replay consistency.
- Unsafe or unauthorized action rate.
- Shadow-mode recommendation acceptance.
- Autonomy earned by workflow.
- Stale-data action prevention.
- Action rollback or compensation success.
- Source-verification rate.
- Commercial-bias and steering test results.

### 16.8 Platform

- API reliability.
- Webhook delivery and replay.
- Integration freshness.
- Tenant-isolation verification.
- Backup restore success.
- Incident recovery time.
- Data export completeness.
- Security-control coverage.
- Partner activation time.

### 16.9 Evidence hierarchy

1. Production outcome from a real workflow.
2. Controlled pilot with real users and artifacts.
3. Observed workflow research.
4. Realistic end-to-end test.
5. Deterministic benchmark.
6. Synthetic scenario.
7. Expert opinion.
8. Documentation claim.
9. Route or component existence.
10. Speculative idea.

No lower evidence tier should be presented as a higher one.

---

## 17. Explicit anti-roadmap and “not now” list

- Generic consumer trip-planning chatbot as the primary product.
- Building a GDS from scratch.
- Full enterprise travel-and-expense replacement.
- Full merchant-of-record or regulated payment role without a deliberate legal and economic decision.
- Fully autonomous booking, refund, rebooking, or payment without verified data and authorization.
- Separate architecture for every persona or vertical.
- Shared intelligence using customer lists, negotiated rates, margins, or proprietary supplier relationships.
- 3D, AR, magazines, biometrics, and frontier visuals ahead of operational completion.
- Broad marketplace before standalone product value and quality controls.
- Unlimited workflow configurability before repeated real needs exist.
- Claims of duty of care, medical safety, legal compliance, or guaranteed savings beyond actual evidence and contractual responsibility.
- Treating simulated Month 6 metrics as real performance evidence.
- Treating all scenario documents as implementation commitments.
- Counting routes or agents as product completeness.
- Rebuilding mature accounting, expense, risk, payment, or identity systems without a specific strategic reason.
- Exposing internal decision logic or supplier economics to travelers by default.
- Automating outbound messaging through unstable or non-compliant channel workarounds.
- Building network effects before earning standalone workflow adoption.
- Retaining sensitive data merely because it may be useful later.
- Inferring health, disability, religion, income, or other sensitive traits from behavior or content.
- Letting an LLM determine legal or safety compliance without deterministic checks and qualified review.
- Creating artificial urgency or misleading price locks.
- Supplier placement based on hidden commercial incentives.
- Public review or blacklist systems without verification, appeal, moderation, and legal review.
- Enterprise customization that forks the core product.
- Creating another roadmap document without a maintained registry and supersession model.

---

## 18. External research and validation program

### 18.1 Customer discovery

Interview and observe:

- Solo advisors.
- Owners of 4–15 seat outbound agencies.
- Junior advisors.
- Operations and ticketing staff.
- DMC sales and operations.
- Supplier contracting staff.
- Group organizers.
- Finance and commission administrators.
- Travelers and primary family organizers.
- Corporate EAs.
- Host-agency operators.
- Field guides, drivers, and coordinators.
- Visa and documentation specialists.
- Support and disruption teams.

For each workflow capture:

- Trigger.
- Inputs and channels.
- Current tools.
- Re-entry and copy/paste.
- Decision points.
- Errors and consequences.
- Time and frequency.
- Workarounds.
- Trust boundaries.
- Willingness to pay.
- Required integration.
- Evidence needed to automate.
- What must remain human.
- Who owns the outcome.
- Who pays for failure.
- What creates a legally binding commitment.

### 18.2 Market validation

- Competitor teardown by complete journey, not feature checklist.
- Pricing and packaging comparison.
- Buyer and distribution mapping.
- Regulatory-role analysis.
- Integration and supplier-access feasibility.
- Payment and support unit economics.
- Market-specific workflow tests.
- Migration and onboarding burden.
- Partner economics.
- Churn and replacement risk.
- Customer interview falsification: actively search for reasons the thesis is wrong.

### 18.3 Technical validation

- End-to-end route and UI verification.
- Data-contract and state-machine audit.
- Real supplier artifacts.
- Realistic failure and stale-data tests.
- Deterministic evaluator.
- Multimodal retrieval benchmark.
- Concurrency and idempotency.
- Security and authorization.
- Reversibility and compensation.
- Offline and low-bandwidth operation.
- Integration contract tests.
- Payment and document threat models.
- Model and prompt version replay.
- Production-like observability.
- Restore from backup.
- Tenant-isolation tests.

### 18.4 Proposed evidence-producing experiments

1. **Native enquiry capture**  
   Import ten real enquiry threads from WhatsApp, email, voice, and screenshots. Measure time, corrections, and trust.

2. **Supplier rate intelligence**  
   Process five real rate sheets from hotels, DMCs, transfers, and activities. Measure mapping, rule coverage, and human correction.

3. **Relationship memory**  
   Reconstruct five repeat-client histories and test whether the system surfaces the right facts without inventing preferences.

4. **Constraint evaluator**  
   Compare deterministic and human review on real family, senior, accessibility, visa, budget, and connection scenarios.

5. **Proposal trust**  
   Compare a simple advisor recommendation with evidence-heavy and trade-off views. Measure understanding and conversion intent.

6. **Group collection**  
   Run a small real group through registration, documents, payments, rooming, and updates.

7. **Commission reconciliation**  
   Parse one real statement and match it to bookings, advisors, and expected amounts.

8. **Disruption simulation**  
   Simulate a delayed arrival affecting transfer, hotel, meeting, and group schedule. Require approval before any action.

9. **Agent shadow mode**  
   Let agents recommend but never execute. Compare recommendations with human decisions and outcomes.

10. **External-agent sandbox**  
    Expose a minimal MCP or A2A interface with read and simulate permissions only.

11. **End-to-end operating loop**  
    Take one real trip from enquiry through post-trip with all artifacts and measure work outside Waypoint.

12. **ICP falsification**  
    Test the same workflow with solo, 4–15 seat, DMC, group, creator, and corporate users. Identify who receives the most value with the lowest missing-infrastructure burden.

---
## 19. Canonical registry schema for future maintenance

Every future item should use a structured record rather than disappearing into prose.

```yaml
id:
canonical_name:
aliases: []
portfolio:
  - current_truth
  - explicit_intent
  - competitive_parity
  - strategic_option
  - research
  - experiment
  - idea_bank
  - frontier
  - parked
source_class:
  - code
  - documentation
  - web
  - inference
  - speculation
evidence:
  code_paths: []
  test_paths: []
  ui_paths: []
  api_paths: []
  doc_paths: []
  web_sources: []
status:
  implementation:
  usability:
  integration:
  production_evidence:
  verification_date:
personas: []
pain_points: []
jobs_to_be_done: []
primary_use_case:
secondary_use_cases: []
horizontal_primitive:
verticals: []
markets: []
distribution_channels: []
competitor_context:
business_outcome:
user_outcome:
success_metrics: []
dependencies: []
data_requirements: []
integration_requirements: []
security_privacy_compliance:
legal_operational_role:
autonomy_level:
human_review:
reversibility:
source_of_truth:
estimated_build_cost:
estimated_operating_cost:
operational_risk:
legal_risk:
data_risk:
confidence:
decision:
  build
  validate
  research
  park
  reject
  frontier
reopen_or_kill_criteria:
owner:
last_reviewed:
supersedes: []
superseded_by:
notes:
```

### 19.1 Suggested identifier families

- `ACQ-*`: acquisition and distribution.
- `INT-*`: intake and extraction.
- `CRM-*`: identity and relationship memory.
- `CASE-*`: trip case and workflow.
- `DEC-*`: suitability, policy, and decision.
- `DEST-*`: destination knowledge and content.
- `SUP-*`: supplier, contract, and inventory.
- `REV-*`: pricing, margin, and revenue.
- `PROP-*`: proposal and conversion.
- `ORD-*`: booking, order, and fulfillment.
- `DOC-*`: documents, visa, and identity.
- `FIN-*`: payment, accounting, commission, settlement.
- `TRV-*`: traveler and group experience.
- `COM-*`: communication.
- `OPS-*`: disruption, concierge, and operations.
- `TEAM-*`: workforce and governance.
- `ANL-*`: analytics and evaluation.
- `PLAT-*`: platform and integrations.
- `SEC-*`: security, privacy, and compliance.
- `AGT-*`: agentic runtime and autonomy.
- `NET-*`: ecosystem and marketplace.
- `FRONT-*`: frontier research.

### 19.2 Status vocabulary

- Verified working.
- Working with limitations.
- Partial workflow.
- Surface exists, behavior unverified.
- Specified, not implemented.
- Research only.
- Experiment planned.
- Experiment completed.
- Deferred.
- Parked.
- Rejected.
- Superseded.
- Frontier.

### 19.3 Decision vocabulary

- **Build now:** approved and sequenced.
- **Validate now:** create evidence before commitment.
- **Research:** resolve a material unknown.
- **Integrate:** use an external system behind a canonical adapter.
- **Partner:** rely on a specialist provider and preserve the handoff.
- **Park:** valid but currently not worth attention.
- **Reject:** contradicts strategy, economics, trust, or safety.
- **Frontier:** research without product commitment.

---

## 20. Source register

The source register preserves traceability. External pages can change; each item should be rechecked before a consequential product or legal decision.

### 20.1 Repository sources

- **[R01] Waypoint OS README:** https://github.com/pranaysuyash/waypoint-os/blob/master/README.md
- **[R02] OpenAPI path snapshot:** https://github.com/pranaysuyash/waypoint-os/blob/master/tests/fixtures/server_openapi_paths_snapshot.json
- **[R03] Product vision and model:** https://github.com/pranaysuyash/waypoint-os/blob/master/Docs/PRODUCT_VISION_AND_MODEL.md
- **[R04] Persona and scenario index:** https://github.com/pranaysuyash/waypoint-os/blob/master/Docs/personas_scenarios/README.md
- **[R05] Product features index:** https://github.com/pranaysuyash/waypoint-os/blob/master/Docs/product_features/INDEX.md
- **[R06] Master phase roadmap:** https://github.com/pranaysuyash/waypoint-os/blob/master/Docs/MASTER_PHASE_ROADMAP.md
- **[R07] Month 6 product audit and simulation:** https://github.com/pranaysuyash/waypoint-os/blob/master/Docs/MONTH6_PRODUCT_AUDIT_AND_SIMULATION_2026-07-28.md
- **[R08] First-principles turnaround priority:** https://github.com/pranaysuyash/waypoint-os/blob/master/Docs/FIRST_PRINCIPLES_TURNAROUND_PRIORITY_2026-07-28.md
- **[R09] Missing frontend components analysis:** https://github.com/pranaysuyash/waypoint-os/blob/master/Docs/MISSING_FRONTEND_COMPONENTS_ANALYSIS_2026-04-18.md
- **[R10] GTM and data network effects:** https://github.com/pranaysuyash/waypoint-os/blob/master/Docs/GTM_AND_DATA_NETWORK_EFFECTS.md
- **[R11] Corporate EA and DMC supplier exploration:** https://github.com/pranaysuyash/waypoint-os/blob/master/Docs/exploration/CORPORATE_EA_AND_DMC_SUPPLIER_PARADIGM_2026-08-03.md
- **[R12] Creator and influencer operations exploration:** https://github.com/pranaysuyash/waypoint-os/blob/master/Docs/exploration/TRAVEL_CREATOR_INFLUENCER_PARADIGM_2026-08-03.md
- **[R13] Frontier expansion V11:** https://github.com/pranaysuyash/waypoint-os/blob/master/Docs/research/RESEARCH_ROADMAP_FRONTIER_EXPANSION_V11.md

### 20.2 Advisor CRM, itinerary, group, and operator products

- **[W01] TravelJoy:** https://traveljoy.com/
- **[W02] TravelJoy Smart Proposals:** https://help.traveljoy.com/hc/en-us/articles/4407244320532-Create-an-Itinerary-or-Smart-proposal
- **[W03] Travefy CRM suite:** https://travefy.com/blog-post/travefy-launches-all-new-crm-suite
- **[W04] Travefy professional platform:** https://travefy.com/go-professional
- **[W05] Tern Q1 2026 launches:** https://help.tern.travel/en/articles/14141693-what-we-launched-at-the-q1-2026-webinar
- **[W06] Tern June 2026 launches:** https://help.tern.travel/en/articles/15373196-what-we-launched-at-the-june-2026-webinar
- **[W07] Tern reporting:** https://help.tern.travel/en/articles/13009064-reporting-overview
- **[W08] Tern commission reconciliation:** https://help.tern.travel/en/articles/12904145-commission-reconciliation-overview
- **[W09] WeTravel operating system:** https://product.wetravel.com/about-us
- **[W10] WeTravel cards and supplier payments:** https://product.wetravel.com/wetravel-card/global-payments-expense-card
- **[W11] WeTravel supplier list:** https://help.wetravel.com/en/articles/3456180-supplier-list
- **[W12] SquadTrip feature list:** https://help.squadtrip.com/en/articles/12840342-what-squadtrip-offers-full-feature-list
- **[W13] TrovaTrip marketplace model:** https://help.trovatrip.com/en/articles/9160801-trovatrip-travel-marketplace
- **[W14] Lemax:** https://lemax.net/
- **[W15] Tourwriter:** https://www.tourwriter.com/software-pricing-plans/
- **[W16] Tourplan NX:** https://help.tourplan.com/products/tourplan-nx
- **[W17] Tourplan supplier connectivity:** https://help.tourplan.com/products/supplier-connectivity

### 20.3 Corporate travel, events, case management, and hospitality

- **[W18] Navan business travel:** https://navan.com/product/business-travel
- **[W19] SAP Concur travel policy:** https://help.sap.com/docs/concur-travel/concur-travel-professional-edition-administration-guides/access-travel-policy-administration
- **[W20] Spotnana platform:** https://www.spotnana.com/platform/
- **[W21] Amex GBT duty of care:** https://www.amexglobalbusinesstravel.com/business-travel/select/duty-of-care/
- **[W22] Amex GBT proactive traveler care:** https://www.amexglobalbusinesstravel.com/why-amex-gbt/proactive-traveler-care/
- **[W23] Cvent housing and travel management:** https://www.cvent.com/en/event-management-software/housing-travel-management
- **[W24] Cvent enterprise event planning:** https://www.cvent.com/in/enterprise/event-planner
- **[W25] ServiceNow case management:** https://www.servicenow.com/docs/r/zurich/customer-service-management/csm-case-management.html
- **[W26] ServiceNow case lines:** https://www.servicenow.com/docs/r/customer-service-management/csm-case-mgmt-case-lines.html
- **[W27] Salesforce hospitality CRM:** https://www.salesforce.com/in/travel-hospitality-transportation/hospitality/

### 20.4 Industry standards, distribution, accreditation, and settlement

- **[W28] IATA NDC:** https://www.iata.org/en/programs/airline-distribution/retailing/ndc
- **[W29] IATA ONE Order:** https://www.iata.org/en/programs/airline-distribution/retailing/one-order/
- **[W30] IATA Business Reference Architecture:** https://www.iata.org/en/programs/airline-distribution/retailing/business-reference-architecture/
- **[W31] Travelport JSON APIs:** https://legacy.developer.travelport.com/restful-json-api
- **[W32] IATA travel-agent accreditation:** https://www.iata.org/en/services/travel-agency-program/accreditation-travel/
- **[W33] IATA BSP:** https://www.iata.org/en/services/finance/bsp/

### 20.5 Regulation, privacy, payments, and India-specific sources

- **[W34] EU Package Travel Directive:** https://commission.europa.eu/law/law-topic/consumer-protection-law/travel-and-timeshare-law/package-travel-directive_en
- **[W35] EU 2026 package-travel amendments:** https://commission.europa.eu/news-and-media/news/package-travel-stronger-rights-travellers-and-simpler-rules-travel-industry-2026-05-28_en
- **[W36] India DPDP Rules 2025:** https://www.meity.gov.in/documents/act-and-policies/digital-personal-data-protection-rules-2025-gDOxUjMtQWa
- **[W37] PCI DSS:** https://www.pcisecuritystandards.org/standards/pci-dss/
- **[W38] NPCI UPI:** https://www.npci.org.in/product/upi/about-upi
- **[W39] NPCI UPI statistics:** https://www.npci.org.in/product/upi/product-statistics
- **[W40] NPCI Hello UPI:** https://www.npci.org.in/product/upi/hello-upi
- **[W41] NPCI UPI AutoPay:** https://www.npci.org.in/product/autopay
- **[W42] India GST e-invoice portal:** https://einvoice6.gst.gov.in/content/irp-for-e-invoicing/

### 20.6 Market and AI-travel direction

- **[W43] Phocuswright 2026 technology trends:** https://www.phocuswright.com/Travel-Research/Research-Updates/2026/Report-Preview-Phocuswrights-Travel-Innovation-and-Technology-Trends-2026
- **[W44] Phocuswright agentic-AI adoption:** https://www.phocuswright.com/Travel-Research/Research-Updates/2026/61-of-travel-business-surveyed-experimenting-with-or-scaling-agentic-ai
- **[W45] Mindtrip:** https://mindtrip.ai/about
- **[W46] Mindtrip for Business:** https://mindtrip.ai/business/how-it-works
- **[W47] Expedia Explore 2026 AI experiences:** https://ir.expediagroup.com/news-and-events/news/news-details/2026/Expedia-Group-Unveils-New-AI-Experiences-Expands-Travel-Ecosystem-and-Launches-Philanthropy-Program-at-Explore-2026/default.aspx
- **[W48] Expedia B2B AI toolkit:** https://ir.expediagroup.com/news-and-events/news/news-details/2026/Expedia-Group-B2B-Introduces-AI-Toolkit-and-Platform-for-the-Future-of-Travel-Distribution/default.aspx
- **[W49] Expedia Trip Matching:** https://www.expedia.com/newsroom/now-live-expedia-launches-industry-first-feature-that-turns-reels-on-instagram-into-bookable-travel-itineraries/
- **[W50] Google AI travel planning:** https://blog.google/products-and-platforms/products/search/agentic-plans-booking-travel-canvas-ai-mode/
- **[W51] Booking.com AI planning:** https://news.booking.com/bookingcom-enhances-travel-planning-with-new-ai-powered-features--for-easier-smarter-decisions/

### 20.7 Agent and agentic-commerce standards

- **[W52] Model Context Protocol:** https://modelcontextprotocol.io/docs/getting-started/intro
- **[W53] A2A protocol:** https://github.com/a2aproject/A2A
- **[W54] Visa Intelligent Commerce:** https://www.visa.com/en-us/solutions/intelligent-commerce
- **[W55] Mastercard Agent Pay:** https://www.mastercard.com/global/en/business/artificial-intelligence/mastercard-agent-pay.html

### 20.8 Research and benchmark sources

- **[A01] TREK benchmark:** https://arxiv.org/abs/2607.26977
- **[A02] VeriTrip benchmark:** https://arxiv.org/abs/2605.28683
- **[A03] WorldTravel benchmark:** https://arxiv.org/abs/2602.08367
- **[A04] TripTailor benchmark:** https://arxiv.org/abs/2508.01432
- **[A05] TravelPlanner benchmark:** https://arxiv.org/abs/2402.01622
- **[A06] TourMart commission-steering audit:** https://arxiv.org/abs/2605.10440

---

## 21. Current conclusions requiring confirmation

These are provisional strategic defaults, not irreversible decisions.

1. **Primary ICP candidate:** mid-market outbound and specialist agencies with roughly 4–15 seats.
2. **Primary positioning candidate:** Agency Operations and Revenue OS with constraint-aware decision and execution intelligence.
3. **Most important near-term product layers:** frictionless intake, state trust, relationship memory, supplier and rate intelligence, proposal conversion, booking readiness, team control, and measurable operational value.
4. **Most natural first adjacency:** DMC, supplier, and multi-day group operations.
5. **B2C role:** public audit, traveler experience, and qualified agency handoff, not generic consumer planning as the primary business.
6. **Autonomy posture:** guarded copilot by default, with autonomy earned by workflow-specific evidence.
7. **Commercial principle:** optimize traveler fit, operational fit, and commercial fit under transparent policy rather than one hidden objective.
8. **Data principle:** build for each agency using its own relationship and supplier intelligence; share only carefully governed non-proprietary intelligence.
9. **Architecture principle:** one canonical case, order, policy, and audit model across verticals.
10. **Exploration principle:** preserve all worthwhile ideas but promote only evidence-backed items into the active roadmap.

---

## 22. Next document actions after review

Once this inventory is reviewed:

1. Create a machine-readable registry from Section 19.
2. Map all existing repository documents and features to canonical IDs.
3. Verify each `[CODE]` claim against current `master`.
4. Mark duplicates, contradictions, superseded plans, and historical-only artifacts.
5. Add owners, confidence, dependencies, and verification dates.
6. Select a narrow active roadmap from the larger portfolio.
7. Preserve strategic options, research, ideas, and frontier work in their own queues.
8. Add customer evidence and experiment outcomes as they are collected.
9. Update the registry rather than creating another isolated roadmap.
10. Save the confirmed version into the repository only after explicit approval.

---

## 23. Closing principle

This document preserves the whole opportunity space. It must not be converted wholesale into tickets.

The operating model is:

> **Explore broadly. Preserve everything useful. Distinguish fact from intent and speculation. Decide narrowly. Build coherently. Earn autonomy through evidence.**
