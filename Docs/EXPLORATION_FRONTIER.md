# The Exploration Frontier

**Date**: Wednesday, April 22, 2026
**Purpose**: A raw, un-filtered repository for ideas, experiments, and "what if" scenarios. This document is a safe space for brainstorming before they are vetted for the Master Roadmap.

---

## 1. Raw Ideas & Experimental Concepts

- **[Architecture] BFF + Modular Monolith Topology**: Current system is neither a pure monolith nor microservices. It is a Next.js BFF plus FastAPI backend modular monolith, with future extraction candidates around workers, integrations, documents, analytics, and public traveler collection. See `Docs/exploration/ARCHITECTURE_TOPOLOGY_REVIEW_2026-05-11.md`.
- **[Concept] Agent-Role Swapping**: Allow operators to "swap" the persona of an agent dynamically (e.g., "Take your current plan and explain it to a budget-conscious traveler instead of the current luxury profile").
- **[Concept] Automatic 'Next-Action' Nudging**: AI detects when a trip has been idle in a stage for X hours and suggests an "Internal Note" to nudge the process forward.
- **[Concept] Visual State Replay**: Rather than just logs, create a "Video-Game Style Replay" button that iterates through the `TimelinePanel` steps at 0.5s intervals, allowing the operator to see the AI's "thought" progression visually.
- **[Concept & Engineering] KDD v0.1: Fuzzy Feature Vector Clustering (`HDBSCAN` / Gower Distance) & Automated Rule Promotion Loop**: Upgrade the `exact-match-v1` override clustering algorithm (`src/analytics/kdd/clustering.py`) to a density-based fuzzy distance metric over `(flag, action, destination, party_size, duration_days)`. Prevents high-value domain overrides from dropping into the noise floor and implements a closed-loop `POST /kdd/clusters/{id}/promote` endpoint to convert verified operator patterns into automated suitability policy overrides. See `Docs/audit/KDD_OVERRIDE_MINING_AND_FEEDBACK_LOOP_AUDIT_2026-07-13.md`.
- **[Intake / Vernacular AI] Hinglish Vernacular Extraction & GeoNames Gazetteer Collision Neutralization**: Discovery and architectural remediation of false positive colliders ("Hai", "Hum", "Khana") in 590k-city GeoNames gazetteers when processing mixed Hindi-English WhatsApp travel inquiries. Formalized Hindi ablative postpositional markers (`"<city> se"`), vernacular count nouns (`bade`, `bacche`, `infant`, `navjaat`), Hindi date range brackets (`"se ... tak"`), and senior citizen age ceiling guards (`<= 17`). Tested and verified in Sim #5 (`SIM-5-TIER2-INDIA-01`). See `Docs/sims/SIM5_TIER2_AGENT_AUDIT_2026-10-30.md`.

---

## 2. Status of Ideas

| Idea | State | Discovery/Next Step |
| :--- | :--- | :--- |
| **BFF + Modular Monolith Topology** | Explored | Adopt as current architecture label; next step is route/service modularization, persistence consolidation, and worker-boundary design. |
| **Agent-Role Swapping** | Raw | Analyze `SessionStrategy` requirements for persona-injection. |
| **Next-Action Nudging** | Raw | Feasibility study: can this be a trigger in the `Orchestrator`? |
| **Visual State Replay** | Experimental | Needs exploration of `PacketPanel` state rehydration (the "Time Travel" feature). |
| **Collaborative Agents** | Raw | Requires multi-agent orchestration infrastructure. |
| **KDD v0.1: Fuzzy Clustering & Rule Promotion** | Explored & Audited | Implement tenant isolation in `spine_api/routers/kdd.py` and benchmark agglomerative Gower clustering across historical overrides (`OverrideStore`). |
| **Hinglish Vernacular Intake & Gazetteer Hygiene** | Implemented & Verified | Tested in Sim #5 (`SIM-5-TIER2-INDIA-01`); remediated count nouns, Hindi postpositions, date brackets, and stopword sweeps in `src/intake/extractors.py`. Next: explore regional dialects (Gujarati / Marwari business idioms). |
| **Group Payment Collection (FND-0409)** | Implemented | Wired through the canonical `group_booking` door: remainder-exact split (`services/group_payments.py`), schedules with derived overdue/due_soon/upcoming statuses, observed-payment ledger (tracking-only, ADR-008), reminder drafts (`operator_manual` floor, DP-04b-gated dispatch), itemized share notes (Chloe JTBD). Operator surface: Payments page panel; traveler: `/g/[token]` portal. Next: owner decision on concierge-draft enqueue for reminders (DP-04b adjacency). |
| **Traveler-visible booking-change monitoring (FND-0410)** | Implemented | `routers/booking_changes.py` ledger (cancellation/overbook/schedule/rate, honest `operator_reported` source, D6 authority-precedence ready for DP-04a feeds), resolve-to-history mirrors FND-0405. Traveler exposure via public proposal payload (`booking_changes`, EXCLUDED from acceptance snapshot — changes never invalidate accepted revisions). Ops door: `BookingChangeReportSection` on trip ops page. Next: provider feeds supersede by source precedence (DP-04a). |

---

## 3. How to use this doc:
1. **Dumping**: When you have an idea, add a bullet point here immediately. Don't worry about whether it's "architecturally sound" or "roadmap-ready."
2. **Review**: Periodically (during our sessions), we will review this list. 
3. **Promotion**: If an idea proves valuable, we will flesh it out into a technical directive and move it to the `MASTER_PHASE_ROADMAP.md`.
4. **Pruning**: If an idea loses relevance, move it to the `Archive/` section or delete it.

*This doc is for your curiosity. Keep adding to it.*

### Workbench feasibility and message review

The [council replay](exploration/ITINERARY_CHECKS_INDUSTRY_COUNCIL_2026-11-24.md#when-one-itinerary-contains-several-commitments) reproduced a dropped rail and access concern when a hotel question was present. The [Workbench implementation and verification record](worklogs/2026-11-24-feasibility-rail-sql-verification.md#25-november-workbench-status-navigation) tracks header navigation, the open multi-commitment result, and persisted audit freshness.

The shared finalizer now collects the supported supplier families independently. It preserves the existing lead question and publishes other matches through the existing advisory list. The compound regression covers both clause orders and the hotel-free control. This verifies the shared packet in process. Real endpoint and browser replay, multiple bookings within a single family, durable per-booking resolution and practitioner validation remain open.

The 25 November browser replay used the updated finalizer against an isolated local PostgreSQL database. The same rail-first inquiry showed the hotel cutoff, rail pickup and step-free boarding questions on the public report and authenticated Workbench in Chrome at 1440 and 390 CSS pixels. Workbench still titles the combined inquiry “Hotel package” and labels the header action in the singular. Treat those as remaining presentation gaps. [Browser assertions and screenshots](evidence/itinerary-diversity-2026-11-24/compound-retained-browser-2026-11-25.json)

### Supplier messaging and availability

The [dedicated Waypoint integration chat](codex://threads/01a2111b-56b4-7ad0-91e0-03beb739d4a9) owns the official WhatsApp adapter, staff takeover, and source-linked supplier rate and calendar lookups for the local implementation. It picks up the source review below from [Review GTM wedge and design direction](codex://threads/01a1fe15-8bb8-7433-9b10-3ce956db2ba6), which continues to own checker and Workbench feasibility. The product recording and itinerary-check acceptance use a separate test agency. Account setup, external sending, spend, and practitioner recruitment remain with the owner.

| Existing path | Finding from the 25 November source review | Acceptance still needed |
| --- | --- | --- |
| [Inbound route](../spine_api/routers/messaging.py), [message store](../spine_api/services/message_store.py), [concierge handler](../spine_api/services/messaging_webhooks.py) | The route already reads provider message IDs and consults the agency message store. The handler also has an in-process idempotency registry. A pre-read followed by separate writes is insufficient evidence of exclusion across workers or crash recovery. | Concurrent duplicate delivery, restart between receipt and reply, and two different agencies using the same fixture ID should yield the correct tenant-scoped inbox item, conversation record and outbound attempt. |
| [Outbound adapter](../spine_api/services/message_dispatch.py), [action contract](../src/intake/action_contract.py) | The dispatch call accepts recipient, channel and content. It needs access to persisted conversation ownership to enforce a staff takeover when a previously queued automated reply reaches dispatch. | An advisor takes over after queueing. Restart the worker. The queued automated reply stays suppressed. Release and staff-initiated sends retain their distinct semantics. |
| [Supplier rate research](research/FRONTIER_2_MULTI_SUPPLIER_RATE_PARITY_AND_RETICKETING_2026-09-01.md), [supplier rate workflow](../frontend/docs/SUPPLIER_01_RATE_MANAGEMENT.md) | Supplier evidence can answer a price or availability question. A rate observation and a reservation are different actions in the existing action contract. | A lookup records supplier, exact service, effective date, timestamp, price basis, availability and expiry. Missing/stale/conflicting observations produce a supplier question. A lookup never issues a hold, booking or confirmation. |

The [earlier channel design](UX_WHATSAPP_INTEGRATION_STRATEGY.md) also covers manual handoff. Preserve it as a user-operated path. The first controlled external proof requires an owner-authorized test number, provider setup and delivery receipt.

The [local implementation and pilot handoff](worklogs/2026-11-25-whatsapp-supplier-local-integration.md) records the signed webhook, inbox takeover and approval, uncertain-delivery recovery, and source-linked supplier evidence. The remaining external inputs are a Meta test sender and consenting recipient, plus a buyer-owned rate source and calendar source.

The [local browser preview](worklogs/2026-11-25-whatsapp-supplier-local-integration.md#local-browser-preview) verified advisor takeover, simulated reply dispatch, correct lead party sizes, and the Suppliers lookup for both current and expired calendar evidence.

The [25 November follow-through](exploration/ITINERARY_CHECKS_INDUSTRY_COUNCIL_2026-11-24.md#compound-finding-party-and-place-role-follow-through) closes the singular header and single-supplier naming issues on the mixed case, records party-size scope, and traces operator sources through both interfaces. A screenshot review also exposed two place-role collisions. The 13-case practitioner packet is ready for independent review.

The [implementation and recording index](worklogs/2026-11-24-feasibility-rail-sql-verification.md#25-november-implemented-header-itinerary-cases-and-saved-draft-checks) supersedes the earlier header proposal and open multi-finding display items. The [public report and sample interaction review](exploration/GTM_WEDGE_UI_UX_DESIGN_REVIEW_2026-11-21.md#25-november-follow-through-on-report-states-samples-and-keyboard-access) covers advisory-only reports, real TXT upload, keyboard controls and the illustrative pacing chart. The remaining operator question is how advisors record decisions for each individual booking, especially two bookings of the same type. The practitioner packet includes a prompt to collect that evidence after the outreach hold is released.

### Traveler comprehension of the first result

The simulated advisor's review led to an implemented change in report order. The original Goa inquiry now leads with two findings. Its missing return date sits next to the edit action. The mixed supplier case leads with all three questions. The [council follow-through](exploration/ITINERARY_CHECKS_INDUSTRY_COUNCIL_2026-11-24.md#public-report-readback-after-the-simulated-advisor-review) contains the before and after states, browser receipts and the ten-second comprehension prompt for the held practitioner review.

The [saved edit recordings](worklogs/2026-11-24-feasibility-rail-sql-verification.md#saved-inquiry-reassessment-without-reloading) track the earlier count and freshness gaps through an actual inquiry revision. The [backend verification record](exploration/GTM_WEDGE_UI_UX_DESIGN_REVIEW_2026-11-21.md#25-november-backend-verification-of-the-workbench-status-checks) covers warm decision reuse, tenant isolation and the local messaging tests. Official WhatsApp delivery and supplier availability verification remain with the dedicated integration owner. The next product evidence is a physical-device replay and the independent practitioner review.

The [rendered accessibility findings](exploration/GTM_WEDGE_UI_UX_DESIGN_REVIEW_2026-11-21.md#rendered-accessibility-of-the-report-and-workbench-highlight) now include before and after measurements from the public report and authenticated Risk Review. Manual assistive-technology and real-device acceptance remain open.

The [practitioner reconciliation table](exploration/ITINERARY_PRACTITIONER_REVIEW_PACKET_2026-11-24.md#facilitator-reconciliation-into-waypoint-os) maps the case IDs to Waypoint intake, feasibility, evidence and review, with a closure test for each.

The [F01 changed-date replay](exploration/ITINERARY_CHECKS_INDUSTRY_COUNCIL_2026-11-24.md#f01-changed-fact-wording-control-25-november) links the shared pacing regression to both local endpoints and rendered desktop screens.

The [booking evidence attribution probe](exploration/ITINERARY_CHECKS_INDUSTRY_COUNCIL_2026-11-24.md#evidence-attribution-across-bookings-25-november) reproduces a hotel update changing a rail follow-up and supplies controls for per-booking resolution.

The [same-property booking trace](exploration/ITINERARY_CHECKS_INDUSTRY_COUNCIL_2026-11-24.md#two-reservations-at-the-same-property) reproduces the remaining gap and identifies the existing agency-scoped component key as the authenticated feasibility integration seam.

The [supplemental practitioner cases](exploration/ITINERARY_PRACTITIONER_REVIEW_PACKET_2026-11-24.md#supplemental-supplier-case-f03-s) now cover same-property ambiguity, matched supplier updates, and definite versus tentative Goa corrections. The facilitator notes link observed product behavior to each case.

The [release preflight](worklogs/2026-11-24-feasibility-rail-sql-verification.md#release-preflight-for-hosted-deployment) records the local changes absent from the current revision and the unresolved staging target and image provenance.

The [vehicle ferry cutoff case](exploration/ITINERARY_CHECKS_INDUSTRY_COUNCIL_2026-11-24.md#vehicle-ferry-cutoff-and-overnight-connection) adds a source-grounded operator deadline check and a reproduced gap in the shared supplier follow-up.

The [practitioner coverage audit](exploration/ITINERARY_PRACTITIONER_REVIEW_PACKET_2026-11-24.md#coverage-audit-for-the-facilitator) reconciles 40 historical paired cases and indexes the supplemental evidence and remaining reviews.

The [fresh standard matrix](exploration/ITINERARY_PRACTITIONER_REVIEW_PACKET_2026-11-24.md#fresh-replay-of-the-39-standard-variants) confirms cross-surface parity on the current local preview after the newer intake and supplier changes.

Practitioner interviews may use the synthetic packet before deployment. The hosted release preflight applies to a hosted pilot. Exploration, local verification, and feasibility improvements can continue while interviews and release work proceed.
