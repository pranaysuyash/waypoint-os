# Elena-Led Persona Council Codebase Audit — 2026-09-11

**Mode:** Whole-repo audit via `$council-orchestrator` (Lead-selected persona), supported by the
`$random-repository-document-audit` protocol (fixed evidence reviewers A–F), the repo's
`Docs/random_document_audit_v2_2026-05-03.md` pattern, and `Docs/PERSONA_COUNCIL_ALL_TASKS_AUDIT_2026-08-29.md`.
**Lead:** Elena Rostova, Agency Owner (`P2-OWNER-01`, `Docs/personas/PERSONA_AGENCY_OWNER_ELENA.md`).
**Repo state at audit:** branch `master`, HEAD `798dddd`; dirty tree = coherent in-flight parallel-agent
remediation batch (`src/intake/decision.py` staged N01 dead-code removal; unstaged X-01/X-08 extractor
hardening in `src/intake/extractors.py`; timestamp-only regens of `d6_audit_gate_snapshot.json`,
`motto_review.md`, `tools/README.md`). Nothing was modified by this audit.
**Persona source:** resolver-ranked canonical `/Users/pranay/Desktop/Understanding_Personas_sept6`
(rank 7, explicit pointer, high confidence) combined with project-repo `Docs/personas/`.

---

## 1. Council Manifest

| Seat | Source | Type | Mission |
|---|---|---|---|
| **Elena Rostova — Agency Owner** | `Docs/personas/PERSONA_AGENCY_OWNER_ELENA.md` | Persona (Lead) | Own the verdict: is the product fit for a boutique agency's real work; margin/risk/settlement lenses |
| Marcus Chen — Junior Associate | `Docs/personas/PERSONA_JUNIOR_AGENT_MARCUS.md` | Persona | Day-1 operator adoption; "can a new hire hurt the agency with this UI?" |
| Clara Sterling — Legal/Compliance | `Docs/personas/PERSONA_LEGAL_COMPLIANCE_CLARA.md` | Persona | PII, tenant isolation, retention, epistemic honesty as contractual exposure |
| Siddharth Mehta — Platform Reliability | `Docs/personas/PERSONA_PLATFORM_RELIABILITY_SIDDHARTH.md` | Persona | Deployability, boot-fail behavior, suite conditioning, retention daemons |
| PER-0442 — Travel Operating Systems Architect | Desktop registry `09 Travel - Waypoint OS` (expanded 2026-09-05) | Persona | Canonical state-substrate coherence; inventory-vs-reality drift as an architecture defect |

**Rejected candidates:** PER-0443 / PER-0700 (already produced the PA-01..40 whole-repo audit — overlap);
PER-WPSYS-0032..47 (near-duplicates of PER-0442 for this task); vertical personas (Klaus/Lars/Devlin/Tariq —
not material to a general audit); Missing-Workflow Red Team (skeptic ran as fixed reviewer F instead — no duplicate seat).

**Activated skills:** council-orchestrator, random-repository-document-audit (protocol), rg search policy.
**Coverage gaps:** none unsupported; frontend rendered-runtime verification (browser) out of scope — code+tests only.

**Fixed evidence team (separate from council):** A status-claims analyst · B codebase verifier ·
C test/runtime verifier · D security/privacy reviewer · E product/UX operator reviewer · F skeptic.

---

## 2. Evidence Summary (what the repo proves, 2026-09-11)

### Verified healthy (evidence-backed)
- **Analytics honesty class holds:** zero `random.uniform|choice|random` in `spine_api/ src/`;
  CSAT None-safe (`src/analytics/metrics.py:307-309`); funnel real-computed (`spine_api/routers/analytics.py:235-253`).
- **Regulatory engines wired, not orphaned:** ICAO MRZ 7-3-1 (`src/intake/mrz.py:18-43`, router `document_extraction.py:28-29`);
  EU261 tiers + claim letters (`spine_api/routers/passenger_rights.py:57-159`); visa_radar mounted (`server.py:382`).
- **Money-path gates real:** margin flag <15% (`src/analytics/engine.py:122-124`), owner escalation <8%
  (`policy_rules.py:114-121`), junior send-block (`policy_rules.py:158-194`), $10k approval (`team_workflows.py:143`),
  ready-check block (`policy_rules.py:91-93`).
- **Retention sweep real and default-on:** 90-day file-store sweep + 180-day segment pruning,
  daemon started at lifespan (`public_checker_access.py:179-294`, `server.py:1327-1330`) — file-store scope only.
- **Standing controls PASS:** FORCE RLS on tenant tables (`add_rls_phase5e_full_coverage.py:236-242`);
  fail-fast `PROPOSAL_SIGNING_KEY`/JWT assertions (`startup_assertions.py:81-93,183-210`); public-checker caps + rate limits;
  egress nonce (`llm_egress.py:194-216`); cross-tenant draft-promote blocks (`drafts.py:280-307`).
- **Findings store gate green at audit time:** `findings.py validate` → 270 events / 258 findings
  (closed 101 · deferred 10 · open 147), 0 warnings, exit 0. No open finding is stale >45d.
- **Operator core flows wired:** ESCALATE banner with `Missing: …` (`workbench/PageClient.tsx:1005-1075`),
  `?repair` deep-link tested (`IntakePanel.repairDeepLink.test.tsx:114-199`), real Quote Review queue
  (`reviews/PageClient.tsx`, `analytics.py:144-156`), escalate-with-audit (`src/analytics/review.py:34-121`).
- **Hybrid engine default OFF in prod, enforced by tests** (`src/intake/decision.py:40`, compose `0`,
  CI `1`, `fly.toml` deliberately unset per PA-03; `tests/test_pa_agentic_remediations.py:140-142`).

### Defects and gaps found (deduped by root cause)

| ID | Sev | Finding | Evidence (exact) |
|---|---|---|---|
| **ISS-001** | **P1** | **Cross-tenant read via client-supplied `X-Agency-ID` on ≥7 routers** — header trusted without JWT-membership verification; middleware already computes `_jwt_agency_id` (`core/middleware.py:126`) but these routers ignore it | `visa_radar.py:40,50,59,64` · `fx_sentinel.py:140-144,226-230` · `concierge_upsell.py:56-60,128-132` · plus `disruption_radar.py`, `loyalty.py`, `passenger_rights.py`, `subagent_payouts.py`; contradicts claimed pattern `core/auth.py:171-190` |
| **ISS-002** | **P1** | **`(agency)/quotes` page is fully fabricated with zero badging** — hardcoded `baseBudget=4200`, invented tiers/status `sent`/dates, fake "GST/TCS 5%" math, dead `waypoint.agency` link; reachable from primary nav next to real Quote Review | `frontend/src/app/(agency)/quotes/PageClient.tsx:71-139,430-460`; `rg SimulatedBadge` in file → 0 hits |
| **ISS-003** | **P1** | **FEATURE_LIST_V3 "runtime-truth" LIVE labels misstate reality on sampled rows** — G01 ghost concierge orphaned (zero serving-path callers of `ghost_concierge.py`); D09 briefings orphaned (no scheduler); E08 accounting export orphaned; I08 counted as LIVE but is a dev script; G02 labeled LIVE while its own router returns `DETERMINISTIC_PREVIEW` "no live feed"; F01/F02 "sandbox credentials" — no credentials ever read; E14 mandates LIVE vs FND-0185 P0 open (mandates default-off, ADR-008 unratified); money tri-state "LIVE" is a decided-but-unimplemented ADR (shipped model is `auto/review/block` gates, `agency_settings.py:55-115`) | Agent F §1 + Agent B §1; V3 evidence pointers themselves (`spine_api/routers/distribution.py:85`) |
| **ISS-004** | P2 | **`ENCRYPTION_KEY` silent dev-key fallback** — committed Fernet key used when unset and `DATA_PRIVACY_MODE != "production"`; `DATA_PRIVACY_MODE` defaults `dogfood`; `ENCRYPTION_KEY` absent from startup assertions | `src/security/encryption.py:22-31`; `privacy_guard.py:51`; `startup_assertions.py:242-253` |
| **ISS-005** | P2 | **Open A4 confirmed on trip lane:** `booking_confirmation` incl. `vcc_card_id` plaintext in `analytics._extra` JSONB (confirmation_service path IS encrypted; trip path is not) | `src/orchestration/booking_fulfillment.py:379-391`; `persistence.py:104-130`; `rg encrypt booking_fulfillment.py` → comments only |
| **ISS-006** | P2 | **LIVE rows silently key-gated; `.env.example` incomplete** — `CAPABILITY_TOKEN_SECRET` required by boundary engine (hard RuntimeError) but absent from the template its own error cites; `REDIS_URL` required in prod but missing; WhatsApp/Twilio keys undocumented → B02 "LIVE P0" channels dead | `src/services/boundary_engine.py:56-63`; `startup_assertions.py:135-143`; `messaging.py:104,135` |
| **ISS-007** | P2 | **Suite-count claims not reproducible / conditional green** — 4,231 static vs 4,437 collected vs claims 3,718/4,250/4,350 across three docs; "of 0" auto-skips integration tests when dev server down, 13 Postgres files, LLM keys; strongest RLS isolation assertion is `xfail` (never green) | `conftest.py:226-246,430-433`; `run_backend_tests.sh:24-29`; `test_rls_live_postgres.py:180-183,530-547`; Agent C baseline |
| **ISS-008** | P2 | **LAUNCH_STATUS (2026-09-04) demonstrably stale** — findings snapshot 183 rows vs store 258; test counts 3,718/1,311 vs current; V3 LIVE verdicts unreconciled with the blocker list on the same surfaces | `LAUNCH_STATUS.md` evidence table vs `FINDINGS_LIVE.md` counts |
| **ISS-009** | P2 | **Roadmap self-contradictions** — A2/A6 claimed both open and "receipt-complete"; undefined item "A8"; duplicate TS-07/08/09 rows with conflicting framing; FND-0117 (P1 corporate_policy auth) folded into "noise floor" narrative | `OPEN_WORK_ROADMAP_2026-09-08.md:13 vs :115-127`; `MIMOSA_FULL_SCAN_RECORD_2026-09-10.md` (48 HIGH residual not per-finding triaged) |
| **ISS-010** | P2 | **New TS-03 S1 attachments surface gaps** — privacy guard has zero coverage of attachment bytes/filenames; storage soft-delete never removes bytes; retention_enforcer self-declares non-enforcement; no magic-byte/malware scan; 5×5 MiB envelope unreachable under 5 MB middleware cap (documented 5×5MiB is a lie at the boundary) | `document_storage.py:21-22,135-141`; `retention_enforcer.py:7`; `privacy_guard.py:117-136` (no attachment fields); `middleware.py:163` vs `contract.py:1383,1396` |
| **ISS-011** | P2 | **No structural SIM_SURFACE registry** — honest-badging is a manual per-component convention (GM-01 badge otherwise well-adopted across ~16 panels); `/quotes` proves nothing structural catches an unbadged fabricated surface | `rg SIM_SURFACE spine_api/` → 0; maps to open A6 TierMetadata + C-01 |
| **ISS-012** | P3 | **Margin floor is modeled, real-margin engine orphaned** — margin base 18% heuristic; `fee_matrix.py` real retail-minus-wholesale engine has zero production callers; no endpoint hard-blocks quote send on margin | `engine.py:62-90`; `fee_matrix.py:24-91` callers = tests only |
| **ISS-013** | P3 | **Elena's exec dashboard criterion partially met** — dashboards honest but no GMV metric exists anywhere; `POST /analytics/export` returns a fabricated URL stub | `rg -i gmv` → 0; `analytics.py:255-267` |
| **ISS-014** | P3 | **Escalation queue shows state, not history** — reviewed_by/at/outcome only on trip page; Rejected/Revision tabs missing; bulk-action endpoint has no UI | `reviews/PageClient.tsx:131-149,342-346`; `analytics.py:169` |
| **ISS-015** | P3 | **Duplicate MRZ check-digit implementations** (two modules, not cross-imported) — divergence risk | `src/intake/mrz.py` vs `src/intake/mrz_parser_engine.py` |

**Working-tree drift (flagged, untouched):** parallel agent's coherent remediation batch (N01 staged;
X-01 quoted-line demotion + X-08 short-fragment rejection unstaged). Consistent with the "all tree work is
shared" doctrine; no conflict with this audit.

---

## 3. Council Rounds (condensed)

**Round 1 — independent lenses.**
- *Elena (Lead):* her four demo criteria map to: exec dashboard (partial — honest but no GMV, ISS-013);
  quote review gate (partial — real gates on a modeled margin, ISS-012); VCC/settlement (PREVIEW_ONLY by design);
  regulatory governance (genuinely live). "The system is honest about almost everything — and then there is a
  quotes page that lies."
- *Marcus:* the `/quotes` page is the literal day-1 catastrophe (copy fabricated pricing to a customer);
  intake/repair/queue flows otherwise serve his JTBD well.
- *Clara:* ISS-001 is a data-isolation breach the moment a second agency exists; ISS-004 is encryption theater;
  ISS-010 retention promise ≠ storage behavior (soft-delete keeps bytes).
- *Siddharth:* ISS-007 means deploy-time truth is unproven (suite conditionally green); REDIS_URL fail-closed is
  good behavior, undocumented requirement is bad hygiene; file-store-only retention = single-process ceiling.
- *PER-0442:* architecture substrate is coherent (one store facade, one findings store, one route map), but the
  feature inventory is repeating the old markdown-register disease: rows drifting from reality (ISS-003), an
  undefined work item, duplicate rows (ISS-009). An inventory whose purpose is runtime truth must be machine-verified.

**Round 2 — material collisions.**
- *Severity of ISS-001:* Siddharth (single-agency pilot → exploitation needs a second agency) vs Clara
  (RLS exists because multi-tenancy is intended; fix is mechanical via `_jwt_agency_id`). **Resolution: P1,
  fix before any second agency / Ravi demo topology.** Falsifier: if the 7 routers are unreachable in the pilot
  topology and no second agency will ever exist pre-launch, downgrade to P2.
- *Severity of ISS-003:* Elena (mislabels don't touch her day-1) vs Agent F (the register is the repo's decision
  instrument — waves are planned off it). **Resolution: P1 as process integrity; P2 as product impact.**
- *`/quotes` disposition:* Marcus (remove now) vs Elena (it signals a desired feature — Quote versions — built
  without a backend). **Resolution: owner call — badge/retire immediately; rebuild only against real spine data.**
- *"Noise floor"*: council accepts residual-74 as mostly mitigated pattern-noise, but rejects the wholesale
  triage: 48 HIGH need per-finding disposition, and FND-0117 (open P1) must not sit inside a "noise" narrative.

**Round 3 — synthesis.** See §4.

---

## 4. Council Decision (Lead: Elena Rostova)

### Recommendation
Run a **"truth consolidation" work unit before any new feature work** (before B6/B7, Wave C, or the TS-03 S2/S3 seams):
1. **Fix ISS-001** — route `X-Agency-ID`-taking routers through the JWT-derived `_jwt_agency_id` (mechanical; pattern exists in `get_trip_for_agency` callers); add a CI grep-gate forbidding raw `X-Agency-ID` reads outside the auth bypass path.
2. **Resolve ISS-002** — badge-or-retire `(agency)/quotes` the same day; no rebuild without real spine data.
3. **Correct ISS-003** — amend the 8 mislabeled V3 rows (G01→UNWIRED, D09→UNWIRED, E08→UNWIRED, I08→TOOLING, G02→PARTIAL, F01/F02→PARTIAL/sandbox-deterministic, E14→GATED, money-tri-state→PLANNED/ADR); add a wiring-evidence requirement (serving-path caller) to the V3 verification method.
4. **Close ISS-006 hygiene** — complete `.env.example` (`CAPABILITY_TOKEN_SECRET`, `REDIS_URL`, `WHATSAPP_*`, `TWILIO_*`, `ENCRYPTION_KEY`, `STRIPE_*`); add `ENCRYPTION_KEY` to startup assertions with production fail-closed (ISS-004).
5. **Refresh ISS-008/ISS-009** — regenerate LAUNCH_STATUS evidence snapshot; reconcile the roadmap's A2/A6 dual status and remove "A8"; re-scope the Mimosa record with per-finding HIGH dispositions referencing FND-0117 instead of folding it.

### Why now
Every decision surface the team relies on (feature inventory, launch status, roadmap, scan record) currently
overstates runtime truth in the same direction; two of the overstatements (ISS-001, ISS-002) are user- or
security-reachable, not just documentation. The parallel remediation batch in the tree is a good moment to
consolidate: nothing new is blocked behind these fixes, but everything planned assumes the register is true.

### Material dissent
Elena would prioritize ISS-012/ISS-013 (real margin floor + GMV) as the fastest route to a usable owner
experience; PER-0442 and the evidence team rank register-integrity (ISS-003) first because misplanned waves
cost more than one dashboard metric. Lead sides with register-integrity; ISS-012/013 follow in the next unit.

### Unknowns / what would change the recommendation
- Full suite not re-run in this audit (bounded lane only); the 4,350/0 claim remains unconfirmed (ISS-007).
- No rendered-runtime/browser verification of frontend findings (code + test evidence only).
- Mimosa 48 HIGH not individually triaged (ISS-009).
- ISS-001 exploitability depends on pilot topology (see falsifier above).

### Next action / falsifier
- **Next safe work unit:** items 1–2 above (one session, ~30 router-line edits + one frontend page disposition + gate + tests).
- **Falsifier:** demonstrate that no second agency can exist before public launch and the 7 routers are unreachable → ISS-001 downgrades to P2 pre-launch hardening and the unit reorders around ISS-002/ISS-003.
- **Findings registration (owner/next session, store currently mid-flight with a parallel agent):**
  `python3 scripts/findings.py open --title "X-Agency-ID cross-tenant read on 7 routers (ISS-001)" --priority P1 --actor elena-council-audit-2026-09-11`
  and equivalents for ISS-002/ISS-003/ISS-004/ISS-010.

### What this audit did NOT do
No code changes, no findings-store writes (shared store mid-flight), no commits, no runtime/browser probes,
no full-suite run, no external research. Report is the sole artifact of this session.
