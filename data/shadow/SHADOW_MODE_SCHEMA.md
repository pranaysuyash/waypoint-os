# Shadow Mode Schema

**Purpose**: Structured format for running real agency notes through the NB01→NB02→NB03 spine and capturing human judgment.

---

## Input Format

One JSON file per case: `data/shadow/inputs/shadow_XXX.json`

```json
{
  "id": "shadow_001",
  "source_type": "whatsapp | call_notes | crm | email",
  "raw_input": "The messy real agency note text",
  "structured_input": null,
  "context": {
    "is_repeat_customer": false,
    "history_notes": null
  },
  "expected": null,
  "system_output": null,
  "review": null
}
```

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique identifier: `shadow_XXX` |
| `source_type` | string | Yes | Where the note came from |
| `raw_input` | string | Yes | The actual messy text — no pre-cleaning |
| `structured_input` | dict\|null | No | Optional CRM/form data |
| `context.is_repeat_customer` | bool\|null | No | If we know this |
| `context.history_notes` | string\|null | No | Any prior context |
| `expected` | null | N/A | Always null for shadow mode |
| `system_output` | null→dict | Filled by runner | See below |
| `review` | null→dict | Filled by reviewer | See below |

---

## System Output (filled by runner)

```json
"system_output": {
  "nb01_packet": {
    "packet_id": "shadow_001",
    "facts": {
      "origin_city": {"value": "Bangalore", "authority": "explicit_owner", "confidence": 0.9},
      ...
    },
    "derived_signals": {},
    "hypotheses": {},
    "unknowns": [],
    "contradictions": []
  },
  "nb02_decision": {
    "decision_state": "ASK_FOLLOWUP",
    "hard_blockers": ["destination_city"],
    "soft_blockers": ["budget_range"],
    "confidence": 0.62,
    "follow_up_questions": [
      {"field_name": "destination_city", "question": "Where would you like to go?", "priority": "critical"}
    ]
  },
  "nb03_strategy": {
    "session_goal": "Collect 1 blocking field: destination_city",
    "priority_sequence": ["Where would you like to go?"],
    "tonal_guardrails": ["Ask focused questions"],
    "suggested_opening": "I'd like to help plan your trip...",
    "next_action": "ASK_FOLLOWUP"
  }
}
```

---

## Human Review (filled by reviewer)

```json
"review": {
  "verdict": "usable | needs_edit | wrong_direction",
  "nb01_issues": ["Missed elderly constraint"],
  "nb02_issues": ["Should be ASK_FOLLOWUP, not PROCEED"],
  "nb03_issues": ["Questions too generic"],
  "overall_issue": "Missed key constraint → wrong decision",
  "what_human_would_do": "Ask for exact dates + suggest Austria",
  "severity": "low | medium | high",
  "reviewer_notes": ""
}
```

### Verdict Definitions

| Verdict | Meaning |
|---------|---------|
| `usable` | Agent could send this with minor tweaks |
| `needs_edit` | Direction correct, but weak execution |
| `wrong_direction` | Wrong decision state OR misleading strategy |

### Severity Definitions

| Severity | Meaning |
|----------|---------|
| `low` | Cosmetic issue, doesn't affect outcome |
| `medium` | Execution weakness, agent would fix |
| `high` | Systemic failure, wrong advice given |

---

## Folder Structure

```
data/
  shadow/
    inputs/
      shadow_001.json
      shadow_002.json
      ...
    outputs/
      shadow_001_output.json    # Filled by runner
    evaluations/
      shadow_001_eval.json      # Filled by reviewer
Docs/
  SHADOW_MODE_REPORT.md         # Aggregate analysis
```

---

## Runner Flow

1. **Load** all `data/shadow/inputs/shadow_*.json` files
2. **Run** each through NB01 (simulated extraction) → NB02 → NB03
3. **Save** system output to `data/shadow/outputs/shadow_XXX_output.json`
4. **Update** input file with `system_output` filled in
5. **Reviewer** fills `review` section
6. **Analyze** patterns → `Docs/SHADOW_MODE_REPORT.md`

---

## Success Gate

- At least ~70% `usable` or `needs_edit` (directionally correct)
- No repeated catastrophic failure mode
- Clear understanding of failure patterns
