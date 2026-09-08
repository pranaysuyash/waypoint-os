# EX-03 — KPI Trust Model Research: Client-Fed Funnel Events (2026-09-08)

Status: research + options. Feeds D-03 follow-on and any KPI-of-record claim. Related: AUD-03 (P1).

## Problem (verified)

`/api/public-checker/events` is unauthenticated, accepts up to 30 events/min/IP with 16 KiB envelopes, and `compute_kpis` (`spine_api/product_b_events.py:462-510`) aggregates whatever arrives: time-to-first-credible-finding p50/p90, qualified-inquiry counts, forwardability. A bot posting valid `intake_started` + `first_credible_finding_shown` with fabricated `session_id`/`inquiry_id` and arbitrary `time_from_intake_start_ms` directly controls the launch KPI of record. No origin binding, no session verification, IP-rotatable. Store-side validation (`:50-130,213-297`) bounds *shape*, not *truth*.

## Why it matters

Every launch/readiness document that cites funnel KPIs inherits this trust gap. A poisoned store cannot be distinguished from a real one retroactively — the store has no integrity boundary. The 2026-09-01 GTM assessment could identify synthetic traffic only by *signature analysis* (workspace ids, empty destinations), which is forensic, not preventive.

## Options

**Option 1 — Server-derived funnel counters (recommended).** The run endpoint already sees everything the funnel needs: intake received, extraction result, findings, blockers. Emit `intake_started`/`first_credible_finding_shown` server-side inside `run_public_checker_submission` (actor_type `system`, channel `api` — the enum already supports exactly this) keyed by server-issued session ids. Client events shrink to interaction-only signals (`action_packet_copied/shared`, revision reports) where fabrication is low-value noise, not KPI-defining. Cost: moderate (service-layer emission + KPI redefinition per ADR-007 addendum). Breaks nothing: event schema unchanged, only the emitter moves.

**Option 2 — Origin/session binding for client events.** Server issues a signed funnel-session token on `/run`; `/events` requires it; per-session event caps enforced server-side. Keeps client telemetry as-is, adds one token round-trip. Weaker than Option 1 for KPI truth (a bot can still run `/run` to get tokens — 12/min rate limit is the only brake) but preserves client-side interaction fidelity.

**Option 3 — Accept and document.** Mark all product-B KPIs "untrusted-by-construction, directional only" in ADR-007 and downstream docs. Zero code. Viable only while the surface has no exposure and no KPI-linked decisions — which is today, but stops being true the moment Option B (wedge inversion) or any launch proceeds.

## Recommendation

Option 1 for KPI-defining events, Option 2's session token as a follow-on if interaction-event fidelity ever matters. Sequenced behind D-01: if the wedge inverts to agency-branded, KPI definitions change anyway (per-tenant funnels) — build the trusted emitter once, on the new definitions.

## Falsifier

If server-side emission cannot reconstruct `time_from_intake_start_ms` honestly (e.g., intake streaming makes server timestamps meaningless), Option 2 becomes primary. Verified premise: the run endpoint processes synchronously and knows intake→result timing (`RunStatusResponse.total_ms` exists).
