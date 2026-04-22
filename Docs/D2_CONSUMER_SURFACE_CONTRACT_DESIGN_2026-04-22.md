# D2 Consumer Surface Contract Design

**Date**: 2026-04-22
**ADR Reference**: `Docs/ARCHITECTURE_DECISION_D2_FREE_ENGINE_PERSONA_2026-04-18.md`
**Gating Doc**: `Docs/D6_EVAL_CONTRACT_DESIGN_2026-04-22.md`
**Purpose**: Define the agency/internal vs consumer/public surface split so D2 can ship safely

---

## 1. The GTM Wedge: Itinerary Checker

The D2 consumer surface is the "free engine" — a public-facing itinerary checker that travelers use to:
1. Paste their rough trip idea (dates, budget, group size, destinations)
2. Receive an instant feasibility assessment + "things to discuss with your planner"
3. Be matched to an agency partner if the trip is complex

The framing is **empowerment**, not adversarial. The consumer doesn't see "your agency is ripping you off." They see "here are 5 questions to ask your planner to get the best trip."

---

## 2. The Split Model

### Two Surfaces, One Engine

| Dimension | Agency Surface (Internal) | Consumer Surface (Public) |
|-----------|----------------------------|----------------------------|
| **User** | Agency owner, agent, junior | Traveler, prospective customer |
| **Goal** | Process leads, make decisions | Self-assess feasibility, find planner |
| **Data shown** | Full packet, confidence scorecard, risk flags, branch options | Feasibility + suggestions only |
| **Confidence** | Full (data/judgment/commercial) | Single "confidence" bar: 🟢🟡🔴 |
| **Follow-ups** | Structured questions for traveler | "Here's what to ask your planner" |
| **CTA** | "Generate proposal" / "Request document" | "Talk to a planner" / "Get matched" |
| **Revenue model** | Agency subscription (₹6k/mo) | Lead generation for agencies |
| **Autonomy gate** | D1 policy: auto/review/block | **Always review** — no autonomous consumer decisions |
| **D6 eval gate** | 90% state accuracy required | **95% state accuracy required** |

### Key Principle: The Consumer Surface Is Read-Only

The consumer surface NEVER:
- Modifies the canonical packet
- Makes a booking or payment
- Autonomously generates a proposal
- Sends messages to suppliers

It ONLY:
- Runs NB01+NB02 on anonymized inputs
- Returns a structured feasibility assessment
- Suggests discussion points
- Optionally captures lead info (email, budget, dates)

---

## 3. Presentation Profile Contract

### Request Differences

**Agency Request** (`/api/spine/run`):
```json
{
  "packet": { /* full CanonicalPacket v0.2 */ },
  "operating_mode": "standard",
  "presentation_profile": "agency_full",
  "options": {
    "include_confidence_scorecard": true,
    "include_risk_flags": true,
    "include_follow_up_questions": true,
    "include_branch_options": true
  }
}
```

**Consumer Request** (`/api/public/check`):
```json
{
  "packet": {
    "facts": {
      "destination_candidates": ["Maldives"],
      "date_start": "2026-12-01",
      "date_end": "2026-12-07",
      "budget_min": 200000,
      "party_size": 2,
      "party_composition": {"adult": 2}
    }
    // Note: lightweight packet, not full CanonicalPacket
  },
  "presentation_profile": "consumer_summary",
  "options": {
    "include_confidence_scorecard": false,
    "include_risk_flags": false,  // Risk flags are internal
    "include_follow_up_questions": true,  // But reframed as "planner questions"
    "include_branch_options": false
  }
}
```

### Response Differences

**Agency Response**:
```json
{
  "decision_state": "PROCEED_TRAVELER_SAFE",
  "confidence_scorecard": {
    "data": 0.92,
    "judgment": 0.87,
    "commercial": 0.73
  },
  "risk_flags": [
    {"type": "budget_feasibility", "level": "low", "reasoning": "..."}
  ],
  "follow_up_questions": [
    {"field_name": "hotel_preference", "question": "...", "priority": "medium"}
  ],
  "autonomy_outcome": {
    "action": "auto",
    "raw_verdict": "PROCEED_TRAVELER_SAFE",
    "rule_source": "..."
  }
}
```

**Consumer Response**:
```json
{
  "status": "feasible",  // Simplified: feasible / needs_clarity / not_recommended
  "confidence_indicator": "high",  // 🟢🟡🔴 mapped from scorecard
  "feasibility_notes": "Your Maldives trip looks feasible with a ₹2L budget for 2 adults in December.",
  "discussion_points": [
    "Ask about local weather patterns in December",
    "Discuss whether water villa or garden villa fits your style",
    "Clarify if transfers are speedboat or seaplane"
  ],
  " estimated_budget_range": "₹1.8L – ₹2.5L",
  "next_steps": {
    "primary_cta": "Get a free consultation with a verified planner",
    "secondary_cta": "Save this itinerary for later"
  }
}
```

### Reframing Rules (Empowerment Framing)

Internal follow-up questions are reframed for consumers:

| Internal Question | Consumer Discussion Point |
|-------------------|---------------------------|
| "What is your hotel preference?" | "Ask your planner about villa types — beach, water, or garden. Each has a different feel." |
| "Is this trip for a special occasion?" | "Tell your planner if it's an anniversary or birthday — they may include something special." |
| "Do you have travel insurance?" | "Ask whether travel insurance is included or if you should arrange it separately." |

---

## 4. API Contract Split

### Endpoint Design

**Internal** (already exists, extends): `POST /api/spine/run`
- Already returns `DecisionResult` + `autonomy_outcome`
- Agency must authenticate (Clerk session)
- Full packet required

**Consumer** (new, proposed): `POST /api/public/check`
- No authentication required (rate-limited by IP)
- Lightweight packet (5-8 fields)
- Returns `ConsumerCheckResult` only
- D6 eval gate: if precision < 95%, return `{"status": "evaluating", "message": "We're reviewing your trip details."}`

### Data Flow Diagram

```
Consumer Visit
    ↓
POST /api/public/check
    ↓
[Rate Limiter] → reject if > 5 req/min per IP
    ↓
[Lightweight Packet Builder] → construct minimal CanonicalPacket
    ↓
[NB02 Evaluation]
    ↓
[D6 Eval Gate] → is eval precision ≥ 95% for this case type?
    ↓ (if NO, return "evaluating" fallback)
    ↓ (if YES, continue)
[D1 Consumer Autonomy Gate] → consumer surface forces "review", not "auto"
    ↓
[Presentation Transformer] → agency format → consumer format
    ↓
Consumer sees feasibility + discussion points
    ↓
[Lead Capture] (optional) → email + trip summary → CRM
    ↓
Agency owner sees lead in dashboard
```

### Anonymization Requirements

The consumer surface must NOT leak:
- Specific agency data
- Internal risk flags (e.g., "toddler pacing risk: HIGH" → "Discuss activity pacing with your planner")
- Other agency's itineraries
- Cost model details

---

## 5. GTM Integration: Lead Capture Flywheel

### Capture Flow

1. Consumer checks trip feasibility
2. System returns discussion points
3. Consumer clicks "Talk to a planner"
4. System asks: email, phone (optional), preferred agency type (luxury/budget/adventure/family)
5. Lead created in agency owner's dashboard
6. Owner sees: "New lead — Maldives, Dec '26, ₹2L budget, 2 adults"
7. Owner can accept, reject, or auto-assign to agent

### Data Retention
- Consumer check data: retained for 30 days, then anonymized
- Lead data: retained per agency CRM policy
- Anonymized aggregate data: used for benchmarking ("average Delhi→Maldives trip budget: ₹1.8L")

---

## 6. D6 Precision Requirements by Surface

| Surface | State Accuracy | False Positive Rate | Confidence Calibration |
|---------|---------------|---------------------|----------------------|
| Internal workbench | 90% | <5% | Per-dimension |
| Agency owner dashboard | 92% | <3% | Single bar |
| Consumer free engine | **95%** | **<2%** | 3-color indicator |
| Public pricing estimate | 99% | <1% | Exact range |

---

## 7. Implementation Order

The consumer surface should be built in this order:

1. **Phase 0 — Contract Design** (this doc) — Define API shapes, request/response, reframing rules
2. **Phase 1 — Presentation Transformer** — Build `presentation_transformer.py` that takes `DecisionResult` + profile and returns consumer format
3. **Phase 2 — Public Endpoint** — Add `/api/public/check` with rate limiting, D6 gate, anonymization
4. **Phase 3 — Consumer UI** — Build the public-facing itinerary checker page (Next.js, not authenticated)
5. **Phase 4 — Lead Capture** — Wire lead capture to agency dashboard
6. **Phase 5 — Analytics** — Track consumer → lead → conversion rates

---

## 8. Risk: The Adversarial Framing Trap

The biggest risk for D2 is being perceived as "TripAdvisor but for criticizing agencies." The empowerment framing must be enforced in code:

### Enforcement Rules
1. **Never say "overpriced"** → Say "budget estimate ranges from ₹X to ₹Y depending on inclusions"
2. **Never say "bad agency"** → Say "here are questions to help any planner serve you better"
3. **Never compare specific agencies** → Say "these are things to clarify with whichever planner you choose"
4. **Always highlight what the planner CAN do** → "A planner may be able to negotiate group rates if you're traveling with friends"

### Content Review Gate
Before any D2 public text is shipped, it must pass a **framing audit**:
- Automated: regex check for forbidden words ("overpriced", "scam", "rip off")
- Manual: PM reviews a sample of 20 outputs to verify empowerment framing

---

## 9. Verification

Success criteria:

1. ✅ `/api/public/check` contract defined and documented
2. ✅ Consumer response shape documented
3. ✅ Reframes rules documented
4. ✅ D6 eval gate requirements specified
5. ✅ Lead capture flow documented
6. ✅ Forbidden framing words listed

```bash
# Conceptual test (no code yet)
uv run pytest tests/d2/test_consumer_contract.py -q
uv run pytest tests/d2/test_framing_audit.py -q
```

---

Checklist applied: IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md
References:
- `Docs/ARCHITECTURE_DECISION_D2_FREE_ENGINE_PERSONA_2026-04-18.md`
- `Docs/D6_EVAL_CONTRACT_DESIGN_2026-04-22.md`
- `Docs/D1_IMPLEMENTATION_SUMMARY_2026-04-22.md`
