# Gemini Wave — Findings for Review (Named & Consolidated)

*Date: 2026-09-02 · Purpose: review-ready consolidation of every finding from the parallel "Gemini" agent wave (2026-09-01), named as such, split by authorship so the reviewer can distinguish Gemini's own findings/fixes from audit findings about Gemini's work.*
*Companion evidence: `Docs/exploration/GEMINI_WAVE_MODULE_AUDIT_2026-09-01.md` (audit of the wave's ~30 modules), `Docs/exploration/SIM_VS_REALITY_RECONCILIATION_2026-09-01.md` (30-claim adjudication), `Docs/exploration/AGENTIC_DEEP_AUDIT_SYNTHESIS_2026-08-31.md` §2.5.*
*Checklist applied: IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md*

---

## Section A — Findings BY Gemini (self-documented in its simulation wave)

Source: `Docs/personas_scenarios/MASTER_PRODUCT_DEMO_SIMULATION_CHRONICLE_2026-09-01.md` §7 ("Discovered Friction & Verification Status"), implemented by Gemini in the working tree. Each item lists the independent verification status added by this audit.

| ID | Gemini's Finding | Gemini's Fix | Audit Verification |
|---|---|---|---|
| **GF-01** | Salutation entity extraction: `Hi Sam!` at message start caused the name to be extracted as a destination | Added `_SALUTATION_RE` to strip greetings in `extractors.py` | Plausible per pattern placement; re-verify with `"Hi Sam! we want to go to bali"` probe |
| **GF-02** | Colon budget connectives: `Budget: Around $14,000` missed parsing | Extended `budget_connective` regex to support colons | Consistent with the budget-scope work; covered by extraction suite |
| **GF-03** | Inline destination labels with parentheticals: `Destinations: Tokyo (4 nights) and Kyoto (6 nights)` | Added `\bdestinations?:\s*([^.\n]+)` regex with parenthetical stripping | Verify interplay with the new city-set pass (both touch multi-destination input) |
| **GF-04** | Settings `tab=comm` red toast on fresh workspaces (missing defaults) | Safe fallback defaults in `CommSettingsTab.tsx` | Frontend fix; verify `CommSettingsTab` renders with zero settings |
| **GF-05** | VCC generation endpoint 404 (relative `/api/v1` path without proxy rewrite) | **Changed fetch to explicit `http://127.0.0.1:8000`** with graceful fallback | ⚠️ **The fix is itself a defect** — see audit finding PT-07 (my findings doc): a hardcoded localhost backend URL breaks every non-local deployment and violates the BFF proxy pattern |

**Gemini's process outcomes (also BY Gemini, register/plan level):**

- **GF-06**: A-14 closed (uncommitted-P0 exposure) — authorized commit `2f9a638` + `A1_1_WORKTREE_CLASSIFICATION_CLOSURE_2026-09-01.md` with machine-checked CSV ledgers (`tools/check_worktree_classification.py`).
- **GF-07**: A-21 closed (parallel-remediation ownership) via the same classification closure.
- **GF-08**: Implementation-plan Wave-0 item 0.4 closed; exit gate 0 correctly left "partially open" (0.3 baseline still required — honest).
- **GF-09**: 12 persona docs (`Docs/personas/PERSONA_*.md`) + 4 live simulations + 16 case studies + simulation chronicle — significant institutional record, **with the caveat** that 17 of 30 capability claims in it are simulated (see Section C).
- **GF-10**: ~30 new wired modules + ~20 new test files (116/116 green) + Dockerfiles.

## Section B — Findings FROM the audit OF Gemini's wave (not by Gemini)

Full evidence in the two companion audit docs; summarized here so the reviewer sees everything in one place. **These are the items most in need of review decisions.**

| ID | Finding | Sev | Suggested disposition |
|---|---|---|---|
| **GM-01** | The wave is two interleaved bodies: (A) genuine hardening; (B) simulated-capability expansion | — | **Split the commit**: land (A) separately from (B) |
| **GM-02** | `spine_api/providers/*` modules named "Production … Adapter" with zero callers and zero network calls; Amadeus docstring claims "live OAuth2" vs in-process simulator | P1 | Rename to `sandbox`/`simulated`, or gate behind real credentials |
| **GM-03** | Stripe `verify_webhook_signature` returns `True` unconditionally (`stripe_issuing_adapter.py:84-90`) — a fake security control | P0-adj | Real signature verification or remove the control surface |
| **GM-04** | Proposal HMAC tokens: hardcoded default secret, ≥16-char "legacy" bypass, test-agency UUID in verify loop | P0-adj | See my findings doc PT-01…PT-06 for the full line-level breakdown |
| **GM-05** | The 116 new tests validate the simulation's shape, not reality | P2 | Mark sim lanes as such in test names/manifests |
| **GM-06** | 9 src/ modules + yield-arbitrage engine have zero production callers (orphaned capability, code-ahead-of-record) | P2 | Wire-or-archive decision per module |
| **GM-07** | 12 new routers skip `_auth_or_skip` — safe only via global AuthMiddleware ordering | P2 | Explicit dependency on each new route |
| **G-01-amp** | 12 NEW unlabeled simulated panels; GDSSandboxPanel says "Live" for uuid-fabricated offers | P1 | Label-or-gate (never-both-and-hidden rule) |
| **REC-1** | 30 chronicle/case-study claims: 7 VERIFIED / 5 PARTIAL / 17 SIMULATED — extraction claims genuinely verify post-IMP-02 | P1 (record) | Annotate chronicle + 16 case studies with a simulator caveat |
| **REC-2** | G-01…G-19 + GM-01…GM-09 captured in no register; BUILD_QUEUE marks shadow modules "Completed"; A-18 has opposite statuses in two registers | P1 (record) | Register-integration pass + resolve the A-18 split |

## Section C — Reviewer checklist (what to actually verify)

1. **GM-03 / GM-04 first** — both are small diffs with security impact; PT-01…PT-06 (my findings doc) give the exact lines.
2. **Commit split** — confirm which files belong to hardening (A) vs simulator expansion (B); the module audit's wiring table is the source.
3. **GF-05 (VCC URL)** — decide the correct fix: restore the BFF-relative path with the proxy rewrite, not a hardcoded backend URL.
4. **G-01-amp labeling** — pick label-or-gate per simulated panel (12 new + previously flagged).
5. **REC-1 annotations** — approve the simulator-caveat wording for the chronicle + case studies.
6. **Register integration** — authorize the pass that adds G-01…G-19, GM-01…GM-09, REC-1/2 rows to the consolidated register (resolving the A-18 split at the same time).
