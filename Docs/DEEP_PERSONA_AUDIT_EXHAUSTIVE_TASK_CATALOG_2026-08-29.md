# Waypoint OS — Exhaustive Multi-Dimensional Task & Findings Catalog (11-Persona Deep Audit)

**System:** Waypoint OS (`pranaysuyash/travel_agency_agent`)  
**Date:** August 29, 2026  
**Governing Doctrines:** `OPERATING_DOCTRINE.md` (v8.0), `ARCHITECTURE_DOCTRINE.md`, `TESTING_DOCTRINE.md`, `SECURITY_PRIVACY_SAFETY_DOCTRINE.md`, `REVIEW_DOCTRINE.md`

---

# Persona 1: `PER-0700: Agentic Systems Architect`

### Deep Architectural & Codebase Audit
Interrogating [`src/agents/runtime.py`](file:///Users/pranay/Projects/travel_agency_agent/src/agents/runtime.py), [`src/agents/engine.py`](file:///Users/pranay/Projects/travel_agency_agent/src/agents/engine.py), and [`spine_api/routers/agent_runtime.py`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/routers/agent_runtime.py).

### Granular Task Inventory

1. **`AGT-01 [Lease Heartbeat Renewal]`**: Implement deterministic 15s background heartbeat coroutine tied to async event loop with exponential jitter to avoid thundering herd on central store.
2. **`AGT-02 [Worker Zombie Reclamation]`**: Periodic lease sweeper identifying leases expired by $>2 \times \text{TTL}$ (120s) and transitioning status from `RUNNING` to `INTERRUPTED_RECOVERABLE`.
3. **`AGT-03 [Idempotency Key Reservation]`**: Attach a unique `idempotency_key` (`trip_id:step_name:run_id`) to every agent action to prevent double-execution on lease failover.
4. **`AGT-04 [Step Checkpoint Serialization]`**: Serialize intermediate agent memory state into `ExecutionCheckpoint` dataclass after each tool invocation.
5. **`AGT-05 [Deterministic Step Resumption]`**: Implement `resume_from_checkpoint(checkpoint_id)` skipping already-executed side-effecting tools.
6. **`AGT-06 [Async Worker Cancellation Token]`**: Support cooperative cancellation tokens (`asyncio.Event`) allowing graceful shutdown during SIGTERM / rolling deployments.
7. **`AGT-07 [Prometheus Telemetry Instrumentation]`**: Add counters `spine_agent_lease_acquired_total`, `spine_agent_lease_timeouts_total`, and histogram `spine_agent_step_duration_seconds`.
8. **`AGT-08 [Tool Execution Sandboxing]`**: Enforce strict per-tool execution timeout budgets (e.g. 15s for supplier search, 5s for database reads).
9. **`AGT-09 [Dead-Letter Queue for Poison Runs]`**: Automatically quarantine runs that fail $\ge 3$ consecutive recovery attempts into `WorkStatus.FAILED_QUARANTINED`.
10. **`AGT-10 [Distributed Lock Backing Store Adapter]`**: Abstract lease storage behind `LeaseStoreBackend` interface supporting InMemory, SQLite, and PostgreSQL Row-Level Advisory Locks.
11. **`AGT-11 [Concurrency Throttling per Tenant]`**: Limit maximum concurrent agent runs per `agency_id` to prevent single-tenant CPU starvation.
12. **`AGT-12 [Agent Execution Graph Visualizer]`**: Generate Mermaid DAGs of agent step sequences and subagent message exchanges for operator debugging.

---

# Persona 2: `PER-0442: Travel Operating Systems Architect`

### Deep Architectural & Codebase Audit
Interrogating [`src/schemas/journey_graph.py`](file:///Users/pranay/Projects/travel_agency_agent/src/schemas/journey_graph.py), [`src/decision/`](file:///Users/pranay/Projects/travel_agency_agent/src/decision/), and [`spine_api/routers/concierge.py`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/routers/concierge.py).

### Granular Task Inventory

1. **`JRN-01 [Topological Sort & Cycle Detection]`**: Implement Kahn's algorithm / Tarjan's strongly connected components to validate DAG acyclicity and chronological sequence.
2. **`JRN-02 [Multi-Segment Rail & Ferry Node Types]`**: Add high-speed rail (`RAIL_TGV`, `RAIL_SHINKANSEN`, `RAIL_EUROSTAR`) and ferry nodes with embarkation buffer requirements.
3. **`JRN-03 [Transfer Cushion Variance Metric]`**: Compute normalized cushion variance: $\Delta t_{\text{cushion}} = (t_{\text{departure\_next}} - t_{\text{arrival\_prev}}) - \text{MCT}_{\text{airport}}$.
4. **`JRN-04 [Downstream Cascade Severity Scoring]`**: Classify ripple impact into `CRITICAL` (missed flight/cruise), `HIGH` (hotel checkin delay > 4h), `MEDIUM` (rescheduled activity), and `LOW` (minor buffer compression).
5. **`JRN-05 [Multi-Airport Co-Terminal Logic]`**: Model physical transfer transit time between co-terminals (e.g. LHR $\leftrightarrow$ LGW = 180 min, JFK $\leftrightarrow$ EWR = 150 min, NRT $\leftrightarrow$ HND = 120 min).
6. **`JRN-06 [Overnight Red-Eye Timezone Math]`**: Handle date rollover across International Date Line (+1 / -1 day) and UTC timezone offsets.
7. **`JRN-07 [Hotel Night Stay Dependency Edge]`**: Link flight arrival nodes to hotel check-in nodes via `HOTEL_NIGHT_FOR` edges with late check-in warning triggers (> 22:00 local).
8. **`JRN-08 [Cruise Embarkation Hard Cutoff]`**: Enforce strict 120-minute pre-departure all-aboard cutoffs for cruise ship nodes with zero relaxation.
9. **`JRN-09 [Graph Serialization Parity]`**: Support bidirectional conversion between `JourneyDependencyGraph` and GeoJSON LineString itineraries for mapping.
10. **`JRN-10 [Activity Weather Dependency Edge]`**: Add `WEATHER_DEPENDENT` attribute to outdoor activities, automatically triggering reschedule alerts upon rainfall forecasts $>50\%$.
11. **`JRN-11 [Baggage Interline Through-Check Tracking]`**: Flag whether baggage is checked through to final destination or requires intermediate customs recheck (e.g. US port of entry).
12. **`JRN-12 [Journey Graph Diff & Versioning]`**: Compute structural delta between Itinerary v1 and v2, highlighting added, modified, or cancelled nodes.

---

# Persona 3: `PER-0922 & PER-0923: Epistemic & Evidence Architects`

### Deep Architectural & Codebase Audit
Interrogating [`src/intake/packet_models.py`](file:///Users/pranay/Projects/travel_agency_agent/src/intake/packet_models.py), [`src/intake/extractors.py`](file:///Users/pranay/Projects/travel_agency_agent/src/intake/extractors.py), and [`spine_api/routers/settings.py`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/routers/settings.py).

### Granular Task Inventory

1. **`EPI-01 [Field-Level Epistemic Provenance]`**: Attach `epistemic_status`, `source_turn_id`, `confidence_score` (0.0–1.0), and `extracted_snippet` to every extracted slot.
2. **`EPI-02 [Assumptions Resolution Pipeline]`**: Endpoint `POST /api/trips/{id}/assumptions/{key}/confirm` allowing operator/traveler to promote `ASSUMED` $\to$ `FACT`.
3. **`EPI-03 [Confidence Decay Calculator]`**: Dynamic decay function reducing confidence score by $5\%$ per day for unconfirmed volatile attributes (pricing, seat maps).
4. **`EPI-04 [Conflicting Statement Arbiter]`**: Detect when traveler says "departing morning" in Turn 1 and "leaving after 6pm" in Turn 3; flag `EPISTEMIC_CONFLICT` for human review.
5. **`EPI-05 [Implicit Constraint Extraction]`**: Recognize implicit preferences (e.g. "traveling with a 6-month-old" $\implies$ implicit `requires_infant_bassinet` and `avoid_tight_connections`).
6. **`EPI-06 [Epistemic Audit Export]`**: Generate machine-readable JSON-LD proof graph showing exact conversational evidence grounding every itinerary decision.
7. **`EPI-07 [Negative Knowledge Tracking]`**: Explicitly record `EXCLUDED_PREFERENCES` (e.g. "no Boeing 737 MAX", "no Ryanair", "no ground-floor rooms").
8. **`EPI-08 [Hallucination Defense Benchmark]`**: Automated eval suite asserting that non-mentioned dates/destinations in customer emails are never fabricated into `FACT` fields.
9. **`EPI-09 [Multi-Source Epistemic Fusion]`**: Reconcile conflicting intake data from WhatsApp voice note vs email attachment, favoring authoritative documents over conversational transcripts.
10. **`EPI-10 [Stale State Warning Engine]`**: Block proposal link dispatch if $> 20\%$ of required itinerary parameters remain in `ASSUMED` or `UNKNOWN` status without explicit signoff.

---

# Persona 4: `PER-0711 & PER-0706: Constraint & Planning Systems Engineers`

### Deep Architectural & Codebase Audit
Interrogating [`src/decision/constraint_engine.py`](file:///Users/pranay/Projects/travel_agency_agent/src/decision/constraint_engine.py), [`src/decision/rules.py`](file:///Users/pranay/Projects/travel_agency_agent/src/decision/rules.py), and [`spine_api/routers/constraints.py`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/routers/constraints.py).

### Granular Task Inventory

1. **`CST-01 [Terminal-to-Terminal Airport MCT Table]`**: Airport-specific connection matrix (e.g. LHR T2 $\leftrightarrow$ T5 = 90m, T2 $\leftrightarrow$ T3 = 60m; CDG 2E $\leftrightarrow$ 2F = 75m).
2. **`CST-02 [Schengen 90/180 Rolling Window Algorithm]`**: Implement exact day-by-day sliding window stay counter tracking cumulative days across all 29 Schengen member states.
3. **`CST-03 [Passport 6-Month Post-Departure Rule]`**: Validate passport expiry date $> 180 \text{ days}$ beyond scheduled return date for Asian, Middle Eastern, and Latin American destinations.
4. **`CST-04 [Passport Blank Visa Pages Requirement]`**: Enforce minimum 2–4 blank visa pages for Southern African and East Asian entry requirements.
5. **`CST-05 [Yellow Fever & Vaccination Validation]`**: Flag mandatory International Certificate of Vaccination (ICVP) for transits through endemic regions.
6. **`CST-06 [Driver Minimum Age & International Driving Permit (IDP)]`**: Check car rental constraints (minimum age 21/25, young driver surcharges, IDP requirements in Japan/Italy).
7. **`CST-07 [Hotel Child Age & Bedding Policy]`**: Enforce hotel maximum room occupancy rules and child age cutoffs (e.g. child $\ge 12$ requires adult rate).
8. **`CST-08 [Domestic Transfer Baggage Reclaim Rule]`**: Enforce mandatory 90-minute connection for international-to-domestic transfers requiring customs baggage re-check (e.g. USA, Canada, Australia).
9. **`CST-09 [4-Tier Constraint Relaxation Solver]`**: Implement relaxation priority: `HARD_SAFETY` (never relaxed) $\to$ `REGULATORY` $\to$ `COMMERCIAL` $\to$ `SOFT_PREFERENCE` (relaxed first).
10. **`CST-10 [Rail-to-Flight MCT Transfers]`**: Model rail-station to airport terminal transit times (e.g. Paris Gare du Nord to CDG RER B = 60m + 45m buffer).
11. **`CST-11 [Over-the-Counter Medication Legality Check]`**: Warn travelers about country-specific medication bans (e.g. pseudoephedrine/Adderall in Japan/UAE).
12. **`CST-12 [Sabbath / Public Holiday Closure Warnings]`**: Flag itinerary activities scheduled during religious or public holidays (e.g. Shabbat in Jerusalem, Golden Week in Japan).

---

# Persona 5: `PER-0924 & PER-0925: Failure Mode & Graceful Degradation Architects`

### Deep Architectural & Codebase Audit
Interrogating [`src/services/resilience_engine.py`](file:///Users/pranay/Projects/travel_agency_agent/src/services/resilience_engine.py) and [`spine_api/routers/resilience.py`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/routers/resilience.py).

### Granular Task Inventory

1. **`RES-01 [Sliding-Window Failure Rate Counter]`**: Track error percentage over rolling 60s window (e.g. trip to `OPEN` if $>50\%$ errors across $>10$ calls).
2. **`RES-02 [Exponential Backoff with Full Jitter]`**: Compute retry interval: $t_{\text{retry}} = \text{random}(0, \min(M, t_{\text{base}} \times 2^{\text{attempt}}))$.
3. **`RES-03 [Half-Open Canary Probing]`**: Allow 1 trial request through after cooldown; if successful, transition to `CLOSED`; if failed, reset cooldown.
4. **`RES-04 [Supplier Failover Routing]`**: If Amadeus NDC fails, automatically route flight search to Sabre or Duffel fallback provider.
5. **`RES-05 [Degraded Result Caching Layer]`**: Serve cached L2 pricing with explicit `is_stale: true` and `cached_at` timestamp when supplier circuits are open.
6. **`RES-06 [Compensating Refund Engine]`**: Issue automated Stripe refund hold when flight booking succeeds but hotel booking fails and no alternative is available.
7. **`RES-07 [Poison Intake Quarantine Sandbox]`**: Isolate unparsable or malformed webhook payloads into a dedicated quarantine store with zero pipeline side effects.
8. **`RES-08 [Operator Escalation Pager Notification]`**: Emit webhook alerts to Slack / PagerDuty when any circuit trips to `OPEN` status.
9. **`RES-09 [Idempotent Payment Webhook Replay]`**: Prevent double-credit on replayed Stripe `checkout.session.completed` events using redis/table uniqueness locks.
10. **`RES-10 [Graceful Partial Itinerary Save]`**: If network drops during 5-day itinerary generation, persist the completed 3 days and mark remaining 2 as `PENDING_GENERATION`.
11. **`RES-11 [Circuit Breaker Admin Reset Endpoint]`**: `POST /api/v1/resilience/circuits/{name}/reset` with operator audit attribution.
12. **`RES-12 [Chaos Monkey Automated Test Suite]`**: Automated integration test injecting simulated 500ms latency and 30% HTTP 500 faults to verify zero data loss.

---

# Persona 6: `PER-0933 & PER-0927: Boundary Systems & Human-AI Authority Architects`

### Deep Architectural & Codebase Audit
Interrogating [`src/schemas/boundary_contracts.py`](file:///Users/pranay/Projects/travel_agency_agent/src/schemas/boundary_contracts.py), [`src/services/boundary_engine.py`](file:///Users/pranay/Projects/travel_agency_agent/src/services/boundary_engine.py), and [`spine_api/routers/boundaries.py`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/routers/boundaries.py).

### Granular Task Inventory

1. **`SEC-01 [HMAC SHA-256 Capability Token Signer]`**: Encode `token_id`, `agency_id`, `trip_id`, `traveler_id`, `role`, `scopes`, and `exp` into base64 payload with cryptographic signature.
2. **`SEC-02 [5-Tier Authority Gatekeeper Matrix]`**:
   * *Tier 0 (Autonomous):* Read-only search, itinerary synthesis, validation.
   * *Tier 1 (Recommendation):* AI proposes changes; operator review recommended.
   * *Tier 2 (Operator Sign-off):* Dispatching proposal to traveler, supplier soft-holds.
   * *Tier 3 (Client Authorization):* Payment processing, legal contract acceptance.
   * *Tier 4 (Dual Control):* Manual fee overrides $> \$500$, supplier cancellations, full cash refunds.
3. **`SEC-03 [Dual-Control Manager Approval Gate]`**: Require distinct secondary `manager` or `owner` signature before executing Tier 4 actions.
4. **`SEC-04 [Token Scope Validation Middleware]`**: FastAPI dependency verifying incoming Bearer token contains required `CapabilityScope` for requested endpoint.
5. **`SEC-05 [Instant Token Revocation Registry]`**: Maintain in-memory / redis revoked token set with instantaneous blacklisting.
6. **`SEC-06 [Cross-Tenant Isolation Guard]`**: Assert that `token.agency_id == requested_trip.agency_id` on every query, throwing HTTP 403 on mismatch.
7. **`SEC-07 [PII Data Masking on Public Endpoints]`**: Strip passport numbers, credit card tokens, and home addresses when exporting public proposals.
8. **`SEC-08 [Session Hijacking Defense]`**: Bind capability tokens to client IP subnets / User-Agent hashes to prevent token replay from unauthorized IPs.
9. **`SEC-09 [Time-Bound TTL Enforcement]`**: Default proposal tokens expire in 72 hours; payment authorization tokens expire in 30 minutes.
10. **`SEC-10 [Immutable Security Audit Trail]`**: Log every token issuance, verification, failure, and revocation event with timestamp and client IP.
11. **`SEC-11 [Role-Based Access Hierarchy]`**: Define `owner` $>$ `admin` $>$ `senior_agent` $>$ `agent` $>$ `traveler_booker` $>$ `traveler_guest`.
12. **`SEC-12 [Public Landing Page Rate Limiter]`**: Strict IP rate limiting (10 req/min) on unauthenticated public proposal and checker endpoints.

---

# Persona 7: `Invoice & Document Extraction Specialist`

### Deep Architectural & Codebase Audit
Interrogating [`src/intake/mrz.py`](file:///Users/pranay/Projects/travel_agency_agent/src/intake/mrz.py) and [`spine_api/routers/multimodal.py`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/routers/multimodal.py).

### Granular Task Inventory

1. **`DOC-01 [ICAO Doc 9303 7-3-1 Modulo-10 Algorithm]`**: Checksum calculator for passport numbers, DOBs, and expiration dates.
2. **`DOC-02 [TD3 2-Line Passport MRZ Parser]`**: Parse 44-character 2-line standard passport format.
3. **`DOC-03 [TD1 3-Line National ID MRZ Parser]`**: Parse 30-character 3-line national identity card MRZ format.
4. **`DOC-04 [TD2 2-Line Official Visa MRZ Parser]`**: Parse 36-character 2-line machine-readable visa format.
5. **`DOC-05 [Composite Checksum Validation]`**: Validate overall composite check digit mathematically proving zero OCR transcription error.
6. **`DOC-06 [OCR Character Noise Correction]`**: Heuristic repair for common OCR confusions ('O' $\leftrightarrow$ '0', 'I' $\leftrightarrow$ '1', 'S' $\leftrightarrow$ '5', 'Z' $\leftrightarrow$ '2') guided by valid checksum targets.
7. **`DOC-07 [Flight E-Ticket PDF Extraction]`**: Extract 13-digit e-ticket numbers (e.g. 006-2345678901), 6-character PNRs, baggage allowance, and fare class.
8. **`DOC-08 [Hotel Voucher Confirmation Parser]`**: Extract check-in/out dates, room category, meal plan (EP, CP, MAP, AP), and cancellation policy deadlines.
9. **`DOC-09 [Multi-Page PDF Document Splitting]`**: Automatically split combined multi-page booking confirmation PDFs into individual atomic passenger vouchers.
10. **`DOC-10 [MRZ Birth Date Century Resolution]`**: Deterministically resolve 2-digit birth year: if $YY > \text{current\_year} \% 100 \implies 19YY$, else $20YY$.
11. **`DOC-11 [Passport Photo Crop & PII Protection]`**: Automatically detect and mask biometric face photograph before storing document copies.
12. **`DOC-12 [Extraction Confidence Scorecard]`**: Return overall document confidence score based on checksum validity and OCR character confidence.

---

# Persona 8: `Travel Entitlements Graph & Passenger Rights Architect`

### Deep Architectural & Codebase Audit
Interrogating [`src/decision/passenger_rights.py`](file:///Users/pranay/Projects/travel_agency_agent/src/decision/passenger_rights.py) and [`spine_api/routers/passenger_rights.py`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/routers/passenger_rights.py).

### Granular Task Inventory

1. **`RGT-01 [EU Regulation 261/2004 Tier Calculator]`**:
   * $\le 1,500\text{km}$ and $\ge 3\text{h delay} \implies €250$.
   * $1,500\text{km} - 3,500\text{km}$ and $\ge 3\text{h delay} \implies €400$.
   * $> 3,500\text{km}$ and $\ge 4\text{h delay} \implies €600$ (or €300 if 3–4h delay).
2. **`RGT-02 [UK261 (Post-Brexit) Currency Tier Calculation]`**: Calculate UK statutory compensation in GBP (£220 / £350 / £520).
3. **`RGT-03 [US DOT 2024 Automatic Refund Rule]`**: Enforce mandatory 100% cash refund for US flight cancellations or significant schedule changes ($>3\text{h domestic}$, $>6\text{h international}$).
4. **`RGT-04 [Statutory Right-to-Care Mandates]`**: Trigger free meal vouchers ($>2\text{h delay}$) and complimentary hotel accommodation + transport ($>8\text{h or overnight delay}$).
5. **`RGT-05 [Extraordinary Circumstances Classifier]`**: Distinguish technical aircraft defects (airline liable) from weather/ATC strikes (exempt from compensation, but duty of care still applies).
6. **`RGT-06 [Baggage Delay Compensation (Montreal Convention)]`**: Calculate airline liability up to 1,288 Special Drawing Rights (SDR) (~$1,700) for lost/delayed baggage.
7. **`RGT-07 [Involuntary Denied Boarding Penalty]`**: Calculate US DOT 400% one-way fare compensation (up to $1,550) for involuntary bumpings.
8. **`RGT-08 [Automated Carrier Legal Claim Packet]`**: Generate pre-formatted legal claim PDF citing applicable EU261 articles, flight numbers, and radar timestamp logs.
9. **`RGT-09 [Statute of Limitations Tracker]`**: Enforce country-specific claim deadlines (e.g. UK = 6 years, Germany = 3 years, France = 5 years).
10. **`RGT-10 [Airline Voucher vs Cash Discrimination]`**: Flag when airline attempts to offer travel vouchers instead of statutory cash compensation and generate decline template.
11. **`RGT-11 [Connecting Flight Total Journey Distance Calculation]`**: Compute Great Circle Distance (Haversine formula) across all legs to determine correct distance bracket for missed connections.
12. **`RGT-12 [Live Flight Telemetry Integration]`**: Pull arrival runway touchdown times vs gate arrival times to accurately substantiate delay duration.

---

# Persona 9: `Travel Financial Systems Architect`

### Deep Architectural & Codebase Audit
Interrogating [`src/fees/currency.py`](file:///Users/pranay/Projects/travel_agency_agent/src/fees/currency.py), [`src/commission/`](file:///Users/pranay/Projects/travel_agency_agent/src/commission/), and [`spine_api/routers/financial_ops.py`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/routers/financial_ops.py).

### Granular Task Inventory

1. **`FIN-01 [Configurable FX Volatility Buffer]`**: Add 1.5%–3.0% slippage margin on cross-currency supplier quotes to guard against inter-settlement rate movement.
2. **`FIN-02 [Payment Gateway Interchange Fee Modeling]`**: Factor in merchant processing fees (e.g. Stripe 2.9% + $0.30 domestic, 3.9% + $0.30 international cards).
3. **`FIN-03 [Live Multi-Currency Mid-Market Rates]`**: Synchronize exchange rates from ECB / OpenExchangeRates with fallback reference table.
4. **`FIN-04 [Dynamic Agency Markup Engine]`**: Calculate retail price: $\text{Price} = (\text{Supplier Cost} \times (1 + \text{FX Buffer}) + \text{Gateway Fixed}) / (1 - \text{Markup Pct} - \text{Gateway Pct})$.
5. **`FIN-05 [Merchant Settlement Reconciliation]`**: Reconcile expected supplier payouts vs actual bank debits, flagging discrepancies $> \$1.00$.
6. **`FIN-06 [Corporate Multi-Currency Virtual Card Support]`**: Generate single-use virtual Mastercard/Visa cards in supplier currency to eliminate international FX conversion fees.
7. **`FIN-07 [Tax & VAT / GST Compliance Calculator]`**: Calculate local tourism taxes, hotel city taxes, and GST/VAT itemized breakdowns.
8. **`FIN-08 [Deposit & Final Balance Payment Schedules]`**: Support split-payment schedules (e.g. 20% non-refundable deposit upon booking, 80% balance 45 days prior).
9. **`FIN-09 [Supplier Cancellation Refund Fee Netting]`**: Automatically deduct non-refundable supplier penalties and agency administrative cancellation fees from traveler refunds.
10. **`FIN-10 [Sub-Agent Commission Split Ledgers]`**: Calculate commission revenue splits between host agency (30%) and independent contractor agent (70%).
11. **`FIN-11 [Multi-Currency Price Lock Risk Exposure]`**: Track aggregate currency exposure on open price locks and alert agency CFO if unhedged exposure exceeds \$50,000.
12. **`FIN-12 [Real-Time Margin Health Telemetry]`**: Metric `spine_commercial_net_margin_ratio` tracking average net profit margin across all booked packages.

---

# Persona 10: `Travel Counterfactual Systems Architect`

### Deep Architectural & Codebase Audit
Interrogating [`src/decision/counterfactual_recovery.py`](file:///Users/pranay/Projects/travel_agency_agent/src/decision/counterfactual_recovery.py) and [`spine_api/routers/counterfactual.py`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/routers/counterfactual.py).

### Granular Task Inventory

1. **`CFT-01 [3-Tier Counterfactual Generator]`**: Deterministically synthesize *Option A (Minimum Delay)*, *Option B (Same Carrier Protection)*, and *Option C (Premium Comfort)* upon node disruption.
2. **`CFT-02 [Multi-Attribute Alternative Scoring Engine]`**: Compute weighted ranking score: $\text{Score} = 100 - (\Delta t_{\text{hours}} \times 5) - (\Delta \$ / 20) + \text{Loyalty Bonus} - \text{Hotel Inconvenience}$.
3. **`CFT-03 [Live NDC Seat Liquidity Pre-Check]`**: Verify that alternative flights have available physical seat inventory before presenting to operator.
4. **`CFT-04 [Cascading Hotel & Transfer Shift Engine]`**: Automatically adjust hotel check-in dates and chauffeur pick-up times to align with selected counterfactual flight.
5. **`CFT-05 [Pre-Emptive 60-Minute Soft-Hold Reservation]`**: Place provisional soft-holds on alternative partner flights when inbound aircraft delay exceeds 90 minutes.
6. **`CFT-06 [Interline Partner Compatibility Matrix]`**: Check airline interline electronic ticketing agreements (IATA MITA) to guarantee baggage can be checked across rerouted airlines.
7. **`CFT-07 [Interactive SMS / WhatsApp 1-Click Reroute]`**: Send traveler 3 buttons on WhatsApp ("Reroute via Amsterdam [Fastest]", "Wait for Air France [Same Airline]", "Upgrade to Business") with instant execution.
8. **`CFT-08 [Trip Insurance Claim Auto-Filing]`**: Generate ready-to-sign trip interruption insurance claim documents for out-of-pocket meals and hotel receipts.
9. **`CFT-09 [Counterfactual Opportunity Cost Visualizer]`**: Display side-by-side timeline diff showing original vs counterfactual arrival times and cost impact in agency workbench.
10. **`CFT-10 [Historical Recovery Path Success Analytics]`**: Track historical rebooking acceptance rates to optimize ranking weights for future disruptions.
11. **`CFT-11 [Overnight Layover Hotel Allocation]`**: Automatically book airport transit hotel when counterfactual itinerary requires $>8\text{h}$ overnight connection.
12. **`CFT-12 [Traveler VIP Loyalty Status Protection]`**: Ensure rebooked flights on partner carriers preserve Star Alliance Gold / SkyTeam Elite Plus lounge access and priority baggage.

---

# Persona 11: `Family & Group Travel Architect`

### Deep Architectural & Codebase Audit
Interrogating [`src/decision/group_consensus.py`](file:///Users/pranay/Projects/travel_agency_agent/src/decision/group_consensus.py) and [`spine_api/routers/group_booking.py`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/routers/group_booking.py).

### Granular Task Inventory

1. **`GRP-01 [Multi-Traveler Preference Profile Model]`**: Store individual budget bounds, preferred pacing (`RELAXED`, `BALANCED`, `INTENSE`), priority activities, rooming needs, and dietary restrictions.
2. **`GRP-02 [Pareto Frontier Consensus Algorithm]`**: Identify non-dominated itinerary proposals where no alternative can make one traveler happier without making another worse off.
3. **`GRP-03 [Harmonic Dissatisfaction Penalty]`**: Use harmonic averaging to heavily penalize options that violate any single traveler's hard budget or physical pacing bounds.
4. **`GRP-04 [Consensus Tier Classification]`**: Tag options as `STRONG_MATCH` ($\ge 80$), `ACCEPTABLE_COMPROMISE` ($50–79$), or `INFEASIBLE` ($<50$ or budget violations).
5. **`GRP-05 [Compromises & Violations Explainer]`**: Output explicit human-readable reasons (e.g. "Alice exceeds budget by \$300", "Bob prefers relaxed pacing vs intense itinerary").
6. **`GRP-06 [Split-Payment Ledger Engine]`**: Calculate individual share balances with customizable allocation rules (equal split, room-based, or itemized activity add-ons).
7. **`GRP-07 [Group Invite & Role Delegation Tokens]`**: Generate scoped capability tokens for `primary_booker` (can authorize payments) vs `traveler_guest` (view and vote only).
8. **`GRP-08 [Asymmetric Activity Opt-In/Opt-Out]`**: Allow group members to participate in separate afternoon activities (e.g. 3 go golfing, 3 go to spa) while maintaining unified dinner/hotel bookings.
9. **`GRP-09 [Dietary Compatibility Scanner]`**: Flag group restaurant reservations that fail to accommodate individual dietary restrictions (e.g. gluten-free, vegan, severe peanut allergy).
10. **`GRP-10 [Connecting Rooms & Bedding Configuration Optimizer]`**: Group family travelers with infants/children into guaranteed connecting rooms or multi-bedroom villas.
11. **`GRP-11 [Collaborative Group Voting Workspace]`**: Real-time voting dashboard where group members cast preference upvotes that dynamically re-rank candidate packages.
12. **`GRP-12 [Group Booking Discount Threshold Sentinel]`**: Alert operator when group size reaches supplier discount thresholds (e.g. 10th traveler unlocks 15% group rate or 1 free tour leader ticket).
