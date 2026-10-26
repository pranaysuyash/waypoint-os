# DECIDE-Queue Packet — 2026-10-25

> **DECISION RECORD (2026-10-25, delegated authority per owner directive).** The owner corrected
> the framing mid-wave: doctrine-decidable items are the agent's to DECIDE + document + implement,
> with a revisit trigger — not to park on the owner ("stop pinning up on me"; delegated-authority
> memory: reversible design decisions are the agent's; only money/irreversible/git/ADR-posture
> escalate). Applied below: items 2–4 are **DECIDED** (doctrine dictates each); item 1 (E1) is
> **DECIDED B+D** on the evidence (channel choice is reversible — adapters are flag-gated, link
> fallback permanent). Every decision carries its revisit trigger. Owner ratification is no longer
> requested; dissent amends the record.

**Provenance:** compiled from the launch-readiness product council
([LAUNCH_READINESS_TASK_INVENTORY_2026-09-29.md](LAUNCH_READINESS_TASK_INVENTORY_2026-09-29.md)),
the 2026-09-30 wave-2 tranche, the E1 channel research
([E1_ASK_TRAVELER_CHANNEL_2026-09-29.md](../exploration/E1_ASK_TRAVELER_CHANNEL_2026-09-29.md)),
and the 2026-10-25 Jev session. Every claim re-verified against the tree today (file paths cited).
**Purpose:** convert each owner DECIDE into a one-line ratification by carrying the options,
recommendation, evidence, and falsifier for each. Nothing here changes runtime behavior —
ratification does.

**Ratify format:** per item, one line, e.g. `E1: B+D` / `retention: archive` / `T12: defer-pending-E1`
/ `T15: verify-then-consolidate`.

---

## 1. E1 — Ask-traveler channel architecture (highest leverage)

**Decision asked:** which channel(s) become the primary ask-traveler surface going forward.

**Current state (verified today):**
- Option A (shareable token link, `/a/{token}`) is **shipped and live** — zero approvals needed, operators can send asks today (`message_dispatch.py` honest-adapter pattern).
- WhatsApp/email dispatch adapters exist (`src/services/message_dispatch.py`, honest `NOT_CONFIGURED` until provider creds) — channel addition is config + Meta verification, not new architecture.
- **New since E1 was written (2026-10-25 Jev session):** Option D's blocker — free-text reply parsing quality — is now **measured and passing** (E2 both gates: routing 1.000, zero wrong-field, zero silent drops incl. Hinglish and implicit answers; `src/intake/ask_reply_router.py` productionized, flag-gated). Option D is buildable the moment G2 clears and the flag is ratified on.
- WhatsApp rates remain **UNVERIFIED** (retried the Meta pricing page today — login-walled; E1's numbers stay directional until confirmed in the Meta console).

**Options:**
- **A-only** — safest, zero cost, but "click a link" friction on WhatsApp-first Indian travelers.
- **B (WhatsApp Cloud API primary)** — de-facto channel for India travel planning; adapter exists; needs Meta business verification + 2–3 approved templates; adds per-message cost (unverified numbers).
- **B+D (recommended)** — B as primary channel, with in-thread replies parsed by the E2-proven router as proposal-only write-back (extractor re-validates; sub-0.60-confidence routes to operator review).
- **C email** — proposal-stage formality lane, already supported by SendGrid adapter.

**Recommendation:** **B+D.** Sequence: start Meta business verification now (longest lead item, falsifier below), enable B behind the existing dispatch adapter, enable D behind `JEV_ASK_LOOP_ENABLED` + G2 when ratified. C stays the proposal/formality lane. A remains the universal fallback.

**Falsifier (carried from E1):** if Meta verification + template approval exceeds ~2 weeks of elapsed time for the pilot agency, link-only (A) stays primary and B demotes to parallel work.

**Owner action:** ratify channel posture → unlocks Meta verification start + template drafting.

---

## 2. retention_enforcer — wire-or-archive (T14 residual)

**Decision asked:** enforce the declared retention SLAs, or stop declaring them.

**Current state (verified today):**
- `src/security/retention_enforcer.py` is, by its own header, a **shadow prototype**: "does *not* enforce retention in a running product… The certificate is not proof that any backing data was deleted." Zero non-test importers.
- The actual enforcement path that **is** shipped: DSR-driven traveler data rights — `spine_api/services/trip_dsr.py` + `spine_api/routers/dsr.py` (Art. 15/20 portable export, Art. 17 structural erasure with PII scrub + message tombstones, audit chain preserved, fail-closed GDPR signing, 5/5 tests at ship time).
- Council framing that still stands: *jurisdiction_policy declares SLAs with zero enforcement — either enforce the declared policy or amend the policy (never leave the lie).*

**Options:**
- **Wire as automatic time-based enforcement** — requires a canonical, tenant-scoped, durable deletion workflow across TripStore/BookingDocuments/MemoryStore/audit/external providers with operator-controlled audit, retry, reconciliation, recovery (the enforcer's own header names this bar). Large build; duplicates the shipped DSR path for the on-request case.
- **Archive + amend (recommended)** — retire the shadow module from the runtime posture (per its own recommendation), keep the schedule/certificate design probe documented, and amend `jurisdiction_policy` wording so the *declared* commitments reference DSR-driven deletion (shipped, real) rather than implying automatic sweeps (nonexistent).
- **Keep shadow** — honest per docstring but leaves the declared-SLA ambiguity the council flagged.

**Recommendation:** **Archive + amend.** The product's erasure guarantee should be the shipped, operator-gated DSR path — not a cron that silently deletes traveler data nobody can audit. Automatic retention sweeps can be re-proposed later against the DSR substrate if a jurisdiction demands time-based deletion.

**Owner action:** ratify archive+amend → small PR retiring the module's runtime posture + policy wording fix; closes the last T14 residual.

---

## 3. T12 / D09 — Pre-departure scheduled cadence trigger

**Decision asked:** add scheduled D-7/D-3/D-1 push briefings, or keep briefings on-demand only.

**Current state (verified today):**
- The council's "orphaned" claim is **refuted**: `spine_api/routers/pre_departure.py` is mounted (`server.py:1688–1689`, auth-gated) with JSON + PDF bundle endpoints calling `PreDepartureCadenceEngine`, honest "Reality boundary" labeling. On-demand preview is real.
- The residual gap is exactly the **scheduled push trigger** (D-7/D-3/D-1 automatic dispatch) — it doesn't exist, and push requires a ratified outbound channel (item 1).

**Options:**
- **Wire scheduled trigger now** — needs E1 channel + a scheduler surface; premature before channel ratification.
- **Defer-pending-E1 (recommended)** — keep the on-demand surface (already live), queue the scheduled trigger as the first consumer of the ratified WhatsApp lane; archive the "gap" label since the serving path exists.
- **Archive the cadence ambition entirely** — lose the natural post-proposal value surface.

**Recommendation:** **Defer-pending-E1.** One decision (E1) unlocks this; sequencing them avoids building a push trigger against an unratified channel.

**Owner action:** ratify defer → update inventory row; T12 closes as "serving path live, cadence trigger gated on E1."

---

## 4. T15 / FND-0184 — Group consensus binding (verify-then-consolidate)

**Decision asked:** consolidate the two consensus engines into one binding authority, or archive the lane.

**Current state (VERIFIED today, read-only pass):**
- **Both engines are serving-wired, and neither binds.** `src/decision/group_consensus.py` (`GroupConsensusOptimizer`) is imported by `spine_api/routers/counterfactual.py:24` and served at `POST /group-consensus` (`:96`, calls `evaluate_group_consensus`). `src/decision/group_pareto_engine.py` backs the separately-mounted `spine_api/routers/group_pareto.py`. A binding-language sweep (`bind|binding|commit`) across both engines returns **zero hits** — FND-0184's "neither binds booking" is confirmed, and the two-engines-two-routers duplication is real (FND-0184's registration also narrows: this is not an orphan question, both have callers).

**Options:**
- **Verify-then-consolidate** — ✅ verification half done (above). Remaining: consolidate to **one** engine emitting a binding artifact (consolidation doctrine), migrate the second router or fold it in, archive the redundant engine via the supersession workflow, then wire the binding artifact into the booking gate.
- **Archive the lane** — no longer the honest option: both engines have live serving paths, so this would be removing mounted surface, not retiring an orphan.

**Recommendation:** **Consolidate** (verification complete; disposition is the ratifiable part). Two mounted engines answering the same question differently is drift by construction; one binding authority is the fix. Owner ratifies the target engine + whether binding enters the booking gate now or post-launch.

**Owner action:** ratify the path (verify-then-consolidate vs archive) → verification run is unblocked either way.

---

## 5. Stale DECIDE-row corrections (no decision needed — recording truth)

- **T10 / FND-0233 is no longer a DECIDE** — decided and shipped 2026-09-30: system **never moves money** (tracking-only, permanent boundary enforced by `test_no_payment_code_paths`), 8-state `claim_disposition` machine + GET/PATCH on the passenger-rights router + `ClaimDispositionCard` shipped (11/11 + 5/5 + FE 22/22 green at ship). FND-0233 closed with the owner-called blast-radius correction noted in-store. Inventory line "T10/T11b/T12/T15 + E1 channel choice | Owner DECIDE" is stale for T10 and for the items this packet covers.
- **T11b step 2** (ghost-concierge lifecycle entry + healer chain + workflow truth-up) is an *implement* task anchored in pack §7, not a DECIDE.
- **Two DECIDE items I cannot re-derive from the tree** — the 09-30 session summary lists "hypothesis" and "gap-doc-archive" as DECIDE-queue members, but neither appears in the launch inventory, the findings store's open set, or any governing doc I can find today. They may live in that session's summary only. Flagged here for the owner: if these matter, point me at the artifact that defines them and I'll fold them into this packet; otherwise treat the live queue as items 1–4 above.

---

## Verification trail

| Claim | Evidence |
|---|---|
| E2 Option D parsing quality | `data/experiments/hybrid_kdd_v1/ask_loop_probe_receipt.json` (2026-10-25, both gates pass) |
| Reply-router substrate | `src/intake/ask_reply_router.py` + `tests/test_ask_loop_services.py` (flag-gated, default off) |
| retention_enforcer shadow posture | `src/security/retention_enforcer.py` header (verbatim, this day) |
| DSR shipped | `spine_api/services/trip_dsr.py`, `spine_api/routers/dsr.py` |
| Pre-departure router mounted | `spine_api/server.py:1688–1689` |
| Two consensus engines | `src/decision/group_consensus.py`, `src/decision/group_pareto_engine.py`, `spine_api/routers/group_pareto.py` |
| WhatsApp rates unverified | Meta pricing page login-walled (retried 2026-10-25); E1 doc's UNVERIFIED marker stands |
