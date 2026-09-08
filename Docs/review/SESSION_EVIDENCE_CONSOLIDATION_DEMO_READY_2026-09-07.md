# Session Evidence — Consolidation + Demo-Readiness + AT-20 (2026-09-07, second session)

**Purpose:** durable record of this conversation (request → method → evidence → artifacts → files changed), so later agents never treat chat as the source of truth. Companions to the same-day PER-0443 artifacts (audit/register/plan/skills/evidence), which this session did **not** redo — it verified, extended, and filed one new finding.

**User request (paraphrase):** use a persona from `~/Desktop/Understanding_Personas_sept6`, audit the repo, document everything, list implicit/explicit findings/tasks, judge 1P/long-term/doctrine alignment, list explore/implement items, catalog skills another agent can be pointed at, use external help (web, codex, subagents, skills), and get the app ready for a meeting this week with Ravi — a travel agent running his own proprietorship.

**Authorization used:** repo docs + contained frontend fix with tests. **Not used:** Git commit/push, hosted deploy, money-path backend change, destructive ops.

**Checklist applied:** `Docs/IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md`

---

## 1. Ground truth loaded (Observed)

| Action | Outcome |
|---|---|
| Skill routing: invoked `audit` skill first per harness mandate | It is a frontend-design audit skill; borrowed its P0–P3/positive-findings taxonomy, applied repo doctrine for the whole-repo audit (repo-local AGENTS.md takes precedence) |
| Persona library listed | `~/Desktop/Understanding_Personas_sept6/01 Expanded Personas/09 Travel - Waypoint OS/` — PER-0443 docx confirmed present |
| `agent-start --skip-index` | Context pack refreshed 16:08 IST (`Docs/context/agent-start/*`) |
| Discovered same-day parallel work | PER-0443 audit (13:44), skills catalog (13:49), register + plan (15:02), session evidence (15:03) — all today, uncommitted; whole-tree-shared doctrine → build on, don't duplicate |
| Read all four PER-0443 artifacts + `Docs/FULL_SKILLS_CATALOG.md` (345 lines) | Basis for verification plan |

## 2. Independent verification (Observed, this session)

**Tests (rerun from clean shell):**
- Backend focused: `test_travel_next_action` `test_booking_fulfillment_lifecycle` `test_irops_healer_simulator` `test_fx_irops_truth_boundary` `test_counterfactual_and_consensus` `test_proposal_compiler_e2e` `test_journey_graph` `test_journey_graph_hydration` `test_capability_routers_batch` → **43 passed in 6.76s** (with a dev-server-on-:8000 warning noted per F-19).
- Frontend honesty vitest (companion, simulated-panels, ProposalCompilerPanel) → **16 passed**; after AT-20 fix the honesty family is **19 passed / 4 files**.
- `npx tsc --noEmit` → clean after AT-20 fix.

**Explore subagent claim audit** (full report in conversation; condensed verdicts in register **Part G**): all PER-0443 Part F claims CONFIRMED with file:line; PARTIAL on visa_radar (`TEST_AGENCY_ID` fallback `spine_api/routers/visa_radar.py:46`, `passport_country="US"` default `:42`); still-OPEN confirmed: AT-04 (no `BookingConfirmation` table; trip-JSON blob at `booking_fulfillment.py:305-312`), PA-40 (`Idempotency-Key` not accepted by `spine_api/routers/fulfillment.py:23-48`; CAS registry wired only on `/spine/run` at `server.py:1982-2068`), F-43 (`next.config.mjs:17-29` rewrites), 2.3b (FlightStatusAgent snapshot-only, `runtime.py:2640-2700`), 2.3c (`src/logistics/irrops_healer.py` orphaned, BA178 at `:153`, only tests import it).

**New P0 found — AT-20:** public proposal page `frontend/src/app/p/[token]/page.tsx` fabricated a complete itinerary on invalid/expired/unreachable tokens (`?? 5030.0`, `?? 'Italian Grand Tour'`, `?? 'Italy'`, `?? 8` days, `?? 'Our Valued Travelers'`, unearned "100% Verified & Protected", empty catch labeled "Fallback demo data if offline"). Worse: it used the Next 15/React 19 `use(params)` pattern against this repo's **Next 14.2 + React 18.3.1** — `use` is not a function in the test/runtime resolution, i.e. the route **crashed before the fabrication even rendered**. `rg 'use\(params\)' frontend/src` → zero other callers; `booking-collection/[agencyId]/[token]` uses `Promise<params>` typing but awaits it (safe, cosmetic mis-typing).

**AT-20 fix (this session, uncommitted):**
- Honest abstention screen (`Proposal unavailable` + status-specific reason + "ask your travel advisor for a fresh link").
- All fabricated fallback literals removed; chip → "E-signature secured" (matches the real durable accept flow); `params: { token: string }` Next-14 signature restored.
- New test `frontend/src/app/p/[token]/__tests__/public-proposal.honesty.test.tsx` (410-abstain, network-abstain, happy-path renders real proposal; asserts absence of every fabricated string).
- Evidence: honesty family 19/19 passed; tsc clean.

**Demo-path verdicts (source-level, Observed):** `/workbench` Proposal Compiler LIVE-and-badged (`deterministic_preview`, `provider_connected=false`, share link gated on real token) — F-42 residual closed at UI level; decision page abstains with no fabricated scores; landing v5 qualitative proof rail (no hero metrics); Persona Council simulators badged at panel level only (Journey Graph visualizer still shows BA178/Mandarin Oriental inside the tab — demo hygiene, not a new register row); a11y code-level notes (sub-44px SOS/day-pill targets, `text-[10px]` micro-type, two unlabeled intake fields in ProposalCompilerPanel) logged for a polish wave.

## 3. External input (Observed)

| Channel | Result |
|---|---|
| Codex CLI 0.150.1 (`codex exec --sandbox read-only`, model gpt-5.6-luna, session 01a07b81) | Blocked by account usage limit — "try again at 6:09 PM" 2026-09-07. **Retry command (verbatim):** `codex exec --sandbox read-only "Read-only external review of an uncommitted change-set in this repo…"` full prompt in conversation §2 and reproducible from register Part G.4. File findings as register Part H on retry. |
| Web research (2 searches) | Sources: [Lark travel CRM guide](https://www.larksuite.com/en_us/blog/travel-agency-crm), [DMC Quote — best travel CRMs for small agencies](https://dmcquote.com/blog/post/travel-crm-systems-best-options-small-agencies), [PHPTravels — software used by travel agents](https://phptravels.com/software-used-by-travel-agents), [BCD Travel payment pain-points survey](https://news.bcdtravel.com/bcd-travel-survey-reveals-biggest-payment-and-expense-pain-points-in-business-travel/), [Rework travel automation guide](https://resources.rework.com/libraries/travel-tour-growth/travel-automation-tools), [Peakflo travel invoicing](https://peakflo.co/id/blog/travel-agency-billing-invoice-automation), [Flywire travel payments](https://www.flywire.com/industries/travel), [Travelbooster mid-office workflows](https://www.travelbooster.com/blog_post/mid-office-workflows-travel-agents/), [Gravity Flow booking workflows](https://gravityflow.io/articles/how-automated-workflow-tools-can-help-the-travel-industry-with-bookings/). Synthesis: small Indian proprietor agencies run consolidators (TBO/Mystifly) over direct GDS, WhatsApp-first CRMs/quotation tools (Zoho/TravoByte/CRMtravel/TraviYo), and their top pains are payment collection/chasing, manual quote/invoice generation, and slow inquiry turnaround. Search-level sources (summaries), not page-fetched — treat as domain orientation, ratified by the stakeholder conversation (demo plan §5). |

## 4. Request → artifact map (this session)

| User ask | Artifact |
|---|---|
| Persona audit, documented, evidence-backed | Verified rather than re-run: PER-0443 audit + this file §2 + register Part G |
| Implicit/explicit findings/tasks list | Register Parts A–B (AT-01…19) + **Part G (AT-20)**; chat summary in final reply |
| 1P/LT/doctrine alignment | Register alignment columns + audit §4/§9 (existing) + Part G verdicts (this session) |
| What else can be done to make it the best | Register Part E (systems) + `Docs/review/RAVI_STAKEHOLDER_DEMO_PLAN_2026-09-07.md` §4–§5 (market/stakeholder) |
| Implementation plan | PER-0443 plan (Waves 0–4) + demo plan §3 pre-flight; AT-20 executed |
| Skills catalog other agents can follow | `Docs/FULL_SKILLS_CATALOG.md` (verified this session; pointer sentence unchanged) |
| Use external help (web/codex/subagents/skills) | This file §3 + Explore subagent verification |
| App ready for Ravi this week | `RAVI_STAKEHOLDER_DEMO_PLAN_2026-09-07.md` (script, pre-flight, risks, discovery questions) |

## 5. Files written/modified this session

| Path | Change |
|---|---|
| `frontend/src/app/p/[token]/page.tsx` | AT-20 fix (abstention screen, fallback removal, chip reword, Next-14 params) |
| `frontend/src/app/p/[token]/__tests__/public-proposal.honesty.test.tsx` | New honesty test (3 cases) |
| `Docs/review/RAVI_STAKEHOLDER_DEMO_PLAN_2026-09-07.md` | New demo plan |
| `Docs/review/SESSION_EVIDENCE_CONSOLIDATION_DEMO_READY_2026-09-07.md` | This file |
| `Docs/review/FINDINGS_TASKS_IMPLICIT_EXPLICIT_REGISTER_PER0443_2026-09-07.md` | Additive **Part G** append (verification + AT-20) |
| `Docs/INDEX.md` | Two ⭐ pointers at top |
| `Docs/context/agent-start/*` | Refreshed via `agent-start` (tooling) |

## 6. Explicitly NOT done (do not assume)

- No Git commit/push (owner gate; the uncommitted tree is now the **single biggest demo risk** — commit before the meeting).
- Codex external review pending usage-limit reset (18:09 IST); findings slot goes to register Part H.
- AT-04, PA-40-on-fulfill, F-43, 2.3b, 2.3c, visa_radar `TEST_AGENCY_ID`/`passport_country` defaults remain open (register Part G.1).
- Browser-executed verification of the demo surfaces (L7) remains open; all demo-path verdicts here are source-level + test-level.

---

## 7. Second implementation unit (owner redirect, same day ~17:00–17:20 IST)

**Owner directive:** do not say "done for Ravi" — the meeting is unconfirmed and the minimum bar (committed tree, L7 browser proof) is not met. Keep working the findings/improvements/features per the audit docs, long-term + first-principles + doctrine aligned. Demo plan re-headered **STATUS: DRAFT** accordingly.

**Executed (all local, uncommitted; full detail in register §G.5):**

| Finding | Change | Verification |
|---|---|---|
| F-43 (P1) | next.config wildcard rewrites deleted; 7 explicit route-map entries added (`v1/logistics/assess-route`, `v1/group/token/{token}` ± `/pay-share`, `public/journey-graph/{trip_id}`, `public/proposals/{token}` ± `/calculate` `/accept`); 2 new tests incl. assert-fulfill-stays-denied | vitest route-map+honesty 27 passed; tsc clean |
| PA-40 (P1) | `Idempotency-Key` on fulfill router wired to the durable CAS registry: COMPLETED→replay, PENDING→409, FAILED→retryable, terminal-failure marking; new replay test | lifecycle 7/7; ruff clean |
| AT-11 residual (P1) | visa_radar: no TEST_AGENCY_ID fallback (400), no `"US"` nationality default (trip-derived or abstain with missing-inputs summary) | capability batch 27 passed |
| 2.3c (P1) | Disposition corrected: NOT deletable — carries the only EU261/UK261/US-DOT compensation calculator; migrate into passenger-rights (AT-17) first, then retire | rg call-site + uniqueness audit |

**Deliberately deferred:** AT-04 SQL confirmation wiring (needs the AsyncSession/RLS + file-store parity decision), 2.3b FlightStatusAgent→disruption escalation, Wave 1.4 TierMetadata batch, Wave 3 observability. Codex retry scheduled via one-shot automation at ~18:15 IST to file register **Part H**.

---

## 8. Codex external review executed + triaged (automated retry, ~18:12–18:35 IST)

The scheduled one-shot retry **succeeded** (gpt-5.6-luna, read-only sandbox, ~233k tokens). Verbatim findings + this session's triage are filed as register **Part H**. Triage outcome: **0 refuted / 9 confirmed** — the review caught real defects in today's own OS-layer unit:

1. **P0:** fulfillment is not exactly-once across the side-effect boundary (guard before 60s-never-renewed lease; VCC/PNR minted before durable confirmation; crash-in-between mints twice). Structural; live-provider impact inferred (simulated adapters today).
2. **P1 (best catch):** fulfill builds a **fresh single-flight-node graph** and overwrites the compiler's persisted quoted DAG — verified directly in `booking_fulfillment.py` step 5.
3. **P1:** companion renders simulator PNR/e-ticket/voucher as truth (only a cosmetic `Reality:` string; no `provider_connected`/`commitment_status` gate) — verified by rg.
4. **P1:** `/p/[token]` `?? 0` renders "$0" on malformed payloads (residue of the AT-20 fix) + unbadged gated demo path.
5. **P1:** NBTA read/compare/write race (no CAS on the read version).
6. **P2:** idempotency replay doesn't compare the stored body hash (this session's PA-40 comment overclaimed — hash is stored, not enforced); `mark_completed` bool ignored.
7. **P2:** `JourneyNode.from_dict` throws on missing timestamps and silently coerces unknown node types to FLIGHT — defect in today's schema work.
8. **P2:** "receipt has been emailed" claim with no email dispatch in the accept path.
9. Heuristic-label check: clean in scope.

**Nothing was coded in response** (automation contract: document-only). Next implementation pass should fold these into: the fulfillment-durability unit (P0 + partial-confirmation + idempotency gaps + AT-04), a graph-merge fix on fulfill (P1), companion reality-gating (P1), proposal-page contract validation + copy fix (P1/P2), NBTA CAS (P1), and schema tolerant-parsing (P2).

---

## 9. Part-H follow-ups implemented (owner directive, ~19:20–20:10 IST)

All nine confirmed Part-H findings addressed in one pass. Full fix-by-fix receipts with evidence: register **Part I**. Headlines:

- **P0 closed:** provider-side idempotency (deterministic sandbox instruments from `fulfillment_provider_key`), durable side-effect-start marker before any provider call, in-lease confirmation re-check, mid-flight lease renewal with fail-loud loss detection. Crash between provider call and persistence now re-enters safely and returns the SAME instruments.
- **P1s closed:** journey graph merged (quoted siblings survive fulfill); companion preview-gates every PNR/e-ticket/voucher on `provider_connected` with an amber "Preview itinerary" banner; proposal page validates payloads (incomplete → abstention, never `$0`), badges the gated demo fixture, and tells the truth about the acceptance record; NBTA uses the canonical `update_trip_if_version` CAS with a verify-and-heal loop (race test proves a stale weather clobber gets healed).
- **P2s closed:** idempotency replay enforces request-hash identity (409 on mismatch); `JourneyNode.from_dict` tolerates undated nodes and preserves unknown node types.
- **AT-04 closed (local):** `try_record_fulfillment_confirmation` writes the SQL BookingConfirmation machine (draft→recorded) from the fulfillment path, with honest degradation (`recorded: False` + reason, surfaced on the result and audit) when no database is configured.

**Verification:** backend pytest **79 passed** + ruff clean; frontend vitest **43 passed** + `tsc --noEmit` clean. One correction absorbed mid-pass: a parallel agent's route-inventory gate removed my `assess-route` mapping (no backend endpoint exists — their call was right; test now asserts the denial; RouteMapStudio's dead fetch recorded as queued). Codex follow-up review dispatched; outcome to be appended as register **Part J**.

---

## 10. Codex re-review + Part-J fix round (same session, ~19:50–20:15 IST)

The codex follow-up review (~423k tokens) judged the Part-I pass honestly: several fixes were partial, one new defect was **reproduced** (naive/aware datetime crash from the tolerant parsing). All 10 findings triaged; the full fix-by-fix disposition table with final invariant status is register **Part J**. Fixed in-session: provider key binds proposal token + Stripe sandbox binds spend/currency params; companion fails **closed** on missing provenance (legacy blobs render as preview); proposal `/calculate` + `/accept` validated; "lock reservations" copy made truthful; strict idempotency hash compare; blob records `sql_confirmation` and **replay repairs** a missing SQL confirmation; fulfillment persist uses `update_trip_if_version` CAS with re-merge; lease renews before the provider window; NBTA fallback fails closed (strips action fields under persistent contention); naive timestamps normalized to UTC.

Final verification: **81 backend + 44 frontend tests passing; ruff + tsc clean.** Honestly still open (register Part J): BookingConfirmation uniqueness migration (A-20 custody), journey-graph top-level provider attestation, adapter heartbeat during long provider awaits, livemode Stripe Idempotency-Key header, RouteMapStudio dead fetch, and all hosted/browser (L7) proof.

---

## 11. Part-K: the still-open list executed (owner directive, ~20:30–21:00 IST)

Owner: "do the still open one(s)." Dispositions in register **Part K**:

1. **Uniqueness constraint** — partial unique index `uq_bc_trip_type_active` at model level + alembic revision `bc_active_type_uniqueness` (dedupe-void-then-index, parameterized; single alembic head confirmed before chaining). 3 SQLite tests.
2. **Top-level provider attestation** — journey-graph GET now attests `provider_connected`/`reality_tier` fail-closed; companion trusts the attestation.
3. **Lease heartbeat** — `lease_heartbeat` async CM (renew-during-await, fail-loud on lost fence) wraps the fulfillment provider window; 2 tests.
4. **Livemode Stripe** — fails closed under `sk_live_*` (no fake live instruments, §13); `missing_for_upgrade` names the native Idempotency-Key requirement; test.
5. **RouteMapStudio** — fabricated-savings fallback (hardcoded numbers, even in ok-paths) removed; honest "endpoint does not exist yet" banner.
6. **L7-lite browser smoke (executed)** — live servers: `/p/invalid-token` → honest "Proposal unavailable" (AT-20 browser-proven); `/companion` no-token → signed-token-required abstention; landing clean with zero console errors. Remaining L7: real-token companion preview banner, authenticated workbench walk, hosted.
7. **Git commit** — NOT executed; needs the owner's explicit go (tree includes parallel agents' work; commit-gate protocol applies). Everything is gate-ready.

**Final receipts:** backend pytest **88 passed** + repo-wide ruff clean; frontend vitest **44 passed** + `tsc --noEmit` clean.

---

## 12. AT-21 copy pass (owner-caught, ~21:00 IST)

Owner spotted engineer-voiced abstention copy on the traveler portal (`"?token="`, "signed proposal share token", raw `deterministic_preview` slugs, "Journey graph"). All traveler surfaces I shipped this session rewritten in traveler voice — honesty preserved, jargon gone; browser re-verified on the live companion. Tests updated to assert the new copy AND the absence of internal terms. Full disposition + remaining-sweep note: register **Part K addendum (AT-21)**. 44/44 FE tests + tsc clean after the pass.
