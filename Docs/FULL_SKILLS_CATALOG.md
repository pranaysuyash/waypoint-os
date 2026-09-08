# Full Skills Catalog — Waypoint OS / travel_agency_agent

**Status:** durable, agent-pointable capability inventory for this repo  
**Date:** 2026-09-07  
**Authority:** this file is the **project-local routing index**. It does not replace `/Users/pranay/Projects/SKILLS_CATALOG.md` (workspace master) or repo `AGENTS.md` (search-order + non-gstack rule).  
**Persona/session that produced it:** PER-0443 Agentic Travel Systems Architect audit (`Docs/review/PERSONA_AUDIT_PER0443_AGENTIC_TRAVEL_SYSTEMS_ARCHITECT_2026-09-07.md`).

---

## How another agent should use this file

Copy one of these sentences into the next agent's prompt. Do not rely on chat memory.

**Generic:**

> Open `Docs/FULL_SKILLS_CATALOG.md`, search for the relevant skill in category `<NAME>`, and follow its `SKILL.md` file.

**With a concrete task:**

> Open `Docs/FULL_SKILLS_CATALOG.md`, search category **Agentic systems & evals**, load `/Users/pranay/Projects/skills/agentic-eval-loop/SKILL.md` and `/Users/pranay/Projects/AGENTIC_EVAL_RULES.md`, then execute that workflow against the named files.

**Discovery if the category is missing:**

> Open `Docs/FULL_SKILLS_CATALOG.md` §0 (search order). If the skill is not listed, open `/Users/pranay/Projects/SKILLS_CATALOG.md`, then load `~/.agents/skills/find-skills/SKILL.md` and run all three discovery phases. Do not default to gstack.

---

## 0. Skill search order (from repo `AGENTS.md`)

Check **all** of these before claiming a skill does not exist. Prefer `~/Projects/skills/` when the same skill exists in several stores.

| # | Store | Absolute root |
|---:|---|---|
| 1 | Claude Code | `/Users/pranay/.claude/skills/` |
| 2 | Agents store | `/Users/pranay/.agents/skills/` |
| 3 | Hermes | `/Users/pranay/.hermes/skills/` |
| 4 | **Curated engineering (prefer)** | `/Users/pranay/Projects/skills/` |
| 5 | Community imports | `/Users/pranay/Projects/external-skills/` |
| 6 | OpenAI Codex copy | `/Users/pranay/Projects/openai-skills/` |
| 7 | Codex runtime | `$CODEX_HOME/skills/` |
| 8 | Codex local | `/Users/pranay/.codex/skills/` |
| 9 | Codex system (read-only) | `/Users/pranay/.codex/skills/.system/` |
| 10 | This repo | `/Users/pranay/Projects/travel_agency_agent/.agents/skills/` |
| 11 | Grok bundled | `/Users/pranay/.grok/bundled/skills/` |

Workspace master catalog: `/Users/pranay/Projects/SKILLS_CATALOG.md`.

**Hard rule:** do **not** default to gstack. Use `browse`, `qa`/`qa-only`, `webapp-testing`, `e2e-testing`, or `design-review` instead (see Category Testing).

**Always-on for this repo:**

1. `/Users/pranay/Projects/skills/verification-before-completion/SKILL.md`
2. `/Users/pranay/Projects/skills/search-first/SKILL.md`
3. `/Users/pranay/Projects/skills/systematic-debugging/SKILL.md` (bugs)
4. `/Users/pranay/Projects/skills/tdd-workflow/SKILL.md` (new tests)
5. `/Users/pranay/Projects/skills/agentic-eval-loop/SKILL.md` + `/Users/pranay/Projects/AGENTIC_EVAL_RULES.md` (any prompt, routing, fallback, review, or agent workflow)

---

## Category index (Waypoint OS work → category)

| If the next agent is doing… | Open this category |
|---|---|
| Intake, extraction, gates, hybrid engine, memory, evals, agents | Agentic systems & evals |
| Booking, fulfillment, IROPS, journey graph, proposals, money | Travel operating system |
| Auth, tenancy, secrets, PII, tokens | Security, privacy, tenancy |
| FastAPI, contracts, persistence, idempotency, recovery | Backend, contracts, state |
| Workbench, companion, BFF, honesty badges | Frontend & operator UX |
| pytest, Playwright, browser smoke, QA | Testing & verification |
| Architecture, ADRs, audits, persona reviews | Review, architecture, docs |
| Stripe, mandates, payouts, insurance quotes | Payments, insurance, legal-adjacent |
| Launch, deploy, Fly/Render, CI | Launch & operations |
| Research before building a missing primitive | Research & exploration |

---

## Category: Agentic systems & evals

**Tell another agent:** Open `Docs/FULL_SKILLS_CATALOG.md`, search for category **Agentic systems & evals**, and follow its `SKILL.md` file.

| Skill | Absolute `SKILL.md` | When to tell an agent to use it | Instruction to give the next agent |
|---|---|---|---|
| agentic-eval-loop | `/Users/pranay/Projects/skills/agentic-eval-loop/SKILL.md` | Any prompt/schema/routing/fallback/review/agent failure | Follow `agentic-eval-loop/SKILL.md`; also load `/Users/pranay/Projects/AGENTIC_EVAL_RULES.md`. Produce layer-classified work items with keep/revert gates. |
| agentic-engineering | `/Users/pranay/Projects/skills/agentic-engineering/SKILL.md` | Eval-first agent work, cost-aware routing | Follow `agentic-engineering/SKILL.md` for decomposition and model routing. |
| ai-agents-architect | `/Users/pranay/.agents/skills/ai-agents-architect/SKILL.md` | Autonomy vs control, failure modes, HITL | Follow `ai-agents-architect/SKILL.md`; design graceful degradation, not unbounded loops. |
| autonomous-agents | `/Users/pranay/.agents/skills/autonomous-agents/SKILL.md` | Compound failure across steps | Follow `autonomous-agents/SKILL.md`; assume 95% per-step ≠ 60% by step 10. |
| autonomous-agent-patterns | `/Users/pranay/.agents/skills/autonomous-agent-patterns/SKILL.md` | Harness/tool-space design | Follow `autonomous-agent-patterns/SKILL.md`. |
| autonomous-loops | `/Users/pranay/Projects/skills/autonomous-loops/SKILL.md` | Continuous agent loops | Follow `autonomous-loops/SKILL.md`. |
| continuous-agent-loop | `/Users/pranay/.agents/skills/continuous-agent-loop/SKILL.md` | Quality gates + recovery in loops | Follow `continuous-agent-loop/SKILL.md`. |
| agent-harness-construction | `/Users/pranay/Projects/skills/agent-harness-construction/SKILL.md` | Tool definitions, observation format | Follow `agent-harness-construction/SKILL.md`. |
| agent-orchestrator | `/Users/pranay/.agents/skills/agent-orchestrator/SKILL.md` | Multi-skill matching | Follow `agent-orchestrator/SKILL.md`. |
| dispatching-parallel-agents | `/Users/pranay/Projects/skills/dispatching-parallel-agents/SKILL.md` | Independent parallel work | Follow `dispatching-parallel-agents/SKILL.md`. |
| iterative-retrieval | `/Users/pranay/Projects/skills/iterative-retrieval/SKILL.md` | Subagent context loss | Follow `iterative-retrieval/SKILL.md` (dispatch → evaluate → refine, max 3). |
| cost-aware-llm-pipeline | `/Users/pranay/Projects/skills/cost-aware-llm-pipeline/SKILL.md` | Token/cost routing, PA-20/E-C | Follow `cost-aware-llm-pipeline/SKILL.md`. |
| eval-harness | `/Users/pranay/.agents/skills/eval-harness/SKILL.md` | Formal eval harness | Follow `eval-harness/SKILL.md`. |
| langgraph-human-in-the-loop | `/Users/pranay/.agents/skills/langgraph-human-in-the-loop/SKILL.md` | Approval interrupts (ADR-008 R1) | Follow `langgraph-human-in-the-loop/SKILL.md` as a pattern reference — extend Waypoint gates, do not import a second runtime. |
| langchain-rag | `/Users/pranay/.agents/skills/langchain-rag/SKILL.md` | RAG pipeline design (A-02) | Follow `langchain-rag/SKILL.md`; compare against `src/rag/` honesty (hash-vector today). |
| rag-patterns | `/Users/pranay/Projects/skills/rag-patterns/SKILL.md` | Vector/hybrid retrieval | Open `rag-patterns/` then the store-specific SKILL (chroma/faiss/qdrant/pinecone). |
| prompt-engineering | `/Users/pranay/Projects/skills/prompt-engineering/SKILL.md` | Structured output, DSPy/Instructor | Follow the matching child under `prompt-engineering/` (dspy, instructor, outlines, guidance). |
| ml-observability | `/Users/pranay/Projects/skills/ml-observability/SKILL.md` | Tracing evals (LangSmith/Phoenix) | Follow `ml-observability/langsmith/SKILL.md` or `phoenix/SKILL.md`. |
| kdd-override-mining-audit | `/Users/pranay/Projects/skills/kdd-override-mining-audit/SKILL.md` | Operator-override learning | Follow `kdd-override-mining-audit/SKILL.md` against `src/decision/override_learning.py`. |

---

## Category: Travel operating system

There is **no** dedicated “GDS/NDC/IROPS” skill in the curated stores. Travel work in this repo is **persona + domain code + adjacent skills**, not a missing travel-SDK skill.

**Tell another agent:** Open `Docs/FULL_SKILLS_CATALOG.md`, search for category **Travel operating system**, then load the persona file **and** the adjacent skill in the table — do not invent a travel skill.

| Resource | Absolute path | When | Instruction to give the next agent |
|---|---|---|---|
| PER-0443 persona | `/Users/pranay/Desktop/Understanding_Personas_sept6/01 Expanded Personas/09 Travel - Waypoint OS/PER-0443 - Agentic Travel Systems Architect.docx` | Autonomy, tools, permissions, memory, travel action | Act as PER-0443. Extract the docx; inspect agent roles, tool contracts, duplicate bookings, approvals, retries. |
| Waypoint OS persona stack index | `/Users/pranay/Desktop/Understanding_Personas_sept6/01 Expanded Personas/09 Travel - Waypoint OS/INDEX - Waypoint OS Persona Stack.docx` | Picking a travel specialist | Filter the stack; do **not** import OrbitCover (folder `10 Travel - OrbitCover/` is a **separate** project). |
| PER-0442 Travel OS Architect | `.../09 Travel - Waypoint OS/PER-0442 - Travel Operating Systems Architect.docx` | OS primitives, lifecycle | Prior audit: `Docs/review/TRAVEL_OS_ARCHITECTURAL_AUDIT_PER0442_2026-09-03.md`. |
| PER-WPSYS-0032…0047 | same folder (`PER-WPSYS-0032` … `0047`) | Trip lifecycle, orchestration, intake, booking autonomy, freshness, escalation | Open the named `PER-WPSYS-00xx` docx and apply it to the named module. |
| PER-880003 Disruption | `.../PER-880003 - Travel Disruption Systems Architect.docx` | IROPS / disruption | Pair with AT-06 in the PER-0443 register. |
| PER-880004 IROPS | `.../PER-880004 - Irregular Operations - IROPS Specialist.docx` | Carrier irregular ops | Do not auto-rebook; R1 human. |
| PER-99010–99017 docs/visa | `.../PER-99010` … `PER-99017` | Passport/visa/readiness | Pair with AT-11; extend `DocumentReadinessAgent`, do not add a second radar. |
| conversation-to-operating-model | `/Users/pranay/Projects/skills/conversation-to-operating-model/SKILL.md` | Turning travel product talk into principles | Follow that SKILL before implementing a new travel primitive. |
| domain-modeling | `/Users/pranay/.agents/skills/domain-modeling/SKILL.md` | Ubiquitous language (trip vs journey vs confirmation) | Follow `domain-modeling/SKILL.md`; keep one canonical term per concept. |
| existing-project-discovery-delivery | `/Users/pranay/Projects/skills/existing-project-discovery-delivery/SKILL.md` | Substantial feature in this existing repo | Follow that SKILL; keep files unchanged until the execution brief is approved **if** the skill’s hard gate applies — this conversation already approved documentation+plan. |

**OrbitCover / insurance-as-carrier skills** live under `.../10 Travel - OrbitCover/` and `.../12 Insurance & Policy Intelligence/`. **Do not merge them into Waypoint.** Adjacent honesty work uses Category Payments, insurance, legal-adjacent.

**Waypoint-named skills (verified 2026-09-07 — no GDS/NDC/IROPS/visa skill exists in any store):**

| Skill | Absolute `SKILL.md` | When | Instruction |
|---|---|---|---|
| kdd-override-mining-audit | `/Users/pranay/Projects/skills/kdd-override-mining-audit/SKILL.md` | OverrideStore, KDD clusters, `/kdd/*` tenancy | Follow it against `src/decision/override_learning.py` and KDD routers. |
| suitability-module-implementation | `/Users/pranay/.hermes/skills/suitability-module-implementation/SKILL.md` | Activity suitability, PA-36 Tier-3 | Deterministic → context → LLM tiers; do not wire Tier-3 until E-D + E-C. |
| generated-type-integration | `/Users/pranay/.hermes/skills/frontend/generated-type-integration/SKILL.md` | FE consuming spine OpenAPI | Never edit generated files; curl the real JSON first (repo API-contract rule). |
| location-intelligence | `/Users/pranay/.hermes/skills/geospatial-mapping/location-intelligence/SKILL.md` | Destinations, proximity | Pair with `src/intake/geography.py`; Haversine, not Euclidean. |

---

## Category: Security, privacy, tenancy

**Tell another agent:** Open `Docs/FULL_SKILLS_CATALOG.md`, search for category **Security, privacy, tenancy**, and follow its `SKILL.md` file.

| Skill | Absolute path | When | Instruction |
|---|---|---|---|
| security-review | `/Users/pranay/Projects/skills/security-review/SKILL.md` | Auth, secrets, payments, input | Follow `security-review/SKILL.md` (+ `cloud-infrastructure-security.md` if deploy). |
| prompt-security-hardening | `/Users/pranay/.hermes/skills/security/prompt-security-hardening/SKILL.md` | Intake notes / RAG injection | Delimit untrusted traveler text; output-filter. Pairs with E-H adversarial corpus. |
| security-scan | `/Users/pranay/Projects/skills/security-scan/SKILL.md` | Config/hook/MCP scan | Follow `security-scan/SKILL.md`. |
| sensitive-source-audit | `/Users/pranay/Projects/skills/sensitive-source-audit/skill.md` | PII, consent, export, GDPR | Follow `sensitive-source-audit/skill.md` (F-05/PA-31/L6). |
| cso | `/Users/pranay/.agents/skills/cso/SKILL.md` | Infra-first security audit | Follow `cso/SKILL.md`. Do not default to gstack-cso. |
| careful | `/Users/pranay/.agents/skills/careful/SKILL.md` | Prod, DROP, reset, force-push | Follow `careful/SKILL.md` before any destructive command. |

---

## Category: Backend, contracts, state

**Tell another agent:** Open `Docs/FULL_SKILLS_CATALOG.md`, search for category **Backend, contracts, state**, and follow its `SKILL.md` file.

| Skill | Absolute path | When | Instruction |
|---|---|---|---|
| backend-patterns | `/Users/pranay/Projects/skills/backend-patterns/SKILL.md` | API, DB, server | Follow `backend-patterns/SKILL.md`. |
| api-design | `/Users/pranay/Projects/skills/api-design/SKILL.md` | REST contracts, errors, pagination | Follow `api-design/SKILL.md`; verify live OpenAPI, do not invent shapes. |
| api-design-principles | `/Users/pranay/.agents/skills/api-design-principles/SKILL.md` | GraphQL/REST principles | Follow `api-design-principles/SKILL.md`. |
| python-patterns | `/Users/pranay/Projects/skills/python-patterns/SKILL.md` | Python idioms, slots, caches | Follow `python-patterns/SKILL.md`. |
| python-testing | `/Users/pranay/Projects/skills/python-testing/SKILL.md` | pytest | Follow `python-testing/SKILL.md`. |
| bff-backend-reconciliation | `/Users/pranay/.hermes/skills/backend-patterns/bff-backend-reconciliation/SKILL.md` | Next BFF vs spine_api drift (F-43) | Verify live JSON before FE types; do not invent contracts. |
| message-queue-patterns | `/Users/pranay/.hermes/skills/backend-patterns/message-queue-patterns/SKILL.md` | Requeue, DLQ, IROPS events | At-least-once + idempotent consumers (AT-03, PA-40). |
| python-performance-optimization | `/Users/pranay/.agents/skills/python-performance-optimization/SKILL.md` | Latency of spine endpoints | Follow that SKILL; for this repo also use pyinstrument under `Docs/profiling/pyinstrument/`. |
| async-audit | `/Users/pranay/Projects/skills/async-audit/skill.md` | Daemon threads, SSE, leases | Follow `async-audit/skill.md`. |
| state-audit | `/Users/pranay/Projects/skills/state-audit/skill.md` | Trip/run/ledger split-brain | Follow `state-audit/skill.md`. |
| docker-patterns | `/Users/pranay/Projects/skills/docker-patterns/SKILL.md` | compose/Dockerfile | Follow `docker-patterns/SKILL.md`. |
| supabase-postgres-best-practices | `/Users/pranay/.claude/plugins/cache/claude-plugins-official/supabase/0.1.12/./skills/supabase-postgres-best-practices/SKILL.md` | RLS, Postgres | Use as Postgres practice reference; this repo’s canonical store is SQL TripStore + RLS, not Supabase product APIs. |

---

## Category: Frontend & operator UX

**Tell another agent:** Open `Docs/FULL_SKILLS_CATALOG.md`, search for category **Frontend & operator UX**, and follow its `SKILL.md` file.

| Skill | Absolute path | When | Instruction |
|---|---|---|---|
| frontend-patterns | `/Users/pranay/Projects/skills/frontend-patterns/SKILL.md` | Next.js App Router, state | Follow `frontend-patterns/SKILL.md`. |
| nextjs-app-router-patterns | `/Users/pranay/.agents/skills/nextjs-app-router-patterns/SKILL.md` | RSC, routing, BFF | Follow `nextjs-app-router-patterns/SKILL.md`. |
| react-effect-discipline | `/Users/pranay/Projects/skills/react-effect-discipline/SKILL.md` | `useEffect` races | Follow `react-effect-discipline/SKILL.md`. |
| react-best-practices | `/Users/pranay/.agents/skills/react-best-practices/SKILL.md` | Perf | Follow `react-best-practices/SKILL.md`. |
| frontend-design | `/Users/pranay/Projects/skills/frontend-design/SKILL.md` | New UI direction | Follow `frontend-design/SKILL.md`. |
| design-review | `/Users/pranay/.claude/skills/design-review/SKILL.md` | Visual QA | Follow `design-review/SKILL.md`. Prefer this over gstack. |
| rendered-design-system-audit | `/Users/pranay/.hermes/skills/frontend/rendered-design-system-audit/SKILL.md` | Live workbench visual QA | Prefer over gstack design-review (no stash/commit). Start servers `:8000` / `:3005`. |
| generated-type-integration | `/Users/pranay/.hermes/skills/frontend/generated-type-integration/SKILL.md` | `spine-api.ts` consumers | Two-layer types; never edit generated files. |
| web-design-guidelines | `/Users/pranay/.claude/skills/web-design-guidelines/SKILL.md` | A11y / UX audit | Follow `web-design-guidelines/SKILL.md`. |
| better-accessibility | `/Users/pranay/.agents/skills/better-accessibility/SKILL.md` | Keyboard, ARIA | Follow `better-accessibility/SKILL.md`. |
| shadcn-ui (repo) | `/Users/pranay/Projects/travel_agency_agent/.agents/skills/shadcn-ui/SKILL.md` | shadcn in this frontend | Follow the **repo-local** skill first. |
| design-taste-frontend (repo) | `/Users/pranay/Projects/travel_agency_agent/.agents/skills/design-taste-frontend/SKILL.md` | Operator UI taste | Follow the repo-local skill. |

---

## Category: Testing & verification

**Tell another agent:** Open `Docs/FULL_SKILLS_CATALOG.md`, search for category **Testing & verification**, and follow its `SKILL.md` file.

| Skill | Absolute path | When | Instruction |
|---|---|---|---|
| verification-before-completion | `/Users/pranay/Projects/skills/verification-before-completion/SKILL.md` | Any “done” claim | Follow it. No completion without fresh command output. |
| verification-loop | `/Users/pranay/Projects/skills/verification-loop/SKILL.md` | Multi-check sessions | Follow `verification-loop/SKILL.md`. |
| tdd-workflow | `/Users/pranay/Projects/skills/tdd-workflow/SKILL.md` | New behavior | Red-green-refactor; user journeys. |
| test-driven-development | `/Users/pranay/.agents/skills/test-driven-development/SKILL.md` | TDD alias | Same intent; prefer `tdd-workflow` as canonical. |
| systematic-debugging | `/Users/pranay/Projects/skills/systematic-debugging/SKILL.md` | Bugs, 500s | Follow the 4-phase loop; no fix without root cause. |
| diagnosing-bugs | `/Users/pranay/.agents/skills/diagnosing-bugs/SKILL.md` | Hard regressions | Follow `diagnosing-bugs/SKILL.md`. |
| e2e-testing | `/Users/pranay/Projects/skills/e2e-testing/SKILL.md` | Playwright POM | Follow `e2e-testing/SKILL.md`. |
| webapp-testing | `/Users/pranay/Projects/skills/webapp-testing/SKILL.md` | Local app via Playwright | Follow `webapp-testing/SKILL.md`. |
| browse | `/Users/pranay/.agents/skills/browse/SKILL.md` | Screenshots, UI check | Prefer over gstack. |
| qa / qa-only | `/Users/pranay/.agents/skills/qa/SKILL.md` · `.../qa-only/SKILL.md` | Systematic QA | `qa` fixes; `qa-only` reports. |
| chrome-devtools | `/Users/pranay/.claude/plugins/cache/claude-plugins-official/chrome-devtools-mcp/1.6.0/skills/chrome-devtools/SKILL.md` | Network/console | Follow `chrome-devtools/SKILL.md` when MCP is connected. |

---

## Category: Review, architecture, docs

**Tell another agent:** Open `Docs/FULL_SKILLS_CATALOG.md`, search for category **Review, architecture, docs**, and follow its `SKILL.md` file.

| Skill | Absolute path | When | Instruction |
|---|---|---|---|
| exploration-doc-review | `/Users/pranay/.agents/skills/exploration-doc-review/SKILL.md` | “is this doc actually built?” | Follow it; script at `.../scripts/exploration_audit.py`. |
| plan-eng-review | `/Users/pranay/.agents/skills/plan-eng-review/SKILL.md` | Lock architecture before coding | Follow `plan-eng-review/SKILL.md`. |
| review (gstack-review) | `/Users/pranay/.agents/skills/gstack-review/SKILL.md` | Pre-landing PR | Only if asked for that workflow; not the default review path. Prefer Review Doctrine. |
| audit-task-triage | `/Users/pranay/Projects/skills/audit-task-triage/SKILL.md` | Collapse audits into one open-task list | Follow `audit-task-triage/SKILL.md` against the findings register. |
| planning-with-files | `/Users/pranay/.agents/skills/planning-with-files/SKILL.md` | Multi-step research | Follow it; planning files stay **in-repo** under `Docs/`, not `/tmp`. |
| document-release | `/Users/pranay/.agents/skills/document-release/SKILL.md` | Post-ship docs | Follow `document-release/SKILL.md`. |
| research | `/Users/pranay/.agents/skills/research/SKILL.md` | Sourced research file | Follow `research/SKILL.md`. |
| search-first | `/Users/pranay/Projects/skills/search-first/SKILL.md` | Before custom code | Follow `search-first/SKILL.md`. |
| think-widely | `/Users/pranay/.agents/skills/think-widely/SKILL.md` | Option frontier | Follow `think-widely/SKILL.md`. |

**Doctrines (not skills, still required):**

| Doctrine | Path | When |
|---|---|---|
| Operating | `/Users/pranay/Projects/agent-start/doctrines/OPERATING_DOCTRINE.md` | Always |
| Review | `.../REVIEW_DOCTRINE.md` | Audits |
| Architecture | `.../ARCHITECTURE_DOCTRINE.md` | Boundaries, contracts |
| Testing | `.../TESTING_DOCTRINE.md` | Evidence tiers |
| Security | `.../SECURITY_PRIVACY_SAFETY_DOCTRINE.md` | Auth/PII/money |
| Documentation | `.../DOCUMENTATION_DOCTRINE.md` | Durable artifacts |
| Research | `.../RESEARCH_DOCTRINE.md` | External facts |
| Release | `.../RELEASE_READINESS_DOCTRINE.md` | Launch |
| Inquiry | `.../INQUIRY_ANALYSIS_DOCTRINE.md` | 5W1H |

---

## Category: Payments, insurance, legal-adjacent

**Tell another agent:** Open `Docs/FULL_SKILLS_CATALOG.md`, search for category **Payments, insurance, legal-adjacent**, and follow its `SKILL.md` file.

| Skill | Absolute path | When | Instruction |
|---|---|---|---|
| security-review | `/Users/pranay/Projects/skills/security-review/SKILL.md` | Mandate, VCC, tokens | Follow it on money paths. |
| sensitive-source-audit | `/Users/pranay/Projects/skills/sensitive-source-audit/skill.md` | PII on loyalty/passport | Follow it; never invent FFN/passport (AT-13). |
| stripe-best-practices | `/Users/pranay/Projects/external-skills/stripe__ai/skills/stripe-best-practices/SKILL.md` | VCC, webhooks, Connect (no Projects/skills copy) | Read Stripe refs before touching `stripe_issuing_adapter.py`. Simulated today (AT-02/03). |
| pci-compliance | `/Users/pranay/.hermes/skills/compliance/pci-compliance/SKILL.md` | Card data / VCC | Never store PAN/CVV on Waypoint servers. |
| pricing-strategy | `/Users/pranay/.agents/skills/pricing-strategy/SKILL.md` | Agency pricing, packaging | Product-model DECIDE only (inventory R-10). |
| churn-prevention | `/Users/pranay/.agents/skills/churn-prevention/SKILL.md` | Ghost/window-shopper NBA | Adjacent to `decide_commercial_action` — do not confuse with travel NBA (AT-07). |

Insurance **product** personas are OrbitCover-scoped. For Waypoint: treat `/quote` and `/attach-policy` as preview/honesty work (AT-12), not carrier integration.

---

## Category: Launch & operations

**Tell another agent:** Open `Docs/FULL_SKILLS_CATALOG.md`, search for category **Launch & operations**, and follow its `SKILL.md` file.

| Skill | Absolute path | When | Instruction |
|---|---|---|---|
| deployment-patterns | `/Users/pranay/Projects/skills/deployment-patterns/SKILL.md` | CI/CD, health, rollback | Follow `deployment-patterns/SKILL.md`. |
| docker-patterns | `/Users/pranay/Projects/skills/docker-patterns/SKILL.md` | compose | Follow `docker-patterns/SKILL.md`. |
| render-deploy / render-blueprints | `/Users/pranay/.claude/plugins/cache/claude-plugins-official/render/0.2.0/skills/render-deploy/SKILL.md` | Render | Only after L1 platform choice. Note `render.yaml` currently pins `USE_HYBRID_DECISION_ENGINE=1` (contested vs PA-03). |
| launch-strategy | `/Users/pranay/.agents/skills/launch-strategy/SKILL.md` | GTM / launch checklist | Follow `launch-strategy/SKILL.md`; public launch is **NO-GO** (`Docs/LAUNCH_STATUS.md`). |
| health | `/Users/pranay/.agents/skills/gstack-health/SKILL.md` | Quality dashboard | Optional; prefer repo scripts `scripts/run_backend_tests.sh`. |

---

## Category: Research & exploration

**Tell another agent:** Open `Docs/FULL_SKILLS_CATALOG.md`, search for category **Research & exploration**, and follow its `SKILL.md` file.

| Skill | Absolute path | When | Instruction |
|---|---|---|---|
| research | `/Users/pranay/.agents/skills/research/SKILL.md` | Sourced markdown in-repo | Write under `Docs/exploration/` or `Docs/architecture/`. |
| parallel-web-search | `/Users/pranay/.agents/skills/parallel-web-search/SKILL.md` | Fast web facts | Default research search skill. |
| parallel-deep-research | `/Users/pranay/.agents/skills/parallel-deep-research/SKILL.md` | Exhaustive reports only | Only when the user asks for deep/exhaustive. |
| market-research | `/Users/pranay/Projects/skills/market-research/SKILL.md` | Competitive / sizing | Follow `market-research/SKILL.md`. |
| find-skills | `/Users/pranay/.agents/skills/find-skills/SKILL.md` | “is there a skill for X?” | Run all three discovery phases. |
| brainstorming | `/Users/pranay/.agents/skills/brainstorming/SKILL.md` | New product behavior | Follow before creative implementation. |

---

## Copy-paste prompt block (give this to any future agent)

```text
You are working in /Users/pranay/Projects/travel_agency_agent.

1. Read AGENTS.md (repo) and Docs/FULL_SKILLS_CATALOG.md.
2. Do not default to gstack.
3. Open Docs/FULL_SKILLS_CATALOG.md, search for category <CATEGORY>,
   and follow the listed SKILL.md (prefer ~/Projects/skills when duplicated).
4. For AI workflows, also load:
   /Users/pranay/Projects/skills/agentic-eval-loop/SKILL.md
   and /Users/pranay/Projects/AGENTIC_EVAL_RULES.md
5. Canonical findings status is Docs/review/FINDINGS_REGISTER_2026-08-31.md.
   PER-0443 addendum is Docs/review/FINDINGS_TASKS_IMPLICIT_EXPLICIT_REGISTER_PER0443_2026-09-07.md
   — do not create a second status store.
6. Do not import OrbitCover into Waypoint.
```

Replace `<CATEGORY>` with one of: `Agentic systems & evals` · `Travel operating system` · `Security, privacy, tenancy` · `Backend, contracts, state` · `Frontend & operator UX` · `Testing & verification` · `Review, architecture, docs` · `Payments, insurance, legal-adjacent` · `Launch & operations` · `Research & exploration`.

---

## Provenance

- Search order copied from repo `AGENTS.md` (2026-09-07).
- Workspace catalog: `/Users/pranay/Projects/SKILLS_CATALOG.md`.
- Live path checks: `~/Projects/skills/agentic-eval-loop/SKILL.md` exists; `~/Projects/skills/` listing 2026-09-07.

### Disk crawl (2026-09-07, this session)

Keyword scan of `SKILL.md` under the AGENTS.md stores:

| | Count |
|---|---:|
| `SKILL.md` files scanned | **11,279** |
| Keyword matches (travel/agent/eval/payment/… — **too broad**) | **9,736** |
| `~/Projects/skills` matches (prefer) | 161 |
| `~/.agents/skills` | 669 |
| `~/.claude/skills` | 853 |
| `~/.hermes/skills` | 4,418 (mostly marketplace mirrors) |
| `~/Projects/external-skills` | 3,499 (Composio + community clones) |
| This repo `.agents/skills` | 11 |

**Do not point another agent at the 9,736-hit list.** Community stores duplicate the same skill many times (e.g. `agent-harness-construction` appears under `~/Projects/skills`, `~/.hermes`, and `external-skills`). Canonical = this file’s tables, preferring `~/Projects/skills/` then `~/.agents/skills/`.

If a named skill is missing here, tell the agent:

> Open `Docs/FULL_SKILLS_CATALOG.md` §0, then load `/Users/pranay/.agents/skills/find-skills/SKILL.md` and run all three discovery phases. Install nothing from `external-skills` without a quality gate.

Adjacent high-signal skills found in the crawl but not duplicated in the tables above (use only if the category tables miss the need):

- `/Users/pranay/.hermes/skills/agent-architecture/agent-evaluation-framework/SKILL.md` — agent eval dimensions (accuracy/reliability/cost/latency/tool-use)
- `/Users/pranay/.hermes/skills/agent-architecture/agent-memory-patterns/SKILL.md` — working/episodic/semantic memory (pairs with AT-10 / E-D)
- `/Users/pranay/.agents/skills/adhd/SKILL.md` — divergent ideation (already used in this repo’s 2026-08-30 ADHD audit)
