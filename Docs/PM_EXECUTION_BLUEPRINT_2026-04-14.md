# PM Execution Blueprint: Flows, JTBD, Aha, and What Still Needs Work

**Date**: 2026-04-14  
**Timezone**: Asia/Kolkata  
**Audience**: Product, Agency Operations, Engineering, Founders

---

## 1) What Makes the Product Tick

This product works when it reliably converts unstructured demand into decision-ready agency output.

Core product loop:
1. Intake quality improves (better extraction + blocker detection).
2. Agent turnaround time drops.
3. Client confidence and option acceptance rise.
4. More real usage data enters the system.
5. Suggestions and defaults improve.

If any link breaks (poor intake accuracy, wrong blocker priorities, weak proposal clarity), the loop stalls.

---

## 2) Persona Outcomes and North-Star Jobs

### Agency Owner
- Primary job: scale trip throughput without quality collapse.
- Aha moment: weekly dashboard shows throughput up while escalations down.
- Success indicators:
  - trips/agent/week
  - escalation rate
  - repeat-client share

### Agency (Senior Agent / Core Operator)
- Primary job: turn messy briefs into confident options fast.
- Aha moment: first inquiry-to-options cycle drops from hours to minutes.
- Success indicators:
  - time to first draft
  - follow-up rounds per trip
  - first-send quality score

### User (Junior Agent)
- Primary job: execute safely and learn fast.
- Aha moment: closes first trip thread without senior rewrite.
- Success indicators:
  - senior edit rate
  - blocker miss rate
  - independent completion rate

### End Client (Traveler)
- Primary job: choose confidently from clear options.
- Aha moment: options map directly to stated priorities and constraints.
- Success indicators:
  - first-response acceptance rate
  - decision latency
  - clarification burden

---

## 3) End-to-End User Flows (Product-Critical)

### A) Senior Agent Flow: Intake to Options
1. Paste/import client thread.
2. Review extracted brief + blockers + contradictions.
3. Send high-signal follow-up questions.
4. Re-run with clarified constraints.
5. Generate 2-3 options with trade-offs.
6. Edit and send traveler-safe output.

Critical product checks:
- Ask only when hard blockers remain.
- For discovery/shortlist, allow business-ready drafts even if budget is tight/infeasible (internal draft path).
- Never leak internal-only reasoning to traveler-safe output.

### B) Agency Owner Flow: Weekly Control Tower
1. Open agency health snapshot.
2. Inspect bottleneck stages (intake/question/proposal/booking).
3. Drill into top failure clusters.
4. Assign process interventions and training actions.
5. Review experiment outcomes and decide keep/tweak/stop.

### C) Junior Agent Guided Flow
1. Start from guided intake template.
2. Resolve mandatory blockers queue.
3. Generate draft and request spot-check.
4. Submit final with captured learnings.

### D) Traveler Decision Flow
1. Receive concise, comparable options.
2. Ask clarifying question in same thread.
3. Confirm selected option.
4. Move to booking checklist.

---

## 4) Policy and Routing Update Applied Today

Decision policy was tuned so business-ready scenarios move from over-conservative `ASK_FOLLOWUP` to `PROCEED_INTERNAL_DRAFT` where appropriate.

Implemented behavior:
- `budget_feasibility` contradiction priority lowered from `critical` to `high`.
- Infeasible budget stage gating:
  - `proposal`/`booking`: remains hard blocker.
  - `discovery`/`shortlist`: treated as soft blocker + contradiction, allowing internal draft progression.

Validation:
- `PYTHONPATH=src uv run pytest -q tests/test_nb02_v02.py tests/test_decision_policy_conformance.py`
- Result: `24 passed`.
- Updated E2E run written to:
  - `Docs/reports/e2e_existing_plus_new_2026-04-14.md`
  - `Docs/reports/e2e_existing_plus_new_2026-04-14.json`

---

## 5) Synthetic Data Added for Product and UX Work

New fixture file:
- `data/fixtures/product_persona_flows_synthetic_v1.json`

Contains:
- persona-level JTBD (functional/emotional/social)
- role-specific aha moments and metric proxies
- end-to-end flows by persona
- product flywheel instrumentation
- open PM questions for roadmap planning

Use this file for:
- PM workshop alignment
- UX acceptance criteria drafting
- telemetry schema planning
- scenario simulation in QA/ops reviews

---

## 6) What We Still Need to Think Through (Priority Backlog)

### P0 (Execution Order Lock: First Principles)
1. Parser-first (deterministic constraints):
   - typed parsers for dates, money, pax, locations
   - locale-aware money/date parsing
   - hard rule: date-shaped tokens can never satisfy budget fields
2. NER/IE second (semantic fill + disambiguation):
   - extract destination, purpose, preferences, medical/accessibility, group structure
   - output confidence + evidence spans (not value-only extraction)
3. OCR/document ingestion layer:
   - support WhatsApp screenshots, PDFs, passports/visa docs, invoices
   - preserve OCR provenance (line/box) for citation and traceability
4. Schema + confidence gate:
   - typed validation before decision policy
   - low-confidence/conflicting critical fields -> `ASK_FOLLOWUP` / `STOP_NEEDS_REVIEW`
5. Fallback strategy:
   - deterministic parser > NER suggestion > regex fallback (never reverse for critical fields)

### P0 (Now)
1. Define stage-specific quality gates for `PROCEED_TRAVELER_SAFE`.
2. Lock a canonical follow-up question strategy (minimal questions, maximum clarity).
3. Create explicit traveler-safe redaction policy and tests.
4. Define Option Quality Rubric (fit, feasibility, clarity, trade-off honesty).

### P1 (Next)
1. Build operator dashboards with actionable deltas, not vanity counts.
2. Add role-based playbooks (owner/senior/junior) and measurable training loops.
3. Implement experiment framework for blocker threshold tuning.
4. Define re-engagement lifecycle (stalled leads, post-proposal drift).

### P2 (Later)
1. Repeat-client memory with consent boundaries.
2. Verticalized packs (family leisure, pilgrimage, corporate, luxury).
3. Integration strategy sequencing (calendar, CRM, pricing feeds).
4. Pricing-packaging tests tied to measurable value realization.

---

## 7) Product Management Operating Cadence

### Weekly
- Review funnel by stage and persona.
- Inspect top blocker categories and contradiction types.
- Ship one quality improvement in intake/question/proposal path.

### Biweekly
- Run one controlled experiment (policy or UX prompting).
- Validate improvement against a fixed baseline scenario set.

### Monthly
- Re-score roadmap using impact/effort/confidence.
- Decide which assumptions are now evidence-backed vs still risky.

---

## 8) Immediate Next Steps

1. Add acceptance tests for stage-aware budget gating in discovery vs proposal/booking.
2. Add telemetry fields for each flow checkpoint in `product_persona_flows_synthetic_v1.json`.
3. Define and publish a one-page operator rubric for “ready to send to traveler”.
4. Establish monthly PM review doc template tied to this blueprint.
