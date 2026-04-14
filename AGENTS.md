# travel_agency_agent Agent Instructions

## Source Hierarchy
1. Repo-local `AGENTS.md` (this file)
2. Workspace-level `/Users/pranay/Projects/AGENTS.md`
3. `.agent/AGENT_KICKOFF_PROMPT.txt` and `.agent/SESSION_CONTEXT.md`

If instructions conflict, follow the stricter rule and cite concrete file paths.

## Workspace Alignment (Adopted)
- Ensure `.agent/AGENT_KICKOFF_PROMPT.txt` and `.agent/SESSION_CONTEXT.md` are loaded before substantive implementation.
- Prefer repository docs and existing scripts over ad-hoc process invention.
- Keep changes small, explicit, and path-cited in summaries.
- Do not claim platform limitations when the gap is implementable; state what is possible, what is implemented, and the concrete path.
- For skill discovery, prioritize project-level skills under `/Users/pranay/Projects/skills/` before defaulting to other skill stores.

## Default Task Lifecycle (Adopted)
1. Analyze request and constraints.
2. Document baseline scope/assumptions.
3. Plan implementation order.
4. Research needed details.
5. Document decision rationale.
6. Implement scoped changes.
7. Verify functionality and run tests.
8. Document outcomes and pending items.

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
- Never delete methods/functions/code to silence warnings without explicit user approval.
- For unused identifiers, prefer non-destructive refactors (for TS, underscore prefix convention where applicable).
- Preserve code intent and structure; ask if deletion is unclear.

### Issue Review Naming
- When an issue is identified and explicitly requires a review note, name the document:
  - `process_issue_review_<date>.md`
- Avoid model-specific naming in issue review files.

### Git Safety (Critical)
- Never commit or push without explicit user approval in the current conversation.
- Staging and checks are allowed proactively.
- Commit/push/merge only when user explicitly asks.

## Current Project Guardrails
- Preserve existing `memory/` contents; do not remove memory artifacts unless explicitly instructed.
- Keep institutional-memory and GTM decision artifacts under `Docs/context/`.
- Keep internal-only process notes under `Archive/context_ingest/internal_notes_*`.

