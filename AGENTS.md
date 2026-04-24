# travel_agency_agent Agent Instructions

## Source Hierarchy

1. Repo-local `AGENTS.md` (this file)
2. Workspace-level `/Users/pranay/Projects/AGENTS.md`
3. `.agent/AGENT_KICKOFF_PROMPT.txt` and `.agent/SESSION_CONTEXT.md`

If instructions conflict, follow the stricter rule and cite concrete file paths.

## Skills Ecosystem (Critical — Read Before Any Task)

**⚠️ DO NOT default to gstack.** You have 3,000+ skills across 5 locations. Always check ALL locations for relevant skills before assuming one doesn't exist.

### Skill Locations (Check in Order)

1. **`~/.claude/skills/*/`** — ~72 skills (Claude Code built-ins)
2. **`~/.agents/skills/*/`** — ~98 skills (All agents, includes Azure/Marketing stack)
3. **`~/Projects/skills/*/`** — 143 skills (Most curated, engineering focus) ⭐ **CHECK THIS FIRST**
4. **`~/Projects/external-skills/*/`** — 2,898+ skills (Community imports)
5. **`~/Projects/openai-skills/`** — OpenAI Codex skills (official standard repo copy)
6. **`$CODEX_HOME/skills/*/`** — Codex runtime-installed skills (when CODEX_HOME is set)
7. **`~/.codex/skills/*/`** — Codex local saved skills (default path)
8. **`~/.codex/skills/.system/*/`** — Codex app bundled/system skills (read-only baseline)

### Reference

- **Master catalog**: `/Users/pranay/Projects/SKILLS_CATALOG.md`
- **Workspace rules**: `/Users/pranay/Projects/AGENTS.md`

### Common Task → Right Skill

| Task                 | Use This Skill                   | Location           |
| -------------------- | -------------------------------- | ------------------ |
| Debug/troubleshoot   | `systematic-debugging`           | ~/Projects/skills/ |
| Write tests          | `tdd-workflow`, `e2e-testing`    | ~/Projects/skills/ |
| QA testing           | `qa`, `qa-only`                  | ~/.agents/skills/  |
| Verify before done   | `verification-before-completion` | ~/Projects/skills/ |
| Research before code | `search-first`                   | ~/Projects/skills/ |
| UI screenshots       | `browse`                         | ~/.agents/skills/  |
| Visual QA            | `design-review`                  | ~/.claude/skills/  |

## Workspace Alignment (Adopted)

- Ensure `.agent/AGENT_KICKOFF_PROMPT.txt` and `.agent/SESSION_CONTEXT.md` are loaded before substantive implementation.
- Prefer repository docs and existing scripts over ad-hoc process invention.
- Keep changes small, explicit, and path-cited in summaries.
- Do not claim platform limitations when the gap is implementable; state what is possible, what is implemented, and the concrete path.
- For skill discovery, prioritize project-level skills under `/Users/pranay/Projects/skills/` before defaulting to other skill stores.

## Naming Conventions (Critical — Prevent Future Symlinks)

**Problem prevented**: `spine-api/` (hyphen) vs `spine_api` (underscore) required a symlink because Python imports need underscores. This is pre-launch — no backward compat needed.

**Rules**:
1. **Directory names** must match the language convention:
   - Python projects: Use `underscores` (e.g., `spine_api/`, not `spine-api/`)
   - JavaScript/TypeScript projects: Use `hyphens` or `camelCase` per project convention
2. **Never create symlinks** to fix naming mismatches. Fix the directory name instead.
3. **Pre-launch products**: No backward compatibility concerns — rename confidently.
4. **Verify imports** after rename: `grep -r "old_name" --include="*.py" --include="*.ts" .`

**Enforcement**:
- Before creating any directory: check if the language requires underscores (Python) or hyphens (JS/TS)
- If you find a symlink fixing a naming mismatch: **delete symlink + rename directory** immediately
- Add this check to every task: "Does the directory name match language conventions?"

## Default Task Lifecycle (Adopted)

1. Analyze request and constraints.
2. Document baseline scope/assumptions.
3. Plan implementation order.
4. Research needed details.
5. Document decision rationale.
6. Implement scoped changes.
7. Verify functionality and run tests.
8. Document outcomes and pending items.

## Autonomous Review + Handoff Protocol (Critical)

When asked to review implementation work and/or propose new tasks for an implementation agent:

1. **Do not repeatedly ask the user for process preferences.**
2. **Automatically apply** `Docs/IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md`.
3. Produce an evidence-first review and a concrete, atomic task package.
4. Include the confirmation line:

- `Checklist applied: IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md`

Only ask a clarification question if blocked by:

- contradictory instructions,
- missing critical artifact for a safety decision,
- destructive action needing explicit approval.

## External Review Evaluation Workflow (Critical Addition)

When receiving external reviews (human or model), do NOT treat them as authority. Apply this critical evaluation:

### Step 1: Source Assessment

- Is this a static document or living feedback loop?
- When was it last updated relative to codebase changes?
- Who owns it and can iterate on it?

### Step 2: Architectural Soundness Check

Evaluate each recommendation against:

- **Layer ownership** (per V02_GOVERNING_PRINCIPLES): Does this recommendation respect which layer owns what?
- **Additive vs. destructive**: Does it add capability or refactor existing working code?
- **Blast radius**: How many files/modules does it touch? >5 files = treat as "ocean" not "lake"
- **Backward compatibility**: Can it be implemented without breaking existing contracts?

### Step 3: Sequencing Challenge

- Does the review recommend parallel work that should be sequential?
- Is the blast radius justified by the value?
- Can it be decomposed into smaller, verifiable chunks?

### Step 4: Current State Verification

- Before implementing, verify the recommendation against ACTUAL codebase state
- Don't assume external reviewers have fresh context
- Check if issues they mention were already fixed, or if the architecture already changed

### Step 5: Decision Documentation

For each recommendation, document:

- **ACCEPT**: Implement as suggested (low risk, high value)
- **ACCEPT+MODIFY**: Implement with changes (explain divergence)
- **DEFER**: Acknowledge but don't implement now (tag with reason)
- **REJECT**: Explicitly reject with rationale (don't silently ignore)

### Step 6: Verification Before Proceeding

- Run full test suite before AND after implementation
- Verify no regressions in unrelated areas
- Confirm the fix actually addresses the root cause (not just symptom)

**Example format**: See `Docs/SPINE_HARDENING_PLAN_STAGE_2_2026-04-15.md` for how this workflow was applied to the destination ambiguity review.

## Repo-Specific Development Rules

### Documentation and Tracking

- Always document work including notes, pending tasks, and completed tasks.
- Do not delete historical documentation. Preserve and archive instead.
- When updating docs, preserve prior context using archival files where needed.
- Maintain clear phase separation and rationale for documentation changes.
- Always check actual environment date before updating documentation.

### Verification Discipline

- Before moving to the next task, verify code still works.
- After verification, run tests.
- Record key verification outcomes in docs.

### Reusable Tools

- Build reusable tools, not throwaway scripts.
- Save helper utilities in `tools/` with descriptive names.
- Document tools in `tools/README.md` with purpose, usage, and examples.
- Prefer portable implementations (HTML/JS for UI tools, Python for CLI tools).
- Do not create throwaway useful tools in `/tmp`.

### Code Preservation

- Never delete code to silence warnings without explicit user approval.
- For unused identifiers, prefer non-destructive refactors (for TS, underscore prefix convention where applicable).
- Preserve code intent and structure; ask if deletion is unclear.
- **Redundant superseded code**: If a component/function is fully replaced by another that does the same job better, removal is preferred over keeping dead code. Document the removal briefly in the commit message (e.g., "Remove WorkbenchTab — superseded by Tabs component which provides identical ARIA functionality"). Do NOT keep code that serves no purpose and will rot — that creates confusion and maintenance debt.
- **Unused but potentially useful**: This is different from redundant. A utility hook, type definition, or helper that isn't currently called but serves a clear purpose for upcoming work — keep it. Use underscore prefix if lint complains.

### Supersession Workflow (Critical — Required Before Any Removal)

Before removing **any** code (function, type, component, export), apply this workflow. No exceptions.

0. **Re-read instruction files** — Before starting any removal analysis, re-read `AGENTS.md` (Code Preservation section), `.agent/AGENT_KICKOFF_PROMPT.txt`, and `.agent/SESSION_CONTEXT.md` to check for project-specific constraints or guardrails that may apply to this removal. If sources conflict, surface the conflict and ask before proceeding.
1. **Identify the candidate for removal** and its supposed superset/replacement.
2. **Field-by-field comparison**: Compare all features, exports, props, type fields, and behavioral contracts. If the candidate has ANY feature the replacement lacks, the replacement is NOT a superset — stop and merge the missing features first.
3. **Call-site audit**: Grep for all references to the candidate. If any call site relies on a feature the replacement doesn't provide, the candidate is NOT redundant — stop.
4. **Verify add-first-then-remove**: If canonical types live elsewhere (e.g., `spine.ts`), add them to the canonical location FIRST. Verify build passes. Only THEN remove the local duplicate.
5. **Document the analysis**: Record the comparison table and verdict in the commit message or session notes. Format:
   ```
   Removal: <candidate> — superseded by <replacement>
   Comparison: <list each dimension checked>
   Call sites: <N> — all migrated
   ```
6. **Post-removal verification**: Run build + tests immediately after removal. If anything breaks, revert and re-analyze.
7. **Ask if unclear** — If at any step the deletion is unclear (e.g., the candidate has unique items, the replacement is not a strict superset, or intent is ambiguous), STOP and ask the user before proceeding. Do not assume.

### Issue Review Naming

- When an issue is identified and explicitly requires a review note, name the document:
  - `travel_agency_process_issue_review_<date>.md` (under `Docs/`)
  - Example: `travel_agency_process_issue_review_2026-04-15.md`
- This makes issue documents project-specific and discoverable
- Avoid model-specific naming in issue review files.

### Git Safety (Critical)

- Never commit or push without explicit user approval in the current conversation.
- Staging and checks are allowed proactively.
- Commit/push/merge only when user explicitly asks.

### Commit Message Rules (Critical)

- **NEVER** add `Co-Authored-By` or any attribution lines to commit messages.
- All commits are authored by the project owner only.
- Commit messages should be concise and descriptive without external credits.

## Current Project Guardrails

- Preserve existing `memory/` contents; do not remove memory artifacts unless explicitly instructed.
- Keep institutional-memory and GTM decision artifacts under `Docs/context/`.
- Keep internal-only process notes under `Archive/context_ingest/internal_notes_*`.

## Development Discipline & Comprehensive Quality Framework

### Core Principle

**Code-ready ≠ Feature-ready ≠ Launch-ready.**

A feature can have perfect code (all tests passing, zero bugs) yet be operationally incomplete (operators can't understand it) and not launchable (missing critical controls). This discipline establishes mandatory frameworks to prevent shipping incomplete features.

### Why This Matters

Single-pass code reviews miss defensive gaps. Mocked tests hide integration bugs. Code-only perspectives miss operator gaps. Without systematic discipline, quality plateaus at "code works, but users are confused."

This framework emerged from real work (Timeline schema fix, 2026-04-23) where code was production-ready (618 tests passing) but the feature was incomplete (missing suitability signals and override controls). The framework catches issues across three dimensions: code quality, feature completeness, and operator readiness.

### The 4-Phase Workflow

Every development task follows this mandatory cycle:

**Phase 1: Fix & Verify**

- Implement the change
- Run tests (baseline + after change)
- Build (zero compiler errors, clean TypeScript)
- Document what was changed and why
- Do not commit yet

**Phase 2: Review & Iterate** (Minimum 2 cycles on schema changes)

- Get first code review (focus: logic errors, data loss, breaking changes)
- Fix all findings
- Verify tests still pass (mandatory retest)
- Get second code review (focus: defensive gaps, fallback inconsistencies, edge cases)
- Fix all findings
- Verify tests still pass (mandatory retest)
- For non-schema changes, 1 review cycle is acceptable if reviewer approves

**Phase 3: Audit & Assess**

- Apply 11-dimension audit checklist (see below)
- Document status for each dimension (✅/🟡/❌)
- Identify gaps that block feature/launch
- Estimate effort and timeline for next phase
- Note: Some dimensions may be "N/A" for small changes

**Phase 4: Handoff & Document**

- Create comprehensive handoff document (minimum 10k characters)
- State explicit verdicts: Merge? Feature-ready? Launch-ready? Why or why not?
- Identify specific blocking dependencies (not vague, actionable)
- Provide realistic timeline and effort estimate
- Include architecture verification and verification evidence

### 11-Dimension Audit Checklist (Mandatory for All Features)

Apply to every feature. For small fixes, some dimensions may be N/A (document this).

| Dimension                 | What to Verify                                                                                           | Verdict  |
| ------------------------- | -------------------------------------------------------------------------------------------------------- | -------- |
| **Code**                  | Compiles, linter clean, tests pass, zero regressions, error handling explicit                            | ✅/🟡/❌ |
| **Operational**           | Can operators use day 1? UI complete? Audit trail visible? State changes clear?                          | ✅/🟡/❌ |
| **User Experience**       | Solves stated problem? UX intuitive? Error messages helpful? Performance OK?                             | ✅/🟡/❌ |
| **Logical Consistency**   | Assumptions documented? Edge cases handled? Business logic sound? State transitions correct?             | ✅/🟡/❌ |
| **Commercial**            | Enables monetization? Reduces cost? Improves retention? Defensible vs competitors?                       | ✅/🟡/❌ |
| **Data Integrity**        | No silent data loss? Invalid values clamped (not skipped)? Audit trail complete? Recoverable on failure? | ✅/🟡/❌ |
| **Quality & Reliability** | All code paths tested? Fallback paths consistent? Defensive programming applied? No flaky tests?         | ✅/🟡/❌ |
| **Compliance**            | Regulatory requirements met? PII handled correctly? Access controls enforced? Logging sufficient?        | ✅/🟡/❌ |
| **Operational Readiness** | Deployment steps documented? Rollback clear? Monitoring configured? Runbooks written?                    | ✅/🟡/❌ |
| **Critical Path**         | Blocking dependencies identified? What must ship first? What can run in parallel? Timeline clear?        | ✅/🟡/❌ |
| **Final Verdict**         | Merge: Yes/No/Depends? Feature-ready: Yes/No/Partial? Launch-ready: Yes/No/Pending X?                    | Explicit |

For each dimension marked 🟡 or ❌, document the specific gap and what would fix it.

### Code Review Iteration Pattern

**Mandatory minimum: 2 cycles for schema/contract changes.**

**Cycle 1 (Logic & Bugs):**

1. Reviewer reads diff
2. Looks for: logic errors, data loss, breaking changes, missing validation
3. Checks: Does the fix actually solve the stated problem?
4. Provides feedback
5. Author fixes all findings
6. Author reruns tests (must pass — no regressions allowed)

**Cycle 2 (Defensive & Edges):**

1. Reviewer reads changes again (now with context from cycle 1 fixes)
2. Looks for: defensive gaps, fallback path inconsistencies, edge cases, error handling symmetry
3. Checks: Are all error paths handled the same way? Do fallback paths behave like primary paths?
4. Provides feedback
5. Author fixes all findings
6. Author reruns tests (must pass)

**Real example (Timeline schema fix):**

- Cycle 1 found: confidence scores being skipped on validation failure → silent data loss
- Fix 1: Changed skip-on-invalid to clamp-to-0-100 + log error
- Tests rerun: 618 backend + 9 frontend ✅
- Cycle 2 found: fallback code path not applying same clamping logic → defensive inconsistency
- Fix 2: Added clamping to fallback path (lines 1103-1110)
- Tests rerun: all still passing ✅

**Non-schema changes:** 1 cycle is acceptable if reviewer explicitly approves and no data loss issues exist.

### Test Schema Validation Strategy

**Critical rule: Tests must validate REAL schema contracts between systems.**

**The Problem:**

- Old tests: TimelinePanel tests mocked schema as `{state: ...}`
- Actual backend: sends `{status: ...}`
- Result: Tests passed locally, failed against real backend
- Root cause: False confidence from mocked schemas

**The Solution:**

1. When schema changes, update backend implementation first
2. Verify backend tests pass
3. Update ALL frontend test mocks to use actual backend schema (not approximations)
4. Verify frontend tests pass
5. Tests now act as integration validators (fail if schema diverges)

**Pattern:**

- Never use old or simplified schemas in tests
- Every test mock must match the actual API contract exactly
- If test mocks diverge from real schema, tests give false confidence
- Real schema contracts catch integration bugs immediately

### 7 Reusable Development Patterns

These patterns are saved to AI memory and auto-suggested during future development tasks.

**Pattern 1: Comprehensive Development Workflow**

- Use the 4-phase approach (Fix → Review → Audit → Handoff) for all tasks
- Prevents ad-hoc processes and inconsistent quality

**Pattern 2: Code Review Iteration Strategy**

- Minimum 2 cycles on schema/contract changes
- First cycle catches logic errors
- Second cycle catches defensive gaps
- Reruns tests after each cycle (mandatory)

**Pattern 3: 11-Dimension Audit Checklist**

- Apply to every feature (even small ones)
- Documents status explicitly (✅/🟡/❌)
- Prevents shipping incomplete features
- Identifies blocking dependencies upfront

**Pattern 4: Test Schema Validation Approach**

- Real contracts, never mocks
- If backend schema changes, tests fail immediately
- Catches integration bugs in review, not production

**Pattern 5: Data Loss Prevention Pattern**

- Never skip data on validation failure
- Instead: clamp invalid values to valid range + preserve event + log error
- Example: confidence score 250 → clamp to 100 + log + preserve event
- Prevents information loss while maintaining integrity

**Pattern 6: Defensive Programming Fallback Paths**

- Apply identical validation rules to fallback code as primary code
- If primary path clamps values, fallback must also clamp
- Inconsistency = latent production bug
- Non-negotiable for production code

**Pattern 7: Feature vs Code Readiness Distinction**

- Code-ready = tests pass (no guarantee feature is complete)
- Feature-ready = solves user problem (no guarantee operators can use it)
- Launch-ready = operators can use day 1 with all controls
- Never claim "done" without explicit verdict on all three levels

### Handoff Document Template

Every work completion produces a handoff. Minimum structure:

**1. Executive Summary** (1 paragraph)

- What was done
- Current state: Code ✅? Feature 🟡? Launch ❌?
- Next immediate action

**2. Technical Changes** (detailed list)

- Files modified (with line numbers and why)
- Files created (with purpose)
- Schema changes (explicit contract)
- API changes (if any)

**3. Code Review Findings** (by cycle)

- Cycle 1: Issues found and fixed
- Cycle 2: Defensive gaps found and fixed
- Final verdict: Approved for merge? Why or why not?

**4. Test Results** (with evidence)

- Baseline tests passing (X count)
- After-change tests passing (X count)
- Regressions: zero (or explain)
- Coverage: percentage

**5. Audit Assessment** (one line per dimension)

- Dimension: verdict (✅/🟡/❌)
- Notable findings or gaps
- What would fix any 🟡 or ❌ items

**6. Launch Readiness** (explicit verdicts)

- Code ready: ✅ Yes / ❌ No (why?)
- Feature ready: ✅ Yes / 🟡 Partial (missing what?) / ❌ No
- Launch ready: ✅ Yes / 🟡 Pending X / ❌ No (blocking what?)

**7. Next Phase** (actionable)

- Specific blocking dependencies (not vague)
- Effort estimate and timeline
- What can start in parallel?
- Who owns next phase?

### When to Apply This Framework

**Apply full framework to:**

- Any feature development
- Schema or data contract changes
- Integration work
- Bug fixes affecting data flow

**Apply simplified (1-2 cycles, audit optional) to:**

- Documentation-only changes
- Typo / comment fixes
- Dependency updates (if build passes)
- Configuration file tweaks (if fully reversible)

### Real Example: Timeline Schema Fix (2026-04-23)

This framework was applied to resolve a production integration bug:

**Problem:** Frontend expected `{state: ...}` but backend sends `{status: ...}`

- TimelinePanel.tsx had wrong field names
- Tests mocked old schema, so they passed locally
- Real backend data caused failures

**Phase 1:** Fixed schema mappings in frontend and backend
**Phase 2 Cycle 1:** Found confidence scores being silently skipped on validation

- Changed to clamp instead of skip (preserves data)
- All tests rerun: 618 backend + 9 frontend passing ✅

**Phase 2 Cycle 2:** Found fallback code path not applying clamping

- Applied same clamping logic to fallback (defensive consistency)
- All tests rerun: still passing ✅

**Phase 3 Audit Results:**

- Code: ✅ (618 tests, zero regressions)
- Operational: 🟡 (can see timeline, but can't see why decisions were made)
- User: 🟡 (timeline visible, but operators still confused)
- Commercial: ❌ (missing controls prevent AI override decisions)

**Phase 4 Handoff:**

- Code ready: ✅ Yes, merge immediately
- Feature ready: 🟡 Partial (infrastructure complete, suitability signals missing)
- Launch ready: ❌ No (blocked on P0-01: suitability renderer, P1-02: override controls)
- Blocking dependencies explicit: P0-01 must ship before operators can launch

**Result:** Clear verdict prevented false "done" claim. Next team knows exactly what's blocking them.

### What This Framework Prevents

This discipline prevents:

- ❌ Code-only reviews missing operator gaps (11-dimension audit catches this)
- ❌ Single-pass reviews missing defensive gaps (2-cycle pattern catches this)
- ❌ Mocked tests hiding integration bugs (real schema validation catches this)
- ❌ Silent data loss on validation errors (clamping pattern prevents this)
- ❌ Fallback paths behaving differently (defensive consistency checks this)
- ❌ "Done" claims when feature incomplete (explicit verdict structure prevents this)
- ❌ Confusion about merge vs launch readiness (handoff template clarifies this)

### Getting Started

For your next development task:

1. **Read:** "The 4-Phase Workflow" section above
2. **Follow:** Phase 1 (Fix & Verify) → Phase 2 (2 review cycles) → Phase 3 (11-dim audit) → Phase 4 (handoff)
3. **Use:** Memory patterns auto-suggest during work (they're listed in your AI system)
4. **Apply:** 11-dimension audit checklist (even for small features)
5. **Document:** Explicit verdicts (code/feature/launch) in handoff

The discipline takes ~20% extra time upfront and saves 80% rework downstream. Apply it consistently.
