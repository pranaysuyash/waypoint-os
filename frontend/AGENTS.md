# Frontend Agent Instructions

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
