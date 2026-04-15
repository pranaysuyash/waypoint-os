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

| Task | Use This Skill | Location |
|------|----------------|----------|
| Debug/troubleshoot | `systematic-debugging` | ~/Projects/skills/ |
| Write tests | `tdd-workflow`, `e2e-testing` | ~/Projects/skills/ |
| QA testing | `qa`, `qa-only` | ~/.agents/skills/ |
| Verify before done | `verification-before-completion` | ~/Projects/skills/ |
| Research before code | `search-first` | ~/Projects/skills/ |
| UI screenshots | `browse` | ~/.agents/skills/ |
| Visual QA | `design-review` | ~/.claude/skills/ |

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
  - `travel_agency_process_issue_review_<date>.md` (under `Docs/`)
  - Example: `travel_agency_process_issue_review_2026-04-15.md`
- This makes issue documents project-specific and discoverable
- Avoid model-specific naming in issue review files (e.g., no "gemini issue review")

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

