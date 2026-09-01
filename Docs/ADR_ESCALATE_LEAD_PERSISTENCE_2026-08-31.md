# ADR: ESCALATE Inquiries Persist as Incomplete Leads

*ADR-2026-08-31-01 · Status: Accepted (implemented) · Decides the open question in `Docs/exploration/DEMO01_LEAD_ROUTING_GAP_2026-08-31.md` §8 Q1–Q3*
*Supersedes the implicit stance at `src/intake/validation.py` INTAKE_MINIMUM comment ("Fields that MUST be present to even save an intake trip").*

---

## 1. Context

A live persona demo (`Docs/SIMULATED_PRODUCT_DEMO_TOOL_TASTER_2026-08-31.md`) exposed a P0: when the NB01 intake gate returns **ESCALATE** (intake minimum — `destination_candidates`, `date_window` — unmet), the pipeline's `early_exit` branch blocks the run, marks the draft `blocked`, and returns **without persisting anything the Lead Inbox can see**. The banner promises "incomplete leads appear in Lead Inbox"; the inbox shows 0 leads; the blocked draft is unreachable from any navigation surface. The first-run loop dead-ends silently.

## 2. The Decision, From First Principles

**Question:** is a blocked inquiry a business record (a lead), or not-yet-a-record?

1. **The real-world object.** The moment a prospect sends *any* message expressing travel intent, a lead exists in the world — someone contacted the agency with intent, and someone must follow up. Data quality is an *attribute* of the lead (its completeness), not a *precondition* for its existence. Every agency CRM (Travefy, Tern, TravelJoy) models the contact as primary and enriches details progressively.
2. **The product's own promise.** The landing page: "turn the notes they already have — calls, emails, WhatsApp messages — into one clean brief." The mouth of this funnel is, by design, *messy input*. A pipeline that discards input below a completeness bar contradicts the product's core value proposition. (The demo's casual note — "want to do japan next spring" — is exactly how real customers write.)
3. **Separation of concerns.** Validation owns *epistemics*: what we may claim to know (quote-ready vs not). Persistence owns *existence*: whether an event happened (a customer made contact). The current code fuses the two — NB01 ESCALATE decides both "not quote-ready" *and* "never happened." Gates should gate the quote, not the record.
4. **The system already disagrees with itself.** The inbox read model was *designed* for leads missing basics: `GET /inbox/stats` carries a `missingTripBasics` counter, unknown-value filters, and an `incomplete` flag (`spine_api/routers/inbox.py:161-172`). The DEGRADE path already persists trips missing `trip_purpose`, `party_size`, and `budget`. The write-side "don't save" stance is the anomaly, not the rule.
5. **Failure-mode asymmetry.**
   - *Drop (current):* silent data loss — the worst class in this repo's data-integrity doctrine. The prospect's words vanish into an unreachable draft. Cost: a lost sale, invisibly.
   - *Save as incomplete:* possible inbox noise if extraction degrades. Cost: agent attention, visibly, triageably. An agency deleting junk from an inbox is a normal act; an agency never learning a prospect asked is not.
   - Asymmetric risk ⇒ save.
6. **Epistemic integrity is preserved.** `status="incomplete"` + the validation report on the trip + unchanged NB01 gates mean we do not claim to know what we don't. We claim only that a contact happened — which is true. This is an *explicit* state, not a dummy fallback (honors "No Dummy Fallbacks: operate on real inputs or explicit error states").
7. **Long-term coherence.** Wave-2/3 autonomy (auto-follow-ups, disruption healing, margin capture) requires durable lead entities with *known gaps* to act on. Draft→trip 1:1 also makes the existing trip repair surface (`/trips/{id}/intake`) reachable for blocked inquiries — one decision unlocks the repair loop (DEMO-06's structural dead-end).

**Decision:** on ESCALATE, persist the inquiry as a **Trip with `status="incomplete"`** through the canonical `save_processed_trip` path, link it to the draft, and make draft-scoped reprocessing update the same trip (idempotent). QUOTE_READY gating is unchanged — an incomplete lead can never be treated as quote-ready.

## 3. Resolved Sub-Decisions

| Question | Decision | Rationale |
|---|---|---|
| Status label | Reuse `incomplete` (no new enum) | Inbox already projects it; the *reasons* for blockage travel in the packet/validation data, not the status. Simpler surface, richer payload. |
| Draft state on ESCALATE | Keep `blocked` + record `linked_trip_ids` | `promoted` is terminal; the draft remains the repair workspace until the inquiry completes. **ESCALATE never overwrites an existing trip**: when a preserve target exists (auto-reassess-on-edit `target_trip_id`, or a draft's linked trip), the save is skipped — the early-exit packet is definitionally incomplete and must never replace a live record. The run still blocks; the linkage and `trip_id` still propagate. |
| DEGRADE / success reprocess | Same linked-trip resolution | Same bug class (draft reprocess duplicated trips), same module, same pass (blast-radius rule); preservation of current status via `trip_store.get_trip`. |
| Strict-leakage / defense-in-depth blocks | Still persist nothing | Policy refusals, not intake gaps — different semantics, out of scope. |
| Inbox noise guard | Deferred | `incomplete` flag + `missingTripBasics` stat + priority sort suffice today; revisit a "Needs basics" filter tab on real noise signal. |
| Dead linked-trip ids | Never reused as preserve targets | If `trip_store.get_trip` misses, the resolution returns nothing and a fresh lead is created — no resurrection of deleted ids. |

## 4. Consequences

- **Positive:** the funnel mouth no longer leaks; the banner promise becomes true; blocked inquiries gain a recovery surface; E2E loop (process → blocked → inbox → repair → reprocess) completes; reprocess idempotency for all draft paths.
- **Costs/risks:** degraded extraction can now produce low-signal inbox rows (accepted, monitored via `missingTripBasics`); trips with no destination/date exist in analytics counts (they were already possible via DEGRADE — this widens the population slightly).
- **Neutral:** no schema change, no new routes, no parallel read model (no-duplicate-systems rule honored).

## 5. Verification Standard

Risk-Class: high (lead lifecycle), Evidence-Tier 3: contract-driven E2E — fresh tenant → process note missing basics → blocked → `GET /inbox` shows the lead → workbench banner names the missing fields → reprocess updates the same trip (no duplicate). Plus pytest coverage of the ESCALATE branch, reprocess idempotency, and ledger-failure isolation.
