# Waypoint OS Launch Readiness Audit

**Repository:** `pranaysuyash/waypoint-os`  
**Reviewed head:** `b4e651d7795c06b0c38d368e79b2effc64b5647f`  
**Review date:** 2026-08-03  
**Review mode:** GitHub connector-backed static review, repository history, current source inspection, committed test/CI configuration, connected Vercel account, and the repository's own executed launch deep-dives. Local cloning and test execution were unavailable in this runtime, so runtime claims are explicitly separated from source-verified claims.

---

## 1. Executive verdict

Waypoint OS is a serious product codebase with a coherent core domain, strong architectural intent, a substantial test corpus, and a better operator model than most early products.

It is not ready for a public or paid launch.

The core problem is not missing features. The core problem is that the system currently mixes four reality levels without reliable boundaries:

1. real and reasonably mature product behavior;
2. partially wired product behavior;
3. deterministic prototypes presented as intelligent systems;
4. fabricated demo behavior presented as real operational or financial truth.

That mix is dangerous in travel operations because the product handles identity, budgets, trip decisions, supplier claims, traveler-facing proposals, and potentially sensitive traveler constraints.

### Launch readiness score

| Area | Score | Verdict |
|---|---:|---|
| Core domain model and workflow | 8/10 | Strong foundation |
| Backend architecture | 7/10 | Good seams, too many convention-based safety controls |
| Operator UI | 7/10 | Thoughtful, broad, not yet proven end-to-end |
| Public website and positioning | 6/10 | Strong wedge, inconsistent CTA and unsupported proof |
| Accessibility and interaction basics | 6/10 | Good intent, needs browser verification |
| Security and tenancy | 3/10 | Reproduced cross-tenant blockers remain |
| Test and CI readiness | 4/10 | CI exists, backend remains red, frontend suite is not gated |
| Deployment and operations | 1/10 | No functioning canonical production path |
| Monetization | 1/10 | Schema hooks exist, billing and enforcement do not |
| SEO and discoverability | 3/10 | Basic metadata only, missing technical foundation |
| Agentic capability truthfulness | 3/10 | Runtime architecture is good; many advertised capabilities are simulated |
| Documentation truth | 6/10 | Excellent corpus, repeated status drift |

**Overall:** 3/10 for public launch, 6/10 for a tightly controlled design-partner program after P0 remediation.

---

## 2. What is genuinely good

### 2.1 The product wedge is clear

The strongest product statement is:

> Turn messy travel requests into quote-ready briefs.

That is narrower, more credible, and commercially stronger than “AI operating system for travel.” It maps to a frequent operational transition:

`conversation -> structured brief -> missing questions -> owner review -> quote`

The homepage now focuses on this transition rather than presenting every planned platform capability.

### 2.2 The canonical intake-to-decision architecture is real

The repository has a coherent pipeline:

- intake and normalization;
- packet construction;
- gaps and deterministic signals;
- decision logic;
- strategy and bundles;
- API persistence and operator surfaces.

The extraction layer being mostly deterministic and explicit is a strength. It reduces hallucination risk and gives the system inspectable contracts.

### 2.3 The operator mental model is stronger than a generic CRM

The overview surface uses operational concepts such as:

- missing customer details;
- planning in progress;
- ready for quote review;
- ready for booking;
- needs attention.

That is closer to an operations cockpit than a record database. The color grammar also attempts to encode state rather than decorate cards.

### 2.4 Auth implementation has good bones

The reviewed auth path includes:

- HTTP-only cookie transport;
- short-lived access token;
- refresh token;
- endpoint rate limits;
- safe redirect resolution;
- user, agency, and membership creation;
- password confirmation and strength feedback.

This is a credible base. The gaps are in fail-closed environment posture, verification, session revocation, and onboarding, not in the basic login form.

### 2.5 The backend has reusable canonical seams

Good examples include:

- explicit BFF route mapping with deny-by-default behavior;
- `get_trip_for_agency` already existing;
- centralized agency-tier definitions;
- product-agent registry and supervisor;
- audit store and trip-level event surfaces;
- Postgres, migrations, RLS, and async SQL infrastructure;
- request body limits and rate limiting;
- OpenTelemetry instrumentation hooks;
- a substantial test corpus.

The repository does not need an architectural rewrite. It needs safety defaults and convergence on the canonical seams that already exist.

### 2.6 Product-agent runtime architecture is credible

The runtime exposes:

- a static agent registry;
- supervisor health;
- recovery behavior;
- permission-gated manual execution;
- agent events;
- retry and failure contracts.

This is useful operational infrastructure. It should remain. The problem is not the runtime. The problem is that some business agents behind it report simulated outcomes as real outcomes.

### 2.7 The design direction is not generic AI SaaS slop

The current landing page has:

- a distinct dark operations aesthetic;
- a visual workflow ribbon;
- good typography;
- product-specific examples;
- restrained hover interactions;
- a credible emphasis on missing information and owner review.

The visual system is not the launch blocker.

---

## 3. Current implementation state

### 3.1 Real and substantially implemented

These areas have meaningful production-shaped implementations:

- authentication and workspace creation;
- multi-tenant agency/user/membership models;
- trip persistence and SQL path;
- intake packet and structured extraction;
- deterministic gap and suitability logic;
- core decision flow;
- operator overview, inbox, trips, reviews, insights, settings, and workbench surfaces;
- audit/event infrastructure;
- BFF route registry;
- public itinerary checker foundation;
- product-agent supervisor and recovery contracts;
- CI workflow infrastructure;
- route and OpenAPI snapshots;
- deployment configuration files, though they are not functional;
- marketing homepage and pricing/access page.

“Implemented” does not mean launch-safe. Several of these areas contain critical boundary failures.

### 3.2 Partial or contract-drifted

These exist but are not reliable end-to-end:

- stage transition flow;
- traveler proposal links;
- proposal acceptance;
- timeline contract;
- messaging and webhook integration;
- team workflows;
- yield panel;
- concierge routes;
- public checker data ownership;
- geography-dependent validation;
- subscription tier configuration;
- settings-based agent feature gating;
- frontend test coverage;
- startup safety configuration;
- onboarding after account creation;
- production observability;
- content/SEO system.

### 3.3 Demo or simulated, not launchable product behavior

These must be gated, relabeled, or removed before customer exposure:

- unknown proposal token returning a fabricated Goa/Taj proposal;
- unknown proposal acceptance returning success;
- hardcoded trust score, verified-partner badges, refund eligibility, price lock, connection buffers, and fee coverage;
- social intake keyword matching presented as extraction;
- hardcoded 96 suitability score;
- arbitrary payment reference treated as deposit confirmation;
- fabricated hotel and flight details;
- corporate duty-of-care cockpit with invented executives and flight states;
- hardcoded corporate policy caps presented as configured company policy;
- supplier contract lookup that fabricates a default contract;
- in-memory inventory holds;
- invalid dates silently converted into a five-night stay;
- concierge rebooking and supplier economics that are not connected to providers;
- autoresearch scores calculated from hardcoded values and simulated latency;
- process-local “federated” intelligence;
- heuristic sentiment presented in agent rationale without a reality label.

### 3.4 Missing

- functioning production backend deployment;
- frontend deployment for Waypoint in the connected Vercel account;
- production database attachment and proven migration release;
- production secrets checklist and fail-closed startup assertions;
- billing provider;
- subscription state and enforcement;
- email verification;
- terms/privacy consent during signup;
- full frontend CI suite;
- golden-path browser E2E;
- technical SEO assets;
- canonical/noindex strategy;
- public launch analytics funnel;
- error tracking and uptime monitoring;
- customer-validated pricing;
- demonstrated customer discovery completion;
- a single current launch-status source of truth.

---

## 4. P0 launch blockers

### P0-1: The test suite is not green

The repository's latest committed verification record says the repaired CI now exposes roughly 190 backend failures on a fresh Postgres instance.

The frontend CI job currently runs:

- TypeScript;
- ESLint;
- one route-map test file.

It does not gate the full frontend suite.

This means merge confidence remains low despite a large passing test corpus.

#### Required outcome

- all non-optional backend tests green on a fresh isolated database;
- full frontend Vitest suite in CI;
- explicit skip accounting;
- geography fixtures available in CI;
- contract drift repaired;
- no “known red” launch branch.

### P0-2: Reproduced cross-tenant access

The August 1 audit reproduced cross-agency reads and mutations using a real second agency. Current source still shows:

- public-checker package loading through unscoped `TripStore.get_trip`;
- public-checker delete using the target trip's agency ID rather than caller ownership;
- timeline endpoint without agency dependency;
- other convention-based scoping misses.

This is not theoretical. It is a paid-SaaS disqualifier.

#### Required outcome

- every authenticated trip read or mutation uses agency-scoped storage;
- public traveler reads return a traveler-safe projection through a separate public-token model;
- cross-agency access consistently returns 404;
- destructive actions are soft-delete or audited;
- a CI rule rejects bare router-level `TripStore.get_trip`.

### P0-3: Fabricated customer-facing truth

The proposal and trust-scorecard paths currently invent:

- suppliers;
- safety;
- guarantees;
- refunds;
- price locks;
- match scores;
- booking acceptance.

This is the single clearest “do not launch” issue.

#### Required outcome

- unknown token returns 404;
- unknown acceptance returns 404;
- no fallback demo data in production routes;
- no score or badge without traceable source evidence;
- no financial or contractual claim without backing data;
- reality tier is explicit in contracts: `real`, `simulated`, or `planned`.

### P0-4: Proposal flow is broken

The generated link uses `/p/{token}`, while the frontend route is `/proposals/[proposalId]`.

The supposedly public token routes are mounted behind auth.

The token expiry is not enforced correctly.

Acceptance can mutate booking state without a real payment, notification, or safe workflow.

#### Required outcome

A browser E2E must prove:

1. agency creates a real proposal;
2. traveler opens it unauthenticated;
3. expired or unknown token returns a safe 404;
4. traveler requests a change or records intent;
5. agency receives an audit event and notification;
6. no booking state changes without the configured approval/payment contract.

### P0-5: No real deployment path

Current source still contains:

- placeholder Fly image `ghcr.io/your-org/spine-api:latest`;
- CD trigger on `main` while the repo uses `master`;
- a Docker runtime that does not copy Alembic migrations or scripts;
- release commands that depend on those missing files;
- production env flags absent;
- dev agency ID in Fly config;
- no Waypoint Vercel project;
- no attached production database.

#### Required outcome

One canonical path:

- backend: Fly or equivalent;
- database: managed Postgres;
- frontend: Vercel or equivalent;
- migrations run before app release;
- CI success gates deployment;
- health plus functional smoke tests;
- rollback;
- production environment assertions;
- backups and restore check.

### P0-6: LLM egress has no policy boundary

The hybrid decision engine can send traveler facts and sensitive constraints to external model providers by default.

The missing abstraction is not another provider wrapper. It is an egress policy.

#### Required outcome

- field allowlist per decision type;
- direct identifiers removed when unnecessary;
- freeform content redacted or rejected;
- untrusted traveler text delimited in prompts;
- deterministic rules cross-check model output;
- provider usage documented;
- third-party processing disclosed;
- model calls auditable by data class, not raw content.

### P0-7: Simulated agents are exposed as product

Agent runtime infrastructure is real. Several business agents are not.

The most damaging pattern is a simulated operation writing a real audit event.

#### Required outcome

- simulated features disabled by default at every tier;
- unavailable endpoints return 501 or remain absent;
- settings do not advertise them as enabled features;
- audit events are written only after external/provider confirmation;
- dev simulations require an explicit flag and visible badge.

### P0-8: Acquisition posture is undecided

The site acts as though self-serve is live:

- Create workspace;
- pricing/access page;
- immediate signup.

But there is:

- no price;
- no trial;
- no billing;
- no email verification;
- no clear design-partner language;
- no waitlist decision;
- no validated customer-discovery evidence in the current TODO.

#### Required outcome

Choose one:

1. controlled design-partner access;
2. open free beta;
3. paid self-serve.

Do not combine them.

**Recommendation:** controlled design-partner access.

---

## 5. Public website audit

### 5.1 Positioning

#### Good

- “Turn raw trip notes into quote-ready briefs” is specific and credible.
- It names inputs agencies actually use.
- It avoids leading with AI.
- It explains the operator value: missing details, cleaner brief, safer proposal.
- “Not a prettier CRM” is directionally useful.

#### Poor

- “Boutique travel operations, without the theater” is stylish but vague and slightly combative.
- The page uses unsupported numerical proof:
  - 2m 14s;
  - 3 questions;
  - 18% owner reviews.
- “If you want, I can show the exact flow” reads like assistant-generated conversational text, not product copy.
- The page does not show actual product screenshots or a fully credible interactive walkthrough.
- It underplays auditability, internal/client separation, and owner control, which are stronger differentiators.
- It does not explain what happens after “Create workspace.”

#### Better direction

Hero:

> Turn messy trip enquiries into quote-ready briefs.

Subhead:

> Capture calls, emails, WhatsApp notes, and copied itineraries in one place. Waypoint extracts the trip facts, shows what is missing, and prepares a safer brief before your team starts quoting.

Primary CTA for design-partner launch:

> Apply for design-partner access

Secondary:

> See the 3-minute workflow

Proof should be qualitative until measured:

- Separate internal judgment from client-facing output.
- Ask the missing questions before research begins.
- Route only high-risk or high-value trips to owner review.

### 5.2 CTA strategy

Current CTA states conflict across public routes:

- Create workspace;
- Get started;
- Book a demo;
- Try the itinerary checker;
- See pricing.

Some “Book a demo” links point to signup rather than scheduling.

This destroys intent clarity and analytics.

#### Recommended CTA hierarchy

For controlled launch:

- Primary: `Apply for design-partner access`
- Secondary: `Try the itinerary checker`
- Tertiary: `View the workflow`
- Utility: `Sign in`

After billing and onboarding exist:

- Primary: `Start 14-day trial`
- Secondary: `Book a workflow review`

### 5.3 Pricing page

The current page is not a pricing page. It is an access-path explanation.

Problems:

- no price;
- no billing term;
- no trial;
- no usage limit;
- no seat limit;
- no feature comparison;
- no upgrade/downgrade behavior;
- defensive copy such as “Is this a real pricing page…”;
- internal language such as “No fake demo gate” and “Not the point of the page.”

#### Recommendation

Until pricing is validated, rename it to `/access` and say:

> Waypoint is currently onboarding a small number of boutique agencies as design partners.

Show:

- who qualifies;
- what is included;
- expected weekly feedback;
- access duration;
- whether it is free;
- what data/privacy commitments apply.

Publish `/pricing` only when it contains actual commercial terms.

### 5.4 Microcopy

#### Remove or rewrite

| Current idea | Problem | Replacement direction |
|---|---|---|
| “without the theater” | vague, defensive | “Built around the work before the quote” |
| “Not a prettier CRM” | negative framing | “A structured intake and quote-preparation layer” |
| “If you want, I can show…” | assistant voice | “See the complete intake-to-brief workflow” |
| “Set up your agency in seconds” | account creation is not agency setup | “Create your workspace” |
| “No fake demo gate” | internal argument | remove |
| “Is this a real pricing page…” | undermines trust | remove |
| “Process New Inquiry” | inconsistent title case | “Process new enquiry” |
| “Create workspace” everywhere | no expectation-setting | launch-phase CTA |

### 5.5 Vocabulary system

The product currently mixes:

- inquiry and enquiry;
- lead;
- request;
- trip;
- planning item;
- workbench;
- workspace;
- quote;
- proposal;
- review;
- decision.

Define the canonical lifecycle:

1. **Enquiry**: incoming customer request.
2. **Brief**: structured understanding of the request.
3. **Planning trip**: internal work item after acceptance into planning.
4. **Options**: candidate itinerary/commercial choices.
5. **Proposal**: client-facing offer.
6. **Booking**: accepted proposal entering fulfillment.

Use those terms consistently in code, API, UI, analytics, help text, and sales copy.

---

## 6. SEO audit

### 6.1 Present

- root title and description;
- page-specific metadata on some routes;
- semantic headings;
- readable product copy;
- image alt text in the hero;
- Next Image use;
- optimized AVIF/WebP configuration.

### 6.2 Missing

- `sitemap.ts` or sitemap file;
- `robots.ts` or robots file;
- web manifest;
- `metadataBase`;
- canonical URLs;
- Open Graph data;
- Twitter card data;
- structured data;
- organization/software application schema;
- search-engine noindex rules for auth and product workspace;
- canonical/noindex handling for `/v2`, `/v3`, `/v4`, `/v5`;
- content/blog implementation;
- production domain and deployed site;
- Search Console setup;
- product-led keyword architecture;
- conversion analytics tied to search landing pages.

### 6.3 Immediate technical SEO package

Before domain indexing:

1. remove or noindex experiment routes;
2. add canonical to `/`;
3. add `robots.ts`;
4. add `sitemap.ts`;
5. add OG/Twitter image and metadata;
6. noindex auth, workspace, traveler-private, token, and experiment routes;
7. add Organization and SoftwareApplication JSON-LD only with factual claims;
8. add public security/privacy/terms pages;
9. instrument CTA and signup funnel;
10. verify rendered metadata and status codes on production.

SEO is not the reason to delay the controlled launch. The technical foundation is cheap and should land before public indexing.

---

## 7. Motion and interaction audit

### 7.1 Good

The landing page uses restrained micro-interactions:

- navigation hover shift;
- button hover and press feedback;
- animated route dash;
- breathing nodes;
- moving workflow pulse;
- sticky glass navigation;
- smooth anchor navigation.

These are aligned with the workflow concept rather than random decoration.

### 7.2 Risks

- full-screen image plus fixed overlays, blur, gradients, and SVG motion can hurt lower-end devices;
- motion is mostly marketing decoration, not product state communication;
- the SVG animation needs explicit reduced-motion behavior verified;
- sticky glass and backdrop filters need browser and mobile performance checks;
- inline mouse event style mutation in the overview creates local behavior rather than a reusable interaction system;
- no evidence reviewed that route transitions, optimistic saves, long-running agent work, or partial failures have a consistent motion grammar.

### 7.3 Recommended motion system

Use motion only for four jobs:

1. **Cause and effect:** item moves from enquiry to planning.
2. **Progress:** extraction, evaluation, or proposal generation.
3. **Attention:** a new blocker or owner-review requirement.
4. **Continuity:** panel expansion, drawer opening, timeline insertion.

Define tokens:

- instant: 80–120 ms;
- feedback: 160–220 ms;
- layout transition: 240–320 ms;
- long-running progress: indeterminate, never fake percentages;
- easing: one emphasized and one standard curve;
- reduced motion: no continuous movement, no parallax, minimal fades.

---

## 8. Operator flow audit

### 8.1 Acquisition to signup

Current:

`homepage -> signup -> account/agency creation -> overview`

Problems:

- no email verification;
- no terms/privacy consent;
- no clear access plan;
- no onboarding checklist;
- no first enquiry imported during signup;
- no explanation of data processing;
- no role/use-case setup;
- fake/disposable account abuse is easy.

Recommended:

`homepage -> access qualification -> verified email -> agency basics -> import first enquiry -> first brief -> guided review -> invite teammate`

The activation event should be:

> first real enquiry converted into a reviewed brief

Not account creation.

### 8.2 Core operator workflow

The intended flow is good:

`enquiry -> intake -> missing details -> decision -> options -> proposal -> booking`

The reviewed implementation is strongest through the brief and decision stages.

The flow breaks or becomes untrustworthy after that:

- stage transition API path is wrong and absent from the BFF map;
- proposal token path is broken;
- proposal data can be fabricated;
- acceptance semantics are unsafe;
- supplier, yield, payment, and concierge behaviors are simulated or partial.

### 8.3 Public checker

The checker is a potentially strong wedge, but its ownership model is unresolved.

Choose one contract:

- traveler-safe public artifact with signed token; or
- authenticated agency tool.

Do not return the internal trip record to any logged-in user who knows an ID.

### 8.4 Empty state and first value

The overview has thoughtful empty-state language, but onboarding should not leave the user to infer the next path.

A new workspace should present exactly one primary task:

> Paste or upload your first enquiry.

Then show:

- what data is extracted;
- what remains missing;
- what stays internal;
- what can be sent to the client.

---

## 9. Agentic architecture audit

### 9.1 Keep

- product-agent registry;
- supervisor health;
- permissioned manual execution;
- recovery contract;
- retry/poison ownership;
- audit events;
- deterministic extraction;
- hybrid decision seam;
- settings/entitlement seam.

### 9.2 Repair

- agency-scope agent events;
- egress policy;
- prompt-injection containment;
- deterministic cross-check of model decisions;
- durable queues only in production;
- feature reality metadata;
- provider confirmation before audit success events;
- error budgets and per-agent metrics;
- idempotency keys on externally consequential actions.

### 9.3 Gate or remove

- simulated concierge;
- simulated auto-rebook;
- simulated yield arbitrage;
- simulated supplier holds;
- simulated duty-of-care;
- simulated autoresearch score claims;
- simulated trust scorecards;
- hardcoded high-value data;
- demo proposal fallbacks.

### 9.4 Reality-tier contract

Every feature must declare:

```text
reality_tier: real | connected_sandbox | deterministic_preview | simulated | planned
```

Rules:

- only `real` can write operational success events;
- only `real` can appear as an enabled paid feature;
- `connected_sandbox` is visible only to internal/design-partner tenants;
- preview/simulated output is visibly labeled;
- planned features have no live endpoint.

---

## 10. Architecture and code quality

### 10.1 Strong

- sensible Python/Next split;
- SQLAlchemy/Alembic/Postgres base;
- explicit API models;
- route snapshots;
- BFF deny-by-default map;
- auth and permission dependencies;
- RLS investment;
- modular router extraction from a large server;
- audit/event concepts;
- typed frontend;
- React Query/Zustand separation;
- sizeable unit/integration corpus;
- documentation and ADR discipline.

### 10.2 Weak

- manual tenant checks instead of structurally scoped repositories;
- broad `except Exception` fallbacks;
- SQL-to-file fallback creates split-brain persistence;
- environment defaults fail open;
- production behavior depends on flags not asserted at startup;
- duplicate deploy paths;
- mixed package manager signals;
- stale descriptions and permissive lint ignores;
- in-memory business state;
- hardcoded IDs and economic values;
- router contracts drift from tests;
- documentation claims outrun executable evidence.

### 10.3 Specific code smells to eliminate

- defaulting production-sensitive environment to `"development"`;
- returning ciphertext as plaintext after decrypt failure;
- swallowing RLS reset failures;
- using any trip's own agency ID to authorize deletion;
- accepting arbitrary payment references;
- converting invalid dates into plausible business values;
- fabricating records when lookup misses;
- mutating trip stage from unauthenticated or weakly authenticated intent;
- writing audit success before external confirmation;
- broad fallback from SQL to local file store;
- hardcoded public base URLs;
- hardcoded dev tenant IDs in deploy config;
- exposing API docs in production without an explicit decision.

---

## 11. Testing and verification plan

### 11.1 CI must run

Backend:

- Ruff;
- static typecheck ratchet;
- migrations on clean Postgres;
- all unit tests;
- all integration tests with server running;
- contract/snapshot checks;
- tenancy tests;
- startup assertion tests;
- skip count report.

Frontend:

- TypeScript;
- ESLint with zero launch-relevant warnings;
- full Vitest;
- accessibility component checks;
- route-map contract;
- build.

Browser:

1. signup/login/logout/refresh;
2. first enquiry to reviewed brief;
3. stage transition;
4. proposal token lifecycle;
5. cross-agency denial;
6. public checker safe projection;
7. direct/deep URL;
8. expired session;
9. missing/legacy data;
10. mobile navigation and first-value flow.

### 11.2 Launch verification evidence

Every “done” item requires:

- exact command;
- date;
- commit SHA;
- output summary;
- artifact/log link;
- owner;
- known exceptions.

No “verified” status based only on a test filename or an agent summary.

---

## 12. Deployment plan

### Recommended canonical stack

- Frontend: Vercel.
- Backend: Fly.io or another managed container platform.
- Database: managed Postgres.
- Storage: explicit durable object/file store where required.
- Observability: structured logs, error tracking, uptime, traces.
- CI/CD: master -> CI -> deployment -> migrations -> health -> functional smoke -> rollback.

### Required repository changes

- Dockerfile copies Alembic and scripts;
- `.dockerignore` excludes runtime trip/run/draft data;
- `fly.toml` builds the repository Dockerfile;
- remove placeholder image;
- set production environment flags;
- remove dev tenant ID;
- change CD trigger to `master`;
- gate CD on CI success;
- replace placeholder health URL;
- document required secrets;
- provision database;
- verify migrations;
- create Vercel project and environment variables;
- configure CORS;
- add backups;
- test rollback and restore.

---

## 13. Monetization and commercial launch

### What exists

- agency plan column;
- starter/pro/enterprise enums;
- feature/limit configuration;
- pricing/access surface;
- traveler payments surface.

### What does not

- Stripe or another subscription provider;
- checkout;
- webhook;
- subscription record;
- trial;
- entitlement resolution;
- usage metering;
- trip-limit enforcement;
- seat-limit enforcement;
- billing settings;
- upgrade/downgrade;
- invoice/tax posture;
- verified price.

### Recommendation

Do not build a full billing system before the first design partners.

Launch sequence:

1. 2–3 design partners;
2. 60-day structured program;
3. measure enquiry volume, time to brief, rework, owner-review load, conversion;
4. ask pricing questions;
5. build hosted checkout and entitlement enforcement;
6. publish pricing only after evidence.

---

## 14. Recommended launch mode

### Option A: Controlled design-partner launch

**Recommended.**

- 2–3 boutique agencies;
- accounts provisioned or approved manually;
- no paid claims;
- no simulated features;
- limited real workflow: enquiry -> brief -> missing questions -> review;
- weekly feedback;
- explicit data-processing agreement;
- support channel;
- manual incident response;
- private/noindex public positioning if necessary.

**Why:** It monetizes learning, limits blast radius, and tests the strongest product wedge.

### Option B: Open free beta

Pros:

- faster acquisition;
- more varied data;
- public feedback.

Cons:

- abuse;
- tenancy risk;
- support burden;
- noisy feedback;
- public trust damage.

Do not choose before P0 security and deployment work.

### Option C: Paid self-serve launch

Reject now.

The product lacks billing, enforcement, verified onboarding, stable proposal flow, green tests, and a production stack.

---

## 15. Agent-ready work packages

### Track A: Truth boundary and feature gating

**Files**

- `spine_api/routers/trust_scorecard.py`
- `spine_api/routers/social_inbound.py`
- `spine_api/routers/corporate.py`
- `spine_api/routers/supplier.py`
- `spine_api/routers/concierge.py`
- `spine_api/routers/yield_arbitrage.py`
- `src/evals/autoresearch_loop.py`
- agency feature settings and related frontend panels

**Tasks**

- remove demo fallbacks;
- introduce reality tier;
- default simulated features off;
- prevent simulated audit success;
- return 404/501 honestly;
- remove unsupported financial/legal claims.

**Acceptance**

- no fabricated value on production request path;
- all simulated endpoints inaccessible without explicit dev flag;
- test unknown/missing data paths;
- UI visibly distinguishes preview from real.

### Track B: Tenant isolation

**Files**

- `spine_api/routers/public_checker.py`
- `spine_api/routers/trip_observability.py`
- `spine_api/routers/analytics.py`
- `spine_api/routers/legacy_ops.py`
- `spine_api/persistence.py`
- auth/RLS helpers

**Tasks**

- scope every read/write;
- add traveler-safe public projection;
- soft-delete;
- audit destructive actions;
- add CI lint/check.

**Acceptance**

- second-agency test returns 404 across every route;
- no router bare `get_trip`;
- RLS reset failures discard connection;
- file backend cannot run in production.

### Track C: CI and contract repair

**Files**

- `.github/workflows/ci.yml`
- `tests/conftest.py`
- geography fixture/loading paths;
- failing router tests;
- timeline contracts;
- frontend Vitest config.

**Tasks**

- fix all backend failures;
- full frontend suite;
- start live server for integration tests;
- add Playwright golden paths;
- report skips.

**Acceptance**

- clean CI from fresh clone;
- no hidden red suite;
- five critical E2E flows green.

### Track D: Deployment

**Files**

- `Dockerfile`
- `.dockerignore`
- `fly.toml`
- `.github/workflows/deploy.yml`
- `.env.example`
- frontend deployment config

**Tasks**

- canonical backend build;
- production flags;
- managed Postgres;
- Vercel project;
- CI-gated CD;
- migrations and rollback;
- monitoring.

**Acceptance**

- production URL;
- migration from empty database;
- health and functional smoke;
- rollback and restore evidence.

### Track E: Marketing, CTA, SEO, copy

**Files**

- `frontend/src/components/marketing/landing-v5.tsx`
- `landing-v5.module.css`
- `pricing-page.tsx`
- root layout/page;
- new sitemap/robots/OG files;
- experiment routes.

**Tasks**

- choose launch CTA;
- remove unsupported metrics;
- rename pricing to access until priced;
- remove defensive copy;
- canonical/noindex;
- analytics events;
- factual schema.

**Acceptance**

- one CTA strategy;
- no duplicate indexable landing variants;
- no unsupported claims;
- metadata verified in production;
- CTA funnel observable.

### Track F: Activation and onboarding

**Files**

- signup;
- auth service/router;
- overview empty state;
- onboarding components;
- agency settings.

**Tasks**

- email verification;
- terms/privacy consent;
- first-enquiry onboarding;
- activation checklist;
- design-partner approval state.

**Acceptance**

- verified user reaches first reviewed brief;
- no blank-workspace dead end;
- disposable accounts cannot immediately abuse authenticated surfaces.

### Track G: LLM privacy and integrity

**Files**

- hybrid decision engine;
- LLM clients/factory;
- privacy guard;
- encryption;
- startup config.

**Tasks**

- egress allowlist;
- PII minimization;
- injection delimiting;
- deterministic cross-check;
- provider policy;
- fail-closed encryption/config.

**Acceptance**

- tests prove names/contact data do not leave when unnecessary;
- malformed or injected text cannot override deterministic policy;
- production refuses unsafe configuration.

---

## 16. Two-week launch-hardening sequence

### Days 1–2: Scope freeze and truth reset

- freeze new feature development;
- create `Docs/LAUNCH_STATUS.md`;
- classify every exposed capability as real/preview/simulated/planned;
- choose design-partner launch;
- select canonical terminology and CTA.

### Days 3–5: Security and honesty

- tenant-scoped repository usage;
- public checker contract;
- remove proposal/demo fallbacks;
- gate simulated agents;
- startup assertions;
- LLM minimization.

### Days 6–8: Make verification real

- fix backend failures;
- full frontend tests in CI;
- add critical Playwright paths;
- repair stage transition and proposal lifecycle.

### Days 9–10: Deploy

- fix Docker/Fly/CD;
- provision Postgres;
- create Vercel project;
- configure secrets/CORS;
- migrations, smoke, rollback, backup.

### Days 11–12: Activation and public surface

- design-partner signup/approval;
- first-enquiry onboarding;
- homepage CTA and copy;
- pricing -> access;
- robots/sitemap/canonical/noindex;
- analytics.

### Days 13–14: Operational rehearsal

- create clean agency;
- process real anonymized enquiry;
- invite second user;
- generate and open traveler-safe output;
- simulate outage/session expiry;
- verify logs and alerts;
- run cross-tenant probes;
- record release evidence.

---

## 17. Launch gate

Do not launch publicly until all are true:

- [ ] backend suite green on clean Postgres;
- [ ] full frontend suite green in CI;
- [ ] critical browser E2E green;
- [ ] cross-tenant probe suite green;
- [ ] no production demo fallback;
- [ ] no unsupported guarantee or score;
- [ ] production startup fails closed;
- [ ] SQL persistence mandatory;
- [ ] real deployment and database;
- [ ] migration/rollback/backup proven;
- [ ] error tracking and uptime live;
- [ ] email verification and legal consent;
- [ ] one acquisition posture and CTA;
- [ ] public/private crawl boundaries;
- [ ] design-partner support and incident owner;
- [ ] current launch status is machine-evidenced.

---

## 18. Final recommendation

Do not spend the next cycle adding more agentic features, corporate modules, supplier modules, or frontier workflows.

Narrow Waypoint OS to its strongest real promise:

> Convert messy travel enquiries into structured, reviewable, quote-ready briefs while keeping internal judgment separate from traveler-facing output.

Launch that with two or three design partners.

Everything else should either be:

- connected to real providers and proven;
- explicitly labeled preview;
- disabled;
- or removed from customer surfaces.

That is the fastest path to a product that earns trust rather than merely looking complete.
