# Implementation Agent Review + Handoff Checklist

**Purpose**: Standardize how this repository performs review and proposes next implementation tasks without repeatedly asking the user for process details.

**Usage rule**: When asked to review implementation work and/or propose next tasks for an implementation agent, follow this checklist by default.

---

## 1) Default document bundle (always read first)

Read these docs before producing a review or new implementation task package:

1. `Docs/DISCUSSION_LOG.md`
2. `Docs/FRONTEND_WAVE_2_READINESS_2026-04-18.md` (if frontend/workspace context exists)
3. `Docs/WAVE_A_HARDENING_SCORECARD_2026-04-18.md` (if backend agentic flow context exists)
4. `Docs/OPERATOR_RUN_RUNBOOK_2026-04-18.md` (if run lifecycle/events are in scope)
5. `Docs/MASTER_GAP_REGISTER_2026-04-16.md`
6. `Docs/DISCOVERY_GAP_ANALYTICS_REPORTING_2026-04-16.md`
7. `Docs/DISCOVERY_GAP_CONFIGURATION_MANAGEMENT_2026-04-16.md`

If a doc is superseded by a newer dated version, prefer the latest dated version and mention the replacement explicitly.

---

## 2) Scope-specific add-on docs (read by trigger)

### Backend / Agentic flow
- `Docs/BACKEND_WAVE_A_AGENTIC_FLOW_2026-04-18.md`
- `Docs/BACKEND_WAVE_A_IMPL_NOTES_2026-04-18.md`
- `Docs/ARCHITECTURE_DECISION_D1_AUTONOMY_GRADIENT_2026-04-18.md`

### Frontend / Workspace flow
- `Docs/FRONTEND_IMPROVEMENT_PLAN_2026-04-16.md`
- `Docs/FRONTEND_WAVE_1L_6H_NOTES_2026-04-18.md`

### Product / strategy alignment
- `Docs/FIRST_PRINCIPLES_FOUNDATION_2026-04-14.md`
- `Docs/FIRST_PRINCIPLES_GAP_ASSESSMENT_2026-04-14.md`

---

## 3) Evidence-first review steps (required)

1. Verify claimed files exist and read them.
2. Verify at least one relevant test/build command output (fresh evidence if possible).
3. Separate findings into:
   - **Verified implemented**
   - **Partially implemented**
   - **Claimed but unverified**
4. Explicitly call out risk level (`low`, `medium`, `high`) for each gap.

---

## 4) Standard review output format (always)

### A. Review verdict
- One-line status (e.g., `B+ foundation, hardening required`).

### B. What is verified
- Bullet list with exact file paths and test evidence.

### C. Gaps to close next
- Ordered by risk and dependency.

### D. Task package for implementation agent
For each task include:
- Objective
- Scope (in/out)
- Expected files to edit
- Acceptance criteria
- Verification commands
- Non-goals

### E. Decision gate
- Explicit go/no-go recommendation and why.

---

## 5) Autonomous behavior policy (no repetitive asking)

By default, do **not** ask the user to restate process preferences for review/handoff.
Proceed using this checklist unless one of these blockers exists:

1. Contradictory requirements between two instruction files.
2. Missing critical artifact required for a safety decision.
3. User requests destructive action without explicit approval.

If blocked, ask one concise clarification question and continue.

---

## 6) Task proposal quality bar (implementation-agent handoff)

Every proposed task must be:
- **Atomic**: can be completed and verified independently.
- **Traceable**: maps to specific docs/gaps/criteria.
- **Testable**: includes exact validation commands.
- **Non-destructive**: preserves existing behavior unless change is intentional.

Prefer a sequence of 2–5 atomic tasks over one large ambiguous task.

---

## 7) Checklist completion marker

When done, include this confirmation line in the review response:

`Checklist applied: IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md`