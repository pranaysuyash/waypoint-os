# P2-S4: The Training Time Problem

**Persona**: Agency Owner
**Scenario**: A new junior agent is spending too much time learning the business, and the owner needs the system to accelerate onboarding.

---

## Situation

A new hire is now part of the sales team.
The owner expects them to become productive in days, but they are still dependent after weeks.
Training is consuming senior agents’ time.

### What is happening now
- New agent asks the same questions repeatedly
- Senior agents review every quote manually
- Customers are waiting longer for responses
- The agency is paying for training, not productivity

### Owner concerns
- Training cost is too high
- Consistency across quotes is poor
- New agent confidence is low
- Knowledge is not embedded in the system

## What the system should do

1. **Guided workflows**
   - Provide step-by-step assistance for building a quote
   - Offer recommendations for hotels, budgets, and suitability

2. **Just-in-time coaching**
   - Explain why a recommendation is good or risky
   - Warn the agent before sending low-quality options

3. **Decision support**
   - Surface the customer’s priority clearly
   - Show how each choice affects budget and fit
   - Provide “best next action” suggestions

4. **Performance feedback**
   - Show confidence scores on the agent’s current quote
   - Highlight issues before the quote leaves the system
   - Capture learning outcomes for future review

## Required system behaviors

- Onboarding-focused UI behavior for junior agents
- Explanation of tradeoffs and rationale
- Safe quote validation before send
- Coaching prompts embedded in the workflow
- Tracking of junior agent quote quality over time

## Why this matters

Faster onboarding means lower cost and less dependence on senior staff.
This scenario proves the system can teach while it works.

## Success criteria

- The junior agent can produce a quote with minimal senior help.
- The system flags risky choices before sending.
- The business sees onboarding time drop.
- The agent gains confidence from clear guidance.

---

## Layman Explanation (Non-Technical)

This scenario checks if the product can train junior agents while they work, so owners do not need to manually review everything.

- Input:
  - A junior agent works on a quote with partial knowledge.
  - The owner expects the system to coach and catch risky choices.
- In the middle:
  - System evaluates confidence and quality signals.
  - System decides whether to proceed or ask follow-up.
  - System should show warnings and coaching in the workflow.
- Output:
  - Junior agent gets guidance in plain language.
  - Owner can see confidence/risk before quote goes out.
  - Bad options are blocked or flagged early.

In simple terms: `junior starts quote -> system coaches and checks risk -> owner sees safer output with less rework`.

## Case Study Execution (2026-04-23)

### Run intent
- Execute this scenario as a training/coaching case study with full observability.
- Validate confidence-based decisioning and UI coaching visibility.
- Capture FE/BE risks that affect onboarding quality.

### Scenario I/P -> Intermediate -> O/P (as tested)

#### Input (user-side)
- Junior-style low-confidence quote-building context.
- Owner/audit review mode checks.
- Suitability/coaching signal payloads in workspace panels.

#### Intermediate (system-side)
- NB02 decision logic for owner review/audit and structured decision result fields.
- NB03 confidence-to-tone mapping and assumption generation under uncertainty.
- Frontend suitability/coaching rendering and interaction contracts.

#### Output (user-side)
- Decision confidence behavior is correctly generated on backend.
- Coaching/suitability frontend tests expose significant UI test-contract drift.
- Training workflow remains partially validated due frontend failures.

### Execution evidence
- Case study report:
  - [/Users/pranay/Projects/travel_agency_agent/Docs/reports/P2_TRAINING_TIME_PROBLEM_OBSERVABILITY_2026-04-23.md](/Users/pranay/Projects/travel_agency_agent/Docs/reports/P2_TRAINING_TIME_PROBLEM_OBSERVABILITY_2026-04-23.md)
- Backend artifacts:
  - [/Users/pranay/Projects/travel_agency_agent/Docs/reports/p2_training_problem_backend_2026-04-23.xml](/Users/pranay/Projects/travel_agency_agent/Docs/reports/p2_training_problem_backend_2026-04-23.xml)
  - [/Users/pranay/Projects/travel_agency_agent/Docs/reports/p2_training_problem_backend_timing_2026-04-23.txt](/Users/pranay/Projects/travel_agency_agent/Docs/reports/p2_training_problem_backend_timing_2026-04-23.txt)
- Frontend artifacts:
  - [/Users/pranay/Projects/travel_agency_agent/Docs/reports/p2_training_problem_frontend_2026-04-23.json](/Users/pranay/Projects/travel_agency_agent/Docs/reports/p2_training_problem_frontend_2026-04-23.json)
  - [/Users/pranay/Projects/travel_agency_agent/Docs/reports/p2_training_problem_frontend_timing_2026-04-23.txt](/Users/pranay/Projects/travel_agency_agent/Docs/reports/p2_training_problem_frontend_timing_2026-04-23.txt)
- Compact summary:
  - [/Users/pranay/Projects/travel_agency_agent/Docs/reports/p2_training_problem_observability_summary_2026-04-23.json](/Users/pranay/Projects/travel_agency_agent/Docs/reports/p2_training_problem_observability_summary_2026-04-23.json)

### Key findings from this run
- Backend training-path confidence logic is healthy for sampled scenario coverage (6/6 pass).
- Frontend coaching/suitability test suite is unstable (27 pass, 14 fail, and one failed suite setup).
- A framework contract issue exists: integration suite failed before assertions with `jest is not defined` under vitest.
- Multiple suitability text/label assertions no longer match rendered UI copy, reducing confidence in training UX guardrails.

### Dependencies and external requirements observed
- Local Python + pytest runtime (`uv`) for backend scenario coverage.
- Local frontend vitest runtime (`npm`) for coaching/suitability coverage.
- No mandatory external network dependency for executed case-study runs.
- Agents used: none (no delegated sub-agents).

### FE/BE correction hooks (scenario-specific)
- FE:
  - Fix `jest` mocks in vitest integration suite (`vi.mock` migration or compatibility layer).
  - Realign suitability panel/signal tests with current UI semantics and copy contracts.
  - Add one true owner-review onboarding journey test (junior quote -> warning/coaching -> owner decision path).
- BE:
  - Maintain current confidence/owner-review behavior; no blocker found in this run.
  - Add an explicit regression test tying confidence score thresholds to owner-facing coaching levels.

### Open task lists (scenario-specific)
- Technical tasks:
  - [/Users/pranay/Projects/travel_agency_agent/Docs/personas_scenarios/task_lists/P2_S4_TECHNICAL_TASK_LIST_2026-04-23.md](/Users/pranay/Projects/travel_agency_agent/Docs/personas_scenarios/task_lists/P2_S4_TECHNICAL_TASK_LIST_2026-04-23.md)
- Logical tasks:
  - [/Users/pranay/Projects/travel_agency_agent/Docs/personas_scenarios/task_lists/P2_S4_LOGICAL_TASK_LIST_2026-04-23.md](/Users/pranay/Projects/travel_agency_agent/Docs/personas_scenarios/task_lists/P2_S4_LOGICAL_TASK_LIST_2026-04-23.md)
