# Logical Policy Decisions Draft (P1-S0 + P2-S4)

- Date: 2026-04-23
- Scope: logical/product open items across:
  - `P1-S0` Solo Agent Happy Path
  - `P2-S4` Training Time Problem
- Status: superseded by ratified file
- Ratified file: `Docs/personas_scenarios/LOGICAL_POLICY_DECISIONS_RATIFIED_2026-04-23.md`

---

## Evidence Baseline (Docs + Code)

### P1 flow and continuity
- Scenario expectation:
  - `Docs/personas_scenarios/P1_SINGLE_AGENT_HAPPY_PATH.md`
- Journey test evidence:
  - `frontend/src/app/__tests__/p1_happy_path_journey.test.tsx`
- Current status mapping used by FE proxy:
  - `frontend/src/app/api/trips/[id]/route.ts`
- Current trip status update endpoint:
  - `spine-api/server.py` (`PATCH /trips/{trip_id}`)

### P2 coaching/review/escalation
- Scenario expectation:
  - `Docs/personas_scenarios/P2_TRAINING_TIME_PROBLEM.md`
- Review action state machine:
  - `src/analytics/review.py`
  - `spine-api/server.py` (`POST /trips/{trip_id}/review/action`)
- Autonomy policy controls:
  - `src/intake/config/agency_settings.py`
  - `frontend/src/app/settings/components/AutonomyTab.tsx`
- Suitability warning/override behavior:
  - `frontend/src/components/workspace/panels/SuitabilitySignal.tsx`
  - `frontend/src/components/workspace/panels/SuitabilityPanel.tsx`
  - `spine-api/server.py` (`POST /trips/{trip_id}/override`)
- Escalation/SLA reference model:
  - `Docs/ASSIGNMENT_ESCALATION_STATE_MACHINE_SPEC_2026-04-22.md`
  - `Docs/SUPPORT_AND_CUSTOMER_SUCCESS.md` (service tier SLA baseline)

---

## Proposed Decisions

## P1-S0 Decisions

### P1S0-L-01: `ready` state hard policy
- Current state:
  - UI has `Save` and review actions, but no explicit canonical "ready gate" checklist.
  - Backend supports status mutation (`new/assigned/in_progress/completed/cancelled`) but no enforced quality gate.
- Proposed policy:
  - `Ready` is allowed only when all are true:
    1. customer message present and non-empty,
    2. decision state is not `ASK_FOLLOWUP` and not `STOP_NEEDS_REVIEW`,
    3. traveler-safe output exists,
    4. all critical suitability flags are either resolved or explicitly acknowledged/overridden,
    5. if review is required, owner action is `approved`.
- Why:
  - Creates one consistent completion standard for agents and owners.

### P1S0-L-02: ambiguity policy for destination/date
- Current state:
  - NB02 already blocks multi-destination ambiguity to `ASK_FOLLOWUP`.
  - Tests confirm multi-candidate destination should not proceed traveler-safe.
- Proposed policy:
  - Destination/date ambiguity policy:
    1. if multiple destination candidates or conflicting date windows exist -> force follow-up,
    2. if destination is single and date window is broad but consistent -> allow internal draft with explicit "assumption" tag,
    3. traveler-safe output cannot proceed while blocking ambiguity remains.
- Why:
  - Aligns with existing engine behavior while clarifying a single business rule.

### P1S0-L-03: urgency policy (last-minute but non-emergency)
- Current state:
  - Decision engine suppresses some soft blockers under urgency; emergency has stronger override behavior.
- Proposed policy:
  - Distinguish urgency levels:
    1. emergency: safety-first routing, no auto traveler-safe send,
    2. high urgency non-emergency: suppress low-value soft blockers only, keep destination/date/budget blockers active,
    3. medium urgency: advisory downgrade only, not blocker removal.
- Why:
  - Prevents "time pressure" from bypassing critical trip correctness.

### P1S0-L-04: completion continuity semantics
- Current state:
  - Save and return-to-inbox behavior exists, but status semantics are not canonized for users.
- Proposed policy glossary:
  - `save`: persist current edits only; no stage completion claim.
  - `needs_correction`: returned to agent with explicit correction reason.
  - `ready`: passed ready gate and can move to next operational queue.
  - `return_to_inbox`: navigation action only; does not change status by itself.
- Why:
  - Removes user confusion between editing, review outcome, and workflow completion.

### P1S0-L-05: scenario traceability naming
- Current state:
  - Scenario IDs vary between persona docs/mapping references.
- Proposed policy:
  - Canonical scenario ID format: `<Persona>-S<index>` (example: `P1-S0`, `P2-S4`) across:
    - scenario file headings,
    - mapping tables,
    - test references,
    - report filenames.
- Why:
  - Prevents coverage/reporting drift.

## P2-S4 Decisions

### P2S4-L-01: onboarding KPI definition
- Current state:
  - No single approved KPI pack in scenario docs.
- Proposed KPI set:
  1. `time_to_independent_quote` (hours from onboarding start to first approved quote without owner edits),
  2. `owner_correction_rate` (% junior drafts requiring revision),
  3. `rework_cycles_per_quote` (count),
  4. `pre_send_risk_catch_rate` (% risky drafts blocked before send),
  5. `median_quote_turnaround` (junior vs baseline).
- Cadence:
  - weekly review for first 6 weeks per junior.
- Why:
  - Converts "training quality" into measurable outcomes.

### P2S4-L-02: owner escalation policy + SLA
- Current state:
  - Review actions and escalated status exist; no scenario-specific trigger matrix/SLA policy finalized.
- Proposed escalation triggers:
  - Auto route to owner when any is true:
    1. critical suitability flag present and unresolved,
    2. decision state is `STOP_NEEDS_REVIEW`,
    3. margin/policy threshold breach (per agency policy),
    4. repeated revision loop (`>=2` revision_needed on same trip).
- Proposed SLA:
  - Critical escalation: first owner response within 2 hours (business hours),
  - High escalation: within 6 hours (business hours),
  - Other owner reviews: same business day.
- Why:
  - Keeps junior throughput high without sacrificing risk control.

### P2S4-L-03: coaching language policy
- Current state:
  - Confidence-driven behavior exists but user-facing coaching tone is not formally standardized.
- Proposed tone matrix:
  - low confidence: supportive + explicit uncertainty + exact next question.
  - medium confidence: neutral guidance + top 2 risks + preferred next step.
  - high confidence: direct recommendation + concise rationale + confirmation cue.
- Guardrails:
  - Never imply certainty when confidence is below threshold.
  - Always include one actionable next step.
- Why:
  - Makes coaching predictable for juniors.

### P2S4-L-04: pre-send policy for critical suitability
- Current state:
  - UI marks critical as hard blockers; override and acknowledge capabilities exist.
  - A separate suitability acknowledge route for stage flow is not currently implemented in active API path.
- Proposed policy:
  - Pre-send contract:
    1. unresolved critical flag -> block send,
    2. override allowed only with reason + actor + timestamp,
    3. acknowledged without override still requires owner approval for junior users.
- Why:
  - Balances operational speed with accountable safety decisions.

### P2S4-L-05: customer communication approval policy (junior drafts)
- Current state:
  - Review workflow exists (`approve/reject/request_changes/escalate`) but not codified as a junior send policy.
- Proposed policy:
  - Junior outbound rules:
    1. low-risk + no critical flags + confidence above threshold -> can send with auto-log,
    2. any critical flag, review-required state, or low confidence -> owner approval required,
    3. all junior outbound messages retain review trace.
- Why:
  - Clarifies when juniors can act independently.

---

## Approval Questions

1. Do we ratify the `ready` gate exactly as listed in `P1S0-L-01`?
2. For escalation SLA, do you want strict business-hours clocks or absolute wall-clock clocks?
3. For junior outbound, should "medium confidence + no critical flags" be auto-send or owner-review by default?

---

## Suggested Next Documentation Step

After approval, update:
- `Docs/personas_scenarios/task_lists/P1_S0_LOGICAL_TASK_LIST_2026-04-23.md`
- `Docs/personas_scenarios/task_lists/P2_S4_LOGICAL_TASK_LIST_2026-04-23.md`

with:
- final policy text links,
- per-item status transition (`Open` -> `Decided`),
- implementation-ready acceptance criteria.
