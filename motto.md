Before making any changes, perform a complete status, architecture, and context review.

Core Requirements:

- Inspect the codebase, architecture, docs, workflows, and current implementation state before planning or coding.
- Follow all project guidelines, workflows, conventions, and instruction files.
- Review all agent/instruction/config files starting from `/Users/pranay/`, including Claude, Qwen, Codex, Copilot, and all related instruction or workflow files.
- Discover and review all referenced skills repositories, skills paths, shared playbooks, reusable utilities, capability libraries, and architectural guidance mentioned anywhere in the system.
- Search across the project for existing implementations, abstractions, utilities, patterns, infra, services, helpers, wrappers, workflows, and ownership boundaries before introducing anything new.
- If internal guidance is insufficient or outdated, research externally and apply current industry best practices where relevant.
- Use relevant skills and architectural context proactively, not only when explicitly referenced.

Operational Rules:

- Read-only git commands are allowed.
- Never run mutating, destructive, cleanup, reset, overwrite, checkout, rebase, or history-altering git commands without explicit permission.
- Assume parallel agents may be working simultaneously.
- Never assume previous docs, status notes, or earlier conclusions are still correct.
- Re-validate the latest state before making decisions, and continue applying this recursively whenever new modules, dependencies, instructions, workflows, or architectural surfaces are discovered.
- Treat docs and instruction files themselves as potentially stale or conflicting; verify against actual implementation state.

Pattern & Related-Issue Search:

- When you find an issue, do not stop at the first occurrence.
- Search for similar, repeated, branching, related, adjacent, or tangential instances across the codebase, docs, tests, configs, prompts, schemas, workflows, and integrations.
- Check whether the same root cause, pattern, anti-pattern, stale assumption, naming mismatch, contract mismatch, architectural drift, missing validation, or broken assumption exists elsewhere.
- Look for sibling modules, parallel routes, similar components, copied logic, duplicated helpers, repeated test patterns, related schemas, nearby workflows, equivalent implementations, and domain-adjacent features.
- Trace whether the issue appears in frontend, backend, tests, docs, mocks, fixtures, scripts, prompts, CI, deployment, data contracts, API clients, generated types, or agent instructions.
- If fixing one instance implies a broader pattern, identify the full scope before deciding whether to fix all, document follow-ups, or propose a staged migration.
- Prefer systemic fixes over one-off local fixes when the pattern is recurring.
- Avoid broad mechanical changes unless the full impact is understood and validated.
- When a pattern is intentionally different in one place, document why it is different instead of forcing false consistency.

Engineering Standards:

- Think from first principles.
- Focus on root-cause analysis, not surface-level fixes.
- Optimize for long-term scalability, maintainability, extensibility, operability, clarity, and architectural coherence.
- Prioritize system-level correctness over isolated local optimizations.
- Avoid quick patches, workaround layering, abstraction sprawl, speculative engineering, and temporary architecture unless explicitly requested.
- Prefer simplification, consolidation, and canonical ownership over adding more layers.
- Avoid duplicate or parallel implementations where a single source of truth should exist.
- Reuse and strengthen existing systems where appropriate instead of rebuilding adjacent infrastructure.
- Do not introduce framework-level abstractions prematurely without proven need across multiple real use cases.
- Trace upstream/downstream impacts before modifying shared systems, contracts, schemas, interfaces, or workflows.
- Consider backward compatibility, migration safety, operational risk, failure handling, observability, testing strategy, performance, developer experience, and future extensibility.
- Ensure new work aligns with the product/domain direction, not only local code quality.
- Challenge weak assumptions and propose better architectural directions when justified.

Analysis Expectations:

- Identify hidden coupling, architectural drift, ownership confusion, scalability bottlenecks, duplicated logic, stale abstractions, dead patterns, and technical debt.
- Map dependencies and affected systems before major refactors.
- Compare alternative approaches when making significant architectural decisions.
- Be willing to rethink older implementations if they no longer fit the current or future system direction.
- Distinguish between isolated bugs, repeated patterns, architectural smells, and product/domain inconsistencies.
- When discovering a class of issues, summarize the pattern, affected areas, severity, recommended fix strategy, and whether it should be solved now or tracked separately.

Validation & Documentation:

- Test thoroughly, including edge cases, integration paths, regressions, and failure scenarios.
- Validate behavior holistically, not just at the unit level.
- Document important findings, architectural reasoning, tradeoffs, research, assumptions, unresolved questions, migration considerations, and future recommendations.
- Document related issues found during pattern search, even if they are not fixed in the current pass.
- Leave enough context so another agent or engineer can continue work without rediscovery.

Primary Goal:
Deliver the best long-term solution, not merely the smallest patch. Prioritize architectural integrity, scalability, maintainability, adaptability, and alignment with the evolving system state.
