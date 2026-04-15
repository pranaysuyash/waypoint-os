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

### Frontend-Specific Skills

| Task | Use This Skill | Location |
|------|----------------|----------|
| Frontend design | `frontend-design` | ~/Projects/skills/ |
| React patterns | `react-best-practices` | ~/Projects/skills/ |
| React effects | `react-effect-discipline` | ~/Projects/skills/ |
| UI testing | `webapp-testing` | ~/Projects/skills/ |
| Visual QA | `design-review` | ~/.claude/skills/ |

---

<!-- BEGIN:nextjs-agent-rules -->
# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` before writing any code. Heed deprecation notices.
<!-- END:nextjs-agent-rules -->
