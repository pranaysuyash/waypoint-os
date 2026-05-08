# Product B Agent Architecture — Launch-Now Design (2026-05-08)

## Premise

Product B launches **before** the Product A backend/spine pipeline is ready for public consumption. The LLM-based agentic architecture is the **primary path** — the spine pipeline (when ready) becomes a fallback/optimization.

This document defines: the agents, their prompts, I/O contracts, orchestration flow, and how the architecture evolves when the BE is ready.

---

## Design Constraints

1. **No dependency on spine pipeline.** Agents must work without `run_spine_once()`.
2. **No agency-side infrastructure.** Traveler-facing only. No agency users, no agency settings.
3. **LLM calls are the primary reasoning engine.** Heuristics supplement, not replace.
4. **Time-to-first-finding < 30s.** First finding must appear before the traveler navigates away.
5. **Findings must be forwardable without edit.** The action packet is the wedge.
6. **Fail gracefully.** Every agent can fail independently. The product still works.

---

## Agent Roster

### Phase 1: Launch Agents (ship now)

| Agent | Type | Purpose | Depends On |
|-------|------|---------|------------|
| ParserAgent | LLM | Raw text → structured TripIntent | Nothing |
| EnrichmentLayer | Rule/API | Per-destination data (weather, holidays, cost, safety) | ParserAgent |
| AnalysisAgent | LLM | Findings from TripIntent + EnrichmentData | EnrichmentLayer |
| PacketAgent | LLM | Findings → forward-ready action packet | AnalysisAgent |

### Phase 2: When BE Is Ready (spine pipeline available)

| Agent | Type | Purpose | Depends On |
|-------|------|---------|------------|
| SpinePipeline | Full pipeline | Extraction → Validation → Decision | BE ready |
| HybridGate | Router | Choose primary path (spine vs LLM) based on quality | Both paths |

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        LAUNCH MODE (LLM primary)                │
│                                                                  │
│  Raw Text                                                        │
│    │                                                             │
│    ▼                                                             │
│  ParserAgent ──► TripIntent                                      │
│    │                                                             │
│    ▼                                                             │
│  EnrichmentLayer ──► EnrichmentData[]                            │
│    │  (parallel: weather / holidays / cost / safety / routing)   │
│    ▼                                                             │
│  AnalysisAgent ──► Ranked Findings[]                             │
│    │                                                             │
│    ▼                                                             │
│  PacketAgent ──► ActionPacket (forward-ready)                    │
│    │                                                             │
│    ▼                                                             │
│  Frontend: Findings + Packet                                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                                                                 
┌─────────────────────────────────────────────────────────────────┐
│                    HYBRID MODE (BE available)                    │
│                                                                  │
│  Raw Text                                                        │
│    ├─────► SpinePipeline (primary if high quality)               │
│    └─────► LLM Agents (fallback if spine degrades)              │
│                     │                                            │
│                     ▼                                            │
│              HybridGate: compare quality, pick best              │
│                     │                                            │
│                     ▼                                            │
│              PacketAgent (on chosen findings)                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Agent Definitions

### 1. ParserAgent

**Purpose:** Convert raw unstructured itinerary text into a structured TripIntent. Single LLM call. No chain-of-thought.

**Type:** LLM (3.5 Sonnet or equivalent, ~250 input tokens, ~200 output tokens)

**Input contract:**
```json
{
  "raw_text": "string — traveler's paste or extracted text from upload",
  "input_mode": "freeform_text | upload | mixed"
}
```

**Output contract (TripIntent):**
```json
{
  "destinations": [
    {"name": "string", "country": "string | null", "days": "int | null"}
  ],
  "date_window": {
    "start": "YYYY-MM-DD | null",
    "end": "YYYY-MM-DD | null",
    "season": "spring | summer | fall | winter | null"
  },
  "party": {
    "total": "int | null",
    "adults": "int | null",
    "children": "int | null",
    "elders": "int | null"
  },
  "budget": {
    "raw": "string | null",
    "band": "budget | mid | premium | luxury | null",
    "currency": "string | null"
  },
  "purpose": "leisure | business | family_visit | wedding | medical | honeymoon | adventure | null",
  "confidence": {
    "destinations": "float 0-1",
    "dates": "float 0-1",
    "party": "float 0-1"
  }
}
```

**Error handling:**
- If `destinations` is empty: return error — cannot proceed. Ask for destination.
- If `destinations` is populated but `dates` is null: proceed with "unknown season" enrichment.
- If `party` is null: default to 2 adults.

**Prompt:**
```
You are a travel itinerary parser. Extract structured data from the following itinerary text.

Rules:
1. Extract ALL destinations mentioned. If a city name is ambiguous (e.g. "Georgia"), include both possibilities with a confidence score.
2. Extract date windows, even partial ones ("mid-June" → approximate to June 15; "summer 2026" → June-August).
3. Extract party composition. If not explicit, note it as "unknown" not "1 adult".
4. Extract budget information from any mention of money, price, cost, or budget.
5. If the text mentions purpose (wedding, honeymoon, business conference), extract it.

Output ONLY valid JSON. No other text. If a field cannot be determined, set it to null (never invent values).

Itinerary text:
{raw_text}
```

---

### 2. EnrichmentLayer

**Purpose:** Add per-destination factual data that the AnalysisAgent needs. Not an LLM — API lookups and static data.

**Type:** Rule-based / API. 5 parallel sub-enrichers.

**Input:** `TripIntent` (from ParserAgent)

**Output (EnrichmentData[]):**
```json
{
  "destinations": [
    {
      "name": "string",
      "weather": {
        "risk": "low | medium | high | null",
        "summary": "string | null",
        "source": "open-meteo"
      },
      "season": {
        "peak": "bool",
        "shoulder": "bool",
        "off": "bool",
        "description": "string"
      },
      "holidays": [
        {"name": "string", "date": "YYYY-MM-DD", "type": "public | cultural | festival"}
      ],
      "cost_band": "budget | mid | premium | luxury",
      "currency_code": "string",
      "safety": {
        "advisory_level": "normal | exercise_caution | avoid | null",
        "source": "string"
      },
      "visa": {
        "required_for": ["string — nationality"],
        "processing_time_days": "int | null"
      },
      "airport_codes": ["string"],
      "timezone": "string",
      "language": "string"
    }
  ]
}
```

**Sub-enrichers (all parallel, any can fail independently):**

| Sub-enricher | Data Source | Timeout | On Failure |
|-------------|-------------|---------|------------|
| WeatherEnricher | Open-Meteo API | 5s | Skip weather enrichment |
| HolidayEnricher | Static holiday DB per country | 500ms | Skip holiday enrichment |
| CostEnricher | Static cost-band map per country | 200ms | Default to "mid" cost band |
| SafetyEnricher | Static advisory map per country | 200ms | Skip safety enrichment |
| VisaEnricher | Static visa policy map | 500ms | Skip visa enrichment |

**Error handling:** Each enricher is independent. If Open-Meteo times out, weather fields are null but the AnalysisAgent still gets cost, safety, and holiday data. The merge is simple: collect all non-null enrichments into a unified per-destination object.

---

### 3. AnalysisAgent

**Purpose:** Produce evidence-backed findings from the enriched trip intent. Two phases: heuristic first, then LLM.

**Type:** Hybrid (heuristic rules + LLM)

**Input:** `TripIntent` + `EnrichmentData[]`

**Output (Ranked Findings[]):**
```json
{
  "findings": [
    {
      "id": "uuid",
      "severity": "must_fix | should_review | good_to_know",
      "category": "cost | suitability | logistics | policy | timing",
      "message": "string — 1 sentence, actionable",
      "evidence": {
        "type": "weather_api | cost_data | visa_policy | llm_reasoning",
        "detail": "string — what the evidence says",
        "confidence": "float 0-1"
      },
      "ask_agent": "string — exact question for traveler to ask their agent",
      "llm_reasoned": "bool"
    }
  ],
  "overall_assessment": "green | yellow | red"
}
```

**Phase A: Heuristic rules (runs first, fast, deterministic)**

| Rule | Trigger | Output Severity | Category |
|------|---------|----------------|----------|
| Weather severity | Enrichment shows extreme weather during travel window | should_review | timing |
| Budget mismatch | Cost band + duration exceeds stated budget band | should_review | cost |
| Visa missing | Traveler nationality needs visa, no visa mentioned | must_fix | policy |
| Holiday conflict | Major holiday during trip (crowds, closures) | good_to_know | timing |
| Overpacked itinerary | Destinations + days ratio > 1.5 cities/week | should_review | logistics |

**Phase B: LLM reasoning (runs after heuristics, on enriched data)**

The LLM prompt is designed to **complement** — not duplicate — the heuristic findings. It focuses on:
1. Cross-destination interactions the rules miss
2. Suitability judgments (is this trip right for this party?)
3. Hidden risks (non-obvious problems an expert would spot)
4. Opportunity cost (what they could do instead)

**Prompt:**
```
You are a travel audit analyst. Given a structured trip plan and enrichment data, identify findings that a travel expert would spot but a casual traveler might miss.

Trip details:
{destinations}
{dates}
{party_size}
{budget}
{purpose}

Enrichment data per destination:
{enrichment_json}

Existing rules-based findings (DO NOT duplicate):
{heuristic_findings}

Rules for new findings:
1. ONLY surface findings that a traveler would not discover by reading a guidebook.
2. Focus on CROSS-DESTINATION interactions (budget + routing, timing + holidays, party + itinerary).
3. Each finding must be specific and actionable — "the connection at LHR is tight" not "be careful with connections."
4. Include the EXACT QUESTION the traveler should ask their agent.
5. If you cannot find a non-obvious finding, output nothing for that dimension.
6. Never invent policy, visa, or safety claims. Only use the enrichment data provided.
7. Confidence < 0.6 means "uncertain — surface lower in the list."

Output findings as JSON array. Each finding: { severity, category, message, ask_agent, confidence: float 0-1 }
```

**Merge strategy (critical):**
1. Heuristic findings get priority (higher confidence, deterministic).
2. LLM findings get inserted at their severity level.
3. Dedup by normalized message text (fuzzy match on edit distance < 0.3).
4. Max 7 findings total. If more, keep top 5 + "N more findings" collapse.
5. `overall_assessment` = 
   - `red` if any `must_fix`
   - `yellow` if any `should_review` and no `must_fix`
   - `green` otherwise

---

### 4. PacketAgent

**Purpose:** Compose findings into a forward-ready action packet designed for TWO audiences: the traveler reads it, the agent acts on it. The real target is the agent's reaction ("I need the tool that produced this").

**Type:** LLM (~400 tokens, single call)

**Input:** `TripIntent` + `Ranked Findings[]` + `overall_assessment`

**Output (ActionPacket):**
```json
{
  "header": {
    "title": "string — consumer-friendly summary",
    "assessment": "green | yellow | red",
    "assessment_label": "Looks good | A few things to check | Needs attention"
  },
  "findings": [
    {
      "severity_label": "🔴 Must fix | 🟡 Should review | 🟢 FYI",
      "message": "string — 15 words max",
      "detail": "string — 1-2 sentences, collapsible",
      "ask_your_agent": "string — exact question"
    }
  ],
  "forward_ready": {
    "subject": "string — email/subject line for agent",
    "body": "string — full email body, copy-paste ready",
    "has_been_edited": "bool — user can toggle"
  }
}
```

**Prompt:**
```
You are a travel packet composer. Take audit findings and compose a forward-ready message that a traveler can copy-paste to their travel agent.

Requirements:
1. The SUBJECT line must make the agent want to open it.
2. The BODY must be professional, specific, and actionable.
3. Each finding must include an "ask your agent" question.
4. The tone is helpful, not adversarial — the traveler and agent are on the same team.
5. The packet is organized as: assessment summary → key findings → what to ask.

Trip: {destinations} | {dates} | {party_size}
Overall assessment: {overall_assessment}

Findings:
{findings_json}

Output JSON:
{
  "subject": "...",
  "body": "...",
  "findings": [...]  
}
```

---

## Orchestration Flow

### Launch Mode (LLM Primary)

```
POST /api/public-checker/run
├── 1. Create session_id, inquiry_id
├── 2. Log intake_started event
├── 3. Run ParserAgent (LLM call #1)
│   └── On parse error: return "Could not parse your itinerary. Try including destinations and dates."
├── 4. Run EnrichmentLayer (parallel API calls, 5s timeout each)
│   └── On enrich fail: continue with null enrichment data
├── 5. Run AnalysisAgent (heuristic rules + LLM call #2)
│   └── On LLM fail: return heuristic findings only
├── 6. Log first_credible_finding_shown event
├── 7. Run PacketAgent (LLM call #3)
│   └── On LLM fail: return raw findings without packet body
├── 8. Log action_packet_copied event (when user copies)
├── 9. Return response to frontend
└── Total: 3 LLM calls, ~15-25s end-to-end
```

### Hybrid Mode (BE Available)

```
POST /api/public-checker/run
├── 1. Run both paths IN PARALLEL:
│   ├── Path A: Spine pipeline (existing)
│   │   └── On success: produce validation + packet + decision
│   └── Path B: LLM agents (as above)
│       └── On LLM fail: use spine result only
├── 2. HybridGate — compare quality of both outputs:
│   ├── If spine confidence >= 0.7 AND has findings: USE SPINE (skip LLM result)
│   ├── If spine quality < 0.7: USE LLM agents result
│   └── If spine degraded (NB01 DEGRADE): USE LLM agents
├── 3. PacketAgent runs on chosen findings
├── 4. Log event with attribution_mode: "spine" | "llm_agents" | "hybrid"
└── Total: depends on slower path, ~15-25s
```

---

## LLM Cost Analysis (Launch Mode)

| Call | Provider | Approx Input Tokens | Approx Output Tokens | Cost/Request |
|------|----------|---------------------|----------------------|-------------|
| ParserAgent | Claude 3.5 Sonnet | 300 | 200 | ~$0.002 |
| AnalysisAgent (LLM phase) | Claude 3.5 Sonnet | 800 | 400 | ~$0.005 |
| PacketAgent | Claude 3.5 Sonnet | 600 | 500 | ~$0.005 |
| **Total** | | **1,700** | **1,100** | **~$0.012** |

At 1,000 audits/month: ~$12/month.
At 10,000 audits/month: ~$120/month.

**Optimization for scale:**
- Cache AnalysisAgent results for identical TripIntent fingerprints
- Use faster/cheaper model (Claude Haiku) for ParserAgent (~$0.0005/call)
- Cache enrichment data per destination per season

---

## Prompt Versioning & Testing

### Per-agent prompt files (for version control and A/B testing)

```
spine_api/product_b/
├── prompts/
│   ├── parser_agent/
│   │   ├── v1.txt
│   │   └── v2.txt
│   ├── analysis_agent/
│   │   ├── v1.txt
│   │   └── v2.txt
│   └── packet_agent/
│       ├── v1.txt
│       └── v2.txt
├── agents/
│   ├── parser_agent.py
│   ├── enrichment_layer.py
│   ├── analysis_agent.py
│   └── packet_agent.py
└── router.py  — orchestrator
```

Each agent loads its prompt from disk. Prompt version is logged in the event envelope.

### Testing strategy

| Agent | Test Type | What to Assert |
|-------|-----------|----------------|
| ParserAgent | Unit (fixture + LLM call) | All fields populated correctly, confidence scores sane |
| AnalysisAgent | Unit | Heuristic rules fire correctly, LLM findings dedup against heuristics |
| PacketAgent | Unit | Subject line < 60 chars, body includes all findings |
| Full flow | Integration (real LLM, mock enrichments) | TTF < 30s, findings >= 1, packet copyable |
| Regression | Snapshot (compare findings against known good outputs) | No regression in finding quality |

---

## What Changes When BE Is Ready

| Component | Launch Mode (LLM primary) | Hybrid Mode (BE available) |
|-----------|--------------------------|---------------------------|
| ParserAgent | LLM call | Spine's extraction pipeline (CanonicalPacket) |
| EnrichmentLayer | API calls + static data | Same — unchanged |
| AnalysisAgent (heuristics) | Rules from this doc | Spine's validation + decision engine |
| AnalysisAgent (LLM) | Full LLM reasoning | Reduced scope (only cross-destination and hidden risks) |
| PacketAgent | Same | Same — unchanged |
| HybridGate | Not present | Routes between spine and LLM based on quality |

**The LLM agents never disappear.** They become:
1. **Fallback** when spine degrades (NB01 DEGRADE path)
2. **Supplement** for cross-destination reasoning the spine doesn't cover
3. **Rapid iteration** path — new finding types prototyped as LLM agents before building into spine rules

---

## Key Decisions and Rationale

| Decision | Rationale | Source |
|----------|-----------|--------|
| 3 LLM calls, not 1 | Separate concerns. Parser, analysis, and packet have distinct optimization paths. | Strategist, Champion |
| Heuristic rules before LLM | Deterministic findings are trust anchors. LLM adds cross-destination reasoning. | Skeptic, Executioner |
| Max 7 findings | Noise drowns signal beyond 3-5. Keeps action packet actionable. | Skeptic, Future Self |
| Packet targets agent, not traveler | The conversion event is the agent's "I need this tool" moment. | Strategist |
| Enrichment is rule-based, not LLM | Weather/cost/safety are facts, not opinions. API data is cheaper and more reliable. | Cartographer, Champion |
| Parallel enrichment | No dependency chain between weather and holiday data. Each can fail independently. | Operator |
| HybridGate when BE ready | LLM agents become fallback. Not "replace LLM with spine" but "pick the higher quality path." | All roles converge |
| Prompt files on disk, not code | Versioned, testable, A/B-testable separately from code deploys. | Champion |

---

## Open Questions for Discussion

1. **ParserAgent model choice.** Sonnet for accuracy vs Haiku for speed/cost? Tradeoff: ~5% accuracy difference, ~4x cost difference.
2. **How many heuristic rules before shipping?** Start with 3 (weather, budget, visa) or build all 5?
3. **Action packet format — email body vs structured JSON vs both?** Email is forwardable. JSON is integratable. Both is more code.
4. **When BE arrives: do we run both paths in parallel (cost: 2x) or sequentially (latency: 2x)?** HybridGate needs a decision.
5. **What's the signal that tells HybridGate "spine is better than LLM" for this input?** Confidence score? Finding count? Specific categories?
