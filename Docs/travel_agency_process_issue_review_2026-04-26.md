# Travel Agency Process Issue Review: 2026-04-26

**Audited doc**: `Docs/personas_scenarios/ADDITIONAL_SCENARIOS_152_REMOTE_WORK_TRAVEL_SETUP.md`
**Audit date**: 2026-04-26
**Status**: Decisions recorded. Docs-only cleanup underway. No code changes.

---

## Decisions Made (Non-Reversible Product/Scope)

### 1. Remote Work / Digital Nomad Travel

**Decision**: NOT in current launch scope.

**Rationale**: The current product (Waypoint OS) has unfinished auth/security launch blockers. Remote work is a new product vertical — it expands across intake, decision rules, visa logic, itinerary planning, frontend types, and tests. Adding it now would cross-cut 5+ modules before the core flow is verified.

**Affected scenarios** (all remain as exploratory inputs, NOT implementation commitments):
- `ADDITIONAL_SCENARIOS_56_REMOTE_WORK_TRAVEL.md`
- `ADDITIONAL_SCENARIOS_74_DIGITAL_NOMAD_LONG_STAY_VISA_PLAN.md`
- `ADDITIONAL_SCENARIOS_132_TECHNOLOGY_FAILOVER_FOR_REMOTE_WORK.md`
- `ADDITIONAL_SCENARIOS_152_REMOTE_WORK_TRAVEL_SETUP.md`
- `ADDITIONAL_SCENARIOS_193_DIGITAL_NOMAD_AND_REMOTE_WORK_TRAVEL.md`
- `ADDITIONAL_SCENARIOS_277_REMOTE_WORKFORCE_RELOCATION_TRAVEL.md`
- `ADDITIONAL_SCENARIOS_329_NOMAD_PIVOT.md`
- `AREA_DEEP_DIVE_WORKCATIONS.md` (WORK-001 through WORK-006)

**Deferred items**:
- Implementation of any remote work / digital nomad features
- `SCENARIO_HANDLING_SPEC.md` subsystem implementation
- `visa_timeline.py` extension for digital nomad visas
- Bleisure (work+leisure) pipeline model
- Coworking taxonomy / workspace recommendation module
- Internet speed / connectivity verification module
- `StructuredRisk` full model vs current `RiskFlag`
- Bulk scenario-to-pipeline mapping for the 287+ additional scenarios

**What may proceed later**: Only if a separate product decision explicitly puts remote work in scope.

### 2. Current Priority Order (Preserved)

```
1. Auth/security launch blockers (middleware.ts auth guards, backend get_current_user on data routes, remove localStorage token fallback, browser dogfood auth flow)
2. Runtime browser dogfooding
3. Resolve uncommitted suitability UI work
4. Docs/roadmap cleanup if still needed
5. Remote work only after explicit product decision
```

---

## Decisions Deferred / Open (Reversible)

| Item | Why deferred | Evidence | What would unblock |
|---|---|---|---|
| Scenario deduplication (7 duplicate remote work files) | Docs-only, deferred alongside all remote work | `Docs/personas_scenarios/ADDITIONAL_SCENARIOS_*.md` (#56, #74, #132, #152, #193, #277, #329) | Decision to keep remote work as a domain implies consolidation will be needed |
| Bulk pipeline mapping (20 of 379 mapped) | Too large, not blocking launch | `SCENARIOS_TO_PIPELINE_MAPPING.md` covers 20; 287 unmapped | Strategic decision on whether ALL ADDITIONAL_SCENARIOS need mapping or only those in scope |
| Inconsistent scenario metadata format | Good idea, not launch-critical | Three formats coexist across 379 files | Dedicated docs-hygiene phase after launch |

---

## Quick Wins Done / Underway

| Item | Action | Status |
|---|---|---|
| ISSUE-003: Stale scenario counts | Update `EXECUTIVE_SUMMARY.md` and `README.md` with actual counts | ⬜ To do |
| ISSUE-007: Orphaned backlog items | Add "Deferred/Future" note for Remote Work Integration Layer | ⬜ To do |

---

## Issues Explicitly Rejected (Not Implementing Now)

| Issue ID | Title | Rejection reason |
|---|---|---|
| ISSUE-001 | Remote work domain zero implementation | Deferred. No code. Product decision needed later. |
| ISSUE-002 | 93% scenarios unmapped | Deferred. Mapping 287 scenarios is not a launch blocker. |
| ISSUE-004 | 7 duplicate remote work scenarios | Deferred. Deduplication only matters if domain is kept. |
| ISSUE-005 | Work visa invisible to visa_timeline | Deferred. No code. Extension only if remote work in scope. |
| ISSUE-006 | SCENARIO_HANDLING_SPEC unimplemented | Deferred. Full subsystem, not for launch phase. |
| ISSUE-008 | No bleisure pipeline model | Deferred. Feature area, not part of core travel agency flow. |
| ISSUE-009 | Inconsistent scenario metadata | Deferred. Good but not launch-critical. |

---

## What Was Not Invented

All findings are repo-evidence based. No external assumptions. No hallucinated issues. No false "missing" claims without search evidence. Every claim cites file path or search result.

---

## Handoff Notes

Current order of work remains unchanged:

1. **P0: Auth/security launch blockers** — do not defer
2. **P1: Browser dogfood, suitability UI** — do not defer
3. **P2: Docs/roadmap hygiene** — this work unit fits here
4. **P3+: Remote work, scenario mapping, dedup, spec implementation** — only after explicit product decision

Next agent should resume auth/security work unless explicitly instructed to do docs cleanup.

---

*Checklist applied: AGENTS.md Supersession Workflow, External Review Evaluation Workflow*
