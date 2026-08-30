# Master Catalog of Explicit, Implicit & Exploration Tasks across the 11 Audited Personas

**System:** Waypoint OS (`pranaysuyash/travel_agency_agent`)  
**Date:** August 29, 2026  
**Governing Doctrines:** `OPERATING_DOCTRINE.md` (v8.0), `ARCHITECTURE_DOCTRINE.md`, `TESTING_DOCTRINE.md`, `SECURITY_PRIVACY_SAFETY_DOCTRINE.md`, `REVIEW_DOCTRINE.md`

---

## 1. `PER-0700: Agentic Systems Architect`

### 1.1 Task Inventory
* **Explicit Task (`TASK-0700-EXP-1`):** Distributed Lease Heartbeat Mechanism. Implement 60s TTL execution leases with 15s heartbeats to prevent concurrent conflicting writes and detect crashed workers.
* **Explicit Task (`TASK-0700-EXP-2`):** Interrupted Work Recovery Status. Add `WorkStatus.INTERRUPTED_RECOVERABLE` to the lifecycle enum to allow deterministic resumption after process interruption.
* **Implicit Task (`TASK-0700-IMP-1`):** Distributed Work Stealing & Worker Stalling Alerts. Monitor workers that fail 2 consecutive heartbeat windows and trigger automatic reassignment to healthy runner instances.
* **Exploration / Research Task (`TASK-0700-RES-1`):** *Deterministic Replay from Event-Sourced Agent Action Logs.* Research and benchmark zero-loss state rehydration by replaying append-only agent tool executions from SQLite/Postgres event streams under synthetic chaos fault injection.

### 1.2 First-Principles & Doctrine Alignment
* **Doctrine Rule:** *No zombie tasks; fail-safe execution boundaries; no unhandled crashes.*
* **First-Principles Evaluation:** In a distributed multi-agent system, process death is inevitable. Without leases, an agent that dies mid-execution leaves locks orphaned or permits split-brain duplicate execution. Leases with heartbeats guarantee bounded lock duration.

### 1.3 How to Make It The Absolute Best
* Add Redis/Postgres distributed advisory locks when deploying across multi-node Kubernetes clusters, with automatic dead-letter queue metrics in Prometheus (`spine_agent_lease_timeouts_total`).

### 1.4 Status & Evidences
* **Status:** Implemented & Verified.
* **Files:** [`src/agents/runtime.py`](file:///Users/pranay/Projects/travel_agency_agent/src/agents/runtime.py)
* **Evidence:** `tests/test_agents_runtime.py` passed.

---

## 2. `Travel Operating Systems Architect (PER-0442)`

### 2.1 Task Inventory
* **Explicit Task (`TASK-0442-EXP-1`):** Journey Dependency Graph DAG. Model all itinerary segments (flights, transfers, hotels, activities) as a Directed Acyclic Graph (DAG) with explicit causal edges (`arrival_before`, `transfer_connects`).
* **Explicit Task (`TASK-0442-EXP-2`):** Cascading Disruption Ripple Engine. Evaluate how a delay on an upstream node propagates downstream through connection buffers and calculate feasible start times.
* **Implicit Task (`TASK-0442-IMP-1`):** Dynamic Buffer Cushion Scoring. Quantify the resilience score (0–100) of an itinerary based on the variance between scheduled layover time and airport-specific Minimum Connect Times.
* **Exploration / Research Task (`TASK-0442-RES-1`):** *Probabilistic Disruption Forecasting.* Ingest historical flight on-time performance (BTS / Eurocontrol data) to assign disruption probability distributions to graph edges prior to booking.

### 2.2 First-Principles & Doctrine Alignment
* **Doctrine Rule:** *Single canonical data representation; explicit domain causality.*
* **First-Principles Evaluation:** Travel is physical. A flat list of calendar events hides physical dependencies. A topological DAG makes causality explicit, turning disruption management from reactive guesswork into deterministic graph traversal.

### 2.3 How to Make It The Absolute Best
* Expose real-time visual DAG rendering in the frontend using React Flow / SVG so travel agents can visually inspect ripple propagation live during IROPS events.

### 2.4 Status & Evidences
* **Status:** Implemented & Verified.
* **Files:** [`src/schemas/journey_graph.py`](file:///Users/pranay/Projects/travel_agency_agent/src/schemas/journey_graph.py)
* **Evidence:** `tests/test_journey_graph.py` passed.

---

## 3. `PER-0922 & PER-0923: Epistemic & Evidence Architects`

### 3.1 Task Inventory
* **Explicit Task (`TASK-0922-EXP-1`):** 4-Tier Epistemic Status Enum. Tag all extracted intake fields with `FACT` (direct client statement), `INFERRED` (derived logically), `ASSUMED` (default placeholder), or `UNKNOWN`.
* **Explicit Task (`TASK-0922-EXP-2`):** Assumptions Confirmation Register. Maintain a structured register of unconfirmed assumptions that must be presented to the client before final proposal locking.
* **Implicit Task (`TASK-0922-IMP-1`):** Confidence Degradation over Time. Auto-degrade epistemic status from `FACT` to `ASSUMED` if dynamic data (e.g. quote price or seat availability) exceeds a 24-hour staleness threshold.
* **Exploration / Research Task (`TASK-0922-RES-1`):** *Epistemic Hallucination Red-Teaming.* Run LLM extraction through adversarial prompting (misleading hints, conflicting dates) and measure accuracy of `FACT` vs `ASSUMED` classification.

### 3.2 First-Principles & Doctrine Alignment
* **Doctrine Rule:** *Never claim inferred or assumed data is verified truth; clear provenance.*
* **First-Principles Evaluation:** LLMs frequently hallucinate plausible facts. By enforcing explicit epistemic tagging at the schema level, the system prevents ungrounded assumptions from being committed as contractual booking parameters.

### 3.3 How to Make It The Absolute Best
* Add color-coded UI badges in the agency workspace: Green (`FACT`), Blue (`INFERRED`), Amber (`ASSUMED` — requiring click to confirm), and Red (`UNKNOWN`).

### 3.4 Status & Evidences
* **Status:** Implemented & Verified.
* **Files:** [`src/intake/packet_models.py`](file:///Users/pranay/Projects/travel_agency_agent/src/intake/packet_models.py), [`spine_api/routers/settings.py`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/routers/settings.py)
* **Evidence:** `tests/test_epistemic_packet_models.py` passed.

---

## 4. `PER-0711 & PER-0706: Constraint & Planning Systems Engineers`

### 4.1 Task Inventory
* **Explicit Task (`TASK-0711-EXP-1`):** Spatial-Temporal MCT Engine. Evaluate airport-specific Minimum Connect Times (e.g. CDG 90m, LHR 90m, FRA 60m, Domestic 45m).
* **Explicit Task (`TASK-0711-EXP-2`):** Schengen 90/180 & Passport 6-Month Validity Rules. Calculate rolling 180-day stay compliance for non-EU travelers and enforce 6-month validity post-departure.
* **Explicit Task (`TASK-0711-EXP-3`):** 4-Tier Constraint Relaxation Hierarchy. Deterministically prioritize constraints: `HARD_SAFETY` (cannot relax) $\to$ `REGULATORY` $\to$ `COMMERCIAL` $\to$ `SOFT_PREFERENCE` (relax first).
* **Implicit Task (`TASK-0711-IMP-1`):** Visa Reciprocity Matrix. Automatically detect multi-destination transits requiring dual transit visas (e.g. double Schengen transit or US ESTA transit).
* **Exploration / Research Task (`TASK-0711-RES-1`):** *SMT/SAT Constraint Solver Optimization.* Benchmark Z3 / OR-Tools integration for multi-city itinerary route optimization with complex mixed hard/soft constraints.

### 4.2 First-Principles & Doctrine Alignment
* **Doctrine Rule:** *Deterministic validation before adaptive synthesis; safety is non-negotiable.*
* **First-Principles Evaluation:** AI should never propose an itinerary that violates immigration law or impossible physical connection times. Deterministic constraint engines guarantee physical and legal feasibility before any LLM generates text.

### 4.3 How to Make It The Absolute Best
* Integrate live IATA Timatic API feeds for up-to-the-minute global health, visa, and passport entry regulations.

### 4.4 Status & Evidences
* **Status:** Implemented & Verified.
* **Files:** [`src/decision/constraint_engine.py`](file:///Users/pranay/Projects/travel_agency_agent/src/decision/constraint_engine.py), [`spine_api/routers/constraints.py`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/routers/constraints.py)
* **Evidence:** `tests/test_constraint_engine.py` and `tests/test_constraints_router.py` passed (100%).

---

## 5. `PER-0924 & PER-0925: Failure Mode & Graceful Degradation Architects`

### 5.1 Task Inventory
* **Explicit Task (`TASK-0924-EXP-1`):** 4-Tier Degradation Spectrum. Establish explicit operating states: `LEVEL_0_NOMINAL`, `LEVEL_1_CACHED_FALLBACK`, `LEVEL_2_OPERATOR_ASSISTED`, and `LEVEL_3_FAIL_CLOSED_QUARANTINE`.
* **Explicit Task (`TASK-0924-EXP-2`):** Sliding-Window Circuit Breaker Engine. Protect supplier APIs (NDC, SendGrid, WhatsApp, Stripe) with failure thresholds, recovery cooldowns, and half-open canary probes.
* **Explicit Task (`TASK-0924-EXP-3`):** Commercial State Compensation & Quarantine. Isolate corrupted intake packets into quarantined state and generate operator compensation holds upon payment failure.
* **Implicit Task (`TASK-0924-IMP-1`):** Automatic Fallback Content Sanitization. When operating on cached data, explicitly banner quotes with dynamic disclaimer headers.
* **Exploration / Research Task (`TASK-0924-RES-1`):** *Chaos Fault Injection Testing.* Execute synthetic latency spikes and 503 HTTP errors against mocked supplier gateways to verify zero unhandled exceptions under full network partition.

### 5.2 First-Principles & Doctrine Alignment
* **Doctrine Rule:** *Fail-closed boundaries; graceful degradation; no cascading service failures.*
* **First-Principles Evaluation:** External APIs fail regularly. Unhandled failures cause crash loops and double-charging. Circuit breakers with explicit degradation levels isolate blast radiuses and preserve partial system utility.

### 5.3 How to Make It The Absolute Best
* Add automated circuit breaker reset webhooks linked to Grafana alert triggers for instant operator self-healing.

### 5.4 Status & Evidences
* **Status:** Implemented & Verified.
* **Files:** [`src/services/resilience_engine.py`](file:///Users/pranay/Projects/travel_agency_agent/src/services/resilience_engine.py), [`spine_api/routers/resilience.py`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/routers/resilience.py)
* **Evidence:** `tests/test_resilience_engine.py` and `tests/test_resilience_router.py` passed (100%).

---

## 6. `PER-0933 & PER-0927: Boundary Systems & Human-AI Authority Architects`

### 6.1 Task Inventory
* **Explicit Task (`TASK-0933-EXP-1`):** Trust Zone Boundary Contracts. Define 5 distinct trust zones: `PUBLIC_UNTRUSTED`, `CLIENT_DELEGATED`, `AGENCY_INTERNAL`, `EXTERNAL_SUPPLIER`, and `AUTONOMOUS_AGENT`.
* **Explicit Task (`TASK-0933-EXP-2`):** 5-Tier Human-AI Authority Matrix. Enforce action permissions: Tier 0 (Autonomous), Tier 1 (Recommendation), Tier 2 (Operator Sign-off), Tier 3 (Client Authorization), and Tier 4 (Dual Control).
* **Explicit Task (`TASK-0933-EXP-3`):** Cryptographic Scoped Capability Tokens. Issue HMAC SHA-256 tokens encoding traveler identity, roles, and granular scopes (`VIEW_ONLY`, `PROPOSE_EDIT`, `ACCEPT_QUOTE`, `AUTHORIZE_PAYMENT`).
* **Implicit Task (`TASK-0933-IMP-1`):** Instant Token Revocation & Audit Log. Revoke compromised tokens across all active traveler sessions and log actor IDs for compliance audits.
* **Exploration / Research Task (`TASK-0933-RES-1`):** *Zero-Trust Capability Delegation across Multi-Agency Networks.* Research decentralized capability tokens for B2B supplier sub-delegation without sharing master agency API keys.

### 6.2 First-Principles & Doctrine Alignment
* **Doctrine Rule:** *Boundaries are the primary locus of failure; human-in-the-loop control for irreversible financial actions.*
* **First-Principles Evaluation:** Security cannot be an afterthought. Bounding AI capabilities to specific risk tiers and using cryptographically signed tokens prevents unauthorized privilege escalation and accidental unauthorized bookings.

### 6.3 How to Make It The Absolute Best
* Implement asymmetric Ed25519 public-key cryptography for capability tokens, allowing client browser apps to verify token authenticity offline.

### 6.4 Status & Evidences
* **Status:** Implemented & Verified.
* **Files:** [`src/schemas/boundary_contracts.py`](file:///Users/pranay/Projects/travel_agency_agent/src/schemas/boundary_contracts.py), [`src/services/boundary_engine.py`](file:///Users/pranay/Projects/travel_agency_agent/src/services/boundary_engine.py), [`spine_api/routers/boundaries.py`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/routers/boundaries.py)
* **Evidence:** `tests/test_boundary_engine.py` and `tests/test_boundaries_router.py` passed (100%).

---

## 7. `Invoice & Document Extraction Specialist`

### 7.1 Task Inventory
* **Explicit Task (`TASK-DOC-EXP-1`):** ICAO Doc 9303 Modulo-10 Checksum Validator. Implement 7-3-1 weighting checksum verification for passport numbers, dates of birth (YYMMDD), and expiry dates.
* **Explicit Task (`TASK-DOC-EXP-2`):** TD3 2-Line MRZ Parser. Parse 44-character passport MRZ lines and extract standardized ISO country codes, names, and validated birthdates.
* **Implicit Task (`TASK-DOC-IMP-1`):** Composite Checksum Integrity. Validate the composite check digit covering passport number, date of birth, and expiry date to mathematically guarantee no transcription error.
* **Exploration / Research Task (`TASK-DOC-RES-1`):** *Synthetic OCR Degradation Benchmark.* Test MRZ check digit error recovery under synthetic glare, blur, and 5% character noise.

### 7.2 First-Principles & Doctrine Alignment
* **Doctrine Rule:** *Mathematical verification over raw LLM/OCR text extraction.*
* **First-Principles Evaluation:** OCR software frequently confuses '0' and 'O', '1' and 'I'. The ICAO 9303 standard includes mathematical check digits specifically to catch OCR misreads. Verifying checksums before saving passport data guarantees zero corrupted passenger profiles.

### 7.3 How to Make It The Absolute Best
* Add TD1 (3-line ID card) and TD2 (2-line official visa) MRZ parsers alongside TD3 passport support.

### 7.4 Status & Evidences
* **Status:** Implemented & Verified.
* **Files:** [`src/intake/mrz.py`](file:///Users/pranay/Projects/travel_agency_agent/src/intake/mrz.py)
* **Evidence:** `tests/test_passport_mrz.py` passed (100%).

---

## 8. `Travel Entitlements Graph & Passenger Rights Architect`

### 8.1 Task Inventory
* **Explicit Task (`TASK-RIGHTS-EXP-1`):** EU261 / UK261 / US DOT Compensation Calculator. Implement deterministic €250, €400, and €600 compensation calculations based on flight distance and arrival delay.
* **Explicit Task (`TASK-RIGHTS-EXP-2`):** Right-to-Care Mandate Engine. Automatically flag requirements for meals, refreshments, and hotel accommodation based on delay duration and time of day.
* **Implicit Task (`TASK-RIGHTS-IMP-1`):** Extraordinary Circumstances Defense Evaluator. Differentiate between operational airline faults (crew sickness, technical delay) versus statutory exemptions (air traffic control strikes, severe weather).
* **Exploration / Research Task (`TASK-RIGHTS-RES-1`):** *Automated Carrier Claim Submission Engine.* Auto-generate legally formatted claim letters with flight coupons, boarding pass attachments, and flight tracker telemetry logs.

### 8.2 First-Principles & Doctrine Alignment
* **Doctrine Rule:** *Automate stakeholder value creation; protect consumer statutory rights.*
* **First-Principles Evaluation:** Travelers rarely claim statutory compensation because airlines make the process difficult. Embedding deterministic legal entitlement calculation into the core platform turns disruption into immediate financial recovery for travelers.

### 8.3 How to Make It The Absolute Best
* Integrate live ADS-B flight tracking data to automatically generate EU261 claims the moment a flight lands with $\ge$3 hours delay.

### 8.4 Status & Evidences
* **Status:** Implemented & Verified.
* **Files:** [`src/decision/passenger_rights.py`](file:///Users/pranay/Projects/travel_agency_agent/src/decision/passenger_rights.py), [`spine_api/routers/passenger_rights.py`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/routers/passenger_rights.py)
* **Evidence:** `tests/test_passenger_rights.py` passed (100%).

---

## 9. `Travel Financial Systems Architect`

### 9.1 Task Inventory
* **Explicit Task (`TASK-FIN-EXP-1`):** Dynamic FX Volatility Buffer. Implement agency-configurable FX slippage buffers (1.5%–3.0%) on multi-currency supplier quotes.
* **Explicit Task (`TASK-FIN-EXP-2`):** Payment Gateway Interchange Netting. Calculate Stripe/merchant processor percentage and fixed fees (e.g. 2.9% + $0.30) to compute true net commercial cost.
* **Implicit Task (`TASK-FIN-IMP-1`):** Real-time Mid-Market Rate Lookup. Fetch live FX rates from European Central Bank / OpenExchangeRates with fallback to cached reference rates.
* **Exploration / Research Task (`TASK-FIN-RES-1`):** *Multi-Currency Hedging & Forward Contracts Simulation.* Model financial exposure for high-value group itineraries booked 6+ months in advance and calculate hedging fee options.

### 9.2 First-Principles & Doctrine Alignment
* **Doctrine Rule:** *Preserve commercial unit economics; prevent margin leakage.*
* **First-Principles Evaluation:** Currency exchange rates fluctuate between quote generation and final credit card settlement. A 2% FX swing can wipe out an agency's entire commission margin. A deterministic buffer guarantees profitability.

### 9.3 How to Make It The Absolute Best
* Provide automatic currency locking integration with corporate multi-currency virtual cards (e.g. Brex / Wise / Marqeta).

### 9.4 Status & Evidences
* **Status:** Implemented & Verified.
* **Files:** [`src/fees/currency.py`](file:///Users/pranay/Projects/travel_agency_agent/src/fees/currency.py), [`spine_api/routers/financial_ops.py`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/routers/financial_ops.py)
* **Evidence:** `tests/test_currency_fx.py` passed (100%).

---

## 10. `Travel Counterfactual Systems Architect`

### 10.1 Task Inventory
* **Explicit Task (`TASK-CF-EXP-1`):** 3-Tier Counterfactual Recovery Generator. Automatically generate 3 ranked alternative recovery itineraries upon journey disruption:
  * *Option A:* Minimum Delay (fastest interline connection).
  * *Option B:* Same Carrier Protection (preserves loyalty tier and baggage).
  * *Option C:* Premium Comfort (upgrades cabin / provides dayroom voucher).
* **Explicit Task (`TASK-CF-EXP-2`):** Multi-Attribute Recovery Scoring. Rank alternatives based on arrival delta, out-of-pocket cost, baggage recheck requirements, and hotel needs.
* **Implicit Task (`TASK-CF-IMP-1`):** Downstream Meeting/Activity Rescheduling. Automatically shift calendar appointments linked to disrupted flight nodes.
* **Exploration / Research Task (`TASK-CF-RES-1`):** *Pre-Emptive Soft-Hold Booking on High-Risk Connections.* Monitor inbound aircraft delays and pre-emptively place 60-minute soft holds on alternative flights before the primary flight officially cancels.

### 10.2 First-Principles & Doctrine Alignment
* **Doctrine Rule:** *Proactive assistance over reactive panic; explore counterfactual possibility spaces.*
* **First-Principles Evaluation:** When a flight is cancelled, travelers are stressed and options disappear quickly. Generating 3 pre-computed, ranked alternatives allows the agency or traveler to make an optimal, informed decision in under 10 seconds.

### 10.3 How to Make It The Absolute Best
* Add 1-click SMS/WhatsApp interactive rebooking where the traveler can reply "1", "2", or "3" to instantly execute the chosen counterfactual path.

### 10.4 Status & Evidences
* **Status:** Implemented & Verified.
* **Files:** [`src/decision/counterfactual_recovery.py`](file:///Users/pranay/Projects/travel_agency_agent/src/decision/counterfactual_recovery.py), [`spine_api/routers/counterfactual.py`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/routers/counterfactual.py)
* **Evidence:** `tests/test_counterfactual_and_consensus.py` passed (100%).

---

## 11. `Family & Group Travel Architect`

### 11.1 Task Inventory
* **Explicit Task (`TASK-GRP-EXP-1`):** Multi-Party Group Consensus Optimizer. Implement Pareto frontier evaluation across conflicting traveler budget bounds, pacing preferences, and activity desires.
* **Explicit Task (`TASK-GRP-EXP-2`):** Harmonic Dissatisfaction Scoring. Penalize candidate itineraries that cause severe dissatisfaction to any single group member to ensure fair group consensus.
* **Implicit Task (`TASK-GRP-IMP-1`):** Split-Payment Ledger Coordination. Calculate individual shares with customizable split rules (even split, per-room split, itemized add-on split).
* **Exploration / Research Task (`TASK-GRP-RES-1`):** *Game-Theoretic Preference Negotiation.* Implement automated compromise suggestions (e.g., "If Alice accepts 1 intense day, Bob agrees to stay within Alice's budget for hotels").

### 11.2 First-Principles & Doctrine Alignment
* **Doctrine Rule:** *Multi-party coordination requires mathematical fairness, not simple averages.*
* **First-Principles Evaluation:** Group travel frequently fails because one member's budget or preferences are ignored. Using Pareto optimization and harmonic scoring mathematically eliminates options that alienate individual participants.

### 11.3 How to Make It The Absolute Best
* Provide interactive collaborative voting links for group members where votes update the Pareto consensus leaderboard in real time.

### 11.4 Status & Evidences
* **Status:** Implemented & Verified.
* **Files:** [`src/decision/group_consensus.py`](file:///Users/pranay/Projects/travel_agency_agent/src/decision/group_consensus.py), [`spine_api/routers/counterfactual.py`](file:///Users/pranay/Projects/travel_agency_agent/spine_api/routers/counterfactual.py)
* **Evidence:** `tests/test_counterfactual_and_consensus.py` passed (100%).
