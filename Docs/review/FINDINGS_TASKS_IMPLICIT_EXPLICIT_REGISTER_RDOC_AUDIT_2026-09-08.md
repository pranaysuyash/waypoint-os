# Findings/Tasks Register — Random Doc Audit: Itinerary Checker GTM Wedge (2026-09-08)

> **STATUS UPDATE (2026-09-08, execution wave).** Buckets A (EXPLORE) and B (IMPLEMENT) executed this session. Corrections: **FT-03 is moot** — the `/n`-404 claim was a subagent false positive; live marketing/pricing links are correct. FT-01/02/04/05/06/07/08/09/10/11 done (tests: 90 backend + 22 frontend green; tsc clean). EX-01..EX-10 documented (`Docs/exploration/RDA_EX*.md`, `Docs/review/WEDGE_FATE_DECISION_PACK_RDA_2026-09-08.md`). Unknowns EX-09 resolved. Bucket C still gated: **D-01/D-02/D-03/D-04/D-05 remain open — owner decisions required.** Per-item status noted inline below.

Source: `Docs/review/RANDOM_DOC_AUDIT_ITINERARY_CHECKER_GTM_WEDGE_2026-09-08.md` (chosen doc `Docs/context/ITINERARY_CHECKER_GTM_WEDGE_2026-04-14.md` + companion `DECISION_MEMO_ITINERARY_CHECKER_2026-04-14.md`).
Origin key: **[E]** = explicit in the docs, **[I]** = implicit (audit-discovered). Status key: verified this session unless noted.

Counts: 10 EXPLORE · 11 IMPLEMENT-ready · 6 decision-gated IMPLEMENT · 5 DECIDE · 3 RECORD · 5 NOT-WORTH-DOING.

**Gating note:** D-01 (wedge fate) gates the entire decision-gated IMPLEMENT cluster — decide it before committing code to those items. The IMPLEMENT-ready bucket is correct regardless of D-01.

> **AUD-07 disposition refined (2026-09-09, Pranay challenge).** The `/n`-404 claim was factually false (links work), but my "correctly link" framing was wrong: the pricing page *is* the wedge narrative — tier 1 is "Traveler checker / Free / pre-qualifying a trip before it reaches the agency", the hero secondary CTA is "Try the public checker", and the shared `PublicHeader` default nav includes "Itinerary Checker" on every marketing page (`frontend/src/components/marketing/pricing-page.tsx:6-14,86-108`, `marketing.tsx:15-22`). This is internally inconsistent with the deliberate 2026-06-28 homepage delink and with the GTM assessment's falsification. The links are therefore **unadjudicated wedge-era surface, D-01-gated** — not "moot". Notably the pricing copy already uses inverted-wedge language (agency-serving pre-qualification): the copy encodes Option B while the product is still consumer-shaped. FT-03 (broken-link fix) stays moot; FT-G7 "marketing-surface checker-link disposition per D-01" joins Bucket C.

## Bucket A — EXPLORE (research and document; no code yet)

| ID | Origin | Task | Priority | Evidence / note |
|---|---|---|---|---|
| EX-01 | [E] | **Wedge-fate decision pack**: refresh competitor scan (Spotinga/Fortrip per GTM assessment), design "agency-branded checker" inversion option, cost/effort for each path → **pack done** (`Docs/review/WEDGE_FATE_DECISION_PACK_RDA_2026-09-08.md`); live competitor refresh kept open for later — quota-blocked until 2026-10-06, tracked as roadmap **B9** with retry queries | P1 | `GTM_ANGLE_ASSESSMENT_2026-09-01.md:14,227,242-244`; feeds D-01 |
| EX-02 | [E][I] | **Retention/TTL policy research** for public-checker trips + event JSONL (storage-limitation norms, GDPR erasure interplay with AUD-04) → written policy | P2 | `public_checker_service.py:281-303` (unconditional save); zero TTL in repo |
| EX-03 | [I] | **KPI trust model research**: server-derived vs client-event KPIs; bot-poisoning mitigations (origin binding, server-side funnel counters, captcha) | P1 | `product_b_events.py:366-385,462-510` (KPIs from unverified client events) |
| EX-04 | [I] | **Capability-token design** for anonymous result access + sharing (precedent: `/api/v1/proposals/token/`); supersedes AUD-04 + AUD-08 together | P2 | `middleware.py:32-39` vs `server.py:1483-1485`; live 401 probes |
| EX-05 | [E] | **Legal disclaimer requirements**: "guidance, not legal travel guarantee" policy-reviewed copy for upload + result views | P2 | Doc :177-178; zero disclaimer hits in `PageClient.tsx` today |
| EX-06 | [E][I] | **Scoring model documentation + calibration plan**: formalize the shipped 0–100 baseline-minus-penalty model; verify `validation.overall_score` has no producer (Unknown); plan calibration trigger | P3 | `live_checker_service.py:8-13,106-156`; doc :111 promised calibration after 100–300 itineraries (never possible — no real traffic) |
| EX-07 | [E] | **Rule-coverage semantic gap register**: doc's 15 rules vs actual taxonomy; which gaps matter for a precision-first public checker (CONN/TRF/CHK/HOT/MEAL/FEE/BUF/INS missing; internal equivalents exist unwired: `/api/v1/logistics/connection-risk`, `timed-entry-audit`) | P2 | `decision.py:1224-1409`; `live_checks.py:406-514`; `logistics.py:197-227` |
| EX-08 | [E] | **Data-moat linkage feasibility**: checker → Template Genome / Pricing Memory / playbooks; intersects PA-18 (memory write-only, forgetting never executes) | P3 | Doc :190-196; never wired |
| EX-09 | [I] | **Runtime trace of a live public run** (single probe run, then document): does `overall_score` ever populate; can any visa check fire at pinned `stage:'discovery'`; are consented `content_base64` uploads actually persisted via artifact store | P3 | `decision.py:1283-1298` + `PageClient.tsx:2871`; Unknowns from code verifier |
| EX-10 | [I] | **Event-store ops posture**: growth/rotation runbook for append-only JSONL + O(N) dedupe scan amplification | P3 | `product_b_events.py:160-174,303-311` |

## Bucket B — IMPLEMENT (ready now; correct regardless of D-01)

| ID | Origin | Task | Priority | Evidence / note |
|---|---|---|---|---|
| FT-01 | [I] | **Remove or clearly relabel fabricated testimonials** ("Sarah K./Marcus T./Priya N.", "Real feedback from real itineraries") | P1 | `PageClient.tsx:1026-1046,1412-1454,1549`; LR-D08 open |
| FT-02 | [E][I] | **Remove fake email-capture success UI** ("Report sent! …full PDF" with no send) | P1 | `PageClient.tsx:2277-2278,2299`; `contract.py:98-117` |
| FT-03 | [I] | **Fix `/n` 404 links** in live pricing/marketing nav → `/itinerary-checker` or remove | P2 | `marketing.tsx`, `pricing-page.tsx`; `frontend/src/app/n` does not exist |
| FT-04 | [I] | **Test coverage**: frontend tests for testimonial/email-gate removal + the result-view fetch path (401 behavior for anonymous); extend beyond lone `blocker-copy.test.tsx` | P2 | `__tests__/` has 1 file, 2 tests; fetch path zero-covered |
| FT-05 | [I] | **Kill switch**: env-gated disable of public checker (backend route + frontend page) with maintenance response + tests | P2 | No flag found (rg zero); mounts `server.py:1434,1955` |
| FT-06 | [I] | **Event-store rotation/size cap mechanics** (implementation side of EX-10: rotate/segment JSONL, bound dedupe scan) | P2 | `product_b_events.py:160-174,303-311` |
| FT-07 | [I] | **Throttle authed `GET`/`export`** on checker trips (no decorators today) | P3 | `public_checker.py:113-124`; `rate_limiter.py:28-39` |
| FT-08 | [I] | **Rate-key behind proxy**: handle `X-Forwarded-For`/proxy topology so limiter buckets aren't shared/bypassed | P3 | `rate_limiter.py:23-25` (peer address) |
| FT-09 | [I] | **Agency misconfiguration guard**: startup warns/fails if `PUBLIC_CHECKER_AGENCY_ID` has memberships/operating role; ship dedicated checker-agency id in `.env.example` (not the test agency) | P3 | `server.py:1102-1161`; `.env.example:39` = test agency UUID |
| FT-10 | [I] | **Dead-share cleanup**: remove `proxy.ts:34-35` allowlist entries (no pages exist) + unreachable `whatsapp`/`email` channel union members (or fold into FT-EX-04 implementation later) | P3 | `proxy.ts:34-35`; `PageClient.tsx:2598` |
| FT-11 | [I] | **Supersession headers** on both 2026-04-14 docs → point to GTM assessment + registry [C] (annotate; do not delete history) | P3 | Doc pair; contradicted claims inside |

## Bucket C — IMPLEMENT (decision-gated; do not start before D-01/D-02/D-03)

| ID | Origin | Task | Gate | Priority |
|---|---|---|---|---|
| FT-G1 | [E] | **Real email capture** (backend field + consent + purpose + actual send or lead record) — replaces FT-02's removal if email capture is ratified | D-02 | P2 |
| FT-G2 | [I] | **Anonymous capability tokens** for result GET/export/DELETE (fixes 401 gap + erasure right) | D-01 (moot if consumer wedge killed) | P2 |
| FT-G3 | [I] | **Tokenized share page** (real `/shared/` route consuming capability tokens) | D-01 | P3 |
| FT-G4 | [E] | **Wire checker outputs to memory ingestion** (Template Genome/Pricing Memory format) | D-01 + PA-18 resolution | P3 |
| FT-G5 | [E] | **Rule expansion for public checker** per EX-07 verdict (incl. wiring internal logistics endpoints or stage-awareness for visa checks) | D-04 | P2 |
| FT-G6 | [E] | **Paid-fix tier / lead routing / payment integration** | D-05 (recommend: hold under NO-GO) | P3 |
| FT-G7 | [I] | **Marketing-surface checker-link disposition** — pricing page tier 1 + "Try the public checker" CTA + `PublicHeader` default nav item are wedge-era surface contradicting the 2026-06-28 homepage delink; keep (A) / rewrite as inverted-wedge copy (B) / remove + redirect (C). Kept open for later per Pranay (2026-09-09) | D-01 (C7 on the open-work roadmap) | P2 |

## Bucket D — DECIDE

| ID | Decision | Note |
|---|---|---|
| D-01 | **Wedge fate**: kill / invert to agency-branded checker / keep as traveler surface | The master gate. Evidence: GTM assessment falsified consumer wedge; NO-GO launch; registry lists checker as "[C] code-backed" only |
| D-02 | **Email capture**: remove (FT-02) vs implement for real (FT-G1) | Current state is deceptive; either path fixes it |
| D-03 | **Retention policy** for public-checker trips + events (informed by EX-02) | Feeds FT-06 scope |
| D-04 | **Public-checker rule expansion** (which of the missing semantic checks matter) | Informed by EX-07 |
| D-05 | **Monetization direction** (paid fix vs subscriptions $49/$199 per later docs) | Blocked behind launch decision anyway |

## Bucket E — RECORD

| ID | Record |
|---|---|
| R-01 | Supersession headers on the two 2026-04-14 docs (= FT-11, docs-only) |
| R-02 | Gate-review closure note: record that the 30-day gates were never run and the retrospective falsification lives in `GTM_ANGLE_ASSESSMENT_2026-09-01.md`; link from the memo |
| R-03 | Decision-memo closure entry once D-01 is made (append, don't rewrite history) |

## Bucket F — NOT WORTH DOING (do not retrofit the doc's specifics)

| ID | Item | Why |
|---|---|---|
| N-01 | Exact `/api/v1/analyze` + `analysis_id` contract | Superseded by shipped `/api/public-checker/run`; retrofitting adds a duplicate surface (violates no-duplicate-routes rule) |
| N-02 | Exact 0–10 scoring formula | Superseded by shipped 0–100 model; recalibration (EX-06) is the real question |
| N-03 | Exact rule-ID names (`CONN_001`…) | Naming retrofit adds no value; semantic coverage (EX-07) is the real question |
| N-04 | ₹999 paid-fix pricing specifically | Superseded by later pricing direction; under NO-GO anyway (fold into D-05) |
| N-05 | 2-week MVP plan | Historical; moot |

## Suggested sequencing

1. **Now**: FT-01 + FT-02 + FT-03 + FT-11 (honesty/dead-nav unit) · R-02 · FT-04.
2. **Next**: EX-01 decision pack → D-01 (everything in Bucket C hangs on this).
3. **Then**: per D-01 outcome — FT-05/06 + EX-03→D-03→FT-06 hardening track; EX-04→FT-G2/G3 consumer track; EX-07→D-04→FT-G5 product track.
