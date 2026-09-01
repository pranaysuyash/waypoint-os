# Demo Follow-Up Task Briefs — Tool-Taster Simulation (2026-08-31)

*Source: `Docs/SIMULATED_PRODUCT_DEMO_TOOL_TASTER_2026-08-31.md` (computer-use persona demo).*
*Status: Briefs authored 2026-08-31. Findings are pending Pranay's ratification before integration into `Docs/review/FINDINGS_TASKS_CONSOLIDATED_2026-08-30.md` (proposed register IDs F-19…F-26 — do NOT self-register; the lifecycle checker + ratification flow governs).*
*Checklist applied: IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md*

---

## 1. Master Inventory (explicit + implicit findings)

Legend: **SRC** = explicit (observed and recorded during demo) / implicit (surfaced in post-demo analysis). **TYPE** = EXPLORE (research + document first) / IMPLEMENT (code change) / DECISION (product call, owner: Pranay).

| ID | Finding | SRC | Type | Disposition |
|----|---------|-----|------|-------------|
| DEMO-01 | **P0 — Lead Inbox promise broken**: pipeline blocks a draft but no lead ever appears in Lead Inbox ("0 leads total"), contradicting the workbench banner ("incomplete leads appear in Lead Inbox") | explicit | EXPLORE → IMPLEMENT | EX-DEMO-01 → IMP-01 |
| DEMO-02 | **P1 — Colloquial extraction misses**: "do japan" + "tokyo + kyoto + osaka" → Destinations `-`; "next spring / late march / flexible ±1 week" → Dates missing | explicit | EXPLORE → IMPLEMENT | EX-DEMO-02 → IMP-02 |
| DEMO-03 | **P1 — Party-size silent error**: "me and 3 friends" (4 pax) → Party 1. Silent wrong data is commercially worse than missing data | explicit | EXPLORE → IMPLEMENT | EX-DEMO-02 → IMP-02 |
| DEMO-04 | **P1 — Stranger profile on fresh tenant**: "Alex Morgan — Repeat Client (3 Bookings) — Delta SkyMiles #928410294…" renders pre-processing on a 0-trip account | explicit | EXPLORE → IMPLEMENT | EX-DEMO-04 → IMP-03 |
| DEMO-05 | **P1-suspect — `/inbox` renderer crash** ("Aw, Snap! Error code: 5") on first load; recovered on reload | explicit | EXPLORE → conditional IMPLEMENT | EX-DEMO-05 → IMP-04 |
| DEMO-06 | **P2 — Repair-surface discoverability**: "Review Missing Fields" does not visibly navigate/scroll/focus an editable form | explicit | EXPLORE → IMPLEMENT | EX-DEMO-06 → IMP-05 |
| DEMO-07 | **P3 — Copy/label drift**: "WORK EMAIL / you@agency.com" gating framing; sidebar label drift ("Waypoint HQ" → "Agency Workspace"); "runtime · development" chip exposure | explicit | EXPLORE (light) → IMPLEMENT (trivial) | EX-DEMO-07 → IMP-06 |
| DEMO-08 | **Stale empty-state copy**: "Captured details will appear here after processing the inquiry" remains true-looking after processing ran and after a blocked result | implicit | EXPLORE | EX-DEMO-04 (same panel family) |
| DEMO-09 | **Blocked banner lacks actionable specificity**: "Trip details are incomplete" without naming missing fields on the first surface; user must click through to Trip Details | implicit | EXPLORE (design note, folds into EX-DEMO-01/06) | EX-DEMO-01 + EX-DEMO-06 |
| DEMO-10 | **Full packet coverage unknown**: visible table only showed Destinations/Destination Status/Budget Min/Max. Unknown whether captured: dietary (vegetarian), fear constraint (no cable cars), activity wish (cooking class), accommodation hint (unnamed ryokan from TikTok), party=4, flexible date window, per-person vs total budget ambiguity, "not sure if includes flights" ambiguity | implicit | EXPLORE (contract-driven: run the pipeline on the exact note and inventory) | EX-DEMO-03 |
| DEMO-11 | **Confidence/authority labeling oddity**: "Destination Status: open @80%, authority=explicit_user" while Destinations itself was never captured — is `explicit_user` truthful there? | implicit | EXPLORE | EX-DEMO-03 |
| DEMO-12 | **Multi-destination modeling**: note contains country (Japan) + 3 cities; "Destination Status: open" implies open-trip support. How should country+city sets be modeled? | implicit | EXPLORE | EX-DEMO-02 |
| DEMO-13 | **Eval/real-world gap**: golden set F1 0.9524 (F-18 budget gate) coexists with these misses → colloquial-phrasing fixtures should feed the D6/F-18 audit-gate eval set, not ad-hoc patterns | implicit | EXPLORE (fixture draft) → IMPLEMENT (manifest wiring) | EX-DEMO-02 → IMP-07 |
| DEMO-14 | **Signup has no email verification** — great demo friction, unknown production posture (spam/fake-tenant risk). Also "WORK EMAIL" framing vs hobbyist signups | implicit | DECISION | DEC-01 (Pranay) |
| DEMO-15 | **Demo-harness limitations** (dropped synthetic keystrokes, macOS Space drift, AX tree timeouts on heavy pages) — must be documented so future sessions don't misattribute harness noise to product bugs | implicit (meta) | EXPLORE (document only) | EX-DEMO-05 (same agent) |

## 2. Explore Work Packages (dispatched to subagents this session)

| Package | Covers | Agent | Deliverable |
|---------|--------|-------|-------------|
| EX-DEMO-01 | DEMO-01 (+DEMO-09 banner specificity) | A | `Docs/exploration/DEMO01_LEAD_ROUTING_GAP_2026-08-31.md` |
| EX-DEMO-02 | DEMO-02, DEMO-03, DEMO-12, DEMO-13 | B | `Docs/exploration/DEMO02_COLLOQUIAL_EXTRACTION_GAPS_2026-08-31.md` |
| EX-DEMO-03 | DEMO-10, DEMO-11 | C | `Docs/exploration/DEMO03_PACKET_COVERAGE_AND_CONFIDENCE_2026-08-31.md` |
| EX-DEMO-04 | DEMO-04, DEMO-08 | D | `Docs/exploration/DEMO04_SAMPLE_PROFILE_PROVENANCE_2026-08-31.md` |
| EX-DEMO-05 | DEMO-05, DEMO-15 | E | `Docs/exploration/DEMO05_INBOX_CRASH_INVESTIGATION_2026-08-31.md` + `Docs/exploration/DEMO08_HARNESS_LIMITATIONS_2026-08-31.md` |
| EX-DEMO-06 | DEMO-06 (+DEMO-09 UX angle) | F | `Docs/exploration/DEMO06_REPAIR_SURFACE_UX_2026-08-31.md` |
| EX-DEMO-07 | DEMO-07 | F | (section inside DEMO06 doc: "Copy & label audit") |

## 3. Implementation Briefs (NOT dispatched — atomic packages for implementation agents)

### IMP-01 — Close the lead loop (blocked draft → Lead Inbox), or fix the promise
- **Depends on:** EX-DEMO-01 decision (promote blocked drafts to leads vs change banner copy).
- **Scope:** the minimal path EX-DEMO-01 recommends; one route/pipeline transition or one copy string + state gate. No parallel route creation (global no-duplicate-routes rule); extend canonical pipeline only.
- **Acceptance:** E2E test: fresh tenant → process note → blocked → Lead Inbox shows the lead (or banner no longer promises it). `uv run ruff check` clean; relevant pytest files pass; handoff doc with code/feature/launch verdicts.
- **Risk:** P0 path; Risk-Class high (touches lead lifecycle), Evidence-Tier 3 (contract-driven E2E evidence required).

### IMP-02 — Colloquial extraction: destination, party, flexible dates
- **Depends on:** EX-DEMO-02 catalog + fixture drafts.
- **Scope:** extend canonical extractors in `src/intake/extractors.py` (no forked pipeline); handle: verb-object destinations ("do/hit/cover japan"), country+city sets, group-size phrasings ("me and N friends", "the four of us", "N of us"), relative date windows ("next spring, late march", "flexible ±1 week"). Party under-detection must emit a validation warning (not silent 1) per Pattern 5 (clamp/warn, never skip).
- **Acceptance:** new eval fixtures (from EX-DEMO-02) pass; existing golden dataset still green (cite `scripts/run_backend_tests.sh` baseline 3,215/0 — only cite baselines from that script); zero regressions in `tests/test_extraction_fixes.py`.

### IMP-03 — Gate the sample profile (Alex Morgan) on fresh tenants
- **Depends on:** EX-DEMO-04 provenance verdict.
- **Scope:** preferred: render the pre-processing memory panel only on a real tenant-memory hit; fallback: explicit "Sample data" badge + no real-looking loyalty numbers. Same component, no duplicate panel.

### IMP-04 — `/inbox` crash fix (conditional)
- **Depends on:** EX-DEMO-05 repro verdict. If not reproducible outside harness: file as watch-item with repro protocol, no code change.

### IMP-05 — Repair surface anchor + focus
- **Depends on:** EX-DEMO-06.
- **Scope:** "Review Missing Fields" scrolls to and focus-rings the first empty field; keyboard reachable; add missing-field names to the blocked banner (DEMO-09).

### IMP-06 — Copy & label sweep (trivial)
- **Depends on:** EX-DEMO-07 audit table.
- **Scope:** strings only: signup email framing, consistent workspace label, dev-runtime chip visibility rules. One PR, zero logic changes.

### IMP-07 — Wire colloquial fixtures into the audit-gate eval set
- **Depends on:** IMP-02 merged (fixtures green).
- **Scope:** add fixtures to `data/fixtures/` + wire into the F-18/D6 audit eval manifest (`src/evals/audit/manifest.yaml` family) so regression protection is structural, not tribal.

### DEC-01 — Signup posture (owner: Pranay)
- No email verification today: intentional dev shortcut vs product decision? Options: keep frictionless + add post-signup verification nudge; verify-before-first-team-invite; per-domain allowlist. Decide before public exposure. Related: "WORK EMAIL" framing vs self-serve inclusivity (ties to pricing page's self-serve positioning).

## 4. Execution Notes

- All EXPLORE agents: read-only on product code/tests/fixtures; may run read-only scripts and in-process pipeline calls that do NOT persist; may create ONLY their assigned doc(s). No git writes. `rg` for search. Cite `file:line` evidence.
- Data safety: never write to the test DB (`waypoint_os`); `TRIPSTORE_BACKEND=sql` stays in `.env`; no TRUNCATE/DELETE anywhere.
- Register integration (F-19…) happens only after Pranay ratifies; agents must not edit the findings register.
