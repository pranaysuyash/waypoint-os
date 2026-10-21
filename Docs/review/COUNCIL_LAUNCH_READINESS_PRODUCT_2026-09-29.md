# Council — Launch Readiness (Product Dimensions)

**Date:** 2026-09-29
**Scope:** features, UI, UX, flows, operator + traveler surfaces. Explicitly excluded: CI, deployment, hosting, infra (per owner instruction).
**Method:** council-orchestrator skill; canonical persona repo `Downloads/Understanding_Personas_24sep`; evidence tiers per doctrine (runtime > tests > source > docs).
**Baseline evidence at session start:** `Docs/LAUNCH_STATUS.md` (NO-GO public / CONDITIONAL-GO pilot, refreshed 2026-09-14), `Docs/status/FEATURE_LIST_V3_2026-09-10.md` (117 features: 94 LIVE / 14 PARTIAL / 6 GATED / 2 SIMULATED / 1 STUB), FINDINGS_STORE.jsonl (corrected 2026-09-29 post-session with latest-event dedup: **19 open — 0 P0 / 0 P1 / 2 P2 / 17 P3**; FND-0185 confirmed closed 2026-09-14; an initial naive count of 147 open / 1 P0 was wrong — it counted superseded append-only rows).

## Roster
Lead: PER 0338 Product Manager (decision ownership).
S1 PER 0391 Travel & Hospitality Experience Architect — workflow coherence.
S2 PER 1098 Travel Agency / TMC UX Designer — operator UX.
S3 PER 1072 Travel Planning UX Architect — traveler UX.
S4 PER 1082 Travel Product Trust & Safety Designer — honesty/trust (absorbed by Lead: grep-verified sim-surface labeling, fabricated-copy sweep, GMV real-or-0).
S5 PER 0468 Missing Workflow Red Team (skeptic) — falsification.

Roster history: initial parallel dispatch of 5 seats hit the user concurrency limit (4 failed, 1 completed); seats were relaunched sequentially; S4 executed inline by the Lead. No material roster contraction/expansion otherwise.

## Seat verdicts
| Seat | Verdict | Headline |
|---|---|---|
| S1 workflow | CONDITIONAL | Lead→ask→decision→proposal axis genuinely strong; ghost-concierge orphaned (zero serving-path callers), group consensus doesn't bind booking, no live supplier/booking production. |
| S2 operator UX | CONDITIONAL | Dual intake routes (`/workbench` vs `/inquiries/new`) + orphaned `DecisionTab` (decision provenance invisible in primary flow); intake is paste-only (no message/attachment consumption); reviews fire rejections with auto-generated notes, no reason capture; `/quotes` nav item ships SAMPLE DATA; breadcrumb lies (UI-cleanliness A1–A7). |
| S3 traveler UX | CONDITIONAL | Public proposal page strong (honest abstention, demo badge, e-sign); **follow-up questions never reach travelers** (only surface is `[High] Origin City` in DecisionTab; `/followups/generate` returns copy, no outbound delivery); repair banner lacks field names (FND-0062 no-op); per-traveler constraint attribution (FND-0275) invisible to the traveler it protects. |
| S4 trust | CONDITIONAL-OK | Sim-surface labeling broadly intact (~30 panels w/ honesty tests); risky copy verified legitimate (real status labels, not fabrications); GMV real-or-0; residuals: VCC/ghost-concierge containment per LAUNCH_STATUS blocker 3, FND-0232 rubber-stamp of defective supplier confirmations. |
| S5 skeptic | NO (operational pilot) | No money-lifecycle path (refund execution out of scope, in-memory commission/payout ledgers, E08 orphaned); retention enforcer unwired + no DSR/export + no TOS/privacy pages; B6/B7 providers blocked to 2026-10-06 → pilot runs on zero live providers; day-30 drift invisible. Supports a disclosure-heavy design-partner demo only. |

## Cross-examined disagreements
1. **Findings-store counts — resolved in S5's favor, then corrected again.** The Lead's in-session "147 open (1 P0, 54 P1)" figure was a naive count over all append-only rows without latest-event dedup per finding_id. The corrected dedup query shows **19 open (0 P0/P1)** and FND-0185's close event (2026-09-14) is the latest row for that ID. S5's read of the LIVE view was correct; no store/view divergence exists. Lesson: dedupe by latest event before quoting store counts. The "no unowned P0/P1" gate is therefore *verifiable and currently satisfied* — the launch blockers are the product gaps below, not findings mass.
2. **Fabricated-success pages (LR-F01/F02, K09/K10).** S5 cited the 2026-09-02 audit; drift addendum records K09/K10 fabrication fixes landed 2026-09-06. Verify in-tree before treating as open; likely stale citation.
3. **Trust posture vs confirmation rubber-stamp.** Not a conflict: UI-facing surfaces are labeled; the FND-0232 supplier-confirmation acceptance path remains a backend trust hole (open P2, real).

## Council Decision (Lead synthesis)

> **Correction (2026-09-29, owner direction):** the original synthesis proposed re-scoping
> the launch ("design-partner pilot"). The owner has a standing rule: **no MVP/pilot/
> design-partner or other scope-reduction framing for his work unless he explicitly
> introduces it.** The decision below is therefore restated against a full launch: the
> seat evidence is unchanged; the recommendation is a ranked gap list to real launch
> readiness, not a smaller launch.

**Recommendation:** The product core is real and above the bar — intake/extraction (incl. Hinglish/multi-voice), ambiguity asks, decision + suitability with safety invariants, overrides, assumption loop, and the public proposal surface are genuinely strong and honest. **On a full-launch basis, the product is NOT launch-ready yet.** The distance to launch is concrete and bounded; these are the gaps, ranked by real-world impact:

**Launch-blocking gaps (ranked):**
1. **Ask-traveler loop must be a product, not an SOP.** Follow-up questions never reach the traveler (`DecisionTab.tsx:312` is the only render surface; `/followups/generate` returns copy with no outbound delivery), and they render in machine vocabulary (`[High] Origin City`). For a real launch, the traveler must receive, answer, and have answers flow back into the packet — through a real channel (shareable answer page or messaging integration).
2. **Operator flow coherence.** One intake route (kill the `/workbench` vs `/inquiries/new` split), decision provenance/confidence surfaced in the primary flow (mount or delete the orphaned `DecisionTab.tsx`), reason capture on Reject/Request-Changes (`reviews/PageClient.tsx:256-264` auto-generates notes), remove the `/quotes` sample-data nav item, fix lying breadcrumbs (UI-cleanliness A1–A7).
3. **Honest multi-channel intake end-to-end.** Channels ingest (voice/images/DMs are accepted backend-side) but the operator cannot view them — intake is paste-only (`IntakeTab.tsx:208-215`), inbox has no message/attachment surface. A real launch needs message consumption UI or the channels must not be marketed as supported.
4. **Traveler-visible trust surfaces.** Per-traveler constraint attribution (FND-0275: Jain meals, no-heights, occasions) is invisible to the traveler it protects; D05 "why this option" exists backend-side but isn't rendered on the public proposal; FND-0062 repair banner lacks field names. These are the differentiators — surface them.
5. **Money lifecycle beyond the proposal.** Refund execution is out of scope by design, commission/payout ledgers are in-memory (E04/E05), accounting export (E08) is orphaned, sourcing resolver defaults to a stub (E13), no wholesale-cost producer (FND-0268), and FND-0232 rubber-stamps defective supplier confirmations. A real launch needs at least one live provider lane (B6/B7, blocked to 2026-10-06) with wired ledgers — or the product must state plainly, in-product, that it is proposal-stage-only and enforce it everywhere.
6. **Use the open-findings backlog deliberately.** Corrected dedup: 19 open findings (0 P0/P1; 2 P2 = FND-0232 defective-confirmations, FND-0233 refund/compensation dead-end; 17 P3). The P3 set overlaps this council's gaps directly: FND-0236 (AI-decision explanation dossier = gap 2/4 provenance), FND-0126 (webhook dedup dormant = gap 3 inbound path), FND-0164/0165 (eval dims), FND-0161 (checkpoint/DLQ in-memory), FND-0168 (watchdog drift). Close the P2s and fold the relevant P3s into the gap work rather than carrying them as separate lanes.

**Material dissent (preserved, restated without scoping language):** S5's falsification stands as evidence: retention enforcer unwired (FND-0091), no DSR/export routes, no TOS/privacy pages, zero live providers until 2026-10-06. These are gaps 3/5/6 territory and belong on the same ranked path to launch, not in a separate "pilot gate" lane.

**Unknowns / falsifiers:** runtime browser journey on the current tree (no seat ran live UI); whether an outbound ask-loop exists unindexed (rg `messaging.py`/`inbound.py`); whether D05 trust scorecard is in the proposal payload but unrendered; AT-15 P0 state across stores.

**Next action / owner:** register the new council findings (done — see FND-0295+), then pick the highest-leverage launch gap from the ranked list (recommendation: gap 1, the ask-traveler loop — it converts the system's strongest capability into user-visible value; Jev is the natural engine for question rendering, see the task inventory). Falsifier: a live authenticated browser journey (signup → intake → blocked/repair → inbox → proposal) plus a traveler answering a follow-up question through a real channel, with the ranked gaps closed.
