# Audit Remediation — 2026-10-25 (FND-0341 / FND-0375 / FND-0376 / FND-0373)

Executed under delegated decision authority (reversible design decisions: decide +
record + implement + revisit trigger; only money/irreversible/git/ADR-posture go to
the owner). All closures carry evidence in `Docs/review/FINDINGS_STORE.jsonl` via
`scripts/findings.py`; this doc is the narrative record.

## FND-0341 (P2, CLOSED — shipped) — unmarked amounts defaulted to USD

**First-principles restatement.** In an India-first product, a bare budget amount in
a traveler's own words ("60k total max") is rupees. Reading it as $60,000 is not a
missing feature — it is a wrong-money-reading defect that poisons every downstream
gate (budget vs quote comparison, margin floors, FINANCIAL_BOUND facts).

**What was already there (supersession check).** `AgencySettings.default_currency =
"INR"` existed (`src/intake/config/agency_settings.py:476`) but had **zero
consumers** — the setting was a promise the pipeline never kept. Extraction's
`_currency_code()` returned a hardcoded `"USD"` for unmarked tokens, and the slot
fallback (`budget_result.get("currency", "INR")`) could never fire because the key
was always present.

**The fix (choke point, not a patch).**
- `PLATFORM_DEFAULT_CURRENCY = "INR"` in `src/intake/extractors.py` — the platform
  constant; the agency setting overrides it per locale.
- `_extract_budget(text, default_currency=...)`: precedence is **explicit marker >
  lakh/crore unit signal (INR, Indian-market signal) > agency/platform default**.
- Threading: `extract()` → `_extract_from_freeform` / `_extract_from_hybrid`;
  `src/intake/orchestration.py` wires `AgencySettings.default_currency` at the one
  place settings are already resolved — one hop, no parallel system.
- **Two latent defects found and fixed in the blast radius:**
  1. `"rupee"/"rupees"` matched the token *pattern* but was absent from the
     currency *map* — "5000 rupees" would have resolved to the (new) default
     instead of FACT-grade INR evidence.
  2. The `currency_after` evidence group was **dead since inception**: the greedy
     `\s*` before it swallowed the separating space, so "5000 USD" parsed as
     unmarked. Replaced with a deterministic post-span peek
     (`_currency_after`), which also means explicit USD now genuinely wins.

**Verification.** `test_budget_currency_ranges_2026_09_04.py` 11/11 (the finding's
own "60k total max" case → INR 60000; agency override seam; rupee word → INR;
lakh dominance; explicit USD wins; unmarked *range* → INR). Regression: 139 tests
across the extraction suites + 177 across budget-consuming suites
(adversarial corpus, canonical roundtrip, reassessment continuity, compiler budget
gate, confirmation/document extraction) — **0 failed**. Side benefit: main
extraction and the reassessment path (which already INR-defaulted via
`Normalizer.parse_budget`) no longer disagree.

**Revisit trigger:** if the product expands beyond India-first (agency locales
where the bare-amount convention differs), the seam is
`AgencySettings.default_currency` — config, not code.

## FND-0375 (P3, CLOSED — shipped) — IVR call_sid unvalidated in Twilio URL path

Same class as FND-0372 (URL-interpolation hardening); the IVR router was outside
that sweep. `spine_api/routers/ivr_gateway.py`:
- `_CALL_SID_RE` — Twilio `CA` + 32 hex, or the in-tree preview sentinel
  (`CA-PREVIEW-` + 16 hex, produced by `_preview_call_sid`). Enforced at the poll
  endpoint **before** any provider URL exists: malformed sid →
  `INVALID_CALL_SID`, `provider_connected: false`, `deterministic_preview` —
  honest, no fetch, no raise.
- Both Twilio URL builds (place-call `Calls.json` POST, poll `Calls/{sid}.json`
  GET) validate `account_sid` **and** `call_sid` format and raise before
  interpolation (defense-in-depth: account_sid is server config, but a bad config
  should fail loudly, not address a wrong account subresource).
- Path-traversal shapes ("CA../../Accounts/…") are rejected at FastAPI routing
  (404) before the handler — test-pinned both rejection modes.

**Verification:** `test_ivr_router_honesty.py` 9/9 (crafted sids, preview
sentinel short-circuit preserved, format helpers), `test_ivr_bypass_bot.py` green,
ruff clean. No route-shape changes → snapshots unaffected.

## FND-0376 (P3, CLOSED — resolved; decision ratified, code already landed)

Supersession check before any work: `_preserve_authoritative_facts`
(`spine_api/persistence.py:3979`) already implements the ruling — **precedence +
operator tombstones** (decision record
`Docs/adr/DECISION_REC_FND0376_DESTINATION_TOMBSTONES_2026-10-25.md`). Merge was
rightly rejected: a union cannot express removal intent — an operator who deletes
a candidate must not have it resurrected by re-extraction. Re-extracted candidates
are filtered through `destination_tombstones`; a tombstone is VOIDED only when the
traveler's new note names the candidate explicitly (canonical customer >
operator). Verified: `test_fnd0376_destination_tombstones.py` 5/5 (filter,
reassertion voiding, FND-0309 behavior untouched, case-insensitivity,
carried-forward slots also filtered). Closed with that evidence.

## FND-0373 (P2, KEPT OPEN — active ownership documented)

Decomposition check against the current tree: (1) the payment_mandates RLS
migration (`alembic/versions/force_rls_payment_mandates.py`) is staged
uncommitted; (2) the day-first date-form gap ("10 June 2027 to 17 June 2027" → no
`date_start` on dependent recompute) is **localized as FND-0368 root cause #4 by
the active parallel lane** (commits `d6bdb2cc`, `b474782c`, `ef7945ef`) — fix in
flight there, deliberately not duplicated; (3) `_make_json_serializable` cycle
recursion not re-verified this pass; (4) stale tests ride the lane's repro work.
A store note records the handoff; the finding closes after the lane lands
FND-0368 and a fresh full-suite baseline runs.

## Verdicts

- Code ready: YES (all three shipped/verified items; suites green; ruff clean).
- Feature-ready: YES (currency behavior correct end-to-end incl. the operator
  queue surfaces that read these facts; IVR hardened at the boundary).
- Launch-ready: unchanged from the standing assessment — the open P1/P2s
  (FND-0368 in flight, FND-0373 pending baseline) remain the blockers, owned.
- Commits: none by this session (standing rule — whole-tree commits are
  owner-directed; this work rides them uncommitted).
