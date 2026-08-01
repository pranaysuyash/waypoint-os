# DD-6: Monetization — Deep-Dive

**Date**: 2026-08-01 · **Parent**: `Docs/LAUNCH_AUDIT_BASELINE_2026-08-01.md` (B11)
**Evidence tier**: Tier 1–2 (static). **Commercial caveat (standing)**: customer discovery is open per operator 2026-08-01 — pricing numbers below are industry-informed hypotheses to test in discovery, not validated facts.

---

## M1 — What exists (the good bones)

Monetization is unbuilt, but the *machinery it plugs into* is unusually ready:

- `Agency.plan` column exists (`spine_api/models/tenant.py:51`, String, default `"free"`) — the subscription hook point is already in the schema.
- `AgencyTier` enum + `_TIER_FEATURE_LIMITS` + `get_tier_limits()` + `tier_allows_feature()` (`src/intake/config/agency_settings.py:347-410`) — a single-source tier-gating module with starter/pro/enterprise limits (trips/month, team seats, feature flags, owner-review thresholds).
- Settings UI already exposes per-tier features (`AiAgentTab`).
- A `/payments` operator surface exists — but it is **traveler-payment tracking** (deposits/balances owed by the agency's clients), not subscription billing. Different domain; do not conflate.
- Pricing page exists and is honest (`pricing-page.tsx` — "Free / Start self-serve / Add support when needed", no invented numbers).

## M2 — What's missing (the full gap list)

1. **No subscription state** — `plan` is never written by anything; every agency is "free" forever. No trial, no expiry, no downgrade path.
2. **No enforcement** — `_TIER_FEATURE_LIMITS` limits (`max_trips_per_month: 50`, `max_team_members: 3`) are **never checked at runtime** (grep: zero enforcement call sites). Tier gating today only works where feature flags are read (frontier/negotiation/call-capture gates); the numeric limits are decorative.
3. **No usage metering** — nothing counts trips/month per agency (the data exists: trips have `agency_id` + `created_at`; the meter is a query, not a pipeline).
4. **No payment provider** — zero Stripe code (verified repo-wide). No webhook endpoint, no customer/subscription models, no checkout.
5. **No signup gating** — self-serve signup creates a full workspace instantly (DD-3 probe proved it: fake email, no verification, instant workspace).
6. **No email verification** — signup → active session with a fake address; also a disposable-account abuse vector (DD-3).

## M3 — Pricing strategy (industry-informed, to validate in discovery)

Comparable SaaS for boutique/small travel agencies (itinerary + ops tooling: Travefy, TravelJoy, TESS/TravelOperations, Safari Portal) clusters at **$30–$100 per user/month**, with agency-level plans common at the low end. For India-targeted small outbound agencies (TODO.md target), willingness-to-pay is materially lower — WhatsApp-first workflows, price-sensitive, INR billing expected. Recommended shape:

- **Free tier** (the wedge, already exists): public itinerary-checker + limited workspace (e.g., 10 trips/month) — acquisition, not revenue.
- **Pro ~₹2,000–3,500/agency/month (~$25–40)** — the realistic India sweet spot for a 1–5 person agency; includes the full pipeline + follow-ups + proposals.
- **Team/Enterprise** — seat-based add-on; owner-review controls, audit, priority support.
- **Trial**: 14 days full-feature, **no card upfront** (India SMB norm; card-upfront kills signup), with in-app day-10/day-13 prompts.
- Annual discount 2 months free — standard, improves cash flow.

Do **not** publish numbers until ≥6 discovery calls include a pricing question (TODO.md already lists commercial questions to ask).

## M4 — Build plan (commit-sized, dependency-ordered)

The minimal honest monetization loop is smaller than it looks because the gating module exists:

1. **Stripe foundation**: `billing` router — `POST /billing/checkout-session` (Stripe Checkout, hosted), `POST /billing/portal-session` (Stripe Customer Portal), `POST /billing/webhook` (signature-verified via `construct_event` — DD-4 L3 pattern applies). No custom card UI.
2. **Schema**: `subscriptions` table (agency_id, stripe_customer_id, stripe_subscription_id, status, tier, current_period_end, trial_end) + alembic migration. Webhook writes; app reads. Stripe is the source of truth, table is the cache.
3. **Gating seam**: a `get_agency_entitlements(agency_id)` dependency that resolves plan → tier → limits, replacing direct `_TIER_FEATURE_LIMITS` reads. Fail-open to `free` tier on Stripe outage (revenue-safe, not abuse-proof — acceptable).
4. **Enforcement at the two real limits**: trip creation (count trips this month per agency vs limit → 402/upgrade prompt) and team invites (seat count). Feature-flag gates already work via tier.
5. **Frontend**: pricing page → real Checkout links; settings → "Billing" tab (portal link, plan status, trial countdown); upgrade prompts at limit hits (402 handling in api-client).
6. **Email verification + trial start** on signup (verification email via the existing alert/messaging infra, or Stripe's).
7. **E2E**: Stripe test-mode webhook in CI (DD-7).

Env: `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PRICE_PRO`, `PUBLIC_BASE_URL`. INR vs USD decision needed for the Stripe account (entity-dependent).

## M5 — Sequencing against the other deep-dives

Monetization should **not** gate first-customer conversations. Recommended order: fix trust blockers (DD-1/3/5) → soft-launch free with 2–3 design-partner agencies at $0 → turn on Stripe (M4) when the first agency says they'd pay. This matches the discovery-open reality: charging infrastructure before the first validated pain is inventory, not progress. But M4.1–M4.3 can be built any time — they have no product risk.

## Decisions needed from operator

1. Free-tier limits (proposal: 10 trips/month, 1 seat) and whether existing dev/test agencies get grandfathered `internal` plan.
2. INR-first vs USD-first billing (depends on the Stripe entity available).
3. Card-less 14-day trial (recommended) vs card-upfront.
4. When to start M4 build: now in parallel (recommended for 4.1–4.3) vs after first design partner.

## "Anything else?" (motto §0.1.1)

- **Design-partner pricing is the real first pricing decision**: 2–3 agencies at $0 for 60–90 days in exchange for weekly feedback is worth more than any paywall. Add to the discovery plan.
- The `require_owner_review_above_value` tier field + DD-5's S4 (simulated features as plan differentiators) interact: pricing tiers must only advertise *real* features — re-check the pricing page copy after DD-5 gating lands.
- Annual-prepaid with a concierge onboarding call is the highest-LTV motion for this segment (agencies buy trust, not software) — worth one line in the sales motion, not the self-serve flow.
- Not verified: whether any agency row already has `plan != 'free'` (dev DB spot-check showed defaults; full sweep trivial during implementation).

## Status

Gap inventory verified; strategy and build plan proposed; **no code changed**. Awaits operator decisions 1–4. Next: DD-7 (verification infrastructure).
