# Launch Audit Synthesis — 2026-08-01

**Engagement**: External consultant pre-launch audit, Waypoint OS.
**Documents**: `LAUNCH_AUDIT_BASELINE_2026-08-01.md` (7-track sweep) → DD-1 (public surfaces) → DD-2 (deployment) → DD-3 (tenancy/auth) → DD-4 (LLM/PII) → DD-5 (simulation boundary) → DD-6 (monetization) → DD-7 (verification infra) → DD-8 (doc truth). This is the capstone.
**Evidence**: every blocker below was verified this session — static with file:line, most with runtime reproduction (Tier 4–5). Both test suites were executed. CI history was inspected.

---

## 1. Verdict (per the repo's own code/feature/launch discipline)

- **Code-ready**: ❌. 144 backend + 18 frontend tests failing; a live production bug in suitability (`ParticipantRef.age_group`); 4 cross-tenant IDORs; dead customer-facing routes.
- **Feature-ready**: ❌. The customer-facing edge (proposals, webhooks, stage advance, waitlist) is broken or fabricated; the frontier tier is simulation presented as real; the trust scorecard makes unsubstantiated claims.
- **Launch-ready**: ❌. Deployment cannot succeed as configured; there is no working CI; monetization is unbuilt; the written record (review docs, TODO, CHANGELOG, git history) does not match reality; customer discovery is open.

**None of this is fatal.** The core is genuinely strong: pipeline discipline, RLS tenancy, BFF proxy, tier/gating machinery, test culture (4,000+ tests), honest docstrings. The gap is concentrated, identifiable, and — importantly — the remediation is mostly *closing and gating*, not building.

## 2. The one-sentence diagnosis

Waypoint OS built a strong core fast, then let the **claims** (docs, reviews, feature surfaces, deploy configs) run ahead of the **verified reality** — and with no working gate, nothing caught the drift.

## 3. Master blocker table (all verified 2026-08-01)

| # | Blocker | Proof | Doc |
|---|---------|-------|-----|
| 1 | The record is uncommitted: DB-head migration, 16 ADRs, ci.yml (unpushed), deploy.yml | git status/log | DD-2, DD-8 W5 |
| 2 | No working CI anywhere; suite not green (144 BE + 18 FE failures) | executed runs; gh history | DD-7 |
| 3 | Real production bug: `suitability/integration.py:381` `age_group` AttributeError | 14 failing tests | DD-7 V1 |
| 4 | Cross-tenant IDOR ×4 (public-checker read+delete, timeline, bulk-action) | runtime Tier 5 | DD-3 |
| 5 | Proposal links 401 for travelers; garbage tokens serve fabricated "Taj Exotica" proposal + fake acceptances | runtime Tier 4 | DD-1 |
| 6 | Messaging webhooks unreachable; when opened, signature verification is fail-open | runtime + static | DD-1, DD-4 |
| 7 | Simulation boundary: negotiation/ghost/yield/concierge fabricated; auto-rebook **writes fake audit events** | static trace | DD-5 |
| 8 | Deploy configs can't deploy (placeholder image, no migrations in image, `main` vs `master`, no `TRIPSTORE_BACKEND`/`ENVIRONMENT`) | static | DD-2 |
| 9 | PII (health-adjacent) flows to LLMs by default, no minimization/redaction/DPA record | static | DD-4 |
| 10 | No monetization (no Stripe, no trial, no enforcement, ungated signup) | runtime probe | DD-6 |
| 11 | Doc truth: "8/8 verified" review falsified; TODO/CHANGELOG 3 months stale; commit gate enforces retired motto_v3 | file/git checks | DD-8 |
| 12 | Dev server runs with `SPINE_API_DISABLE_AUTH=1` — the masking habit that hid #5–#6 | process env | DD-1 F0 |

## 4. Remediation program (commit-ordered, dependency-aware)

### Phase A — Restore the record & the gate (nothing works without this)

1. Commit + push: migration `0cd0399e2c3c`, ADR batch, Jul-29 docs, `d13f38b` (ci.yml), deploy.yml. *(operator git approval)*
2. Startup config-assertion module (fail-closed in production; refuse boot with `SPINE_API_DISABLE_AUTH`).
3. CI fixes: full frontend vitest, uvicorn for integration tests, re-enabled contract guard with fixed lint glob, deploy gated on CI.

### Phase B — Close the holes (trust blockers)

1. DD-3: scope public-checker/timeline/bulk-action to agency (+ audit events, soft-delete decision); migrate routers to `get_trip_for_agency` + lint rule.
2. DD-1: public router for proposal tokens (expiry, rate limit, real frontend URL); delete demo fallbacks; fix stage-advance path + route-map; fix or remove SSE route; decide waitlist vs signup.
3. DD-4: LLM egress policy module (field allowlist, untrusted-content delimiters); webhook signature hardening bundled with the endpoint opening; encryption fail-closed.

### Phase C — Honesty of surfaces

1. DD-5: gate simulated features off at all tiers; `simulated: true` contract marker; hide settings toggles; stop auto-rebook audit fabrication. Strip trust-scorecard fabrications; register remaining claims in the launch-claim registry.
2. DD-7: fix `age_group`; isolate test DB; debris cleanup; single lockfile.
3. DD-8: rewrite Jul-29 status table honestly; motto v4 cutover; TODO/CHANGELOG refresh; create single `Docs/LAUNCH_STATUS.md`.

### Phase D — Ship path

1. DD-2: Dockerfile + fly.toml fixes, secrets, Postgres, delete render.yaml, frontend deploy (Vercel recommended), error tracking + uptime.
2. DD-6: Stripe foundation (M4.1–4.3 can start any time); pricing after discovery; design partners at $0 first.

**Parallel (non-code)**: customer discovery — 7–10 agency calls incl. pricing questions. It selects the first real frontier feature (DD-5) and validates pricing (DD-6).

## 5. Decision register (everything awaiting the operator)

| # | Decision | From | My recommendation |
|---|----------|------|-------------------|
| D-a | Git approval to commit/push the record (Phase A.1) | DD-2/7/8 | Do first, today |
| D-b | Deploy from `master` or create `main` | DD-2 | Stay on `master` |
| D-c | Frontend host: Vercel vs Fly | DD-2 | Vercel |
| D-d | Public-checker audience: traveler-public vs operator-only | DD-3 | Traveler-public w/ safe projection |
| E | Soft-delete policy for trips | DD-3 | Soft-delete + sweeper |
| D-f | LLM launch posture: disclose vs minimize-first vs gate-off | DD-4 | Minimize-first (field allowlist) |
| D-g | Simulated features: gate-off vs "Preview" labels | DD-5 | Gate off (trust surfaces) |
| D-h | First frontier feature to build for real | DD-5 | Defer to discovery |
| D-i | Free-tier limits, INR vs USD, card-less trial, design partners | DD-6 | 10 trips/mo, INR, card-less, 2–3 partners at $0 |
| D-j | Single lockfile (npm per CI) | DD-7 | npm |
| D-k | Motto v4 cutover execution | DD-8 | Run the two scripts + fix 6 files |

## 6. "Anything else?" (motto_v4 §0.1.1)

- **The mentor paragraph.** The engineering instinct in this repo is real — the ADR discipline, the gating machinery, the test culture, the honest docstrings. What failed is the *operating loop*: gates were allowed to stay red, claims were allowed to go unverified, and truth accumulated uncommitted. None of the twelve blockers is technically hard. All of them are the same habit. Fix the habit (Phase A), and Phases B–D become routine execution. This is also the first-principles answer: a launch is not a feature list, it is a *trustworthy system for knowing what is true* — about the code, the deploy, and the customer.
- **Discovery is the real P0.** Every technical plan above assumes the wedge (WhatsApp-heavy small outbound leisure agencies) is real. TODO.md's discovery section is unchecked and the operator confirmed it's open. Book the calls; run them while Phase A/B lands.
- **What I'd do if this were my company**: Phase A + B before showing any agency anything; Phase C before charging anyone; Phase D.10 before the first real customer account; Stripe only after the first verbal "I'd pay."
- **Audit artifacts created this engagement**: 9 docs under `Docs/LAUNCH_AUDIT_*`; probe agency/user in the dev DB (flagged for cleanup, DD-8 plan item 7); a running backend instance on port 8010 (can be stopped anytime); no code was modified anywhere; no git mutations performed.

## 7. Status

Audit complete: baseline + DD-1…DD-8 + synthesis, all documented. Zero code changed; 12 blockers verified and registered; 11 decisions awaiting operator. The remediation program is ready to execute on your word — say which phase to start.
