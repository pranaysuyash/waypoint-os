# Product B — n8n-Ready Agent Workflow (Launch Without BE)

**Date:** 2026-05-08
**Goal:** Build Product B itinerary audit as a multi-agent LLM workflow in n8n. No dependency on the existing Python backend/spine pipeline.

---

## Architecture: 4 Agents, 3 LLM Calls

```
Traveler Text
     │
     ▼
┌─────────────────────────────┐
│ Agent 1: ParserAgent        │  LLM call #1
│ Unstructured text → TripIntent
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│ Agent 2: EnrichmentLayer    │  5 parallel API calls (NO LLM)
│ TripIntent → per-destination weather/holidays/cost/safety/visa
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│ Agent 3: AnalysisAgent      │  Heuristic rules + LLM call #2
│ TripIntent + Enrichment → Ranked Findings[]
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│ Agent 4: PacketAgent        │  LLM call #3
│ Findings → forward-ready email body for the traveler's agent
└──────────┬──────────────────┘
           │
           ▼
       ActionPacket (output to traveler)

Total: 3 LLM calls, 5 API calls. ~$0.012/audit.
```

---

## Agent 1: ParserAgent

**Type:** LLM (single call, no chain-of-thought)
**Model recommendation:** Claude 3.5 Sonnet or GPT-4o-mini
**Estimated cost:** ~$0.002/request

### Input
```
{
  "raw_text": "string — full text the traveler pasted or we extracted from upload",
  "input_mode": "freeform_text | upload | mixed"
}
```

### Prompt (system message)
```
You are a travel itinerary parser. Extract structured data from the itinerary text below.

Rules:
1. Extract ALL destinations mentioned. If a city name is ambiguous (e.g. "Georgia" could be country or US state), include both with a confidence score.
2. Extract date windows, even partial ones. "mid-June" → approximate to June 15 of the current or next year. "summer 2026" → June-August 2026.
3. Extract party composition (total people, adults, children, elders). If not explicit, set each to null — never default to "1 adult".
4. Extract budget information from any mention of money, price range, cost, or budget keywords.
5. If the text mentions purpose (wedding, honeymoon, business, medical, family visit), extract it.
6. Output ONLY valid JSON. No explanations, no markdown formatting. Just the JSON object.
7. If a field cannot be determined, set it to null. NEVER invent or guess values.

Itinerary text:
{{ raw_text }}
```

### Output (TripIntent JSON)
```json
{
  "destinations": [
    {"name": "Singapore", "country": "Singapore", "days": 4},
    {"name": "Bali", "country": "Indonesia", "days": 3}
  ],
  "date_window": {
    "start": "2026-06-01",
    "end": "2026-06-07",
    "season": "summer"
  },
  "party": {
    "total": 5,
    "adults": 2,
    "children": 1,
    "elders": 2
  },
  "budget": {
    "raw": "mid-range budget around 3000 USD",
    "band": "mid",
    "currency": "USD"
  },
  "purpose": "leisure",
  "confidence": {
    "destinations": 0.95,
    "dates": 0.8,
    "party": 0.9
  }
}
```

### Error handling
- If `destinations` is empty or null → return error: "I couldn't identify any destinations. Please include city/country names."
- If `destinations` has values but `date_window` is null → proceed with "unknown season" (enrichment will use current season as fallback)
- If `party.total` is null → default to 2 adults (most common traveler profile)

---

## Agent 2: EnrichmentLayer

**Type:** 5 parallel API/subworkflow calls. NO LLM calls.
**Estimated cost:** ~$0 (API calls only, most are static data lookups)

### Input
```
TripIntent (from Agent 1)
```

### Sub-agent 2a: WeatherEnricher

**Purpose:** Get climate data for each destination during the travel window.

**Data source:** Open-Meteo API (free, no key required)

**HTTP call:**
```
GET https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lng}&monthly=temperature_2m_max,temperature_2m_min,precipitation_sum&timezone=auto
```

**Fallback logic (when destination not in Open-Meteo):** Static climate table for common destinations.

**Output:**
```json
{
  "destination": "Singapore",
  "weather": {
    "risk": "medium",
    "summary": "Hot and humid. June avg temp 27-32°C. High precipitation (170mm avg).",
    "seasonality": "Dry season start — lower rain than Nov-Jan peak",
    "alerts": ["High humidity warning", "Afternoon thunderstorm probability >60%"],
    "source": "open-meteo"
  }
}
```

**Timeout:** 5 seconds. On failure → return null for weather.

### Sub-agent 2b: HolidayEnricher

**Purpose:** Check for public holidays, festivals, school breaks during travel window.

**Data source:** Static JSON file per country (small, maintained manually or from a public holiday API)

**Lookup:** `holidays_by_country[country_code][month]`

**Output:**
```json
{
  "destination": "Singapore",
  "holidays": [
    {"name": "Hari Raya Haji", "date": "2026-06-07", "type": "public", "impact": "Some attractions may have adjusted hours"}
  ]
}
```

**Timeout:** 500ms. On failure → return empty array.

### Sub-agent 2c: CostEnricher

**Purpose:** Estimate daily cost band for the destination.

**Data source:** Static map: `cost_bands_by_country = {"Singapore": "high", "Indonesia": "low", "Thailand": "low", ...}`

**Output:**
```json
{
  "destination": "Singapore",
  "cost_band": "high",
  "currency_code": "SGD",
  "daily_estimate": {
    "budget": 80,
    "mid": 150,
    "premium": 300
  }
}
```

**Timeout:** 200ms. On failure → default to "mid".

### Sub-agent 2d: SafetyEnricher

**Purpose:** Provide travel advisory level for the destination.

**Data source:** Static map: `advisories_by_country = {"Singapore": "normal", "Indonesia": "exercise_caution", ...}`

**Output:**
```json
{
  "destination": "Singapore",
  "safety": {
    "advisory_level": "normal",
    "notes": "Generally safe. Watch for pickpocketing in tourist areas."
  }
}
```

**Timeout:** 200ms. On failure → default to "normal".

### Sub-agent 2e: VisaEnricher

**Purpose:** Check visa requirements for the traveler's nationality.

**Input needed:** Traveler's nationality (ask if not provided in original text)

**Data source:** Static map: `visa_policy[destination_country][traveler_nationality]`

**Output:**
```json
{
  "destination": "Singapore",
  "visa": {
    "required": false,
    "max_stay_days": 90,
    "processing_time_days": null,
    "notes": "Visa-free for most nationalities for up to 90 days"
  }
}
```

**Timeout:** 500ms. On failure → skip visa enrichment.

### Merge step (after all 5 parallel sub-agents complete):
```json
{
  "destinations": [
    {
      "name": "Singapore",
      "weather": { ... } or null,
      "holidays": [...] or [],
      "cost_band": "high",
      "safety": { ... } or null,
      "visa": { ... } or null,
      "airport_codes": ["SIN"],
      "timezone": "Asia/Singapore",
      "language": "English, Mandarin, Malay, Tamil"
    },
    {
      "name": "Bali",
      ...
    }
  ]
}
```

---

## Agent 3: AnalysisAgent

**Type:** Hybrid — Phase A (heuristic rules, no LLM) → Phase B (LLM call)
**Model recommendation:** Claude 3.5 Sonnet or GPT-4o-mini for LLM phase
**Estimated cost:** ~$0.005/request

### Input
```json
{
  "trip_intent": { ... from Agent 1 },
  "enrichment": { ... from Agent 2 }
}
```

### Phase A: Heuristic Rules (run first, deterministic)

Run these checks. Output `heuristic_findings[]` array. Every finding that fires here is NOT passed to the LLM (avoid duplication).

| Rule # | Check | Condition | Severity | Output |
|--------|-------|-----------|----------|--------|
| R1 | Weather risk | Any destination has weather.risk == "high" | should_review | "High weather risk during your stay" |
| R2 | Budget mismatch | cost_band == "high" AND budget.band == "budget" | should_review | "Your budget may be tight for destinations with higher costs" |
| R3 | Visa needed | visa.required == true | must_fix | "Visa required — check processing times" |
| R4 | Holiday conflict | holidays.length > 0 | good_to_know | "Your trip overlaps with local holidays — expect crowds" |
| R5 | Overpacked | total destinations × 2 < total days? (optional) | should_review | "Packed itinerary — consider fewer destinations" |

**Important:** R1-R5 are simple conditional checks. No LLM needed.

### Phase B: LLM Reasoning (complement, not duplicate)

**System prompt:**
```
You are a travel audit analyst. Given a structured trip plan and enrichment data, identify findings that a travel expert would spot but a casual traveler might miss.

Trip details:
- Destinations: {{ destinations }}
- Dates: {{ date_window.start }} to {{ date_window.end }}
- Party: {{ party.total }} people ({{ party.adults }} adults, {{ party.children }} children, {{ party.elders }} elders)
- Budget: {{ budget.raw }} (band: {{ budget.band }})
- Purpose: {{ purpose }}

Per-destination enrichment data:
{{ enrichment_json }}

Existing rules-based findings (DO NOT duplicate these):
{{ heuristic_findings }}

RULES:
1. ONLY surface findings a traveler would NOT discover by reading a guidebook or travel blog.
2. Focus on CROSS-DESTINATION interactions — how destinations interact (budget split, routing feasibility, time allocation).
3. Focus on HIDDEN RISKS — non-obvious problems an experienced traveler would spot.
4. Focus on SUITABILITY — is each activity/destination appropriate for the party composition (toddlers, elders)?
5. Each finding must be SPECIFIC and ACTIONABLE. Include the exact question the traveler should ask their agent.
6. If you cannot find a non-obvious finding, output NOTHING. An empty array is acceptable.
7. NEVER invent visa, safety, or policy claims. Only use the enrichment data provided.
8. Confidence score < 0.6 means uncertain — these will be surfaced lower in priority.

Output as a JSON array of finding objects:
[
  {
    "severity": "must_fix|should_review|good_to_know",
    "category": "cost|suitability|logistics|timing|hidden_risk",
    "message": "string — 1 sentence, 15 words max, actionable",
    "detail": "string — 2-3 sentences explaining the finding",
    "ask_agent": "string — exact question the traveler should send to their agent",
    "confidence": 0.0 to 1.0
  }
]
If no non-obvious findings, output: []
```

### Merge Phase: Combine heuristic_findings + llm_findings

**Rules:**
1. Start with heuristic findings (higher confidence, deterministic).
2. Insert LLM findings at their severity level.
3. **Deduplicate** — if heuristic and LLM produce findings with similar normalized message text (edit distance < 0.3), keep the heuristic version.
4. **Max 7 findings total.** If more than 7, keep top 5 + add a "N more findings" collapsible entry.
5. **Compute overall_assessment:**
   - `red` if any finding has severity == "must_fix"
   - `yellow` if any finding has severity == "should_review" and no "must_fix"
   - `green` otherwise

### Output (Ranked Findings[])
```json
{
  "overall_assessment": "yellow",
  "findings": [
    {
      "id": "finding-001",
      "severity": "must_fix",
      "category": "policy",
      "message": "Visa required for your nationality",
      "detail": "Your destination requires a visa for your nationality. Processing can take 2-4 weeks.",
      "ask_agent": "Can you check visa requirements for my nationality and start the application process?",
      "confidence": 0.95,
      "llm_reasoned": false
    },
    {
      "id": "finding-002",
      "severity": "should_review",
      "category": "cost",
      "message": "Budget may be tight for your destinations",
      "detail": "Singapore is in the 'high' cost band. Your stated budget of $3000 for 7 days for 5 people averages $85/person/day, which is below typical Singapore costs.",
      "ask_agent": "Can you help me understand if $3000 is realistic for this trip, or suggest adjustments?",
      "confidence": 0.85,
      "llm_reasoned": false
    },
    {
      "id": "finding-003",
      "severity": "good_to_know",
      "category": "suitability",
      "message": "Universal Studios may not suit your toddler",
      "detail": "Universal Studios Singapore has height restrictions on many rides. Your 2-year-old may not be able to participate in most attractions.",
      "ask_agent": "Are there toddler-friendly alternatives near Sentosa that the whole family can enjoy together?",
      "confidence": 0.78,
      "llm_reasoned": true
    }
  ]
}
```

---

## Agent 4: PacketAgent

**Type:** LLM (single call, structured template + LLM-composed descriptions)
**Model recommendation:** Claude 3.5 Sonnet or GPT-4o-mini
**Estimated cost:** ~$0.005/request

### Input
```json
{
  "trip_intent": { ... },
  "findings": { ... ranked findings with overall_assessment },
  "enrichment": { ... }
}
```

### System prompt
```
You are a travel packet composer. Take audit findings and compose a forward-ready message that a traveler can copy-paste to their travel agent.

The REAL GOAL: make the receiving travel agent think "I need the tool that produced this."

Trip: {{ destinations }} | {{ dates }} | {{ party_size }} people
Assessment: {{ overall_assessment }}

Findings to include:
{{ findings_formatted }}

REQUIREMENTS:
1. SUBJECT LINE (under 60 chars): Must make the agent want to open the email. Specific, not generic.
2. BODY: Professional, specific, actionable. Tone is collaborative — traveler and agent on same team.
3. Each finding must include its "Ask your agent" question embedded in the email.
4. Structure: Assessment summary → Key findings → What I'd like you to look into
5. End with: "Can you review these points and let me know your thoughts?"
6. The body should be complete — the traveler should be able to copy-paste the entire text into an email to their agent without adding anything.

Output JSON:
{
  "subject": "string (under 60 chars)",
  "body": "string (complete email body, 2-3 paragraphs)",
  "findings": [
    {
      "severity_label": "🔴 Must fix | 🟡 Should review | 🟢 FYI",
      "message": "string (15 words max)",
      "detail": "string (1-2 sentences, collapsible)",
      "ask_your_agent": "string"
    }
  ]
}
```

### Output (ActionPacket)
```json
{
  "header": {
    "title": "Your Singapore & Bali Trip — A Few Things to Check",
    "assessment": "yellow",
    "assessment_label": "A few things to check"
  },
  "findings": [
    {
      "severity_label": "🔴 Must fix",
      "message": "Visa required for your nationality",
      "detail": "Your destination requires a visa. Processing takes 2-4 weeks.",
      "ask_your_agent": "Can you check visa requirements for my nationality and start the application process?"
    },
    {
      "severity_label": "🟡 Should review",
      "message": "Budget may be tight for Singapore",
      "detail": "Singapore is high-cost. Your $3000 budget for 5 people for 7 days averages $85/person/day, below typical costs.",
      "ask_your_agent": "Can you review if this budget is realistic, or suggest adjustments?"
    },
    {
      "severity_label": "🟢 FYI",
      "message": "Universal Studios rides may not suit your toddler",
      "detail": "Many rides have height restrictions that your 2-year-old may not meet.",
      "ask_your_agent": "Are there toddler-friendly alternatives near Sentosa for the whole family?"
    }
  ],
  "forward_ready": {
    "subject": "Quick check on our Singapore-Bali trip plan",
    "body": "Hi [Agent Name],\n\nI ran our planned itinerary through an audit tool and there are a few points I'd love your input on.\n\nOverall it looks good, but a few things came up:\n\n1. VISA: It looks like we might need a visa for our nationality. Can you check and let me know the process?\n\n2. BUDGET: Our budget of $3000 for 5 people over 7 days might be tight for Singapore. Can you review if this is realistic?\n\n3. ACTIVITIES: We were planning Universal Studios but some rides may not work for our 2-year-old. Any alternatives nearby for the whole family?\n\nLet me know your thoughts!\n\nThanks,\n[Traveler Name]"
  }
}
```

---

## Error Handling Per Agent

| Agent | Failure scenario | Behavior |
|-------|-----------------|----------|
| ParserAgent | LLM returns null/invalid JSON | Return error: "Could not parse — try including destinations and dates" |
| WeatherEnricher | Open-Meteo API down | Return null — other enrichment still works |
| HolidayEnricher | Data not found | Return [] — skip |
| CostEnricher | Country not in map | Default to "mid" |
| SafetyEnricher | Country not in map | Default to "normal" |
| VisaEnricher | Nationality not in map | Return null — skip |
| AnalysisAgent LLM phase | LLM call fails | Return heuristic findings only |
| PacketAgent | LLM call fails | Return raw findings without the email body |

**Golden rule:** No single agent failure should prevent the output from being shown. The product degrades gracefully.

---

## Orchestration Flow (n8n Workflow)

```
[Webhook: POST /product-b/audit]
        │
        ▼
[IF: input is valid?] ───NO──→ [Return error to user]
        │ YES
        ▼
[Log event: intake_started]
        │
        ▼
[Agent 1: ParserAgent — HTTP Request to LLM API]
        │
        ▼
[IF: destinations found?] ───NO──→ [Return "add destination" to user]
        │ YES
        ▼
[Parallel Branch × 5: Enrichment]
  ├── [WeatherEnricher — HTTP to Open-Meteo]
  ├── [HolidayEnricher — lookup from static data]
  ├── [CostEnricher — lookup from static data]
  ├── [SafetyEnricher — lookup from static data]
  └── [VisaEnricher — lookup from static data]
        │
        ▼
[Wait for all branches → Merge enrichments into one JSON]
        │
        ▼
[Agent 3 Phase A: Heuristic Rules — 5 conditional checks]
        │
        ▼
[Log: first_credible_finding_shown (if any heuristic findings)]
        │
        ▼
[Agent 3 Phase B: AnalysisAgent LLM — HTTP Request to LLM API]
        │
        ▼
[Merge heuristic + LLM findings → Dedup → Rank → Max 7]
        │
        ▼
[Agent 4: PacketAgent — HTTP Request to LLM API]
        │
        ▼
[Return ActionPacket to traveler]
        │
        ▼
[Log: action_packet_copied (when traveler copies)]
```

---

## Static Data Files Needed (for enrichment)

Create these tiny JSON files in your n8n workflow or upload them as assets:

### `weather_fallback.json`
```json
{
  "bali": {"lat": -8.3405, "lng": 115.0920, "country": "Indonesia"},
  "singapore": {"lat": 1.3521, "lng": 103.8198, "country": "Singapore"},
  "bangkok": {"lat": 13.7563, "lng": 100.5018, "country": "Thailand"},
  "dubai": {"lat": 25.2048, "lng": 55.2708, "country": "UAE"},
  "london": {"lat": 51.5074, "lng": -0.1278, "country": "UK"}
}
```

### `cost_bands.json`
```json
{
  "Singapore": "high",
  "Indonesia": "low",
  "Thailand": "low",
  "Malaysia": "low",
  "Vietnam": "low",
  "Japan": "high",
  "South Korea": "mid",
  "UAE": "high",
  "UK": "high",
  "USA": "high",
  "Australia": "high",
  "India": "low"
}
```

### `safety_advisories.json`
```json
{
  "Singapore": {"level": "normal", "notes": "Generally safe"},
  "Indonesia": {"level": "exercise_caution", "notes": "Exercise caution in tourist areas"},
  "Thailand": {"level": "exercise_caution", "notes": "Exercise normal precautions"},
  "Japan": {"level": "normal", "notes": "Very safe"},
  "UAE": {"level": "normal", "notes": "Generally safe"}
}
```

### `visa_policy.json`
```json
{
  "Singapore": {
    "US": {"required": false, "max_stay": 90},
    "UK": {"required": false, "max_stay": 90},
    "India": {"required": true, "processing_days": 7},
    "Australia": {"required": false, "max_stay": 90}
  },
  "Indonesia": {
    "US": {"required": false, "max_stay": 30},
    "UK": {"required": false, "max_stay": 30},
    "India": {"required": true, "processing_days": 5},
    "Australia": {"required": true, "processing_days": 5}
  }
}
```

---

## Summary

| # | Agent | Type | Calls | Est Cost | Key Failure Mode |
|---|-------|------|-------|----------|------------------|
| 1 | ParserAgent | LLM | 1 LLM | $0.002 | No destinations found |
| 2 | EnrichmentLayer | API/Rule | 5 API | ~$0 | Weather API down |
| 3a | AnalysisAgent (heuristic) | Rule | 0 LLM | ~$0 | No findings fire |
| 3b | AnalysisAgent (LLM) | LLM | 1 LLM | $0.005 | LLM produces noise |
| 4 | PacketAgent | LLM | 1 LLM | $0.005 | LLM produces generic body |
| **Total** | | | **3 LLM + 5 API** | **~$0.012** | None fatal alone |

**Time estimate per audit:** ~15-25s (bottleneck is Parser → Analysis LLM calls)
