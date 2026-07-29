# Frontend Agent Instructions

<!-- PROJECTS_MEMORY_AGENT_ALIGNMENT_BEGIN -->

## Projects-Level Agent Alignment (Workspace Memory)

**Purpose:** ensure any agent/LLM (Codex, Copilot, Claude Code, Qwen, GLM, etc.) starts aligned with the same workspace memory + project context.

### Step 0 (first time in this folder)
Generate the per-project context pack:
```bash
/Users/pranay/Projects/agent-start
```

### Step 1 (per shell)
Load the shared defaults for this project session:
```bash
source Docs/context/agent-start/STEP1_ENV.sh
# Or (no file read) print exports and eval:
/Users/pranay/Projects/agent-start --print-step1 --skip-index
```

### Step 2 (generate aligned context pack)
```bash
/Users/pranay/Projects/agent-start
```

Outputs:
- Canonical project-local pack:
  - `Docs/context/agent-start/SESSION_CONTEXT.md`
  - `Docs/context/agent-start/AGENT_KICKOFF_PROMPT.txt`
  - `Docs/context/agent-start/STEP1_ENV.sh`
- Compatibility mirrors when present:
  - `.agent/SESSION_CONTEXT.md`
  - `.agent/AGENT_KICKOFF_PROMPT.txt`
  - `.agent/STEP1_ENV.sh`
  - `frontend/docs/context/agent-start/*`

### Automation (already configured)
- Terminal auto-loads `Docs/context/agent-start/STEP1_ENV.sh` when you `cd` into a project under `/Users/pranay/Projects` (zsh hook).
- VS Code/Antigravity can run `agent-start --skip-index` on folder open via `.vscode/tasks.json`.

### How agents should use this
- Provide the canonical `Docs/context/agent-start/AGENT_KICKOFF_PROMPT.txt` and `Docs/context/agent-start/SESSION_CONTEXT.md` as the first context for the agent.
- If sources conflict, the agent must cite concrete file paths and ask before proceeding.
- If the canonical context pack is missing or stale, run `/Users/pranay/Projects/agent-start --skip-index` before planning changes.
- Treat `.agent/` files as compatibility mirrors only.
- Do not start implementation until `Docs/context/agent-start/AGENT_KICKOFF_PROMPT.txt` and `Docs/context/agent-start/SESSION_CONTEXT.md` are loaded.

### Mandatory agent operating mandate
- Begin every substantial task by refreshing ground truth: read the applicable instruction stack, repo-local `AGENTS.md`/`CLAUDE.md`, and any Qwen, Codex, Copilot, or other agent-specific instruction files relevant to the repo.
- Check the current codebase, docs, worklogs, and project status before planning or coding. Parallel agents may have changed files, decisions, or docs since the last session.
- Treat drift as normal: before editing and again before finalizing, re-check the files and docs you rely on, then adapt rather than assuming older context still holds.
- Use relevant skills and workflow guidance after checking the configured skill locations. Do not default to one toolset when a better domain skill exists.
- Think from first principles and optimize for long-term, scalable, architecturally sound solutions. Existing code is evidence, not a boundary; if current implementation no longer fits the product reality or architecture, propose or implement the proper path.
- Avoid building duplicate or parallel systems. Extend canonical routes, pipelines, validation, docs, and tools unless the project explicitly calls for a new replacement path.
- Git safety: read-only git inspection is allowed; no destructive commands, staging, commits, pushes, resets, or checkouts without explicit permission in the current conversation.
- Research online when facts may be current, external, or uncertain; cite sources when research affects decisions.
- Test changes, verify for regressions, and document findings, decisions, open questions, and follow-up work in durable project artifacts.

### Mandatory commit gate
Install or refresh the managed repo-local git hooks. They resolve the repo's effective hook path, block commit creation in `prepare-commit-msg` until the current full `motto_v3.md` has a fresh attestation, then enforce objective diff checks plus commit trailers in `pre-commit` and `commit-msg`:
```bash
python3 /Users/pranay/Projects/workspace_memory/scripts/install_git_precommit_agent_hook.py
```

Refresh the current repo's motto attestation before committing:
```bash
python3 /Users/pranay/Projects/workspace_memory/scripts/attest_motto.py --repo "$PWD"
```

### Shared Idea Pad Protocol (Required)
- Canonical file: `/Users/pranay/Projects/idea_pad/IDEA_PAD.md`
- Raw capture file: `/Users/pranay/Projects/idea_pad/IDEA_DUMP.md`
- Do not create per-model primary copies of the idea pad.
- Do not overwrite the whole file; use append/update workflow with validation.
- Capture rough ideas in `IDEA_DUMP.md`, then promote high-signal items into `IDEA_PAD.md`.
- Before edits:
```bash
python3 /Users/pranay/Projects/idea_pad/scripts/idea_pad_tool.py validate
```
- Add new ideas safely:
```bash
python3 /Users/pranay/Projects/idea_pad/scripts/idea_pad_tool.py add --title "<title>" --owner "<agent>" --type build
```
- After updates, refresh shared memory index:
```bash
cd /Users/pranay/Projects
./projects-memory index
```

<!-- PROJECTS_MEMORY_AGENT_ALIGNMENT_END -->


## Skills Ecosystem (Critical — Read Before Any Task)

**⚠️ DO NOT default to gstack.** You have 3,000+ skills across 8 locations. Always check ALL locations for relevant skills before assuming one doesn't exist.

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
- **Project rules**: `../AGENTS.md`
- **Review/handoff checklist**: `../Docs/IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md`
- **Shared eval doctrine**: `/Users/pranay/Projects/AGENTIC_EVAL_RULES.md` and `~/Projects/skills/agentic-eval-loop/`

## Autonomous Review/Handoff Rule (Frontend)

For frontend implementation reviews and new task proposals:

1. Apply `../Docs/IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md` automatically.
2. Do not repeatedly ask the user to restate review format/process.
3. Provide evidence-first findings + atomic implementation tasks with verification commands.

### Frontend-Specific Skills

| Task | Use This Skill | Location |
|------|----------------|----------|
| Frontend design | `frontend-design` | ~/Projects/skills/ |
| React patterns | `react-best-practices` | ~/Projects/skills/ |
| React effects | `react-effect-discipline` | ~/Projects/skills/ |
| UI testing | `webapp-testing` | ~/Projects/skills/ |
| Visual QA | `design-review` | ~/.claude/skills/ |
| Design system audit | `rendered-design-system-audit` | ~/.hermes/skills/frontend/ + `tools/rendered-design-system-audit/` |
| Agentic evals | `agentic-eval-loop` | ~/Projects/skills/ |

---

## API Contract Verification (Critical — Mandatory Before Any Integration Work)

**Rule: Never assume the shape of API responses. Test the real contract first.**

When modifying code that consumes backend endpoints, you MUST verify the actual data shape before writing any consumer code.

**Why this matters:** Frontend types, mocks, and assumptions often drift from the real backend response. Writing code against an imagined contract causes runtime crashes (e.g., `TypeError: Cannot read properties of undefined`) that TypeScript and unit tests cannot catch.

**Mandatory steps for any frontend task touching backend data:**

1. **Inspect the backend response directly**
   ```bash
   # Submit a run and inspect the actual JSON
   curl -s -X POST http://localhost:8000/run \
     -H "Authorization: Bearer <token>" \
     -d '{"raw_note":"test"}' | python3 -m json.tool
   
   # Poll for status and look at the real shape
   curl -s "http://localhost:8000/runs/$RUN_ID" \
     -H "Authorization: Bearer <token>" | python3 -m json.tool
   ```
   Or read the backend source (`spine_api/server.py`, `spine_api/contract.py`) to see the exact Pydantic model fields.

2. **Compare backend output to frontend types**
   - Check `src/types/spine.ts` and `src/types/generated/spine-api.ts`
   - If they don't match the real API response, update the types FIRST.

3. **Write frontend code ONLY against the verified shape**
   - Use optional chaining (`?.`) and nullish coalescing (`??`) for every nested field access.
   - Never access `.length`, `.map()`, or property keys without guarding against `undefined`.

4. **Test end-to-end before claiming it works**
   - Submit a real request through the frontend BFF proxy or directly to the backend.
   - Verify the UI renders correctly with the actual response data.
   - Screenshot or describe what you see. Do not say "it works" based on build passing or unit tests alone.

**Real example of failure from 2026-04-29:**
- Backend `RunStatusResponse.validation` returns: `{status: "ESCALATED", gate: "NB01", reasons: ["..."]}`
- Frontend assumed: `{is_valid: false, errors: [{field, message}], warnings: [...]}`
- Result: `TypeError: Cannot read properties of undefined (reading 'length')` on `.errors.length`
- Root cause: Agent modified frontend without ever `curl`-ing the real API response.

<!-- BEGIN:nextjs-agent-rules -->
# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` before writing any code. Heed deprecation notices.
<!-- END:nextjs-agent-rules -->

## Real-World Logic Rule

- Existing code is context, not authority.
- If current implementation conflicts with first-principles product logic, stakeholder impact, or real runtime behavior, update the implementation.
- Frontend acceptance is not "type-safe only"; it must be behavior-safe with real backend payloads and user flow outcomes.
