# Launch Readiness Audit — PER-0100 (Launch Readiness Director)

*Date: 2026-09-02 · Persona: PER-0100 Launch Readiness Director (Desktop persona repo, `01 Expanded Personas/06 Launch, Growth & Market/`)*
*Specialist doctrines applied: `RELEASE_READINESS_DOCTRINE.md` v1.0 + `OPERATING_DOCTRINE.md` v8.0 (canonical: `/Users/pranay/Projects/agent-start/doctrines/`)*
*Companion: `Docs/review/LAUNCH_IMPLEMENTATION_PLAN_2026-09-02.md` (execution plan). Prior-art registers integrated, not duplicated: `Docs/exploration/MASTER_FINDINGS_TASKS_INVENTORY_2026-09-02.md`, `Docs/LAUNCH_AUDIT_SYNTHESIS_2026-08-01.md`, `Docs/review/GTM_ANGLE_ASSESSMENT_2026-09-01.md`.*
*Checklist applied: IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md*

**Decision (doctrine §7 semantics): NO-GO for public/paid launch today · CONDITIONAL-GO path exists for a bounded invite-only pilot after Phase 1–2 of the implementation plan. NOT-READY-TO-DECIDE on pricing/packaging/business-model gates (operator D1–D8 pending).**

---

## 1. Process Record (chat → evidence, per documentation doctrine)

| Step | What was done | Evidence |
|---|---|---|
| Instruction stack refresh | Read repo `AGENTS.md` (in context), `OPERATING_DOCTRINE.md` v8.0 (530 lines), `RELEASE_READINESS_DOCTRINE.md` v1.0 (canonical path), `Docs/context/agent-start/SESSION_CONTEXT.md`; doctrine routing resolved this task to Review + Release-Readiness modes | `OPERATING_DOCTRINE.md` §16 routing table |
| Persona selection | Listed 754 persona docs; filtered for launch relevance; read `PER-0100 - Launch Readiness Director.docx` in full (via `textutil`); also read `09 Travel - Waypoint OS/INDEX - Waypoint OS Persona Stack.docx` for the project-specific persona families (266 titles) | `/Users/pranay/Desktop/Understanding_Personas_29aug26/`; persona core question: "What must be true before this launch is responsible and useful, what evidence proves it, and what is the safest mechanism for exposing it?" |
| Prior-art load | Read `MASTER_FINDINGS_TASKS_INVENTORY_2026-09-02.md` in full (60 rows) + `AGENTIC_DEEP_AUDIT_SYNTHESIS_2026-08-31.md` (§1–§5) to avoid duplicating registered findings | Both INDEX-linked |
| Audit sweep | 4 parallel read-only Explore agents (backend serving path / frontend+product / CI+release+ops / docs+record), 170 agent tool calls total (54/69/27/20) | §5 findings LR-B/F/O/D below, all file:line-cited |
| Lead verification pass | Spot-verified the 8 most load-bearing blocking claims by direct file inspection before admitting them into this record (S2-tier checks): auth kill-switch truthiness, secret blocklist gap, alembic DB-URL blind spot, DB-blind `/health`, compose env defects, landing fabricated metrics, chatbot-voice CTA, intake fake-success fallback, git tree scale | Each cited claim reproduced verbatim in lead's session; git: 45 modified files (+2770/−422), 228 dirty entries, 183 untracked |
| Truth taxonomy | Every finding below is **Observed** (file:line) unless marked *Inferred* (assumption named) or *Verified* (S2 spot-check noted) | §2 doctrine taxonomy applied |

## 2. Release Unit & Exposure Definition (doctrine §1–§3)

- **Release unit:** Waypoint OS multi-tenant agency platform, current `master` (2f9a638) **plus ~2,770 lines of uncommitted hardening and 183 untracked files including the entire deploy layer** — i.e., what would actually ship today is not what was last CI-verified.
- **Release type:** new product launch (first exposure to external agency users). Internal-only exposure would be a different, smaller unit.
- **Target users:** travel-agency owners/admins (the signup flow creates agency + owner membership). Traveler-facing surface exists (public proposals, booking collection) but is secondary.
- **Exposure mechanism — undecided.** Repo artifacts imply three different answers simultaneously: `fly.toml` (public app `spine-api`), `render.yaml`, `docker-compose` (self-host). None is ratified; the 2026-08-01 launch suite + GTM assessment left D1–D8 pending. Per persona §6, the mechanism is a risk instrument and must be chosen deliberately — recommendation in §9.

## 3. Readiness Profile (doctrine §4–§5 — states, not a percentage)

| State | Verdict | One-line evidence |
|---|---|---|
| BUILD READY | ❌ | docker-compose spine_api cannot start as written (LR-O01); Fly image is a placeholder `ghcr.io/your-org/spine-api:latest`; CI never builds either Dockerfile; Dockerfiles themselves are untracked |
| CODE READY | 🟡 | Deterministic core strong (2f9a638 + hardening wave) but 45 files uncommitted; auth kill-switch truthiness bypass (LR-B01); `ENABLE_TEST_TOKEN` has no prod guard (LR-B06) |
| TEST READY | 🟡 | 3206 backend tests green in CI (~70s), 168 frontend suites, CI-parity wrapper engineered; but eval lanes grade mirrors (E-01/E-02), no journey smoke in CI (E-04), zero security scanning (LR-O05) |
| INTEGRATION READY | ❌ | Alembic migrates the wrong (localhost) DB in real deploy targets (LR-B03); run ledger + proposal revocations on ephemeral local disk (LR-B07); generated FE types 30 days stale with 8 missing models (LR-F05); SSE route uses wrong env var + wrong cookie name (LR-F06) |
| PRODUCT READY | 🟡→❌ | Signup→trip→review flow works with real error/empty/loading states; but fabricated-success demo pages are publicly reachable (LR-F01/F02), landing carries invented proof metrics (LR-F03), 12+ unlabeled simulated panels (C-01), no user guide (LR-D04) |
| OPERATIONALLY READY | ❌ | `/health` always returns ok and every deploy config probes it (LR-B08); `/metrics` is static JSON that scrapers can't even reach (LR-B09); no backups/restore anywhere (LR-B04); no alert destinations (alerts "silently dropped", server.py:1296-1305); no incident/on-call runbook (LR-D03) |
| RELEASE READY | ❌ | Blocking gates unsatisfied; uncommitted deploy layer means the release unit itself is undefined |
| LAUNCH READY | ❌ | No GTM decision (80 GTM docs, "no GTM" per GTM_ANGLE §exec); business model contradicted inside the top-of-stack memory file (LR-D06); zero customer discovery; no TOS/privacy/DPA (LR-D05); fabricated testimonials live on public pages since 2026-08-03 (LR-D08) |

A release with six ❌ and two 🟡 is **not** "≈75% ready" — the trust/ops failures dominate (doctrine §5: nine green categories + one critical trust failure ≠ 90%).

## 4. Launch Gate Matrix (doctrine §71 structure; Blocking/Conditional/Advisory/OK)

| # | Gate | Requirement | Evidence tier | Status | Blocker? | Next action |
|---|---|---|---|---|---:|---|
| G1 | Deployment boots | Compose/Fly/Render each start the API with valid env | T2 | ❌ LR-O01 | Yes | Fix compose env + dialect; add image-build CI job |
| G2 | Migrations hit the real DB | Alembic reads `DATABASE_URL` | T2 | ❌ LR-B03 | Yes | env.py override + release-command test |
| G3 | Auth cannot be silently disabled | Kill-switch parses "0" as off; assertion + middleware agree | T2 (S2-verified) | ❌ LR-B01 | Yes | Fix truthiness; add startup+prod assertion |
| G4 | No default secrets in prod | Placeholder from .env.example rejected at boot | T2 (S2-verified) | ❌ LR-B02 | Yes | Extend blocklist; add PROPOSAL_SIGNING_KEY assertion (matches .env.example's own claim) |
| G5 | Test backdoors closed in prod | `ENABLE_TEST_TOKEN` unusable outside dev | T2 | ❌ LR-B06 | Yes | ENVIRONMENT guard + assertion |
| G6 | Health reflects reality | Probes check DB | T2 (S2-verified) | ❌ LR-B08 | Yes | Point all probes at `/ready`; un-swallow `/health` exceptions |
| G7 | Security state survives deploy | Token revocations + run ledger durable | T1 | ❌ LR-B07 | Yes | Move to DB (or explicit single-host + volume contract) |
| G8 | Backups exist and restore | pg backup + documented restore test | T0 | ❌ LR-B04 | Yes | pg_dump job + restore drill |
| G9 | Observability can detect failure | Real metrics reachable by scraper; request IDs; error tracking | T1 | ❌ LR-B09 | Conditional→Yes for pilot | prometheus_client + auth-scoped /metrics + Sentry |
| G10 | Known security register cleared | S-01…S-07 closed | T2 | ❌ (all open) | Yes | Existing plan (~2 days) |
| G11 | Tenant isolation enforced on promote | Cross-tenant draft-promote closed | T2 | ❌ S-05 | Yes | Ownership check |
| G12 | Public endpoints abuse-bounded | Rate limits proxy-aware; proposal-token endpoints limited; webhook sig enforced | T1 | 🟡 LR-B11–B13 | Conditional | limiter keying + limits + default-deny webhook |
| G13 | Worker topology consistent | workers=4 artifacts vs single-process idempotency seam; 4× background duplication; ~200 conns vs PG 100 | T1 | 🟡 LR-O03 | Conditional for pilot (1–2 agencies) | Pin workers=1 + pool sizing, or adopt the PT-08 seam |
| G14 | Landing claims honest | No invented proof metrics; no chatbot-voice CTA | T2 (S2-verified) | ❌ LR-F03/F04 | Yes (for any public exposure) | Remove/annotate; 30-min fix |
| G15 | Demo pages cannot fake success | `/intake/fast`, `/corporate/offsites` show real errors | T2 (S2-verified) | ❌ LR-F01/F02 | Yes | Delete fallback fabrication or take pages down |
| G16 | Simulated surfaces labeled | 12+ panels + GDSSandbox "Live" labeled-or-gated | T1 | ❌ C-01/G-01-amp | Yes for pilot | Ratify C-01, then label |
| G17 | Frontend prod env contract defined | SPINE_API_URL wired in deploy configs; no browser-side localhost fallbacks | T1 | 🟡 LR-F07/F08 | Conditional | Add env to deploy configs; fix 2 orphan pages |
| G18 | Launch decision documented | `LAUNCH_STATUS.md` exists, current, cites gates | T1 | ❌ LR-D01 | Yes | Create at end of Phase 1 (plan doc) |
| G19 | Record coherent | One findings register; MEMORY.md contradiction resolved; launch suite indexed | T1 | ❌ LR-D02/D06/D07 | Conditional for pilot, Yes for public | E-05 + memory rewrite |
| G20 | Legal/privacy layer | TOS, privacy policy, PII-minimization decision (D-f), DPA | T0 | ❌ LR-D05 | Yes for paid/public; Conditional for invite-only | Operator decision + drafts |
| G21 | GTM/commercial | Business model, wedge, pricing, ICP decided; pilot cohort chosen | T0 | ❌ LR-D06/D09 | Not-ready-to-decide (does not block invite-only pilot) | D1–D8 ratification |
| G22 | Support/incident ready | On-call/escalation runbook; known-issues ledger | T0 | ❌ LR-D03 | Conditional for pilot | Minimal runbook + ledger |
| G23 | Eval judges reality | E-01…E-04 live collectors, holdout, journey smoke | T1 | ❌ | Conditional for pilot (roadmap), Yes before expanding exposure | Existing eval plan |
| G24 | CI gates deploy | Security scan + image build + findings gate; CD gated on CI | T1 | ❌ LR-O04/O05 | Conditional | Add jobs; gate deploy.yml |
| G25 | Accessibility baseline | Auth errors announced (`aria-live`); core flows labeled | T1 | 🟡 LR-F09 | Advisory | role="alert" on auth errors |

**Blocker count for public launch: 14. Blockers for a bounded invite-only pilot: 10 (G1–G8, G14/G15-or-delisting, G16 label-minimum).**

## 5. Findings — NEW this audit (launch-gating; not in the 2026-09-02 inventory)

Severity: P0 = exploit/blocker on shipped surface · P1 = launch-blocking correctness · P2 = conditional · P3 = advisory.
Alignment: 1P = first-principles, LT = long-term coherence, DOC = doctrine (Operating 8.0 / Release-Readiness 1.0). ✗ violates · ✓ aligned · ? needs decision.

### 5.1 Backend serving path (LR-B, from audit agent + lead spot-checks)

| ID | Finding | Evidence (Observed unless noted) | Sev | Gate | 1P | LT | DOC |
|---|---|---|---|---|---|---|---|
| LR-B01 | `SPINE_API_DISABLE_AUTH=0` (string "0") **disables all auth** — truthiness check `os.environ.get(...)` treats "0" as on; `.env.example:45` literally suggests "Leave unset/0"; startup assertion parses the same var correctly (`.lower() in ("1","true","yes")`) so boot checks pass while middleware bypasses | `spine_api/core/middleware.py:39-40,72` vs `startup_assertions.py:51`; `.env.example:44-45`; same truthy pattern in `core/auth.py:61,71,96`. **Verified S2 by lead** | P0 | G3 | ✗ (fail-closed violated by a parse mismatch between two guards) | ✗ | ✗ Security doctrine (authority boundary) |
| LR-B02 | Placeholder secret from `.env.example` (`change-me-to-a-random-secret`, 28 chars) **passes** the JWT_SECRET default-blocklist (`{"secret","changeme","password","default","test","dev"}`); `.env.example:14` claims PROPOSAL_SIGNING_KEY "fails fast at startup" but no such assertion exists in `_ASSERTIONS` | `startup_assertions.py:61-71`; `.env.example:11-16`. **Verified S2** | P0 | G4 | ✗ | ✗ | ✗ |
| LR-B03 | Alembic never reads `DATABASE_URL` — `env.py` uses `alembic.ini`'s `sqlalchemy.url` = hardcoded `localhost` dev creds (`alembic.ini:87` commits them) → fly/render release commands migrate the **wrong database**; runtime app hard-fails without `DATABASE_URL` (asymmetry) | `alembic/env.py:38,59-63`; `fly.toml:15`; `render.yaml:17`; `core/database.py:27-33`. **Verified S2** | P0 | G2 | ✗ (the release command operates on a fiction) | ✗ | ✗ |
| LR-B04 | **Zero backup/restore/retention tooling** anywhere (no pg_dump, no snapshot job, no restore doc) | repo-wide search; §7 of ops agent report | P0 (data) | G8 | ✗ (irreversible-loss path with no recovery) | ✗ | ✗ RRD §26–27 |
| LR-B05 | Compose deployment inert-secure: no `ENVIRONMENT` → all fail-closed assertions downgrade to warnings; postgres+redis ports host-published with hardcoded creds; redis no auth | `docker-compose.yml:11-16,55-56,72-77`; `startup_assertions.py:163-172` | P0 | G1 | ✗ | ✗ | ✗ |
| LR-B06 | `POST /api/auth/test-token` mints real owner JWTs for arbitrary email/role/agency_id, guarded **only** by `ENABLE_TEST_TOKEN=1` — no ENVIRONMENT guard, not in startup assertions | `spine_api/routers/auth.py:377-430` | P0-adj | G5 | ✗ | ✗ | ✗ |
| LR-B07 | Security/operational state lives on local disk: proposal-token revocations (`data/proposals/revoked_tokens.json`), run ledger (`data/runs/`) — fly.toml has **no volume** + `auto_stop_machines=true` → revocations evaporate on every deploy/restart | `public_proposals.py:152-155`; `run_ledger.py:46`; `fly.toml:30-32` | P0-adj | G7 | ✗ (revocation is a promise the platform can silently forget) | ✗ | ✗ |
| LR-B08 | `/health` swallows exceptions and **always** returns `"ok"`; it never checks the DB; **every** deploy config probes `/health` (compose healthcheck, Dockerfile HEALTHCHECK, fly checks, render healthCheckPath) while the real DB-checking `/ready` is unused → dead-DB deploys read healthy everywhere | `routers/health.py:19-32` vs `:35-63`; `docker-compose.yml:25`; `Dockerfile.spine_api:33`; `fly.toml:43`; `render.yaml:19`. **Verified S2** | P1 | G6 | ✗ (probe lies to the orchestrator) | ✗ | ✗ RRD §49 |
| LR-B09 | `/metrics` is static JSON, not Prometheus, and auth-required (scrapers get 401) → effectively no metrics; no request-ID middleware, no structured logging, no error tracking; log scrubber has a tuple-args bug expanding args N→N×7, corrupting %-formatted logs | `server.py:1914-1917`; `middleware.py:27`; `core/logging_filter.py:28-35`; alerts "silently dropped" `server.py:1296-1305` | P1 | G9 | ✗ (launch without measurement = exposure without learning, persona §3) | ✗ | ✗ RRD §37 |
| LR-B10 | Messaging webhook signature enforcement is **WhatsApp-only**; any other `{provider}` accepted with no signature check despite "Default-deny" comment; GET handshake returns "VERIFIED" for arbitrary providers | `messaging_webhooks` (`spine_api/services/messaging.py:118-121,137-149` per agent) | P1 | G12 | ✗ | ✗ | ✗ |
| LR-B11 | `GET /api/auth/validate-code/{code}` unauthenticated with **no router rate limit** vs multi-use invite codes → enumeration surface | `auth.py:437-456,474` | P1 | G12 | ✗ | ✓ | ✗ |
| LR-B12 | Public proposal token GET/accept have **zero rate limiting** (unlimited guessing/accepting; distinct from the known token-secret findings) | `trust_scorecard.py:287,341` | P1 | G12 | ✗ | ✓ | ✗ |
| LR-B13 | Rate limiter keyed on `get_remote_address` behind any proxy → one global 60/min bucket for all users (DoS-by-429); fly/render set no REDIS_URL → per-process memory limiters ×4 workers | `rate_limiter.py:23-25,42-49`; `fly.toml`/`render.yaml` env | P1 | G12 | ✗ | ✗ | ✗ |
| LR-B14 | 4 uvicorn workers (all 4 deploy artifacts) × in-process supervisor/recovery/requeue/watchdog threads = 4× duplicate background work; run execution sticky to accepting worker + filesystem ledger breaks on any multi-machine topology; no request timeouts; per-worker pool 30+20 → ~200 conns vs PG default 100 | `Dockerfile.spine_api:36`; `fly.toml`; `Procfile`; `render.yaml`; `server.py:1263,1270-1276,1898-1904`; `database.py:48-56` | P1 | G13 | ✗ (deployment config contradicts the architecture's own seam) | ✗ | ✗ ARCH |
| LR-B15 | API container runs as root (frontend correctly drops to non-root) | `Dockerfile.spine_api` (no USER) vs `Dockerfile.frontend:28-36` | P3 | — | ✓ intent | ✓ | 🟡 |

### 5.2 Frontend / product surface (LR-F)

| ID | Finding | Evidence | Sev | Gate | 1P | LT | DOC |
|---|---|---|---|---|---|---|---|
| LR-F01 | `/intake/fast` **fabricates success when the backend fails** (`catch` → `{ok:true, trip_id:'trip_fast_demo123', teaser_url:…, "Stage 1 teaser live"}`), uses browser-side `http://127.0.0.1:8000` fallback, sends no `credentials`, hardcodes `creator_sarah` — publicly reachable by URL, indistinguishable from real product | `frontend/src/app/intake/fast/page.tsx:23-56`. **Verified S2 by lead** | P0-adj (trust) | G15 | ✗ (worst class: inventing user outcomes) | ✗ | ✗ Doctrine §13 claim-reality |
| LR-F02 | `/corporate/offsites` silently swaps demo data on failure while a permanent "Duty-of-Care SLA: Active" badge renders; hardcoded tenant ids `comp_techcorp_01`, `trip_zrh_offsite_01` | `frontend/src/app/corporate/offsites/page.tsx:13-40,123-125` | P1 | G15 | ✗ | ✗ | ✗ |
| LR-F03 | Landing page renders **invented operator-proof metrics** as social proof: "2m 14s from inquiry to usable brief", "3 questions before quote", "18% Owner reviews routed" — no data source; flagged in GTM assessment §2.2 (with fabricated testimonials) on 2026-09-01, still live | `frontend/src/components/marketing/landing-v5.tsx:22-26,146-152`. **Verified S2** | P1 (public/legal) | G14 | ✗ | ✗ | ✗ Doctrine §13; FTC-style claims |
| LR-F04 | Leftover AI-assistant voice in public CTA: "If you want, I can show the exact flow: …" reads as pasted chat output on the marketing page | `landing-v5.tsx:199`. **Verified S2** | P2 | G14 | ✗ | ✓ | ✗ |
| LR-F05 | Generated API types stale 30 days (`types/generated/spine-api.ts` @2026-08-01 vs evolving `contract.py`) with 8 recent models missing; the "build error if out of sync" guarantee is not enforced | `frontend/src/types/generated/spine-api.ts` (git dates); `spine_api/contract.py` header | P2 | G17 | ✗ (contract drift is the repo's #1 historical bug source — 2026-04-29 TypeError class) | ✗ | ✗ |
| LR-F06 | SSE route dormant-broken: uses `NEXT_PUBLIC_API_URL` (wrong var; BFF uses `SPINE_API_URL`) and cookie name `spine_auth_token` (real: `access_token`) → silent 401s if ever enabled | `frontend/src/app/api/stream-events/[runId]/route.ts:28-29` vs `lib/bff-auth.ts:35`; SSE default-off `useSSEStream.ts:83` | P2 | G17 | ✓ (dormant) | ✗ | 🟡 |
| LR-F07 | No frontend production env contract: `render.yaml` has no frontend service at all; `Dockerfile.frontend` sets no `SPINE_API_URL`; compose bakes `NEXT_PUBLIC_API_URL=http://spine_api:8000` — a hostname browsers cannot resolve — into a public bundle var | `render.yaml`; `Dockerfile.frontend`; `docker-compose.yml:43` | P1 | G17 | ✗ | ✗ | ✗ RRD §49–50 |
| LR-F08 | Dev fake-session bypass in `(agency)/layout.tsx:56-62` silently grants a fabricated `agency_admin` session when `NODE_ENV !== "production"` — the only guard on a deployed non-prod env; no prod assertion complements it | `frontend/src/app/(agency)/layout.tsx:56-62` | P2 | G17 | 🟡 | 🟡 | 🟡 |
| LR-F09 | Auth error regions lack `aria-live`/`role="alert"` — screen-reader users get no failure announcement; everything else spot-checked clean (labels, skip-link, aria-sort, aria-pressed) | `signup/page.tsx:85`; login equivalent | P3 | G25 | ✓ | ✓ | 🟡 |
| LR-F10 | Positive finding (record for balance): token handling is exemplary — httpOnly cookies end-to-end, zero localStorage tokens, header-allowlisting proxy with prod error-hiding (`proxy-core.ts`), correct autocomplete/labels on auth forms | `frontend/src/lib/api-client.ts:110`; `proxy-core.ts:1-22` | — | — | ✓ | ✓ | ✓ |

### 5.3 CI / release / ops (LR-O)

| ID | Finding | Evidence | Sev | Gate | 1P | LT | DOC |
|---|---|---|---|---|---|---|---|
| LR-O01 | docker-compose spine_api is **non-startable as written**: `DATABASE_URL` lacks `+asyncpg` (async engine rejects it); `JWT_SECRET` absent (import-time raise); `PROPOSAL_SIGNING_KEY` absent; dead var `SPINE_API_SECRET_KEY` read nowhere; `DATA_PRIVACY_MODE=standard` invalid (valid: dogfood\|beta\|production) silently degrading to dogfood | `docker-compose.yml:11-16` vs `core/security.py:21-25`, `core/database.py:48`, `public_proposals.py:106-109`, `src/security/privacy_guard.py:34`. **Verified S2** | P0 | G1 | ✗ | ✗ | ✗ |
| LR-O02 | The release unit is undefined: **45 modified files (+2770/−422) uncommitted; 228 dirty entries; 183 untracked** — including `Dockerfile.spine_api`, `Dockerfile.frontend`, the compose file, ci.yml changes, and the whole hardening stack. Last CI-green commit (2f9a638) contains none of the deploy layer | `git diff --stat` / `git status` 2026-09-02. **Verified** | P0 | G1/G18 | ✗ (deploying ≠ verifying) | ✗ | ✗ (supersession/commit-split F-04 open) |
| LR-O03 | All four deploy artifacts ship `--workers 4`, contradicting the single-process idempotency seam (PT-08) and tripling connection pressure (see LR-B14) | `Dockerfile.spine_api:36`; `fly.toml`; `Procfile`; `render.yaml` | P1 | G13 | ✗ | ✗ | ✗ |
| LR-O04 | CD not gated on CI: `deploy.yml` is an independent push workflow (no `needs:`), deploying an un-pinned placeholder image; fly.toml header even suggests `TRAVELER_SAFE_STRICT=0` in prod; render leaves TRAVELER_SAFE_STRICT unset (= log-only) | `.github/workflows/deploy.yml:3-24`; `fly.toml`; `render.yaml` | P1 | G24 | ✗ | ✗ | ✗ |
| LR-O05 | Zero security scanning (no pip-audit/bandit/semgrep/trivy/npm-audit) and no dependabot; Dockerfiles never build-tested in CI; contract-guard workflow disabled | `.github/workflows/*`; `pyproject.toml` | P1 | G24 | ✗ | ✗ | ✗ |
| LR-O06 | Dual frontend lockfiles (`package-lock.json` + `pnpm-lock.yaml` + `packageManager: pnpm@11.8.0`) while CI installs with `npm ci` → CI/prod dependency drift risk | `frontend/package.json:62`; `ci.yml:173` | P2 | G24 | ✗ | ✗ | ✗ |
| LR-O07 | `ENVIRONMENT` defaults to `development` at ~9 call sites — any deploy target that forgets it silently gets dev-mode semantics (incl. auth kill-switch surface) | `server.py:202,1143,1156,1216`; `routers/auth.py:53,178,336`; `persistence.py:1567` | P1 | G3/G5 | ✗ (secure-by-default violated) | ✗ | ✗ |
| LR-O08 | Positive: env fail-fast discipline in code is genuinely good — sqlite refused in prod, kill-switch refused in prod/staging (when parsed correctly), CORS prod guard bans localhost/`*`, per-endpoint auth rate limits, ASGI body caps, alembic wired into CI with pinned postgres:16 | `startup_assertions.py:38-54`; `server.py:1217-1242`; `auth.py:162-460`; `middleware.py:138-186`; `ci.yml:102,126` | — | — | ✓ | ✓ | ✓ |

### 5.4 Record / GTM / legal (LR-D)

| ID | Finding | Evidence | Sev | Gate | 1P | LT | DOC |
|---|---|---|---|---|---|---|---|
| LR-D01 | The canonical launch-status doc (`Docs/LAUNCH_STATUS.md`) ordered into existence by both the 08-01 synthesis (Phase C.3) and DD-8 **was never created**; no current verdict doc exists after four subsequent audit waves | `ls Docs/LAUNCH_STATUS.md` → absent; LAUNCH_AUDIT_SYNTHESIS_2026-08-01 Phase C.3 | P1 | G18 | ✗ (decision assembled from ≥5 unreconciled docs) | ✗ | ✗ Doc doctrine canonicality |
| LR-D02 | Known-issues ledger does not exist as a single citable surface (3+ competing registers; E-05 open); the 08-01 "Launch-ready ❌" verdict was never re-affirmed or superseded by later waves | MASTER_FINDINGS_TASKS_INVENTORY §E-05; LAUNCH_AUDIT_SYNTHESIS (stale) | P1 | G19 | ✗ | ✗ | ✗ |
| LR-D03 | No incident-response/on-call/escalation runbook (only 3 stale feature runbooks from May); support doc is an April planning essay still indexed as current | `Docs/operations/*` (2026-05-04); `Docs/SUPPORT_AND_CUSTOMER_SUCCESS.md` (2026-04-14); `Docs/INDEX.md:268` | P1 | G22 | ✗ | ✗ | ✗ RRD §41–42 |
| LR-D04 | No user-facing help: USER_GUIDE.md covers one April feature (call capture); no admin manual, FAQ, onboarding guide, or in-app help for a paying agency admin | `Docs/USER_GUIDE.md` | P1 | G22 | ✗ (operator cannot recover/explain — doctrine §13) | ✗ | ✗ |
| LR-D05 | Legal/privacy layer absent: no executed TOS, privacy policy, DPA, or retention schedule (`LEGAL_BASICS.md` = advice + draft-in-fences); the PII→LLM minimization decision (D-f) is still pending; traveler PII (names, passports, medical/dietary, payments) flows to third-party LLM prompts | `Docs/LEGAL_BASICS.md`; LAUNCH_AUDIT_BASELINE H1 + D-f; R-15 doc (resolved guard ≠ resolved policy) | P0 for paid/public | G20 | ✗ | ✗ | ✗ |
| LR-D06 | Business model contradicted inside top-of-stack memory: `memory/MEMORY.md:5` says "white-label B2B SaaS, NOT direct-to-consumer"; `:13` says "Be like Calendly/Typeform, **not** white-label"; `:14` promotes `SINGLE_TENANT_MVP_STRATEGY.md` while `Docs/INDEX.md:238` marks that same doc DEPRECATED (current = multi-tenant) | exact lines cited; Docs agent report §6. **Observed** | P1 | G19/G21 | ✗ | ✗ | ✗ (canonical-path + contradiction) |
| LR-D07 | INDEX.md does not index the 2026-08-01 launch-audit suite (the most load-bearing launch record, 10 docs) nor GTM_ANGLE_ASSESSMENT_2026-09-01, while its top slots foreground simulated case studies carrying unannotated "WILL BUY" verdicts | Docs agent report §7 | P2 | G19 | ✗ | ✗ | ✗ |
| LR-D08 | Fabricated testimonials ("Sarah K.", "Marcus T.", "Priya N.") live on public marketing pages since 2026-08-03 flag — unfixed as of 2026-09-01 (companion finding to LR-F03; recorded as legal/trust exposure on a shipped surface) | GTM_ANGLE_ASSESSMENT_2026-09-01 §2.2 | P1 | G14 | ✗ | ✗ | ✗ |
| LR-D09 | GTM reality: ~80 GTM documents, zero GTM — 3 competing wedge theses, 4 ICP theses, 4 pricing schemes, 2 currencies, 2 geographies, D1–D8 all pending, zero customer discovery ("Not really" — operator verbatim, baseline §9) | `Docs/review/GTM_ANGLE_ASSESSMENT_2026-09-01.md` | — (decision) | G21 | ? | ? | ⚖ operator |
| LR-D10 | Positive: R-15 PII-guard record is exemplary — premise corrected, decision + failsafe recorded, 7 tests, register closed; proves the repo can produce decision-grade records when the discipline is applied | `Docs/review/R-15_PII_GUARD_DEFAULT_2026-08-31.md` | — | — | ✓ | ✓ | ✓ |

## 6. Carried findings mapped to launch gates (no re-audit; IDs from `MASTER_FINDINGS_TASKS_INVENTORY_2026-09-02.md`)

| Launch gate | Carried items | Launch note |
|---|---|---|
| G10 security | S-01…S-04 (token secret/bypass/guess-loop, fake Stripe verify) | Same hotfix class as LR-B01/B02/B06 — batch them |
| G10/G11 | S-05 cross-tenant promote, S-06 egress delimiter, S-07 public-checker DoS, S-08 memory partition, S-09 "Production" adapters, S-10 middleware-order reliance, S-11 revocation/sig-truncation | S-11 is superseded-in-part by LR-B07 (durability), which must be fixed first |
| G23 eval | E-01…E-11 | Gate for expanding exposure beyond pilot, not for pilot start |
| G16 simulated surfaces | C-01…C-06, G-01-amp | Ratify label-vs-wire; minimum viable = label all simulated panels before pilot |
| Product contracts | D-01…D-03 (trip_duration, flights-inclusiveness, multi-destination), D-05…D-09 | Pre-pilot product-correctness; D-01…D-03 are ⚖ decisions |
| Record | R-01…R-10 | LR-D02/D06/D07 are the launch-critical subset; the rest post-pilot |
| Ops decisions | F-04 commit split, F-05 Dockerfile review | F-04 is **now the single largest launch risk** (LR-O02) — the release unit doesn't exist until the split lands |

## 7. Doctrine-Alignment Verdict (the user's central question: is this 1st-principles, long-term, doctrine-aligned?)

**The pattern found in the 08-31 audit holds and extends to the launch surface: *where the code is honest, it is excellent; where the deployment envelope or the record outruns the code, doctrine is violated.***

**Aligned (keep and extend):**

- The deterministic serving core, explicit gates, blocked-as-first-class intake, epistemics/existence split — textbook first-principles (08-31 audit §4.1 stands).
- Security instincts in code: startup assertions, prod CORS guard, sqlite refusal, per-endpoint rate limits, ASGI body caps, httpOnly-cookie-only frontend auth, non-root frontend container, alembic-in-CI. These are the right designs — **the launch audit's core discovery is that the deployment layer defeats almost every one of them.**
- R-15-style decision records and the MASTER inventory's 🛠/🔬/⚖/📝 classification — the record machinery exists and works when used.

**Violations (systemic, three families):**

1. **Fail-open-by-default deployment envelope** (LR-B01/02/05, LR-O01/03/07): the code's fail-closed guards are bypassed or inerted by the configs that actually ship — truthy "0", placeholder secret passing the validator, ENVIRONMENT defaulting to development, compose omitting required secrets while shipping a dead one. First-principles verdict: ✗ — the system's real-world behavior is the opposite of its designed behavior. This is a parse/contract mismatch between two guard layers, i.e., exactly the class the 2026-04-29 API-contract rule was written to prevent, applied to security config.
2. **Claims outrunning behavior** (LR-F01/F02/F03/F08, LR-D05/D08, C-01): fabricated success on failure, invented metrics/testimonials on public pages, an SLA badge over demo data, PII policy gaps. First-principles: ✗ — real-world harm (trust, legal) with zero code-quality offset. Long-term: ✗ — every fabricated proof becomes a future retraction.
3. **No recovery surface** (LR-B04/07/08/09, LR-D03/D04): no backups, ephemeral security state, health probes that lie, no metrics/error-tracking, no incident runbook, no user help. Release-Readiness doctrine: ✗ across §25–27 (rollback/recovery/backup), §37/§41–42 (observability/support). Persona §12's failure mode list reads like this audit's table of contents ("analytics added after release", "support and documentation treated as post-launch work", "no kill switch").

**Undecidable without operator calls (⚖):** business model (LR-D06), exposure mechanism + pilot cohort (G21/D1–D8), signup posture (R-09), C-01 label-vs-wire, PII minimization D-f. These are decision gates, not implementation gaps — and per persona §7, uncertainty here should be resolved by a *bounded* launch design, not by waiting or by shipping wide.

## 8. Launch Risk Register (persona §5 — probability × consequence × detectability × reversibility × exposure radius)

| Risk | Source | Consequence | Reversibility | Detection today | Exposure radius | Class (persona taxonomy) |
|---|---|---|---|---|---|---|
| Auth disabled in a deployed env by `"0"` | LR-B01 | Full tenant bypass | High (unset var) — but silent while active | **None** (metrics absent) | All tenants | **known blocking risk** |
| JWTs signed with documented placeholder | LR-B02 | Token forgery = total compromise | High | None | All tenants | known blocking |
| Migrations ran against wrong DB | LR-B03 | Schema divergence / failed release | Low after divergence | None | All data | known blocking |
| Zero backups | LR-B04 | Catastrophic, permanent data loss | **None** | n/a | All data | known blocking, irreversible |
| Revocations lost on deploy (fly) | LR-B07 | Revoked proposal links re-accepted | High per-event | None | Traveler-facing | known blocking |
| Dead DB reads healthy | LR-B08 | Extended outage masked as healthy | High | User reports only | All users | known blocking |
| Cross-tenant promote | S-05 | Data leak across agencies | Low (data exposure irreversible) | None | Tenant-pair | known blocking |
| PII→LLM w/o minimization/DPA | LR-D05/D-f | Regulatory/contractual exposure | Low (already-sent prompts) | None | All travelers | dependency/legal risk |
| Fabricated proof/testimonials public | LR-F03/D08 | Trust + legal exposure | High (copy fix) | Already flagged | All visitors | known blocking, cheap fix |
| 4-worker duplicate background processing | LR-B14/O03 | Duplicate side-effects, conn exhaustion | High (workers=1) | None | All tenants | monitored uncertainty (needs G13 decision) |
| Unlanded deploy layer | LR-O02 | Ship ≠ verified artifact | High (commit discipline) | CI green on wrong tree | Release integrity | known blocking |
| Unknown unknowns in deploy path | — | — | — | None (no smoke) | — | **unknown because evidence is missing** → resolved by the Phase-2 deploy smoke |

Launch scope must stay proportional to reversibility (persona §5): the irreversible items (backups, PII, tenant isolation) gate hardest.

## 9. Launch Mechanism Recommendation & Decision (persona §6–§8, doctrine §7)

**Public/paid launch: NO-GO.** Blocking gates G1–G8, G10, G14–G16, G20 unsatisfied. Per doctrine §8, the blocking condition is concrete: the deployment envelope is fail-open and unrecoverable (no backups, lying probes, ephemeral security state). The exact condition that flips this: Phase 1 + Phase 2 of the implementation plan verified (S2/S3 evidence per task), plus G18 (`LAUNCH_STATUS.md`) published.

**Bounded invite-only pilot (owner + 1–2 design-partner agencies): CONDITIONAL GO** after Phase 1 hotfixes + minimum record honesty, under these recorded constraints (doctrine §9):

- **Rollout limit:** ≤3 agencies, owner-issued invite codes only; public proposal links acceptable only after S-01…S-04 + LR-B07/B12 close.
- **Monitoring signals:** /ready-based probes; error rate + run-completion rate reviewed daily; Sentry (or equivalent) live before first external user — no metrics, no pilot (persona §3: "Do not use a checklist as proof when the evidence behind the check is weak").
- **Owner:** Pranay (decision authority); agent pool executes, does not expand exposure.
- **Rollback trigger:** any auth anomaly, any cross-tenant error, PII guard AUDIT spike → pause signups (flag) + investigate.
- **Time bound:** 2-week observation window; expansion decision only after G23 (eval core) lands.
- **Not-ready-to-decide (does not block pilot):** pricing/packaging/GTM D1–D8, business model — an invite-only pilot is itself the instrument that answers them (persona §7: "design the launch to answer uncertainty").

**Launch-day minimum (persona §8), to be filled by the plan's Phase 4:** decision authority = Pranay; incident channel = repo issue + direct message; change freeze = none needed at pilot scale; kill switches available: signup rate-limit tightening, `SPINE_API_DISABLE_AUTH` assertion (post-fix), feature flags for SSE/scenario-lab; expansion authority = Pranay only.

## 10. What Else Can Be Done / Improved / Added (net-new, beyond the findings)

1. **One-command deploy contract.** Collapse fly/render/compose/Procfile into one ratified target with a single `make deploy` path + image-build CI job; delete or archive the rest (canonical-path rule §5). Four half-maintained deploy stories is how LR-O01 happened.
2. **Security-config contract tests.** The LR-B01/B02 class (two guard layers parsing the same var differently) is testable: a pytest that boots the app with `.env.example` verbatim and asserts boot **fails**. Cheap, permanent, S3-able.
3. **Deploy smoke in CI (Tier-3).** `tools/runtime_smoke_matrix.py` exists but is manual — wire a compose-up + authenticated smoke job on the release branch. This converts "unknown unknowns" (§8) into tested knowns.
4. **Durable-state policy.** A one-page ADR: what lives on disk vs DB vs object storage, and the rule ("security state must be DB-resident") that prevents LR-B07's class.
5. **Honest-metrics for the deterministic core.** The core is deterministic and fast (3–7ms extraction) — real Prometheus counters on it (runs, escalations, gate hits, extraction latency) would give the launch its learning instrument this week, without any LLM routing work.
6. **Waypoint persona stack adoption** (G-17 extension): pull the launch-relevant Waypoint personas (Travel Lifecycle Architect, Missing-Workflow Red Team, Journey Continuity Architect) into `Docs/personas/` so pilot feedback maps to named review lenses.
7. **Pilot-feedback loop as eval corpus.** Every pilot-agency correction becomes a fixture (failure-becomes-fixture, E-09) — the pilot doubles as the adversarial-corpus collector (E-11) at zero extra build.
8. **Kill-switch inventory.** A table of every flag that can degrade the system live (signup pause, proposal links, SSE, scenario-lab, extraction provider) with owner + trigger — the persona's §8 artifact, mostly derivable from existing flags.

## 11. Explicit Findings/Task Lists — Explore (research-and-document first) vs Implement

**Implement now (explicit, evidence in hand):** LR-B01–B09, LR-F01–F04/F07, LR-O01–O05/O07, LR-D01/D02/D07, plus carried S-01…S-07, E-01…E-05, C-01-labeling, D-05/D-06/D-08/D-10, F-03/F-04. Sequenced and estimated in `LAUNCH_IMPLEMENTATION_PLAN_2026-09-02.md`.

**Explore first (research → document → decide):**

- E-06/E-07 trajectory eval + shadow-eval (post-pilot, needs real usage data — the pilot is the data source)
- C-02/C-03 wire-or-archive dossiers (hybrid engine, router, ghost concierge, 9 zero-caller modules)
- C-04 browser-LLM (parked behind SLM benchmark)
- D-01…D-03 contract decisions (trip_duration, flights-inclusiveness, multi-destination) — ⚖ decisions with a small 🔬 probe each (D-04 interplay)
- F-05 Dockerfile hardening review (after LR-O01 fix makes them buildable)
- **New explores from this audit:** (a) proxy-aware rate-limiting design (LR-B13 — research X-Forwarded-For trust across the chosen deploy target); (b) backup/retention design (LR-B04 — RPO/RTO choice before tooling); (c) durable-state placement (LR-B07 → DB vs volume, an ARCH decision); (d) worker topology (LR-B14 — PT-08 idempotency seam vs workers=1, decide with data); (e) PII minimization options for LLM paths (D-f — research redaction approaches + DPA templates); (f) request-timeout policy (LR-B14 tail); (g) GTM D1–D8 + business model (operator research, GTM_ANGLE is the working doc).
- **Record:** R-01…R-10 per existing plan; plus LR-D03/D04 (runbook + user guide — writing tasks, not research).

## 12. Release Completeness Statement (doctrine §73)

**Verified (S2 spot-checks + direct observation):** the nine headline launch blockers (LR-B01/02/03/08, LR-F01/03/04, LR-O01/O02) — each reproduced verbatim from source during this session.
**Inferred/Unverified:** exact blast radius of LR-B14 duplicate workers under real load (needs the deploy smoke); webhook handler growth risk (LR-B10 — current handler is log-only, *inferred* from code read).
**Blockers:** §4 matrix, 14 for public launch; 10 for invite-only pilot.
**Conditions:** §9 constraint list.
**Residual Risks:** unknown-unknowns in the deploy path until the CI deploy-smoke exists; zero-caller module behaviors under first real load (C-02 dossiers pending).
**Not Assessed:** mobile (no mobile surface shipped), app-store distribution, internationalization, load/capacity beyond conn-pool arithmetic, penetration testing beyond the registered red-team corpus.
**Recommended Decision:** **NO-GO (public) / CONDITIONAL GO (bounded invite-only pilot, post-Phase-1).** Final test (doctrine §74): *"Given what we can actually prove today, is exposing this to real agencies responsible, and can we detect and recover if we are wrong?"* — Today, no: we cannot detect (no metrics/error-tracking) and cannot recover (no backups, ephemeral security state). After the plan's Phases 1–2, the bounded-pilot answer becomes yes.

---
*Next artifact: `Docs/review/LAUNCH_IMPLEMENTATION_PLAN_2026-09-02.md`. This audit supersedes no prior doc; it layers the launch lens on `MASTER_FINDINGS_TASKS_INVENTORY_2026-09-02.md` (which remains the findings union) and re-affirms with new evidence the 2026-08-01 "Launch-ready ❌" verdict.*
