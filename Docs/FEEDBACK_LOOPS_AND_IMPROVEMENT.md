# Feedback Loops and Improvement

**Date**: 2026-04-14
**Purpose**: How to continuously improve the product

---

## The Improvement Engine

> "Products don't improve by magic. They improve through systematic learning."

---

## The Feedback-Iteration Loop

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  THE LOOP                                                                        │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  Usage → Data → Insights → Changes → Measure → Repeat                           │
│                                                                                  │
│  1. Users generate trips, errors, successes                                      │
│       ↓                                                                         │
│  2. System logs everything (source envelope, decisions, outcomes)                │
│       ↓                                                                         │
│  3. You review weekly, categorize findings                                       │
│       ↓                                                                         │
│  4. Prioritize and implement changes                                            │
│       ↓                                                                         │
│  5. Measure impact                                                              │
│       ↓                                                                         │
│  6. Repeat                                                                      │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Part 1: What to Log

### Every Trip Should Capture

```sql
CREATE TABLE trip_logs (
    id UUID PRIMARY KEY,
    agency_id UUID NOT NULL,
    trip_id UUID NOT NULL,

    -- Input
    raw_input TEXT NOT NULL,              -- Original message/exchange
    extracted_constraints JSONB,           -- What was extracted
    contradictions JSONB,                 -- Any contradictions found

    -- Processing
    llm_calls JSONB,                      -- All LLM interactions
    gate_decision TEXT NOT NULL,           -- PROCEED, ASK, ESCALATE, STOP
    options_generated JSONB,               -- The options

    -- Output
    agent_edits BOOLEAN,                   -- Did agent edit?
    edit_ratio DECIMAL,                    -- How much they edited
    traveler_sent BOOLEAN,                 -- Was it sent to traveler?

    -- Outcome
    traveler_feedback TEXT,                -- Optional feedback
    booked BOOLEAN DEFAULT NULL,           -- Did it result in booking?

    -- Meta
    created_at TIMESTAMP DEFAULT NOW(),
    processing_time_ms INTEGER             -- Performance
);
```

### Every Error Should Capture

```sql
CREATE TABLE error_logs (
    id UUID PRIMARY KEY,
    agency_id UUID,
    trip_id UUID,

    error_type TEXT NOT NULL,              -- Category
    error_message TEXT NOT NULL,           -- Details
    stack_trace TEXT,

    context JSONB,                         -- State when error occurred
    resolved BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Part 2: Weekly Review Ritual

### Every Monday, 30-60 minutes

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  WEEKLY REVIEW TEMPLATE                                                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  Week of: _____                                                                  │
│                                                                                  │
│  NUMBERS:                                                                        │
│  Trips processed: _____                                                          │
│  Active agencies: _____                                                          │
│  Errors: _____                                                                   │
│  Avg processing time: _____ ms                                                   │
│                                                                                  │
│  WINS:                                                                           │
│  - What worked well this week?                                                   │
│  - Any positive feedback from users?                                             │
│                                                                                  │
│  LOSSES:                                                                         │
│  - What broke?                                                                   │
│  - Any frustrated users?                                                         │
│                                                                                  │
│  PATTERNS:                                                                       │
│  - Recurring issues?                                                             │
│  - Surprising usage patterns?                                                    │
│                                                                                  │
│  NEXT WEEK:                                                                      │
│  - Top 3 things to fix/improve:                                                  │
│    1.                                                                            │
│    2.                                                                            │
│    3.                                                                            │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Part 3: Categorization Framework

### Every Finding Gets a Category

| Category | Definition | Example | Priority |
|----------|------------|---------|----------|
| **Bug** | Broken functionality | Gate decision crashes app | P0 (fix now) |
| **Quality** | Output isn't good enough | Suggests hotels in wrong city | P1 (fix soon) |
| **Feature** | Requested capability | "Add visa check" | P2 (backlog) |
| **UX** | Confusing interface | "Can't find download button" | P1 |
| **Performance** | Too slow | Takes 30 seconds to generate options | P1 |
| **Edge case** | Rare scenario | "Solo traveler with 10 kids" | P2 |
| **WONTFIX** | Out of scope | "Build a mobile app" | — |

### Priority Matrix

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  PRIORITY MATRIX                                                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  P0 (Critical): System broken, data loss, security issue                        │
│       → Fix same day                                                             │
│                                                                                  │
│  P1 (High): Broken for some users, bad experience                               │
│       → Fix within 1 week                                                        │
│                                                                                  │
│  P2 (Medium): Improvement, nice to have                                         │
│       → Backlog, fix when P0/P1 clear                                           │
│                                                                                  │
│  P3 (Low): Polishing, minor improvements                                        │
│       → Icebox, maybe never                                                      │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Part 4: Feature Request Management

### Simple System (Trello/Notion/Linear)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  BACKLOG                                                                         │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  🔥 THIS WEEK                                                                    │
│  ├─ Fix gate crash when budget is zero                                          │
│  ├─ Improve constraint extraction for dates                                     │
│  └─ Add "download as PDF" button                                                │
│                                                                                  │
│  📋 NEXT UP                                                                      │
│  ├─ Add timezone support                                                        │
│  ├─ Improve contradiction detection                                             │
│  └─ Add onboarding tooltips                                                     │
│                                                                                  │
│  🗂️ BACKLOG                                                                      │
│  ├─ Multi-trip comparison view                                                  │
│  ├─ Calendar integration                                                        │
│  ├─ Mobile app                                                                  │
│  └─ WhatsApp automation                                                         │
│                                                                                  │
│  ❄️ MAYBE / LATER                                                                │
│  ├─ White-labeling                                                              │
│  ├─ GDS integration                                                             │
│  └─ Enterprise SSO                                                              │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Part 5: User Feedback Channels

### In-App Feedback

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  [thumbs up] 👍   [thumbs down] 👎                                               │
│                                                                                  │
│  Was this helpful? (optional)                                                    │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ Tell us more (optional)                                                │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│  [Send Feedback]                                                                │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Keep it minimal** — don't interrupt workflow.

### Quarterly Survey

Every 3 months, send to active users:

```markdown
# Agency OS Feedback

1. How likely are you to recommend Agency OS to other travel agents? (0-10)
2. What's the ONE thing we could do to make this 10x more useful for you?
3. What frustrates you most about the tool right now?
4. How much time does this save you per trip, on average?

(Optional) Any other thoughts?
```

---

## Part 6: A/B Testing (Later)

### When to Start A/B Testing

- You have 100+ weekly active users
- You have a clear hypothesis
- You can measure impact

### What to A/B Test

| What | Example | How to measure |
|------|---------|----------------|
| Onboarding | Video vs. text | Activation rate |
| Message wording | "Your options" vs. "Trip suggestions" | Click-through |
| Feature placement | Button position | Feature usage |
| Pricing | Monthly vs. annual | Conversion rate |

**Don't A/B test yet** — you don't have enough users. Use your judgment.

---

## Part 7: Regression Testing

### Before Every Release

```bash
# Run these tests
pytest tests/test_critical_paths.py
pytest tests/test_gate_decisions.py
pytest tests/test_extraction.py
```

### Critical Paths to Test

1. Intake → extraction → gate decision works
2. Options generation doesn't crash
3. Edit workflow doesn't lose data
4. Traveler-safe output filtering works

---

## Part 8: Learning from Churn

### Exit Interview Template

```markdown
# Thanks for trying Agency OS

We're sorry to see you go. If you have a moment, we'd love to learn:

1. What was the main reason you stopped using Agency OS?
   - [ ] Not useful enough
   - [ ] Too expensive
   - [ ] Too complex to learn
   - [ ] Missing a specific feature: _____
   - [ ] Just busy / not the right time
   - [ ] Other: _____

2. What one thing would have made you stay?

3. Would you consider trying again in the future? Why/why not?

Thank you!
```

**Track every churn response.** Look for patterns.

---

## Part 9: The Improvement Kaizen

### Small, Constant Improvements

> "1% better every day = 37x better in a year"

**Weekly goal**: Ship at least one improvement, no matter how small.

**Examples**:
- Better error message
- Faster loading
- Clearer onboarding text
- Bug fix
- Feature flag toggle

**Over time**: These compound into a much better product.

---

## Part 10: Knowing When to Pivot

### Signs You Might Need to Pivot

| Sign | What to do |
|------|------------|
| Low activation (< 20%) after fixes | Product-market fit problem |
| High churn (> 30%/month) | Not solving real problem |
| Users consistently requesting different features | Wrong value prop |
| Can't acquire customers profitably | Wrong customer or pricing |
| You're not excited to work on it | Founder-market fit problem |

**Before pivoting**: Talk to 10-20 users. Confirm it's not just execution.

---

## Summary

**Log everything**: Trips, errors, outcomes

**Review weekly**: 30-60 min, categorize findings

**Categorize**: Bug/Quality/Feature/UX/Performance

**Prioritize**: P0 > P1 > P2 > P3

**Fix in order**: Critical first, improvements later

**Talk to users**: Especially churned users

**Ship small improvements weekly**: 1% better every day

**The goal**: Constant learning, not perfect knowledge
