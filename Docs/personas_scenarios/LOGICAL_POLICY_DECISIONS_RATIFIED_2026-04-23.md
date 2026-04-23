# Logical Policy Decisions (Ratified) — P1-S0 + P2-S4

- Date ratified: 2026-04-23
- Source draft: `Docs/personas_scenarios/LOGICAL_POLICY_DECISIONS_DRAFT_2026-04-23.md`
- Principle: single canonical implementation path; no parallel route or duplicate policy stack.

## Canonical Implementation Path (No Parallel Implementation)

- Ready gate enforcement uses existing endpoint:
  - `PATCH /trips/{trip_id}` in `spine-api/server.py`
- Escalation/send policy uses shared policy module:
  - `src/analytics/policy_rules.py`
- Policy outputs are applied through existing analytics/review flow:
  - `src/analytics/engine.py`
  - `src/analytics/review.py`
- Trip persistence remains single route:
  - `spine-api/persistence.py` via existing save path

No alternate API route or duplicate pipeline was introduced.

---

## Ratified Decisions

## P1-S0

1. Ready gate is mandatory before completion:
   - customer message present
   - decision state not `ASK_FOLLOWUP` / `STOP_NEEDS_REVIEW` / `suitability_review_required`
   - traveler-safe output present
   - critical suitability flags resolved or explicitly overridden/acknowledged
   - owner approval required if review-required state is active

2. Ambiguity policy:
   - unresolved destination/date ambiguity forces follow-up
   - traveler-safe completion cannot proceed while blocking ambiguity remains

3. Urgency policy:
   - non-emergency urgency may suppress low-value soft blockers only
   - critical blockers remain active

4. Completion semantics glossary:
   - `save`: persist edits only
   - `needs_correction`: returned for correction
   - `ready` (mapped to completed transition): ready-gate passed
   - `return_to_inbox`: navigation only

5. Scenario traceability format:
   - canonical ID format `<Persona>-S<index>` across scenario/report/task artifacts

## P2-S4

1. Onboarding KPIs:
   - time to independent quote
   - owner correction rate
   - rework cycles
   - pre-send risk catch rate
   - quote turnaround

2. Owner escalation + SLA policy:
   - escalate on:
     - critical suitability presence
     - `STOP_NEEDS_REVIEW` / `suitability_review_required`
     - margin below threshold
     - repeated revisions (`>=2`)
   - SLA targets:
     - critical: 2h
     - high: 6h

3. Coaching language policy:
   - low confidence: supportive + explicit uncertainty + next question
   - medium confidence: neutral + top risks + recommended next step
   - high confidence: direct recommendation + concise rationale

4. Critical suitability pre-send policy:
   - unresolved critical -> block send
   - override requires actor + reason + timestamp
   - acknowledge-only path for juniors still requires owner approval

5. Junior outbound approval policy:
   - direct send only when no criticals, no review-required state, confidence above threshold
   - otherwise owner approval required

---

## Implementation Evidence

- `src/analytics/policy_rules.py` (single-source policy logic)
- `spine-api/server.py` (`PATCH /trips/{trip_id}` ready-gate enforcement)
- `src/analytics/engine.py` (owner escalation + send-policy computation)
- `src/analytics/review.py` (revision-loop escalation handling)
- `spine-api/persistence.py` (traveler/internal bundle persisted for readiness checks)

## Verification Evidence

Executed:

```bash
PYTHONPATH=. uv run pytest -q \
  tests/test_policy_rules.py \
  tests/test_review_policy_escalation.py \
  tests/test_review_logic.py
```

Result:
- 9 passed
- 0 failed

---

## Rollout Note

This ratification captures policy + implementation + test evidence in one place so future scenario runs can verify behavior against a stable operational contract.
