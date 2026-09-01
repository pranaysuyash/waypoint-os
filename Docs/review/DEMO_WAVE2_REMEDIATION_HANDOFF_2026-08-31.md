# Handoff — Demo Remediation Wave (IMP-02/03/05/06/07)

*Date: 2026-08-31 · Follows: [IMP01_ESCALATE_LEAD_PERSISTENCE_HANDOFF_2026-08-31](IMP01_ESCALATE_LEAD_PERSISTENCE_HANDOFF_2026-08-31.md) · Briefs: `Docs/exploration/DEMO_FOLLOWUP_TASK_BRIEFS_2026-08-31.md`*
*Checklist applied: IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md*

## 1. Executive Summary

Shipped the remaining demo remediation in one reviewed wave: **IMP-02** colloquial extraction (the demo note now extracts Tokyo/Kyoto/Osaka, party 4, "next spring (Mar-May), late march", per-person budget — it now DEGRADEs into a visible lead instead of dead-ending), **IMP-03** sample-profile honesty (Alex Morgan panel badged, fake-ified, injection button removed, state-aware empty states), **IMP-05** repair navigation (blocked banner reaches the editable trip intake surface), **IMP-06** copy sweep, **IMP-07** 15 colloquial fixtures wired into the F-18/D6 audit gate (F1 1.0, honest live-collector green, drift-protected, proven to trip on revert). Two review cycles; final verdict **APPROVE, P0: 0, P1: 0**. Code-ready ✅ · Feature-ready ✅ · Launch-ready ✅ (dev; visual banner confirmation from IMP-01 still the one pending manual item).

## 2. What Changed

| Stream | Files | Substance |
|---|---|---|
| IMP-02 extraction | `src/intake/extractors.py`, `validation.py`, `packet_models.py`, `tests/test_extraction_fixes.py` | Destination verb-object phrasings + leading-word retry + city-set pass (+/,/and separators, `or` preserved for options) + `somewhere` position-restricted; party group patterns (`me/us and N friends` incl. +1 self for "us", `N of us`, word numbers, `party of N`) with `PARTY_UNDERDETECTED`/`PARTY_UNPARSED_GROUP_PHRASING` warnings (never silent); season windows (qualifier required) + `late/early/mid month` + flexibility phrases; budget `each`→per_person; dead `_TRAVEL_VERB_DEST_RE` shadow removed |
| IMP-07 gate | `data/fixtures/extraction/colloquial_golden.json` (new, 15), `src/evals/audit/snapshot.py`, `manifest.yaml`, `scripts/verify_d6_gate_snapshot.py`, `tests/evals/test_d6_gate_snapshot.py` | New `colloquial` gating category (min_accuracy 0.85) in the D6 audit gate; stable view gained `by_document_type`/`by_difficulty` fixture_accuracy (closes the budget view's value-regression blind spot); guard-proof: revert of one pattern → verify exits 1; restore → 0 with byte-identical hash |
| IMP-03 sample profile | `RepeatTravelerRecallCard.tsx`, `IntakeTab.tsx` | "Sample data" badge; honest copy; loyalty numbers zeroed; provenance marked `Sample:`; **Apply-to-Proposal removed** (it injected `[Verified Profile Memory Applied]` facts into real runs); component now prop-less (structurally cannot pipe sample data); empty state now draft-status-aware (blocked/processing/failed/open), recall card gated `!trip` |
| IMP-05 repair nav | `PageClient.tsx` | "Review Missing Fields" → `<Link>` to `/trips/{id}/intake` (editable IntakePanel) when a trip exists; packet-tab fallback when not |
| IMP-06 copy | signup/login/forgot/join/AuthProvider, `useRuntimeVersion.ts`, `.env.local.example` | "Work email"→"Email", `you@agency.com`→`you@example.com` (zero remaining); runtime chip gated behind `NEXT_PUBLIC_SHOW_RUNTIME_META` (default hidden) |

## 3. Review Cycles (combined reviewer, whole-tree scope per doctrine)

- **Cycle 1: FIX-FIRST (P1: 2).** P1-1 bare-season regex invented `date_window` from prose verbs ("we will **fall** in love" → a season window — on an INTAKE_MINIMUM field); P1-2 `"each"` scope heuristic overrode explicit totals ("5000 total, breakfast each morning" → per_person — inverting the 4x-misquote class it fixed). Plus P2s: "us and N" undercount, prose "of us" false signals + duplicate unknowns, city-set origin hole (and the or-pattern hole behind it), sibling-panel inconsistency, unimplemented AC2/AC3.
- **Cycle 2: APPROVE (P0: 0, P1: 0).** All findings RESOLVED with probe evidence. Notably: my first P2-3 fix (adding "us" to the always-self pattern) regressed "one of us" → party 1, and the **new colloquial gate caught it red** before any human noticed — the structural protection working exactly as built; fixed via a scoped +1 self in the self-plus branch. Two P3 nits acknowledged (untested `failed` branch; multi-word canonical-name edge in `_is_origin_candidate`), non-blocking.

## 4. Verification

- Backend: **377 passed** across extraction (242→260 with review tests), gate (52), escalate/persistence, spine-unit, roundtrip canaries; **340-test extractor-adjacent regression sweep** green; ruff clean.
- Gate: `verify_d6_gate_snapshot.py` exit 0 — colloquial F1 1.0 over 15 fixtures, honest live-collector; revert-proof demonstrated (exit 1 on pattern revert, byte-identical restore).
- Demo-note anchor: `[Tokyo, Kyoto, Osaka]` semi_open · party 4 · budget 3500 USD per_person · "next spring (Mar-May), late march" · flexible · no PARTY warnings — identical across unit test, gate fixture, and live pipeline (triple-verified).
- Frontend: tsc clean; 36+ targeted vitest green (RecallCard 7, IntakeTab 6, page 14, runtime 3, blocking-copy 6); eslint 0 errors.

## 5. Audit (condensed)

Code ✅ · Operational ✅ · UX ✅ (the demo's dead-ends are all now through-paths) · Logical ✅ (existence/epistemics split preserved; qualifier-gated dates) · Commercial ✅ (4x misquote class closed + gate-protected) · Data integrity ✅ (party never silently 1 when group phrasing exists) · Compliance ✅ (fake facts can no longer enter runs) · Critical path ✅ · **Verdict: Merge Yes · Feature-ready Yes · Launch-ready Yes (dev)**.

## 6. Deferred (documented, non-blocking)

1. **P2-6**: sibling hardcoded Alex Morgan defaults (`MemoryArchitectPanel`, `CrisisEvacuationPanel`, `MemorySettingsTab`) need the same sample treatment.
2. **P2-7 AC2/AC3**: `?repair=<field>` deep-link + focus/auto-open of the first empty editor in IntakePanel (machinery exists at IntakePanel.tsx:1032, :1231-1237).
3. **Schema gaps needing contract decisions**: `trip_duration`, `flights_inclusiveness` ambiguity, `destination_country` containment model (DEMO-02 §9 Q1–Q3).
4. **Gate notes**: warning-codes not assertable in the gate format; `expected-as-actuals` fallback inherited from F-18; "+"-joined city sets remain `semi_open` (status-semantics decision pending).
5. **IMP-01 residue**: banner visual confirmation still pending (environment); register integration awaits ratification.
