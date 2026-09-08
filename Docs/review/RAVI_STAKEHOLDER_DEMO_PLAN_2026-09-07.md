# Stakeholder Demo Plan — "Ravi" (proprietor travel agent) — 2026-09-07

> **STATUS: DRAFT — the meeting is not yet confirmed by Ravi.** Treat everything below as prepared-in-anticipation, not as a commitment made on his behalf. "Ready" here means **source-level + test-level verified only**: browser-executed walkthrough (L7), the commit gate on the uncommitted tree, and the morning pre-flight (§3) are still the minimum bar before any demo claim. Do not present the app as demo-ready until §3 passes the same day.

**Purpose:** the app must be ready for a working session with Ravi — a travel agent who runs his own proprietorship — if/when the meeting is confirmed this week. This plan makes the demo honest, smooth, and discovery-productive. It builds on the PER-0443 audit + register (same date) and assumes **nothing is committed yet** (see pre-flight #1).

**Posture:** invite-only stakeholder demo. Public/paid launch remains **NO-GO** (`Docs/LAUNCH_STATUS.md` L1–L8); this demo neither claims nor requires launch readiness.

---

## 1. Who Ravi is and what he will judge (Observed domain research, sources in session evidence doc)

A proprietor travel agent's day: inquiries (mostly WhatsApp/phone), quotations and itinerary drafts, follow-ups, booking via a **consolidator** (TBO/Mystifly) rather than direct GDS (IATA accreditation is rare at this scale), invoicing, **payment collection and chasing**, and **commission tracking** across suppliers. India-specific tools he likely uses today: Zoho CRM, TravoByte/CRMtravel/TraviYo, Excel, WhatsApp Web.

**What he will implicitly test in 10 minutes:**
1. "Does this understand how I actually work?" (intake → quote → follow-up → booking → money)
2. "Can I trust what it shows me?" (no invented prices/availability)
3. "What does it do that my current CRM doesn't?" (the honest answer must be real: durable client e-sign acceptance, audit trail, disruption watch, commission reconciliation)

## 2. Demo script (60 min, in this order)

| # | Beat | Surface | Point being made | Guardrail |
|---|---|---|---|---|
| 1 | Natural-language intake | `/workbench` → new inquiry | Colloquial note → structured trip packet with gates (NB01/NB02) | Use a real seeded trip, not live typing, unless tested |
| 2 | Proposal compile | Workbench → Proposal Compiler | Deterministic pricing preview in seconds | **Keep the SIMULATION badge visible and frame it**: "deterministic engine; provider feeds are the next milestone — it refuses to pretend otherwise" |
| 3 | **Client e-sign acceptance** | `/p/[token]` real share link on a phone | The differentiator: signed, durable, auditable client acceptance — survives restarts, replay-safe | Generate the token fresh that morning; verify the link renders BEFORE he arrives (AT-20 fix makes invalid links abstain honestly) |
| 4 | Decision transparency | Trip → decision page | Every number carries its rationale and reality tier; hybrid LLM is opt-in, off by default | Do not enable the hybrid engine mid-demo |
| 5 | Traveler companion | `/companion?tripId=…&token=…` | Client-facing itinerary view that abstains instead of inventing PNRs | Token-gated; abstention screen is a feature — say so |
| 6 | Money & ops honesty | Commission reconciliation + financial ops views | "We track supplier commissions and settlement splits" (module: `commission_reconciliation`, IDEA-124) | Present as operational backbone, not a live bank feed |
| 7 | Discovery questions | Conversation | Fill D-01…D-03 + §5 gaps | See §5 |

**Do not show / do not claim:** Persona Council simulators (Journey Graph/IROPS/Document MRZ panels are panel-badged simulations — skip or explicitly frame as simulators); any auto-booking ("nothing books without a human — by design"); live GDS/NDC availability; insurance as a carrier (preview only); loyalty balances; auto-rebooking on disruption (R1 human-approved, per ADR-008 posture); legacy landing routes `/v2`–`/v5` (still routable, don't navigate there).

## 3. Pre-flight checklist (run the morning of the meeting, in order)

1. **Commit the tree first** (owner-gated): 60+ modified files hold the entire honesty remediation (PER-0700 Phase 0–2 + PER-0443 OS-layer + AT-20). An accidental `git checkout`/stash silently reverts all of it. Run `uv run ruff check .` then commit per repo gate protocol — commit needs explicit owner authorization, so do this before the meeting, not during.
2. Backend: `cd spine_api && TRIPSTORE_BACKEND=sql uv run uvicorn spine_api.server:app --port 8000` — verify `curl -s http://localhost:8000/health` = 200 and `/metrics` = 200.
3. Frontend: `cd frontend && npm run dev -- -p 3005` — verify `curl -s -o /dev/null -w "%{http_code}" http://localhost:3005` = 200.
4. Seed/warm: one demo trip end-to-end (intake → compile → accepted via real token), open `/inbox` once (past crash history), open `/p/[token]` once, open `/companion` once with the real token.
5. Auth posture: confirm whether `SPINE_API_DISABLE_AUTH` is set; know which mode you're demoing (F-43 note: `/api/v1/*` and `/api/public/*` rewrites bypass the BFF allowlist — acceptable for a localhost demo, never expose this machine to the internet).
6. Phone on the same network for beat 3 (share link on mobile is the strongest moment).

## 4. Strengths to lead with (all verified in the working tree, evidence in register Part G)

- **Honesty as architecture:** reality tiers, SIMULATED badges, abstention instead of fabrication (companion, public proposal, loyalty, insurance). No competitor says "we refuse to invent availability."
- **Durable client acceptance:** signed share token → e-sign → durable, replay-safe record (PA-02; verified).
- **Human-gated autonomy:** intake gates never auto-suppressed; booking is always human-approved (AT-15 posture until ADR-008 ratified).
- **Commission reconciliation & split settlement** already built (IDEA-124) — a real proprietor pain point few tools solve well.
- **Disruption-aware journey model:** journey graph persisted per trip; IROPS previews operate on the traveler's actual stored itinerary (AT-01/AT-06 fixed, verified).

## 5. Discovery questions for Ravi (feeds the roadmap)

1. Where do inquiries come from and where do they die? (feeds NBA/commercial follow-up: AT-07 projection)
2. Current booking stack: TBO/Mystifly/consolidator portal/GDS sub-agent? (feeds provider connector priority — R-09/R-10 DECIDE)
3. How do quotes go out — WhatsApp? PDF? (feeds proposal export + WhatsApp channel DECIDE)
4. Payment rails: UPI/Razorpay/bank transfer/Stripe? (feeds financial_ops India-path DECIDE; AT-15 mandate work)
5. Commission models per supplier — flat %, net rates, overrides? (feeds commission_reconciliation realism)
6. Group/family bookings: how do you collect per-person decisions? (AT-14; per-pax accept on proposal token)
7. Visa/document handling today? (AT-11; DocumentReadinessAgent roadmap)
8. What did he check FIRST when evaluating competitor tools — mirror that question back.

## 6. Known demo risks (from register Part G verification)

| Risk | Mitigation |
|---|---|
| Uncommitted tree reverted by accident | Pre-flight #1 — commit before the meeting (owner-authorized) |
| `/p/[token]` expired-link moment | AT-20 now abstains honestly; still pre-test the real token (Pre-flight #4) |
| Accidental click into Persona Council simulators | Don't open the tab; if opened, the panel badge is the script line |
| `SPINE_API_DISABLE_AUTH` posture confusion | Pre-flight #5 — decide and note which mode |
| `/inbox` unknown runtime state | Warm it (Pre-flight #4) |
| a11y/small type on projector | Demo on the 3005 dev server at 100% zoom; text-[10px] labels are legible in person, not on screen-share — prefer in-person/phone beats |

## 7. After the meeting

- Log Ravi's answers into `Docs/exploration/` as a stakeholder-requirements note mapped to DECIDE rows (D-01…D-03, R-09/R-10, WhatsApp channel, India payments).
- Retry the codex external review (usage limit reset 18:09 IST 2026-09-07; command preserved in session evidence doc) and file its findings into the register as a Part H addendum.
- Promote AT-20 and Part G verification into `Docs/review/FINDINGS_REGISTER_2026-08-31.md` by additive append at the next register pass.
