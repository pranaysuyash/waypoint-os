# Product B Agent Architecture — Wide-Open Brainstorm

**Date:** 2026-05-08
**Skill:** wide-open-brainstorm
**Execution mode:** Single-agent (Task subagents — no external LLM CLIs detected)
**Panel:** Strategist, Champion, Operator, Cartographer, Trickster, Skeptic, Executioner, Future Self

---

## 1) Seed Brief

### What we are designing

Product B is a free consumer-facing itinerary audit tool. The GTM wedge hypothesis: travelers submit their itinerary/plan → get a structured audit with evidence-backed findings → share a forward-ready action packet with their existing travel agent → agent revises the plan → demand pull for Product A (the agency OS).

### Current state of codebase

**Existing:**
- `frontend/src/app/(traveler)/itinerary-checker/page.tsx` (2018 lines) — full frontend UX: upload (PDF/OCR), paste, results
- `src/public_checker/live_checks.py` — live weather/seasonality checks via Open-Meteo. `build_live_checker_signals()` produces hard/soft blockers, score penalties, structured risks
- `src/intake/checker_agent.py` — `CheckerAgent` with `audit(packet, decision)` method. Checks budget blindness, high-risk trip purposes, low-confidence-without-hard-blockers
- `src/agents/risk_contracts.py` — shared `to_structured_risk()` factory
- `spine_api/product_b_events.py` (467 lines) — `ProductBEventStore`: append-only JSONL, 8 events, KPI computation
- `spine_api/services/public_checker_service.py` (284 lines) — orchestrates full flow
- `spine_api/services/live_checker_service.py` (79 lines) — consented submission, raw text collection, live checker adjustments
- `spine_api/server.py` — routes: `POST /api/public-checker/run`, `POST /api/public-checker/events`, `GET /analytics/product-b/kpis`
- `spine_api/contract.py` — all Pydantic models

**Not existing:**
- No dedicated LLM prompt templates — all logic is code-based heuristics
- No multi-agent dispatch infrastructure

### The question

What distinct agents should Product B run? What does each agent do? What are their exact prompts, inputs, outputs, and composition pattern? Where does LLM reasoning fit vs. rule-based heuristics? How does this change if we launch **now** before the Product A backend/spine pipeline is ready?

### Core outcome

A documented agent architecture with per-agent prompts and contracts, ready for implementation.

### Permission

Be practical, silly, weird, and ambitious. All altitudes welcome.

---

## 2) Individual Role Outputs

### 2.1 Strategist

**Output:**

*10,000 ft: The Wedge Shapes the Architecture*

Product B's agents must not mirror Product A's. Product A is a depth-first, high-fidelity decision engine for agents — it optimizes for correctness, audit trails, and defensibility. Product B is the opposite: a speed-first, density-maximizing consumer product that optimizes for the "aha moment per second" ratio. Its agents must produce findings that are so viscerally specific and surprising that a traveler reflexively forwards them to their agent.

The strategic thesis: Product B agents should be stateless, single-purpose, composable analyzers that converge on a ranked finding list, not a decision. Product A makes decisions (proceed, stop, ask). Product B makes findings — and the aggregation of findings into severity-ranked evidence is the product.

This means the agent pipeline should invert the Product A pattern. Instead of "intake → deep reasoning → decision → surface output," Product B should be "intake → parallel shallow analyzers → finding ranker → surface immediately → deep synthesis on demand."

*1,000 ft: The Agent Roster*

**ParserAgent** (LLM, ~300 tokens): Raw itinerary text → structured TripIntent. Single LLM call, no chain-of-thought. The only acceptable complexity is extracting N destinations from unstructured text.

**EnrichmentAgents** (rule-based/API, zero LLM): A registry of lightweight plugins — WeatherAgent (wraps live_checks.py), CalendarAgent (public holidays/events), CostAgent (cost-of-living bands), SafetyAgent (travel advisories/visas), RoutingAgent (flight times, connection viability). All stateless — `Enrich(destination, date_range) -> EnrichmentData`. Parallelize trivially across N destinations. None call an LLM.

**AnalysisAgent** (hybrid): Two-phase. 1) Rule-based analyzers: budget match, weather severity, holiday disruption, minimum-stay violation. 2) LLM-based analyzers: trip coherence, pacing, purpose-fit, hidden risks. One LLM call with full enriched TripIntent, outputting Findings[]. Rule-based findings get priority ranking by severity. LLM findings inserted at matched severity level. Deduplicate.

**PacketAgent** (LLM, ~600 tokens): Takes ranked findings + original trip intent. Produces forward-ready action packet. Each finding in consumer language with exact question to ask agent. Envelope: consumer-friendly title, bullet findings, agent-facing ask-list at bottom.

**No CheckerAgent equivalent for Product B.** The secondary audit pattern exists for Product A's high-stakes decisions. Product B doesn't make decisions — it makes findings. If confidence is low on a finding, downgrade severity and surface deeper in the list. Don't re-audit.

*Composition pattern:*
```
ParserAgent(text) → TripIntent
                        ↓
               [EnrichmentAgent * 5]  (parallel, per-destination)
                        ↓
               TripIntent + EnrichmentData[]
                        ↓
               AnalysisAgent (rules first, then LLM)
                        ↓
               Ranked Findings[]
                        ↓
               PacketAgent → ActionPacket
```

Target: under 5 seconds total. Critical path is Parser → Analysis (LLM parts are the bottleneck). Enrichment is fully parallel and API-bound.

*Ground level: The first agent to build:*
AnalysisAgent — specifically its LLM reasoning component. The rule-based analyzers already mostly exist (live_checks.py handles weather). The ParserAgent can lean on existing spine pipeline's envelope builder. The PacketAgent is a template with LLM fill-ins. What doesn't exist and creates the wedge: an LLM that can look at an enriched trip and say something a human would never spot in 30 seconds.

The critical LLM prompt instruction: "Identify exactly one finding per destination that a traveler would not discover by reading a guidebook. Surface cross-destination interactions. Do not produce generic travel advice. If you cannot find a non-obvious finding, output nothing for that dimension."

**The thing most people miss about this:** The action packet isn't designed for the traveler — it's designed for the agent who receives it. The packet's real job is to make the receiving agent think "I need the tool that produced this" (Product A). Every field, every phrasing should be optimized for the agent's reaction, not the traveler's. The traveler is the delivery mechanism; the agent is the conversion target.

---

### 2.2 Operator

**Output:**

Traced the full code. Here is the architecture step by step.

**The Five Agents, In Order:**

**Agent 1: Input Triage & Enrichment Gate**
- Input: request_dict (raw_note, structured_json, retention_consent, session_id, inquiry_id)
- Output: consented_submission, session_id, inquiry_id, input_mode, has_* booleans
- Timeout: ~50ms (pure dict manipulation)
- On failure: Don't block — log and proceed with fallback IDs
- Type: Rule-based

Before anything else, classify input richness. Determines whether downstream runs in discovery mode or can produce credible findings.

**Agent 2: Spine Pipeline (Multi-Stage Extraction → Decision → Safety)**

This is 8 mandatory sequential sub-agents sharing a single CanonicalPacket:

| Stage | Agent | Input | Output | ~Time | On Failure |
|-------|-------|-------|--------|-------|------------|
| 2a | ExtractionPipeline | SourceEnvelope[] | CanonicalPacket | ~2-8s (LLM) | Raise → 500 |
| 2b | Validation | CanonicalPacket, stage | PacketValidationReport | ~100ms | Raise → 500 |
| 2c | NB01 Gate | CanonicalPacket, validation | GateVerdict + reasons | ~10ms | Degrade → partial intake. Escalate → early exit |
| 2d | Gap & Decision | CanonicalPacket, feasibility, settings | DecisionResult | ~3-12s (hybrid) | Raise → 500 |
| 2e | NB02 Autonomy Gate | DecisionResult, settings | AutonomyOutcome | ~50ms | Conservative default |
| 2f | Suitability | CanonicalPacket | SuitabilityFlag[] | ~500ms-2s | Silently fail → empty flags |
| 2g | Frontier (Ghost/Sentiment) | CanonicalPacket, DecisionResult | FrontierResult | ~1-5s | Silently fail → default empty |
| 2h | Output Bundles | strategy, decision, packet | bundles + leakage_result | ~200ms | Raise → 500 |

**Critical partial-data contract:** If NB01 returns DEGRADE (missing origin, budget, purpose, or party_size), pipeline sets `decision_state="ASK_FOLLOWUP"` and returns immediately — skipping everything downstream. The frontend renders follow_up_questions as inline form fields.

**Agent 3: Live Checker (Post-Spine Enrichment)**
- Input: packet_payload, raw_text (concatenated from all sources)
- Output: live_checker dict with destination, seasonality, current_conditions, signals, blockers, structured_risks, score_penalty
- Timeout: ~10s total (geocode 4s + climate 5s + forecast 5s, sequential)
- On failure: Returns None → no adjustment. Non-fatal.

**Agent 4: Adjustment Merger (Rule-Based)**
- Input: packet_payload, validation_payload, decision_payload, live_checker
- Output: All three payloads mutated — score reduced, blockers extended, live_checker data attached
- Timeout: ~10ms
- On failure: Skip adjustments

Fragile merge algorithm: searches for base score across 4 possible fields (overall_score, quality_score, packet's quality_score, packet's score), falls back to hardcoded map based on decision_state. If none match, defaults to 70.

**Agent 5: Finding Selection & Event Logging**
- Input: decision_payload (post-adjustment), validation_payload, execution time
- Output: First hard/soft blocker selected → logged as first_credible_finding_shown
- Selection: primary_hard_blockers[0] → "must_fix", else primary_soft_blockers[0] → "should_review"

**The 5 Micro-Decisions Product B Must Get Right:**

1. **Credibility threshold:** Currently any non-empty blocker. Should be score_penalty >= 15, not len(blockers) > 0. Wet-season monsoon finding for June Singapore is obvious — is it credible or noise?
2. **Partial data output:** NB01 DEGRADE produces ASK_FOLLOWUP. Frontend must render these as inline form fields, not a "try again" error.
3. **Action packet structure:** Response has follow_up_questions, blockers — but no structured copyable brief the traveler can send to agent. The traveler_bundle from spine has user_message — use that.
4. **Open-Meteo failure:** If destination extractor regex fails on "SIN→NRT" (airport codes), traveler gets no location-specific findings. The regex `\bto\s+([A-Z][A-Za-z0-9&.'-]+` is the weakest link.
5. **First frame ordering:** First blocker shown matters. If weather shows first (obvious monsoon), traveler dismisses the tool. If cost shows first (realistic budget), they get value. Cost/policy findings should surface before weather.

**The thing most people miss about this:** The live checker runs AFTER the spine, not in parallel. A Singapore itinerary takes 18-30 seconds to return results. For a consumer tool, that's dangerously long. The fix: run live checker concurrently with spine — weather data is additive, not dependent on spine output. But the current architecture serializes them.

---

### 2.3 Skeptic

**Output: The Voice of Restraint**

**1. "More agents = better audit"** — FALSE.

Agent churn: each agent produces findings. Findings compete for attention. Traveler sees 12+ bullet points, reads none. Minimum viable count: 2. One for hard blockers (wrong season, visa expired). One for opportunity cost (you could go somewhere else for half). Everything else is noise until proven otherwise. Ship 2 finding types that are undeniable, then add.

**2. "Evidence-backed findings require LLM reasoning"** — FALSE.

Structured rules win for MVP. live_checks.py with Open-Meteo + heuristic scoring already produces high-signal findings with zero hallucination risk. Singapore in November is monsoon — that's a lookup, not an LLM insight. LLM failure modes: hallucinated hotel policies, invented visa rules, generic advice masquerading as specific. What should NOT be built: an LLM-based safety analysis agent. If it says "safe" and something happens, you're liable. If it says "unsafe" for a fine area, you look alarmist.

**3. "Travelers want detailed evidence"** — FALSE.

Travelers want a decision signal. "This plan has a problem" vs "this plan is fine." Evidence is for the moment they doubt you, not the moment they first see output. 60% of users scroll past findings to see "should I cancel this hotel?" One-line verdict first. Evidence collapsible. If a finding can't be stated in 15 words, it's not a finding.

**4. "The action packet needs to be forward-ready"** — TENSION.

Forward-ready means professional language. Professional means generic. Generic means agent glances for 2 seconds and says "yes that's fine." You lose differentiation. The whole point is specificity: "your Oct 12 flight to Changi arrives at midnight, no hotel check-in until 3pm with 2 toddlers." That's the wedge. Forward-ready corporate language is the opposite.

**5. "Multi-destination scaling needs more agents"** — FALSE.

Needs better data, not more agents. Singapore is one country, one visa policy, one climate. The agents you build for Singapore are country-specific data, not agent logic. Agent count doesn't scale with destinations. Data sources scale. One DestinationRulesEngine with per-country config files, not BaliCheckerAgent, TokyoCheckerAgent, ParisCheckerAgent.

**Failure modes:**

| Failure | Trigger | Why invisible |
|---------|---------|---------------|
| Noise drowns signal | >3 finding types | Users don't read audit |
| Hallucinated specificity | LLM generates wrong claim | Only caught when traveler acts on it |
| Buried verdict | Evidence before conclusion | 60% bounce after first scroll |
| Generic polish | Action packet sounds templated | Agency dismisses as fluff |
| Agent explosion | New country = new agent class | Unmaintainable at 5 destinations |

**What to build first:** One undeniable finding type (hard blocker — wrong season/wrong visa). One decision signal (green/yellow/red). Raw text output (no PDF, no branding). Destination data config (one file per country).

**The thing most people miss about this:** The real competitor isn't other audit tools — it's the traveler not opening the audit at all. The biggest risk is that your output looks like work they have to do, not a decision they can make. A 3-line verdict they read and act on beats a 30-page report they bookmark and forget.

---

### 2.4 Executioner

**Output: Kill Case**

**Verdict: KILL IT. Assuming the spine pipeline is available.**

The existing pipeline already does all of it — in one pass, at lower cost, with fewer moving parts.

**1. Wrong timing — the pipeline is already good enough.**

`run_spine_once()` already produces budget checking (via gap_and_decision), policy checking (via hybrid_engine rules), logistics checking (via timing rules, NB01), weather checking (via build_live_checker_signals against Open-Meteo), suitability checking (via assess_activity_suitability with 4 tiers), secondary audit (via CheckerAgent, 76 lines), safety/filtering (via sanitize_for_traveler, NB02). Every category a multi-agent architecture would "specialize" in is already covered by a single linear pipeline. Adding agents doesn't generate new signal — it re-packages existing signal with 5x latency and 5x failure surface.

**2. Premise collapses on first contact.**

Product B is a free wedge. The metrics already tell you what matters: time_to_first_credible_finding_ms, forward_without_edit, agency_revision_rate. The entire funnel is about speed to one credible signal. Multi-agent does the opposite — each agent needs its own extraction from wildly varying traveler inputs, each can fail independently, orchestration must handle partial failures, latency compounds linearly. Traveler inputs are unstructured garbage (pasted emails, 2-line descriptions, OCR noise). The current pipeline collapses this into a CanonicalPacket once. Multi-agent would either share extraction (defeating specialization) or each re-parse (multiplying hallucination and cost).

**3. Audience mismatch.**

The key event is first_credible_finding_shown — not "all findings from all agents." ONE. A traveler doesn't want a dashboard of 6 agent verdicts. They want "your plan has a problem with X." Product B is a lead generation wedge. Nobody converts because they saw a multi-agent dashboard. They convert because one finding made them think "I need professional help."

**4. Wrong approach — and already tried.**

The existing CheckerAgent is precisely the "second agent" pattern. It's 46 lines and already sufficient. The frontier orchestrator already runs LLM-based checks. The hybrid decision engine already has feature flags. What the system needs is better rules and data extraction, not more agents.

**5. Cost asymmetry.**

Product B is free. Every agent means another LLM call, another API call, another error handling path, another monitoring dashboard, more tests. For a pipeline that already produces all the same categories through a single pass.

**The right answer: make the existing single pipeline faster, better at extraction, and cheaper per run.** The "agents" are already there — they're just phases in a well-ordered pipeline, not distributed services with their own failure modes.

---

### 2.5 Cartographer

**Output: Views, Maps, and Grouping**

**Organizing Metaphor: Emergency Medical Diagnostic Clinic**

The itinerary is the patient. The audit is the workup. The action packet is the prescription.
- Triage (gate): is this a real case?
- Primary Care (spine pipeline): comprehensive workup
- Specialists (live checks, checker agent): parallel consults
- Attending (public_checker_service): synthesizes all consults
- Discharge (action packet): prescription + follow-up

**Flow:**
```
INTAKE → TRIAGE → FAN-OUT (3 parallel) → MERGE → PACKET
```

Total elapsed time = max(spine_ms, live_ms, checker_ms) + merge overhead. No chain dependency between agents.

**Zoom levels:**

*Bird's eye:* Intake → normalizes → three parallel agents (spine, live checks, checker) → merge + dedup → rank findings → build packet → output.

*Per-agent:* Each agent has internal sequential pipeline. Spine: extract → validate → classify → decide. Live: geocode → weather → seasonality → flag. Checker: budget → risk → confidence.

*Per-finding:* raw data → extracted → enriched → evidence → finding → merged. Every finding carries a provenance chain.

**Navigation / "You Are Here":**
Frontend progress bar: `[Intake ✓] [Analyzing ···] [Checking Weather ···] [Building Report ⬜]`
Per-finding breadcrumb: `Heat Warning (Venice) └─ Evidence: OpenMeteo data └─ Source: Live Weather └─ Confidence: 0.78`

**Branching:** Agent level = parallel (no agent depends on another). Within agent = sequential. Merge = sequential (must wait for ALL). Ranking = sequential (after dedup). Key invariant: No agent reads another agent's output.

**Boundaries:**

| Condition | Behavior |
|-----------|----------|
| Spine timeout (5s) | Return partial, mark incomplete |
| Live check timeout (3s) | Omit weather, packet still valid |
| Checker timeout (5s) | Omit budget/risk, return spine only |
| All timeout | Return error with retry button |
| Gate reject | Return immediately with explanation |
| Partial data | Run on available data, flag gaps |
| Zero findings | "Your itinerary looks solid" |

**The thing most people miss about this:** The merge layer is harder than any single agent. Each agent independently produces findings in its own schema, with its own confidence scale, its own naming conventions. Two agents can flag "Venice in August" — one as heat, one as overcrowding — and if you concatenate, user gets two separate cards saying the same thing. The merge layer must normalize entities, detect convergent findings, and fuse evidence chains. The agent architecture is straightforward; the synthesis architecture is where the product earns its trust.

---

### 2.6 Trickster

**Output: Whimsical Reframes**

**Ship's Bridge:**
Captain = traveler. Navigator = orchestrator. Lookout = weather checker. Chief Engineer = logistics checker. Ship's Purser = budget checker. Passenger Manifest = suitability checker.
Reveals: Alarm hierarchy is life-or-death. Findings must carry severity flags that restructure output — a visa issue preempts everything. Weather checker shouldn't just say "rain" — say "reschedule outdoor day 3." Output recommendations, not just observations.

**Restaurant Kitchen:**
Chef = synthesis layer. Expediter = scheduler. Stations = agents prepping independently. The pass = output wall. The ticket = the itinerary.
Reveals: Mise en place — agents run in parallel but timing of assembly is magic. You don't serve dessert before main course — don't tell about hotel cost before establishing destination is suitable. The ticket is canonical source of truth. All agents must receive the SAME normalized representation.

**Detective's Evidence Board:**
The crime = "will this trip be a disaster?" Evidence board covered in findings, red string between them.
Reveals: Evidence without narrative is noise. Need a cross-agent synthesis step: "Weather + Suitability individually say nothing, but together they say 'rain on day 3 + toddler can't handle wet trails = swap activity.'" Explicit contraindication detection step.

**Jazz Session:**
Bandleader = orchestrator. Rhythm section = policy + budget (steady). Horns = weather + suitability (improvisational). Trading fours = back-and-forth on ambiguous findings. The head = itinerary stated at start, restated at end with new meaning.
Reveals: Worst thing is playing too loud during someone else's solo. Orchestration layer needs to listen dynamically and adjust the mix. Presentation in flexible priority order, not fixed template.

**⭐ Medical Diagnostic (MOST USEFUL):**
- Vitals: Policy checker (visa, entry requirements)
- History: Itinerary itself
- Labs: Budget checker
- Imaging: Suitability
- Differential Diagnosis: Ranked failure modes
- Treatment Plan: Action packet

**Reveals 6 non-obvious requirements:**
1. Problem lists merged and ranked by severity + treatability, not per-agent. P0 = both severe AND actionable.
2. Contraindications are a first-class architectural step. Cross-agent interaction scan: "Weather says rain day 3. Suitability says activity needs dry. Together: swap this activity."
3. Vital signs vs diagnostic tests: Vitals always-on (budget, logistics). Diagnostics conditionally triggered (suitability only for certain parties, policy only for certain destinations). Continuous vs conditional scheduling.
4. Differential diagnosis changes treatment priority. Same finding gets different priority based on other findings. Synthesis layer must re-rank after collecting ALL agents.
5. Follow-up is a design parameter. Packet should include "after changing X, re-run Y." Iterative/recursive re-evaluation.
6. Patient is dynamic. Treatment changes state. Accept modified itinerary, re-check only affected agents. Caching + delta-checking: if only day 3 changed, don't re-run visa checker.

---

### 2.7 Future Self

**Output: May 2027, Product B has been live for 12 months**

**Agent Architecture Evolution:**

*Removed:* Weather Agent — absorbed into Risk. Weather alone had zero actionability (nobody cancels a safari because Day 4 has 30% rain). What mattered was compound risk: weather + transportation mode + refund policy = real exposure.

*Merged:* Budget + Suitability + Policy → Alignment Agent. Travelers don't think in those categories. They think "does this trip work for me?" Collapsed finding count by 60%, improved packet-share by 2x.

*Added:*
- **Contradiction Agent** — internal itinerary consistency. Hotel checkout ≠ flight departure. Timezone-naive connections. Addresses 90 minutes apart called "nearby."
- **Hidden Cost Agent** — dynamic pricing traps, currency conversion losses, resort fees, "free" transfers requiring specific flight times. Only surfaces items >$50 impact.
- **Negotiation Leverage Agent** — for each finding, generates specific action the agent can take (rebook, upgrade, price match) with dollar estimate. Bridge from audit to Product A.
- **Preference Gap Agent** — cross-references against inferred preferences from past behavior. A traveler who always books airport hotels doesn't want "charming local B&B."

**The Data Surprise That Changed Architecture:**

The packet share → Product A interest path was backwards. We assumed: traveler shares → traveler convinces agent → agent sees value → agency buys Product A. Data showed the opposite: the AGENT initiated Product A conversations — but only after receiving 3+ audit packets from DIFFERENT clients within 7 days. The agent experienced a workflow problem: "I have 7 audit packets and no system to manage them."

Architecture change: Added packet_inbox_agent on agency side. When agent receives 3+ packets, surfaces "you're managing this manually — here's what Product A would do." Self-qualifying lead, 40% conversion.

Second surprise: "Forward without edit" was the HIGHEST-intent signal. Users who forwarded unedited packets had 2.3x higher pull-through. They used the packet as conversation starter, not final product.

**Leapfrog: The Agent Handshake Protocol**

Skip human-forwarded-packet entirely. Build protocol: traveler's AI agent (Product B) and travel agent's AI agent (Product A) communicate directly.
1. Traveler uploads itinerary
2. Product B audits, generates findings + negotiation positions
3. Product B calls Product A webhook: `POST /negotiate`
4. Product A checks CRM, inventory, contracts — responds accept/counter/reject per finding
5. Humans only see resolution summary, not the negotiation

Collapses 4-day revision cycle to 90 seconds. Product is the resolution, not the packet.

**Assumptions That Stopped Mattering:**

| Assumption | Reality at Month 12 |
|------------|---------------------|
| Itinerary is ground truth | Itinerary is first draft. Ground truth is what traveler actually wants |
| Traveler is the customer | Traveler is user. Agency is customer. Product A sells to agencies |
| More findings = more value | 3 actionable > 12 informative |
| Weather is core feature | Weather is table stakes. Implicit risk is the feature |
| Agents will feel threatened | Top agents loved it — gave them reason to call clients, showed proactivity |

**Month 12 Output vs Month 0:**
Month 0 (checklist): Weather, Budget, Suitability, Policies — passive.
Month 12 (decision-support): PRIORITY with dollar estimates, agent-ready scripts, NEGOTIATION STATUS with resolution tracking. Already partially resolved before human sees it.

---

### 2.8 Champion

**Output: First-Principles Case for Multi-Agent Architecture**

**1. Why agents beat monolithic pipelines.**

The spine produces three outputs (validation, packet, decision_state) in one opaque pass. Bug in visa heuristic bloats weather cache. Suitability logic change requires full pipeline retest. Prompt tweak for "does this make sense for a family?" can degrade city extraction.

With decoupled agents: test each in isolation, swap strategies per agent (weather → heuristic, suitability → LLM, visa → hybrid), measure drift per agent — know WHICH agent degraded. Monolithic pass becomes untunable because there's no isolation boundary.

**2. Why prompt-based agents complement heuristic checks.**

| Aspect | Best approach | Why |
|--------|--------------|-----|
| "Will it rain in Tokyo Wednesday?" | Heuristic (API) | Deterministic, factual |
| "45min connection at LHR clear customs?" | Heuristic + rule | Known policy, computable |
| "14-city Europe trip in 10 days with toddler?" | LLM agent | Ambiguous, requires judgment |
| "Hotel rate suspiciously good for Zermatt in Feb?" | LLM agent | Pattern recognition, vibe check |
| "Booking reference format valid?" | Heuristic (regex) | Simple pattern match |

Heuristic agents run first, fast, free. LLM agents fire only when signal is genuinely ambiguous. Cost controlled by heuristic pre-screening. Confidence layering: heuristic = high confidence (use unconditionally). LLM = carry uncertainty. Graceful degradation: if LLM API is down, heuristics still produce findings.

**3. Why the wedge needs this NOW.**

The wedge dies on finding quality. Not speed. Not feature count. Whether findings are good enough that user says "that's actually useful."

Math: 100 first users, 1 itinerary each, 5-8 findings each. If 1 in 5 is wrong, trust drops below threshold. Trust below threshold = no sharing, no return, no word-of-mouth. Wedge requires ~1,000 active users to generate data. 100 × 0.3 retention = 30 returning users. Not enough.

Agent architecture is trust insurance. Each finding's confidence traces to specific agent/prompt. Wrong finding = know exactly which to fix, without touching others. Monolithic blob of findings with no provenance = can't debug, can't improve incrementally.

**4. What would make this wrong:**

| Condition | What it would prove |
|-----------|---------------------|
| Users only need 2-3 heuristic finding types | Monolithic pipeline with rules is sufficient |
| LLM experiments <50% precision on ambiguous cases after 200 test cases | LLM agents premature — stick to heuristics |
| Agent architecture ships but prompt quality is bad | Worst of both worlds — complexity without quality gain |
| Feedback loop broken — users don't rate/contest/return | Can't improve per-agent performance → agents provide no advantage |
| Team spends >3 weeks on infrastructure instead of shipping findings | Validates Executioner's overengineering concern |

**The thing most people miss about this:** Multi-agent for a free consumer tool isn't about scale or extensibility — it's about debuggability and trust recovery. Every finding a user flags as wrong must trace to a specific agent, prompt, and input. Without agent boundaries, you cannot recover trust incrementally. The architecture's primary value isn't the happy path — it's what happens when things go wrong, which they will, frequently, in the first 100 itineraries.

---

## 3) Champion vs. Executioner Arbitration

### Champion's Strongest Case (3-5 bullets)

1. **Debugability is non-negotiable for trust recovery.** A traveler who gets one wrong finding from a monolithic pipeline stops using the tool forever because you can't fix the specific problem without risking regression elsewhere. With agents, each finding's provenance pinpoints the fix.

2. **Heuristic-LLM boundary creates cost control.** Not "add LLM everywhere" but "heuristic first, LLM for ambiguity." The cost of running 5 rule-based enrichers is near-zero. The 1-2 LLM calls that remain are the minimum needed for judgments heuristics can't make.

3. **The wedge lives or dies on finding quality.** Not on speed, scope, or feature count. The first finding shown determines whether the user forwards or bounces. Agents let you optimize per-finding-type quality independently.

4. **The architecture scales through data, not code.** With agents, adding Thailand isn't "build ThailandCheckerAgent" — it's "add Thailand enrichment data." Same agents, new data.

5. **When BE arrives, agents become fallback.** Not "replace agents with spine" but "pick the higher quality path per input." This is the hybrid architecture the Future Self described.

### Executioner's Strongest Kill Case (3-5 bullets)

1. **The pipeline already does everything.** budget checking, policy checking, logistics checking, weather checking, suitability checking, secondary audit, safety filtering — all in one pass at lower latency.

2. **Latency kills consumer products.** 6 agents × 2-5s each = 12-30s total vs current 3-5s. Travelers navigate away before findings appear.

3. **Cost compounds linearly with agent count.** Free product with per-agent LLM calls means each agent is a money pit. At scale, 6 LLM agents per request is unsustainable.

4. **Traveler inputs are unstructured garbage.** Parser handles this once in the pipeline. Multi-agent either shares extraction (defeating specialization) or each re-parses (multiplying hallucination).

5. **The "specialization" categories are already covered.** cost/policy/logistics/suitability — all have existing code paths with matching and classification.

### What Evidence Would Make Each Side Concede?

**Champion concedes if:** LLM agent experiments show <50% precision on ambiguous cases after 200 test cases. Or if first 100 real users only engage with 2 finding types (both already handled heuristically). Or if team spends >3 weeks on infrastructure without shipping.

**Executioner concedes if:** The spine pipeline is NOT available at launch (which is the new constraint). Or if heuristic-only findings fail to produce sufficient share/revision behavior in first 50 users. Or if user research shows travelers want cross-destination reasoning that the spine doesn't produce.

### Converted to Build Conditions

**Proceed now (build LLM agents as primary) if:** The spine pipeline is NOT available for public consumption. The LLM agents are the only path to launch.

**Prototype first (build both paths) if:** The spine IS available but quality uncertain. Run both, compare, iterate.

**Pause or kill (use spine only) if:** The spine is stable, fast, and produces high-quality findings that match user needs. LLM agents add no signal.

---

## 4) Cross-Pollination Round

**Roles independently converged on:**
- Heuristic first, LLM second
- Maximum 3-7 findings, not 12+
- Packet agent targets the agent's reaction, not just the traveler's
- Enrichment is rule-based, not LLM-based
- Parallel where possible, sequential where necessary

**Roles disagreed on:**
- Agent count: anywhere from 2 (Skeptic) to 8+ (Operator) to 4 (Strategist) to "kill them all" (Executioner)
- Whether to build now or wait for BE

---

## 5) "Launch Now Without BE" — Full Design

After the initial brainstorm, a new constraint was introduced: **launch Product B NOW, before the Product A backend/spine pipeline is ready.** The LLM-based agentic architecture IS the primary path. The spine becomes a fallback/optimization later.

### Design Constraints

1. No dependency on spine pipeline. Agents must work without `run_spine_once()`.
2. No agency-side infrastructure. Traveler-facing only.
3. LLM calls are the primary reasoning engine. Heuristics supplement.
4. Time-to-first-finding < 30s. Must appear before traveler navigates away.
5. Findings must be forwardable without edit. The action packet IS the wedge.
6. Every agent can fail independently. Product still works.

### Agent Roster (Launch Mode)

| Agent | Type | Purpose | Depends On |
|-------|------|---------|------------|
| ParserAgent | LLM | Raw text → structured TripIntent | Nothing |
| EnrichmentLayer | Rule/API | Per-destination data (weather, holidays, cost, safety) | ParserAgent |
| AnalysisAgent | Hybrid | Findings from TripIntent + EnrichmentData | EnrichmentLayer |
| PacketAgent | LLM | Findings → forward-ready action packet | AnalysisAgent |

### Data Flow

```
Raw Text
  │
  ▼
ParserAgent (LLM call #1) ──► TripIntent {destinations, dates, party, budget, purpose}
  │
  ▼
EnrichmentLayer (5 parallel rule/API calls)
  │  WeatherEnricher | HolidayEnricher | CostEnricher | SafetyEnricher | VisaEnricher
  ▼
AnalysisAgent
  │  Phase A: Heuristic rules (weather severity, budget mismatch, visa missing, holiday conflict, overpacked)
  │  Phase B: LLM call #2 (cross-destination reasoning, hidden risks, opportunity cost)
  ▼
Ranked Findings[] + overall_assessment (green/yellow/red)
  │
  ▼
PacketAgent (LLM call #3) ──► ActionPacket {subject, body, findings, ask_your_agent}
  │
  ▼
Frontend: Findings + Forward-Ready Packet
```

Total: 3 LLM calls, ~15-25s end-to-end.

### ParserAgent Prompt

```
You are a travel itinerary parser. Extract structured data from the following itinerary text.

Rules:
1. Extract ALL destinations mentioned. If ambiguous (e.g., "Georgia"), include both.
2. Extract date windows, even partial ("mid-June" → approximate to June 15).
3. Extract party composition. If not explicit, note as "unknown" not "1 adult."
4. Extract budget from any mention of money, price, or cost.
5. If text mentions purpose (wedding, business conference), extract it.

Output ONLY valid JSON. If a field cannot be determined, set to null (never invent).

Itinerary text:
{raw_text}
```

### AnalysisAgent Prompt (LLM phase only — after heuristics)

```
You are a travel audit analyst. Given a structured trip plan and enrichment data, identify findings that a travel expert would spot but a casual traveler might miss.

Trip details: {destinations} | {dates} | {party_size} | {budget} | {purpose}
Enrichment data per destination: {enrichment_json}
Existing rules-based findings (DO NOT duplicate): {heuristic_findings}

Rules:
1. ONLY surface findings a traveler would not discover by reading a guidebook.
2. Focus on CROSS-DESTINATION interactions (budget + routing, timing + holidays, party + itinerary).
3. Each finding must be specific and actionable ("connection at LHR is tight" not "be careful").
4. Include EXACT QUESTION for traveler to ask agent.
5. If you cannot find a non-obvious finding, output nothing for that dimension.
6. Never invent policy, visa, or safety claims. Use only the enrichment data.
7. Confidence < 0.6 means uncertain — surface lower.

Output findings as JSON: [{ severity, category, message, ask_agent, confidence: float 0-1 }]
```

### PacketAgent Prompt

```
You are a travel packet composer. Take audit findings and compose a forward-ready message that a traveler can copy-paste to their travel agent.

Requirements:
1. The SUBJECT line must make the agent want to open it.
2. The BODY must be professional, specific, and actionable.
3. Each finding must include "ask your agent" question.
4. Tone is helpful, not adversarial — traveler and agent are on the same team.
5. Organized as: assessment summary → key findings → what to ask.

Trip: {destinations} | {dates} | {party_size}
Overall assessment: {overall_assessment}
Findings: {findings_json}

Output JSON: { subject, body, findings: [{ severity_label, message, detail, ask_your_agent }] }
```

### Launch Mode Orchestration

```
POST /api/public-checker/run
├── 1. Create session_id, inquiry_id
├── 2. Log intake_started event
├── 3. Run ParserAgent (LLM call #1)
│   └── On parse error: "Could not parse. Try including destinations and dates."
├── 4. Run EnrichmentLayer (5 parallel API calls, 5s timeout each)
│   └── On fail: continue with null enrichment
├── 5. Run AnalysisAgent (heuristic rules + LLM call #2)
│   └── On LLM fail: return heuristic findings only
├── 6. Log first_credible_finding_shown event
├── 7. Run PacketAgent (LLM call #3)
│   └── On LLM fail: return raw findings without packet body
├── 8. Return response
└── Total: ~15-25s
```

### LLM Cost Analysis (Launch Mode)

| Call | Provider | Input Tokens | Output Tokens | Cost/Req |
|------|----------|-------------|---------------|----------|
| ParserAgent | Claude 3.5 Sonnet | ~300 | ~200 | ~$0.002 |
| AnalysisAgent (LLM) | Claude 3.5 Sonnet | ~800 | ~400 | ~$0.005 |
| PacketAgent | Claude 3.5 Sonnet | ~600 | ~500 | ~$0.005 |
| **Total** | | **~1,700** | **~1,100** | **~$0.012** |

At 1,000 audits/month: ~$12. At 10,000/month: ~$120.

### What Changes When BE Arrives

| Component | Launch (LLM only) | Hybrid (BE available) |
|-----------|-------------------|----------------------|
| Parser | LLM call | Spine's extraction pipeline |
| Enrichment | API + static data | Same — unchanged |
| Analysis (heuristic) | Rules from this doc | Spine's validation + decision |
| Analysis (LLM) | Full LLM reasoning | Reduced scope (cross-destination only) |
| Packet | Same | Same |
| Router | Not present | HybridGate picks best path |

LLM agents NEVER disappear. They become fallback, supplement, and rapid-iteration path.

---

## 6) Convergence / Synthesis

### Where roles independently converged

| Idea | Roles agreeing | Signal strength |
|------|----------------|-----------------|
| Heuristic-first, LLM-supplement pattern | Strategist, Champion, Cartographer, Skeptic, Executioner | 🔴🔴🔴🔴🔴 |
| Max findings 3-7, not 12+ | Skeptic, Strategist, Future Self, Cartographer | 🔴🔴🔴🔴 |
| Packet targets agent reaction, not just traveler | Strategist, Champion, Cartographer | 🔴🔴🔴 |
| Enrichment is rule-based, not LLM | Every role | 🔴🔴🔴🔴🔴🔴 |
| Parallel where possible for latency | Operator, Cartographer, Champion | 🔴🔴🔴 |
| Cross-destination reasoning is the differentiator | Future Self, Trickster, Champion | 🔴🔴🔴 |
| Agent boundaries for debugability | Champion, Strategist, Cartographer | 🔴🔴🔴 |

### Strongest contradictory positions

| Position A | Position B | Resolution |
|------------|------------|------------|
| Ship 2 agents (Skeptic) | Ship 4+ agents (Strategist, Champion) | Start with 4, but launch with 2 finding types, add weekly |
| Kill multi-agent (Executioner) | Build multi-agent now (Champion) | Kill IF spine available. Proceed since spine ISN'T available |
| 4 separate LLM calls (Strategist) | 1 monolithic call (Skeptic) | 3 calls (parse, analyze, packet) — balanced |
| Sequential agents (Operator) | Parallel agents (Cartographer) | Parallel at agent level, sequential within each agent |

### Decisions required NOW

1. **Launch with 4 agents:** ParserAgent → EnrichmentLayer → AnalysisAgent → PacketAgent. (Resolution: converged after launch-now constraint.)
2. **Output contract:** Each finding includes severity, rationale, confidence, evidence pointer, exact question for agent. (Resolution: all roles converge.)
3. **Measurement contract:** Instrument share rate, revision rate, Product A pull-through via existing 8-event schema. (Resolution: already implemented.)
4. **Risk posture:** Legal-safe language templates. No LLM-generated visa/safety claims — enrichment data only. (Resolution: Skeptic + Executioner forced this.)
5. **Cost discipline:** Max 3 LLM calls per audit. Cached enrichment data per destination per season. (Resolution: Champion + Executioner converge.)

---

## 7) Six-Hat Coverage Check

| Hat | Coverage | Notes |
|-----|----------|-------|
| **White** (facts/data) | ✅ Strong | Full codebase exploration, all existing agents/endpoints documented, exact file paths and line counts |
| **Yellow** (optimism/value) | ✅ Strong | Champion's first-principles case, Future Self's 12-month vision, Strategist's wedge thesis all covered |
| **Black** (risks/failures) | ✅ Strong | Executioner's full kill case, Skeptic's 5 failure modes, latency and cost risks explicitly surfaced |
| **Green** (creative alternatives) | ✅ Strong | Trickster's 5 metaphors (Medical Diagnostic was genuinely architecturally useful), Cartographer's organizing metaphor |
| **Red** (taste/emotion) | 🟡 Partial | Trickster touched on emotion through metaphor but no dedicated Customer Whisperer role. Would benefit from explicit user emotional journey mapping |
| **Blue** (facilitation/next steps) | ✅ Strong | Build conditions table, convergence summary, open questions, and next implementation move all documented |

---

## 8) Build Conditions

| Condition | Action | Evidence to change |
|-----------|--------|---------------------|
| Spine NOT available | BUILD LLM agents as primary (proceed) | Spine becomes available + passes quality checks |
| Spine available + passes quality | USE SPINE primary, LLM fallback (prototype) | Spine degrades on real inputs |
| Spine available + degrades often | KEEP LLM primary, spine as structured data source (prototype) | Spine improves |
| First 50 real users ignore findings | KILL Product B wedge (pause) | Finding quality improves through prompt iteration |
| Share rate >10% + revision rate >5% after 200 users | SCALE traffic (proceed) | Metrics degrade at scale |

---

## 9) Reusable Prompt Templates

### ParserAgent Seed
```
You are a travel itinerary parser. Extract structured data from the following itinerary text.

Rules:
1. Extract ALL destinations mentioned. If ambiguous, include possibilities with confidence.
2. Extract date windows, even partial ones. Approximate when only season is known.
3. Extract party composition. If not explicit, note as "unknown" — never default to "1 adult."
4. Extract budget from any mention of money, price, or cost.
5. Extract purpose if mentioned (wedding, business, family visit).
6. Output ONLY valid JSON. Set undetermined fields to null. Never invent values.

Itinerary text: {raw_text}
```

### AnalysisAgent Seed (LLM phase)
```
You are a travel audit analyst. Identify findings a travel expert would spot but a casual traveler might miss.

Trip: {destinations} | {dates} | {party_size} | {budget} | {purpose}
Per-destination data: {enrichment_json}
Existing rule-based findings (DO NOT duplicate): {heuristic_findings}

Rules:
1. Surface only findings not discoverable by reading a guidebook.
2. Focus on CROSS-DESTINATION interactions and hidden risks.
3. Each finding must be specific and actionable. Include exact question for agent.
4. If you cannot find a non-obvious finding, output nothing. Silence is acceptable.
5. Never invent policy, visa, or safety claims. Use provided data only.
6. Confidence < 0.6 = uncertain — surface lower in priority.

Output JSON array: [{ severity: "must_fix|should_review|good_to_know", category: "string", message: "string (15 words max)", ask_agent: "string", confidence: float 0-1 }]
```

### PacketAgent Seed
```
You are a travel packet composer. Turn audit findings into a forward-ready message the traveler copy-pastes to their agent.

Trip: {destinations} | {dates} | {party_size}
Assessment: {overall_assessment}
Findings: {findings_json}

Requirements:
1. Subject line makes the agent want to open it. Under 60 characters.
2. Body is professional, specific, actionable. Not adversarial.
3. Each finding includes "ask your agent" question in traveler's voice.
4. Organized: assessment summary → key findings → what to ask.
5. The tone makes the receiving agent think "the tool that produced this is worth paying for."

Output JSON: { subject: str, body: str, findings: [{ severity_label: str, message: str, detail: str, ask_your_agent: str }] }
```

---

## 10) Artifact Summary

**Document:** `Docs/brainstorm/PRODUCTB_AGENT_ARCH_WIDE_OPEN_BRAINSTORM_2026-05-08.md`

**Contains:**
- Seed brief + codebase context
- 8 individual role outputs (complete, unedited)
- Champion vs Executioner arbitration with build conditions
- Cross-pollination (convergence + disagreements)
- "Launch now without BE" full design with per-agent prompts, I/O contracts, cost analysis
- Convergence / synthesis table
- Six-hat coverage check
- Build conditions table
- Reusable prompt templates for ParserAgent, AnalysisAgent, PacketAgent

**Status:** DONE (all sections written, all role outputs captured, full discussion documented)
