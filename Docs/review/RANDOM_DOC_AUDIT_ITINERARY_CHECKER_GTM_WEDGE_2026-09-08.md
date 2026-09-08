# Random Document Audit — Itinerary Checker GTM Wedge (2026-09-08)

> **EXECUTION ADDENDUM (2026-09-08, same day).** The register produced from this audit was executed the same session. Corrections to this report: **AUD-07 was a false positive** — the skeptic agent's `/n`-404 claim failed direct verification; live `marketing.tsx`/`pricing-page.tsx` correctly link `/itinerary-checker`, and the checker is therefore linked from live surfaces (pricing + marketing nav), refining the "orphaned" framing further. FT-03 is moot. Two Unknowns were resolved by a live run: `validation.overall_score` IS populated (61 on a probe run; the baseline map is fallback-only), and consented-artifact persistence was confirmed wired (`PublicCheckerArtifactStore` inside `save_processed_trip`). See `Docs/review/FINDINGS_TASKS_IMPLICIT_EXPLICIT_REGISTER_RDOC_AUDIT_2026-09-08.md` for per-item status and `Docs/exploration/RDA_EX*.md` + `Docs/review/WEDGE_FATE_DECISION_PACK_RDA_2026-09-08.md` for the explore-wave outputs.

Audit method: one document selected uniformly at random (Python `random.SystemRandom`, urandom-backed) from 2,225 repo markdown documents (root `*.md` + `Docs/**` + `Archive/**`, excluding caches/skills/mirrors). Population hash `14d89b285ba8`; selected index 598.

- Chosen document: `Docs/context/ITINERARY_CHECKER_GTM_WEDGE_2026-04-14.md`
- Companion doc read: `Docs/context/DECISION_MEMO_ITINERARY_CHECKER_2026-04-14.md` (locked v1 scope, gates, P0/P1 actions)
- Audit mode: evidence-only. No durable implementation performed.

## Verdict

The wedge was **implemented divergently, then quietly demoted — and never formally closed.** A public checker exists (`POST /api/public-checker/run`, frontend `/itinerary-checker`, product-B event funnel + KPI backend via ADR-007), but almost none of the doc's specific contracts survived: the 15 rule IDs were never implemented, the scoring model is contradicted (0–100 subtractive, not 0–10 weighted), the API contract differs (`extra:"forbid"` rejects the doc's `file`/`email` inputs), the paid-fix ₹999 tier / lead routing / fix-request were never built, and the 30-day go/no-go gates were never run. The wedge thesis was falsified and a replacement strategy recommended in `Docs/review/GTM_ANGLE_ASSESSMENT_2026-09-01.md`, the homepage delink was a deliberate 2026-06-28 decision, and public launch is NO-GO (`Docs/LAUNCH_STATUS.md`, 2026-09-04). No record formally closes the 2026-04-14 decision memo.

## 1. Document Inventory

Population: 2,225 markdown docs (root, `Docs/**`, `Archive/**`). Types present: ADRs, architecture maps, findings registers, launch-readiness audits, exploration docs, strategy/context memos, status handoffs, archived design references. Selection was real-random (disclosed method above), not convenience-picked.

## 2. Random Selection

- Chosen document: `Docs/context/ITINERARY_CHECKER_GTM_WEDGE_2026-04-14.md`
- Selection method: `random.SystemRandom().choice()` over the deduped inventory (urandom-backed)
- Why worth auditing: a 5-month-old GTM strategy doc whose subject (public checker) demonstrably exists in the codebase under different names — high stale-claim density, active code surface, unresolved decision record.

## 3. Chosen Document Deep Analysis

Extracted items (abridged; full classes): Strategic thesis + flywheel (steps 1–5), free tier spec, paid-fix ₹999 tier, quote/lead-routing flow, NB01–NB03 Lite mapping, 15-rule seed (6 critical, 8 warning, 3 info), scoring model `clamp(10 − critical·2.0 − warning·1.0 − info·0.3, 0, 10)`, API contract `POST /api/v1/analyze` + `POST /api/v1/fix-request`, 2-week MVP plan, metric set (funnel/monetization/moat/quality), risk controls (false positives, legal disclaimer, OCR fallback, privacy/retention/consent), data-moat linkage (Template Genome, Pricing Memory, playbooks), decision to proceed with strict scope. Decision memo adds: 10-check lock, 30-day go/no-go gates, P0 instrumentation, P1 paid-fix handoff + memory-ingestion mapping.

## 4. Extracted Task Candidates

TC-01 build free checker (score/risks/summary/CTA) · TC-02 paid-fix tier ₹999+SLA · TC-03 quote request + partner lead routing · TC-04 implement 15 (later 10) named rules · TC-05 scoring model as specified · TC-06 `/api/v1/analyze` contract · TC-07 `/api/v1/fix-request` contract · TC-08 PDF/image/text ingestion · TC-09 landing/upload UX + result card · TC-10 email capture · TC-11 funnel + per-rule instrumentation · TC-12 payment integration · TC-13 lead-routing workflow · TC-14 legal disclaimer copy · TC-15 privacy: minimization, retention, consent · TC-16 FP controls (confidence thresholds) · TC-17 OCR fallback / manual-review branch · TC-18 checker data → Template Genome / Pricing Memory / playbooks · TC-19 run 30-day go/no-go gates · TC-20 metrics dashboards.

## 5. Static Codebase Reality Check

| TC | Status | Evidence |
|---|---|---|
| TC-01 | Renamed-equivalent, done differently | `spine_api/routers/public_checker.py`; `spine_api/services/public_checker_service.py`; result card `frontend/src/app/(traveler)/itinerary-checker/PageClient.tsx` |
| TC-02/03/07/12/13 | Missing (never built) | No payment/fix-request/lead code near checker; only `stripe_issuing_adapter.py`/`subagent_payouts.py` (unrelated) |
| TC-04 | Missing IDs; partial semantics | Rule IDs occur only in docs + archived HTML. Actual taxonomy: risk flags `src/intake/decision.py:1224-1409`; live weather/safety checks `src/public_checker/live_checks.py:406-514`; validation codes `src/intake/validation.py:72-78` |
| TC-05 | Contradicted | `spine_api/services/live_checker_service.py:8-13,106-156`: 0–100 baseline map + subtractive live-check penalty (cap 35); frontend renders `/100` |
| TC-06 | Contradicted | Actual: `POST /api/public-checker/run` (`spine_api/server.py:1955-1971`); `SpineRunRequest` `extra:"forbid"`, no `file`/`email` (`spine_api/contract.py:98-117`); no `analysis_id`/`issues[]` |
| TC-08 | Done (client-side, text-over-wire) | `PageClient.tsx:527-563` pdfjs + Tesseract; caps `public_checker_service.py:40-118` |
| TC-09 | Done | `/itinerary-checker` page + result card |
| TC-10 | Fake | `PageClient.tsx:2299` — `onClick={() => email.includes('@') && setSent(true)}`; no POST; backend forbids email |
| TC-11 | Superseded (different KPIs) | `spine_api/product_b_events.py`, `spine_api/routers/product_b_analytics.py`, `frontend/src/components/insights/ProductBKpiPanel.tsx` (ADR-007, 2026-09-04) |
| TC-14 | Missing | No disclaimer on result/upload views (rg: zero hits) |
| TC-15 | Partial | Consent toggle exists (`PageClient.tsx:1735-1761`); raw-text stripped without consent (`live_checker_service.py:76-83`); but full trip rows persist unconditionally (`public_checker_service.py:281-303`); no TTL/retention anywhere |
| TC-16 | Partial | STOP_NEEDS_REVIEW escalation `src/intake/orchestration.py:300-333`; per-issue confidence absent from public API (`contract.py:174-175` plain strings) |
| TC-17 | Renamed-equivalent | `extraction_quality` hard blocker → STOP_NEEDS_REVIEW (`src/intake/gates.py:101-117,208-213`) |
| TC-18 | Not wired | No checker→memory ingestion; PA-18 (memory write-only) corroborates |
| TC-19 | Never performed | No gate-review record anywhere; superseded framework (2026-05-07 kill test) also never run |
| TC-20 | Superseded | Product-B KPI panel computes forwardability/revision/pull-through, not the memo's five gates |

## 6. Dynamic Verification and Test Baseline

- Targeted backend: `pytest tests/test_live_checker_service.py tests/test_public_checker_agency_config.py tests/test_public_checker_contract_authority.py tests/test_public_checker_live_checks.py tests/test_public_checker_path_safety.py tests/test_public_checker_payload_limits.py tests/test_product_b_events.py tests/test_product_b_analytics_router_behavior.py` → **68 passed** (Tier 2, S1).
- Targeted frontend: `blocker-copy.test.tsx` → **2 passed**.
- Full suite NOT run this session: both dev servers were live (uvicorn :8000 up ~14h; next-server :3005 up ~10h), which this repo's own doctrine (F-19, FINDINGS_TASKS_CONSOLIDATED_2026-08-30) flags as a phantom-failure source, and the ~3,800-test suite is expensive. Last recorded full-suite evidence (prior session, 2026-09-05): 3,818 passed / 0 failed — prior evidence, not today's. Full-suite command: `scripts/run_backend_tests.sh` with dev servers stopped.
- Live probes against running :8000 (read-only / no-op): unauthenticated `GET /api/public-checker/trip_doesnotexist123` → **401**; `GET .../export` → **401**; `DELETE ...` → **401** (no record); `POST /api/public-checker/events` `{}` → **422** (validation live; endpoint openly reachable). Confirms middleware gap: `AuthMiddleware.PUBLIC_PREFIXES` (`spine_api/core/middleware.py:32-39`) allowlists only `run` + `events`, while the router is documented "public-by-design" (`server.py:1483-1485`).

## 7. Critical Implementation and Test Traps Checked

- Env/config: `PUBLIC_CHECKER_AGENCY_ID` is read at call time via `_get_public_checker_agency_id()` (`server.py:172-178`), validated at startup with fail-fast (`server.py:1102-1161`). No module-level caching issue found. `.env.example:39` ships the concrete test-agency UUID (`d1e3b2b6-…`), which is why all post-May synthetic events carry that workspace id — dev checker runs land in the developer's persistent test agency (DataBoundaryRisk, minor but real).
- Kill switch: none (no env/flag; router unconditionally mounted `server.py:1434`, run route `:1955`).
- Event store: append-only JSONL, no pruning, O(N) dedupe scan per write under lock (`product_b_events.py:160-174,303-311`) — write amplification on an unauthenticated path.
- Test isolation: checker frontend has exactly one test file; the result-view fetch path (401 for anonymous) has zero coverage.

## 8. Data, Privacy, and PII Boundary Checks

- PII: email can never reach the backend (schema `extra:"forbid"`); privacy guard on trip writes exists (`src/security/privacy_guard.py:526-566`). The exposure risk is the reverse: a fake "Report sent!" success UI over a nonexistent capability.
- Consent: honored for raw text/uploads only; derived trip payloads persist regardless. Self-service deletion exists in UI and router but 401s for the anonymous user (live-probed) — the erasure path is unexercisable by its target user.
- Fixture boundary: all 1,098 funnel events are synthetic (workspace signatures + `has_destination:false`); north-star `action_packet_shared` fired twice, both fixture/script runs using a channel value the current code cannot emit.
- Public checkers trips are isolated from agency dashboards by env-resolved agency_id + RLS scoping; residual: startup validates existence, not non-operating status — misconfiguration risk only.

## 9. Deduped Issue / Task Register

### AUD-01: Fabricated testimonials still live on public checker (P1, trust/legal)
Origin: implicit (doc's legal/trust controls) + prior register LR-D08.
Evidence: `PageClient.tsx:1026-1046` (TESTIMONIALS: "Sarah K.", "Marcus T.", "Priya N."), rendered `:1412-1454` ("Real feedback from real itineraries"), mounted `:1549`; `Docs/review/LAUNCH_READINESS_AUDIT_PER0100_2026-09-02.md:141`.
Gap: LR-D08 recorded 2026-09-02; still unremediated 2026-09-08.
Acceptance: [ ] fabricated quotes removed or clearly labeled as illustrative; [ ] copy sweep test extended beyond blocker-copy.
Rollback: content-only change, trivially revertible.

### AUD-02: Fake email-capture success UI (P1, deceptive UX)
Evidence: `PageClient.tsx:2299` (no network call), `:2277-2278` ("Check your inbox for the full PDF" — no PDF exists); `contract.py:98-117` (backend cannot accept email).
Decision needed: remove the gate, or implement real capture (needs backend field + consent + purpose).
Acceptance: [ ] no success messaging for a capability that doesn't exist; [ ] if kept, real POST + test.
Rollback: frontend-only.

### AUD-03: Unauthenticated KPI-poisonable event surface (P1, security)
Evidence: `spine_api/routers/public_checker.py:81-110` (30/min, 16 KiB); `product_b_events.py:366-385,462-510` (KPIs computed from unverified client events); O(N) dedupe `:160-174`.
Risk: public input controls the launch KPI of record; unbounded append-only storage.
Acceptance: [ ] decide KPI trust model (server-derived counters vs client events); [ ] store rotation/retention; [ ] rate-key behind proxy reviewed.
Rollback: kill switch needed (see AUD-06).

### AUD-04: Anonymous result/export/delete 401 — erasure path unexercisable (P2, functional+privacy)
Evidence: `middleware.py:32-39` vs `server.py:1483-1485`; `PageClient.tsx:2502-2521` (result-view fetch), `:2548`, `:2582`; live probes 401×3 (this audit).
Fix shape: signed per-trip capability token on the run response (pattern exists for proposals: `/api/v1/proposals/token/`) or add trip-id routes to PUBLIC_PREFIXES with capability checks.
Acceptance: [ ] anonymous consumer can fetch/export/delete own report; [ ] authz tests; [ ] full suite green.
Rollback: middleware allowlist + token are feature-flaggable.

### AUD-05: No retention/TTL for public-checker trips + events (P2, privacy/ops)
Evidence: `public_checker_service.py:281-303` (unconditional save); rg retention/TTL/cleanup → zero for checker paths; PA-12 corroboration.
Acceptance: [ ] retention policy decided; [ ] TTL job or documented indefinite-retention rationale.

### AUD-06: No kill switch for the public checker surface (P2, ops)
Evidence: rg `PUBLIC_CHECKER_ENABLED|kill switch|feature flag` → zero; unconditional mounts above.
Acceptance: [ ] env-gated disable returning a clean maintenance page/response; [ ] startup + test coverage.

### AUD-07: Live pricing/marketing nav links checker to nonexistent `/n` route (P2, broken nav)
Evidence: `frontend/src/components/marketing/marketing.tsx` (`href: '/n'`), `pricing-page.tsx` same; `frontend/src/app/n` does not exist; rendered by live `/pricing` route.
Acceptance: [ ] links point to `/itinerary-checker` or are removed; [ ] nav link lint/test.

### AUD-08: Dead share machinery (P3, cleanup)
Evidence: `proxy.ts:34-35` allowlist entries with no pages; channel union `'whatsapp'|'email'` unreachable (`PageClient.tsx:2598`); historical share events used impossible channel `copy_link`.
Acceptance: [ ] remove dead allowlist entries + unreachable union members or implement tokenized sharing deliberately (ties to AUD-04).

### AUD-09: Decision memo never formally closed (P2, product-decision)
Evidence: gates never run; `GTM_ANGLE_ASSESSMENT_2026-09-01.md:242-244` recommends inverting the wedge; `LAUNCH_STATUS.md:9` NO-GO; `DISCUSSION_LOG.md:1048` permanent deferral hook.
Acceptance: [ ] explicit operator decision recorded (kill / invert per GTM assessment / keep as traveler surface); [ ] 2026-04-14 memo annotated with the outcome.

### AUD-10: `PUBLIC_CHECKER_AGENCY_ID` misconfiguration + dev data-boundary wrinkle (P3)
Evidence: `server.py:1102-1161` validates existence, not non-operating status; `.env.example:39` ships the persistent test-agency UUID → dev checker runs land in the working test agency.
Acceptance: [ ] startup warns if agency has memberships/operating role; [ ] dev example uses a dedicated checker agency.

### AUD-11: Stale strategy docs need supersession headers (P3, docs)
Evidence: `Docs/context/ITINERARY_CHECKER_GTM_WEDGE_2026-04-14.md` + `DECISION_MEMO_ITINERARY_CHECKER_2026-04-14.md` contain contradicted claims (scoring, contract, rule IDs) with no pointer to current truth.
Acceptance: [ ] dated addendum header pointing to GTM assessment + registry [C] entry (archive/annotate, do not delete — history preserved per repo doctrine).

### AUD-12: Residual hardening batch (P3)
Rate-key uses peer address behind proxy (`rate_limiter.py:23-25`); export/GET unthrottled for authed users; `visa_not_applied` unreachable at pinned `stage:'discovery'` (`decision.py:1283-1298` + `PageClient.tsx:2871`); no producer found for `validation.overall_score` (score effectively always from baseline map) — last two are Unknown pending a traced live run.

## 10. Prioritization

| ID | Title | Sev | Blast | Effort | Conf | Pri |
|---|---|---|---|---|---|---|
| AUD-01 | Fabricated testimonials live | 4 | 3 | 1 | 5 | P1 |
| AUD-02 | Fake email success UI | 4 | 3 | 1 | 5 | P1 |
| AUD-03 | KPI-poisonable event surface | 4 | 2 | 3 | 5 | P1 |
| AUD-04 | Anonymous 401 / dead erasure path | 3 | 3 | 3 | 5 | P2 |
| AUD-05 | No retention/TTL | 3 | 2 | 2 | 5 | P2 |
| AUD-06 | No kill switch | 3 | 2 | 2 | 5 | P2 |
| AUD-07 | `/n` 404 nav links | 3 | 2 | 1 | 5 | P2 |
| AUD-09 | Wedge decision never closed | 3 | 4 | 1 | 5 | P2 |
| AUD-08/10/11/12 | Cleanup batch | 2 | 1-2 | 1-2 | 4-5 | P3 |

**P0: none** (no real users under current NO-GO posture; every defect is latent until exposure).
Quick wins: AUD-01, AUD-02, AUD-07, AUD-11. Risky changes: AUD-03/04 (auth surface). Needs discussion first: AUD-09 (the wedge's fate gates whether AUD-02/04 should be fixed or deleted), plus AUD-05 retention policy.

## 11. Proof-of-Concept Validation

No proof-of-concept probe was needed. Static evidence from four parallel agents plus existing targeted tests and read-only live-server probes (401×3, 422×1) were sufficient. Files touched this audit: none (this report only).

## 12. Assumptions Challenged by Implementation

| Assumption | Disproved by | Changed conclusion |
|---|---|---|
| "F-43 rewrites dissolve the BFF allowlist, endangering the checker" | `next.config.mjs:26-31` — wildcard rewrites were removed 2026-09-07; catch-all enforces `route-map.ts:88-96` which includes checker routes | Checker is inside the allowlist; F-43 risk reversed |
| "Orphaned by neglect" | `FRONTEND_LANDING_REDESIGN_2026-06-28.md:22` — deliberate delink decision | Reframed: deliberate demotion, never formalized |
| "No doc records the wedge's fate" | `GTM_ANGLE_ASSESSMENT_2026-09-01.md` documents falsification + inversion recommendation | Narrow surviving claim: memo never formally closed |
| "822 events" (from Sept-1 audit) | Store now holds 1,098; post-May all synthetic | Count refreshed; conclusion unchanged |
| "Email capture exists as a funnel stage" | Client-only `setSent(true)`; backend forbids email | Gate is unmeasurable + deceptive (elevated to AUD-02) |
| "Wedge never reviewed ⇒ full suite risk unknown" | Targeted 68+2 tests green this session | Runtime health of checker stack is good; auth layer is where risk lives |

## 13. Parallel Agent / Multi-Model Findings

Four subagents used (Explore, read-only): code-claims verifier, security/privacy reviewer, GTM-supersession tracer, skeptic. One retry round was needed (two rate-limited, one cancelled on first dispatch). Reconciliation: all four converge on "built divergently, demoted, never closed." Disagreements resolved by evidence: the skeptic corrected the F-43 reading, the "orphaned" framing, and the supersession agent's "no verdict recorded" overstatement; the security agent's middleware-gap finding was confirmed by live probe. Final responsibility and this register: main agent. Full subagent evidence (search lists, line cites) is embedded in the sections above.

## 14. Discussion Pack

**My recommendation — work on:**
1. **AUD-01** — remove/label fabricated testimonials (legal exposure on a public surface; one-file fix).
2. **AUD-02** — remove the fake email-success gate (trust honesty; small).
3. **AUD-07 + AUD-11** — fix `/n` 404 links; add supersession headers to the two 2026-04-14 docs.

**Why now:** zero-risk content/copy repairs that remove deception from a public URL regardless of what the wedge decision turns out to be.

**What breaks if ignored:** the public surface keeps displaying fabricated social proof and a fake "email sent" flow — both are credibility defects that any stakeholder demo (e.g., Ravi) or accidental discovery would surface badly.

**What I would not work on yet:** AUD-03/04 auth-surface changes and any real email capture — these should follow the AUD-09 decision (if the wedge is inverted to agency-branded, the consumer auth model changes anyway).

**Ambiguous / questions for you:**
1. Should the 2026-04-14 wedge decision be formally closed as **killed**, **inverted to agency-branded checker** (per GTM_ANGLE_ASSESSMENT Option 1), or **kept as a traveler surface**? This gates AUD-02/04/05.
2. Should KPIs of record be computed server-side (poison-proof) or is the client-event funnel acceptable for now (AUD-03)?
3. Is indefinite retention of public-checker trips acceptable, or do you want a TTL now (AUD-05)?

**Needs runtime verification:** a traced live public run (resolves: does `validation.overall_score` ever populate; can any visa check fire at `stage:'discovery'`).
**Needs online research:** none. Findings are repo-evidence based.
**Needs external review:** no — the wedge decision is yours, and the evidence is unambiguous.

## 15. Online Research

Not used. Current findings are repo-evidence based.

## 16. ChatGPT / External Review Escalation

Not needed. No genuinely uncertain technical decision remains; the open items are product decisions (Section 14 Q1–Q3).

## 17. Recommended Next Work Unit

### Unit-1: Public-checker honesty + dead-nav repair

Goal: remove deceptive content from the public checker surface and repair broken navigation, independent of the wedge decision.

Issues covered: AUD-01, AUD-02, AUD-07, AUD-11.
Scope in: `PageClient.tsx` (testimonials removal/relabel, email-gate removal), `marketing.tsx` + `pricing-page.tsx` link fix, supersession headers on the two 2026-04-14 docs, test extension.
Scope out: auth/middleware changes, email backend, retention, events hardening, decision memo closure.
Likely files: `frontend/src/app/(traveler)/itinerary-checker/PageClient.tsx`, `frontend/src/components/marketing/marketing.tsx`, `frontend/src/components/marketing/pricing-page.tsx`, `Docs/context/ITINERARY_CHECKER_GTM_WEDGE_2026-04-14.md`, `Docs/context/DECISION_MEMO_ITINERARY_CHECKER_2026-04-14.md`, `frontend/.../​__tests__/`.
Acceptance: [ ] no fabricated testimonials rendered; [ ] no fake success messaging; [ ] no `/n` links from live routes; [ ] docs carry dated supersession pointers; [ ] extended frontend tests green; [ ] targeted backend checker tests still green; [ ] full suite run with servers stopped.
Operational safety: content-only; revertible per-file; no auth/data behavior changed.
Risks: copy edits touching honesty-badged surfaces (PER0443 sweep) — must not regress `blocker-copy` test; run the existing copy tests after.

## 18. Appendix: Searches Performed

Consolidated from four subagents + main agent: `CONN_001…WEATHER_001` (repo-wide), `public_checker|public-checker|PUBLIC_CHECKER` (code+tests+docs), `v1/analyze`, `fix-request|fix_request`, `overall_score|quality_score`, `hard_blockers|soft_blockers|STOP_NEEDS_REVIEW`, `retention|TTL|cleanup|purge|expire`, `email|sent|gate` + `fetch(|api.post` in PageClient, `TESTIMONIALS|disclaimer|guidance|guarantee`, `itinerary-checker/shared` (repo-wide), `PUBLIC_CHECKER_ENABLED|kill.?switch`, `stripe|999|lead routing|paid fix` (checker scope), event-schema reads (`product_b_events.py`), env/config files (`fly.toml`, `docker-compose.yml`, `render.yaml`, `.env.example`, `dev.sh`), landing/nav link sweeps (landing-v5, marketing, pricing, v2–v5), `app/n` + sitemap/robots existence checks, event-store JSONL statistical read (workspaces/sessions/channels/synthetic signatures), `git check-ignore data/product_b_events/`, gates/go-no-go sweeps across Docs. Nothing was claimed missing without the corresponding search listed above.
