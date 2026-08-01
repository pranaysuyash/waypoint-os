# Launch Audit Baseline — 2026-08-01

**Engagement**: External consultant pre-launch audit of Waypoint OS (travel_agency_agent).
**Method**: 7 parallel read-only audit tracks (backend pipeline, API/contracts, frontend, deployment/ops, security/data-safety, tests/quality, docs/launch-readiness), each producing file:line-evidenced findings. This document is the synthesis and the index for all follow-up deep-dives.
**Evidence tier**: Tier 1–2 (static inspection + targeted commands). No runtime verification performed yet. Every finding below needs a verification pass before a fix is claimed done.
**Governing doctrine**: `motto_v4.md` (canonical), repo `AGENTS.md`.

---

## 1. Executive Summary

Waypoint OS has a disciplined core pipeline (intake → extraction → gates → decision) with strong tenancy fundamentals (Postgres RLS, bcrypt, httpOnly JWT cookies, allowlisted BFF proxy). But it is **not launch-ready**. The audit found **cross-cutting blockers** in four classes:

1. **Customer-facing surfaces serve fabricated or dead functionality** — proposal links return hardcoded fake data on failure, stage-advance calls a nonexistent route, the waitlist captures emails into the void, and the frontier tier simulates negotiations presented as real.
2. **Deployment cannot succeed as configured** — fly.toml has a placeholder image, the Docker image can't run migrations, the CD workflow targets a branch that doesn't exist, and `TRIPSTORE_BACKEND=sql` (the exact 2026-05-03 data-loss incident) is absent from every prod config.
3. **Monetization is entirely unbuilt** — zero Stripe/billing/trial code; pricing page is decorative; signup is ungated.
4. **Security has two cross-tenant blockers and an unguarded LLM boundary** — public-checker IDOR allows cross-agency read + hard delete; customer PII flows into third-party LLM prompts with no redaction, injection defense, or consent gate.

Overarching theme: **the gap between documented claims and code reality is itself a launch risk.** The 2026-07-29 review declares 8 priorities "Tier-3 verified" citing test files that do not exist; TODO.md is 3 months stale; CHANGELOG is dead since April. Any launch decision made from docs alone will be wrong.

---

## 2. Blocker Register (must close before any paying customer)

| # | Finding | Evidence | Track |
|---|---------|----------|-------|
| B1 | `/proposals/[proposalId]` ships hardcoded fake data ("Taj Exotica, $4,200, 96% match") and silently substitutes it on fetch failure for any `prop_*` token | `frontend/src/app/proposals/[proposalId]/page.tsx:30-50,69-90`; backend mirror `spine_api/routers/trust_scorecard.py:159-183` | FE + API |
| B2 | Proposal link endpoints unreachable: router mounted behind `_auth_or_skip` + AuthMiddleware; `/api/v1/proposals/*` not in public prefixes — customer links 401 | `spine_api/routers/trust_scorecard.py:142,215`; `spine_api/server.py:1145`; `spine_api/core/middleware.py:25-26` | API |
| B3 | Messaging webhooks unreachable by providers (same auth layering) — Meta/SendGrid callbacks 401 | `spine_api/routers/messaging.py:85,111`; `server.py:1146` | API |
| B4 | Cross-tenant IDOR + hard delete: `GET/DELETE /api/public-checker/{trip_id}` — agency A user can read full PII and hard-delete agency B's trips; no permission check, no audit event | `spine_api/routers/public_checker.py:101-134` | API + Security |
| B5 | `transitionTripStage()` calls `/trips/{id}/stage` — missing `/api` prefix, absent from route-map → stage-advance button dead in production; mocked tests hid it | `frontend/src/lib/api-client.ts:995`; `frontend/src/lib/route-map.ts` | FE |
| B6 | Frontier tier fabricates supplier negotiations: invented suppliers/prices, logs "Sent automated RFP", status NEGOTIATING; ghost concierge mints unpersisted workflow IDs; federated intelligence pool is a process-local list | `src/intake/negotiation_engine.py:44-90`; `src/intake/frontier_orchestrator.py:84-86`; `src/intake/federated_intelligence.py:31-33` | Backend |
| B7 | fly.toml `[build] image = "ghcr.io/your-org/spine-api:latest"` placeholder — CD deploy cannot succeed | `fly.toml:12` | Deploy |
| B8 | Docker image lacks `alembic/`, `alembic.ini`, `scripts/` and runtime `uv` → fly release_command and compose migrations both fail | `Dockerfile:53-59`; `fly.toml:15`; `docker-compose.yml:35-37` | Deploy |
| B9 | `TRIPSTORE_BACKEND=sql` absent from fly.toml/render.yaml/Dockerfile → file store on ephemeral FS → trip data loss (2026-05-03 incident in prod) | `fly.toml:17-24`; `render.yaml:20-32`; `spine_api/persistence.py:1384` | Deploy |
| B10 | CD workflow triggers on `main`, repo only has `master` → deploys never run; also no CI-pass gate before deploy | `.github/workflows/deploy.yml` (uncommitted) | Deploy |
| B11 | No billing/trial/monetization code anywhere (zero `stripe`/`trial` refs); signup is ungated self-serve | repo-wide grep; `frontend/src/app/signup/page.tsx:35` | FE + Docs |
| B12 | Landing waitlist is fake — `setSubmitted(true)`, email never sent anywhere; leads silently lost | `frontend/src/components/marketing/marketing-client.tsx:78,85` | FE |

## 3. High-Severity Register (close before or immediately at launch)

| # | Finding | Evidence |
|---|---------|----------|
| H1 | Raw customer PII flows into third-party LLM prompts — no redaction, no injection delimiters, no consent/DPA gate | `src/decision/hybrid_engine.py:543,593,649-655`; `src/llm/openai_client.py:149-168`; `src/llm/gemini_client.py:148-160` |
| H2 | Prompt-injection surface unmitigated — ingested WhatsApp/email text interpolated undelimited into decision prompts | same as H1; repo-wide grep for countermeasures finds nothing |
| H3 | Webhook signature verification fail-open (HMAC only if env set; SendGrid unverified; hardcoded fallback verify token; no replay protection) | `spine_api/routers/messaging.py:99-126` |
| H4 | `SPINE_API_DISABLE_AUTH` globally disables auth + trusts `X-Agency-ID` header; no production startup assertion it's unset | `spine_api/core/middleware.py:30-31`; `spine_api/core/auth.py:160-161` |
| H5 | Hardcoded dev Fernet key in source, guarded only by `DATA_PRIVACY_MODE=production`; `decrypt()` returns ciphertext-as-plaintext on failure | `src/security/encryption.py:29-30,53-57` |
| H6 | `ENVIRONMENT` unset in deploy configs → all prod safety guards off (ENCRYPTION_KEY, auth-bypass block, cookie Secure flag, rate limits) | `spine_api/server.py:203,901`; `spine_api/routers/auth.py:52-53` |
| H7 | Staged edit (+93 lines) to already-released migration `0cd0399e2c3c` — checksum/order drift risk on applied DBs | `git diff --cached alembic/versions/0cd0399e2c3c*` |
| H8 | render.yaml is a stale duplicate deploy path (no Postgres provisioned, localhost DATABASE_URL fallback) — three half-paths instead of one | `render.yaml:10-32` |
| H9 | SSE route dead three ways: wrong cookie name (`spine_auth_token` vs `access_token`), runId regex requires `run_` prefix, backend endpoint doesn't exist | `frontend/src/app/api/stream-events/[runId]/route.ts:29` |
| H10 | Overclaimed verification: 2026-07-29 review cites 3 nonexistent test files as PASSED — treat the "8/8 Tier-3" status table as unverified | `Docs/travel_agency_process_issue_review_2026-07-29.md:26-29` |
| H11 | No e2e automation at all (zero Playwright specs); CI runs only 1 of ~161 frontend test files; contract-guard workflow disabled | `frontend/` (no playwright.config); `.github/workflows/ci.yml`; `run-contract-guard.yml.disabled` |
| H12 | ~30 `detail=str(e)` sites leak raw exception messages (DB/file internals) to clients; no global JSON exception handler | e.g. `spine_api/routers/rag.py:74,102`; `server.py:3382-3616` |
| H13 | Proposal token weaknesses: 16-hex token, `expires_at` never enforced, no rate limit, O(n) cross-agency `list_trips()` scan per lookup | `spine_api/routers/trust_scorecard.py:118-152,221` |
| H14 | No error tracking (Sentry), no structured logging, OTel off by default, no uptime monitoring | `spine_api/server.py:95-119,3637` |

## 4. Medium-Severity Highlights (selected; full lists in track reports)

- Contract drift persists by design: `GET /trips` list returns raw untyped dicts; `assigned_to` injected then silently dropped by `TripResponse.from_dict` (`server.py:1672-1674`); frontend compensates with dual-key reads — the documented crash class, banded not fixed.
- 60/min/IP global rate limit will 429 real dashboard polling sessions.
- RLS reset failure swallowed (`core/rls.py:246`) — tenant-bleed edge on pooled connections.
- No security headers (CSP/HSTS/X-Frame-Options) frontend or backend; CSRF origin validation on only 3 of 17 mutating BFF routes.
- Public experiment pages `/v2`–`/v5` reachable, no robots.txt; `/suppliers` and `/knowledge` live but nav-hidden.
- Conflicting acquisition posture: "Join the waitlist" and "Create workspace" CTAs both ship; the P0 waitlist-vs-signup decision is unresolved.
- TODO.md (2026-04-30) and CHANGELOG.md (dead since 2026-04-29) are 3 months stale; 27 docs still reference retired Streamlit; motto_v3 (AGENTS.md commit gate) vs motto_v4 (doctrine) unresolved.
- No backend static type checking (mypy absent); 16 ruff errors outstanding incl. 1 invalid-syntax + 1 F821.
- Orphaned modules: `src/intake/lifecycle.py`, `src/decision/whatsapp_formatter.py`; in-package test/migration scripts; root-level test debris (DBs, PNGs, 16 playwright profiles).
- Refresh tokens stateless, no revocation; hard delete only, no soft-delete; destructive ops lack audit events.
- `data/` baked into local Docker builds; jupyter/pandas are runtime deps.

## 5. Cross-Cutting Themes

1. **Simulated-vs-real boundary is unmarked.** Frontier tier, demo proposal fallback, fake waitlist — the app presents fabricated data as real on customer-facing surfaces. First-principles fix: a single, contract-level `simulated: true` marker (or hard absence) everywhere synthetic data can surface, plus launch gating of `enable_frontier_orchestration`.
2. **Env-var-dependent safety posture.** `TRIPSTORE_BACKEND`, `ENVIRONMENT`, `DATA_PRIVACY_MODE`, `SPINE_API_DISABLE_AUTH`, `ENCRYPTION_KEY` — each silently downgrades safety when unset. First-principles fix: a single startup config assertion module that fails closed in production and is the only place these are read.
3. **Docs-as-liability.** Overclaimed verification, stale TODO/CHANGELOG, Streamlit ghosts. The doc corpus needs a truth-reconciliation pass, not more docs.
4. **Contract drift is institutionalized as band-aids** (dual-key adapters) instead of being fixed at the source (`response_model` on list endpoints + generated types).
5. **Auth layering has holes at exactly the public/partner boundaries** (proposals, webhooks) while being strict everywhere else — the public-prefix model needs a redesign pass, not per-route patches.

## 6. Proposed Deep-Dive Order

Sequenced by launch-blocking leverage. Each deep-dive produces its own doc (per motto_v4 §0.3.1) and a verification pass at Tier 3+.

1. **DD-1: Public surface integrity** — proposals flow end-to-end (B1, B2, H13, H9), stage-advance (B5), waitlist (B12). The exact surfaces a paying customer's client touches.
2. **DD-2: Deployment path** — pick Fly as canonical, fix Dockerfile/fly.toml/deploy.yml, pin `TRIPSTORE_BACKEND`+`ENVIRONMENT`, delete or complete render.yaml, gate deploy on CI (B7–B10, H6–H8).
3. **DD-3: Tenancy & auth hardening** — public-checker IDOR (B4), auth-disable guard (H4), RLS reset swallow, token revocation, soft-delete + audit on destructive ops.
4. **DD-4: LLM boundary & PII** — redaction/consent gate before third-party calls, injection defenses, webhook signature hardening (H1–H3, H5).
5. **DD-5: Frontier simulation boundary** — gate or honestly label simulated features (B6); decide cut/keep/finish per motto_v4 §0.12.4.
6. **DD-6: Monetization** — Stripe + trial gating + pricing/checkout (B11). Largest build item; can start discovery in parallel.
7. **DD-7: Verification infrastructure** — e2e suite for the golden path, CI coverage of frontend tests, re-enable contract guard, startup config assertions (H11).
8. **DD-8: Doc truth reconciliation** — TODO/CHANGELOG/Streamlit cleanup, re-verify or retract the 2026-07-29 claims, motto v3/v4 resolution (H10).

## 7. Verification Status of This Baseline

- Verified (Tier 1–2): all findings above have file:line evidence from static inspection; test counts from `pytest --collect-only`; grep-based absence claims (stripe/blog) are repo-wide.
- Not verified: runtime behavior of any finding; live env values; whether migration `0cd0399e2c3c` was applied to the persistent DB; actual `fly secrets` contents; whether a Fly app exists.
- Next execution step: DD-1 and DD-2 include runtime reproduction (curl proposal link, attempt deploy dry-run) as entry criteria.

## 8. "Anything else?" (motto_v4 §0.1.1)

- **Uncommitted work in tree**: the 14 ADRs + deploy.yml + migration edit are staged/uncommitted. Per repo git-safety rules no commit was made. The migration edit (H7) is the riskiest staged item.
- **Root-level `.env` exists and was not read** (secrets discipline). Deploy-track env claims are based on `.env.example` + code reads.
- **Commercial reality check**: TODO.md P0 (customer discovery calls) is unchecked. If those 7–10 agency-owner calls haven't happened, every technical blocker above is secondary to validating the wedge. Recommend confirming discovery status before sequencing DD-6 (monetization) build.
- **Positive finding worth preserving**: the core intake→decision pipeline, tenancy model, BFF allowlist proxy, and frontend defensive-fetching posture are genuinely good. The launch risk is concentrated at the edges (public surfaces, deploy config, simulation boundary), not the core.

---

*Track reports were produced by parallel read-only audit agents on 2026-08-01; this synthesis is the canonical index. Follow-up deep-dives reference this doc as DD-1 … DD-8.*

---

## 9. Operator Decisions (2026-08-01, recorded verbatim per motto_v4 §0.3.1)

Asked after baseline presentation:

> **Q: Where should I take the audit next?** — A: **"all one after the other"** (i.e., execute DD-1 → DD-8 sequentially, each documented).
>
> **Q: Did the P0 customer discovery (7-10 agency owner calls) from TODO.md actually happen?** — A: **"Not really"** (discovery is still open).

**Consequence recorded**: The technical launch plan proceeds DD-1 → DD-8 as ordered, but "launch-ready" verdicts must be framed against an unvalidated wedge. Discovery status is a standing caveat on every readiness claim in this engagement, and DD-6 (monetization) sequencing assumes discovery completes in parallel. This mirrors the standing commandment: real-world behavior and business impact before matching existing assumptions.

---

## 10. Errata (appended per motto_v4 §0.12.1)

- **2026-08-01 — H7 reframed**: the staged +93-line migration change is a NEW file, not an edit to a committed migration. The real defect: the migration the persistent dev DB currently sits at (`0cd0399e2c3c`) is applied-but-uncommitted. Full analysis and required action in `Docs/LAUNCH_AUDIT_DD2_DEPLOYMENT_PATH_2026-08-01.md` (Erratum section).
- **2026-08-01 — B2/B3 nuance from DD-1 runtime work**: the proposal/webhook endpoints return 401 under correct config (verified Tier 4), but the operator's dev server runs with `SPINE_API_DISABLE_AUTH=1`, under which they return 200 — this masking effect is why the breakage was invisible. See `Docs/LAUNCH_AUDIT_DD1_PUBLIC_SURFACES_2026-08-01.md` F0.
- **2026-08-01 — Streamlit doc count correction**: the actual count is 24 `Docs/*.md` files, not 27 (DD-8 evidence). Also corrected by DD-7: baseline H11's "CI runs 1 of 161 frontend test files" refers to the local ci.yml — which is committed only in the unpushed `d13f38b` commit and has never run; origin's sole workflow (run-contract-guard) failed on every run and is now disabled. See `LAUNCH_AUDIT_DD7_VERIFICATION_INFRA_2026-08-01.md` V0.
- **2026-08-01 — Test-suite reality added**: executed full suites — backend 2,864 passed / 144 failed, frontend 1,205 passed / 18 failed. Baseline's "test culture is strong" positive note stands, but "verified" claims anywhere in older docs must be re-checked against DD-7 V1.
- **2026-08-01 — Engagement complete**: all deep-dives delivered. Capstone: `Docs/LAUNCH_AUDIT_SYNTHESIS_2026-08-01.md` (verdicts, master blocker table, remediation program, decision register).
