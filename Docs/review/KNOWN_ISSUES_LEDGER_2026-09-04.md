# Known Issues Ledger — 2026-09-04

This is the companion issue ledger for [`Docs/LAUNCH_STATUS.md`](../LAUNCH_STATUS.md).
It records unresolved constraints that must not be hidden by local green tests.
The full 183-row lifecycle register remains authoritative for finding IDs;
this ledger is the operator-facing risk subset.

| Area | IDs | Current issue | Evidence / next action | Gate |
|---|---|---|---|---|
| Deployment and durability | S-11, N-07, LR-B07, F-09 | Revocations and run state are locally crash-safe but not shared across replicas | Promote to PostgreSQL or a ratified durable volume; run restart, backup/restore, failover, and convergence drills | Public blocker |
| Proposal truth | F-02, N-05, F-03 | Local proposal paths are tenant-bound, but hosted issuance/revocation and acceptance durability remain unproven | Verify hosted multi-worker issuance, revocation, expiry, and resource projection | Public blocker |
| Public/agency sample state | S-09, C-01, F-03, N-11 | Bookings, suppliers, and the legacy public proposal/persona surfaces still contain hardcoded or live-sounding residue even where the new paths are labelled sample/demo | Replace with canonical persisted provider records or an explicit unavailable/sample state; consolidate legacy proposal route and remove remaining identity/payload residue | S0 public blocker |
| Operational simulator mutation | S-09, C-01 | Disruption, crisis, GDS/distribution, FX, IROPS, and duty-of-care routes now fail closed or return explicit preview metadata locally; VCC, ghost-concierge, residual legacy copy, and provider execution remain unproven | Extend `RealityTier`/source/effects metadata to every remaining route; require external reference + idempotency before mutation; contain customer-visible copy; wire provider-backed actions only after contract and credential review | S1 public blocker |
| Provider reality | S-09, F-03, N-11, C-01 | Several adapters and dashboards remain simulations or carry live-sounding copy | Label, gate, wire, or archive each surface; obtain provider contracts and cost/failure semantics | Public blocker |
| Evaluation validity | E-01, E-02, E-03, E-06, E-07, E-08, E-10, E-11, N-02, N-03 | Extraction/pipeline producers and holdouts are incomplete; trajectory and calibrated judging are not promotion authority | Add independent producers, private holdouts, red-team corpus, and shadow evaluation | Public blocker |
| Semantic contracts | D-01, D-02, D-03, F-21, F-22, A-02 | Duration, flight inclusiveness, destination scope, epistemic authority, and retrieval semantics are not all canonical | Ratify contracts; implement schema/extractor/API/UI changes; benchmark real retrieval provider | Product gate |
| Frontend quality | A-05, A-06, A-11, A-12, A-15, A-16, A-17, F-17, F-19 | Competing fetch layers, generated-type drift, edge-auth uncertainty, missing browser/a11y proof, and provider-backed booking/supplier/proposal contracts; A-17's local non-modal semantics are corrected and local renders inspected but browser accessibility remains incomplete | Add drift/E2E/a11y gates, verify canonical BFF routes, and complete persisted provider-backed records; run browser/device accessibility observation for the WelcomeCard | Pilot gate |
| Agent/runtime safety | A-03, C-02, C-03, C-04, C-05, C-06, F-07, F-10, F-11, F-12 | Mock/live routing, orphaned modules, lease versioning, spend ceilings, and SSE limits remain incomplete | Produce wire/archive dossiers, runtime router contract, lease/version/spend/connection controls | Pilot gate |
| Audit and recovery | F-06, F-08, F-14, F-15, F-16, R-16 | Local audit continuity plus tamper/fork verification is covered; anchoring, gap/replay operations, dated-perishable ownership, confirmation defects, compensation, and trace correlation remain open | Add durable event lineage, external head anchoring, operator-facing gap/replay handling, owners/deadlines, claims, and trace reader | Pilot gate |
| Documentation and governance | A-07, A-08, A-09, A-10, R-01, R-02, R-04, R-06, R-07, R-08, G-12, G-13, G-15, G-17 | Stale references, ADR numbering, idea-pad drift, simulator caveats, business-model contradictions, and persona adoption remain | Consolidate canonical records without deleting history; refresh through approved tools | Pilot gate |
| Legal and privacy | R-09, R-10 plus launch audit legal gates | Signup posture, business model, PII, retention, consent, DPA/TOS, and provider processing lack human sign-off | Obtain explicit owner/legal decisions before customer exposure | Public blocker |
| Git and ownership | A1-1, A-14, A-21, F-04 | The dirty tree contains hundreds of custody-covered source/concurrent paths that are not semantically classified; current tree is not a release slice | Classify by coherent change, refresh attestation/hooks, and authorize an exact snapshot separately | Release gate |

## Evidence discipline

- Local tests, static checks, and synthetic fixtures are Tier 1/2 evidence only.
- Live local PostgreSQL is stronger for database behavior but is not hosted
  production proof.
- Browser, provider, device, legal, customer, backup/restore, and release
  claims require their own evidence.
- An issue may be closed only when the matching evidence tier and owner are
  recorded; a passing aggregate does not close an unrelated boundary.
