# git
- Do not create branches unless explicitly requested; work only on master/main. Confidence: 0.90
- No mutating git commands (commit, push, reset, clean, delete, rebase, squash, merge, checkout/restore) without explicit approval; read-only git commands are always allowed. Confidence: 0.95
- No AI-agent Co-Authored-By trailers in commit messages (applies to Claude, ChatGPT, Codex, Copilot, Qwen, Gemini, all agents/tools). Confidence: 0.95
- Before any mutating git action, run a full read-only state check first: git status, branch, diff, stash, worktree, untracked files. Confidence: 0.85
- Commit message format examples: `feat(scope): description`, `fix(scope): description`, `docs(scope): description`, `test(scope): description`, `chore(scope): description`, `perf(scope): description`. Confidence: 0.80

# collaboration
See [collaboration/taste.md](collaboration/taste.md)
# documentation
- Document discussions on disk first before providing the summary to the user, not the reverse. Confidence: 0.70
- Save useful learnings and instructions globally (user-level agent configs) when they're generally applicable, not just in the project repo. Confidence: 0.75
# research
- When user provides a list of proposed domain concepts/models and asks to check coverage, first cross-reference each concept against existing research series file names/prefixes; map findings (e.g., Enquiry→LEAD_*, Booking→BOOKING_ENGINE_*) and report what's covered before deciding what new docs to create. Confidence: 0.70
- When user explicitly requests research on a specific topic during exploration phase (e.g., agentic systems, user guidance), create a full research series covering it immediately within the current phase rather than deferring to a planned list. Confidence: 0.70
- When user says "your call" it means choose the next highest-value exploration area aligned with project goals; pick the area with the broadest cross-cutting impact. Confidence: 0.65

# documentation
- Write all assistant-produced outputs (role documents, analyses, synthesis, plans, findings) as files on disk in the project repo proactively; never leave produced content only in conversation text, and do not wait to be reminded. Confidence: 0.85
- Save full discussion trails — decisions, trade-offs, user's suggestions, and reasoning — as persistent documents so future agents can reference context without re-reading conversations. Confidence: 0.80
- Preserve ALL content verbatim when saving discussion output to docs; never condense, summarize, or reduce original content. If the content is too large for a single file, split it across multiple files but keep the full original text intact in each. Confidence: 0.98
- During research/exploration phase, produce research documents (Key Questions, Research Areas with data model sketches and UI mockups, Open Problems, Next Steps) not implementation code; keep code samples as illustrative sketches not production implementations. Confidence: 0.85
- Cover all identified gaps systematically when user says "all of these" or similar — do not cherry-pick or stop after partial coverage; iterate until all related areas are documented. Confidence: 0.80

# architecture
See [architecture/taste.md](architecture/taste.md)
# research
- Structure exploration series as: 4 topic docs covering different angles + 1 master index with cross-references, per research area. Confidence: 0.85
- Use background agents for parallel doc creation when series have independent topic files that don't depend on each other. Confidence: 0.75
- Before claiming a topic is uncovered, run a systematic file-name-based audit against existing docs using grep/find or an explore agent; cross-reference findings to avoid false positives from different naming prefixes. Confidence: 0.80
- Maintain an EXPLORATION_TRACKER.md as central registry of all exploration areas with Parts, completion status per series, and next actions. Confidence: 0.85
- When user asks about gaps, use an iterative cycle: identify gaps via audit → present findings with evidence (what exists vs missing) → confirm with user → create all confirmed series. Confidence: 0.80

# workflow
See [workflow/taste.md](workflow/taste.md)

# collaboration
- Before starting any work, check all agent instruction files at these paths in order: /Users/pranay/ (AGENTS.md, CLAUDE.md, QWEN.md, COPILOT.md related files), then project-level (AGENTS.md, CLAUDE.md), then any skill-routing or agent-specific config files — do not rely only on project-level CLAUDE.md. Confidence: 0.80

# collaboration
- Before starting work, read ALL instruction/config files (AGENTS.md, CLAUDE.md, frontend/AGENTS.md, all skill routing docs) — not just the project-level CLAUDE.md. Confidence: 0.70
- Use an external reviewer (ChatGPT/human reviewer) as a quality gate before completing phases; produce structured "writeup for review" reports covering architecture, decisions, blockers resolved, and acceptance criteria. Confidence: 0.75

# design
- Implement design guides pixel-perfectly; approximations or "close enough" implementations that don't match the provided design spec will be rejected — read the design files fully, reproduce token values and layout exactly. Confidence: 0.80
- When evaluating design quality, assess all aspects comprehensively: visual design, UX, interaction, accessibility, responsiveness, consistency, hierarchy, and spacing — not just surface-level styling changes. Confidence: 0.70

# research
- When model names, pricing, or provider capabilities are needed, verify against actual current provider pages/docs — do not rely on stale training data for model IDs, pricing tiers, or SDK APIs. Confidence: 0.70
- When a domain is covered across multiple scattered research series (e.g., Enquiry→LEAD_*, Booking→BOOKING_ENGINE_*, Buyer→CRM_*/IDENTITY_*/SEGMENT_*) with no single unified core-layer document, create a dedicated bridging series (DOMAIN_*) that consolidates upstream entities, workflows, events, and contracts — showing how scattered research fits together into a coherent foundation. Confidence: 0.75
- When a user shares external analysis/audit text about codebase state and asks to validate research coverage, the validation workflow is: (1) read the analysis and extract named concepts, (2) run a file-name-based audit against existing docs, (3) map each concept to specific series/prefixes with clear evidence, (4) report what's covered vs what's not, (5) if gaps exist, propose new research series. Confidence: 0.75

# operations
- Reuse or recycle existing dev servers and ports; do not spawn new server processes on new ports if one is already running — kill and restart or reuse. Confidence: 0.65
- Do not save project-related files or artifacts outside the project repo directory (no /tmp, no .codex, no .claude, no auxiliary directories for project files). Confidence: 0.92

# testing
- For UI changes, use Browser/Computer visual verification tools to confirm runtime behavior visually, not just static code review or unit tests — start the dev server and verify visually. Confidence: 0.65
- Tests must contain real behavioral assertions — reject placeholder tests with `assert True`, `pass`, or unimplemented branches that do not validate actual functionality. Confidence: 0.70

# collaboration
- Use a structured external peer-review gate before marking phases as complete: implement → produce structured "writeup for [reviewer]" report → get review feedback → resolve all blockers → close phase. Confidence: 0.85
- Every phase plan must explicitly list non-goals / "do not include" items — bounding what is deliberately excluded prevents scope creep and keeps implementation focused on the agreed contract. Confidence: 0.80

# validation
- Schema validation must reject type-mismatched field values (non-string, non-null), never coerce or stringify them; wrong types produce a clear failed-extraction status, not silently normalized data. Confidence: 0.85
