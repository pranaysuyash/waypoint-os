# travel_agency_agent Agent Instructions

## Source Hierarchy

1. Repo-local `AGENTS.md` (this file)
2. Workspace-level `/Users/pranay/Projects/AGENTS.md`
3. `Docs/context/agent-start/AGENT_KICKOFF_PROMPT.txt` and `Docs/context/agent-start/SESSION_CONTEXT.md`

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
| Design system audit  | `rendered-design-system-audit`   | ~/.hermes/skills/ + `tools/rendered-design-system-audit/` |

## Workspace Alignment (Adopted)

- Ensure `Docs/context/agent-start/AGENT_KICKOFF_PROMPT.txt` and `Docs/context/agent-start/SESSION_CONTEXT.md` are loaded before substantive implementation.
- Prefer repository docs and existing scripts over ad-hoc process invention.
- Keep changes small, explicit, and path-cited in summaries.
- Do not claim platform limitations when the gap is implementable; state what is possible, what is implemented, and the concrete path.
- For skill discovery, prioritize project-level skills under `/Users/pranay/Projects/skills/` before defaulting to other skill stores.

## Working Style (User Preference)

- Solutions must be elegant, built from first principles, scalable, long-term, better, comprehensive, and architecturally correct.
- Maintain a vision-oriented approach while staying open to updates and avoiding rigidity.
- Treat "works with the current code" as necessary but not sufficient. The expected bar is a first-principles solution that is long-term coherent, scalable, additive, better than the existing state, and compatible with the intended architecture.
- When recovering or evaluating partial work, do not reject a direction merely because it requires architectural work. Separate "right long-term direction" from "unsafe partial implementation," then recover the direction through a comprehensive, verified implementation path.

## Preview & Feedback (Critical)

**Rule**: Before showing work to the user for feedback, **always start the servers first**:
1. **Backend**: `cd spine_api && uv run uvicorn spine_api.server:app --port 8000`
2. **Frontend**: `cd frontend && npm run dev` (Next.js on :3000)

**Why**: User needs to see live preview immediately when giving feedback. Don't make them wait or ask them to start servers.

**Verification**: After starting servers, verify:
- `curl -s http://localhost:8000/health` returns OK
- `curl -s -o /dev/null -w "%{http_code}" http://localhost:3000` returns 200

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

## Package / Dependency Preference

Before writing custom code for any well-understood functionality, **always search for an existing package first.**

1. **Prefer battle-tested dependencies.** If a reputable library already solves the problem (e.g. `date-fns` for date math, `zod` for validation, `set-cookie-parser` for cookie parsing, `lodash` for utilities), use it — whether or not it's already in the dependency tree.
2. **Do not build from scratch** unless:
   - no package exists that does exactly what you need
   - the package has security issues, is unmaintained, or is poorly tested
   - the custom implementation is genuinely simpler and more correct than adding a dependency
3. **Rationale:** Vendor code is battle-tested, typed, and maintained by domain experts. Hand-rolling equivalent logic introduces bugs, bloats the codebase, and wastes engineering time.
4. **Exception:** one-liner utilities where introducing a dependency is heavier than the code (e.g. a single `Array.prototype.map` call).

### Scope (Non-exhaustive)
- Date/time math, formatting, parsing
- Form validation, schema validation
- Cookie parsing / serialization
- Query string / URL parsing
- Deep cloning / merging
- Debounce / throttle / memoization
- UUID / nanoid generation
- CSV / JSON parsing
- Color manipulation
- Unit conversion
- Currency formatting
- Slug generation
- HTML sanitization
- Markdown parsing
- Anything else where npm registry or PyPI has a well-maintained solution

## Performance Optimization Patterns (Critical)

Before writing new code, check if these patterns apply to your task:

### 1. O(n) → O(1) Lookups

**Problem**: Using `any()` generators or list scans on sets/dicts.
**Fix**: Use `in` operator for set/dict membership (O(1)).
```python
# BAD: O(n) scan on a set
any(x.lower() == target for x in my_set)

# GOOD: O(1) hash lookup
target in my_set  # if elements already normalized
```

**Real example**: `is_known_city_normalized()` in `src/intake/geography.py` was doing O(n) scan on a 590k-city set. Fixed: `name_lower in all_cities` (O(1)).

### 2. functools.lru_cache for Repeated Calls

**Problem**: Functions called many times with same args recompute every time.
**Fix**: Use `@lru_cache(maxsize=N)` for deterministic functions.

```python
from functools import lru_cache

@lru_cache(maxsize=32)  # Power-of-2, covers all inputs
def _month_to_num(month_str: str) -> Optional[int]:
    return _MONTH_MAP.get(month_str.lower()[:3].rstrip("e")) or _MONTH_MAP.get(month_str.lower())
```

**When to use**:
| Scenario | Approach |
|----------|----------|
| Module-level constant, built once | Global variable (like `_MONTH_MAP`) |
| Function result depends on args, called repeatedly | `@lru_cache` |
| Function result is constant, called multiple times | `@lru_cache(maxsize=1)` |
| Lazy init with complex logic | Global `None` + init check |

**Real example**: `_month_to_num()` in `extractors.py`, `_get_forbidden_terms()` in `orchestration.py`.

### 3. __slots__ for Memory Efficiency (Python 3.10+)

**Problem**: Dataclasses create `__dict__` per instance (~56 bytes overhead).
**Fix**: Use `@dataclass(slots=True)` for high-frequency dataclasses.

```python
@dataclass(slots=True)
class Slot:
    value: Any = None
    confidence: float = 0.0
```

**Impact**: For 10,000 instances: ~560KB saved (no `__dict__` overhead).
**Cookie**: After adding `slots=True`, code using `vars(obj)` or `obj.__dict__` breaks. Fix:
- Use `dataclasses.asdict(obj)` for serialization
- Update helpers like `_to_dict()` to check `is_dataclass(obj)` before `hasattr(obj, "__dict__")`

**Applied to**: All 39+ dataclasses across `packet_models.py`, `gates.py`, `validation.py`, `strategy.py`, `decision.py`, `suitability/models.py`, etc.

**Reference**: `Docs/performance_optimization_geography_lru_cache_slots_2026-05-01.md`

### 4. Verify Data Normalization

**Problem**: Looking up `name.lower()` in a mixed-case set never matches.
**Fix**: Verify both sides of the lookup use the same normalization.

```python
# BROKEN: _BLACKLIST has "January", lookup is lowercase
if name.lower() in _BLACKLIST:  # Never matches!

# FIXED: Cache a lowercase version
_BLACKLIST_LOWER = {b.lower() for b in _BLACKLIST}
if name.lower() in _BLACKLIST_LOWER:  # Works
```

### 5. Don't Recreate Constant Data Structures

```python
# BAD: Creates new set on every call
if x in {item.lower() for item in my_list}:
    ...

# GOOD: Pre-build or cache
_LOWER_SET = {item.lower() for item in my_list}  # Module level
# or
@lru_cache(maxsize=1)
def _get_lower_set():
    return {item.lower() for item in my_list}
```

---

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
- No documentation should be lost. Do not delete historical, planning, review, research, scenario, status, or worklog documentation unless the user explicitly authorizes that exact deletion in the current conversation.
- Preserve and archive instead of deleting. If a doc is obsolete, superseded, renamed, or moved, keep a pointer or archive copy with rationale and date.
- During stash/reset/reflog recovery, any doc deletion in a candidate patch is rejected by default. Only accept doc changes that add, preserve, clarify, or relocate content without losing history.
- When updating docs, preserve prior context using archival files where needed.
- Maintain clear phase separation and rationale for documentation changes.
- Always check actual environment date before updating documentation.
- Keep project-related artifacts inside the project tree. Do not place project notes, reports, worklogs, or handoff content in `/tmp`, `.agent/`, `.codex/`, or other out-of-repo folders when an in-repo location exists.

### Verification Discipline

- Before moving to the next task, verify code still works.
- After verification, run tests.
- Record key verification outcomes in docs.

### API Contract Verification (Critical — Mandatory for FE/BE Integration Work)

**Rule: Never assume the shape of API responses. Test the real contract first.**

When modifying code that crosses the frontend/backend boundary (e.g., a frontend component consuming a backend endpoint, or vice versa), you MUST verify the actual data shape before writing any consumer code.

**Why this matters:** Frontend types, mocks, and assumptions often drift from the real backend response. Writing code against an imagined contract causes runtime crashes (e.g., `TypeError: Cannot read properties of undefined`) that TypeScript and unit tests cannot catch.

**Mandatory steps for any integration task:**

1. **Inspect the backend response directly**
   ```bash
   # Example: submit a run and inspect the actual JSON
   curl -s -X POST http://localhost:8000/run \
     -H "Authorization: Bearer <token>" \
     -d '{"raw_note":"test"}' | python3 -m json.tool
   
   # Then poll for status and look at the real shape
   curl -s "http://localhost:8000/runs/$RUN_ID" \
     -H "Authorization: Bearer <token>" | python3 -m json.tool
   ```
   Or read the backend source (`spine_api/server.py`, `spine_api/contract.py`) to see the exact Pydantic model fields.

2. **Compare backend output to frontend types**
   - Check `frontend/src/types/spine.ts` and `frontend/src/types/generated/spine-api.ts`
   - If they don't match the real API response, update the types FIRST.

3. **Write frontend code ONLY against the verified shape**
   - Use optional chaining (`?.`) and nullish coalescing (`??`) for every nested field access.
   - Never access `.length`, `.map()`, or property keys without guarding against `undefined`.

4. **Test end-to-end before claiming it works**
   - Submit a real request through the frontend BFF proxy (`/api/spine/run`) or directly to the backend.
   - Verify the UI renders correctly with the actual response data.
   - Screenshot or describe what you see. Do not say "it works" based on build passing or unit tests alone.

**Real example of failure from 2026-04-29:**
- Backend `RunStatusResponse.validation` returns: `{status: "ESCALATED", gate: "NB01", reasons: ["..."]}`
- Frontend assumed: `{is_valid: false, errors: [{field, message}], warnings: [...]}`
- Result: `TypeError: Cannot read properties of undefined (reading 'length')` on `.errors.length`
- Root cause: Agent modified frontend without ever `curl`-ing the real API response.

**Penalty for skipping this:** Wasted user time, broken production UI, and forced rollback.

### Reusable Tools

- Build reusable tools, not throwaway scripts.
- Save helper utilities in `tools/` with descriptive names.
- Document tools in `tools/README.md` with purpose, usage, and examples.
- Prefer portable implementations (HTML/JS for UI tools, Python for CLI tools).
- Do not create throwaway useful tools in `/tmp`.

### Code Preservation

- All new, revised, or recovered code must be additive, better, and comprehensive against the current codebase. "Additive" means preserving product intent and useful capability while improving the implementation; it does not mean leaving legacy, duplicate, broken, stale, or lower-quality code in place.
- When newer code fully covers older code's intent and behavior, consolidate to the better implementation. Remove or replace the worse legacy path only after applying the Supersession Workflow below.
- When legacy code has unique useful behavior, do not delete it. Merge that behavior into the canonical implementation first, verify, then remove the redundant legacy shell if it is truly superseded.
- Never delete code to silence warnings without explicit user approval.
- For unused identifiers, prefer non-destructive refactors (for TS, underscore prefix convention where applicable).
- Preserve code intent and structure; ask if deletion is unclear.
- **Redundant superseded code**: If a component/function is fully replaced by another that does the same job better, removal is preferred over keeping dead code. Document the removal briefly in the commit message (e.g., "Remove WorkbenchTab — superseded by Tabs component which provides identical ARIA functionality"). Do NOT keep code that serves no purpose and will rot — that creates confusion and maintenance debt.
- **Unused but potentially useful**: This is different from redundant. A utility hook, type definition, or helper that isn't currently called but serves a clear purpose for upcoming work — keep it. Use underscore prefix if lint complains.

### Supersession Workflow (Critical — Required Before Any Removal)

Before removing **any** code (function, type, component, export), apply this workflow. No exceptions.

0. **Re-read instruction files** — Before starting any removal analysis, re-read `AGENTS.md` (Code Preservation section), `Docs/context/agent-start/AGENT_KICKOFF_PROMPT.txt`, and `Docs/context/agent-start/SESSION_CONTEXT.md` to check for project-specific constraints or guardrails that may apply to this removal. If sources conflict, surface the conflict and ask before proceeding.
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

### Stash / Reset / Recovery Discipline (Critical)

- Do not use `git reset`, `git checkout --`, `git restore`, `git clean`, `git stash pop`, or `git stash apply` as workflow shortcuts. These commands can hide, delete, or regress other agents' and users' work.
- If a stash or reflog commit might contain useful work, inspect it first with read-only commands (`git stash show`, `git show`, `git diff`, `git diff-tree`, `git reflog`). Compare each touched file against the current tree before deciding what to keep.
- Never apply a stash wholesale unless the user explicitly authorizes that exact operation in the current conversation. Prefer selective patching of only changes that are additive, better, comprehensive, and compatible with current architecture.
- Reject any stash/commit fragment that reintroduces duplicate API routes, stale imports, deleted documentation, removed tests, downgraded validation, or behavior that current commits already fixed.
- When recovering from another agent's stash/reset, document the decision per file: merged, already present, rejected, or needs user decision. Keep the stash intact unless the user explicitly asks to drop it.
- If an agent previously used stash/reset carelessly, treat that as a process defect: add or update a repo-local guardrail and run verification before claiming recovery is complete.

### Commit Message Rules (Critical)

- **NEVER** add `Co-Authored-By` or any attribution lines to commit messages.
- All commits are authored by the project owner only.
- Commit messages should be concise and descriptive without external credits.

## Current Project Guardrails

- Preserve existing `memory/` contents; do not remove memory artifacts unless explicitly instructed.
- Keep institutional-memory and GTM decision artifacts under `Docs/context/`.
- Keep internal-only process notes under `Archive/context_ingest/internal_notes_*`.

### Data Safety: Test Data Must Be Additive (2026-05-03)

**Rule: Under NO circumstances may you overwrite, truncate, delete, or reset the existing test database (`waypoint_os` Postgres) when seeding or running tests.**

The default test agency ID is `d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b` (user: `newuser@test.com`).
This agency contains persistent trip data representing the developer's working environment.

**What this means in practice:**

1. **`TRIPSTORE_BACKEND=sql` must remain in `.env`** — do not revert to file store, which would silently lose all SQL trips.
2. **Test scripts that seed trips must INSERT with `ON CONFLICT DO NOTHING` logic** — skip existing, never replace all.
3. **Never run `TRUNCATE` or `DELETE` on production or test databases without explicit user permission.**
4. **The `seed_test_user.py` script is additive by design** (`aget_trip` skip — check existing before inserting).

**Root cause learned 2026-05-03:** Previous agent restarted uvicorn without `TRIPSTORE_BACKEND=sql` → file store activated → 40 Postgres trips became invisible → `count=0` in UI → user thought 55 trips were "missing." In reality, backend was looking at the wrong database.

**Dual-Store Architecture Warning:** The `TripStore` facade (`spine_api/persistence.py`) supports both JSON file store (`data/trips/`) and PostgreSQL via `TRIPSTORE_BACKEND` env var. The default is **file store** if the env var is absent. This creates a split-brain where:
- Auth data (Users, Agencies, Memberships) is always in PostgreSQL ✅
- Trip data may be in file store OR PostgreSQL depending on env ⚠️
- **This ambiguity caused the "missing trips" bug on 2026-05-03**

**Resolution:** `TRIPSTORE_BACKEND=sql` is pinned in `.env`. Future agents must never remove this or trips will silently evaporate from the UI.

**Long-term:** Migrate to PostgreSQL as the sole persistence layer to eliminate dual-store risk.

**If you ever need to create a clean test DB:**
- Clone the existing test DB (`createdb waypoint_os_copy --template waypoint_os`) first
- Operate on the copy, never the original
- Document the change in `Archive/` with datestamp

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
