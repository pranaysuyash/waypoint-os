# TS Register Execution Handoff — training-session items TS-01…TS-06 (2026-09-09)

**Scope:** full execution of the training-session findings register (`Docs/exploration/CHATGPT_SYSTEMS_TRAINING_SESSION_FINDINGS_2026-09-09.md`): two implementations (TS-01, TS-04), four exploration documents (TS-02/03/05/06), four review cycles, full-suite verification. All work is in the working tree, **uncommitted** (git safety: no commit without owner approval; note the Mimosa SSRF gate from the prior roadmap entry still blocks the staged tree independently of this work).

---

## 1. Executive summary

All six TS register items are closed: TS-01 (hard itinerary-feasibility validators) and TS-04 (provenance actor vocabulary) are implemented, review-hardened across 4 cycles, and fully tested; TS-02/03/05/06 are delivered as exploration/design documents with explicit decision gates. State: **Code ✅ · Feature ✅ (TS-01/04) · Launch-readyness unchanged** (nothing here alters the launch envelope; the validators are additive deterministic checks that abstain without declared data). Next immediate action: none blocked on this handoff — TS-03 S1–S3 and TS-06 implementation are the natural follow-ups, sequenced per the register.

## 2. Technical changes

**TS-01 — `src/decision/constraint_engine.py`** (canonical home extended, beside existing MCT/overlap/passport checks):

| Check family | Constraint IDs | Type | Semantics |
|---|---|---|---|
| Ground-access buffer (§1b) | `GROUND_OVERLAP_`, `GROUND_ACCESS_DEFICIT_` / `GROUND_BUFFER_TIGHT_` | HARD / SOFT | Negative gap or unmet **explicit** per-node requirement (`required_transfer_minutes` / `recommended_arrival_buffer_minutes` — TimedEntry vocabulary) → hard; heuristic mode defaults (FLIGHT 90m, surface 45m, TRANSFER 15m) → advisory only. Door-drop-off pair (TRANSFER→HOTEL_CHECKIN) suppresses only the heuristic, never the hard checks |
| First-night lodging coverage (§1c) | `UNCOVERED_FIRST_NIGHT_` | HARD | Interval coverage per arrival: lodging (`HOTEL_CHECKIN` ∪ `HOTEL_STAY`) must intersect [arrival, arrival+12h]. Return legs skipped via `RETURN_LEG_OF` edges or refined final-arrival rule (homeward only if all lodging already ended); transit arrivals (<12h onward transport departure) exempt; overnight stranding still flagged |
| Occupancy (§4b) | `OCCUPANCY_EXCEEDED_` | HARD | First producer of the dormant `CAPACITY_ROOMING` category; metadata shapes `max_guests`/`capacity`/`rooms[]`/`room_count`×`max_occupancy_per_room`; abstains without declared capacity |
| Ticket pax (§4b) | `PAX_OVERBOOKED_` / `PAX_MISMATCH_` / `PAX_PARTIAL_` | HARD / HARD / SOFT | Over-booking always hard; under-coverage hard on whole-party products (transport/lodging/transfer), advisory on optional nodes |
| Product age rules (§4b) | `AGE_RULE_` | HARD | Only unambiguous whole-party bounds (`min_age`/`max_age`); fare-CATEGORY keys (`infant_max_age`, `child_fare_min_age`) deliberately excluded |

Also: §1 connection checks extended to all transport modes with `SURFACE_MODE_CONNECT_MIN_MINUTES=20` for rail/ferry/cruise (airport MCT no longer leaks to surface modes); `_as_utc` normalization in §1; None-time guards in §1/§1b; new `party_size` parameter (caller `src/orchestration/proposal_compiler.py` now passes `traveler_count`; `spine_api/routers/constraints.py` unchanged — already passes `travelers`).

**TS-04 — `spine_api/services/field_merge.py`:** canonical actor vocabulary `operator | customer | system | tool | provider`. Precedence: **commercial: provider(4) > operator(3) > tool/system(2) > customer(1)**; **preference: customer(3) > operator(2) > machines(1)**. Trust boundary: `CLIENT_ACTOR_ROLES = (operator, customer)` — a client-claimed `provider` folds to operator on the `/optimistic-sync` surface; internal writers opt in via `resolve_field_merge(..., allow_internal_actors=True)`; stored provenance parsed against the full vocabulary so stored internal actors keep rank. The unattributed-commercial conservative guard is now rank-based (any incoming rank < operator rejected; provider applies). `spine_api/contract.py` `actor_role` description updated.

**Tests:** `tests/test_constraint_engine_feasibility.py` (31 tests), `tests/test_field_merge_actor_vocabulary.py` (18 tests). Every family has paired fail/pass shapes (S1 + S3 mutation sensitivity); the regression guards prove the exact reviewer-constructed false-positive shapes now pass/fail correctly.

**Exploration docs:** `TS02_QUOTE_FRESHNESS_CONTRACT_2026-09-09.md` · `TS03_MULTIMODAL_INTAKE_COMPLETION_2026-09-09.md` · `TS05_PARALLEL_ORCHESTRATION_DESIGN_NOTE_2026-09-09.md` (parked w/ unpark trigger) · `TS06_CANDIDATE_ROUTE_STRUCTURES_2026-09-09.md`.

**Drift resolved in-pass (shared-tree doctrine):** route/OpenAPI parity snapshots regenerated (`scripts/snapshot_server_routes.py --write`) — diff verified to contain exactly the parallel checker-wave routes (`/api/public-checker/disputes`, `/trip/{trip_id}`, `/trip/{trip_id}/export`); nothing from this work added paths.

## 3. Code-review findings (4 cycles, same reviewer)

- **Cycle 1 (logic):** P0 — first-night check compared every check-in to the *earliest* trip arrival (false hard-reject on ALL multi-check-in itineraries; my single-hotel tests masked it) → rewritten to interval coverage per arrival. P1 — fare-category keys treated as whole-party hard eligibility → restricted to explicit `min_age`/`max_age`. P2s — pax partial-booking over-fire (split hard/advisory), transfer-coverage holes (TRANSFER→commitment advisory; rail→transfer overlap), TS-04 customer-only conservative guard (made rank-based).
- **Cycle 2 (defensive):** P1 — per-arrival 12h window didn't model return legs (false reject when any ground node follows the homeward flight) or transit days (long multi-leg journeys) → `RETURN_LEG_OF` skip + refined final-arrival discriminator + transit exemption. P2s — compiler standing advisory (door-drop-off, heuristic-only suppression), surface-mode MCT calibration, §1 None-guard, HOTEL_STAY as lodging.
- **Cycle 3 (adversarial):** P1 #1 — TRANSFER in the transit-exemption set swallowed the canonical "lands→transfer→no hotel" case (the check's founding case) → departure set restricted to transport modes. P1 #2 — door-drop-off exemption was over-broad, disabling hard checks for the pair → narrowed to heuristic-only. P2s — §1 `_as_utc`, RETURN_LEG_OF producer contract, malformed-lodging asymmetry, <12h-layover policy.
- **Cycle 4: mergeable — sign-off.** "The interval coverage core, the refined final-arrival discriminator, surface MCT, the None guard, §4b, and field_merge are verified correct and ready."

**Final verdict: APPROVED for merge** (staging/commit awaits owner approval + the pre-existing Mimosa gate).

## 4. Test results (evidence)

- Full backend suite (dev server stopped, `scripts/run_backend_tests.sh`): **4,250 passed / 0 failed / 44 skipped** (baseline at wave start 4,228 incl. 2 parity failures → +22 tests across the review cycles and the owner-confirmed layover advisory; parity fixed). Tier 2–3 evidence; S2 satisfied for every fixed defect (each failed for the stated reason before its fix — the cycle-1 P0 and cycle-3 P1s were caught as failing shapes and their tests now prove the fix); S3 mutation-style coverage via paired pass/fail shapes.
- `uv run mypy` (curated 21-file scope): clean. `uv run ruff check --fix .` (repo-wide): clean.

## 5. Audit assessment (11 dimensions)

- Code: ✅ (4,247/0, lint/type clean, 4 review cycles) · Operational: ✅ for TS-01 (violations flow into the existing constraint report the router already serves); 🟡 TS-04 (no internal writer uses the new roles yet — by design) · UX: ✅ (soft advisories carry actionable relaxation options) · Logical: ✅ (abstention-without-data is the consistent rule) · Commercial: ✅ (occupancy/pax checks protect money paths) · Data integrity: ✅ (nothing silently lost; provenance preserved) · Quality: ✅ (49 new tests, paired sensitivity) · Compliance: 🟡 PII unchanged (no new data collected) · Ops readiness: ✅ (no new deploy steps; validators are in-process) · Critical path: ✅ no new blockers · **Verdict: merge YES.**

## 6. Launch readiness

Code ready: ✅. Feature ready: ✅ TS-01/TS-04; TS-02 recheck engine rides B6/B7; TS-03/TS-06 documented not built (by design). Launch ready: unchanged from `LAUNCH_STATUS.md` — this wave neither blocks nor unblocks the envelope.

## 7. Open items carried forward (reviewer P2s + policy confirmations)

1. **Owner policy CONFIRMED + implemented (2026-09-09):** <12h onward-connection exempts an arrival from first-night coverage — no hard block, ever. The layover-comfort signal ships as a **SOFT operator suggestion**: a transit-exempt arrival with no lodging covering it and a ≥6h wait to the onward leg emits `LONG_LAYOVER_NO_HOTEL_` (TEMPORAL_PACING, advisory) with a transit-room upsell relaxation option. Short connections (<6h) stay silent; a transit hotel covering the wait suppresses the advisory; >12h stranding with no onward leg remains the hard `UNCOVERED_FIRST_NIGHT_` gate. Constant: `LONG_LAYOVER_ADVISORY_MIN_HOURS = 6.0` in `constraint_engine.py`.
2. **Producer contract (P2 #2):** emit `RETURN_LEG_OF` edges when building journey graphs (compiler + future fulfillment writers) so return legs are structurally labeled rather than inferred.
3. **Malformed-lodging asymmetry (P2 #3):** all-before-trip lodging silently passes vs. covering-node-missing-`start_time` can hard-reject — noted, accepted for malformed input.
4. **Pre-existing (reviewer side-observation):** multimodal endpoints (`/voice-note`, `/image-ocr`) write packet fields with plain last-write-wins, bypassing field-merge precedence — register as a follow-up to route them through `resolve_field_merge` as `tool` actors (now possible thanks to TS-04).
5. TS-03 S1–S3 (attachment envelope + vision-lane routing + injection fixtures) and TS-06 enumerator are the next implementation units, per the register's sequencing.

**Checklist applied: IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md**
