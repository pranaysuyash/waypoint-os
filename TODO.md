# Waypoint OS — Actionable Todos

**Generated**: 2026-04-30
**Priority**: P0 = customer conversations first (per Ayse advisory call)

---

## P0: Must Do (Next 14 Days) — Customer Discovery

- [ ] **Send 50 LinkedIn connection requests to travel agency owners** (7-10 days, not 10-20)
- [ ] Lead list tracked in Google Sheet: https://docs.google.com/spreadsheets/d/1voQUxncEqXPF36wrr7fdDkKj5YETh2Cv0X-mKJZZs-0/edit?gid=0
- [ ] Target: small outbound leisure agencies in India, custom itineraries, WhatsApp-heavy
- [ ] DM the ones who accept — "15-min chat? No pitch, learning the workflow."
- [ ] Run 7-10 calls minimum
- [ ] Track TWO tracks per call: inquiry intake pain + follow-up/lead leakage pain
- [ ] Add commercial questions: inquiry volume, booking value, response time sensitivity
- [ ] Capture exact words they use (this becomes your positioning)
- [ ] After 10 calls: decide based on clear pattern (6+ same pain) or pause

## P1: After Customer Discovery

### Product / Launch

- [ ] Decide: waitlist vs live signups for initial launch
- [ ] Update landing page CTA from "Book a demo" to appropriate phase
- [ ] Set up Stripe billing integration (monthly + annual)
- [ ] Implement 14-day trial gating
- [ ] Build pricing page with current plan structure

### Content / SEO

- [ ] Create Cloudflare R2 bucket `waypoint-blog` and configure rclone
- [ ] Create `tools/build-blog.py` — converts markdown → JSON → uploads to R2
- [ ] Create blog lib + blog listing page + individual post page in frontend
- [ ] Convert first 3 Tier 1 docs to blog posts (pick from: pricing research, competitive analysis, market overview)
- [ ] Add blog section to homepage between trust section and CTA band
- [ ] Set up meta tags + Open Graph on all pages
- [ ] Submit sitemap to Google Search Console

### Sales / Outreach

- [ ] Create simple CRM spreadsheet (name, agency, stage, next action, dates)
- [ ] Identify first 3 Facebook travel agent groups to join
- [ ] Join groups, spend 2 weeks answering questions (no pitching yet)
- [ ] Post first value-first content in FB group
- [ ] Start LinkedIn: update profile with Waypoint OS context
- [ ] LinkedIn: send 10 connection requests/week to travel agency owners
- [ ] LinkedIn: post 1 insight post/week (industry research-based)
- [ ] Write first 3 LinkedIn DM templates (connection note, welcome DM, follow-up)

---

## P1: Important (Next 60 Days)

### Product

- [ ] Build 1 add-on module (flight tracking recommended — most requested)
- [ ] Annual billing option with 20% discount
- [ ] Customer onboarding flow (guided setup → first inquiry processed)

### Content

- [ ] Write and publish 5 more blog posts (convert Tier 1 docs)
- [ ] Weekly posting cadence established
- [ ] Create free itinerary checker as wedge (already exists, promote it more)

### Sales

- [ ] Get first 5 paying customers
- [ ] Monthly check-in email sequence for active users
- [ ] Start referral conversation with first happy customer
- [ ] Qualify and reach out to first host agency

### Side Project Sustainability

- [ ] Set up 10-15 hrs/week schedule (see SIDE_PROJECT_PLAYBOOK.md)
- [ ] Keep 6 months of fixed costs (₹36K) in bank before spending on growth
- [ ] Automation: billing, reporting, email sequences

---

## P2: Future (60+ Days)

### Product

- [ ] Additional add-on modules (price intelligence, traveler portal)
- [ ] Usage-based seat pack pricing finalized
- [ ] API access for larger agencies

### Content

- [ ] Convert 50+ docs to blog posts
- [ ] Tag/category system on blog
- [ ] RSS feed for blog
- [ ] Monitor Google Search Console for keyword performance

### Growth

- [ ] Affiliate program (manual, after 50 customers)
- [ ] Host agency partnership program
- [ ] Paid acquisition (after 50 paying customers, LTV/CAC confirmed)
- [ ] Evaluate: keep side project, go full-time, or sell

---

## Event Log & Snapshot Audit — Task Candidate Disposition (2026-05-03)

| TC | Task | Disposition |
|----|------|-------------|
| 01 | Append-only event log with spec shape | Done — AuditStore JSONL + `_EventTrackingDict` |
| 02 | Event replay to materialize CanonicalPacket | Deferred (see below) |
| 03 | Contradiction lifecycle state machine | Done — `ContradictionState` + 4 transition methods |
| 04 | Hypothesis lifecycle state machine | Done — `HypothesisState` + 5 transition methods |
| 05 | UI audit trail (who/what/why/where) | Done (2026-05-04) — `actor`/`reason`/`pre_state` on `TimelineEvent`. Had been claimed done but `actor` field was absent from model until May 4 fix. |
| 06 | Value-to-event lineage tracing | Done — `old_value`/`new_value` in events + `Slot.evidence_refs` |
| 07 | Align in-memory events with spec shape | Done — spec updated to match actual event format |
| 08 | Verify append-only semantics enforced | Done — JSONL per AuditStore, append-only per `run_events` |
| 09 | Verify "no silent mutations" guarantee | Done — `_EventTrackingDict` on all three dict layers |
| 10 | Consolidate three parallel event systems | Deferred (see below) |
| 11 | Add FIELD_EXTRACTED/FIELD_OVERWRITTEN/etc types | Done — spec reconciled; `fact_set`/`contradiction_resolved` exist |

## Static Codebase Reality Check — Resolution Detail

| TC | Original Gap | What Changed | Files |
|----|-------------|--------------|-------|
| 01 | No single system matches full spec shape | JSONL AuditStore + `_EventTrackingDict` on `facts`/`derived_signals`/`hypotheses`. Every dict mutation emits event with `field_name`/`old_value`/`new_value`. Spec updated to match. | `spine_api/persistence.py`, `src/intake/packet_models.py` |
| 02 | No replay mechanism | Claim removed from spec. Fresh extraction per run is correct for single-run pipeline. Deferred with revisit trigger in TODO. | `specs/event_log_and_snapshot_model.md` |
| 03 | Contradiction detection only, no lifecycle | `ContradictionState` enum (`detected`/`open`/`resolved`). `add_contradiction()` stores state. `open_contradiction()`, `resolve_contradiction()`, `reopen_contradiction()` with event emission. | `src/intake/packet_models.py` |
| 04 | Hypotheses dict only, no lifecycle | `HypothesisState` enum (`proposed`→`active`→`validated`/`rejected`→`stale`). `set_hypothesis()` auto-inits PROPOSED. `activate/validate/reject/stale` methods with event emission. | `src/intake/packet_models.py` |
| 05 | Backend has data; frontend unverified | `actor` field added to `TimelineEvent` model, mapped from AuditStore `user_id`. Also added to `spine_api/contract.py`, `server.py` endpoint (both paths), frontend types, and `TimelinePanel.tsx` render. | `src/analytics/logger.py`, `spine_api/contract.py`, `spine_api/server.py`, `frontend/src/types/generated/spine-api.ts`, `frontend/src/components/workspace/panels/TimelinePanel.tsx` |
| 06 | Lineage at Slot level only | Events now carry `old_value`/`new_value` per mutation. Combined with `Slot.evidence_refs` (`envelope_id`, `evidence_type`, `excerpt`), the full value→source chain is traceable. | `src/intake/packet_models.py` |
| 07 | In-memory events use `event_id: int`, no `packet_id`/`actor` in payload | Spec updated to reflect actual shape: `{event_id, event_type, timestamp, details.{field_name, old_value, new_value}}`. The packet identity is implicit (events live on the packet). Actor is tracked at the `TimelineEvent` level. | `specs/event_log_and_snapshot_model.md` |
| 08 | File-based AuditStore not crash-safe | Converted from load-modify-save JSON array → atomic JSONL append (one line per event, append mode). Trim uses `write-to-tmp + os.replace`. 1317 tests pass. | `spine_api/persistence.py` |
| 09 | Direct `packet.facts["x"] = slot` bypasses events | `_EventTrackingDict.__setitem__` fires event on every write. `__delitem__` fires on removal. No convention required — enforced by architecture. | `src/intake/packet_models.py` |
| 10 | Three parallel event stores | Boundaries documented in spec: `CanonicalPacket.events` (field-level, in-memory), `AuditStore` (business-level, global JSONL), `run_events.jsonl` (pipeline-level, per-run). Consolidation deferred. | `specs/event_log_and_snapshot_model.md` |
| 11 | Spec event types not used in code | Spec updated to use actual event types: `fact_set`, `derived_signal_set`, `hypothesis_set`, `contradiction_detected`, `contradiction_resolved`, `contradiction_opened`, `contradiction_reopened`, `hypothesis_activated`, `hypothesis_validated`, `hypothesis_rejected`, `hypothesis_staled`. `CONTRADICTION_RESOLVED` exists as `contradiction_resolved`. | `specs/event_log_and_snapshot_model.md` |

## Issue Register — Resolution Detail

| Issue | Verdict | Acceptance Criteria Met |
|-------|---------|------------------------|
| ISSUE-001 Three parallel systems | **Resolved** | Boundaries documented in spec. `CanonicalPacket.events` = field-level source of truth. `AuditStore` = business-level. `run_events` = pipeline-level. Consolidation deferred. |
| ISSUE-002 No event replay | **Deferred** | Spec rewritten: "Fresh extraction per run is the canonical approach." Replay deferred to TODO with revisit trigger. |
| ISSUE-003 Contradiction lifecycle | **Resolved** | `ContradictionState` enum (`detected`/`open`/`resolved`). `add/open/resolve/reopen` methods. `contradiction_resolved` event emitted. `state`, `resolved_at`, `resolution`, `resolved_by` fields stored. |
| ISSUE-004 Hypothesis lifecycle | **Resolved** | `HypothesisState` enum (`proposed`/`active`/`validated`/`rejected`/`stale`). `set_hypothesis` auto-inits PROPOSED. `activate/validate/reject/stale` methods. Events: `hypothesis_activated`, `hypothesis_validated`, `hypothesis_rejected`, `hypothesis_staled`. |
| ISSUE-005 Event shape drift | **Resolved** | Approach (b) selected: spec documents two-level provenance — events carry `field_name`/`old_value`/`new_value`; `Slot.evidence_refs` carry `envelope_id`/`evidence_type`/`excerpt`. Together they provide full audit trail without schema changes. |
| ISSUE-006 Silent mutations | **Resolved** | `_EventTrackingDict.__setitem__` fires event on every dict write. `__delitem__` fires on removal. Enforcement is architectural, not convention-based. Any code path — `set_fact()` or direct `packet.facts["x"] = slot` — emits an event. |
| ISSUE-007 UI audit trail | **Resolved (2026-05-04)** | `actor` was missing from both `logger.py` model and mapper. Fixed: added to `TimelineEvent` Pydantic model + mapper extracts `user_id` from audit events. Frontend `TimelinePanel` now renders actor line. All 4 dimensions (who/why/where/previous) present in API response. |
| ISSUE-008 Event type naming | **Resolved** | Spec updated to match actual event type vocabulary. No code changes needed — types were always correct, just documented differently. |
| ISSUE-009 AuditStore atomicity | **Resolved** | Converted from load-modify-save JSON array → atomic JSONL append. `log_event` = one `f.write(line + "\n")` per call. Trim uses `write-to-tmp + os.replace` (non-destructive on crash). Legacy `events.json` auto-migrated to `events.jsonl`. |

## Deferred from Event Log & Snapshot Audit (2026-05-03)

These were identified as spec claims during audit of `specs/event_log_and_snapshot_model.md`.  
The current implementation is architecturally superior for the single-run pipeline model.  
Revisit if/when the system moves to a multi-stage persistent state model.

- [ ] **Event replay for CanonicalPacket** (DI-03/DI-04) — Spec claimed "state is materialized by replaying the event log."  
  Current: fresh extraction per run via `ExtractionPipeline.extract()`. This is correct for the single-run model.  
  Deferred because: no use case yet for time-travel debugging or cross-run state reconstruction.  
  Trigger to revisit: when runs need to resume from a prior checkpoint rather than re-extracting from raw input.

- [ ] **Three event system consolidation** (ISSUE-001) — `CanonicalPacket.events`, `AuditStore`, `run_events.jsonl` serve different scopes.  
  Current: boundaries documented in spec. Each system covers a distinct need (field-level, business-level, pipeline-level).  
  Deferred because: consolidation would touch 81+ call sites with no user-facing benefit.  
  Trigger to revisit: if a single unified log becomes needed for compliance or cross-system querying.

- [ ] **CanonicalPacket event shape expansion** (DI-02/ISSUE-005) — In-memory events use `{event_id, event_type, timestamp, details}` rather than the full spec shape with `actor`, `packet_id`, structured `payload`.  
  Current: `details` carries `field_name`/`old_value`/`new_value`. `Slot.evidence_refs` provides provenance.  
  Deferred because: the two-level provenance (events + evidence refs) covers all audit trail questions without schema changes.  
  Trigger to revisit: if a consumer needs the full spec shape in a single event without joining data.

## References

| Resource | What It Covers |
|----------|---------------|
| `Docs/SIDE_PROJECT_PLAYBOOK.md` | Side project schedule, milestones, go full-time signals |
| `Docs/CONTENT_ARCHITECTURE.md` | R2 JSON dump setup, build script, frontend pages |
| `Docs/CONTENT_SEO_STRATEGY.md` | Keyword targets, promotion channels, publishing cadence |
| `Docs/SALES_MARKETING_FIT.md` | FB group outreach, founder sales flow, ICP |
| `Docs/SAAS_PLAYBOOK.md` | Objection scripts, conversation flows, weekly cadence |
| `Docs/REVENUE_FIRST_GROWTH_APPLICATION.md` | Customer-funded dev, annual billing, cash reserves |
| `Docs/PRICING_REVENUE_AUDIT_2026-04-29.md` | Full pricing audit |
| `tools/financial_model_v7.py` | Side project financial model |

## Tools Created

| Tool | Purpose |
|------|---------|
| `tools/financial_model_v1.py` through `v7.py` | Financial models (v7 = current side project version) |

## Model Versions

| Version | File | Best For |
|---------|------|----------|
| v7 | `financial_model_v7.py` | **Current** — side project mode |
| v6 | `financial_model_v6.py` | Startup mode with PLG + retention feedback |
| v1-5 | `financial_model_v*.py` | Archived baselines |
