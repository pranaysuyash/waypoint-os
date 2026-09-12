# Audit Personas In Use — In-Repo Record of the Audit Methodology's Identity Layer

**Date**: 2026-09-02 · **Purpose**: make the persona-council audit methodology reproducible in-repo. The audit identities (`PER-*`) that frame every exploration and review doc live in an external Desktop repository; this file records the six personas applied in the 2026-08-31/09-02 audit cycle — who they are, which doc each framed, and where the full definitions live.
**Origin**: shadow-audit R-07 / §3(d)1 of `Docs/exploration/DOCS_CORPUS_SHADOW_AUDIT_2026-08-31.md` ("Persona definitions on the Desktop… are not in the repo"). The `/tmp/personas_txt/` conversions used during the audit session were ephemeral and no longer exist; the source `.docx` repository below is the durable source.

**Full persona repository (read-only, external to this repo):**
`/Users/pranay/Desktop/Understanding_Personas_29aug26/` — registry + 15 families under
`01 Expanded Personas/`; this is the snapshot cited by `Docs/review/PERSONA_COUNCIL_AUDIT_2026-08-31.md:7`
and `Docs/exploration/AGENTIC_DEEP_AUDIT_SYNTHESIS_2026-08-31.md` §1. A later snapshot,
`/Users/pranay/Desktop/Understanding_Personas_sept6/`, carries the same six files. Master
registry: `00 Registry & Governance/Master Persona Registry.xlsx`. If the Desktop copies are
ever reorganized, the definitions below (summarized 2026-09-02 from the `29aug26` snapshot)
remain valid in-repo context.

> Note: `Docs/personas/PERSONA_*.md` files are **product personas** (Elena, Marcus, …) — a
> different concept. This file is about **audit personas** (methodology lenses).

---

## PER-0700 — Agentic Systems Architect

**Family**: Agentic systems (`07 Agentic AI & Exploration/PER-0700 - Agentic Systems Architect.docx`)
Designs systems where agents pursue goals through tools, state, memory, planning, delegation
and feedback while staying observable, bounded, and recoverable. Central test: *"first ask
whether deterministic workflow, direct tools or conventional automation are sufficient"*
before justifying adaptive autonomy; where agents are justified, make state, tools, authority,
completion, and failure semantics explicit. Known failure modes include "agent for every
workflow," prompts carrying business logic, and success judged by plausible conversation.
**Framed**: `Docs/exploration/AGENTIC_FLOW_DEEP_MAP_2026-08-31.md` (the real pipeline map:
the serving path is 100% deterministic), and the keep/wire/archive verdicts in
`Docs/exploration/C02_WIRE_OR_ARCHIVE_DOSSIERS_2026-09-02.md` (§3 applies its decision
framework).

## PER-0882 — Model-Routing Optimization Engineer

**Family**: Agentic systems (`07 Agentic AI & Exploration/PER-0882 - Model-Routing Optimization Engineer.docx`)
Designs dynamic policies that choose the model/provider/inference path per request based on
task difficulty, modality, cost, latency, privacy and quality — and demands evidence that a
routing policy beats one-model-for-everything. Warns against routing on prompt length alone,
uncalibrated weak classifiers causing silent quality loss, and cost savings measured without
task success; keeps critical constraints deterministic. **Framed**:
`Docs/exploration/BROWSER_LLM_SLM_RESEARCH_2026-08-31.md` (browser/on-device inference
research; deterministic extractors correctly understood as routing tier 0), and co-framed
`C02_WIRE_OR_ARCHIVE_DOSSIERS_2026-09-02.md` and `Docs/exploration/C03_ROUTER_DESIGN_2026-09-02.md`.

## PER-0897 — Agent Evaluation Architect

**Family**: Agentic systems (`07 Agentic AI & Exploration/PER-0897 - Agent Evaluation Architect.docx`)
Designs the end-to-end framework for measuring agent quality at component, trajectory, and
outcome levels, before and after deployment. Central question: *what evidence proves this
agent reliably achieves the intended task under representative and difficult conditions?*
Flags final-answer-only evaluation, uncalibrated model-as-judge, benchmarks detached from
real tasks, and evaluation sets leaked into development. **Framed**:
`Docs/exploration/EVAL_ARCHITECTURE_AND_RED_TEAM_AUDIT_2026-08-31.md` (jointly with
PER-PDEV-0425 and PER-0902) — the audit that confirmed the eval-harness "expected-as-actual"
lanes and the colloquial-fixture holdout leak.

## PER-PDEV-0425 — LLM Evaluation Specialist

**Family**: Testing, research & validation (`13 Testing, Research & Validation/PER-PDEV-0425 - LLM Evaluation Specialist.docx`)
Evaluates language-model behavior with curated datasets, human rubric review, model graders,
pairwise comparison, and adversarial prompt sets; insists subjective rubrics be calibrated on
shared examples, graders validated against expert humans, and hidden holdouts maintained.
Evaluates by task and failure slice, inspecting disagreements and exemplar outputs rather
than trusting averages. **Framed**: `EVAL_ARCHITECTURE_AND_RED_TEAM_AUDIT_2026-08-31.md`
(LLM-output evaluation dimension of the eval audit, including the F1=1.0-memorization
finding).

## PER-0902 — Agent Red-Team Specialist

**Family**: Agentic systems (`07 Agentic AI & Exploration/PER-0902 - Agent Red-Team Specialist.docx`)
Adversarially tests agent systems for unsafe, unauthorized, deceptive, brittle, or
exploitable behavior across prompts, tools, data, memory, permissions, and multi-step
actions. Demands confirmed, reproduced exploit paths (not speculative threats) and durable
mitigations plus regression tests; attacks the full trust boundary, including tool side
effects and cross-tenant risk. **Framed**: `EVAL_ARCHITECTURE_AND_RED_TEAM_AUDIT_2026-08-31.md`
§3 (confirmed red-team findings: escapeable egress delimiter `llm_egress.py:193`,
cross-tenant draft-promote, unauthenticated 100KB CPU-amp endpoint, unbounded
`structured_json` recursion, legacy unpartitioned memory store).

## PER-0930 — Shadow-System Investigator

**Family**: Meta-reasoning & product systems (`14 Meta-Reasoning & Decision Systems/PER-0930 - Shadow-System Investigator.docx`)
Discovers the unofficial spreadsheets, side channels, hidden approvals, and tacit processes
that exist because the official record does not match reality — then classifies root cause
and separates harmful process debt from valuable unmet-capability signals. Treats "official
process equals actual process" as the core fallacy. **Framed**:
`Docs/exploration/DOCS_CORPUS_SHADOW_AUDIT_2026-08-31.md` (docs-vs-code shadow map,
verified-claims ledger) and `Docs/exploration/SIM_VS_REALITY_RECONCILIATION_2026-09-01.md`
(30 chronicle/case-study claims adjudicated: 7 VERIFIED / 5 PARTIAL / 17 SIMULATED).

---

## How to reuse this methodology

1. Pick the persona whose central question matches the audit target (deterministic-vs-agentic
   → PER-0700; routing → PER-0882; eval design → PER-0897/PER-PDEV-0425; adversarial
   → PER-0902; record-vs-reality → PER-0930).
2. Load the persona's docx from the Desktop repository (path above) — or use the summaries
   here if the desktop copy moves.
3. Apply it as the audit lens and cite the persona ID in the produced doc's header (the
   convention used across `Docs/exploration/` since 2026-08-31).
4. Record which doc the persona framed by adding a row here, keeping the audit identity
   layer recoverable in-repo.
