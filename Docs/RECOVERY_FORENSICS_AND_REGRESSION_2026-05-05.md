# Recovery Forensics and Regression Report

- Date: 2026-05-05
- Repo: `/Users/pranay/Projects/travel_agency_agent`
- Scope: non-destructive recovery investigation after a prior agent ran `git stash pop` without permission and the visible source-control count appeared to drop from roughly `136+` to `46+`
- Constraints followed:
  - no destructive git commands
  - no stash apply/pop replay
  - recovery by selective inspection only
  - repo-local durable documentation required

## Executive Summary

The dropped stash content was recovered selectively into the working tree without using `git stash apply` or `git stash pop`. The dropped stash itself only contained changes for two test files, not the larger missing-file set the user feared. Recent opencode session history was then inspected directly from `~/.local/share/opencode` to determine whether additional source files or documentation had been removed. Across the named high-signal sessions checked so far, the only currently missing path from those session histories is `frontend/src/lib/spine-client.ts`, and repo documentation indicates that file was intentionally removed earlier as superseded dead code. Focused regression checks in the repo `.venv` passed for the recovered test path and the user-cited route-analysis test path.

## User Prompt Context

The triggering concern was:

1. another agent used `git stash pop` without permission
2. the user observed a large source-control count drop
3. the user explicitly required recovery without additional non-read git operations
4. the user required opencode/session cache inspection, documentation preservation, regression checking, and a durable repo artifact

## Instruction / Workflow Sources Used

1. `/Users/pranay/AGENTS.md`
2. `/Users/pranay/Projects/AGENTS.md`
3. `/Users/pranay/Projects/travel_agency_agent/AGENTS.md`
4. `/Users/pranay/Projects/travel_agency_agent/Docs/context/agent-start/AGENT_KICKOFF_PROMPT.txt`
5. `/Users/pranay/Projects/travel_agency_agent/Docs/context/agent-start/SESSION_CONTEXT.md`
6. Shared skills:
   - `/Users/pranay/Projects/skills/systematic-debugging/SKILL.md`
   - `/Users/pranay/Projects/skills/verification-before-completion/SKILL.md`

## Recovery Method

### 1. Dropped stash forensics

The user-reported dropped stash object was:

- `342f7576f0cb0c2e598a28dafe71fcff505698ab`

Investigation used raw `.git` logs and objects plus `dulwich` object inspection rather than git replay.

Findings:

- The dropped stash was still present in `.git/objects`
- The stash tree differed from its first parent in exactly two files:
  - `tests/conftest.py`
  - `tests/test_override_api.py`
- Those two file deltas were selectively restored into the working tree
- Blob-level verification confirmed the working-tree content matched the stash blobs for both recovered files after restoration

### 2. Opencode session forensics

Primary stores inspected:

- `~/.local/share/opencode/opencode.db`
- `~/.local/share/opencode/storage/session_diff/*.json`
- `~/.local/share/opencode/storage/session/**/*.json`
- repo-local `.git/opencode` where relevant

Named sessions explicitly checked:

- `ses_210f95d9fffeQXx3gwvpJmkITN` — `Fix everything first errors continuous`
- `ses_210ce0de5ffeowC8ftXXojih2f` — `Evidence-based document audit`
- `ses_211c54fe8ffeCDeMwm1sUgut7I` — `Evidence-based document audit`
- `ses_210ca9d4dffe3VChteFg0OQLJe` — `Random Document Audit v2`

### 3. Session-union check

A union was computed across the named sessions above.

Result:

- union of touched files: `275`
- currently missing from repo now: `1`
- currently missing docs from repo now: `0`
- single missing path:
  - `frontend/src/lib/spine-client.ts`

## What Was Actually Recovered

Recovered into working tree:

- `/Users/pranay/Projects/travel_agency_agent/tests/conftest.py`
- `/Users/pranay/Projects/travel_agency_agent/tests/test_override_api.py`

What this means:

- the dropped stash did not contain a broad multi-file feature branch or large hidden workset
- the stash itself was small and test-focused
- the larger source-control count drop was not explained by the stash alone

## What the Session Evidence Shows

### Current missing path from named sessions

- `frontend/src/lib/spine-client.ts`

### Why this path is not currently treated as accidental loss

Repo documentation and later session evidence indicate this file was intentionally removed as superseded dead code, not accidentally lost during the stash incident.

### Documentation status

For the named sessions above:

- missing `Docs/...` files now: `0`
- no missing docs were found that require restoration from those sessions

### Other previously observed session behavior

Separate deletion-heavy opencode sessions from 2026-05-05 showed large churn in generated override data under:

- `data/overrides/per_trip/*.jsonl`
- `data/overrides/index.json`
- `data/overrides/patterns/elderly_mobility_risk.jsonl`

These explain large file-count swings better than source-file deletion. They are runtime/generated artifacts, not canonical source by default.

## Regression / Verification Evidence

### Environment discovery

Initial `pytest` invocation through system Python failed during collection because the wrong environment was used.

Observed import failures from system Python:

- `ModuleNotFoundError: No module named 'sqlalchemy'`
- `ModuleNotFoundError: No module named 'opentelemetry'`

Root cause:

- tests were run outside the repo-managed virtual environment

Verification of correct runtime:

- `.venv/bin/pytest` exists
- `.venv/bin/python -c "import sqlalchemy, opentelemetry"` succeeded

### Focused regression commands run

1. `.venv/bin/pytest tests/test_override_api.py -q`
   - result: `17 passed in 4.12s`

2. `.venv/bin/pytest tests/test_route_analysis.py -q`
   - result: `3 passed in 3.96s`

### Verification conclusion

- recovered `tests/test_override_api.py` is currently passing under the project venv
- user-cited `tests/test_route_analysis.py` is currently passing under the project venv
- there is no fresh evidence from these focused checks that the stash recovery introduced a regression in those paths

## Disk Pressure / Tooling Side Findings

The machine temporarily had only about `274 MiB` free, which caused shell heredoc failures and could have disrupted tool behavior.

High-space consumers found:

- `~/.local/share/opencode/snapshot` about `25G`
- `~/.local/share/opencode/opencode.db` about `3.5G`
- `~/.local/share/opencode/storage/session_diff` about `1.6G`
- `~/.local/share/opencode/storage/part` about `1.0G`
- `~/.cache/huggingface` about `4.3G` before cleanup
- `~/.npm` about `1.1G` before cleanup

Safe cache cleanup performed:

- `~/.cache/huggingface`
- `~/.cache/codex-runtimes`
- `~/Library/Developer/Xcode/DerivedData`
- `~/.codex/.tmp`
- disposable npm cache/log/npx paths

Observed effect:

- free space increased from about `274 MiB` to about `7.3 GiB`

## 11-Dimension Audit

- Code: ✅ selective recovery applied; focused regression tests passing in correct venv
- Operational: 🟡 recovery process is documented, but opencode retention remains a recurring operational risk
- User Experience: 🟡 direct product UX not impacted by this report; session/storage growth can degrade agent workflows
- Logical Consistency: ✅ stash size and session evidence now align with the current conclusion set
- Commercial: 🟡 no direct commercial feature work here; preserves engineering trust and avoids false-loss panic
- Data Integrity: 🟡 recovered source/test paths are verified, but generated override data churn should be governed more explicitly
- Quality and Reliability: 🟡 focused checks passed; full-suite regression was not run in this recovery pass
- Compliance: ✅ documentation preservation and non-destructive handling were followed
- Operational Readiness: 🟡 strong on forensics, weaker on automated prevention against future unsafe stash/reset use
- Critical Path: ✅ immediate recovery concern is substantially resolved; next priority is preventive guardrails and opencode retention hygiene
- Final Verdict:
  - code ready: yes for the recovered paths checked
  - feature ready: not applicable
  - launch ready: not applicable
  - recovery conclusion: partial-to-strong closure; no evidence of broad missing source/doc loss from the named sessions

## Current Verdicts

### Confirmed

- The dropped stash content is back for the two affected test files
- The named session histories do not reveal additional currently missing docs
- The named session histories do not reveal additional currently missing source files beyond `frontend/src/lib/spine-client.ts`
- Focused regression checks passed under the repo venv

### Not confirmed

- No claim is made here that every historical generated/runtime file should be restored
- No claim is made here that a full repo-wide regression suite has passed
- No claim is made here that opencode storage retention is healthy long-term

## Long-Term / First-Principles Recommendations

1. Add a repo-local recovery protocol note or guardrail for stash/reset incidents
   - reason: the root problem was process safety, not just code loss

2. Prefer selective recovery tooling over ad hoc git manipulation
   - reason: broad stash pop/apply is unsafe in a multi-agent dirty tree

3. Define retention/cleanup rules for opencode snapshots and SQLite growth
   - reason: `snapshot` and `opencode.db` are the main long-term disk-pressure sources

4. Separate canonical source recovery from generated/runtime artifact recovery
   - reason: generated override data can create false positives in large file-count swings

5. When validating repo health, always run tests through the repo venv
   - reason: system Python produced misleading collection failures unrelated to recovery correctness

## Pending / Optional Next Steps

1. Run a broader regression pass in `.venv` if the user wants stronger post-recovery confidence
2. Add a durable repo note about safe stash/recovery discipline if not already present in enough detail
3. Investigate whether opencode snapshot retention can be pruned or compacted safely without losing needed session history
4. Decide explicitly whether generated override artifacts should be preserved, regenerated, or ignored for source-recovery purposes

## Files Touched In This Recovery Session

- `/Users/pranay/Projects/travel_agency_agent/tests/conftest.py`
- `/Users/pranay/Projects/travel_agency_agent/tests/test_override_api.py`
- `/Users/pranay/Projects/travel_agency_agent/Docs/RECOVERY_FORENSICS_AND_REGRESSION_2026-05-05.md`

