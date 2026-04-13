# Rolling Context Synthesis

Last updated: 2026-04-13 (IST)

## Purpose
This document is the rolling synthesis of user-shared conversation drops.
It translates raw discussion inputs into stable implementation contracts and
execution priorities without deleting historical context.

## Canonical Principle
Treat the system as a compiler pipeline, not a freeform prompt generator.

Online path:
1. Context normalization
2. Intake routing/classification
3. Prompt composition from versioned blocks
4. Agent execution (generalist/specialist)
5. Verifier pass
6. Memory + telemetry update

Offline path:
1. Run eval harness on labeled cases
2. Mutate one dimension at a time
3. Accept only score-improving changes
4. Version and deploy

## Synthesis Snapshot

### Part 1 (including continuation)
- Product framing is B2B agency OS, not a generic direct trip planner.
- Core value is sourcing intelligence + suitability + waste detection.
- Voice/WhatsApp intake and workflow orchestration are first-mile priorities.
- Preserve strict sourcing hierarchy:
  1. Agency inventory
  2. Preferred suppliers
  3. Network inventory
  4. Open market fallback

### Part 2 (router/composer/verifier + autoresearch)
- Do not generate a new "optimized prompt" from scratch every turn.
- Use fixed taxonomy and registry-based prompt composition.
- Keep routing coarse in v1; split only with evidence.
- Apply "autoresearch" only in offline optimization loops, not live hot path.
- Require explicit contracts:
  - normalized packet schema
  - router output schema
  - prompt profile schema
  - verifier output schema
  - per-turn logging schema

## Immediate Implementation Contracts
1. Add/validate `taxonomy.json` (coarse domains first).
2. Define normalized context packet with hard/soft fields separation.
3. Make router JSON-only, classification-only, with confidence and escalation.
4. Build prompt registry (base + domain + policy + tool + output schema + few-shot).
5. Add verifier stage that can override escalation flags.
6. Log route/prompt/version/latency/cost/outcome for offline evals.

## Risks to Avoid
- Live taxonomy drift
- Per-turn freeform prompt rewriting
- Over-segmentation into many micro-agents
- No eval harness for optimization claims
- Hidden coupling between router and composer versions

## Open Intake Status
- User indicated more context drops are coming after Part 2 re-share.
- Keep ingesting each drop as a separate archive artifact or addendum.
- Merge into this rolling synthesis after each intake.
