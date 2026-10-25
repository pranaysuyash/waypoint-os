
## TRV-DP-01 (opened 2026-10-12 01:10 IST, nightly orchestrator): ownership of the dirty tree before nightly implementation
- **Context:** The tree has uncommitted work as recent as 2026-10-05 (sim3 tools, about 15 tests). The Codex register says the owner state is unclear. The nightly orchestrator wrote `Docs/audit/OPEN_ITEMS_AUDIT.md` and `IMPLEMENTATION_PLAN.md` but made no code changes.
- **Options:** A. Pranay names the current owner/session, and the nightly task does doc-only work here. B. Nightly may do plan items 1–2 (LAUNCH_STATUS receipt refresh, TODO-to-findings check), which are test/doc additions only. C. Hold everything.
- **Recommendation:** B for item 1 (refresh the evidence receipt) only after the in-flight sim3 work is classified. Otherwise A.
- **Also for decision:** root clutter list (audit TRV-N04), including classifying `dogfood_cookies.txt` (possible session secret; not opened). Fly CD on push while public launch is NO-GO (TRV-N05, already blocker 8).
- **Blocked:** IMPLEMENTATION_PLAN items 1–3.

## TRV-DP-02 (resolved 2026-10-21, authorized by operator):
- **Decision P-1 (Live Jev vs Heuristic Serving)**: Adopted Option A as standard default (Live Smart Assistant active automatically when credentials present, with zero-downtime heuristic fallback when absent or offline). Option B (higher limits / pro features) reserved for commercial packaging while ongoing local research, evaluation, and documentation proceed.
- **Decision P-3 (Statutory Airline Claim Processing)**: Adopted Option A as standard default (Software Helper: exact statutory compensation calculation and dispute letter generation under EC 261 / UK261 / US DOT / Montreal Convention Art. 19; airline pays traveler directly). Paid direct recovery representation reserved for future phase.
- **Decision P-4 (GDPR Art. 17 Erasure Depth)**: Adopted Option A (Recursive deep erasure of personal direct PII, contact info, and identity certificates while preserving non-PII aggregated bookkeeping/margin metrics).
- **Maintenance TRV-N04 (Root Clutter & Secret Hygiene)**: Adopted Option A (Temporary test databases `test_*.db` and `dogfood_cookies.txt` are confirmed `.gitignore` excluded to prevent accidental Git commits or leakages).

## TRV-DP-03 (opened 2026-10-21, Sim #4 council — owner decisions outstanding)
- **DP-03a (Dev privacy posture, FND-0326/P-1):** dogfood (fail-closed, refuses real-shaped leads) vs beta+key (encrypted, fail-open audit) as the DEFAULT local/dev posture — either is coherent ONLY with the persistence boundary extended to run-ledger + drafts + message store (the P0). Options: A. guard-all-doors in dogfood; B. encrypt ledger/drafts/messages and make beta the dev default; C. keep as-is and document dogfood as synthetic-only.
- **DP-03b (PAN redact-at-ingest, new R-15 row):** test-card PANs in free text are never product-needed (money boundary is tracking-only); propose Luhn-validated redaction at ingest in ALL modes. Does not weaken any ratified matrix row; changes customer text at rest.
- **DP-03c (BFF parity scope, FND-0340):** which backend-only doors need product UI before launch — DSR (Art.15/17) is the compliance-mandatory one; visa-radar/corporate/accounting/analytics/mandates/supplier/pre-departure each need a ship-or-document call. A CI route-map parity gate is ready to enforce whatever is decided.
- **DP-03d (Agency default currency, FND-0341):** replace the D1-RQ-01 "unmarked amounts = USD" convention with an AgencySettings default currency (India-first product).
- **DP-03e (Carried from Sim #3):** U4 occasion→date-window inference; LLM-lane destination-resolver sim (X-09 posture); commit authorization for the Sim #3+Sim #4 artifact sets.

## TRV-DP-04 (opened 2026-10-22, exploration topics 48-50 follow-through — owner decision outstanding)
- **DP-04a (Producer rail vendor, topics 48/50):** which externally-licensed producer supplies the sandbox lane (B6/B7, ADR-008 posture: sandbox = preview, never live). Evidence from the 2026-10-20 trvl probe (`data/experiments/trvl_probe_2026-10-20/`): trvl v1.27.0 is **PolyForm Noncommercial** — reference design only; honest typed provider statuses match our doctrine, but 30% of rows were unpriced, 27 were currency-converted estimates, and one hotel set mixed five currencies, so any ingestion needs the unpriced/converted/FX clamp gate at the boundary. Options: A. **Dida-Hotel-MCP** (official commercial wholesale MCP, 2M+ hotels — recommended first sandbox lane); B. **LetsFG** (MIT code, but the hosted letsfg.co API has its own ToS — requires a ToS review before any wiring); C. hold and keep the Amadeus sandbox as the only lane. Recommendation: A with the clamp gate, B pending ToS review, trvl never in production.
- **DP-04b (E1 WhatsApp direct channel, topic 36):** Meta business verification + 2-3 message templates for direct WhatsApp dispatch (the fare-drop draft and ask-loop currently stop at the link-only floor / DRAFT_AWAITING_OPERATOR). Real-world account action + per-message India rates (unverified until quota refresh); owner account gate, not a code choice.
- **Blocked:** producer adapter implementation (decision-free clamp layer can be built against any vendor's row shape once A/B is chosen); traveler-message dispatch beyond draft.


---

## TRV-DP-05 (decided 2026-10-25 by delegated authority — Sim #4 door-wave agent; revisit triggers noted per item)

Under the delegated-decision-authority correction (2026-10-25): reversible
design decisions are the agent's to make, document, and implement; a decision
record is revisable, a parked question is not. Each decision carries its
rationale, falsifier, and rollback.

- **DP-03a DECIDED: Option B — encrypt ledger/drafts/messages; encryption is
  the boundary.** Rationale: the Sim #4 P0 (FND-0326) proved guard-all-doors
  cannot work (three stores receive the same note; checks-on-doors leak by
  construction), while encryption composes with every posture and the FND-0327
  kid/rotation machinery already exists. Dogfood keeps its synthetic-data
  tripwire; beta becomes the dev default once ledger/draft/message encryption
  ships. Implementation: invariant-1 phase (multi-session, sequenced in the
  structural roadmap). Falsifier: if encrypted-ledger writes break the
  run-ledger replay contract in the first integration pass, fall back to
  guard-all-doors and re-decide. Rollback: decrypt-in-place via the rotation
  tool's inverse.

- **DP-03b DECIDED: PAN redact-at-ingest in all modes (Luhn-validated).**
  Rationale: card numbers are never product-needed (the money boundary is
  tracking-only, ADR-008), and storing them is pure PCI liability — redaction
  weakens no ratified matrix row. Implementation: queued (guard seam, S
  effort); flag R15_PAN_REDACTION default-on at ship so the owner can veto
  with a one-line env change. Falsifier: any legitimate workflow needing a
  raw PAN reopens this.

- **DP-03c DECIDED: DSR (Art.15/17) is compliance-mandatory — map its doors
  first; the other gap routes are ship-or-document per door, tracked in the
  parity snapshot.** Rationale: a data-subject request with no product surface
  is a regulatory failure regardless of API completeness. Falsifier: a
  compliance review ruling the API-only surface sufficient.

- **DP-03d DECIDED: AgencySettings.default_currency (INR default for this
  India-first deployment), replacing the D1-RQ-01 unmarked-USD convention;
  unmarked amounts fall back to USD only when the agency has no setting
  (backward compatible). Implementation: queued (S effort). Falsifier: an
  agency whose unmarked amounts are genuinely USD-dominated.

- **DP-03e DECIDED:** occasion-to-date-window inference implemented as a
  LABELED HYPOTHESIS (authority derived, epistemic hypothesis — never FACT;
  the truth taxonomy already supports this). LLM-lane destination-resolver sim
  stays gated on X-09 spend authorization (the only true owner-gate left).
  Commit authorization remains explicitly owner-only (git safety rule) — the
  Sim #3+4 artifact set stays uncommitted until you say so.
