# Waypoint OS — Current Status

**Last updated:** 2026-10-26
**Canonical source:** This file (replaces scattered TODO.md, NAVIGATION_TASKS.md, etc.)

## Product-Done Score: 5/10

## Resolved This Session
- [x] Frontend lint: 0 errors (was 7)
- [x] Frontend typecheck: clean (was 8 stale errors)
- [x] Removed fabricated suitability score (96 → None)
- [x] Removed simulated deposit_payment_ref default (now required)
- [x] Cross-tenant audit: router layer clean, service layer largely mitigated
- [x] Fabricated proposal data: already gated by PUBLIC_PROPOSAL_DEMO_MODE
- [x] Audit document created: Docs/review/PRODUCT_DONE_AUDIT_2026-10-26.md
- [x] 11 new findings registered (FND-0385–FND-0395)
- [x] Consent capture: User model + signup service + migration + auth tests pass
- [x] Consent capture: frontend signup checkbox + terms_accepted in request body
- [x] Frontend build verified after consent changes
- [x] Skip-to-content link added to root layout (H-01)
- [x] Reduced-motion CSS support added to globals.css (H-02)
- [x] Email verification: EmailVerificationToken model + migration + auth_service functions + endpoints
- [x] Email verification: ruff clean, auth tests pass
- [x] DB backup/restore tools: fixed ruff errors, created runbook
- [x] Session revocation: RevokedToken model + migration + revoke on logout + check on refresh
- [x] Session revocation: ruff clean, auth tests pass (34/34)
- [x] Ruff: 0 errors across entire repo
- [x] RAG groundedness: echo-hallucination guard added (FND-0164 closed)

## Open P0 (Blocking)
- [ ] FND-0368: 6 backend test files with order-dependent failures (polluter identification in progress)
- [ ] Test-order pollution: 3+ failures in full suite run
- [ ] Deployment: no production backend/frontend deployment (HELD - pending user decision)
- [ ] Monetization: no billing/subscription (HELD - pending user decision)

## Open P1 (Important)
- [x] Email verification (backend: model + migration + endpoints; email sending pending provider) on signup
- [x] Terms/privacy consent capture (terms_accepted_at on User model, required in signup)
- [x] Session revocation (RevokedToken model + migration + revoke on logout + check on refresh)
- [ ] Guided onboarding flow
- [ ] Golden-path browser E2E test
- [ ] Frontend CI gating (already in ci.yml, needs verification)

## Open P2 (Nice to Have)
- [x] CSRF protection (validateOrigin in BFF, SameSite cookies)
- [ ] Rate limiting on auth endpoints
- [ ] Bundle size budget
- [ ] Tablet breakpoint testing
- [x] Reduced-motion CSS support (globals.css)
- [ ] Keyboard navigation audit
- [x] Color contrast in CI (added to ci.yml)
- [ ] DB backup/restore runbook
- [ ] Incident response runbook
- [ ] API versioning strategy
- [ ] DB migration rollback tested

## Held (Pending User Decision)
- [ ] Hosting provider (Render/Fly/Railway/Vercel)
- [ ] Billing provider (Stripe/Razorpay)
- [x] Email verification (backend: model + migration + endpoints; email sending pending provider) provider
- [ ] Interactive departure board (feature flag vs immediate)

## Findings Store
- 832 events, 395 findings (362 closed, 6 deferred, 27 open)
- All 27 open findings are P3 except FND-0368 (P1)

## Test Status
- Backend: 5,729 tests collected. Full suite has order-dependent failures.
- Frontend: typecheck clean, lint 0 errors/64 warnings, build succeeds.
- mypy: only scoped files checked (not whole repo).
